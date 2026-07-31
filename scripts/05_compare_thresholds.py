from pathlib import Path
import math

import numpy as np
import pandas as pd

from scipy.optimize import linear_sum_assignment

from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score


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
    / "threshold_comparison"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================
# 2. 比較条件
# =========================================

DATASETS = {
    0.5: PROCESSED_DIR / "multihot_0_5pct.csv",
    1.0: PROCESSED_DIR / "multihot_1_0pct.csv",
    2.0: PROCESSED_DIR / "multihot_2_0pct.csv",
}


# 1%を比較基準にする
REFERENCE_THRESHOLD = 1.0

K = 6

RANDOM_STATE = 42
N_INIT = 10

TOP_N = 10


# =========================================
# 3. カテゴリ取得
# =========================================

def get_category_columns(
    feature_columns
):

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

    weighted_X = X.copy()

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

    return weighted_X


# =========================================
# 5. K-means実行
# =========================================

def run_clustering(
    dataset_path
):

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


    category_columns = (
        get_category_columns(
            feature_columns
        )
    )


    weighted_X = (
        apply_category_weighting(
            X,
            category_columns
        )
    )


    model = KMeans(
        n_clusters=K,
        random_state=RANDOM_STATE,
        n_init=N_INIT
    )


    labels = model.fit_predict(
        weighted_X
    )


    return {
        "df": df,
        "X": X,
        "feature_columns":
            feature_columns,
        "labels": labels,
        "model": model,
    }


# =========================================
# 6. クラスタ番号を対応付ける
# =========================================

def align_clusters(
    reference_labels,
    target_labels
):
    """
    K-meansのクラスタ番号には意味がない。

    そこで、

    「同じ回答者が最も多く入っている」

    クラスタ同士を対応付ける。

    Hungarian Algorithmを使用。
    """

    contingency = np.zeros(
        (K, K),
        dtype=int
    )


    for reference_cluster in range(K):

        for target_cluster in range(K):

            contingency[
                reference_cluster,
                target_cluster
            ] = np.sum(
                (
                    reference_labels
                    == reference_cluster
                )
                &
                (
                    target_labels
                    == target_cluster
                )
            )


    # 最大一致を探したいが、
    # linear_sum_assignmentは
    # 最小値を探す関数なので
    # マイナスにする
    row_ind, col_ind = (
        linear_sum_assignment(
            -contingency
        )
    )


    mapping = {}


    for reference_cluster, target_cluster in zip(
        row_ind,
        col_ind
    ):

        mapping[
            target_cluster
        ] = reference_cluster


    aligned_labels = np.array(
        [
            mapping[label]
            for label in target_labels
        ]
    )


    return (
        aligned_labels,
        mapping,
        contingency
    )


# =========================================
# 7. 特徴的技術Top10
# =========================================

def calculate_top_features(
    X,
    labels,
    threshold
):

    overall_usage = (
        X.mean(axis=0)
        * 100
    )


    rows = []


    for cluster_id in range(K):

        mask = (
            labels == cluster_id
        )


        cluster_X = X.loc[
            mask
        ]


        cluster_usage = (
            cluster_X.mean(axis=0)
            * 100
        )


        difference = (
            cluster_usage
            - overall_usage
        )


        ranking = (
            difference
            .sort_values(
                ascending=False
            )
            .head(TOP_N)
        )


        for rank, (
            feature,
            difference_point
        ) in enumerate(
            ranking.items(),
            start=1
        ):

            category, technology = (
                feature.split(
                    "__",
                    1
                )
            )


            rows.append(
                {
                    "threshold":
                        threshold,

                    "cluster":
                        cluster_id,

                    "rank":
                        rank,

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
                            difference_point
                        ),
                }
            )


    return pd.DataFrame(
        rows
    )


# =========================================
# 8. 開始
# =========================================

print(
    "======================================"
)

print(
    "閾値ごとのクラスタ安定性比較"
)

print(
    "======================================"
)

print()


