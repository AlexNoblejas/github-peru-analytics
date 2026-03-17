import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

st.set_page_config(page_title="Overview Dashboard", page_icon="📊", layout="wide")
st.title("📊 Ecosystem Overview")

@st.cache_data
def load_data():
    base_dir = "data/processed"
    metrics_dir = "data/metrics"
    
    repos_df = pd.DataFrame()
    user_metrics_df = pd.DataFrame()
    eco_metrics = {}
    
    if os.path.exists(f"{base_dir}/repositories.csv"):
        repos_df = pd.read_csv(f"{base_dir}/repositories.csv")
    if os.path.exists(f"{metrics_dir}/user_metrics.csv"):
        user_metrics_df = pd.read_csv(f"{metrics_dir}/user_metrics.csv")
    if os.path.exists(f"{metrics_dir}/ecosystem_metrics.json"):
        with open(f"{metrics_dir}/ecosystem_metrics.json", "r", encoding="utf-8") as f:
            eco_metrics = json.load(f)
            
    return repos_df, user_metrics_df, eco_metrics

repos_df, user_metrics_df, eco_metrics = load_data()

if user_metrics_df.empty:
    st.warning("No data available.")
    st.stop()

st.markdown("### Top 10 Developers by Impact Score")
top_devs = user_metrics_df.nlargest(10, 'impact_score')[['login', 'name', 'impact_score', 'total_stars_received', 'followers', 'h_index']]
st.dataframe(top_devs, use_container_width=True)

st.markdown("### Top 10 Repositories by Stars")
if not repos_df.empty:
    top_repos = repos_df.nlargest(10, 'stargazers_count')[['name', 'owner_login', 'stargazers_count', 'forks_count', 'language']]
    st.dataframe(top_repos, use_container_width=True)

st.markdown("### Ecosystem Averages")
avgs = eco_metrics.get('averages', {})
c1, c2, c3, c4 = st.columns(4)
c1.metric("Avg Repos / Dev", avgs.get("avg_repos_per_dev", 0))
c2.metric("Avg Stars / Dev", avgs.get("avg_stars_per_dev", 0))
c3.metric("Avg Followers / Dev", avgs.get("avg_followers_per_dev", 0))
c4.metric("Avg Acc Age (Years)", avgs.get("avg_account_age_years", 0))
