"""Fund suggestions database and selection logic."""
from typing import List, Dict, Any


# Popular Indian Mutual Funds Database
FUNDS_DATABASE = [
    # Equity Funds
    {
        "name": "SBI Bluechip Fund",
        "type": "equity",
        "category": "Large Cap",
        "risk_level": "high",
        "min_investment": 5000,
        "description": "Large cap equity fund with consistent returns"
    },
    {
        "name": "HDFC Equity Fund",
        "type": "equity",
        "category": "Multi Cap",
        "risk_level": "high",
        "min_investment": 5000,
        "description": "Multi cap fund for diversified equity exposure"
    },
    {
        "name": "ICICI Prudential Bluechip Fund",
        "type": "equity",
        "category": "Large Cap",
        "risk_level": "high",
        "min_investment": 5000,
        "description": "Large cap fund with strong track record"
    },
    {
        "name": "Axis Bluechip Fund",
        "type": "equity",
        "category": "Large Cap",
        "risk_level": "high",
        "min_investment": 5000,
        "description": "Large cap equity fund"
    },
    {
        "name": "Mirae Asset Large Cap Fund",
        "type": "equity",
        "category": "Large Cap",
        "risk_level": "high",
        "min_investment": 5000,
        "description": "Large cap fund with good returns"
    },
    # Debt Funds
    {
        "name": "HDFC Debt Fund",
        "type": "debt",
        "category": "Corporate Bond",
        "risk_level": "low",
        "min_investment": 5000,
        "description": "Low risk debt fund for stable returns"
    },
    {
        "name": "ICICI Prudential Corporate Bond Fund",
        "type": "debt",
        "category": "Corporate Bond",
        "risk_level": "low",
        "min_investment": 5000,
        "description": "Corporate bond fund with low risk"
    },
    {
        "name": "SBI Magnum Gilt Fund",
        "type": "debt",
        "category": "Gilt",
        "risk_level": "low",
        "min_investment": 5000,
        "description": "Government securities fund"
    },
    # Hybrid Funds
    {
        "name": "HDFC Balanced Advantage Fund",
        "type": "hybrid",
        "category": "Balanced",
        "risk_level": "medium",
        "min_investment": 5000,
        "description": "Balanced fund with equity and debt mix"
    },
    {
        "name": "ICICI Prudential Balanced Advantage Fund",
        "type": "hybrid",
        "category": "Balanced",
        "risk_level": "medium",
        "min_investment": 5000,
        "description": "Dynamic asset allocation fund"
    },
    # Gold Funds
    {
        "name": "SBI Gold Fund",
        "type": "gold",
        "category": "Gold ETF",
        "risk_level": "medium",
        "min_investment": 5000,
        "description": "Gold ETF for portfolio diversification"
    },
    {
        "name": "HDFC Gold Fund",
        "type": "gold",
        "category": "Gold ETF",
        "risk_level": "medium",
        "min_investment": 5000,
        "description": "Gold investment fund"
    },
]


def get_funds_by_risk_profile(risk_profile: str, investable_amount: float = 0) -> List[Dict[str, Any]]:
    """
    Get fund suggestions based on risk profile and investable amount.
    
    Args:
        risk_profile: User's risk profile (low | medium | high)
        investable_amount: Amount available for investment
        
    Returns:
        List of suggested funds
    """
    # Filter by minimum investment
    available_funds = [
        fund for fund in FUNDS_DATABASE
        if investable_amount == 0 or fund["min_investment"] <= investable_amount
    ]
    
    if risk_profile == "low":
        # Prefer debt and hybrid funds
        suggested = [
            f for f in available_funds
            if f["type"] in ["debt", "hybrid"] or f["risk_level"] == "low"
        ]
        # Add some equity for diversification
        equity_funds = [f for f in available_funds if f["type"] == "equity"][:1]
        suggested.extend(equity_funds)
    elif risk_profile == "high":
        # Prefer equity funds
        suggested = [
            f for f in available_funds
            if f["type"] == "equity" or f["risk_level"] == "high"
        ]
        # Add some debt for stability
        debt_funds = [f for f in available_funds if f["type"] == "debt"][:1]
        suggested.extend(debt_funds)
    else:  # medium
        # Balanced mix
        suggested = available_funds
    
    # Limit to 5-6 funds
    return suggested[:6]


def format_fund_suggestions(funds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format fund suggestions for API response.
    
    Args:
        funds: List of fund dictionaries
        
    Returns:
        Formatted fund suggestions
    """
    return [
        {
            "name": fund["name"],
            "type": fund["type"],
            "category": fund["category"],
            "risk_level": fund["risk_level"],
            "min_investment": fund["min_investment"],
            "description": fund["description"]
        }
        for fund in funds
    ]

