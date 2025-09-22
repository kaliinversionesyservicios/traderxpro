from scipy import stats
import pandas as pd
import numpy as np

#==FUNCIONES==
def obtEntrada(dfpl,i,j, idvelafintend, var_adx1,tag):
    if tag == "long":
        cruce_medias = "cruce_medias"
        EMACorta = "EMACorta"
    elif tag=="short":
        cruce_medias = "cruce_medias2"
        EMACorta="EMACorta2"


    indiceFinal=0
    indiceFinal2=0
    if (dfpl[cruce_medias][i]==1): #ALCISTA
        #ALZA, velas por encima de promedios moviles
        #ultimo high por encima y ultimo low cerca a los promedios
        #Obtener Siguiente Low
        siguiente_L = dfpl[(dfpl.index>=j) & (dfpl.index<idvelafintend) & ((dfpl["isPivot"]==2) | (dfpl["isPivot2"]==2) | (dfpl["isPivot3"]==2))].head(1)        
        if (siguiente_L.shape[0]>0):         
            #if (((siguiente_L.iloc[0]['Low']-siguiente_L.iloc[0]['EMA35'])<1.5) | ((siguiente_L.iloc[0]['adx'])>20)):
            if (
                    (((siguiente_L.iloc[0]['isPivot']==2) | (siguiente_L.iloc[0]['isPivot2']==2)))
                &
                    (siguiente_L.iloc[0]['adx']>var_adx1)
                &
                    (
                        (    
                        ((siguiente_L.iloc[0]['Low']-siguiente_L.iloc[0][EMACorta])<=siguiente_L.iloc[0]['ATR']*2) &
                        ((siguiente_L.iloc[0]['Low']-siguiente_L.iloc[0][EMACorta])>=-(siguiente_L.iloc[0]['ATR']*2))
                        )
                        |
                        (    
                        ((siguiente_L.iloc[0]['High']-siguiente_L.iloc[0][EMACorta])<=siguiente_L.iloc[0]['ATR']*2) &
                        ((siguiente_L.iloc[0]['High']-siguiente_L.iloc[0][EMACorta])>=-(siguiente_L.iloc[0]['ATR']*2))
                        )
                    )


            ):
                indiceFinal = siguiente_L.index[0]
                indiceFinal2 = siguiente_L.index[0]
            elif (                
                    ((siguiente_L.iloc[0]['isPivot3']==2)  & np.isnan(siguiente_L.iloc[0]['isPivot']) & np.isnan(siguiente_L.iloc[0]['isPivot2']))
                &
                    (siguiente_L.iloc[0]['adx']>25)
                &
                    (
                        (    
                        ((siguiente_L.iloc[0]['Low']-siguiente_L.iloc[0][EMACorta])<=siguiente_L.iloc[0]['ATR']*2) &
                        ((siguiente_L.iloc[0]['Low']-siguiente_L.iloc[0][EMACorta])>=-(siguiente_L.iloc[0]['ATR']*2))
                        )
                        |
                        (    
                        ((siguiente_L.iloc[0]['High']-siguiente_L.iloc[0][EMACorta])<=siguiente_L.iloc[0]['ATR']*2) &
                        ((siguiente_L.iloc[0]['High']-siguiente_L.iloc[0][EMACorta])>=-(siguiente_L.iloc[0]['ATR']*2))
                        )
                    )
            ):
                indiceFinal = siguiente_L.index[0]
                indiceFinal2 = siguiente_L.index[0]
            #CASOS donde hubo salto de ATR
            elif (
                    ((siguiente_L.iloc[0]['isPivot']==2) | (siguiente_L.iloc[0]['isPivot2']==2))
                &
                    ((siguiente_L.iloc[0]['Low']<siguiente_L.iloc[0][EMACorta]))
                &
                    (siguiente_L.iloc[0]['adx']>15)
                &
                    (siguiente_L.iloc[0]['ATR']>=siguiente_L.iloc[0]['EMA35_ATR']*1.15)
            ):
                indiceFinal = siguiente_L.index[0]
                indiceFinal2 = siguiente_L.index[0]

            else:
                #si es cero ir a la siguiente entrada
                indiceFinal2prev = siguiente_L.index[0]
                siguiente_L2 = dfpl[(dfpl.index>=indiceFinal2prev) & (dfpl.index<idvelafintend) & ((dfpl["isPivot"]==2) | (dfpl["isPivot2"]==2) | (dfpl["isPivot3"]==2) )].head(1)
                if (siguiente_L2.shape[0]>0):
                    indiceFinal2 = siguiente_L2.index[0]
                else:
                    indiceFinal2 = siguiente_L.index[0]

    elif (dfpl[cruce_medias][i]==-1): #BAJISTA                    
        #BAJA, velas por debajo de promedios moviles
        #ultimo low por debajo y ultimo high cerca a los promedios
        #Obtener Siguiente High
        siguiente_H = dfpl[(dfpl.index>=j) & (dfpl.index<idvelafintend) & ((dfpl["isPivot"]==1) | (dfpl["isPivot2"]==1) | (dfpl["isPivot3"]==1))].head(1)        
        if (siguiente_H.shape[0]>0):         
            #if (((siguiente_H.iloc[0]['EMA35']-siguiente_H.iloc[0]['High'])<1.5) | ((siguiente_H.iloc[0]['adx'])>20)):
            if (
                    ((siguiente_H.iloc[0]['isPivot']==1) | (siguiente_H.iloc[0]['isPivot2']==1))
                    &
                    (siguiente_H.iloc[0]['adx']>var_adx1)
                    &
                    (
                        (
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['High'])<=siguiente_H.iloc[0]['ATR']*2) 
                        &
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['High'])>=-(siguiente_H.iloc[0]['ATR']*2))
                        )
                        |
                        (
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['Low'])<=siguiente_H.iloc[0]['ATR']*2) 
                        &
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['Low'])>=-(siguiente_H.iloc[0]['ATR']*2))
                        )
                    
                    )
                ):
                indiceFinal = siguiente_H.index[0]
                indiceFinal2 = siguiente_H.index[0]
            elif (
                    (siguiente_H.iloc[0]['isPivot3']==1)
                    &
                    (siguiente_H.iloc[0]['adx']>25)
                    &
                    (
                        (
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['High'])<=siguiente_H.iloc[0]['ATR']*2) 
                        &
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['High'])>=-(siguiente_H.iloc[0]['ATR']*2))
                        )
                        |
                        (
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['Low'])<=siguiente_H.iloc[0]['ATR']*2) 
                        &
                        ((siguiente_H.iloc[0][EMACorta]-siguiente_H.iloc[0]['Low'])>=-(siguiente_H.iloc[0]['ATR']*2))
                        )
                    )
                ):
                indiceFinal = siguiente_H.index[0]
                indiceFinal2 = siguiente_H.index[0]
            #CASOS donde hubo salto de ATR
            elif (
                    ((siguiente_H.iloc[0]['isPivot']==1) | (siguiente_H.iloc[0]['isPivot2']==1))
                    &
                    ((siguiente_H.iloc[0][EMACorta]<siguiente_H.iloc[0]['High']))
                    &
                    (siguiente_H.iloc[0]['adx']>15)
                    &
                    (siguiente_H.iloc[0]['ATR']>=siguiente_H.iloc[0]['EMA35_ATR']*1.15)
                ):
                indiceFinal = siguiente_H.index[0]
                indiceFinal2 = siguiente_H.index[0]
            else:
                #si es cero ir a la siguiente entrada
                indiceFinal2prev = siguiente_H.index[0]
                siguiente_H2 = dfpl[(dfpl.index>=indiceFinal2prev) & (dfpl.index<idvelafintend) & ((dfpl["isPivot"]==1) | (dfpl["isPivot2"]==1) | (dfpl["isPivot3"]==1))].head(1)
                if siguiente_H2.shape[0]>0:
                    indiceFinal2 = siguiente_H2.index[0]
                else:
                    indiceFinal2 = siguiente_H.index[0]
    return indiceFinal, indiceFinal2