results = {}


# =========================================
# 9. 各閾値でK=6を実行
# =========================================

for threshold, path in (
    DATASETS.items()
):

    print(
        f"{threshold}% を分析中..."
    )


    result = (
        run_clustering(
            path
        )
    )


    results[
        threshold
    ] = result


    print(
        f"  回答者数: "
        f"{len(result['X']):,}"
    )

    print(
        f"  特徴数  : "
        f"{len(result['feature_columns'])}"
    )


print()


# =========================================
# 10. analysis_idの一致確認
# =========================================

reference_ids = (
    results[
        REFERENCE_THRESHOLD
    ]["df"]["analysis_id"]
    .to_numpy()
)


for threshold, result in (
    results.items()
):

    ids = (
        result["df"][
            "analysis_id"
        ]
        .to_numpy()
    )


    if not np.array_equal(
        reference_ids,
        ids
    ):

        raise ValueError(
            f"{threshold}% と "
            "1%でanalysis_idの順序が"
            "一致していません。"
        )


# =========================================
# 11. 1%を基準にクラスタ番号を揃える
# =========================================

reference_labels = (
    results[
        REFERENCE_THRESHOLD
    ]["labels"]
)


aligned_labels_dict = {
    REFERENCE_THRESHOLD:
        reference_labels.copy()
}


mapping_rows = []


for threshold, result in (
    results.items()
):

    if threshold == REFERENCE_THRESHOLD:
        continue


    aligned_labels, mapping, contingency = (
        align_clusters(
            reference_labels,
            result["labels"]
        )
    )


    aligned_labels_dict[
        threshold
    ] = aligned_labels


    for original_cluster, aligned_cluster in (
        mapping.items()
    ):

        mapping_rows.append(
            {
                "threshold":
                    threshold,

                "original_cluster":
                    original_cluster,

                "aligned_cluster":
                    aligned_cluster,
            }
        )


mapping_df = pd.DataFrame(
    mapping_rows
)


