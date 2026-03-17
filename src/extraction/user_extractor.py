import logging
from typing import List, Dict, Any
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class UserExtractor:
    def __init__(self, client: GitHubClient):
        self.client = client
        self.locations = ["Peru", "Lima", "Arequipa", "Cusco", "Trujillo"]

    def search_users_robust(self, min_followers: int = 0) -> List[Dict[str, Any]]:
        """
        Search for users combining different location queries and optional follower 
        filters to bypass the 1000 limit.
        """
        all_users = {}  # Use dict to deduplicate by username
        
        for location in self.locations:
            logger.info(f"Searching for users in location: {location}")
            # Try ascending
            self._fetch_user_pages(location, min_followers, "asc", all_users)
            # Try descending to get other side of the 1000 limit if needed
            self._fetch_user_pages(location, min_followers, "desc", all_users)

        return list(all_users.values())

    def _fetch_user_pages(self, location: str, min_followers: int, order: str, all_users: dict):
        page = 1
        per_page = 100
        
        query = f"location:{location}"
        if min_followers > 0:
            query += f" followers:>={min_followers}"

        while True:
            params = {
                "q": query,
                "per_page": per_page,
                "page": page,
                "sort": "followers",
                "order": order
            }
            try:
                result = self.client.make_request("search/users", params=params)
                items = result.get("items", [])
                
                if not items:
                    break
                
                for item in items:
                    # De-duplicate
                    if item["login"] not in all_users:
                        all_users[item["login"]] = item
                        
                if len(items) < per_page:
                    break  # Last page
                    
                page += 1
                
                # GitHub allows max 1000 results per search query (page * per_page <= 1000)
                if page * per_page > 1000:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching users for query {query} page {page}: {e}")
                break

    def get_user_details(self, username: str) -> Dict[str, Any]:
        """Get detailed information for a specific user."""
        try:
            return self.client.make_request(f"users/{username}")
        except Exception as e:
            logger.error(f"Error fetching details for user {username}: {e}")
            return {}

    def get_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """Get all repositories for a user."""
        repos = []
        page = 1
        while True:
            try:
                result = self.client.make_request(
                    f"users/{username}/repos",
                    params={
                        "per_page": 100,
                        "page": page,
                        "type": "owner"
                    }
                )
                if not result:
                    break
                    
                repos.extend(result)
                page += 1
            except Exception as e:
                logger.error(f"Error fetching repos for user {username} page {page}: {e}")
                break
                
        return repos
