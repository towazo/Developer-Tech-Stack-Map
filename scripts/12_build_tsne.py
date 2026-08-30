from pathlib import Path
import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE, trustworthiness


# =========================================
# 1. Paths
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CLUSTER_ANALYSIS_DIR = ROOT_DIR / "analysis_output" / "cluster_analysis"

TSNE_DATA_DIR = PROCESSED_DIR / "tsne"
TSNE_OUTPUT_DIR = ROOT_DIR / "analysis_output" / "tsne_preview"

TSNE_DATA_DIR.mkdir(parents=True, exist_ok=True)
TSNE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
CLUSTER_PATH = CLUSTER_ANALYSIS_DIR / "cluster_assignments_k6.csv"


# =========================================
# 2. Analysis settings
# =========================================

K = 6
PCA_PRE_COMPONENTS = 50
PERPLEXITY = 30
LEARNING_RATE = "auto"
MAX_ITER = 1000
RANDOM_STATE = 42
SAMPLE_PER_CLUSTER = 500
TRUSTWORTHINESS_SAMPLE_SIZE = 3000


# =========================================
# 3. Data loading
# =========================================

print("======================================")
print("t-SNE data build started")
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
# 5. PCA preprocessing
# =========================================
#
# t-SNE is intended for visualization. For higher-dimensional input,
# reducing noise with PCA first is a common and faster preprocessing step.
# =========================================

pca_components = min(PCA_PRE_COMPONENTS, len(feature_columns))

print("Running PCA preprocessing...")
print(f"components: {pca_components}")

pca = PCA(
    n_components=pca_components,
    svd_solver="full",
    random_state=RANDOM_STATE,
)

preprocessed_X = pca.fit_transform(weighted_X)
pca_explained_ratio = float(pca.explained_variance_ratio_.sum())

print(f"PCA explained variance: {pca_explained_ratio * 100:.2f}%")
print()


# =========================================
# 6. t-SNE
# =========================================

print("Running t-SNE...")
print(f"perplexity   : {PERPLEXITY}")
print(f"learning_rate: {LEARNING_RATE}")
print(f"max_iter     : {MAX_ITER}")
print(f"seed         : {RANDOM_STATE}")
print()

tsne = TSNE(
    n_components=2,
    perplexity=PERPLEXITY,
    learning_rate=LEARNING_RATE,
    max_iter=MAX_ITER,
    init="pca",
    random_state=RANDOM_STATE,
    method="barnes_hut",
)

embedding = tsne.fit_transform(preprocessed_X)

print("t-SNE completed")
print()


# =========================================
# 7. Save respondent coordinates
# =========================================

coordinates_df = pd.DataFrame(
    {
        "analysis_id": df["analysis_id"],
        "cluster": df["cluster"],
        "tsne1": embedding[:, 0],
        "tsne2": embedding[:, 1],
    }
)

coordinates_path = TSNE_DATA_DIR / "tsne_coordinates.csv"
coordinates_df.to_csv(coordinates_path, index=False, encoding="utf-8-sig")

print(f"Saved: {coordinates_path}")
print()


# =========================================
# 8. Cluster centers in the t-SNE map
# =========================================

center_rows = []

print("=== t-SNE cluster centers ===")

for cluster_id in range(K):
    mask = coordinates_df["cluster"] == cluster_id
    cluster_coordinates = coordinates_df.loc[mask, ["tsne1", "tsne2"]]
    count = int(mask.sum())
    rate = count / len(coordinates_df) * 100

    center_tsne1 = float(cluster_coordinates["tsne1"].mean())
    center_tsne2 = float(cluster_coordinates["tsne2"].mean())

    center_rows.append(
        {
            "cluster": cluster_id,
            "count": count,
            "rate": rate,
            "tsne1": center_tsne1,
            "tsne2": center_tsne2,
        }
    )

    print(f"Cluster {cluster_id}: ({center_tsne1:.4f}, {center_tsne2:.4f})")

centers_df = pd.DataFrame(center_rows)
centers_path = TSNE_DATA_DIR / "cluster_centers_tsne.csv"
centers_df.to_csv(centers_path, index=False, encoding="utf-8-sig")

print()
print(f"Saved: {centers_path}")
print()


# =========================================
# 9. Quality summary
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
    n_neighbors=PERPLEXITY,
)

