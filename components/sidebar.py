import streamlit as st

def generarSidebar():
    st.markdown("""
                <style>
                    .stSidebar{
                        width:400px;
                    }
                    .stSidebar  [data-testid="stSidebarHeader"]{
                        background-image: url("https://raw.githubusercontent.com/kaliinversionesyservicios/TraderEstrategias/refs/heads/main/tradingscanx.png"); /* Ajusta URL */
                        background-repeat: no-repeat;
                        background-position: center;
                        background-size: contain;
                        height: 75px; /* Puedes ajustar esta altura según la imagen */
                        margin: 10px 0px
                    }
                    .stSidebar > [data-testid="stSidebarContent"]{
                        width: 100%;
                        background: 
                        radial-gradient(circle at 30% 20%, rgba(29, 29, 29, 0.8) 0%, rgba(29, 29, 29, 0.6) 30%, transparent 80%),
                        radial-gradient(circle at 70% 40%, rgba(29, 29, 29, 0.7) 10%, rgba(29, 29, 29, 0.5) 40%, transparent 85%),
                        radial-gradient(circle at 50% 80%, rgba(29, 29, 29, 0.6) 5%, rgba(29, 29, 29, 0.4) 30%, transparent 90%),
                        radial-gradient(circle at 40% 60%, rgba(34, 93, 58, 0.3) 5%, rgba(34, 93, 58, 0.15) 30%, transparent 85%),
                        linear-gradient(45deg, rgba(29, 29, 29, 0.9) 0%, rgba(29, 29, 29, 0.7) 40%, rgba(34, 93, 58, 0.4) 100%),
                        url('https://raw.githubusercontent.com/LinderCa/assets/refs/heads/main/fondo.png') no-repeat center center fixed !important;
                        background-size: cover !important;
                    }

                    .stButton > button{
                        width: 100%;
                        margin:0px;
                        border-color: #57cc99;
                    }
                    
                    .stButton > button:hover{
                        box-shadow: 0px 0px 5px #80ed99;
                    }
                    .stButton > button p{
                        font-size:18px;
                        color: #57cc99;
                    }
                    
                    .sidebar-separador{
                        border: 0;
                        height: 1px;
                        background-color: #c7f9cc !important;
                        margin: 2px 0px !important;
                    }

                </style>
                """,unsafe_allow_html=True)
    # Sección Historical en la sidebar con expander
    
    with st.sidebar.expander("📜 Estrategias"):
        #st.page_link("pages/pm40.py", label="PM40", icon="⚙️")
        st.page_link("pages/pm40.py", label="⩚ Promedio Movil de 40")
        st.page_link("pages/ruptura_bajista.py", label="Ϟ Ruptura de Canal ")
        st.page_link("pages/cncf.py", label="↙ Caida Normal-Fuerte")
        st.page_link("pages/gap_alza.py", label="⇧ Gap a la Alza")
        st.page_link("pages/piso_fuerte.py", label="✪ Piso Fuerte")
        #st.page_link("pages/ruptura_alcista.py", label="✪ Ruptura Alcista")
        st.page_link("pages/cba.py", label="✪ Caida Bajista Alcista")

    st.sidebar.markdown("<hr class='sidebar-separador'>", unsafe_allow_html=True)

   # Sesion salir
    with st.sidebar.expander("🔒 Salir", expanded=False):
        if st.button("Cerrar sesión", key="logout_button"):
            # Limpiar modo de sesión
            if "modo" in st.session_state:
                del st.session_state["modo"]

            # Redirigir (simulado)
            st.success("👋 Has cerrado sesión correctamente.")
            st.switch_page("inicio.py")  # ← Cambia esto si tu archivo principal tiene otro nombre


