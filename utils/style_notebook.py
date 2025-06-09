import streamlit as st

def mostrar_style_notebook(title):
    st.markdown(f"""
        <div style='text-align: left;'>
            <h1 style='
                font-size: 38px;
                font-weight: bold;
                background: linear-gradient(to right,#57cc99, #c7f9cc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: inline-block;
            '>
                {title}
            </h1>
            <hr style='
                border: none;
                height: 2px;
                width: 460px;
                background-color: #212529;
                margin-top: 0;
                margin-bottom: 10px;
            '/>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        div[data-baseweb="select"] > div {
            border: 1px solid #57cc99 !important;
            border-radius: 8px;
            box-shadow: 0px 0px 1.2px rgba(87, 204, 153, 0.6);
        }
        </style>
    """, unsafe_allow_html=True)