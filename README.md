# AI-Prediciton: Easy Niche Model

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
