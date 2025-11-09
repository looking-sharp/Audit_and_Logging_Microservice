# Audit and Logging Microservice

Microservice Communication Contract

## Implementation Status

- **POST /log** - IMPLEMENTED
- **GET /logs**  - IMPLEMENTED
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

### 1. Record User Actions (IMPLEMENTED)

**Endpoint:** `POST /log`

**Purpose:** Record user and system actions for audit trail

**Request:** 
```
*POST http://localhost:5000/log
Content-Type: application/json

{
  "service": "Auth",
  "user_id": "user123",
  "action": "login",
  "level": "INFO",
  "details": "User successfully logged in"
}
```
**Response:** 
```
HTTP 201 Created
{
  "status": "success",
  "id": "654f8a1c28b9f0a0b2d4e321"
}
```
**Error Response:**
```
HTTP 400 Bad Request
{
  "error": "Missing required fields: service, action, level"
}

HTTP 500 Internal Server Error
{
  "error": "Database unavailable"
}

```

### 2. Retrieve Audit Logs (IMPLEMENTED)

**Endpoint:** `GET /logs`

**Purpose:** Query audit logs with filters for compliance analysis

**Request:** 
```
GET http://localhost:5000/logs?service=Auth&level=INFO&limit=50
```

**Response:**
```
HTTP 200 OK
{
  "logs": [
    {
      "_id": "654f8b9d1f4aef010fbf71a4",
      "timestamp": "2025-11-08T10:30:00Z",
      "service": "Auth",
      "user_id": "user123",
      "action": "login",
      "level": "INFO",
      "details": "User successfully logged in"
    },
    {
      "_id": "654f8b9d1f4aef010fbf71a5",
      "timestamp": "2025-11-08T10:45:00Z",
      "service": "Training",
      "user_id": "trainer42",
      "action": "create",
      "level": "WARNING",
      "details": "Attempted to upload unsupported file type"
    }
  ],
  "total": 1500,
  "filtered": 25,
  "chronological_order": true
}
```
**Error Response:**
```
HTTP 400 Bad Request
{
  "error": "Invalid start_date format (expected YYYY-MM-DD)"
}
HTTP 500 Internal Server Error
{
  "error": "Failed to retrieve logs"
}
```

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
<img width="812" height="708" alt="image" src="https://github.com/user-attachments/assets/d46f5112-4404-4396-95d7-f52bc4879479" />

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
| **POST /log** | **COMPLETE** | Implemented |
| **GET /logs** | **COMPLETE** | Implemented |  
| **POST /purge-logs** | **COMPLETE** | Implemented |
| **Daily Auto-Purge** | **COMPLETE** | Runs automatically at 2 AM UTC |

---
