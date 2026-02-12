import streamlit as st
import requests
import re
import pandas as pd
from urllib.parse import urlparse
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="B2B Lead Extractor Pro", page_icon="🚀")

# --- CREDENCIALES ---
API_KEY = "c4d338518fmsh31a457d13e649b8p146580jsn30ec67d26e2b"
HOST_MAPS = "local-business-data.p.rapidapi.com"

# --- LÓGICA DE EXTRACCIÓN ---
def analizar_web_detallado(web):
    email, tech, social = "No encontrado", "N/A", "N/A"
    if not web or web == 'N/A': return email, tech, social
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(web, headers=headers, timeout=5)
        html = res.text
        # Emails
        mails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
        email = mails[0].lower() if mails else "No visible"
        # Tech & RRSS
        tech = "WordPress" if "wp-content" in html else "Shopify" if "shopify" in html else "N/A"
        redes = [r for r in ["LinkedIn", "Instagram", "Facebook"] if r.lower() in html.lower()]
        social = ", ".join(redes) if redes else "N/A"
    except: pass
    return email, tech, social

# --- INTERFAZ STREAMLIT ---
st.title("🔎 B2B Master Lead Extractor")
st.markdown("### Automatización de prospección inteligente")

query = st.text_input("¿Qué actividad y zona quieres buscar?", placeholder="Ej: Talleres en Vizcaya")
num_leads = st.slider("Número de leads a extraer", 10, 50, 20)

if st.button("Lanzar Prospección"):
    with st.spinner('Analizando webs y redes sociales...'):
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST_MAPS}
        params = {"query": query, "limit": str(num_leads), "region": "es", "language": "es"}
        
        try:
            resp = requests.get(f"https://{HOST_MAPS}/search", headers=headers, params=params).json()
            data = resp.get('data', [])
            
            resultados = []
            for biz in data:
                mail, tech, soc = analizar_web_detallado(biz.get('website'))
                resultados.append({
                    "Empresa": biz.get('name'),
                    "Rating": biz.get('rating', 0),
                    "Reseñas": biz.get('review_count', 0),
                    "Email": mail,
                    "Teléfono": biz.get('phone_number', 'N/A'),
                    "Web": biz.get('website', 'N/A'),
                    "Dirección": biz.get('full_address', 'N/A'),
                    "Tecnología": tech,
                    "Social": soc
                })

            # Convertir a DataFrame y Ordenar
            df = pd.DataFrame(resultados).sort_values(by="Rating", ascending=False)
            
            # Mostrar Tabla Interactiva
            st.success(f"¡Éxito! Encontrados {len(df)} leads cualificados.")
            st.dataframe(df)

            # Botón de Descarga
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Descargar Base de Datos (CSV)",
                data=csv,
                file_name=f"leads_{query.replace(' ', '_')}.csv",
                mime='text/csv',
            )
        except Exception as e:
            st.error(f"Error en la conexión: {e}")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Desarrollado por Jose Luis Asenjo</p>", unsafe_allow_html=True)
