from pathlib import Path
import math

import pandas as pd

from sklearn.cluster import KMeans


# =========================================
# 1. パス設定
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    ROOT_DIR / "data" / "processed"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "analysis_output"
    / "cluster_analysis"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================
# 2. 今回分析する条件
# =========================================

DATASET_PATH = (
    PROCESSED_DIR
    / "multihot_1_0pct.csv"
)

K_VALUES = [
    4,
    5,
    6,
]

RANDOM_STATE = 42
N_INIT = 10

# ターミナルへ表示する
# 特徴技術数
TOP_N = 10


# =========================================
# 3. カテゴリを取得する関数
# =========================================

def get_category_columns(
    feature_columns
):
    """
    例:

    language__Java
    database__PostgreSQL

    という列名を、

    language
    database

    ごとに分類する。
    """

    categories = {}

    for column in feature_columns:

        if "__" not in column:
            continue

        category = column.split(
            "__",
            1
        )[0]

        if category not in categories:
            categories[category] = []

        categories[category].append(
            column
        )

    return categories


# =========================================
# 4. カテゴリ重み付け
# =========================================

def apply_category_weighting(
    X,
    category_columns
):
    """
    各カテゴリの特徴数を p として、

        1 / sqrt(p)

    を各特徴へ掛ける。
    """

    weighted_X = X.copy()

    weights = {}

    for category, columns in (
        category_columns.items()
    ):

        p = len(columns)

        weight = (
            1 / math.sqrt(p)
        )

        weighted_X[
            columns
        ] = (
            weighted_X[columns]
            * weight
        )

        weights[category] = weight

    return weighted_X, weights


# =========================================
# 5. 技術名を分解する関数
# =========================================

def split_feature_name(
    feature_name
):
    """
    language__Java

    ↓

    category = language
    technology = Java
    """

    category, technology = (
        feature_name.split(
            "__",
            1
        )
    )

    return category, technology


# =========================================
# 6. データ読み込み
# =========================================

print(
    "======================================"
)

print(
    "クラスタ特徴分析 開始"
)

print(
    "======================================"
)

print()

print(
    "1%閾値のMulti-hotデータを"
    "読み込んでいます..."
)


df = pd.read_csv(
    DATASET_PATH
)


if "analysis_id" not in df.columns:

    raise ValueError(
        "analysis_id列が"
        "見つかりません。"
    )


feature_columns = [
    column
    for column in df.columns
    if column != "analysis_id"
]


X = df[
    feature_columns
].copy()


analysis_ids = df[
    "analysis_id"
].copy()


print(
    f"回答者数: {len(X):,}"
)

print(
    f"特徴数  : {len(feature_columns)}"
)

print()


# =========================================
# 7. カテゴリ重み付け
# =========================================

category_columns = (
    get_category_columns(
        feature_columns
    )
)


weighted_X, weights = (
    apply_category_weighting(
        X,
        category_columns
    )
)


print(
    "=== カテゴリ重み ==="
)


for category, weight in (
    weights.items()
):

    print(
        f"{category:10}: "
        f"{weight:.4f}"
    )


print()


# =========================================
# 8. 全体での技術利用率
# =========================================

overall_usage = (
    X.mean(axis=0)
    * 100
)


# =========================================
# 9. K=4 / 5 / 6 を分析
# =========================================

comparison_rows = []


