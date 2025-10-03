from ib_insync import *
import math
from datetime import datetime, timezone, date
import os
import json
import decimal as Decimal

# === Configuración ===
#IB_HOST = '127.0.0.1'
IB_CLIENT_ID = 502


#path_folder="/mnt/efs" #Produccion
# path_folder="D:/traderxpro/" #Desarrollo
path_folder="/mnt/efs"


MAX_DAYS_TO_EXPIRY = 8
TAKE_PROFIT_MULT = 1.75   # 75% profit
ESTIMATED_FEES_PER_CONTRACT = 1.00  # ajusta según tu cuenta/mercado
USE_MID_PRICE = True      # True: usar mid, False: usar last/ask

# ===== Helpers =====

def connect_ib(ip,port):
    ib = IB()
    ib.connect(ip, port, clientId=IB_CLIENT_ID)
    ib.reqMarketDataType(1)  # 1=live, 2=frozen, 3=delayed, 4=delayed-frozen
    return ib

def get_spot_price(ib: IB, symbol: str) -> float:
    stk = Stock(symbol, 'SMART', 'USD')
    ib.qualifyContracts(stk)
    ticker = ib.reqMktData(stk, '', False, False)
    ib.sleep(1.0)
    price = ticker.last or ticker.close or ticker.marketPrice()
    if not price or math.isnan(price):
        # fallback a midpoint si existiera
        bid, ask = ticker.bid, ticker.ask
        if bid and ask:
            price = (bid + ask) / 2
    if not price or math.isnan(price):
        raise RuntimeError(f"No se pudo obtener precio spot de {symbol}")
    return float(price)

def nearest_strikes(strikes, target, tol):
    # filtra strikes dentro de ±tol del objetivo
    return sorted([s for s in strikes if abs(float(s) - target) <= tol],
                  key=lambda x: abs(float(x) - target))

def expirations_within(expirations, max_days=7):
    out = []
    today = datetime.now(timezone.utc).date()
    for e in expirations:
        # IB devuelve 'YYYYMMDD' (a veces con HHMM); tomamos primeros 8
        d = datetime.strptime(e[:8], "%Y%m%d").date()
        if (d - today).days >= 0 and (d - today).days <= max_days:
            out.append(e)
    return sorted(out)

def option_mid_or_last(t: Ticker):
    bid, ask, last = t.bid, t.ask, t.last
    if USE_MID_PRICE and bid and ask:
        return (bid + ask) / 2
    # fallbacks
    for v in [last, ask, bid]:
        if v and not math.isnan(v):
            return float(v)
    return None

