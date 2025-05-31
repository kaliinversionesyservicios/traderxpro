import streamlit as st
import os

def load_css(file_name):
    # Construimos la ruta absoluta
    file_path = os.path.join(os.path.dirname(__file__), '..', file_name)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error al cargar el CSS desde {file_path}: {e}")
