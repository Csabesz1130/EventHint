# EventHint: Intelligent Inbox-to-Calendar System

**Parse anything → One-click approve → Calendar magic ✨**

EventHint automatically extracts events and tasks from emails, PDFs, images, and screenshots, then lets you add them to your calendar with a single click. No more manual data entry.

## Features

- 📧 **Gmail Integration**: Automatic email monitoring with push notifications
- 🔍 **Smart Extraction**: Hybrid OCR (Tesseract + Google Vision) and LLM-powered parsing
- 🌍 **Multi-language Support**: Hungarian, English, and more
- 📅 **One-Click Approval**: Review and approve events with inline editing
- ⏰ **Smart Reminders**: Context-aware reminder suggestions (exams, flights, meetings)
- 🔄 **Google Calendar Sync**: Direct integration with smart conflict detection
- 🎯 **High Accuracy**: Deterministic parsers + GPT-4o for complex formats

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Google Cloud account (for OAuth & optional Vision API)
- OpenAI API key

### Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Fill in your credentials in `.env`:
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (from Google Cloud Console)
   - `OPENAI_API_KEY` (from OpenAI)
   - `SECRET_KEY` (generate with `openssl rand -hex 32`)

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Development Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Architecture

```
┌─────────────┐
│   Gmail     │
│  Outlook    │◄──── Email connectors with webhooks
└─────┬───────┘
      │
      ▼
┌─────────────────────────────────────────┐
│         Ingestion & Processing          │
│  ┌──────────┐  ┌─────────┐  ┌────────┐ │
│  │   OCR    │  │  Parser │  │  LLM   │ │
│  │Tesseract │  │ dateutil│  │ GPT-4o │ │
│  │ +Vision  │  │  regex  │  │        │ │
│  └──────────┘  └─────────┘  └────────┘ │
└─────────────┬───────────────────────────┘
              │
              ▼
       ┌──────────────┐
       │  Event Draft │
       │  (pending)   │
       └──────┬───────┘
              │
              ▼
    ┌──────────────────┐
    │  Approval Card   │◄──── User reviews & approves
    │  (Web/Email)     │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────┐
    │   Calendar   │
    │    (Google)  │
    └──────────────┘
```

## Example Use Cases

### Hungarian Exam Schedule
Upload a screenshot with text like:
```
2025.11.04.
Balogh Csaba — 8 óra 50 perc
```
→ Automatically creates: "Exam appointment" on Nov 4, 2025 at 8:50 AM (Budapest time)

### Flight Booking Email
Receives email with flight details
→ Extracts: flight number, departure/arrival times, terminals
→ Adds smart reminders: T-24h (check-in), T-3h, T-1h

### Meeting Invite
Parses meeting invites with Zoom links
→ Creates event with online meeting URL and attendees

## Tech Stack

**Backend**: Python, FastAPI, PostgreSQL, Redis, Celery, SQLAlchemy  
**Frontend**: React, TypeScript, Vite, TanStack Query, Tailwind CSS  
**OCR**: Tesseract, Google Cloud Vision  
**AI**: OpenAI GPT-4o, dateparser, custom regex patterns  
**Calendar**: Google Calendar API  

## Project Structure

```
io0py/
├── backend/          # Python FastAPI backend
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic (OCR, extraction, calendar)
│   │   └── tasks/    # Celery tasks
│   └── alembic/      # Database migrations
├── frontend/         # React TypeScript frontend
│   └── src/
│       ├── pages/    # Main views
│       └── components/ # Reusable UI components
└── docs/             # Documentation
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Specification](docs/api-spec.md)
- [Event Schema Reference](docs/event-schema.md)
- [Extraction Pipeline](docs/extraction-pipeline.md)
- [OCR Enhancement Guide](docs/ocr-guide.md)
- [Deployment Guide](docs/deployment.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Security

- OAuth 2.0 with minimal scopes
- Encrypted token storage
- PII redaction in logs
- Per-tenant data isolation

## Roadmap

- [ ] Outlook/Office 365 support
- [ ] Apple Calendar (CalDAV)
- [ ] Mobile apps (iOS/Android)
- [ ] Gmail Add-on for in-inbox approval
- [ ] Batch event import from tables
- [ ] Template gallery (universities, airlines)
- [ ] Team collaboration features
- [ ] Advanced recurrence rules

## Support

For issues and questions, please open a GitHub issue.

---

Built with ❤️ for people who hate manual calendar entry

