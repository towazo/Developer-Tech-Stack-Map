from pathlib import Path
import json
import math

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
FRONTEND_DATA_DIR = ROOT_DIR / "public" / "data"
MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
UMAP_COORDINATES_PATH = PROCESSED_DIR / "umap" / "umap_coordinates.csv"

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

if not multihot_df["analysis_id"].equals(coordinates_df["analysis_id"]):
    raise ValueError("multihot rows and UMAP coordinate rows do not match.")

sampled_df = coordinates_df.sample(
    n=min(MAP_SAMPLE_SIZE, len(coordinates_df)),
    random_state=RANDOM_STATE,
).reset_index(drop=True)
map_points = [
    {
        "id": int(row.analysis_id),
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

print(f"map_points.json: {len(map_points):,} points")
print(f"technologies.json: {len(feature_order)} technologies")
