from pathlib import Path
import pandas as pd


# =========================================
# 1. パス設定
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    ROOT_DIR
    / "data"
    / "processed"
)

PCA_DIR = (
    PROCESSED_DIR
    / "pca"
)

ANALYSIS_OUTPUT_DIR = (
    ROOT_DIR
    / "analysis_output"
)

CLUSTER_ANALYSIS_DIR = (
    ANALYSIS_OUTPUT_DIR
    / "cluster_analysis"
)

CLUSTER_METADATA_DIR = (
    ANALYSIS_OUTPUT_DIR
    / "cluster_metadata"
)


# =========================================
# 2. 確認するファイル
# =========================================

FILES = {
    "Multi-hot":
        PROCESSED_DIR
        / "multihot_1_0pct.csv",

    "Metadata":
        PROCESSED_DIR
        / "analysis_metadata.csv",

    "Cluster assignments":
        CLUSTER_ANALYSIS_DIR
        / "cluster_assignments_k6.csv",

    "Cluster feature profiles":
        CLUSTER_ANALYSIS_DIR
        / "cluster_feature_profiles_k6.csv",

    "Top distinctive features":
        CLUSTER_ANALYSIS_DIR
        / "top_distinctive_features_k6.csv",

    "Metadata response summary":
        CLUSTER_METADATA_DIR
        / "metadata_response_summary.csv",

    "Categorical metadata profiles":
        CLUSTER_METADATA_DIR
        / "categorical_metadata_profiles.csv",

    "Top distinctive metadata":
        CLUSTER_METADATA_DIR
        / "top_distinctive_metadata.csv",

    "WorkExp summary":
        CLUSTER_METADATA_DIR
        / "workexp_summary.csv",

    "PCA coordinates":
        PCA_DIR
        / "pca_coordinates.csv",

    "PCA cluster centers":
        PCA_DIR
        / "cluster_centers_pca.csv",

    "Weighted cluster centers":
        PCA_DIR
        / "cluster_centers_weighted.csv",
}


# =========================================
# 3. 各CSVを確認
# =========================================

print(
    "======================================"
)

print(
    "最終データセット用ファイル確認"
)

print(
    "======================================"
)

print()


for name, path in FILES.items():

    print(
        "======================================"
    )

    print(
        name
    )

    print(
        "======================================"
    )

    print(
        f"Path: {path}"
    )

    print()


    if not path.exists():

        print(
            "【ファイルが見つかりません】"
        )

        print()

        continue


    df = pd.read_csv(
        path
    )


    print(
        f"行数: {len(df):,}"
    )

    print(
        f"列数: {len(df.columns):,}"
    )

    print()


    print(
        "=== 列名 ==="
    )


    for index, column in enumerate(
        df.columns
    ):

        print(
            f"{index}: {column}"
        )


    print()


    print(
        "=== 先頭3行 ==="
    )


    # 131列あるMulti-hotなどを
    # 全部表示すると見づらいので、
    # 最大12列まで表示する
    preview_columns = list(
        df.columns[
            :12
        ]
    )


    print(
        df[
            preview_columns
        ]
        .head(3)
        .to_string(
            index=False
        )
    )


    if len(df.columns) > 12:

        print()

        print(
            f"※ 表示は先頭12列のみ "
            f"（全{len(df.columns)}列）"
        )


    print()
    print()


print(
    "======================================"
)

print(
    "確認完了"
)

print(
    "======================================"
)