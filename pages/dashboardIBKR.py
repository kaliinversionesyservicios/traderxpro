import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd
#import plotly.express as px
import boto3
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from bokeh.plotting import figure, column
from bokeh.models import  NumeralTickFormatter, Span, CrosshairTool, Label
from bokeh.layouts import gridplot
import os
import numpy as np
import json
from scipy.signal import argrelextrema
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from decimal import Decimal
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from bot import script_crud as bd
from components.sidebar import generarSidebar
from streamlit_cookies_manager import EncryptedCookieManager

# 1) Página en modo ancho
st.set_page_config(page_title="IBKR Dashboard", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    "<h1 style=' background: linear-gradient(to right,#57cc99, #c7f9cc);-webkit-background-clip: text; -webkit-text-fill-color: transparent; '>IBKR Dashboard</h1>"
    "<h4 style='color:#c7f9cc;'>Control y monitoreo de tu cuenta y ejecución de bots</h4>",
    unsafe_allow_html=True
)

generarSidebar()

#----------------------------
# VALIDACION DE USUARIO
#----------------------------
cookies = EncryptedCookieManager(prefix="miapp", password="clave-secreta-123")
if not cookies.ready():
    st.stop()

if "usuario" not in st.session_state:
    st.session_state.usuario = cookies.get("usuario")

# st.write(f"Usuario:",st.session_state.get("usuario"))
user=st.session_state.get("usuario")

if not st.session_state.usuario:
    st.warning("⚠️ No estás autenticado. Inicia sesión primero.")
    st.switch_page("inicio.py")
    st.stop()

#----------------------
# VARIABLES GLOBALES
#----------------------
#path_folder="/mnt/efs" #PRODUCCION
path_folder="D:\TraderEstrategias" #DESARROLLO CARLOS

# API_BASE = "http://127.0.0.1:8000"
client = boto3.client("scheduler", region_name="us-east-2") # Cliente de EventBridge Scheduler
#Verificar si existe un usuario

match user:
    case "carlosml0287":
        SCHEDULE_NAME="cron_scanner_bot_carlos"
        #API_BASE="http://3.13.179.45:8000"
        API_BASE = "http://127.0.0.1:8000"
    case "investyolanda1":
        SCHEDULE_NAME="cron_scanner_bot_yolanda"
        API_BASE="http://3.140.173.63:8000"
    case "Ventanilla39":
        SCHEDULE_NAME="cron_scanner_bot_elsy"
        API_BASE="http://3.149.168.211:8000"
    case "usuario04":
        SCHEDULE_NAME="cron_scanner_usuario04"
CONFIG_FILE=f"{path_folder}/config_gestion_riesgo/param.json"

def get_schedule_state():
    try:
        response = client.get_schedule(Name=SCHEDULE_NAME)
        return response.get("State", "UNKNOWN"), response  # devolvemos todo el schedule
    except Exception as e:
        return f"Error: {e}", None

def update_schedule_state(new_state):
    try:
        # Obtener el schedule actual
        state, schedule = get_schedule_state()
        if not schedule:
            return "No se pudo leer el schedule"

        # Llamar a update_schedule con todos los parámetros obligatorios
        client.update_schedule(
            Name=schedule["Name"],
            Description=schedule.get("Description", ""),
            ScheduleExpression=schedule["ScheduleExpression"],
            FlexibleTimeWindow=schedule["FlexibleTimeWindow"],
            Target=schedule["Target"],
            State=new_state
        )
        return f"Estado cambiado a {new_state}"
    except Exception as e:
        return f"Error: {e}"

