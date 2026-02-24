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

monthly = df.groupby(
    df["order_purchase_timestamp"].dt.to_period("M")
)["order_id"].nunique()

monthly.index = monthly.index.astype(str)

fig, ax = plt.subplots()
ax.plot(monthly.index, monthly.values, marker="o")
plt.xticks(rotation=45)
st.pyplot(fig)

# ======================================
# PRODUK PALING LARIS
# ======================================
st.subheader("🔥 Produk Paling Laris")

top_product = (
    df.groupby("product_category_name_english")["product_id"]
    .count()
    .sort_values(ascending=False)
    .head(10)
)

fig, ax = plt.subplots()
sns.barplot(x=top_product.values, y=top_product.index, ax=ax)
st.pyplot(fig)

# ======================================
# BASIS PELANGGAN
# ======================================
st.subheader("👥 Distribusi Pelanggan per State")

state = (
    df.groupby("customer_state")["customer_id"]
    .nunique()
    .sort_values(ascending=False)
    .head(10)
)

fig, ax = plt.subplots()
sns.barplot(x=state.index, y=state.values, ax=ax)
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

fig, ax = plt.subplots()
sns.barplot(x=rev.values, y=rev.index, ax=ax)
st.pyplot(fig)

# ======================================
# RFM ANALYSIS
# ======================================
st.subheader("⭐ RFM Customer Segmentation")

rfm = df.groupby("customer_unique_id").agg({
    "order_purchase_timestamp":"max",
    "order_id":"nunique",
    "price":"sum"
}).reset_index()

max_date = df["order_purchase_timestamp"].max()
rfm["recency"] = (max_date - rfm["order_purchase_timestamp"]).dt.days
rfm.rename(columns={"order_id":"frequency","price":"monetary"}, inplace=True)

st.dataframe(rfm.sort_values("monetary", ascending=False).head(10))

# ======================================
# GEOSPATIAL MAP (OPTIONAL)
# ======================================
if "geolocation_lat" in df.columns and "geolocation_lng" in df.columns:
    st.subheader("🌍 Peta Distribusi Pelanggan")

    sample = df.sample(1000)

    m = folium.Map(location=[sample["geolocation_lat"].mean(),
                             sample["geolocation_lng"].mean()], zoom_start=4)

    for _, row in sample.iterrows():
        folium.CircleMarker(
            [row["geolocation_lat"], row["geolocation_lng"]],
            radius=2
        ).add_to(m)

    st_folium(m, width=700)

