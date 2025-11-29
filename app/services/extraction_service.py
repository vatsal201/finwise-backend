"""Service for extracting structured transaction data from text using Gemini (primary) or Ollama (fallback)."""
import json
import requests
from datetime import date
from typing import Dict, Any, Optional
from app.config import settings

# Try to import Gemini, but make it optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def _extract_with_gemini(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract transaction using Gemini API.
    
    Args:
        text: Input text
        
    Returns:
        Transaction data dict or None if failed
    """
    if not GEMINI_AVAILABLE:
        return None
    
    if not settings.gemini_api_key:
        return None
    
    try:
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        
        # Create prompt
        prompt = f"""Extract financial transaction information from the following text and return ONLY a valid JSON object with no additional text.

Text: {text}

Return a JSON object with the following structure:
{{
    "income": <number or 0 if no income mentioned>,
    "expense": <number or 0 if no expense mentioned>,
    "tags": [<list of expense tags/descriptions>],
    "expenseType": "<needs|wants|null>",
    "date": "<YYYY-MM-DD or today's date if not mentioned>"
}}

Example:
Text: "I earned 5000 rupees today and spent 2000 on groceries"
Response: {{"income": 5000, "expense": 2000, "tags": ["groceries"], "expenseType": "needs", "date": "2024-01-15"}}

Now extract from the given text:"""

        # Call Gemini API
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        response_text = response.text.strip()
        
        # Parse JSON response
        transaction_data = json.loads(response_text)
        
        return transaction_data
        
    except Exception as e:
        # Return None to trigger fallback
        return None


def _extract_with_ollama(text: str) -> Dict[str, Any]:
    """
    Extract transaction using Ollama API.
    
    Args:
        text: Input text
        
    Returns:
        Transaction data dict
        
    Raises:
        Exception: If extraction fails
    """
    # Create prompt for Ollama
    prompt = f"""Extract financial transaction information from the following text and return ONLY a valid JSON object with no additional text.

Text: {text}

Return a JSON object with the following structure:
{{
    "income": <number or 0 if no income mentioned>,
    "expense": <number or 0 if no expense mentioned>,
    "tags": [<list of expense tags/descriptions>],
    "expenseType": "<needs|wants|null>",
    "date": "<YYYY-MM-DD or today's date if not mentioned>"
}}

Example:
Text: "I earned 5000 rupees today and spent 2000 on groceries"
Response: {{"income": 5000, "expense": 2000, "tags": ["groceries"], "expenseType": "needs", "date": "2024-01-15"}}

Now extract from the given text:"""

    # Call Ollama API
    url = f"{settings.ollama_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    response_text = result.get("response", "")
    
    if not response_text:
        raise Exception("Empty response from Ollama API")
    
    # Parse JSON response
    # Sometimes Ollama returns markdown code blocks, so we need to extract JSON
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        # Extract JSON from code block
        lines = response_text.split("\n")
        json_lines = [line for line in lines if not line.strip().startswith("```")]
        response_text = "\n".join(json_lines)
    elif response_text.startswith("```"):
        # Extract JSON from code block (any language)
        lines = response_text.split("\n")
        json_lines = [line for line in lines if not line.strip().startswith("```")]
        response_text = "\n".join(json_lines)
    
    # Try to find JSON object in response
    if "{" in response_text and "}" in response_text:
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        response_text = response_text[start_idx:end_idx]
    
    transaction_data = json.loads(response_text)
    
    return transaction_data


def extract_transaction(text: str) -> Dict[str, Any]:
    """
    Extract structured transaction information from text.
    Tries Gemini first, falls back to Ollama if Gemini is unavailable.
    
    Args:
        text: Input text (transcribed or direct text)
        
    Returns:
        Dictionary containing extracted transaction data:
        {
            "income": number,
            "expense": number,
            "tags": [string],
            "expenseType": "needs" | "wants",
            "date": "YYYY-MM-DD"
        }
        
    Raises:
        Exception: If both Gemini and Ollama fail
    """
    # Try Gemini first
    transaction_data = _extract_with_gemini(text)
    
    # Fallback to Ollama if Gemini failed or is unavailable
    if transaction_data is None:
        try:
            transaction_data = _extract_with_ollama(text)
        except requests.exceptions.ConnectionError as e:
            raise Exception(
                f"Cannot connect to Ollama API at {settings.ollama_url}. "
                "Make sure Ollama is running. Also ensure Gemini API key is set if you want to use Gemini."
            )
        except requests.exceptions.Timeout as e:
            raise Exception("Ollama API request timed out after 60 seconds")
        except requests.RequestException as e:
            raise Exception(f"Failed to call Ollama API: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response from Ollama: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to extract transaction with Ollama: {str(e)}")
    
    # Validate and set defaults
    transaction_data.setdefault("income", 0)
    transaction_data.setdefault("expense", 0)
    transaction_data.setdefault("tags", [])
    transaction_data.setdefault("expenseType", None)
    transaction_data.setdefault("date", None)
    
    # Validate types
    if not isinstance(transaction_data["income"], (int, float)):
        transaction_data["income"] = 0
    if not isinstance(transaction_data["expense"], (int, float)):
        transaction_data["expense"] = 0
    if not isinstance(transaction_data["tags"], list):
        transaction_data["tags"] = []
    
    # Set default date to today if not provided
    if not transaction_data.get("date"):
        transaction_data["date"] = date.today().isoformat()
    
    return transaction_data
