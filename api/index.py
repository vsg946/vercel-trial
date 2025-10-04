import json
import pandas as pd
import numpy as np
from pathlib import Path
from http.server import BaseHTTPRequestHandler

DATA_FILE = Path(__file__).parent.parent / "data" / "q-vercel-latency.json"
df = pd.read_json(DATA_FILE)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"message": "Vercel Latency Analytics API is running."}')

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        payload = json.loads(body)

        regions_to_process = payload.get("regions", [])
        threshold = payload.get("threshold_ms", 200)

        results = []
        for region in regions_to_process:
            region_df = df[df["region"] == region]
            if not region_df.empty:
                avg_latency = round(region_df["latency_ms"].mean(), 2)
                p95_latency = round(np.percentile(region_df["latency_ms"], 95), 2)
                avg_uptime = round(region_df["uptime_pct"].mean(), 3)
                breaches = int(region_df[region_df["latency_ms"] > threshold].shape[0])

                results.append({
                    "region": region,
                    "avg_latency": avg_latency,
                    "p95_latency": p95_latency,
                    "avg_uptime": avg_uptime,
                    "breaches": breaches,
                })

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"regions": results}).encode("utf-8"))
