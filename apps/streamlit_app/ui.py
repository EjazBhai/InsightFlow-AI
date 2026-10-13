
"""Shared visual language and presentation helpers for the Streamlit workspace."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

COLORS = {
    "indigo": "#6366F1",
    "blue": "#3B82F6",
    "purple": "#8B5CF6",
    "teal": "#14B8A6",
    "emerald": "#10B981",
    "coral": "#FB7185",
    "amber": "#F59E0B",
    "navy": "#172033",
    "slate": "#64748B",
    "border": "#E2E8F0",
    "canvas": "#F5F7FF",
}

DISPLAY_COLUMNS = {
    "invoice_no": "Invoice number",
    "stock_code": "Stock code",
    "description": "Product description",
    "quantity": "Quantity",
    "invoice_date": "Invoice date",
    "unit_price": "Unit price",
    "customer_id": "Customer ID",
    "country": "Country",
    "is_cancellation": "Cancellation",
    "revenue": "Revenue",
    "net_sales": "Net sales",
    "gross_sales": "Gross sales",
    "units": "Units",
}


def inject_styles() -> None:
    """Apply the branded dashboard theme and improve control contrast."""
    st.html(f"""<style>
    .stApp {{background:{COLORS["canvas"]}; color:{COLORS["navy"]};}}

    [data-testid="stSidebar"] {{
        background:linear-gradient(180deg,#172033 0%,#28245B 100%);
    }}
    [data-testid="stSidebar"] * {{color:#F8FAFC;}}
    [data-testid="stSidebar"] .stRadio label {{
        border-radius:10px;
        padding:5px 8px;
    }}

    h1,h2,h3,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {{
        color:{COLORS["navy"]} !important;
    }}

    [data-testid="stMetric"] {{
        background:#FFFFFF;
        border:1px solid {COLORS["border"]};
        border-radius:16px;
        padding:18px;
        box-shadow:0 5px 18px rgba(15,23,42,.06);
    }}

    [data-testid="stDataFrame"] {{
        border:1px solid {COLORS["border"]};
        border-radius:12px;
        overflow:hidden;
    }}

    .if-hero {{
        background:linear-gradient(120deg,#4F46E5,#7C3AED);
        padding:1.6rem 1.8rem;
        border-radius:20px;
        color:#FFFFFF;
        margin-bottom:1.2rem;
    }}
    .if-hero h1,
    .if-hero p {{
        color:#FFFFFF !important;
        margin:0;
    }}
    .if-hero p {{
        opacity:.88;
        margin-top:.4rem;
    }}

    .if-kpi-note {{
        color:{COLORS["slate"]};
        font-size:.78rem;
        margin-top:.35rem;
    }}

    .if-card {{
        background:#FFFFFF;
        border:1px solid {COLORS["border"]};
        border-radius:16px;
        padding:1rem 1.2rem;
        box-shadow:0 5px 18px rgba(15,23,42,.05);
    }}
    .if-card h3 {{
        margin:0 0 .25rem 0;
        color:{COLORS["navy"]} !important;
        font-size:1rem;
    }}
    .if-card p {{
        margin:0;
        color:{COLORS["slate"]};
        font-size:.86rem;
    }}

    .if-status {{
        background:rgba(16,185,129,.15);
        border-radius:9px;
        padding:.45rem .55rem;
        color:#D1FAE5 !important;
        font-size:.78rem;
    }}

    /* Select boxes */
    .stApp [data-baseweb="select"] > div {{
        background-color:#FFFFFF !important;
        color:#172033 !important;
        border-color:#CBD5E1 !important;
    }}
    .stApp [data-baseweb="select"] input,
    .stApp [data-baseweb="select"] [data-testid="stMarkdownContainer"],
    .stApp [data-baseweb="select"] span {{
        color:#172033 !important;
    }}

    /* Text inputs and text areas */
    .stApp [data-baseweb="input"] > div,
    .stApp [data-baseweb="textarea"] > div {{
        background-color:#FFFFFF !important;
        border-color:#CBD5E1 !important;
    }}
    .stApp [data-baseweb="input"] input,
    .stApp [data-baseweb="textarea"] textarea {{
        background-color:#FFFFFF !important;
        color:#172033 !important;
        -webkit-text-fill-color:#172033 !important;
        border-color:#CBD5E1 !important;
    }}

    /* Buttons, suggested questions, and downloads */
    .stApp [data-testid="stButton"] button,
    .stApp [data-testid="stFormSubmitButton"] button,
    .stApp [data-testid="stDownloadButton"] button {{
        background-color:#FFFFFF !important;
        color:#4338CA !important;
        border:1px solid #C7D2FE !important;
        border-radius:10px !important;
    }}
    .stApp [data-testid="stButton"] button *,
    .stApp [data-testid="stFormSubmitButton"] button *,
    .stApp [data-testid="stDownloadButton"] button * {{
        color:#4338CA !important;
        -webkit-text-fill-color:#4338CA !important;
    }}
    .stApp [data-testid="stButton"] button:hover,
    .stApp [data-testid="stFormSubmitButton"] button:hover,
    .stApp [data-testid="stDownloadButton"] button:hover {{
        background-color:#EEF2FF !important;
        border-color:#A5B4FC !important;
    }}

    /* Labels on the light content canvas */
    .stApp label,
    .stApp [data-testid="stWidgetLabel"] p {{
        color:#334155 !important;
    }}

    @media (max-width:700px) {{
        .block-container {{padding:1rem;}}
        .if-hero {{padding:1.2rem;}}
    }}
    </style>""")


def hero(
    title: str,
    subtitle: str,
    eyebrow: str = "INSIGHTFLOW AI",
) -> None:
    """Render the branded page heading."""
    st.html(
        f'<div class="if-hero"><p>{eyebrow}</p>'
        f'<h1>{title}</h1><p>{subtitle}</p></div>'
    )


def kpi(
    label: str,
    value: str,
    icon: str,
    note: str,
    accent: str,
) -> None:
    """Render a KPI card."""
    with st.container(border=True):
        st.markdown(f":material/{icon}:  **{label}**")
        st.markdown(f"## {value}")
        st.html(f'<p class="if-kpi-note">{note}</p>')


def display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Format analytical data for display without changing the source frame."""
    visible = frame.copy()

    if "invoice_date" in visible:
        visible["invoice_date"] = (
            pd.to_datetime(visible["invoice_date"]).dt.strftime("%d %b %Y")
        )

    for field in ("revenue", "net_sales", "gross_sales", "unit_price"):
        if field in visible:
            visible[field] = visible[field].map(
                lambda value: f"£{value:,.2f}" if pd.notna(value) else "—"
            )

    if "is_cancellation" in visible:
        visible["is_cancellation"] = visible["is_cancellation"].map(
            {True: "Yes", False: "No"}
        )

    return visible.rename(
        columns={
            column: DISPLAY_COLUMNS.get(
                column, column.replace("_", " ").title()
            )
            for column in visible.columns
        }
    )


def plot_layout(title: str) -> dict[str, Any]:
    """Return shared Plotly styling for dashboard charts."""
    return {
        "title": {"text": title, "font": {"color": COLORS["navy"], "size": 18}},
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor": "#FFFFFF",
        "font": {"color": COLORS["slate"]},
        "margin": {"l": 22, "r": 16, "t": 54, "b": 24},
        "xaxis": {
            "gridcolor": "#F1F5F9",
            "linecolor": COLORS["border"],
        },
        "yaxis": {
            "gridcolor": "#EAF0F7",
            "linecolor": COLORS["border"],
        },
    }


def chart_line(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: str,
) -> go.Figure:
    """Create a branded line chart."""
    figure = go.Figure(
        go.Scatter(
            x=frame[x],
            y=frame[y],
            mode="lines+markers",
            line={"color": COLORS["indigo"], "width": 3},
            marker={"size": 8, "color": COLORS["purple"]},
            fill="tozeroy",
            fillcolor="rgba(99,102,241,.10)",
        )
    )
    figure.update_layout(
        **plot_layout(title),
        showlegend=False,
        hovermode="x unified",
    )
    figure.update_yaxes(tickprefix="£")
    return figure


def chart_bar(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str = "#14B8A6",
) -> go.Figure:
    """Create a branded bar chart."""
    figure = go.Figure(
        go.Bar(
            x=frame[x],
            y=frame[y],
            marker_color=color,
            marker_line_width=0,
            hovertemplate="%{x}<br>£%{y:,.2f}<extra></extra>",
        )
    )
    figure.update_layout(**plot_layout(title), showlegend=False)
    figure.update_yaxes(tickprefix="£")
    return figure
