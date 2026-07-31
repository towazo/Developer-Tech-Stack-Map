from pathlib import Path
import math

import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# =========================================
# 1. パス設定
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    ROOT_DIR / "data" / "processed"
)

OUTPUT_DIR = (
    ROOT_DIR / "analysis_output"
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)


# =========================================
# 2. 使用するMulti-hotデータ
# =========================================

DATASETS = {
    0.5: PROCESSED_DIR / "multihot_0_5pct.csv",
    1.0: PROCESSED_DIR / "multihot_1_0pct.csv",
    2.0: PROCESSED_DIR / "multihot_2_0pct.csv",
}


# =========================================
# 3. K-means設定
# =========================================

K_VALUES = range(3, 11)

RANDOM_STATE = 42

# KMeansを初期値を変えて何回試すか
N_INIT = 10

# シルエット係数は計算量が大きいため、
# 最大2000人をランダム抽出して評価する
SILHOUETTE_SAMPLE_SIZE = 2000


# =========================================
# 4. カテゴリを取得する関数
# =========================================

def get_category_columns(feature_columns):
    """
    language__Java
    database__PostgreSQL

    のような列名から、
    カテゴリごとの列をまとめる。
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
# 5. カテゴリ重み付け
# =========================================

def apply_category_weighting(
    X,
    category_columns
):
    """
    カテゴリ内の技術数を p としたとき

        1 / sqrt(p)

    を各技術へ掛ける。

    これによって、
    特徴数の多いカテゴリだけが
    距離計算へ強く影響することを抑える。
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

        weights[category] = {
            "feature_count": p,
            "weight": weight,
        }

    return weighted_X, weights


# =========================================
# 6. 開始
# =========================================

print(
    "======================================"
)

print(
    "K-means クラスタリング評価開始"
)

print(
    "======================================"
)

print()


evaluation_rows = []

cluster_size_rows = []

category_weight_rows = []


# =========================================
# 7. 各閾値を処理
# =========================================

for threshold, dataset_path in (
    DATASETS.items()
):

    print()
    print(
        "======================================"
    )

    print(
        f"利用率閾値: {threshold}%"
    )

    print(
        "======================================"
    )


    # -------------------------------------
    # Multi-hotデータ読み込み
    # -------------------------------------

    df = pd.read_csv(
        dataset_path
    )


    if "analysis_id" not in df.columns:

        raise ValueError(
            f"{dataset_path.name} に "
            "analysis_id がありません。"
        )


    feature_columns = [
        column
        for column in df.columns
        if column != "analysis_id"
    ]


    X = df[
        feature_columns
    ].copy()


    print(
        f"回答者数: {len(X):,}"
    )

    print(
        f"特徴数  : {len(feature_columns)}"
    )


    # -------------------------------------
    # カテゴリごとの列を取得
    # -------------------------------------

    category_columns = (
        get_category_columns(
            feature_columns
        )
    )


    print()

    print(
        "カテゴリ別特徴数:"
    )


    for category, columns in (
        category_columns.items()
    ):

        print(
            f"  {category:10}: "
            f"{len(columns)}"
        )


    # -------------------------------------
    # 重み付けデータを作る
    # -------------------------------------

    weighted_X, weights = (
        apply_category_weighting(
            X,
            category_columns
        )
    )


    # 重みを保存
    for category, information in (
        weights.items()
    ):

        category_weight_rows.append(
            {
                "threshold": threshold,
                "category": category,
                "feature_count":
                    information[
                        "feature_count"
                    ],
                "weight":
                    information[
                        "weight"
                    ],
            }
        )


    print()

    print(
        "カテゴリ重み:"
    )


    for category, information in (
        weights.items()
    ):

        print(
            f"  {category:10}: "
            f"1 / sqrt("
            f"{information['feature_count']}"
            f")"
            f" = "
            f"{information['weight']:.4f}"
        )


    # =====================================
    # 8. 重みなし / 重みありを比較
    # =====================================

    CONDITIONS = {
        "unweighted": X,
        "category_weighted": weighted_X,
    }


    for weighting_name, clustering_X in (
        CONDITIONS.items()
    ):

        print()
        print(
            "--------------------------------------"
        )

        print(
            f"条件: {weighting_name}"
        )

        print(
            "--------------------------------------"
        )


        # =================================
        # 9. K=3〜10
        # =================================

        for k in K_VALUES:

            print(
                f"K={k} ... ",
                end="",
                flush=True
            )


            # -----------------------------
            # K-means
            # -----------------------------

            model = KMeans(
                n_clusters=k,
                random_state=RANDOM_STATE,
                n_init=N_INIT
            )


            labels = model.fit_predict(
                clustering_X
            )


            # -----------------------------
            # シルエット係数
            # -----------------------------

            sample_size = min(
                SILHOUETTE_SAMPLE_SIZE,
                len(clustering_X)
            )


            silhouette = silhouette_score(
                clustering_X,
                labels,
                sample_size=sample_size,
                random_state=RANDOM_STATE
            )


            # -----------------------------
            # クラスタ人数
            # -----------------------------

            cluster_counts = (
                pd.Series(labels)
                .value_counts()
                .sort_index()
            )


            min_cluster_size = int(
                cluster_counts.min()
            )

            max_cluster_size = int(
                cluster_counts.max()
            )


            min_cluster_rate = (
                min_cluster_size
                / len(clustering_X)
                * 100
            )


            max_cluster_rate = (
                max_cluster_size
                / len(clustering_X)
                * 100
            )


            imbalance_ratio = (
                max_cluster_size
                / min_cluster_size
            )


            # -----------------------------
            # 評価結果
            # -----------------------------

            evaluation_rows.append(
                {
                    "threshold":
                        threshold,

                    "weighting":
                        weighting_name,

                    "k":
                        k,

                    "respondents":
                        len(clustering_X),

                    "features":
                        len(
                            feature_columns
                        ),

                    "inertia":
                        model.inertia_,

                    "silhouette_score":
                        silhouette,

                    "min_cluster_size":
                        min_cluster_size,

                    "max_cluster_size":
                        max_cluster_size,

                    "min_cluster_rate":
                        min_cluster_rate,

                    "max_cluster_rate":
                        max_cluster_rate,

                    "imbalance_ratio":
                        imbalance_ratio,
                }
            )


            # -----------------------------
            # 各クラスタ人数も保存
            # -----------------------------

            for cluster_id, count in (
                cluster_counts.items()
            ):

                cluster_size_rows.append(
                    {
                        "threshold":
                            threshold,

                        "weighting":
                            weighting_name,

                        "k":
                            k,

                        "cluster":
                            int(
                                cluster_id
                            ),

                        "count":
                            int(
                                count
                            ),

                        "rate":
                            (
                                count
                                / len(
                                    clustering_X
                                )
                                * 100
                            ),
                    }
                )


            print(
                f"silhouette="
                f"{silhouette:.4f}, "
                f"最小クラスタ="
                f"{min_cluster_size:,}人"
            )


