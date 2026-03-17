# GitHub Peru Analytics

Data analytics platform to extract, process, and visualize information about the Peruvian developer ecosystem using the GitHub API and GPT-4 for industry classification.

## Antigravity

![Antigravity Easter Egg](./demo/antigravity_screenshot.png)

## Overview

This project provides an end-to-end data pipeline and a dashboard to explore the Peruvian developer ecosystem. It answers questions about top developers, prevalent programming languages, and uses AI to classify what industries these repositories are targeting (A-U CIIU).

## Architecture

1.  **Data Extraction**: Fetches >1000 repos and detailed user data using the GitHub API with a robust querying strategy (Location, Topics, Stars/Date) with rate limiting and retry handling.
2.  **Classification**: Uses GPT-4 to map repository metadata to 21 distinct CIIU industries.
3.  **Metrics Calculation**: Derives comprehensive User-Level metrics (`h_index`, `impact_score`, `activity`, etc.) and Ecosystem Metrics.
4.  **Dashboard**: Streamlit app with multiple views to explore the data.
5.  **AI Insights Agent**: Langchain-powered AI agent that acts as an interface to query the gathered datasets.

## Requirements

- Python 3.10+
- A GitHub Personal Access Token
- An OpenAI API Key

## Setup

1. Clone the repository and navigate to `github-peru-analytics`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API tokens.
   ```bash
   cp .env.example .env
   ```

## Usage

### 1. Data Pipeline
First, extract the data:
```bash
python scripts/extract_data.py
```

Then, classify industries using GPT-4:
```bash
python scripts/classify_repos.py
```

Calculate all metrics:
```bash
python scripts/calculate_metrics.py
```

### 2. Dashboard

Launch the Streamlit dashboard:
```bash
streamlit run app/main.py
```
