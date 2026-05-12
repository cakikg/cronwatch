"""Tests for cronwatch configuration loading."""

import textwrap
import pytest

from cronwatch.config import load_config, CronwatchConfig, JobConfig


@pytest.fixture
def valid_config_file(tmp_path):
    content = textwrap.dedent("""
        log_file: /tmp/cronwatch.log
        smtp_host: mail.example.com
        smtp_port: 587
        default_alert_email: ops@example.com

        jobs:
          - name: daily_backup
            schedule: "0 2 * * *"
            timeout: 3600
            alert_email: backup@example.com
            max_retries: 2
            tags: [backup, storage]

          - name: hourly_sync
            schedule: "0 * * * *"
            timeout: 300
    """)
    config_path = tmp_path / "cronwatch.yml"
    config_path.write_text(content)
    return str(config_path)


def test_load_valid_config(valid_config_file):
    config = load_config(valid_config_file)
    assert isinstance(config, CronwatchConfig)
    assert config.log_file == "/tmp/cronwatch.log"
    assert config.smtp_host == "mail.example.com"
    assert config.smtp_port == 587
    assert config.default_alert_email == "ops@example.com"


def test_load_jobs(valid_config_file):
    config = load_config(valid_config_file)
    assert len(config.jobs) == 2

    backup = config.jobs[0]
    assert isinstance(backup, JobConfig)
    assert backup.name == "daily_backup"
    assert backup.schedule == "0 2 * * *"
    assert backup.timeout == 3600
    assert backup.alert_email == "backup@example.com"
    assert backup.max_retries == 2
    assert backup.tags == ["backup", "storage"]

    sync = config.jobs[1]
    assert sync.name == "hourly_sync"
    assert sync.max_retries == 0
    assert sync.tags == []


def test_file_not_found():
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config("/nonexistent/path/cronwatch.yml")


def test_missing_name_raises(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("jobs:\n  - schedule: '* * * * *'\n    timeout: 60\n")
    with pytest.raises(ValueError, match="must have a 'name'"):
        load_config(str(bad))


def test_missing_timeout_raises(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("jobs:\n  - name: myjob\n    schedule: '* * * * *'\n")
    with pytest.raises(ValueError, match="missing 'timeout'"):
        load_config(str(bad))


def test_empty_jobs(tmp_path):
    cfg = tmp_path / "empty.yml"
    cfg.write_text("jobs: []\n")
    config = load_config(str(cfg))
    assert config.jobs == []
