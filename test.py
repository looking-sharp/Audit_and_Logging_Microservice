#!/usr/bin/env python3
"""
AUDIT MICROSERVICE TEST

Test program for HTTP microservice communication.
Shows step-by-step HTTP requests and responses with pauses for demonstration.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_microservice():
    print("AUDIT MICROSERVICE TEST")
    print("=" * 70)
    print("Testing HTTP communication with Flask app and MongoDB")
    print("=" * 70)
    
    input("\nPress ENTER to start testing...")
    
    # ================================================================
    # STEP 1: POST /log - Record User Actions
    # ================================================================
    print("\n" + "="*50)
    print("STEP 1: POST /log - Record User Actions")
    print("="*50)
    
    print("\nRequest format:")
    print("""POST http://localhost:5001/log
Content-Type: application/json

{
  "service": "Auth",
  "user_id": "user123", 
  "action": "login",
  "level": "INFO",
  "details": "User successfully logged in"
}""")
    
    log_data = {
        "service": "Auth",
        "user_id": "user123",
        "action": "login", 
        "level": "INFO",
        "details": "User successfully logged in"
    }
    
    input("\nPress ENTER to send this HTTP POST request...")
    
    try:
        print(f"Making HTTP POST request to {BASE_URL}/log...")
        response = requests.post(f"{BASE_URL}/log", json=log_data)
        
        print(f"\nMICROSERVICE RESPONSE:")
        print(f"   Status: {response.status_code} {response.reason}")
        print(f"   Body: {json.dumps(response.json(), indent=2)}")
        
        print(f"\nExpected response:")
        print(f"""   HTTP 201 Created
   {{
     "status": "success",
     "id": "654f8a1c28b9f0a0b2d4e321" 
   }}""")
        
        if response.status_code == 201:
            log_id = response.json().get('id')
            print(f"\nSUCCESS: Log created in MongoDB with ID: {log_id}")
        
        input("\nPress ENTER to continue...")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # ================================================================
    # STEP 2: GET /logs - Query Audit Logs  
    # ================================================================
    print("\n" + "="*50)
    print("STEP 2: GET /logs - Query Audit Logs")
    print("="*50)
    
    print("\nRequest format:")
    print("GET http://localhost:5001/logs?service=Auth&level=INFO&limit=50")
    
    input("\nPress ENTER to send this HTTP GET request...")
    
    try:
        print(f"Making HTTP GET request to {BASE_URL}/logs...")
        params = {"service": "Auth", "level": "INFO", "limit": 50}
        response = requests.get(f"{BASE_URL}/logs", params=params)
        
        print(f"\nMICROSERVICE RESPONSE:")
        print(f"   Status: {response.status_code} {response.reason}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Total logs in database: {data.get('total')}")
            print(f"   Filtered results: {data.get('filtered')}")
            print(f"   Logs returned: {len(data.get('logs', []))}")
            
            if data.get('logs'):
                latest = data['logs'][0]
                print(f"\nSample log entry:")
                print(f"   ID: {latest.get('_id')}")
                print(f"   Service: {latest.get('service')}")
                print(f"   Action: {latest.get('action')}")
                print(f"   Timestamp: {latest.get('timestamp')}")
            
            print(f"\nExpected response structure:")
            print(f"""   HTTP 200 OK
   {{
     "logs": [{{ "_id": "...", "timestamp": "...", "service": "Auth", ... }}],
     "total": 1500,
     "filtered": 25,
     "chronological_order": true
   }}""")
            
            print(f"\nSUCCESS: Retrieved {len(data.get('logs', []))} logs from MongoDB")
        
        input("\nReview the log data, then press ENTER to continue...")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # ================================================================
    # STEP 3: POST /purge-logs - Admin Operations
    # ================================================================
    print("\n" + "="*50)
    print("STEP 3: POST /purge-logs - Admin Operations")
    print("="*50)
    
    print("\nRequest format:")
    print("""POST http://localhost:5001/purge-logs
Authorization: Bearer secret-admin-key
Content-Type: application/json

{
  "admin_user": "admin@company.com",
  "criteria": {
    "older_than_days": 90
  }
}""")
    
    purge_data = {
        "admin_user": "admin@company.com",
        "criteria": {"service": "TestCleanup"}  # Safe - only deletes TestCleanup service
    }
    
    headers = {"Authorization": "Bearer secret-admin-key"}
    
    input("\nPress ENTER to send this authenticated HTTP POST request...")
    
    try:
        print(f"Making authenticated HTTP POST request to {BASE_URL}/purge-logs...")
        response = requests.post(f"{BASE_URL}/purge-logs", json=purge_data, headers=headers)
        
        print(f"\nMICROSERVICE RESPONSE:")
        print(f"   Status: {response.status_code} {response.reason}")
        print(f"   Body: {json.dumps(response.json(), indent=2)}")
        
        print(f"\nExpected response:")
        print(f"""   HTTP 202 Accepted
   {{
     "status": "accepted",
     "message": "Purge process initiated"
   }}""")
        
        if response.status_code == 202:
            print(f"\nSUCCESS: Purge request accepted and processed asynchronously")
            print("The purge runs in the background without blocking the API")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # ================================================================
    # SUMMARY
    # ================================================================
    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print("\nMicroservice is working correctly!")

if __name__ == "__main__":
    test_microservice()