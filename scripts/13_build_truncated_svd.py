from pathlib import Path
import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.manifold import trustworthiness


# =========================================
# 1. Paths
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CLUSTER_ANALYSIS_DIR = ROOT_DIR / "analysis_output" / "cluster_analysis"

SVD_DATA_DIR = PROCESSED_DIR / "truncated_svd"
SVD_OUTPUT_DIR = ROOT_DIR / "analysis_output" / "truncated_svd_preview"

SVD_DATA_DIR.mkdir(parents=True, exist_ok=True)
SVD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
CLUSTER_PATH = CLUSTER_ANALYSIS_DIR / "cluster_assignments_k6.csv"


# =========================================
# 2. Analysis settings
# =========================================

K = 6
N_COMPONENTS = 2
RANDOM_STATE = 42
SAMPLE_PER_CLUSTER = 500
TRUSTWORTHINESS_SAMPLE_SIZE = 3000


# =========================================
# 3. Data loading
# =========================================

print("======================================")
print("TruncatedSVD data build started")
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
# 5. TruncatedSVD
# =========================================

print("Running TruncatedSVD...")
print(f"components: {N_COMPONENTS}")
print(f"seed      : {RANDOM_STATE}")
print()

svd = TruncatedSVD(
    n_components=N_COMPONENTS,
    algorithm="randomized",
    random_state=RANDOM_STATE,
)

embedding = svd.fit_transform(weighted_X)
explained_ratio_1 = float(svd.explained_variance_ratio_[0])
explained_ratio_2 = float(svd.explained_variance_ratio_[1])
explained_ratio_total = float(svd.explained_variance_ratio_.sum())

print("TruncatedSVD completed")
print()
print("=== Explained variance ratio ===")
print(f"SVD1 : {explained_ratio_1 * 100:.2f}%")
print(f"SVD2 : {explained_ratio_2 * 100:.2f}%")
print(f"Total: {explained_ratio_total * 100:.2f}%")
print()


# =========================================
# 6. Save respondent coordinates
# =========================================

coordinates_df = pd.DataFrame(
    {
        "analysis_id": df["analysis_id"],
        "cluster": df["cluster"],
        "svd1": embedding[:, 0],
        "svd2": embedding[:, 1],
    }
)

coordinates_path = SVD_DATA_DIR / "truncated_svd_coordinates.csv"
coordinates_df.to_csv(coordinates_path, index=False, encoding="utf-8-sig")

print(f"Saved: {coordinates_path}")
print()


# =========================================
# 7. Cluster centers
# =========================================

center_rows = []

print("=== TruncatedSVD cluster centers ===")

for cluster_id in range(K):
    mask = df["cluster"] == cluster_id
    cluster_weighted_X = weighted_X.loc[mask]
    center_frame = cluster_weighted_X.mean(axis=0).to_frame().T
    center_coordinate = svd.transform(center_frame)[0]

    count = int(mask.sum())
    rate = count / len(df) * 100

    center_rows.append(
        {
            "cluster": cluster_id,
            "count": count,
            "rate": rate,
            "svd1": float(center_coordinate[0]),
            "svd2": float(center_coordinate[1]),
        }
    )

    print(f"Cluster {cluster_id}: ({center_coordinate[0]:.4f}, {center_coordinate[1]:.4f})")

centers_df = pd.DataFrame(center_rows)
centers_path = SVD_DATA_DIR / "cluster_centers_truncated_svd.csv"
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
    n_neighbors=15,
)

summary_df = pd.DataFrame(
    [
        {
            "method": "TruncatedSVD",
            "n_components": N_COMPONENTS,
            "algorithm": "randomized",
            "random_state": RANDOM_STATE,
            "explained_variance_ratio_1": explained_ratio_1,
            "explained_variance_ratio_2": explained_ratio_2,
            "explained_variance_ratio_total": explained_ratio_total,
            "trustworthiness": trust,
            "trustworthiness_sample_size": trust_sample_size,
            "respondents": len(df),
            "features": len(feature_columns),
        }
    ]
)

summary_path = SVD_DATA_DIR / "truncated_svd_summary.csv"
summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

print(f"Trustworthiness: {trust:.4f} ({trust_sample_size:,} sampled rows)")
print(f"Saved: {summary_path}")
print()


# =========================================
# 9. Preview plots
# =========================================

def plot_svd_map(plot_df, output_path, point_size, alpha, title):
    fig, ax = plt.subplots(figsize=(12, 9))

    for cluster_id in sorted(plot_df["cluster"].unique()):
        cluster_plot_df = plot_df[plot_df["cluster"] == cluster_id]

        ax.scatter(
            cluster_plot_df["svd1"],
            cluster_plot_df["svd2"],
            s=point_size,
            alpha=alpha,
            label=f"Cluster {cluster_id}",
        )

    for _, row in centers_df.iterrows():
        ax.scatter(row["svd1"], row["svd2"], s=160, marker="X", c="black")

        ax.annotate(
            f"C{int(row['cluster'])}",
            (row["svd1"], row["svd2"]),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_title(title)
    ax.set_xlabel(f"SVD 1 ({explained_ratio_1 * 100:.2f}%)")
    ax.set_ylabel(f"SVD 2 ({explained_ratio_2 * 100:.2f}%)")
    ax.legend(title="Cluster", markerscale=1.5)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


print("Creating all-respondents preview...")
all_output_path = SVD_OUTPUT_DIR / "truncated_svd_scatter_all.png"
plot_svd_map(
    coordinates_df,
    all_output_path,
    point_size=8,
    alpha=0.18,
    title="TruncatedSVD Cluster Map - All Respondents",
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

sampled_csv_path = SVD_OUTPUT_DIR / "truncated_svd_sampled_coordinates.csv"
sampled_df.to_csv(sampled_csv_path, index=False, encoding="utf-8-sig")

print("Creating sampled preview...")
sampled_output_path = SVD_OUTPUT_DIR / "truncated_svd_scatter_sampled.png"
plot_svd_map(
    sampled_df,
    sampled_output_path,
    point_size=16,
    alpha=0.35,
    title="TruncatedSVD Cluster Map - Sampled Respondents",
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

    svd1_q05 = cluster_coordinates["svd1"].quantile(0.05)
    svd1_q95 = cluster_coordinates["svd1"].quantile(0.95)
    svd2_q05 = cluster_coordinates["svd2"].quantile(0.05)
    svd2_q95 = cluster_coordinates["svd2"].quantile(0.95)

    range_rows.append(
        {
            "cluster": cluster_id,
            "svd1_5_percentile": svd1_q05,
            "svd1_95_percentile": svd1_q95,
            "svd2_5_percentile": svd2_q05,
            "svd2_95_percentile": svd2_q95,
        }
    )

    print(f"Cluster {cluster_id}")
    print(f"  SVD1: {svd1_q05:.4f} to {svd1_q95:.4f}")
    print(f"  SVD2: {svd2_q05:.4f} to {svd2_q95:.4f}")

range_df = pd.DataFrame(range_rows)
range_path = SVD_OUTPUT_DIR / "cluster_coordinate_ranges.csv"
range_df.to_csv(range_path, index=False, encoding="utf-8-sig")

print()
print(f"Saved: {range_path}")
print()

print("======================================")
print("TruncatedSVD data build completed")
print("======================================")
