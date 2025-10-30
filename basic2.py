import spacy
import yfinance as yf
import random
import numpy as np
from sklearn.linear_model import LinearRegression
import re

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# ------------------------------
# FETCH & ANALYZE INDIAN STOCK DATA
# ------------------------------
def get_stock_report(company):
    # Always append ".NS" for Indian companies
    ticker_symbol = company.upper().replace(".NS", "") + ".NS"

    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="60d")
        if hist.empty:
            return f"⚠️ No data found for '{ticker_symbol}'. Check if the NSE symbol is correct."
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

    X = np.arange(len(hist)).reshape(-1, 1)
    y = hist["Close"].values

    model = LinearRegression()
    model.fit(X, y)

    next_day = np.array([[len(hist) + 1]])
    predicted_price = model.predict(next_day)[0]
    profit_pred = ((predicted_price - current_price) / current_price) * 100

    # ------------------------------
    # FINAL REPORT
    # ------------------------------
    report = f"📊 NSE Stock Report for {ticker_symbol}\n"
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
    """
    Improved preprocessing:
    - strip filler words
    - use spaCy NER for ORG/PRODUCT
    - fall back to proper nouns / alpha tokens
    - fallback to simple regex ticker-like token
    - normalize and append .NS if missing
    """
    # clean input
    s = user_input.lower()
    # remove common filler words that users often include
    fillers = ["stock", "stocks", "price", "predict", "prediction", "report", "nse", "share", "shares", "invest", "of", "for", "on", "the"]
    for f in fillers:
        s = re.sub(r'\b' + re.escape(f) + r'\b', ' ', s)
    s = re.sub(r'[^\w\s]', ' ', s).strip()

    # try spaCy NER first
    doc = nlp(s)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:
            name = ent.text.strip()
            return normalize_ticker(name)

    # try proper nouns / nouns (PROPN, NOUN) excluding stop words
    tokens = [t.text for t in doc if (t.pos_ in ["PROPN", "NOUN"] and not t.is_stop)]
    for tok in tokens:
        if tok.isalpha():
            return normalize_ticker(tok)

    # fallback: pick an alphanumeric token that looks like a ticker (2-6 letters)
    m = re.search(r'\b([A-Za-z]{2,6})\b', s)
    if m:
        return normalize_ticker(m.group(1))

    return None

def normalize_ticker(name):
    """
    Normalize extracted company name/ticker to NSE ticker form:
    - If user already provided an NSE-style ticker (ends with .NS) return uppercased
    - Otherwise uppercase and append .NS
    - Remove common suffixes like 'ltd', 'limited', 'inc' when present in full company names
    """
    if not name:
        return None
    name = name.strip()
    # Remove corporate suffixes
    name = re.sub(r'\b(limited|ltd|inc|corporation|co|company|private|pvt)\b', ' ', name, flags=re.I).strip()
    # If already has .NS or NSE in name, normalize
    if name.upper().endswith(".NS"):
        return name.upper()
    # If user typed a long company name (contains spaces), take last token (often ticker or short name)
    if " " in name:
        # use last meaningful token
        parts = [p for p in name.split() if p.isalpha()]
        if parts:
            name = parts[-1]
    name = re.sub(r'[^A-Za-z0-9]', '', name).upper()
    if not name:
        return None
    return name + ".NS"


def chatbot_response(user_input):
    intent = get_intent(user_input)
    if intent in ["get_report", "predict"]:
        company = extract_company_name(user_input)
        if company:
            return get_stock_report(company)
        else:
            return "Please specify an Indian company name or NSE ticker (e.g., RELIANCE, TCS, INFY)."
    else:
        return random.choice([
            "Ask me about any NSE stock! e.g., 'Show report on TCS'",
            "I can predict if an Indian stock is profitable to invest.",
            "Try saying: 'Predict next day price of Reliance'"
        ])


# ------------------------------
# MAIN LOOP
# ------------------------------
print("🤖 SmartStockBot (India Edition): Ask me about any NSE stock! Type 'exit' to quit.")
while True:
    user = input("You: ")
    if user.lower() in ["exit", "quit"]:
        print("Bot: Goodbye! 👋")
        break
    print("Bot:", chatbot_response(user))
