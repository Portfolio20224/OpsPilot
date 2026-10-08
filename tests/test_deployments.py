from app.repositories.deployments import DeploymentRepository


def test_load_deployments():

    repository = DeploymentRepository(
        "acmepay_dataset/deployments.json"
    )

    deployments = repository.get_all()

    assert len(deployments) > 0


def test_get_by_service():

    repository = DeploymentRepository(
        "acmepay_dataset/deployments.json"
    )

    deployments = repository.get_by_service(
        "payment-api"
    )

    assert len(deployments) > 0

    assert all(
        deployment.service == "payment-api"
        for deployment in deployments
    )