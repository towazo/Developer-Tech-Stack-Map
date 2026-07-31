from pathlib import Path
import json
import math

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

FRONTEND_DATA_DIR = (
    ROOT_DIR
    / "public"
    / "data"
)

FRONTEND_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================
# 2. 入力ファイル
# =========================================

MULTIHOT_PATH = (
    PROCESSED_DIR
    / "multihot_1_0pct.csv"
)

CLUSTER_ASSIGNMENTS_PATH = (
    CLUSTER_ANALYSIS_DIR
    / "cluster_assignments_k6.csv"
)

TOP_FEATURES_PATH = (
    CLUSTER_ANALYSIS_DIR
    / "top_distinctive_features_k6.csv"
)

TOP_METADATA_PATH = (
    CLUSTER_METADATA_DIR
    / "top_distinctive_metadata.csv"
)

WORKEXP_PATH = (
    CLUSTER_METADATA_DIR
    / "workexp_summary.csv"
)

PCA_COORDINATES_PATH = (
    PCA_DIR
    / "pca_coordinates.csv"
)

PCA_CENTERS_PATH = (
    PCA_DIR
    / "cluster_centers_pca.csv"
)

FEATURE_DEFINITIONS_PATH = (
    PCA_DIR
    / "feature_definitions.json"
)

PCA_MODEL_PATH = (
    PCA_DIR
    / "pca_model.json"
)


# =========================================
# 3. Web側設定
# =========================================

MAP_SAMPLE_SIZE = 5000
RANDOM_STATE = 42

K = 6
THRESHOLD_PERCENT = 1.0


# =========================================
# 4. クラスタ名
# =========================================
#
# 名前は技術スタックだけを基準にする。
# 年齢・職種・企業規模などは
# クラスタ名には使用しない。
# =========================================

CLUSTER_NAMES = {
    0: "C#・.NET中心型",
    1: "PHP・Laravel中心型",
    2: "React・TypeScript中心型",
    3: "Python Web中心型",
    4: "Java・Spring中心型",
    5: "Python・Node.js複合型",
}


# =========================================
# 5. カテゴリ表示名
# =========================================

CATEGORY_LABELS = {
    "language": "プログラミング言語",
    "database": "データベース",
    "platform": "プラットフォーム・開発技術",
    "webframe": "Webフレームワーク・技術",
}

CATEGORY_ORDER = [
    "language",
    "database",
    "platform",
    "webframe",
]


# =========================================
# 6. 補助情報表示名
# =========================================

METADATA_CONFIG = {
    "DevType": {
        "key": "devType",
        "label": "職種",
    },
    "OrgSize": {
        "key": "orgSize",
        "label": "企業規模",
    },
    "Industry": {
        "key": "industry",
        "label": "業界",
    },
    "RemoteWork": {
        "key": "remoteWork",
        "label": "働き方",
    },
    "Age": {
        "key": "age",
        "label": "年代",
    },
}


# =========================================
# 7. JSON保存用関数
# =========================================

def save_json(path, data):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


# =========================================
# 8. 開始
# =========================================

print(
    "======================================"
)

print(
    "Web用最終データセット作成 開始"
)

print(
    "======================================"
)

print()


# =========================================
# 9. データ読み込み
# =========================================

multihot_df = pd.read_csv(
    MULTIHOT_PATH
)

cluster_df = pd.read_csv(
    CLUSTER_ASSIGNMENTS_PATH
)

top_features_df = pd.read_csv(
    TOP_FEATURES_PATH
)

top_metadata_df = pd.read_csv(
    TOP_METADATA_PATH
)

workexp_df = pd.read_csv(
    WORKEXP_PATH
)

coordinates_df = pd.read_csv(
    PCA_COORDINATES_PATH
)

centers_df = pd.read_csv(
    PCA_CENTERS_PATH
)


with open(
    FEATURE_DEFINITIONS_PATH,
    "r",
    encoding="utf-8"
) as file:

    feature_definitions = json.load(
        file
    )


with open(
    PCA_MODEL_PATH,
    "r",
    encoding="utf-8"
) as file:

    pca_model = json.load(
        file
    )


print(
    f"分析対象者数: "
    f"{len(multihot_df):,}"
)

