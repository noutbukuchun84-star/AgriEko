from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3

app = Flask(__name__)

# Yuklangan rasmlar saqlanadigan papka joyi
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Vercel-da xatolik bermasligi uchun bazani /tmp papkasiga bog'laymiz
DB_PATH = '/tmp/database.db'

# MA'LUMOTLAR BAZASINI SOZLASH (SQLite)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elonlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            price TEXT,
            phone TEXT,
            description TEXT,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Sayt yurganda bazani yaratib oladi
init_db()

# 1. BOSH SAHIFANI OCHISH
@app.route('/')
def home():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM elonlar ORDER BY id DESC')
    barcha_elonlar = cursor.fetchall()
    conn.close()
    return render_template('index.html', elonlar=barcha_elonlar)

# 2. E'lon berish sahifasini ochish
@app.route('/elon.html')
def elon_page():
    return render_template('elon.html')

# 3. Chat sahifasini ochish
@app.route('/chat.html')
def chat_page():
    return render_template('chat.html')

# 4. E'lon formasi yuborilganda ma'lumotlarni bazaga saqlash
@app.route('/elon-yuborish', methods=['POST'])
def elon_yuborish():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        price = request.form.get('price')
        phone = request.form.get('phone')
        description = request.form.get('description')
        
        file = request.files.get('file-upload')
        image_name = ""
        
        if file and file.filename != '':
            # Vercel-da rasmlarni ham vaqtinchalik /tmp papkasiga yoki static ichiga yozishga urinib ko'ramiz
            if not os.path.exists(UPLOAD_FOLDER):
                try:
                    os.makedirs(UPLOAD_FOLDER)
                except:
                    pass
            try:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
                image_name = file.filename
            except:
                image_name = "" # Agar rasm saqlashda server ruxsat bermasa xato bermay o'tib ketadi

        # MA'LUMOTLARNI BAZAGA YOZISH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO elonlar (title, category, price, phone, description, image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, category, price, phone, description, image_name))
        conn.commit()
        conn.close()

        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
