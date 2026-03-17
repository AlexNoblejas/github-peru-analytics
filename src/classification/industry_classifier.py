import os
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

class IndustryClassifier:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=api_key)
        
        self.industries = {
            "A": "Agriculture, forestry and fishing",
            "B": "Mining and quarrying",
            "C": "Manufacturing",
            "D": "Electricity, gas, steam supply",
            "E": "Water supply; sewerage",
            "F": "Construction",
            "G": "Wholesale and retail trade",
            "H": "Transportation and storage",
            "I": "Accommodation and food services",
            "J": "Information and communication",
            "K": "Financial and insurance activities",
            "L": "Real estate activities",
            "M": "Professional, scientific activities",
            "N": "Administrative and support activities",
            "O": "Public administration and defense",
            "P": "Education",
            "Q": "Human health and social work",
            "R": "Arts, entertainment and recreation",
            "S": "Other service activities",
            "T": "Activities of households",
            "U": "Extraterritorial organizations"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def classify_repository(self, name: str, description: str, readme: str, topics: List[str], languages: Dict[str, int]) -> Dict[str, Any]:
        """Classify a single repository utilizing GPT-4 with JSON output."""
        
        # Format inputs to avoid massive tokens
        desc = description or "No description"
        clean_readme = readme[:3000] if readme else "No README"
        top_topics = ", ".join(topics) if topics else "None"
        primary_lang = list(languages.keys())[0] if languages else "Not specified"
        
        prompt = f"""Analyze this GitHub repository and classify it into ONE of the following industry categories based on its potential application or the industry it serves.

REPOSITORY INFORMATION:
- Name: {name}
- Description: {desc}
- Primary Language: {primary_lang}
- Topics: {top_topics}
- README (excerpt): {clean_readme}

INDUSTRY CATEGORIES:
{json.dumps(self.industries, indent=2)}

INSTRUCTIONS:
1. Analyze the repository's purpose, functionality, and potential use cases.
2. Consider what industry would most benefit from or use this software.
3. If it's a general-purpose tool (e.g., utility library, web framework), classify based on the most likely industry application.
4. If truly generic (e.g., "hello world", personal config files, general learning), use "J" (Information and communication).
5. Always select exactly ONE valid industry code from A to U.

Respond in JSON format with the exact following keys:
{{
  "industry_code": "X",
  "industry_name": "Full industry name",
  "confidence": "high|medium|low",
  "reasoning": "Brief explanation of why this classification was chosen based on the repo metadata"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at classifying software projects by industry. Always respond with valid JSON matching the requested schema."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_str = response.choices[0].message.content
            return json.loads(result_str)
            
        except Exception as e:
            logger.warning(f"GPT classification failed for '{name}': {e}. Trying embedding fallback...")
            # --- Embedding fallback ---
            try:
                from src.classification.embedding_classifier import classify_with_embeddings
                api_key = os.getenv("OPENAI_API_KEY", "")
                topics_for_embed = topics if isinstance(topics, list) else []
                lang_for_embed = list(languages.keys())[0] if languages else ""
                result = classify_with_embeddings(
                    name=name,
                    description=description,
                    topics=topics_for_embed,
                    language=lang_for_embed,
                    api_key=api_key
                )
                result["reasoning"] = "[Embedding fallback] " + result.get("reasoning", "")
                return result
            except Exception as e2:
                logger.error(f"Embedding fallback also failed for '{name}': {e2}")
                return {
                    "industry_code": "J",
                    "industry_name": "Information and communication",
                    "confidence": "low",
                    "reasoning": f"Both GPT and embedding fallback failed: {str(e)} / {str(e2)}"
                }

    def batch_classify(self, repositories: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        """Classify a batch of repositories."""
        results = []
        total = len(repositories)
        
        logger.info(f"Starting classification of {total} repositories in batches of {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = repositories[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
            
            for repo in batch:
                name = repo.get("name", "")
                
                # Extract languages
                langs_raw = repo.get("languages_dict", "{}")
                if isinstance(langs_raw, str):
                    try:
                        langs = json.loads(langs_raw)
                    except:
                        langs = {}
                else:
                    langs = langs_raw
                    
                # Extract topics
                topics_raw = repo.get("topics", "[]")
                if isinstance(topics_raw, str):
                    try:
                        topics = json.loads(topics_raw)
                    except:
                        topics = []
                else:
                    topics = topics_raw
                
                classification = self.classify_repository(
                    name=name,
                    description=repo.get("description", ""),
                    readme=repo.get("readme_content", ""),
                    topics=topics,
                    languages=langs
                )
                
                results.append({
                    "repo_id": repo["id"],
                    "repo_name": name,
                    **classification
                })
                
        return results
