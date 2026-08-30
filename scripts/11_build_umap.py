from pathlib import Path
import math
import os


ROOT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT_DIR / ".cache"
os.environ.setdefault("NUMBA_CACHE_DIR", str(CACHE_DIR / "numba"))
os.environ.setdefault("TMP", str(CACHE_DIR / "tmp"))
os.environ.setdefault("TEMP", str(CACHE_DIR / "tmp"))
(CACHE_DIR / "numba").mkdir(parents=True, exist_ok=True)
(CACHE_DIR / "tmp").mkdir(parents=True, exist_ok=True)

import joblib
import matplotlib
import pandas as pd
from sklearn.manifold import trustworthiness
from umap import UMAP

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROCESSED_DIR = ROOT_DIR / "data" / "processed"
UMAP_DATA_DIR = PROCESSED_DIR / "umap"
UMAP_OUTPUT_DIR = ROOT_DIR / "analysis_output" / "umap_preview"
MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
UMAP_MODEL_PATH = UMAP_DATA_DIR / "umap_reducer.joblib"

N_NEIGHBORS = 15
MIN_DIST = 0.1
METRIC = "euclidean"
RANDOM_STATE = 42
PREVIEW_SAMPLE_SIZE = 3000
TRUSTWORTHINESS_SAMPLE_SIZE = 3000

UMAP_DATA_DIR.mkdir(parents=True, exist_ok=True)
UMAP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading multi-hot data...")
multihot_df = pd.read_csv(MULTIHOT_PATH).sort_values("analysis_id").reset_index(drop=True)

if "analysis_id" not in multihot_df.columns:
    raise ValueError("multihot data must include analysis_id.")
if multihot_df["analysis_id"].duplicated().any():
    raise ValueError("multihot analysis_id contains duplicates.")

feature_columns = [column for column in multihot_df.columns if column != "analysis_id"]
features = multihot_df[feature_columns].astype(float).copy()
category_columns = {}

for column in feature_columns:
    if "__" not in column:
        raise ValueError(f"Unexpected feature name: {column}")
    category_columns.setdefault(column.split("__", 1)[0], []).append(column)

category_weights = {
    category: 1 / math.sqrt(len(columns))
    for category, columns in category_columns.items()
}
weighted_features = features.copy()
for category, columns in category_columns.items():
    weighted_features[columns] *= category_weights[category]

print(f"Respondents: {len(multihot_df):,}")
print(f"Features: {len(feature_columns):,}")
print("Running UMAP...")

reducer = UMAP(
    n_components=2,
    n_neighbors=N_NEIGHBORS,
    min_dist=MIN_DIST,
    metric=METRIC,
    random_state=RANDOM_STATE,
)
embedding = reducer.fit_transform(weighted_features)
joblib.dump(reducer, UMAP_MODEL_PATH)

coordinates_df = pd.DataFrame({
    "analysis_id": multihot_df["analysis_id"],
    "umap1": embedding[:, 0],
    "umap2": embedding[:, 1],
})
coordinates_path = UMAP_DATA_DIR / "umap_coordinates.csv"
coordinates_df.to_csv(coordinates_path, index=False, encoding="utf-8-sig")

trust_sample_size = min(TRUSTWORTHINESS_SAMPLE_SIZE, len(coordinates_df))
trust_indexes = coordinates_df.sample(
    n=trust_sample_size,
    random_state=RANDOM_STATE,
).index.to_numpy()
trust = trustworthiness(
    weighted_features.iloc[trust_indexes],
    embedding[trust_indexes],
    n_neighbors=N_NEIGHBORS,
)

summary_df = pd.DataFrame([{
    "method": "UMAP",
    "n_components": 2,
    "n_neighbors": N_NEIGHBORS,
    "min_dist": MIN_DIST,
    "metric": METRIC,
    "random_state": RANDOM_STATE,
    "trustworthiness": trust,
    "trustworthiness_sample_size": trust_sample_size,
    "respondents": len(multihot_df),
    "features": len(feature_columns),
}])
summary_df.to_csv(UMAP_DATA_DIR / "umap_summary.csv", index=False, encoding="utf-8-sig")

preview_df = coordinates_df.sample(
    n=min(PREVIEW_SAMPLE_SIZE, len(coordinates_df)),
    random_state=RANDOM_STATE,
)
preview_df.to_csv(
    UMAP_OUTPUT_DIR / "umap_sampled_coordinates.csv",
    index=False,
    encoding="utf-8-sig",
)

fig, ax = plt.subplots(figsize=(12, 9))
ax.scatter(preview_df["umap1"], preview_df["umap2"], s=12, alpha=0.3, color="#64748b")
ax.set_title("UMAP Map - Sampled Respondents")
ax.set_xlabel("UMAP 1")
ax.set_ylabel("UMAP 2")
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(UMAP_OUTPUT_DIR / "umap_scatter_sampled.png", dpi=180)
plt.close(fig)

print(f"Trustworthiness: {trust:.4f}")
print(f"Saved: {UMAP_MODEL_PATH}")
print(f"Saved: {coordinates_path}")
print("UMAP data build completed.")
