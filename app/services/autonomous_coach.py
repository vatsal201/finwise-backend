"""Autonomous coaching agent that analyzes transactions and provides personalized advice."""
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import settings
from app.services.fund_suggestions import get_funds_by_risk_profile, format_fund_suggestions

# Try to import Gemini, but make it optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def _call_gemini_for_coaching(prompt: str) -> Optional[Dict[str, Any]]:
    """Call Gemini API for autonomous coaching analysis."""
    if not GEMINI_AVAILABLE or not settings.gemini_api_key:
        return None
    
    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )
        
        result_text = response.text.strip()
        # Clean JSON if needed
        if result_text.startswith("```json"):
            lines = result_text.split("\n")
            result_text = "\n".join([line for line in lines if not line.strip().startswith("```")])
        elif result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join([line for line in lines if not line.strip().startswith("```")])
        
        if "{" in result_text and "}" in result_text:
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1
            result_text = result_text[start_idx:end_idx]
        
        return json.loads(result_text)
    except Exception:
        return None


def _call_ollama_for_coaching(prompt: str) -> Dict[str, Any]:
    """Call Ollama API for autonomous coaching analysis."""
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
    response_text = result.get("response", "").strip()
    
    # Parse JSON response
    if response_text.startswith("```json"):
        lines = response_text.split("\n")
        response_text = "\n".join([line for line in lines if not line.strip().startswith("```")])
    elif response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join([line for line in lines if not line.strip().startswith("```")])
    
    if "{" in response_text and "}" in response_text:
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        response_text = response_text[start_idx:end_idx]
    
    return json.loads(response_text)


def _detect_language(text: str) -> str:
    """Detect if text is in Hinglish/Hindi or English."""
    # Simple detection: check for Devanagari script or common Hindi words
    hindi_words = ['maine', 'kamaye', 'kharch', 'diye', 'liye', 'kar', 'tune', 'tera', 'tu']
    text_lower = text.lower()
    if any(word in text_lower for word in hindi_words):
        return "hinglish"
    # Check for Devanagari characters
    if any('\u0900' <= char <= '\u097F' for char in text):
        return "hindi"
    return "english"


