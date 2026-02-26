import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

st.title("📊 E-Commerce Performance Dashboard")

# ======================================
# LOAD DATA (SATU FILE)
# ======================================
@st.cache_data
def load_data():
    df = pd.read_csv("Main_data.csv", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# ======================================
# PREPROCESS
# ======================================
df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])

# ======================================
# SIDEBAR FILTER
# ======================================
st.sidebar.header("Filter Data")

year = st.sidebar.multiselect(
    "Pilih Tahun",
    df["order_purchase_timestamp"].dt.year.unique(),
    default=df["order_purchase_timestamp"].dt.year.unique()
)

df = df[df["order_purchase_timestamp"].dt.year.isin(year)]

# ======================================
# KPI
# ======================================
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Orders", df["order_id"].nunique())
col2.metric("Total Revenue", f"${df['price'].sum():,.0f}")
col3.metric("Total Customers", df["customer_unique_id"].nunique())

# ======================================
# TREN PENJUALAN
# ======================================
st.subheader("📈 Tren Penjualan")

trend_df = df.copy()

trend_df = trend_df[
    (trend_df["order_purchase_timestamp"] >= "2016-09-01") &
    (trend_df["order_purchase_timestamp"] <= "2018-08-31")
]

if "order_status" in trend_df.columns:
    trend_df = trend_df[trend_df["order_status"] == "delivered"]

trend_df["month_year"] = trend_df["order_purchase_timestamp"].dt.to_period("M")

monthly_orders = (
    trend_df.groupby("month_year")["order_id"]
    .nunique()
    .sort_index()
)

monthly_orders = monthly_orders[monthly_orders > 0]
monthly_orders.index = monthly_orders.index.astype(str)

fig, ax = plt.subplots(figsize=(12,5))
ax.plot(monthly_orders.index, monthly_orders.values, marker="o")

ax.set_title("Tren Penjualan Periode September 2016 – Agustus 2018")
ax.set_xlabel("Periode (Bulan-Tahun)")
ax.set_ylabel("Jumlah Order")
ax.tick_params(axis='x', rotation=45)
ax.grid(True)

st.pyplot(fig)

# =====================================================
# 📦 5 KATEGORI PRODUK PALING LARIS
# =====================================================
st.subheader("📦 5 Kategori Produk Paling Laris")

top_products = (
    df.groupby("product_category_name_english")["product_id"]
    .count()
    .sort_values(ascending=False)
    .head(5)
)

palette = sns.color_palette("Blues_r", n_colors=5)

fig, ax = plt.subplots(figsize=(12,6))

sns.barplot(
    x=top_products.values,
    y=top_products.index,
    hue=top_products.index,
    palette=palette,
    legend=False,
    ax=ax
)

ax.patches[0].set_facecolor("#1f77b4")

ax.set_title(
    "5 Kategori Produk Paling Laris (Berdasarkan Jumlah Terjual)",
    fontsize=15,
    weight="bold"
)
ax.set_xlabel("Jumlah Terjual")
ax.set_ylabel("Kategori Produk")
ax.grid(axis='x', linestyle=':', alpha=0.6)

plt.tight_layout()
st.pyplot(fig)

# ======================================
# BASIS PELANGGAN
# ======================================
st.subheader("👥 Distribusi Pelanggan per State")

state = (
    df.groupby("customer_state")["customer_id"]
    .nunique()
    .sort_values(ascending=False)
    .head(5)
)

palette = sns.color_palette("viridis", n_colors=len(state))

fig, ax = plt.subplots(figsize=(10,5))

sns.barplot(
    x=state.index,
    y=state.values,
    hue=state.index,      
    palette=palette,
    legend=False,
    ax=ax
)

ax.set_title("5 Negara Bagian dengan Jumlah Pelanggan Terbanyak", fontsize=14)
ax.set_xlabel("Negara Bagian (State)")
ax.set_ylabel("Jumlah Pelanggan Unik")
ax.grid(axis='y', linestyle=':', alpha=0.6)

plt.tight_layout()
st.pyplot(fig)

# ======================================
# REVENUE PER KATEGORI
# ======================================
st.subheader("💰 Revenue per Kategori")

rev = (
    df.groupby("product_category_name_english")["price"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

palette = sns.color_palette("magma", n_colors=len(rev))

fig, ax = plt.subplots(figsize=(10,6))

sns.barplot(
    x=rev.values,
    y=rev.index,
    hue=rev.index,     
    palette=palette,
    legend=False,
    ax=ax
)

ax.set_title("10 Kategori Produk dengan Revenue Tertinggi", fontsize=14)
ax.set_xlabel("Total Revenue")
ax.set_ylabel("Kategori Produk")
ax.grid(axis='x', linestyle=':', alpha=0.6)

plt.tight_layout()
st.pyplot(fig)

# ======================================
# RFM ANALYSIS
# ======================================
st.subheader("⭐ RFM Customer Analysis")


def create_rfm_dataframe(data):

    rfm = (
        data.groupby("customer_unique_id", as_index=False)
        .agg({
            "order_purchase_timestamp": "max",
            "order_id": "nunique",
            "price": "sum"
        })
    )

    rfm.rename(columns={
        "customer_unique_id": "customer_id",
        "order_purchase_timestamp": "last_order_date",
        "order_id": "frequency",
        "price": "monetary"
    }, inplace=True)

    snapshot_date = data["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm["recency"] = (snapshot_date - rfm["last_order_date"]).dt.days

    rfm.drop("last_order_date", axis=1, inplace=True)

    return rfm

rfm_source = load_data()
rfm_source["order_purchase_timestamp"] = pd.to_datetime(
    rfm_source["order_purchase_timestamp"]
)

rfm = create_rfm_dataframe(rfm_source)

col1, col2, col3 = st.columns(3)

col1.metric("Average Recency (days)", round(rfm.recency.mean(),1))
col2.metric("Average Frequency", round(rfm.frequency.mean(),2))
col3.metric("Average Monetary", f"${rfm.monetary.mean():,.0f}")

st.subheader("🏆 Top Customers Based on RFM Parameters")

fig, axes = plt.subplots(1,3, figsize=(20,6))
color_main = "#2E86C1"

sns.barplot(
    data=rfm.sort_values("recency").head(5),
    x="customer_id",
    y="recency",
    color=color_main,
    ax=axes[0]
)
axes[0].set_title("Top 5 Customers by Recency")

sns.barplot(
    data=rfm.sort_values("frequency", ascending=False).head(5),
    x="customer_id",
    y="frequency",
    color=color_main,
    ax=axes[1]
)
axes[1].set_title("Top 5 Customers by Frequency")

sns.barplot(
    data=rfm.sort_values("monetary", ascending=False).head(5),
    x="customer_id",
    y="monetary",
    color=color_main,
    ax=axes[2]
)
axes[2].set_title("Top 5 Customers by Monetary")

for ax in axes:
    ax.tick_params(axis='x', rotation=45)

plt.tight_layout()
st.pyplot(fig)
