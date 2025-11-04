# EventHint API Specification

## Base URL

```
Development: http://localhost:8000
Production: https://api.eventhint.com
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

## Endpoints

### Authentication

#### `GET /api/auth/google/login`

Initiate Google OAuth flow.

**Response:**
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```

#### `GET /api/auth/google/callback`

OAuth callback endpoint (redirects to frontend with token).

**Query Parameters:**
- `code`: Authorization code from Google

**Redirects to:**
```
{FRONTEND_URL}/auth/callback?token={jwt_token}
```

#### `GET /api/auth/me`

Get current user information.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "neptun_id": "ABC123",
  "default_timezone": "Europe/Budapest",
  "auto_approve_enabled": false,
  "is_active": true,
  "created_at": "2024-11-04T12:00:00Z"
}
```

### Events

#### `GET /api/events`

List events for current user.

**Query Parameters:**
- `status` (optional): Filter by status (pending_approval, approved, synced, rejected)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Results per page (default: 100, max: 100)

**Response:**
```json
[
  {
    "id": "uuid",
    "type": "event",
    "title": "Exam appointment",
    "start": "2025-11-04T08:50:00+01:00",
    "end": "2025-11-04T09:20:00+01:00",
    "allday": false,
    "timezone": "Europe/Budapest",
    "location": null,
    "online_url": null,
    "notes": "Imported from schedule",
    "attendees": [],
    "reminders": [
      {"method": "popup", "minutes": 1440}
    ],
    "labels": ["exam"],
    "status": "pending_approval",
    "confidence": 0.85,
    "created_at": "2024-11-04T10:00:00Z"
  }
]
```

#### `GET /api/events/{event_id}`

Get a specific event.

**Response:** Same as single event in list above.

#### `POST /api/events`

Create a new event (typically used by extraction pipeline).

**Request Body:**
```json
{
  "type": "event",
  "title": "Meeting",
  "start": "2024-11-05T14:00:00+01:00",
  "end": "2024-11-05T15:00:00+01:00",
  "timezone": "Europe/Budapest",
  "reminders": [
    {"method": "popup", "minutes": 15}
  ]
}
```

**Response:** Created event (same as GET).

#### `PATCH /api/events/{event_id}`

Update an event.

**Request Body:** Partial event (only fields to update).

**Response:** Updated event.

#### `POST /api/events/{event_id}/approve`

Approve a pending event and sync to calendar.

**Request Body (optional):**
```json
{
  "modifications": {
    "title": "Updated title",
    "start": "2024-11-05T14:30:00+01:00"
  },
  "calendar_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "event_id": "uuid",
  "calendar_event_id": "google_calendar_id",
  "message": "Event approved successfully"
}
```

#### `POST /api/events/{event_id}/reject`

Reject a pending event.

**Response:**
```json
{
  "success": true,
  "message": "Event rejected"
}
```

#### `DELETE /api/events/{event_id}`

Delete an event.

**Response:**
```json
{
  "success": true,
  "message": "Event deleted"
}
```

### Ingestion

#### `POST /api/ingestion/upload`

Upload a file for processing.

**Request:** multipart/form-data
- `file`: File (image, PDF, email)

**Response:**
```json
{
  "success": true,
  "message_id": "uuid",
  "filename": "schedule.png",
  "size": 123456
}
```

#### `POST /api/ingestion/webhooks/gmail`

Gmail push notification webhook (internal).

**Request Body:** Gmail notification payload.

### Calendars

#### `GET /api/calendars`

List connected calendars.

**Response:**
```json
[
  {
    "id": "uuid",
    "provider": "google",
    "name": "Primary Calendar",
    "color": "#0B8043",
    "is_default": true,
    "last_sync": "2024-11-04T12:00:00Z"
  }
]
```

#### `POST /api/calendars/{calendar_id}/set-default`

Set a calendar as default.

**Response:**
```json
{
  "success": true,
  "message": "Default calendar updated"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message"
}
```

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File upload exceeds limit
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

- API: 100 requests/minute per user
- Upload: 10 files/minute per user
- Webhooks: No limit (authenticated via signature)

## Webhooks

### Gmail Push Notifications

EventHint receives push notifications from Gmail when new messages arrive.

**Setup:**
1. User authorizes Gmail access
2. Backend calls `users.watch()` with Pub/Sub topic
3. Gmail sends notifications to our webhook
4. Webhook triggers background processing

**Notification Format:**
```json
{
  "message": {
    "data": "base64_encoded_data",
    "messageId": "...",
    "publishTime": "..."
  }
}
```

## SDK Examples

### Python

```python
import requests

API_URL = "http://localhost:8000/api"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# List pending events
response = requests.get(
    f"{API_URL}/events?status=pending_approval",
    headers=headers
)
events = response.json()

# Approve event
event_id = events[0]["id"]
response = requests.post(
    f"{API_URL}/events/{event_id}/approve",
    headers=headers
)
print(response.json())
```

### JavaScript

```javascript
const API_URL = 'http://localhost:8000/api';
const TOKEN = 'your_jwt_token';

// List pending events
const response = await fetch(
  `${API_URL}/events?status=pending_approval`,
  {
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    }
  }
);
const events = await response.json();

// Approve event
const eventId = events[0].id;
await fetch(`${API_URL}/events/${eventId}/approve`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json'
  }
});
```

## OpenAPI Spec

Full OpenAPI 3.0 specification available at:
```
GET /docs          # Swagger UI
GET /redoc         # ReDoc
GET /openapi.json  # Raw OpenAPI JSON
```

