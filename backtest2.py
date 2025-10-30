import requests
from transformers import pipeline
from termcolor import colored
import numpy as np
import emoji
from datetime import datetime

# ===============================
# 🔑 SETUP
# ===============================
NEWS_API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"  # Replace with your API key

# Initialize FinBERT model (financial sentiment model)
sentiment_analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")

# Helper function
def slow_print(text):
    print(emoji.emojize(text))


# ===============================
# 📰 Fetch News from NewsAPI
# ===============================
def get_news(company):
    query = f"{company} stock OR shares OR results OR earnings"
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    )

    try:
        resp = requests.get(url)
        data = resp.json()

        if data["status"] != "ok" or not data["articles"]:
            print(colored(f"⚠️ No news found for {company}.", "yellow"))
            return []

        articles = data["articles"]
        print(colored(f"📰 Found {len(articles)} recent articles for {company}.", "magenta"))

        news_list = []
        for a in articles:
            title = a.get("title") or ""
            desc = a.get("description") or ""
            date = a.get("publishedAt") or ""
            source = a.get("source", {}).get("name", "Unknown Source")

            news_item = {
                "title": title.strip(),
                "desc": desc.strip(),
                "date": date,
                "source": source
            }
            news_list.append(news_item)

        return news_list

    except Exception as e:
        print(colored(f"❌ Error fetching news: {e}", "red"))
        return []


# ===============================
# 📊 Analyze Sentiment with FinBERT
# ===============================
def analyze_sentiment(news_list):
    if not news_list:
        return None

    results = []
    for item in news_list:
        text = f"{item['title']}. {item['desc']}"[:512]
        try:
            res = sentiment_analyzer(text)[0]
            res["title"] = item["title"]
            res["source"] = item["source"]
            res["date"] = item["date"]
            results.append(res)
        except Exception as e:
            print(f"Error analyzing: {e}")

    labels = [r["label"].lower() for r in results]
    scores = [r["score"] for r in results]

    total_articles = len(results)
    positive = labels.count("positive")
    negative = labels.count("negative")
    neutral = labels.count("neutral")

    print(colored(f"\n🧾 Sentiment Breakdown ({total_articles} articles):", "cyan"))
    print(f"🟢 Positive: {positive}")
    print(f"🔴 Negative: {negative}")
    print(f"🟡 Neutral: {neutral}")

    avg_confidence = np.mean(scores) if scores else 0
    if positive > negative:
        overall = "positive"
    elif negative > positive:
        overall = "negative"
    else:
        overall = "neutral"

    return {
        "overall": overall,
        "confidence": round(avg_confidence * 100, 2),
        "details": results,
        "count": {"pos": positive, "neg": negative, "neu": neutral}
    }


# ===============================
# 🧠 Generate Investment Report
# ===============================
def generate_report(company):
    print(colored(f"\n📊 Generating full sentiment report for {company.upper()}...", "cyan"))

    news_list = get_news(company)
    if not news_list:
        return

    sentiment_result = analyze_sentiment(news_list)
    if not sentiment_result:
        print("⚠️ Unable to analyze sentiment.")
        return

    overall = sentiment_result["overall"]
    confidence = sentiment_result["confidence"]
    pos = sentiment_result["count"]["pos"]
    neg = sentiment_result["count"]["neg"]
    neu = sentiment_result["count"]["neu"]

    sentiment_icon = {
        "positive": "🟢",
        "negative": "🔴",
        "neutral": "🟡"
    }.get(overall, "⚪")

    print(colored("\n📈 MARKET SENTIMENT SUMMARY", "green"))
    print(f"• Overall Sentiment: {sentiment_icon} {overall.title()}")
    print(f"• Confidence Level: {confidence:.2f}%")
    print(f"• Total Articles Analyzed: {pos + neg + neu}")

    # Top 5 Headlines Preview
    print(colored("\n🗞️ Top 5 Headlines Analyzed:", "magenta"))
    for i, art in enumerate(sentiment_result["details"][:5], 1):
        color = (
            "green" if art["label"].lower() == "positive"
            else "red" if art["label"].lower() == "negative"
            else "yellow"
        )
        print(colored(f"{i}. [{art['label']}] {art['title']} ({art['source']})", color))

    # Investment reasoning
    print(colored("\n💡 Investment Insight & Market Factors", "blue"))
    if overall == "positive":
        print("✅ Majority of articles indicate optimism — positive business or market trends.")
        print("📊 Favorable indicators: strong earnings, expansion plans, investor confidence.")
        print("💰 Suggestion: Short-term bullish — good for accumulation or entry on dips.")
    elif overall == "negative":
        print("⚠️ News flow is bearish — mentions of losses, legal, or market concerns.")
        print("📉 Unfavorable indicators: declining profit margins, weak market performance.")
        print("🚫 Suggestion: Avoid new entries until sentiment improves.")
    else:
        print("🤔 Mixed signals detected — balance of positive and negative news.")
        print("📊 Indicators: market uncertainty or neutral earnings outlook.")
        print("🕓 Suggestion: Wait for clearer momentum or upcoming earnings release.")

    # Timestamp
    print(colored(f"\n📅 Report Generated On: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", "cyan"))


# ===============================
# 💬 Chatbot Interface
# ===============================
def chatbot():
    print(colored("🤖 Welcome to SmartStock Sentiment Analyzer!", "cyan"))
    print("Type a company name (e.g., Reliance, TCS, Infosys) or 'exit' to quit.\n")

    while True:
        user_input = input(colored("You: ", "yellow")).strip().lower()
        if user_input in ["exit", "quit", "bye"]:
            print(colored("👋 Goodbye! Stay informed and invest wisely!", "cyan"))
            break
        elif len(user_input) < 2:
            print("⚠️ Please enter a valid company name.")
            continue
        else:
            generate_report(user_input)


if __name__ == "__main__":
    chatbot()
