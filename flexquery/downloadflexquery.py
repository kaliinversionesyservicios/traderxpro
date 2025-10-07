import requests
import boto3
import xmltodict
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal
import os
import json
import sys
import time

#Parametros a recibir
user = str(sys.argv[1])
param_cuenta=int(sys.argv[2]) #0 paper 1 live
#user="carlosml0287" #configurar

#variables globales
#path_folder="/mnt/efs" #Produccion
#path_folder="/bot_aws" #Desarrollo Linder
path_folder="/traderxpro" #Desarrollo Carlos

#PRODUCCION
CONFIG_FILE  = f"{path_folder}/config_gestion_riesgo/param.json"

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
if usuarios is None:
    print("Error: No se pudo cargar el archivo de configuración.")
    sys.exit(1)  # Termina el programa con un código de error 1

if user not in usuarios:
    print(f"Error: El usuario '{user}' no se encontró en el archivo de configuración.")
    sys.exit(1)  # Termina el programa con un código de error 1

user_data = usuarios[user]
id_folder=user_data.get("account_idpaper") #solo exite una sola carpeta de mi folder de config_riesgo.json

#verificamos que cuenta es
if param_cuenta==0:
    tipo_cuenta="PAPER"
    id_cuenta=user_data.get("account_idpaper")
    print(f"Usuario: {user} - Cuenta seleccionada: {id_cuenta} PAPER - con folder: {id_folder}")
elif param_cuenta==1:
    tipo_cuenta="LIVE"
    id_cuenta=user_data.get("account_idlive")
    print(f"Usuario: {user} - Cuenta seleccionada: {id_cuenta} LIVE - con folder: {id_folder}")

CONFIG_FILE2 = f"{path_folder}/config_gestion_riesgo/config_{id_folder}/config_riesgo.json"

config = cargar_config()
print("FOLDER: ",CONFIG_FILE2)
print("configuracion leida: ",config)
#--------------------------
# ASIGNACION DE VARIABLES
#----------------------------
if tipo_cuenta=="PAPER":
    print("El tipo de cuenta es paper")
    table_IBKR_Trades=user_data.get("table_IBKR_Trades_paper")
    table_IBKR_Account=user_data.get("table_IBKR_Account_paper")
    TOKEN=user_data.get("token_flexquery_paper")
    QUERY_ID=user_data.get("id_flexquery_paper")
else: 
    table_IBKR_Trades=user_data.get("table_IBKR_Trades_live")
    table_IBKR_Account=user_data.get("table_IBKR_Account_live")
    print("EL TIPO DE CUENTA ES LIVE")
    TOKEN=user_data.get("token_flexquery_live")
    QUERY_ID=user_data.get("id_flexquery_live")
acceskey=user_data.get("aws_access_key_id")
secretaccess=user_data.get("aws_secret_access_key")

print(f"table_IBKR_Trades: {table_IBKR_Trades}")
print(f"table_IBKR_Account: {table_IBKR_Account}")
print(f"AWS Access Key: {acceskey}")
print(f"AWS Secret Access Key: {secretaccess}")
print(f"Token FlexQuery: {TOKEN}")
print(f"Query ID: {QUERY_ID}")

table_name = table_IBKR_Trades
table_nameAccount = table_IBKR_Account


# === DynamoDB produccion===
#dynamodb = boto3.resource("dynamodb-admin", region_name="us-east-1")


# ====== CONFIG DYNAMODB LOCAL ======
dynamodb = boto3.resource(
    "dynamodb",
    #region_name="us-west-2",  # región dummy para local
    endpoint_url="http://localhost:8000",  # URL DynamoDB local
    region_name="us-east-2",  # región produccion
    aws_access_key_id=acceskey,
    aws_secret_access_key=secretaccess
)

