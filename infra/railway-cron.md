# Railway Cron Configuration

Configure in Railway dashboard for the API service:

- **Cron Schedule:** `0 9 * * *` (9am UTC daily)
- **Command:** `curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" $INTERNAL_API_URL/digest/run`

Where:
- `ADMIN_TOKEN` is the env var on the API service
- `INTERNAL_API_URL` is the internal Railway URL (e.g. `http://localhost:8000`) since cron runs in the same service

Alternatively, deploy a separate "cron" service that just runs the curl on schedule and points at the public API URL.
