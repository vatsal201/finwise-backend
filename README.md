# FinWise - Financial Coaching Backend

A FastAPI backend for a financial coaching app that processes voice/text input, extracts transaction data, and provides personalized financial advice through autonomous AI agents.

## Features

- **NLP Processing**: Transcribe audio (Hinglish/Hindi/English) using Whisper
- **Transaction Extraction**: Extract structured transaction data using Gemini (primary) or Ollama (fallback)
- **Financial Analysis**: Three autonomous agents (Auditor, Strategist, Catalyst)
- **Personalized Coaching**: Generate conversational financial advice

## Prerequisites

1. **Python 3.10+** (project uses Python 3.12)
2. **Gemini API Key** (optional, but recommended - primary method)
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Ollama** installed and running with `llama3` model (fallback if Gemini unavailable)
4. **uv** package manager (already initialized)

## Setup Instructions

### 1. Install Dependencies

```bash
uv sync
```

This will install all required packages:
- FastAPI
- SQLAlchemy
- Whisper
- Requests
- And more...

### 2. Set Up Gemini (Primary - Recommended)

Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey) and add it to your environment.

### 3. Set Up Ollama (Fallback)

If Gemini is not available, the system will automatically fallback to Ollama. Make sure Ollama is running and has the `llama3` model:

```bash
# Start Ollama (if not running)
ollama serve

# Pull llama3 model (if not already installed)
ollama pull llama3
```

### 4. Configure Environment (Optional)

Create a `.env` file in the project root to customize settings:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
WHISPER_MODEL_SIZE=medium
```

**Note**: Data is stored in JSON files (`data/users.json` and `data/transactions.json`). No database installation required!

**Note**: The system will try Gemini first, and automatically fallback to Ollama if:
- Gemini API key is not set
- Gemini API is unavailable
- Gemini request fails

### 5. Run the Application

```bash
uv run uvicorn app.main:app --reload
```

**Note**: Since we're using `uv`, use `uv run` to execute commands with the project's dependencies. Alternatively, you can activate the virtual environment first:
```bash
source .venv/bin/activate  # After uv sync
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### POST `/nlp/parse`

Parse transaction from text or audio input.

**Request** (multipart/form-data):
- `user_id` (int, required): User ID
- `text` (str, optional): Direct text input
- `audio` (file, optional): Audio file for transcription

**Response**:
```json
{
  "success": true,
  "transcribed_text": "...",
  "transaction": {
    "income": 5000,
    "expense": 2000,
    "tags": ["groceries"],
    "expenseType": "needs",
    "date": "2024-01-15"
  }
}
```

### POST `/coach/advise`

Get personalized financial coaching advice.

**Request**:
```json
{
  "user_id": 1
}
```

**Response**:
```json
{
  "transaction": {...},
  "report": {
    "monthly_income": 50000,
    "monthly_expenses": 40000,
    "burn_rate": 80.0,
    "leaks": ["shopping"],
    "saving_potential": 10000
  },
  "plan": {
    "emergency_fund_goal": 120000,
    "months_to_reach_goal": 12,
    "monthly_savings_target": 10000,
    "allocation": {
      "liquid": 50,
      "locked": 50
    }
  },
  "proposal": {
    "investable_amount": 5000,
    "portfolio": {
      "equity": 55,
      "debt": 30,
      "gold": 10,
      "cash": 5
    },
    "scenario_notes": [...]
  },
  "message": "Great job earning ₹5000 today! ..."
}
```

## Data Storage

Data is stored in JSON files in the `data/` directory:
- `data/users.json` - User data
- `data/transactions.json` - Transaction data

### User Schema
- `id` (int, auto-generated)
- `name` (string)
- `risk_profile` (string): "low" | "medium" | "high"
- `goals` (string, optional)

### Transaction Schema
- `id` (int, auto-generated)
- `user_id` (int)
- `amount` (float)
- `type` (string): "income" | "expense"
- `tag` (string, optional)
- `category` (string, optional): "needs" | "wants"
- `date` (string, ISO format: "YYYY-MM-DD")

## Testing the API

### 1. Create a Test User

You'll need to create a user first. Use the provided script:

```bash
uv run python create_user.py
```

This will create a test user with ID 1.

### 2. Test Text Parsing

```bash
curl -X POST "http://localhost:8000/nlp/parse" \
  -F "user_id=1" \
  -F "text=I earned 5000 rupees today and spent 2000 on groceries"
```

### 3. Test Audio Parsing

```bash
curl -X POST "http://localhost:8000/nlp/parse" \
  -F "user_id=1" \
  -F "audio=@path/to/audio.mp3"
```

### 4. Test Coaching Advice

```bash
curl -X POST "http://localhost:8000/coach/advise" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

## Architecture

```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── routers/
│   ├── nlp.py          # NLP parsing endpoints
│   └── coaching.py     # Coaching advice endpoints
├── services/
│   ├── whisper_service.py      # Audio transcription
│   ├── extraction_service.py   # Transaction extraction
│   ├── auditor.py              # Financial analysis
│   ├── strategist.py           # Safety net planning
│   └── catalyst.py             # Portfolio proposals
├── models/
│   ├── user.py         # User model
│   └── transaction.py  # Transaction model
└── db/
    └── db.py           # Database setup
```

## Notes

- The database is automatically created on first startup
- Whisper model is loaded lazily (on first use) to speed up startup
- Make sure Ollama is running before making requests to `/nlp/parse`
- Audio files are temporarily saved to disk during transcription

## Troubleshooting

1. **Gemini API errors**: 
   - Make sure your API key is set in environment or `.env` file
   - System will automatically fallback to Ollama if Gemini fails
2. **Ollama connection error**: 
   - Make sure Ollama is running at `http://localhost:11434`
   - Only needed if Gemini is unavailable
3. **Whisper model not found**: The model will be downloaded automatically on first use
4. **Data file errors**: 
   - Delete `data/` directory and restart the app to recreate data files
   - Files are automatically created on first run
5. **Import errors**: Make sure you're running from the project root directory

