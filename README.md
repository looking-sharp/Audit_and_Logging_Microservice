# Audit and Logging Microservice

Microservice Communication Contract

## Implementation Status

- **POST /log** - PENDING
- **GET /logs**  - PENDING 
- **POST /purge-logs** - IMPLEMENTED

## Setup

```bash
git clone https://github.com/looking-sharp/Audit_and_Logging_Microservice
cd Audit_and_Logging_Microservice
pip install -r requirements.txt
python app.py
```

Service runs on `http://localhost:5000`

---

## ENDPOINTS

### 1. Record User Actions (PENDING)

**Endpoint:** `POST /log`

**Purpose:** Record user and system actions for audit trail

**Request:** *(To be implemented)*

**Response:** *(To be implemented)*

### 2. Retrieve Audit Logs (PENDING)

**Endpoint:** `GET /logs`

**Purpose:** Query audit logs with filters for compliance analysis

**Request:** *(To be implemented)*

**Response:** *(To be implemented)*

### 3. Purge Audit Logs (IMPLEMENTED)

**Endpoint:** `POST /purge-logs`

**Authentication:** Bearer token required

**Request:**
```
POST http://localhost:5000/purge-logs
Authorization: Bearer secret-admin-key
Content-Type: application/json

{
  "admin_user": "admin@company.com",
  "criteria": {
    "older_than_days": 90
  }
}
```

**Criteria Options:**
- `{"older_than_days": 90}` - Delete logs older than X days
- `{"service": "ServiceName"}` - Delete logs from specific service
- `{"delete_all": true}` - Delete all logs

**Response:**

```json
{
  "status": "accepted",
  "message": "Purge process initiated"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key or user
- 400 Bad Request: Missing or invalid criteria

**Detailed Error Responses:**

401 Unauthorized - Missing Authorization:
```json
{"error": "Missing or invalid Authorization header"}
```

401 Unauthorized - Invalid User:
```json
{"error": "Unauthorized user"}
```

400 Bad Request - Missing Criteria:
```json
{"error": "Missing purge criteria"}
```

## UML SEQUENCE DIAGRAM
Pending

## Configuration

Environment Variables:
- `ADMIN_API_KEY`: Authentication key (default: "secret-admin-key")
- `RETENTION_DAYS`: Auto-purge retention period (default: 1095 days = 3 years)
- `PURGE_TIME`: Daily purge time in HH:MM format (default: "02:00" UTC)
- `MONGO_URI`: Database connection string (default: "mongodb://localhost:27017/")

## Testing

```bash
python test_purge.py
```

Tests cover purge validation, authentication, error handling, and MongoDB operations (mocked for speed).

## Dependencies

```
Flask==2.3.3
pymongo==4.6.0
schedule==1.2.0
```

## DEPLOYMENT STATUS

| Feature | Status | Implementation |
|---------|--------|----------------|
| **POST /log** | **PENDING** | Pending |
| **GET /logs** | **PENDING** | Pending |  
| **POST /purge-logs** | **COMPLETE** | Implemented |
| **Daily Auto-Purge** | **COMPLETE** | Runs automatically at 2 AM UTC |

---