# Crear tabla si no existe
def create_table():
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "tradeID", "KeyType": "HASH"}],  # PK
            AttributeDefinitions=[{"AttributeName": "tradeID", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✅ Tabla {table_name} creada en DynamoDB")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"⚠️ La tabla {table_name} ya existe")
        else:
            raise

# Crear tabla account
def create_tableAccount():
    try:
        table = dynamodb.create_table(
            TableName=table_nameAccount,
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],  # PK
            AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
    except ClientError as e:
        print(f"✅ Tabla creada {table_nameAccount} en DynamoDB")
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"⚠️ La tabla {table_nameAccount} ya existe")
        else:
            raise

# Obtener Reference Code
# def get_reference_code():
#     url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest?t={TOKEN}&q={QUERY_ID}&v=3"
#     resp = requests.get(url)
#     resp.raise_for_status()
#     data = xmltodict.parse(resp.text)
#     return data["FlexStatementResponse"]["ReferenceCode"]

# Obtener data
# def get_data():
#     ref_code = get_reference_code()
#     url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement?q={ref_code}&t={TOKEN}&v=3"
#     resp = requests.get(url)
#     resp.raise_for_status()
#     return resp

def fetch_account():
    #OBTENCION DE REFERENCE CODE 
    url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest?t={TOKEN}&q={QUERY_ID}&v=3"
    resp = requests.get(url)
    resp.raise_for_status()
    data = xmltodict.parse(resp.text)
    time.sleep(3)
    ref_code = data["FlexStatementResponse"]["ReferenceCode"]
    #Validacion del codigo obtenido
    if "FlexStatementResponse" not in data or "ReferenceCode" not in data["FlexStatementResponse"]:
        error_msg = data.get("FlexStatementResponse", {}).get("ErrorMessage", "Respuesta inválida")
        raise RuntimeError(f"❌ Error en SendRequest (account): {error_msg}")
    
    #OBTENCION DE DATOS
    #Polling hasta que el reporte este listo
    for intento in range(10): 
        url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement?q={ref_code}&t={TOKEN}&v=3"
        resp2 = requests.get(url)
        resp2.raise_for_status()
        data = xmltodict.parse(resp2.text)

        if "FlexQueryResponse" in data:
            print("✅ Reporte de cuentas listas")
            break
        else:
            error_msg = data.get("FlexStatementResponse", {}).get("ErrorMessage", "Desconocido")
            print(f"⏳ Intento {intento+1}: Reporte aún no disponible ({error_msg})")
            time.sleep(5)
    else:
        print("❌ No se pudo obtener el reporte de cuentas tras varios intentos:", data)
        raise RuntimeError(f"❌ No se pudo obtener el reporte de cuentas tras varios intentos: {data}")


    statements = data["FlexQueryResponse"]["FlexStatements"]["FlexStatement"]
    accounts = statements.get("AccountInformation", [])
    if not accounts:
        return []
    
    # Si solo hay un account, xmltodict devuelve un dict en vez de lista
    if isinstance(accounts, dict):
        accounts = [accounts]
    
    results = []
    for account in accounts:
        #print(account)
        accountId = str(account.get("@accountId"))
        if accountId.startswith("DU"):
            tipo_cuenta="PAPER"
        else:
            tipo_cuenta="LIVE" 

        results.append({
            "accountId":accountId,
            "name":account.get("@name"),
            "tipo_cuenta":tipo_cuenta
        })
    return results

# Descargar XML y parsearlo
def fetch_trades():
    url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest?t={TOKEN}&q={QUERY_ID}&v=3"
    resp = requests.get(url)
    resp.raise_for_status()
    data = xmltodict.parse(resp.text)
    time.sleep(3)
    ref_code = data["FlexStatementResponse"]["ReferenceCode"]

     # Validar si vino ReferenceCode
    if "FlexStatementResponse" not in data or "ReferenceCode" not in data["FlexStatementResponse"]:
        error_msg = data.get("FlexStatementResponse", {}).get("ErrorMessage", "Respuesta inválida")
        raise RuntimeError(f"❌ Error en SendRequest (trades): {error_msg}")
    

    #OBTENCION DE DATA
    # --- Polling hasta que el reporte esté listo ---
    for intento in range(10):  # máximo 10 intentos
        url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement?q={ref_code}&t={TOKEN}&v=3"
        #print("url: ",url)
        resp2 = requests.get(url)
        resp2.raise_for_status()
        data = xmltodict.parse(resp2.text)

        if "FlexQueryResponse" in data:
            print("reporte listo ")
            break
        else:
            error_msg = data.get("FlexStatementResponse", {}).get("ErrorMessage", "Desconocido")
            print(f"⏳ Intento {intento+1}: Reporte aún no disponible ({error_msg})")
            time.sleep(5)  # espera 5 segundos antes de reintentar
    else:
        raise RuntimeError(f"❌ No se pudo obtener el reporte de trades tras varios intentos: {data}")

    statements = data["FlexQueryResponse"]["FlexStatements"]["FlexStatement"].get("Trades",{})
    trades = statements.get("Trade", [])

    if not trades:
        return []

    # Si solo hay un trade, xmltodict devuelve un dict en vez de lista
    if isinstance(trades, dict):
        trades = [trades]

    results = []
    for t in trades:
        #trade_id = f"{t.get('@tradeDate')}_{t.get('@symbol')}_{t.get('@conid')}"
        trade_id = f"{t.get('@buySell')}_{t.get('@symbol')}_{t.get('@conid')}"
        #Profit = Proceeds - Cost Basis - IB Commission
        profit_cal = Decimal(t.get("@proceeds")) - Decimal(t.get("@cost")) - Decimal(t.get("@ibCommission"))
        #print(trade_id)
        strike = t.get("@strike")
        if strike == "":
            strike=0
        results.append({
            "trade_id": trade_id,
            "tradeID":t.get("@tradeID"),
            "symbol": t.get("@symbol"),
            "underlyingSymbol":t.get("@underlyingSymbol"),
            "description":t.get("@description"),
            "action": t.get("@buySell"),
            "putCall":t.get("@putCall"),
            "dateTime":t.get("@dateTime"),        
            "cost":Decimal(t.get("@cost")),
            "closePrice":Decimal(t.get("@closePrice")),
            "strike":Decimal(strike),
            "exchange":t.get("@exchange"),
            "orderType":t.get("@orderType"), 
            "quantity": int(t.get("@quantity")),
            "price": Decimal(t.get("@tradePrice")),
            "currency": t.get("@currency"),
            "account": t.get("@accountId"),
            "timestamp": datetime.utcnow().isoformat(),
            "fifoPnlRealized":Decimal(t.get("@fifoPnlRealized")),
            "mtmPnl":Decimal(t.get("@mtmPnl")),
            "proceeds":Decimal(t.get("@proceeds")),
            "netCash":Decimal(t.get("@netCash")),
            "ibCommission":Decimal(t.get("@ibCommission")),
            "profit_cal":profit_cal,
            "conId": int(t.get("@conid"))

        })
    return results

# Guardar en DynamoDB
def save_trades(trades):
    table = dynamodb.Table(table_name)
    with table.batch_writer() as batch:
        for trade in trades:
            batch.put_item(Item=trade)
    print(f"✅ {len(trades)} trades guardados en DynamoDB")

# Guardar en DynamoDB
def save_account(accounts):
    table = dynamodb.Table(table_nameAccount)
    with table.batch_writer() as batch:
        for account in accounts:
            batch.put_item(Item=account)
    print(f"✅ {len(accounts)} Accounts guardados en DynamoDB")

if __name__ == "__main__":
    create_table()
    trades = fetch_trades()
    if trades:
        save_trades(trades)
    else:
        print("⚠️ No se encontraron trades en el reporte Flex Query")
    time.sleep(10)  # pausa de 10 segundos
    create_tableAccount()
    accounts = fetch_account()
    if accounts:
        save_account(accounts)
    else:
        print("⚠️ No se encontraron accounts en el reporte Flex Query")