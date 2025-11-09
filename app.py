"""
Audit and Logging Microservice

Implements three core user stories:

1. USER ACTIONS RECORD (POST /log - Tiffany's implementation required)
   - Records all user and service actions (login, data updates, API calls) in centralized audit log
   - Enables system administrators to trace activity, monitor usage, investigate security issues
   - Accepts service, user_id, action, level, details with automatic UTC timestamping
   - Stores persistently in MongoDB with success confirmation
   - Handles logs from multiple microservices (Auth, Training, Procedures) concurrently

2. FILTER AUDIT LOGS (GET /logs - Tiffany's implementation required)
   - Enables compliance administrators to query logs with filters
   - Supports filtering by service name, user ID, log level for compliance analysis
   - Returns logs in chronological order with full event details
   - Handles missing filters gracefully (returns all logs when none specified)
   - Performance target: <1 second response for 1,000 logs

3. USER LOG PURGE (POST /purge-logs - implemented)
   - Automated daily purging respecting 3-year data retention requirement
   - Admin-only manual purge with flexible criteria (delete_all, older_than_days, service)
   - Secure authentication with API key validation
   - Asynchronous processing with 202 Accepted response

Configuration via environment variables:
- RETENTION_DAYS: Data retention period in days (default: 1095 = 3 years)
- PURGE_TIME: Daily automated purge time HH:MM (default: 02:00 UTC)
- ADMIN_API_KEY: Authentication key for purge operations
- MONGO_URI: MongoDB connection string
"""

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os
import threading
import schedule
import time
from functools import wraps

class Config:
    ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'secret-admin-key')
    ADMIN_USERS = ['admin@company.com', 'sysadmin@company.com']
    RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '1095'))
    PURGE_TIME = os.getenv('PURGE_TIME', '02:00')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

app = Flask(__name__)

try:
    from pymongo import MongoClient
    client = MongoClient(Config.MONGO_URI)
    db = client.audit_logs
    logs = db.logs
    print("Connected to MongoDB")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    logs = None

def require_admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        if token != Config.ADMIN_API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

class PurgeManager:
    """Centralized purge logic for both automatic and manual operations"""
    
    @staticmethod
    def execute_purge(criteria, admin_user=None, is_automatic=False):
        """Execute purge based on criteria - handles both manual and automatic purges"""
        if logs is None:
            return 0
        
        # Build MongoDB query based on criteria
        if criteria.get('delete_all'):
            query = {}
            purge_type = "all logs"
        elif 'older_than_days' in criteria:
            cutoff = datetime.utcnow() - timedelta(days=criteria['older_than_days'])
            query = {"timestamp": {"$lt": cutoff.isoformat()}}
            purge_type = f"logs older than {criteria['older_than_days']} days"
        elif 'service' in criteria:
            query = {"service": criteria['service']}
            purge_type = f"logs from service '{criteria['service']}'"
        else:
            return 0
        
        # Execute purge
        result = logs.delete_many(query)
        count = result.deleted_count
        
        # Log purge results
        if is_automatic:
            print(f"Automatic daily purge: {count} records deleted ({purge_type})")
        elif admin_user:
            print(f"Manual admin purge by {admin_user}: {count} records deleted ({purge_type})")
        else:
            print(f"Purge completed: {count} records deleted ({purge_type})")
        
        return count
    
    @staticmethod
    def get_automatic_criteria():
        """Get criteria for automatic daily purge (3-year retention)"""
        return {"older_than_days": Config.RETENTION_DAYS}
    
    @staticmethod
    def validate_manual_criteria(criteria):
        """Validate manual purge criteria"""
        if not criteria:
            return False, "Missing purge criteria"
        
        valid_keys = ['delete_all', 'older_than_days', 'service']
        has_valid_key = any(key in criteria for key in valid_keys)
        
        if not has_valid_key:
            return False, "Invalid purge criteria. Must specify one of: delete_all, older_than_days, service"
        
        return True, None

def daily_purge():
    """Daily automatic purge job - uses centralized PurgeManager"""
    criteria = PurgeManager.get_automatic_criteria()
    PurgeManager.execute_purge(criteria, is_automatic=True)

schedule.every().day.at(Config.PURGE_TIME).do(daily_purge)

