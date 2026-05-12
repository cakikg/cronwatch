"""Configuration loader for cronwatch.

Supports YAML config files defining monitored cron jobs,
their expected runtimes, and alert thresholds.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class JobConfig:
    name: str
    schedule: str
    timeout: int  # seconds before considered overrun
    alert_email: Optional[str] = None
    max_retries: int = 0
    tags: list = field(default_factory=list)


@dataclass
class CronwatchConfig:
    jobs: list[JobConfig] = field(default_factory=list)
    log_file: str = "/var/log/cronwatch.log"
    smtp_host: str = "localhost"
    smtp_port: int = 25
    default_alert_email: Optional[str] = None


def load_config(path: str) -> CronwatchConfig:
    """Load and parse a YAML configuration file.

    Args:
        path: Path to the YAML config file.

    Returns:
        A populated CronwatchConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is malformed or missing required fields.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError("Config file must be a YAML mapping.")

    jobs = []
    for job_data in raw.get("jobs", []):
        if "name" not in job_data:
            raise ValueError("Each job must have a 'name' field.")
        if "schedule" not in job_data:
            raise ValueError(f"Job '{job_data['name']}' is missing 'schedule'.")
        if "timeout" not in job_data:
            raise ValueError(f"Job '{job_data['name']}' is missing 'timeout'.")

        jobs.append(JobConfig(
            name=job_data["name"],
            schedule=job_data["schedule"],
            timeout=int(job_data["timeout"]),
            alert_email=job_data.get("alert_email"),
            max_retries=int(job_data.get("max_retries", 0)),
            tags=job_data.get("tags", []),
        ))

    return CronwatchConfig(
        jobs=jobs,
        log_file=raw.get("log_file", "/var/log/cronwatch.log"),
        smtp_host=raw.get("smtp_host", "localhost"),
        smtp_port=int(raw.get("smtp_port", 25)),
        default_alert_email=raw.get("default_alert_email"),
    )
