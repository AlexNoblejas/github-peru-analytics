import os
import json
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class InsightsAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        self.llm = ChatOpenAI(temperature=0, api_key=api_key, model="gpt-4-turbo-preview")
        
        # Load datasets as dataframes memory-wise
        self.base_dir = "data"
        self._load_datasets()
        
        self.tools = [
            Tool(
                name="Search Top Developers",
                func=self._search_developers,
                description="Use this tool to find top developers by stars, followers, or impact score. Input should be a metric to sort by, like 'impact_score' or 'followers'. Optionally filter."
            ),
            Tool(
                name="Find Repositories by Industry",
                func=self._search_industry,
                description="Use this tool to get repositories that match a specific industry name or code. Input should be the exact industry name (e.g. 'Manufacturing')."
            ),
            Tool(
                name="Get Ecosystem Overview",
                func=self._get_overview,
                description="Use this tool to get the high-level metrics of the entire developer ecosystem like total devs, active percentage, and top languages. Input is ignored (just pass 'overview')."
            )
        ]
        
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )
        
    def _load_datasets(self):
        self.user_metrics = pd.DataFrame()
        self.class_df = pd.DataFrame()
        self.eco_metrics = {}
        
        try:
            if os.path.exists(f"{self.base_dir}/metrics/user_metrics.csv"):
                self.user_metrics = pd.read_csv(f"{self.base_dir}/metrics/user_metrics.csv")
                
            if os.path.exists(f"{self.base_dir}/processed/classifications.csv"):
                # Join with repos to get nice info in industry search
                classifications = pd.read_csv(f"{self.base_dir}/processed/classifications.csv")
                if os.path.exists(f"{self.base_dir}/processed/repositories.csv"):
                    repos = pd.read_csv(f"{self.base_dir}/processed/repositories.csv")
                    self.class_df = pd.merge(repos, classifications, left_on='id', right_on='repo_id')
                    
            if os.path.exists(f"{self.base_dir}/metrics/ecosystem_metrics.json"):
                with open(f"{self.base_dir}/metrics/ecosystem_metrics.json", "r", encoding="utf-8") as f:
                    self.eco_metrics = json.load(f)
        except Exception as e:
            logger.error(f"Error loading datasets for agent: {e}")

    def _search_developers(self, query: str) -> str:
        if self.user_metrics.empty:
            return "Developer data is not available."
            
        sort_col = 'impact_score'
        if 'star' in query.lower():
            sort_col = 'total_stars_received'
        elif 'follower' in query.lower():
            sort_col = 'followers'
            
        top_devs = self.user_metrics.nlargest(5, sort_col)
        results = []
        for _, dev in top_devs.iterrows():
            results.append(f"Name: {dev['login']}, Impact: {dev['impact_score']}, Stars: {dev['total_stars_received']}")
            
        return f"Top developers sorted by {sort_col}:\n" + "\n".join(results)
        
    def _search_industry(self, query: str) -> str:
        if self.class_df.empty:
            return "Classification data not available."
            
        industry = query.strip()
        filtered = self.class_df[self.class_df['industry_name'].str.contains(industry, case=False, na=False)]
        
        if filtered.empty:
            return f"No repositories found for industry containing '{industry}'"
            
        filtered = filtered.sort_values(by='stargazers_count', ascending=False).head(5)
        results = []
        for _, repo in filtered.iterrows():
            results.append(f"Repo: {repo['name']}, Stars: {repo['stargazers_count']}, Industry: {repo['industry_name']} (Confidence: {repo['confidence']})")
            
        return f"Top repositories for industry '{industry}':\n" + "\n".join(results)
        
    def _get_overview(self, query: str) -> str:
        if not self.eco_metrics:
            return "Ecosystem data not available."
            
        ov = self.eco_metrics.get('overview', {})
        av = self.eco_metrics.get('averages', {})
        return (
            f"Developer Ecosystem Overview:\n"
            f"- Total Developers: {ov.get('total_developers', 0)}\n"
            f"- Total Repos: {ov.get('total_repositories', 0)}\n"
            f"- Active Devs: {ov.get('active_percentage', 0)}%\n"
            f"- Avg Stars/Dev: {av.get('avg_stars_per_dev', 0)}\n"
        )
        
    def run_query(self, query: str) -> str:
        """Execute a query through the agent."""
        try:
            return self.agent.run(f"Answer the following question about the Peruvian GitHub developer ecosystem using only your tools. Question: {query}")
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return f"Error processing query: {str(e)}"

# Example usage (for testing)
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    agent = InsightsAgent()
    print(agent.run_query("Who are the top developers based on stars?"))