def run_scheduler():
    """Background thread for scheduled tasks"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# USER STORY 1: User Actions Record - Tiffany's Implementation Required
@app.route('/log', methods=['POST'])
def create_log():
    """
    Records user and service actions in centralized audit log
    
    ACCEPTANCE CRITERIA:
    - Accept POST /log with service, user_id, action, level, details
    - Auto-timestamp with UTC time
    - Store persistently in MongoDB
    - Return {"status": "success"} confirmation on successful storage
    - Return descriptive error for missing/invalid required fields
    - Handle concurrent logs from multiple microservices (Auth, Training, Procedures)
    
    FUNCTIONAL REQUIREMENT:
    Given: microservice needs to record an event
    When: sends valid POST /log with service, action, level
    Then: store log with UTC timestamp and respond 200 {"status": "success"}
    
    Required Fields: service, action, level
    Optional Fields: user_id, details
    
    Expected Request:
    {
        "service": "Auth|Training|Procedures|etc",
        "user_id": "user123" (optional),
        "action": "login|logout|create|update|delete|api_call", 
        "level": "INFO|WARNING|ERROR",
        "details": "Human readable description" (optional)
    }
    
    Success Response: 200 OK {"status": "success"}
    Error Response: 400 Bad Request with descriptive message
    """
    return jsonify({"status": "success"}), 201

# USER STORY 2: Filter Audit Logs - Partner Implementation Required
@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Enables compliance administrators to query audit logs with filters
    
    ACCEPTANCE CRITERIA:
    - GET /logs returns JSON list of log entries
    - Query parameters allow filtering by service, level, user_id
    - Logs returned in chronological order by default
    - Each entry includes timestamp, service, user_id, action, level, details
    - Responds within <1 second for 1,000 logs (performance requirement)
    - Handles missing filters gracefully (returns all logs when none specified)
    
    FUNCTIONAL REQUIREMENT:
    Given: multiple logs stored from different microservices
    When: user sends GET /logs with no query parameters
    Then: return all stored logs in chronological order with full details
    
    Query Parameters (all optional):
    - service: Filter by microservice name (e.g., "Auth", "Training")
    - level: Filter by log level ("INFO", "WARNING", "ERROR")
    - user_id: Filter by specific user ID
    - action: Filter by action type
    - start_date: Filter from date (ISO format YYYY-MM-DD)
    - end_date: Filter to date (ISO format YYYY-MM-DD)
    - limit: Max results (default: 100, max: 1000)
    - offset: Pagination offset (default: 0)
    
    Success Response: 200 OK
    {
        "logs": [
            {
                "_id": "mongodb_object_id",
                "timestamp": "2025-11-08T10:30:00Z",
                "service": "Auth",
                "user_id": "user123",
                "action": "login",
                "level": "INFO",
                "details": "User successfully logged in"
            }
        ],
        "total": 1500,
        "filtered": 25,
        "chronological_order": true
    }
    """
    return jsonify({"logs": []}), 200

@app.route('/purge-logs', methods=['POST'])
@require_admin_auth
def purge_logs():
    """
    USER STORY 3: User Log Purge
    
    Supports 3-year data retention requirement with automated and manual purge capabilities.
    Enables system administrators to manage log storage and comply with data governance.
    
    IMPLEMENTED FEATURES:
    - Automated daily purging of logs older than retention period (configurable, default 3 years)
    - Manual admin purge with flexible criteria (delete_all, older_than_days, service-specific)
    - Secure admin authentication with API key and user validation
    - Asynchronous processing with 202 Accepted response (non-blocking)
    - Background scheduler for automated daily maintenance
    
    Authentication Required:
    - Authorization: Bearer {ADMIN_API_KEY}
    - admin_user must be in authorized admin list
    
    Request Body - Purge Criteria (one required):
    {
        "admin_user": "admin@company.com",
        "criteria": {
            "delete_all": true  OR
            "older_than_days": 90  OR
            "service": "OldService"
        }
    }
    
    Response: 202 Accepted {"status": "accepted", "message": "Purge process initiated"}
    """
    if logs is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    # Validate body parameters
    admin_user = request.json.get('admin_user')
    if admin_user not in Config.ADMIN_USERS:
        return jsonify({"error": "Unauthorized user"}), 401
    
    criteria = request.json.get('criteria', {})
    is_valid, error_msg = PurgeManager.validate_manual_criteria(criteria)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    def async_purge():
        PurgeManager.execute_purge(criteria, admin_user=admin_user)
    
    threading.Thread(target=async_purge, daemon=True).start()
    
    return jsonify({
        "status": "accepted",
        "message": "Purge process initiated"
    }), 202

if __name__ == "__main__":
    if logs is not None:
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print(f"Automatic purge scheduled daily at {Config.PURGE_TIME}")
    
    print("Starting Flask server...")
    app.run(debug=True)