print(
    f"技術特徴数  : "
    f"{len(multihot_df.columns) - 1}"
)

print()


# =========================================
# 10. 基本チェック
# =========================================

if len(multihot_df) != 15239:

    raise ValueError(
        "分析対象人数が想定値 "
        "15,239人と一致しません。"
    )


if len(multihot_df.columns) - 1 != 131:

    raise ValueError(
        "技術特徴数が想定値 "
        "131と一致しません。"
    )


if len(cluster_df) != len(multihot_df):

    raise ValueError(
        "クラスタ割り当ての人数が"
        "Multi-hotデータと一致しません。"
    )


if len(coordinates_df) != len(multihot_df):

    raise ValueError(
        "PCA座標の人数が"
        "Multi-hotデータと一致しません。"
    )


if coordinates_df["cluster"].nunique() != K:

    raise ValueError(
        "PCA座標のクラスタ数が"
        "6ではありません。"
    )


if len(feature_definitions) != 131:

    raise ValueError(
        "feature_definitions.jsonの"
        "特徴数が131ではありません。"
    )


if pca_model["feature_count"] != 131:

    raise ValueError(
        "PCAモデルの特徴数が"
        "131ではありません。"
    )


# =========================================
# 11. 特徴順序を確認
# =========================================

multihot_feature_order = [
    column
    for column in multihot_df.columns
    if column != "analysis_id"
]


model_feature_order = (
    pca_model[
        "feature_order"
    ]
)


if multihot_feature_order != model_feature_order:

    raise ValueError(
        "Multi-hotデータとPCAモデルで"
        "特徴の順番が一致していません。"
    )


print(
    "特徴順序チェック: OK"
)

print()


# =========================================
# 12. 5,000人の比例サンプリング
# =========================================
#
# 各クラスタの元の人数比率を
# できるだけ正確に維持する。
# =========================================

cluster_counts = (
    coordinates_df[
        "cluster"
    ]
    .value_counts()
    .sort_index()
)


sample_info = []


for cluster_id, count in (
    cluster_counts.items()
):

    exact_sample = (
        MAP_SAMPLE_SIZE
        * count
        / len(coordinates_df)
    )


    floor_sample = math.floor(
        exact_sample
    )


    remainder = (
        exact_sample
        - floor_sample
    )


    sample_info.append(
        {
            "cluster":
                int(cluster_id),

            "original_count":
                int(count),

            "exact_sample":
                exact_sample,

            "sample_count":
                floor_sample,

            "remainder":
                remainder,
        }
    )


# 切り捨てで不足した人数を
# 小数部分が大きいクラスタへ1人ずつ追加
current_total = sum(
    item["sample_count"]
    for item in sample_info
)

remaining = (
    MAP_SAMPLE_SIZE
    - current_total
)


sample_info_sorted = sorted(
    sample_info,
    key=lambda item:
        item["remainder"],
    reverse=True,
)


for i in range(remaining):

    sample_info_sorted[
        i
    ][
        "sample_count"
    ] += 1


# =========================================
# 13. 実際にサンプリング
# =========================================

sampled_frames = []


print(
    "=== マップ表示用サンプリング ==="
)


for item in sorted(
    sample_info,
    key=lambda x:
        x["cluster"]
):

    cluster_id = (
        item[
            "cluster"
        ]
    )

    sample_count = (
        item[
            "sample_count"
        ]
    )


    cluster_points = (
        coordinates_df[
            coordinates_df[
                "cluster"
            ]
            == cluster_id
        ]
    )


    sampled_cluster = (
        cluster_points.sample(
            n=sample_count,
            random_state=(
                RANDOM_STATE
                + cluster_id
            ),
        )
    )


    sampled_frames.append(
        sampled_cluster
    )


    original_rate = (
        len(cluster_points)
        / len(coordinates_df)
        * 100
    )

    sample_rate = (
        sample_count
        / MAP_SAMPLE_SIZE
        * 100
    )


    print(
        f"Cluster {cluster_id}: "
        f"{sample_count:,}点 "
        f"({sample_rate:.2f}%) "
        f"/ 元 {original_rate:.2f}%"
    )


sampled_df = pd.concat(
    sampled_frames,
    ignore_index=True
)


