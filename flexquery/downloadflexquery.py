import requests
import boto3
import xmltodict
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal
import os
import json

# Ruta donde se guardará la configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # carpeta actual (bot)
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
            if clave=="table_IBKR_Trades_paper":
                table_IBKR_Trades=valor
            if clave=="table_IBKR_Account_paper":
                table_IBKR_Account=valor           
        elif tipo_cuenta=="LIVE":
            if clave=="table_IBKR_Trades_live":
                table_IBKR_Trades=valor
            if clave=="table_IBKR_Account_live":
                table_IBKR_Account=valor
        if clave=="aws_access_key_id":
            acceskey=valor
        if clave=="aws_secret_access_key":
            secretaccess=valor
        if clave=="token_flexquery":
            token=valor
        if clave=="id_flexquery":
            queryid=valor

# === Configuración Flex Query ===
#TOKEN = "747110534787996057748287"
#QUERY_ID = "1286419"
#QUERY_ID = "1287673"

print("token:",token)
print("queryid:",queryid)
print("table_IBKR_Trades:",table_IBKR_Trades)
print("table_IBKR_Account:",table_IBKR_Account)
print("acceskey:",acceskey)
print("secretaccess:",secretaccess)

TOKEN = token
QUERY_ID=queryid

# === DynamoDB produccion===
#dynamodb = boto3.resource("dynamodb-admin", region_name="us-east-1")

#table_name = "IBKR_Trades"
#table_nameAccount = "IBKR_Account"

table_name = table_IBKR_Trades
table_nameAccount = table_IBKR_Account
# ====== CONFIG DYNAMODB LOCAL ======
dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-west-2",  # región dummy para local
    endpoint_url="http://localhost:8000",  # URL DynamoDB local
    aws_access_key_id=acceskey,
    aws_secret_access_key=valor
)

# Crear tabla si no existe
def create_table():
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "trade_id", "KeyType": "HASH"}],  # PK
            AttributeDefinitions=[{"AttributeName": "trade_id", "AttributeType": "S"}],
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
def get_reference_code():
    url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest?t={TOKEN}&q={QUERY_ID}&v=3"
    resp = requests.get(url)
    resp.raise_for_status()
    data = xmltodict.parse(resp.text)
    return data["FlexStatementResponse"]["ReferenceCode"]

# Obtener data
def get_data():
    ref_code = get_reference_code()
    url = f"https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement?q={ref_code}&t={TOKEN}&v=3"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp

def fetch_account():
    resp = get_data()
    data = xmltodict.parse(resp.text)
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
    resp = get_data()
    data = xmltodict.parse(resp.text)
    statements = data["FlexQueryResponse"]["FlexStatements"]["FlexStatement"]["Trades"]
    trades = statements.get("Trade", [])
    if not trades:
        return []

    # Si solo hay un trade, xmltodict devuelve un dict en vez de lista
    if isinstance(trades, dict):
        trades = [trades]

    results = []
    for t in trades:
        trade_id = f"{t.get('@tradeDate')}_{t.get('@symbol')}_{t.get('@tradeID')}"
        #Profit = Proceeds - Cost Basis - IB Commission
        profit_cal = Decimal(t.get("@proceeds")) - Decimal(t.get("@cost")) - Decimal(t.get("@ibCommission"))
        #print(trade_id)
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
            "strike":Decimal(t.get("@strike")),
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
            "conid": int(t.get("@conid"))

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

    create_tableAccount()
    accounts = fetch_account()
    if trades:
        save_account(accounts)
    else:
        print("⚠️ No se encontraron accounts en el reporte Flex Query")