import streamlit as st
import requests
import re
import pandas as pd
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="B2B Lead Extractor", layout="wide")

API_KEY = "c4d338518fmsh31a457d13e649b8p146580jsn30ec67d26e2b"
HOST_MAPS = "local-business-data.p.rapidapi.com"

def extraer_datos_web(web):
    email, tech = "No encontrado", "N/A"
    if not web or web == 'N/A': return email, tech
    try:
        res = requests.get(web, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        mails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        email = mails[0].lower() if mails else "No visible"
        tech = "WordPress" if "wp-content" in res.text else "Shopify" if "shopify" in html else "N/A"
    except: pass
    return email, tech

# --- INTERFAZ ---
st.title("🚀 B2B Lead Extractor Pro")
st.subheader("Desarrollado por Jose Luis Asenjo")

query = st.text_input("Buscar actividad (Ej: Fontaneros en Donostia)", "")

if st.button("Buscar Leads"):
    if query:
        with st.spinner('Buscando en Google Maps y analizando webs...'):
            headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST_MAPS}
            params = {"query": query, "limit": "20", "region": "es", "language": "es"}
            
            try:
                data = requests.get(f"https://{HOST_MAPS}/search", headers=headers, params=params).json().get('data', [])
                
                lista_final = []
                for biz in data:
                    mail, tech = extraer_datos_web(biz.get('website'))
                    lista_final.append({
                        "Empresa": biz.get('name'),
                        "Rating": biz.get('rating', 0),
                        "Reviews": biz.get('review_count', 0),
                        "Email": mail,
                        "Teléfono": biz.get('phone_number', 'N/A'),
                        "Web": biz.get('website', 'N/A'),
                        "Tecnología": tech
                    })
                
                df = pd.DataFrame(lista_final).sort_values(by="Rating", ascending=False)
                st.dataframe(df, use_container_width=True)
                
                # Descarga CSV
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Descargar Excel (CSV)", data=csv, file_name="leads_b2b.csv", mime='text/csv')
                
            except Exception as e:
                st.error(f"Error técnico: {e}")
    else:
        st.warning("Por favor, introduce un término de búsqueda.")
