import streamlit as st
import pandas as pd
import numpy as np


def app_prueba():
    url_casos = "/home/ec2-user/data/tba.txt"
    url_prediccion = "/home/ec2-user/data/prediccion_strike.txt"
    st.title("ESTO ES UN ARCHIVO DE PRUEBA")
    df_prueba=pd.read_csv(url_casos,sep='\t')
    st.dataframe(df_prueba)
    st.write("PREDICCION STRIKE")
    df_prediccion=pd.read_csv(url_prediccion,sep='\t')
    st.dataframe(df_prediccion)

if __name__=="__main__":
    app_prueba()