def pick_option_contract(ib: IB, symbol: str, side: str, expected_move: float,precio_max_prima:float):
    """
    side: 'CALL' o 'PUT'
    expected_move: cuánto esperas que suba/baje el subyacente (en USD)
    """
    side = side.upper()
    if side not in ('CALL', 'PUT'):
        raise ValueError("side debe ser 'CALL' o 'PUT'")

    # 1) spot y strike objetivo
    print("pick_option_contract h1")
    spot = get_spot_price(ib, symbol)
    strike_obj = spot + expected_move if side == 'CALL' else spot - expected_move

    # 2) parámetros de opciones
    print("pick_option_contract h2")
    stk = Stock(symbol, 'SMART', 'USD')
    ib.qualifyContracts(stk)
    params = ib.reqSecDefOptParams(symbol, '', 'STK', stk.conId)
    if not params:
        raise RuntimeError("No se pudo obtener parámetros de opciones")

    # Tomamos el primer set para SMART (u otro si corresponde)
    p = next((x for x in params if x.exchange == 'SMART'), params[0])
    expirations = expirations_within(p.expirations, MAX_DAYS_TO_EXPIRY)
    if not expirations:
        #raise RuntimeError("No hay expiraciones ≤ 7 días")
        print("No hay expiraciones ≤ 8 días")

    # 3) armar candidatos (±1 del strike objetivo)
    print("pick_option_contract h3")
    strike_list = list(map(float, p.strikes))
    mult = 1.5 * expected_move
    nearby = nearest_strikes(strike_list, strike_obj, mult)
    if not nearby:
        #raise RuntimeError(f"Sin strikes dentro de ± {mult} de {strike_obj:.2f}")
        print(f"Sin strikes dentro de ± {mult} de {strike_obj:.2f}")
    
    print("pick_option_contract h4")

    right = 'C' if side == 'CALL' else 'P'
    candidates = []
    for exp in expirations:
        for s in nearby:
            try:
                opt = Option(symbol, lastTradeDateOrContractMonth=exp, strike=float(s), right=right, exchange='SMART', currency='USD')            
                val_contract = ib.qualifyContracts(opt)
                if not val_contract:
                    print("===> Contrato no encontrado en IB")
                    print("symbol:", symbol)
                    print("exp:", exp)
                    print("s:", s)
                    print("right:", right)
                else:
                    candidates.append(opt)
            except Exception as e:
                print("ERRORR:", e)
                continue

    #if not candidates:
    #    raise RuntimeError("No se pudieron calificar contratos candidatos")
    
    print("pick_option_contract h5")
    if candidates:
        # 4) cotizar candidatos y filtrar por prima <= $250
        tickers = ib.reqTickers(*candidates)
        valid = []
        for opt, tik in zip(candidates, tickers):
            px = option_mid_or_last(tik)
            if not px: 
                continue
            mult = int(opt.multiplier or 100)
            premium_total = px * mult
            if premium_total <= precio_max_prima:
                valid.append((opt, px, premium_total))

        if not valid:
            print (f"No hay contratos con prima ≤ {precio_max_prima} USD en la ventana")
            #raise RuntimeError("No hay contratos con prima ≤ 200 USD en la ventana")

        # 5) elegir el más caro (pero ≤ 250)
        if valid:
            print ("Si paso validaciones")
            chosen = max(valid, key=lambda row: row[2])  # por premium_total
            contract, entry_price_per_share, premium_total = chosen

            return {
                "contract": contract,
                "spot": spot,
                "strike_objetivo": strike_obj,
                "entry_price_per_share": entry_price_per_share,
                "premium_total": premium_total,
                "multiplier": int(contract.multiplier or 100)
            }
        else:
            print ("No paso validaciones")
            return {}
    else:
        print ("No hay opciones candidatos")
        return {}
        

def place_with_take_profit(ib: IB, contract: Contract, qty: int,
                           entry_price_per_share: float, tp_mult=1.75):
    """
    Coloca BUY 
    """
    # Parent BUY
    #parent = LimitOrder('BUY', qty, entry_price_per_share, tif='GTC', transmit=False)
    parent = MarketOrder('BUY', qty, transmit=True)
    
    #Enviar orden buy
    trade_parent = ib.placeOrder(contract, parent)
  
    ib.sleep(1)
    ib.waitOnUpdate()
    return trade_parent

def place_with_take_profit_old(ib: IB, contract: Contract, qty: int,
                           entry_price_per_share: float, tp_mult=1.75):
    """
    Coloca BUY LMT como orden padre y SELL LMT (TP) como hijo.
    """
    # Parent BUY
    #parent = LimitOrder('BUY', qty, entry_price_per_share, tif='GTC', transmit=False)
    parent = MarketOrder('BUY', qty, transmit=True)
    parent.orderRef = 'parent_buy'
    
    # Take Profit SELL
    tp_price = round(entry_price_per_share * tp_mult, 2)
    child = LimitOrder('SELL', qty, tp_price, tif='GTC', transmit=True) # última transmit=True
    child.parentId = parent.orderId
    child.orderRef = 'tp_75'        
    
    #Enviar ambas ordenes
    trade_parent = ib.placeOrder(contract, parent)
    trade_tp = ib.placeOrder(contract, child)
    
    #if trade_parent.OrderStatus.status == 'Filled':   
    ib.sleep(1)
    ib.waitOnUpdate()
    return trade_parent, trade_tp, tp_price


def breakeven(side: str, strike: float, premium_per_share: float) -> float:
    if side.upper() == 'CALL':
        return round(strike + premium_per_share, 2)
    else:
        return round(strike - premium_per_share, 2)
    
def positions_open(ib: IB, symbol, side):    
    cant = 0
    if side=="CALL":
        right = "C"
    elif side=="PUT":
        right = "P"

    # Obtener posiciones abiertas
    positions = ib.positions()
    for pos in positions:
        con = pos.contract       # contrato (Option, Stock, etc.)
        position = pos.position  # cantidad (int)
        #avgCost = pos.avgCost    # costo promedio (float)
        if isinstance(con, Option):
            if (con.symbol == symbol and
                con.right == right and 
                position != 0):
                    cant=cant+1    
    return cant

