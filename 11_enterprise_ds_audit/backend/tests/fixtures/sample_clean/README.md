# Sample Clean Project

## Problem statement

Demo project that trains a classifier without obvious leakage.

## Dataset & source

Synthetic gaussian features generated in-process.

## Methodology

Train/test split first, then scaler fit on train only.

## How to run

```bash
python train.py
pytest
```

## Fairness

No protected attributes; fairness metrics N/A for this toy example.
