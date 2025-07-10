import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from db_config import db_connection

# Reusable DB query function
def run_query(query):
    engine = db_connection()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

# ===========================
# CASE STUDY 1
# ===========================

    # Set style
sns.set(style="whitegrid")

def case_1():
    st.subheader("1. Decoding Transaction Dynamics on PhonePe")
    
    # Replace with your actual SQL query
    query = """
WITH state_trend AS (SELECT state, year, quarter, transaction_type, 
SUM(transaction_count) AS total_transactions,SUM(transaction_amount) AS total_amount,
LAG(SUM(transaction_amount)) OVER (PARTITION BY state, transaction_type ORDER BY year, quarter) AS prev_amount
FROM agg_trans GROUP BY state, year, quarter, transaction_type),
growth_analysis AS (SELECT state, year, quarter, transaction_type, total_transactions, total_amount,
(total_amount - prev_amount) / NULLIF(prev_amount, 0) * 100 AS growth_percentage
FROM state_trend), category_trend AS (SELECT transaction_type, year, quarter, 
SUM(transaction_count) AS total_transactions, SUM(transaction_amount) AS total_amount,
LAG(SUM(transaction_amount)) OVER (PARTITION BY transaction_type ORDER BY year, quarter) AS prev_amount
FROM agg_trans GROUP BY transaction_type, year, quarter), category_growth AS (SELECT 
transaction_type, year, quarter, total_transactions, total_amount,
(total_amount - prev_amount) / NULLIF(prev_amount, 0) * 100 AS growth_percentage
FROM category_trend), final_trends AS (SELECT state, transaction_type, year, quarter, total_transactions, total_amount, growth_percentage,
CASE WHEN growth_percentage > 5 THEN 'Growing'WHEN growth_percentage BETWEEN -5 AND 5 THEN 'Stable'
ELSE 'Declining' END AS trend_status FROM growth_analysis)
SELECT * FROM final_trends ORDER BY year DESC, quarter DESC, growth_percentage DESC;
"""
    df = run_query(query)

    fig1 = px.bar(df, x="transaction_type", y="total_amount", color="trend_status", barmode="group", title="Transaction Amount by Type and Trend")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(df, x="quarter", y="growth_percentage", color="transaction_type", line_group="year", title="Quarterly Growth Trend by Type")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.scatter(df, x="state", y="growth_percentage", color="transaction_type", size="total_amount", title="State-wise Growth by Transaction Type")
    st.plotly_chart(fig3, use_container_width=True)



    fig4 = px.box(df, x="trend_status", y="growth_percentage", color="trend_status", title="Growth Distribution by Trend Status")
    st.plotly_chart(fig4, use_container_width=True)

# ===========================
# CASE STUDY 2
# ===========================


def case_2():
    st.subheader("2. Device Dominance and User Engagement Analysis")

    query = """ 
    WITH ranked_metrics AS (
        SELECT State, Brand, Year, Quarter, Transaction_count, Percentage,
               LAG(Transaction_count) OVER (PARTITION BY Brand ORDER BY Year, Quarter) AS prev_txn_count
        FROM agg_users
        WHERE Brand IS NOT NULL AND Brand <> 'Unknown'
    ),
    growth_calc AS (
        SELECT *, 
               ((Transaction_count - prev_txn_count) / NULLIF(prev_txn_count, 0)) * 100 AS growth_percentage
        FROM ranked_metrics
    )
    SELECT * FROM growth_calc
    ORDER BY Year, Quarter;
    """

    df = run_query(query)

    if df.empty:
        st.warning("No data available for this scenario.")
        return

    df["time"] = df["Year"].astype(str) + " Q" + df["Quarter"].astype(str)

    # -- fig1: Average Engagement by Brand --
    avg_engagement = df.groupby("Brand")["Percentage"].mean().reset_index().sort_values("Percentage", ascending=False)
    fig1 = px.bar(avg_engagement, x="Brand", y="Percentage", color="Brand", 
                  title="Average Engagement (Percentage) by Brand")
    st.plotly_chart(fig1, use_container_width=True)

    # -- fig2: Average Transactions by Brand (Simplified & Clear) --
    avg_txns = df.groupby("Brand")["Transaction_count"].mean().reset_index().sort_values("Transaction_count", ascending=False)
    fig2 = px.bar(avg_txns, x="Brand", y="Transaction_count", color="Brand",
                  title="Average Transactions by Brand")
    st.plotly_chart(fig2, use_container_width=True)

    # -- fig3: Growth Percentage by Brand --
    avg_growth = df.groupby("Brand")["growth_percentage"].mean().reset_index().sort_values("growth_percentage", ascending=False)
    fig3 = px.bar(avg_growth, x="Brand", y="growth_percentage", color="Brand", 
                  title="Average Growth in Transaction Count by Brand")
    st.plotly_chart(fig3, use_container_width=True)

    # -- fig4: Engagement Heatmap (State vs Brand) --
    heatmap_df = df.groupby(["State", "Brand"])["Percentage"].mean().reset_index()
    fig4 = px.density_heatmap(heatmap_df, x="Brand", y="State", z="Percentage", 
                              color_continuous_scale="Viridis",
                              title="Engagement Heatmap (Brand vs State)")
    st.plotly_chart(fig4, use_container_width=True)


