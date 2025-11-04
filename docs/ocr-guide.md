# OCR Enhancement Guide

## Overview

EventHint uses a dual-OCR strategy to balance cost, speed, and accuracy:
1. **Tesseract** (free, local): First attempt
2. **Google Cloud Vision** (premium, cloud): Fallback for low confidence

This guide explains how to optimize both and when to use each.

## Tesseract Setup

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hun
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Docker:**
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hun \
    tesseract-ocr-eng \
    libtesseract-dev
```

### Language Packs

EventHint supports:
- **English** (eng): Default, high accuracy
- **Hungarian** (hun): For Hungarian exam schedules
- **Multi-language** (eng+hun): Both simultaneously

**Add more languages:**
```bash
# German
sudo apt-get install tesseract-ocr-deu

# Spanish
sudo apt-get install tesseract-ocr-spa

# Check installed languages
tesseract --list-langs
```

### Configuration

**Python Integration:**
```python
import pytesseract
from PIL import Image

# Set Tesseract path (if not in PATH)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Basic OCR
text = pytesseract.image_to_string(image, lang='eng+hun')

# With confidence data
data = pytesseract.image_to_data(image, lang='eng+hun', output_type=pytesseract.Output.DICT)
```

### Performance Tuning

#### 1. Image Pre-processing

**Improve accuracy with:**
```python
from PIL import Image, ImageEnhance, ImageFilter

def preprocess_for_ocr(image):
    # Convert to grayscale
    image = image.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)
    
    # Resize if too small (< 300 DPI equivalent)
    width, height = image.size
    if width < 1000:
        scale = 1000 / width
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    
    # Threshold (binarize)
    threshold = 128
    image = image.point(lambda p: 255 if p > threshold else 0, mode='1')
    
    return image
```

#### 2. Page Segmentation Mode

```python
# Try different PSM modes for different layouts
custom_config = r'--psm 6'  # Assume uniform block of text
text = pytesseract.image_to_string(image, config=custom_config)
```

**PSM Modes:**
- `0`: Orientation and script detection (OSD) only
- `1`: Automatic page segmentation with OSD
- `3`: Fully automatic (default)
- `4`: Single column of variable sizes
- `6`: Assume uniform block of text
- `7`: Treat image as single text line
- `11`: Sparse text (find as much text as possible)

#### 3. Character Whitelist

For structured data (dates, times):
```python
# Only digits and specific chars
config = r'--psm 6 -c tessedit_char_whitelist=0123456789./:óperc'
text = pytesseract.image_to_string(image, config=config)
```

## Google Cloud Vision

### Setup

**1. Create GCP Project**
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth login

# Create project
gcloud projects create eventhint-ocr

# Enable Vision API
gcloud services enable vision.googleapis.com --project=eventhint-ocr
```

**2. Service Account**
```bash
# Create service account
gcloud iam service-accounts create eventhint-vision \
    --display-name="EventHint Vision OCR"

# Grant permissions
gcloud projects add-iam-policy-binding eventhint-ocr \
    --member="serviceAccount:eventhint-vision@eventhint-ocr.iam.gserviceaccount.com" \
    --role="roles/cloudvision.user"

# Create key
gcloud iam service-accounts keys create ~/eventhint-vision-key.json \
    --iam-account=eventhint-vision@eventhint-ocr.iam.gserviceaccount.com
```

**3. Set Environment Variable**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/eventhint-vision-key.json
```

### Usage

```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()

# Detect text
image = vision.Image(content=image_bytes)
response = client.document_text_detection(image=image)

# Full text
full_text = response.full_text_annotation.text

# With confidence per word
for page in response.full_text_annotation.pages:
    for block in page.blocks:
        for paragraph in block.paragraphs:
            for word in paragraph.words:
                word_text = ''.join([symbol.text for symbol in word.symbols])
                confidence = word.confidence
```

### Advanced Features

#### Table Detection

```python
def detect_tables(image_bytes):
    from google.cloud import vision
    
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    
    # Use DOCUMENT_TEXT_DETECTION for layout
    response = client.document_text_detection(image=image)
    
    # Extract blocks that look like tables
    tables = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            # Heuristic: multiple paragraphs in a grid
            if len(block.paragraphs) > 2:
                tables.append(block)
    
    return tables
```

#### Handwriting Recognition

Vision API has better handwriting support than Tesseract:
```python
# No special config needed - it's automatic
response = client.document_text_detection(image=image)
```

## Smart OCR Router

### Decision Logic

```python
async def extract_text_smart(image_bytes, prefer_free=True):
    if prefer_free:
        # Try Tesseract first
        tesseract = TesseractOCR()
        result = tesseract.extract(image_bytes)
        
        if result.confidence >= 0.75:
            return result  # Good enough
        
        logger.info(f"Tesseract confidence {result.confidence:.2f} < 0.75, trying Vision")
    
    # Use Google Vision
    if settings.ENABLE_GOOGLE_VISION:
        vision = GoogleVisionOCR()
        return vision.extract(image_bytes)
    
    # Fallback to Tesseract even if low confidence
    return result
