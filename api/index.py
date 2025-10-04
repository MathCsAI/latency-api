import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Initialize the FastAPI app
app = FastAPI()

# Enable CORS to allow POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["POST"], # Allows only POST method
    allow_headers=["*"],    # Allows all headers
)

# Load the latency data once when the application starts up
# The file is in the same 'api' directory, so the path is relative
try:
    data = pd.read_json("api/q-vercel-latency.json")
except Exception as e:
    # If the file is missing, create an empty DataFrame to avoid crashing
    data = pd.DataFrame()
    print(f"Error loading data: {e}")


# Define the structure of the incoming request body using Pydantic
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Define the main POST endpoint
@app.post("/")
def get_latency_metrics(request: LatencyRequest):
    results = {}
    if data.empty:
        return {"error": "Telemetry data not available."}

    for region in request.regions:
        # Filter the DataFrame for the current region
        region_df = data[data['region'] == region]

        if region_df.empty:
            continue

        # Calculate the required metrics
        avg_latency = region_df['latency_ms'].mean()
        p95_latency = region_df['latency_ms'].quantile(0.95)
        avg_uptime = region_df['uptime_pct'].mean()
        # Count how many records are above the user-provided threshold
        breaches = int((region_df['latency_ms'] > request.threshold_ms).sum())

        # Store the results for the region
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches,
        }

    return results
