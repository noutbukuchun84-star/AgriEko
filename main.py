from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3

app = Flask(__name__)

# Yuklangan rasmlar saqlanadigan papka joyi
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MA'LUMOTLAR BAZASINI SOZLASH (SQLite)
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # E'lonlar jadvalini yaratish
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

# 1. BOSH SAHIFANI OCHISH (Bazadan hamma e'lonlarni o'qib HTMLga yuboradi)
@app.route('/')
def home():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Ma'lumotlarni qulay o'qish uchun
    cursor = conn.cursor()
    
    # E'lonlarni eng yangisidan boshlab saralab olish
    cursor.execute('SELECT * FROM elonlar ORDER BY id DESC')
    barcha_elonlar = cursor.fetchall()
    conn.close()
    
    # E'lonlarni bosh sahifaga (index.html) uzatamiz
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
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            image_name = file.filename

        # MA'LUMOTLARNI BAZAGA YOZISH
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO elonlar (title, category, price, phone, description, image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, category, price, phone, description, image_name))
        conn.commit()
        conn.close()

        print(f"Yangi e'lon bazaga saqlandi: {title}")
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