mapping_df.to_csv(
    OUTPUT_DIR
    / "cluster_label_mapping.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 12. ARIと一致率を計算
# =========================================

comparison_pairs = [
    (0.5, 1.0),
    (1.0, 2.0),
    (0.5, 2.0),
]


stability_rows = []


print(
    "=== クラスタリング一致度 ==="
)

print()


for threshold_a, threshold_b in (
    comparison_pairs
):

    labels_a = (
        results[
            threshold_a
        ]["labels"]
    )

    labels_b = (
        results[
            threshold_b
        ]["labels"]
    )


    # ARIはクラスタ番号が違っていても
    # 正しく比較できる
    ari = adjusted_rand_score(
        labels_a,
        labels_b
    )


    # こちらはクラスタ番号を
    # 1%基準へ対応付けした後の
    # 単純一致率
    aligned_a = (
        aligned_labels_dict[
            threshold_a
        ]
    )

    aligned_b = (
        aligned_labels_dict[
            threshold_b
        ]
    )


    agreement_rate = (
        np.mean(
            aligned_a
            == aligned_b
        )
        * 100
    )


    stability_rows.append(
        {
            "threshold_a":
                threshold_a,

            "threshold_b":
                threshold_b,

            "adjusted_rand_index":
                ari,

            "aligned_agreement_rate":
                agreement_rate,
        }
    )


    print(
        f"{threshold_a}% vs "
        f"{threshold_b}%"
    )

    print(
        f"  ARI              : "
        f"{ari:.4f}"
    )

    print(
        f"  回答者の一致率   : "
        f"{agreement_rate:.2f}%"
    )

    print()


stability_df = pd.DataFrame(
    stability_rows
)


stability_df.to_csv(
    OUTPUT_DIR
    / "threshold_stability_summary.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 13. クラスタ別の人数を比較
# =========================================

cluster_size_rows = []


print(
    "=== クラスタ別人数 ==="
)


for threshold in [
    0.5,
    1.0,
    2.0
]:

    aligned_labels = (
        aligned_labels_dict[
            threshold
        ]
    )


    print()

    print(
        f"--- {threshold}% ---"
    )


    for cluster_id in range(K):

        count = int(
            np.sum(
                aligned_labels
                == cluster_id
            )
        )


        rate = (
            count
            / len(
                aligned_labels
            )
            * 100
        )


        print(
            f"Cluster {cluster_id}: "
            f"{count:,}人 "
            f"({rate:.2f}%)"
        )


        cluster_size_rows.append(
            {
                "threshold":
                    threshold,

                "cluster":
                    cluster_id,

                "count":
                    count,

                "rate":
                    rate,
            }
        )


cluster_size_df = pd.DataFrame(
    cluster_size_rows
)


cluster_size_df.to_csv(
    OUTPUT_DIR
    / "threshold_cluster_sizes.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 14. 特徴的技術Top10を計算
# =========================================

top_feature_frames = []


for threshold in [
    0.5,
    1.0,
    2.0
]:

    X = (
        results[
            threshold
        ]["X"]
    )


    aligned_labels = (
        aligned_labels_dict[
            threshold
        ]
    )


    top_df = (
        calculate_top_features(
            X,
            aligned_labels,
            threshold
        )
    )


    top_feature_frames.append(
        top_df
    )


top_features_df = pd.concat(
    top_feature_frames,
    ignore_index=True
)


top_features_df.to_csv(
    OUTPUT_DIR
    / "threshold_top_features.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 15. Top10特徴の一致度
# =========================================

feature_overlap_rows = []


print()

print(
    "=== 1%との特徴技術Top10一致 ==="
)


reference_top = (
    top_features_df[
        top_features_df[
            "threshold"
        ]
        == REFERENCE_THRESHOLD
    ]
)


for threshold in [
    0.5,
    2.0
]:

    print()

    print(
        f"--- {threshold}% vs 1.0% ---"
    )


    target_top = (
        top_features_df[
            top_features_df[
                "threshold"
            ]
            == threshold
        ]
    )


    for cluster_id in range(K):

        reference_features = set(
            reference_top[
                reference_top[
                    "cluster"
                ]
                == cluster_id
            ]["technology"]
        )


        target_features = set(
            target_top[
                target_top[
                    "cluster"
                ]
                == cluster_id
            ]["technology"]
        )


        intersection = (
            reference_features
            & target_features
        )


        union = (
            reference_features
            | target_features
        )


        common_count = len(
            intersection
        )


        jaccard = (
            len(intersection)
            / len(union)
            if len(union) > 0
            else 0
        )


        print(
            f"Cluster {cluster_id}: "
            f"共通 {common_count}/10 "
            f"(Jaccard={jaccard:.3f})"
        )


        feature_overlap_rows.append(
            {
                "threshold":
                    threshold,

                "reference_threshold":
                    REFERENCE_THRESHOLD,

                "cluster":
                    cluster_id,

                "common_top10_features":
                    common_count,

                "jaccard":
                    jaccard,
            }
        )


feature_overlap_df = pd.DataFrame(
    feature_overlap_rows
)


feature_overlap_df.to_csv(
    OUTPUT_DIR
    / "top_feature_overlap.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 16. 回答者ごとのクラスタを保存
# =========================================

assignments_df = pd.DataFrame(
    {
        "analysis_id":
            reference_ids,

        "cluster_0_5pct":
            aligned_labels_dict[
                0.5
            ],

        "cluster_1_0pct":
            aligned_labels_dict[
                1.0
            ],

        "cluster_2_0pct":
            aligned_labels_dict[
                2.0
            ],
    }
)


assignments_df.to_csv(
    OUTPUT_DIR
    / "aligned_cluster_assignments.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 17. 完了
# =========================================

print()

print(
    "======================================"
)

print(
    "閾値比較 完了"
)

print(
    "======================================"
)

print()

print(
    "出力先:"
)

print(
    OUTPUT_DIR
)