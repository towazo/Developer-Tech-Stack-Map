from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import sys
import traceback


ROOT_DIR = Path(__file__).resolve().parents[1]

CACHE_DIR = ROOT_DIR / ".cache"
NUMBA_CACHE_DIR = CACHE_DIR / "numba"
TMP_DIR = CACHE_DIR / "tmp"

NUMBA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("NUMBA_CACHE_DIR", str(NUMBA_CACHE_DIR))
os.environ.setdefault("TMP", str(TMP_DIR))
os.environ.setdefault("TEMP", str(TMP_DIR))

import joblib
import numpy as np
import pandas as pd


PROCESSED_DIR = ROOT_DIR / "data" / "processed"
UMAP_MODEL_PATH = PROCESSED_DIR / "umap" / "umap_reducer.joblib"
MULTIHOT_PATH = PROCESSED_DIR / "multihot_1_0pct.csv"
UMAP_COORDINATES_PATH = PROCESSED_DIR / "umap" / "umap_coordinates.csv"
TECHNOLOGIES_PATH = ROOT_DIR / "public" / "data" / "technologies.json"
METADATA_PATH = PROCESSED_DIR / "analysis_metadata.csv"

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
NEIGHBOR_COUNT = 500
METADATA_FIELDS = {
    "DevType": {"key": "devType", "label": "職種"},
    "OrgSize": {"key": "orgSize", "label": "企業規模"},
    "Industry": {"key": "industry", "label": "業界"},
    "RemoteWork": {"key": "remoteWork", "label": "働き方"},
    "Age": {"key": "age", "label": "年代"},
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_runtime():
    if not UMAP_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"UMAP model not found: {UMAP_MODEL_PATH}. "
            "Run python .\\scripts\\11_build_umap.py first."
        )

    reducer = joblib.load(UMAP_MODEL_PATH)
    technologies = load_json(TECHNOLOGIES_PATH)
    multihot_df = pd.read_csv(MULTIHOT_PATH)
    coordinates_df = pd.read_csv(UMAP_COORDINATES_PATH)
    metadata_df = pd.read_csv(METADATA_PATH)

    feature_order = [
        column for column in multihot_df.columns if column != "analysis_id"
    ]
    feature_count = len(feature_order)
    weight_vector = np.zeros(feature_count, dtype=np.float32)

    for category in technologies["categories"]:
        for technology in category["technologies"]:
            weight_vector[int(technology["index"])] = float(technology["weight"])

    if list(multihot_df.columns[1:]) != feature_order:
        raise ValueError("multihot feature order does not match technologies.json.")

    coordinates_df = coordinates_df.sort_values("analysis_id").reset_index(drop=True)
    multihot_df = multihot_df.sort_values("analysis_id").reset_index(drop=True)
    metadata_df = metadata_df.sort_values("analysis_id").reset_index(drop=True)

    if not multihot_df["analysis_id"].equals(coordinates_df["analysis_id"]):
        raise ValueError("multihot rows and UMAP coordinate rows do not match.")

    if not metadata_df["analysis_id"].equals(coordinates_df["analysis_id"]):
        raise ValueError("metadata rows and UMAP coordinate rows do not match.")

    technology_by_feature = {}
    for category in technologies["categories"]:
        for technology in category["technologies"]:
            technology_by_feature[technology["feature"]] = {
                "category": category["key"],
                "categoryLabel": category["label"],
                "name": technology["name"],
            }

    return {
        "reducer": reducer,
        "feature_count": feature_count,
        "feature_order": feature_order,
        "weight_vector": weight_vector,
        "umap_coordinates": coordinates_df[["umap1", "umap2"]].to_numpy(
            dtype=np.float32
        ),
        "multihot": multihot_df[feature_order].to_numpy(dtype=np.float32),
        "metadata": metadata_df,
        "technology_by_feature": technology_by_feature,
        "map": {
            "method": "UMAP",
            "dimensions": 2,
            "neighborBasis": "umap_2d",
            "neighborCount": NEIGHBOR_COUNT,
        },
    }


RUNTIME = load_runtime()


def make_weighted_vector(selected_indexes):
    feature_count = RUNTIME["feature_count"]
    vector = np.zeros((1, feature_count), dtype=np.float32)

    if not isinstance(selected_indexes, list):
        raise ValueError("selectedIndexes must be a list.")

    for selected_index in selected_indexes:
        if not isinstance(selected_index, int):
            raise ValueError("selectedIndexes must contain only integers.")

        if selected_index < 0 or selected_index >= feature_count:
            raise ValueError(
                f"selected index out of range: {selected_index}"
            )

        vector[0, selected_index] = RUNTIME["weight_vector"][selected_index]

    return vector


def transform_selected_indexes(selected_indexes):
    weighted_vector = make_weighted_vector(selected_indexes)
    coordinate = RUNTIME["reducer"].transform(weighted_vector)[0]
    neighborhood = find_neighborhood(coordinate)

    return {
        "x": round(float(coordinate[0]), 6),
        "y": round(float(coordinate[1]), 6),
        "method": "UMAP.transform",
        "selectedCount": len(selected_indexes),
        "neighborhood": neighborhood,
    }


