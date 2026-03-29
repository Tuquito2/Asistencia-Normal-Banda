import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Asistencia", page_icon="🎓", layout="centered")

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
    pdf.cell(200, 10, txt="Listado de Asistencia", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, "Apellido", 1)
    pdf.cell(60, 10, "Nombre", 1)
    pdf.cell(70, 10, "Fecha y Hora", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 12)
    for row in datos:
        pdf.cell(60, 10, str(row[0]), 1)
        pdf.cell(60, 10, str(row[1]), 1)
        pdf.cell(70, 10, str(row[2]), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE USUARIO ---

# Inicializar estado de sesión para el modo
if 'modo' not in st.session_state:
    st.session_state.modo = "Alumno"

# Botón superior derecho para cambiar de modo
col_t, col_btn = st.columns([0.8, 0.2])
with col_btn:
    if st.session_state.modo == "Alumno":
        if st.button("Panel Profesor 🔒"):
            st.session_state.modo = "Login"
            st.rerun()
    else:
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
    st.write("Listado actual de alumnos presentes (Orden Alfabético):")
    
    lista_alumnos = obtener_alumnos()
    
    if lista_alumnos:
        df = pd.DataFrame(lista_alumnos, columns=["Apellido", "Nombre", "Fecha/Hora"])
        st.table(df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Botón para descargar PDF
            pdf_data = generar_pdf(lista_alumnos)
            st.download_button(
                label="📥 Descargar Listado (PDF)",
                data=pdf_data,
                file_name=f"asistencia_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            
        with col2:
            # Botón para borrar todo con confirmación simple
            if st.button("🗑️ Eliminar todos los registros"):
                borrar_todos()
                st.success("Registros eliminados correctamente.")
                st.rerun()
    else:
        st.write("No hay alumnos registrados todavía.")