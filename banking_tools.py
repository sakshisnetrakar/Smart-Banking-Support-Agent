"""Simulated banking tools for the LangChain agent."""

from math import pow
from uuid import uuid4

from langchain_core.tools import tool

ACCOUNTS = {
    "CUST1001": {"customer_name": "Aarav Sharma", "account_type": "Savings", "account_status": "Active", "credit_score": 755},
    "CUST1002": {"customer_name": "Diya Patel", "account_type": "Salary", "account_status": "Active", "credit_score": 720},
}
APPLICATIONS: list[dict] = []


@tool
def calculate_emi(principal: float, annual_interest_rate: float, tenure_years: float) -> dict:
    """Calculate the monthly EMI for a loan. Interest rate is annual percentage."""
    months = int(tenure_years * 12)
    monthly_rate = annual_interest_rate / 1200
    emi = principal / months if monthly_rate == 0 else principal * monthly_rate * pow(1 + monthly_rate, months) / (pow(1 + monthly_rate, months) - 1)
    return {"monthly_emi": round(emi, 2), "formatted_emi": f"₹{emi:,.2f}", "months": months}


@tool
def check_loan_eligibility(monthly_salary: float, existing_monthly_emi: float, proposed_monthly_emi: float, loan_amount: float) -> dict:
    """Check affordability. Total EMIs must not exceed 40 percent of monthly salary."""
    maximum_total = monthly_salary * 0.40
    total = existing_monthly_emi + proposed_monthly_emi
    eligible = total <= maximum_total
    return {"eligible": eligible, "maximum_total_emi": round(maximum_total, 2), "total_emi": round(total, 2), "reason": "Affordable within the 40% EMI-to-income limit." if eligible else "Total EMI exceeds the 40% EMI-to-income limit.", "requested_amount": loan_amount}


@tool
def retrieve_account_details(customer_id: str) -> dict:
    """Retrieve simulated account information using a customer ID such as CUST1001."""
    account = ACCOUNTS.get(customer_id.upper())
    return {"found": bool(account), "customer_id": customer_id.upper(), **(account or {"message": "No demo account found."})}


@tool
def submit_loan_application(customer_id: str, loan_type: str, loan_amount: float, tenure_years: float) -> dict:
    """Submit a simulated application after eligibility and customer confirmation."""
    application = {"application_id": f"APP-{uuid4().hex[:8].upper()}", "customer_id": customer_id.upper(), "loan_type": loan_type.title(), "loan_amount": loan_amount, "tenure_years": tenure_years, "status": "Submitted for bank review"}
    APPLICATIONS.append(application)
    return application
