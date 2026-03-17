import logging
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MetricsGenerator:
    def __init__(self, users_df: pd.DataFrame, repos_df: pd.DataFrame, class_df: pd.DataFrame = None):
        self.users_df = users_df
        # Ensure datetimes
        self.users_df['created_at'] = pd.to_datetime(self.users_df['created_at'])
        
        self.repos_df = repos_df
        if not self.repos_df.empty:
            self.repos_df['created_at'] = pd.to_datetime(self.repos_df['created_at'])
            self.repos_df['pushed_at'] = pd.to_datetime(self.repos_df['pushed_at'])
        
        self.class_df = class_df if class_df is not None else pd.DataFrame()

    def calculate_user_metrics(self) -> pd.DataFrame:
        """Calculate the required user metrics based on the assignment rules."""
        if self.users_df.empty:
            return pd.DataFrame()
            
        metrics = []
        now = pd.Timestamp(datetime.now(tz=self.users_df['created_at'].dt.tz))
        
        for _, user in self.users_df.iterrows():
            login = user['login']
            
            # Filter repos for this user
            user_repos = self.repos_df[self.repos_df['owner_login'] == login] if not self.repos_df.empty else pd.DataFrame()
            
            # 1. Activity Metrics
            total_repos = len(user_repos)
            total_stars = user_repos['stargazers_count'].sum() if total_repos > 0 else 0
            total_forks = user_repos['forks_count'].sum() if total_repos > 0 else 0
            avg_stars = total_stars / total_repos if total_repos > 0 else 0
            account_age_days = (now - user['created_at']).days if pd.notna(user['created_at']) else 1
            account_age_days = max(1, account_age_days) # prevent div by zero
            repos_per_year = total_repos / (account_age_days / 365.25)
            
            # 2. Influence Metrics
            followers = user.get('followers', 0)
            following = user.get('following', 0)
            follower_ratio = followers / following if following > 0 else followers
            
            # Calculate h-index
            h_index = 0
            if total_repos > 0:
                stars_list = sorted(user_repos['stargazers_count'].dropna().tolist(), reverse=True)
                for i, stars in enumerate(stars_list):
                    if stars >= i + 1:
                        h_index = i + 1
                    else:
                        break
                        
            impact_score = (total_stars * 0.5) + (followers * 0.3) + (total_forks * 0.2)
            
            # 3. Technical Metrics
            primary_languages = "None"
            language_diversity = 0
            has_readme_pct = 0
            has_license_pct = 0
            industries_served = "None"
            
            if total_repos > 0:
                # Primary languages setup
                all_langs = user_repos['language'].dropna().value_counts()
                if not all_langs.empty:
                    primary_languages = ", ".join(all_langs.head(3).index.tolist())
                    language_diversity = len(all_langs)
                    
                # Setup percentages
                repos_with_readme = user_repos['readme_content'].apply(lambda x: isinstance(x, str) and len(x) > 10).sum()
                has_readme_pct = (repos_with_readme / total_repos) * 100
                
                repos_with_license = user_repos['license_key'].notna().sum()
                has_license_pct = (repos_with_license / total_repos) * 100
                
                # Industries served
                if not self.class_df.empty and 'repo_id' in self.class_df.columns:
                    repo_ids = user_repos['id'].tolist()
                    user_classes = self.class_df[self.class_df['repo_id'].isin(repo_ids)]
                    if not user_classes.empty:
                        inds = user_classes['industry_name'].dropna().unique().tolist()
                        industries_served = ", ".join(inds)
            
            # 4. Engagement Metrics
            total_open_issues = user_repos['open_issues_count'].sum() if total_repos > 0 else 0
            
            days_since_last_push = 9999
            if total_repos > 0 and not user_repos['pushed_at'].isna().all():
                latest_push = user_repos['pushed_at'].max()
                if pd.notna(latest_push):
                    # Ensure now is timezone aware if push is
                    if latest_push.tzinfo is not None and now.tzinfo is None:
                        import pytz
                        now_tz = datetime.now(pytz.utc)
                        days_since_last_push = (now_tz - latest_push).days
                    else:
                        days_since_last_push = (now.replace(tzinfo=None) - latest_push.replace(tzinfo=None)).days
                        
            is_active = days_since_last_push <= 90
            
            metrics.append({
                "login": login,
                "name": user.get('name', ''),
                # Activity
                "total_repos": total_repos,
                "total_stars_received": total_stars,
                "total_forks_received": total_forks,
                "avg_stars_per_repo": round(avg_stars, 2),
                "account_age_days": account_age_days,
                "repos_per_year": round(repos_per_year, 2),
                # Influence
                "followers": followers,
                "following": following,
                "follower_ratio": round(follower_ratio, 2),
                "h_index": h_index,
                "impact_score": round(impact_score, 2),
                # Technical
                "primary_languages": primary_languages,
                "language_diversity": language_diversity,
                "industries_served": industries_served,
                "has_readme_pct": round(has_readme_pct, 2),
                "has_license_pct": round(has_license_pct, 2),
                # Engagement
                "total_open_issues": total_open_issues,
                "days_since_last_push": days_since_last_push,
                "is_active": is_active,
                # For consistency just measure stars per repo roughly
                "contribution_consistency": "High" if total_repos > 10 and is_active else "Medium" if is_active else "Low"
            })
            
        return pd.DataFrame(metrics)

    def calculate_ecosystem_metrics(self, user_metrics_df: pd.DataFrame) -> Dict[str, Any]:
        """Aggregate data to build overall ecosystem metrics."""
        if user_metrics_df.empty or self.repos_df.empty:
            return {}
            
        total_devs = len(user_metrics_df)
        active_devs = user_metrics_df['is_active'].sum()
        
        eco_metrics = {
            "overview": {
                "total_developers": total_devs,
                "active_developers": int(active_devs),
                "active_percentage": round((active_devs / total_devs) * 100, 1) if total_devs > 0 else 0,
                "total_repositories": len(self.repos_df),
                "total_stars_given": int(self.repos_df['stargazers_count'].sum()),
                "total_forks": int(self.repos_df['forks_count'].sum())
            },
            "averages": {
                "avg_repos_per_dev": round(len(self.repos_df) / total_devs, 1) if total_devs > 0 else 0,
                "avg_stars_per_dev": round(user_metrics_df['total_stars_received'].mean(), 1),
                "avg_followers_per_dev": round(user_metrics_df['followers'].mean(), 1),
                "avg_account_age_years": round(user_metrics_df['account_age_days'].mean() / 365.25, 1)
            },
            "top_languages": {},
            "top_industries": {}
        }
        
        # Aggregate languages
        if not self.repos_df.empty and 'language' in self.repos_df.columns:
            lang_counts = self.repos_df['language'].value_counts().head(10).to_dict()
            eco_metrics["top_languages"] = {str(k): int(v) for k, v in lang_counts.items() if pd.notna(k)}
            
        # Aggregate industries
        if not self.class_df.empty and 'industry_name' in self.class_df.columns:
            ind_counts = self.class_df['industry_name'].value_counts().head(10).to_dict()
            eco_metrics["top_industries"] = {str(k): int(v) for k, v in ind_counts.items() if pd.notna(k)}
            
        return eco_metrics
