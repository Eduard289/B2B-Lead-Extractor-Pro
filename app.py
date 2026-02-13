import streamlit as st
import requests
import re
import pandas as pd
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="B2B Lead Extractor Pro", layout="wide")

# CSS para ocultar elementos de Streamlit y dar aspecto de App profesional
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- VALIDACIÓN DE CREDENCIALES ---
try:
    # Asegúrate de que en Streamlit Cloud el nombre sea exactamente RAPIDAPI_KEY
    API_KEY = st.secrets["RAPIDAPI_KEY"]
except Exception:
    st.error("🔑 Error: No se ha encontrado 'RAPIDAPI_KEY' en los Secrets de Streamlit.")
    st.stop()

HOST_MAPS = "local-business-data.p.rapidapi.com"

def extraer_datos_web(web):
    email, tech = "No encontrado", "N/A"
    if not web or web == 'N/A': return email, tech
    try:
        # User-Agent para evitar bloqueos por IP [cite: 2026-02-09]
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(web, headers=headers, timeout=5)
        # Búsqueda de emails con regex mejorada
        mails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        email = mails[0].lower() if mails else "No visible"
        # Detección de tecnología básica
        tech = "WordPress" if "wp-content" in res.text else "Shopify" if "shopify" in res.text else "N/A"
    except:
        pass
    return email, tech

# --- INTERFAZ DE USUARIO ---
st.title("🚀 Inteligencia Comercial B2B")
st.subheader("Extractor de Leads mediante Google Maps")

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Actividad y Zona:", placeholder="Ej: Talleres en Vizcaya")
with col2:
    limit = st.selectbox("Cantidad de leads", ["20", "50"], index=0)

if st.button("Lanzar Análisis Pro"):
    if not query:
        st.info("Por favor, introduce un término de búsqueda.")
    else:
        with st.spinner('Conectando con la API y analizando resultados...'):
            headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST_MAPS}
            params = {"query": query, "limit": limit, "region": "es", "language": "es"}
            
            try:
                response = requests.get(f"https://{HOST_MAPS}/search", headers=headers, params=params)
                
                # --- SISTEMA DE DIAGNÓSTICO ---
                # Verificamos créditos restantes en los headers de RapidAPI
                quota_remaining = response.headers.get('x-ratelimit-requests-remaining', 'N/A')
                
                if response.status_code == 200:
                    json_data = response.json()
                    data = json_data.get('data', [])
                    
                    if not data:
                        st.warning(f"⚠️ No hay datos para '{query}'. Créditos restantes: {quota_remaining}")
                    else:
                        lista_final = []
                        # Barra de progreso para el scraping de emails
                        progreso = st.progress(0)
                        for i, biz in enumerate(data):
                            mail, tech = extraer_datos_web(biz.get('website'))
                            lista_final.append({
                                "Empresa": biz.get('name'),
                                "Email": mail,
                                "Teléfono": biz.get('phone_number', 'N/A'),
                                "Rating": biz.get('rating', 0),
                                "Reviews": biz.get('review_count', 0),
                                "Web": biz.get('website', 'N/A'),
                                "Dirección": biz.get('full_address', 'N/A'),
                                "Tecnología": tech
                            })
                            progreso.progress((i + 1) / len(data))
                        
                        df = pd.DataFrame(lista_final).sort_values(by="Rating", ascending=False)
                        
                        st.success(f"✅ {len(df)} prospectos encontrados. (Créditos API restantes: {quota_remaining})")
                        
                        # Mostrar tabla con ancho optimizado
                        st.dataframe(df, width=None) 
                        
                        # Exportación profesional
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 Descargar Informe CSV para Excel",
                            data=csv,
                            file_name=f"leads_{query.replace(' ', '_')}.csv",
                            mime='text/csv'
                        )
                elif response.status_code == 429:
                    st.error("🚫 Has agotado tu cuota de RapidAPI para hoy. Espera hasta mañana o mejora tu plan.")
                elif response.status_code == 403:
                    st.error("🔑 Error 403: API Key no válida o no estás suscrito al plan (incluso si es el gratuito).")
                else:
                    st.error(f"Ocurrió un error inesperado (Código {response.status_code}).")
            
            except Exception as e:
                st.error(f"Fallo en la conexión: {str(e)}")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888; font-size: 12px;'>Desarrollado por Jose Luis Asenjo | B2B Lead Extractor Pro</p>", unsafe_allow_html=True)
