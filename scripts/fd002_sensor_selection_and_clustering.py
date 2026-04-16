from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


RANDOM_STATE = 42
K_RANGE = range(2, 10)
FINAL_K = 6
WORKING_SET_SIZE = 12
RESERVE_SET_SIZE = 14
ROLLING_WINDOW = 5
SILHOUETTE_SAMPLE_SIZE = 5000

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURES_DIR = ROOT / "reports" / "figures"
TABLES_DIR = ROOT / "reports" / "tables"

OP_COLS = ["op1", "op2", "op3"]
SENSOR_COLS = [f"s{i}" for i in range(1, 22)]
ALL_COLS = ["unit", "cycle", *OP_COLS, *SENSOR_COLS]


def load_split(split: str) -> pd.DataFrame:
    path = RAW_DIR / f"{split}_FD002.txt"
    df = pd.read_csv(path, sep=r"\s+", header=None).iloc[:, :26].copy()
    df.columns = ALL_COLS
    return df


def add_train_rul(train_df: pd.DataFrame) -> pd.DataFrame:
    train_df = train_df.copy()
    max_cycle = train_df.groupby("unit")["cycle"].transform("max")
    train_df["train_rul"] = max_cycle - train_df["cycle"]
    return train_df


def fit_regime_model(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scaler = StandardScaler()
    train_ops = scaler.fit_transform(train_df[OP_COLS].to_numpy(dtype=float))
    test_ops = scaler.transform(test_df[OP_COLS].to_numpy(dtype=float))

    rng = np.random.default_rng(RANDOM_STATE)
    sample_size = min(SILHOUETTE_SAMPLE_SIZE, len(train_ops))
    sample_idx = rng.choice(len(train_ops), size=sample_size, replace=False)
    silhouette_sample = train_ops[sample_idx]

    k_records: list[dict[str, float]] = []
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")
        for k in K_RANGE:
            model = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE)
            train_labels = model.fit_predict(train_ops)
            sil_labels = model.predict(silhouette_sample)
            k_records.append(
                {
                    "k": k,
                    "inertia": float(model.inertia_),
                    "silhouette": float(silhouette_score(silhouette_sample, sil_labels)),
                }
            )

        final_model = KMeans(n_clusters=FINAL_K, n_init=50, random_state=RANDOM_STATE)
        raw_train_labels = final_model.fit_predict(train_ops)
        raw_test_labels = final_model.predict(test_ops)

    centers = pd.DataFrame(
        scaler.inverse_transform(final_model.cluster_centers_),
        columns=OP_COLS,
    )
    centers["raw_cluster"] = np.arange(len(centers))
    centers = centers.sort_values(OP_COLS).reset_index(drop=True)
    centers["regime_id"] = np.arange(len(centers))

    label_map = dict(zip(centers["raw_cluster"], centers["regime_id"]))
    train_df = train_df.copy()
    test_df = test_df.copy()
    train_df["regime_id"] = pd.Series(raw_train_labels).map(label_map).astype(int).to_numpy()
    test_df["regime_id"] = pd.Series(raw_test_labels).map(label_map).astype(int).to_numpy()

    centers = centers.drop(columns=["raw_cluster"])
    centers["train_rows"] = centers["regime_id"].map(train_df["regime_id"].value_counts().sort_index()).astype(int)
    centers["test_rows"] = centers["regime_id"].map(test_df["regime_id"].value_counts().sort_index()).astype(int)
    centers["train_share"] = centers["train_rows"] / len(train_df)
    centers["test_share"] = centers["test_rows"] / len(test_df)

    return train_df, test_df, centers, pd.DataFrame(k_records)


