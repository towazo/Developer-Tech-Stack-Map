from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from sklearn.decomposition import PCA


# =========================================
# 1. パス設定
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    ROOT_DIR
    / "data"
    / "processed"
)

CLUSTER_ANALYSIS_DIR = (
    ROOT_DIR
    / "analysis_output"
    / "cluster_analysis"
)

PCA_DATA_DIR = (
    PROCESSED_DIR
    / "pca"
)

PCA_OUTPUT_DIR = (
    ROOT_DIR
    / "analysis_output"
    / "pca"
)

PCA_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PCA_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


MULTIHOT_PATH = (
    PROCESSED_DIR
    / "multihot_1_0pct.csv"
)

CLUSTER_PATH = (
    CLUSTER_ANALYSIS_DIR
    / "cluster_assignments_k6.csv"
)


# =========================================
# 2. 最終分析条件
# =========================================

THRESHOLD = 1.0
K = 6


# =========================================
# 3. データ読み込み
# =========================================

print(
    "======================================"
)

print(
    "PCAデータ作成 開始"
)

print(
    "======================================"
)

print()

print(
    "Multi-hotデータを読み込んでいます..."
)

multihot_df = pd.read_csv(
    MULTIHOT_PATH
)


print(
    "クラスタ割り当てを読み込んでいます..."
)

cluster_df = pd.read_csv(
    CLUSTER_PATH
)

print()


# =========================================
# 4. データ確認
# =========================================

if "analysis_id" not in multihot_df.columns:

    raise ValueError(
        "Multi-hotデータに "
        "analysis_id がありません。"
    )


if "analysis_id" not in cluster_df.columns:

    raise ValueError(
        "クラスタデータに "
        "analysis_id がありません。"
    )


if "cluster" not in cluster_df.columns:

    raise ValueError(
        "クラスタデータに "
        "cluster がありません。"
    )


if multihot_df["analysis_id"].duplicated().any():

    raise ValueError(
        "Multi-hotデータのanalysis_idに"
        "重複があります。"
    )


if cluster_df["analysis_id"].duplicated().any():

    raise ValueError(
        "クラスタデータのanalysis_idに"
        "重複があります。"
    )


# =========================================
# 5. Multi-hotとクラスタを結合
# =========================================

df = pd.merge(
    multihot_df,
    cluster_df,
    on="analysis_id",
    how="inner",
    validate="one_to_one"
)


df = (
    df
    .sort_values(
        "analysis_id"
    )
    .reset_index(
        drop=True
    )
)


if len(df) != len(multihot_df):

    raise ValueError(
        "Multi-hotデータと"
        "クラスタ割り当ての人数が"
        "一致していません。"
    )


print(
    f"回答者数: {len(df):,}"
)


# =========================================
# 6. 技術特徴を取り出す
# =========================================

feature_columns = [
    column
    for column in df.columns
    if column not in [
        "analysis_id",
        "cluster",
    ]
]


X = (
    df[
        feature_columns
    ]
    .astype(float)
    .copy()
)


print(
    f"特徴数  : {len(feature_columns)}"
)

print()


# =========================================
# 7. カテゴリ別に特徴を整理
# =========================================

category_columns = {}


for column in feature_columns:

    if "__" not in column:

        raise ValueError(
            f"特徴名の形式が不正です: "
            f"{column}"
        )


    category = column.split(
        "__",
        1
    )[0]


    if category not in category_columns:

        category_columns[
            category
        ] = []


    category_columns[
        category
    ].append(
        column
    )


print(
    "=== カテゴリ別特徴数 ==="
)


for category, columns in (
    category_columns.items()
):

    print(
        f"{category:10}: "
        f"{len(columns)}"
    )


print()


# =========================================
# 8. カテゴリ重みを計算
# =========================================

category_weights = {}


for category, columns in (
    category_columns.items()
):

    p = len(columns)

    weight = (
        1 / math.sqrt(p)
    )

    category_weights[
        category
    ] = weight


print(
    "=== カテゴリ重み ==="
)


for category, weight in (
    category_weights.items()
):

    print(
        f"{category:10}: "
        f"{weight:.6f}"
    )


print()


# =========================================
# 9. Multi-hotデータへ重み付け
# =========================================

weighted_X = X.copy()


for category, columns in (
    category_columns.items()
):

    weight = (
        category_weights[
            category
        ]
    )


    weighted_X[
        columns
    ] = (
        weighted_X[
            columns
        ]
        * weight
    )