# ===========================
# CASE STUDY 3
# ===========================


def case_3():
    st.subheader("3. Insurance Penetration and Growth Potential Analysis")

    query = """
    WITH insurance_trend AS (
        SELECT state, year, quarter, 
               SUM(insurance_count) AS total_policies,
               SUM(insurance_amount) AS total_value,
               LAG(SUM(insurance_amount)) OVER (
                   PARTITION BY state ORDER BY year, quarter
               ) AS prev_value
        FROM map_insur
        GROUP BY state, year, quarter
    )
    SELECT 
        state, year, quarter, total_policies, total_value,
        (total_value - prev_value) / NULLIF(prev_value, 0) * 100 AS growth_percentage
    FROM insurance_trend
    ORDER BY growth_percentage DESC;
    """

    df = run_query(query)

    if df.empty:
        st.warning("No insurance data available for this scenario.")
        return

    sns.set(style="whitegrid")

    # Chart 1: Top 10 states by insurance value growth
    top_growth = df.sort_values("growth_percentage", ascending=False).head(10)
    fig1 = px.bar(top_growth, x="growth_percentage", y="state", orientation='h',
                 title="Top 10 States by Insurance Value Growth (%)")
    st.plotly_chart(fig1, use_container_width=True)

    # Chart 2: Insurance Distribution by State
    fig2 = px.bar(df.sort_values("total_value", ascending=False), x="state", y="total_value",
                 title="Total Insurance Value by State")
    st.plotly_chart(fig2, use_container_width=True)

    # Chart 3: Insurance Policies Count per State
    fig3 = px.bar(df.sort_values("total_policies", ascending=False), x="state", y="total_policies",
                 title="Total Insurance Policies by State")
    st.plotly_chart(fig3, use_container_width=True)


# ===========================
# CASE STUDY 4
# ===========================
def case_4():
    st.subheader("4. Transaction Analysis for Market Expansion")

    query = """
    WITH state_growth AS (SELECT state, year, quarter
, SUM(transaction_count) AS total_transactions, 
SUM(transaction_amount) AS total_amount,LAG(SUM(transaction_amount)) 
OVER (PARTITION BY state ORDER BY year, quarter) AS prev_amount FROM agg_trans
GROUP BY state, year, quarter) SELECT state, SUM(total_transactions) AS total_transactions,
SUM(total_amount) AS total_transaction_amount,
ROUND(AVG((total_amount - prev_amount) / NULLIF(prev_amount, 0) * 100), 2) AS avg_growth_rate 
FROM state_growth GROUP BY state ORDER BY avg_growth_rate DESC, total_transaction_amount DESC;
"""

    df = run_query(query)

    fig1 = px.bar(df, x="state", y="total_transactions", title="Top state by total Transactions")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(df.melt(id_vars="state", 
                      value_vars=["total_transaction_amount", "total_transactions"], 
                      var_name="Metric", value_name="Value"),
              x="state", y="Value", color="Metric", barmode="group",
              title="Total Transactions vs Transaction Amount by State")
    st.plotly_chart(fig2, use_container_width=True)


    fig3 = px.scatter(df, x="avg_growth_rate", y="total_transaction_amount",size="total_transactions", color="state",
                      title="Transaction Amount vs Avg Growth Rate by State",
                      labels={"avg_growth_rate": "Avg Growth Rate (%)", "total_transaction_amount": "Total Amount"})
    st.plotly_chart(fig3, use_container_width=True)


    fig4 = px.funnel(df, x="total_transaction_amount", y="state", title="state-wise Transaction Funnel")
    st.plotly_chart(fig4, use_container_width=True)



# ===========================
# MAIN FUNCTION
# ===========================
def business_case_study():
    st.title("📊 Business Case Study Visualizations")

    options = [
        "1. Decoding Transaction Dynamics on PhonePe",
        "2. Device Dominance and User Engagement Analysis",
        "3. Insurance Penetration and Growth Potential Analysis",
        "4. Transaction Analysis for Market Expansion",
    ]

    selection = st.selectbox("Choose a Case Study", options)

    if "1." in selection:
        case_1()
    elif "2." in selection:
        case_2()
    elif "3." in selection:
        case_3()
    elif "4." in selection:
        case_4()

def case_study_page():
    business_case_study()
