# Audit and Logging Microservice

Centralized audit logging for compliance, security monitoring, and system debugging across multiple services.

## Features

- **User Actions Record** *(pending)*: Centralized logging of all user and system actions
- **Filter Audit Logs** *(pending)*: Query logs with filters for compliance analysis  
- **User Log Purge** *(implemented)*: Automated daily purging with 3-year retention and manual admin controls

## Setup

**Prerequisites:** Python 3.8+, MongoDB, pip

```bash
git clone <repository-url>
cd Audit_and_Logging_Microservice
pip install -r requirements.txt
python app.py
```

Service runs on `http://localhost:5000` with automatic daily purging enabled.

## API Endpoints

### POST /log *(pending)*
Records audit log entries. Requires: `service`, `action`, `level`. Optional: `user_id`, `details`.

### GET /logs *(pending)*  
Retrieves logs with filtering by service, user_id, level, action, date range. Supports pagination.

### POST /purge-logs *(implemented)*
Admin-only purging. Requires `Authorization: Bearer <ADMIN_API_KEY>`. 
Criteria: `delete_all`, `older_than_days`, or `service`. Returns `202 Accepted`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_API_KEY` | `secret-admin-key` | API key for purge operations |
| `RETENTION_DAYS` | `1095` | Data retention period (3 years) |
| `PURGE_TIME` | `02:00` | Daily auto-purge time (HH:MM UTC) |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |

## Dependencies

Flask 2.3.3, pymongo 4.6.0, schedule 1.2.0

## Testing

```bash
python test_purge.py
python -c "from app import app; print('App loads successfully')"
```

**Features**: Daily auto-purging, concurrent processing, graceful MongoDB degradation, <1s response time for 1000 logs, API key authentication.
