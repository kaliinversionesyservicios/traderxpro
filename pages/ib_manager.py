from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from ib_insync import IB, MarketOrder, ExecutionFilter, Stock, util
import asyncio
import json
from datetime import datetime, timedelta
import math
import pandas as pd
import os
import numpy as np
from scipy.signal import argrelextrema
from decimal import Decimal
from fastapi.responses import JSONResponse
import ta as ta2
import boto3
from boto3.dynamodb.conditions import Key, Attr
import sys
import pytz
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from bot import script_crud as bd

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

# Ruta donde se guardará la configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # carpeta actual (pages)
ROOT_DIR = os.path.dirname(BASE_DIR)  # subimos un nivel (raíz del proyecto)
CONFIG_FILE = os.path.join(ROOT_DIR, "config_gestion_riesgo", "param.json")
CONFIG_FILE2 = os.path.join(ROOT_DIR, "config_gestion_riesgo", "config_riesgo.json")
market_data_cache = {}   # diccionario global, cache en memoria

user="carlosml0287" #CAMBIAR DE SER NECESARIO

def cargar_usuario():
    """Carga parametros de Usuario"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def cargar_config():
    """Carga configuracion de Usuario"""
    if os.path.exists(CONFIG_FILE2):
        with open(CONFIG_FILE2, "r") as f:
            return json.load(f)
    return None

usuarios = cargar_usuario()
config = cargar_config()

ip=""
port = 0
clientId = 9999
tipo_cuenta = config.get("tipo_cuenta")
inicio_ts = Decimal(config.get("inicio_ts"))
acceskey=""
secretaccess=""
# Tiempo mínimo entre lecturas reales de DynamoDB
REFRESH_INTERVAL = 900  # segundos, 15minutos

if user in usuarios:
    valores = usuarios[user]
    #print(f"Datos de {user}:")
    for clave, valor in valores.items():        
        if tipo_cuenta=="PAPER":
            if clave=="ip_paper":
                ip=valor
            if clave=="port_paper":
                port=valor
            if clave=="clientid_Dashpaper":
                clientId=valor
            if clave=="table_IBKR_Trades_paper":
                table_IBKR_Trades=valor
            if clave=="table_IBKR_Account_paper":
                table_IBKR_Account=valor
            table_posiciones_abiertas="posiciones_abiertas_paper"
        elif tipo_cuenta=="LIVE":
            if clave=="ip_live":
                ip=valor
            if clave=="port_live":
                port=valor
            if clave=="clientid_Dash":
                clientId=valor
            if clave=="table_IBKR_Trades_live":
                table_IBKR_Trades=valor
            if clave=="table_IBKR_Account_live":
                table_IBKR_Account=valor
            table_posiciones_abiertas="posiciones_abiertas"
        if clave=="aws_access_key_id":
            acceskey=valor
        if clave=="aws_secret_access_key":
            secretaccess=valor

        #print(f"{clave}: {valor}")
else:
    print("Usuario no encontrado")


#BASE DE DATOS DYNAMODB
dynamodb = boto3.resource("dynamodb", region_name="us-east-2",
                          endpoint_url="http://localhost:8000",  # URL DynamoDB local
                          aws_access_key_id=acceskey,
                          aws_secret_access_key=secretaccess
                          )
# Cache en memoria
cache_data = {"items": [], "last_update": None}

app = FastAPI()

async def get_data_from_dynamodb():
    """Consulta DynamoDB (ejemplo usando scan, pero mejor usar query)."""
    table = dynamodb.Table(table_IBKR_Trades)    
    response = table.scan()  # Ojo: scan es caro, mejor usar query
    return response.get("Items", [])

async def get_cached_data_dynamodb():
    """Devuelve datos de cache o actualiza si pasó REFRESH_INTERVAL."""
    global cache_data
    now = datetime.utcnow()

    if (
        cache_data["last_update"] is None
        or (now - cache_data["last_update"]).total_seconds() > REFRESH_INTERVAL
    ):
        print("🔄 Consultando DynamoDB...")
        items = await get_data_from_dynamodb()
        cache_data = {
            "items": items,
            "last_update": now,
        }
    else:
        print("⚡ Usando datos del cache...")

    return cache_data["items"]

async def get_posiciones_abiertas(conId: int):
    tabla = dynamodb.Table(table_posiciones_abiertas)  # usa el nombre real
    print("Tabla:", tabla.table_name)
    response = tabla.query(
        KeyConditionExpression=Key('conId').eq(conId)  # conId es NUMBER
    )
    
    items = response['Items']
    return items

# async def get_ibkr_trades(conId: int):
#     tabla = dynamodb.Table(table_IBKR_Trades)
#     # Query: filtra por la partition key (ej. "UserId") y aplica un filtro adicional
#     response = tabla.query(         
#         KeyConditionExpression=Key('conId').eq(conId) # obligatorio usar partition key
#     )
#     items = response['Items']
#     return items

# Permitir conexiones desde Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Conexión a IB
ib = IB()


@app.on_event("startup")
async def startup_event():
    await ib.connectAsync(ip, port, clientId=clientId)
    #await ib.connectAsync('3.13.179.45', 4002, clientId=801)
    #await ib.connectAsync('127.0.0.1', 4002, clientId=801)
    #await ib.connectAsync('127.0.0.1', 7497, clientId=801)

def clean_value(val):
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None  # 👈 o 0.0 si prefieres
    return val

def clean_dict(d):
    return {k: clean_value(v) for k, v in d.items()}

# ----------------------
# Endpoint HTTP: Posiciones abiertas
# ----------------------
@app.get("/positions")
async def get_positions():
    positions = ib.positions()
    results = []
    for p in positions:
        ticker = p.contract.symbol
        pos = p.position
        avg_cost = p.avgCost
        
        p.contract.exchange = "SMART"
        ticker_data = ib.reqMktData(p.contract, '', False, False)
        #ib.sleep(1) # esperar un segundo
        market_price = ticker_data.last if ticker_data.last else ticker_data.marketPrice()
        market_value = market_price * pos if market_price else 0
        
        pnl = (market_price - avg_cost) * pos if market_price else 0
        data={
            'ticker': ticker,
            'position': pos,
            'avgCost': avg_cost,
            'marketPrice': market_price,
            'marketValue': market_value,
            'pnl': pnl
        }

        results.append(clean_dict(data))
    return results

# @app.get("/positions")
# async def get_positions():
#     positions = ib.positions()
#     contracts = [p.contract for p in positions]
#     tickers = ib.reqTickers(*contracts)

#     data = []
#     for p, t in zip(positions, tickers):        
#         market_price = t.marketPrice()
#         if not market_price or math.isnan(market_price):
#             market_price = 0.0

#         pnl = (market_price - p.avgCost) * p.position if p.position else 0.0

#         data.append({
#             'ticker': p.contract.symbol,
#             'position': p.position,
#             'avgCost': p.avgCost,
#             'marketPrice': round(market_price, 2),
#             'pnl': round(pnl, 2)
#         })
#     return data


# ----------------------
# Endpoint HTTP: Trades históricos
# ----------------------
@app.get("/trades")
async def get_trades():
    # Forzar sincronización de órdenes y trades
    #ib.reqOpenOrders()
    #ib.reqAllOpenOrders()
    #ib.reqCompletedOrders(apiOnly=False)
    #ib.sleep(1)  # darle un respiro para actualizar

    # Pedir a IBKR todas las órdenes completadas (no solo las locales)
    await ib.reqCompletedOrdersAsync(apiOnly=False)

    trades = ib.trades()    
    #print("=== TRADES BACK ===")
    #print("hito1 cantidad TRADES:", len(trades))
    #print(trades)
    data1 = []
    for t in trades:
        for fill in t.fills:      
            #if t.orderStatus.status in ['Filled', 'Submitted', 'Cancelled']:
            financial_instrument = f"{t.contract.symbol} {t.contract.lastTradeDateOrContractMonth} {t.contract.strike} {t.contract.right}"
            #filled = t.orderStatus.filled
            #price = t.orderStatus.avgFillPrice
            #status = t.orderStatus.status
            #side = t.order.action
            
            data1.append({
                'financial_instrument': financial_instrument,
                'dateTime':fill.execution.time,
                'side': fill.execution.side,
                'action': t.order.action,
                'filledQuantity': t.order.filledQuantity,
                'price': fill.execution.price,
                'Exch.': fill.execution.exchange,
                'Exch2.': t.contract.exchange,
                'secType': t.contract.secType,
                'last Trading Day':t.contract.lastTradeDateOrContractMonth,
                'strike': t.contract.strike,
                'Put/Call':t.contract.right,
                'comission':fill.commissionReport.commission,
                'Rlzd P&L':fill.commissionReport.realizedPNL,
                'conId':t.contract.conId
            })

    print("cantidad final:",len(data1))
    return data1

# ----------------------
# Endpoint HTTP: Portfolio
# ----------------------
@app.get("/portfolio")
async def get_portfolio():
    portfolio = ib.portfolio()
    items = await get_cached_data_dynamodb()
    trades_data = await get_trades()

   
    #print("hito1 cantidad portafolo:", len(portfolio))
    #print (portfolio)
    data2 = []
    for p in portfolio:
        # PnL en USD
        qty = p.position
        pnl = (p.marketValue - p.averageCost) * qty if p.marketValue else 0
        # Porcentaje de PnL
        pnl_pct = (pnl / (p.averageCost * qty)) * 100 if p.averageCost and qty != 0 else 0
        financial_instrument = f"{p.contract.symbol} {p.contract.lastTradeDateOrContractMonth} {p.contract.strike} {p.contract.right}"

        print("===REVISION DE FECHAS===")
        id = p.contract.conId
        count=0
        dateTime = None
        for indice2, trade in enumerate(items):
            id2 = trade["conid"]
            if id==id2:
                count=count+1
                print("entro flex:", count)
                dateTime =  pd.to_datetime(trade["dateTime"], format="%d/%m/%Y;%H:%M:%S")

        if count==0:
            for indice3, trade3 in enumerate(trades_data):
                id3=trade3["conId"]
                if id==id3:
                    count=count+1
                    print("entro trade:", count)
                    #La infomacion esta en en zona horaria UTC, la convertiremos a zona horaria New York                
                    ts=pd.to_datetime(trade3["dateTime"])
                    ny_time = ts.tz_convert('America/New_York')
                    # Quitar la zona horaria
                    ny_naive = ny_time.tz_localize(None)
                    dateTime = ny_naive
        inicio_ts=0

        trades_dynamo = await get_posiciones_abiertas(id)
        if len(trades_dynamo)>0:
                    inicio_ts=trades_dynamo[0]["inicio_ts"]

        data2.append({
            "conId": id,
            "Symbol": p.contract.symbol,
            "Financial Instrument":financial_instrument,
            "Position": p.position,
            "Cost basis": p.averageCost,
            "Market Value": p.marketValue,
            "strike": p.contract.strike,
            "right": p.contract.right,
            #"Market Price": p.marketPrice,
            #"Avg Cost": p.averageCost,
            "Unrealized PnL": p.unrealizedPNL,
            "Realized PnL": p.realizedPNL,
            "Total PnL":round(pnl,2),
            "% PnL":round(pnl_pct,2),
            "dateTime":dateTime,
            "inicio_ts": inicio_ts
        })
    return data2

# ----------------------
# Endpoint HTTP: Order
# ----------------------
@app.get("/order")
async def get_order():
    # Forzar a traer todas las órdenes abiertas
    await ib.reqAllOpenOrdersAsync()
    
    orders = ib.openOrders()

    print(orders)
    
    data3 = []
    for o in orders:
        data3.append({
            "permId":o.permId,            
            "orderType":o.orderType,
            "action":o.action,
            "totalQuantity":o.totalQuantity,
            "lmtPrice":o.lmtPrice,
            "tif":o.tif
        })
    return data3

# ----------------------
# Endpoint HTTP: AllOrder
# ----------------------
# @app.get("/allorder")
# async def get_allorder():
#     allorder = ib.reqAllOpenOrders()
#     data = []
#     for o in allorder:
#         data.append({
#             "orderId":o.orderId,            
#             "orderType":o.orderType,
#             "action":o.action,
#             "totalQuantity":o.totalQuantity,
#             "lmtPrice":o.lmtPrice,
#             "tif":o.tif
#         })
#     return data

# ----------------------
# Endpoint HTTP: Summary
# ----------------------
@app.get("/summary")
async def get_trade_summary():
    trades = ib.trades()
    rows = []
    summary = []

    if len(trades)>0:
        for t in trades:
            for fill in t.fills:
                financial_instrument = f"{t.contract.symbol} {t.contract.lastTradeDateOrContractMonth} {t.contract.strike} {t.contract.right}"
                rows.append({
                    'Financial Instrument': financial_instrument,
                    'symbol': t.contract.symbol,
                    'action': fill.execution.side,   # BOT o SLD
                    'qty': fill.execution.shares,
                    'price': fill.execution.price,
                    'comission':fill.commissionReport.commission,
                    'realizedPNL':fill.commissionReport.realizedPNL
                })

        if not rows:
            return []

        df = pd.DataFrame(rows)

        
        for fin_instr, group in df.groupby('Financial Instrument'):
            buys = group[group['action'] == 'BOT']
            sells = group[group['action'] == 'SLD']

            pos = buys['qty'].sum() - sells['qty'].sum()
            avg_bot = (buys['qty'] * buys['price']).sum() / buys['qty'].sum() if not buys.empty else 0
            avg_sld = (sells['qty'] * sells['price']).sum() / sells['qty'].sum() if not sells.empty else 0
            com = buys['comission'].sum() + sells['comission'].sum()
            realizedPNL = buys['realizedPNL'].sum() + sells['realizedPNL'].sum()
            #realized_pnl = (sells['qty'] * (sells['price'] - avg_bot)).sum() - com if not sells.empty else 0

            summary.append({
                'Financial Instrument': fin_instr,
                'Pos': pos,
                'Buys': buys['qty'].sum(),
                'Sells': sells['qty'].sum(),
                'Net': pos,
                'Avg(BOT)': round(avg_bot, 2),
                'Avg(SLD)': round(avg_sld, 2),
                'commision': com,
                'Realized P&L': round(realizedPNL, 2)
            })

    return summary

# ----------------------
# Endpoint HTTP: Account Summary
# ----------------------
@app.get("/accountSummary")
async def get_account_summary():
    accountSummary = await ib.accountSummaryAsync()
    data4 = []
    for a in accountSummary:
        data4.append({
            "account":a.account,            
            "tag":a.tag,
            "value":a.value,
            "currency":a.currency

        })
    return data4

async def stream_data(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            positions = await get_positions()
            trades = await get_trades()
            portfolio = await get_portfolio()
            order = await get_order()
            summary = await get_trade_summary()            
            # Aquí se usan datos del cache
            
            data = market_data_cache
            #allorder = await get_allorder()
            message = json.dumps({
                'positions': positions,
                'trades': trades,
                'portfolio': portfolio,
                'order': order,
                'summary':summary,
                'data': data
                #'allorder':allorder
            })
            await websocket.send_text(message)
            await asyncio.sleep(30)  # actualizar cada 1 segundo
    except Exception as e:
        print(f"WebSocket closed: {e}")
    finally:
        await websocket.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await stream_data(websocket)

# Endpoint para cerrar posición
@app.post("/close_position/{conId}")
async def close_position(conId: int):
    positions = ib.positions()
    pos = [p for p in positions if p.contract.conId == conId]
    if pos:
        position = pos[0].position
        action = 'SELL' if position > 0 else 'BUY'
        order = MarketOrder(action, abs(position))
        print("orderId:",order.orderId)
        ib.placeOrder(pos[0].contract, order)
        return {"status": "ok", "message": f"Orden enviada para cerrar {conId}"}
    return {"status": "error", "message": "Ticker no encontrado"}

# Endpoint obtener datos
@app.get("/datamkt/{ticker}")
async def get_data(ticker: str):
    contract = Stock(ticker, 'SMART', 'USD')
    bars = await ib.reqHistoricalDataAsync(
    contract=contract,
    endDateTime="",
    durationStr='10 D',
    barSizeSetting='1 hour',
    whatToShow='TRADES',
    useRTH=0,
    formatDate=1,
    keepUpToDate=False,
    chartOptions=[]
    )
    
    #return bars
    df = util.df(bars)
    df["date"] = df["date"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df.to_dict(orient="records")  # porque FastAPI no puede devolver DataFrames directo

# Endpoint obtener datos total
@app.get("/alldatamkt")
async def get_data_all():
    df_total = pd.DataFrame()
    portfolios = await get_portfolio()
    print("PORTAFOLIO:", len(portfolios))
    #Lista distinta de tickets
    tickers = list({item["Symbol"] for item in portfolios})
    #Revisar si todos los casos abiertos estan guardados en el dynamo
    #now = datetime.utcnow()
    # Zona horaria New York
    ny_tz = pytz.timezone("America/New_York")
    # Hora actual en New York
    now_ny = datetime.now(ny_tz)
    # Formatear
    now_ny_str = now_ny.strftime("%d-%m-%Y %H:%M:%S")

    for portfolio in portfolios:
        conId = int(portfolio["conId"])
        print("Consultando con conId:", conId, type(conId))
        trades_dynamo = await get_posiciones_abiertas(conId)
        print(len(trades_dynamo))
        if len(trades_dynamo)==0:
            # Guardar informacion relevante en base de datos dynamo
            bd.create_item(table_posiciones_abiertas, {
                "conId": portfolio["conId"],
                "financial_instrument":portfolio["Financial Instrument"],
                "ticker": portfolio["Symbol"],
                "cantidad": 1,
                "precio_entrada": None,
                "right": portfolio["right"],
                "stike_calculado": None,
                "fecha_apertura": None,
                "fecha_registro": now_ny_str, 
                "inicio_ts": inicio_ts,
                "fecha_inicio_ts": None,
                "modo_entrada": 2, #2: Registro Manual
                "fecha_cierre": None
            })
        

    for ticker in tickers:
        print("TICKER:", ticker)
        contract = Stock(ticker, 'SMART', 'USD')
        bars = await ib.reqHistoricalDataAsync(
        contract=contract,
        endDateTime="",
        durationStr='13 D',
        barSizeSetting='1 hour',
        whatToShow='TRADES',
        useRTH=0,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[]
        )
       
        #return bars
        df_datamkt = util.df(bars)
        df_datamkt["date"] = df_datamkt["date"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        df_datamkt["ticker"]=ticker

        df_datamkt.sort_values(by=['date'])
        #EMAS
        filtro = df_variable.query("Ticker==@ticker and Tag=='long'")
        if filtro.shape[0]>0:
            periodoCorto1 = filtro.iloc[0]["periodoCorto"]
            periodoLargo1 = filtro.iloc[0]["periodoLargo"]
        else:
            periodoCorto1 = 20
            periodoLargo1 = 40

        filtro = df_variable.query("Ticker==@ticker and Tag=='short'")
        if filtro.shape[0]>0:
            periodoCorto2 = filtro.iloc[0]["periodoCorto"]
            periodoLargo2 = filtro.iloc[0]["periodoLargo"]
        else:
            periodoCorto2 = 20
            periodoLargo2 = 40

        #company = df_datamkt.query("companyName==@ticker").copy()
        df_datamkt.sort_values(by=['date'])

        df_datamkt['EMACorta'] = df_datamkt['low'].ewm(span=periodoCorto1, adjust=False).mean()
        df_datamkt.dropna(inplace=False)
        df_datamkt['EMALarga'] = df_datamkt['low'].ewm(span=periodoLargo1, adjust=False).mean()
        df_datamkt.dropna(inplace=False)

        df_datamkt['EMACorta2'] = df_datamkt['high'].ewm(span=periodoCorto2, adjust=False).mean()
        df_datamkt.dropna(inplace=False)
        df_datamkt['EMALarga2'] = df_datamkt['high'].ewm(span=periodoLargo2, adjust=False).mean()
        df_datamkt.dropna(inplace=False)
        # fin EMAS

         #ATR indicador para Trailing Stop Loss
        df_datamkt['ATR'] = ta2.volatility.average_true_range(df_datamkt['high'], df_datamkt['low'], df_datamkt['close'], window=14)        

        #PIVOTS
        orders = [20,10,7]
        for ord in orders:
            max_idx = argrelextrema(df_datamkt['high'].values, np.greater, order=ord)[0]
            min_idx = argrelextrema(df_datamkt['low'].values, np.less, order=ord)[0]
            # Aplicar el cálculo solo a los índices en la lista
            df_datamkt.loc[df_datamkt.index[max_idx], 'pivotHigh'] =df_datamkt['high']+1e-3
            df_datamkt.loc[df_datamkt.index[min_idx], 'pivotLow'] = df_datamkt['low']-(1e-3)
            df_datamkt.loc[df_datamkt.index[max_idx], 'isPivot'] = 1
            df_datamkt.loc[df_datamkt.index[min_idx], 'isPivot'] = 2

        #TRAILING STOP
        #Generar Trailing Stop con ATR
        atr_mult_sl_1 = 1.2
        atr_mult_tp = 5
        entry_price = trailing_stop = None
      
        #pricenow = df_datamkt["close"].iloc[-1]
        df_datamkt['date'] = pd.to_datetime(df_datamkt.date)
        for portfolio in portfolios:

            if (ticker==portfolio["Symbol"]):
                cnt_cerrar=0
                fechaEvaluar = pd.to_datetime(portfolio["dateTime"])
                df_datamkt["inicioTrade"] = np.where(df_datamkt["date"].dt.floor("h") == fechaEvaluar.floor("h"),  1, 0)
                indiceIni = df_datamkt.index[df_datamkt["inicioTrade"] == 1][0]
                df3 = (df_datamkt.query("index>=@indiceIni")).copy()
                right = portfolio["right"]
                conId = portfolio["conId"]
                tipo_stop = 1 #STOP LOSS ESTATICO
                por_profit = portfolio["% PnL"]                
                trailing_stop = None  # inicial
                df_datamkt['trailing_stop'] = None
               
                if por_profit>=inicio_ts: #ACTIVAR Trailing Stop
                    trades_dynamo = await get_posiciones_abiertas(conId)
                    if len(trades_dynamo)>0:
                        for item in trades_dynamo:
                            # Obtener la PK del item
                            key ={
                                'conId': int(item['conId'])
                            }
                            update_expression= "SET fecha_inicio_ts = :new_fec"

                            expression_values={
                                ':new_fec': now_ny_str
                            }
                            bd.update_item(table_posiciones_abiertas, key,update_expression, expression_values)

                    
                #if por_profit>=0: #ACTIVAR Trailing Stop
                    #Obtener Salida utilizando Trailing Stop ATR
                    for k, row3 in df3.iterrows():
                        price = df_datamkt.loc[k, 'close']
                        atr = df_datamkt.loc[k, 'ATR']
                        if right=="C":
                            new_stop = price - atr_mult_sl_1 * atr
                            if trailing_stop is None:
                                trailing_stop = new_stop
                            else:
                                trailing_stop = max(trailing_stop, new_stop)

                            # Salida de la operación (long example)
                            if price <= trailing_stop:                        
                                cnt_cerrar = cnt_cerrar + 1
                        
                        elif right=="P":
                            new_stop = price + atr_mult_sl_1 * atr
                            if trailing_stop is None:
                                trailing_stop = new_stop
                            else:
                                trailing_stop = min(trailing_stop, new_stop)
                            # Salida de la operación (short example)
                            if price >= trailing_stop:
                                cnt_cerrar = cnt_cerrar + 1
                            
                            
                        #print("k:",k,",trailing_stop:", trailing_stop)
                        df_datamkt.loc[k, 'trailing_stop'] = trailing_stop
                

                if cnt_cerrar>0:
                    print("❌ Stop alcanzado, cerrando posición")
                    try:
                        #mensaje_cierre= await close_position(conId)
                        #print(f"cerrar:{ticker} - {conId}: {mensaje_cierre}")
                        print(f"Debe cerrar:{ticker} - {conId}")
                    except (ValueError, TypeError) as e:
                        print("Error:", e)
                

        #     elif right=="P":
        df_datamkt["date"] = df_datamkt["date"].dt.strftime("%Y-%m-%dT%H:%M:%S") #volver a cambiar tipo de dato por el JSON
        print("df_datamkt:", df_datamkt.shape[0])

        print(df_datamkt[["date","close","ATR","close","open","low","high","trailing_stop"]].tail(40))

        if df_total.shape[0]<=0:
            df_total = df_datamkt
        else:
            df_total = pd.concat([df_total,df_datamkt], ignore_index=True)

        df_total = df_total.replace([np.inf, -np.inf], np.nan)
        df_total = df_total.where(pd.notnull(df_total), None)
        data = df_total.astype(object).where(pd.notnull(df_total), None).to_dict(orient="records")
    #return df_total.to_dict(orient="records")  # porque FastAPI no puede devolver DataFrames directo
    return JSONResponse(content=data)


@app.on_event("startup")
async def start_background_listener():
    asyncio.create_task(update_market_data())

async def update_market_data():
    global market_data_cache
    while True:
        try:
            df = await get_data_all()  # tu misma función que genera el DF
            market_data_cache = df     # guardas en memoria
            print("✅ Market data actualizado")
        except Exception as e:
            print(f"Error actualizando datos: {e}")
        await asyncio.sleep(30)  # actualiza cada 10s (o lo que necesites)