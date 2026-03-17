import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classification.industry_classifier import IndustryClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"data/classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting GitHub Peru Analytics Industry Classification (fast mode)")
    
    input_file = "data/processed/repositories.csv"
    output_file = "data/processed/classifications.csv"
    
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found. Run extract_data.py first.")
        return
        
    try:
        classifier = IndustryClassifier()
    except ValueError as e:
        logger.error(f"Initialization error: {e}")
        return
        
    logger.info(f"Loading repositories from {input_file}")
    repos_df = pd.read_csv(input_file)
    repos_df = repos_df.dropna(subset=['id', 'name'])
    
    # Sort by stars and take top 500 only for fast, relevant classification
    repos_df = repos_df.sort_values('stargazers_count', ascending=False).head(500)
    logger.info(f"Will classify top {len(repos_df)} repositories by stars.")
    
    # --- Resume support: skip already classified repos ---
    already_done = set()
    existing_results = []
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        already_done = set(existing_df['repo_id'].tolist())
        existing_results = existing_df.to_dict('records')
        logger.info(f"Resuming: {len(already_done)} repos already classified, skipping them.")
    
    # Filter to only unclassified repos
    repos_list = [r for r in repos_df.to_dict('records') if r['id'] not in already_done]
    logger.info(f"Repos left to classify: {len(repos_list)}")
    
    if not repos_list:
        logger.info("All repos already classified! Nothing to do.")
        return

    batch_size = 20
    total = len(repos_list)
    all_results = list(existing_results)  # start from previously saved

    for batch_start in range(0, total, batch_size):
        batch = repos_list[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        logger.info(f"Processing batch {batch_num}/{total_batches}")
        
        for repo in batch:
            name = repo.get("name", "")
            
            langs_raw = repo.get("languages_dict", "{}")
            if isinstance(langs_raw, str):
                try:
                    langs = json.loads(langs_raw)
                except:
                    langs = {}
            else:
                langs = langs_raw
                
            topics_raw = repo.get("topics", "[]")
            if isinstance(topics_raw, str):
                try:
                    topics = json.loads(topics_raw)
                except:
                    topics = []
            else:
                topics = topics_raw
            
            classification = classifier.classify_repository(
                name=name,
                description=repo.get("description", ""),
                readme=repo.get("readme_content", ""),
                topics=topics,
                languages=langs
            )
            
            all_results.append({
                "repo_id": repo["id"],
                "repo_name": name,
                **classification
            })
        
        # Save after every batch (incremental)
        pd.DataFrame(all_results).to_csv(output_file, index=False)
        logger.info(f"Saved {len(all_results)} classifications so far.")
    
    logger.info(f"Classification complete! Total: {len(all_results)} repos classified.")

if __name__ == "__main__":
    main()
