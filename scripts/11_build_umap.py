from pathlib import Path
import math
import os


ROOT_DIR = Path(__file__).resolve().parents[1]

CACHE_DIR = ROOT_DIR / ".cache"
NUMBA_CACHE_DIR = CACHE_DIR / "numba"
TMP_DIR = CACHE_DIR / "tmp"

NUMBA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("NUMBA_CACHE_DIR", str(NUMBA_CACHE_DIR))
os.environ.setdefault("TMP", str(TMP_DIR))
os.environ.setdefault("TEMP", str(TMP_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import joblib
import pandas as pd
from sklearn.manifold import trustworthiness
from umap import UMAP


# =========================================
# 1. Paths and runtime settings
# =========================================

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CLUSTER_ANALYSIS_DIR = ROOT_DIR / "analysis_output" / "cluster_analysis"

UMAP_DATA_DIR = PROCESSED_DIR / "umap"
UMAP_OUTPUT_DIR = ROOT_DIR / "analysis_output" / "umap_preview"

UMAP_DATA_DIR.mkdir(parents=True, exist_ok=True)
UMAP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
CLUSTER_PATH = CLUSTER_ANALYSIS_DIR / "cluster_assignments_k6.csv"
UMAP_MODEL_PATH = UMAP_DATA_DIR / "umap_reducer.joblib"


# =========================================
# 2. Analysis settings
# =========================================

K = 6
N_NEIGHBORS = 15
MIN_DIST = 0.1
METRIC = "euclidean"
RANDOM_STATE = 42
SAMPLE_PER_CLUSTER = 500
TRUSTWORTHINESS_SAMPLE_SIZE = 3000


# =========================================
# 3. Data loading
# =========================================

print("======================================")
print("UMAP data build started")
print("======================================")
print()

print("Loading multi-hot data...")
multihot_df = pd.read_csv(MULTIHOT_PATH)

print("Loading cluster assignments...")
cluster_df = pd.read_csv(CLUSTER_PATH)
print()

required_multihot_columns = {"analysis_id"}
required_cluster_columns = {"analysis_id", "cluster"}

if not required_multihot_columns.issubset(multihot_df.columns):
    raise ValueError("multihot data must include analysis_id.")

if not required_cluster_columns.issubset(cluster_df.columns):
    raise ValueError("cluster assignments must include analysis_id and cluster.")

if multihot_df["analysis_id"].duplicated().any():
    raise ValueError("multihot analysis_id contains duplicates.")

if cluster_df["analysis_id"].duplicated().any():
    raise ValueError("cluster assignment analysis_id contains duplicates.")

df = pd.merge(
    multihot_df,
    cluster_df,
    on="analysis_id",
    how="inner",
    validate="one_to_one",
)

df = df.sort_values("analysis_id").reset_index(drop=True)

if len(df) != len(multihot_df):
    raise ValueError("multihot rows and cluster assignment rows do not match.")

feature_columns = [
    column
    for column in df.columns
    if column not in ["analysis_id", "cluster"]
]

X = df[feature_columns].astype(float).copy()

print(f"Respondents: {len(df):,}")
print(f"Features   : {len(feature_columns):,}")
print()


# =========================================
# 4. Category weighting
# =========================================

category_columns = {}

for column in feature_columns:
    if "__" not in column:
        raise ValueError(f"Unexpected feature name format: {column}")

    category = column.split("__", 1)[0]
    category_columns.setdefault(category, []).append(column)

category_weights = {
    category: 1 / math.sqrt(len(columns))
    for category, columns in category_columns.items()
}

weighted_X = X.copy()

for category, columns in category_columns.items():
    weighted_X[columns] = weighted_X[columns] * category_weights[category]

print("=== Category weights ===")
for category, weight in category_weights.items():
    print(f"{category:10}: {weight:.6f}")
print()


# =========================================
# 5. UMAP
# =========================================

print("Running UMAP...")
print(f"n_neighbors: {N_NEIGHBORS}")
print(f"min_dist   : {MIN_DIST}")
print(f"metric     : {METRIC}")
print(f"seed       : {RANDOM_STATE}")
print()

reducer = UMAP(
    n_components=2,
    n_neighbors=N_NEIGHBORS,
    min_dist=MIN_DIST,
    metric=METRIC,
    random_state=RANDOM_STATE,
)

embedding = reducer.fit_transform(weighted_X)

print("UMAP completed")
print()

joblib.dump(reducer, UMAP_MODEL_PATH)
print(f"Saved: {UMAP_MODEL_PATH}")
print()


# =========================================
# 6. Save respondent coordinates
# =========================================

coordinates_df = pd.DataFrame(
    {
        "analysis_id": df["analysis_id"],
        "cluster": df["cluster"],
        "umap1": embedding[:, 0],
        "umap2": embedding[:, 1],
    }
)

coordinates_path = UMAP_DATA_DIR / "umap_coordinates.csv"
coordinates_df.to_csv(coordinates_path, index=False, encoding="utf-8-sig")

print(f"Saved: {coordinates_path}")
print()


# =========================================
# 7. Cluster centers in the UMAP map
# =========================================

center_rows = []

print("=== UMAP cluster centers ===")

for cluster_id in range(K):
    mask = coordinates_df["cluster"] == cluster_id
    cluster_coordinates = coordinates_df.loc[mask, ["umap1", "umap2"]]
    count = int(mask.sum())
    rate = count / len(coordinates_df) * 100

    center_umap1 = float(cluster_coordinates["umap1"].mean())
    center_umap2 = float(cluster_coordinates["umap2"].mean())

    center_rows.append(
        {
            "cluster": cluster_id,
            "count": count,
            "rate": rate,
            "umap1": center_umap1,
            "umap2": center_umap2,
        }
    )

    print(f"Cluster {cluster_id}: ({center_umap1:.4f}, {center_umap2:.4f})")

centers_df = pd.DataFrame(center_rows)
centers_path = UMAP_DATA_DIR / "cluster_centers_umap.csv"
centers_df.to_csv(centers_path, index=False, encoding="utf-8-sig")

print()
print(f"Saved: {centers_path}")
print()


# =========================================
# 8. Quality summary
# =========================================

print("Calculating trustworthiness...")

trust_sample_size = min(TRUSTWORTHINESS_SAMPLE_SIZE, len(coordinates_df))
trust_sample_df = coordinates_df.sample(
    n=trust_sample_size,
    random_state=RANDOM_STATE,
)
trust_sample_index = trust_sample_df.index.to_numpy()

trust = trustworthiness(
    weighted_X.iloc[trust_sample_index],
    embedding[trust_sample_index],
    n_neighbors=N_NEIGHBORS,
)

summary_df = pd.DataFrame(
    [
        {
            "method": "UMAP",
            "n_components": 2,
            "n_neighbors": N_NEIGHBORS,
            "min_dist": MIN_DIST,
            "metric": METRIC,
            "random_state": RANDOM_STATE,
            "trustworthiness": trust,
            "trustworthiness_sample_size": trust_sample_size,
            "respondents": len(df),
            "features": len(feature_columns),
        }
    ]
)

summary_path = UMAP_DATA_DIR / "umap_summary.csv"
summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

print(f"Trustworthiness: {trust:.4f} ({trust_sample_size:,} sampled rows)")
print(f"Saved: {summary_path}")
print()


# =========================================
# 9. Preview plots
# =========================================

def plot_umap_map(plot_df, output_path, point_size, alpha, title):
    fig, ax = plt.subplots(figsize=(12, 9))

    for cluster_id in sorted(plot_df["cluster"].unique()):
        cluster_plot_df = plot_df[plot_df["cluster"] == cluster_id]

        ax.scatter(
            cluster_plot_df["umap1"],
            cluster_plot_df["umap2"],
            s=point_size,
            alpha=alpha,
            label=f"Cluster {cluster_id}",
        )

    for _, row in centers_df.iterrows():
        ax.scatter(row["umap1"], row["umap2"], s=160, marker="X", c="black")

        ax.annotate(
            f"C{int(row['cluster'])}",
            (row["umap1"], row["umap2"]),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_title(title)
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.legend(title="Cluster", markerscale=1.5)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


print("Creating all-respondents preview...")
all_output_path = UMAP_OUTPUT_DIR / "umap_scatter_all.png"
plot_umap_map(
    coordinates_df,
    all_output_path,
    point_size=8,
    alpha=0.18,
    title="UMAP Cluster Map - All Respondents",
)
print(f"Saved: {all_output_path}")

sampled_frames = []

for cluster_id in sorted(coordinates_df["cluster"].unique()):
    cluster_coordinates = coordinates_df[coordinates_df["cluster"] == cluster_id]
    sample_size = min(SAMPLE_PER_CLUSTER, len(cluster_coordinates))

    sampled_frames.append(
        cluster_coordinates.sample(
            n=sample_size,
            random_state=RANDOM_STATE + int(cluster_id),
        )
    )

sampled_df = pd.concat(sampled_frames, ignore_index=True)

sampled_csv_path = UMAP_OUTPUT_DIR / "umap_sampled_coordinates.csv"
sampled_df.to_csv(sampled_csv_path, index=False, encoding="utf-8-sig")

print("Creating sampled preview...")
sampled_output_path = UMAP_OUTPUT_DIR / "umap_scatter_sampled.png"
plot_umap_map(
    sampled_df,
    sampled_output_path,
    point_size=16,
    alpha=0.35,
    title="UMAP Cluster Map - Sampled Respondents",
)
print(f"Saved: {sampled_output_path}")
print(f"Saved: {sampled_csv_path}")
print()


# =========================================
# 10. Coordinate ranges
# =========================================

range_rows = []

print("=== Coordinate ranges by cluster ===")

for cluster_id in sorted(coordinates_df["cluster"].unique()):
    cluster_coordinates = coordinates_df[coordinates_df["cluster"] == cluster_id]

    umap1_q05 = cluster_coordinates["umap1"].quantile(0.05)
    umap1_q95 = cluster_coordinates["umap1"].quantile(0.95)
    umap2_q05 = cluster_coordinates["umap2"].quantile(0.05)
    umap2_q95 = cluster_coordinates["umap2"].quantile(0.95)

    range_rows.append(
        {
            "cluster": cluster_id,
            "umap1_5_percentile": umap1_q05,
            "umap1_95_percentile": umap1_q95,
            "umap2_5_percentile": umap2_q05,
            "umap2_95_percentile": umap2_q95,
        }
    )

    print(f"Cluster {cluster_id}")
    print(f"  UMAP1: {umap1_q05:.4f} to {umap1_q95:.4f}")
    print(f"  UMAP2: {umap2_q05:.4f} to {umap2_q95:.4f}")

range_df = pd.DataFrame(range_rows)
range_path = UMAP_OUTPUT_DIR / "cluster_coordinate_ranges.csv"
range_df.to_csv(range_path, index=False, encoding="utf-8-sig")

print()
print(f"Saved: {range_path}")
print()

print("======================================")
print("UMAP data build completed")
print("======================================")
