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

# --- OCULTAR MENÚS DE STREAMLIT (PARA ALUMNOS) ---
# Este bloque elimina el menú de la derecha, el botón de deploy y el footer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    #stDecoration {display:none;}
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
    cursor.execute('INSERT INTO alumnos (nombre, apellido, fecha_hora) VALUES (?, ?, ?)', 
                   (nombre.strip().upper(), apellido.strip().upper(), ahora))
    conn.commit()

def obtener_alumnos():
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
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(15, 10, "N°", 1)
    pdf.cell(55, 10, "Apellido", 1)
    pdf.cell(55, 10, "Nombre", 1)
    pdf.cell(65, 10, "Fecha y Hora", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 12)
    for i, row in enumerate(datos, 1):
        pdf.cell(15, 10, str(i), 1)
        pdf.cell(55, 10, str(row[0]), 1)
        pdf.cell(55, 10, str(row[1]), 1)
        pdf.cell(65, 10, str(row[2]), 1)
        pdf.ln()
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Total de alumnos presentes: {len(datos)}", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- GESTIÓN DE ESTADO DE SESIÓN (Persistencia F5) ---
if 'modo' not in st.session_state:
    st.session_state.modo = "Alumno"

# Botón de navegación discreto
col_t, col_btn = st.columns([0.8, 0.2])
with col_btn:
    if st.session_state.modo in ["Alumno", "Login"]:
        if st.button("🔒"):
            st.session_state.modo = "Login"
            st.rerun()
    elif st.session_state.modo == "Profesor":
        if st.button("🏠"):
            st.session_state.modo = "Alumno"
            st.rerun()

# --- LÓGICA DE PANTALLAS ---

if st.session_state.modo == "Login":
    st.subheader("Acceso Administrativo")
    password = st.text_input("Contraseña:", type="password")
    if st.button("Entrar"):
        if password == "1234":
            st.session_state.modo = "Profesor"
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    if st.button("Cancelar"):
        st.session_state.modo = "Alumno"
        st.rerun()

elif st.session_state.modo == "Alumno":
    st.title("🎓 Registro de Asistencia")
    st.write("Ingresa tus datos para registrar tu presencia hoy.")
    
    with st.form("registro_form", clear_on_submit=True):
        apellido = st.text_input("Apellido").upper()
        nombre = st.text_input("Nombre").upper()
        submit = st.form_submit_button("Registrar Asistencia")
        
        if submit:
            if nombre and apellido:
                registrar_asistencia(nombre, apellido)
                st.success("✅ Asistencia registrada correctamente.")
            else:
                st.warning("⚠️ Completa ambos campos.")

elif st.session_state.modo == "Profesor":
    st.title("👨‍🏫 Panel del Profesor")
    
    lista_alumnos = obtener_alumnos()
    total_presentes = len(lista_alumnos)
    
    st.metric(label="Alumnos Registrados", value=total_presentes)
    
    if lista_alumnos:
        df = pd.DataFrame(lista_alumnos, columns=["Apellido", "Nombre", "Fecha/Hora"])
        df.index = range(1, len(df) + 1)
        st.table(df)
        
        col1, col2 = st.columns(2)
        with col1:
            pdf_data = generar_pdf(lista_alumnos)
            st.download_button(
                label="📥 Descargar PDF",
                data=pdf_data,
                file_name=f"asistencia_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        with col2:
            if st.button("🗑️ Vaciar Lista"):
                borrar_todos()
                st.rerun()
    else:
        st.write("No hay registros.")