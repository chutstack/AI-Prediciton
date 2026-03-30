# AI Prediction — Automated Trading & Forecasting System

A machine-learning-driven system for market data ingestion, price prediction, signal generation, and back-testing of trading strategies.

## Features

- Fetch OHLCV data (Yahoo Finance / CSV)
- Feature engineering (technical indicators)
- Train ML models (RandomForest, LSTM)
- Backtest strategies with performance metrics
- Generate buy/sell signals via a simple CLI

## Project Structure

```
ai_prediction/
├── data/          # Data ingestion & caching
├── features/      # Feature engineering
├── models/        # Model training & inference
├── backtest/      # Strategy back-testing
└── cli.py         # Command-line interface
```

## Quick Start

```bash
pip install -r requirements.txt
python -m ai_prediction.cli fetch --ticker AAPL --days 365
python -m ai_prediction.cli train --ticker AAPL
python -m ai_prediction.cli predict --ticker AAPL
python -m ai_prediction.cli backtest --ticker AAPL
```

## Requirements

Python 3.9+

```
yfinance
pandas
numpy
scikit-learn
ta
matplotlib
```
