"""Unified chat/message router - single entry point for all user messages."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from datetime import datetime, date
from typing import Optional
from app.db.db import get_user, create_transaction, get_transactions
from app.services.whisper_service import whisper_service
from app.services.extraction_service import extract_transaction
from app.services.autonomous_coach import analyze_and_coach

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def handle_message(
    user_id: int = Form(...),
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
):
    """
    Single unified endpoint for all user messages.
    
    Flow:
    1. Receives text or audio message from user
    2. Transcribes audio if needed
    3. Extracts transaction data
    4. Saves transaction to database
    5. Autonomous coach analyzes and decides if intervention needed
    6. Returns response with coaching message (only if intervention needed)
    
    Accepts either:
    - text: Direct text input (e.g., "bhai aaj maine 500 kamaye aur 200 ki cigarette pili")
    - audio: Audio file for transcription
    
    Returns:
    - If intervention needed: { "message": "coaching message in user's language" }
    - If no intervention: { "message": null } or no message field
    """
    # Validate input
    if not text and not audio:
        raise HTTPException(
            status_code=400,
            detail="Either 'text' or 'audio' must be provided"
        )
    
    # Validate user exists
    user = get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found"
        )
    
    # Get text input
    input_text = ""
    if audio:
        # Transcribe audio
        try:
            input_text = whisper_service.transcribe_audio(audio)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to transcribe audio: {str(e)}"
            )
    elif text:
        input_text = text
    
    if not input_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text content found in input"
        )
    
    # Extract transaction data
    try:
        transaction_data = extract_transaction(input_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract transaction: {str(e)}"
        )
    
    # Parse date
    transaction_date = date.today()
    if transaction_data.get("date"):
        try:
            transaction_date = datetime.strptime(
                transaction_data["date"],
                "%Y-%m-%d"
            ).date()
        except ValueError:
            # If date parsing fails, use today
            transaction_date = date.today()
    
    # Save income transaction if present
    if transaction_data.get("income", 0) > 0:
        income_transaction = {
            "user_id": user_id,
            "amount": transaction_data["income"],
            "type": "income",
            "tag": "income",
            "category": None,
            "date": transaction_date
        }
        create_transaction(income_transaction)
    
    # Save expense transaction if present
    if transaction_data.get("expense", 0) > 0:
        tags = transaction_data.get("tags", [])
        tag_str = ", ".join(tags) if tags else "expense"
        
        expense_transaction = {
            "user_id": user_id,
            "amount": transaction_data["expense"],
            "type": "expense",
            "tag": tag_str,
            "category": transaction_data.get("expenseType"),
            "date": transaction_date
        }
        create_transaction(expense_transaction)
    
    # Get all user transactions for autonomous coaching analysis
    all_transactions = get_transactions(user_id=user_id)
    
    # Call autonomous coaching agent (works silently in background)
    coaching_response = None
    try:
        coaching_response = analyze_and_coach(
            user_id=user_id,
            transaction_data=transaction_data,
            user=user,
            all_transactions=all_transactions,
            input_text=input_text  # Pass input text for language detection
        )
    except Exception as e:
        # If coaching fails, silently continue (non-blocking)
        coaching_response = {
            "should_intervene": False,
            "regret_message": None,
            "fund_suggestions": []
        }
    
    # Build response - simple and clean
    # Only return message if autonomous coach decided intervention is needed
    response = {
        "success": True
    }
    
    # ONLY add message if agent decided intervention is needed
    # This ensures we work silently and only speak when necessary
    if coaching_response and coaching_response.get("should_intervene", False):
        response["message"] = coaching_response.get("regret_message")  # Single message in user's language
        
        # Only include fund suggestions if provided and meaningful
        if coaching_response.get("fund_suggestions"):
            response["fund_suggestions"] = coaching_response.get("fund_suggestions")
    else:
        # No intervention needed - return null message or omit it
        response["message"] = None
    
    return response
