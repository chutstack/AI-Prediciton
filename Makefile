.PHONY: test train run backtest

test:
	pytest -q

train:
	python -m trader train --config configs/config.yaml

run:
	python -m trader run --config configs/config.yaml --mode paper

backtest:
	python -m trader backtest --config configs/config.yaml
