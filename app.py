import streamlit as st
import requests
import re
import pandas as pd
import io

# --- CONFIGURACIÓN DE PRIVACIDAD ---
st.set_page_config(page_title="B2B Lead Extractor", layout="wide")

# CSS para ocultar menús, pie de página de Streamlit y proteger la interfaz
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# Recuperar API Key de forma segura
try:
    API_KEY = st.secrets["RAPIDAPI_KEY"]
except:
    st.error("Error: No se ha configurado la API Key en los Secrets de Streamlit.")
    st.stop()

HOST_MAPS = "local-business-data.p.rapidapi.com"

def extraer_datos_web(web):
    email, tech = "No encontrado", "N/A"
    if not web or web == 'N/A': return email, tech
    try:
        # User-Agent de móvil para evitar bloqueos y mantener bajo consumo
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10)'}
        res = requests.get(web, headers=headers, timeout=5)
        mails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        email = mails[0].lower() if mails else "No visible"
        tech = "WordPress" if "wp-content" in res.text else "Shopify" if "shopify" in res.text else "N/A"
    except: pass
    return email, tech

# --- INTERFAZ ---
st.title("🚀 Inteligencia Comercial B2B")
st.markdown("Analizador de mercado de alto rendimiento.")

query = st.text_input("Actividad o Sector a analizar:", placeholder="Ej: Talleres en Vizcaya")

if st.button("Lanzar Análisis"):
    if query:
        with st.spinner('Analizando datos de mercado...'):
            headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST_MAPS}
            params = {"query": query, "limit": "50", "region": "es", "language": "es"}
            
            try:
                response = requests.get(f"https://{HOST_MAPS}/search", headers=headers, params=params).json()
                data = response.get('data', [])
                
                # Gestión de término no encontrado
                if not data:
                    st.warning(f"⚠️ El término '{query}' no ha devuelto resultados. Prueba con otra actividad o zona.")
                else:
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
                            "Dirección": biz.get('full_address', 'N/A'),
                            "Tecnología": tech
                        })
                    
                    # Ordenar por relevancia comercial [cite: 2026-02-12]
                    df = pd.DataFrame(lista_final).sort_values(by="Rating", ascending=False)
                    st.success(f"Análisis completado: {len(df)} prospectos cualificados.")
                    st.dataframe(df, use_container_width=True)
                    
                    # Exportación CSV profesional
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Exportar Informe de Prospección",
                        data=csv,
                        file_name=f"leads_{query.replace(' ', '_')}.csv",
                        mime='text/csv'
                    )
                
            except Exception as e:
                st.error("El servicio de datos no está respondiendo. Inténtalo de nuevo en unos minutos.")
    else:
        st.info("Introduce un término para iniciar la extracción.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888; font-size: 12px;'>Desarrollado por Jose Luis Asenjo</p>", unsafe_allow_html=True)
