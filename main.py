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
    * { box-sizing: border-box; margin: 0; }

body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  background: #f0fdf4;
  color: #14532d;
  line-height: 1.5;
}

.page { max-width: 560px; margin: 0 auto; padding: 24px 16px 32px; }

h1 { font-size: 26px; font-weight: 800; line-height: 1.2; }
.sub { margin: 6px 0 20px; color: #4b6b57; font-size: 15px; }

.card {
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  display: grid;
  gap: 16px;
  box-shadow: 0 8px 24px rgba(22, 101, 52, .08);
}

.field { display: grid; gap: 6px; }
.field > span { font-size: 14px; font-weight: 600; }

input[type="text"], input[type="number"], input[type="tel"], select, textarea {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  font: inherit;
  font-size: 16px; /* iOS'da zoom bo'lmasligi uchun */
  color: inherit;
  background: #fff;
  border: 1.5px solid #bbf7d0;
  border-radius: 12px;
  outline: none;
  transition: border-color .2s, box-shadow .2s;
}
textarea { height: auto; padding: 12px 14px; resize: vertical; }

input:focus, select:focus, textarea:focus {
  border-color: #16a34a;
  box-shadow: 0 0 0 4px rgba(22, 163, 74, .15);
}

.input-suffix, .input-prefix { position: relative; display: flex; align-items: center; }
.input-suffix em, .input-prefix em {
  position: absolute; font-style: normal; font-weight: 600; color: #15803d;
}
.input-suffix em { right: 14px; }
.input-suffix input { padding-right: 56px; }
.input-prefix em { left: 14px; }
.input-prefix input { padding-left: 62px; }

.drop {
  display: grid; justify-items: center; gap: 2px;
  padding: 24px 16px;
  text-align: center;
  background: #f0fdf4;
  border: 2px dashed #86efac;
  border-radius: 16px;
  cursor: pointer;
  transition: background .2s, border-color .2s;
}
.drop:hover { background: #dcfce7; border-color: #16a34a; }
.drop strong { color: #15803d; }
.drop small { color: #6b8f78; font-size: 13px; }

.submit {
  height: 50px;
  border: 0;
  border-radius: 14px;
  font: inherit;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #16a34a, #15803d);
  box-shadow: 0 6px 16px rgba(22, 163, 74, .35);
  cursor: pointer;
}
.submit:active { transform: scale(.98); }

footer { margin-top: 24px; text-align: center; font-size: 13px; color: #6b8f78; }
