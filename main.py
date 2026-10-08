from flask import Flask, render_template, request, redirect, url_for
import os

# HTML fayllar templates papkasida emas, bosh papkada turgani uchun template_folder='.' deb ko'rsatamiz
app = Flask(__name__, template_folder='.')

# Yuklangan rasmlar saqlanadigan papka joyi
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 1. Bosh sahifani ochish
@app.route('/')
def home():
    return render_template('index.html')

# 2. E'lon berish sahifasini ochish
@app.route('/elon.html')
def elon_page():
    return render_template('elon.html')

# 3. Chat sahifasini ochish
@app.route('/chat.html')
def chat_page():
    return render_template('chat.html')

# 4. E'lon formasi yuborilganda ma'lumotlarni qabul qilish
@app.route('/elon-yuborish', methods=['POST'])
def elon_yuborish():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        price = request.form.get('price')
        phone = request.form.get('phone')
        description = request.form.get('description')
        
        # Rasm faylini qabul qilib olish
        file = request.files.get('file-upload')
        
        if file and file.filename != '':
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

        print("--- YANGI E'LON KELDI ---")
        print(f"Nomi: {title}, Kategoriya: {category}, Narxi: {price}, Tel: {phone}")
        print("-------------------------")

        return redirect('/')

if __name__ == '__main__
