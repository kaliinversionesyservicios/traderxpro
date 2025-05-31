import streamlit as st
from pages.visitante import app_visitante
from pages.autenticacion import login

#Funcion que permite simular la carga de paginas
def route(modo):
    if modo=="usuario":
        st.write("Dirigite a una pagina de autenticacion")
        login()
    elif modo=="visitante":
        app_visitante()
    else: 
        st.error("⚠️ Página no encontrada. Redirigiendo a la página de inicio...")
        st.session_state["inicio"] = False
        if st.button("Volver al inicio"):
            st.session_state.modo = None  # Resetear el modo
            st.rerun()   