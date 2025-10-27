# Thesis Manager API Documentation

This document provides an overview of the Thesis Manager REST API. For interactive documentation and detailed endpoint specifications, visit the [Swagger UI](http://localhost/api/docs/) after starting the application.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Best Practices](#best-practices)

## Overview

The Thesis Manager API provides programmatic access to thesis, student, supervisor, and comment management functionality. The API follows REST principles and returns JSON responses.

**Base URL**: `http://localhost/api/` (adjust for your deployment)

**Version**: 1.0.0

**Documentation**:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## Authentication

The API uses token-based authentication with [Knox](https://github.com/jazzband/django-rest-knox). Each user can create multiple API tokens for different applications or use cases.

### Creating an API Token

1. Log in to the web interface
2. Navigate to **API** → **My API Tokens**
3. Click **Create New Token**
4. Copy the token immediately (it won't be shown again)

Alternatively, create a token programmatically:

```bash
curl -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

Response:
```json
{
  "expiry": null,
  "token": "your_api_token_here"
}
```

### Using Your Token

Include the token in the `Authorization` header of all API requests:

```
Authorization: Token YOUR_TOKEN_HERE
```

### Token Management

- **Maximum tokens per user**: 10
- **Token expiry**: None (tokens don't expire by default)
- **Revoke token**: DELETE `/api/auth/logout/`
- **Revoke all tokens**: DELETE `/api/auth/logoutall/`

## API Endpoints

### Theses

| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| GET | `/api/theses/` | List all theses | Authenticated |
| POST | `/api/theses/` | Create a new thesis | Staff or Supervisor |
| GET | `/api/theses/{id}/` | Get thesis details | Authenticated |
| PUT | `/api/theses/{id}/` | Update thesis | Staff or Supervisor |
| PATCH | `/api/theses/{id}/` | Partial update | Staff or Supervisor |
| DELETE | `/api/theses/{id}/` | Delete thesis | Staff or Supervisor |
| GET | `/api/theses/{id}/comments/` | Get thesis comments | Authenticated |
| POST | `/api/theses/{id}/add_comment/` | Add comment | Authenticated |

**Filtering & Search:**
- `?phase=registered` - Filter by phase
- `?thesis_type=bachelor` - Filter by type
- `?student=123` - Filter by student ID
- `?supervisor=456` - Filter by supervisor ID
- `?search=machine learning` - Search in title, student names, description

**Ordering:**
- `?ordering=-date_first_contact` - Order by first contact (descending)
- `?ordering=date_deadline` - Order by deadline (ascending)

### Students

| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| GET | `/api/students/` | List all students | Authenticated |
| POST | `/api/students/` | Create a new student | Staff only |
| GET | `/api/students/{id}/` | Get student details | Authenticated |
| PUT | `/api/students/{id}/` | Update student | Staff only |
| PATCH | `/api/students/{id}/` | Partial update | Staff only |
| DELETE | `/api/students/{id}/` | Delete student | Staff only |
| GET | `/api/students/{id}/theses/` | Get student's theses | Authenticated |

**Search:**
- `?search=john` - Search in name, email, or student ID

### Supervisors

| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| GET | `/api/supervisors/` | List all supervisors | Authenticated |
| POST | `/api/supervisors/` | Create a new supervisor | Staff only |
| GET | `/api/supervisors/{id}/` | Get supervisor details | Authenticated |
| PUT | `/api/supervisors/{id}/` | Update supervisor | Staff only |
| PATCH | `/api/supervisors/{id}/` | Partial update | Staff only |
| DELETE | `/api/supervisors/{id}/` | Delete supervisor | Staff only |
| GET | `/api/supervisors/{id}/theses/` | Get supervised theses | Authenticated |

**Search:**
- `?search=smith` - Search in name or email

### Comments

| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| GET | `/api/comments/` | List all comments | Authenticated |
| POST | `/api/comments/` | Create a comment | Authenticated |
| GET | `/api/comments/{id}/` | Get comment details | Authenticated |
| PUT | `/api/comments/{id}/` | Update comment | Owner or Staff |
| PATCH | `/api/comments/{id}/` | Partial update | Owner or Staff |
| DELETE | `/api/comments/{id}/` | Delete comment | Owner or Staff |

**Filtering:**
- `?thesis=123` - Filter by thesis ID
- `?user=456` - Filter by user ID
- `?is_auto_generated=false` - Filter manual comments

## Usage Examples

### Python (requests library)

```python
import requests

API_BASE = "http://localhost/api"
TOKEN = "your_api_token_here"
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

# List all theses
response = requests.get(f"{API_BASE}/theses/", headers=HEADERS)
theses = response.json()

# Get a specific thesis
thesis_id = 1
response = requests.get(f"{API_BASE}/theses/{thesis_id}/", headers=HEADERS)
thesis = response.json()

# Create a new thesis
new_thesis = {
    "title": "Machine Learning for Healthcare",
    "thesis_type": "master",
    "phase": "first_contact",
    "students": [1, 2],  # Student IDs
    "supervisors": [1],  # Supervisor IDs
    "date_first_contact": "2025-10-27",
    "description": "Exploring ML applications in healthcare"
}
response = requests.post(f"{API_BASE}/theses/", headers=HEADERS, json=new_thesis)
created_thesis = response.json()

# Update a thesis (partial)
updates = {
    "phase": "registered",
    "date_registration": "2025-11-01"
}
response = requests.patch(f"{API_BASE}/theses/{thesis_id}/", headers=HEADERS, json=updates)
updated_thesis = response.json()

# Add a comment
comment = {
    "thesis": thesis_id,
    "text": "Initial meeting completed. Student is enthusiastic!"
}
response = requests.post(f"{API_BASE}/comments/", headers=HEADERS, json=comment)

# Search theses
response = requests.get(
    f"{API_BASE}/theses/",
    headers=HEADERS,
    params={"search": "machine learning", "phase": "registered"}
)
results = response.json()
```

### JavaScript (fetch API)

```javascript
const API_BASE = 'http://localhost/api';
const TOKEN = 'your_api_token_here';
const HEADERS = {
    'Authorization': `Token ${TOKEN}`,
    'Content-Type': 'application/json'
};

// List all theses
fetch(`${API_BASE}/theses/`, { headers: HEADERS })
    .then(response => response.json())
    .then(data => console.log(data));

// Create a new thesis
const newThesis = {
    title: 'Machine Learning for Healthcare',
    thesis_type: 'master',
    phase: 'first_contact',
    students: [1, 2],
    supervisors: [1],
    date_first_contact: '2025-10-27',
    description: 'Exploring ML applications in healthcare'
};

fetch(`${API_BASE}/theses/`, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(newThesis)
})
.then(response => response.json())
.then(data => console.log('Created:', data));

// Update thesis
const updates = {
    phase: 'registered',
    date_registration: '2025-11-01'
};

fetch(`${API_BASE}/theses/1/`, {
    method: 'PATCH',
    headers: HEADERS,
    body: JSON.stringify(updates)
})
.then(response => response.json())
.then(data => console.log('Updated:', data));
```

### curl

```bash
# List all theses
curl -H "Authorization: Token YOUR_TOKEN" http://localhost/api/theses/

# Get specific thesis
curl -H "Authorization: Token YOUR_TOKEN" http://localhost/api/theses/1/

# Create a thesis
curl -X POST http://localhost/api/theses/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Machine Learning for Healthcare",
    "thesis_type": "master",
    "phase": "first_contact",
    "students": [1],
    "supervisors": [1],
    "date_first_contact": "2025-10-27"
  }'

# Update thesis
curl -X PATCH http://localhost/api/theses/1/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type": "application/json" \
  -d '{"phase": "registered", "date_registration": "2025-11-01"}'

# Delete thesis
curl -X DELETE http://localhost/api/theses/1/ \
  -H "Authorization: Token YOUR_TOKEN"

# Search and filter
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost/api/theses/?search=machine%20learning&phase=registered"
```

## Error Handling

The API uses standard HTTP status codes:

| Status Code | Meaning |
|-------------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request successful, no content returned |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Server error |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

Or for field-specific errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

### Common Errors

**Missing Authentication:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Invalid Token:**
```json
{
  "detail": "Invalid token."
}
```

**Validation Error:**
```json
{
  "students": ["At least one student must be assigned to the thesis."],
  "date_deadline": ["Ensure this field is a valid date."]
}
```

## Rate Limiting

Currently, there is no rate limiting implemented. For production deployments, consider implementing rate limiting at the nginx level or using Django rate limiting middleware.

## Best Practices

### 1. Store Tokens Securely

- Never commit tokens to version control
- Use environment variables or secure vaults
- Rotate tokens periodically

### 2. Use HTTPS in Production

Always use HTTPS to encrypt API communications:

```python
API_BASE = "https://theses.example.com/api"
```

### 3. Handle Pagination

API responses are paginated (50 items per page). Always handle pagination:

```python
def get_all_theses():
    theses = []
    url = f"{API_BASE}/theses/"

    while url:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        theses.extend(data['results'])
        url = data['next']  # Next page URL or None

    return theses
```

### 4. Use Filtering and Search

Reduce bandwidth by filtering on the server:

```python
# Good: Filter on server
response = requests.get(
    f"{API_BASE}/theses/",
    headers=HEADERS,
    params={"phase": "registered", "thesis_type": "master"}
)

# Bad: Fetch everything and filter locally
response = requests.get(f"{API_BASE}/theses/", headers=HEADERS)
filtered = [t for t in response.json()['results'] if t['phase'] == 'registered']
```

### 5. Use PATCH for Partial Updates

Use PATCH instead of PUT when updating only specific fields:

```python
# Good: PATCH with only changed fields
requests.patch(f"{API_BASE}/theses/1/", headers=HEADERS, json={"phase": "registered"})

# Bad: PUT requires all fields
requests.put(f"{API_BASE}/theses/1/", headers=HEADERS, json=full_thesis_data)
```

### 6. Error Handling

Always implement proper error handling:

```python
try:
    response = requests.post(f"{API_BASE}/theses/", headers=HEADERS, json=data)
    response.raise_for_status()  # Raises HTTPError for bad status codes
    thesis = response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
    print(f"Response: {e.response.json()}")
except requests.exceptions.ConnectionError:
    print("Connection error - check if server is running")
except requests.exceptions.Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 7. Batch Operations

When creating multiple resources, do it efficiently:

```python
# Create multiple students
students_data = [
    {"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
    {"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"}
]

created_students = []
for student_data in students_data:
    response = requests.post(f"{API_BASE}/students/", headers=HEADERS, json=student_data)
    if response.status_code == 201:
        created_students.append(response.json())
    else:
        print(f"Failed to create student: {student_data}, Error: {response.json()}")
```

## Integration Examples

### Automated Thesis Status Updates

```python
import requests
from datetime import date, timedelta

def check_upcoming_deadlines():
    """Send notifications for theses with deadlines in the next 7 days"""
    today = date.today()
    week_from_now = today + timedelta(days=7)

    # Get all active theses
    response = requests.get(
        f"{API_BASE}/theses/",
        headers=HEADERS,
        params={"phase": "working"}
    )

    for thesis in response.json()['results']:
        if thesis['date_deadline']:
            deadline = date.fromisoformat(thesis['date_deadline'])
            if today <= deadline <= week_from_now:
                # Add a reminder comment
                comment = {
                    "thesis": thesis['id'],
                    "text": f"Reminder: Deadline is in {(deadline - today).days} days!"
                }
                requests.post(f"{API_BASE}/comments/", headers=HEADERS, json=comment)
```

### Bulk Data Export

```python
import csv

def export_theses_to_csv(filename="theses_export.csv"):
    """Export all theses to CSV"""
    theses = []
    url = f"{API_BASE}/theses/"

    # Fetch all pages
    while url:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        theses.extend(data['results'])
        url = data['next']

    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['id', 'title', 'thesis_type', 'phase', 'date_first_contact',
                      'date_deadline', 'students', 'supervisors']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for thesis in theses:
            writer.writerow({
                'id': thesis['id'],
                'title': thesis['title'],
                'thesis_type': thesis['thesis_type_display'],
                'phase': thesis['phase_display'],
                'date_first_contact': thesis['date_first_contact'] or '',
                'date_deadline': thesis['date_deadline'] or '',
                'students': ', '.join([s['first_name'] + ' ' + s['last_name']
                                      for s in thesis['students_details']]),
                'supervisors': ', '.join([s['first_name'] + ' ' + s['last_name']
                                         for s in thesis['supervisors_details']])
            })

    print(f"Exported {len(theses)} theses to {filename}")
```

## Additional Resources

- **Interactive API Documentation**: [/api/docs/](/api/docs/) (Swagger UI)
- **Alternative Documentation**: [/api/redoc/](/api/redoc/) (ReDoc)
- **OpenAPI Schema**: [/api/schema/](/api/schema/)
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Knox Authentication**: https://github.com/jazzband/django-rest-knox

## Support

For issues or questions about the API:
1. Check the interactive documentation at `/api/docs/`
2. Review this guide
3. Contact your system administrator
