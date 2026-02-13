import streamlit as st
import requests
import re
import pandas as pd
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="B2B Lead Extractor Pro", layout="wide", page_icon="🚀")

# CSS para profesionalizar la interfaz y ocultar elementos internos
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (CONTADORES Y SESIÓN) ---
if 'contador_visitas' not in st.session_state:
    st.session_state['contador_visitas'] = random.randint(150, 210)  # Valor inicial simulado

if 'calificacion' not in st.session_state:
    st.session_state['calificacion'] = None

# --- VALIDACIÓN DE CREDENCIALES ---
try:
    API_KEY = st.secrets["RAPIDAPI_KEY"]
except Exception:
    st.error("🔑 Error: Configuración de API pendiente en los Secrets de Streamlit.")
    st.stop()

HOST_MAPS = "local-business-data.p.rapidapi.com"

# --- FUNCIONES DE APOYO ---
def obtener_ip_cliente():
    try:
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
        # Detección de tecnología CMS [cite: 2026-02-12]
        tech = "WordPress" if "wp-content" in res.text else "Shopify" if "shopify" in res.text else "N/A"
    except:
        pass
    return email, tech

# --- PANTALLA DE IDENTIFICACIÓN ---
if 'usuario_nombre' not in st.session_state:
    st.session_state['usuario_nombre'] = ""

if not st.session_state['usuario_nombre']:
    st.write("### 🖐️ Bienvenido al Laboratorio de Inteligencia Comercial")
    nombre_input = st.text_input("Introduce tu nombre o alias (pulsa Enter para entrar como anónimo):", placeholder="Ej: Eduardo")
    
    if st.button("Acceder a la herramienta"):
        if not nombre_input.strip():
            # Asignación de alias aleatorio si se pulsa enter o está vacío [cite: 2026-02-12]
            nombres_azar = ["Analista", "Lead_Hunter", "Estratega_B2B", "Explorador", "Growth_User"]
            st.session_state['usuario_nombre'] = f"{random.choice(nombres_azar)}_{random.randint(10, 99)}"
        else:
            st.session_state['usuario_nombre'] = nombre_input
        st.session_state['contador_visitas'] += 1
        st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
ip_actual = obtener_ip_cliente()
st.title("🚀 Inteligencia Comercial B2B")

# Cabecera personalizada
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.markdown(f"""
        <div style='background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3;'>
            <strong>🤖 Sistema:</strong> ¡Hola, <b>{st.session_state['usuario_nombre']}</b>! 👋 <br>
            Conectado desde: <code>{ip_actual}</code>. Entorno de prospección cualificada activo.
        </div>
    """, unsafe_allow_html=True)
with col_head2:
    st.metric("Analistas hoy", st.session_state['contador_visitas'])

# Bloque Informativo
with st.expander("ℹ️ Capacidades de la herramienta y potencial B2B", expanded=False):
    st.markdown("""
    Esta plataforma automatiza la **prospección comercial** mediante el análisis de datos públicos en tiempo real.
    
    **Campos compilados:** Identidad comercial, Rating de mercado, Dirección, Teléfono, URL Web, Email corporativo y Tecnología CMS (WordPress/Shopify).
    
    **Desarrollo B2B**: Ideal para generar listas de ventas cualificadas y realizar captación estratégica basada en reputación online.
    """)

# Aviso de Disponibilidad y Contacto
st.info(f"💡 Debido al alto tráfico, si la consulta no devuelve resultados, el servicio podría estar fuera de rango momentáneamente por exceso de peticiones. Estará operativo de nuevo en unos minutos. Para cualquier consulta o proyecto personal, puedes ponerte en contacto con el desarrollador por mail: **asenjo.jose@hotmail.com**")

# --- ÁREA DE BÚSQUEDA ---
col_bus1, col_bus2 = st.columns([3, 1])
with col_bus1:
    query = st.text_input("Define actividad y zona geográfica:", placeholder="Ej: Talleres en Vizcaya")
with col_bus2:
    limit = st.selectbox("Volumen de datos", ["20", "50"], index=0)

if st.button("Ejecutar Análisis Pro"):
    if not query:
        st.warning("Por favor, introduce un término de búsqueda.")
    else:
        with st.spinner(f'Procesando base de datos para {st.session_state["usuario_nombre"]}...'):
            headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST_MAPS}
            params = {"query": query, "limit": limit, "region": "es", "language": "es"}
            
            try:
                response = requests.get(f"https://{HOST_MAPS}/search", headers=headers, params=params)
                
                if response.status_code == 200:
                    json_data = response.json()
                    data = json_data.get('data', [])
                    
                    if not data:
                        st.warning(f"⚠️ {st.session_state['usuario_nombre']}, el servicio está fuera de rango momentáneamente por exceso de peticiones. Reintenta en unos minutos. Soporte: asenjo.jose@hotmail.com")
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
                        st.success(f"✅ Análisis completado con éxito para {len(df)} prospectos.")
                        st.dataframe(df, use_container_width=True) 
                        
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 Exportar Informe (CSV)",
                            data=csv,
                            file_name=f"leads_{query.replace(' ', '_')}.csv",
                            mime='text/csv'
                        )
                elif response.status_code in [429, 403]:
                    st.warning(f"⚠️ {st.session_state['usuario_nombre']}, servicio fuera de rango temporalmente por exceso de consultas. Reintenta en unos minutos o contacta a asenjo.jose@hotmail.com")
                else:
                    st.error("Error técnico en el servidor de datos.")
            
            except Exception:
                st.error("Servicio no disponible momentáneamente.")

# --- SISTEMA DE CALIFICACIÓN ---
st.markdown("---")
st.write("### ⭐ Valora tu experiencia")
valoracion = st.feedback("stars")
if valoracion is not None:
    st.session_state['calificacion'] = valoracion + 1
    st.success(f"¡Gracias {st.session_state['usuario_nombre']}! Has valorado la herramienta con {st.session_state['calificacion']} estrellas.")

# --- PIE DE PÁGINA ---
st.markdown(f"""
<div style='text-align: center; color: #888; font-size: 13px; margin-top: 50px;'>
    <p>Desarrollado por <strong>Jose Luis Asenjo</strong></p>
    <p>📧 Contacto directo: <strong>asenjo.jose@hotmail.com</strong></p>
    <p style='font-size: 10px;'>ID Sesión: {st.session_state['usuario_nombre']} | IP: {ip_actual}</p>
</div>
""", unsafe_allow_html=True)
