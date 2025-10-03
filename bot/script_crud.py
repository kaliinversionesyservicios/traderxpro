import boto3
from botocore.exceptions import ClientError

# Configuración de conexión desarrollo 
# dynamodb = boto3.resource(
#     'dynamodb',
#     endpoint_url="http://localhost:8000",  # Cambiar a None si usas AWS real
#     region_name="us-west-2"
# )


# Configuración de conexión produccion
dynamodb = boto3.resource( 
    'dynamodb',
    region_name="us-east-2",
    aws_access_key_id="AKIAYCUP6PDKIQ25PGUY",
    aws_secret_access_key="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"
)


# ========================
# Función para secuencia
# ========================
def get_next_id(sequence_name):
    """Obtiene el próximo ID secuencial para la tabla indicada"""
    seq_table = dynamodb.Table("secuencia")
    response = seq_table.update_item(
        Key={"tabla": sequence_name},
        UpdateExpression="SET ultimo_id = ultimo_id + :inc",
        ExpressionAttributeValues={":inc": 1},
        ReturnValues="UPDATED_NEW"
    )
    return int(response["Attributes"]["ultimo_id"])

# ========================
# CRUD con secuencia
# ========================
# 🔹 1. CREATE (insertar item en una tabla)
def create_item(table_name, item):
    try:       
        table = dynamodb.Table(table_name)        
        #new_id = get_next_id(table_name) #genera secuencia unica        
        #item["id"] = new_id        
        response = table.put_item(Item=item)        
        print(f"✅ Item creado en {table_name}: {item}")        
        return response
    except ClientError as e:
        print(f"❌ Error al crear item: {e}")
        return None

# 🔹 2. READ (obtener item por clave primaria)
def read_item(table_name, key):
    try:
        table = dynamodb.Table(table_name)
        response = table.get_item(Key=key)
        if 'Item' in response:
            print(f"📖 Item leído: {response['Item']}")
            return response['Item']
        else:
            print("⚠️ Item no encontrado")
            return None
    except ClientError as e:
        print(f"❌ Error al leer item: {e}")
        return None

# 🔹 3. UPDATE (modificar atributos de un item)
def update_item(table_name, key, update_expression, expression_values):
    try:
        table = dynamodb.Table(table_name)
        response = table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="UPDATED_NEW"
        )
        print(f"✏️ Item actualizado: {response['Attributes']}")
        return response
    except ClientError as e:
        print(f"❌ Error al actualizar item: {e}")
        return None

# 🔹 4. DELETE (eliminar un item por clave)
def delete_item(table_name, key):
    try:
        table = dynamodb.Table(table_name)
        response = table.delete_item(Key=key)
        print(f"🗑️ Item eliminado de {table_name}: {key}")
        return response
    except ClientError as e:
        print(f"❌ Error al eliminar item: {e}")
        return None