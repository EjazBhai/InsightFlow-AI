"""InsightFlow dashboard. Start with: streamlit run apps/streamlit_app/app.py"""
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from insightflow.agent import AnalyticsAgent  # noqa: E402
from insightflow.config import get_settings  # noqa: E402
from insightflow.database import AnalyticsRepository  # noqa: E402

st.set_page_config(page_title="InsightFlow AI", page_icon="✦", layout="wide")
st.markdown("""<style>
.stApp { background: #f7f9fc; } .block-container { padding-top: 2rem; max-width: 1400px; }
[data-testid='stMetric'] { background: white; border: 1px solid #e5eaf2; border-radius: 14px; padding: 14px; }
</style>""", unsafe_allow_html=True)

settings = get_settings()
repository = AnalyticsRepository(settings)


def rows(sql: str) -> pd.DataFrame:
    return pd.DataFrame(repository.execute(sql))


st.sidebar.title("✦ InsightFlow AI")
page = st.sidebar.radio("Workspace", ["Executive overview", "AI analyst", "Sales explorer", "Data quality", "Settings"])
st.sidebar.caption("Local-first • SQL verified • UCI Online Retail")

try:
    if page == "Executive overview":
        st.title("Executive overview")
        st.caption("Revenue is sales value, not profit. Net sales include negative return/cancellation lines.")
        summary = repository.summary()
        cols = st.columns(5)
        for col, (label, key) in zip(cols, [("Gross sales", "gross_sales"), ("Net sales", "net_sales"), ("Invoices", "invoices"), ("Products", "products"), ("Customers", "customers")], strict=True):
            col.metric(label, f"£{summary[key]:,.2f}" if "sales" in key else f"{summary[key]:,}")
        trend = rows("SELECT date_trunc('month', invoice_date) AS month, SUM(revenue) AS net_sales FROM transactions GROUP BY month ORDER BY month")
        left, right = st.columns(2)
        left.plotly_chart(px.line(trend, x="month", y="net_sales", markers=True, title="Monthly net sales"), use_container_width=True)
        countries = rows("SELECT country, SUM(revenue) AS net_sales FROM transactions GROUP BY country ORDER BY net_sales DESC")
        right.plotly_chart(px.bar(countries, x="country", y="net_sales", title="Sales by country"), use_container_width=True)
        st.subheader("Top products")
        st.dataframe(rows("SELECT description, SUM(revenue) AS net_sales, SUM(quantity) AS units FROM transactions GROUP BY description ORDER BY net_sales DESC"), use_container_width=True, hide_index=True)
    elif page == "AI analyst":
        st.title("Ask the AI analyst")
        st.caption("Answers run through a bounded LangGraph workflow and SELECT-only SQL policy.")
        question = st.chat_input("e.g. What were monthly sales trends?")
        if question:
            with st.chat_message("user"): st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("Planning and validating query…"):
                    result = AnalyticsAgent(repository).query(question)
                st.write(result.answer)
                st.caption(f"{result.status} • {result.latency_ms} ms • request {result.request_id}")
                if result.chart and result.data:
                    st.plotly_chart(px.bar(pd.DataFrame(result.data), x=result.chart.x, y=result.chart.y, title=result.chart.title) if result.chart.kind == "bar" else px.line(pd.DataFrame(result.data), x=result.chart.x, y=result.chart.y, title=result.chart.title), use_container_width=True)
                with st.expander("Evidence, definitions, and SQL"):
                    st.write(result.metric_definitions)
                    st.code(result.sql or "No SQL executed", language="sql")
                    st.dataframe(pd.DataFrame(result.data), hide_index=True)
                if result.warnings: st.warning(" ".join(result.warnings))
    elif page == "Sales explorer":
        st.title("Sales explorer")
        data = rows("SELECT * FROM transactions ORDER BY invoice_date DESC")
        selected_countries = st.multiselect("Country", sorted(data.country.dropna().unique()))
        if selected_countries: data = data[data.country.isin(selected_countries)]
        st.dataframe(data, use_container_width=True, hide_index=True)
        st.download_button("Download filtered CSV", data.to_csv(index=False), "insightflow_export.csv", "text/csv")
    elif page == "Data quality":
        st.title("Data quality")
        st.json(repository.quality())
        st.info("Cancellations and negative quantities are retained. Missing customer IDs are not imputed.")
    else:
        st.title("Settings & provenance")
        st.write({"model_provider": settings.model_provider, "model_name": settings.model_name, "database": str(settings.database_path)})
        st.markdown("Dataset: UCI Machine Learning Repository, Online Retail Data Set (Chen, 2015).")
except Exception as exc:
    st.error("Dataset is not ready. Run `python scripts/prepare_data.py` first.")
    st.exception(exc)
