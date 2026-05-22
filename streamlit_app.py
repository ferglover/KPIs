from pathlib import Path
from datetime import datetime, timedelta
import calendar

import streamlit as st
import pandas as pd

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="KPI Calculator",
    layout="wide"
)

st.markdown("""
<style>

/* INPUT EDITABLE */
div[data-baseweb="input"] input {
    font-size: 36px !important;
    font-weight: 400 !important;
}

/* BOTONES + / - */
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] {
    height: 38px !important;
    width: 38px !important;
}

/* LABEL DEL INPUT */
label[data-testid="stWidgetLabel"] p {
    font-size: 18px !important;
    font-weight: 700 !important;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# PATH
# =====================================

BASE_DIR = Path(__file__).resolve().parent

# =====================================
# LOAD ACTUAL DATA
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

# =====================================
# LOAD FORECAST DATA
# Format expected:
# SalesRoom, Metric, Value
# =====================================

@st.cache_data
def load_forecast():
    df = pd.read_csv(
        BASE_DIR / "data" / "FORECAST MAY.csv",
        header=None,
        names=["SalesRoom", "Metric", "Value"],
        encoding="latin1"
    )

    df["SalesRoom"] = df["SalesRoom"].astype(str).str.strip()
    df["Metric"] = df["Metric"].astype(str).str.strip()
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    df["Metric"] = df["Metric"].replace({
        "% Penetraci?n": "Penetration",
        "% Penetración": "Penetration",
        "Q's": "Qs",
        "Q´s": "Qs",
        "Q’s": "Qs",
        "Contracts ": "Contracts",
        "Contracts": "Contracts",
        "Average Price ": "Average Price",
        "Closing Rate ": "Closing Rate",
        "VPG ": "VPG",
        "Volume ": "Volume",
        "Arrivals ": "Arrivals"
    })

    df = df.pivot_table(
        index="SalesRoom",
        columns="Metric",
        values="Value",
        aggfunc="first"
    ).reset_index()

    df.columns.name = None
    return df

# =====================================
# LOAD DATAFRAMES
# =====================================

df = load_data()
forecast_df = load_forecast()

# =====================================
# TITLE
# =====================================

st.title("Calculadora BI")

# =====================================
# DATE LEGEND
# =====================================

yesterday = datetime.now() - timedelta(days=1)
st.caption(f"Data until {yesterday.strftime('%B %d, %Y')}")

# =====================================
# SALESROOM FILTER
# =====================================

salesroom = st.selectbox(
    "Select SalesRoom",
    sorted(df["SalesRoom"].dropna().unique().tolist())
)

filtered = df[df["SalesRoom"] == salesroom]
forecast_filtered = forecast_df[forecast_df["SalesRoom"] == salesroom]

if filtered.empty:
    st.warning("No actual data found")
    st.stop()

if forecast_filtered.empty:
    st.warning("No forecast data found")
    st.stop()

row = filtered.iloc[0]
forecast_row = forecast_filtered.iloc[0]

# =====================================
# ACTUALS KPIs
# =====================================

st.subheader("Actuals KPIs")

def input_card(title, value, step, fmt="%d"):

    with st.container(border=True):

        st.markdown(f"**{title}**")

        return st.number_input(
            title,
            value=value,
            step=step,
            format=fmt,
            label_visibility="collapsed"
        )

c1, c2, c3, c4 = st.columns(4)

with c1:
    arrivals = input_card(
        "Arrivals",
        int(round(float(row["Arrivals"]))),
        step=1,
        fmt="%d"
    )

with c2:
    contracts = input_card(
        "Contracts Processable",
        int(round(float(row["Contracts Processable"]))),
        step=1,
        fmt="%d"
    )

with c3:
    closing_rate = input_card(
        "Closing Rate %",
        float(row["Closing Rate"]) * 100
        if float(row["Closing Rate"]) <= 1
        else float(row["Closing Rate"]),
        step=0.1,
        fmt="%.1f"
    )

with c4:
    avg_price = input_card(
        "Average Price ($)",
        int(round(float(row["Average Price"]))),
        step=100,
        fmt="%d"
    )

# =====================================
# DERIVED CALCULATIONS - ACTUALS
# =====================================

qs = contracts / (closing_rate / 100) if closing_rate else 0

penetration = (
    (qs / arrivals) * 100
    if arrivals else 0
)

volume = contracts * avg_price

vpg = (
    volume / qs
    if qs else 0
)

# =====================================
# CALCULATED KPIs
# =====================================

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "Penetration",
        f"{penetration:.2f}%"
    )

with m2:
    st.metric(
        "Qs",
        f"{qs:,.0f}"
    )

with m3:
    st.metric(
        "VPG",
        f"${vpg:,.0f}"
    )

with m4:
    st.metric(
        "Volume",
        f"${volume:,.0f}"
    )

# =====================================
# FORECAST EOM
# =====================================

today = pd.Timestamp.today().normalize()
legend_date = today - pd.Timedelta(days=1)

days_elapsed = legend_date.day
days_in_month = calendar.monthrange(legend_date.year, legend_date.month)[1]
days_remaining = days_in_month - days_elapsed

def project_mtd(value):
    return (value / days_elapsed) * days_in_month if days_elapsed else 0

proj_arrivals = project_mtd(arrivals)
proj_contracts = project_mtd(contracts)
proj_qs = project_mtd(qs)
proj_volume = project_mtd(volume)

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

# =====================================
# FORECAST TARGETS
# =====================================

forecast_arrivals = float(forecast_row.get("Arrivals", 0))
forecast_penetration = float(forecast_row.get("Penetration", 0))
forecast_qs = float(forecast_row.get("Qs", 0))
forecast_contracts = float(forecast_row.get("Contracts", 0))
forecast_avg_price = float(forecast_row.get("Average Price", 0))
forecast_closing_rate = float(forecast_row.get("Closing Rate", 0))
forecast_vpg = float(forecast_row.get("VPG", 0))
forecast_volume = float(forecast_row.get("Volume", 0))

if forecast_closing_rate <= 1:
    forecast_closing_rate = forecast_closing_rate * 100

st.subheader("Forecast Targets")

f1, f2, f3, f4 = st.columns(4)

with f1:
    st.metric("Forecast Arrivals", f"{forecast_arrivals:,.0f}")

with f2:
    st.metric("Forecast Qs", f"{forecast_qs:,.0f}")

with f3:
    st.metric("Forecast Contracts", f"{forecast_contracts:,.0f}")

with f4:
    st.metric("Forecast Volume", f"${forecast_volume:,.0f}")

f5, f6, f7, f8 = st.columns(4)

with f5:
    st.metric("Forecast Penetration", f"{forecast_penetration:.2f}%")

with f6:
    st.metric("Forecast Closing Rate", f"{forecast_closing_rate:.2f}%")

with f7:
    st.metric("Forecast VPG", f"${forecast_vpg:,.0f}")

with f8:
    st.metric("Forecast Average Price", f"${forecast_avg_price:,.0f}")

# =====================================
# VARIANCE VS FORECAST
# =====================================

var_arrivals = proj_arrivals - forecast_arrivals
var_qs = proj_qs - forecast_qs
var_contracts = proj_contracts - forecast_contracts
var_volume = proj_volume - forecast_volume

var_penetration_pp = proj_penetration - forecast_penetration
var_closing_pp = proj_closing_rate - forecast_closing_rate
var_vpg = proj_vpg - forecast_vpg
var_avg_price = proj_avg_price - forecast_avg_price

st.subheader("Projected vs Forecast")

v1, v2, v3, v4 = st.columns(4)

with v1:
    st.metric(
        "Arrivals",
        f"{proj_arrivals:,.0f}",
        f"{var_arrivals:+,.0f}"
    )

with v2:
    st.metric(
        "Qs",
        f"{proj_qs:,.0f}",
        f"{var_qs:+,.0f}"
    )

with v3:
    st.metric(
        "Contracts",
        f"{proj_contracts:,.0f}",
        f"{var_contracts:+,.0f}"
    )

with v4:
    st.metric(
        "Volume",
        f"${proj_volume:,.0f}",
        f"${var_volume:+,.0f}"
    )

v5, v6, v7, v8 = st.columns(4)

with v5:
    st.metric(
        "Penetration",
        f"{proj_penetration:.2f}%",
        f"{var_penetration_pp:+.2f} pp"
    )

with v6:
    st.metric(
        "Closing Rate",
        f"{proj_closing_rate:.2f}%",
        f"{var_closing_pp:+.2f} pp"
    )

with v7:
    st.metric(
        "VPG",
        f"${proj_vpg:,.0f}",
        f"${var_vpg:+,.0f}"
    )

with v8:
    st.metric(
        "Average Price",
        f"${proj_avg_price:,.0f}",
        f"${var_avg_price:+,.0f}"
    )

    #test
