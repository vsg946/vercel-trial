from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Define Request Body (still needed for POST method)
class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: int

# CORS configuration (still needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# --- 5. The POST Endpoint (MODIFIED) ---
@app.post("/")
async def get_dashboard_metrics(body: RequestBody):
    # TEMPORARY: Return a simple success message
    return {"status": "OK", "message": "Framework is alive!"}

# IMPORTANT: DO NOT run Pandas/NumPy code here for now
# df_telemetry = generate_mock_data()
