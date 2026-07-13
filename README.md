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
