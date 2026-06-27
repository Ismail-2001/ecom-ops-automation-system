from locust import HttpUser, task, between, tag
import json
import uuid

API_KEY = "opsiq-dev-key-2024"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


class OpsIQUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.client.headers.update(HEADERS)

    @tag("health")
    @task(2)
    def health_check(self):
        self.client.get("/health")

    @tag("approvals")
    @task(5)
    def get_approvals(self):
        self.client.get("/api/approvals?status=pending")

    @tag("analytics")
    @task(3)
    def get_analytics(self):
        self.client.get("/api/analytics")

    @tag("agents")
    @task(3)
    def get_agent_status(self):
        self.client.get("/api/agents/status")

    @tag("audit")
    @task(2)
    def get_audit_logs(self):
        self.client.get("/api/audit?page=1&limit=20")

    @tag("settings")
    @task(1)
    def get_settings(self):
        self.client.get("/api/settings")

    @tag("run")
    @task(1)
    def trigger_pipeline(self):
        self.client.post("/api/run")

    @tag("metrics")
    @task(1)
    def get_metrics(self):
        self.client.get("/metrics")


class OpsIQApprovalUser(HttpUser):
    wait_time = between(2, 5)

    def on_start(self):
        self.client.headers.update(HEADERS)

    @tag("approve")
    @task(1)
    def approve_action(self):
        resp = self.client.get("/api/approvals?status=pending&risk_level=low")
        if resp.status_code == 200:
            actions = resp.json()
            for action in actions:
                self.client.post(f"/api/approvals/{action['id']}/approve", json={})

    @tag("audit_export")
    @task(1)
    def export_csv(self):
        self.client.get("/api/audit/export?format=csv")
