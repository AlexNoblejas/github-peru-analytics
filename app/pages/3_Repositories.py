import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Repository Browser", page_icon="📁", layout="wide")
st.title("📁 Repository Browser")

@st.cache_data
def load_data():
    base_dir = "data/processed"
    repos_df = pd.DataFrame()
    class_df = pd.DataFrame()
    
    if os.path.exists(f"{base_dir}/repositories.csv"):
        repos_df = pd.read_csv(f"{base_dir}/repositories.csv")
    if os.path.exists(f"{base_dir}/classifications.csv"):
        class_df = pd.read_csv(f"{base_dir}/classifications.csv")
        
    return repos_df, class_df

repos_df, class_df = load_data()

if repos_df.empty:
    st.warning("No repository data available.")
    st.stop()

# Merge classification data explicitly if available
if 'id' in repos_df.columns and not class_df.empty and 'repo_id' in class_df.columns:
    df = pd.merge(repos_df, class_df, left_on='id', right_on='repo_id', how='left')
else:
    df = repos_df.copy()
    df['industry_name'] = "Unclassified"
    df['confidence'] = "N/A"

st.sidebar.header("Filters")

# Filters
language = st.sidebar.selectbox("Filter by Main Language", ["All"] + list(df['language'].dropna().unique()))
if language != "All":
    df = df[df['language'] == language]

if 'industry_name' in df.columns:
    industry = st.sidebar.selectbox("Filter by Industry", ["All"] + list(df['industry_name'].dropna().unique()))
    if industry != "All":
        df = df[df['industry_name'] == industry]

min_stars = st.sidebar.slider("Min Stars", 0, int(df['stargazers_count'].max() or 100), 0)
df = df[df['stargazers_count'] >= min_stars]

search_term = st.text_input("Search Repository (Name or Description):", "")
if search_term:
    mask = df['name'].str.contains(search_term, case=False, na=False) | df['description'].str.contains(search_term, case=False, na=False)
    df = df[mask]

st.markdown(f"**Showing {len(df)} repositories**")

display_cols = ['name', 'owner_login', 'description', 'language', 'stargazers_count']
if 'industry_name' in df.columns:
    display_cols.append('industry_name')
    display_cols.append('confidence')

st.dataframe(df[display_cols], use_container_width=True)
