# Marathon Coach — AI-Powered Training App

An end-to-end machine learning application that connects to Strava analyzes your running history and predicts your marathon finish time with explainable AI.

I built this for my future marathons, the next one is the **NYC Marathon** (or probably the **SF Marathon**).

**Aeolus** he's the God of Wind.

## Live Demo

> Start the app locally with one command:
> ```bash
> docker-compose up -d && streamlit run dashboard/app.py
> ```
> Then open `http://localhost:8501`

---

## What it does

| Screen | Description |
|---|---|
| Dashboard | Predicted finish time, overtraining risk, SHAP insight |
| This week | Personalized 7-day training plan with pace targets |
| Trends | Pace improvement chart over last 8 weeks |
| Connect Strava | OAuth 2.0 authorization flow |

---

## ML Results

| Model | Metric | Result |
|---|---|---|
| Race time predictor | MAE | 19.5 minutes |
| Overtraining classifier | F1 score | 0.87 |
| Baseline (predict mean) | MAE | 37.5 minutes |
| Improvement over baseline | MAE reduction | 18.0 minutes |

Current prediction: **4h25m** finish time for NYC Marathon 2026.
Current status: **LOW RISK** (92.2% confidence).

---

## Architecture

```
Strava API (OAuth 2.0)
       ↓
PostgreSQL (106 runs stored)
       ↓
Feature Engineering (ACWR, pace trend, weekly load)
       ↓
XGBoost Predictor + Random Forest Classifier
       ↓
SHAP Explainability
       ↓
FastAPI (5 endpoints)
       ↓
Streamlit Dashboard
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Backend | FastAPI + Pydantic |
| ML | XGBoost, scikit-learn, SHAP |
| Database | PostgreSQL + SQLAlchemy |
| Cache | Redis |
| Dashboard | Streamlit + Plotly |
| Infrastructure | Docker + docker-compose |
| Auth | Strava OAuth 2.0 |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker Desktop
- A Strava account

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/iamafram/aeolus.git
cd aeolus

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Strava API credentials

# 5. Start services
docker-compose up -d

# 6. Run the dashboard
streamlit run dashboard/app.py
```

### First run
1. Open `http://localhost:8501`
2. Click **Connect Strava**
3. Authorize access
4. Your runs are imported automatically

### Train the models
```bash
python scripts/export_activities.py
python -m ml.train_predictor
python -m ml.train_classifier
python -m ml.evaluate
```

---

## Key Engineering Decisions

**TimeSeriesSplit over random split** — ML models trained on running data must always predict the future from the past. Random splitting leaks future data into training, inflating accuracy metrics. `TimeSeriesSplit` enforces temporal ordering.

**ACWR for overtraining detection** — Acute:Chronic Workload Ratio is a published sports science metric. Using domain knowledge to engineer features produces more reliable models than purely data-driven approaches.

**SHAP for explainability** — Every prediction includes a breakdown of which features drove it and by how much. This makes the model auditable and the insights actionable.

**Redis caching** — Strava rate-limits at 100 requests per 15 minutes. All API responses are cached with a 60-second TTL to prevent hitting limits during active dashboard use.

---

## Project Structure

```
aeolus/
├── api/                  # FastAPI backend
│   ├── routes/           # auth, plan, insights endpoints
│   ├── services.py       # training plan generator
│   └── main.py           # app entrypoint
├── pipeline/             # data layer
│   ├── strava_client.py  # OAuth 2.0 + API calls
│   ├── ingest.py         # fetch and store activities
│   ├── features.py       # ML feature engineering
│   └── models.py         # SQLAlchemy schema
├── ml/                   # machine learning
│   ├── train_predictor.py   # XGBoost race time model
│   ├── train_classifier.py  # overtraining risk model
│   └── evaluate.py          # SHAP explainability
├── dashboard/            # Streamlit UI
│   └── app.py
├── scripts/              # operational scripts
├── docs/                 # architecture documentation
├── docker-compose.yml
└── README.md
```

## Author

Built by **[Afram](https://www.linkedin.com/in/afram-diril/)**