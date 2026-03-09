# 5-Minute Quickstart

## 1) Setup

```bash
git clone https://github.com/jakerslam/pqts.git
cd pqts
make setup
source .venv/bin/activate
cp .env.example .env
```

## 2) Run Paper Engine

```bash
python main.py config/paper.yaml
```

## 3) Open Dashboard

```bash
python -m streamlit run src/dashboard/app.py
```

Dashboard URL: `http://localhost:8501`

## 4) Produce a Simulation Leaderboard

```bash
make sim-suite
python scripts/export_simulation_leaderboard_site.py --reports-dir data/reports --output-dir site
```

## 5) Optional Docker Launch

```bash
docker compose up --build
```
