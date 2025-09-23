from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from ib_insync import IB, MarketOrder, ExecutionFilter, Stock, util
import asyncio
import json
from datetime import datetime, timedelta
import math
import pandas as pd
import os


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

if user in usuarios:
    valores = usuarios[user]
    #print(f"Datos de {user}:")
    for clave, valor in valores.items():        
        if tipo_cuenta=="PAPER":
            if clave=="ip_paper":
                ip=valor
            if clave=="port_paper":
                port=valor
            if clave=="clientid_Dash":
                clientId=valor
        elif tipo_cuenta=="LIVE":
            if clave=="ip_live":
                ip=valor
            if clave=="port_live":
                port=valor
            if clave=="clientid_Dash":
                clientId=valor

        #print(f"{clave}: {valor}")
else:
    print("Usuario no encontrado")

app = FastAPI()

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
    print("=== TRADES BACK ===")
    print("hito1 cantidad TRADES:", len(trades))
    print(trades)
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

        data2.append({
            "conId": p.contract.conId,
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
            "% PnL":round(pnl_pct,2)
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
            data = await get_data("SPY")
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
            await asyncio.sleep(1)  # actualizar cada 1 segundo
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