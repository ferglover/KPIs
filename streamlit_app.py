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

#==============================================================================SEGUNDA SECCION=================================================

from datetime import datetime
import calendar

# =====================================
# FORECAST EOM
# =====================================

today = pd.Timestamp.today().normalize()

# Si ya tienes una fecha en la leyenda, úsala aquí.
# Si no, toma la fecha de ayer como referencia.
legend_date = today - pd.Timedelta(days=1)

days_elapsed = legend_date.day
days_in_month = calendar.monthrange(legend_date.year, legend_date.month)[1]
days_remaining = days_in_month - days_elapsed

def project_mtd(value):
    return (value / days_elapsed) * days_in_month if days_elapsed else 0

# Proyecciones de volumen
proj_arrivals = project_mtd(arrivals)
proj_contracts = project_mtd(contracts)
proj_qs = project_mtd(qs)
proj_volume = project_mtd(volume)

# KPIs derivados
proj_penetration = (proj_qs / proj_arrivals * 100) if proj_arrivals else 0
proj_closing_rate = (proj_contracts / proj_qs * 100) if proj_qs else 0
proj_vpg = (proj_volume / proj_qs) if proj_qs else 0
proj_avg_price = (proj_volume / proj_contracts) if proj_contracts else 0

st.subheader("Projected KPIs to Month End")

st.caption(
    f"Projection based on {legend_date.strftime('%B %d, %Y')} | "
    f"{days_elapsed} days elapsed | {days_remaining} days remaining"
)

p1, p2, p3, p4 = st.columns(4)

with p1:
    st.metric("Projected Arrivals", f"{proj_arrivals:,.0f}")

with p2:
    st.metric("Projected Qs", f"{proj_qs:,.0f}")

with p3:
    st.metric("Projected Contracts", f"{proj_contracts:,.0f}")

with p4:
    st.metric("Projected Volume", f"${proj_volume:,.0f}")

p5, p6, p7, p8 = st.columns(4)

with p5:
    st.metric("Projected Penetration", f"{proj_penetration:.2f}%")

with p6:
    st.metric("Projected Closing Rate", f"{proj_closing_rate:.2f}%")

with p7:
    st.metric("Projected VPG", f"${proj_vpg:,.0f}")

with p8:
    st.metric("Projected Average Price", f"${proj_avg_price:,.0f}")
