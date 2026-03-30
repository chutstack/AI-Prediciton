from setuptools import setup, find_packages

setup(
    name="ai-prediction",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "yfinance>=0.2.36",
        "pandas>=2.0.0",
        "numpy>=1.26.0",
        "scikit-learn>=1.4.0",
        "ta>=0.11.0",
        "matplotlib>=3.8.0",
    ],
    entry_points={
        "console_scripts": [
            "ai-prediction=ai_prediction.cli:main",
        ],
    },
    python_requires=">=3.9",
)
