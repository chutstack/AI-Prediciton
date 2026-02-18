from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from trader.backtest.walkforward import run_walkforward
from trader.config import load_config
from trader.data.adapters import CryptoAdapter, EquityAdapter
from trader.execution.live_placeholders import LiveBrokerPlaceholder
from trader.execution.paper import PaperBroker
from trader.features.compute import compute_features, make_dataset
from trader.logging import JsonlLogger
from trader.model.artifacts import ArtifactStore
from trader.model.predict import predict_probability
from trader.model.train import train_asset
from trader.risk.caps import apply_crypto_cap
from trader.risk.regime import regime_status
from trader.risk.sizing import target_weight


def load_prices(cfg: dict) -> dict[str, pd.DataFrame]:
    c, e = CryptoAdapter(), EquityAdapter()
    out: dict[str, pd.DataFrame] = {}
    for asset in cfg["assets"]:
        out[asset] = c.fetch(asset) if asset in {"BTC-USD", "ETH-USD"} else e.fetch(asset)
    return out


def ensure_models(cfg: dict, prices: dict[str, pd.DataFrame], store: ArtifactStore) -> None:
    for asset in cfg["assets"]:
        if not Path(f"models/{asset}_model.pkl").exists():
            train_asset(asset, prices, cfg, store)


def cmd_train(args: argparse.Namespace) -> None:
    cfg = load_config(args.config).raw
    prices = load_prices(cfg)
    store = ArtifactStore()
    for asset in cfg["assets"]:
        metrics = train_asset(asset, prices, cfg, store)
        print(asset, metrics)


def cmd_run(args: argparse.Namespace) -> None:
    cfg = load_config(args.config).raw
    if os.getenv("KILL_SWITCH", "false").lower() == "true":
        print("Kill switch enabled; no trading.")
        return
    prices = load_prices(cfg)
    logger = JsonlLogger()
    store = ArtifactStore()
    ensure_models(cfg, prices, store)
    broker = (
        PaperBroker(fee_bps=cfg["paper_costs"]["fee_bps"], slippage_bps=cfg["paper_costs"]["slippage_bps"])
        if args.mode == "paper"
        else LiveBrokerPlaceholder()
    )
    weights: dict[str, float] = {}
    probs: dict[str, float] = {}
    regimes: dict[str, dict[str, float | bool]] = {}
    p_longs: dict[str, float] = {}
    latest_prices = {a: float(prices[a]["close"].iloc[-1]) for a in cfg["assets"]}

    snap = broker.snapshot()
    if bool(snap.get("disable_until_reset", False)):
        print("Trading disabled by drawdown lock.")
        return

    for asset in cfg["assets"]:
        model, meta = store.load(asset)
        feats = compute_features(prices[asset])
        full_x, _ = make_dataset(asset, prices, cfg["thresholds"][asset])
        prob = predict_probability(model, full_x, meta["features"])
        probs[asset] = prob
        p_long = float(meta.get("p_long", cfg["p_long"][asset]))
        p_longs[asset] = p_long
        regime = regime_status(asset, feats)
        regimes[asset] = regime
        sigma20 = float(feats["r1"].rolling(20).std().iloc[-1])
        tw = 0.0 if regime["bad"] else target_weight(prob, p_long, sigma20, cfg["vol_target"][asset], cfg["caps"]["per_asset"][asset])
        weights[asset] = tw
        print(
            f"{asset}: prob={prob:.4f}, p_long={p_long:.2f}, "
            f"regime_bad={regime['bad']}, sigma20={sigma20:.4f}, target={tw:.4f}"
        )

    weights = apply_crypto_cap(weights, cfg["caps"]["total_crypto"])

    portfolio_value = float(snap.get("cash", 0.0)) + sum(
        float(q) * latest_prices.get(sym, 0.0) for sym, q in snap.get("positions", {}).items()
    )
    if snap.get("equity_curve"):
        peak = max(v["equity"] for v in snap["equity_curve"])
        dd = 1 - portfolio_value / peak if peak else 0.0
        if dd > 0.20:
            snap["disable_until_reset"] = True
            broker.store.save(snap)
            print("Drawdown kill-switch triggered")
            return

    for asset, tw in weights.items():
        fill = broker.rebalance(asset, tw, latest_prices[asset])
        logger.log(
            {
                "asset": asset,
                "prob": probs[asset],
                "p_long": p_longs[asset],
                "regime_bad": regimes[asset]["bad"],
                "regime": regimes[asset],
                "target_weight": tw,
                "order": fill,
                "timestamp": pd.Timestamp.utcnow().isoformat(),
            }
        )
    state = broker.snapshot()
    eq = state.get("cash", 0.0) + sum(q * latest_prices.get(sym, 0.0) for sym, q in state.get("positions", {}).items())
    state.setdefault("equity_curve", []).append({"ts": pd.Timestamp.utcnow().isoformat(), "equity": eq})
    broker.store.save(state)
    print("Run complete", weights)


def cmd_backtest(args: argparse.Namespace) -> None:
    cfg = load_config(args.config).raw
    prices = load_prices(cfg)
    results = run_walkforward(prices, cfg)
    results.to_csv("backtest_results.csv", index=False)
    print(results.groupby("asset")[["accuracy", "auc", "logloss"]].mean())


def main() -> None:
    parser = argparse.ArgumentParser(prog="trader")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ["train", "run", "backtest"]:
        p = sub.add_parser(name)
        p.add_argument("--config", default="configs/config.yaml")
        if name == "run":
            p.add_argument("--mode", default="paper", choices=["paper", "live"])
    args = parser.parse_args()
    if args.cmd == "train":
        cmd_train(args)
    elif args.cmd == "run":
        cmd_run(args)
    else:
        cmd_backtest(args)
