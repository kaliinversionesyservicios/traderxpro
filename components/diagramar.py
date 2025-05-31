from bokeh.plotting import figure, show, column
from bokeh.models import DatetimeTickFormatter, NumeralTickFormatter, CategoricalAxis,FactorRange, Span
import numpy as np
import pandas as pd
import streamlit as st

def tipo_vela(df_casos):
    

    df_casos['datetime'] = pd.to_datetime (df_casos.datetime) 
    df_casos["Datetime_str"] = df_casos["datetime"].astype(str)
    df_casos["BarColor"] = df_casos[["Open","Close"]].apply(lambda o: "red" if o.Open>o.Close else "green", axis=1)
    
    return df_casos



"""
df=tipo_vela()
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
p.xaxis.axis_line_width = 4

p.xaxis.major_label_overrides = {
    i: date.strftime('%b %d %T') for i, date in zip(dfpl.index, dfpl["datetime"])
}

p.segment("index", "High", "index","Low",  color="black", line_width=1, source=dfpl)

p.vbar(    
    x="index",
    width=0.6,
    bottom="Open",
    top="Close",
    fill_color="red",
    line_color="red",    
    source=dec   
)

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

r_sq_h=dfpl["r_sq_h"].iloc[0]
val = str(slopeH) + "," + str(r_sq_h)

p.scatter(x="index", y="pivotLow", marker="circle", size=5,
        line_color="navy", fill_color="red", alpha=0.5, legend_label="Cambio Tendencia Alcista", source=dfpl)

p.scatter(x="index", y="pivotHigh", marker="circle", size=5,
        line_color="navy", fill_color="green", alpha=0.5, legend_label="Cambio Tendencia Bajista", source=dfpl)


p.scatter(x="index", y="High", marker="square_pin", size=8,
        line_color="navy", fill_color="black", alpha=0.5, legend_label=val , source=dfpl[(dfpl.trendH==1)])

p.scatter(x="index", y="breakpointpos", marker="triangle", size=12,
        line_color="navy", fill_color="black", alpha=0.5, legend_label="Ruptura del Canal", source=dfpl)


inicio = (dfpl[(dfpl.ind_posicion==0)].index).tolist()[0]

vline=Span(location=inicio,dimension='height', line_color='grey',line_width=0.8, line_dash_offset= 0, line_dash='dashed', name="hola esto es una prueba", level='annotation', tags= ['square'])

p.line(
x="index",
y="trendcurrhigh",
color="purple",
legend_label="Slope High",
source=dfpl)

p.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")
p.xaxis.axis_label = "Fecha"
p.yaxis.axis_label = "Precio"
p.legend.location="top_left"
p.legend.click_policy="hide"

p.renderers.extend([vline])

volume = figure(x_axis_type="datetime", height=120, width=1000, tooltips = [("Volume", "@Volume"),("datetime", "@Datetime_str")],background_fill_color="#efefef")
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
"""