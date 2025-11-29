"""Auditor agent for analyzing financial transactions."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.models.transaction import Transaction


def audit_finances(transactions: List[Transaction]) -> Dict[str, Any]:
    """
    Analyze user transactions and generate financial report.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        FinancialReport dictionary containing:
        - monthly_income
        - monthly_expenses
        - burn_rate
        - leaks (list of expense tags where spending > 15% of total)
        - saving_potential
    """
    if not transactions:
        return {
            "monthly_income": 0.0,
            "monthly_expenses": 0.0,
            "burn_rate": 0.0,
            "leaks": [],
            "saving_potential": 0.0
        }
    
    # Get current month's transactions
    now = datetime.now()
    current_month_start = datetime(now.year, now.month, 1)
    
    monthly_transactions = [
        t for t in transactions
        if datetime.combine(t.date, datetime.min.time()) >= current_month_start
    ]
    
    # Calculate monthly income and expenses
    monthly_income = sum(
        t.amount for t in monthly_transactions
        if t.type == "income"
    )
    
    monthly_expenses = sum(
        t.amount for t in monthly_transactions
        if t.type == "expense"
    )
    
    # Calculate burn rate (expenses / income)
    # If no income, burn rate is 100% (spending everything)
    if monthly_income > 0:
        burn_rate = (monthly_expenses / monthly_income * 100)
    elif monthly_expenses > 0:
        burn_rate = 100.0  # Spending without income
    else:
        burn_rate = 0.0
    
    # Identify leaks (expense tags where spending > 15% of total expenses)
    leaks = []
    if monthly_expenses > 0:
        tag_totals = {}
        for t in monthly_transactions:
            if t.type == "expense" and t.tag:
                tag_totals[t.tag] = tag_totals.get(t.tag, 0) + t.amount
        
        leak_threshold = monthly_expenses * 0.15
        leaks = [
            tag for tag, total in tag_totals.items()
            if total > leak_threshold
        ]
    
    # Calculate saving potential
    saving_potential = monthly_income - monthly_expenses
    
    return {
        "monthly_income": round(monthly_income, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "burn_rate": round(burn_rate, 2),
        "leaks": leaks,
        "saving_potential": round(saving_potential, 2)
    }

