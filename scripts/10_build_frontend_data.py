from pathlib import Path
import json
import math

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
FRONTEND_DATA_DIR = ROOT_DIR / "public" / "data"
MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
UMAP_COORDINATES_PATH = PROCESSED_DIR / "umap" / "umap_coordinates.csv"
METADATA_PATH = PROCESSED_DIR / "analysis_metadata.csv"
CLUSTER_ASSIGNMENTS_PATH = (
    ROOT_DIR / "analysis_output" / "cluster_analysis" / "cluster_assignments_k6.csv"
)
TOP_CLUSTER_FEATURES_PATH = (
    ROOT_DIR / "analysis_output" / "cluster_analysis" / "top_distinctive_features_k6.csv"
)

MAP_SAMPLE_SIZE = 5000
RANDOM_STATE = 42
CATEGORY_LABELS = {
    "language": "プログラミング言語",
    "database": "データベース",
    "platform": "プラットフォーム・開発技術",
    "webframe": "Webフレームワーク・技術",
}
CATEGORY_ORDER = ["language", "database", "platform", "webframe"]


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
multihot_df = pd.read_csv(MULTIHOT_PATH).sort_values("analysis_id").reset_index(drop=True)
coordinates_df = pd.read_csv(UMAP_COORDINATES_PATH).sort_values("analysis_id").reset_index(drop=True)
cluster_df = pd.read_csv(CLUSTER_ASSIGNMENTS_PATH).sort_values("analysis_id").reset_index(drop=True)

if not multihot_df["analysis_id"].equals(coordinates_df["analysis_id"]):
    raise ValueError("multihot rows and UMAP coordinate rows do not match.")
if not cluster_df["analysis_id"].equals(coordinates_df["analysis_id"]):
    raise ValueError("cluster rows and UMAP coordinate rows do not match.")

coordinates_df["cluster"] = cluster_df["cluster"].astype(int)

sampled_df = coordinates_df.sample(
    n=min(MAP_SAMPLE_SIZE, len(coordinates_df)),
    random_state=RANDOM_STATE,
).reset_index(drop=True)
map_points = [
    {
        "id": int(row.analysis_id),
        "cluster": int(row.cluster),
        "x": round(float(row.umap1), 6),
        "y": round(float(row.umap2), 6),
    }
    for row in sampled_df.itertuples(index=False)
]
save_json(FRONTEND_DATA_DIR / "map_points.json", {
    "sampleSize": len(map_points),
    "originalSize": len(coordinates_df),
    "samplingMethod": "simple_random",
    "randomState": RANDOM_STATE,
    "points": map_points,
})

feature_order = [column for column in multihot_df.columns if column != "analysis_id"]
category_counts = {}
for feature in feature_order:
    category = feature.split("__", 1)[0]
    category_counts[category] = category_counts.get(category, 0) + 1

categories = []
for category in CATEGORY_ORDER:
    technologies = []
    weight = 1 / math.sqrt(category_counts[category])
    for index, feature in enumerate(feature_order):
        feature_category, name = feature.split("__", 1)
        if feature_category != category:
            continue
        technologies.append({
            "index": index,
            "feature": feature,
            "name": name,
            "weight": weight,
            "overallUsageRate": round(float(multihot_df[feature].mean() * 100), 4),
        })
    technologies.sort(key=lambda item: item["name"].casefold())
    categories.append({
        "key": category,
        "label": CATEGORY_LABELS[category],
        "count": len(technologies),
        "technologies": technologies,
    })

save_json(FRONTEND_DATA_DIR / "technologies.json", {
    "total": len(feature_order),
    "thresholdPercent": 1.0,
    "categories": categories,
})

top_cluster_features_df = pd.read_csv(TOP_CLUSTER_FEATURES_PATH)
top_cluster_features_df = top_cluster_features_df[
    top_cluster_features_df["k"] == 6
]
cluster_summaries = []

for cluster_id in sorted(coordinates_df["cluster"].unique()):
    cluster_coordinates = coordinates_df[coordinates_df["cluster"] == cluster_id]
    feature_rows = top_cluster_features_df[
        top_cluster_features_df["cluster"] == cluster_id
    ].sort_values("rank").head(3)
    cluster_summaries.append({
        "id": int(cluster_id),
        "count": int(len(cluster_coordinates)),
        "rate": round(float(len(cluster_coordinates) / len(coordinates_df) * 100), 4),
        "center": {
            "x": round(float(cluster_coordinates["umap1"].mean()), 6),
            "y": round(float(cluster_coordinates["umap2"].mean()), 6),
        },
        "representativeTechnologies": feature_rows["technology"].tolist(),
    })

save_json(FRONTEND_DATA_DIR / "cluster_summary.json", {
    "count": len(cluster_summaries),
    "clusters": cluster_summaries,
})

metadata_df = pd.read_csv(METADATA_PATH).sort_values("analysis_id").reset_index(drop=True)
if not metadata_df["analysis_id"].equals(coordinates_df["analysis_id"]):
    raise ValueError("metadata rows and UMAP coordinate rows do not match.")

metadata_columns = ["DevType", "OrgSize", "Industry", "RemoteWork", "Age"]
metadata_labels = ["職種", "企業規模", "業界", "働き方", "年代"]
metadata_dictionaries = []
metadata_codes = []

for column in metadata_columns:
    values = sorted(str(value) for value in metadata_df[column].dropna().unique())
    value_to_code = {value: index for index, value in enumerate(values)}
    metadata_dictionaries.append(values)
    metadata_codes.append([
        value_to_code.get(str(value), -1) if pd.notna(value) else -1
        for value in metadata_df[column]
    ])

weights = [
    1 / math.sqrt(category_counts[feature.split("__", 1)[0]])
    for feature in feature_order
]
respondents = []

for row_index, row in multihot_df.iterrows():
    selected_features = [
        feature_index
        for feature_index, feature in enumerate(feature_order)
        if row[feature] > 0
    ]
    work_experience = metadata_df.iloc[row_index]["WorkExp"]
    respondents.append([
        selected_features,
        round(sum(weights[index] ** 2 for index in selected_features), 8),
        round(float(coordinates_df.iloc[row_index]["umap1"]), 6),
        round(float(coordinates_df.iloc[row_index]["umap2"]), 6),
        [codes[row_index] for codes in metadata_codes],
        round(float(work_experience), 2) if pd.notna(work_experience) else None,
        int(cluster_df.iloc[row_index]["cluster"]),
    ])

save_json(FRONTEND_DATA_DIR / "browser_runtime.json", {
    "featureCount": len(feature_order),
    "weights": weights,
    "metadata": [
        {
            "key": column[0].lower() + column[1:],
            "label": label,
            "values": values,
        }
        for column, label, values in zip(
            metadata_columns,
            metadata_labels,
            metadata_dictionaries,
        )
    ],
    "clusters": cluster_summaries,
    "respondents": respondents,
})

print(f"map_points.json: {len(map_points):,} points")
print(f"technologies.json: {len(feature_order)} technologies")
print(f"browser_runtime.json: {len(respondents):,} respondents")
print(f"cluster_summary.json: {len(cluster_summaries)} clusters")
