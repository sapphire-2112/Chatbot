import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from textblob import TextBlob
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards  # pip install streamlit-extras

# ==========================
# CONFIG
# ==========================
st.set_page_config(page_title="StockVerse - AI Stock Advisor", layout="wide")
st.title("📊 StockVerse – AI Stock Market Advisor (India)")
st.caption("Analyze fundamentals, technicals & sentiment for Indian companies in real-time")

NEWS_API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"  # Replace with your News API key

# ==========================
# COMPANY INPUT WITH SUGGESTIONS
# ==========================
popular_companies = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
    "LT", "HINDUNILVR", "AXISBANK", "CIPLA", "SUNPHARMA", "Cian Agro"
]

col1, col2 = st.columns([2, 1])
company = col1.selectbox("🔍 Choose a company", options=popular_companies, index=0)
custom = col2.text_input("Or type another company name")
if custom.strip():
    company = custom.strip()

symbol = company.upper().replace(" ", "") + ".NS"  # Yahoo Finance ticker format for NSE

# ==========================
# FETCH FUNDAMENTALS
# ==========================
def get_fundamentals(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info

    fundamentals = {
        "Market Cap": info.get("marketCap", "N/A"),
        "P/E Ratio": info.get("trailingPE", "N/A"),
        "P/B Ratio": info.get("priceToBook", "N/A"),
        "EPS": info.get("trailingEps", "N/A"),
        "Dividend Yield": info.get("dividendYield", "N/A"),
    }
    return fundamentals, ticker

# ==========================
# FETCH NEWS & SENTIMENT
# ==========================
def fetch_relevant_news(company, limit=10):
    query = f"{company} stock OR shares OR earnings OR results OR market OR forecast OR profit OR loss"
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en&sortBy=publishedAt&pageSize={limit}&apiKey={NEWS_API_KEY}"
    )
    try:
        resp = requests.get(url)
        data = resp.json()
        if data.get("status") != "ok" or not data.get("articles"):
            return []
        articles = []
        for a in data["articles"]:
            title = a.get("title") or ""
            desc = a.get("description") or ""
            if company.lower() in title.lower() or company.lower() in desc.lower():
                articles.append(f"{title}. {desc}")
        return articles
    except Exception:
        return []

def analyze_sentiment(news_list):
    sentiments = {"Positive": 0, "Negative": 0, "Neutral": 0}
    polarity_scores = []
    for news in news_list:
        blob = TextBlob(news)
        polarity = blob.sentiment.polarity
        polarity_scores.append(polarity)
        if polarity > 0.1:
            sentiments["Positive"] += 1
        elif polarity < -0.1:
            sentiments["Negative"] += 1
        else:
            sentiments["Neutral"] += 1

    avg_polarity = np.mean(polarity_scores) if polarity_scores else 0
    if avg_polarity > 0.05:
        overall = "Positive"
    elif avg_polarity < -0.05:
        overall = "Negative"
    else:
        overall = "Neutral"

    return sentiments, overall

# ==========================
# PRICE ANALYSIS
# ==========================
def get_price_summary(ticker):
    hist = ticker.history(period="6mo")
    if hist.empty:
        return None
    last_close = hist["Close"].iloc[-1]
    prev_close = hist["Close"].iloc[-2]
    change = last_close - prev_close
    percent = (change / prev_close) * 100
    return last_close, change, percent

def get_investment_suggestion(sentiment, fundamentals, price_change):
    if sentiment == "Positive" and price_change > 0:
        return "BUY ✅"
    elif sentiment == "Negative" and price_change < 0:
        return "SELL ⚠️"
    else:
        return "HOLD 🤔"

# ==========================
# RUN ANALYSIS
# ==========================
fundamentals, ticker = get_fundamentals(symbol)
price_data = get_price_summary(ticker)
news_list = fetch_relevant_news(company)
sentiments, overall_sentiment = analyze_sentiment(news_list)
suggestion = get_investment_suggestion(overall_sentiment, fundamentals, price_data[1] if price_data else 0)

# ==========================
# DISPLAY RESULTS
# ==========================
st.subheader(f"📈 {company.upper()} – Stock Overview")

if price_data:
    st.metric("Last Close", f"₹{price_data[0]:.2f}", f"{price_data[2]:.2f}%")
else:
    st.warning("No price data found for this company.")

# ---- Fundamentals Grid ----
st.markdown("### 🧮 Fundamental Overview")
cols = st.columns(len(fundamentals))
for (key, val), col in zip(fundamentals.items(), cols):
    display_val = f"{val:.2f}" if isinstance(val, (int, float)) else val
    col.metric(label=key, value=display_val)
style_metric_cards(background_color="#f5f5f5", border_left_color="#1E90FF", border_color="#dcdcdc")

# ---- Sentiment Section ----
st.markdown("### 🧠 News Sentiment Analysis")
st.write(f"**Overall Sentiment:** 🟢 {overall_sentiment}" if overall_sentiment == "Positive"
         else f"**Overall Sentiment:** 🔴 {overall_sentiment}" if overall_sentiment == "Negative"
         else f"**Overall Sentiment:** 🟡 {overall_sentiment}")

st.write(
    f"✅ Positive: {sentiments['Positive']} | ⚠️ Negative: {sentiments['Negative']} | ⚪ Neutral: {sentiments['Neutral']}"
)

if news_list:
    with st.expander("📰 Recent Relevant News"):
        for n in news_list[:8]:
            st.markdown(f"- {n}")
else:
    st.warning("No relevant stock news found.")

# ---- Investment Suggestion ----
st.markdown("### 💡 Investment Suggestion")
st.success(f"Suggested Action: **{suggestion}**")

# ---- Footer ----
st.caption("Powered by Yahoo Finance + NewsAPI | Built with Streamlit 💹")
