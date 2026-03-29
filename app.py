import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Control de Asistencia", 
    page_icon="🎓", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ESCONDER ELEMENTOS DE DESARROLLADOR (Deploy, GitHub, Menú, Footer y Manage App) ---
# Se agregan selectores adicionales para forzar el ocultamiento de la barra de gestión
st.markdown("""
    <style>
    /* Ocultar Menú hamburguesa y Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Ocultar Header completo (donde están Deploy y GitHub) */
    header {visibility: hidden !important;}
    
    /* Ocultar botón de Deploy específico */
    .stDeployButton {display:none !important;}
    
    /* Ocultar barra de herramientas (Toolbar) donde aparece 'Manage app' */
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    
    /* Ocultar widgets de estado y decoración superior */
    [data-testid="stStatusWidget"] {visibility: hidden !important;}
    #stDecoration {display:none !important;}
    
    /* Eliminar espacio en blanco superior que deja el header oculto */
    .stAppViewBlockContainer {padding-top: 2rem !important;}
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('asistencia.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            fecha_hora TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# --- FUNCIONES DE AYUDA ---
def registrar_asistencia(nombre, apellido):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Guardamos en Capitalizado para mantener orden didáctico y uniforme
    cursor.execute('INSERT INTO alumnos (nombre, apellido, fecha_hora) VALUES (?, ?, ?)', 
                   (nombre.strip().capitalize(), apellido.strip().capitalize(), ahora))
    conn.commit()

def obtener_alumnos():
    # Obtenemos y ordenamos alfabéticamente por Apellido y luego Nombre
    cursor.execute('SELECT apellido, nombre, fecha_hora FROM alumnos ORDER BY apellido ASC, nombre ASC')
    return cursor.fetchall()

def borrar_todos():
    cursor.execute('DELETE FROM alumnos')
    conn.commit()

def generar_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Listado de Asistencia - Normal Banda", ln=True, align='C')
    pdf.ln(10)
    
    # Encabezados con numeración
    pdf.set_font("Arial", "B", 12)
    pdf.cell(15, 10, "N°", 1)
    pdf.cell(55, 10, "Apellido", 1)
    pdf.cell(55, 10, "Nombre", 1)
    pdf.cell(65, 10, "Fecha y Hora", 1)
    pdf.ln()
    
    # Filas de datos
    pdf.set_font("Arial", "", 12)
    for i, row in enumerate(datos, 1):
        pdf.cell(15, 10, str(i), 1)
        pdf.cell(55, 10, str(row[0]), 1)
        pdf.cell(55, 10, str(row[1]), 1)
        pdf.cell(65, 10, str(row[2]), 1)
        pdf.ln()
    
    # Resumen total solicitado al final del PDF
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Total de alumnos presentes: {len(datos)}", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE USUARIO ---

# Inicializar estado de sesión para el modo (Persistencia tras F5)
if 'modo' not in st.session_state:
    st.session_state.modo = "Alumno"

# Botón superior derecho para cambiar de modo
col_t, col_btn = st.columns([0.8, 0.2])
with col_btn:
    if st.session_state.modo in ["Alumno", "Login"]:
        if st.button("Panel Profesor 🔒"):
            st.session_state.modo = "Login"
            st.rerun()
    elif st.session_state.modo == "Profesor":
        if st.button("Volver Inicio 🏠"):
            st.session_state.modo = "Alumno"
            st.rerun()

# --- MODO LOGIN ---
if st.session_state.modo == "Login":
    st.subheader("Acceso Administrativo")
    password = st.text_input("Ingrese la contraseña:", type="password")
    if st.button("Entrar"):
        if password == "1234":
            st.session_state.modo = "Profesor"
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    if st.button("Cancelar"):
        st.session_state.modo = "Alumno"
        st.rerun()

# --- MODO ALUMNO ---
elif st.session_state.modo == "Alumno":
    st.title("🎓 Registro de Asistencia Normal Banda")
    st.info("Por favor, ingrese sus datos para registrar su presencia en clase.")
    
    with st.form("registro_form", clear_on_submit=True):
        apellido = st.text_input("Apellido")
        nombre = st.text_input("Nombre")
        submit = st.form_submit_button("Registrar Asistencia")
        
        if submit:
            if nombre and apellido:
                registrar_asistencia(nombre, apellido)
                st.success(f"¡Hecho! Asistencia registrada para {nombre} {apellido}.")
            else:
                st.warning("Por favor, complete ambos campos.")

# --- MODO PROFESOR ---
elif st.session_state.modo == "Profesor":
    st.title("👨‍🏫 Panel del Profesor")
    
    lista_alumnos = obtener_alumnos()
    total_presentes = len(lista_alumnos)
    
    # Contador de alumnos presentes en el panel
    st.metric(label="Alumnos Registrados", value=total_presentes)
    
    st.write("Listado actual de alumnos presentes (Orden Alfabético):")
    
    if lista_alumnos:
        # Tabla web numerada para el profesor
        df = pd.DataFrame(lista_alumnos, columns=["Apellido", "Nombre", "Fecha/Hora"])
        df.index = range(1, len(df) + 1) # Numeración empezando en 1
        st.table(df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Botón para descargar PDF con numeración y resumen
            pdf_data = generar_pdf(lista_alumnos)
            st.download_button(
                label="📥 Descargar Listado (PDF)",
                data=pdf_data,
                file_name=f"asistencia_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            
        with col2:
            # Botón para borrar todo
            if st.button("🗑️ Eliminar todos los registros"):
                borrar_todos()
                st.success("Registros eliminados correctamente.")
                st.rerun()
    else:
        st.write("No hay alumnos registrados todavía.")