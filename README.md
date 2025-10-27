# Audit_and_Logging_Microservice
A microservice that tracks all user and system actions for compliance and debugging.

## GET requests
All the GET requests our microservice allows

## POST requests
All the POST requests our microservice allows

## Register
This request is used to register a new user with this microservice
### Endpoint
```http
POST /register
```
### Description
This endpoint accepts a JSON payload containing the user's email, username, and password

### Request
**Content-type:** application/json \
**Schema:**
```json
{
  "email": "string",
  "password": "string",
  "username": "string"
}
```
|Field|Required|Notes|
|-----|--------|-----|
|email|yes|email of the new user (must be valid email)|
|password|yes|password for new user|
|username|yes|username or display name for new user|

### Response
**Content-type:** application/json \
**Schema:**
```json
{
  "message": "string",
  "userId": "string"
}

```
