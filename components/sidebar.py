import streamlit as st

def generarSidebar():
    st.markdown("""
                <style>
                    .st-emotion-cache-6qob1r {
                        width: 85%;
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
                    
                    .st-emotion-cache-1oou9d  > p{
                        color: #fff;
                        padding-bottom: 5px;  
                        font-size:12px;  
                    }
                    .st-emotion-cache-1w3omjh {
                        font-size: 18px !important;  /* Aumenta el tamaño del texto */
                        font-weight: bold !important; /* Hace que el texto sea más grueso */
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
        st.page_link("pages/pm40.py", label="⩚ Promedio Movil")
        st.page_link("pages/canal_bajista.py", label="Ϟ Ruptura Bajista")
        st.page_link("pages/caida_normal.py", label="⩏ Caida Normal")
        #st.page_link("pages/rsi_bollinger.py", label="RSI + Bollinger", icon="📈")

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


