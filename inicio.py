import streamlit as st
from utils.custom_style import load_css

# Configuración de la página
st.set_page_config(page_title="TraderXPRO", layout="wide")
load_css("styles/style.css")
st.markdown("<div class='header'><div class='header-img'></div><div>-</div></div>",unsafe_allow_html=True)

def mostrar_inicio():
    st.markdown("<div class='title_header'><h2>Trading</h2><h3>SCANX</h3></div>", unsafe_allow_html=True)
    st.markdown("<div class='p_descripcion'>Escaneo de estrategias utilizando Inteligencia Artificial.</div>", unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])

    ## UN SOLO BOTON
    with col_center:
        empty_left, main_col, empty_right = st.columns([1, 2, 1])
    
    with main_col:
        if st.button("🔑 Iniciar Sesión"):
            st.session_state.modo = "usuario"
            st.rerun()
   
    # with col_center:
    #     button_col1, button_col2 = st.columns(2)
    #     with button_col1:
    #         if st.button("👤 Iniciar como Visitante"):
    #             st.session_state.modo = "visitante"
    #             st.rerun()
    #     with button_col2:
    #         if st.button("🔑 Iniciar Sesión"):
    #             st.session_state.modo = "usuario"
    #             st.rerun()
def main():
    if "modo" not in st.session_state:
        mostrar_inicio()
    elif st.session_state.modo == "visitante":
        from pages.ruptura_bajista import app_ruptura_bajista
        print(st.session_state.modo)
        app_ruptura_bajista()
        st.stop()
    elif st.session_state.modo == "usuario":
        from pages.autenticacion import login
        login()
        st.stop()

if __name__ == "__main__":
    main()
