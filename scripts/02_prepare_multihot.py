from pathlib import Path

import pandas as pd


# =========================================
# 1. パス設定
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"

ANALYSIS_OUTPUT_DIR = (
    ROOT_DIR / "analysis_output"
)

PROCESSED_DIR = (
    DATA_DIR / "processed"
)

SURVEY_PATH = (
    DATA_DIR / "results.csv"
)

ANALYSIS_OUTPUT_DIR.mkdir(
    exist_ok=True
)

PROCESSED_DIR.mkdir(
    exist_ok=True
)


# =========================================
# 2. 今回クラスタリングに使うカテゴリ
# =========================================

CORE_TECH_COLUMNS = {
    "language": "LanguageHaveWorkedWith",
    "database": "DatabaseHaveWorkedWith",
    "platform": "PlatformHaveWorkedWith",
    "webframe": "WebframeHaveWorkedWith",
}


# 比較する利用率の閾値
THRESHOLDS = [
    0.5,
    1.0,
    2.0,
]


# =========================================
# 3. CSV読み込み
# =========================================

print(
    "======================================"
)

print(
    "Multi-hotデータ作成開始"
)

print(
    "======================================"
)

print()

print(
    "CSVを読み込んでいます..."
)

df = pd.read_csv(
    SURVEY_PATH,
    low_memory=False
)

print(
    "読み込み完了"
)

print()


# =========================================
# 4. 必要な列が存在するか確認
# =========================================

