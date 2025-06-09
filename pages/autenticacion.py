import streamlit as st
import firebase_admin
from firebase_admin import credentials,firestore,initialize_app
from dotenv import load_dotenv
import os
import time

#Cargar las variables de entorno
load_dotenv()

# Función para inyectar CSS personalizado
def aplicar_estilos():
    st.markdown("""
    <style>
        /* Título de la página */
        .login-title {
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            color: #57cc99;
            margin-bottom: 1.5rem;
        }
        
        /* Estilo para el contenedor del formulario */
        .stForm {
            background-color: rgba(33, 37, 41, 0.85); /* Fondo oscuro con algo de transparencia */
            box-shadow: 0px 6px 12px rgba(128, 237, 153, 0.3); /* Sombra suave con el verde claro */
            border-radius: 12px; /* Bordes redondeados para un toque más suave */
            padding: 2rem; /* Espaciado interno para mejorar la apariencia */
            width:700px;
            max-width: 900px;
            margin: 0 auto; /* Centrar el formulario */
        }
        
        /* Estilo para los botones */
        .stButton button {
            background-color: #57cc99;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 1.1rem;
            width: 100%;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        /* Efecto hover para el botón */
        .stButton button:hover {
            background-color: #48a97e;
            box-shadow: 0px 4px 8px rgba(128, 237, 153, 0.4);
        }
        
        /* Estilo para los inputs de texto */
        .stTextInput > div > div > input {
            background-color: #1c1c1c;
            color: white;
            padding: 0.75rem;
            border-radius: 8px;
            font-size: 1rem;
            width: 100%;
        }
        
        /* Estilo cuando el campo de input está enfocado */
        .stTextInput input:focus {
            border-color: #57cc99;
            outline: none;
        }

        /* Estilo para los mensajes de error/success */
        .stSuccess, .stError {
            text-align: center;
            font-size: 1.2em;
        }

    </style>
    """, unsafe_allow_html=True)


# Inicializar Firebase
if not firebase_admin._apps:
    import json
    service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
    #cred_path=os.getenv("FIREBASE_KEY_PATH")
    #cred_path = "D:/secrets/traderxpro-466db-firebase-adminsdk-fbsvc-35c9d96ef7.json"
    print("Ruta cargada desde .env:", service_account_info)
    cred=credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)

db=firestore.client()

def validar_usuario(username,password):
    try:
        usuarios_ref = db.collection("usuarios")
        query = usuarios_ref.where("username", "==", username).limit(1)
        results = query.get()
        if results:
            user_data = results[0].to_dict()
            if user_data.get("password") == password:
                return True
        return False
    except Exception as e:
        st.error(f"Error al validar: {e}")
        return False



# Formulario de login
def login():
    aplicar_estilos()

    # Título del formulario
    st.markdown('<div class="login-title">🔒 Login</div>', unsafe_allow_html=True)

    # Formulario de login
    with st.form(key="login_form"):
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        login_button = st.form_submit_button("Ingresar")

    # Lógica de validación
    if login_button:
        if validar_usuario(usuario,contraseña):
            st.success("✅ ¡Bienvenido! Acceso autorizado.")
            st.toast("Redirigiendo a tu panel...", icon="🔄")
            time.sleep(1.5)
            st.switch_page("pages/pm40.py")
            return True
        else:
            st.error("❌ Usuario o contraseña incorrectos. Intenta de nuevo.", icon="🚫")
            return False
    return False

if __name__ == "__main__":
    login()
