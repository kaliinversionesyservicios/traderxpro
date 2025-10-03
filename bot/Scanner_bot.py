# -*- coding: utf-8 -*-
# Importar librerías
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import *
from ib_insync import *
#from IB_Trading import IB_Trading, Contract
#from Analisis_Tecnico import Cruce_MA
import Analisis_Tecnico as ana_tecnico
import pandas as pd
import numpy as np
from datetime import datetime
import time
import config
import os
import ta as ta2
#import script_bd as bd
import script_crud as bd
from decimal import Decimal
import funciones_ibkr as ibkr
from scipy.signal import argrelextrema
from zoneinfo import ZoneInfo
import json
import csv
import sys
import pytz

# ny_tz = pytz.timezone("America/New_York")
#------------------------
# funciones
#------------------------
def cargar_usuario():
    """Carga parametros de Usuario"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def cargar_config():
    """Carga configuracion"""
    if os.path.exists(CONFIG_FILE2):
        with open(CONFIG_FILE2, "r") as f:
            return json.load(f)
    return None

#--------------------------
# Variables
#--------------------------
path_folder="/mnt/efs" #produccion
# path_folder="/bot_aws" #Desarrollo
# path_folder= "D:/TraderEstrategias" #Desarrollo carlos
user="carlosml0287"
# user="investyolanda1"
# user="Ventanilla39"
param_cuenta=int(sys.argv[1]) #0 paper 1 live

CONFIG_FILE  = f"{path_folder}/config_gestion_riesgo/param.json"

usuarios = cargar_usuario()
user_data=usuarios[user]


if param_cuenta==0:
    print("CUENTA PAPER")
    id_file=user_data.get("account_idpaper")
    tipo_cuenta="PAPER"
elif param_cuenta==1:
    print("CUENA LIVE")
    id_file=user_data.get("account_idlive")
    tipo_cuenta="LIVE"
else:
    print("Error: el parametro ingresado es errado.")
    sys.exit(1)  # Termina el programa con un código de error 1
print("id_file es: ",id_file)

CONFIG_FILE2 = f"{path_folder}/config_gestion_riesgo/config_{id_file}/config_riesgo.json"
CONFIG_FILE2 = f"{path_folder}/config_gestion_riesgo/config_{id_file}/config_riesgo.json"
CONFIG_FILE3 = f"{path_folder}/config_gestion_riesgo/config_{id_file}/estrategias_seleccionadas.csv"

config = cargar_config()
#casos = cargar_casos()

#cargamos los valores segun el tipo de cuenta 
if tipo_cuenta=="PAPER":
    print("Valores de paper")
    ip=user_data.get("ip_paper")
    port=user_data.get("port_paper")
    clientId=user_data.get("clientid_Bot_paper")
elif tipo_cuenta=="LIVE":
    print("valores de live")
    ip=user_data.get("ip_live")
    port=user_data.get("port_live")
    clientId=user_data.get("clientid_Bot_live")
else:
    print("Usuario con tipo de cuenta no encontrado")
    sys.exit(1)  # Termina el programa con un código de error 1

table_posiciones_abiertas=f"posiciones_abiertas_{id_file}"
inicio_ts = config.get("inicio_ts")
cant_trades=config.get("cant_trades")
precio_max_prima=config.get("precio_max_prima")
print("Valores")
print("ip: ",ip)
print("port: ",port)
print("clientId: ",clientId)
print("table_posiciones_abiertas: ",table_posiciones_abiertas)
print("tipocuenta: ",tipo_cuenta)


# Seleccionar Activos a Analizar
#tickers = config.tickers
#tickers = config.tickers_prueba
marco_tiempo = "1 hour"
tiempo_descargado = "15 D"


# zona New York
ny_tz = ZoneInfo("America/New_York")

# Hora actual en Nueva York
ny_time = datetime.now(ZoneInfo("America/New_York"))
print("type:", type(ny_time), ", ny_time:",ny_time)

dt1_hour = ny_time.replace(minute=0, second=0, microsecond=0)
print("dt1_hour:", dt1_hour)


class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}

    def historicalData(self, reqId: int, bar: BarData):
        ticker = self.reqId_to_ticker.get(reqId, f"ID{reqId}")
        if ticker not in self.data:
            self.data[ticker] = []
        self.data[ticker].append((bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume))

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print(f"✔ Datos recibidos para {self.reqId_to_ticker[reqId]}")
        self.pending_requests -= 1
        if self.pending_requests == 0:
            self.disconnect()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"❌ Error: ReqID={reqId}, Code={errorCode}, Msg={errorString}")

    def start_requests(self, tickers):
        self.reqId_to_ticker = {}
        self.pending_requests = len(tickers)

        for i, ticker in enumerate(tickers):
            contract = Contract()
            contract.symbol = ticker
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            self.reqId_to_ticker[i] = ticker

            self.reqHistoricalData(
                reqId=i,
                contract=contract,
                endDateTime="",
                durationStr="2 Y",
                barSizeSetting="1 hour",
                whatToShow="TRADES",
                useRTH=0,  #int. Whether (1) or not (0) to retrieve data generated only within Regular Trading Hours (RTH)
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            time.sleep(1.5)  # importante para evitar bloqueo de IB por exceso de llamadas

def df_limpiar(df_eval):
    meandif1 = df_eval['ATR'].mean()
    stddif1 = df_eval['ATR'].std()
    topdif1 = meandif1 + stddif1 * 1.96
    copydf = df_eval.copy()
    copydf['ind1'] = copydf.apply(lambda row: 1 if row['ATR'] > topdif1 else 0, axis=1)
    q3_dif1 = copydf[copydf['ind1']!=1]['ATR'].quantile(0.75)

    copydf =copydf.apply(
        lambda row: q3_dif1 if (row['ind1']==1) else 
        row['ATR'], axis=1)
    return copydf
                
def mercado_abierto(contract, usar_liquid=True):
    print("h1 mercado_abierto")
    details_list =ib.reqContractDetails(contract)
    details = details_list[0]
    print("h2 mercado_abierto")
    ahora = datetime.now(ny_tz)
    print("ahora (NY):", ahora)

    # elegir entre horario extendido (tradingHours) o solo RTH (liquidHours)
    horarios_str = details.liquidHours if usar_liquid else details.tradingHours
    horarios = horarios_str.split(";")

    for h in horarios:
        if "CLOSED" not in h:
            inicio, fin = h.split("-")
            #inicio = ny_tz.localize(datetime.strptime(inicio, "%Y%m%d:%H%M"))
            inicio = datetime.strptime(inicio, "%Y%m%d:%H%M").replace(tzinfo=ny_tz)

            #fin = ny_tz.localize(datetime.strptime(fin, "%Y%m%d:%H%M"))
            fin = datetime.strptime(fin, "%Y%m%d:%H%M").replace(tzinfo=ny_tz)

            print("inicio:", inicio, "fin:", fin)
            if inicio <= ahora <= fin:
                return True
    return False



# Generar Instancia
ib = IB()
ib.connect(ip, port, clientId=clientId)
#ib.connect("3.13.179.45", 4002, clientId=501)
#ib.connect("127.0.0.1", 4002, clientId=501) #IB GATEWAY DESARROLLO
#ib.connect("3.13.179.45", 7497, clientId=501) #TWS DESARROLLO
#ib.connect("127.0.0.1", 7497, clientId=501) #TWS DESARROLLO
  
# Crear Contrato
contrato = Contract()
contrato.secType = "STK"
contrato.exchange = "SMART"
contrato.currency = "USD"

# Ejecutar Sistema:
#Carga de Variables
#Leer el archivo de Variables
ruta_archivo=f'{path_folder}/data/strategy.txt'
if os.path.exists(ruta_archivo):
    # Cargar el archivo
    df_variable = pd.read_csv(ruta_archivo, sep='\t')
    print("Archivo cargado correctamente.")
else:
    # Crear un DataFrame vacío
    df_variable = pd.DataFrame()
    print("Archivo no existe. Se creó un DataFrame vacío.")

#Carga Estadisticas
#Leer el archivo de estadisticas
ruta_archivo=f'{path_folder}/data/backtesting/estadisticas_cba.txt'
if os.path.exists(ruta_archivo):
    # Cargar el archivo
    dfestadisticas = pd.read_csv(ruta_archivo, sep='\t')
    print("Archivo cargado correctamente.")
else:
    # Crear un DataFrame vacío
    dfestadisticas = pd.DataFrame()
    print("Archivo no existe. Se creó un DataFrame vacío.")

#print("===ESTADISTICAS===")
#print(dfestadisticas[(dfestadisticas["Sharpe Ratio"]>1.7) | (dfestadisticas["Win Rate [%]"]>=75)] )
#excluir = ['GOOG', 'AAPL']
#df_estadisticas = dfestadisticas[(((dfestadisticas["Sharpe Ratio"]>1.7) | (dfestadisticas["Win Rate [%]"]>=75)))]

#for ticker in df_tickers["Ticker"]:
#    print(ticker)
#df_tickers = df_estadisticas[['Ticker']].drop_duplicates()
#df_tickers = df_tickers.head(2)
casos = pd.read_csv(CONFIG_FILE3) 
df_casos = pd.DataFrame(casos)
df_tickers = df_casos[['Ticker']].drop_duplicates()
print("cantidad de tickers:", df_tickers.shape[0])

""" # Iterar hasta que cierre el mercado
#while True:"""
# Revisar si se han generado señales para cada ticker
cont = Stock('AAPL', "SMART", "USD")
valMercado = mercado_abierto(cont,True)
if valMercado==True:
    for i,row in df_tickers.iterrows():
        ticker = row["Ticker"]
        print(f"Ticker: {ticker}")
        contrato.symbol = ticker
        bars = ib.reqHistoricalData(contract=contrato, endDateTime="", durationStr=tiempo_descargado, barSizeSetting=marco_tiempo, whatToShow="TRADES", useRTH=False, formatDate=1)
        df_hist = util.df(bars)
        df_hist.rename(columns={'date':'Datetime','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}, inplace=True)

        if df_hist is None:
            #Volver a ejecutar la descarga, antes intentar encender el ushmds
            ## === REVISAR SI IB GATEWAY esta activo usHmds ====

            #IB_app2 = IB_Trading(log_file="alternative_errors2.txt", errors_verbose=True)
            ib2 = IB()
            clientId2 = clientId+1
            ib2.connect(ip, port, clientId=clientId2)
            #ib2.connect("127.0.0.1", 4002, clientId=998)
            #ib2.connect("3.13.179.45", 4002, clientId=998)
            #ib2.connect("127.0.0.1", 7497, clientId=998)
            # Definir contrato dummy simple
            contract = Stock('AAPL', 'SMART', 'USD')
            
            # Enviar solicitud dummy
            bars = ib2.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr='1 D',
                barSizeSetting='1 day',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1,
                keepUpToDate=False
            )
            
            # Cancelar la suscripción inmediatamente para evitar sobrecarga
            time.sleep(2)
            ib2.cancelHistoricalData(bars)
            ib2.disconnect()
            print("Propósito usHmds activado.")

            bars = ib.reqHistoricalData(contract=contrato, endDateTime="", durationStr=tiempo_descargado, barSizeSetting=marco_tiempo, whatToShow="TRADES", useRTH=False, formatDate=1)        
            df_hist = util.df(bars)
            df_hist.rename(columns={'date':'Datetime','open':'Open','high':'High', 'low':'Low','close':'Close','volume':'Volume'}, inplace=True)
    
        if (df_hist is None):
            (f"===> NO SE PUDO DESCARGAR {ticker}:")
            continue
        else:
            (f"===> Cantidad descargada {ticker}:", df_hist.shape[0])

    
        #Configurar dataframe
        #==== ALZA ======#    
        filtro = df_variable.query("Ticker==@ticker")
        if filtro[filtro["Tag"]=="long"].shape[0]>0:
            periodoCortoLong = filtro[filtro["Tag"]=="long"].iloc[0]["periodoCorto"]
            periodoLargoLong = filtro[filtro["Tag"]=="long"].iloc[0]["periodoLargo"]
        else:
            periodoCortoLong = 20
            periodoLargoLong = 40

        #==== BAJA ======#
        if filtro[filtro["Tag"]=="short"].shape[0]>0:
            periodoCortoShort = filtro[filtro["Tag"]=="short"].iloc[0]["periodoCorto"]
            periodoLargoShort = filtro[filtro["Tag"]=="short"].iloc[0]["periodoLargo"]
        else:
            periodoCortoShort = 20
            periodoLargoShort = 40

        print("PeriodoCortoLong:", periodoCortoLong,"periodoLargoLong:", periodoLargoLong, "periodoCortoShort:", periodoCortoShort,  "periodoLargoShort:", periodoLargoShort)

        df = df_hist.copy()
        # Quitar zona horaria
        df['Datetime'] = df['Datetime'].dt.tz_localize(None)
        df.sort_values(by=['Datetime'])

        #print(df.tail(5))

        df['EMACorta'] = df['Low'].ewm(span=periodoCortoLong, adjust=False).mean()
        df.dropna(inplace=False)
        df['EMALarga'] = df['Low'].ewm(span=periodoLargoLong, adjust=False).mean()
        df.dropna(inplace=False)

        df['EMACorta2'] = df['High'].ewm(span=periodoCortoShort, adjust=False).mean()
        df.dropna(inplace=False)
        df['EMALarga2'] = df['High'].ewm(span=periodoLargoShort, adjust=False).mean()
        df.dropna(inplace=False)

        # Calcular +DI, -DI y ADX (todo el DMI)
        dmi = ta2.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
        df['plus_di'] = dmi.adx_pos()   # +DI
        df['minus_di'] = dmi.adx_neg()  # -DI
        df['adx'] = dmi.adx()           # ADX

        #ATR indicador para Trailing Stop Loss
        df['ATR'] = ta2.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
        df['ATR2'] = df_limpiar(df)
        df['EMA35_ATR'] = df['ATR2'].ewm(span=35, adjust=False).mean()
        df.dropna(inplace=False)
        
        #=====AGREGAR PIVOTS=====
        ord=20
        ord2=10
        ord3=7

        # Aseguramos que estas columnas existen
        pivot_cols = [
            'pivotHigh', 'pivotLow', 'isPivot',
            'pivotHigh2', 'pivotLow2', 'isPivot2',
            'pivotHigh3', 'pivotLow3', 'isPivot3'
        ]

        for col in pivot_cols:
            if col not in df.columns:
                df[col] = np.nan

        max_idx = argrelextrema(df['High'].values, np.greater, order=ord)[0]
        min_idx = argrelextrema(df['Low'].values, np.less, order=ord)[0]

        max_idx2 = argrelextrema(df['High'].values, np.greater, order=ord2)[0]
        min_idx2 = argrelextrema(df['Low'].values, np.less, order=ord2)[0]

        max_idx3 = argrelextrema(df['High'].values, np.greater, order=ord3)[0]
        min_idx3 = argrelextrema(df['Low'].values, np.less, order=ord3)[0]

        # Aplicar el cálculo solo a los índices en la lista
        df.loc[df.index[max_idx], 'pivotHigh'] = df['High']+1e-3
        df.loc[df.index[min_idx], 'pivotLow'] = df['Low']-(1e-3)
        df.loc[df.index[max_idx], 'isPivot'] = 1
        df.loc[df.index[min_idx], 'isPivot'] = 2

        df.loc[df.index[max_idx2], 'pivotHigh2'] = df['High']+1e-3
        df.loc[df.index[min_idx2], 'pivotLow2'] = df['Low']-(1e-3)
        df.loc[df.index[max_idx2], 'isPivot2'] = 1
        df.loc[df.index[min_idx2], 'isPivot2'] = 2

        df.loc[df.index[max_idx3], 'pivotHigh3'] = df['High']+1e-3
        df.loc[df.index[min_idx3], 'pivotLow3'] = df['Low']-(1e-3)
        df.loc[df.index[max_idx3], 'isPivot3'] = 1
        df.loc[df.index[min_idx3], 'isPivot3'] = 2
        #=====FIN AGREGAR PIVOTS=====

        #=====AGREGAR COLUMNAS DE CRUCE DE EMAs=====
        #==CANAL ALCISTA==
        df['prev_EMACorta'] = df['EMACorta'].shift(1)
        df['prev_EMALarga'] = df['EMALarga'].shift(1)

        #Cruce de medias
        df['cruce_medias'] = 0
        df.loc[(df['prev_EMACorta'] < df['prev_EMALarga']) & (df['EMACorta'] > df['EMALarga']), 'cruce_medias'] = 1  # Golden Cross (Compra)
        df.loc[(df['prev_EMACorta'] > df['prev_EMALarga']) & (df['EMACorta'] < df['EMALarga']), 'cruce_medias'] = -1 # Death Cross (Venta)

        #drop columnas
        df.drop({'prev_EMACorta','prev_EMALarga'}, axis=1, inplace=True)

        #==CANAL BAJISTA==#
        df['prev_EMACorta2'] = df['EMACorta2'].shift(1)
        df['prev_EMALarga2'] = df['EMALarga2'].shift(1)

        #Cruce de medias
        df['cruce_medias2'] = 0
        df.loc[(df['prev_EMACorta2'] < df['prev_EMALarga2']) & (df['EMACorta2'] > df['EMALarga2']), 'cruce_medias2'] = 1  # Golden Cross (Compra)
        df.loc[(df['prev_EMACorta2'] > df['prev_EMALarga2']) & (df['EMACorta2'] < df['EMALarga2']), 'cruce_medias2'] = -1 # Death Cross (Venta)

        #drop columnas
        df.drop({'prev_EMACorta2','prev_EMALarga2'}, axis=1, inplace=True)

        print(f"===>{ticker}:", df.shape[0])


        #===ULTIMO CRUCE===
        #==CANAL ALCISTA==
        df['cruce_mediasx'] = 0
        #for ticker in tickers:
        #Tendencias a la Alza
        lstUltCruceB = df[(df['cruce_medias']==1)].tail(1).index
        df.loc[lstUltCruceB,'cruce_mediasx'] = 1
        if lstUltCruceB.size>0:
            idxEvaluar = lstUltCruceB[0]
            #Tendencias a la Alza
            lstUltCruceA = df[(df['cruce_medias']==-1) & (df.index>=idxEvaluar)].index
            df.loc[lstUltCruceA,'cruce_mediasx'] = -1

        #drop columnas
        df.drop({'cruce_medias'}, axis=1, inplace=True)
        df = df.rename(columns={'cruce_mediasx': 'cruce_medias'}) 

        #==CANAL BAJISTA==
        df['cruce_mediasx'] = 0
        #for ticker in tickers:
        #Tendencias a la Baja
        lstUltCruceB = df[(df['cruce_medias2']==-1)].tail(1).index
        df.loc[lstUltCruceB,'cruce_mediasx'] = -1
        if lstUltCruceB.size>0:
            idxEvaluar = lstUltCruceB[0]
            #Tendencias a la Alza
            lstUltCruceA = df[(df['cruce_medias2']==1) & (df.index>=idxEvaluar)].index
            df.loc[lstUltCruceA,'cruce_mediasx'] = 1

        #print("===> cantidad cruce alcista:", df[(df['cruce_medias']==1)].shape[0])
        #print("===> cantidad cruce bajista:", df[(df['cruce_medias2']==-1)].shape[0])

        #drop columnas
        df.drop({'cruce_medias2'}, axis=1, inplace=True)
        df = df.rename(columns={'cruce_mediasx': 'cruce_medias2'})


        #Leer el archivo de PREDICCION DE STRIKE
        #Archivo anterior
        ruta_archivo=f'{path_folder}/data/prediccion_strike.txt'
        if os.path.exists(ruta_archivo):
            # Cargar el archivo
            df_strike_pred_old = pd.read_csv(ruta_archivo, sep='\t')
            print("Archivo cargado correctamente.")
        else:
            # Crear un DataFrame vacío
            df_strike_pred_old = pd.DataFrame()
            print("Archivo no existe. Se creó un DataFrame vacío.")

        # Tabla que se mostrara en la APP como sugerencia de strike para opciones financieras
        #df_strike_pred_old[df_strike_pred_old['semana']=='s1']


        #Revisar si la seleccion del ticket es a la ALZA o a la BAJA
        ticker_alza = df_casos[df_casos["Tag"]=="long"].shape[0]
        ticker_baja = df_casos[df_casos["Tag"]=="short"].shape[0]

        now = datetime.utcnow()

        if ticker_alza>0:
            #=== OBTENCION DE CASOS ALCISTAS===
            df_casos_alza = pd.DataFrame()
            df_casos_alza = ana_tecnico.obtener_casos(df, df_strike_pred_old, df_variable, ticker, "long", "ALZA")
            print("Casos ALZA:",df_casos_alza.shape[0])
            if df_casos_alza.shape[0]>0:
                print("Casos abiertos ALZA:",df_casos_alza[np.isnan(df_casos_alza["ExitTime"])].shape[0])
                df_casos_abiertos_alza = df_casos_alza[np.isnan(df_casos_alza["ExitTime"])]
                if (df_casos_abiertos_alza.shape[0]>0):
                    for i,row in df_casos_abiertos_alza.iterrows():
                        # Verificar si la fecha de entrada es de hoy
                        # Dejamos solo hasta la hora

                        print("type EntryTime:", type(row["EntryTime"]), ", EntryTime:",row["EntryTime"])
                        
                        dt1_hour = ny_time.replace(minute=0, second=0, microsecond=0)                    
                        dt2_hour = row["EntryTime"].replace(tzinfo=ny_tz).replace(minute=0, second=0, microsecond=0)
                        print ("===== HORAS EVALUAR, hora1:", dt1_hour, ", hora2:", dt2_hour)

                        #if (ny_time.date() == row["EntryTime"].date()): #HABILITAR DESPUES
                        # Calcular diferencia
                        diff = (dt1_hour - dt2_hour).total_seconds() / 3600  # diferencia en horas
                        print ("DIFERENCIA HORAS:", diff)
                        if 0<dt1_hour.hour<=9:
                            hor_rango=6
                        else:
                            hor_rango=2

                        if 0 <= diff <= hor_rango: #HORAS MENOR AL RANGO HORARIO
                            print("===PASO HORAS===")
                            cantidad=1
                            precio = 0
                            right="C"
                            fecha_entrada = row["EntryTime"].strftime("%Y-%m-%d %H:%M:%S")                
                            print("fecha_entrada:", type(fecha_entrada), fecha_entrada)

                            filtro = df_strike_pred_old.query("Ticker==@ticker and semana=='s1' and Tag=='long'")
                            mov_calculado = np.float64(filtro.iloc[0]["strike_price_q3"])
                            print("--- Alza semana:", filtro.shape[0],", dato:", mov_calculado)
                            strike_calculado = Decimal(str(mov_calculado))
                            #bd.registrar_orden(ticker, cantidad, precio, tipo, fecha_entrada)
                            # Long CALL esperando +strike_calculado USD de movimiento
                            
                            order_call = ibkr.run_strategy(
                                symbol=ticker,
                                side='CALL',
                                expected_move=np.float64(strike_calculado), 
                                qty_contracts=1,
                                ip=ip,
                                port=port,
                                id_file=id_file,
                                inicio_ts=inicio_ts,
                                cant_trades=cant_trades,
                                precio_max_prima=precio_max_prima)

                            if order_call:
                                print("====Datos de la posicion===")
                                print("entry_price_per_share:",order_call["entry_price_per_share"])
                                print("premium_total:",order_call["premium_total"])
                                print("estimated_total_cost:",order_call["estimated_total_cost"])
                                print("breakeven:",order_call["breakeven"])
                                print("take_profit_price:",order_call["take_profit_price"])
                                print("parent_orderId:",order_call["parent_orderId"])

                                contract = Contract(order_put["contract"])
                                financial_instrument = f"{contract.symbol} {contract.lastTradeDateOrContractMonth} {contract.strike} {contract.right}"

                                # Guardar informacion relevante en base de datos dynamo
                                table_name = table_posiciones_abiertas
                                bd.create_item(table_name, {
                                    "conId": contract.conId,                                
                                    "ticker": contrato.symbol,
                                    "financial_instrument":financial_instrument,
                                    "cantidad": cantidad,
                                    "precio_entrada": None,
                                    "right":right,
                                    "stike_calculado": strike_calculado,
                                    "fecha_apertura": fecha_entrada,
                                    "fecha_registro": now,
                                    "inicio_ts": inicio_ts,
                                    "fecha_inicio_ts": None,
                                    "modo_entrada": 1, #1: bot
                                    "fecha_cierre": None
                                })
        
        if ticker_baja>0:
            #=== OBTENCION DE CASOS BAJISTAS===
            df_casos_baja = pd.DataFrame()
            df_casos_baja = ana_tecnico.obtener_casos(df, df_strike_pred_old, df_variable, ticker, "short", "BAJA")
            print("Casos BAJA:",df_casos_baja.shape[0])
            if df_casos_baja.shape[0]>0:
                print("Casos abiertos BAJA:",df_casos_baja[np.isnan(df_casos_baja["ExitTime"])].shape[0])
                df_casos_abiertos_baja = df_casos_baja[np.isnan(df_casos_baja["ExitTime"])]
                if (df_casos_abiertos_baja.shape[0]>0):
                    for i,row in df_casos_abiertos_baja.iterrows():
                        # Verificar si la fecha de entrada es de hoy
                        # Dejamos solo hasta la hora
                        dt1_hour = ny_time.replace(minute=0, second=0, microsecond=0)
                        dt2_hour = row["EntryTime"].replace(tzinfo=ny_tz).replace(minute=0, second=0, microsecond=0)         
                        #if (ny_time.date() == row["EntryTime"].date()): #HABILITAR DESPUES
                        print ("====== HORAS EVALUAR, hora1:", dt1_hour, ", hora2:", dt2_hour)
                        # Calcular diferencia
                        diff = (dt1_hour - dt2_hour).total_seconds() / 3600  # diferencia en horas
                        print ("DIFERENCIA HORAS:", diff)
                        if 0<dt1_hour.hour<=9:
                            hor_rango=6
                        else:
                            hor_rango=1

                        if 0 <= diff <= hor_rango: #HORAS MENOR A 5
                            print("===PASO HORAS===")
                            cantidad=1
                            precio = 0
                            right="P"
                            fecha_entrada = row["EntryTime"].strftime("%Y-%m-%d %H:%M:%S") 
                            print("fecha_entrada:", type(fecha_entrada), fecha_entrada)
                            #bd.registrar_orden(ticker, cantidad, precio, tipo, fecha_entrada)
                            
                            filtro = df_strike_pred_old.query("Ticker==@ticker and semana=='s1' and Tag=='short'")
                            mov_calculado =   np.float64(filtro.iloc[0]["strike_price_q3"])
                            print("----- Baja semana:", filtro.shape[0], ", dato:", mov_calculado, ", tipo:", type(mov_calculado))
                            strike_calculado = Decimal(str(mov_calculado))

                            
                            # Long PUT esperando -strike_calculado USD de movimientoo                    
                            order_put = ibkr.run_strategy(
                                symbol=ticker, 
                                side='PUT', 
                                expected_move=np.float64(strike_calculado), 
                                qty_contracts=1,
                                ip=ip,
                                port=port,
                                id_file=id_file,
                                inicio_ts=inicio_ts,
                                cant_trades=cant_trades,
                                precio_max_prima=precio_max_prima)
                            if order_put:   
                                print("====Datos de la posicion===")
                                print("entry_price_per_share:",order_put["entry_price_per_share"])
                                print("premium_total:",order_put["premium_total"])
                                print("estimated_total_cost:",order_put["estimated_total_cost"])
                                print("breakeven:",order_put["breakeven"])
                                #print("take_profit_price:",order_put["take_profit_price"])
                                #print("parent_orderId:",order_put["parent_orderId"])

                                contrat = Contract(order_put["contract"])
                                financial_instrument = f"{contract.symbol} {contract.lastTradeDateOrContractMonth} {contract.strike} {contract.right}"

                                # Guardar informacion relevante en base de datos dynamo
                                table_name = table_posiciones_abiertas
                                bd.create_item(table_name, {
                                    "conId": contrato.conId,
                                    "financial_instrument":financial_instrument,
                                    "ticker": ticker,
                                    "cantidad": cantidad,
                                    "precio_entrada": precio,
                                    "right": right,
                                    "stike_calculado": strike_calculado,
                                    "fecha_apertura": fecha_entrada,
                                    "fecha_registro": now,
                                    "inicio_ts": inicio_ts,
                                    "fecha_inicio_ts": None,
                                    "modo_entrada": 1, #1: bot
                                    "fecha_cierre": None
                                })
                

        # Detectar Cruces
        ## cma = Cruce_MA(df=df, tendencia_rapida=9, tendencia_lenta=21)
        # Detectar Casos a la ALZA

time.sleep(30)
#app.disconnect()
# Cancelar la suscripción
ib.cancelHistoricalData(bars)
ib.disconnect