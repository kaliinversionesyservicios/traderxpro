import streamlit as st
def proteger_pagina():
    print("HITO 03: ",st.session_state.get("autenticado"))
    if not st.session_state.get("autenticado", False):
        st.warning("🔐 Acceso denegado. Por favor, inicia sesión.")
        st.stop()