def positions_open_day(ib: IB):
    trades = ib.trades()
    hoy =date.today()
    # Ejecuciones del día
    trades_hoy = [
        t for t in trades 
        if any(log.time.date() == hoy for log in t.log)
        ]
    symbols_hoy = {t.contract.symbol for t in trades_hoy}
    cant = len(symbols_hoy)
    return cant

# ===== Ejecución end-to-end =====

def run_strategy(symbol: str, side: str, expected_move: float, qty_contracts: int = 1,ip:str="3.3.3.3",port:int=0,id_file:str="default",inicio_ts:float=0.0,cant_trades=0,precio_max_prima:float=0.0):
    """
    symbol: subyacente (ej. 'AAPL')
    side: 'CALL' o 'PUT'
    expected_move: movimiento esperado en USD para calcular strike objetivo
    qty_contracts: cantidad de contratos a comprar (cada contrato suele ser 100 acciones)
    """
    ib = connect_ib(ip,port)
    try:
        print("carlos h1 run_strategy")

        #Revisar si hay trade abierto mismo symbol y right --> es decir por ejemplo SPY - CALL, no abrira posiciones con el mismo symbol y right
        cant_pos = positions_open(ib, symbol, side)
        cant_pos_day = positions_open_day(ib)


#config_prev = cargar_configuracion_riesgo()
#inicio_ts = config_prev.get("inicio_ts")
#inv_sesion = config_prev.get("inv_sesion")
#precio_max_prima = config_prev.get("precio_max_prima")
#cant_trades = config_prev.get("cant_trades")

        if cant_pos==0 & cant_pos_day<=cant_trades:
            choice = pick_option_contract(ib, symbol, side, expected_move,precio_max_prima)
            print("carlos h2 run_estrategy")
            if choice:
                c = choice["contract"]
                entry_px = choice["entry_price_per_share"]
                mult = choice["multiplier"]

                # Métricas
                premium_total = entry_px * mult * qty_contracts
                est_fees = ESTIMATED_FEES_PER_CONTRACT * qty_contracts
                est_cost_total = round(premium_total + est_fees, 2)
                be = breakeven(side, c.strike, entry_px)

                print(f"\n=== Selección ===")
                print(f"Subyacente: {symbol}  Spot: {choice['spot']:.2f}")
                print(f"Lado: {side}  Strike objetivo: {choice['strike_objetivo']:.2f}")
                print(f"Contrato elegido: {c.localSymbol}  Exp: {c.lastTradeDateOrContractMonth} Strike: {c.strike} Right: {c.right}")
                print(f"Precio entrada/opción (por acción): {entry_px:.2f}")
                print(f"Premium total: ${premium_total:.2f}  (mult={mult}, qty={qty_contracts})")
                print(f"Coste estimado total (incl. fees ~${ESTIMATED_FEES_PER_CONTRACT:.2f}/contr): ${est_cost_total:.2f}")
                print(f"Breakeven: ${be:.2f}\n")

                # Orden + Take Profit 75%
                #trade_parent, trade_tp, tp_price = place_with_take_profit(
                #    ib, c, qty_contracts, entry_px, TAKE_PROFIT_MULT
                #)

                #Trade buy simple, sin take profit ni limit
                trade_parent = place_with_take_profit(
                    ib, c, qty_contracts, entry_px, TAKE_PROFIT_MULT
                )
                
                print ("STATUS orden:", trade_parent.orderStatus.status)
                if trade_parent.orderStatus.status=="Filled":
                    print(f"Orden BUY enviada (parentId={trade_parent.order.orderId})")
                    #print(f"Take Profit SELL LMT @ {tp_price} colocado (child of {trade_parent.order.orderId})")

                    return {
                        "contract": c,
                        "entry_price_per_share": entry_px,
                        "premium_total": premium_total,
                        "estimated_total_cost": est_cost_total,
                        "breakeven": be,
                        "trailing_stop": inicio_ts,
                        "orderId": trade_parent.order.orderId
                    }
                else:
                    return {}
            else:
                return {}
        else:
            return {}
    finally:
        # Mantén la conexión abierta si deseas gestionar fills en vivo;
        # si no, puedes desconectar.
        ib.disconnect()
