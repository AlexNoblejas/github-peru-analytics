import os
import time
import requests
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

load_dotenv()


class GitHubRateLimitError(Exception):
    """Exception raised when GitHub API rate limit is exceeded."""
    def __init__(self, message, reset_time):
        self.message = message
        self.reset_time = reset_time
        super().__init__(self.message)


class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not found in environment variables.")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def check_rate_limit(self) -> dict:
        """Check current rate limit status."""
        response = requests.get(f"{self.base_url}/rate_limit", headers=self.headers)
        return response.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException, GitHubRateLimitError)),
    )
    def make_request(self, endpoint: str, params: dict = None) -> dict | list:
        """Make a rate-limit-aware request to GitHub API."""
        if params is None:
            params = {}

        response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)

        # Check rate limit
        remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
        
        if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait_time = reset_time - int(time.time())
            if wait_time > 0:
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds until reset...")
                time.sleep(wait_time + 1)
                raise GitHubRateLimitError("Rate limit exceeded", reset_time)
        elif remaining < 10:
             reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
             wait_time = reset_time - int(time.time())
             if wait_time > 0:
                 print(f"Warning: Low rate limit remaining ({remaining}). Waiting for {wait_time} seconds until reset...")
                 time.sleep(wait_time + 1)

        response.raise_for_status()
        
        # GitHub API returns an empty response for 204 No Content
        if response.status_code == 204:
            return {}
            
        return response.json()
