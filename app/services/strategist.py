"""Strategist agent for creating safety net plans."""
from typing import Dict, Any


def create_safety_plan(
    report: Dict[str, Any],
    risk_profile: str
) -> Dict[str, Any]:
    """
    Create safety net plan based on financial report and risk profile.
    
    Args:
        report: FinancialReport dictionary from auditor
        risk_profile: User's risk profile (low | medium | high)
        
    Returns:
        SafetyNetPlan dictionary containing:
        - emergency_fund_goal (3 × average monthly expense)
        - months_to_reach_goal
        - monthly_savings_target
        - allocation: { liquid: %, locked: % }
    """
    monthly_expenses = report.get("monthly_expenses", 0)
    saving_potential = report.get("saving_potential", 0)
    
    # Calculate emergency fund goal (3 × average monthly expense)
    emergency_fund_goal = monthly_expenses * 3
    
    # Calculate monthly savings target (use saving_potential if positive)
    monthly_savings_target = max(saving_potential, 0)
    
    # Calculate months to reach goal
    if monthly_savings_target > 0 and emergency_fund_goal > 0:
        months_to_reach_goal = max(1, int(emergency_fund_goal / monthly_savings_target))
    elif emergency_fund_goal > 0:
        months_to_reach_goal = 0  # Cannot reach goal with no savings
    else:
        months_to_reach_goal = 0  # No goal to reach
    
    # Allocate liquid vs locked based on risk profile
    if risk_profile == "low":
        # Conservative: more locked, less liquid
        liquid_percentage = 30
        locked_percentage = 70
    elif risk_profile == "high":
        # Aggressive: more liquid, less locked
        liquid_percentage = 70
        locked_percentage = 30
    else:  # medium
        # Balanced
        liquid_percentage = 50
        locked_percentage = 50
    
    return {
        "emergency_fund_goal": round(emergency_fund_goal, 2),
        "months_to_reach_goal": months_to_reach_goal,
        "monthly_savings_target": round(monthly_savings_target, 2),
        "allocation": {
            "liquid": liquid_percentage,
            "locked": locked_percentage
        }
    }

