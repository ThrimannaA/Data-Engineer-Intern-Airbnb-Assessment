# 🏠 Airbnb Market Intelligence

## Overview

A comprehensive data engineering and analytics project analyzing short-term rental markets across **New York City, Barcelona, and Edinburgh**. This project transforms raw Airbnb data into actionable business insights through a complete data pipeline, statistical analysis, machine learning, and an interactive dashboard.

**Key Deliverables:**
- ✅ End-to-end data pipeline (ingestion → cleaning → enrichment → star schema)
- ✅ 5 statistical hypotheses with effect sizes
- ✅ Price prediction ML model (XGBoost, R²=0.78)
- ✅ NLP sentiment analysis & topic modeling
- ✅ Interactive Streamlit dashboard
- ✅ 20+ page professional report

# Project Structure

```text
airbnb-assessment/
├── src/
│   ├── ingestion/          # Data loading from CSV/GZ files
│   ├── cleaning/           # Price, date, categorical standardization
│   ├── enrichment/         # Derived features (host tenure, price per bedroom)
│   ├── modeling/           # Star schema implementation in SQLite
│   └── pipeline/           # Orchestration script
├── notebooks/              # Analysis notebooks (EDA, statistics, ML, NLP)
├── dashboard/              # Streamlit interactive dashboard
├── reports/
│   ├── final_report.md     # 20+ page professional report
│   ├── assumptions.md      # Complete data assumptions
│   ├── decision_log.md     # Engineering decisions & trade-offs
│   ├── ai_disclosure.md    # AI tool usage disclosure
│   ├── completed_work.md   # Work summary with prioritization rationale
│   └── figures/            # High-quality visualization images
├── data/                   # Raw and processed data (gitignored)
├── config/                 # YAML configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

# Quick Start

## Prerequisites

* Python 3.9+
* Virtual environment (recommended)

---

## Setup & Installation

```bash
# Clone repository
git clone <repo-url>
cd airbnb-assessment

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Data Setup

### Option 1: Manual Download (Recommended)

Download data from Inside Airbnb and place files in:

```text
data/raw/nyc/
data/raw/barcelona/
data/raw/edinburgh/
```

### Option 2: Pipeline Download

```bash
python src/pipeline/run_pipeline.py --download --cities all
```

---

## Run Complete Pipeline

### Process All Cities

```bash
python src/pipeline/run_pipeline.py --cities all
```

### Process a Single City

```bash
python src/pipeline/run_pipeline.py --cities nyc
```

---

## Model Artifacts

Trained machine learning models (`.pkl`, `.pickle`, `.model`) are not stored in the repository and are excluded via `.gitignore` to keep the repository lightweight.

Models are generated during execution of the machine learning pipeline and can be recreated by running:

```bash
python src/pipeline/run_pipeline.py --cities all
```

or the machine learning notebook:

```bash
jupyter notebook notebooks/04_price_prediction.ipynb
```

---

## Launch Dashboard

```bash
streamlit run dashboard/app.py
```
## Dashboard Demo

A demonstration video of the interactive Streamlit dashboard is available below:

**Demo Video:**
[Watch Dashboard Demo](https://drive.google.com/file/d/1i7sESTA_APfy8OUfjv5Fu8R9fkVmqei9/view?usp=sharing)

The video showcases:

* City selection (NYC, Barcelona, Edinburgh)
* Market overview metrics
* Price distribution analysis
* Room type distribution
* Neighbourhood-level insights
* Rating distribution
* Cross-city radar comparison

# Analysis Workflow

## Step 1: Data Exploration

```bash
jupyter notebook notebooks/01_schema_exploration.ipynb
```

### Activities

* Schema documentation
* Data relationships mapping
* Cross-city schema comparison

---

## Step 2: Exploratory Data Analysis

```bash
jupyter notebook notebooks/02_eda_analysis.ipynb
```

### Activities

* Price distributions
* Geographic patterns
* Temporal trends
* Host & review analysis
* Business interpretations

---

## Step 3: Statistical Analysis

```bash
jupyter notebook notebooks/03_statistical_analysis.ipynb
```

### Activities

* 5 hypothesis tests (H1-H5)
* Effect sizes (Cohen's d, η²)
* Confidence intervals
* Correlation & driver analysis

---

## Step 4: Machine Learning

```bash
jupyter notebook notebooks/04_price_prediction.ipynb
```

### Activities

* 3 models (Linear Regression, Random Forest, XGBoost)
* Cross-validation
* SHAP explainability
* Residual analysis

---

## Step 5: NLP & AI Analysis

```bash
jupyter notebook notebooks/05_nlp_analysis.ipynb
```

### Activities

* Sentiment analysis (VADER)
* Topic modeling (NMF)
* RAG system (TF-IDF retrieval)
* LLM insight generation

---

## Step 6: Interactive Dashboard

```bash
streamlit run dashboard/app.py
```

### Features

* City selection (NYC, Barcelona, Edinburgh)
* Market overview metrics
* Price distribution
* Room type distribution
* Price by neighbourhood
* Rating distribution
* Cross-city radar comparison

---

# Key Findings

| Finding             | NYC          | Barcelona    | Edinburgh     |
| ------------------- | ------------ | ------------ | ------------- |
| Average Price       | $245         | $180         | $145          |
| Entire Home Premium | 89%          | 63%          | 72%           |
| Superhost Effect    | +0.22 rating | +0.18 rating | +0.25 rating  |
| Seasonal Peak       | Mar, Sep     | Jun-Aug      | August (+45%) |
| Multi-listing Hosts | 34%          | 22%          | 18%           |

---

# Technologies Used

| Category         | Tools                       |
| ---------------- | --------------------------- |
| Languages        | Python, SQL                 |
| Data Processing  | pandas, numpy, SQLite       |
| Visualization    | matplotlib, seaborn, plotly |
| Statistics       | scipy, statsmodels          |
| Machine Learning | scikit-learn, XGBoost, SHAP |
| NLP              | NLTK, VADER, sklearn        |
| Dashboard        | Streamlit                   |
| Containerization | Docker, docker-compose      |

---

# Report

The complete analysis is documented in `reports/final_report.pdf`, including:

* Executive summary
* Methodology
* Engineering approach
* EDA findings
* Statistical results
* ML results
* NLP & AI analysis
* Business recommendations
* Cross-city comparison
* AI usage disclosure
* Decision log

Additional supporting documentation is available in:

* `reports/ai_disclosure.pdf` – AI tool usage disclosure
* `reports/assumptions.pdf` – Data assumptions and constraints
* `reports/completed_work.pdf` – Work summary and prioritization rationale
* `reports/decision_log.pdf` – Engineering decisions and trade-offs
---



