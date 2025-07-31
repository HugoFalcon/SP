# lanzar con streamlit run c_front_end.py en el terminal

import b_backend
import streamlit as st

st.title("BOT de preguntas a la base de datos")
st.write("Te sugiero iniciar prguntandome MUESTRAME LOS CAMPOS DISPONIBLES DE LA TABLA DE SOCIOS ACTIVOS para que veas los campos disponibles y puedas hacer las consultas con los filtros que ocupes.")

# Inicializar el estado de la sesión
if 'mensajes' not in st.session_state:
    st.session_state.mensajes = []

# Contenedor para el historial de chat
chat_container = st.container()

# Mostrar historial de mensajes
with chat_container:
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

# Input del usuario
if prompt := st.chat_input("¿En qué te puedo ayudar?"):
    # Agregar mensaje del usuario al historial
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.write(prompt)
    
    # Obtener respuesta del backend
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta = b_backend.consulta(prompt)
        st.write(respuesta)
    
    # Agregar respuesta al historial
    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})

# Botón para limpiar conversación
if st.button("Nueva conversación"):
    st.session_state.mensajes = []
    st.rerun()