# =========================================
# 10. 評価結果をCSV保存
# =========================================

evaluation_df = pd.DataFrame(
    evaluation_rows
)


evaluation_df = (
    evaluation_df
    .sort_values(
        [
            "threshold",
            "weighting",
            "k"
        ]
    )
)


evaluation_path = (
    OUTPUT_DIR
    / "clustering_evaluation.csv"
)


evaluation_df.to_csv(
    evaluation_path,
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 11. クラスタ人数を保存
# =========================================

cluster_size_df = pd.DataFrame(
    cluster_size_rows
)


cluster_size_path = (
    OUTPUT_DIR
    / "cluster_size_details.csv"
)


cluster_size_df.to_csv(
    cluster_size_path,
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 12. カテゴリ重みを保存
# =========================================

category_weight_df = pd.DataFrame(
    category_weight_rows
)


category_weight_path = (
    OUTPUT_DIR
    / "category_weights.csv"
)


category_weight_df.to_csv(
    category_weight_path,
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 13. 条件ごとのシルエット最大値を表示
# =========================================

print()
print(
    "======================================"
)

print(
    "各条件のシルエット係数 最大"
)

print(
    "======================================"
)


best_rows = (
    evaluation_df
    .loc[
        evaluation_df
        .groupby(
            [
                "threshold",
                "weighting"
            ]
        )[
            "silhouette_score"
        ]
        .idxmax()
    ]
)


for _, row in best_rows.iterrows():

    print()

    print(
        f"閾値       : "
        f"{row['threshold']}%"
    )

    print(
        f"重み       : "
        f"{row['weighting']}"
    )

    print(
        f"K          : "
        f"{int(row['k'])}"
    )

    print(
        f"silhouette : "
        f"{row['silhouette_score']:.4f}"
    )

    print(
        f"最小クラスタ: "
        f"{int(row['min_cluster_size']):,}人 "
        f"({row['min_cluster_rate']:.2f}%)"
    )


# =========================================
# 14. 完了
# =========================================

print()

print(
    "======================================"
)

print(
    "クラスタリング評価完了"
)

print(
    "======================================"
)

print()

print(
    "出力ファイル:"
)

print(
    evaluation_path
)

print(
    cluster_size_path
)

print(
    category_weight_path
)