import streamlit as st
import time


def mostrar_spinner(segundos=3):
    loading_placeholder = st.empty()
    spinner_css = """
    <style>
    .loading-screen {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(87, 204, 153, 0);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    .loader {
        border: 8px solid #c7f9cc;
        border-top: 8px solid #57cc99;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    <div class="loading-screen">
      <div class="loader"></div>
    </div>
    """
    loading_placeholder.markdown(spinner_css, unsafe_allow_html=True)
    time.sleep(segundos)
    loading_placeholder.empty()