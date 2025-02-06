from flask import Flask,request,redirect,flash,render_template,url_for,send_from_directory

from fpdf import FPDF
import os
from werkzeug.utils import secure_filename
import secrets

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

app=Flask(__name__)

UPLOAD_FOLDER = os.path.join('static')

if not os.path.exists(UPLOAD_FOLDER): 
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = secrets.token_hex(16)





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    images = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
    return render_template('index.html', images=images)



@app.route('/discard', methods=['POST'])
def discard_images():
    discarded_images = request.form.getlist('discarded_images')
    if discarded_images:
        for image in discarded_images:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image))
                flash(f"Removed: {image}")
            except Exception as e:
                flash(f"Error removing {image}: {str(e)}")
    return redirect(url_for('home'))



def compile():
    pdf = FPDF()
    pdf.set_auto_page_break(0)
    img_lis = [x for x in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(x)]
    
    if not img_lis:
        flash("No valid images found in the uploads directory")
        return None
    
    for img in img_lis:
        try:
            image = os.path.join(app.config['UPLOAD_FOLDER'], img)
            pdf.add_page()
            pdf.image(image, w=200, h=260)
        except Exception as e:
            flash(f"Error adding image {img} to PDF: {str(e)}")
    
    pdf_output_path = os.path.join(app.config['UPLOAD_FOLDER'], "images.pdf")
    pdf.output(pdf_output_path)
    return pdf_output_path


@app.route('/compile', methods=['GET'])
def compile_pdf():
    try:
        pdf_path = compile()
        if pdf_path:
            return send_from_directory(app.config['UPLOAD_FOLDER'], "images.pdf", as_attachment=True)
        else:
            flash("Failed to compile PDF")
            return redirect(url_for('home'))
    except Exception as e:
        flash(f"Error compiling PDF: {str(e)}")
        return redirect(url_for('home'))




import uuid

@app.route("/img", methods=["POST"])
def edit():
    if 'file' not in request.files:
        flash("No file part in the request")
        return redirect(url_for('home'))

    file = request.files.get('file')
    if file.filename == '':
        flash("No file selected")
        return redirect(url_for('home'))

    if file and allowed_file(file.filename):
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        try:
            file.save(file_path)
            flash(f"File uploaded successfully as {unique_filename}")
        except Exception as e:
            flash(f"Error saving file: {str(e)}")
            return redirect(url_for('home'))
        
        return redirect(url_for('home'))
    
    flash("Invalid file format")
    return redirect(url_for('home'))


@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



if __name__=="__main__":
    app.run(debug=True)