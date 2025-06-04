import streamlit as st
import pandas as pd
import time
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode,GridUpdateMode
from utils.graficar import graficar
from utils.kpis_mean import mean_duration,mean_price
from components.sidebar import generarSidebar
from utils.proteger_pag import proteger_pagina

proteger_pagina()


def app_pm40():
    generarSidebar()
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
    time.sleep(2)
    loading_placeholder.empty()

    # URLs
    url_casos = "https://raw.githubusercontent.com/kaliinversionesyservicios/TraderEstrategias/main/data/pm40_h.txt"
    estadisticas="https://raw.githubusercontent.com/kaliinversionesyservicios/TraderEstrategias/main/data/backtesting/estadisticas_pm40.txt"
    trades="https://raw.githubusercontent.com/kaliinversionesyservicios/TraderEstrategias/main/data/backtesting/trades_pm40.txt"

    st.markdown("""
        <div style='text-align: left;'>
            <h1 style='
                font-size: 38px;
                font-weight: bold;
                background: linear-gradient(to right,#57cc99, #c7f9cc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: inline-block;
            '>
                Estrategia Promedio Movil
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
    
    try:
        df_casos=pd.read_csv(url_casos,sep='\t')
        df_estadisticas = pd.read_csv(estadisticas,sep='\t')   
        df_trades=pd.read_csv(trades,sep='\t')

        #st.dataframe(df_casos)
        #st.dataframe(df_estadisticas)
        #Modificamos el tipo en datetime
        df_estadisticas["EntryTime"]=pd.to_datetime(df_estadisticas["EntryTime"])
        df_estadisticas["ExitTime"]=pd.to_datetime(df_estadisticas["ExitTime"])
        df_trades['EntryTime']=pd.to_datetime(df_trades['EntryTime'])
        df_trades['ExitTime']=pd.to_datetime(df_trades['ExitTime'])

        dict_fecha={'EntryTime':df_estadisticas["EntryTime"].loc[0],'ExitTime':df_estadisticas["ExitTime"].loc[0]}

        # Mostrar métricas por ticker con selectbox
        tickers = sorted(df_estadisticas["Ticker"].unique())
        tickers.insert(0,"Todos")
        ticker_current=st.selectbox("Selecciona un ticker", tickers,key="ticker_selector")
        #st.success(f"Ticker seleccionado: {ticker_current}")
        columns=['Ticker','EntryTime','ExitTime','EntryPrice','ExitPrice','Duration','caso']

        if ticker_current=="Todos":
            df_grilla=df_trades[columns]
        else:
            df_grilla =df_trades[df_trades['Ticker']==ticker_current]
            df_grilla=df_grilla[columns]

        # Preprocesar columnas para grilla
        #columnas = ["Ticker", "EntryTime", "ExitTime","Duration","EntryPrice","ExitPrice",'Caso']
        data = df_grilla[columns].copy()
        data.sort_values("EntryTime", ascending=False, inplace=True)

        # Columas Auxiliares para pintar filas actaules de grilla
        data["EntryDateTime"]=pd.to_datetime(data["EntryTime"])
        data["EntryDate"]=data["EntryDateTime"].dt.date 
        #Fecha de hoy
        hoy=date.today()
        data["EsHoy"]=data["EntryDate"]==hoy

        # Convertir EntryTime y ExitTime a string con zona horaria
        data["EntryTime"] = data["EntryTime"].dt.strftime("%Y-%m-%d %H:%M:%S%z")
        data["ExitTime"] = data["ExitTime"].dt.strftime("%Y-%m-%d %H:%M:%S%z")

        # Eliminar la columna auxiliar
        data.drop(columns=["EntryDateTime",'EntryDate'], inplace=True)

        data_mean=data[['Duration','EntryPrice','ExitPrice']]

        #RESERVA DE ESPACIO
        kpi_holder=st.empty()

        df_inicial=df_estadisticas.groupby("Ticker").mean(numeric_only=True).reset_index()
        with kpi_holder:
            mostrar_kpis_por_ticker(df_inicial, promedio=True,fecha=dict_fecha,data=data_mean)
        
        # Mostrar grilla interactiva
        gb = GridOptionsBuilder.from_dataframe(data)
        
        # Usar JsCode para pintar filas donde EsHoy es True
        row_style_jscode = JsCode("""
        function(params) {
            if (params.data.EsHoy) {
                return { backgroundColor: 'rgba(255,200,150,0.3)', color: 'black' };
            }
            return {};
        }
        """)
        gb.configure_grid_options(getRowStyle=row_style_jscode)

        gb.configure_selection("single", use_checkbox=True)
        
        grid_options = gb.build()

        grid_response = AgGrid(
            data,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            height=400,
            width='100%',
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True  # <- Necesario para usar JsCode
        )
        

        selected = grid_response["selected_rows"]

        #FUNCION PROBADA
        def tipo_vela():
            df_casos['datetime'] = pd.to_datetime(df_casos.datetime) 
            df_casos["Datetime_str"] = df_casos["datetime"].astype(str)
            df_casos["BarColor"] = df_casos[["Open","Close"]].apply(lambda o: "red" if o.Open>o.Close else "green", axis=1)
            return df_casos

        # 6) Cuando el usuario cambie el selectbox, **vuelve a pintar solo el placeholder**
        if ticker_current != "Todos":
            df_sub = df_estadisticas[df_estadisticas['Ticker']==ticker_current]
            data_for_ticker=data[['Duration','EntryPrice','ExitPrice']]
            with kpi_holder:
                mostrar_kpis_por_ticker(df_sub, promedio=False, fecha=dict_fecha,data=data_for_ticker)

        if selected is not None:
            if len(selected) > 0:
                titulo = "Gráfico"
                st.markdown(f'<h3 style="color: #57cc99; text-align: left;">{titulo}</h3>', unsafe_allow_html=True)
                df=tipo_vela()
                ticker=selected.iloc[0]['Ticker']
                caso=selected.iloc[0]['caso']
                st.success(f"Fila Seleccionada {ticker} | Fecha Entrada: {selected.iloc[0]['EntryTime']} | caso: {caso}")
                dfpl = df.query("companyName == @ticker and caso == @caso")
                df_sub = df_estadisticas[df_estadisticas["Ticker"] == ticker]
                #df_casos_prueba=dfpl.query("ind_posicion==0 or isBreakOutIni==1 or isBreakOutFinal==1").copy()
                columna_for_ticker=data.query("Ticker== @ticker")
                column_ticker_mean=columna_for_ticker[['Duration','EntryPrice','ExitPrice']]
                with kpi_holder:
                    mostrar_kpis_por_ticker(df_sub, promedio=False, fecha=dict_fecha,data=column_ticker_mean)
                graficar(dfpl,"Promedio Movil")
            else:
                st.warning("⚠️ No hay ninguna fila seleccionada.")
        else: 
            st.warning("⚠️ No hay ninguna fila seleccionada.")
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")

def mostrar_kpis_por_ticker(df_stats, promedio=False, fecha={},data=None):
    media_duracion=mean_duration(data['Duration'])
    media_precio=mean_price((data['ExitPrice']-data['EntryPrice'])/data['EntryPrice'])
   
    start = fecha['EntryTime'].strftime("%d/%m/%Y %H:%M")
    end = fecha['ExitTime'].strftime("%d/%m/%Y %H:%M")
    if promedio:
        row = {}
        row["# Trades"] = df_stats["# Trades"].sum()
        columnas_promedio = [
            "Win Rate [%]", "Max. Drawdown [%]", "Return [%]",
            "Sharpe Ratio", "Profit Factor", "CAGR [%]", "Expectancy [%]"
        ]
        for col in columnas_promedio:
            row[col] = df_stats[col].mean()
            
    else:
        row = df_stats.iloc[0]

    titulo = f"Todos los Ticker" if promedio else row["Ticker"]

    st.markdown(f"""
        <style>
        .kpi-container {{
            display: grid;
            grid-template-columns: repeat(5, 1fr); 
            gap: 20px;
            margin-top: 20px;
            justify-items: center;
            margin-bottom: 30px;

        }}
        .kpi-card {{
            pointer-events: auto;
            position: relative;
            width: 95%;
            height: 140px;
            background: linear-gradient(145deg, #121416, #1a1d1f);
            box-shadow: 0 4px 10px #212529, 0 0 10px rgb(33, 37, 41); 
            border-radius: 5px;
            padding: 20px;
            overflow: visible;
            transition: transform 0.3s ease-in-out, background 0.3s, color 0.3s;
            color: #c7f9cc;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
         .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 15px #212529, 0 0 12px #212529;
        }}
         .kpi-card:hover .kpi-title {{
            color: #57cc99; /* Color nuevo para título en hover */
        }}
        .kpi-card:hover .kpi-value {{
            color: #80ed99; /* Color nuevo para valor en hover */
        }}
        
        .kpi-title {{
            position: absolute;
            bottom: 10px;
            left: 15px;
            font-size: 14px;
            font-weight: 600;
            color: #80ed99;
        }}
        .kpi-value {{
            font-size: 40px;
            font-weight: bold;
            color: #c7f9cc;
            z-index: 1;
        }}
        
        .kpi-card .tooltip {{
            visibility: hidden;
            width: 200px;
            background-color: #57cc99;
            color: #001524;
            text-align: center;
            padding: 10px;
            border-radius: 6px;
            position: absolute;
            z-index: 2;
            bottom: 70%;
            right: 0%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0px 0px 10px #000;
            font-size: 13.5px;
        }}
        
        .kpi-card:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        </style>

        <h3 style="color: #57cc99; text-align: left;"> 🗒️ {titulo}</h3>
        <div style="text-align: left; font-size: 14px; color: #c7f9cc; font-weight: 600;">
            🕒 Periodo analizado: <strong>{start}</strong> → <strong>{end}</strong>
        </div>
        <div class="kpi-container">
            <div class="kpi-card"  >
                <div class="tooltip">Cantidad total de operaciones realizadas en el periodo.</div>
                <div class="kpi-title">∑ # Trades</div>
                <div class="kpi-value">{int(row["# Trades"])}</div>
            </div>
            <div class="kpi-card" >
                <div class="tooltip">Porcentaje de operaciones ganadoras respecto al total.</div>
                <div class="kpi-title">∆ Win Rate</div>
                <div class="kpi-value">{round(row["Win Rate [%]"], 2)}%</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">La máxima caída de capital desde un punto alto hasta uno bajo.</div>
                <div class="kpi-title">↓ Max Drawdown</div>
                <div class="kpi-value">{round(row["Max. Drawdown [%]"], 2)}%</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">Retorno total durante el periodo analizado.</div>
                <div class="kpi-title">↑ Retorno</div>
                <div class="kpi-value">{round(row["Return [%]"], 2)}%</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">Medida de rentabilidad ajustada al riesgo.</div>
                <div class="kpi-title">ƒ Sharpe Ratio</div>
                <div class="kpi-value">{round(row["Sharpe Ratio"], 2)}</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">Relación entre ganancias totales y pérdidas totales.</div>
                <div class="kpi-title">⚐ Profit Factor</div>
                <div class="kpi-value">{round(row["Profit Factor"], 2)}</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">Tasa de crecimiento anual compuesta.</div>
                <div class="kpi-title">✓ CAGR</div>
                <div class="kpi-value">{round(row["CAGR [%]"], 2)}%</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">Rentabilidad promedio esperada por operación.</div>
                <div class="kpi-title">≈ Expectancy</div>
                <div class="kpi-value">{round(row["Expectancy [%]"], 2)}%</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">Duracion esperada</div>
                <div class="kpi-title">⏱ Duracion</div>
                <div class="kpi-value">{media_duracion}</div>
            </div>
            <div class="kpi-card">
                <div class="tooltip">Retorno porcentual promedio por trade</div>
                <div class="kpi-title">% Promedio por Operación</div>
                <div class="kpi-value">{round(media_precio,2)*100}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Para probar la función de inmediato
if __name__ == "__main__":
    app_pm40()
