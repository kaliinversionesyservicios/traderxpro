import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import pandas as pd

# Datos de ejemplo
data = pd.DataFrame({
    'Nombre': ['Ana', 'Luis', 'Carla', 'Pedro'],
    'Edad': [23, 45, 31, 22],
    'Score': [88, 92, 95, 70]
})

# Construcción de las opciones del grid
gb = GridOptionsBuilder.from_dataframe(data)
gb.configure_default_column(editable=True)

# JavaScript para aplicar estilos a filas completas
row_style_jscode = JsCode("""
function(params) {
    if (params.data.Score > 90) {
        return {'backgroundColor': 'lightgreen', 'color': 'black'};
    } else if (params.data.Score > 80) {
        return {'backgroundColor': 'lightyellow', 'color': 'black'};
    } else {
        return {'backgroundColor': 'lightcoral', 'color': 'white'};
    }
}
""")

# Aplicar el estilo de fila al grid completo
gb.configure_grid_options(getRowStyle=row_style_jscode)

# Generar las opciones finales
grid_options = gb.build()

# Renderizar el AgGrid con JavaScript habilitado
AgGrid(data, gridOptions=grid_options, height=250, allow_unsafe_jscode=True)
