import streamlit as st
import yfinance as yf
import requests
from textblob import TextBlob
from datetime import datetime
import pandas as pd

# ===============================
# 🔑 API Configuration
# ===============================
NEWS_API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"  # Get yours from https://newsapi.org/

# ===============================
# 🧾 Fetch Stock Data
# ===============================
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol + ".NS")
        info = ticker.info

        if not info or "regularMarketPrice" not in info:
            # Try global symbol
            ticker = yf.Ticker(symbol)
            info = ticker.info

        if not info or "regularMarketPrice" not in info:
            return None, None

        last_close = info.get("previousClose", 0)
        current_price = info.get("regularMarketPrice", last_close)
        day_change = round(((current_price - last_close) / last_close) * 100, 2) if last_close else 0

        fundamentals = {
            "Company": info.get("longName", symbol),
            "Sector": info.get("sector", "N/A"),
            "Last Close": f"₹{last_close}",
            "Current Price": f"₹{current_price}",
            "Daily Change": f"{day_change}%",
            "52W High": f"₹{info.get('fiftyTwoWeekHigh', 'N/A')}",
            "52W Low": f"₹{info.get('fiftyTwoWeekLow', 'N/A')}",
            "Market Cap": f"{info.get('marketCap', 'N/A'):,}",
            "P/E Ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
            "P/B Ratio": round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else "N/A",
            "EPS": info.get("trailingEps", "N/A"),
            "Dividend Yield": f"{round(info.get('dividendYield', 0)*100, 2)}%" if info.get("dividendYield") else "N/A",
        }

        hist = ticker.history(period="1mo").reset_index()
        return fundamentals, hist
    except Exception as e:
        print("Error fetching stock data:", e)
        return None, None

# ===============================
# 📰 Fetch Relevant Financial News
# ===============================
def get_relevant_news(company, limit=10):
    query = f'"{company}" AND (stock OR share OR market OR NSE OR BSE OR results OR earnings OR profit OR loss OR dividend OR forecast)'
    domains = "moneycontrol.com,livemint.com,economictimes.indiatimes.com,business-standard.com,reuters.com,bloomberg.com"

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en&sortBy=relevancy&pageSize={limit}&domains={domains}&apiKey={NEWS_API_KEY}"
    )

    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") != "ok":
            return []
        return data.get("articles", [])
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

# ===============================
# 🧠 Sentiment Analysis
# ===============================
def analyze_sentiment(news_articles):
    pos, neg, neu = 0, 0, 0
    for article in news_articles:
        text = article["title"] + " " + article.get("description", "")
        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.1:
            pos += 1
        elif polarity < -0.1:
            neg += 1
        else:
            neu += 1
    total = pos + neg + neu
    overall = "Positive" if pos > neg and pos > neu else "Negative" if neg > pos else "Neutral"
    return {"positive": pos, "negative": neg, "neutral": neu, "overall": overall, "total": total}

# ===============================
# 💬 AI Recommendation
# ===============================
def get_recommendation(fundamentals, sentiment):
    pe = fundamentals.get("P/E Ratio")
    pb = fundamentals.get("P/B Ratio")
    if pe == "N/A" or pb == "N/A":
        return "❓ Insufficient data for AI recommendation."

    try:
        if isinstance(pe, (int, float)) and isinstance(pb, (int, float)):
            if pe < 15 and pb < 3 and sentiment["overall"] == "Positive":
                return "✅ BUY — undervalued fundamentals and positive market sentiment."
            elif pe > 25 and sentiment["overall"] == "Negative":
                return "⚠️ SELL — overvalued with negative sentiment."
            else:
                return "🤝 HOLD — mixed or neutral conditions."
        else:
            return "❓ Data not sufficient for analysis."
    except Exception:
        return "❌ Error generating recommendation."

# ===============================
# 🎨 Streamlit Chatbot UI
# ===============================
st.set_page_config(page_title="📈 Stock Market Chatbot", page_icon="💹", layout="wide")

st.title("💬 StockVerse AI — Indian & Global Stock Chatbot")
st.caption("Your personal AI analyst for real-time fundamentals, news, and sentiment.")

# Session setup
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask about any company (e.g., TCS, RELIANCE, INFY, AAPL)...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Process user query
if user_input:
    company = user_input.strip().upper()
    with st.chat_message("assistant"):
        with st.spinner(f"Fetching data for {company}..."):
            fundamentals, hist = get_stock_data(company)

            if not fundamentals:
                st.error(f"⚠️ No market data found for {company}. Try another company.")
            else:
                # ---------------- Fundamentals ----------------
                st.subheader(f"📊 {fundamentals['Company']} — Overview")
                cols = st.columns(3)
                for i, (k, v) in enumerate(fundamentals.items()):
                    cols[i % 3].metric(k, v)

                # ---------------- Price Chart ----------------
                if hist is not None and not hist.empty:
                    st.subheader("📈 Last 30 Days Trend")
                    st.line_chart(hist.set_index("Date")["Close"])

                # ---------------- News & Sentiment ----------------
                news = get_relevant_news(company)
                if news:
                    st.subheader("📰 Financial News")
                    for n in news:
                        st.markdown(f"**[{n['title']}]({n['url']})** — *{n['source']['name']}*")
                        st.caption(f"🕓 {n['publishedAt'][:10]} | {n.get('description', '')}")

                    sentiment = analyze_sentiment(news)
                    st.subheader("🧠 Sentiment Analysis")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("🟢 Positive", sentiment["positive"])
                    c2.metric("🔴 Negative", sentiment["negative"])
                    c3.metric("🟡 Neutral", sentiment["neutral"])

                    st.progress(sentiment["positive"] / sentiment["total"] if sentiment["total"] else 0.1)
                    st.write(f"**Overall Sentiment:** {sentiment['overall']}")

                    # ---------------- AI Recommendation ----------------
                    rec = get_recommendation(fundamentals, sentiment)
                    st.subheader("🤖 AI Recommendation")
                    st.success(rec)
                else:
                    st.warning("No relevant financial news found.")
