# 🛡️ infra-sentinel

![Terraform Apply](https://github.com/belzibab/infra-sentinel/actions/workflows/terraform-apply.yml/badge.svg)
![Deploy App](https://github.com/belzibab/infra-sentinel/actions/workflows/deploy-app.yml/badge.svg)
![Daily SLO Report](https://github.com/belzibab/infra-sentinel/actions/workflows/slo-report.yml/badge.svg)

> Platform reliability engineering suite built on GCP — featuring GitOps infrastructure, SLO tracking, chaos engineering, and full observability stack.

---

## 🏗️ Architecture
```
GitHub Actions (CI/CD)
        │
        ▼
  Terraform (IaC)
        │
        ▼
GCP ── VPC ── GKE Cluster
              │
              ├── FastAPI Service (2 replicas)
              │         └── /health · /metrics
              │
              ├── Prometheus (metrics + alerting)
              ├── Grafana (dashboards)
              ├── Alertmanager (Slack notifications)
              │
              └── SLO Calculator CronJob
                        └── error budget tracking
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Cloud | GCP (GKE, Cloud SQL, GCS, Artifact Registry) |
| IaC | Terraform 1.5+ with remote state on GCS |
| Orchestration | Kubernetes (Deployments, HPA, CronJobs, RBAC) |
| Containers | Docker multi-stage builds via Cloud Build |
| Observability | Prometheus + Grafana + Alertmanager |
| Language | Python 3.12 |
| CI/CD | GitHub Actions + Workload Identity Federation |
| Secrets | GCP Workload Identity (no long-lived credentials) |

---

## 📁 Project Structure
```
infra-sentinel/
├── terraform/
│   ├── modules/
│   │   ├── networking/     # VPC, subnets, secondary ranges
│   │   └── gke/            # GKE cluster + node pools
│   └── environments/
│       └── staging/        # Staging environment config
│
├── kubernetes/
│   ├── apps/
│   │   └── api-service/    # FastAPI deployment + LoadBalancer
│   └── monitoring/
│       ├── service-monitor.yaml   # Prometheus scrape config
│       └── slo-cronjob.yaml       # SLO calculator CronJob
│
├── src/
│   ├── api/                # FastAPI app with Prometheus metrics
│   └── slo_calculator/     # SLO/error budget calculator
│
└── .github/
    └── workflows/
        ├── terraform-plan.yml    # PR → terraform plan as comment
        ├── terraform-apply.yml   # merge → terraform apply
        ├── deploy-app.yml        # src changes → build + deploy
        └── slo-report.yml        # daily SLO report
```

---

## ⚙️ How It Works

### GitOps Flow
Every pull request targeting `terraform/` triggers a `terraform plan` as a PR comment. Merging to `main` automatically applies the infrastructure changes. No manual `terraform apply` needed.

### SLO Tracking
A Python CronJob runs every 5 minutes inside the cluster, querying Prometheus for real SLIs and calculating the error budget remaining. Current SLO targets:

| SLO | Target | Window |
|-----|--------|--------|
| Availability | 99.9% | 30 days |
| Error Rate | < 1% | 5 min rate |
| Latency p99 | < 500ms | 5 min rate |

### Observability
- **Prometheus** scrapes `/metrics` from the FastAPI app every 15 seconds
- **Grafana** dashboards show cluster health, node metrics, and app performance
- **Alertmanager** routes alerts to Slack based on severity

### Security
- No long-lived service account keys — uses **Workload Identity Federation**
- GKE Workload Identity enabled on all node pools
- Secrets managed via GCP Secret Manager

---

## Getting Started

### Prerequisites
- GCP account with billing enabled
- `gcloud` CLI, `terraform >= 1.5`, `kubectl`, `helm`

### Deploy
```bash
# Clone
git clone https://github.com/belzibab/infra-sentinel.git
cd infra-sentinel

# Configure
cat > terraform/environments/staging/terraform.tfvars << 'TFEOF'
project_id = "YOUR_GCP_PROJECT_ID"
region     = "us-central1"
TFEOF

# Deploy infrastructure
cd terraform/environments/staging
terraform init
terraform apply

# Connect kubectl
gcloud container clusters get-credentials infra-sentinel-staging \
  --region us-central1

# Deploy app and monitoring
kubectl apply -f kubernetes/apps/api-service/deployment.yaml
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

### Verify
```bash
# Check pods
kubectl get pods
kubectl get pods -n monitoring

# Test app
curl http://$(kubectl get svc api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')/health

# Check SLO
kubectl logs -l job-name=slo-calculator --tail=20
```

---

## SRE Practices Demonstrated

- **SLO/SLI/Error Budget** — defined and tracked automatically
- **Infrastructure as Code** — 100% of infra managed by Terraform
- **GitOps** — no manual infrastructure changes, everything via PR
- **Observability** — metrics, dashboards, and alerting configured
- **Chaos Engineering** — automated fault injection to test resilience
- **Zero-trust security** — Workload Identity, no static credentials
- **Runbooks as code** — operational procedures version-controlled

---

## 📄 License

MIT