# 描画順によって特定クラスタが
# 常に前面に来ないようシャッフル
sampled_df = (
    sampled_df.sample(
        frac=1,
        random_state=RANDOM_STATE,
    )
    .reset_index(
        drop=True
    )
)


if len(sampled_df) != MAP_SAMPLE_SIZE:

    raise ValueError(
        "サンプリング人数が"
        "5,000人になっていません。"
    )


print()


# =========================================
# 14. map_points.json
# =========================================

map_points = []


for _, row in sampled_df.iterrows():

    map_points.append(
        {
            "id":
                int(
                    row[
                        "analysis_id"
                    ]
                ),

            "cluster":
                int(
                    row[
                        "cluster"
                    ]
                ),

            "x":
                round(
                    float(
                        row[
                            "pc1"
                        ]
                    ),
                    6,
                ),

            "y":
                round(
                    float(
                        row[
                            "pc2"
                        ]
                    ),
                    6,
                ),
        }
    )


map_points_data = {
    "sampleSize":
        MAP_SAMPLE_SIZE,

    "originalSize":
        len(coordinates_df),

    "samplingMethod":
        "proportional_stratified_random",

    "randomState":
        RANDOM_STATE,

    "points":
        map_points,
}


MAP_POINTS_OUTPUT = (
    FRONTEND_DATA_DIR
    / "map_points.json"
)


save_json(
    MAP_POINTS_OUTPUT,
    map_points_data,
)


# =========================================
# 15. technologies.json
# =========================================

technology_groups = []


for category in CATEGORY_ORDER:

    category_features = [
        item
        for item in feature_definitions
        if item[
            "category"
        ]
        == category
    ]


    # UI上では利用率が高い順に並べる
    category_features = sorted(
        category_features,
        key=lambda item:
            item[
                "overall_usage_rate"
            ],
        reverse=True,
    )


    technologies = []


    for item in category_features:

        technologies.append(
            {
                "index":
                    int(
                        item[
                            "index"
                        ]
                    ),

                "feature":
                    item[
                        "feature"
                    ],

                "name":
                    item[
                        "technology"
                    ],

                "weight":
                    float(
                        item[
                            "weight"
                        ]
                    ),

                "overallUsageRate":
                    round(
                        float(
                            item[
                                "overall_usage_rate"
                            ]
                        ),
                        4,
                    ),
            }
        )


    technology_groups.append(
        {
            "key":
                category,

            "label":
                CATEGORY_LABELS[
                    category
                ],

            "count":
                len(
                    technologies
                ),

            "technologies":
                technologies,
        }
    )


technologies_data = {
    "total":
        len(
            feature_definitions
        ),

    "thresholdPercent":
        THRESHOLD_PERCENT,

    "categories":
        technology_groups,
}


TECHNOLOGIES_OUTPUT = (
    FRONTEND_DATA_DIR
    / "technologies.json"
)


save_json(
    TECHNOLOGIES_OUTPUT,
    technologies_data,
)


# =========================================
# 16. クラスタ情報作成
# =========================================

clusters = []


