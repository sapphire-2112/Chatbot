import streamlit as st
import yfinance as yf
import requests
from textblob import TextBlob
import numpy as np
import pandas as pd

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="StockVerse - Simple Market Analyzer", layout="wide")
st.title("📈 StockVerse: Simple Stock Analyzer")
st.write("Enter any company name to analyze fundamentals, sentiment, and market signals.")

NEWS_API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"  # 🔑 Replace with your valid NewsAPI key


# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def get_symbol_from_name(company_name):
    """Try to get a valid symbol from Yahoo Finance search."""
    company_name = company_name.strip()
    if not company_name:
        return None

    try:
        res = requests.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={company_name}", timeout=5).json()
        quotes = res.get("quotes", [])
        if quotes:
            return quotes[0]["symbol"]
    except Exception:
        pass

    # Fallback for Indian NSE
    fallback_symbol = company_name.replace(" ", "").upper() + ".NS"
    try:
        ticker = yf.Ticker(fallback_symbol)
        data = ticker.history(period="1d")
        if not data.empty:
            return fallback_symbol
    except Exception:
        pass

    return None


def get_fundamentals(symbol):
    """Fetch company fundamentals."""
    ticker = yf.Ticker(symbol)
    try:
        info = ticker.get_info()
    except Exception:
        info = {}

    fast_info = getattr(ticker, "fast_info", {})

    fundamentals = {
        "Market Cap": info.get("marketCap", fast_info.get("market_cap", "N/A")),
        "P/E Ratio": info.get("trailingPE", fast_info.get("pe_ratio", "N/A")),
        "P/B Ratio": info.get("priceToBook", "N/A"),
        "EPS": info.get("trailingEps", "N/A"),
        "Dividend Yield": round(info.get("dividendYield", 0) * 100, 2)
        if info.get("dividendYield") else "N/A",
    }

    overview = {
        "Company Name": info.get("longName", symbol.replace(".NS", "")),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Currency": info.get("currency", "INR"),
    }

    return fundamentals, overview


def fetch_relevant_news(company, limit=5):
    """Fetch company-related news headlines."""
    query = f"{company} stock OR {company} results OR earnings OR profit OR loss"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=relevancy&pageSize={limit}&apiKey={NEWS_API_KEY}"

    try:
        resp = requests.get(url)
        data = resp.json()
        if data["status"] != "ok" or not data["articles"]:
            return []
        articles = []
        for a in data["articles"]:
            title = a.get("title") or ""
            desc = a.get("description") or ""
            articles.append(f"{title}. {desc}")
        return articles
    except Exception:
        return []


def analyze_sentiment(news_list):
    """Perform basic sentiment analysis using TextBlob."""
    if not news_list:
        return None

    sentiments = {"positive": 0, "negative": 0, "neutral": 0}
    scores = []

    for news in news_list:
        blob = TextBlob(news)
        polarity = blob.sentiment.polarity
        scores.append(polarity)

        if polarity > 0.1:
            sentiments["positive"] += 1
        elif polarity < -0.1:
            sentiments["negative"] += 1
        else:
            sentiments["neutral"] += 1

    avg_polarity = np.mean(scores)
    if avg_polarity > 0.05:
        overall = "Positive"
    elif avg_polarity < -0.05:
        overall = "Negative"
    else:
        overall = "Neutral"

    return {"summary": sentiments, "avg": avg_polarity, "overall": overall}


def analyze_stock(symbol):
    """Fetch price trend and predict next move."""
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="6mo")

    if data.empty:
        return None

    last_close = data["Close"].iloc[-1]
    prev_close = data["Close"].iloc[-2]
    change = last_close - prev_close
    percent = (change / prev_close) * 100

    x = np.arange(len(data["Close"]))
    y = data["Close"].values
    m, b = np.polyfit(x, y, 1)
    predicted_next = m * (len(data["Close"]) + 1) + b

    if predicted_next > last_close * 1.02:
        suggestion = "BUY"
    elif predicted_next < last_close * 0.98:
        suggestion = "SELL"
    else:
        suggestion = "HOLD"

    return {
        "last_close": last_close,
        "change": change,
        "percent": percent,
        "predicted_next": predicted_next,
        "suggestion": suggestion,
    }


# ----------------------------
# UI INPUT
# ----------------------------
company_input = st.text_input("🔍 Enter Company Name (e.g., TCS, Infosys, Reliance, Apple):")

if st.button("Analyze") and company_input:
    symbol = get_symbol_from_name(company_input)
    if not symbol:
        st.error("❌ Could not find this company on Yahoo Finance.")
    else:
        st.write(f"**✅ Found Symbol:** {symbol}")

        fundamentals, overview = get_fundamentals(symbol)
        stock_data = analyze_stock(symbol)
        news_list = fetch_relevant_news(company_input, limit=8)
        sentiment = analyze_sentiment(news_list)

        # --- Overview ---
        st.subheader("🏢 Company Overview")
        for k, v in overview.items():
            st.write(f"**{k}:** {v}")

        # --- Fundamentals ---
        st.subheader("📊 Fundamentals")
        for k, v in fundamentals.items():
            if isinstance(v, (int, float)):
                v = f"{v:,.2f}"
            st.write(f"**{k}:** {v}")

        # --- Market Trend ---
        if stock_data:
            st.subheader("💰 Market Summary")
            st.write(f"**Last Close:** ₹{stock_data['last_close']:.2f}")
            st.write(f"**Change:** {stock_data['change']:+.2f} ({stock_data['percent']:+.2f}%)")
            st.write(f"**Predicted Next Close:** ₹{stock_data['predicted_next']:.2f}")

            suggestion = stock_data["suggestion"]
            color = "green" if suggestion == "BUY" else "red" if suggestion == "SELL" else "orange"
            st.markdown(f"### Suggested Action: <span style='color:{color}'>{suggestion}</span>", unsafe_allow_html=True)

        # --- Sentiment ---
        if sentiment:
            st.subheader("🧠 Sentiment Analysis (from latest news)")
            pos = sentiment["summary"]["positive"]
            neg = sentiment["summary"]["negative"]
            neu = sentiment["summary"]["neutral"]
            overall = sentiment["overall"]
            st.markdown(f"""
            🟢 **Positive:** {pos}  
            🔴 **Negative:** {neg}  
            ⚪ **Neutral:** {neu}  
            **Overall Sentiment:** <b style='color:blue'>{overall}</b>
            """, unsafe_allow_html=True)

        # --- News ---
        if news_list:
            st.subheader("🗞️ Latest News Headlines")
            for i, article in enumerate(news_list, 1):
                st.markdown(f"{i}. {article}")

        # --- Insight ---
        if sentiment and stock_data:
            overall = sentiment["overall"]
            sugg = stock_data["suggestion"]

            st.subheader("💡 Investment Insight")
            if overall == "Positive" and sugg == "BUY":
                st.success("✅ Strong BUY signal — positive sentiment & growth trend detected.")
            elif overall == "Negative" and sugg == "SELL":
                st.error("⚠️ SELL signal — negative sentiment & falling trend.")
            else:
                st.info("🤔 Mixed signals — HOLD and monitor upcoming results.")