#Funcion revisar Velas
def revisarVelas(dfpl, indiceFinal, i, tipo_pivot, idBreakOutIniPrev, tag):
    if tag == "long":
        cruce_medias = "cruce_medias"
    elif tag=="short":
        cruce_medias = "cruce_medias2"

    ind_trendHL=0

    if ((tipo_pivot==1) | (tipo_pivot==2)):
        ultimos_2H = dfpl[(dfpl["isPivot"]==1) | (dfpl["isPivot2"]==1)].loc[:indiceFinal].tail(2)
        ultimos_2L = dfpl[(dfpl["isPivot"]==2) | (dfpl["isPivot2"]==2)].loc[:indiceFinal].tail(2)
    else:
        ultimos_2H = dfpl[(dfpl["isPivot"]==1) | (dfpl["isPivot2"]==1) | (dfpl["isPivot3"]==1)].loc[:indiceFinal].tail(2)
        ultimos_2L = dfpl[(dfpl["isPivot"]==2) | (dfpl["isPivot2"]==2) | (dfpl["isPivot3"]==2)].loc[:indiceFinal].tail(2)

    #print("inicio")
    #print(ultimos_2H.index[0])
    #print("fin")
        
    if (ultimos_2H.shape[0]==2 & ultimos_2L.shape[0]==2):
        #print("h1")
        penultimo_valorH = ultimos_2H.iloc[0]['High']
        ultimo_valorH = ultimos_2H.iloc[1]['High']
        penultimo_valorL = ultimos_2L.iloc[0]['Low']
        ultimo_valorL = ultimos_2L.iloc[1]['Low']

        if idBreakOutIniPrev!=0:
            penultimo_valorHCasoPrev = dfpl.loc[idBreakOutIniPrev, 'High']
            penultimo_valorLCasoPrev = dfpl.loc[idBreakOutIniPrev, 'Low']
            filtroComparaVelas1 = (penultimo_valorLCasoPrev<ultimo_valorL)
            filtroComparaVelas2 = (penultimo_valorHCasoPrev>ultimo_valorH)
        else:
            filtroComparaVelas1 = True
            filtroComparaVelas2 = True

        #print("idpenultimoH:",  ultimos_2H.index[0], ", penultimo_valorH:", penultimo_valorH, "idultimoH:",  ultimos_2H.index[1], ", ultimo_valorH:", ultimo_valorH)
        #print("idpenultimoL:",  ultimos_2L.index[0], ", penultimo_valorL:", penultimo_valorL, "idultimoH:",  ultimos_2L.index[1], ", ultimo_valorL:", ultimo_valorL)

        #En caso de tendencia ALCISTA
        #tomar los 2 ultimos HH – Higher High (Maximos mas Altos)
        #tomar los 2 ultimos HL – Higher Low (Maximos mas bajos)
        if (dfpl[cruce_medias][i]==1): #ALCISTA
            if ((tipo_pivot==1) & filtroComparaVelas1  & ((ultimo_valorH>penultimo_valorH) | (ultimo_valorL>penultimo_valorL))):
                ind_trendHL=1
            elif (((tipo_pivot==2) | (tipo_pivot==3)) & (ultimo_valorH>penultimo_valorH) & (ultimo_valorL>penultimo_valorL) & filtroComparaVelas1):
                ind_trendHL=1

        #En caso de tendencia BAJISTA
        #tomar los 2 ultimos LH – Lower High (Minimos mas Altos)
        #tomar los 2 ultimos LL – Lower Low (Minimos mas bajos)
        elif (dfpl[cruce_medias][i]==-1): #BAJISTA
            if ((tipo_pivot==1) & filtroComparaVelas2 & ((ultimo_valorH<penultimo_valorH) | (ultimo_valorL<penultimo_valorL))):
                ind_trendHL=1
            elif (((tipo_pivot==2) | (tipo_pivot==3)) & (ultimo_valorH<penultimo_valorH) & (ultimo_valorL<penultimo_valorL) & filtroComparaVelas2):
                ind_trendHL=1
    return ind_trendHL