def analyze_and_coach(
    user_id: int,
    transaction_data: Dict[str, Any],
    user: Dict[str, Any],
    all_transactions: List[Dict[str, Any]],
    input_text: str = ""
) -> Dict[str, Any]:
    """
    Autonomous coaching agent that analyzes transactions and decides on intervention.
    Works silently - only returns message when intervention is needed.
    
    Args:
        user_id: User ID
        transaction_data: Latest transaction data
        user: User information dict
        all_transactions: All user transactions
        input_text: Original input text to detect language
        
    Returns:
        Coaching response with regret message and fund suggestions (only if intervention needed)
    """
    # Detect input language
    detected_language = _detect_language(input_text) if input_text else "hinglish"
    
    # Prepare context for AI analysis
    recent_transactions = all_transactions[:20]  # Last 20 transactions
    
    # Calculate spending patterns
    expense_tags = {}
    total_expenses = 0
    for t in recent_transactions:
        if t.get("type") == "expense":
            tag = t.get("tag", "unknown")
            amount = t.get("amount", 0)
            expense_tags[tag] = expense_tags.get(tag, 0) + amount
            total_expenses += amount
    
    # Get current transaction details
    current_expense = transaction_data.get("expense", 0)
    current_income = transaction_data.get("income", 0)
    current_tags = transaction_data.get("tags", [])
    current_tag = ", ".join(current_tags) if current_tags else "expense"
    transaction_date_str = str(transaction_data.get('date', 'today'))
    
    # Calculate spending on current tag in recent period (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_tag_spending = 0
    recent_tag_count = 0
    
    for t in recent_transactions:
        t_date = t.get("date")
        t_datetime = None
        
        if isinstance(t_date, str):
            try:
                t_datetime = datetime.strptime(t_date, "%Y-%m-%d")
            except:
                try:
                    # Try parsing as date object string
                    from datetime import date as date_class
                    t_date_obj = date_class.fromisoformat(t_date)
                    t_datetime = datetime.combine(t_date_obj, datetime.min.time())
                except:
                    continue
        elif hasattr(t_date, 'isoformat'):
            # It's a date object
            try:
                t_datetime = datetime.combine(t_date, datetime.min.time())
            except:
                continue
        else:
            continue
            
        if t_datetime and t.get("type") == "expense" and t.get("tag") == current_tag:
            if t_datetime >= week_ago:
                recent_tag_spending += t.get("amount", 0)
                recent_tag_count += 1
    
    # Build comprehensive prompt
    language_instruction = ""
    if detected_language in ["hinglish", "hindi"]:
        language_instruction = "IMPORTANT: The user is speaking in Hinglish/Hindi. You MUST respond ONLY in Hinglish/Hindi mix. Use words like 'bhai', 'yaar', 'tune', 'tu', 'tera', 'me', 'diye', 'kar deta', etc."
    else:
        language_instruction = "IMPORTANT: The user is speaking in English. Respond in English but you can use some Hinglish terms naturally if appropriate."
    
    prompt = f"""You are an autonomous financial coaching agent for Indian users. You work SILENTLY in the background. Only intervene when there's a clear need.

{language_instruction}

Analyze the following transaction and user context, then decide if you should intervene with a regret/coaching message.

USER CONTEXT:
- Name: {user.get('name', 'User')}
- Risk Profile: {user.get('risk_profile', 'medium')}
- Goals: {user.get('goals', 'Not specified')}

CURRENT TRANSACTION:
- Income: ₹{current_income}
- Expense: ₹{current_expense}
- Expense Tag/Category: {current_tag}
- Date: {transaction_date_str}

SPENDING PATTERNS (Last 20 transactions):
{json.dumps(expense_tags, indent=2)}
Total Expenses (recent): ₹{total_expenses}

RECENT SPENDING ON CURRENT TAG (Last 7 days):
- Amount spent on "{current_tag}": ₹{recent_tag_spending}
- Number of transactions: {recent_tag_count}
- Current transaction adds: ₹{current_expense}

RECENT TRANSACTIONS (Last 5):
{json.dumps(recent_transactions[:5], indent=2, default=str)}

YOUR TASK:
1. Analyze if this transaction shows a problematic spending pattern:
   - Is this a recurring expense on the same tag/category? (e.g., cigarettes, alcohol, eating out)
   - Is the spending on this tag accumulating significantly? (e.g., ₹400 + ₹200 = ₹600 this week)
   - Is this an unhealthy/unnecessary expense that could be avoided?
   
2. Check against user goals:
   - Would saving this money (and similar recent expenses) help achieve the user's goals faster?
   - Reference specific goals mentioned (e.g., "laptop lene ka goal")
   
3. Decide if intervention is needed:
   - should_intervene: true if there's a clear pattern of wasteful/recurring spending
   - should_intervene: false if it's a one-time small expense or necessary spending
   
4. If intervention needed, generate a regret message:
   - Use natural Hinglish/Hindi/English mix (like a friend talking)
   - Be empathetic but direct and concerned
   - Reference specific amounts: "tune pehle hi 400 cigarette me udaa diye"
   - Reference time period: "ye pure week me"
   - Show impact: "vahi 600 tu save kar deta toh tera laptop lene ka goal jaldi pura hota"
   - Use casual, friendly tone: "bhai", "yaar", etc.
   
5. Provide clear reasoning for your decision

CRITICAL RULES:
- WORK SILENTLY: Only return a message if intervention is TRULY needed
- Only intervene if there's a CLEAR pattern of wasteful/recurring spending (e.g., same tag multiple times, accumulating amount)
- DON'T intervene for:
  - Small one-time expenses (< ₹100)
  - Necessary expenses (groceries, bills, rent, etc.)
  - First-time expenses on a category
  - Income transactions (unless there's a spending problem)
- Be STRICT about when to intervene - most transactions should NOT trigger a message
- If user speaks Hinglish/Hindi, respond ONLY in Hinglish/Hindi mix
- Be empathetic - you're a friend helping, not scolding
- Keep messages concise and actionable

Return ONLY a valid JSON object (no markdown, no code blocks):
{{
    "should_intervene": true or false,
    "regret_message": "message in Hinglish/Hindi/English mix or null",
    "reasoning": "brief explanation of why you decided to intervene or not",
    "spending_insight": "key insight about the spending pattern (e.g., 'Spent ₹600 on cigarettes this week')"
}}"""

    # Try Gemini first, fallback to Ollama
    coaching_result = _call_gemini_for_coaching(prompt)
    
    if coaching_result is None:
        try:
            coaching_result = _call_ollama_for_coaching(prompt)
        except Exception as e:
            # If both fail, return default response
            return {
                "should_intervene": False,
                "regret_message": None,
                "fund_suggestions": [],
                "reasoning": f"Coaching analysis unavailable: {str(e)}"
            }
    
    # Get fund suggestions ONLY if intervention is needed AND there's meaningful savings potential
    fund_suggestions = []
    if coaching_result.get("should_intervene", False):
        # Calculate potential savings from this and similar wasteful expenses
        investable_amount = max(0, current_income - current_expense) if current_income > 0 else 0
        # Add recent wasteful spending to show what could be saved
        if recent_tag_spending > 0 and current_tag in expense_tags:
            investable_amount = max(investable_amount, recent_tag_spending)
        
        # Only suggest funds if there's meaningful amount (> ₹1000)
        if investable_amount >= 1000:
            suggested_funds = get_funds_by_risk_profile(
                user.get("risk_profile", "medium"),
                investable_amount
            )
            fund_suggestions = format_fund_suggestions(suggested_funds[:2])  # Top 2 suggestions only
    
    return {
        "should_intervene": coaching_result.get("should_intervene", False),
        "regret_message": coaching_result.get("regret_message"),
        "fund_suggestions": fund_suggestions,
        "reasoning": coaching_result.get("reasoning", ""),
        "spending_insight": coaching_result.get("spending_insight", "")
    }

