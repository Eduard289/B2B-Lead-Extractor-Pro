
import streamlit as st
import requests
import re
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="B2B Lead Extractor Pro", layout="wide", page_icon="🚀")

# CSS para ocultar menús y profesionalizar la interfaz
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    .reportview-container { background: #f0f2f6; }
    </style>
""", unsafe_allow_html=True)

# --- VALIDACIÓN DE CREDENCIALES ---
try:
    API_KEY = st.secrets["RAPIDAPI_KEY"]
except Exception:
    st.error("🔑 Error: Configuración de API pendiente en Secrets.")
    st.stop()

HOST_MAPS = "local-business-data.p.rapidapi.com"

# --- FUNCIONES DE APOYO ---
def obtener_ip_cliente():
    try:
        # Usamos un servicio externo para captar la IP de quien visita
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "IP Privada/No detectada"

def extraer_datos_web(web):
    email, tech = "No encontrado", "N/A"
    if not web or web == 'N/A': return email, tech
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(web, headers=headers, timeout=5)
        # Búsqueda de emails corporativos [cite: 2026-02-12]
        mails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        email = mails[0].lower() if mails else "No visible"
        # Detección de tecnología [cite: 2026-02-12]
        tech = "WordPress" if "wp-content" in res.text else "Shopify" if "shopify" in res.text else "N/A"
    except:
        pass
    return email, tech

# --- SISTEMA DE IDENTIFICACIÓN TIPO TELEGRAM ---
if 'usuario_nombre' not in st.session_state:
    st.session_state['usuario_nombre'] = ""

if not st.session_state['usuario_nombre']:
    st.write("### 🖐️ Bienvenido al Laboratorio de Inteligencia Comercial")
    nombre_input = st.text_input("Para una experiencia personalizada, dinos tu nombre o alias:", placeholder="Ej: Eduardo")
    if st.button("Acceder a la herramienta"):
        if nombre_input:
            st.session_state['usuario_nombre'] = nombre_input
            st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
ip_actual = obtener_ip_cliente()
st.title("🚀 Inteligencia Comercial B2B")

# Mensaje de bienvenida personalizado
st.markdown(f"""
    <div style='background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3; margin-bottom: 20px;'>
        <strong>🤖 Sistema:</strong> ¡Hola, <b>{st.session_state['usuario_nombre']}</b>! 👋 <br>
        Has accedido desde la IP: <code>{ip_actual}</code>. Estás en un entorno de desarrollo para prospección avanzada.
    </div>
""", unsafe_allow_html=True)

# Bloque Informativo de Funcionalidades
with st.expander("ℹ️ Ver capacidades de esta herramienta y potencial B2B", expanded=False):
    st.markdown("""
    Esta plataforma automatiza la **prospección comercial** analizando bases de datos públicas en tiempo real.
    
    **Campos compilados:**
    * **Identidad**: Nombre comercial, Rating de mercado y volumen de reseñas de clientes.
    * **Localización**: Dirección física completa y teléfono de contacto.
    * **Huella Digital**: URL del sitio web oficial.
    * **Contacto Directo**: Extracción de correos electrónicos corporativos visibles para campañas de ventas.
    * **Auditoría Técnica**: Identificación de CMS (WordPress/Shopify) para servicios IT o agencias.
    
    **Desarrollo B2B**: Ideal para generar listas de ventas cualificadas, estudios de mercado locales y captación de clientes de alta reputación.
    """)

st.info("💡 **Aviso de disponibilidad**: Debido al alto tráfico, si la consulta no devuelve resultados, el servicio podría estar fuera de rango momentáneamente por exceso de peticiones. Estará operativo de nuevo en unos minutos.")

# --- FORMULARIO DE BÚSQUEDA ---
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Actividad y Zona Geográfica:", placeholder="Ej: Talleres en Vizcaya")
with col2:
    limit = st.selectbox("Volumen de datos", ["20", "50"], index=0)

if st.button("Ejecutar Análisis de Mercado"):
    if not query:
        st.warning("Introduce un término para buscar.")
    else:
        with st.spinner(f'Procesando datos para {st.session_state["usuario_nombre"]}...'):
            headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST_MAPS}
            params = {"query": query, "limit": limit, "region": "es", "language": "es"}
            
            try:
                response = requests.get(f"https://{HOST_MAPS}/search", headers=headers, params=params)
                
                if response.status_code == 200:
                    json_data = response.json()
                    data = json_data.get('data', [])
                    
                    if not data:
                        st.warning(f"⚠️ Hola {st.session_state['usuario_nombre']}, el servicio está fuera de rango por exceso de peticiones en este momento. Inténtalo de nuevo en unos minutos.")
                    else:
                        lista_final = []
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
                        st.success(f"✅ Análisis finalizado. Se han cualificado {len(df)} prospectos.")
                        st.dataframe(df, use_container_width=True) 
                        
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 Descargar Informe de Prospección (CSV)",
                            data=csv,
                            file_name=f"leads_{query.replace(' ', '_')}.csv",
                            mime='text/csv'
                        )
                elif response.status_code in [429, 403]:
                    st.warning(f"⚠️ {st.session_state['usuario_nombre']}, hemos superado el límite de consultas permitidas momentáneamente. Por favor, espera unos minutos.")
                else:
                    st.error("Error en el servidor de datos. Reintenta en breve.")
            
            except Exception as e:
                st.error("Servicio no disponible temporalmente.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #888; font-size: 13px;'>
    <p>Desarrollado por <strong>Jose Luis Asenjo</strong></p>
    <p>📧 Contacto: tu-correo@ejemplo.com</p>
    <p style='font-size: 10px;'>Sesión activa para: {st.session_state['usuario_nombre']} | IP: {ip_actual}</p>
</div>
""", unsafe_allow_html=True)