#Funcion revisar SLOPE
def obtSlope(dfpl,i,j,indiceFinal, tag):
    if tag == "long":
        cruce_medias = "cruce_medias"
    elif tag=="short":
        cruce_medias = "cruce_medias2"

    #print("j:",j)
    ind_sl=sl35=sl50=sl=slH=slL=0

    #Inicio determinar slope que indica tendencia al ALZA o a la BAJA
    #El periodo de evaluacion estara dado por los 2 ultimos pivot
    
    dfHigher = dfpl[(dfpl.index<=indiceFinal) & (dfpl["isPivot"]==1)].tail(2)
    dfLower = dfpl[(dfpl.index<=indiceFinal) & (dfpl["isPivot"]==2)].tail(2)

    if ((len(dfHigher)>=2) and (len(dfLower)>=2)):
        idultHigher = dfHigher.index[-1]
        idpultHigher = dfHigher.index[-2]

        idultLower = dfLower.index[-1]
        idpultLower = dfLower.index[-2]

        # medias35 = dfpl.loc[j:indiceFinal].EMA35.values
        # idxmedias35 = dfpl.loc[j:indiceFinal].EMA35.index
        # medias50 = dfpl.loc[j:indiceFinal].EMA50.values
        # idxmedias50 = dfpl.loc[j:indiceFinal].EMA50.index
        # mediasClose = dfpl.loc[j:indiceFinal].Close.values
        # idxmediasClose = dfpl.loc[j:indiceFinal].Close.index

        mediasH = dfpl.loc[idpultHigher:idultHigher].High.values
        idxmediasH = dfpl.loc[idpultHigher:idultHigher].High.index

        mediasL = dfpl.loc[idpultLower:idultLower].Low.values
        idxmediasL = dfpl.loc[idpultLower:idultLower].Low.index

    
        slH, intercH, r_valueH, _, _ = stats.linregress(idxmediasH,mediasH)
        slL, intercL, r_valueL, _, _ = stats.linregress(idxmediasL,mediasL)
    
    # if ((len(medias35)>=2) and  (len(medias50)>=2)):
    #     sl35, interc35, r_value35, _, _ = stats.linregress(idxmedias35,medias35)
    #     sl50, interc50, r_value50, _, _ = stats.linregress(idxmedias50,medias50)
    #     sl, interc, r_value, _, _ = stats.linregress(idxmediasClose,mediasClose)
    #Fin slope

    #print ("sl35:", sl35,"sl50:", sl50,"sl:", sl)
    #print ("cruce_medias:", dfpl[cruce_medias][i])
    
    if (dfpl[cruce_medias][i]==1): #ALCISTA
        #Revision de pendiente
        if (slH>0 or slL>0 #Pendiente positiva
        #and np.isclose(sl35, sl50, atol=1e-5) #Verificar si son paralelas
        #and interc35>interc50 #La línea 35 está por encima de la línea 50
        ):
            ind_sl=1
    elif (dfpl[cruce_medias][i]==-1): #BAJISTA
        #Revision de pendiente
        if (slH<0 or slL<0 #Pendiente negativa
            #and np.isclose(sl35, sl50, atol=1e-5) #Verificar si son paralelas
            #and interc50>interc35 #La línea 50 está por encima de la línea 35
        ):
            ind_sl=1
    return ind_sl, sl35, sl50, sl


