import streamlit as st
import yfinance as yf
import requests
import numpy as np
from textblob import TextBlob
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# ===============================
# 🔑 CONFIGURATION
# ===============================
NEWS_API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"  # Replace with your own valid key

# Custom mapping for BSE tickers
CUSTOM_TICKERS = {
    "cianagro": "CIANAGRO.BO",
    "hdfcbank": "HDFCBANK.NS",
    "reliance": "RELIANCE.NS",
    "infy": "INFY.NS",
    "tcs": "TCS.NS",
}

# ===============================
# 📰 FETCH NEWS
# ===============================
def fetch_news(company, limit=10):
    query = f"{company} stock OR shares OR earnings OR results"
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en&sortBy=publishedAt&pageSize={limit}&apiKey={NEWS_API_KEY}"
    )
    try:
        resp = requests.get(url)
        data = resp.json()
        if data["status"] != "ok" or not data["articles"]:
            return []
        articles = []
        for a in data["articles"]:
            title = a.get("title") or ""
            desc = a.get("description") or ""
            content = f"{title}. {desc}"
            articles.append(content)
        return articles
    except Exception:
        return []

# ===============================
# 🧠 SENTIMENT ANALYSIS
# ===============================
def analyze_sentiment(news_list):
    if not news_list:
        return None
    sentiments = {"positive": 0, "negative": 0, "neutral": 0}
    polarity_scores = []

    for news in news_list:
        blob = TextBlob(news)
        polarity = blob.sentiment.polarity
        polarity_scores.append(polarity)
        if polarity > 0.1:
            sentiments["positive"] += 1
        elif polarity < -0.1:
            sentiments["negative"] += 1
        else:
            sentiments["neutral"] += 1

    avg_polarity = np.mean(polarity_scores)
    if avg_polarity > 0.05:
        overall = "Positive"
    elif avg_polarity < -0.05:
        overall = "Negative"
    else:
        overall = "Neutral"

    return {
        "summary": sentiments,
        "avg_polarity": avg_polarity,
        "overall": overall,
    }

# ===============================
# 💹 STOCK DATA FETCH + PREDICTION
# ===============================
def get_symbol_for_company(company):
    return CUSTOM_TICKERS.get(company.lower(), company.upper() + ".NS")

def fetch_stock_data(company):
    symbol = get_symbol_for_company(company)
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="6mo", interval="1d")

    # If no data, try alternate (.BO)
    if data.empty:
        if symbol.endswith(".NS"):
            alt_symbol = company.upper() + ".BO"
            ticker = yf.Ticker(alt_symbol)
            data = ticker.history(period="6mo", interval="1d")
        if data.empty:
            return None

    last_close = data["Close"].iloc[-1]
    prev_close = data["Close"].iloc[-2]
    change = last_close - prev_close
    percent_change = (change / prev_close) * 100

    # Simple linear trend prediction
    x = np.arange(len(data["Close"]))
    y = data["Close"].values
    m, b = np.polyfit(x, y, 1)
    predicted_next = m * (len(data["Close"]) + 1) + b

    # Suggestion
    if predicted_next > last_close * 1.02:
        suggestion = "BUY"
    elif predicted_next < last_close * 0.98:
        suggestion = "SELL"
    else:
        suggestion = "HOLD"

    return {
        "symbol": symbol,
        "last_close": last_close,
        "prev_close": prev_close,
        "change": change,
        "percent": percent_change,
        "predicted_next": predicted_next,
        "suggestion": suggestion,
        "info": ticker.info,
    }

# ===============================
# 📊 GENERATE FULL REPORT
# ===============================
def generate_report(company):
    st.markdown(f"## 📊 {company.upper()} Stock Report")

    stock_data = fetch_stock_data(company)
    if not stock_data:
        st.warning(f"⚠️ No market data found for {company.upper()}. Try another company.")
        return

    info = stock_data["info"]
    fundamentals = {
        "Market Cap": info.get("marketCap", "N/A"),
        "P/E Ratio": info.get("trailingPE", "N/A"),
        "P/B Ratio": info.get("priceToBook", "N/A"),
        "EPS": info.get("trailingEps", "N/A"),
        "Dividend Yield": info.get("dividendYield", "N/A"),
    }

    st.markdown(
        f"""
        **💰 Market Summary**
        - Last Close: ₹{stock_data['last_close']:.2f}
        - Daily Change: {stock_data['change']:+.2f} ({stock_data['percent']:+.2f}%)
        - Predicted Next Day Close: ₹{stock_data['predicted_next']:.2f}
        - Suggestion: **{stock_data['suggestion']}**
        """
    )

    st.markdown("### 📈 Fundamentals")
    for k, v in fundamentals.items():
        st.write(f"**{k}:** {v}")

    # --- News + Sentiment ---
    news_list = fetch_news(company, limit=10)
    if not news_list:
        st.warning("⚠️ No news data found.")
        return

    sentiment = analyze_sentiment(news_list)
    if sentiment:
        st.markdown(
            f"""
            ### 🧠 Sentiment Analysis  
            - Positive: {sentiment['summary']['positive']}  
            - Negative: {sentiment['summary']['negative']}  
            - Neutral: {sentiment['summary']['neutral']}  
            - **Overall Sentiment:** {sentiment['overall']}  
            """
        )

    st.markdown("### 🗞️ Recent News Headlines")
    for n in news_list[:5]:
        st.markdown(f"📰 {n}")

    # Final Recommendation
    st.markdown("### 💡 Investment Insight")
    overall = sentiment["overall"]
    suggestion = stock_data["suggestion"]

    if overall == "Positive" and suggestion == "BUY":
        st.success("✅ Positive sentiment and bullish trend — strong **BUY** signal.")
    elif overall == "Negative" and suggestion == "SELL":
        st.error("⚠️ Negative sentiment and downtrend — consider **SELLING**.")
    else:
        st.info("🤔 Mixed or neutral signals — consider **HOLDING** for now.")

# ===============================
# 💬 STREAMLIT CHATBOT UI
# ===============================
def run_chatbot_ui():
    st.set_page_config(page_title="StockVerse Chatbot", page_icon="💹", layout="centered")

    st.title("🤖 StockVerse — AI Stock Market Chatbot (India)")
    st.caption("Analyze Indian stocks using sentiment & trend prediction")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    user_input = st.chat_input("Ask about a company (e.g., TCS, Reliance, HDFCBANK, CIANAGRO)...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Display all messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Generate response
        with st.chat_message("assistant"):
            generate_report(user_input)

# ===============================
# 🚀 MAIN
# ===============================
if __name__ == "__main__":
    run_chatbot_ui()
