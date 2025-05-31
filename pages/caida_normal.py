# grafica basado en: https://docs.bokeh.org/en/latest/docs/user_guide/topics/timeseries.html#candlestick-chart
import pandas as pd
import streamlit as st
#import yfinance as yf
import numpy as np
from bokeh.plotting import figure, show, column
#from bokeh.sampledata.stocks import MSFT 25092024
#from yahoofinancials import YahooFinancials
#from datetime import datetime, date, timedelta
from bokeh.models import DatetimeTickFormatter, NumeralTickFormatter, CategoricalAxis,FactorRange, Span
#from scipy import stats

file_path = r'./data/rcb_h.txt'
tickers = [
    'AAPL',
    'AMZN',
    'GOOG',
    'GOOGL',
    'META',
    'MSFT',
    'QQQ',
    'TSLA',
    'SPY',
    'NFLX',
    'MRNA',
    'TNA',
    'GLD',
    'SLV',
    'USO',
    'BAC',
    'CVX',
    'XOM'
]

@st.cache_data
def load_dataset3():
    df = pd.read_csv(file_path, sep='\t')
    #df['date'] = pd.to_datetime (df.date)
    df['datetime'] = pd.to_datetime (df.datetime) 
    df["Datetime_str"] = df["datetime"].astype(str)
    df["BarColor"] = df[["Open","Close"]].apply(lambda o: "red" if o.Open>o.Close else "green", axis=1)
    return df

df = load_dataset3()
companys = df['companyName'].drop_duplicates()
sel_companys = st.sidebar.selectbox("Compañias:",companys,0)

df_filtrado = df.query("companyName in @sel_companys")
casos=df_filtrado['caso'].drop_duplicates()

sel_casos = st.sidebar.selectbox("Seleccionar caso:", casos,0)
dfpl = df.query("companyName in @sel_companys and caso == @sel_casos")

#reiniciar index dataframe
dfpl.reset_index(drop=True, inplace=True)

st.dataframe(dfpl)

inc = dfpl.query("Close>Open")
dec = dfpl.query("Open>Close")

#st.text('sl_lows:' + str(sl_lows) +", sl_highs:" + str(sl_highs) + ", r_sq_l:" + str(r_sq_l) +", r_sq_h:" + str(r_sq_h))

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

p = figure(width=1000, height=500,
        title="RCB",
        background_fill_color="#efefef",
        tooltips=[("Index", "@index"),("datetime", "@Datetime_str"), ("Open", "@Open"), ("High","@High"), ("Low","@Low"), ("Close","@Close"), 
                    ("cdlengulfing","@cdlengulfing"), 
                    ("cdlhammer","@cdlhammer"), 
                    ("cdlmorningstar","@cdlmorningstar"), 
                    ("cdlpiercing","@cdlpiercing"), 
                    ("cdlclosingmarubozu","@cdlclosingmarubozu"), 
                    ("cdlmarubozu","@cdlmarubozu"), 
                    ("cdl3whitesoldiers","@cdl3whitesoldiers"), 
                    ("cdlharami","@cdlharami"), 
                    ("cdlharamicross","@cdlharamicross"), 
                    ("cdlinvertdhammer","@cdlinvertdhammer"), 
                    ("cdlladderbottom","@cdlladderbottom")]
        )
p.xaxis.major_label_orientation = 0.8 # radians
p.x_range.range_padding = 0.05
#p.xaxis.axis_line_join = "bevel" # radians
p.xaxis.axis_line_width = 4

# map dataframe indices to date strings and use as label overrides
p.xaxis.major_label_overrides = {
    #i: date.strftime('%b %d') for i, date in zip(df.index, df["datetime"])
    i: date.strftime('%b %d %T') for i, date in zip(dfpl.index, dfpl["datetime"])
}

# one tick per week (5 weekdays)
#p.xaxis.ticker = list(range(df.index[0], df.index[-1], 5))

#p.segment(df.index, df.high, df.index, df.low, color="black")
p.segment("index", "High", "index","Low",  color="black", line_width=1, source=dfpl)
#p.segment("low", color="red", line_width=1, source=df)


#p.vbar(df.index[dec], 0.6, df.open[dec], df.close[dec], color="#eb3c40")
p.vbar(    
    x="index",
    width=0.6,
    bottom="Open",
    top="Close",
    fill_color="red",
    line_color="red",    
    source=dec   
)

