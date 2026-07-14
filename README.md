# Forecast Lab

A working MVP for transparent, AI-assisted prediction. Users define a binary forecasting question, set a base-rate prior, add evidence, and receive an explainable probability estimate.

## What works

- Interactive prediction form
- Adjustable prior probability
- Evidence-aware scoring
- Confidence rating and visible reasoning
- Responsive UI
- No API key or backend required
- Ready to deploy on Vercel

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Production build

```bash
npm run build
npm start
```

## MVP limitations

The current scoring engine is deliberately deterministic and inspectable. It is not a trained forecasting model and should not be used as financial, medical, or legal advice. A future version can replace `scoreForecast` with an LLM-backed structured prediction API, persistent forecast history, calibration tracking, and live evidence retrieval.

## Included Python model

This repository now includes a **workable best-of blend model** aimed at solving easy niche binary prediction tasks.

## What it does

`niche_model.py` trains multiple lightweight strategies, evaluates them, and blends the top performers:

- **Prior strategy**: robust baseline for imbalanced outcomes.
- **Single-feature threshold**: captures strong one-variable cutoffs.
- **Nearest centroid**: captures geometric separation in small tabular datasets.

It then keeps the best strategies and combines their outputs using score-based weights.

## Why this fits "easy niche problems"

- Fast to train.
- Works with tiny datasets.
- No heavy ML frameworks required.
- Strategy-level transparency (you can see which approaches won).

## Run

```bash
python3 niche_model.py
```

You should see selected strategies and overall accuracy on the synthetic niche dataset.