def getBreakOutFinal(dfpl, i, dfprincipal):
    idbreakOutFinal = np.nan

    #Final de caso es siguiente Pivot o trailing stop loss con ATR
    if (dfpl["cruce_medias"][i]==1): #ALCISTA

        k=0
        while (k<=5):
            cnt2 = dfpl.query("index>@idBreakOutIni and isPivot==1").shape[0]
            if cnt2>0:        
                idbreakOutFinal = dfpl.query("index>@idBreakOutIni and isPivot==1").index[0]
                dfpl.loc[idbreakOutFinal,'isBreakOutFinal'] = 1
                k=6
            else:
                idfinal = dfpl.index[-1] 
                idfinal2 = idfinal+25
                if idfinal2 in dfprincipal[dfprincipal['companyName']==ticker].index:
                    dfpl2 = (dfprincipal[(dfprincipal.companyName==ticker)].loc[idfinal+1:idfinal2]).copy()
                    dfpl = pd.concat([dfpl, dfpl2],ignore_index=False)                           
                #else:                  
                #    dfpl['isBreakOutFinal'] = np.nan
                k=k+1
    
    elif (dfpl["cruce_medias"][i]==-1): #BAJISTA
        k=0
        while (k<=5):
            cnt2 = dfpl.query("index>@idBreakOutIni and isPivot==2").shape[0]
            if cnt2>0:        
                idbreakOutFinal = dfpl.query("index>@isBreakOutFinal and isPivot==2").index[0]
                dfpl.loc[idbreakOutFinal,'isBreakOutFinal'] = -1
                k=6
            else:
                idfinal = dfpl.index[-1] 
                idfinal2 = idfinal+25
                if idfinal2 in dfprincipal[dfprincipal['companyName']==ticker].index:
                    dfpl2 = (dfprincipal[(dfprincipal.companyName==ticker)].loc[idfinal+1:idfinal2]).copy()
                    dfpl = pd.concat([dfpl, dfpl2],ignore_index=False)                           
                #else:                  
                #    dfpl['isBreakOutFinal'] = np.nan
                k=k+1
    
    return idbreakOutFinal


