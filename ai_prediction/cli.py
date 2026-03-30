"""Command-line interface for AI Prediction."""
from __future__ import annotations

import argparse
import sys

from .data import fetch_ohlcv
from .features import build_features
from .models import ModelTrainer
from .backtest import BacktestEngine


def cmd_fetch(args: argparse.Namespace) -> None:
    print(f"Fetching {args.ticker} ({args.days} days)…")
    df = fetch_ohlcv(args.ticker, days=args.days, use_cache=False)
    print(df.tail())
    print(f"\n{len(df)} rows cached.")


def cmd_train(args: argparse.Namespace) -> None:
    print(f"Training model for {args.ticker}…")
    df = fetch_ohlcv(args.ticker, days=args.days)
    X, y = build_features(df, horizon=args.horizon)
    trainer = ModelTrainer(args.ticker, horizon=args.horizon)
    metrics = trainer.train(X, y)
    print(f"  CV accuracy : {metrics['cv_accuracy_mean']:.4f} ± {metrics['cv_accuracy_std']:.4f}")
    print(f"  CV scores   : {[round(s, 4) for s in metrics['cv_scores']]}")
    print("Model saved.")


def cmd_predict(args: argparse.Namespace) -> None:
    df = fetch_ohlcv(args.ticker, days=args.days)
    X, _ = build_features(df, horizon=args.horizon)
    trainer = ModelTrainer(args.ticker, horizon=args.horizon)
    proba = trainer.predict_proba(X.tail(1))
    direction = "UP" if proba[0, 1] >= 0.5 else "DOWN/FLAT"
    print(f"\nPrediction for {args.ticker} (next {args.horizon} day(s)): {direction}")
    print(f"  P(up)   = {proba[0, 1]:.4f}")
    print(f"  P(down) = {proba[0, 0]:.4f}")


def cmd_backtest(args: argparse.Namespace) -> None:
    print(f"Back-testing {args.ticker}…")
    df = fetch_ohlcv(args.ticker, days=args.days)
    X, y = build_features(df, horizon=args.horizon)
    trainer = ModelTrainer(args.ticker, horizon=args.horizon)

    try:
        signals = trainer.predict(X)
    except FileNotFoundError:
        print("No saved model found — training now…")
        trainer.train(X, y)
        signals = trainer.predict(X)

    engine = BacktestEngine(initial_capital=args.capital)
    engine.run(df.loc[X.index], signals)
    summary = engine.summary()

    print(f"\n{'=' * 40}")
    print(f"  Ticker          : {args.ticker}")
    print(f"  Initial capital : ${summary['initial_capital']:,.2f}")
    print(f"  Final value     : ${summary['final_value']:,.2f}")
    print(f"  Strategy return : {summary['total_return_pct']:+.2f}%")
    print(f"  Buy & hold      : {summary['buy_hold_return_pct']:+.2f}%")
    print(f"  Sharpe ratio    : {summary['sharpe_ratio']:.3f}")
    print(f"  Max drawdown    : {summary['max_drawdown_pct']:.2f}%")
    print(f"  Trading days    : {summary['trading_days']}")
    print(f"{'=' * 40}")


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="ai_prediction",
        description="AI-driven market prediction & back-testing CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── fetch ──────────────────────────────────────────────────────────
    p_fetch = sub.add_parser("fetch", help="Download & cache OHLCV data")
    p_fetch.add_argument("--ticker", default="AAPL")
    p_fetch.add_argument("--days", type=int, default=365)
    p_fetch.set_defaults(func=cmd_fetch)

    # ── train ──────────────────────────────────────────────────────────
    p_train = sub.add_parser("train", help="Train a prediction model")
    p_train.add_argument("--ticker", default="AAPL")
    p_train.add_argument("--days", type=int, default=730)
    p_train.add_argument("--horizon", type=int, default=1)
    p_train.set_defaults(func=cmd_train)

    # ── predict ────────────────────────────────────────────────────────
    p_pred = sub.add_parser("predict", help="Predict next-day direction")
    p_pred.add_argument("--ticker", default="AAPL")
    p_pred.add_argument("--days", type=int, default=730)
    p_pred.add_argument("--horizon", type=int, default=1)
    p_pred.set_defaults(func=cmd_predict)

    # ── backtest ───────────────────────────────────────────────────────
    p_bt = sub.add_parser("backtest", help="Back-test signals on historical data")
    p_bt.add_argument("--ticker", default="AAPL")
    p_bt.add_argument("--days", type=int, default=730)
    p_bt.add_argument("--horizon", type=int, default=1)
    p_bt.add_argument("--capital", type=float, default=10_000.0)
    p_bt.set_defaults(func=cmd_backtest)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
