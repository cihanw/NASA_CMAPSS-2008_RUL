# NASA C-MAPSS FD002 RUL Workflow

This repository contains the current local version of the NASA C-MAPSS Remaining Useful Life (RUL) workflow for the FD002 subset.

The intended run order is:

1. Run `preprocess/fd002_sensor_selection_and_clustering.py`.
2. Continue in the notebooks under `notebooks/`; the remaining preparation, training, evaluation, and artifact writing are handled there.

## Project Layout

- `data/raw/`: NASA C-MAPSS raw train, test, and RUL text files.
- `data/processed/`: FD002 operating-regime CSV files produced by the preprocessing script.
- `preprocess/fd002_sensor_selection_and_clustering.py`: clusters FD002 operating conditions, ranks sensors, and writes the processed FD002 regime files.
- `notebooks/fd002_svm_rf_training.ipynb`: classical FD002 model training with SVR and Random Forest.
- `notebooks/fd002_attention_lstm_training.ipynb`: FD002 Attention-LSTM training workflow.
- `artifacts/`: generated model outputs, metrics, predictions, and training history when notebooks have been run locally.
- `requirements.txt`: Python package requirements for the project environment.

## Environment Setup

Use a virtual environment for all Python commands.

```bash
cd /Users/cihan/Desktop/CMAPSS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run Order

First, generate or refresh the FD002 operating-regime files:

```bash
source .venv/bin/activate
python preprocess/fd002_sensor_selection_and_clustering.py
```

The script reads:

- `data/raw/train_FD002.txt`
- `data/raw/test_FD002.txt`

It writes the notebook inputs:

- `data/processed/fd002_train_regimes.csv`
- `data/processed/fd002_test_regimes.csv`

It also writes analysis tables and figures under `reports/` when the script is run.

After that, use the notebooks for the rest of the workflow:

```bash
jupyter notebook notebooks/fd002_svm_rf_training.ipynb
jupyter notebook notebooks/fd002_attention_lstm_training.ipynb
```

For non-interactive execution:

```bash
python -m jupyter nbconvert --to notebook --execute notebooks/fd002_svm_rf_training.ipynb --inplace
python -m jupyter nbconvert --to notebook --execute notebooks/fd002_attention_lstm_training.ipynb --inplace
```

The notebooks contain the feature preparation, model training, evaluation, and output-writing steps needed after the FD002 preprocessing script has been run.

## Notes

- The current repository flow is FD002-focused.
- `AGENTS.md` is intentionally ignored by Git.
- Large generated artifacts and local virtual-environment files should stay machine-local unless Git LFS is configured intentionally.
