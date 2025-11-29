"""Coaching router for financial advice."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.db.db import get_user, get_transactions
from app.models.transaction import Transaction
from app.services.auditor import audit_finances
from app.services.strategist import create_safety_plan
from app.services.catalyst import propose_portfolio

router = APIRouter(prefix="/coach", tags=["coaching"])


class CoachAdviseRequest(BaseModel):
    """Request model for coach advise endpoint."""
    user_id: int


class InvestmentPlanRequest(BaseModel):
    """Request model for investment plan endpoint."""
    user_id: int


def generate_conversational_summary(
    latest_transaction: Dict[str, Any],
    report: Dict[str, Any],
    plan: Dict[str, Any],
    proposal: Dict[str, Any]
) -> str:
    """
    Generate natural-language conversational summary.
    
    Args:
        latest_transaction: Most recent transaction dict
        report: FinancialReport from auditor
        plan: SafetyNetPlan from strategist
        proposal: InvestmentPortfolioProposal from catalyst
        
    Returns:
        Conversational summary string
    """
    # Get latest transaction details
    transaction_type = latest_transaction.get("type", "expense")
    amount = latest_transaction.get("amount", 0)
    tag = latest_transaction.get("tag") or "transaction"
    
    # Build message
    message_parts = []
    
    if transaction_type == "income":
        message_parts.append(f"Great job earning ₹{amount:.0f} today!")
    else:
        message_parts.append(f"You spent ₹{amount:.0f} on {tag}.")
    
    # Add burn rate
    burn_rate = report.get("burn_rate", 0)
    message_parts.append(f"Your burn rate this month is {burn_rate:.0f}%.")
    
    # Add savings plan
    monthly_savings = plan.get("monthly_savings_target", 0)
    months_to_goal = plan.get("months_to_reach_goal", 0)
    if monthly_savings > 0 and months_to_goal > 0:
        message_parts.append(
            f"If you save ₹{monthly_savings:.0f}/month, "
            f"you'll complete your emergency fund in {months_to_goal} months."
        )
    
    # Add portfolio suggestion
    portfolio = proposal.get("portfolio", {})
    if portfolio:
        equity = portfolio.get("equity", 0)
        debt = portfolio.get("debt", 0)
        gold = portfolio.get("gold", 0)
        cash = portfolio.get("cash", 0)
        message_parts.append(
            f"Suggested portfolio: {equity}% equity, {debt}% debt, "
            f"{gold}% gold, {cash}% cash."
        )
    
    return " ".join(message_parts)


@router.post("/advise")
def get_coaching_advice(request: CoachAdviseRequest):
    """
    Get personalized financial coaching advice.
    
    Pipeline:
    1. Fetch user and latest transactions
    2. Run auditor → strategist → catalyst
    3. Return complete coaching response
    """
    # Fetch user
    user = get_user(request.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {request.user_id} not found"
        )
    
    # Fetch user transactions
    transactions_data = get_transactions(user_id=request.user_id)
    
    if not transactions_data:
        raise HTTPException(
            status_code=404,
            detail="No transactions found for this user"
        )
    
    # Convert to Transaction objects for auditor
    transactions = [Transaction(**t) for t in transactions_data]
    
    # Get latest transaction
    latest_transaction = transactions_data[0]
    
    # Run auditor
    try:
        report = audit_finances(transactions)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate financial report: {str(e)}"
        )
    
    # Run strategist
    try:
        plan = create_safety_plan(report, user["risk_profile"])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create safety plan: {str(e)}"
        )
    
    # Run catalyst
    try:
        proposal = propose_portfolio(plan, user["risk_profile"])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to propose portfolio: {str(e)}"
        )
    
    # Generate conversational summary
    try:
        message = generate_conversational_summary(
            latest_transaction,
            report,
            plan,
            proposal
        )
    except Exception as e:
        # Fallback message if summary generation fails
        message = f"Your financial analysis is ready. Monthly income: ₹{report.get('monthly_income', 0):.0f}, Expenses: ₹{report.get('monthly_expenses', 0):.0f}."
    
    # Format latest transaction for response
    transaction_date = latest_transaction.get("date")
    if hasattr(transaction_date, "isoformat"):
        date_str = transaction_date.isoformat()
    else:
        date_str = str(transaction_date)
    
    transaction_dict = {
        "id": latest_transaction.get("id"),
        "amount": latest_transaction.get("amount"),
        "type": latest_transaction.get("type"),
        "tag": latest_transaction.get("tag"),
        "category": latest_transaction.get("category"),
        "date": date_str
    }
    
    return {
        "transaction": transaction_dict,
        "report": report,
        "plan": plan,
        "proposal": proposal,
        "message": message
    }


@router.post("/investment-plan")
def get_investment_plan(request: InvestmentPlanRequest):
    """
    Get personalized investment plan for user.
    
    Pipeline:
    1. Fetch user and transactions
    2. Run auditor → strategist → catalyst
    3. Return investment plan with fund suggestions
    
    Returns:
        Investment plan with portfolio allocation and fund recommendations
    """
    # Fetch user
    user = get_user(request.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {request.user_id} not found"
        )
    
    # Fetch user transactions
    transactions_data = get_transactions(user_id=request.user_id)
    
    if not transactions_data:
        raise HTTPException(
            status_code=404,
            detail="No transactions found for this user"
        )
    
    # Convert to Transaction objects for auditor
    transactions = [Transaction(**t) for t in transactions_data]
    
    # Run auditor
    try:
        report = audit_finances(transactions)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate financial report: {str(e)}"
        )
    
    # Run strategist
    try:
        plan = create_safety_plan(report, user["risk_profile"])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create safety plan: {str(e)}"
        )
    
    # Run catalyst
    try:
        proposal = propose_portfolio(plan, user["risk_profile"])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to propose portfolio: {str(e)}"
        )
    
    # Get fund suggestions based on risk profile and investable amount
    from app.services.fund_suggestions import get_funds_by_risk_profile, format_fund_suggestions
    
    investable_amount = proposal.get("investable_amount", 0)
    suggested_funds = get_funds_by_risk_profile(
        user["risk_profile"],
        investable_amount
    )
    fund_suggestions = format_fund_suggestions(suggested_funds[:5])  # Top 5 funds
    
    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "risk_profile": user["risk_profile"],
            "goals": user.get("goals")
        },
        "financial_summary": {
            "monthly_income": report.get("monthly_income", 0),
            "monthly_expenses": report.get("monthly_expenses", 0),
            "saving_potential": report.get("saving_potential", 0),
            "burn_rate": report.get("burn_rate", 0)
        },
        "safety_plan": plan,
        "investment_plan": {
            "investable_amount": proposal.get("investable_amount", 0),
            "portfolio_allocation": proposal.get("portfolio", {}),
            "scenario_notes": proposal.get("scenario_notes", []),
            "fund_suggestions": fund_suggestions
        }
    }
