from fastapi import FastAPI 
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response 

app = FastAPI(title="infra-sentinel-api")

REQUEST_COUNT = Counter(
    "app_request_total",
    "Total request",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency",
    ["endpoint"]
)

@app.get("/")
def root():
    REQUEST_COUNT.labels("GET", "/", "200").inc()
    return {"status": "ok", "service": "infra-sentinel"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
    
