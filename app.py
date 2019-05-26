import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug import secure_filename
app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['pdf', 'PDF', 'zip', 'ZIP'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('./index.html')

@app.route('/send', methods=['GET', 'POST'])
def send():
    if request.method == 'POST':
        img_file = request.files['img_file']
        if img_file and allowed_file(img_file.filename):
            filename = secure_filename(img_file.filename)
            uppath = os.path.join("/var/www/app/marksheet/static/uploads", filename)
            downpath = os.path.join("/var/www/app/marksheet/static/downloads", filename+".xls")
            img_file.save(uppath)
            command = "cd /var/www/app/marksheet; python3 main.py "+uppath+" "+downpath
            os.system(command)
            return render_template('index.html', command=command, download_url="static/downloads/"+filename+".xls")
        else:
            return ''' <p>invalid file type</p> '''
    else:
        return redirect(url_for('index'))

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.debug = True
                        
