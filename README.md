# Smart Banking Support Agent

A single Python agent built around LangChain tools. It coordinates EMI calculation, eligibility checking, simulated account lookup, and application submission.

## Safety flow

1. The agent collects missing data.
2. It calculates EMI and passes that result into eligibility checking.
3. It retrieves a simulated account after receiving a customer ID.
4. It asks for explicit confirmation before calling the submission tool.

No real customer data or banking systems are connected.

## Run

```cmd
cd "C:\Users\Sakshi S Netrakar\Desktop\Smart Banking Support Agent"
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

## Demo conversation

1. `I want to apply for a personal loan of ₹5,00,000 for three years. My monthly salary is ₹60,000, and I already pay ₹5,000 as an EMI.`
2. `The interest rate is 10% and my customer ID is CUST1001.`
3. `I confirm.`

The agent submits only a simulated application after message 3.
