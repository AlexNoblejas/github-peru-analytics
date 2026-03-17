import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Language Analytics", page_icon="💻", layout="wide")
st.title("💻 Language Analytics")

@st.cache_data
def load_data():
    base_dir = "data/processed"
    if os.path.exists(f"{base_dir}/repositories.csv"):
        return pd.read_csv(f"{base_dir}/repositories.csv")
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No repository data available.")
    st.stop()


col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Programming Languages")
    lang_counts = df['language'].value_counts().reset_index().head(15)
    lang_counts.columns = ['Language', 'Repository Count']
    
    fig1 = px.bar(lang_counts, x='Repository Count', y='Language', orientation='h', color='Repository Count', color_continuous_scale='Blues')
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Stars by Language")
    stars_lang = df.groupby('language')['stargazers_count'].sum().reset_index().sort_values(by='stargazers_count', ascending=False).head(15)
    
    fig2 = px.bar(stars_lang, x='stargazers_count', y='language', orientation='h', color='stargazers_count', color_continuous_scale='Oranges')
    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Language Correlation with Repository Age")
df['created_year'] = pd.to_datetime(df['created_at']).dt.year
top_5_langs = lang_counts['Language'].head(5).tolist()

trend_df = df[df['language'].isin(top_5_langs)]
trend_counts = trend_df.groupby(['created_year', 'language']).size().reset_index(name='count')

fig3 = px.line(trend_counts, x='created_year', y='count', color='language', title="Repository Creation Trend for Top 5 Languages")
st.plotly_chart(fig3, use_container_width=True)
