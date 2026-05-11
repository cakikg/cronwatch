# cronwatch

Lightweight daemon that monitors cron job execution times and sends alerts on failures or overruns.

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/cronwatch.git && cd cronwatch && pip install .
```

## Usage

Add a `cronwatch.yaml` config file to define the jobs you want to monitor:

```yaml
jobs:
  nightly-backup:
    schedule: "0 2 * * *"
    max_duration: 3600   # seconds
    alert_on: [failure, overrun]
    notify:
      email: ops@example.com

  data-sync:
    schedule: "*/15 * * * *"
    max_duration: 120
    notify:
      slack_webhook: https://hooks.slack.com/services/xxx/yyy/zzz
```

Start the daemon:

```bash
cronwatch start --config cronwatch.yaml
```

Wrap an existing cron command to report its status:

```bash
# In your crontab
* * * * * cronwatch run --job data-sync -- /usr/local/bin/sync.sh
```

Check daemon status:

```bash
cronwatch status
```

## Configuration

| Field | Description | Default |
|---|---|---|
| `schedule` | Cron expression for expected run time | required |
| `max_duration` | Maximum allowed runtime in seconds | `3600` |
| `alert_on` | Trigger conditions: `failure`, `overrun`, `missed` | `[failure]` |

## License

MIT © 2024 cronwatch contributors