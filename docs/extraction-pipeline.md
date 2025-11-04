# Extraction Pipeline

## Overview

The extraction pipeline is the core of EventHint's intelligence. It takes raw input (email text, OCR'd images, PDFs) and outputs structured calendar events with high accuracy using a hybrid approach.

## Pipeline Architecture

```
Input (Email/File)
    ↓
┌───────────────────────────────────┐
│  1. Pre-processing                │
│  - Normalize MIME                 │
│  - Extract attachments            │
│  - Clean HTML → Plain text        │
└───────────┬───────────────────────┘
            ↓
┌───────────────────────────────────┐
│  2. OCR (if attachments)          │
│  - Tesseract first                │
│  - Vision fallback                │
│  - Confidence: 0.75 threshold     │
└───────────┬───────────────────────┘
            ↓
┌───────────────────────────────────┐
│  3. Deterministic Extraction      │
│  - Language detection             │
│  - Pattern matching (regex)       │
│  - dateparser                     │
└───────────┬───────────────────────┘
            │
            ├──────────────┐
            ↓              ↓
┌───────────────────┐  ┌───────────────────┐
│  4a. Hungarian    │  │  4b. English      │
│  - YYYY.MM.DD.    │  │  - MM/DD/YYYY     │
│  - X óra Y perc   │  │  - Meetings       │
│  - Neptun ID      │  │  - Flights        │
└───────────┬───────┘  └───────┬───────────┘
            │                  │
            └────────┬─────────┘
                     ↓
         ┌───────────────────────────┐
         │  5. LLM Extraction        │
         │  (parallel)               │
         │  - GPT-4o JSON mode       │
         │  - Structured output      │
         │  - Context-aware          │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │  6. Merge & Validate      │
         │  - Deduplicate            │
         │  - Prefer deterministic   │
         │  - Calculate confidence   │
         │  - Validate schema        │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │  7. Create Draft Events   │
         │  - Status: pending/auto   │
         │  - Store in DB            │
         └───────────────────────────┘
```

## Step-by-Step Breakdown

### 1. Pre-processing

**Input**: Raw email message or uploaded file  
**Output**: Clean text + attachments

```python
def preprocess_message(message):
    # 1. Extract headers
    subject = extract_subject(message)
    sender = extract_sender(message)
    
    # 2. Extract body
    if message.has_html:
        text = html_to_text(message.html)
    else:
        text = message.text
    
    # 3. Clean
    text = clean_email_text(text)  # Remove signatures, quotes
    
    # 4. Extract attachments
    attachments = extract_attachments(message)
    
    return {
        'subject': subject,
        'sender': sender,
        'text': text,
        'attachments': attachments
    }
```

### 2. OCR Processing

**Input**: Image/PDF attachments  
**Output**: Extracted text with confidence

```python
async def process_attachments(attachments):
    full_text = ""
    
    for attachment in attachments:
        if is_image(attachment) or is_pdf(attachment):
            # Smart OCR: Tesseract → Vision fallback
            ocr_result = await extract_text_smart(attachment.bytes)
            
            attachment.ocr_text = ocr_result.text
            attachment.ocr_confidence = ocr_result.confidence
            
            full_text += f"\n\n--- {attachment.filename} ---\n"
            full_text += ocr_result.text
    
    return full_text
```

**OCR Strategy:**
- Try Tesseract first (free, fast)
- If confidence < 75%, use Google Vision (premium, accurate)
- Cache results to avoid re-processing

### 3. Language Detection

```python
def detect_language(text):
    # Check for language-specific markers
    if contains_hungarian_markers(text):
        return 'hungarian'
    elif contains_english_markers(text):
        return 'english'
    else:
        # Use dateparser's language detection
        return dateparser.detect_language(text)
```

### 4. Deterministic Extraction

#### 4a. Hungarian Patterns

**Exam Schedule Example:**

```
2025.11.04.
Balogh Csaba — 8 óra 50 perc
Kovács János — 9 óra 30 perc
```

**Pattern Matching:**
```python
# Date header
DATE_PATTERN = r"(?P<y>\d{4})\.(?P<m>\d{2})\.(?P<d>\d{2})\."

# Time
TIME_PATTERN = r"(?P<h>\d{1,2})\s*óra\s*(?P<m>\d{1,2})\s*perc"

def extract_hungarian_exam_schedule(text, user_name, neptun_id):
    # Find date
    date_match = re.search(DATE_PATTERN, text)
    base_date = datetime(int(date_match['y']), int(date_match['m']), int(date_match['d']))
    
    events = []
    for line in text.split('\n'):
        # Match user
        if user_name in line or neptun_id in line:
            time_match = re.search(TIME_PATTERN, line)
            if time_match:
                start = base_date.replace(
                    hour=int(time_match['h']),
                    minute=int(time_match['m'])
                )
                
                events.append({
                    'title': 'Exam appointment',
                    'start': start.isoformat(),
                    'end': (start + timedelta(minutes=30)).isoformat(),
                    'timezone': 'Europe/Budapest',
                    'labels': ['exam']
                })
    
    return events
```

#### 4b. English Patterns

**Meeting Example:**
```
Meeting: Project sync on 11/04/2024 at 2:00 PM
```

**Pattern Matching:**
```python
MEETING_PATTERN = r"(?i)meeting[:\s]+([^\.]+?)(?:\s+on\s+)(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})(?:\s+at\s+)(\d{1,2}:\d{2}\s*(?:AM|PM)?)"

def extract_meeting(text):
    match = re.search(MEETING_PATTERN, text)
    if match:
        title, date_str, time_str = match.groups()
        dt = dateparser.parse(f"{date_str} {time_str}")
        
        return {
            'title': title + ' meeting',
            'start': dt.isoformat(),
            'end': (dt + timedelta(hours=1)).isoformat(),
            'labels': ['meeting']
        }
```

