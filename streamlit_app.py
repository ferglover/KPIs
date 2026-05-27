import html
from pathlib import Path
from datetime import datetime, timedelta
import calendar

import pandas as pd
import streamlit as st

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="KPI Calculator",
    layout="wide"
)

# =====================================
# SIMPLE LOGIN
# =====================================



# =====================================
# THEME HELPERS
# =====================================

def theme_colors():
    return {
        "bg": "#0e1117",
        "card_bg": "rgba(255,255,255,0.03)",
        "text": "#f5f7fa",
        "muted": "rgba(245,247,250,0.70)",
        "border": "rgba(255,255,255,0.12)",
        "header_bg": "#0e1117",
        "sticky_bg": "#0e1117",
        "positive": "#28a745",
        "negative": "#dc3545",
    }

    return {
        "bg": "#0e1117",
        "card_bg": "rgba(255,255,255,0.03)",
        "text": "#f5f7fa",
        "muted": "rgba(245,247,250,0.70)",
        "border": "rgba(255,255,255,0.12)",
        "header_bg": "#0e1117",
        "sticky_bg": "#0e1117",
        "positive": "#28a745",
        "negative": "#dc3545",
    }

COLORS = theme_colors()

# =====================================
# STYLES
# =====================================

st.markdown(
    f"""
    <style>
    .block-container {{
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 1rem;
    }}

    /* INPUT EDITABLE */
    div[data-baseweb="input"] input {{
        font-size: 28px !important;
        font-weight: 500 !important;
    }}

    /* BOTONES + / - */
    button[data-testid="stNumberInputStepUp"],
    button[data-testid="stNumberInputStepDown"] {{
        height: 32px !important;
        width: 32px !important;
    }}

    /* LABEL DEL INPUT */
    label[data-testid="stWidgetLabel"] p {{
        font-size: 14px !important;
        font-weight: 700 !important;
    }}

    .section-title {{
        font-size: 20px;
        font-weight: 800;
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
    }}

    .matrix-scroll {{
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }}

    .matrix-table {{
        width: 100%;
        min-width: 980px;
        border-collapse: separate;
        border-spacing: 0 10px;
    }}

    .matrix-table thead th {{
        font-size: 13px;
        font-weight: 800;
        padding: 8px 10px 12px 10px;
        text-align: center;
        border-bottom: 1px solid {COLORS["border"]};
        white-space: nowrap;
        background: {COLORS["header_bg"]};
        color: {COLORS["text"]};
    }}

    .matrix-table thead th:first-child,
    .matrix-table tbody td:first-child {{
        position: sticky;
        left: 0;
        z-index: 3;
        background: {COLORS["header_bg"]};
        text-align: left !important;
        color: {COLORS["text"]};
    }}

    .matrix-table thead th:first-child {{
        z-index: 4;
    }}

    .matrix-kpi-cell {{
        font-size: 14px;
        font-weight: 700;
        padding-top: 12px;
        line-height: 1.15;
        min-width: 30px;
        color: {COLORS["text"]};
    }}

    .matrix-value-card {{
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 12px 12px 10px 12px;
        min-height: 1.15px;
        background: {COLORS["card_bg"]};
        display: flex;
        align-items: center;
    }}

    .matrix-value {{
        font-size: 14px;
        font-weight: 700;
        line-height: 1.1;
        word-break: break-word;
        color: {COLORS["text"]};
    }}

    .matrix-value.positive {{
        color: {COLORS["positive"]};
    }}

    .matrix-value.negative {{
        color: {COLORS["negative"]};
    }}

    .matrix-value.neutral {{
        color: {COLORS["text"]};
    }}

    @media (max-width: 768px) {{
        .matrix-table {{
            min-width: 860px;
        }}

        .matrix-value {{
            font-size: 18px;
        }}

        .matrix-kpi-cell {{
            font-size: 13px;
            min-width: 150px;
        }}

        .section-title {{
            font-size: 18px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

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

    df.columns = (
        df.columns
        .str.replace("[", "", regex=False)
        .str.replace("]", "", regex=False)
        .str.strip()
    )

    return df

# =====================================
# LOAD FORECAST DATA
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

    def clean_metric(x):
        x = str(x).strip()

        if "Penetr" in x:
            return "Penetration"

        x = x.replace("Q’s", "Qs").replace("Q´s", "Qs").replace("Q's", "Qs")
        x = x.replace("Contracts ", "Contracts").replace("Average Price ", "Average Price")
        x = x.replace("Closing Rate ", "Closing Rate").replace("VPG ", "VPG")
        x = x.replace("Volume ", "Volume").replace("Arrivals ", "Arrivals")

        return x

    df["Metric"] = df["Metric"].apply(clean_metric)

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
# TITLE / LEGEND
# =====================================

st.title("Calculadora BI")

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
# HELPERS
# =====================================

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

def fmt_matrix(kind, value, variance=False):
    if kind == "int":
        return f"{value:+,.0f}" if variance else f"{value:,.0f}"
    if kind == "money":
        return f"${value:+,.0f}" if variance else f"${value:,.0f}"
    if kind == "pct":
        return f"{value:+.2f} pp" if variance else f"{value:.2f}%"
    return str(value)

def value_card(value, tone="neutral"):
    return f"""
    <div class="matrix-value-card">
        <div class="matrix-value {tone}">{html.escape(value)}</div>
    </div>
    """

def render_matrix(rows):
    html_out = f"""
    <html>
    <head>
      <style>
        body {{
          margin: 0;
          padding: 0;
          background: {COLORS["bg"]};
          color: {COLORS["text"]};
          font-family: sans-serif;
        }}

        .matrix-shell {{
            background: {COLORS["bg"]};
            border-radius: 14px;
            padding: 8px 0 0 0;
        }}

        .matrix-scroll {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}

        .matrix-table {{
            width: 100%;
            min-width: 980px;
            border-collapse: separate;
            border-spacing: 0 10px;
        }}

        .matrix-table thead th {{
            font-size: 13px;
            font-weight: 800;
            padding: 8px 10px 12px 10px;
            text-align: center;
            border-bottom: 1px solid {COLORS["border"]};
            white-space: nowrap;
            background: {COLORS["header_bg"]};
            color: {COLORS["text"]};
        }}

        .matrix-table thead th:first-child,
        .matrix-table tbody td:first-child {{
            position: sticky;
            left: 0;
            z-index: 3;
            background: {COLORS["sticky_bg"]};
            text-align: left !important;
            color: {COLORS["text"]};
        }}

        .matrix-table thead th:first-child {{
            z-index: 4;
        }}

        .matrix-kpi-cell {{
            font-size: 14px;
            font-weight: 700;
            padding-top: 12px;
            line-height: 1.15;
            min-width: 90px;
            color: {COLORS["text"]};
        }}

        .matrix-value-card {{
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
            padding: 12px 12px 10px 12px;
            min-height: 82px;
            background: {COLORS["card_bg"]};
            display: flex;
            align-items: center;
        }}

        .matrix-value {{
            font-size: 22px;
            font-weight: 700;
            line-height: 1.1;
            word-break: break-word;
            color: {COLORS["text"]};
        }}

        .matrix-value.positive {{
            color: {COLORS["positive"]};
        }}

        .matrix-value.negative {{
            color: {COLORS["negative"]};
        }}

        .matrix-value.neutral {{
            color: {COLORS["text"]};
        }}

        @media (max-width: 768px) {{
            .matrix-table {{
                min-width: 860px;
            }}

            .matrix-value {{
                font-size: 18px;
            }}

            .matrix-kpi-cell {{
                font-size: 13px;
                min-width: 150px;
            }}
        }}
      </style>
    </head>
    <body>
      <div class="matrix-shell">
        <div class="matrix-scroll">
          <table class="matrix-table">
            <thead>
              <tr>
                <th style="text-align:left;">KPI</th>
                <th>Actuals KPIs</th>
                <th>Projected KPIs to Month End</th>
                <th>Forecast Targets</th>
                <th>Projected vs Forecast</th>
              </tr>
            </thead>
            <tbody>
    """

    for label, actual, projected, forecast, variance, kind in rows:
        tone = "neutral"
        if variance > 0:
            tone = "positive"
        elif variance < 0:
            tone = "negative"

        html_out += f"""
              <tr>
                <td>
                  <div class="matrix-kpi-cell">{html.escape(label)}</div>
                </td>
                <td>{value_card(fmt_matrix(kind, actual), tone="neutral")}</td>
                <td>{value_card(fmt_matrix(kind, projected), tone="neutral")}</td>
                <td>{value_card(fmt_matrix(kind, forecast), tone="neutral")}</td>
                <td>{value_card(fmt_matrix(kind, variance, variance=True), tone=tone)}</td>
              </tr>
        """

    html_out += """
            </tbody>
          </table>
        </div>
      </div>
    </body>
    </html>
    """

    height = 140 + (len(rows) * 96)
    st.components.v1.html(html_out, height=height, scrolling=True)

# =====================================
# ACTUAL INPUTS
# =====================================

st.markdown("<div class='section-title'>Actuals KPIs</div>", unsafe_allow_html=True)

i1, i2, i3, i4 = st.columns(4, gap="small")

with i1:
    arrivals = input_card(
        "Arrivals",
        int(round(float(row["Arrivals"]))),
        step=1,
        fmt="%d"
    )

with i2:
    contracts = input_card(
        "Contracts Processable",
        int(round(float(row["Contracts Processable"]))),
        step=1,
        fmt="%d"
    )

with i3:
    closing_rate = input_card(
        "Closing Rate %",
        float(row["Closing Rate"]) * 100 if float(row["Closing Rate"]) <= 1 else float(row["Closing Rate"]),
        step=0.1,
        fmt="%.1f"
    )

with i4:
    avg_price = input_card(
        "Average Price ($)",
        int(round(float(row["Average Price"]))),
        step=100,
        fmt="%d"
    )

# =====================================
# ACTUAL CALCULATIONS
# =====================================

qs = contracts / (closing_rate / 100) if closing_rate else 0
penetration = (qs / arrivals * 100) if arrivals else 0
volume = contracts * avg_price
vpg = volume / qs if qs else 0

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

# =====================================
# FORECAST TARGETS
# =====================================

forecast_arrivals = float(forecast_row.get("Arrivals", 0))

forecast_penetration = float(forecast_row.get("Penetration", 0))
if forecast_penetration <= 1:
    forecast_penetration *= 100

forecast_qs = float(forecast_row.get("Qs", 0))
forecast_contracts = float(forecast_row.get("Contracts", 0))
forecast_avg_price = float(forecast_row.get("Average Price", 0))

forecast_closing_rate = float(forecast_row.get("Closing Rate", 0))
if forecast_closing_rate <= 1:
    forecast_closing_rate *= 100

forecast_vpg = float(forecast_row.get("VPG", 0))
forecast_volume = float(forecast_row.get("Volume", 0))

# =====================================
# VARIANCES
# =====================================

var_arrivals = proj_arrivals - forecast_arrivals
var_contracts = proj_contracts - forecast_contracts
var_qs = proj_qs - forecast_qs
var_volume = proj_volume - forecast_volume
var_penetration_pp = proj_penetration - forecast_penetration
var_closing_pp = proj_closing_rate - forecast_closing_rate
var_vpg = proj_vpg - forecast_vpg
var_avg_price = proj_avg_price - forecast_avg_price

# =====================================
# MATRIX
# =====================================

st.markdown("<div class='section-title'>KPI Matrix</div>", unsafe_allow_html=True)
st.caption(
    f"Projection based on {legend_date.strftime('%B %d, %Y')} | {days_remaining} days remaining"
)

matrix_rows = [
    ("Arrivals", arrivals, proj_arrivals, forecast_arrivals, var_arrivals, "int"),
    ("Contracts", contracts, proj_contracts, forecast_contracts, var_contracts, "int"),
    ("Closing Rate", closing_rate, proj_closing_rate, forecast_closing_rate, var_closing_pp, "pct"),
    ("Average Price", avg_price, proj_avg_price, forecast_avg_price, var_avg_price, "money"),
    ("Qs", qs, proj_qs, forecast_qs, var_qs, "int"),
    ("Penetration", penetration, proj_penetration, forecast_penetration, var_penetration_pp, "pct"),
    ("VPG", vpg, proj_vpg, forecast_vpg, var_vpg, "money"),
    ("Volume", volume, proj_volume, forecast_volume, var_volume, "money"),
]

render_matrix(matrix_rows)
