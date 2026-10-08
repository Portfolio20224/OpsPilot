import os


class Settings:
    app_name: str = os.getenv(
        "OPSPILOT_APP_NAME",
        "OpsPilot",
    )

    api_host: str = os.getenv(
        "OPSPILOT_API_HOST",
        "0.0.0.0",
    )

    api_port: int = int(
        os.getenv(
            "OPSPILOT_API_PORT",
            "8000",
        )
    )

    incident_data_path: str = os.getenv(
        "OPSPILOT_INCIDENT_DATA_PATH",
        "acmepay_dataset/incidents.json",
    )

    deployment_data_path: str = os.getenv(
        "OPSPILOT_DEPLOYMENT_DATA_PATH",
        "acmepay_dataset/deployments.json",
    )

    analysis_history_path: str = os.getenv(
        "OPSPILOT_ANALYSIS_HISTORY_PATH",
        "acmepay_dataset/analysis_history.json",
    )

    gemini_model: str = os.getenv(
        "OPSPILOT_GEMINI_MODEL",
        "gemini-3.5-flash",
    )


settings = Settings()