**Flight Example:**
```
Flight UA123 from SFO to JFK on 12/15/2024 at 10:30 AM
```

```python
FLIGHT_PATTERN = r"(?i)(?:flight\s+)?([A-Z]{2}\s*\d{3,4}).*?(?:from\s+)?([A-Z]{3}).*?(?:to\s+)?([A-Z]{3}).*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s+(?:at\s+)?(\d{1,2}:\d{2}\s*(?:AM|PM)?)"

def extract_flight(text):
    match = re.search(FLIGHT_PATTERN, text)
    if match:
        flight_num, origin, dest, date_str, time_str = match.groups()
        dt = dateparser.parse(f"{date_str} {time_str}")
        
        return {
            'title': f'Flight {flight_num}: {origin} → {dest}',
            'start': dt.isoformat(),
            'labels': ['flight', 'travel'],
            'reminders': [
                {'method': 'popup', 'minutes': 1440},  # 24h
                {'method': 'popup', 'minutes': 180},   # 3h
                {'method': 'popup', 'minutes': 60}     # 1h
            ]
        }
```

### 5. LLM Extraction

**When to use:**
- Deterministic methods found nothing
- Text is messy or non-standard format
- Natural language descriptions

**Prompt Engineering:**
```python
SYSTEM_PROMPT = """You extract calendar events from text.
Output JSON matching this schema:
{
  "events": [{
    "type": "event" | "task",
    "title": "string",
    "start": "ISO-8601",
    "end": "ISO-8601 or null",
    ...
  }]
}

Rules:
- Extract ALL events
- Honor locales (e.g., "YYYY.MM.DD." = Europe/Budapest)
- Never invent locations
- Add smart reminders by type
"""

def extract_with_llm(text, timezone, context):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Text: {text}\n\nTimezone: {timezone}"}
        ],
        temperature=0.1,  # Low for consistency
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result['events']
```

### 6. Merge & Validate

**Deduplication Strategy:**
```python
def deduplicate_events(events):
    # Group by rounded start time (15-min buckets)
    groups = group_by_time(events, bucket_size=15)
    
    unique = []
    for group in groups:
        if len(group) == 1:
            unique.append(group[0])
        else:
            # Merge similar events
            merged = merge_similar_in_group(group)
            unique.extend(merged)
    
    return unique

def merge_similar_in_group(events):
    # Check title similarity
    for e1, e2 in combinations(events, 2):
        if titles_similar(e1['title'], e2['title']):
            # Prefer deterministic over LLM
            if e1.get('_source') == 'deterministic':
                base = e1
                supplement = e2
            else:
                base = e2
                supplement = e1
            
            # Merge missing fields
            for key, value in supplement.items():
                if key not in base or not base[key]:
                    base[key] = value
            
            return [base]
    
    return events
```

**Confidence Calculation:**
```python
def calculate_confidence(event, context):
    confidence = 0.0
    
    # Date/time presence
    if event['start']:
        confidence += 0.3
    
    # Title quality
    if len(event['title']) > 3:
        confidence += 0.2
    
    # Location
    if event.get('location') or event.get('online_url'):
        confidence += 0.1
    
    # Extraction method
    if event.get('_source') == 'deterministic':
        confidence += 0.2
    elif event.get('_source') == 'llm':
        confidence += 0.15
    
    # Trusted sender
    if context.get('trusted_sender'):
        confidence += 0.05
    
    # OCR confidence
    if 'ocr_confidence' in context:
        confidence *= context['ocr_confidence']
    
    return min(confidence, 1.0)
```

### 7. Auto-Approval Logic

```python
def should_auto_approve(event, user, context):
    if not user.auto_approve_enabled:
        return False
    
    confidence = event.get('confidence', 0.0)
    
    # Very high confidence
    if confidence >= 0.9:
        return True
    
    # Trusted sender + good confidence
    if context.get('trusted_sender') and confidence >= 0.7:
        return True
    
    return False
```

## Performance Considerations

### Caching
- **OCR Results**: Cache by file hash (SHA256)
- **LLM Results**: Cache by text hash + prompt version
- **Parsed Dates**: Cache dateparser results

### Batching
- Process multiple attachments in parallel
- Batch LLM calls when possible (multiple events in one prompt)

### Timeouts
- OCR: 30 seconds per file
- LLM: 60 seconds per call
- Total pipeline: 5 minutes max

## Error Handling

```python
try:
    deterministic_events = extract_deterministic(text)
except Exception as e:
    logger.warning(f"Deterministic extraction failed: {e}")
    deterministic_events = []

try:
    llm_events = extract_llm(text)
except Exception as e:
    logger.warning(f"LLM extraction failed: {e}")
    llm_events = []

if not deterministic_events and not llm_events:
    # No events found
    return []

# Continue with merge...
```

## Testing Strategy

### Unit Tests
- Test each pattern matcher individually
- Test date parsing edge cases
- Test merge logic

### Integration Tests
- End-to-end pipeline with sample inputs
- Test OCR fallback behavior
- Test LLM timeout handling

### Evaluation Metrics
- **Precision**: % of extracted events that are correct
- **Recall**: % of actual events that were extracted
- **F1 Score**: Harmonic mean of precision and recall
- **Confidence Calibration**: Does 0.8 confidence mean 80% accurate?

## Future Improvements

1. **Machine Learning Classifier**: Predict event type from text features
2. **Active Learning**: User corrections → fine-tune patterns
3. **Multi-language Support**: Add more language-specific patterns
4. **Template Learning**: Automatically detect recurring formats
5. **Contextual Understanding**: Use conversation history for better extraction

