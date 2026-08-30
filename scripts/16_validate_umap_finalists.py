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


MULTIHOT_PATH = ROOT_DIR / "data" / "processed" / "multihot_1_0pct.csv"
OUTPUT_DIR = ROOT_DIR / "analysis_output" / "umap_tuning" / "full_validation"
RANDOM_STATE = 42
EVALUATION_SAMPLE_SIZE = 3000
PLOT_SAMPLE_SIZE = 5000
EVALUATION_NEIGHBORS = (15, 50)
FINALISTS = [
    ("current", 15, 0.1),
    ("balanced_20_02", 20, 0.2),
    ("balanced_25_02", 25, 0.2),
    ("balanced_30_02", 30, 0.2),
    ("recommended", 30, 0.3),
]


def spread_metrics(embedding):
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
print("Loading all respondents...")
multihot_df = pd.read_csv(MULTIHOT_PATH).sort_values("analysis_id").reset_index(drop=True)
feature_columns = [column for column in multihot_df.columns if column != "analysis_id"]
features = multihot_df[feature_columns].astype(np.float32).copy()
category_columns = {}

for column in feature_columns:
    category_columns.setdefault(column.split("__", 1)[0], []).append(column)
for columns in category_columns.values():
    features[columns] *= 1 / math.sqrt(len(columns))

weighted_features = features.to_numpy(dtype=np.float32)
respondent_count = len(weighted_features)
rng = np.random.default_rng(RANDOM_STATE)
evaluation_indexes = rng.choice(
    respondent_count,
    size=min(EVALUATION_SAMPLE_SIZE, respondent_count),
    replace=False,
)
plot_indexes = rng.choice(
    respondent_count,
    size=min(PLOT_SAMPLE_SIZE, respondent_count),
    replace=False,
)

embeddings = {}
elapsed_times = {}
for label, n_neighbors, min_dist in FINALISTS:
    print(f"Running {label}: n_neighbors={n_neighbors}, min_dist={min_dist}")
    started_at = time.perf_counter()
    reducer = UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="euclidean",
        random_state=RANDOM_STATE,
        low_memory=True,
    )
    embeddings[label] = reducer.fit_transform(weighted_features).astype(np.float32)
    elapsed_times[label] = time.perf_counter() - started_at
    del reducer
    gc.collect()

print("Calculating original-space nearest neighbors...")
max_k = max(EVALUATION_NEIGHBORS)
original_model = NearestNeighbors(n_neighbors=max_k + 1, metric="euclidean")
original_model.fit(weighted_features)
original_neighbors_all = original_model.kneighbors(
    weighted_features[evaluation_indexes], return_distance=False
)[:, 1:]

rows = []
fig, axes = plt.subplots(1, len(FINALISTS), figsize=(18, 5.8))
evaluation_features = weighted_features[evaluation_indexes]

for axis, (label, n_neighbors, min_dist) in zip(axes, FINALISTS):
    embedding = embeddings[label]
    evaluation_embedding = embedding[evaluation_indexes]
    embedded_model = NearestNeighbors(n_neighbors=max_k + 1, metric="euclidean")
    embedded_model.fit(embedding)
    embedded_neighbors_all = embedded_model.kneighbors(
        evaluation_embedding, return_distance=False
    )[:, 1:]

    overlaps = {}
    for k in EVALUATION_NEIGHBORS:
        original_neighbors = original_neighbors_all[:, :k]
        embedded_neighbors = embedded_neighbors_all[:, :k]
        overlaps[k] = float(np.mean([
            len(set(original).intersection(reduced)) / k
            for original, reduced in zip(original_neighbors, embedded_neighbors)
        ]))

    trust_15 = trustworthiness(
        evaluation_features, evaluation_embedding, n_neighbors=15
    )
    trust_50 = trustworthiness(
        evaluation_features, evaluation_embedding, n_neighbors=50
    )
    spread = spread_metrics(embedding)
    rows.append({
        "label": label,
        "n_neighbors": n_neighbors,
        "min_dist": min_dist,
        "metric": "euclidean",
        "trustworthiness_15": trust_15,
        "trustworthiness_50": trust_50,
        "neighbor_overlap_15": overlaps[15],
        "neighbor_overlap_50": overlaps[50],
        **spread,
        "elapsed_seconds": elapsed_times[label],
        "respondents": respondent_count,
        "evaluation_sample_size": len(evaluation_indexes),
    })

    axis.scatter(
        embedding[plot_indexes, 0],
        embedding[plot_indexes, 1],
        s=5,
        alpha=0.25,
        color="#64748b",
        linewidths=0,
    )
    axis.set_title(
        f"{label}\nneighbors={n_neighbors}, min_dist={min_dist}\n"
        f"trust@15={trust_15:.3f}, overlap@15={overlaps[15]:.3f}"
    )
    axis.set_xticks([])
    axis.set_yticks([])

    pd.DataFrame({
        "analysis_id": multihot_df["analysis_id"],
        "umap1": embedding[:, 0],
        "umap2": embedding[:, 1],
    }).to_csv(
        OUTPUT_DIR / f"{label}_coordinates.csv",
        index=False,
        encoding="utf-8-sig",
    )

results_df = pd.DataFrame(rows)
results_df["quality_score"] = (
    results_df["trustworthiness_15"] * 0.35
    + results_df["trustworthiness_50"] * 0.25
    + results_df["neighbor_overlap_15"] * 0.25
    + results_df["neighbor_overlap_50"] * 0.15
)
results_df["quality_rank"] = results_df["quality_score"].rank(
    ascending=False, method="min"
).astype(int)
results_df = results_df.sort_values("quality_rank").reset_index(drop=True)
results_df.to_csv(
    OUTPUT_DIR / "full_validation_summary.csv", index=False, encoding="utf-8-sig"
)

fig.suptitle(f"UMAP finalists - all {respondent_count:,} respondents", fontsize=16)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(OUTPUT_DIR / "full_validation_comparison.png", dpi=180)
plt.close(fig)

print()
print(results_df.to_string(index=False))
print(f"Saved: {OUTPUT_DIR / 'full_validation_summary.csv'}")
print(f"Saved: {OUTPUT_DIR / 'full_validation_comparison.png'}")
