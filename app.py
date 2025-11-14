"""
Audit and Logging Microservice
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
    
    # Create performance indexes for fast querying
    try:
        logs.create_index("timestamp")  # Critical for date filtering and sorting
        logs.create_index("service")    # For service filtering
        logs.create_index("level")      # For level filtering  
        logs.create_index("user_id")    # For user filtering
        logs.create_index("action")     # For action filtering
        logs.create_index([("service", 1), ("timestamp", -1)])  # Compound index for common queries
        print("Connected to MongoDB with performance indexes")
    except Exception as idx_error:
        print(f"Index creation warning: {idx_error}")
        
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
            query = {"timestamp": {"$lt": cutoff}}  # Query datetime objects directly
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

# USER STORY 1: User Actions Record
@app.route('/log', methods=['POST'])
def create_log():
    """
    Records user and service actions in centralized audit log
    """
    if logs is None:
        return jsonify({"error": "Database unavailable"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    required_fields = ["service", "action", "level"]
    missing = [f for f in required_fields if f not in data or not data[f]]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Build log entry - store timestamp as datetime object for proper querying
    log_entry = {
        "timestamp": datetime.utcnow(),
        "timestamp_str": datetime.utcnow().isoformat() + "Z",  # Keep string for display
        "service": data["service"],
        "user_id": data.get("user_id"),
        "action": data["action"],
        "level": data["level"].upper(),
        "details": data.get("details"),
    }

    try:
        result = logs.insert_one(log_entry)
        return jsonify({"status": "success", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error inserting log: {e}")
        return jsonify({"error": "Failed to store log entry"}), 500

# USER STORY 2: Filter Audit Logs - Partner Implementation Required
@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Enables compliance administrators to query audit logs with filters
    """
    if logs is None:
        return jsonify({"error": "Database unavailable"}), 500

    # Parse filters from query parameters
    query = {}
    service = request.args.get("service")
    level = request.args.get("level")
    user_id = request.args.get("user_id")
    action = request.args.get("action")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    limit = min(int(request.args.get("limit", 100)), 1000)
    offset = int(request.args.get("offset", 0))

    if service:
        query["service"] = service
    if level:
        query["level"] = level.upper()
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    if start_date or end_date:
        date_query = {}
        if start_date:
            try:
                # Parse date string and create datetime object for comparison
                start_dt = datetime.fromisoformat(start_date)
                date_query["$gte"] = start_dt
            except Exception:
                return jsonify({"error": "Invalid start_date format (expected YYYY-MM-DD)"}), 400
        if end_date:
            try:
                # Include up to the end of the given date
                end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
                date_query["$lte"] = end_dt
            except Exception:
                return jsonify({"error": "Invalid end_date format (expected YYYY-MM-DD)"}), 400
        query["timestamp"] = date_query

    try:
        total_count = logs.count_documents({})
        filtered_count = logs.count_documents(query)

        cursor = (
            logs.find(query)
            .sort("timestamp", 1)
            .skip(offset)
            .limit(limit)
        )

        result_logs = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            # Use string timestamp for API response (compatibility)
            if "timestamp_str" in doc:
                doc["timestamp"] = doc["timestamp_str"]
                del doc["timestamp_str"]
            elif isinstance(doc.get("timestamp"), datetime):
                doc["timestamp"] = doc["timestamp"].isoformat() + "Z"
            result_logs.append(doc)

        return jsonify({
            "logs": result_logs,
            "total": total_count,
            "filtered": filtered_count,
            "chronological_order": True
        }), 200

    except Exception as e:
        print(f"Error retrieving logs: {e}")
        return jsonify({"error": "Failed to retrieve logs"}), 500

# USER STORY 3: User Log Purge
@app.route('/purge-logs', methods=['POST'])
@require_admin_auth
def purge_logs():
    """
    Supports 3-year data retention requirement with automated and manual purge capabilities.
    Enables system administrators to manage log storage and comply with data governance.
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
    app.run(debug=False, port=5001)