for cluster_id in range(K):

    center_row = (
        centers_df[
            centers_df[
                "cluster"
            ]
            == cluster_id
        ]
    )


    if len(center_row) != 1:

        raise ValueError(
            f"Cluster {cluster_id} の"
            "PCA中心が1件ではありません。"
        )


    center_row = (
        center_row.iloc[0]
    )


    # -----------------------------
    # 特徴的な技術 Top10
    # -----------------------------

    cluster_features = (
        top_features_df[
            top_features_df[
                "cluster"
            ]
            == cluster_id
        ]
        .sort_values(
            "rank"
        )
    )


    top_technologies = []


    for _, row in (
        cluster_features.iterrows()
    ):

        category = row[
            "category"
        ]


        top_technologies.append(
            {
                "rank":
                    int(
                        row[
                            "rank"
                        ]
                    ),

                "category":
                    category,

                "categoryLabel":
                    CATEGORY_LABELS.get(
                        category,
                        category,
                    ),

                "name":
                    row[
                        "technology"
                    ],

                "clusterUsageRate":
                    round(
                        float(
                            row[
                                "cluster_usage_rate"
                            ]
                        ),
                        4,
                    ),

                "overallUsageRate":
                    round(
                        float(
                            row[
                                "overall_usage_rate"
                            ]
                        ),
                        4,
                    ),

                "differencePoint":
                    round(
                        float(
                            row[
                                "difference_point"
                            ]
                        ),
                        4,
                    ),
            }
        )


    # -----------------------------
    # 補助情報
    # -----------------------------

    metadata = {}


    for source_column, config in (
        METADATA_CONFIG.items()
    ):

        rows = (
            top_metadata_df[
                (
                    top_metadata_df[
                        "cluster"
                    ]
                    == cluster_id
                )
                &
                (
                    top_metadata_df[
                        "column"
                    ]
                    == source_column
                )
            ]
            .sort_values(
                "rank"
            )
        )


        items = []


        for _, row in rows.iterrows():

            items.append(
                {
                    "rank":
                        int(
                            row[
                                "rank"
                            ]
                        ),

                    "value":
                        row[
                            "value"
                        ],

                    "clusterRate":
                        round(
                            float(
                                row[
                                    "cluster_rate"
                                ]
                            ),
                            4,
                        ),

                    "overallRate":
                        round(
                            float(
                                row[
                                    "overall_rate"
                                ]
                            ),
                            4,
                        ),

                    "differencePoint":
                        round(
                            float(
                                row[
                                    "difference_point"
                                ]
                            ),
                            4,
                        ),
                }
            )


        metadata[
            config[
                "key"
            ]
        ] = {
            "label":
                config[
                    "label"
                ],

            "items":
                items,
        }


    # -----------------------------
    # 実務経験
    # -----------------------------

    workexp_row = (
        workexp_df[
            workexp_df[
                "cluster"
            ].astype(
                str
            )
            == str(
                cluster_id
            )
        ]
    )


    if len(workexp_row) != 1:

        raise ValueError(
            f"Cluster {cluster_id} の"
            "WorkExp情報が1件ではありません。"
        )


    workexp_row = (
        workexp_row.iloc[0]
    )


    work_experience = {
        "label":
            "実務経験",

        "validCount":
            int(
                workexp_row[
                    "valid_count"
                ]
            ),

        "median":
            float(
                workexp_row[
                    "median"
                ]
            ),

        "q1":
            float(
                workexp_row[
                    "q1"
                ]
            ),

        "q3":
            float(
                workexp_row[
                    "q3"
                ]
            ),
    }


    clusters.append(
        {
            "id":
                cluster_id,

            "name":
                CLUSTER_NAMES[
                    cluster_id
                ],

            "count":
                int(
                    center_row[
                        "count"
                    ]
                ),

            "rate":
                round(
                    float(
                        center_row[
                            "rate"
                        ]
                    ),
                    4,
                ),

            "center":
                {
                    "x":
                        round(
                            float(
                                center_row[
                                    "pc1"
                                ]
                            ),
                            6,
                        ),

                    "y":
                        round(
                            float(
                                center_row[
                                    "pc2"
                                ]
                            ),
                            6,
                        ),
                },

            "topTechnologies":
                top_technologies,

            "metadata":
                metadata,

            "workExperience":
                work_experience,
        }
    )


# =========================================
# 17. 全体の実務経験情報
# =========================================

overall_workexp_row = (
    workexp_df[
        workexp_df[
            "cluster"
        ].astype(
            str
        )
        == "overall"
    ]
)


if len(overall_workexp_row) != 1:

    raise ValueError(
        "全体WorkExp情報が"
        "1件ではありません。"
    )


overall_workexp_row = (
    overall_workexp_row.iloc[0]
)


overall_work_experience = {
    "validCount":
        int(
            overall_workexp_row[
                "valid_count"
            ]
        ),

    "median":
        float(
            overall_workexp_row[
                "median"
            ]
        ),

    "q1":
        float(
            overall_workexp_row[
                "q1"
            ]
        ),

    "q3":
        float(
            overall_workexp_row[
                "q3"
            ]
        ),
}


clusters_data = {
    "count":
        K,

    "respondents":
        len(
            coordinates_df
        ),

    "clusters":
        clusters,

    "overallWorkExperience":
        overall_work_experience,
}


CLUSTERS_OUTPUT = (
    FRONTEND_DATA_DIR
    / "clusters.json"
)


save_json(
    CLUSTERS_OUTPUT,
    clusters_data,
)