required_columns = [
    "MainBranch",
    *CORE_TECH_COLUMNS.values()
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    raise ValueError(
        "必要な列が見つかりません: "
        + ", ".join(missing_columns)
    )


# =========================================
# 5. Professional Developerを抽出
# =========================================

PROFESSIONAL_VALUE = (
    "I am a developer by profession"
)


professional_df = df[
    df["MainBranch"]
    == PROFESSIONAL_VALUE
].copy()


print(
    "=== Professional Developer ==="
)

print(
    f"{len(professional_df):,}人"
)

print()


# =========================================
# 6. 主要4カテゴリの回答状況を確認
# =========================================

print(
    "=== 主要4カテゴリの回答状況 ==="
)


for category, column in (
    CORE_TECH_COLUMNS.items()
):

    answered = (
        professional_df[column]
        .notna()
        .sum()
    )

    rate = (
        answered
        / len(professional_df)
        * 100
    )

    print(
        f"{category:10}: "
        f"{answered:,}人 "
        f"({rate:.2f}%)"
    )


print()


# =========================================
# 7. 4カテゴリすべて回答した人だけに絞る
# =========================================

core_columns = list(
    CORE_TECH_COLUMNS.values()
)


analysis_df = (
    professional_df
    .dropna(
        subset=core_columns
    )
    .copy()
)


print(
    "=== 分析対象者 ==="
)

print(
    f"Professional Developer : "
    f"{len(professional_df):,}"
)

print(
    f"4カテゴリ回答済み      : "
    f"{len(analysis_df):,}"
)


excluded_count = (
    len(professional_df)
    - len(analysis_df)
)


print(
    f"除外                  : "
    f"{excluded_count:,}"
)


analysis_rate = (
    len(analysis_df)
    / len(professional_df)
    * 100
)


print(
    f"残存率                : "
    f"{analysis_rate:.2f}%"
)

print()


# =========================================
# 8. 分析用IDを追加
# =========================================

analysis_df = (
    analysis_df
    .reset_index(drop=True)
)

analysis_df[
    "analysis_id"
] = range(
    len(analysis_df)
)


# =========================================
# 9. Multi-hot化
# =========================================

print(
    "=== Multi-hot化 ==="
)


category_dummies = {}

feature_catalog_rows = []


for category, column in (
    CORE_TECH_COLUMNS.items()
):

    print()

    print(
        f"[{category}]"
    )


    # -------------------------------------
    # 例:
    #
    # Java;Python;SQL
    #
    # ↓
    #
    # Java   1
    # Python 1
    # SQL    1
    #
    # それ以外は0
    # -------------------------------------

    dummies = (
        analysis_df[column]
        .astype(str)
        .str.get_dummies(
            sep=";"
        )
    )


    # 技術名の前後の空白を除去
    dummies.columns = [
        technology.strip()
        for technology
        in dummies.columns
    ]


    # 同名列が発生していないか確認
    if dummies.columns.duplicated().any():

        raise ValueError(
            f"{category}で"
            "重複した技術名が見つかりました。"
        )


    category_dummies[
        category
    ] = dummies


    print(
        f"技術数: "
        f"{len(dummies.columns)}"
    )


    # -------------------------------------
    # 技術ごとの利用人数・利用率
    # -------------------------------------

    users = (
        dummies
        .sum(axis=0)
    )


    usage_rate = (
        users
        / len(analysis_df)
        * 100
    )


    for technology in (
        dummies.columns
    ):

        row = {
            "category": category,
            "source_column": column,
            "technology": technology,
            "users": int(
                users[technology]
            ),
            "usage_rate": float(
                usage_rate[technology]
            ),
        }


        # 各閾値で残るかどうかも記録
        for threshold in THRESHOLDS:

            key = (
                "keep_"
                + str(threshold)
                .replace(".", "_")
                + "pct"
            )

            row[key] = (
                usage_rate[technology]
                >= threshold
            )


        feature_catalog_rows.append(
            row
        )


# =========================================
# 10. 全技術の一覧を保存
# =========================================

feature_catalog_df = pd.DataFrame(
    feature_catalog_rows
)


feature_catalog_df = (
    feature_catalog_df
    .sort_values(
        [
            "category",
            "usage_rate"
        ],
        ascending=[
            True,
            False
        ]
    )
)


feature_catalog_df.to_csv(
    ANALYSIS_OUTPUT_DIR
    / "feature_catalog.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 11. 閾値ごとのMulti-hotデータ作成
# =========================================

threshold_summary_rows = []


print()

print(
    "=== 閾値比較 ==="
)


for threshold in THRESHOLDS:

    print()

    print(
        f"--- {threshold}% ---"
    )


    selected_frames = []

    category_feature_counts = {}


    for category, dummies in (
        category_dummies.items()
    ):

        users = (
            dummies
            .sum(axis=0)
        )

        usage_rate = (
            users
            / len(analysis_df)
            * 100
        )


        selected_columns = (
            usage_rate[
                usage_rate >= threshold
            ]
            .index
            .tolist()
        )


        category_feature_counts[
            category
        ] = len(
            selected_columns
        )


        # ---------------------------------
        # 技術名だけだとカテゴリが
        # 分からなくなるため、
        #
        # language__Java
        # database__PostgreSQL
        #
        # の形式にする
        # ---------------------------------

        selected = (
            dummies[
                selected_columns
            ]
            .copy()
        )


        selected.columns = [
            f"{category}__{technology}"
            for technology
            in selected.columns
        ]


        selected_frames.append(
            selected
        )


        print(
            f"{category:10}: "
            f"{len(selected_columns)}技術"
        )


    # 4カテゴリを横方向に結合
    multihot_df = pd.concat(
        selected_frames,
        axis=1
    )


    # analysis_idを先頭に追加
    multihot_df.insert(
        0,
        "analysis_id",
        analysis_df[
            "analysis_id"
        ]
    )


    threshold_name = (
        str(threshold)
        .replace(".", "_")
    )


    output_path = (
        PROCESSED_DIR
        / (
            "multihot_"
            + threshold_name
            + "pct.csv"
        )
    )


    multihot_df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )


    total_features = (
        len(multihot_df.columns)
        - 1
    )


    print(
        f"合計: "
        f"{total_features}技術"
    )


    threshold_summary_rows.append(
        {
            "threshold": threshold,
            "respondents": len(
                analysis_df
            ),
            "language_features":
                category_feature_counts[
                    "language"
                ],
            "database_features":
                category_feature_counts[
                    "database"
                ],
            "platform_features":
                category_feature_counts[
                    "platform"
                ],
            "webframe_features":
                category_feature_counts[
                    "webframe"
                ],
            "total_features":
                total_features,
        }
    )


# =========================================
# 12. 閾値比較結果を保存
# =========================================

threshold_summary_df = (
    pd.DataFrame(
        threshold_summary_rows
    )
)


threshold_summary_df.to_csv(
    ANALYSIS_OUTPUT_DIR
    / "threshold_summary.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 13. 後でクラスタ特徴分析に使う情報を保存
# =========================================

metadata_candidates = [
    "DevType",
    "WorkExp",
    "OrgSize",
    "Industry",
    "RemoteWork",
    "Age",
]


available_metadata = [
    column
    for column in metadata_candidates
    if column in analysis_df.columns
]


metadata_df = analysis_df[
    [
        "analysis_id",
        *available_metadata
    ]
].copy()


metadata_df.to_csv(
    PROCESSED_DIR
    / "analysis_metadata.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 14. 分析対象人数の概要
# =========================================

population_summary_df = pd.DataFrame(
    [
        {
            "stage": "all_respondents",
            "count": len(df),
        },
        {
            "stage":
                "professional_developers",
            "count":
                len(professional_df),
        },
        {
            "stage":
                "complete_core_categories",
            "count":
                len(analysis_df),
        },
    ]
)


population_summary_df.to_csv(
    ANALYSIS_OUTPUT_DIR
    / "population_summary.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 15. 完了
# =========================================

print()

print(
    "======================================"
)

print(
    "Multi-hotデータ作成完了"
)

print(
    "======================================"
)

print()

print(
    "確認してほしいファイル:"
)

print(
    ANALYSIS_OUTPUT_DIR
    / "threshold_summary.csv"
)

print(
    ANALYSIS_OUTPUT_DIR
    / "feature_catalog.csv"
)

print()

print(
    "Multi-hotデータ:"
)

print(
    PROCESSED_DIR
)