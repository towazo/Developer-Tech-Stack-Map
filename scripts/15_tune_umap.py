from pathlib import Path
import gc
import math
import os
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT_DIR / ".cache"
os.environ.setdefault("NUMBA_CACHE_DIR", str(CACHE_DIR / "numba"))
os.environ.setdefault("TMP", str(CACHE_DIR / "tmp"))
os.environ.setdefault("TEMP", str(CACHE_DIR / "tmp"))
(CACHE_DIR / "numba").mkdir(parents=True, exist_ok=True)
(CACHE_DIR / "tmp").mkdir(parents=True, exist_ok=True)

import matplotlib
import numpy as np
import pandas as pd
from sklearn.manifold import trustworthiness
from sklearn.neighbors import NearestNeighbors
from umap import UMAP

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
OUTPUT_DIR = ROOT_DIR / "analysis_output" / "umap_tuning"

RANDOM_STATE = 42
TUNING_SAMPLE_SIZE = 3000
EVALUATION_SAMPLE_SIZE = 1000
PLOT_SAMPLE_SIZE = 2000
EVALUATION_NEIGHBORS = (15, 50)
PARAMETER_CANDIDATES = [
    (15, 0.1),
    (15, 0.3),
    (15, 0.6),
    (30, 0.1),
    (30, 0.3),
    (30, 0.6),
    (50, 0.1),
    (50, 0.3),
    (50, 0.6),
    (100, 0.1),
    (100, 0.3),
    (100, 0.6),
]


def calculate_neighbor_overlap(original_neighbors, embedding, evaluation_indexes, k):
    model = NearestNeighbors(n_neighbors=k + 1, metric="euclidean")
    model.fit(embedding)
    embedded_neighbors = model.kneighbors(
        embedding[evaluation_indexes], return_distance=False
    )[:, 1:]

    overlaps = [
        len(set(original).intersection(embedded)) / k
        for original, embedded in zip(original_neighbors[k], embedded_neighbors)
    ]
    return float(np.mean(overlaps))


def calculate_spread_metrics(embedding):
    lower = np.quantile(embedding, 0.01, axis=0)
    upper = np.quantile(embedding, 0.99, axis=0)
    span = np.maximum(upper - lower, 1e-9)
    normalized = np.clip((embedding - lower) / span, 0, 1)
    histogram, _, _ = np.histogram2d(
        normalized[:, 0], normalized[:, 1], bins=20, range=((0, 1), (0, 1))
    )

    nearest_model = NearestNeighbors(n_neighbors=2, metric="euclidean")
    nearest_model.fit(normalized)
    nearest_distances = nearest_model.kneighbors(return_distance=True)[0][:, 1]

    return {
        "occupied_grid_rate": float(np.count_nonzero(histogram) / histogram.size),
        "nearest_distance_median": float(np.median(nearest_distances)),
        "nearest_distance_q10": float(np.quantile(nearest_distances, 0.1)),
    }


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading weighted multi-hot data...")
multihot_df = pd.read_csv(MULTIHOT_PATH).sort_values("analysis_id").reset_index(drop=True)
feature_columns = [column for column in multihot_df.columns if column != "analysis_id"]
features = multihot_df[feature_columns].astype(np.float32).copy()
category_columns = {}

for column in feature_columns:
    category_columns.setdefault(column.split("__", 1)[0], []).append(column)

for columns in category_columns.values():
    features[columns] *= 1 / math.sqrt(len(columns))

sample_size = min(TUNING_SAMPLE_SIZE, len(features))
sample_indexes = multihot_df.sample(
    n=sample_size, random_state=RANDOM_STATE
).index.to_numpy()
sample_features = features.iloc[sample_indexes].to_numpy(dtype=np.float32)
sample_ids = multihot_df.iloc[sample_indexes]["analysis_id"].to_numpy()

rng = np.random.default_rng(RANDOM_STATE)
evaluation_indexes = rng.choice(
    sample_size, size=min(EVALUATION_SAMPLE_SIZE, sample_size), replace=False
)
plot_indexes = rng.choice(
    sample_size, size=min(PLOT_SAMPLE_SIZE, sample_size), replace=False
)

