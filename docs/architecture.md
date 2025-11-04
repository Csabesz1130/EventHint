# EventHint Architecture

## Overview

EventHint is an intelligent inbox-to-calendar system that automatically extracts events from emails, PDFs, and images, presents them for one-click approval, and syncs them to user calendars.

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │ EventCard    │  │EventApproval │          │
│  │ (Inbox View) │  │ (One-Click)  │  │  (Editor)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API (FastAPI)
┌───────────────────────────┴─────────────────────────────────────┐
│                        Backend (Python)                          │
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│  │   Gmail     │     │  File       │     │  Webhooks   │      │
│  │  Connector  │     │  Upload     │     │  (Push)     │      │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘      │
│         │                    │                    │              │
│         └────────────────────┴────────────────────┘              │
│                              │                                   │
│                    ┌─────────▼──────────┐                       │
│                    │   Message Queue    │                       │
│                    │    (Celery)        │                       │
│                    └─────────┬──────────┘                       │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         │                    │                    │             │
│  ┌──────▼──────┐    ┌───────▼────────┐   ┌──────▼──────┐     │
│  │     OCR     │    │  Extraction    │   │  Calendar   │     │
│  │  (Dual)     │───▶│   Engine       │───▶│   Writer    │     │
│  │ Tesseract   │    │ (Deterministic │   │  (Google)   │     │
│  │ + Vision    │    │   + LLM)       │   └─────────────┘     │
│  └─────────────┘    └────────────────┘                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │             Database (PostgreSQL + pgvector)              │ │
│  │  Users | Events | Messages | Calendars                    │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Ingestion

**Gmail Push Notifications:**
```
Gmail → Pub/Sub → Webhook → FastAPI → Celery Task
```

**File Upload:**
```
User → Upload → FastAPI → Save to Disk → Celery Task
```

### 2. Processing Pipeline

```
1. Fetch/Load Message
   ↓
2. OCR (if attachments)
   - Try Tesseract first (free)
   - Fallback to Vision if confidence < 75%
   ↓
3. Extract Text
   - Clean HTML → Plain text
   - Concatenate: email body + OCR text
   ↓
4. Deterministic Extraction
   - Hungarian patterns (dates: YYYY.MM.DD., times: X óra Y perc)
   - English patterns (meetings, flights, deadlines)
   - Generic dateparser fallback
   ↓
5. LLM Extraction (parallel)
   - GPT-4o with JSON schema
   - Structured output validation
   ↓
6. Merge & Validate
   - Deduplicate by time + title similarity
   - Prefer deterministic over LLM
   - Calculate confidence scores
   ↓
7. Create Draft Events
   - Status: pending_approval or approved (auto)
   - Store in DB with metadata
   ↓
8. Notify Frontend
   - Poll or WebSocket (future)
```

### 3. Approval & Sync

