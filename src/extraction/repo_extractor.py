import base64
import logging
from typing import List, Dict, Any
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class RepoExtractor:
    def __init__(self, client: GitHubClient):
        self.client = client
        self.topic_queries = ["topic:peru", "topic:lima", "topic:peruvian"]

    def search_repos_robust(self, min_stars: int = 1) -> List[Dict[str, Any]]:
        """
        Search for top repositories related to Peru using topics.
        """
        all_repos = {}
        for query in self.topic_queries:
            q = query
            if min_stars > 0:
                q += f" stars:>={min_stars}"
                
            self._fetch_repo_pages(q, all_repos)
            
        return list(all_repos.values())
        
    def _fetch_repo_pages(self, query: str, all_repos: dict):
        page = 1
        per_page = 100
        while True:
            params = {
                "q": query,
                "per_page": per_page,
                "page": page,
                "sort": "stars",
                "order": "desc"
            }
            try:
                result = self.client.make_request("search/repositories", params=params)
                items = result.get("items", [])
                
                if not items:
                    break
                    
                for item in items:
                    if item["id"] not in all_repos:
                        all_repos[item["id"]] = item
                        
                if len(items) < per_page:
                    break
                    
                page += 1
                if page * per_page > 1000:
                    break
            except Exception as e:
                logger.error(f"Error fetching repos for query {query} page {page}: {e}")
                break

    def get_user_top_repos(self, username: str, min_stars: int = 0) -> List[Dict[str, Any]]:
        """Get the top repositories for a specific user"""
        repos = []
        try:
            user_repos = self.client.make_request(
                f"users/{username}/repos", 
                params={"sort": "stargazers_count", "direction": "desc", "per_page": 100, "type": "owner"}
            )
            for repo in user_repos:
                if repo.get("stargazers_count", 0) >= min_stars:
                    repos.append(repo)
        except Exception as e:
            logger.error(f"Error fetching top repos for {username}: {e}")
            
        # Top 10 by stars for specific user evaluation
        repos.sort(key=lambda x: x.get("stargazers_count", 0), reverse=True)
        return repos[:10]

    def get_repo_readme(self, owner: str, repo: str) -> str:
        """
        Get the README content of a repository.
        Returns empty string if not found.
        LIMITS content to 5000 chars for API limits in classification phase.
        """
        try:
            result = self.client.make_request(f"repos/{owner}/{repo}/readme")
            if not result or "content" not in result:
                return ""
                
            content = base64.b64decode(result["content"]).decode("utf-8", errors='ignore')
            return content[:5000]
        except Exception as e:
            logger.debug(f"README not found or error for {owner}/{repo}: {e}")
            return ""

    def get_repo_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get the language breakdown of a repository (bytes per language)."""
        try:
            return self.client.make_request(f"repos/{owner}/{repo}/languages")
        except Exception as e:
            logger.debug(f"Could not fetch languages for {owner}/{repo}: {e}")
            return {}

    def get_repo_contributors(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get the contributors of a repository."""
        try:
            # Check length to avoid massive repos blowing up rate limits (if desired), 
            # here we just take the first page to estimate
            result = self.client.make_request(
                f"repos/{owner}/{repo}/contributors", 
                params={"per_page": 100, "anon": "true"}
            )
            # handle cases where history is massive
            if isinstance(result, list):
                return result
            # sometimes returns 204 or dict if error
            return []
        except Exception as e:
            logger.debug(f"Could not fetch contributors for {owner}/{repo}: {e}")
            return []
