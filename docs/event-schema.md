# Event/Task Schema Reference

## Overview

The Event/Task schema is the canonical data structure that EventHint uses throughout the system. All extraction methods (deterministic, LLM, hybrid) must output events conforming to this schema.

## Schema Definition

### EventBase (Core Fields)

```typescript
{
  type: "event" | "task",
  title: string,              // Required, 1-500 chars
  start: datetime,            // Required, ISO-8601 with timezone
  end?: datetime | null,      // Optional, must be after start
  allday: boolean,            // Default: false
  timezone: string,           // IANA format, default: "Europe/Budapest"
  location?: string | null,   // Max 500 chars
  online_url?: string | null, // Meeting URL (Zoom, Meet, Teams)
  notes?: string | null,      // Free-form text
  attendees: Attendee[],      // Default: []
  reminders: Reminder[],      // Default: []
  labels: string[],           // Default: []
  recurrence?: string | null  // RRULE format
}
```

### Reminder

```typescript
{
  method: "popup" | "email",
  minutes: number  // Minutes before event (>= 0)
}
```

### Attendee

```typescript
{
  name: string,
  email: string  // Valid email format
}
```

### EventSource (Metadata)

```typescript
{
  message_id?: string,        // UUID of source message
  provider: "gmail" | "outlook" | "upload",
  confidence: number          // 0.0-1.0
}
```

### Full Event (Database Model)

```typescript
{
  // Core fields (from EventBase)
  ...EventBase,
  
  // Database fields
  id: UUID,
  user_id: UUID,
  status: "pending_approval" | "approved" | "rejected" | "synced" | "error",
  confidence: number,
  extraction_method?: "deterministic" | "llm" | "hybrid" | null,
  
  // Source tracking
  message_id?: UUID,
  provider: string,
  
  // Calendar sync
  calendar_id?: UUID,
  external_event_id?: string,  // Google Calendar event ID
  synced_at?: datetime,
  
  // Audit
  created_at: datetime,
  updated_at: datetime,
  approved_at?: datetime,
  rejected_at?: datetime
}
```

## Field Descriptions

### Required Fields

#### `type`
- **Values**: `"event"` (time-bound), `"task"` (deadline/checklist item)
- **Usage**: Determines calendar rendering (event vs todo list)

#### `title`
- **Length**: 1-500 characters
- **Examples**: "Exam appointment", "Team standup", "Flight UA123: SFO → JFK"
- **Validation**: Non-empty, trimmed

#### `start`
- **Format**: ISO-8601 with timezone: `2025-11-04T08:50:00+01:00`
- **Validation**: Valid datetime, not in distant past (> 1 year ago)

### Optional Fields

#### `end`
- **Format**: Same as `start`
- **Validation**: If provided, must be after `start`
- **Default Behavior**: If null, calendar providers use 1-hour duration for events

#### `allday`
- **Type**: Boolean
- **Default**: `false`
- **Usage**: When `true`, ignore time portion of `start`/`end`

#### `timezone`
- **Format**: IANA timezone string
- **Examples**: `"Europe/Budapest"`, `"America/New_York"`, `"UTC"`
- **Default**: `"Europe/Budapest"`
- **Validation**: Must be valid IANA timezone

#### `location`
- **Max Length**: 500 characters
- **Examples**: "Room A-123", "1234 Main St, Budapest", "Building B, 2nd floor"
- **Usage**: Physical location (use `online_url` for virtual meetings)

#### `online_url`
- **Format**: Valid URL
- **Examples**: 
  - `"https://zoom.us/j/1234567890"`
  - `"https://meet.google.com/abc-defg-hij"`
  - `"https://teams.microsoft.com/l/meetup-join/..."`
- **Usage**: Virtual meeting link (takes precedence over `location` in some UIs)

#### `notes`
- **Format**: Free-form text (supports line breaks)
- **Usage**: Additional context, agenda, booking references, etc.

#### `attendees`
- **Format**: Array of `{name, email}` objects
- **Validation**: Each email must be valid format
- **Usage**: For meeting invites, calendar sharing

#### `reminders`
- **Format**: Array of `{method, minutes}` objects
- **Smart Defaults** (by label):
  - **Exam**: T-1 day, T-2h, T-30m
  - **Flight**: T-24h (check-in), T-3h, T-1h
  - **Meeting**: T-15m
  - **Deadline**: T-1 day, T-6h

#### `labels`
- **Format**: Array of strings
- **Common Values**: `"exam"`, `"meeting"`, `"deadline"`, `"flight"`, `"travel"`, `"payment"`
- **Usage**: Color-coding, filtering, reminder defaults

#### `recurrence`
- **Format**: RRULE string (RFC 5545)
- **Examples**:
  - Daily for 5 days: `"FREQ=DAILY;COUNT=5"`
  - Weekly on Mondays: `"FREQ=WEEKLY;BYDAY=MO"`
  - Monthly on 15th: `"FREQ=MONTHLY;BYMONTHDAY=15"`

## Validation Rules

### At Extraction Time