def obtener_casos(df, df_strike_pred_old, df_variable, ticker, tag, tipoDir):
    df_casos = pd.DataFrame()
    idcaso = 0
    idcasopadre = 0
    idcasohijo = 0
    ticker2 = ""
    dfprincipal = df.copy()

    #Generar Trailing Stop con ATR
    atr_mult_sl_1 = 1.2
    atr_mult_sl_2 = 2
    atr_mult_tp = 5
    #dfprincipal['TS']=dfprincipal['Close'] - atr_mult_sl_1 * dfprincipal['ATR']

    #Generar Trailing Stop con EMA20
    #Opciones ITM/ATM a corto plazo (trading activo)	1.5% – 3% (0.015 – 0.03)
    #Opciones más lejanas o swing (mayor horizonte)	2.5% – 5% (0.025 – 0.05)
    #Basado en subyacente más estable (como índices)	1% – 2% (0.01 – 0.02
    buffer_pct = 0.002  # 0.05%
    filas = []

    for i, row in dfprincipal.iterrows():
        #Obtener la tendencia hasta donde se evaluaran casos
        idvelafintend=0
        tipo=""
        #ticker=dfprincipal['companyName'][i]
        
        #Reinicio de casos por company
        if ticker2 != ticker:
            ticker2 = ticker
            idcaso = 0
            idcasopadre = 0

        if tag=="long":
            if ((dfprincipal["cruce_medias"][i]==1)): #ALCISTA
                velafintend = dfprincipal[(dfprincipal["cruce_medias"]==-1) & (dfprincipal.index>i)].head(1)
                tipo="ALZA"
                position = 'long'
                if (velafintend.shape[0]>0):
                    idvelafintend = velafintend.index[0]
            elif ((dfprincipal["cruce_medias"][i]==-1)): #BAJISTA
                velafintend = dfprincipal[(dfprincipal["cruce_medias"]==1) & (dfprincipal.index>i)].head(1)
                tipo="BAJA" 
                position = 'short'
                if (velafintend.shape[0]>0):
                    idvelafintend = velafintend.index[0]
        elif tag=="short":
            if ((dfprincipal["cruce_medias2"][i]==1)): #ALCISTA
                velafintend = dfprincipal[(dfprincipal["cruce_medias2"]==-1) & (dfprincipal.index>i)].head(1)
                tipo="ALZA"
                position = 'long'
                if (velafintend.shape[0]>0):
                    idvelafintend = velafintend.index[0]
            elif ((dfprincipal["cruce_medias2"][i]==-1)): #BAJISTA
                velafintend = dfprincipal[(dfprincipal["cruce_medias2"]==1) & (dfprincipal.index>i)].head(1)
                tipo="BAJA" 
                position = 'short'
                if (velafintend.shape[0]>0):
                    idvelafintend = velafintend.index[0]
        
        if (tipo!=""):
            # if ((idvelafintend-i)<=75):
            #     posteval=i+75
            # elif ((idvelafintend-i)>75):
            #     #posteval=i+idvelafintend+10
            #     posteval=idvelafintend+10

            #Revisar prediccion STRIKE
            strike_calculado = None        
            strike_pred = 5 #valor predeterminado si no se ha calculado
            filtro = df_strike_pred_old.query("Ticker==@ticker and semana=='s1' and Tag==@position")
            if filtro.shape[0]>0:
                strike_calculado = filtro.iloc[0]["strike_price_q3"]
            if strike_calculado is None:
                strike_calculado = strike_pred

            #print("strike_calculado:", strike_calculado)
            #print ("====> dfprincipal:", dfprincipal.shape[0])
            #print ("====> i:", i)
            #print ("====> idmax:", dfprincipal.idxmax())
            #print ("====> consulta:", dfprincipal[(dfprincipal.index>i)])
            #print ("====> consulta:", dfprincipal[(dfprincipal.index>i)].shape[0])
            
            cnt_fintend = dfprincipal[(dfprincipal.index>i)].shape[0]

            if cnt_fintend==0:
                continue

            ind_sl = 0    
            df2 = pd.DataFrame()
            if idvelafintend==0:
                idvelafintend = dfprincipal[(dfprincipal.index>i)].index[-1]
            print("==>hito carlos, i:", i, ", idvelafintend:", idvelafintend )
            df2 = (dfprincipal.query("index>=@i and index<@idvelafintend")).copy() #no tomar en cuenta el ultimo registro porque ya es cambio de tendencia
            
            iniEval = i

            idcasohijo = 0
            idBreakOutIniPrev = 0
            for j, row in df2.iterrows():                
                if (j==iniEval):
                    #print ("j:", j, ", iniEval:", iniEval)
                    dfpl = pd.DataFrame()
                    #dfpl = (df[(df.companyName==ticker)].loc[i-backeval:posteval]).copy()
                    #dfpl = (df[(df.companyName==ticker)]).copy()
                    dfpl = df.copy()

                    #Obtener variable de ADX para cada ticker evaluado
                    filtro = df_variable.query("Ticker==@ticker and Tag==@tag")
                    if filtro.shape[0]>0:
                        var_adx1 = filtro.iloc[0]["var_adx1"]
                    else:
                        var_adx1 = 15
                        
                    idBreakOutIni, idBreakOutIni2 = obtEntrada(dfpl, i, j, idvelafintend, var_adx1, tag)
                    if idBreakOutIni2==j: idBreakOutIni2+=1
                    #print("===obteniendo entrada===")
                    #print ("idBreakOutIni:", idBreakOutIni)
                    #print ("idBreakOutIni2:", idBreakOutIni2)
                    #print("===obteniendo entrada===")
                    if idBreakOutIni>0:
                        #Guardar entrada para comparar con el siguiente caso, (premisa: Entrada debe de estar mas arriba que el caso anterior)
                        
                        
                        #revisar si es pivot3
                        tipo_pivot=1
                        if ((dfpl["isPivot2"][idBreakOutIni]==1) | (dfpl["isPivot2"][idBreakOutIni]==2)) & pd.isna(dfpl["isPivot"][idBreakOutIni]):
                            tipo_pivot=2
                        elif ((dfpl["isPivot3"][idBreakOutIni]==1) | (dfpl["isPivot3"][idBreakOutIni]==2)) & pd.isna(dfpl["isPivot2"][idBreakOutIni]):
                            tipo_pivot=3
                        
                        ind_trendHL = revisarVelas(dfpl, idBreakOutIni, i, tipo_pivot, idBreakOutIniPrev, tag) #COMETADO CARLOS 24072025
                        #ind_trendHL = 1  
                        #ind_sl, sl35, sl50, sl = obtSlope(dfpl,i,j,idBreakOutIni, tag)
                        adx = dfpl.loc[idBreakOutIni, "adx"]
                        #if ( (((ind_trendHL>0) or (ind_sl>0)) and (dfpl.loc[idBreakOutIni, "adx"]>15)) or ((dfpl.loc[idBreakOutIni, "adx"]>25) and (dfpl.loc[idBreakOutIni, "ATR"]>dfpl.loc[idBreakOutIni, "EMA35_ATR"]))):
                        #if ( ((ind_trendHL>0) and (dfpl.loc[idBreakOutIni, "adx"]>15)) or ((dfpl.loc[idBreakOutIni, "adx"]>25) and (dfpl.loc[idBreakOutIni, "ATR"]>dfpl.loc[idBreakOutIni, "EMA35_ATR"]))):
                        #if ( (ind_trendHL>0) or ((dfpl.loc[idBreakOutIni, "adx"]>15) and (dfpl.loc[idBreakOutIni, "ATR"]>dfpl.loc[idBreakOutIni, "EMA35_ATR"]*1.5))):

                        
                        if (ind_trendHL>0) & (tipo==tipoDir):
                            #INSERT CASO
                            idcaso = idcaso + 1
                            idcasohijo = idcasohijo + 1
                            if idcasohijo==1: idcasopadre = idcasopadre + 1
                            idBreakOutIniPrev = idBreakOutIni
                            #Recorrer para obtener la salida
                            df3 = (dfprincipal.query("index>=@idBreakOutIni")).copy()
                            #price = dfprincipal.loc[idBreakOutIni, 'EMA5'] #Revisar que EMA es la apropiada                            
                            price = dfprincipal.loc[idBreakOutIni, 'Close'] #carlos 1707
                            #priceL = dfprincipal.loc[idBreakOutIni, 'Low'] #carlos 1707
                            #priceH = dfprincipal.loc[idBreakOutIni, 'High'] #carlos 1707

                            if dfprincipal.loc[idBreakOutIni, 'Close']>dfprincipal.loc[idBreakOutIni, 'Open']:
                                priceLong = dfprincipal.loc[idBreakOutIni, 'Open']
                                priceShort = dfprincipal.loc[idBreakOutIni, 'Close']
                            else:
                                priceLong = dfprincipal.loc[idBreakOutIni, 'Close']
                                priceShort = dfprincipal.loc[idBreakOutIni, 'Open']
                            
                            atr = dfprincipal.loc[idBreakOutIni, 'ATR']
                            atr2 = dfprincipal.loc[idBreakOutIni, 'ATR2']
                            datetime = dfprincipal.loc[idBreakOutIni, 'Datetime']

                            # Variables de control
                            #position = None  # 'long' o 'short'
                            
                            entry_price = trailing_stop = np.nan
                            
                            if (tipo=="ALZA"):
                                position = 'long'
                                entry_price = price
                                entry_date = datetime                                
                                #trailing_stop = price * (1 - buffer_pct)
                                #trailing_stop = price - atr_mult_sl_1 * atr
                                trailing_stop = priceLong - atr_mult_sl_1 * atr2
                                #take_profit_pred = (price+strike_calculado) + atr_mult_sl * atr
                                take_profit_pred = price+strike_calculado+atr_mult_sl_2*atr
                                dfprincipal.loc[i,'ind_posicion']=1
                                dfprincipal.loc[idBreakOutIni,'isBreakOutIni']=1
                                print(f"ENTRADA LONG en {price:.2f} el {datetime} (TSL: {trailing_stop:.2f}) idBreakOutIni: {idBreakOutIni}")
                            
                            elif (tipo=="BAJA"):
                                position = 'short'
                                entry_price = price
                                entry_date = datetime                                
                                #trailing_stop = price * (1 + buffer_pct)
                                #trailing_stop = price + atr_mult_sl_1 * atr
                                trailing_stop = priceShort + atr_mult_sl_1 * atr2
                                #take_profit_pred = (price-strike_calculado) - atr_mult_sl * atr
                                take_profit_pred = price-strike_calculado-atr_mult_sl_2*atr
                                dfprincipal.loc[i,'ind_posicion2']=-1
                                dfprincipal.loc[idBreakOutIni,'isBreakOutIni2']=-1
                                print(f"ENTRADA SHORT en {price:.2f} el {datetime} (TSL: {trailing_stop:.2f}) idBreakOutIni2: {idBreakOutIni}")

                            datetime2 = None
                            #price2 = None
                            id2 = 0
                            #Revisar puntos mas altos, para obtener el STRIKE minimo
                            if position == 'long': #ALCISTA
                                cnt2 = dfpl.query("index>@idBreakOutIni and isPivot==1").shape[0]
                                if cnt2>0:
                                    id2 = dfpl.query("index>@idBreakOutIni and isPivot==1").index[0]
                            elif position == 'short': #BAJISTA
                                cnt2 = dfpl.query("index>@idBreakOutIni and isPivot==2").shape[0]
                                if cnt2>0:
                                    id2 = dfpl.query("index>@idBreakOutIni and isPivot==2").index[0]

                            exit_date_pivote = exit_price_pivote = np.nan

                            if (id2>0):
                                exit_date_pivote = dfpl.loc[id2, 'Datetime']
                                exit_price_pivote = dfpl.loc[id2, 'Close']

                            fila_pivote = [ticker, idcaso,entry_price, exit_price_pivote, entry_date, exit_date_pivote, position, adx, atr, idcasopadre, idcasohijo, trailing_stop, strike_calculado, take_profit_pred] 
                            
                            #ticker, idcaso, price, "ExitPrice", datetime, "ExitTime", position
                            fila = [ticker, idcaso,entry_price, np.nan, entry_date, np.nan, position, adx, atr, idcasopadre, idcasohijo, trailing_stop, strike_calculado, take_profit_pred]

                            if tag=="long":
                                dfprincipal.loc[idBreakOutIni,'trailing_stop']=trailing_stop #carlos tmp
                            elif tag=="short":
                                dfprincipal.loc[idBreakOutIni,'trailing_stop2']=trailing_stop #carlos tmp

                            
                            #estrategia para hallar la salida: usar stop loss estatico, si precio supera el strike calculado usar trailing stop
                            #STOP LOSS ESTATICO
                            tipo_stop = 1

                            #Obtener Salida utilizando Trailing Stop ATR
                            for k, row3 in df3.iterrows():
                                #price = dfprincipal.loc[k, 'EMA5']
                                price = dfprincipal.loc[k, 'Close']
                                atr = dfprincipal.loc[k, 'ATR']
                                datetime = dfprincipal.loc[k, 'Datetime']

                                #revisar si tipo cambia a STOP LOSS DINAMICO
                                if position == 'long' and price >= take_profit_pred:
                                    tipo_stop = 2
                                elif position == 'short' and price <= take_profit_pred:
                                    tipo_stop = 2
                                            
                                # Cerrar posición si el precio toca el trailing stop                                                               
                                if position == 'long' and price <= trailing_stop:
                                    iniEval = k
                                    dfprincipal.loc[k,'isBreakOutFinal']=1
                                    print(f"SALIDA LONG en {price:.2f} el {datetime} (TSL: {trailing_stop:.2f})  idBreakOutFinal: {iniEval}")
                                    #fila[3]=price
                                    fila[3] = trailing_stop #+ (1e-3)
                                    fila[5]=datetime
                                    position = np.nan
                                    entry_price = trailing_stop
                                    break

                                if position == 'short' and price >= trailing_stop:
                                    iniEval = k
                                    dfprincipal.loc[k,'isBreakOutFinal2']=-1
                                    print(f"SALIDA SHORT en {price:.2f} el {datetime} (TSL: {trailing_stop:.2f})  idBreakOutFinal2: {iniEval}")
                                    #fila[3]=price
                                    fila[3] = trailing_stop #- (1e-3)
                                    fila[5]=datetime
                                    position = np.nan
                                    entry_price = trailing_stop
                                    break
                                    
                                if tipo_stop == 2:
                                    #Si hay posición abierta y es TRAILING STOP, actualizar nuevo stop (se incrementa multiplicador)
                                    if position=="long":                                  
                                        #new_stop = price * (1 - buffer_pct)
                                        new_stop = price - atr_mult_sl_2 * atr
                                        if new_stop > trailing_stop:
                                            trailing_stop = new_stop
                                        
                                    elif position=="short":                                    
                                        #new_stop = price * (1 + buffer_pct)
                                        new_stop = price + atr_mult_sl_2 * atr
                                        if new_stop < trailing_stop:
                                            trailing_stop = new_stop
                                if tag=="long":
                                    dfprincipal.loc[k, 'trailing_stop'] = trailing_stop #carlos tmp
                                elif tag=="short":
                                    dfprincipal.loc[k, 'trailing_stop2'] = trailing_stop #carlos tmp
                            filas.append(fila)
                        else:
                            iniEval = idBreakOutIni2
                    else:
                        iniEval = idBreakOutIni2

    #Convertir a dataframe la lista
    columnas = ['Ticker', 'caso', 'EntryPrice', 'ExitPrice', 'EntryTime', 'ExitTime', 'Tag', 'ADX', 'ATR', 'casopadre', 'casohijo','trailingstop','strike_price_q3_old', 'take_profit']
    df_casos = pd.DataFrame(filas, columns=columnas)
    print("AQUI CARLOS")
    #print("cantidad:", df_casos.shape[0])
    #df_casos['price_distance'] = np.nan
    #df_casos['duration'] = np.nan

    #print("df_casos.info")    



    if (df_casos.shape[0]>0):
        print("===>CASOS")
        print(df_casos)        
        if df_casos[~np.isnan(df_casos['ExitTime'])].shape[0]==0:
            df_casos['ExitTime'] = pd.to_datetime(df_casos['ExitTime'], errors='coerce').dt.tz_localize(None)
            #df_casos['ExitTime'] = pd.to_datetime(df_casos['ExitTime'])
        #print(df_casos.info())
        df_casos['duration'] = np.where(~np.isnan(df_casos['ExitTime']), (df_casos['ExitTime'] - df_casos['EntryTime']).dt.days, np.nan)
        df_casos['price_distance'] =  np.where(((~np.isnan(df_casos['ExitPrice'])) & (df_casos['Tag']=="long")), 
                                               df_casos['ExitPrice'] - df_casos['EntryPrice'],
                                               np.where((~np.isnan(df_casos['ExitPrice'].notna()) & (df_casos['Tag']=="short")), df_casos['EntryPrice'] - df_casos['ExitPrice'], np.nan))
    else:
       df_casos['duration'] = np.nan
       df_casos['price_distance'] =  np.nan
    
    return df_casos