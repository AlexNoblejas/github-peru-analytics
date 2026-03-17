import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Industry Analysis", page_icon="🏭", layout="wide")
st.title("🏭 Industry Analysis")

@st.cache_data
def load_data():
    base_dir = "data/processed"
    if os.path.exists(f"{base_dir}/classifications.csv") and os.path.exists(f"{base_dir}/repositories.csv"):
        class_df = pd.read_csv(f"{base_dir}/classifications.csv")
        repos_df = pd.read_csv(f"{base_dir}/repositories.csv")
        merged = pd.merge(repos_df, class_df, left_on='id', right_on='repo_id')
        return merged
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Classification data is not available. Have you run the classification script?")
    st.stop()

st.markdown("This view uses the GPT-4 classifications mapped to the 21 Peruvian CIIU categories to analyze the domain relevance of open-source projects.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Repository Distribution by Industry")
    ind_counts = df['industry_name'].value_counts().reset_index()
    ind_counts.columns = ['Industry', 'Count']
    
    fig = px.pie(ind_counts, values='Count', names='Industry', hole=0.4, title="Industry Market Share")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Most Starred Industries")
    stars_by_ind = df.groupby('industry_name')['stargazers_count'].sum().reset_index().sort_values(by='stargazers_count', ascending=False)
    
    fig2 = px.bar(stars_by_ind.head(10), x='stargazers_count', y='industry_name', orientation='h', title="Total Stars per Industry")
    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Top Repositories by Industry")
selected_industry = st.selectbox("Select Industry to view top repos:", sorted(df['industry_name'].unique()))

industry_repos = df[df['industry_name'] == selected_industry].sort_values(by='stargazers_count', ascending=False)
st.dataframe(
    industry_repos[['name', 'owner_login', 'description', 'stargazers_count', 'language', 'confidence', 'reasoning']], 
    use_container_width=True
)