```
User Views Dashboard
   ↓
Sees Pending Events (EventCard)
   ↓
Clicks Approve (or Edit → Save → Approve)
   ↓
API Updates Event Status
   ↓
Celery Task: Sync to Calendar
   ↓
Google Calendar API: Create Event
   ↓
Update Event with external_event_id
   ↓
Status: synced
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+ (async, high performance)
- **Database**: PostgreSQL 16 with pgvector extension
- **Caching**: Redis 7
- **Task Queue**: Celery with Redis broker
- **ORM**: SQLAlchemy 2.0 (async capable)
- **Migrations**: Alembic

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: TanStack Query (server state)
- **Styling**: Tailwind CSS + shadcn/ui patterns
- **Routing**: React Router v6

### AI/ML
- **OCR**: Tesseract 5 + Google Cloud Vision API
- **LLM**: OpenAI GPT-4o with JSON mode
- **Date Parsing**: dateparser, python-dateutil, custom regex
- **Language Detection**: Built-in (CLD3 future)

### APIs
- **Gmail**: Google API Client (OAuth2, watch channels)
- **Calendar**: Google Calendar API v3
- **Future**: Microsoft Graph, CalDAV

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Orchestration**: (Production: Kubernetes ready)
- **Observability**: OpenTelemetry (structured logging)
- **Secrets**: Environment variables (KMS in production)

## Security Architecture

### Authentication
- **OAuth 2.0**: Google (authorization_code flow)
- **JWT**: Internal session tokens (HS256)
- **Token Storage**: Encrypted (Fernet) in PostgreSQL
- **Scopes**: Minimal (gmail.readonly, calendar.events)

### Data Protection
- **Encryption at Rest**: Database-level + application-level for tokens
- **Encryption in Transit**: HTTPS/TLS everywhere
- **PII Handling**: Redacted from logs, GDPR-compliant deletion
- **Tenant Isolation**: Row-level user_id filtering

### API Security
- **Rate Limiting**: (TODO: Redis-based)
- **Input Validation**: Pydantic schemas everywhere
- **SQL Injection**: Prevented by SQLAlchemy ORM
- **XSS**: React auto-escaping + CSP headers (TODO)

## Scalability Considerations

### Horizontal Scaling
- **API**: Stateless FastAPI instances behind load balancer
- **Workers**: Multiple Celery workers (CPU-bound OCR, I/O-bound API calls)
- **Database**: Read replicas for queries, write leader for mutations
- **Redis**: Sentinel for HA

### Performance Optimization
- **OCR Caching**: Store results to avoid re-processing
- **LLM Caching**: Dedupe similar prompts (embeddings)
- **Database Indexes**: user_id, status, created_at
- **CDN**: Static assets (frontend) via CDN
- **Lazy Loading**: Paginate events list

### Cost Optimization
- **OCR Strategy**: Tesseract first (free), Vision on-demand
- **LLM Strategy**: Deterministic first, GPT-4o fallback
- **Batching**: Batch API calls where possible
- **Compression**: Gzip responses, compact JSON

## Monitoring & Observability

### Metrics
- **API**: Request rate, latency, error rate (RED)
- **Workers**: Task duration, queue depth, failure rate
- **OCR**: Success rate, confidence distribution
- **LLM**: Token usage, cost, extraction accuracy

### Logging
- **Structured JSON**: All logs with correlation IDs
- **Levels**: DEBUG (dev), INFO (prod), ERROR (always)
- **Sensitive Data**: Redact emails, tokens, PII

### Tracing
- **OpenTelemetry**: End-to-end request tracing
- **Spans**: API → Task → OCR → Extraction → Calendar

### Alerting
- **Critical**: Auth failures, database down, calendar sync failures
- **Warning**: High error rate, queue backlog, low OCR confidence
- **Info**: Daily summaries, usage stats

## Deployment Architecture (Production)

```
┌──────────────────────────────────────────────────────────┐
│                    Load Balancer (nginx)                  │
└─────────────────────┬────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │                           │
┌───────▼──────┐            ┌──────▼───────┐
│  Frontend    │            │   Backend    │
│  (CDN)       │            │  (API x3)    │
└──────────────┘            └──────┬───────┘
                                   │
                      ┌────────────┼────────────┐
                      │                         │
              ┌───────▼────────┐      ┌────────▼────────┐
              │   PostgreSQL   │      │  Celery Workers │
              │   (Primary +   │      │     (x5)        │
              │   Read Replica)│      └─────────────────┘
              └────────────────┘
                      │
              ┌───────▼────────┐
              │     Redis      │
              │   (Sentinel)   │
              └────────────────┘
```

## Future Enhancements

### Phase 2
- [ ] Outlook/Office 365 integration
- [ ] Apple Calendar (CalDAV)
- [ ] Batch event import from tables
- [ ] Template gallery (user-submitted)

### Phase 3
- [ ] Mobile apps (iOS/Android)
- [ ] Gmail Add-on (in-inbox approval)
- [ ] Outlook Actionable Messages
- [ ] Team collaboration

### Phase 4
- [ ] Advanced recurrence rules
- [ ] Conflict detection & resolution
- [ ] Smart scheduling suggestions
- [ ] Multi-calendar sync
- [ ] Group event matching

