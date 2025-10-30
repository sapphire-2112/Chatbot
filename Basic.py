import spacy
import yfinance as yf
import random
import numpy as np
from sklearn.linear_model import LinearRegression

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# ------------------------------
# FETCH & ANALYZE STOCK DATA
# ------------------------------
def get_stock_report(company):
    # Try getting ticker automatically
    try:
        stock = yf.Ticker(company)
        hist = stock.history(period="60d")  # last 60 days
        if hist.empty:
            # Try NSE suffix for Indian companies
            stock = yf.Ticker(company + ".NS")
            hist = stock.history(period="60d")
        if hist.empty:
            return f"⚠️ No data found for '{company}'. Try its ticker symbol (like RELIANCE.NS, AAPL, etc.)"
    except Exception as e:
        return f"❌ Error fetching data: {e}"

    # Basic stats
    current_price = hist["Close"].iloc[-1]
    previous_close = hist["Close"].iloc[-2]
    change = current_price - previous_close
    percent_change = (change / previous_close) * 100
    trend = "📈 up" if change > 0 else "📉 down"

    # ------------------------------
    # SIMPLE PRICE PREDICTION MODEL
    # ------------------------------
    hist["Return"] = hist["Close"].pct_change()
    hist = hist.dropna()

    # Use last 30 days returns as features
    X = np.arange(len(hist)).reshape(-1, 1)
    y = hist["Close"].values

    model = LinearRegression()
    model.fit(X, y)

    next_day = np.array([[len(hist) + 1]])
    predicted_price = model.predict(next_day)[0]
    profit_pred = ((predicted_price - current_price) / current_price) * 100

    # ------------------------------
    # MAKE FINAL REPORT
    # ------------------------------
    report = f"📊 Stock Report for {company.upper()}\n"
    report += f"Current Price: ₹{current_price:.2f}\n"
    report += f"Previous Close: ₹{previous_close:.2f} ({trend}, {percent_change:.2f}%)\n"
    report += f"🔮 Predicted Next Day Price: ₹{predicted_price:.2f}\n"

    if profit_pred > 0:
        report += f"✅ Expected Gain: +{profit_pred:.2f}% (Looks Profitable!)"
    else:
        report += f"⚠️ Expected Loss: {profit_pred:.2f}% (Risky to Invest Now)"

    return report


# ------------------------------
# NLP INTENT & CHATBOT LOGIC
# ------------------------------
def get_intent(user_input):
    user_input = user_input.lower()
    if "report" in user_input or "stock" in user_input:
        return "get_report"
    elif "predict" in user_input or "invest" in user_input:
        return "predict"
    return "smalltalk"


def extract_company_name(user_input):
    doc = nlp(user_input)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:
            return ent.text
    words = user_input.split()
    for w in words:
        if w.isalpha():
            return w
    return None


def chatbot_response(user_input):
    intent = get_intent(user_input)
    if intent in ["get_report", "predict"]:
        company = (extract_company_name(user_input)+".NS")
        if company:
            return get_stock_report(company)
        else:
            return "Please specify the company name or ticker (e.g., TCS.NS, INFY.NS, AAPL)."
    else:
        return random.choice([
            "Ask me about any stock! e.g., 'Show report on TCS.NS'",
            "I can predict if a stock is profitable to invest.",
            "Try saying: 'Predict next day price of Reliance.NS'"
        ])


# ------------------------------
# MAIN LOOP
# ------------------------------
print("🤖 SmartStockBot: Ask me about any stock! Type 'exit' to quit.")
while True:
    user = input("You: ")
    if user.lower() in ["exit", "quit"]:
        print("Bot: Goodbye! 👋")
        break
    print("Bot:", chatbot_response(user))
