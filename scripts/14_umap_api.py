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


PROCESSED_DIR = ROOT_DIR / "data" / "processed"
UMAP_MODEL_PATH = PROCESSED_DIR / "umap" / "umap_reducer.joblib"
TECHNOLOGIES_PATH = ROOT_DIR / "public" / "data" / "technologies.json"
MODEL_PATH = ROOT_DIR / "public" / "data" / "model.json"

HOST = "127.0.0.1"
PORT = 8000


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
    model = load_json(MODEL_PATH)

    feature_count = int(model["featureCount"])
    weight_vector = np.zeros(feature_count, dtype=np.float32)

    for category in technologies["categories"]:
        for technology in category["technologies"]:
            weight_vector[int(technology["index"])] = float(technology["weight"])

    return {
        "reducer": reducer,
        "feature_count": feature_count,
        "weight_vector": weight_vector,
        "map": model.get("map", {}),
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

    return {
        "x": round(float(coordinate[0]), 6),
        "y": round(float(coordinate[1]), 6),
        "method": "UMAP.transform",
        "selectedCount": len(selected_indexes),
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
    print("Health: http://127.0.0.1:8000/api/health", flush=True)
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
