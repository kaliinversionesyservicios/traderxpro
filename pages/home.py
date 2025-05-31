import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Funciones para generar los gráficos (puedes personalizar esto con tus propias estrategias)
def plot_rsi():
    # Aquí generas tu gráfico de RSI
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(100), y=np.random.rand(100), mode='lines', name='RSI'))
    return fig

def plot_moving_average():
    # Aquí generas tu gráfico de media móvil
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(100), y=np.random.rand(100), mode='lines', name='Media Móvil'))
    return fig

def plot_bollinger_bands():
    # Aquí generas tu gráfico de bandas de Bollinger
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(100), y=np.random.rand(100), mode='lines', name='Bollinger'))
    return fig

def plot_fuerte_caida():
    # Aquí generas tu gráfico de caída fuerte
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(100), y=np.random.rand(100), mode='lines', name='Caída Fuerte'))
    return fig

# Diccionario de estrategias
estrategias = {
    'RSI': plot_rsi,
    'Media Móvil': plot_moving_average,
    'Bollinger Bands': plot_bollinger_bands,
    'Caída Fuerte': plot_fuerte_caida
}

# Crear una grilla o dataframe con las estrategias
df_estrategias = pd.DataFrame({
    'Estrategia': ['RSI', 'Media Móvil', 'Bollinger Bands', 'Caída Fuerte'],
    'Descripción': [
        'Índice de Fuerza Relativa.',
        'Media Móvil Simple.',
        'Bandas de Bollinger.',
        'Identificación de caídas fuertes.'
    ]
})

# Mostrar la grilla de estrategias
st.title("Análisis de Estrategias de Trading")
st.dataframe(df_estrategias)

# Seleccionar la estrategia
seleccionada = st.selectbox("Elige una estrategia", estrategias.keys())

# Mostrar el gráfico de la estrategia seleccionada
st.subheader(f"Gráfico de {seleccionada}")
fig = estrategias[seleccionada]()
st.plotly_chart(fig)
