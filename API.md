# 🔌 API Documentation

Bot এর সাথে programmatically interact করার জন্য REST API এবং webhook support।

## Table of Contents

- [Authentication](#authentication)
- [REST API Endpoints](#rest-api-endpoints)
- [Webhook Integration](#webhook-integration)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Authentication

### API Key

API requests এর জন্য API key প্রয়োজন:

```bash
# Header
Authorization: Bearer YOUR_API_KEY
```

### Generate API Key

```bash
# Admin command in Telegram
/admin apikey generate

# Or via CLI
python manage.py create-api-key --user-id 123456789
```

## REST API Endpoints

### Base URL

```
https://your-domain.com/api/v1
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "services": {
    "database": "ok",
    "redis": "ok",
    "bot": "ok"
  }
}
```

### Create Download Job

**Endpoint:** `POST /jobs`

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "format": "video",
  "quality": "720p",
  "callback_url": "https://your-app.com/webhook"
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z",
  "estimated_completion": "2024-01-01T12:05:00Z"
}
```

### Get Job Status

**Endpoint:** `GET /jobs/{job_id}`

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "format": "video",
  "quality": "720p",
  "file_size": 45678901,
  "download_url": "https://cdn.example.com/file.mp4",
  "created_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:04:30Z"
}
```

### List Jobs

**Endpoint:** `GET /jobs`

**Query Parameters:**
- `status` - Filter by status (pending, processing, completed, failed)
- `limit` - Number of results (default: 50, max: 100)
- `offset` - Pagination offset

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Cancel Job

**Endpoint:** `DELETE /jobs/{job_id}`

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

### User Statistics

**Endpoint:** `GET /users/me/stats`

**Response:**
```json
{
  "user_id": 123456789,
  "total_downloads": 45,
  "today_downloads": 3,
  "remaining_today": 17,
  "total_bandwidth": 1234567890,
  "member_since": "2024-01-01T00:00:00Z",
  "last_active": "2024-01-15T12:00:00Z"
}
```

## Webhook Integration

### Configure Webhook

**Endpoint:** `POST /webhooks`

**Request:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["job.completed", "job.failed"],
  "secret": "your-webhook-secret"
}
```

### Webhook Events

#### Job Completed

```json
{
  "event": "job.completed",
  "timestamp": "2024-01-01T12:04:30Z",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "download_url": "https://cdn.example.com/file.mp4",
    "file_size": 45678901,
    "duration": 270
  }
}
```

#### Job Failed

```json
{
  "event": "job.failed",
  "timestamp": "2024-01-01T12:04:30Z",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "failed",
    "error": "Video not available",
    "error_code": "VIDEO_UNAVAILABLE"
  }
}
```

#### Job Progress

```json
{
  "event": "job.progress",
  "timestamp": "2024-01-01T12:02:00Z",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "progress": 45,
    "eta_seconds": 120
  }
}
```

### Verify Webhook Signature

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

# Usage
signature = request.headers.get('X-Webhook-Signature')
payload = request.body
is_valid = verify_signature(payload, signature, WEBHOOK_SECRET)
```

## Rate Limiting

### Limits

- **API Requests**: 100 requests per minute per API key
- **Download Jobs**: Based on user tier

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

### Rate Limit Exceeded Response

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

## Error Handling

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {
    "field": "Additional error details"
  },
  "request_id": "req_123456789"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Invalid request parameters |
| `unauthorized` | 401 | Invalid or missing API key |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `rate_limit_exceeded` | 429 | Too many requests |
| `server_error` | 500 | Internal server error |
| `video_unavailable` | 400 | Video not accessible |
| `invalid_url` | 400 | Invalid YouTube URL |

## Examples

### Python Example

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://your-domain.com/api/v1"

def create_download_job(url, format="video", quality="720p"):
    """Create a new download job"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "url": url,
        "format": format,
        "quality": quality
    }
    
    response = requests.post(
        f"{BASE_URL}/jobs",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Error: {response.json()}")

def get_job_status(job_id):
    """Get job status"""
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    response = requests.get(
        f"{BASE_URL}/jobs/{job_id}",
        headers=headers
    )
    
    return response.json()

# Usage
job = create_download_job("https://youtube.com/watch?v=dQw4w9WgXcQ")
print(f"Job ID: {job['job_id']}")

# Poll for status
import time
while True:
    status = get_job_status(job['job_id'])
    print(f"Status: {status['status']} - Progress: {status.get('progress', 0)}%")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(5)

if status['status'] == 'completed':
    print(f"Download URL: {status['download_url']}")
```

### JavaScript Example

```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://your-domain.com/api/v1';

async function createDownloadJob(url, format = 'video', quality = '720p') {
  const response = await fetch(`${BASE_URL}/jobs`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ url, format, quality })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

async function getJobStatus(jobId) {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}`, {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  });
  
  return await response.json();
}

// Usage
(async () => {
  const job = await createDownloadJob('https://youtube.com/watch?v=dQw4w9WgXcQ');
  console.log(`Job ID: ${job.job_id}`);
  
  // Poll for status
  while (true) {
    const status = await getJobStatus(job.job_id);
    console.log(`Status: ${status.status} - Progress: ${status.progress || 0}%`);
    
    if (['completed', 'failed'].includes(status.status)) {
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
})();
```

### cURL Example

```bash
# Create download job
curl -X POST https://your-domain.com/api/v1/jobs \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "video",
    "quality": "720p"
  }'

# Get job status
curl https://your-domain.com/api/v1/jobs/JOB_ID \
  -H "Authorization: Bearer YOUR_API_KEY"

# List jobs
curl "https://your-domain.com/api/v1/jobs?status=completed&limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Webhook Handler Example (Flask)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret"

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.data.decode('utf-8')
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process webhook
    data = request.json
    event = data.get('event')
    
    if event == 'job.completed':
        job_id = data['data']['job_id']
        download_url = data['data']['download_url']
        print(f"Job {job_id} completed: {download_url}")
        
        # Your logic here
        
    elif event == 'job.failed':
        job_id = data['data']['job_id']
        error = data['data']['error']
        print(f"Job {job_id} failed: {error}")
        
        # Your logic here
    
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

## SDK Libraries

### Python SDK

```bash
pip install yt-telegram-bot-sdk
```

```python
from yt_bot_sdk import YTBotClient

client = YTBotClient(api_key="your_api_key")

# Create job
job = client.download(
    url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    format="video",
    quality="720p"
)

# Wait for completion
result = job.wait()
print(f"Download URL: {result.download_url}")
```

### JavaScript SDK

```bash
npm install yt-telegram-bot-sdk
```

```javascript
import { YTBotClient } from 'yt-telegram-bot-sdk';

const client = new YTBotClient({ apiKey: 'your_api_key' });

// Create job
const job = await client.download({
  url: 'https://youtube.com/watch?v=dQw4w9WgXcQ',
  format: 'video',
  quality: '720p'
});

// Wait for completion
const result = await job.wait();
console.log(`Download URL: ${result.downloadUrl}`);
```

---

**Need Help?** Visit our [API Support Portal](https://support.example.com) or email api@example.com