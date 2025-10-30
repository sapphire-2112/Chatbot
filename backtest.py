# stock_sentiment_model.py
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings("ignore")

# ---------- CONFIGURATION ----------
NEWS_API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"   # e.g., from newsapi.org
# You will need to register and get a key.

# Map common symbols to NSE tickers
SYMBOL_MAP = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFC": "HDFCBANK.NS",
    "HDFCBANK": "HDFCBANK.NS",
    # add more as needed
}

# ---------- FUNCTIONS ----------
def get_stock_data(symbol, months=6):
    ticker = SYMBOL_MAP.get(symbol.upper(), symbol.upper() + ".NS")
    end = datetime.now()
    start = end - timedelta(days=30 * months)
    data = yf.download(ticker, start=start, end=end, progress=False)
    if data.empty:
        print(f"⚠️ No market data for {symbol} ({ticker})")
        return None
    return data

def get_news_sentiment(symbol, days=7):
    """Fetch news headlines for the symbol in last `days`, compute average sentiment."""
    query = symbol.upper()
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = (f"https://newsapi.org/v2/everything?"
           f"q={query}&from={from_date}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}")
    try:
        resp = requests.get(url)
        items = resp.json().get("articles", [])
    except Exception as e:
        print("❌ News API error:", e)
        items = []
    if not items:
        return 0.0  # neutral sentiment if none found
    sid = SentimentIntensityAnalyzer()
    scores = []
    for art in items:
        text = art.get("title", "") + " " + art.get("description", "")
        vs = sid.polarity_scores(text)
        scores.append(vs["compound"])
    return np.mean(scores)

def build_features(data, sentiment_score):
    df = data.copy()
    df["Return1"] = df["Close"].pct_change()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA10"] = df["Close"].rolling(10).mean()
    df["Vol5"] = df["Close"].pct_change().rolling(5).std()
    df["Sentiment"] = sentiment_score
    df = df.dropna().reset_index(drop=True)
    return df

def prepare_target(df):
    df["TargetReturn"] = df["Close"].shift(-1) / df["Close"] - 1.0
    df = df.dropna().reset_index(drop=True)
    return df

def train_and_predict(symbol):
    print(f"\n🔍 Processing symbol: {symbol}")
    data = get_stock_data(symbol, months=6)
    if data is None:
        return
    sentiment = get_news_sentiment(symbol, days=7)
    print(f"• News sentiment (last 7 days): {sentiment:.3f}")
    df = build_features(data, sentiment)
    df = prepare_target(df)
    features = ["Return1", "MA5", "MA10", "Vol5", "Sentiment"]
    X = df[features]
    y = df["TargetReturn"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"• Model MAE: {mae:.4f} (in return units)")
    # Predict next day
    last_features = X.iloc[-1].values.reshape(1, -1)
    pred_return = model.predict(last_features)[0]
    last_close = float(data["Close"].iloc[-1])
    pred_price = last_close * (1 + pred_return)
    direction = "UP 📈" if pred_return > 0 else "DOWN 📉"
    print(f"📊 Prediction Summary for {symbol}:")
    print(f"• Last Close: ₹{last_close:.2f}")
    print(f"• Predicted Return: {pred_return*100:.2f}% → Predicted Price: ₹{pred_price:.2f}")
    print(f"• Direction: {direction}")
    return {
        "symbol": symbol,
        "last_close": last_close,
        "pred_price": pred_price,
        "pred_return": pred_return,
        "sentiment": sentiment
    }

# ---------- MAIN ----------
if __name__ == "__main__":
    import nltk
    nltk.download('vader_lexicon')
    symbol = input("Enter NSE symbol (TCS, RELIANCE, etc): ").strip().upper()
    train_and_predict(symbol)