max_k = max(EVALUATION_NEIGHBORS)
original_model = NearestNeighbors(n_neighbors=max_k + 1, metric="euclidean")
original_model.fit(sample_features)
all_original_neighbors = original_model.kneighbors(
    sample_features[evaluation_indexes], return_distance=False
)[:, 1:]
original_neighbors = {
    k: all_original_neighbors[:, :k]
    for k in EVALUATION_NEIGHBORS
}

fig, axes = plt.subplots(3, 4, figsize=(18, 13.5))
results = []

for candidate_index, (n_neighbors, min_dist) in enumerate(PARAMETER_CANDIDATES):
    print(f"[{candidate_index + 1:02d}/{len(PARAMETER_CANDIDATES)}] "
          f"n_neighbors={n_neighbors}, min_dist={min_dist}")
    started_at = time.perf_counter()
    reducer = UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="euclidean",
        random_state=RANDOM_STATE,
        low_memory=True,
    )
    embedding = reducer.fit_transform(sample_features)
    elapsed_seconds = time.perf_counter() - started_at

    evaluation_features = sample_features[evaluation_indexes]
    evaluation_embedding = embedding[evaluation_indexes]
    trust_15 = trustworthiness(
        evaluation_features, evaluation_embedding, n_neighbors=15
    )
    trust_50 = trustworthiness(
        evaluation_features, evaluation_embedding, n_neighbors=50
    )
    overlap_15 = calculate_neighbor_overlap(
        original_neighbors, embedding, evaluation_indexes, 15
    )
    overlap_50 = calculate_neighbor_overlap(
        original_neighbors, embedding, evaluation_indexes, 50
    )
    spread = calculate_spread_metrics(embedding)

    candidate_name = f"nn{n_neighbors}_md{str(min_dist).replace('.', 'p')}"
    results.append({
        "candidate": candidate_name,
        "n_neighbors": n_neighbors,
        "min_dist": min_dist,
        "metric": "euclidean",
        "trustworthiness_15": trust_15,
        "trustworthiness_50": trust_50,
        "neighbor_overlap_15": overlap_15,
        "neighbor_overlap_50": overlap_50,
        **spread,
        "elapsed_seconds": elapsed_seconds,
        "sample_size": sample_size,
        "evaluation_sample_size": len(evaluation_indexes),
    })
    axis = axes.flat[candidate_index]
    axis.scatter(
        embedding[plot_indexes, 0],
        embedding[plot_indexes, 1],
        s=5,
        alpha=0.28,
        color="#64748b",
        linewidths=0,
    )
    axis.set_title(
        f"neighbors={n_neighbors}, min_dist={min_dist}\n"
        f"trust@15={trust_15:.3f}, overlap@15={overlap_15:.3f}"
    )
    axis.set_xticks([])
    axis.set_yticks([])

    del reducer
    del embedding
    gc.collect()

results_df = pd.DataFrame(results)
results_df["quality_score"] = (
    results_df["trustworthiness_15"] * 0.35
    + results_df["trustworthiness_50"] * 0.25
    + results_df["neighbor_overlap_15"] * 0.25
    + results_df["neighbor_overlap_50"] * 0.15
)
results_df = results_df.sort_values("quality_score", ascending=False).reset_index(drop=True)
results_df.insert(0, "quality_rank", np.arange(1, len(results_df) + 1))
results_df.to_csv(OUTPUT_DIR / "umap_parameter_evaluation.csv", index=False, encoding="utf-8-sig")
fig.suptitle(
    f"UMAP parameter comparison (same {sample_size:,} respondents)",
    fontsize=16,
)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(OUTPUT_DIR / "umap_parameter_comparison.png", dpi=170)
plt.close(fig)

print()
print(results_df[[
    "quality_rank",
    "n_neighbors",
    "min_dist",
    "trustworthiness_15",
    "trustworthiness_50",
    "neighbor_overlap_15",
    "neighbor_overlap_50",
    "occupied_grid_rate",
    "quality_score",
]].to_string(index=False))
print(f"Saved: {OUTPUT_DIR / 'umap_parameter_evaluation.csv'}")
print(f"Saved: {OUTPUT_DIR / 'umap_parameter_comparison.png'}")
