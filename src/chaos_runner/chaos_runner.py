import random
import time
import json
import logging
from datetime import datetime
from kubernetes import client, config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChaosRunner:
    def __init__(self):
        try:
            config.load_incluster_config()
            logger.info("Running inside cluster")
        except:
            config.load_kube_config()
            logger.info("Running outside cluster")

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.results = []

    def get_target_pods(self, namespace: str = "default", label_selector: str = "app=api-service") -> list:
        pods = self.v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        return [pod.metadata.name for pod in pods.items if pod.status.phase == "Running"]

    def experiment_pod_kill(self, namespace: str = "default") -> dict:
        experiment = {
            "name": "pod-kill",
            "timestamp": datetime.utcnow().isoformat(),
            "namespace": namespace,
            "status": "unknown",
            "details": {}
        }

        pods = self.get_target_pods(namespace)
        if not pods:
            experiment["status"] = "skipped"
            experiment["details"]["reason"] = "No running pods found"
            return experiment

        target = random.choice(pods)
        logger.info(f"[pod-kill] Killing pod: {target}")

        try:
            self.v1.delete_namespaced_pod(name=target, namespace=namespace)
            experiment["details"]["killed_pod"] = target
            experiment["details"]["remaining_pods"] = [p for p in pods if p != target]

            logger.info(f"[pod-kill] Waiting 15s for recovery...")
            time.sleep(15)

            recovered_pods = self.get_target_pods(namespace)
            experiment["details"]["pods_after_recovery"] = recovered_pods
            experiment["details"]["recovered"] = len(recovered_pods) >= len(pods)
            experiment["status"] = "success" if experiment["details"]["recovered"] else "failed"

            logger.info(f"[pod-kill] Recovery: {experiment['details']['recovered']} — pods after: {recovered_pods}")

        except Exception as e:
            experiment["status"] = "error"
            experiment["details"]["error"] = str(e)
            logger.error(f"[pod-kill] Error: {e}")

        return experiment

    def experiment_scale_down(self, namespace: str = "default", deployment: str = "api-service") -> dict:
        experiment = {
            "name": "scale-down",
            "timestamp": datetime.utcnow().isoformat(),
            "namespace": namespace,
            "deployment": deployment,
            "status": "unknown",
            "details": {}
        }

        try:
            dep = self.apps_v1.read_namespaced_deployment(name=deployment, namespace=namespace)
            original_replicas = dep.spec.replicas
            experiment["details"]["original_replicas"] = original_replicas

            logger.info(f"[scale-down] Scaling {deployment} from {original_replicas} to 1")
            dep.spec.replicas = 1
            self.apps_v1.patch_namespaced_deployment(name=deployment, namespace=namespace, body=dep)

            time.sleep(10)

            logger.info(f"[scale-down] Restoring {deployment} to {original_replicas} replicas")
            dep.spec.replicas = original_replicas
            self.apps_v1.patch_namespaced_deployment(name=deployment, namespace=namespace, body=dep)

            time.sleep(15)

            recovered_pods = self.get_target_pods(namespace)
            experiment["details"]["pods_after_recovery"] = recovered_pods
            experiment["details"]["recovered"] = len(recovered_pods) >= original_replicas
            experiment["status"] = "success" if experiment["details"]["recovered"] else "degraded"

            logger.info(f"[scale-down] Recovery: {experiment['details']['recovered']}")

        except Exception as e:
            experiment["status"] = "error"
            experiment["details"]["error"] = str(e)
            logger.error(f"[scale-down] Error: {e}")

        return experiment

    def run_random_experiment(self, namespace: str = "default") -> dict:
        experiments = [
            self.experiment_pod_kill,
            self.experiment_scale_down,
        ]
        chosen = random.choice(experiments)
        logger.info(f"Running experiment: {chosen.__name__}")
        return chosen(namespace=namespace)

    def generate_report(self, results: list) -> dict:
        total = len(results)
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] in ["failed", "error"]])

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_experiments": total,
                "successful": successful,
                "failed": failed,
                "resilience_score": round((successful / total * 100), 1) if total > 0 else 0
            },
            "experiments": results
        }


if __name__ == "__main__":
    runner = ChaosRunner()

    logger.info("=== CHAOS ENGINEERING SESSION STARTED ===")

    results = []
    for i in range(2):
        logger.info(f"\n--- Experiment {i+1}/2 ---")
        result = runner.run_random_experiment(namespace="default")
        results.append(result)
        time.sleep(5)

    report = runner.generate_report(results)

    print("\n=== CHAOS REPORT ===")
    print(json.dumps(report, indent=2))

    score = report["summary"]["resilience_score"]
    if score == 100:
        print("\n✅ System is highly resilient")
    elif score >= 50:
        print("\n⚠️  System has partial resilience — review failed experiments")
    else:
        print("\n🔥 System resilience is low — immediate action required")