def compute_sensor_scores(train_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    grouped = train_df.groupby("unit", sort=True)

    for sensor in SENSOR_COLS:
        monotonicity_values: list[float] = []
        start_values: list[float] = []
        end_values: list[float] = []

        for _, group in grouped:
            smooth = group[sensor].rolling(window=ROLLING_WINDOW, min_periods=1, center=True).median()
            if smooth.nunique() < 2:
                monotonicity_values.append(0.0)
            else:
                monotonicity_values.append(abs(float(spearmanr(group["cycle"], smooth).statistic)))
            start_values.append(float(smooth.iloc[0]))
            end_values.append(float(smooth.iloc[-1]))

        monotonicity = float(np.nanmean(monotonicity_values))
        start_values_arr = np.asarray(start_values)
        end_values_arr = np.asarray(end_values)
        mean_drift = float(np.mean(np.abs(end_values_arr - start_values_arr)))
        prognosability = float(np.exp(-np.std(end_values_arr) / mean_drift)) if mean_drift > 1e-12 else 0.0

        series = train_df[sensor]
        overall_mean = float(series.mean())
        regime_group = train_df.groupby("regime_id")[sensor]
        regime_means = regime_group.mean()
        regime_sizes = regime_group.size()
        between_ss = float(np.sum(regime_sizes * (regime_means - overall_mean) ** 2))
        total_ss = float(np.sum((series - overall_mean) ** 2))
        regime_sensitivity = between_ss / total_ss if total_ss > 0 else 0.0

        nunique = int(series.nunique())
        continuity = min(1.0, np.log1p(nunique) / np.log1p(len(series)))
        score = (
            0.45 * monotonicity
            + 0.35 * prognosability
            + 0.10 * (1.0 - regime_sensitivity)
            + 0.10 * continuity
        )

        rows.append(
            {
                "sensor": sensor,
                "std": float(series.std()),
                "nunique": nunique,
                "monotonicity": monotonicity,
                "prognosability": prognosability,
                "regime_sensitivity": regime_sensitivity,
                "continuity": continuity,
                "composite_score": score,
            }
        )

    scores = pd.DataFrame(rows).sort_values("composite_score", ascending=False).reset_index(drop=True)
    scores["rank"] = np.arange(1, len(scores) + 1)
    scores["bucket"] = "drop"
    scores.loc[scores["rank"] <= WORKING_SET_SIZE, "bucket"] = "working_set"
    scores.loc[(scores["rank"] > WORKING_SET_SIZE) & (scores["rank"] <= RESERVE_SET_SIZE), "bucket"] = "reserve"
    return scores


def build_summary(train_df: pd.DataFrame, test_df: pd.DataFrame, centers: pd.DataFrame, k_metrics: pd.DataFrame, scores: pd.DataFrame) -> dict[str, object]:
    working_set = scores.loc[scores["bucket"] == "working_set", "sensor"].tolist()
    reserve_set = scores.loc[scores["bucket"] == "reserve", "sensor"].tolist()
    dropped_set = scores.loc[scores["bucket"] == "drop", "sensor"].tolist()
    best_k_row = k_metrics.loc[k_metrics["silhouette"].idxmax()]

    return {
        "dataset": "FD002",
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_units": int(train_df["unit"].nunique()),
        "test_units": int(test_df["unit"].nunique()),
        "final_k": FINAL_K,
        "best_silhouette_k": int(best_k_row["k"]),
        "best_silhouette_value": float(best_k_row["silhouette"]),
        "working_set": working_set,
        "reserve_set": reserve_set,
        "dropped_set": dropped_set,
        "top_sensor": working_set[0],
        "top_score": float(scores.iloc[0]["composite_score"]),
        "cluster_centers": centers.round(4).to_dict(orient="records"),
    }


def plot_k_selection_metrics(k_metrics: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    sns.lineplot(data=k_metrics, x="k", y="inertia", marker="o", ax=axes[0], color="#b44f1d")
    axes[0].axvline(FINAL_K, color="#1d3557", linestyle="--", linewidth=1.2)
    axes[0].set_title("K-Means Inertia by k")
    axes[0].set_xlabel("k")
    axes[0].set_ylabel("Inertia")

    sns.lineplot(data=k_metrics, x="k", y="silhouette", marker="o", ax=axes[1], color="#2a9d8f")
    axes[1].axvline(FINAL_K, color="#1d3557", linestyle="--", linewidth=1.2)
    axes[1].set_title("Sample Silhouette by k")
    axes[1].set_xlabel("k")
    axes[1].set_ylabel("Silhouette")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fd002_k_selection_metrics.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_operating_regimes(train_df: pd.DataFrame, centers: pd.DataFrame) -> None:
    sample = train_df.sample(n=min(6000, len(train_df)), random_state=RANDOM_STATE)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    pairings = [("op1", "op2"), ("op1", "op3"), ("op2", "op3")]
    palette = sns.color_palette("tab10", n_colors=FINAL_K)

    for ax, (x_col, y_col) in zip(axes, pairings):
        sns.scatterplot(
            data=sample,
            x=x_col,
            y=y_col,
            hue="regime_id",
            palette=palette,
            s=12,
            linewidth=0,
            alpha=0.45,
            ax=ax,
            legend=ax is axes[0],
        )
        sns.scatterplot(
            data=centers,
            x=x_col,
            y=y_col,
            hue="regime_id",
            palette=palette,
            s=180,
            marker="X",
            edgecolor="black",
            linewidth=0.7,
            legend=False,
            ax=ax,
        )
        for _, row in centers.iterrows():
            ax.text(row[x_col], row[y_col], f"R{int(row['regime_id'])}", fontsize=8, weight="bold")
        ax.set_title(f"{x_col} vs {y_col}")

    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles=handles, labels=labels, title="regime_id", loc="best", fontsize=8, title_fontsize=9)
    fig.suptitle("FD002 Operating Regimes from op1-op2-op3", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fd002_operating_regimes.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_sensor_ranking(scores: pd.DataFrame) -> None:
    plot_df = scores.sort_values("composite_score", ascending=True)
    palette = {
        "working_set": "#2a9d8f",
        "reserve": "#e9c46a",
        "drop": "#b0b7c3",
    }

    fig, ax = plt.subplots(figsize=(9, 8))
    colors = [palette[bucket] for bucket in plot_df["bucket"]]
    ax.barh(plot_df["sensor"], plot_df["composite_score"], color=colors)
    ax.set_title("FD002 Sensor Ranking Heuristic")
    ax.set_xlabel("Composite score")
    ax.set_ylabel("Sensor")

    from matplotlib.patches import Patch

    ax.legend(
        handles=[
            Patch(color=palette["working_set"], label="Working set"),
            Patch(color=palette["reserve"], label="Reserve"),
            Patch(color=palette["drop"], label="Drop"),
        ],
        loc="lower right",
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fd002_sensor_ranking.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_sensor_metric_heatmap(scores: pd.DataFrame) -> None:
    heatmap_df = (
        scores.set_index("sensor")[["monotonicity", "prognosability", "regime_sensitivity", "continuity"]]
        .sort_values("monotonicity", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(heatmap_df, cmap="YlGnBu", annot=True, fmt=".2f", linewidths=0.5, ax=ax)
    ax.set_title("FD002 Sensor Metrics")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fd002_sensor_metric_heatmap.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_sensor_examples(train_df: pd.DataFrame, scores: pd.DataFrame) -> None:
    selected = scores.head(3)["sensor"].tolist()
    rejected = scores.tail(3)["sensor"].tolist()
    sensors = selected + rejected
    plot_df = train_df[["train_rul", *sensors]].copy()
    plot_df["rul_bin"] = pd.cut(plot_df["train_rul"], bins=30, include_lowest=True)

    fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharex=True)
    for ax, sensor in zip(axes.flat, sensors):
        binned = plot_df.groupby("rul_bin", observed=False)[sensor].mean().reset_index()
        binned["rul_mid"] = binned["rul_bin"].apply(lambda interval: interval.mid)
        ax.plot(binned["rul_mid"], binned[sensor], color="#1d3557")
        ax.set_title(sensor)
        ax.set_xlabel("Train RUL")
        ax.set_ylabel("Mean sensor value")
        ax.invert_xaxis()

    axes[0, 0].text(0.03, 0.92, "Selected", transform=axes[0, 0].transAxes, fontsize=10, weight="bold")
    axes[1, 0].text(0.03, 0.92, "Rejected", transform=axes[1, 0].transAxes, fontsize=10, weight="bold")
    fig.suptitle("Example Sensor Trends against Train RUL", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fd002_sensor_examples.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_outputs(train_df: pd.DataFrame, test_df: pd.DataFrame, centers: pd.DataFrame, k_metrics: pd.DataFrame, scores: pd.DataFrame, summary: dict[str, object]) -> None:
    train_df.loc[:, ["unit", "cycle", "regime_id"]].to_csv(PROCESSED_DIR / "fd002_train_regimes.csv", index=False)
    test_df.loc[:, ["unit", "cycle", "regime_id"]].to_csv(PROCESSED_DIR / "fd002_test_regimes.csv", index=False)
    centers.to_csv(TABLES_DIR / "fd002_cluster_centers.csv", index=False)
    k_metrics.to_csv(TABLES_DIR / "fd002_k_selection_metrics.csv", index=False)
    scores.to_csv(TABLES_DIR / "fd002_sensor_scores.csv", index=False)

    selected = scores.loc[:, ["sensor", "rank", "bucket", "composite_score"]].copy()
    selected.to_csv(TABLES_DIR / "fd002_sensor_selection_summary.csv", index=False)

    summary_path = TABLES_DIR / "fd002_analysis_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))


def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    for directory in [PROCESSED_DIR, FIGURES_DIR, TABLES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    train_df = add_train_rul(load_split("train"))
    test_df = load_split("test")

    train_df, test_df, centers, k_metrics = fit_regime_model(train_df, test_df)
    scores = compute_sensor_scores(train_df)
    summary = build_summary(train_df, test_df, centers, k_metrics, scores)

    plot_k_selection_metrics(k_metrics)
    plot_operating_regimes(train_df, centers)
    plot_sensor_ranking(scores)
    plot_sensor_metric_heatmap(scores)
    plot_sensor_examples(train_df, scores)
    save_outputs(train_df, test_df, centers, k_metrics, scores, summary)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