1. **Title**: Required, non-empty, trimmed
2. **Start**: Required, valid datetime
3. **End**: If provided, must be > start
4. **Timezone**: Must be valid IANA string or fallback to default
5. **Attendees**: Each must have valid email
6. **Reminders**: minutes >= 0

### At Approval Time

User can modify any field before approval. Same validation applies.

### At Sync Time

- Convert to calendar provider format (Google Calendar, etc.)
- Handle timezone conversions
- Validate external constraints (e.g., Google Calendar max title length)

## Examples

### 1. Hungarian Exam Schedule

**Extracted from image:**
```
2025.11.04.
Balogh Csaba — 8 óra 50 perc
```

**Event Schema:**
```json
{
  "type": "event",
  "title": "Exam appointment",
  "start": "2025-11-04T08:50:00+01:00",
  "end": "2025-11-04T09:20:00+01:00",
  "allday": false,
  "timezone": "Europe/Budapest",
  "location": null,
  "online_url": null,
  "notes": "Imported from schedule. Matched name: Balogh Csaba.",
  "attendees": [],
  "reminders": [
    {"method": "popup", "minutes": 1440},
    {"method": "popup", "minutes": 120},
    {"method": "popup", "minutes": 30}
  ],
  "labels": ["exam"],
  "recurrence": null
}
```

### 2. Flight Booking Email

**Extracted from email:**
```
Flight UA123 from SFO to JFK on 12/15/2024 at 10:30 AM
```

**Event Schema:**
```json
{
  "type": "event",
  "title": "Flight UA123: SFO → JFK",
  "start": "2024-12-15T10:30:00-08:00",
  "end": "2024-12-15T18:30:00-05:00",
  "allday": false,
  "timezone": "America/Los_Angeles",
  "location": "San Francisco International Airport",
  "online_url": null,
  "notes": "Flight from SFO to JFK. Check in 24h before.",
  "attendees": [],
  "reminders": [
    {"method": "popup", "minutes": 1440},
    {"method": "popup", "minutes": 180},
    {"method": "popup", "minutes": 60}
  ],
  "labels": ["flight", "travel"],
  "recurrence": null
}
```

### 3. Recurring Team Meeting

**Extracted from calendar invite:**
```
Weekly team standup every Monday at 9 AM
```

**Event Schema:**
```json
{
  "type": "event",
  "title": "Weekly team standup",
  "start": "2024-11-04T09:00:00+01:00",
  "end": "2024-11-04T09:30:00+01:00",
  "allday": false,
  "timezone": "Europe/Budapest",
  "location": null,
  "online_url": "https://meet.google.com/abc-defg-hij",
  "notes": "Weekly team sync",
  "attendees": [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"}
  ],
  "reminders": [
    {"method": "popup", "minutes": 15}
  ],
  "labels": ["meeting"],
  "recurrence": "FREQ=WEEKLY;BYDAY=MO"
}
```

### 4. All-Day Task

**Extracted from to-do list:**
```
Project proposal due December 20th
```

**Event Schema:**
```json
{
  "type": "task",
  "title": "Project proposal",
  "start": "2024-12-20T23:59:00+01:00",
  "end": null,
  "allday": true,
  "timezone": "Europe/Budapest",
  "location": null,
  "online_url": null,
  "notes": null,
  "attendees": [],
  "reminders": [
    {"method": "popup", "minutes": 1440},
    {"method": "popup", "minutes": 360}
  ],
  "labels": ["deadline"],
  "recurrence": null
}
```

## Google Calendar Mapping

EventHint schema → Google Calendar API:

| EventHint | Google Calendar |
|-----------|----------------|
| `title` | `summary` |
| `notes` | `description` |
| `start` | `start.dateTime` or `start.date` (if allday) |
| `end` | `end.dateTime` or `end.date` |
| `timezone` | `start.timeZone` |
| `location` | `location` |
| `online_url` | Appended to `description` |
| `attendees` | `attendees` |
| `reminders` | `reminders.overrides` |
| `recurrence` | `recurrence` (array of RRULE) |
| `labels` | `colorId` (mapped) |

## Confidence Scoring

Events include a `confidence` score (0.0-1.0):

| Score | Meaning |
|-------|---------|
| 0.9-1.0 | Very confident (auto-approve candidate) |
| 0.7-0.9 | Confident (user approval recommended) |
| 0.5-0.7 | Uncertain (needs review) |
| 0.0-0.5 | Low confidence (manual editing likely) |

**Factors:**
- Has clear date/time: +0.3
- Has title: +0.2
- Has location: +0.1
- Deterministic extraction: +0.2
- LLM extraction: +0.15
- Trusted sender: +0.05
- OCR confidence: multiplier

## Best Practices for Extractors

1. **Always set confidence**: Calculate based on extraction method and data quality
2. **Preserve source data**: Store original text in `notes`
3. **Use appropriate labels**: Enables smart reminders
4. **Set timezone explicitly**: Don't assume UTC or local
5. **Validate before outputting**: Ensure all required fields are present
6. **Include extraction metadata**: Helps debugging and improvement


