from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# =========================================
# 1. パス設定
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PCA_DATA_DIR = (
    ROOT_DIR
    / "data"
    / "processed"
    / "pca"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "analysis_output"
    / "pca_preview"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


COORDINATES_PATH = (
    PCA_DATA_DIR
    / "pca_coordinates.csv"
)

CENTERS_PATH = (
    PCA_DATA_DIR
    / "cluster_centers_pca.csv"
)


# =========================================
# 2. 表示設定
# =========================================

# サンプリング版では
# 各クラスタ最大500人表示
SAMPLE_PER_CLUSTER = 500

RANDOM_STATE = 42


# =========================================
# 3. データ読み込み
# =========================================

print(
    "======================================"
)

print(
    "PCAマップ確認用グラフ作成"
)

print(
    "======================================"
)

print()


coordinates_df = pd.read_csv(
    COORDINATES_PATH
)

centers_df = pd.read_csv(
    CENTERS_PATH
)


required_coordinate_columns = {
    "analysis_id",
    "cluster",
    "pc1",
    "pc2",
}

required_center_columns = {
    "cluster",
    "pc1",
    "pc2",
}


if not required_coordinate_columns.issubset(
    coordinates_df.columns
):

    raise ValueError(
        "pca_coordinates.csv の"
        "必要な列が不足しています。"
    )


if not required_center_columns.issubset(
    centers_df.columns
):

    raise ValueError(
        "cluster_centers_pca.csv の"
        "必要な列が不足しています。"
    )


print(
    f"回答者数: "
    f"{len(coordinates_df):,}"
)

print(
    f"クラスタ数: "
    f"{coordinates_df['cluster'].nunique()}"
)

print()


# =========================================
# 4. クラスタごとの人数
# =========================================

print(
    "=== クラスタ人数 ==="
)


cluster_counts = (
    coordinates_df[
        "cluster"
    ]
    .value_counts()
    .sort_index()
)


for cluster_id, count in (
    cluster_counts.items()
):

    print(
        f"Cluster {cluster_id}: "
        f"{count:,}人"
    )


print()


# =========================================
# 5. 全15,239点を描画
# =========================================

print(
    "全回答者版を作成しています..."
)


fig, ax = plt.subplots(
    figsize=(12, 9)
)


for cluster_id in sorted(
    coordinates_df[
        "cluster"
    ].unique()
):

    cluster_df = (
        coordinates_df[
            coordinates_df[
                "cluster"
            ]
            == cluster_id
        ]
    )


    ax.scatter(
        cluster_df["pc1"],
        cluster_df["pc2"],
        s=8,
        alpha=0.18,
        label=f"Cluster {cluster_id}",
    )


# クラスタ中心
for _, row in (
    centers_df.iterrows()
):

    ax.scatter(
        row["pc1"],
        row["pc2"],
        s=140,
        marker="X",
    )

    ax.annotate(
        f"C{int(row['cluster'])}",
        (
            row["pc1"],
            row["pc2"]
        ),
        xytext=(6, 6),
        textcoords="offset points",
        fontsize=11,
        fontweight="bold",
    )


ax.set_title(
    "PCA Cluster Map - All Respondents"
)

ax.set_xlabel(
    "PC1 (8.57%)"
)

ax.set_ylabel(
    "PC2 (6.15%)"
)

ax.legend(
    title="Cluster",
    markerscale=2,
)

ax.grid(
    alpha=0.2
)

fig.tight_layout()


all_output_path = (
    OUTPUT_DIR
    / "pca_scatter_all.png"
)


fig.savefig(
    all_output_path,
    dpi=180
)

plt.close(fig)


print(
    f"保存: {all_output_path}"
)


# =========================================
# 6. クラスタごとにサンプリング
# =========================================

sampled_frames = []


for cluster_id in sorted(
    coordinates_df[
        "cluster"
    ].unique()
):

    cluster_df = (
        coordinates_df[
            coordinates_df[
                "cluster"
            ]
            == cluster_id
        ]
    )


    sample_size = min(
        SAMPLE_PER_CLUSTER,
        len(cluster_df)
    )


    sampled_cluster = (
        cluster_df.sample(
            n=sample_size,
            random_state=RANDOM_STATE
            + int(cluster_id)
        )
    )


    sampled_frames.append(
        sampled_cluster
    )


sampled_df = pd.concat(
    sampled_frames,
    ignore_index=True
)


print()

print(
    f"サンプリング版: "
    f"{len(sampled_df):,}点"
)


# =========================================
# 7. サンプリング版を描画
# =========================================

print(
    "サンプリング版を作成しています..."
)


fig, ax = plt.subplots(
    figsize=(12, 9)
)


for cluster_id in sorted(
    sampled_df[
        "cluster"
    ].unique()
):

    cluster_df = (
        sampled_df[
            sampled_df[
                "cluster"
            ]
            == cluster_id
        ]
    )


    ax.scatter(
        cluster_df["pc1"],
        cluster_df["pc2"],
        s=16,
        alpha=0.35,
        label=f"Cluster {cluster_id}",
    )


# クラスタ中心
for _, row in (
    centers_df.iterrows()
):

    ax.scatter(
        row["pc1"],
        row["pc2"],
        s=160,
        marker="X",
    )

    ax.annotate(
        f"C{int(row['cluster'])}",
        (
            row["pc1"],
            row["pc2"]
        ),
        xytext=(7, 7),
        textcoords="offset points",
        fontsize=11,
        fontweight="bold",
    )


ax.set_title(
    "PCA Cluster Map - Sampled Respondents"
)

ax.set_xlabel(
    "PC1 (8.57%)"
)

ax.set_ylabel(
    "PC2 (6.15%)"
)

ax.legend(
    title="Cluster",
    markerscale=1.5,
)

ax.grid(
    alpha=0.2
)

fig.tight_layout()


sampled_output_path = (
    OUTPUT_DIR
    / "pca_scatter_sampled.png"
)


fig.savefig(
    sampled_output_path,
    dpi=180
)

plt.close(fig)


print(
    f"保存: {sampled_output_path}"
)


# =========================================
# 8. サンプリングデータも保存
# =========================================

sampled_csv_path = (
    OUTPUT_DIR
    / "pca_sampled_coordinates.csv"
)


sampled_df.to_csv(
    sampled_csv_path,
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 9. 各クラスタの座標範囲を確認
# =========================================

spread_rows = []


print()

print(
    "=== クラスタごとの座標範囲 ==="
)


for cluster_id in sorted(
    coordinates_df[
        "cluster"
    ].unique()
):

    cluster_df = (
        coordinates_df[
            coordinates_df[
                "cluster"
            ]
            == cluster_id
        ]
    )


    pc1_q05 = (
        cluster_df["pc1"]
        .quantile(0.05)
    )

    pc1_q95 = (
        cluster_df["pc1"]
        .quantile(0.95)
    )

    pc2_q05 = (
        cluster_df["pc2"]
        .quantile(0.05)
    )

    pc2_q95 = (
        cluster_df["pc2"]
        .quantile(0.95)
    )


    spread_rows.append(
        {
            "cluster":
                cluster_id,

            "pc1_5_percentile":
                pc1_q05,

            "pc1_95_percentile":
                pc1_q95,

            "pc2_5_percentile":
                pc2_q05,

            "pc2_95_percentile":
                pc2_q95,
        }
    )


    print(
        f"Cluster {cluster_id}"
    )

    print(
        f"  PC1: "
        f"{pc1_q05:.4f}"
        f" ～ "
        f"{pc1_q95:.4f}"
    )

    print(
        f"  PC2: "
        f"{pc2_q05:.4f}"
        f" ～ "
        f"{pc2_q95:.4f}"
    )


spread_df = pd.DataFrame(
    spread_rows
)


spread_df.to_csv(
    OUTPUT_DIR
    / "cluster_coordinate_ranges.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 10. 完了
# =========================================

print()

print(
    "======================================"
)

print(
    "PCAマップ作成 完了"
)

print(
    "======================================"
)

print()

print(
    "確認する画像:"
)

print(
    all_output_path
)

print(
    sampled_output_path
)