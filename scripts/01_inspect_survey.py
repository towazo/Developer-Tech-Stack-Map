from pathlib import Path

import pandas as pd


# =========================================
# 1. ファイルの場所を設定
# =========================================

# このPythonファイルの1つ上の階層
# ZEMI-TASK-2 を取得
ROOT_DIR = Path(__file__).resolve().parents[1]

# dataフォルダ
DATA_DIR = ROOT_DIR / "data"

# 分析結果を保存するフォルダ
OUTPUT_DIR = ROOT_DIR / "analysis_output"

# 元データ
SURVEY_PATH = DATA_DIR / "results.csv"

# analysis_outputが存在しなければ作成
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================================
# 2. 今回確認する技術系の列
# =========================================

TECH_COLUMNS = {
    "language": "LanguageHaveWorkedWith",
    "database": "DatabaseHaveWorkedWith",
    "platform": "PlatformHaveWorkedWith",
    "webframe": "WebframeHaveWorkedWith",
    "devenvs": "DevEnvsHaveWorkedWith",
    "sotags": "SOTagsHaveWorkedWith",
}


# =========================================
# 3. CSVを読み込む
# =========================================

print("======================================")
print("Stack Overflow Survey 調査開始")
print("======================================")
print()

print("CSVを読み込んでいます...")

df = pd.read_csv(
    SURVEY_PATH,
    low_memory=False
)

print("読み込み完了")
print()


# =========================================
# 4. データ全体を確認
# =========================================

print("=== 元データ ===")

print(f"回答者数 : {len(df):,}")
print(f"列数     : {len(df.columns):,}")

print()


# =========================================
# 5. MainBranch列を確認
# =========================================

if "MainBranch" not in df.columns:
    raise ValueError(
        "MainBranch列が見つかりません。"
    )


print("=== MainBranch ===")

main_branch_counts = df[
    "MainBranch"
].value_counts(
    dropna=False
)

print(main_branch_counts)

print()


# =========================================
# 6. Professional Developerを抽出
# =========================================

PROFESSIONAL_VALUE = (
    "I am a developer by profession"
)

professional_df = df[
    df["MainBranch"] == PROFESSIONAL_VALUE
].copy()


professional_count = len(
    professional_df
)

professional_rate = (
    professional_count
    / len(df)
    * 100
)


print("=== Professional Developer ===")

print(
    f"元の回答者数             : "
    f"{len(df):,}"
)

print(
    f"Professional Developer : "
    f"{professional_count:,}"
)

print(
    f"割合                     : "
    f"{professional_rate:.2f}%"
)

print()


# =========================================
# 7. 技術系の列が本当に存在するか確認
# =========================================

print("=== 技術系の列 ===")

available_tech_columns = {}


for category, column in TECH_COLUMNS.items():

    if column in df.columns:

        print(
            f"○ {category:10} "
            f"{column}"
        )

        available_tech_columns[
            category
        ] = column

    else:

        print(
            f"× {category:10} "
            f"{column}"
        )


print()


# =========================================
# 8. 各カテゴリの未回答率を調べる
# =========================================

print(
    "=== 技術カテゴリごとの回答状況 ==="
)

summary_rows = []


for category, column in (
    available_tech_columns.items()
):

    total = len(
        professional_df
    )

    answered = (
        professional_df[column]
        .notna()
        .sum()
    )

    missing = (
        professional_df[column]
        .isna()
        .sum()
    )

    answered_rate = (
        answered
        / total
        * 100
    )

    missing_rate = (
        missing
        / total
        * 100
    )


    print()

    print(
        f"[{category}]"
    )

    print(
        f"列名       : {column}"
    )

    print(
        f"回答あり   : "
        f"{answered:,} "
        f"({answered_rate:.2f}%)"
    )

    print(
        f"未回答     : "
        f"{missing:,} "
        f"({missing_rate:.2f}%)"
    )


    summary_rows.append(
        {
            "category": category,
            "column": column,
            "professional_developers": total,
            "answered": answered,
            "missing": missing,
            "answered_rate": answered_rate,
            "missing_rate": missing_rate,
        }
    )


# =========================================
# 9. 回答状況をCSVへ保存
# =========================================

summary_df = pd.DataFrame(
    summary_rows
)

summary_df.to_csv(
    OUTPUT_DIR
    / "category_response_summary.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================================
# 10. 各技術の利用率を調べる
# =========================================

print()
print(
    "=== 各技術の利用率 ==="
)


for category, column in (
    available_tech_columns.items()
):

    print()

    print(
        f"--- {category} ---"
    )


    # この質問に回答している人だけ取り出す
    answered_series = (
        professional_df[column]
        .dropna()
    )


    valid_respondents = len(
        answered_series
    )


    # 例:
    # Java;Python;SQL
    #
    # ↓
    #
    # Java
    # Python
    # SQL

    technologies = (
        answered_series
        .astype(str)
        .str.split(";")
        .explode()
        .str.strip()
    )


    # 万が一空文字があれば除外
    technologies = technologies[
        technologies != ""
    ]


    # 技術ごとの利用人数
    counts = (
        technologies
        .value_counts()
    )


    usage_df = (
        counts
        .rename_axis(
            "technology"
        )
        .reset_index(
            name="users"
        )
    )


    # -------------------------------------
    # 利用率
    #
    # 技術を選択した人数
    # -----------------------------
    # その質問に回答した人数
    #
    # 未回答者は分母に含めない
    # -------------------------------------

    usage_df[
        "usage_rate"
    ] = (
        usage_df["users"]
        / valid_respondents
        * 100
    )


    print(
        f"有効回答者数 : "
        f"{valid_respondents:,}"
    )

    print(
        f"技術の種類   : "
        f"{len(usage_df):,}"
    )

    print()

    print(
        "利用率 上位10件"
    )

    print(
        usage_df
        .head(10)
        .to_string(
            index=False
        )
    )


    # カテゴリ別にCSV保存
    output_path = (
        OUTPUT_DIR
        / f"{category}_technology_usage.csv"
    )

    usage_df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )


# =========================================
# 11. 完了
# =========================================

print()
print(
    "======================================"
)

print(
    "調査完了"
)

print(
    "======================================"
)

print()

print(
    "分析結果:"
)

print(
    OUTPUT_DIR
)