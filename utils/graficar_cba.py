import streamlit as st
import pandas as pd
from bokeh.plotting import figure, show, column
from bokeh.models import DatetimeTickFormatter, NumeralTickFormatter, CategoricalAxis,FactorRange, Span
from bokeh.models import LabelSet, ColumnDataSource
import gc



gc.collect()

def graficar(dfpl,title,Tag):
    #st.write(Tag)
    dfpl.reset_index(drop=True, inplace=True)
    inc = dfpl.query("Close>Open")
    dec = dfpl.query("Open>Close")
    #TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
    p = figure(width=1000, height=500,
            title=title,
            background_fill_color="#efefef",
            tooltips=[("Index", "@index"),("Datetime", "@Datetime_str"), ("Open", "@Open"), ("High","@High"), ("Low","@Low"), ("Close","@Close")]
            )
    p.xaxis.major_label_orientation = 0.8 # radians
    p.x_range.range_padding = 0.05
    p.xaxis.axis_line_width = 4
    p.xaxis.major_label_overrides = {
        i: date.strftime('%b %d %T') for i, date in zip(dfpl.index, dfpl["Datetime"])
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
        y="EMACorta", 
        color="#ffb81c",
        legend_label="EMACorta",
        source=dfpl)
    p.line(
        x="index", 
        y="EMALarga", 
        color="red",
        legend_label="EMALarga",
        source=dfpl)
    
    
    if Tag=="long":    

        if (dfpl[dfpl["isBreakOutFinal"]==1].shape[0]>0):
            i2 = dfpl[dfpl["isBreakOutIni"]==1].index[0]
            fin2 = dfpl[dfpl["isBreakOutFinal"]==1].index[0]
            print("i2:", i2)
            print("i_fin2:", fin2)
        else:
            i2 = dfpl[dfpl["isBreakOutIni"]==1].index[0]
            fin2 = dfpl.index[-1]
            print("i2:",i2)
            print("i_fin2:", fin2)
        p.line(
        x="index", 
        y="trailing_stop", 
        color="black",
        legend_label="trailing_stop",
        source=dfpl[i2:fin2])
    else:
        if (dfpl[dfpl["isBreakOutFinal2"]==-1].shape[0]>0):
            i2 = dfpl[dfpl["isBreakOutIni2"]==-1].index[0]
            fin2 = dfpl[dfpl["isBreakOutFinal2"]==-1].index[0]
            print("i2:", i2)
            print("i_fin2:", fin2)
        else:
            i2 = dfpl[dfpl["isBreakOutIni2"]==-1].index[0]
            fin2 = dfpl.index[-1]
            print("i2:",i2)
            print("i_fin2:", fin2)
    
        p.line(
        x="index", 
        y="trailing_stop2", 
        color="black",
        legend_label="trailing_stop2",
        source=dfpl[i2:fin2])
    
    
    #codigo para dibujar pivots
    p.scatter(x="index", y="pivotLow", marker="circle", size=3,
                    line_color="navy", fill_color="red", alpha=0.5, legend_label="Pivot Alcista", source=dfpl)
    p.scatter(x="index", y="pivotHigh", marker="circle", size=3,
                    line_color="navy", fill_color="green", alpha=0.5, legend_label="Pivot Bajista", source=dfpl)
    
    # p.scatter(x="index", y="pivotLow2", marker="circle", size=3,
    #                 line_color="navy", fill_color="red", alpha=0.5, legend_label="Pivot Alcista", source=dfpl)
    # p.scatter(x="index", y="pivotHigh2", marker="circle", size=3,
    #                 line_color="navy", fill_color="green", alpha=0.5, legend_label="Pivot Bajista", source=dfpl)
    
    # p.scatter(x="index", y="pivotLow3", marker="circle", size=3,
    #                 line_color="navy", fill_color="red", alpha=0.5, legend_label="Pivot Alcista", source=dfpl)
    # p.scatter(x="index", y="pivotHigh3", marker="circle", size=3,
    #                 line_color="navy", fill_color="green", alpha=0.5, legend_label="Pivot Bajista", source=dfpl)
    

    inicio = (dfpl[(dfpl.indicador==0)].index).tolist()[0]
    vline=Span(location=inicio,dimension='height', line_color='grey',line_width=0.8, line_dash_offset= 0, line_dash='dashed',  level='annotation', tags= ['square'])
    
    if Tag=="long":
        entradas=dfpl[dfpl["isBreakOutIni"]==1]
        p.triangle(
            x=entradas.index,
            y=entradas["Low"] - 0.07,  # un poco debajo del mínimo
            size=12,
            color="#184e77",
            legend_label="Entrada",
            alpha=0.8
        )
        salidas=dfpl[dfpl["isBreakOutFinal"]==1]
        p.inverted_triangle(
            x=salidas.index,
            y=salidas["High"] + 0.07,  # un poco encima del máximo
            size=12,
            color="#3a0ca3",
            legend_label="Salida",
            alpha=0.8
        )
    elif Tag=="short":
        entradas=dfpl[dfpl["isBreakOutIni2"]==-1]
        p.inverted_triangle(
            x=entradas.index,
            y=entradas["High"] - 0.07,  # un poco debajo del mínimo
            size=12,
            color="#ff1808",
            legend_label="Entrada",
            alpha=0.8
        )
        salidas=dfpl[dfpl["isBreakOutFinal2"]==-1]
        p.triangle(
            x=salidas.index,
            y=salidas["Low"] + 0.07,  # un poco encima del máximo
            size=12,
            color="#ff1100",
            legend_label="Salida",
            alpha=0.8
        )
    p.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")
    p.xaxis.axis_label = "Fecha"
    p.yaxis.axis_label = "Precio"
    p.legend.location="top_left"
    p.legend.click_policy="hide"
    p.renderers.extend([vline])
    volume = figure(x_axis_type="datetime", height=120, width=1000, tooltips = [("Volume", "@Volume"),("Datetime", "@Datetime_str")],
    background_fill_color="#efefef",x_range=p.x_range)

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
        i: date.strftime('%b %d %T') for i, date in zip(dfpl.index, dfpl["Datetime"])
    }
    volume.yaxis[0].formatter = NumeralTickFormatter(format="0,0")
    fig = column(children=[p, volume], sizing_mode="scale_width")
    st.bokeh_chart(fig, use_container_width=True)

def mostrar_kpi():
    return 1