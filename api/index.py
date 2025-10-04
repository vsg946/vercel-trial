import pandas as pd
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Union
from fastapi.middleware.cors import CORSMiddleware

# --- 1. Define Request/Response Models ---

# Defines the expected input JSON structure
class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: int

# Defines the structure of the metrics returned for a single region
class RegionMetrics(BaseModel):
    region: str
    avg_latency: float
    p95_latency: float
    avg_uptime: float
    breaches: int

# --- 2. Initialize FastAPI and Data ---

app = FastAPI()

# --- MOCK DATA GENERATION ---
# NOTE: Replace this section with code to load your actual 'telemetry bundle' data.
# For demonstration, we create a DataFrame with latency and region data.
def generate_mock_data():
    np.random.seed(42)
    data = {
        'region': np.random.choice(['emea', 'apac', 'na', 'latam'], size=1000),
        'latency_ms': np.concatenate([
            np.random.normal(loc=150, scale=20, size=500), # emea/apac
            np.random.normal(loc=120, scale=15, size=500)  # na/latam
        ])
    }
    # Ensure latency is positive and convert to integers for realism
    data['latency_ms'] = np.maximum(0, data['latency_ms']).astype(int)
    return pd.DataFrame(data)

# Load the mock data once when the server starts
df_telemetry = generate_mock_data()
# -----------------------------

# --- 3. CORS Configuration ---
# Enables POST requests from any dashboard origin (*)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# --- 4. Metric Calculation Function ---

def get_region_metrics(region_data: pd.DataFrame, region_name: str, threshold: int) -> RegionMetrics:
    """Calculates all required metrics for a single region's DataFrame."""
    
    if region_data.empty:
        return RegionMetrics(
            region=region_name,
            avg_latency=0.0,
            p95_latency=0.0,
            avg_uptime=1.0, # Assume 100% uptime if no data
            breaches=0
        )

    latencies = region_data['latency_ms']
    
    # Calculate required metrics
    avg_latency = latencies.mean()
    p95_latency = np.percentile(latencies, 95)
    breaches = (latencies > threshold).sum()
    
    # Uptime: Since the source data is 'latency pings', we assume a successful
    # ping implies the service was 'up' for that record. We set avg_uptime = 1.0 (100%).
    avg_uptime = 1.0 
    
    return RegionMetrics(
        region=region_name,
        avg_latency=round(avg_latency, 2),
        p95_latency=round(p95_latency, 2),
        avg_uptime=avg_uptime,
        breaches=int(breaches)
    )

# --- 5. The POST Endpoint ---

@app.post("/", response_model=List[RegionMetrics])
async def get_dashboard_metrics(body: RequestBody) -> List[RegionMetrics]:
    """Accepts regions and a threshold, returns per-region metrics."""
    
    results = []
    
    for region in body.regions:
        # Filter the global data for the current region
        region_data = df_telemetry[df_telemetry['region'] == region]
        
        # Calculate metrics for the filtered data
        metrics = get_region_metrics(region_data, region, body.threshold_ms)
        results.append(metrics)
        
    return results

# --- Example Response Verification ---
# When testing with {"regions":["emea","apac"],"threshold_ms":159} against the mock data,
# the output will be deterministic due to the seed (np.random.seed(42)).
# Example expected metrics (approximate due to floats):
# emea: avg_latency ~ 149, p95_latency ~ 180, breaches ~ 190
# apac: avg_latency ~ 149, p95_latency ~ 180, breaches ~ 190
