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
# Se han añadido selectores de alto nivel para asegurar que desaparezcan en la versión web
st.markdown("""
    <style>
    /* 1. Ocultar Menú hamburguesa y Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. Ocultar Header completo (donde están Deploy y GitHub) */
    header {visibility: hidden !important;}
    
    /* 3. Ocultar botones de Deploy y herramientas de gestión */
    .stDeployButton {display:none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;}
    
    /* 4. Ocultar específicamente el botón 'Manage app' y el menú de la nube */
    .stAppDeployButton {display:none !important;}
    #stDecoration {display:none !important;}
    
    /* 5. Bloqueador agresivo para elementos flotantes de Streamlit Cloud */
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* Botón flotante de 'Manage App' en versiones recientes de Cloud */
    div[data-testid="stToolbar"] {display: none !important;}
    button[title="View source on GitHub"] {display: none !important;}
    
    /* 6. Ajustar el espacio superior para compensar el header oculto */
    .stApp {
        margin-top: -60px;
    }
    .stAppViewBlockContainer {
        padding-top: 0rem !important;
    }
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
def verificar_duplicado(nombre, apellido):
    """Verifica si el alumno ya existe en la base de datos."""
    cursor.execute('SELECT id FROM alumnos WHERE nombre = ? AND apellido = ?', (nombre, apellido))
    return cursor.fetchone() is not None

def registrar_asistencia(nombre, apellido):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('INSERT INTO alumnos (nombre, apellido, fecha_hora) VALUES (?, ?, ?)', 
                   (nombre.strip().capitalize(), apellido.strip().capitalize(), ahora))
    conn.commit()

def obtener_alumnos_con_id():
    """Obtiene alumnos incluyendo el ID para poder borrar individualmente."""
    cursor.execute('SELECT id, apellido, nombre, fecha_hora FROM alumnos ORDER BY apellido ASC, nombre ASC')
    return cursor.fetchall()

def borrar_alumno(id_alumno):
    cursor.execute('DELETE FROM alumnos WHERE id = ?', (id_alumno,))
    conn.commit()

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
        pdf.cell(55, 10, str(row[1]), 1)
        pdf.cell(55, 10, str(row[2]), 1)
        pdf.cell(65, 10, str(row[3]), 1)
        pdf.ln()
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Total de alumnos presentes: {len(datos)}", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE USUARIO ---

if 'modo' not in st.session_state:
    st.session_state.modo = "Alumno"

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
        apellido_input = st.text_input("Apellido").strip().capitalize()
        nombre_input = st.text_input("Nombre").strip().capitalize()
        submit = st.form_submit_button("Registrar Asistencia")
        
        if submit:
            if nombre_input and apellido_input:
                if verificar_duplicado(nombre_input, apellido_input):
                    st.warning(f"⚠️ El alumno {nombre_input} {apellido_input} ya se encuentra registrado hoy.")
                else:
                    registrar_asistencia(nombre_input, apellido_input)
                    st.success(f"¡Hecho! Asistencia registrada para {nombre_input} {apellido_input}.")
            else:
                st.warning("Por favor, complete ambos campos.")

# --- MODO PROFESOR ---
elif st.session_state.modo == "Profesor":
    st.title("👨‍🏫 Panel del Profesor")
    
    lista_alumnos = obtener_alumnos_con_id()
    total_presentes = len(lista_alumnos)
    
    st.metric(label="Alumnos Registrados", value=total_presentes)
    
    st.write("Listado actual (puedes borrar registros individuales):")
    
    if lista_alumnos:
        h1, h2, h3, h4, h5 = st.columns([0.5, 2, 2, 2, 1])
        h1.write("**N°**")
        h2.write("**Apellido**")
        h3.write("**Nombre**")
        h4.write("**Fecha/Hora**")
        h5.write("**Acción**")
        
        for i, row in enumerate(lista_alumnos, 1):
            id_db, ape, nom, fec = row
            c1, c2, c3, c4, c5 = st.columns([0.5, 2, 2, 2, 1])
            c1.write(str(i))
            c2.write(ape)
            c3.write(nom)
            c4.write(fec)
            if c5.button("🗑️", key=f"del_{id_db}"):
                borrar_alumno(id_db)
                st.rerun()
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            pdf_data = generar_pdf(lista_alumnos)
            st.download_button(
                label="📥 Descargar Listado (PDF)",
                data=pdf_data,
                file_name=f"asistencia_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            
        with col2:
            if st.button("🔥 Vaciar Lista Completa"):
                borrar_todos()
                st.success("Registros eliminados correctamente.")
                st.rerun()
    else:
        st.write("No hay alumnos registrados todavía.")