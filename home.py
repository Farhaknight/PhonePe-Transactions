import streamlit as st
import pandas as pd
import json
import plotly.express as px
from sqlalchemy import create_engine
from db_config import db_connection


def home_page():
    st.title("PhonePe Transactions in India")

    # Load GeoJSON for India Map
    with open("india_states.json", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    state_name_mapping = { 
        "Andaman and Nicobar": "andaman-&-nicobar-islands",
        "Andhra Pradesh": "andhra-pradesh",
        "Arunachal Pradesh": "arunachal-pradesh",
        "Assam": "assam",
        "Bihar": "bihar",
        "Chandigarh": "chandigarh",
        "Chhattisgarh": "chhattisgarh",
        "Dadra and Nagar Haveli and Daman and Diu": "dadra-&-nagar-haveli-&-daman-&-diu",
        "Delhi": "delhi",
        "Goa": "goa",
        "Gujarat": "gujarat",
        "Haryana": "haryana",
        "Himachal Pradesh": "himachal-pradesh",
        "Jammu and Kashmir": "jammu-&-kashmir",
        "Jharkhand": "jharkhand",
        "Karnataka": "karnataka",
        "Kerala": "kerala",
        "Ladakh": "ladakh",
        "Lakshadweep": "lakshadweep",
        "Madhya Pradesh": "madhya-pradesh",
        "Maharashtra": "maharashtra",
        "Manipur": "manipur",
        "Meghalaya": "meghalaya",
        "Mizoram": "mizoram",
        "Nagaland": "nagaland",
        "Odisha": "odisha",
        "Puducherry": "puducherry",
        "Punjab": "punjab",
        "Rajasthan": "rajasthan",
        "Sikkim": "sikkim",
        "Tamil Nadu": "tamil-nadu",
        "Telangana": "telangana",
        "Tripura": "tripura",
        "Uttar Pradesh": "uttar-pradesh",
        "Uttarakhand": "uttarakhand",
        "West Bengal": "west-bengal"
    }

    engine = db_connection()

    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    transaction_type = st.sidebar.selectbox("Select Transaction Type", [
        "peer-to-peer payments",
        "recharge & bill payments",
        "financial services",
        "others"
    ])
    year = st.sidebar.selectbox("Select Year", list(range(2018, 2024)))
    quarter = st.sidebar.selectbox("Select Quarter", [1, 2, 3, 4])

    # --- Total Transaction Amount by State (Bar Chart) ---
    st.subheader("Total Transaction Amount by State")

    query_bar = f"""
        SELECT state, SUM(transaction_amount) AS total_amount
        FROM agg_trans_new
        GROUP BY state
        ORDER BY total_amount DESC
    """
    df_bar = pd.read_sql(query_bar, con=engine)
    df_bar["state"] = df_bar["state"].str.title().str.strip()

    fig = px.bar(
        df_bar,
        x="state",
        y="total_amount",
        color="state",
        title="State-wise Total Transaction Amount",
        labels={"total_amount": "Transaction Amount (₹)"},
        height=500
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # --- Category-wise Total Transactions ---
    st.subheader("Transactions")
    cat_query = f"""
        SELECT transaction_type, SUM(transaction_count) AS total_count
        FROM agg_trans_new
        WHERE year={year} AND quarter={quarter}
        GROUP BY transaction_type
    """
    df_cat = pd.read_sql(cat_query, con=engine)
    for idx, row in df_cat.iterrows():
        st.markdown(f"**{row['transaction_type'].title()}**: `{'{:,.0f}'.format(row['total_count'])}`")

    st.markdown("---")

    # --- Top 10 Buttons ---
    view_type = st.radio("Select View", ["States", "Districts", "Postal Codes"], horizontal=True)

    if view_type == "States":
        top_query = f"""
            SELECT State AS name, SUM(Transaction_amount) AS total_amount
            FROM agg_trans_new
            WHERE Year={year} AND Quarter={quarter}
              AND transaction_type = '{transaction_type}'
            GROUP BY State
            ORDER BY total_amount DESC
            LIMIT 10
        """

    elif view_type == "Districts":
        top_query = f"""
            SELECT `District` AS name, SUM(`Transaction_amount`) AS total_amount
            FROM Map_trans_New
            WHERE `Year`={year} AND `Quarter`={quarter}
              AND District NOT REGEXP '^[0-9]+$'
            GROUP BY `District`
            ORDER BY total_amount DESC
            LIMIT 10
        """

    else:  # Postal Codes
        top_query = f"""
            SELECT Pincode AS name, SUM(Transaction_amount) AS total_amount
            FROM top_trans_pin
            WHERE Year = {year} AND Quarter = {quarter}
              AND Pincode REGEXP '^[0-9]{{6}}$'
            GROUP BY Pincode
            HAVING total_amount < 9999 * 1e7
            ORDER BY total_amount DESC
            LIMIT 10
        """

    df_top = pd.read_sql(top_query, con=engine)

    st.subheader(f"Top 10 {view_type}")
    for idx, row in df_top.iterrows():
        amount_cr = row['total_amount'] / 1e7  # Convert to Cr
        st.markdown(f"**{idx + 1}. {row['name']}** — `{amount_cr:.2f} Cr`")
