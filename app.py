from flask import Flask, request, render_template_string, send_file, render_template
import requests
import re
import csv
import io
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)
DB_NAME = "leads_b2b_pro.db"

# --- CREDENCIALES ---
API_KEY = "c4d338518fmsh31a457d13e649b8p146580jsn30ec67d26e2b"
HOST_MAPS = "local-business-data.p.rapidapi.com"
HOST_HUNTER = "hunter-io.p.rapidapi.com"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS leads 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, empresa TEXT, 
                     direccion TEXT, web TEXT, email TEXT, tel TEXT, rating REAL, 
                     reviews INTEGER, tech TEXT, social TEXT)''')
    conn.commit()
    conn.close()

def analizar_web_pro(web):
    email, tech, social = "No encontrado", "N/A", "N/A"
    if not web or web == 'N/A': return email, tech, social
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(web, headers=headers, timeout=5)
        html = res.text
        # Emails
        mails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
        email = mails[0].lower() if mails else "No visible"
        # Tech & Social
        if "wp-content" in html: tech = "WordPress"
        elif "shopify" in html: tech = "Shopify"
        redes = []
        if "linkedin.com" in html: redes.append("LinkedIn")
        if "facebook.com" in html: redes.append("FB")
        social = ", ".join(redes) if redes else "N/A"
    except: pass
    return email, tech, social

@app.route('/', methods=['GET', 'POST'])
def home():
    resultados = []
    if request.method == 'POST':
        query = request.form.get('query')
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST_MAPS}
        params = {"query": query, "limit": "50", "region": "es", "language": "es"}
        
        try:
            resp = requests.get(f"https://{HOST_MAPS}/search", headers=headers, params=params).json()
            data = resp.get('data', [])
            
            conn = sqlite3.connect(DB_NAME)
            for biz in data:
                mail, tech, soc = analizar_web_pro(biz.get('website'))
                lead = {
                    "empresa": biz.get('name'),
                    "direccion": biz.get('full_address', 'N/A'),
                    "web": biz.get('website', 'N/A'),
                    "tel": biz.get('phone_number', 'N/A'),
                    "rating": biz.get('rating', 0),
                    "reviews": biz.get('review_count', 0),
                    "email": mail,
                    "tech": tech,
                    "social": soc
                }
                resultados.append(lead)
                conn.execute("INSERT INTO leads (fecha, empresa, direccion, web, email, tel, rating, reviews, tech, social) VALUES (?,?,?,?,?,?,?,?,?,?)",
                             (datetime.now().strftime("%Y-%m-%d"), lead['empresa'], lead['direccion'], lead['web'], lead['email'], lead['tel'], lead['rating'], lead['reviews'], lead['tech'], lead['social']))
            conn.commit()
            conn.close()
            # Ordenar por Rating (Estrellas)
            resultados = sorted(resultados, key=lambda x: x['rating'], reverse=True)
        except: pass
            
    return render_template('index.html', resultados=resultados)

@app.route('/descargar')
def descargar():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT empresa, direccion, web, email, tel, rating, reviews, tech, social FROM leads ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Empresa", "Dirección", "Web", "Email", "Teléfono", "Rating", "Reseñas", "Tecnología", "Social"])
    writer.writerows(datos)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')), mimetype="text/csv", as_attachment=True, download_name="leads_b2b.csv")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