# =========================================
# 10. PCA
# =========================================

print(
    "PCAを実行しています..."
)


# 2次元表示が目的なので
# PC1 / PC2 の2成分を作る
#
# fullを指定して、
# 毎回同じ計算結果になるようにする

pca = PCA(
    n_components=2,
    svd_solver="full"
)


coordinates = (
    pca.fit_transform(
        weighted_X
    )
)


print(
    "PCA完了"
)

print()


# =========================================
# 11. 寄与率
# =========================================

pc1_ratio = (
    pca.explained_variance_ratio_[0]
    * 100
)

pc2_ratio = (
    pca.explained_variance_ratio_[1]
    * 100
)

cumulative_ratio = (
    pc1_ratio
    + pc2_ratio
)


print(
    "=== PCA 寄与率 ==="
)

print(
    f"PC1 : {pc1_ratio:.2f}%"
)

print(
    f"PC2 : {pc2_ratio:.2f}%"
)

print(
    f"累積: {cumulative_ratio:.2f}%"
)

print()


# =========================================
# 12. 回答者の2次元座標を保存
# =========================================

coordinates_df = pd.DataFrame(
    {
        "analysis_id":
            df["analysis_id"],

        "cluster":
            df["cluster"],

        "pc1":
            coordinates[:, 0],

        "pc2":
            coordinates[:, 1],
    }
)


coordinates_path = (
    PCA_DATA_DIR
    / "pca_coordinates.csv"
)


