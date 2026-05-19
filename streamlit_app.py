import math
from functools import partial

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Calculadora BI de Sensibilidad",
    page_icon=":bar_chart:",
    layout="wide",
)


# -----------------------------
# Helpers
# -----------------------------

def fmt_int(n: float) -> str:
    return f"{int(round(float(n) if n is not None else 0)):,}"


def fmt_money(n: float) -> str:
    return f"${int(round(float(n) if n is not None else 0)):,}"


def fmt_pct(n: float) -> str:
    return f"{float(n):.1f}%"


def calc_all(state: dict, driver: str = "default") -> dict:
    arrivals = float(state["arrivals"])
    qs = float(state["qs"])
    contracts = float(state["contracts"])
    avg_price = float(state["avg_price"])
    closing = float(state["closing"])
    penetration = float(state["penetration"])
    vpg = float(state["vpg"])
    volume = float(state["volume"])

    if driver in {"arrivals", "qs"}:
        penetration = (qs / arrivals) * 100 if arrivals > 0 else 0
        contracts = qs * (closing / 100)
        volume = contracts * avg_price
        vpg = volume / qs if qs > 0 else 0
    elif driver == "contracts":
        closing = (contracts / qs) * 100 if qs > 0 else 0
        volume = contracts * avg_price
        vpg = volume / qs if qs > 0 else 0
    elif driver == "avg_price":
        volume = contracts * avg_price
        vpg = volume / qs if qs > 0 else 0
    elif driver == "closing":
        contracts = qs * (closing / 100)
        volume = contracts * avg_price
        vpg = volume / qs if qs > 0 else 0
    elif driver == "penetration":
        qs = arrivals * (penetration / 100)
        contracts = qs * (closing / 100)
        volume = contracts * avg_price
        vpg = volume / qs if qs > 0 else 0
    elif driver == "vpg":
        volume = vpg * qs
        avg_price = volume / contracts if contracts > 0 else avg_price
    elif driver == "volume":
        avg_price = volume / contracts if contracts > 0 else avg_price
        vpg = volume / qs if qs > 0 else 0
    else:
        penetration = (qs / arrivals) * 100 if arrivals > 0 else 0
        closing = (contracts / qs) * 100 if qs > 0 else 0
        volume = contracts * avg_price
        vpg = volume / qs if qs > 0 else 0

    return {
        "arrivals": arrivals,
        "qs": qs,
        "contracts": contracts,
        "avg_price": avg_price,
        "closing": closing,
        "penetration": penetration,
        "vpg": vpg,
        "volume": volume,
    }


def sensitivity_table(c: dict) -> pd.DataFrame:
    rows = []
    previous_volume = None
    start_pen = c["penetration"]

    p = start_pen
    while p <= start_pen + 8.0 + 0.0001:
        raw_qs = c["arrivals"] * (p / 100)
        qs_int = round(raw_qs)
        raw_contracts = raw_qs * (c["closing"] / 100)
        contracts_int = round(raw_contracts)
        row_volume = contracts_int * c["avg_price"]
        row_vpg = row_volume / qs_int if qs_int > 0 else 0
        delta = None if previous_volume is None else row_volume - previous_volume
        rows.append(
            {
                "Penetration": p,
                "Q’s": qs_int,
                "Contratos": contracts_int,
                "VPG": row_vpg,
                "Volumen": row_volume,
                "Incremento marginal": delta,
            }
        )
        previous_volume = row_volume
        p = round(p + 1.0, 1)

    return pd.DataFrame(rows)


# -----------------------------
# Session state
# -----------------------------
DEFAULTS = {
    "arrivals": 32514,
    "qs": 2845,
    "contracts": 484,
    "avg_price": 20576,
    "closing": 17.0,
    "penetration": 8.7,
    "vpg": 3511,
    "volume": 9980000,
}

for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

st.session_state.setdefault("driver", "default")


def sync(driver_name: str) -> None:
    state = {k: st.session_state[k] for k in DEFAULTS}
    calculated = calc_all(state, driver_name)
    for k, v in calculated.items():
        st.session_state[k] = v
    st.session_state["driver"] = driver_name