```

### Confidence Threshold Tuning

Adjust `OCR_CONFIDENCE_THRESHOLD` based on:
- **Cost sensitivity**: Higher threshold (0.85) → more Vision API calls
- **Accuracy needs**: Lower threshold (0.65) → more free Tesseract
- **Document type**: Printed text → lower OK, handwriting → higher needed

## Cost Optimization

### Google Cloud Vision Pricing (as of 2024)

- First 1,000 requests/month: **Free**
- 1,001 - 5,000,000: **$1.50 per 1,000**
- 5,000,001+: **$0.60 per 1,000**

### Cost-Saving Strategies

1. **Cache Results**: Store OCR text with file hash
```python
import hashlib

def get_cached_ocr(image_bytes):
    file_hash = hashlib.sha256(image_bytes).hexdigest()
    
    # Check cache (Redis or DB)
    cached = cache.get(f"ocr:{file_hash}")
    if cached:
        return cached
    
    # Perform OCR
    result = extract_text_smart(image_bytes)
    
    # Cache for 30 days
    cache.set(f"ocr:{file_hash}", result, ttl=30*24*3600)
    return result
```

2. **Batch Processing**: Process multiple images in one Vision API call
```python
def batch_ocr(image_list):
    requests = [
        vision.AnnotateImageRequest(
            image=vision.Image(content=img_bytes),
            features=[vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]
        )
        for img_bytes in image_list
    ]
    
    response = client.batch_annotate_images(requests=requests)
    return [r.full_text_annotation.text for r in response.responses]
```

3. **Selective Vision**: Only use Vision for critical documents
```python
def is_critical_document(filename):
    # Exam schedules, flight tickets, etc.
    critical_keywords = ['exam', 'flight', 'ticket', 'booking', 'schedule']
    return any(kw in filename.lower() for kw in critical_keywords)

if is_critical_document(filename) or tesseract_confidence < 0.5:
    result = vision_ocr(image)
else:
    result = tesseract_ocr(image)
```

## Improving Tesseract Accuracy

### Training Custom Models

For domain-specific text (e.g., Hungarian exam schedules):

```bash
# 1. Generate training data
# Create box files with ground truth

# 2. Train
tesseract input.tif output box.train
unicharset_extractor *.box
shapeclustering -F font_properties -U unicharset *.tr
mftraining -F font_properties -U unicharset -O unicharset *.tr
cntraining *.tr

# 3. Combine
combine_tessdata hun_exam
```

### Using layoutparser

For complex layouts:
```python
import layoutparser as lp

# Load model
model = lp.Detectron2LayoutModel('lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config')

# Detect layout
layout = model.detect(image)

# Extract text blocks in reading order
for block in layout:
    if block.type == 'Text':
        text = pytesseract.image_to_string(
            image.crop(block.coordinates)
        )
```

## Monitoring & Metrics

### Track OCR Performance

```python
import logging

logger = logging.getLogger('eventhint.ocr')

def track_ocr_usage(provider, confidence, cost):
    logger.info(
        "OCR completed",
        extra={
            'provider': provider,
            'confidence': confidence,
            'cost': cost,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
```

### Dashboards

Monitor:
- **Tesseract success rate**: % with confidence >= 0.75
- **Vision API usage**: Calls per day, cost per month
- **Confidence distribution**: Histogram
- **Processing time**: P50, P95, P99

## Troubleshooting

### Low Tesseract Confidence

**Causes:**
- Poor image quality (blurry, low resolution)
- Unusual fonts
- Skewed or rotated text
- Background noise

**Solutions:**
1. Pre-process image (see above)
2. Deskew: `image.rotate(-angle, expand=True)`
3. Denoise: `image.filter(ImageFilter.MedianFilter())`
4. Try different PSM modes

### Vision API Errors

**`INVALID_ARGUMENT`:**
- Image too large (> 20 MB): Resize before sending
- Unsupported format: Convert to PNG/JPEG

**`QUOTA_EXCEEDED`:**
- Check quotas in GCP Console
- Request quota increase if needed
- Enable billing

**`DEADLINE_EXCEEDED`:**
- Image processing timeout (> 60s)
- Reduce image size or complexity

## Best Practices

1. **Always pre-process images** before OCR
2. **Set appropriate confidence thresholds** per document type
3. **Cache aggressively** to avoid re-processing
4. **Monitor costs** and adjust strategy
5. **Collect ground truth** for accuracy measurement
6. **Version OCR pipelines** for A/B testing
7. **Fail gracefully** if both OCR methods fail

## Example: Full OCR Pipeline

```python
async def process_document(file_path):
    # 1. Load image
    image = Image.open(file_path)
    
    # 2. Pre-process
    processed = preprocess_for_ocr(image)
    
    # 3. Check cache
    cached = get_cached_ocr(processed)
    if cached:
        return cached
    
    # 4. Try Tesseract
    tesseract_result = tesseract_ocr(processed)
    
    if tesseract_result.confidence >= 0.75:
        cache_ocr(processed, tesseract_result)
        return tesseract_result
    
    # 5. Fallback to Vision
    if settings.ENABLE_GOOGLE_VISION:
        vision_result = vision_ocr(processed)
        cache_ocr(processed, vision_result)
        return vision_result
    
    # 6. Return best attempt
    return tesseract_result
```