coordinates_df.to_csv(
    coordinates_path,
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 13. クラスタ中心を計算
# =========================================
#
# K-meansは重み付け済み131次元空間で
# 実行している。
#
# そのため各クラスタ所属者の
# 重み付きベクトル平均を取れば、
# K-meansのクラスタ中心に相当する。
#
# クラスタ番号も、
# これまでのCluster 0〜5と一致する。
# =========================================

cluster_center_rows = []

cluster_center_vectors = []


print(
    "=== クラスタ中心 ==="
)


for cluster_id in range(K):

    mask = (
        df["cluster"]
        == cluster_id
    )


    cluster_weighted_X = (
        weighted_X.loc[
            mask
        ]
    )


    center_vector = (
        cluster_weighted_X
        .mean(axis=0)
        .to_numpy()
    )


    # 131次元のクラスタ中心を
    # 同じ学習済みPCAで2次元化
    center_coordinate = (
        pca.transform(
            center_vector.reshape(
                1,
                -1
            )
        )[0]
    )


    count = int(
        mask.sum()
    )


    rate = (
        count
        / len(df)
        * 100
    )


    cluster_center_rows.append(
        {
            "cluster":
                cluster_id,

            "count":
                count,

            "rate":
                rate,

            "pc1":
                float(
                    center_coordinate[0]
                ),

            "pc2":
                float(
                    center_coordinate[1]
                ),
        }
    )


    cluster_center_vectors.append(
        {
            "cluster":
                cluster_id,

            "count":
                count,

            "rate":
                rate,

            "vector":
                center_vector.tolist(),

            "pc1":
                float(
                    center_coordinate[0]
                ),

            "pc2":
                float(
                    center_coordinate[1]
                ),
        }
    )


    print(
        f"Cluster {cluster_id}: "
        f"({center_coordinate[0]:.4f}, "
        f"{center_coordinate[1]:.4f})"
    )


print()


cluster_centers_df = pd.DataFrame(
    cluster_center_rows
)


cluster_centers_df.to_csv(
    PCA_DATA_DIR
    / "cluster_centers_pca.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 14. 131次元クラスタ中心もCSV保存
# =========================================

center_matrix_rows = []


for center in cluster_center_vectors:

    row = {
        "cluster":
            center["cluster"]
    }


    for feature, value in zip(
        feature_columns,
        center["vector"]
    ):

        row[
            feature
        ] = value


    center_matrix_rows.append(
        row
    )


center_matrix_df = pd.DataFrame(
    center_matrix_rows
)


center_matrix_df.to_csv(
    PCA_DATA_DIR
    / "cluster_centers_weighted.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 15. 技術定義を作成
# =========================================
#
# React側で
#
# 「Javaを選択したら何番目を1にするか」
#
# を判断できるようにする。
# =========================================

overall_usage = (
    X.mean(axis=0)
    * 100
)


feature_definitions = []


for index, feature in enumerate(
    feature_columns
):

    category, technology = (
        feature.split(
            "__",
            1
        )
    )


    feature_definitions.append(
        {
            "index":
                index,

            "feature":
                feature,

            "category":
                category,

            "technology":
                technology,

            "weight":
                float(
                    category_weights[
                        category
                    ]
                ),

            "overall_usage_rate":
                float(
                    overall_usage[
                        feature
                    ]
                ),
        }
    )


with open(
    PCA_DATA_DIR
    / "feature_definitions.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        feature_definitions,
        file,
        ensure_ascii=False,
        indent=2
    )


# =========================================
# 16. Web側でPCA.transformするための
#     モデル情報をJSON保存
# =========================================

model_data = {
    "version": 1,

    "threshold_percent":
        THRESHOLD,

    "k":
        K,

    "respondents":
        len(df),

    "feature_count":
        len(feature_columns),

    # 順番が非常に重要
    "feature_order":
        feature_columns,

    "category_weights":
        {
            category:
                float(weight)
            for category, weight
            in category_weights.items()
        },

    "pca": {
        # PCA.fit時の平均
        "mean":
            pca.mean_.tolist(),

        # PC1とPC2の軸
        "components":
            pca.components_.tolist(),

        "explained_variance_ratio":
            pca
            .explained_variance_ratio_
            .tolist(),
    },

    # 近いクラスタ判定は
    # PCA上ではなく、
    # この131次元中心との距離で行う
    "cluster_centers_weighted":
        cluster_center_vectors,
}


model_path = (
    PCA_DATA_DIR
    / "pca_model.json"
)


with open(
    model_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        model_data,
        file,
        ensure_ascii=False,
        indent=2
    )


# =========================================
# 17. PCAをWeb側で再現できるか確認
# =========================================
#
# sklearnのPCA.transformは基本的に
#
# (x - mean) @ components.T
#
# で計算できる。
#
# JSONへ保存した値だけで
# 同じ結果になるかチェックする。
# =========================================

test_count = min(
    100,
    len(weighted_X)
)


test_X = (
    weighted_X
    .iloc[
        :test_count
    ]
    .to_numpy()
)


manual_coordinates = (
    (
        test_X
        - pca.mean_
    )
    @ pca.components_.T
)


sklearn_coordinates = (
    pca.transform(
        test_X
    )
)


max_error = float(
    np.max(
        np.abs(
            manual_coordinates
            - sklearn_coordinates
        )
    )
)


print(
    "=== Web側PCA再現チェック ==="
)

print(
    "最大誤差:"
)

print(
    f"{max_error:.12f}"
)

print()


if max_error > 1e-10:

    raise ValueError(
        "PCAの手計算再現結果と"
        "scikit-learnの結果が"
        "一致しません。"
    )


# =========================================
# 18. 座標範囲
# =========================================

pc1_min = float(
    coordinates[:, 0].min()
)

pc1_max = float(
    coordinates[:, 0].max()
)

pc2_min = float(
    coordinates[:, 1].min()
)

pc2_max = float(
    coordinates[:, 1].max()
)


print(
    "=== PCA座標範囲 ==="
)

print(
    f"PC1: "
    f"{pc1_min:.4f} "
    f"〜 "
    f"{pc1_max:.4f}"
)

print(
    f"PC2: "
    f"{pc2_min:.4f} "
    f"〜 "
    f"{pc2_max:.4f}"
)

print()


# =========================================
# 19. PCA概要を保存
# =========================================

summary_df = pd.DataFrame(
    [
        {
            "respondents":
                len(df),

            "features":
                len(feature_columns),

            "threshold":
                THRESHOLD,

            "k":
                K,

            "pc1_explained_variance_percent":
                pc1_ratio,

            "pc2_explained_variance_percent":
                pc2_ratio,

            "pc1_pc2_cumulative_percent":
                cumulative_ratio,

            "pc1_min":
                pc1_min,

            "pc1_max":
                pc1_max,

            "pc2_min":
                pc2_min,

            "pc2_max":
                pc2_max,

            "web_transform_max_error":
                max_error,
        }
    ]
)


summary_df.to_csv(
    PCA_OUTPUT_DIR
    / "pca_summary.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 20. 完了
# =========================================

print(
    "======================================"
)

print(
    "PCAデータ作成 完了"
)

print(
    "======================================"
)

print()

print(
    "回答者座標:"
)

print(
    coordinates_path
)

print()

print(
    "PCAモデル:"
)

print(
    model_path
)

print()

print(
    "出力フォルダ:"
)

print(
    PCA_DATA_DIR
)