summary_df = pd.DataFrame(
    [
        {
            "method": "t-SNE",
            "n_components": 2,
            "pca_pre_components": pca_components,
            "pca_pre_explained_variance_ratio": pca_explained_ratio,
            "perplexity": PERPLEXITY,
            "learning_rate": LEARNING_RATE,
            "max_iter": MAX_ITER,
            "random_state": RANDOM_STATE,
            "kl_divergence": float(tsne.kl_divergence_),
            "trustworthiness": trust,
            "trustworthiness_sample_size": trust_sample_size,
            "respondents": len(df),
            "features": len(feature_columns),
        }
    ]
)

summary_path = TSNE_DATA_DIR / "tsne_summary.csv"
summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

print(f"KL divergence: {tsne.kl_divergence_:.4f}")
print(f"Trustworthiness: {trust:.4f} ({trust_sample_size:,} sampled rows)")
print(f"Saved: {summary_path}")
print()


# =========================================
# 10. Preview plots
# =========================================

def plot_tsne_map(plot_df, output_path, point_size, alpha, title):
    fig, ax = plt.subplots(figsize=(12, 9))

    for cluster_id in sorted(plot_df["cluster"].unique()):
        cluster_plot_df = plot_df[plot_df["cluster"] == cluster_id]

        ax.scatter(
            cluster_plot_df["tsne1"],
            cluster_plot_df["tsne2"],
            s=point_size,
            alpha=alpha,
            label=f"Cluster {cluster_id}",
        )

    for _, row in centers_df.iterrows():
        ax.scatter(row["tsne1"], row["tsne2"], s=160, marker="X", c="black")

        ax.annotate(
            f"C{int(row['cluster'])}",
            (row["tsne1"], row["tsne2"]),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_title(title)
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.legend(title="Cluster", markerscale=1.5)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


print("Creating all-respondents preview...")
all_output_path = TSNE_OUTPUT_DIR / "tsne_scatter_all.png"
plot_tsne_map(
    coordinates_df,
    all_output_path,
    point_size=8,
    alpha=0.18,
    title="t-SNE Cluster Map - All Respondents",
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

sampled_csv_path = TSNE_OUTPUT_DIR / "tsne_sampled_coordinates.csv"
sampled_df.to_csv(sampled_csv_path, index=False, encoding="utf-8-sig")

print("Creating sampled preview...")
sampled_output_path = TSNE_OUTPUT_DIR / "tsne_scatter_sampled.png"
plot_tsne_map(
    sampled_df,
    sampled_output_path,
    point_size=16,
    alpha=0.35,
    title="t-SNE Cluster Map - Sampled Respondents",
)
print(f"Saved: {sampled_output_path}")
print(f"Saved: {sampled_csv_path}")
print()


# =========================================
# 11. Coordinate ranges
# =========================================

range_rows = []

print("=== Coordinate ranges by cluster ===")

for cluster_id in sorted(coordinates_df["cluster"].unique()):
    cluster_coordinates = coordinates_df[coordinates_df["cluster"] == cluster_id]

    tsne1_q05 = cluster_coordinates["tsne1"].quantile(0.05)
    tsne1_q95 = cluster_coordinates["tsne1"].quantile(0.95)
    tsne2_q05 = cluster_coordinates["tsne2"].quantile(0.05)
    tsne2_q95 = cluster_coordinates["tsne2"].quantile(0.95)

    range_rows.append(
        {
            "cluster": cluster_id,
            "tsne1_5_percentile": tsne1_q05,
            "tsne1_95_percentile": tsne1_q95,
            "tsne2_5_percentile": tsne2_q05,
            "tsne2_95_percentile": tsne2_q95,
        }
    )

    print(f"Cluster {cluster_id}")
    print(f"  t-SNE1: {tsne1_q05:.4f} to {tsne1_q95:.4f}")
    print(f"  t-SNE2: {tsne2_q05:.4f} to {tsne2_q95:.4f}")

range_df = pd.DataFrame(range_rows)
range_path = TSNE_OUTPUT_DIR / "cluster_coordinate_ranges.csv"
range_df.to_csv(range_path, index=False, encoding="utf-8-sig")

print()
print(f"Saved: {range_path}")
print()

print("======================================")
print("t-SNE data build completed")
print("======================================")
