from pathlib import Path

import pandas as pd


# =========================================
# 1. パス設定
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    ROOT_DIR / "data" / "processed"
)

CLUSTER_ANALYSIS_DIR = (
    ROOT_DIR
    / "analysis_output"
    / "cluster_analysis"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "analysis_output"
    / "cluster_metadata"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


METADATA_PATH = (
    PROCESSED_DIR
    / "analysis_metadata.csv"
)

CLUSTER_PATH = (
    CLUSTER_ANALYSIS_DIR
    / "cluster_assignments_k6.csv"
)


# =========================================
# 2. 分析する項目
# =========================================

CATEGORICAL_COLUMNS = [
    "DevType",
    "OrgSize",
    "Industry",
    "RemoteWork",
    "Age",
]

NUMERIC_COLUMNS = [
    "WorkExp",
]

TOP_N = 5


# =========================================
# 3. データ読み込み
# =========================================

print(
    "======================================"
)

print(
    "クラスタ補助情報分析 開始"
)

print(
    "======================================"
)

print()

metadata_df = pd.read_csv(
    METADATA_PATH
)

cluster_df = pd.read_csv(
    CLUSTER_PATH
)


# =========================================
# 4. データ確認
# =========================================

if "analysis_id" not in metadata_df.columns:
    raise ValueError(
        "analysis_metadata.csv に "
        "analysis_id がありません。"
    )

if "analysis_id" not in cluster_df.columns:
    raise ValueError(
        "cluster_assignments_k6.csv に "
        "analysis_id がありません。"
    )

if "cluster" not in cluster_df.columns:
    raise ValueError(
        "cluster_assignments_k6.csv に "
        "cluster がありません。"
    )


# =========================================
# 5. クラスタ情報と補助情報を結合
# =========================================

df = pd.merge(
    cluster_df,
    metadata_df,
    on="analysis_id",
    how="inner",
    validate="one_to_one"
)


print(
    f"分析対象者数: {len(df):,}"
)

print()


if len(df) != len(cluster_df):
    raise ValueError(
        "クラスタデータとMetadataの人数が"
        "一致していません。"
    )


# =========================================
# 6. 存在する列だけ利用
# =========================================

available_categorical_columns = [
    column
    for column in CATEGORICAL_COLUMNS
    if column in df.columns
]

available_numeric_columns = [
    column
    for column in NUMERIC_COLUMNS
    if column in df.columns
]


print(
    "=== 利用する補助情報 ==="
)

for column in available_categorical_columns:
    print(
        f"○ {column}"
    )

for column in available_numeric_columns:
    print(
        f"○ {column}"
    )

print()


# =========================================
# 7. クラスタ人数
# =========================================

cluster_counts = (
    df["cluster"]
    .value_counts()
    .sort_index()
)


print(
    "=== クラスタ人数 ==="
)

for cluster_id, count in cluster_counts.items():

    rate = (
        count
        / len(df)
        * 100
    )

    print(
        f"Cluster {cluster_id}: "
        f"{count:,}人 "
        f"({rate:.2f}%)"
    )

print()


# =========================================
# 8. 各項目の回答率を確認
# =========================================

response_summary_rows = []


for column in (
    available_categorical_columns
    + available_numeric_columns
):

    # 全体
    overall_answered = (
        df[column]
        .notna()
        .sum()
    )

    overall_missing = (
        df[column]
        .isna()
        .sum()
    )


    response_summary_rows.append(
        {
            "cluster": "overall",
            "column": column,
            "total": len(df),
            "answered": overall_answered,
            "missing": overall_missing,
            "answered_rate":
                overall_answered
                / len(df)
                * 100,
            "missing_rate":
                overall_missing
                / len(df)
                * 100,
        }
    )


    # クラスタごと
    for cluster_id in sorted(
        df["cluster"].unique()
    ):

        cluster_data = df[
            df["cluster"]
            == cluster_id
        ]

        answered = (
            cluster_data[column]
            .notna()
            .sum()
        )

        missing = (
            cluster_data[column]
            .isna()
            .sum()
        )


        response_summary_rows.append(
            {
                "cluster":
                    int(cluster_id),

                "column":
                    column,

                "total":
                    len(cluster_data),

                "answered":
                    answered,

                "missing":
                    missing,

                "answered_rate":
                    answered
                    / len(cluster_data)
                    * 100,

                "missing_rate":
                    missing
                    / len(cluster_data)
                    * 100,
            }
        )


response_summary_df = pd.DataFrame(
    response_summary_rows
)


response_summary_df.to_csv(
    OUTPUT_DIR
    / "metadata_response_summary.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 9. カテゴリデータを分析
# =========================================

categorical_profile_rows = []

top_distinctive_rows = []


for column in available_categorical_columns:

    print(
        "======================================"
    )

    print(
        f"{column}"
    )

    print(
        "======================================"
    )


    # -------------------------------------
    # 全体の有効回答
    #
    # 未回答は「その選択肢ではない」
    # と扱わない
    # -------------------------------------

    overall_valid = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
    )


    overall_valid = overall_valid[
        overall_valid != ""
    ]


    overall_answered = len(
        overall_valid
    )


    overall_counts = (
        overall_valid
        .value_counts()
    )


    overall_rates = (
        overall_counts
        / overall_answered
        * 100
    )


    print(
        f"全体の有効回答者: "
        f"{overall_answered:,}"
    )

    print()


    # -------------------------------------
    # クラスタごと
    # -------------------------------------

    for cluster_id in sorted(
        df["cluster"].unique()
    ):

        cluster_data = df[
            df["cluster"]
            == cluster_id
        ]


        cluster_valid = (
            cluster_data[column]
            .dropna()
            .astype(str)
            .str.strip()
        )


        cluster_valid = cluster_valid[
            cluster_valid != ""
        ]


        cluster_answered = len(
            cluster_valid
        )


        cluster_counts_column = (
            cluster_valid
            .value_counts()
        )


        cluster_rates = (
            cluster_counts_column
            / cluster_answered
            * 100
        )


        # 全体とクラスタに存在する
        # すべての選択肢
        values = sorted(
            set(
                overall_counts.index
            )
            |
            set(
                cluster_counts_column.index
            )
        )


        cluster_rows = []


        for value in values:

            cluster_count = int(
                cluster_counts_column.get(
                    value,
                    0
                )
            )

            overall_count = int(
                overall_counts.get(
                    value,
                    0
                )
            )


            cluster_rate = float(
                cluster_rates.get(
                    value,
                    0
                )
            )

            overall_rate = float(
                overall_rates.get(
                    value,
                    0
                )
            )


            difference_point = (
                cluster_rate
                - overall_rate
            )


            row = {
                "cluster":
                    int(cluster_id),

                "column":
                    column,

                "value":
                    value,

                "cluster_answered":
                    cluster_answered,

                "cluster_count":
                    cluster_count,

                "cluster_rate":
                    cluster_rate,

                "overall_answered":
                    overall_answered,

                "overall_count":
                    overall_count,

                "overall_rate":
                    overall_rate,

                "difference_point":
                    difference_point,
            }


            categorical_profile_rows.append(
                row
            )

            cluster_rows.append(
                row
            )


        # ---------------------------------
        # 特徴的な項目 Top5
        # ---------------------------------

        cluster_profile_df = (
            pd.DataFrame(
                cluster_rows
            )
            .sort_values(
                [
                    "difference_point",
                    "cluster_rate"
                ],
                ascending=[
                    False,
                    False
                ]
            )
        )


        top_df = (
            cluster_profile_df
            .head(TOP_N)
            .copy()
        )


        top_df["rank"] = range(
            1,
            len(top_df) + 1
        )


        top_distinctive_rows.extend(
            top_df.to_dict(
                orient="records"
            )
        )


        # ---------------------------------
        # ターミナル表示
        # ---------------------------------

        print(
            f"--- Cluster {cluster_id} ---"
        )

        print(
            f"有効回答: "
            f"{cluster_answered:,}人"
        )


        for rank, (_, row) in enumerate(
            top_df.iterrows(),
            start=1
        ):

            print(
                f"{rank}. "
                f"{row['value']}"
            )

            print(
                f"   クラスタ: "
                f"{row['cluster_rate']:.1f}%"
                f" / "
                f"全体: "
                f"{row['overall_rate']:.1f}%"
                f" / "
                f"差: "
                f"{row['difference_point']:+.1f}pt"
            )


        print()


# =========================================
# 10. カテゴリ分析結果を保存
# =========================================

categorical_profile_df = (
    pd.DataFrame(
        categorical_profile_rows
    )
)


categorical_profile_df.to_csv(
    OUTPUT_DIR
    / "categorical_metadata_profiles.csv",
    index=False,
    encoding="utf-8-sig"
)


top_distinctive_df = (
    pd.DataFrame(
        top_distinctive_rows
    )
)


top_distinctive_df = (
    top_distinctive_df
    .sort_values(
        [
            "column",
            "cluster",
            "rank"
        ]
    )
)


top_distinctive_df.to_csv(
    OUTPUT_DIR
    / "top_distinctive_metadata.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 11. WorkExpを分析
# =========================================

workexp_rows = []


if "WorkExp" in available_numeric_columns:

    print(
        "======================================"
    )

    print(
        "WorkExp"
    )

    print(
        "======================================"
    )


    # 数値へ変換
    workexp_numeric = pd.to_numeric(
        df["WorkExp"],
        errors="coerce"
    )


    overall_valid = (
        workexp_numeric
        .dropna()
    )


    overall_median = (
        overall_valid
        .median()
    )

    overall_q1 = (
        overall_valid
        .quantile(0.25)
    )

    overall_q3 = (
        overall_valid
        .quantile(0.75)
    )


    print(
        f"全体中央値: "
        f"{overall_median:.1f}年"
    )

    print(
        f"全体Q1-Q3 : "
        f"{overall_q1:.1f}"
        f"〜"
        f"{overall_q3:.1f}年"
    )

    print()


    # -------------------------------------
    # 全体
    # -------------------------------------

    workexp_rows.append(
        {
            "cluster":
                "overall",

            "valid_count":
                len(overall_valid),

            "median":
                float(
                    overall_median
                ),

            "q1":
                float(
                    overall_q1
                ),

            "q3":
                float(
                    overall_q3
                ),
        }
    )


    # -------------------------------------
    # クラスタごと
    # -------------------------------------

    for cluster_id in sorted(
        df["cluster"].unique()
    ):

        cluster_mask = (
            df["cluster"]
            == cluster_id
        )


        cluster_workexp = (
            workexp_numeric[
                cluster_mask
            ]
            .dropna()
        )


        if len(cluster_workexp) == 0:

            continue


        median = (
            cluster_workexp
            .median()
        )

        q1 = (
            cluster_workexp
            .quantile(0.25)
        )

        q3 = (
            cluster_workexp
            .quantile(0.75)
        )


        workexp_rows.append(
            {
                "cluster":
                    int(cluster_id),

                "valid_count":
                    len(
                        cluster_workexp
                    ),

                "median":
                    float(
                        median
                    ),

                "q1":
                    float(
                        q1
                    ),

                "q3":
                    float(
                        q3
                    ),
            }
        )


        print(
            f"Cluster {cluster_id}:"
        )

        print(
            f"  有効回答: "
            f"{len(cluster_workexp):,}人"
        )

        print(
            f"  中央値  : "
            f"{median:.1f}年"
        )

        print(
            f"  Q1-Q3   : "
            f"{q1:.1f}"
            f"〜"
            f"{q3:.1f}年"
        )

        print()


workexp_df = pd.DataFrame(
    workexp_rows
)


workexp_df.to_csv(
    OUTPUT_DIR
    / "workexp_summary.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 12. 結合済みデータも保存
# =========================================

df.to_csv(
    OUTPUT_DIR
    / "cluster_metadata_joined.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 13. 完了
# =========================================

print(
    "======================================"
)

print(
    "クラスタ補助情報分析 完了"
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