#p.vbar(df.index[inc], 0.6, df.open[inc], df.close[inc], fill_color="white",line_color="#49a3a3", line_width=2)
p.vbar(    
    x="index",
    width=0.6,
    bottom="Open",
    top="Close",
    fill_color="green",
    line_color="green", 
    source=inc   
)

p.line(
    x="index", 
    y="SMA20", 
    color="#ffb81c",
    legend_label="SMA20",
    source=dfpl)

p.line(
    x="index", 
    y="SMA40", 
    color="red",
    legend_label="SMA40",
    source=dfpl)

slopeH=dfpl["sl_highs"].iloc[0]
#print(slopeH)

r_sq_h=dfpl["r_sq_h"].iloc[0]
#print(r_sq_h)

val = str(slopeH) + "," + str(r_sq_h)

# p.scatter(x="index", y="pointpos", marker="circle", size=12,
#         line_color="navy", fill_color="blue", alpha=0.5, legend_label="Cambio Tend. Alcista", source=dfpl[(dfpl.isPivot==2)])

# p.scatter(x="index", y="pointpos", marker="circle", size=12,
#         line_color="navy", fill_color="red", alpha=0.5, legend_label="Cambio Tend. Bajsita", source=dfpl[(dfpl.isPivot==1)])

p.scatter(x="index", y="pivotLow", marker="circle", size=5,
            line_color="navy", fill_color="red", alpha=0.5, legend_label="Cambio Tendencia Alcista", source=dfpl)

p.scatter(x="index", y="pivotHigh", marker="circle", size=5,
            line_color="navy", fill_color="green", alpha=0.5, legend_label="Cambio Tendencia Bajista", source=dfpl)


p.scatter(x="index", y="High", marker="square_pin", size=8,
            line_color="navy", fill_color="black", alpha=0.5, legend_label=val , source=dfpl[(dfpl.trendH==1)])

#p.scatter(x="index", y="Low", marker="square_pin", size=8,
#           line_color="navy", fill_color="orange", alpha=0.5, legend_label="Punto tendencia LOW", source=dfpl[(dfpl.trendL==1)])

p.scatter(x="index", y="breakpointpos", marker="triangle", size=12,
        line_color="navy", fill_color="black", alpha=0.5, legend_label="Ruptura del Canal", source=dfpl)

#p.vspan(x="index", line_width=[4], line_color="#7fc97f",source=dfpl[(dfpl.ind_posicion==0)])

#p.ray(x=[0],y=[0],length=300, angle=np.pi, legend="y(x) = 0")

inicio = (dfpl[(dfpl.ind_posicion==0)].index).tolist()[0]
#inicio2 = inicio.iloc[-1]


#print(inicio2)
#print(type(inicio2))

vline=Span(location=inicio,dimension='height', line_color='grey',line_width=0.8, line_dash_offset= 0, line_dash='dashed', name="hola esto es una prueba", level='annotation', tags= ['square'])


# p.line(
# x="index",
# y="trendcurrlow",
# color="purple",
# legend_label="Slope Lower",
# source=dfpl)

p.line(
x="index",
y="trendcurrhigh",
color="purple",
legend_label="Slope High",
source=dfpl)

#p.segment("datetime", "low", "datetime", "high", color="black", line_width=1, source=df)
#p.segment("datetime", "open", "datetime", "close", color="BarColor", line_width=2 if len(df)>100 else 6, source=df)
p.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")
p.xaxis.axis_label = "Fecha"
p.yaxis.axis_label = "Precio"
p.legend.location="top_left"
p.legend.click_policy="hide"

p.renderers.extend([vline])

## Volume Bars Logic
volume = figure(x_axis_type="datetime", height=120, width=1000, tooltips = [("Volume", "@Volume"),("datetime", "@Datetime_str")],background_fill_color="#efefef")
#volume.segment("index", 0, "index", "volume", line_width=2 if len(df)>100 else 6, line_color="BarColor", alpha=0.8, source=df)
volume.x_range.range_padding = 0.05

volume.vbar(    
    x="index",
    width=0.6,
    top="Volume",
    fill_color="BarColor",
    line_color="BarColor", 
    source=dfpl   
)


volume.yaxis.axis_label="Volume"
volume.xaxis.major_label_overrides = {
    #i: date.strftime('%b %d') for i, date in zip(df.index, df["datetime"])
    i: date.strftime('%b %d %T') for i, date in zip(dfpl.index, dfpl["datetime"])
}
volume.yaxis[0].formatter = NumeralTickFormatter(format="0,0")

fig = column(children=[p, volume], sizing_mode="scale_width")

#show(p)
st.bokeh_chart(fig, use_container_width=True)