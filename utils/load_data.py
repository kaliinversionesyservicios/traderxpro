import pandas as pd


def load_data(url_stats):
    df_stats = pd.read_csv(url_stats)
    df_stats["Start"]=pd.to_datetime(df_stats["Start"])
    df_stats["End"]=pd.to_datetime(df_stats["End"])
    
    return df_stats
  