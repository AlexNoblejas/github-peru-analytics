import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Developer Explorer", page_icon="👩‍💻", layout="wide")
st.title("👩‍💻 Developer Explorer")

@st.cache_data
def load_data():
    metrics_dir = "data/metrics"
    if os.path.exists(f"{metrics_dir}/user_metrics.csv"):
        return pd.read_csv(f"{metrics_dir}/user_metrics.csv")
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No developer data available.")
    st.stop()

st.sidebar.header("Filters")
min_stars = st.sidebar.slider("Min Stars Received", 0, int(df['total_stars_received'].max() or 100), 0)
min_followers = st.sidebar.slider("Min Followers", 0, int(df['followers'].max() or 100), 0)
active_only = st.sidebar.checkbox("Active users only (Pushed in last 90 days)", value=False)

filtered_df = df[
    (df['total_stars_received'] >= min_stars) &
    (df['followers'] >= min_followers)
]

if active_only:
    filtered_df = filtered_df[filtered_df['is_active'] == True]

search_term = st.text_input("Search Developer by Login:", "")
if search_term:
    filtered_df = filtered_df[filtered_df['login'].str.contains(search_term, case=False, na=False)]

st.markdown(f"**Found {len(filtered_df)} matching developers**")
st.dataframe(filtered_df, use_container_width=True)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

st.download_button(
    "📥 Download Export as CSV",
    convert_df(filtered_df),
    "peru_developers.csv",
    "text/csv"
)
