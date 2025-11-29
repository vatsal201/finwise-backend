"""Catalyst agent for proposing investment portfolios."""
from typing import Dict, Any, List


def propose_portfolio(
    plan: Dict[str, Any],
    risk_profile: str
) -> Dict[str, Any]:
    """
    Propose investment portfolio based on safety plan and risk profile.
    
    Args:
        plan: SafetyNetPlan dictionary from strategist
        risk_profile: User's risk profile (low | medium | high)
        
    Returns:
        InvestmentPortfolioProposal dictionary containing:
        - investable_amount (saving_potential - emergency_fund_target_contribution)
        - portfolio { equity, debt, gold, cash }
        - scenario_notes (list of strings)
    """
    monthly_savings_target = plan.get("monthly_savings_target", 0)
    emergency_fund_goal = plan.get("emergency_fund_goal", 0)
    months_to_reach_goal = plan.get("months_to_reach_goal", 0)
    
    # Calculate monthly contribution to emergency fund
    if months_to_reach_goal > 0 and emergency_fund_goal > 0:
        emergency_fund_monthly_contribution = emergency_fund_goal / months_to_reach_goal
    else:
        emergency_fund_monthly_contribution = 0
    
    # Calculate investable amount (remaining after emergency fund contribution)
    investable_amount = max(0, monthly_savings_target - emergency_fund_monthly_contribution)
    
    # Create portfolio allocation based on risk profile
    if risk_profile == "low":
        # Conservative: more debt and cash, less equity
        portfolio = {
            "equity": 30,
            "debt": 50,
            "gold": 10,
            "cash": 10
        }
        scenario_notes = [
            "Conservative portfolio suitable for low-risk tolerance",
            "Focus on capital preservation with steady returns",
            "Higher allocation to debt instruments for stability"
        ]
    elif risk_profile == "high":
        # Aggressive: more equity, less debt
        portfolio = {
            "equity": 70,
            "debt": 15,
            "gold": 10,
            "cash": 5
        }
        scenario_notes = [
            "Aggressive portfolio for high-risk tolerance",
            "Higher equity exposure for long-term growth",
            "Lower cash allocation to maximize returns"
        ]
    else:  # medium
        # Balanced
        portfolio = {
            "equity": 55,
            "debt": 30,
            "gold": 10,
            "cash": 5
        }
        scenario_notes = [
            "Balanced portfolio for moderate risk tolerance",
            "Diversified allocation across asset classes",
            "Good balance between growth and stability"
        ]
    
    return {
        "investable_amount": round(investable_amount, 2),
        "portfolio": portfolio,
        "scenario_notes": scenario_notes
    }