def reset_all() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    sync("default")


# -----------------------------
# UI
# -----------------------------
st.title("Calculadora BI de Sensibilidad")
st.caption("Edita la base o cualquiera de los KPIs y la calculadora resolverá automáticamente el resto.")

with st.sidebar:
    st.subheader("Datos de entrada")
    driver_labels = {
        "default": "Auto",
        "arrivals": "Arrivals",
        "qs": "Q’s",
        "contracts": "Contracts",
        "avg_price": "Avg Price",
        "closing": "Closing",
        "penetration": "Penetration",
        "vpg": "VPG",
        "volume": "Volume",
    }
    st.selectbox(
        "Variable que gobierna el cálculo",
        options=list(driver_labels.keys()),
        format_func=lambda x: driver_labels[x],
        key="driver_selector",
        on_change=lambda: sync(st.session_state.driver_selector),
    )

    st.number_input("Arrivals", min_value=0, step=1, key="arrivals", on_change=partial(sync, "arrivals"))
    st.number_input("Q’s", min_value=0, step=1, key="qs", on_change=partial(sync, "qs"))
    st.number_input("Contracts", min_value=0, step=1, key="contracts", on_change=partial(sync, "contracts"))
    st.number_input("Avg Price", min_value=0, step=1, key="avg_price", on_change=partial(sync, "avg_price"))

    if st.button("Reset", use_container_width=True):
        reset_all()


# Keep the screen in sync on the first load or after reset.
if st.session_state.driver == "default":
    sync("default")

c = {k: st.session_state[k] for k in DEFAULTS}

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("KPIs")
    k1, k2 = st.columns(2)
    with k1:
        st.metric("Arrivals", fmt_int(c["arrivals"]))
        st.metric("Contracts", fmt_int(c["contracts"]))
        st.metric("Closing", fmt_pct(c["closing"]))
        st.metric("VPG", fmt_money(c["vpg"]))
    with k2:
        st.metric("Q’s", fmt_int(c["qs"]))
        st.metric("Avg Price", fmt_money(c["avg_price"]))
        st.metric("Penetration", fmt_pct(c["penetration"]))
        st.metric("Volume", fmt_money(c["volume"]))

    st.subheader("Lectura automática")
    one_pp = c["arrivals"] * 0.01 * (c["closing"] / 100) * c["avg_price"]
    st.write(
        f"Base cargada: {fmt_int(c['arrivals'])} arrivals, {fmt_int(c['qs'])} Q’s, "
        f"{fmt_int(c['contracts'])} contratos y {fmt_money(c['volume'])} de volumen. "
        f"Eso equivale a {fmt_pct(c['penetration'])} de penetración, {fmt_pct(c['closing'])} de closing, "
        f"{fmt_money(c['avg_price'])} de avg price y {fmt_money(c['vpg'])} de VPG. "
        f"Cada +1 pp adicional de penetración agrega aproximadamente {fmt_int(c['arrivals'] / 100)} Q’s, "
        f"{fmt_int((c['arrivals'] / 100) * (c['closing'] / 100))} contratos y {fmt_money(one_pp)} de volumen, "
        f"manteniendo constantes el closing y el precio promedio."
    )

with right:
    st.subheader("Tabla de sensibilidad por +1 pp de penetración")
    st.caption("Basada en la base actual")
    df = sensitivity_table(c)
    df_display = df.copy()
    df_display["Penetration"] = df_display["Penetration"].map(lambda x: f"{x:.1f}%")
    df_display["Q’s"] = df_display["Q’s"].map(fmt_int)
    df_display["Contratos"] = df_display["Contratos"].map(fmt_int)
    df_display["VPG"] = df_display["VPG"].map(fmt_money)
    df_display["Volumen"] = df_display["Volumen"].map(fmt_money)
    df_display["Incremento marginal"] = df_display["Incremento marginal"].map(lambda x: "—" if pd.isna(x) else fmt_money(x))
    st.dataframe(df_display, use_container_width=True, hide_index=True)