for k in K_VALUES:

    print()

    print(
        "======================================"
    )

    print(
        f"K = {k}"
    )

    print(
        "======================================"
    )


    # -------------------------------------
    # K-means
    # -------------------------------------

    model = KMeans(
        n_clusters=k,
        random_state=RANDOM_STATE,
        n_init=N_INIT
    )


    labels = model.fit_predict(
        weighted_X
    )


    # -------------------------------------
    # クラスタ割り当てを保存
    # -------------------------------------

    assignment_df = pd.DataFrame(
        {
            "analysis_id":
                analysis_ids,

            "cluster":
                labels,
        }
    )


    assignment_df.to_csv(
        OUTPUT_DIR
        / f"cluster_assignments_k{k}.csv",
        index=False,
        encoding="utf-8-sig"
    )


    # -------------------------------------
    # クラスタ人数
    # -------------------------------------

    cluster_counts = (
        assignment_df[
            "cluster"
        ]
        .value_counts()
        .sort_index()
    )


    print()

    print(
        "=== クラスタ人数 ==="
    )


    for cluster_id, count in (
        cluster_counts.items()
    ):

        rate = (
            count
            / len(X)
            * 100
        )

        print(
            f"Cluster {cluster_id}: "
            f"{count:,}人 "
            f"({rate:.2f}%)"
        )


        comparison_rows.append(
            {
                "k": k,
                "cluster":
                    int(cluster_id),
                "count":
                    int(count),
                "rate":
                    rate,
            }
        )


    # -------------------------------------
    # 技術特徴の分析
    # -------------------------------------

    profile_rows = []

    top_feature_rows = []


    for cluster_id in range(k):

        cluster_mask = (
            labels == cluster_id
        )


        cluster_X = X.loc[
            cluster_mask
        ]


        cluster_size = len(
            cluster_X
        )


        # クラスタ内利用率
        cluster_usage = (
            cluster_X.mean(
                axis=0
            )
            * 100
        )


        # 全体との差
        difference = (
            cluster_usage
            - overall_usage
        )


        cluster_profile = []


        for feature in (
            feature_columns
        ):

            category, technology = (
                split_feature_name(
                    feature
                )
            )


            row = {
                "k":
                    k,

                "cluster":
                    cluster_id,

                "cluster_size":
                    cluster_size,

                "category":
                    category,

                "technology":
                    technology,

                "cluster_usage_rate":
                    float(
                        cluster_usage[
                            feature
                        ]
                    ),

                "overall_usage_rate":
                    float(
                        overall_usage[
                            feature
                        ]
                    ),

                "difference_point":
                    float(
                        difference[
                            feature
                        ]
                    ),
            }


            profile_rows.append(
                row
            )

            cluster_profile.append(
                row
            )


        # ---------------------------------
        # 特徴的な技術を抽出
        # ---------------------------------
        #
        # 「クラスタ内利用率」
        # ではなく、
        #
        # クラスタ内利用率
        # -
        # 全体利用率
        #
        # が大きい順
        # ---------------------------------

        cluster_profile_df = (
            pd.DataFrame(
                cluster_profile
            )
            .sort_values(
                "difference_point",
                ascending=False
            )
        )


        top_features = (
            cluster_profile_df
            .head(TOP_N)
            .copy()
        )


        top_features[
            "rank"
        ] = range(
            1,
            len(top_features) + 1
        )


        top_feature_rows.extend(
            top_features
            .to_dict(
                orient="records"
            )
        )


        # ---------------------------------
        # ターミナル表示
        # ---------------------------------

        print()

        print(
            f"--- Cluster {cluster_id} ---"
        )

        print(
            f"人数: "
            f"{cluster_size:,}人"
        )

        print()

        print(
            "特徴的な技術 Top10"
        )


        for rank, (_, row) in enumerate(
            top_features.iterrows(),
            start=1
        ):

            print(
                f"{rank:2}. "
                f"[{row['category']}] "
                f"{row['technology']}"
            )

            print(
                f"    クラスタ: "
                f"{row['cluster_usage_rate']:.1f}%"
                f" / "
                f"全体: "
                f"{row['overall_usage_rate']:.1f}%"
                f" / "
                f"差: "
                f"{row['difference_point']:+.1f}pt"
            )


    # =====================================
    # 10. 全技術プロファイル保存
    # =====================================

    profile_df = pd.DataFrame(
        profile_rows
    )


    profile_df = (
        profile_df
        .sort_values(
            [
                "cluster",
                "difference_point"
            ],
            ascending=[
                True,
                False
            ]
        )
    )


    profile_df.to_csv(
        OUTPUT_DIR
        / f"cluster_feature_profiles_k{k}.csv",
        index=False,
        encoding="utf-8-sig"
    )


    # =====================================
    # 11. Top特徴を保存
    # =====================================

    top_features_df = pd.DataFrame(
        top_feature_rows
    )


    top_features_df = (
        top_features_df
        .sort_values(
            [
                "cluster",
                "rank"
            ]
        )
    )


    top_features_df.to_csv(
        OUTPUT_DIR
        / f"top_distinctive_features_k{k}.csv",
        index=False,
        encoding="utf-8-sig"
    )


# =========================================
# 12. K比較用クラスタ人数を保存
# =========================================

comparison_df = pd.DataFrame(
    comparison_rows
)


comparison_df.to_csv(
    OUTPUT_DIR
    / "cluster_size_comparison_k4_k5_k6.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 13. 完了
# =========================================

print()

print(
    "======================================"
)

print(
    "クラスタ特徴分析 完了"
)

print(
    "======================================"
)

print()

print(
    "結果:"
)

print(
    OUTPUT_DIR
)