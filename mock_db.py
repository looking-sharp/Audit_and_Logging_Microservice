#!/usr/bin/env python3
"""
Mock Database Module for Audit and Logging Microservice Testing

Provides in-memory mock database functionality to simulate MongoDB operations
without requiring an actual database connection. Supports all CRUD operations
needed for testing the audit logging API endpoints.

Features:
- In-memory log storage with auto-incrementing IDs
- Query filtering by service, level, user_id, action, date ranges
- Pagination support with limit/offset
- Purge operations with various criteria
- Thread-safe operations for concurrent testing
- Realistic data validation matching the real API
"""

import json
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


class MockLogEntry:
    """Represents a single log entry in the mock database"""
    
    def __init__(self, data: Dict[str, Any], entry_id: str):
        self.data = data.copy()
        self.data["_id"] = entry_id
        if "timestamp" not in self.data:
            self.data["timestamp"] = datetime.utcnow()
            self.data["timestamp_str"] = self.data["timestamp"].isoformat() + "Z"
    
    def matches_query(self, query: Dict[str, Any]) -> bool:
        """Check if this entry matches the given query parameters"""
        for key, value in query.items():
            if key == "timestamp" and isinstance(value, dict):
                # Handle date range queries - matches app.py logic exactly
                entry_time = self.data.get("timestamp")
                if isinstance(entry_time, str):
                    try:
                        entry_time = datetime.fromisoformat(entry_time.replace('Z', ''))
                    except:
                        continue
                
                if "$gte" in value and entry_time < value["$gte"]:
                    return False
                if "$lte" in value and entry_time > value["$lte"]:
                    return False  
                if "$lt" in value and entry_time >= value["$lt"]:
                    return False
            elif key in self.data:
                if isinstance(value, dict) and "$regex" in value:
                    # Handle regex queries (case insensitive)
                    import re
                    pattern = value["$regex"]
                    flags = re.IGNORECASE if value.get("$options") == "i" else 0
                    if not re.search(pattern, str(self.data[key]), flags):
                        return False
                else:
                    if self.data[key] != value:
                        return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API responses"""
        result = self.data.copy()
        # Convert datetime to string for API response
        if isinstance(result.get("timestamp"), datetime):
            result["timestamp"] = result["timestamp"].isoformat() + "Z"
        return result


class MockDatabase:
    """Thread-safe in-memory mock database for audit logs"""
    
    def __init__(self):
        self.logs: List[MockLogEntry] = []
        self.counter = 1
        self.lock = threading.Lock()
    
    def insert_one(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Insert a new log entry and return insertion result"""
        with self.lock:
            entry_id = f"mock_id_{self.counter}"
            self.counter += 1
            
            # Validate required fields - matches app.py exactly
            required_fields = ["service", "action", "level"]
            missing = [f for f in required_fields if f not in data or not data[f]]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
            # Process data like app.py does
            processed_data = data.copy()
            processed_data["level"] = data["level"].upper()  # Match app.py level processing
            
            entry = MockLogEntry(processed_data, entry_id)
            self.logs.append(entry)
            
            return {"inserted_id": entry_id}
    
    def find(self, query: Dict[str, Any] = None) -> 'MockCursor':
        """Find logs matching the query"""
        if query is None:
            query = {}
        
        with self.lock:
            matching_logs = [log for log in self.logs if log.matches_query(query)]
        
        return MockCursor(matching_logs)
    
    def count_documents(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching the query"""
        if query is None:
            query = {}
        
        with self.lock:
            return len([log for log in self.logs if log.matches_query(query)])
    
    def delete_many(self, query: Dict[str, Any]) -> Dict[str, int]:
        """Delete multiple documents matching the query"""
        with self.lock:
            original_count = len(self.logs)
            self.logs = [log for log in self.logs if not log.matches_query(query)]
            deleted_count = original_count - len(self.logs)
            
            return {"deleted_count": deleted_count}
    
    def clear_all(self):
        """Clear all logs (useful for test cleanup)"""
        with self.lock:
            self.logs.clear()
            self.counter = 1
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Get all logs as dictionaries (for debugging/inspection)"""
        with self.lock:
            return [log.to_dict() for log in self.logs]


class MockCursor:
    """Mock cursor for database query results with MongoDB-like interface"""
    
    def __init__(self, logs: List[MockLogEntry]):
        self.logs = logs
        self.sort_field = None
        self.sort_direction = 1
        self.skip_count = 0
        self.limit_count = None
    
    def sort(self, field: str, direction: int = 1) -> 'MockCursor':
        """Sort results by field (1 for ascending, -1 for descending)"""
        self.sort_field = field
        self.sort_direction = direction
        return self
    
    def skip(self, count: int) -> 'MockCursor':
        """Skip a number of results"""
        self.skip_count = count
        return self
    
    def limit(self, count: int) -> 'MockCursor':
        """Limit the number of results"""
        self.limit_count = count
        return self
    
    def __iter__(self):
        """Iterate over the results"""
        # Apply sorting
        if self.sort_field:
            def sort_key(log):
                value = log.data.get(self.sort_field)
                if isinstance(value, datetime):
                    return value.timestamp()
                return value or ""
            
            sorted_logs = sorted(
                self.logs, 
                key=sort_key, 
                reverse=(self.sort_direction == -1)
            )
        else:
            sorted_logs = self.logs
        
        # Apply skip and limit
        start_idx = self.skip_count
        end_idx = None
        if self.limit_count is not None:
            end_idx = start_idx + self.limit_count
        
        result_logs = sorted_logs[start_idx:end_idx]
        
        # Return dictionaries for API compatibility
        for log in result_logs:
            yield log.to_dict()


class MockDatabaseManager:
    """Singleton manager for mock database instances"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.databases = {}
        return cls._instance
    
    def get_database(self, name: str = "audit_logs") -> MockDatabase:
        """Get or create a mock database by name"""
        if name not in self.databases:
            self.databases[name] = MockDatabase()
        return self.databases[name]
    
    def reset_all(self):
        """Reset all databases (useful for test cleanup)"""
        for db in self.databases.values():
            db.clear_all()


# Global instance for easy access
mock_db_manager = MockDatabaseManager()


def get_mock_logs_collection() -> MockDatabase:
    """Get the mock logs collection (equivalent to MongoDB's logs collection)"""
    return mock_db_manager.get_database("audit_logs")


def create_sample_data() -> List[str]:
    """Create sample log entries for testing"""
    logs_db = get_mock_logs_collection()
    
    sample_logs = [
        {
            "service": "Auth",
            "user_id": "user123",
            "action": "login",
            "level": "INFO",
            "details": "User successfully logged in"
        },
        {
            "service": "Training",
            "user_id": "user456",
            "action": "create_session",
            "level": "INFO",
            "details": "New training session created"
        },
        {
            "service": "Auth",
            "user_id": "user123",
            "action": "logout",
            "level": "INFO",
            "details": "User logged out"
        },
        {
            "service": "Procedures",
            "user_id": "admin789",
            "action": "update_procedure",
            "level": "WARNING",
            "details": "Critical procedure updated"
        },
        {
            "service": "Auth",
            "user_id": "hacker999",
            "action": "failed_login",
            "level": "ERROR",
            "details": "Multiple failed login attempts"
        }
    ]
    
    inserted_ids = []
    for log_data in sample_logs:
        result = logs_db.insert_one(log_data)
        inserted_ids.append(result["inserted_id"])
    
    return inserted_ids


if __name__ == "__main__":
    # Demo/test the mock database
    print("Mock Database Demo")
    print("=" * 50)
    
    # Create sample data
    ids = create_sample_data()
    print(f"Created {len(ids)} sample log entries")
    
    # Test queries
    logs_db = get_mock_logs_collection()
    
    # Count all logs
    total = logs_db.count_documents({})
    print(f"Total logs: {total}")
    
    # Query by service
    auth_logs = list(logs_db.find({"service": "Auth"}))
    print(f"Auth service logs: {len(auth_logs)}")
    
    # Query by level
    error_logs = list(logs_db.find({"level": "ERROR"}))
    print(f"Error level logs: {len(error_logs)}")
    
    # Test sorting and limiting
    recent_logs = list(
        logs_db.find({})
        .sort("timestamp", -1)
        .limit(3)
    )
    print(f"Most recent 3 logs: {len(recent_logs)}")
    
    # Test purge operation
    result = logs_db.delete_many({"level": "ERROR"})
    print(f"Deleted {result['deleted_count']} error logs")
    
    print("\nMock database demo completed successfully!")