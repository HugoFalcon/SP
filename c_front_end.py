# lanzar con streamlit run c_front_end.py en el terminal

import b_backend
import streamlit as st

st.title("BOT de preguntas a la tabla de socios")
st.write("Te sugiero iniciar prguntandome ¿CUALES SON LOS NOMBRES DE LAS COLUMNAS DE LA TABLA SOCIOS?. Otros ejemplos interesantes de consultas utiles son: a) MUESTRAME LOS 5 NUMEROS DE SOCIOS CON MAYOR SALDO EN DPFs, b) ¿CUÁNTOS SOCIOS TIENEN TARJETA DE CREDITO EN LA REGION ORIENTE?, c) DAME LA SUMA DE SALDO DE AHORRO DE SOCIOS QUE ESTAN EN CARTERA VENCIDA, d) AGRUPAME LAS SUMAS DE RESPONSABILIDAD TOTAL DE LOS CREDITOS ACTIVOS POR REGIONES, e)¿QUIEN ES EL SOCIO QUE TIENE EL MAYOR BC SCORE?. Si quieres ver los campos de un socio en particular solicitalo así DAME EL REGISTRO DEL SOCIO ###")

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
