import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import the CORS middleware
from pydantic import BaseModel
from typing import List

# Initialize the FastAPI app
app = FastAPI()

# 👇 THIS BLOCK FIXES THE CORS ERROR
# It adds headers to the response that tell browsers it's safe
# to allow requests from any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

try:
    data = pd.read_json("api/q-vercel-latency.json")
except Exception:
    data = pd.DataFrame()

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# 👇 THIS DECORATOR FIXES THE "METHOD NOT ALLOWED" ERROR
# It specifically tells FastAPI to route POST requests to the root path ("/")
# to this function. GET requests will be rejected.
@app.post("/")
def get_latency_metrics(request: LatencyRequest):
    results = {}
    if data.empty:
        return {"error": "Telemetry data not available."}

    for region in request.regions:
        region_df = data[data['region'] == region]

        if region_df.empty:
            continue

        avg_latency = region_df['latency_ms'].mean()
        p95_latency = region_df['latency_ms'].quantile(0.95)
        avg_uptime = region_df['uptime_pct'].mean()
        breaches = int((region_df['latency_ms'] > request.threshold_ms).sum())

        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches,
        }

    return results
