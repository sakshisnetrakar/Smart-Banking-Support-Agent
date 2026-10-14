"""One stateful LangChain-tool agent coordinating a banking request."""

import re
from typing import Any

from banking_tools import calculate_emi, check_loan_eligibility, retrieve_account_details, submit_loan_application

SESSIONS: dict[str, dict[str, Any]] = {}
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def _money(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text.lower().replace(",", ""))
    return float(match.group(1)) if match else None


def extract_details(message: str, state: dict[str, Any]) -> None:
    """Store any requested loan data provided in this turn."""
    lower = message.lower()
    values = {
        "loan_amount": _money(r"(?:loan of|for)\s*(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)", message),
        "monthly_salary": _money(r"salary(?: is| of)?\s*(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)", message),
        "existing_emi": _money(r"(?:pay|emi).*?(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)", message),
    }
    for key, value in values.items():
        if value is not None:
            state[key] = value
    if "personal loan" in lower:
        state["loan_type"] = "personal loan"
    rate = re.search(r"(?:interest(?: rate)?(?: is| at)?|at)\s*(\d+(?:\.\d+)?)\s*%", lower)
    years = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", lower)
    word_years = re.search(r"\b(" + "|".join(WORDS) + r")\s+years?", lower)
    customer = re.search(r"\b(cust\d+)\b", message, re.I)
    if rate:
        state["annual_interest_rate"] = float(rate.group(1))
    if years:
        state["tenure_years"] = float(years.group(1))
    elif word_years:
        state["tenure_years"] = float(WORDS[word_years.group(1)])
    if customer:
        state["customer_id"] = customer.group(1).upper()
    if re.search(r"\b(confirm|confirmed|yes,? submit|proceed|submit it)\b", lower):
        state["confirmed"] = True


class SmartBankingAgent:
    """A single agent that selects tools and uses each output in the next decision."""

    tools = [calculate_emi, check_loan_eligibility, retrieve_account_details, submit_loan_application]

    def respond(self, message: str, conversation_id: str) -> dict[str, Any]:
        state = SESSIONS.setdefault(conversation_id, {"history": []})
        extract_details(message, state)
        state["history"].append({"role": "customer", "content": message})
        required = {"loan_amount": "loan amount", "tenure_years": "loan tenure", "monthly_salary": "monthly salary", "existing_emi": "existing monthly EMI", "annual_interest_rate": "annual interest rate", "customer_id": "customer ID"}
        missing = [label for key, label in required.items() if key not in state]
        if missing:
            return self._result(state, conversation_id, "To continue, please provide your " + ", ".join(missing) + ". Use demo customer ID CUST1001 or CUST1002.", missing)

        emi = calculate_emi.invoke({"principal": state["loan_amount"], "annual_interest_rate": state["annual_interest_rate"], "tenure_years": state["tenure_years"]})
        eligibility = check_loan_eligibility.invoke({"monthly_salary": state["monthly_salary"], "existing_monthly_emi": state["existing_emi"], "proposed_monthly_emi": emi["monthly_emi"], "loan_amount": state["loan_amount"]})
        account = retrieve_account_details.invoke({"customer_id": state["customer_id"]})
        state.update(emi=emi, eligibility=eligibility, account=account)
        if not account["found"]:
            return self._result(state, conversation_id, "I calculated your EMI and eligibility, but could not retrieve your demo account. Please check the customer ID.")
        if not eligibility["eligible"]:
            return self._result(state, conversation_id, f"Estimated EMI: {emi['formatted_emi']}. You are not eligible: {eligibility['reason']} No application was submitted.")
        if not state.get("confirmed"):
            answer = f"Estimated EMI: {emi['formatted_emi']}. Eligibility: eligible ({eligibility['reason']}) Account: {account['customer_name']} ({account['account_status']}). Reply 'I confirm' to submit the application."
            return self._result(state, conversation_id, answer, ["customer confirmation"])
        application = submit_loan_application.invoke({"customer_id": state["customer_id"], "loan_type": state.get("loan_type", "personal loan"), "loan_amount": state["loan_amount"], "tenure_years": state["tenure_years"]})
        state["application"] = application
        return self._result(state, conversation_id, f"Estimated EMI: {emi['formatted_emi']}. Eligibility: eligible. Account verified for {account['customer_name']}. Application {application['application_id']} has been submitted for bank review.")

    def _result(self, state: dict[str, Any], conversation_id: str, answer: str, missing: list[str] | None = None) -> dict[str, Any]:
        state["history"].append({"role": "assistant", "content": answer})
        return {"answer": answer, "conversation_id": conversation_id, "missing_information": missing or [], "emi": state.get("emi"), "eligibility": state.get("eligibility"), "account": state.get("account"), "application": state.get("application"), "tools_available": [tool.name for tool in self.tools]}


agent = SmartBankingAgent()
