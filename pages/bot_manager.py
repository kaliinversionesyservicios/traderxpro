# bot_manager.py
import asyncio, sys
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import streamlit as st
import pandas as pd
from pages.ib_manager2 import IBManager  # el archivo anterior

st.set_page_config(layout="wide")
st.title("IBKR Live Dashboard")

# cache the manager so Streamlit doesn't recreate it each rerun
@st.cache_resource
def init_manager():
    m = IBManager(host="3.13.179.45", port=4002, client_id=801)
    m.connect_and_run()
    return m

manager = init_manager()

# sidebar controls
refresh_secs = st.sidebar.number_input("Refresco (s)", min_value=1, max_value=30, value=3)

# auto refresh by rerunning page every refresh_secs
#st.query_params()  # small no-op to ensure rerun works
st_autorefresh_key = f"rf_{refresh_secs}"
# alternative: use st.experimental_rerun() together with time.sleep in a loop,
# or use an external autorefresh mechanism

# Show portfolio
st.subheader("Portfolio")
portfolio = manager.get_portfolio()
if portfolio:
    df = pd.DataFrame([{
        "symbol": p.contract.symbol,
        "position": p.position,
        "marketPrice": p.marketPrice,
        "avgCost": p.averageCost,
        "unrealizedPnl": p.unrealizedPNL,
        "realizedPnl": p.realizedPNL
    } for p in portfolio])
    st.dataframe(df, use_container_width=True)
else:
    st.info("No portfolio data yet.")

# Show positions
st.subheader("Positions")
positions = manager.get_positions()
for pos in positions:
    st.write(f"{pos.contract.symbol} | qty={pos.position} | avgCost={pos.avgCost}")

# Buttons to act
st.subheader("Actions")
if positions:
    sel = st.selectbox("Seleccionar símbolo a cerrar", [p.contract.symbol for p in positions])
    if st.button("Cerrar posición seleccionada"):
        # find position object
        p = next((x for x in positions if x.contract.symbol == sel), None)
        if p:
            manager.close_position(p)
            st.success(f"Orden de cierre enviada para {sel}")
