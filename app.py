# app.py  —  E-Commerce Data Warehouse Analytics Dashboard
# Run: streamlit run app.py

import os
import time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="DW Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme palette ─────────────────────────────────────────────
COLORS = {
    "primary":    "#6366f1",
    "secondary":  "#f59e0b",
    "success":    "#10b981",
    "danger":     "#ef4444",
    "info":       "#3b82f6",
    "purple":     "#8b5cf6",
    "pink":       "#ec4899",
    "teal":       "#14b8a6",
    "sequence":   px.colors.qualitative.Vivid,
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#e2e8f0"),
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
)

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f172a; }
    [data-testid="stSidebar"]          { background: #1e293b; border-right: 1px solid #334155; }
    .metric-card {
        background: #1e293b; border: 1px solid #334155; border-radius: 12px;
        padding: 20px; text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #6366f1; }
    .metric-label { font-size: 0.85rem; color: #94a3b8; margin-top: 4px; }
    .section-title {
        font-size: 1.4rem; font-weight: 700; color: #f1f5f9;
        border-left: 4px solid #6366f1; padding-left: 12px;
        margin: 24px 0 16px 0;
    }
    .stButton > button {
        width: 100%; border-radius: 10px; border: 1px solid #334155;
        background: #1e293b; color: #e2e8f0; font-weight: 600;
        padding: 14px; margin-bottom: 8px; transition: all 0.2s;
    }
    .stButton > button:hover { background: #6366f1; border-color: #6366f1; color: white; }
    .active-btn > button    { background: #6366f1 !important; border-color: #6366f1 !important; color: white !important; }
    div[data-testid="stMetricValue"] { color: #6366f1; }
</style>
""", unsafe_allow_html=True)


# ── DB connection ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_engine():
    url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER','postgres')}:"
        f"{os.getenv('DB_PASSWORD','postgres')}@"
        f"{os.getenv('DB_HOST','localhost')}:"
        f"{os.getenv('DB_PORT','5432')}/"
        f"{os.getenv('DB_NAME','ecommerce_dw')}"
    )
    return create_engine(url, pool_pre_ping=True, pool_size=3)


@st.cache_data(ttl=300, show_spinner=False)
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='text-align:center; padding: 20px 0 10px 0;'>
            <div style='font-size:2.5rem;'>📊</div>
            <div style='font-size:1.1rem; font-weight:700; color:#f1f5f9;'>DW Analytics</div>
            <div style='font-size:0.75rem; color:#64748b;'>E-Commerce Data Warehouse</div>
        </div>
        <hr style='border-color:#334155; margin:12px 0 20px 0;'>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Analytics")
    page = st.session_state.get("page", "overview")

    if st.button("🏠  Overview Dashboard",     key="btn_overview"):
        st.session_state.page = "overview"
    if st.button("🏆  Top Selling Products",   key="btn_products"):
        st.session_state.page = "products"
    if st.button("📈  Monthly Revenue Trends", key="btn_trends"):
        st.session_state.page = "trends"
    if st.button("👥  Top Customers",          key="btn_customers"):
        st.session_state.page = "customers"

    st.markdown("<hr style='border-color:#334155; margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Filters")
    top_n = st.slider("Top N results", 5, 25, 10)

    years_df = query("SELECT DISTINCT year FROM dim_time ORDER BY year")
    year_options = ["All Years"] + years_df["year"].tolist()
    selected_year = st.selectbox("Filter by Year", year_options)
    year_param = None if selected_year == "All Years" else int(selected_year)

    st.markdown("<hr style='border-color:#334155; margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown("""
        <div style='font-size:0.72rem; color:#475569; text-align:center;'>
            Star Schema · PostgreSQL 15<br>
            50K facts · 40K dimension rows
        </div>
    """, unsafe_allow_html=True)

page = st.session_state.get("page", "overview")


# ══════════════════════════════════════════════════════════════
# PAGE: OVERVIEW DASHBOARD
# ══════════════════════════════════════════════════════════════
if page == "overview":
    st.markdown("## 🏠 Overview Dashboard")
    st.caption("High-level KPIs across the entire data warehouse")

    with st.spinner("Loading KPIs…"):
        kpis = query("""
            SELECT
                ROUND(SUM(net_revenue),2)                  AS total_revenue,
                ROUND(SUM(profit),2)                       AS total_profit,
                COUNT(DISTINCT order_id)                   AS total_orders,
                ROUND(AVG(net_revenue),2)                  AS avg_order_value,
                SUM(quantity)                              AS total_units,
                SUM(CASE WHEN return_flag THEN 1 ELSE 0 END) AS total_returns
            FROM fact_sales
        """)
        rev     = kpis["total_revenue"].iloc[0]
        profit  = kpis["total_profit"].iloc[0]
        orders  = kpis["total_orders"].iloc[0]
        aov     = kpis["avg_order_value"].iloc[0]
        units   = kpis["total_units"].iloc[0]
        returns = kpis["total_returns"].iloc[0]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, label, value in [
        (c1, "Total Revenue",    f"${rev:,.0f}"),
        (c2, "Total Profit",     f"${profit:,.0f}"),
        (c3, "Total Orders",     f"{orders:,}"),
        (c4, "Avg Order Value",  f"${aov:,.2f}"),
        (c5, "Units Sold",       f"{units:,}"),
        (c6, "Total Returns",    f"{returns:,}"),
    ]:
        col.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{value}</div>
                <div class='metric-label'>{label}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ── Row 1: Category revenue  +  Channel pie ──────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("<div class='section-title'>Revenue by Category</div>", unsafe_allow_html=True)
        cat_df = query("SELECT * FROM vw_category_performance")
        fig = px.bar(cat_df, x="total_revenue", y="category", orientation="h",
                     color="profit_margin_pct",
                     color_continuous_scale="Viridis",
                     labels={"total_revenue": "Revenue ($)", "category": "",
                             "profit_margin_pct": "Margin %"},
                     text=cat_df["total_revenue"].apply(lambda x: f"${x/1e6:.1f}M"))
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOTLY_LAYOUT, height=380,
                          coloraxis_colorbar=dict(title="Margin %"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='section-title'>Sales by Channel</div>", unsafe_allow_html=True)
        ch_df = query("SELECT * FROM vw_channel_performance")
        fig = px.pie(ch_df, names="sales_channel", values="total_revenue",
                     hole=0.55, color_discrete_sequence=COLORS["sequence"])
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(**PLOTLY_LAYOUT, height=380,
                          showlegend=False,
                          annotations=[dict(text="Channel<br>Mix", x=0.5, y=0.5,
                                           font_size=14, showarrow=False,
                                           font_color="#e2e8f0")])
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 2: Region map  +  Loyalty tier breakdown ─────────
    col3, col4 = st.columns([3, 2])

    with col3:
        st.markdown("<div class='section-title'>Revenue by Region & Country</div>",
                    unsafe_allow_html=True)
        reg_df = query("SELECT * FROM vw_region_performance")
        fig = px.treemap(reg_df, path=["region", "country"],
                         values="total_revenue", color="total_profit",
                         color_continuous_scale="RdYlGn",
                         labels={"total_revenue": "Revenue", "total_profit": "Profit"})
        fig.update_layout(**PLOTLY_LAYOUT, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("<div class='section-title'>Customers by Loyalty Tier</div>",
                    unsafe_allow_html=True)
        tier_df = query("""
            SELECT loyalty_tier, COUNT(*) AS customer_count,
                   ROUND(AVG(age),1) AS avg_age
            FROM dim_customers GROUP BY loyalty_tier
            ORDER BY CASE loyalty_tier
                WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2
                WHEN 'Silver'   THEN 3 ELSE 4 END
        """)
        tier_colors = {"Platinum": "#a78bfa", "Gold": "#f59e0b",
                       "Silver": "#94a3b8",   "Bronze": "#b45309"}
        fig = px.bar(tier_df, x="loyalty_tier", y="customer_count",
                     color="loyalty_tier",
                     color_discrete_map=tier_colors,
                     text="customer_count",
                     labels={"customer_count": "Customers", "loyalty_tier": ""})
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# PAGE: TOP SELLING PRODUCTS
# ══════════════════════════════════════════════════════════════
elif page == "products":
    st.markdown("## 🏆 Top Selling Products")
    st.caption(f"Top {top_n} products by net revenue — excluding returned orders")

    with st.spinner("Calling get_top_selling_products()…"):
        t0 = time.time()
        df = query(
            "SELECT * FROM get_top_selling_products(:n)",
            {"n": top_n}
        )
        elapsed = time.time() - t0

    st.caption(f"⚡ Query returned {len(df)} rows in {elapsed:.2f}s")

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "Total Revenue",   f"${df['total_revenue'].sum():,.0f}"),
        (c2, "Total Profit",    f"${df['total_profit'].sum():,.0f}"),
        (c3, "Units Sold",      f"{df['total_quantity'].sum():,}"),
        (c4, "Avg Margin",      f"{df['profit_margin'].mean():.1f}%"),
    ]:
        col.metric(label, value)

    # ── Chart 1: Horizontal bar — revenue ────────────────────
    st.markdown("<div class='section-title'>Revenue & Quantity by Product</div>",
                unsafe_allow_html=True)

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Net Revenue ($)", "Units Sold"))
    df_sorted = df.sort_values("total_revenue")
    fig.add_trace(go.Bar(
        y=df_sorted["product_name"], x=df_sorted["total_revenue"],
        orientation="h", name="Revenue",
        marker_color=COLORS["primary"],
        text=df_sorted["total_revenue"].apply(lambda x: f"${x:,.0f}"),
        textposition="outside",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        y=df_sorted["product_name"], x=df_sorted["total_quantity"],
        orientation="h", name="Quantity",
        marker_color=COLORS["teal"],
        text=df_sorted["total_quantity"].apply(lambda x: f"{x:,}"),
        textposition="outside",
    ), row=1, col=2)
    fig.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart 2: Scatter — revenue vs quantity ────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Revenue vs Quantity (by Category)</div>",
                    unsafe_allow_html=True)
        fig = px.scatter(df, x="total_quantity", y="total_revenue",
                         size="total_profit", color="category",
                         hover_name="product_name",
                         hover_data={"profit_margin": ":.1f%",
                                     "avg_unit_price": ":$,.2f"},
                         color_discrete_sequence=COLORS["sequence"],
                         labels={"total_quantity": "Units Sold",
                                 "total_revenue": "Net Revenue ($)",
                                 "total_profit": "Profit"})
        fig.update_layout(**PLOTLY_LAYOUT, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='section-title'>Profit Margin by Product</div>",
                    unsafe_allow_html=True)
        df_m = df.sort_values("profit_margin", ascending=True)
        fig = px.bar(df_m, x="profit_margin", y="product_name",
                     orientation="h",
                     color="profit_margin",
                     color_continuous_scale="RdYlGn",
                     text=df_m["profit_margin"].apply(lambda x: f"{x:.1f}%"),
                     labels={"profit_margin": "Margin (%)", "product_name": ""})
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOTLY_LAYOUT, height=380,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Chart 3: Category donut ───────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("<div class='section-title'>Revenue Share by Category</div>",
                    unsafe_allow_html=True)
        cat_rev = df.groupby("category")["total_revenue"].sum().reset_index()
        fig = px.pie(cat_rev, names="category", values="total_revenue",
                     hole=0.5, color_discrete_sequence=COLORS["sequence"])
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("<div class='section-title'>Avg Discount % by Product</div>",
                    unsafe_allow_html=True)
        df_d = df.sort_values("avg_discount_pct", ascending=False)
        fig = px.bar(df_d, x="product_name", y="avg_discount_pct",
                     color="avg_discount_pct",
                     color_continuous_scale="Reds",
                     text=df_d["avg_discount_pct"].apply(lambda x: f"{x:.1f}%"),
                     labels={"avg_discount_pct": "Avg Discount (%)",
                             "product_name": ""})
        fig.update_traces(textposition="outside")
        fig.update_xaxes(tickangle=30)
        fig.update_layout(**PLOTLY_LAYOUT, height=360,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Raw data table ────────────────────────────────────────
    with st.expander("📋 Raw Data Table"):
        st.dataframe(df.style.format({
            "total_revenue":    "${:,.2f}",
            "total_profit":     "${:,.2f}",
            "total_cost":       "${:,.2f}",
            "avg_unit_price":   "${:,.2f}",
            "profit_margin":    "{:.2f}%",
            "avg_discount_pct": "{:.2f}%",
        }), use_container_width=True)


# ══════════════════════════════════════════════════════════════
# PAGE: MONTHLY REVENUE TRENDS
# ══════════════════════════════════════════════════════════════
elif page == "trends":
    st.markdown("## 📈 Monthly Revenue Trends")
    label = f"Year: {selected_year}" if year_param else "All Years"
    st.caption(f"Aggregated revenue, profit and order trends — {label}")

    with st.spinner("Calling get_monthly_revenue_trends()…"):
        t0 = time.time()
        df = query(
            "SELECT * FROM get_monthly_revenue_trends(:yr)",
            {"yr": year_param}
        )
        elapsed = time.time() - t0

    st.caption(f"⚡ Query returned {len(df)} rows in {elapsed:.2f}s")

    if df.empty:
        st.warning("No data found for the selected filters.")
        st.stop()

    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "Total Revenue",   f"${df['total_revenue'].sum():,.0f}"),
        (c2, "Total Profit",    f"${df['total_profit'].sum():,.0f}"),
        (c3, "Total Orders",    f"{df['total_orders'].sum():,}"),
        (c4, "Avg Return Rate", f"{df['return_rate'].mean():.1f}%"),
    ]:
        col.metric(label, value)

    # ── Chart 1: Revenue + Profit line ────────────────────────
    st.markdown("<div class='section-title'>Revenue & Profit Over Time</div>",
                unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["total_revenue"], name="Net Revenue",
        line=dict(color=COLORS["primary"], width=2.5),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.15)",
        mode="lines+markers", marker=dict(size=5),
    ))
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["total_profit"], name="Profit",
        line=dict(color=COLORS["success"], width=2),
        mode="lines+markers", marker=dict(size=4),
    ))
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["total_cost"], name="Cost",
        line=dict(color=COLORS["danger"], width=1.5, dash="dot"),
        mode="lines",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=360,
                      xaxis_title="Month", yaxis_title="Amount ($)",
                      hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart 2: MoM change  +  Orders bar ───────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Month-over-Month Revenue Change (%)</div>",
                    unsafe_allow_html=True)
        df_mom = df.dropna(subset=["mom_revenue_chg"])
        colors = [COLORS["success"] if v >= 0 else COLORS["danger"]
                  for v in df_mom["mom_revenue_chg"]]
        fig = go.Figure(go.Bar(
            x=df_mom["period"], y=df_mom["mom_revenue_chg"],
            marker_color=colors,
            text=df_mom["mom_revenue_chg"].apply(lambda x: f"{x:+.1f}%"),
            textposition="outside",
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#475569")
        fig.update_layout(**PLOTLY_LAYOUT, height=340,
                          xaxis_title="Month", yaxis_title="MoM Change (%)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='section-title'>Monthly Order Volume</div>",
                    unsafe_allow_html=True)
        fig = px.bar(df, x="period", y="total_orders",
                     color="total_orders",
                     color_continuous_scale="Blues",
                     text=df["total_orders"].apply(lambda x: f"{x:,}"),
                     labels={"period": "Month", "total_orders": "Orders"})
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOTLY_LAYOUT, height=340,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Chart 3: Heatmap ──────────────────────────────────────
    st.markdown("<div class='section-title'>Revenue Heatmap — Month × Year</div>",
                unsafe_allow_html=True)
    pivot = df.pivot_table(index="year", columns="month_name",
                           values="total_revenue", aggfunc="sum")
    month_order = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    existing = [m for m in month_order if m in pivot.columns]
    pivot = pivot[existing]
    fig = px.imshow(pivot, color_continuous_scale="Viridis",
                    labels=dict(x="Month", y="Year", color="Revenue ($)"),
                    text_auto=".2s", aspect="auto")
    fig.update_layout(**PLOTLY_LAYOUT, height=280)
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart 4: Avg order value + return rate ────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("<div class='section-title'>Average Order Value Trend</div>",
                    unsafe_allow_html=True)
        fig = px.line(df, x="period", y="avg_order_value",
                      markers=True,
                      color_discrete_sequence=[COLORS["secondary"]],
                      labels={"avg_order_value": "AOV ($)", "period": "Month"})
        fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
        fig.update_layout(**PLOTLY_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("<div class='section-title'>Return Rate Trend (%)</div>",
                    unsafe_allow_html=True)
        fig = px.area(df, x="period", y="return_rate",
                      color_discrete_sequence=[COLORS["danger"]],
                      labels={"return_rate": "Return Rate (%)", "period": "Month"})
        fig.update_traces(line=dict(width=2), fillcolor="rgba(239,68,68,0.2)")
        fig.update_layout(**PLOTLY_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Raw Data Table"):
        st.dataframe(df.style.format({
            "total_revenue":   "${:,.2f}",
            "total_profit":    "${:,.2f}",
            "total_cost":      "${:,.2f}",
            "avg_order_value": "${:,.2f}",
            "return_rate":     "{:.2f}%",
            "mom_revenue_chg": "{:+.2f}%",
        }), use_container_width=True)


# ══════════════════════════════════════════════════════════════
# PAGE: TOP CUSTOMERS
# ══════════════════════════════════════════════════════════════
elif page == "customers":
    st.markdown("## 👥 Top Customers")
    st.caption(f"Top {top_n} customers by total spending with behavioural insights")

    with st.spinner("Calling get_top_customers()…"):
        t0 = time.time()
        df = query(
            "SELECT * FROM get_top_customers(:n)",
            {"n": top_n}
        )
        elapsed = time.time() - t0

    st.caption(f"⚡ Query returned {len(df)} rows in {elapsed:.2f}s")

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "Total Revenue",  f"${df['total_revenue'].sum():,.0f}"),
        (c2, "Total Profit",   f"${df['total_profit'].sum():,.0f}"),
        (c3, "Total Orders",   f"{df['total_orders'].sum():,}"),
        (c4, "Avg AOV",        f"${df['avg_order_value'].mean():,.2f}"),
    ]:
        col.metric(label, value)

    # ── Chart 1: Horizontal bar — customer revenue ────────────
    st.markdown("<div class='section-title'>Top Customers by Total Revenue</div>",
                unsafe_allow_html=True)
    df_s = df.sort_values("total_revenue", ascending=True)
    tier_colors = {"Platinum": "#a78bfa", "Gold": "#f59e0b",
                   "Silver": "#94a3b8",   "Bronze": "#cd7c32"}
    fig = go.Figure()
    for tier, grp in df_s.groupby("loyalty_tier"):
        fig.add_trace(go.Bar(
            y=grp["full_name"], x=grp["total_revenue"],
            name=tier, orientation="h",
            marker_color=tier_colors.get(tier, "#6366f1"),
            text=grp["total_revenue"].apply(lambda x: f"${x:,.0f}"),
            textposition="outside",
        ))
    fig.update_layout(**PLOTLY_LAYOUT, height=420,
                      barmode="stack",
                      xaxis_title="Total Revenue ($)", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart 2: Donut (loyalty tier share)  +  Scatter ──────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Spend Share by Loyalty Tier</div>",
                    unsafe_allow_html=True)
        tier_rev = df.groupby("loyalty_tier")["total_revenue"].sum().reset_index()
        fig = px.pie(tier_rev, names="loyalty_tier", values="total_revenue",
                     hole=0.55,
                     color="loyalty_tier",
                     color_discrete_map=tier_colors)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=True,
                          annotations=[dict(text="Tier<br>Spend", x=0.5, y=0.5,
                                           font_size=13, showarrow=False,
                                           font_color="#e2e8f0")])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='section-title'>Revenue vs Orders (by Tier)</div>",
                    unsafe_allow_html=True)
        fig = px.scatter(df, x="total_orders", y="total_revenue",
                         size="avg_order_value", color="loyalty_tier",
                         hover_name="full_name",
                         hover_data={"country": True,
                                     "favourite_category": True,
                                     "total_returns": True},
                         color_discrete_map=tier_colors,
                         labels={"total_orders": "Number of Orders",
                                 "total_revenue": "Total Revenue ($)",
                                 "avg_order_value": "AOV"})
        fig.update_layout(**PLOTLY_LAYOUT, height=360)
        st.plotly_chart(fig, use_container_width=True)

    # ── Chart 3: Favourite category  +  Country breakdown ────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("<div class='section-title'>Favourite Categories (Top Customers)</div>",
                    unsafe_allow_html=True)
        cat_counts = df["favourite_category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.bar(cat_counts, x="count", y="category", orientation="h",
                     color="count", color_continuous_scale="Purples",
                     text="count",
                     labels={"count": "Customers", "category": ""})
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOTLY_LAYOUT, height=340,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("<div class='section-title'>Revenue by Country</div>",
                    unsafe_allow_html=True)
        country_rev = df.groupby("country")["total_revenue"].sum().reset_index()
        fig = px.pie(country_rev, names="country", values="total_revenue",
                     hole=0.4, color_discrete_sequence=COLORS["sequence"])
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(**PLOTLY_LAYOUT, height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Chart 4: AOV comparison ───────────────────────────────
    st.markdown("<div class='section-title'>Average Order Value per Customer</div>",
                unsafe_allow_html=True)
    df_aov = df.sort_values("avg_order_value", ascending=False)
    fig = px.bar(df_aov, x="full_name", y="avg_order_value",
                 color="loyalty_tier",
                 color_discrete_map=tier_colors,
                 text=df_aov["avg_order_value"].apply(lambda x: f"${x:,.0f}"),
                 labels={"avg_order_value": "AOV ($)", "full_name": ""})
    fig.update_traces(textposition="outside")
    fig.update_xaxes(tickangle=30)
    fig.update_layout(**PLOTLY_LAYOUT, height=340)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Raw Data Table"):
        display_cols = ["full_name", "loyalty_tier", "country", "age",
                        "total_revenue", "total_profit", "total_orders",
                        "avg_order_value", "total_returns",
                        "favourite_category", "favourite_channel"]
        st.dataframe(df[display_cols].style.format({
            "total_revenue":   "${:,.2f}",
            "total_profit":    "${:,.2f}",
            "avg_order_value": "${:,.2f}",
        }), use_container_width=True)
