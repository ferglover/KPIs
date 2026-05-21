from pathlib import Path
import streamlit as st
import pandas as pd

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="KPI Calculator",
    layout="wide"
)

# =====================================
# PATH
# =====================================

BASE_DIR = Path(__file__).resolve().parent

# =====================================
# LOAD DATA
# =====================================

@st.cache_data
def load_data():
    df = pd.read_csv(BASE_DIR / "data" / "kpi_table.csv")

    # Limpia corchetes del CSV
    df.columns = (
        df.columns
        .str.replace("[", "", regex=False)
        .str.replace("]", "", regex=False)
        .str.strip()
    )

    return df

df = load_data()

# =====================================
# TITLE
# =====================================

st.title("Calculadora BI")
#LEYENDA DE FECHA
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(days=1)

st.caption(
    f"Datos hasta el {yesterday.strftime('%B %d, %Y')}"
)
# =====================================
# SALESROOM FILTER
# =====================================

salesroom = st.selectbox(
    "Select SalesRoom",
    sorted(df["SalesRoom"].dropna().unique().tolist())
)

filtered = df[df["SalesRoom"] == salesroom]

if filtered.empty:
    st.warning("No data found")
    st.stop()

row = filtered.iloc[0]

# =====================================
# INPUTS
# =====================================

col1, col2, col3 = st.columns(3)

with col1:
    arrivals = st.number_input(
        "Arrivals",
        value=int(row["Arrivals"]),
step=1
    )

with col2:
    contracts = st.number_input(
        "Contracts Processable",
        value=int(row["Contracts Processable"]),
step=1
    )

    closing_rate = st.number_input(
        "Closing Rate %",
        value=float(row["Closing Rate"] * 100),
        step=0.1
    )

with col3:
    avg_price = st.number_input(
    "Average Price ($)",
    value=int(row["Average Price"]),
    step=100,
    format="%d"
)


# =====================================
# DERIVED CALCULATIONS
# =====================================

qs = contracts / (closing_rate / 100) if closing_rate else 0
penetration = (qs / arrivals * 100) if arrivals else 0
volume = contracts * avg_price
vpg = volume / qs if qs else 0

# =====================================
# KPI OUTPUTS
# =====================================

st.subheader("Calculated KPIs")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Penetration", f"{penetration:.2f}%")

with k2:
    st.metric("Qs", f"{qs:,.0f}")

with k3:
    st.metric("VPG", f"${vpg:,.0f}")

with k4:
    st.metric("Volume", f"${volume:,.0f}")
