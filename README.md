# AI Prediction Trader

Production-minded AI auto-trading scaffold for BTC-USD, ETH-USD, and SPY with strict safeguards and paper trading by default.

## Quickstart

1. Create env and install:
   - `pip install -r requirements.txt`
2. Copy env file:
   - `cp .env.example .env`
3. Train models:
   - `python -m trader train --config configs/config.yaml`
4. Run paper trading:
   - `python -m trader run --config configs/config.yaml --mode paper`
5. Run walk-forward backtest:
   - `python -m trader backtest --config configs/config.yaml`

## What training now does

- Performs per-asset walk-forward parameter search over several model candidates.
- Selects the best candidate by walk-forward AUC (with logloss tie-break).
- Calibrates each asset's `p_long` cutoff from walk-forward predictions (balanced accuracy objective).
- Stores tuned settings in `models/<asset>_meta.json` and uses calibrated `p_long` during `run`.

## Backtest output

`python -m trader backtest` writes `backtest_results.csv` with per-split:

- `accuracy`
- `auc`
- `logloss`
- `n_test`

## Scheduling

Use cron/systemd to call the run command once daily after market close.

## Safety

- Live mode requires both `--mode live` and `ENABLE_LIVE_TRADING=true`.
- `KILL_SWITCH=true` disables all order placement.
- Drawdown kill switch disables trading if portfolio drawdown exceeds 20%.
