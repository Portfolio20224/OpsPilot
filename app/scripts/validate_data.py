import json
from pathlib import Path

from app.models.schemas import Incident, Deployment


incidents_path = Path("acmepay_dataset/incidents.json")
deployments_path = Path("acmepay_dataset/deployments.json")

with incidents_path.open() as f:
    raw_incidents = json.load(f)

incidents = [Incident.model_validate(item) for item in raw_incidents]

print(f"Loaded {len(incidents)} incidents")

for incident in incidents[:3]:
    print(
        incident.id,
        incident.service,
        incident.severity,
        incident.timestamp,
    )
with deployments_path.open() as f:
    raw_deployments = json.load(f)

deployments = [Deployment.model_validate(item) for item in raw_deployments]

print(f"Loaded {len(deployments)} incidents")

for deployment in deployments[:3]:
    print(
        deployment.id,
        deployment.service,
        deployment.previous_version,
        deployment.status,
    )