# =========================================
# 18. model.json
# =========================================
#
# PCAのモデル値は精度を落とさないため
# 丸めず、そのまま保存する。
#
# React側では
#
# 1. 131次元Multi-hotを作る
# 2. カテゴリ重みを掛ける
# 3. PCAで2次元座標を計算
# 4. 131次元中心との距離を計算
#
# に使用する。
# =========================================

explained_variance_ratio = (
    pca_model[
        "pca"
    ][
        "explained_variance_ratio"
    ]
)


model_data = {
    "version":
        1,

    "respondents":
        int(
            pca_model[
                "respondents"
            ]
        ),

    "featureCount":
        int(
            pca_model[
                "feature_count"
            ]
        ),

    "clusterCount":
        K,

    "thresholdPercent":
        THRESHOLD_PERCENT,

    "featureOrder":
        pca_model[
            "feature_order"
        ],

    "categoryWeights":
        pca_model[
            "category_weights"
        ],

    "pca": {
        "mean":
            pca_model[
                "pca"
            ][
                "mean"
            ],

        "components":
            pca_model[
                "pca"
            ][
                "components"
            ],

        "explainedVarianceRatio":
            explained_variance_ratio,

        "pc1ExplainedPercent":
            (
                explained_variance_ratio[
                    0
                ]
                * 100
            ),

        "pc2ExplainedPercent":
            (
                explained_variance_ratio[
                    1
                ]
                * 100
            ),

        "cumulativeExplainedPercent":
            (
                sum(
                    explained_variance_ratio
                )
                * 100
            ),
    },

    "clusterCentersWeighted":
        pca_model[
            "cluster_centers_weighted"
        ],

    "notes": {
        "map":
            (
                "PCAによる2次元表示。"
                "技術スタック全体の距離判定には使用しない。"
            ),

        "clusterDistance":
            (
                "最も近いクラスタは、"
                "カテゴリ重み付き131次元空間で判定する。"
            ),
    },
}


MODEL_OUTPUT = (
    FRONTEND_DATA_DIR
    / "model.json"
)


save_json(
    MODEL_OUTPUT,
    model_data,
)


# =========================================
# 19. 最終検証
# =========================================

print(
    "=== 最終検証 ==="
)


print(
    f"map_points.json : "
    f"{len(map_points):,}点"
)

print(
    f"clusters.json   : "
    f"{len(clusters)}クラスタ"
)

print(
    f"technologies.json: "
    f"{len(feature_definitions)}技術"
)

print(
    f"model.json      : "
    f"{model_data['featureCount']}次元"
)


if len(map_points) != 5000:

    raise ValueError(
        "map_points.jsonが"
        "5,000点ではありません。"
    )


if len(clusters) != 6:

    raise ValueError(
        "clusters.jsonが"
        "6クラスタではありません。"
    )


if len(feature_definitions) != 131:

    raise ValueError(
        "technologies.jsonが"
        "131技術ではありません。"
    )


if len(
    model_data[
        "pca"
    ][
        "mean"
    ]
) != 131:

    raise ValueError(
        "PCA平均ベクトルが"
        "131次元ではありません。"
    )


if len(
    model_data[
        "pca"
    ][
        "components"
    ]
) != 2:

    raise ValueError(
        "PCA componentsが"
        "2成分ではありません。"
    )


for component in (
    model_data[
        "pca"
    ][
        "components"
    ]
):

    if len(component) != 131:

        raise ValueError(
            "PCA componentが"
            "131次元ではありません。"
        )


if len(
    model_data[
        "clusterCentersWeighted"
    ]
) != 6:

    raise ValueError(
        "131次元クラスタ中心が"
        "6個ではありません。"
    )


print(
    "すべての検証: OK"
)

print()


# =========================================
# 20. 完了
# =========================================

print(
    "======================================"
)

print(
    "Web用最終データセット作成 完了"
)

print(
    "======================================"
)

print()

print(
    "出力先:"
)

print(
    FRONTEND_DATA_DIR
)

print()

print(
    "作成ファイル:"
)

print(
    MAP_POINTS_OUTPUT
)

print(
    CLUSTERS_OUTPUT
)

print(
    TECHNOLOGIES_OUTPUT
)

print(
    MODEL_OUTPUT
)