import streamlit as st
import pandas as pd
from components.sidebar import generarSidebar
from utils.spinner import mostrar_spinner
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode,GridUpdateMode
import os
import streamlit.components.v1 as components


def app_estadisticas():
    generarSidebar()
    mostrar_spinner(segundos=3)
    st.write("Estadisticas")

    #URL PRODUCCION
    url_trades="/home/ubuntu/script/data/backtesting/estadisticas_cba.txt"
    url_plots="/home/ubuntu/script/plots"

    #url  LINDER 
    # url_trades="D:/scripts_aws/data/backtesting/estadisticas_cba.txt"
    # url_plots="D:/scripts_aws/plots"
    df_estadisticas=pd.read_csv(url_trades,sep='\t')

    #FILTRO
    tickers = sorted(df_estadisticas["Ticker"].unique())
    tickers.insert(0,"Todos")
    ticker_current=st.selectbox("Selecciona un ticker", tickers,key="ticker_selector")

    if ticker_current == "Todos":
        df_grilla=df_estadisticas
        #Agrupacion por Tipo de operacion
    else:
        df_grilla=df_estadisticas[df_estadisticas['Ticker']==ticker_current]
        
     # Mostrar grilla interactiva
    gb = GridOptionsBuilder.from_dataframe(df_grilla)

    # Usar JsCode para pintar filas donde EsHoy es True
    row_style_jscode = JsCode("""
    function(params) {
        if (params.data.EsHoy) {
            return { backgroundColor: 'rgba(199, 249, 204,0.7)', color: 'black' };
        }
        return {};
    }
    """)
    gb.configure_grid_options(getRowStyle=row_style_jscode)

    gb.configure_selection("single", use_checkbox=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        df_grilla,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        height=400,
        width='100%',
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True  # <- Necesario para usar JsCode
    )
    selected = grid_response["selected_rows"]

    if selected is not None:
        if len(selected) > 0:
            #st.write("Mostrar plot")
            #st.write(selected)
            ticker=selected.iloc[0]['Ticker']
            tag=selected.iloc[0]['Tag']
            st.write(f"Backtesting")
            file_name=f"plot-{tag}-{ticker}.html"
            file_path=os.path.join(url_plots, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                components.html(html_content, height=800, scrolling=True)
            else:
                st.warning(f"El archivo {file_name} no existe.")
    else:
        st.warning("Seleccione un registro para su plot")

if __name__=="__main__":
    app_estadisticas()