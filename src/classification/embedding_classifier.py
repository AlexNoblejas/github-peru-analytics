import os
import json
import logging
import numpy as np
import requests
from typing import List, Dict, Any
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

# CIIU category names and rich descriptions for embedding comparison
CIIU_INDUSTRIES = {
    "A": ("Agriculture, forestry and fishing",
          "farming crops livestock aquaculture forestry fishing agriculture rural food production"),
    "B": ("Mining and quarrying",
          "mining quarrying minerals oil gas extraction petroleum coal resources geological"),
    "C": ("Manufacturing",
          "manufacturing factory production industrial assembly processing goods fabrication"),
    "D": ("Electricity, gas, steam supply",
          "electricity gas steam energy power utility generation distribution grid"),
    "E": ("Water supply; sewerage",
          "water sewerage sanitation treatment waste utility infrastructure"),
    "F": ("Construction",
          "construction building infrastructure civil engineering architecture real estate development"),
    "G": ("Wholesale and retail trade",
          "commerce retail wholesale ecommerce marketplace shopping trade sales store"),
    "H": ("Transportation and storage",
          "transportation logistics delivery shipping cargo fleet tracking mobility"),
    "I": ("Accommodation and food services",
          "hotel restaurant food service hospitality accommodation catering tourism"),
    "J": ("Information and communication",
          "software programming technology IT web app mobile data cloud AI machine learning"),
    "K": ("Financial and insurance activities",
          "finance banking insurance fintech payments investment credit loan economy"),
    "L": ("Real estate activities",
          "real estate property housing rent mortgage land urban planning"),
    "M": ("Professional, scientific activities",
          "consulting engineering research scientific laboratory professional services legal accounting"),
    "N": ("Administrative and support activities",
          "administration HR human resources office management operations support back-office"),
    "O": ("Public administration and defense",
          "government public policy defense military state administration civic"),
    "P": ("Education",
          "education learning teaching school university course e-learning academic training"),
    "Q": ("Human health and social work",
          "health medical hospital clinic telemedicine social care welfare patient"),
    "R": ("Arts, entertainment and recreation",
          "art entertainment media music gaming culture recreation sports creative"),
    "S": ("Other service activities",
          "personal services community nonprofit civil society membership organizations"),
    "T": ("Activities of households",
          "housework domestic household family personal home private"),
    "U": ("Extraterritorial organizations",
          "international organizations UN NGO embassy multilateral global governance"),
}


def _get_embedding_from_api(text: str, api_key: str, model: str = "text-embedding-3-small") -> np.ndarray:
    """Get embedding from OpenAI API."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"input": text[:8000], "model": model}
    r = requests.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    return np.array(r.json()["data"][0]["embedding"])


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def classify_with_embeddings(
    name: str,
    description: str,
    topics: List[str],
    language: str,
    api_key: str
) -> Dict[str, Any]:
    """
    Fast, cost-efficient classification using OpenAI embeddings.
    
    Uses text-embedding-3-small (~20x cheaper than GPT calls) to embed
    the repo metadata and compute cosine similarity against CIIU category
    descriptions. Best match wins.
    """
    # Build a rich text representation of this repo
    repo_text = " ".join(filter(None, [
        name,
        description or "",
        " ".join(topics) if topics else "",
        language or ""
    ]))

    if not repo_text.strip():
        return {
            "industry_code": "J",
            "industry_name": "Information and communication",
            "confidence": "low",
            "reasoning": "No text available; defaulted to software/IT category."
        }

    try:
        # Embed the repo description
        repo_vec = _get_embedding_from_api(repo_text, api_key)

        # Embed each CIIU category description (cached for speed on repeated calls)
        best_code = "J"
        best_score = -1.0
        scores = {}

        for code, (ind_name, ind_desc) in CIIU_INDUSTRIES.items():
            cat_text = f"{ind_name}: {ind_desc}"
            cat_vec = _get_embedding_from_api(cat_text, api_key)
            sim = _cosine_similarity(repo_vec, cat_vec)
            scores[code] = (ind_name, sim)
            if sim > best_score:
                best_score = sim
                best_code = code

        best_name, _ = scores[best_code]

        # Map similarity to confidence
        if best_score >= 0.35:
            confidence = "high"
        elif best_score >= 0.28:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "industry_code": best_code,
            "industry_name": best_name,
            "confidence": confidence,
            "reasoning": f"Embedding similarity score: {best_score:.3f} (cosine, text-embedding-3-small, vs CIIU category descriptions)."
        }

    except Exception as e:
        logger.error(f"Embedding classification error for '{name}': {e}")
        return {
            "industry_code": "J",
            "industry_name": "Information and communication",
            "confidence": "low",
            "reasoning": f"Embedding fallback error: {str(e)}"
        }
