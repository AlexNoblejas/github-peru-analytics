import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.metrics.user_metrics import MetricsGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"data/metrics_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting GitHub Peru Analytics Metrics Calculation")
    
    users_file = "data/processed/users.csv"
    repos_file = "data/processed/repositories.csv"
    class_file = "data/processed/classifications.csv"
    
    if not os.path.exists(users_file) or not os.path.exists(repos_file):
        logger.error("Required processed data files not found. Please run extraction first.")
        return
        
    logger.info("Loading processed data...")
    users_df = pd.read_csv(users_file)
    repos_df = pd.read_csv(repos_file)
    
    class_df = None
    if os.path.exists(class_file):
        class_df = pd.read_csv(class_file)
    else:
        logger.warning(f"Classifications file {class_file} not found. Industry metrics will be skipped.")
        
    generator = MetricsGenerator(users_df, repos_df, class_df)
    
    logger.info("Calculating User Metrics...")
    user_metrics_df = generator.calculate_user_metrics()
    
    if not user_metrics_df.empty:
        os.makedirs("data/metrics", exist_ok=True)
        user_metrics_df.to_csv("data/metrics/user_metrics.csv", index=False)
        logger.info(f"Saved {len(user_metrics_df)} user metrics to data/metrics/user_metrics.csv")
    else:
        logger.error("User metrics calculation returned empty dataframe.")
        return
        
    logger.info("Calculating Ecosystem Metrics...")
    eco_metrics = generator.calculate_ecosystem_metrics(user_metrics_df)
    
    if eco_metrics:
        with open("data/metrics/ecosystem_metrics.json", "w", encoding="utf-8") as f:
            json.dump(eco_metrics, f, indent=2, ensure_ascii=False)
        logger.info("Saved ecosystem metrics to data/metrics/ecosystem_metrics.json")
    else:
        logger.error("Ecosystem metrics calculation failed.")
        
    logger.info("Metrics calculation completed successfully!")

if __name__ == "__main__":
    main()
