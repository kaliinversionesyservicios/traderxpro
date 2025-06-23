import pandas as pd
from scipy import stats

#Funcion obtner vela entrada
def obtEntrada(dfpl,i,j):
    indiceFinal=0
    indiceFinal2=0
    if (dfpl["cruce_medias"][i]==1): #ALCISTA               
        #ALZA, velas por encima de promedios moviles
        #ultimo high por encima y ultimo low cerca a los promedios                
        siguiente_H = dfpl[(dfpl.index>=j) & ((dfpl["isPivot"]==1) | (dfpl["isPivot2"]==1))].head(1)
        if (siguiente_H.shape[0]>0):
            if (siguiente_H.iloc[0]['High']>siguiente_H.iloc[0]['EMA35']):
                indice = siguiente_H.index[0]
                siguiente_L = dfpl[(dfpl.index>indice) & ((dfpl["isPivot"]==2) | (dfpl["isPivot2"]==2))].head(1)
                if (siguiente_L.shape[0]>0):
                    if (((siguiente_L.iloc[0]['Low']-siguiente_L.iloc[0]['EMA35'])<1) &  (siguiente_L.iloc[0]['Low']<siguiente_H.iloc[0]['High'])):
                        indiceFinal = siguiente_L.index[0]
                    else:
                        indiceFinal2 = siguiente_L.index[0]
    
    
    elif (dfpl["cruce_medias"][i]==-1): #BAJISTA                    
        #BAJA, velas por debajo de promedios moviles
        #ultimo low por debajo y ultimo high cerca a los promedios
        siguiente_L = dfpl[(dfpl.index>=j) & ((dfpl["isPivot"]==2) | (dfpl["isPivot2"]==2)) ].head(1)
        if (siguiente_L.shape[0]>0):
            if (siguiente_L.iloc[0]['Low']<siguiente_L.iloc[0]['EMA35']):
                indice = siguiente_L.index[0]
                siguiente_H = dfpl[(dfpl.index>indice) & ((dfpl["isPivot"]==1) | (dfpl["isPivot2"]==1))].head(1)
                if (siguiente_H.shape[0]>0):
                    if (((siguiente_H.iloc[0]['EMA35']-siguiente_H.iloc[0]['High'])<1) & (siguiente_H.iloc[0]['High']>siguiente_L.iloc[0]['Low'])):
                        indiceFinal = siguiente_H.index[0]
                    else:
                        indiceFinal2 = siguiente_L.index[0]

    return indiceFinal, indiceFinal2



#Funcion revisar Velas
def revisarVelas(dfpl, indiceFinal,i):
    ind_trendHL=0
    ultimos_2H = dfpl[(dfpl["isPivot"]==1) | (dfpl["isPivot2"]==1)].loc[:indiceFinal].tail(2)
    ultimos_2L = dfpl[(dfpl["isPivot"]==2) | (dfpl["isPivot2"]==2)].loc[:indiceFinal].tail(2)

    #print("inicio")
    #print(ultimos_2H.index[0])
    #print("fin")
        
    if (ultimos_2H.shape[0]==2 & ultimos_2L.shape[0]==2):
        #print("h1")
        penultimo_valorH = ultimos_2H.iloc[0]['High']
        ultimo_valorH = ultimos_2H.iloc[1]['High']
        penultimo_valorL = ultimos_2L.iloc[0]['Low']
        ultimo_valorL = ultimos_2L.iloc[1]['Low']

        print("idpenultimoH:",  ultimos_2H.index[0], ", penultimo_valorH:", penultimo_valorH, "idultimoH:",  ultimos_2H.index[1], ", ultimo_valorH:", ultimo_valorH)
        print("idpenultimoL:",  ultimos_2L.index[0], ", penultimo_valorL:", penultimo_valorL, "idultimoH:",  ultimos_2L.index[1], ", ultimo_valorL:", ultimo_valorL)

        #En caso de tendencia ALCISTA
        #tomar los 2 ultimos HH – Higher High (Maximos mas Altos)
        #tomar los 2 ultimos HL – Higher Low (Maximos mas bajos)
        if (dfpl["cruce_medias"][i]==1): #ALCISTA
            #print("h2")
            if ((ultimo_valorH>penultimo_valorH) | (ultimo_valorL>penultimo_valorL)):
                #print("h21")
                ind_trendHL=1

        #En caso de tendencia BAJISTA
        #tomar los 2 ultimos LH – Lower High (Minimos mas Altos)
        #tomar los 2 ultimos LL – Lower Low (Minimos mas bajos)
        elif (dfpl["cruce_medias"][i]==-1): #BAJISTA
            #print("h3")
            if ((ultimo_valorH<penultimo_valorH) | (ultimo_valorL<penultimo_valorL)):
                #print("h31")
                ind_trendHL=1
    return ind_trendHL


#Funcion revisar SLOPE
def obtSlope(dfpl,i,j,indiceFinal):
    print("j:",j)
    ind_sl=0
    #Inicio determinar slope que indica tendencia al ALZA o a la BAJA
    medias35 = dfpl.loc[j:indiceFinal].EMA35.values
    idxmedias35 = dfpl.loc[j:indiceFinal].EMA35.index
    medias50 = dfpl.loc[j:indiceFinal].EMA50.values
    idxmedias50 = dfpl.loc[j:indiceFinal].EMA50.index
    mediasClose = dfpl.loc[j:indiceFinal].Close.values
    idxmediasClose = dfpl.loc[j:indiceFinal].Close.index
    
    if ((len(medias35)>=2) and  (len(medias50)>=2)):
        print("h1")
        sl35, interc35, r_value35, _, _ = stats.linregress(idxmedias35,medias35)
        sl50, interc50, r_value50, _, _ = stats.linregress(idxmedias50,medias50)
        sl, interc, r_value, _, _ = stats.linregress(idxmediasClose,mediasClose)
    #Fin slope

    print ("sl35:", sl35,"sl50:", sl50,"sl:", sl)
    print ("cruce_medias:", dfpl["cruce_medias"][i])
    
    if (dfpl["cruce_medias"][i]==1): #ALCISTA
        print("h2")
        #Revision de pendiente
        if (sl35>0 or sl50>0 #Pendiente positiva
           #and np.isclose(sl35, sl50, atol=1e-5) #Verificar si son paralelas
           #and interc35>interc50 #La línea 35 está por encima de la línea 50
           ):
            ind_sl=1
    elif (dfpl["cruce_medias"][i]==-1): #BAJISTA
        print("h3")
        #Revision de pendiente
        if (sl35<0 or sl50<0 #Pendiente negativa
            #and np.isclose(sl35, sl50, atol=1e-5) #Verificar si son paralelas
            #and interc50>interc35 #La línea 50 está por encima de la línea 35
           ):
            print("h4")
            ind_sl=1
    return ind_sl, sl35, sl50, sl