def find_neighborhood(coordinate):
    center = np.array(
        [
            float(coordinate[0]),
            float(coordinate[1]),
        ],
        dtype=np.float32,
    )

    differences = RUNTIME["umap_coordinates"] - center
    squared_distances = np.einsum(
        "ij,ij->i",
        differences,
        differences,
    )
    squared_distances = np.maximum(squared_distances, 0)

    neighbor_count = min(NEIGHBOR_COUNT, len(squared_distances))
    neighbor_indexes = np.argpartition(
        squared_distances,
        neighbor_count - 1,
    )[:neighbor_count]

    neighbor_indexes = neighbor_indexes[
        np.argsort(squared_distances[neighbor_indexes])
    ]

    map_distances = np.sqrt(squared_distances[neighbor_indexes])
    statistics = calculate_neighborhood_statistics(neighbor_indexes)

    return {
        "basis": "umap_2d",
        "count": neighbor_count,
        "radius": round(float(map_distances[-1]), 6),
        "statistics": statistics,
    }


def calculate_neighborhood_statistics(neighbor_indexes):
    count = len(neighbor_indexes)
    total_count = len(RUNTIME["umap_coordinates"])
    neighborhood_multihot = RUNTIME["multihot"][neighbor_indexes]
    overall_multihot = RUNTIME["multihot"]

    neighborhood_rates = neighborhood_multihot.mean(axis=0) * 100
    overall_rates = overall_multihot.mean(axis=0) * 100
    differences = neighborhood_rates - overall_rates
    top_indexes = np.argsort(-differences)[:10]

    top_technologies = []
    for rank, feature_index in enumerate(top_indexes, start=1):
        feature = RUNTIME["feature_order"][feature_index]
        technology = RUNTIME["technology_by_feature"][feature]
        top_technologies.append(
            {
                "rank": rank,
                **technology,
                "usageRate": round(float(neighborhood_rates[feature_index]), 4),
                "overallUsageRate": round(float(overall_rates[feature_index]), 4),
                "differencePoint": round(float(differences[feature_index]), 4),
            }
        )

    neighborhood_metadata = RUNTIME["metadata"].iloc[neighbor_indexes]
    metadata_statistics = {}

    for column, config in METADATA_FIELDS.items():
        neighborhood_values = neighborhood_metadata[column].dropna()
        overall_values = RUNTIME["metadata"][column].dropna()
        neighborhood_value_rates = neighborhood_values.value_counts(normalize=True) * 100
        overall_value_rates = overall_values.value_counts(normalize=True) * 100

        items = []
        for value, usage_rate in neighborhood_value_rates.items():
            overall_rate = float(overall_value_rates.get(value, 0.0))
            items.append(
                {
                    "value": str(value),
                    "usageRate": round(float(usage_rate), 4),
                    "overallRate": round(overall_rate, 4),
                    "differencePoint": round(float(usage_rate) - overall_rate, 4),
                }
            )

        items.sort(key=lambda item: item["differencePoint"], reverse=True)
        for rank, item in enumerate(items[:3], start=1):
            item["rank"] = rank

        metadata_statistics[config["key"]] = {
            "label": config["label"],
            "answered": int(len(neighborhood_values)),
            "items": items[:3],
        }

    work_experience = pd.to_numeric(
        neighborhood_metadata["WorkExp"],
        errors="coerce",
    ).dropna()

    return {
        "count": count,
        "rate": round(count / total_count * 100, 4),
        "topTechnologies": top_technologies,
        "metadata": metadata_statistics,
        "workExperience": {
            "answered": int(len(work_experience)),
            "median": round(float(work_experience.median()), 4),
            "q1": round(float(work_experience.quantile(0.25)), 4),
            "q3": round(float(work_experience.quantile(0.75)), 4),
        },
    }


class UmapApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write("%s - %s\n" % (self.address_string(), format % args))

    def send_json(self, status_code, payload):
        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/api/health":
            self.send_json(
                200,
                {
                    "ok": True,
                    "modelLoaded": True,
                    "featureCount": RUNTIME["feature_count"],
                    "map": RUNTIME["map"],
                },
            )
            return

        self.send_json(
            404,
            {
                "ok": False,
                "error": "Not found.",
            },
        )

    def do_POST(self):
        if self.path != "/api/umap-position":
            self.send_json(
                404,
                {
                    "ok": False,
                    "error": "Not found.",
                },
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body) if body else {}

            result = transform_selected_indexes(
                payload.get("selectedIndexes")
            )

            self.send_json(
                200,
                {
                    "ok": True,
                    **result,
                },
            )
        except Exception as error:
            traceback.print_exc()
            self.send_json(
                400,
                {
                    "ok": False,
                    "error": str(error),
                },
            )


def main():
    server = ThreadingHTTPServer(
        (HOST, PORT),
        UmapApiHandler,
    )

    print("======================================", flush=True)
    print("UMAP API server started", flush=True)
    print("======================================", flush=True)
    print(f"URL: http://{HOST}:{PORT}", flush=True)
    print(f"Health: http://{HOST}:{PORT}/api/health", flush=True)
    print(flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(flush=True)
        print("Stopping UMAP API server...", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
