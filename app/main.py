import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(
    page_title="GitHub Peru Analytics",
    page_icon="🇵🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading ---
@st.cache_data
def load_data():
    base_dir = "data/processed"
    metrics_dir = "data/metrics"
    
    users_df = pd.DataFrame()
    repos_df = pd.DataFrame()
    class_df = pd.DataFrame()
    user_metrics_df = pd.DataFrame()
    eco_metrics = {}
    
    if os.path.exists(f"{base_dir}/users.csv"):
        users_df = pd.read_csv(f"{base_dir}/users.csv")
    
    if os.path.exists(f"{base_dir}/repositories.csv"):
        repos_df = pd.read_csv(f"{base_dir}/repositories.csv")
        
    if os.path.exists(f"{base_dir}/classifications.csv"):
        class_df = pd.read_csv(f"{base_dir}/classifications.csv")
        
    if os.path.exists(f"{metrics_dir}/user_metrics.csv"):
        user_metrics_df = pd.read_csv(f"{metrics_dir}/user_metrics.csv")
        
    if os.path.exists(f"{metrics_dir}/ecosystem_metrics.json"):
        with open(f"{metrics_dir}/ecosystem_metrics.json", "r", encoding="utf-8") as f:
            eco_metrics = json.load(f)
            
    return users_df, repos_df, class_df, user_metrics_df, eco_metrics

# Load the data quietly
users_df, repos_df, class_df, user_metrics_df, eco_metrics = load_data()


# --- Main Layout ---
st.title("GitHub Peru Analytics 🇵🇪")
st.markdown("### Developer Ecosystem Dashboard")

if user_metrics_df.empty or not eco_metrics:
    st.warning("⚠️ Data is not fully loaded or processed yet. Please run the extraction, classification, and metrics scripts first.")
    st.stop()

# --- Sidebar ---
st.sidebar.title("Navigation")
st.sidebar.markdown("Use the navigation menu above or the sidebar links (if multi-page structure is used natively by Streamlit `pages/` dir) to explore different sections.")

st.sidebar.info(
    """
    **Data Stats:**
    - Developers: {:,}
    - Repositories: {:,}
    - Stars: {:,}
    """.format(
        eco_metrics.get("overview", {}).get("total_developers", 0),
        eco_metrics.get("overview", {}).get("total_repositories", 0),
        eco_metrics.get("overview", {}).get("total_stars_given", 0)
    )
)

st.markdown("""
Welcome to the **GitHub Peru Analytics** dashboard.
This tool visualizes data extracted from more than 1,000 repositories and 500+ top developers based in Peru.
""")

# Show key ecosystem overview here briefly before users jump to pages
ov = eco_metrics.get('overview', {})
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Developers", f"{ov.get('total_developers', 0):,}")
col2.metric("Total Repositories", f"{ov.get('total_repositories', 0):,}")
col3.metric("Total Stars", f"{ov.get('total_stars_given', 0):,}")
col4.metric("Active Devs", f"{ov.get('active_percentage', 0)}%")
