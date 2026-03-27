import requests
import json
from datetime import datetime

PROMETHEUS_URL = "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"

SLO_TARGETS = {
        "availability": 99.9, #99.9% uptime
        "latency_p99":0.5,    #500ms max p99
        "error_rate":1.0 #max 1% errors
}

def query_prometheus(query: str) -> float:
    try:
        response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
                timeout=10
                )
        data = response.json()
        if data["data"]["result"]:
            return float(data["data"]["result"][0]["value"][1])
        return 0.0
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return 0.0

def calculate_availability() -> dict:
    total = query_prometheus('sum(app_requests_total)')
    errors = query_prometheus('sum(app_requests_total{status=~"5.."})')

    if total == 0:
        availability = 100.0
    else:
        availability = ((total - errors) / total) *100

    target = SLO_TARGETS["availability"]
    error_budget_total = 100 - target
    error_budget_used = max(0, (100 - availability))
    error_budget_remaining = max(0, error_budget_total - error_budget-used)

    return {
        "sli": round(error_rate, 4),
        "target": target,
        "status": "OK" if error_rate <= target else "BURNING"
    }

def generate_report() -> dict:
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "infra-sentinel-api",
        "slos": {
            "availability": calculate_availability(),
            "error_rate": calculate_error_rate()
        }
    }
    return report

if __name__ == "__main__":
    report = generate_report()
    print(json.dumps(report, indent=2))

    print("\n=== SLO REPORT ===")
    for slo_name, data in report["slos"].items():
        status_icon = "✅" if data["status"] == "OK" else "🔥"
        print(f"{status_icon} {slo_name.upper()}: {data['sli']} (target: {data['target']})")
        if "error_budget_remaining_pct" in data:
            print(f" Error budget remaining: {data['error_budget_remaining_pct']}%")

