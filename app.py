import os
import rarfile
import gdown
import logging
from flask import Flask, render_template_string, request, redirect, session, url_for

# ========== الإعدادات ==========
app = Flask(__name__)
app.secret_key = "fsint-super-secret-key-123"

FILE_ID = "1MDSf7r-vekMUTxx1q0osUswpERso5xyv"
RAR_PATH = "data/data.rar"
EXTRACT_DIR = "data/extracted/"

USERS = {
    "fro": "frofro",
    "barod": "barodbarod"
}

INDEX = {}

logging.basicConfig(level=logging.INFO)

# ========== HTML مباشر ==========
LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FSINT — تسجيل دخول</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
        body { background: #0f0f1a; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-box { background: #1a1a2e; padding: 2.5rem; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.6); width: 360px; border: 1px solid #2a2a4a; }
        h1 { color: #e0e0ff; text-align: center; margin-bottom: 0.5rem; font-size: 1.8rem; }
        .subtitle { color: #8888aa; text-align: center; margin-bottom: 2rem; font-size: 0.9rem; }
        input { width: 100%; padding: 12px 16px; margin-bottom: 16px; border: 1px solid #2a2a4a; border-radius: 10px; background: #0f0f1a; color: #e0e0ff; font-size: 1rem; outline: none; transition: 0.2s; }
        input:focus { border-color: #4a4aff; box-shadow: 0 0 0 3px rgba(74,74,255,0.2); }
        button { width: 100%; padding: 12px; background: #4a4aff; color: #fff; border: none; border-radius: 10px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: 0.2s; }
        button:hover { background: #5a5aff; transform: translateY(-1px); }
        .error { color: #ff6b6b; text-align: center; margin-top: 1rem; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔍 FSINT</h1>
        <p class="subtitle">دخول للمصرّح لهم فقط</p>
        <form method="POST">
            <input type="text" name="username" placeholder="يوزر" required autocomplete="off">
            <input type="password" name="password" placeholder="باسورد" required autocomplete="off">
            <button type="submit">دخول</button>
        </form>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

INDEX_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FSINT — بحث</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
        body { background: #0f0f1a; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background: #1a1a2e; padding: 2.5rem; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.6); width: 500px; border: 1px solid #2a2a4a; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        h1 { color: #e0e0ff; font-size: 1.5rem; }
        .user-info { color: #8888aa; font-size: 0.85rem; }
        .user-info span { color: #4a4aff; font-weight: 600; }
        .logout-btn { color: #ff6b6b; text-decoration: none; font-size: 0.85rem; margin-right: 1rem; }
        .logout-btn:hover { text-decoration: underline; }
        input { width: 100%; padding: 14px 18px; margin-bottom: 12px; border: 1px solid #2a2a4a; border-radius: 10px; background: #0f0f1a; color: #e0e0ff; font-size: 1rem; outline: none; transition: 0.2s; }
        input:focus { border-color: #4a4aff; box-shadow: 0 0 0 3px rgba(74,74,255,0.2); }
        button { width: 100%; padding: 12px; background: #4a4aff; color: #fff; border: none; border-radius: 10px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: 0.2s; }
        button:hover { background: #5a5aff; transform: translateY(-1px); }
        .result-box { margin-top: 1.5rem; padding: 1.2rem; border-radius: 10px; background: #0f0f1a; border: 1px solid #2a2a4a; min-height: 60px; display: flex; align-items: center; justify-content: center; }
        .result-box.found { border-color: #4a4aff; }
        .result-box.not-found { border-color: #ff6b6b; }
        .result-label { color: #8888aa; font-size: 0.8rem; margin-bottom: 4px; text-align: center; }
        .result-value { color: #e0e0ff; font-size: 1.3rem; font-weight: 600; text-align: center; direction: ltr; }
        .hint { color: #555; text-align: center; font-size: 0.8rem; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 FSINT</h1>
            <div class="user-info">
                <span>{{ user }}</span>
                <a href="/logout" class="logout-btn">خروج</a>
            </div>
        </div>
        <form method="POST">
            <input type="text" name="query" placeholder="يوزر أو ID (مثال: @username أو 12345)" value="{{ query }}" required autocomplete="off">
            <button type="submit">🔎 بحث</button>
        </form>
        {% if result is not none %}
        <div class="result-box {{ 'found' if result != '❌' else 'not-found' }}">
            <div>
                <div class="result-label">{{ 'رقم الهاتف' if result != '❌' else 'النتيجة' }}</div>
                <div class="result-value">{{ result }}</div>
            </div>
        </div>
        {% endif %}
        <div class="hint">أدخل username أو ID للبحث في قاعدة البيانات</div>
    </div>
</body>
</html>
"""

# ========== تحميل وفك البيانات ==========
def download_and_extract():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(RAR_PATH):
        logging.info("⬇️ جاري تحميل الملف من Drive...")
        gdown.download(f"https://drive.google.com/uc?id={FILE_ID}", RAR_PATH, quiet=False)
        logging.info("✅ تم التحميل")
    if not os.path.exists(EXTRACT_DIR) or not os.listdir(EXTRACT_DIR):
        logging.info("📂 جاري فك الضغط...")
        with rarfile.RarFile(RAR_PATH) as rf:
            rf.extractall(EXTRACT_DIR)
        logging.info(f"✅ تم فك الضغط إلى {EXTRACT_DIR}")
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
                            INDEX[parts[0].strip().lower()] = parts[1].strip()
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
        return render_template_string(LOGIN_PAGE, error="❌ يوزر أو باس غلط")
    return render_template_string(LOGIN_PAGE)

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
            for key, val in list(INDEX.items())[:500]:
                if query in key:
                    result = val
                    break
            if not result:
                result = "❌"
    return render_template_string(INDEX_PAGE, result=result, query=query, user=session['user'])

# ========== للتشغيل ==========
if __name__ == "__main__":
    download_and_extract()
    app.run(host="0.0.0.0", port=10000)