# ----------------------
# Funciones para obtener datos del backend
# ----------------------
def fetch_positions():
    try:
        resp = requests.get(f"{API_BASE}/positions", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Error fetching positions: {e}")
    return []

def fetch_trades():
    try:
        resp = requests.get(f"{API_BASE}/trades", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Error fetching trades: {e}")
    return []

def fetch_portfolio():
    try:
        resp = requests.get(f"{API_BASE}/portfolio", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Error fetching portfolio: {e}")
    return []

def fetch_order():
    try:
        resp = requests.get(f"{API_BASE}/order", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Error fetching order: {e}")
    return []

def fetch_summary():
    try:
        resp = requests.get(f"{API_BASE}/summary", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Error fetching summary: {e}")
    return []

def fetch_accountSummary():
    try:
        resp = requests.get(f"{API_BASE}/accountSummary", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Error fetching accountsummary: {e}")
    return []

def fetch_datamkt(ticker):
    #df_datamkt = pd.DataFrame()
    try:
        resp = requests.get(f"{API_BASE}/datamkt/{ticker}", timeout=5)      
        if resp.status_code == 200: 
            bars = resp.json()
        return bars
    except Exception as e:
        st.warning(f"Error fetching portfolio: {e}")
    return []

def fetch_alldatamkt():
    #df_datamkt = pd.DataFrame()
    try:
        resp = requests.get(f"{API_BASE}/alldatamkt", timeout=7) 
        if resp.status_code == 200: 
            bars = resp.json()
        return bars
    except Exception as e:
        st.warning(f"Error fetching alldatamark: {e}")
    return []

# def fetch_allorder():
#     try:
#         resp = requests.get(f"{API_BASE}/allorder", timeout=2)
#         if resp.status_code == 200:
#             return resp.json()
#     except Exception as e:
#         st.warning(f"Error fetching order: {e}")
#     return []



# Ruta donde se guardará la configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # carpeta actual (pages)
ROOT_DIR = os.path.dirname(BASE_DIR)  # subimos un nivel (raíz del proyecto)
CONFIG_FILE = os.path.join(ROOT_DIR, "config_gestion_riesgo", "param.json")
CONFIG_FILE2 = os.path.join(ROOT_DIR, "config_gestion_riesgo", "config_riesgo.json")


user="carlosml0287" #configurar

def cargar_usuario():
    """Carga parametros de Usuario"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def cargar_config():
    """Carga la configuración de riesgo desde un archivo JSON si existe"""
    if os.path.exists(CONFIG_FILE2):
        with open(CONFIG_FILE2, "r") as f:
            return json.load(f)
    return None


st.title("📊 Dashboard - IBKR")

 # Cargar valores previos si existen
config_prev = cargar_config()
valTipo_cuenta_prev = config_prev.get("tipo_cuenta") if config_prev else ""
valStatus_bot_prev= config_prev.get("status_bot") if config_prev else ""

usuarios = cargar_usuario()
config = cargar_config()
tipo_cuenta = config.get("tipo_cuenta")

token=""
queryid =""
table_IBKR_Trades=""
table_IBKR_Account=""
acceskey=""
secretaccess=""

if user in usuarios:
    valores = usuarios[user]
    print(f"Datos de {user}:")
    for clave, valor in valores.items():
        if tipo_cuenta=="PAPER":
            if clave=="account_idpaper":
                id_file=valor
            if clave=="table_IBKR_Trades_paper":
                table_IBKR_Trades=valor
            if clave=="table_IBKR_Account_paper":
                table_IBKR_Account=valor                  
            table_posiciones_abiertas=f"posiciones_abiertas_{id_file}"            
        elif tipo_cuenta=="LIVE":
            if clave=="account_idlive":
                id_file=valor
            if clave=="table_IBKR_Trades_live":
                table_IBKR_Trades=valor
            if clave=="table_IBKR_Account_live":
                table_IBKR_Account=valor
            table_posiciones_abiertas=f"posiciones_abiertas_{id_file}"
        if clave=="aws_access_key_id":
            acceskey=valor
        if clave=="aws_secret_access_key":
            secretaccess=valor
        if clave=="token_flexquery":
            token=valor
        if clave=="id_flexquery":
            queryid=valor        

dynamodb = boto3.resource("dynamodb", region_name="us-east-2",
                          endpoint_url="http://localhost:8000",  # URL DynamoDB local
                          aws_access_key_id=acceskey,
                          aws_secret_access_key=secretaccess
                          )

#table = dynamodb.Table("IBKR_Trades")
#tableAccounts = dynamodb.Table("IBKR_Account")

table = dynamodb.Table(table_IBKR_Trades)
tableAccounts = dynamodb.Table(table_IBKR_Account)

# Scan DynamoDB
response = table.scan()
responseAccounts = tableAccounts.scan()

itemsAccounts =  responseAccounts ["Items"] #Cuentas dynamoDB
for indice, account in enumerate(itemsAccounts):
    tipo_cuenta = account["tipo_cuenta"]
    accountId = account["accountId"]
    name = account["name"]
    if valTipo_cuenta_prev==tipo_cuenta:
        st.session_state.accountId = accountId
        st.session_state.name = name


positions_data = fetch_positions()
portfolio_data = fetch_portfolio()
trades_data = fetch_trades()
summary_data = fetch_summary()
ordens_data = fetch_order()
accountSummary_data = fetch_accountSummary()
items = response["Items"] #Datos de dynamoDB

netLiquidation=0
currency=''
for indice, acc in enumerate(accountSummary_data):
    account = acc["account"]
    tag = acc["tag"]
    value = acc["value"]    
    if tag=='NetLiquidation':
        netLiquidation = format(Decimal(value),",")
        currency = acc["currency"]



# Auto-refresh cada 15 segundo
st_autorefresh(interval=15000, key="refresh")

path_file = "D:/TraderEstrategias" #DESARROLLO
#path_file = "/home/ubuntu/script" #PRODUCCION
#Carga de Variables
#Leer el archivo de Variables
ruta_archivo=f'{path_file}/data/strategy.txt'
if os.path.exists(ruta_archivo):
    # Cargar el archivo
    df_variable = pd.read_csv(ruta_archivo, sep='\t')
    print("Archivo cargado correctamente.")
else:
    # Crear un DataFrame vacío
    df_variable = pd.DataFrame()
    print("Archivo no existe. Se creó un DataFrame vacío.")



#Estilo
# Función para aplicar colores
def color_cel(val):
    if val > 0:
        return "color: white; background-color: green"
    elif val < 0:
        return "color: white; background-color: red"
    else:
        return "color: black; background-color: lightgray"
    
#Estilos
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Compactar métricas */
        .stMetric {
            padding: 0rem 0rem;
            font-size: 12px !important;
        }
        /* Reducir espacio entre tabs y título */
        .stTabs [role="tablist"] {
            margin-top: -1rem;
        }
         
        /* Ajustar títulos */
        h1 { font-size: 22px !important; margin-bottom: 0.5rem; margin-top: 0.6rem !important; }
        h2 { font-size: 18px !important; margin-bottom: 0.2rem !important; }
        h3 { font-size: 14px !important; margin-bottom: 0.1rem !important; }

        
        /* Reducir alto de inputs/selectbox */
        .stSelectbox div[data-baseweb="select"] > div {
            min-height: 18px;
        }

        /* Reducir botones */
        button[kind="primary"], button[kind="secondary"] {
            padding: 0.25rem 0.75rem;
            font-size: 13px !important;
        }

        /* Reducir espacio entre filas (columnas de Streamlit) */
        .css-1kyxreq, .st-emotion-cache-1kyxreq, .st-emotion-cache-vlxhtx e1lln2w83, .stVerticalBlock {
            gap: 0.1rem !important;
        }

    
        .st-emotion-cache-1wivap2, .e14qm3311{
            font-size: 20px !important;
        }
        

        .st-emotion-cache-1dd9c22, .e14qm3314{
            font-size: 15px !important;
        }

      

        /*class=stVerticalBlock st-emotion-cache-vlxhtx e1lln2w83*/
        /*st-emotion-cache-p38tq e14qm3313*/
        /*st-emotion-cache-1wivap2 e14qm3311*/

        /* Compactar tablas AgGrid/Styler */
        .ag-theme-streamlit .ag-cell {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            font-size: 12px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================
# Interfaz Web
# ======================


# Botones para cambiar modo
colh1, colh2, colh3, colh4, _ = st.columns([1, 1.2, 2, 2, 2])


with colh1:
    if valTipo_cuenta_prev=="LIVE":
        st.markdown(f":gray-badge[Tipo Cuenta:] :green-badge[{valTipo_cuenta_prev}]")
    else:
        st.markdown(f":gray-badge[Tipo Cuenta:] :red-badge[{valTipo_cuenta_prev}]")
with colh2:
    if valStatus_bot_prev=="ACTIVADO":
        st.markdown(f":gray-badge[Estado BOT:] :green-badge[{valStatus_bot_prev}]")
    else:
        st.markdown(f":gray-badge[Estado BOT:] :red-badge[{valStatus_bot_prev}]")
with colh3:    
        st.markdown(f":gray-badge[👤 Cuenta:] :gray-badge[{st.session_state.accountId} - {st.session_state.name}]")
with colh4:
        st.markdown(f":gray-badge[Net Liquidation:] :gray-badge[{netLiquidation} {currency}]")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Portafolio", "🔄 Trades", "📑 Ordenes", "⚠️ Configuracion Y Gestion de Riesgo"])
# ----------------------
def graficar(dfpl,title,Tag, portafolio, periodoCorto, periodoLargo):
    #st.write(Tag)
    dfpl.reset_index(drop=True, inplace=True)
    inc = dfpl.query("close>open")
    dec = dfpl.query("open>close")
    #TOOLS = "pan,wheel_zoom,box_zoom,reset,save,crosshair"
    #width=500, height=300,
    p = figure(
                height=300,
                title=title,
                background_fill_color="#efefef",
                #tools=TOOLS,
                tooltips=[("Index", "@index"),("Datetime", "@Datetime_str"), ("Open", "@open"), ("High","@high"), ("Low","@low"), ("Close","@close"), ("Volume","@volume")],
                #sizing_mode="stretch_both"
                sizing_mode="stretch_width"
            )
    #p.xaxis.major_label_orientation = 0.8 # radians
    #p.x_range.range_padding = 0.05
    #p.xaxis.axis_line_width = 4
    p.xaxis.major_label_overrides = {
        i: date.strftime('%b %d %T') for i, date in zip(dfpl.index, dfpl["date"])
    }
    # Ocultar etiquetas X en el gráfico superior para que no se repitan
    p.xaxis.visible = False

    p.segment("index", "high", "index","low",  color="black", line_width=1, source=dfpl)
    p.vbar(    
        x="index",
        width=0.6,
        bottom="open",
        top="close",
        fill_color="red",
        line_color="red",    
        source=dec   
    )
    p.vbar(    
        x="index",
        width=0.6,
        bottom="open",
        top="close",
        fill_color="green",
        line_color="green", 
        source=inc   
    )

    if Tag=="long":
        p.line(
            x="index", 
            y="EMACorta", 
            color="#ffb81c",
            legend_label=f"EMA Corta {periodoCorto}",
            line_width=1.5,
            source=dfpl)
        p.line(
            x="index", 
            y="EMALarga", 
            color="red",
            line_width=1.5,
            legend_label=f"EMA Larga {periodoLargo}",
            source=dfpl)
    else:
        p.line(
            x="index", 
            y="EMACorta2", 
            color="#ffb81c",
            line_width=1.5,
            legend_label=f"EMA Corta {periodoCorto}",
            source=dfpl)
        p.line(
            x="index", 
            y="EMALarga2", 
            color="red",
            line_width=1.5,
            legend_label=f"EMA Larga {periodoLargo}",
            source=dfpl)
    
    # if Tag=="long":

    cnt_iniTrade = dfpl[dfpl["inicioTrade"]==1]
    cnt_ts = dfpl[(np.isnan(dfpl["trailing_stop"])==False)]
    print ("carlosss cnt_ts:", cnt_ts.shape[0])
    cnt_ts2 = dfpl[(dfpl.trailing_stop!=None)]
    print ("carlosss cnt_ts:", cnt_ts2.shape[0])

    #print (dfpl)

    if cnt_iniTrade.shape[0]>0:
        #i2 = dfpl[dfpl["inicioTrade"]==1].index[0]
        #fin2 = dfpl.index[-1]
        #print("i2:",i2)
        #print("i_fin2:", fin2)
        p.line(
        x="index", 
        y="trailing_stop", 
        color="blue",
        line_width=1,
        legend_label="trailing_stop",
        source=dfpl)
        #source=dfpl[dfpl["trailing_stop"]!=None])

        ts_now = (dfpl[["trailing_stop"]][(np.isnan(dfpl["trailing_stop"])==False)]).iloc[-1]["trailing_stop"]
        print("ts_now:", ts_now)        
        hTS=Span(location=ts_now,dimension='width', line_color='blue',line_width=0.8, line_dash_offset= 0, line_dash='dashed',  level='annotation', tags= ['square'])
        
        labeltS = Label(x=0,           # posición X (puedes ajustar según necesites)
              y=ts_now,                # posición Y = ubicación de la línea
              x_units='screen',        # relativo al ancho del gráfico
              y_units='data',          # relativo a los datos (eje Y)
              text=f"TS {ts_now}", # texto a mostrar
              text_font_size="9pt",
              text_color="blue",
              background_fill_color="#efefef",
              background_fill_alpha=0.7)
        
        p.renderers.extend([hTS])
        p.add_layout(labeltS)

        inicio = (dfpl[(dfpl.inicioTrade==1)].index).tolist()[0]
        vline=Span(location=inicio,dimension='height', line_color='grey',line_width=0.8, line_dash_offset= 0, line_dash='dashed',  level='annotation', tags= ['square'])

        labelInicio = Label(x=inicio,           # posición X (puedes ajustar según necesites)
              y=dfpl['low'].min(),                # posición Y = ubicación de la línea            
              text=f"Ini. Trade", # texto a mostrar
              text_font_size="9pt",
              text_color="grey",
              text_align="center",
              background_fill_color="#efefef",
              background_fill_alpha=0.7)
        p.renderers.extend([vline])
        p.add_layout(labelInicio)
    
    # else:        
    #     i2 = dfpl[dfpl["inicioTrade"]==1].index[0]
    #     fin2 = dfpl.index[-1]
    #     print("i2:",i2)
    #     print("i_fin2:", fin2)
    
    #     p.line(
    #     x="index",
    #     y="trailing_stop2",
    #     color="black",
    #     legend_label="trailing_stop 2",
    #     source=dfpl[i2:fin2])
    
    #codigo para dibujar pivots
    p.scatter(x="index", y="pivotLow", marker="circle", size=6,
                    line_color="navy", fill_color="red", alpha=0.5, legend_label="Pivot Alcista", source=dfpl)
    p.scatter(x="index", y="pivotHigh", marker="circle", size=6,
                    line_color="navy", fill_color="green", alpha=0.5, legend_label="Pivot Bajista", source=dfpl)
    
  

    
    
    #print("FECHA DATE:",type(dfpl["date"]))
    #print("FECHA DATE2:",type(dfpl["Datetime_str"]))

    strike = portafolio.iloc[0]["strike"]
    #print("Strike:", strike)
    hStrike=Span(location=strike,dimension='width', line_color='green',line_width=0.8, line_dash_offset= 0, line_dash='dashed',  level='annotation', tags= ['square'])
    # Etiqueta asociada a la línea
    labelStrike = Label(x=0,           # posición X (puedes ajustar según necesites)
              y=strike,                # posición Y = ubicación de la línea
              x_units='screen',        # relativo al ancho del gráfico
              y_units='data',          # relativo a los datos (eje Y)
              text=f"Strike {strike}", # texto a mostrar
              text_font_size="9pt",
              text_color="green",
              background_fill_color="#efefef",
              background_fill_alpha=0.7)



    pricenow = dfpl["close"].iloc[-1]
    hPriceNow=Span(location=pricenow,dimension='width', line_color='grey',line_width=0.8, line_dash_offset= 0, line_dash='dashed',  level='annotation', tags= ['square'])
    # Etiqueta asociada a la línea
    labelPriceNow = Label(x=0,           # posición X (puedes ajustar según necesites)
              y=pricenow,                # posición Y = ubicación de la línea
              x_units='screen',        # relativo al ancho del gráfico
              y_units='data',          # relativo a los datos (eje Y)
              text=f"Price now {pricenow}", # texto a mostrar
              text_font_size="9pt",
              text_color="grey",
              background_fill_color="#efefef",
              background_fill_alpha=0.7)
       
    p.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")
    #p.xaxis.axis_label = "Fecha"
    p.yaxis.axis_label = "Precio"
    p.legend.location="top_left"
    p.legend.click_policy="hide"
    
    p.renderers.extend([hStrike])
    p.add_layout(labelStrike)
    p.renderers.extend([hPriceNow])
    p.add_layout(labelPriceNow)
       

    p.add_tools(CrosshairTool(line_width=0.4, line_alpha=0.7))
    #p.add_tools(CrosshairTool([width,height]))

    #height=50, width=500,
    volume = figure(x_axis_type="datetime", tooltips = [("Volume", "@volume"),("Datetime", "@Datetime_str")], height=80, sizing_mode="stretch_width",
    background_fill_color="#efefef",x_range=p.x_range)

    volume.x_range.range_padding = 0.05
    volume.vbar(    
        x="index",
        width=0.6,
        top="volume",
        fill_color="BarColor",
        line_color="BarColor", 
        source=dfpl   
    )

    volume.yaxis.axis_label="volume"
    volume.xaxis.major_label_overrides = {
        i: date.strftime('%b %d %T') for i, date in zip(dfpl.index, dfpl["date"])
    }
    volume.yaxis[0].formatter = NumeralTickFormatter(format="0,0")
    #fig = column(children=[p, volume], sizing_mode="scale_width")
    #stretch_both
    # make a grid
    #, height=300, width=500
    grid = gridplot([[p],[volume]], sizing_mode="stretch_width")
    #st.bokeh_chart(fig, use_container_width=True)
    st.bokeh_chart(grid)
# ----------------------

# ----------------------
# Posiciones
# ----------------------
#with positions_container:

print("===TRADES FRONT ===")
print(trades_data)

#print("======= PORTAFOLIO After=============")
#print(portfolio_data)
#print ("positions_data")
#print(positions_data)
#print ("ordens_data")
#print(ordens_data)

#revisar cantidades
print("======CANTIDADES=========")
print("portfolio_data:", len(portfolio_data))
print("trades_data:", len(trades_data))
print("summary_data:", len(summary_data))
print("ordens_data:", len(ordens_data))
print("positions_data:", len(positions_data))
print("accountSummary_data:", len(accountSummary_data))

with tab1:
    st.subheader("📊 Posiciones Abiertas")
    if portfolio_data:
        portfolio_df = pd.DataFrame(portfolio_data)        
        df_trades = pd.DataFrame(trades_data)
        unrealized_pnl = portfolio_df["Unrealized PnL"].sum()
        
        if  (df_trades.shape[0]>0):
            realized_pnl = portfolio_df["Realized PnL"].sum() + df_trades["Rlzd P&L"].sum()
        else:
            realized_pnl = portfolio_df["Realized PnL"].sum()

        col1, col2 = st.columns(2, gap="small")

        with col1:            
            
            # ========================
            # Configuración AgGrid
            # ========================
            gb = GridOptionsBuilder.from_dataframe(portfolio_df)
            gb.configure_selection("single", use_checkbox=True)
            gb.configure_pagination(enabled=True, paginationPageSize=5)
            gb.configure_grid_options(domLayout="normal")
    
            grid_options = gb.build()
            df_display = portfolio_df.copy()

            # Renderizar grilla
            grid_response = AgGrid(
                df_display,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                theme="balham",
                height=600
            )

        with col2:
            # ========================
            # Detectar fila seleccionada
            # ========================
            
            col11, col21, col31, col41 = st.columns([1, 1, 1, 1])
            selected = grid_response.get("selected_rows", [])
            # Asegurarnos que selected sea lista o DataFrame
            if selected is not None and len(selected) > 0:
                if isinstance(selected, pd.DataFrame):
                    ticker = selected.iloc[0]["Financial Instrument"]   # si es DataFrame
                    symbol = selected.iloc[0]["Symbol"]
                    conId = selected.iloc[0]["conId"]
                    inicio_ts = selected.iloc[0]["inicio_ts"]
                #else:
                #    ticker = selected.iloc[0]["Financial Instrument"]        # si es lista de dicts
                

                with col11:
                    if st.button(f"❌ Cerrar {ticker}"):
                        try:
                            requests.post(f"{API_BASE}/close_position/{conId}")
                            st.success(f"Cerro el trade {ticker}")
                        except Exception as e:
                            st.warning(f"Error cerrando posición: {e}")

                with col21:
                    st.write("Ini. T. Stop:")
                
                with col31:
                    #Caja de Texto
                    new_value = st.number_input("", min_value=-100, step=1, value=int(inicio_ts), format="%d")
                    new_value = int(new_value)

                with col41:
                    # Botón para actualizar
                    if st.button("Actualizar"):
                        #update_value_in_dynamo(pk, new_value)
                        key ={
                            'conId': int(conId)
                        }
                        update_expression= "SET inicio_ts = :ini_ts"                        

                        # Conversión segura antes de armar expression_values
                        if hasattr(new_value, "item"):
                            safe_value = int(new_value.item())
                        else:
                            safe_value = int(new_value)
                            
                        expression_values = {
                            ':ini_ts': int(safe_value)
                        }

                        #print("Tipo final:", type(expression_values[":ini_ts"]), expression_values[":ini_ts"])
                        
                        bd.update_item(table_posiciones_abiertas, key,update_expression, expression_values)
                        st.success("actualizado correctamente ✅")

            print ("hito2")
            if selected is not None and len(selected) > 0:
                ticker = selected.iloc[0]["Financial Instrument"]
                symbol = selected.iloc[0]["Symbol"]
                right = selected.iloc[0]["right"]
                st.subheader(f"Gráfico de {ticker}")

                try:
                    print ("hito3")
                    alldatamark = fetch_alldatamkt()
                    df_alldatamark = pd.DataFrame(alldatamark)
                    ##datamkt=fetch_datamkt(symbol)                    
                    print ("hito4")
                    #df_datamkt = pd.DataFrame(datamkt)
                    df_datamkt = df_alldatamark[df_alldatamark["ticker"]==symbol] #Filtrar por un symbol
                    df_datamkt['date'] = pd.to_datetime(df_datamkt.date)
                    print ("hito5")
                    #print("info dataframe")    
                    #print(selected.info())
                    #print(selected)
                    print("dateTime:",selected.iloc[0]["dateTime"])
                    #fechaEvaluar = pd.to_datetime(selected.iloc[0]["dateTime"])
                    print ("hito55")
                    #print("fechaEvaluar:", fechaEvaluar)
                    #print("tipo fechaEvaluar:", type(fechaEvaluar))

                    #print(df_datamkt["date"].tail(10))

                    #fechaEvaluarstr = selected.iloc[0]["dateTime"]
                    #print ("fechaEvaluar:", fechaEvaluarstr, ", tipo:", type(fechaEvaluarstr))
                    #fechaEvaluar = pd.to_datetime(fechaEvaluarstr, format="%d/%m/%Y;%H:%M:%S")


                    #st.dataframe(df_datamkt)
                    #print("df_datamkt")

                    #df_datamkt["inicioTrade"] = np.where(df_datamkt[(df_datamkt["date"].dt.floor("h") == fechaEvaluar.floor("h"))], 1, 0)
                    #df_datamkt["inicioTrade"] = np.where(df_datamkt["date"].dt.floor("h") == fechaEvaluar.floor("h"),  1, 0)

                    print ("hito6")
                    df_datamkt["Datetime_str"] = df_datamkt["date"].astype(str)
                    df_datamkt["BarColor"] = df_datamkt[["open","close"]].apply(lambda o: "red" if o.open>o.close else "green", axis=1)

                    if right=="C":
                        tag="long"
                    else:
                        tag="short"

                    filtro = df_variable.query("Ticker==@symbol and Tag==@tag")

                    if filtro.shape[0]>0:
                        periodoCorto = filtro.iloc[0]["periodoCorto"]
                        periodoLargo = filtro.iloc[0]["periodoLargo"]
                    else:
                        periodoCorto = 20
                        periodoLargo = 40
                    print ("hito7")

                    #print("datos df_datamkt-->")
                    #print(df_datamkt)

                    #print(df_datamkt.info())
                    hoy = datetime.today().date()
                    print ("hito8")
                    hace_5_dias = pd.to_datetime(hoy - timedelta(days=8))
                    df_datamkt2 = df_datamkt[df_datamkt["date"]>=hace_5_dias].copy()
                    print ("hito9")
                    graficar(df_datamkt2,"",tag, selected, periodoCorto, periodoLargo)

                except Exception as e:
                    st.warning(f"Error datos del mercado: {e}")

        st.markdown("---")  # línea divisoria opcional
        col1_2, col2_2, col3_2 = st.columns(3, gap="small")
        total_pnl = unrealized_pnl + realized_pnl
        
        with col1_2:
            st.metric("Unrealized PnL", f"${unrealized_pnl:.2f}",  border=True )
        with col2_2:
            st.metric("Realized PnL", f"${realized_pnl:.2f}",  border=True)
        with col3_2:
            st.metric("PnL Total", f"${total_pnl:.2f}",  border=True)
            # Ejemplo de riesgo: pérdida diaria máxima $500
            if total_pnl < -500:
                st.error("⚠️ Límite de pérdida diaria alcanzado (-500 USD). Considera cerrar posiciones.")

    else:
        st.info("No hay Posiciones Abiertas.")
    


# ----------------------
# Trades históricos
# ----------------------

#print("trades_data:", trades_data)

with tab2:
    st.subheader("Summary")
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        #st.dataframe(df_summary)    
        # Aplicar estilo a la columna Realized P&L
        styled_df = df_summary.style.applymap(color_cel, subset=["Realized P&L"])
        st.dataframe(styled_df, use_container_width=True)
    
    st.subheader("📈 Trades")
    if trades_data:
        df_trades = pd.DataFrame(trades_data)
        st.dataframe(df_trades)
    else:
        st.info("No hay trades históricos")

    if items:
        df_trades2 = pd.DataFrame(items)
        st.subheader("📈 Trades Históricos")
        st.dataframe(df_trades2)

# allordens_data = fetch_allorder()
with tab3:
    st.subheader("Ordenes abiertas")
    if ordens_data:
        df_orders = pd.DataFrame(ordens_data)
        st.dataframe(df_orders)
    else:
        st.info("No hay Ordenes abiertas")

    # if allordens_data:
    #      df_order2 = pd.DataFrame(allordens_data)
    #      st.subheader("📈 Ordenes Históricos")
    #      st.dataframe(df_order2)

# ----------------------
# Portfolio
# ----------------------
def guardar_configuracion_riesgo(config):
    # Crear carpeta si no existe
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    # Guardar JSON
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def guardar_estrategias(df):
    os.makedirs(os.path.dirname(ESTRATEGIAS_FILE), exist_ok=True)
    df.to_csv(ESTRATEGIAS_FILE, index=False)

def cargar_estrategias():
    """Carga estrategias seleccionadas desde CSV si existe"""
    if os.path.exists(ESTRATEGIAS_FILE):
        return pd.read_csv(ESTRATEGIAS_FILE)
    return pd.DataFrame()

with tab4:
    # URL PRODUCCION
    #url_trades="/home/ubuntu/script/data/backtesting/estadisticas_cba.txt"
    # URL LINDER
    #url_trades = "D:/scripts_aws/data/backtesting/estadisticas_cba.txt"
    #URL CARLOS
    url_trades="D:/data/backtesting/estadisticas_cba.txt"

    ESTRATEGIAS_FILE = os.path.join(ROOT_DIR, "config_gestion_riesgo", "estrategias_seleccionadas.csv")

    data = pd.read_csv(url_trades, sep='\t')
    # ----------- BARRA SUPERIOR -----------
    #st.markdown("---")
    # ----------- FORMULARIO DE RIESGO -----------
    with st.form("form_riesgo"):
        st.subheader("⚙️ Configuración de Riesgo")
        
        col1, col2 = st.columns(2)
        with col1:
            inicio_ts = st.number_input(
            "INICIO T.S (%)", 
            min_value=0.0, max_value=100.0, step=0.1, 
            value=config_prev.get("inicio_ts", 0.0) if config_prev else 0.0
            )
            precio_max_prima = st.number_input(
                "PRECIO MAX PRIMA ($)", 
                min_value=0.0, step=0.1, 
                value=config_prev.get("precio_max_prima", 0.0) if config_prev else 0.0
            )

            opTipo_cuenta = ["PAPER", "LIVE"]
            valTipo_cuenta_prev = config_prev.get("tipo_cuenta") if config_prev else ""
            #print("hito1:", valTipo_cuenta_prev)

            # obtener índice según el nombre
            if valTipo_cuenta_prev in opTipo_cuenta:
                indexTipo = opTipo_cuenta.index(valTipo_cuenta_prev)
            else:
                indexTipo = 0  # fallback si no existe

            selTipo_cuenta = st.selectbox("Tipo Cuenta",                            
                            opTipo_cuenta,
                            index=indexTipo,
                            placeholder="Select tip Account"
            )

        with col2:
            inv_sesion = st.number_input(
                "INV. SESION ($)",   # 💵 ahora es monto en dólares
                min_value=0.0, step=0.1, 
                value=config_prev.get("inv_sesion", 0.0) if config_prev else 0.0
            )
            cant_trades = st.number_input(
                "CANT. TRADES X DÍA", 
                min_value=0, step=1, 
                value=config_prev.get("cant_trades", 0) if config_prev else 0
            )

            opStatus_bot = ["DESACTIVADO", "ACTIVADO"]
            valStatus_bot_prev= config_prev.get("status_bot") if config_prev else ""

            # obtener índice según el nombre
            if valStatus_bot_prev in opStatus_bot:
                indexStatus = opStatus_bot.index(valStatus_bot_prev)
            else:
                indexStatus = 0  # fallback si no existe

            selStatus_bot = st.selectbox("Estado BOT",
                            opStatus_bot,
                            index=indexStatus,
                            placeholder="Select Status Bot"
            )


        submitted = st.form_submit_button("✅ Guardar Configuración", use_container_width=True)
    if submitted:
        config = {
            "inicio_ts": inicio_ts,
            "inv_sesion": inv_sesion,   # 💵 ahora en dólares
            "precio_max_prima": precio_max_prima,
            "cant_trades": cant_trades,
            "tipo_cuenta": selTipo_cuenta,
            "status_bot": selStatus_bot
        }

        guardar_configuracion_riesgo(config)
        st.success("Configuración de riesgo guardada en archivo 📂")
        st.json(config)
    st.markdown("---")
    # ----------- FORMULARIO DE ESTRATEGIAS -----------
    st.subheader("📊 Selección de Estrategias")

    # --- Mostrar tabla filtrada ---
    with st.form("form_tabla"):
        gb = GridOptionsBuilder.from_dataframe(data)
        gb.configure_side_bar()
        gb.configure_default_column(editable=False, groupable=True)

        # Selección múltiple con checkbox y "seleccionar todo"
        gb.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            header_checkbox=True
        )

        # Scroll sin paginación
        gb.configure_grid_options(domLayout="normal")

        grid_response = AgGrid(
            data,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True,
            theme="alpine",
            height=400,
            width="100%",
        )

        submitted_tabla = st.form_submit_button("💾 Guardar Configuración Estrategia(s)", use_container_width=True)

    if submitted_tabla:
        seleccionadas = grid_response.get("selected_rows")

        if seleccionadas is not None and len(seleccionadas) > 0:  # ✅ valida que haya filas
            seleccion = pd.DataFrame(seleccionadas)

            # 🔥 Solo guardar columnas Ticker y Tag
            if "Ticker" in seleccion.columns and "Tag" in seleccion.columns:
                seleccion = seleccion[["Ticker", "Tag", "Sharpe Ratio", "Win Rate [%]"]]
            else:
                st.warning("⚠️ No se encontraron las columnas Ticker, Tag, Sharpe Ratio, Win Rate [%] en la tabla.")

            guardar_estrategias(seleccion)  # 🔥 Guardar en archivo
            st.success(f"📌 {len(seleccion)} estrategia(s) seleccionada(s) y guardada(s) en archivo 📂")
            st.dataframe(seleccion, use_container_width=True)
        else:
            st.warning("⚠️ No se seleccionó ninguna estrategia.")