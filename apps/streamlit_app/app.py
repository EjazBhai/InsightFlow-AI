"""InsightFlow's vibrant, local-first Streamlit analytics workspace."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ui import COLORS, chart_bar, chart_line, display_frame, hero, inject_styles, kpi  # noqa: E402

from insightflow import __version__  # noqa: E402
from insightflow.agent import AnalyticsAgent  # noqa: E402
from insightflow.config import get_settings  # noqa: E402
from insightflow.database import AnalyticsRepository  # noqa: E402

st.set_page_config(page_title="InsightFlow AI", page_icon=":material/analytics:", layout="wide")
inject_styles()
settings = get_settings()


@st.cache_resource
def get_repository(database_path: str, data_dir: str) -> AnalyticsRepository:
    return AnalyticsRepository(get_settings())


repository = get_repository(str(settings.database_path), str(settings.data_dir))


@st.cache_data(ttl="5m", show_spinner=False)
def query_frame(sql: str) -> pd.DataFrame:
    return pd.DataFrame(repository.execute(sql))


def initialize_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("analyst_question", "")


def submit_example(question: str) -> None:
    st.session_state["analyst_question"] = question


def shell() -> str:
    labels = {
        "Executive overview": ":material/dashboard:  Executive overview",
        "AI analyst": ":material/auto_awesome:  AI analyst",
        "Sales explorer": ":material/travel_explore:  Sales explorer",
        "Data quality": ":material/verified:  Data quality",
        "Settings": ":material/settings:  Settings",
    }
    with st.sidebar:
        st.title("InsightFlow AI", icon=":material/insights:")
        st.caption("Intelligent business analytics")
        st.space("small")
        page = st.radio(
            "Workspace navigation",
            list(labels),
            format_func=labels.get,
            label_visibility="collapsed",
        )
        st.space("large")
        st.html('<div class="if-status">● Local data · SQL protected</div>')
        st.space("small")
        st.caption(f"v{__version__} · {settings.model_provider} mode")
    return page


def executive_overview() -> None:
    hero(
        "Executive overview",
        "A clear, evidence-led view of retail performance.",
        "LIVE RETAIL SNAPSHOT",
    )
    try:
        summary = repository.summary()
        st.caption("Values use the source dataset currency. Revenue is sales value, not profit.")
        metrics = [
            (
                "Gross sales",
                f"£{summary['gross_sales']:,.2f}",
                "payments",
                "Positive quantity only",
                "indigo",
            ),
            (
                "Net sales",
                f"£{summary['net_sales']:,.2f}",
                "account_balance",
                "Includes returns",
                "blue",
            ),
            (
                "Invoices",
                f"{summary['invoices']:,}",
                "receipt_long",
                "Distinct invoice numbers",
                "purple",
            ),
            ("Products", f"{summary['products']:,}", "inventory_2", "Unique stock codes", "teal"),
            ("Customers", f"{summary['customers']:,}", "groups", "Identified customers", "emerald"),
        ]
        for column, metric in zip(st.columns(5), metrics, strict=True):
            with column:
                kpi(*metric)
        trend = query_frame(
            "SELECT date_trunc('month', invoice_date) AS month, SUM(revenue) AS net_sales FROM transactions GROUP BY month ORDER BY month"
        )
        countries = query_frame(
            "SELECT country, SUM(revenue) AS net_sales FROM transactions GROUP BY country ORDER BY net_sales DESC"
        )
        left, right = st.columns(2)
        with left, st.container(border=True):
            st.plotly_chart(
                chart_line(trend, "month", "net_sales", "Monthly net sales"),
                width="stretch",
                key="monthly_sales_chart",
            )
        with right, st.container(border=True):
            st.plotly_chart(
                chart_bar(countries, "country", "net_sales", "Sales by country", COLORS["teal"]),
                width="stretch",
                key="country_sales_chart",
            )
        st.subheader("Top products", icon=":material/leaderboard:")
        products = query_frame(
            "SELECT description, SUM(revenue) AS net_sales, SUM(quantity) AS units FROM transactions GROUP BY description ORDER BY net_sales DESC"
        )
        st.dataframe(
            display_frame(products), hide_index=True, width="stretch", key="top_products_table"
        )
    except Exception as exc:
        st.error(
            "The analytics dataset is not ready. Run `python scripts/prepare_data.py` and refresh this page.",
            icon=":material/error:",
        )
        st.caption(str(exc))


def render_response(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant", avatar=":material/auto_awesome:"):
        with st.status("Validating your analytical request", expanded=False) as status:
            result = AnalyticsAgent(repository).query(question)
            status.update(
                label="Analysis complete"
                if result.status == "success"
                else "Analysis needs attention",
                state="complete" if result.status == "success" else "error",
            )
        if result.status == "success":
            st.success(result.answer, icon=":material/check_circle:")
        else:
            st.error(result.answer, icon=":material/error:")
        if result.data:
            result_frame = pd.DataFrame(result.data)
            if result.chart:
                figure = (
                    chart_bar(
                        result_frame,
                        result.chart.x,
                        result.chart.y,
                        result.chart.title,
                        COLORS["purple"],
                    )
                    if result.chart.kind == "bar"
                    else chart_line(
                        result_frame, result.chart.x, result.chart.y, result.chart.title
                    )
                )
                st.plotly_chart(figure, width="stretch", key=f"agent_chart_{result.request_id}")
            with st.expander("View evidence and SQL", icon=":material/visibility:"):
                for definition in result.metric_definitions:
                    st.caption(definition)
                st.code(result.sql or "No query was run.", language="sql")
                st.dataframe(
                    display_frame(result_frame),
                    hide_index=True,
                    width="stretch",
                    key=f"agent_table_{result.request_id}",
                )
        if result.warnings:
            st.warning(" ".join(result.warnings), icon=":material/warning:")
        st.caption(
            f"{result.status.capitalize()} · {result.latency_ms:.0f} ms · request {result.request_id}"
        )
    st.session_state.messages.append({"role": "assistant", "content": result.answer})


def ai_analyst() -> None:
    hero(
        "Ask your data anything",
        "Query retail and sales data using natural language. Every query is validated before execution.",
        "AI ANALYST",
        )

    suggestions = [
        "What were the monthly net sales trends?",
        "Which countries generated the most revenue?",
        "Which products sold the most?",
        "How many transactions were cancellations?",
        "Which customers generated the highest sales?",
    ]
    st.subheader("Try a question", icon=":material/lightbulb:")
    for index, suggestion in enumerate(suggestions):
        with st.container(border=True):
            st.markdown(f"**{suggestion}**")
            st.button(
                "Use question",
                key=f"suggestion_{index}",
                on_click=submit_example,
                args=(suggestion,),
                icon=":material/north_east:",
                width="stretch",
            )
    with st.form("analyst_form", border=True):
        question = st.text_area(
            "Your question",
            key="analyst_question",
            placeholder="Ask about sales, products, countries, customers, returns, or trends…",
            height=96,
        )
        submitted = st.form_submit_button(
            "Analyze data", type="primary", icon=":material/auto_awesome:", width="content"
        )
    if submitted:
        if question.strip():
            render_response(question.strip())
        else:
            st.warning("Enter a business question to begin.", icon=":material/edit:")


def sales_explorer() -> None:
    hero(
        "Sales explorer",
        "Filter transaction records without changing the analytical database.",
        "EXPLORE DATA",
    )
    try:
        data = query_frame("SELECT * FROM transactions ORDER BY invoice_date DESC")
        total_rows = len(data)
        with st.container(border=True):
            a, b, c, d = st.columns(4)
            with a:
                countries = st.multiselect(
                    "Countries",
                    sorted(data["country"].dropna().unique()),
                    placeholder="All countries",
                )
            with b:
                products = st.multiselect(
                    "Products",
                    sorted(data["description"].dropna().unique()),
                    placeholder="All products",
                )
            with c:
                cancellations = st.selectbox(
                    "Cancellation status", ["All records", "Cancellations only", "Sales only"]
                )
            with d:
                search = st.text_input(
                    "Search invoices or products", placeholder="Search", type="search"
                )
            start, end = (
                pd.to_datetime(data["invoice_date"]).min().date(),
                pd.to_datetime(data["invoice_date"]).max().date(),
            )
            dates = st.date_input(
                "Invoice date range", value=(start, end), min_value=start, max_value=end
            )
        filtered = data.copy()
        if countries:
            filtered = filtered[filtered["country"].isin(countries)]
        if products:
            filtered = filtered[filtered["description"].isin(products)]
        if cancellations == "Cancellations only":
            filtered = filtered[filtered["is_cancellation"]]
        elif cancellations == "Sales only":
            filtered = filtered[~filtered["is_cancellation"]]
        if len(dates) == 2:
            invoice_dates = pd.to_datetime(filtered["invoice_date"]).dt.date
            filtered = filtered[(invoice_dates >= dates[0]) & (invoice_dates <= dates[1])]
        if search.strip():
            contains = filtered["invoice_no"].astype(str).str.contains(
                search, case=False, na=False
            ) | filtered["description"].astype(str).str.contains(search, case=False, na=False)
            filtered = filtered[contains]
        st.caption(f"Showing **{len(filtered):,}** of **{total_rows:,}** transaction records.")
        st.dataframe(
            display_frame(filtered), hide_index=True, width="stretch", key="sales_explorer_table"
        )
        st.download_button(
            "Download filtered CSV",
            filtered.to_csv(index=False),
            "insightflow_filtered_sales.csv",
            "text/csv",
            icon=":material/download:",
        )
    except Exception as exc:
        st.error("The sales explorer needs an initialized dataset.", icon=":material/error:")
        st.caption(str(exc))


def data_quality() -> None:
    hero(
        "Data quality",
        "Transparent preparation decisions and pipeline health for the active retail dataset.",
        "PIPELINE REPORT",
    )
    report = repository.quality()
    if report.get("status") == "not_ingested":
        st.warning(
            "No successful ingestion report is available. Run `python scripts/prepare_data.py`.",
            icon=":material/pending:",
        )
        return
    items = [
        ("Input rows", "input_rows", "dataset", "Source records received", "blue"),
        ("Output rows", "output_rows", "table_rows", "Clean records retained", "emerald"),
        (
            "Duplicates removed",
            "duplicates_removed",
            "content_copy",
            "Exact duplicate lines",
            "amber",
        ),
        (
            "Invalid rows rejected",
            "invalid_rows_rejected",
            "rule",
            "Required-field failures",
            "coral",
        ),
        (
            "Cancellation rows",
            "cancellation_rows",
            "undo",
            "Retained for net-sales reporting",
            "purple",
        ),
        ("Missing customer IDs", "missing_customer_ids", "person_off", "Never imputed", "teal"),
    ]
    quality_columns = st.columns(3)
    for index, item in enumerate(items):
        with quality_columns[index % 3]:
            kpi(item[0], f"{report.get(item[1], 0):,}", item[2], item[3], item[4])
    st.subheader("Preparation record", icon=":material/fact_check:")
    details = pd.DataFrame(
        {
            "Field": ["Processed at", "Pipeline version", "Source"],
            "Value": [
                report.get("processed_at", "—"),
                report.get("pipeline_version", "—"),
                report.get("source", "—"),
            ],
        }
    )
    st.dataframe(details, hide_index=True, width="stretch")
    


def settings_page() -> None:
    hero(
        "Settings & provenance",
        "Runtime information for this local-first analytical workspace.",
        "ENVIRONMENT",
    )
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Runtime configuration", icon=":material/settings:")
        config = pd.DataFrame(
            {
                "Setting": [
                    "Model provider",
                    "Model name",
                    "Database path",
                    "Data directory",
                    "Application version",
                ],
                "Value": [
                    settings.model_provider,
                    settings.model_name,
                    str(settings.database_path),
                    str(settings.data_dir),
                    __version__,
                ],
            }
        )
        st.dataframe(config, hide_index=True, width="stretch")
    with right, st.container(border=True):
        st.subheader("Security posture", icon=":material/shield:")
        st.success("Local-first processing", icon=":material/check_circle:")
        st.success("Read-only, allowlisted SQL", icon=":material/check_circle:")
        st.success("No secrets displayed in this workspace", icon=":material/check_circle:")
        st.caption(
            "Runtime details are read-only. Environment configuration is managed outside the dashboard."
        )
    st.subheader("Dataset provenance", icon=":material/database:")
    st.markdown(
        "UCI Machine Learning Repository · Online Retail Data Set (Chen, 2015). The interface reports source values in their supplied currency; it does not perform currency conversion."
    )


initialize_state()
selected_page = shell()
if selected_page == "Executive overview":
    executive_overview()
elif selected_page == "AI analyst":
    ai_analyst()
elif selected_page == "Sales explorer":
    sales_explorer()
elif selected_page == "Data quality":
    data_quality()
else:
    settings_page()
