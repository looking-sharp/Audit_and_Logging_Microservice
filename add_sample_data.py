#!/usr/bin/env python3
"""
Add Sample Data to MongoDB
This script directly connects to MongoDB and adds sample log entries
so you can see them in VS Code MongoDB extension
"""

from pymongo import MongoClient
from datetime import datetime

def add_sample_data():
    print("Adding sample data to MongoDB...")
    
    # Connect to MongoDB (same as your app.py)
    client = MongoClient('mongodb://localhost:27017/')
    db = client.audit_logs
    logs = db.logs
    
    # Sample log entries
    sample_logs = [
        {
            "timestamp": datetime.utcnow(),
            "timestamp_str": datetime.utcnow().isoformat() + "Z",
            "service": "Auth",
            "user_id": "user123",
            "action": "login",
            "level": "INFO",
            "details": "User successfully logged in"
        },
        {
            "timestamp": datetime.utcnow(),
            "timestamp_str": datetime.utcnow().isoformat() + "Z",
            "service": "Training",
            "user_id": "trainer456",
            "action": "create_session",
            "level": "INFO",
            "details": "New training session created"
        },
        {
            "timestamp": datetime.utcnow(),
            "timestamp_str": datetime.utcnow().isoformat() + "Z",
            "service": "Procedures",
            "user_id": "admin789",
            "action": "update_procedure",
            "level": "WARNING",
            "details": "Critical procedure updated"
        }
    ]
    
    # Insert the sample logs
    result = logs.insert_many(sample_logs)
    print(f"Inserted {len(result.inserted_ids)} log entries")
    
    # Show current count
    total_logs = logs.count_documents({})
    print(f"Total logs in database: {total_logs}")
    
    # Show a sample log
    sample = logs.find_one()
    if sample:
        print(f"📄 Sample log entry:")
        print(f"   ID: {sample['_id']}")
        print(f"   Service: {sample['service']}")
        print(f"   Action: {sample['action']}")
        print(f"   Timestamp: {sample['timestamp_str']}")
    
    print("🎉 Sample data added! Check VS Code MongoDB extension now.")

if __name__ == "__main__":
    add_sample_data()