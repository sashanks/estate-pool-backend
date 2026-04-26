# Neighborhood Due Diligence Backend - Setup Guide

A production-ready Python FastAPI backend for neighborhood analysis, integrating Firebase authentication, Firestore data, Google Search, and local Llama 3.2 LLM inference.

---

## 📋 Prerequisites

- **Python 3.9+** (tested on 3.10, 3.11)
- **Ollama** installed and running with Llama 3.2 model
- **Firebase Project** (`neighbourhood-4c5b6`) with service account credentials
- **Git** for version control

---

## 🚀 Quick Start

### 1. Clone & Setup Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project `neighbourhood-4c5b6`
3. Go to **Project Settings → Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file as `firebase_credentials.json` in the `backend/` directory

### 3. Start Ollama with Llama 3.2

In a separate terminal:

```bash
ollama serve
```

In another terminal, pull and verify Llama 3.2:

```bash
ollama pull llama3.2
ollama list  # Should show llama3.2
```

### 4. Create `.env` File

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
FIREBASE_CREDENTIALS_PATH=./firebase_credentials.json
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
CACHE_DIR=./cache
CACHE_TTL_SECONDS=86400
```

### 5. Setup Firestore Data Structure

Ensure your Firestore has documents structured like:

```
Collection: areas
  Document: {area_id}
    - name: string
    - pincode: string
    - education: array
    - greenery: array
    - health: array
    - infrastructure: array
    - religious_establishment: array
    - transport: array
```

### 6. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

---

## 📚 API Documentation

### Swagger UI

Interactive API docs available at: **http://localhost:8000/docs**

### Endpoints

#### Health Check
```
GET /health
```
Returns: `{"status": "healthy", "timestamp": "..."}`

#### Neighborhood Summary (Main Endpoint)
```
POST /api/v1/neighborhood/summary
```

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "area_name": "New Delhi",
  "pincode": "110001"
}
```

**Response:**
```json
{
  "area_name": "New Delhi",
  "pincode": "110001",
  "firestore_data": {
    "education": [...],
    "greenery": [...],
    "health": [...],
    "infrastructure": [...],
    "religious_establishment": [...],
    "transport": [...]
  },
  "fun_fact": "Delhi is one of the oldest inhabited cities in the world...",
  "ai_summary": "The neighborhood offers... [AI-generated analysis] ...\n\nDisclaimer: This summary is AI-generated...",
  "cached": false,
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## 🔐 Authentication

### Firebase ID Token Retrieval

From your Flutter app, after user authentication:

```dart
// Flutter Example
User? user = FirebaseAuth.instance.currentUser;
String? token = await user?.getIdToken();

// Use in API call
final response = await http.post(
  Uri.parse('http://localhost:8000/api/v1/neighborhood/summary'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: json.encode({
    'latitude': 28.6139,
    'longitude': 77.2090,
    'area_name': 'New Delhi',
    'pincode': '110001',
  }),
);
```

---

## 💾 Caching Strategy

- **Cache Key:** MD5 hash of `{pincode}:{area_name}`
- **Storage:** Disk-based using `diskcache`
- **TTL:** 24 hours (configurable via `CACHE_TTL_SECONDS`)
- **Behavior:** Subsequent identical requests return cached data with `cached: true`

Example cache hit response (much faster):
```json
{
  "cached": true,
  "timestamp": "2024-01-15T11:00:00"
}
```

---

## 🌐 Google Search Integration

### Option 1: SerpApi (Recommended)

```bash
pip install google-search-results
```

Set `SERPAPI_KEY` in `.env`:
```
SERPAPI_KEY=your_key_here
```

Get key from: https://serpapi.com/

### Option 2: Native Google Search Library

Already included in `requirements.txt`. Works but may be rate-limited.

---

## 🤖 Ollama / Llama 3.2 Configuration

### Minimum System Requirements
- **RAM:** 8GB (16GB+ recommended)
- **Storage:** 5GB for Llama 3.2 model
- **GPU:** Optional but recommended (NVIDIA/AMD with proper drivers)

### Common Ollama Commands

```bash
# Start Ollama server
ollama serve

# Pull Llama 3.2
ollama pull llama3.2

# List available models
ollama list

# Run interactive prompt
ollama run llama3.2

# Check API connectivity
curl http://localhost:11434/api/tags
```

### Troubleshooting Ollama

**Issue:** Connection refused on `localhost:11434`
```bash
# Ensure Ollama is running in another terminal
ollama serve

# Check connectivity
curl -X POST http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"test"}'
```

**Issue:** Out of memory
- Reduce batch size or use a smaller model
- Increase system swap space
- Adjust Ollama memory settings

---

## 📦 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FIREBASE_CREDENTIALS_PATH` | `./firebase_credentials.json` | Path to Firebase service account JSON |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Model name to use |
| `GOOGLE_API_KEY` | None | Google Search API key (optional) |
| `SERPAPI_KEY` | None | SerpApi key (optional but recommended) |
| `CACHE_DIR` | `./cache` | Cache storage directory |
| `CACHE_TTL_SECONDS` | `86400` | Cache time-to-live (24 hours) |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |

---

## 🧪 Testing the API

### Using cURL

```bash
# Get Firebase token first (from Flutter app or Firebase CLI)
TOKEN="your_firebase_id_token"

curl -X POST http://localhost:8000/api/v1/neighborhood/summary \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "area_name": "New Delhi",
    "pincode": "110001"
  }'
```

### Using Python Requests

```python
import requests
import json

token = "your_firebase_id_token"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "area_name": "New Delhi",
    "pincode": "110001"
}

response = requests.post(
    "http://localhost:8000/api/v1/neighborhood/summary",
    headers=headers,
    json=payload
)

print(json.dumps(response.json(), indent=2))
```

### Using Swagger UI

1. Navigate to `http://localhost:8000/docs`
2. Click on `/api/v1/neighborhood/summary`
3. Click "Try it out"
4. Paste your Firebase token in the "Authorization" field
5. Fill in the request body
6. Click "Execute"

---

## 🐳 Docker Deployment (Optional)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY firebase_credentials.json .

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run

```bash
docker build -t neighborhood-api:latest .

docker run -d \
  -p 8000:8000 \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/firebase_credentials.json:/app/firebase_credentials.json \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name neighborhood-api \
  neighborhood-api:latest
```

---

## 📊 Monitoring & Logging

Logs are printed to stdout with INFO level. Key log messages:

- `Firebase initialized successfully` - Firebase connection OK
- `Connected to Ollama` - Ollama is reachable
- `Cache HIT for {pincode}:{area_name}` - Cache retrieved successfully
- `Cached data for {pincode}:{area_name}` - Data stored in cache

### Enable Debug Logging

In `main.py`, change logging level:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

---

## 🔄 Firestore Query Adjustment

The current query in `fetch_firestore_civic_data()`:

```python
query = db.collection("areas").where("name", "==", area_name).where("pincode", "==", pincode).limit(1)
```

**If your Firestore structure differs**, adjust accordingly:

```python
# Example 1: Query by document ID
doc = db.collection("areas").document(area_id).get()

# Example 2: Query by nested fields
query = db.collection("areas").where("location.name", "==", area_name)

# Example 3: Geospatial query (requires special setup)
# Use geopoint comparison for latitude/longitude
```

---

## 🛡️ Security Considerations

1. **Firebase Token Verification:** Tokens are verified server-side on every request
2. **CORS:** Add CORS middleware if needed:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Rate Limiting:** Consider adding `slowapi` for rate limiting:
   ```bash
   pip install slowapi
   ```

4. **HTTPS:** Always use HTTPS in production (use Nginx/reverse proxy)

---

## 🐛 Troubleshooting

### 401 Unauthorized
- Ensure Firebase token is valid and not expired
- Verify Firebase credentials JSON is correct
- Check `Authorization` header format: `Bearer <token>`

### 500 Firestore Error
- Verify Firestore database exists and is accessible
- Check Firebase service account has Firestore read permissions
- Adjust query in `fetch_firestore_civic_data()` to match your schema

### 500 Ollama Error
- Ensure Ollama is running: `ollama serve`
- Verify model exists: `ollama list`
- Check `OLLAMA_BASE_URL` in `.env`
- Test connectivity: `curl http://localhost:11434/api/tags`

### Cache Issues
- Delete cache directory to reset: `rm -rf cache/`
- Increase TTL if cache expires too quickly: `CACHE_TTL_SECONDS=259200` (3 days)

---

## 📈 Performance Optimization

1. **Parallel Requests:** Endpoints use async/await for concurrent operations
2. **Disk Cache:** Significantly reduces API response time for repeat queries
3. **Model Optimization:** Consider running quantized Llama models for faster inference
4. **Database Indexing:** Add indexes to Firestore on `name` and `pincode` fields

---

## 📝 Project Structure

```
backend/
├── main.py                      # Main FastAPI application
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Environment template
├── firebase_credentials.json    # Firebase service account (DO NOT COMMIT)
├── cache/                      # Disk cache storage (auto-created)
├── venv/                       # Virtual environment (auto-created)
└── README.md                   # This file
```

---

## 🤝 Contributing

Ensure code follows these practices:
- Add logging for new functions
- Handle exceptions gracefully
- Test with real Firestore and Ollama
- Document new endpoints in this README

---

## 📄 License

Proprietary - Estate Pool Project

---

## 📞 Support

For issues or questions:
1. Check logs: `python main.py` output
2. Review Swagger UI: `http://localhost:8000/docs`
3. Verify all prerequisites are installed and running
4. Check Firebase console for service account permissions

---

**Last Updated:** January 2025
**Version:** 1.0.0
