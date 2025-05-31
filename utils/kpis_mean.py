import pandas as pd


def mean_duration(data):
    duration=pd.to_timedelta(data)
    media=duration.mean()
    std=duration.std()
    # 3. Filtrar eliminando los valores muy extremos (por ejemplo, fuera de ±2 std)
    serie_filtrada = (duration > media - 2 * std) & (duration < media + 2 * std)
    
    # 4. Obtener la nueva media sin outliers
    media_filtrada = duration[serie_filtrada].mean()
    total_second=media_filtrada.total_seconds() 
    print(f"Media nueva: {media_filtrada}")
    days=int(total_second//86400)
    hours=int((total_second%86400)//3600)
    minutes=int((total_second%3600)//60)
    return f"{days} días {hours:02d}:{minutes:02d}"


def mean_price(data):
    print("-----------------------")
    return data.mean()