import requests
from textblob import TextBlob
import yfinance as yf
import numpy as np
from termcolor import colored
import datetime
import warnings

warnings.filterwarnings("ignore")

# ===============================
# 🔑 API KEY CONFIGURATION
# ===============================
NEWS_API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"  # Replace with your valid key

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
            print(colored(f"⚠️ No news found for {company}.", "yellow"))
            return []

        articles = []
        for a in data["articles"]:
            title = a.get("title") or ""
            desc = a.get("description") or ""
            content = f"{title}. {desc}"
            articles.append(content)
        return articles

    except Exception as e:
        print(colored(f"❌ Error fetching news: {e}", "red"))
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
        overall = "positive"
    elif avg_polarity < -0.05:
        overall = "negative"
    else:
        overall = "neutral"

    return {
        "summary": sentiments,
        "avg_polarity": avg_polarity,
        "overall": overall,
    }

# ===============================
# 💹 STOCK DATA & PREDICTION
# ===============================
def fetch_stock_data(company):
    try:
        ticker = yf.Ticker(company + ".NS")
        data = ticker.history(period="6mo")

        if data.empty:
            print(colored(f"⚠️ No market data found for {company}.", "yellow"))
            return None

        last_close = data["Close"].iloc[-1]
        prev_close = data["Close"].iloc[-2]
        change = last_close - prev_close
        percent_change = (change / prev_close) * 100

        # Simple trend prediction (linear extrapolation)
        x = np.arange(len(data["Close"]))
        y = data["Close"].values
        m, b = np.polyfit(x, y, 1)
        predicted_next = m * (len(data["Close"]) + 1) + b

        # Buy/Sell/Hold logic
        if predicted_next > last_close * 1.02:
            suggestion = "BUY"
        elif predicted_next < last_close * 0.98:
            suggestion = "SELL"
        else:
            suggestion = "HOLD"

        return {
            "last_close": last_close,
            "prev_close": prev_close,
            "change": change,
            "percent": percent_change,
            "predicted_next": predicted_next,
            "suggestion": suggestion,
        }

    except Exception as e:
        print(colored(f"❌ Error fetching stock data: {e}", "red"))
        return None

# ===============================
# 📊 GENERATE COMBINED REPORT
# ===============================
def generate_report(company):
    print(colored(f"\n📊 Generating report for {company.upper()}...\n", "cyan"))

    # Fetch and analyze news
    news_list = fetch_news(company, limit=15)
    if not news_list:
        print(colored("⚠️ No news data to analyze.", "yellow"))
        return

    sentiment_result = analyze_sentiment(news_list)
    overall = sentiment_result["overall"]
    summary = sentiment_result["summary"]

    print(colored("🧾 Sentiment Analysis Summary", "green"))
    print(f"🟢 Positive: {summary['positive']}")
    print(f"🔴 Negative: {summary['negative']}")
    print(f"🟡 Neutral:  {summary['neutral']}")
    print(f"📈 Overall Sentiment: {overall.upper()}\n")

    # Fetch market data
    stock_data = fetch_stock_data(company)
    if not stock_data:
        return

    print(colored("💹 Market Summary", "magenta"))
    print(f"• Last Close: ₹{stock_data['last_close']:.2f}")
    print(f"• Change: {stock_data['change']:+.2f} ({stock_data['percent']:+.2f}%)")
    print(f"• Predicted Next Day Close: ₹{stock_data['predicted_next']:.2f}")
    print(colored(f"📊 Suggested Action: {stock_data['suggestion']}", "blue"))

    # Combine both aspects
    print(colored("\n💡 Investment Insight:", "cyan"))
    if overall == "positive" and stock_data["suggestion"] == "BUY":
        print("✅ Positive news sentiment aligns with upward price prediction — strong BUY signal.")
    elif overall == "negative" and stock_data["suggestion"] == "SELL":
        print("⚠️ Negative sentiment and falling trend — consider SELLING or avoiding entry.")
    else:
        print("🤔 Mixed signals — consider HOLDING and re-evaluating after next market session.")

# ===============================
# 💬 INTERACTIVE CHATBOT
# ===============================
def run_chatbot():
    print(colored("🤖 Welcome to StockVerse: Your AI Market Advisor!", "cyan"))
    print("Type a company name (e.g., Reliance, TCS, Infosys) or 'exit' to quit.\n")

    while True:
        cmd = input(colored("You: ", "yellow")).strip()
        if cmd.lower() in ["exit", "quit"]:
            print(colored("👋 Exiting StockVerse. Stay smart with your investments!", "cyan"))
            break
        elif len(cmd) < 2:
            print("⚠️ Please enter a valid company name.")
            continue
        else:
            generate_report(cmd)

# ===============================
# 🚀 MAIN ENTRY
# ===============================
if __name__ == "__main__":
    run_chatbot()
