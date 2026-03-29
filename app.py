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

# --- ESCONDER ELEMENTOS DE DESARROLLADOR (ESTRATEGIA DEFINITIVA) ---
# He añadido selectores específicos para las clases dinámicas de Streamlit Cloud
st.markdown("""
    <style>
    /* 1. Ocultar el Header completo (Contiene Share, Deploy, GitHub y Menú) */
    header[data-testid="stHeader"] {
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
    }
    
    /* 2. Ocultar específicamente la barra de herramientas y el botón de 'Manage app' */
    [data-testid="stToolbar"] {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* 3. Ocultar el widget de estado (icono del barquito / círculo de carga) */
    [data-testid="stStatusWidget"] {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* 4. Ocultar el botón flotante de 'Manage App' que aparece abajo a la derecha en la nube */
    .stAppDeployButton, .st-emotion-cache-10trblm, .st-emotion-cache-12m02zu {
        display: none !important;
    }

    /* 5. Ocultar decoraciones de fondo e iconos de edición */
    #stDecoration {
        display: none !important;
    }
    
    /* 6. Eliminar el pie de página (Made with Streamlit) */
    footer {
        visibility: hidden !important;
    }

    /* 7. Ajuste de margen para eliminar el espacio muerto superior y lateral */
    .stApp {
        margin-top: -60px !important;
    }
    
    .stAppViewBlockContainer {
        padding-top: 0rem !important;
    }
    
    /* Ocultar cualquier elemento que contenga el texto 'Manage app' o iconos de gestión */
    div:has(> button:contains("Manage app")) {
        display: none !important;
    }
    
    /* Estilo para las tarjetas de alumnos en móviles */
    .alumno-card {
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 10px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
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
    cursor.execute('SELECT id FROM alumnos WHERE nombre = ? AND apellido = ?', (nombre, apellido))
    return cursor.fetchone() is not None

def registrar_asistencia(nombre, apellido):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('INSERT INTO alumnos (nombre, apellido, fecha_hora) VALUES (?, ?, ?)', 
                   (nombre.strip().capitalize(), apellido.strip().capitalize(), ahora))
    conn.commit()

def obtener_alumnos_con_id():
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

# Layout superior
col_t, col_btn = st.columns([0.7, 0.3])
with col_btn:
    if st.session_state.modo in ["Alumno", "Login"]:
        if st.button("Panel Profesor 🔒"):
            st.session_state.modo = "Login"
            st.rerun()
    elif st.session_state.modo == "Profesor":
        if st.button("Volver Inicio 🏠"):
            st.session_state.modo = "Alumno"
            st.rerun()

# Lógica de navegación
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
                    st.warning(f"⚠️ El alumno {nombre_input} {apellido_input} ya está registrado.")
                else:
                    registrar_asistencia(nombre_input, apellido_input)
                    st.success(f"¡Hecho! Asistencia registrada para {nombre_input} {apellido_input}.")
            else:
                st.warning("Por favor, complete ambos campos.")

elif st.session_state.modo == "Profesor":
    st.title("👨‍🏫 Panel del Profesor")
    lista_alumnos = obtener_alumnos_con_id()
    total_presentes = len(lista_alumnos)
    st.metric(label="Alumnos Registrados", value=total_presentes)

    if lista_alumnos:
        with st.expander("Ver Listado de Alumnos", expanded=True):
            for i, row in enumerate(lista_alumnos, 1):
                id_db, ape, nom, fec = row
                with st.container():
                    col_info, col_del = st.columns([0.85, 0.15])
                    with col_info:
                        st.markdown(f"**{i}. {ape}, {nom}**")
                        st.caption(f"📅 {fec}")
                    with col_del:
                        if st.button("🗑️", key=f"del_{id_db}"):
                            borrar_alumno(id_db)
                            st.rerun()
                    st.markdown("---")
        
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
            if st.button("🔥 Vaciar Lista"):
                borrar_todos()
                st.rerun()
    else:
        st.write("No hay alumnos registrados todavía.")