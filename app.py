import os
import rarfile
import gdown
import logging
from flask import Flask, render_template, request, redirect, session, url_for

# ========== الإعدادات ==========
app = Flask(__name__)
app.secret_key = "fsint-super-secret-key-123"  # غيرها لو تحب

FILE_ID = "1MDSf7r-vekMUTxx1q0osUswpERso5xyv"
RAR_PATH = "data/data.rar"
EXTRACT_DIR = "data/extracted/"

# ========== المستخدمين ==========
USERS = {
    "fro": "frofro",
    "barod": "barodbarod"
}

INDEX = {}  # خريطة البحث العمومية

logging.basicConfig(level=logging.INFO)

# ========== تحميل وفك البيانات ==========
def download_and_extract():
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # نزل الملف من Drive لو ما هو موجود
    if not os.path.exists(RAR_PATH):
        logging.info("⬇️ جاري تحميل الملف من Drive...")
        url = f"https://drive.google.com/uc?id={FILE_ID}"
        gdown.download(url, RAR_PATH, quiet=False)
        logging.info("✅ تم التحميل")
    
    # فك الضغط
    if not os.path.exists(EXTRACT_DIR) or not os.listdir(EXTRACT_DIR):
        logging.info("📂 جاري فك الضغط...")
        with rarfile.RarFile(RAR_PATH) as rf:
            rf.extractall(EXTRACT_DIR)
        logging.info(f"✅ تم فك الضغط إلى {EXTRACT_DIR}")
    
    # بناء الفهرس
    build_index()

def build_index():
    global INDEX
    INDEX = {}
    for root, dirs, files in os.walk(EXTRACT_DIR):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line or '|' not in line:
                            continue
                        parts = line.split('|')
                        if len(parts) >= 2:
                            key = parts[0].strip().lower()
                            val = parts[1].strip()
                            INDEX[key] = val
            except Exception as e:
                logging.warning(f"⚠️ خطأ في {fname}: {e}")
    logging.info(f"📊 تم فهرسة {len(INDEX)} سجل")

# ========== الصفحات ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password'].strip()
        
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="❌ يوزر أو باس غلط")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    result = None
    query = ""
    
    if request.method == 'POST':
        query = request.form['query'].strip().lower().lstrip('@')
        if query in INDEX:
            result = INDEX[query]
        else:
            # بحث جزئي (أول 500 سجل)
            for key, val in list(INDEX.items())[:500]:
                if query in key:
                    result = val
                    break
            if not result:
                result = "❌"
    
    return render_template('index.html', result=result, query=query, user=session['user'])

# ========== للتشغيل على رندر ==========
if __name__ == "__main__":
    download_and_extract()
    app.run(host="0.0.0.0", port=10000)
