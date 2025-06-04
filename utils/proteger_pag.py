def proteger_pagina(modos_permitidos=["usuario", "visitante"]):
    import streamlit as st
    modo_actual = st.session_state.get("modo")

    if modo_actual not in modos_permitidos:
        st.warning("🔐 Acceso denegado. Por favor, inicia sesión.")
        st.stop()
