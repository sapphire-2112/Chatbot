import requests
import json

# 🔑 Replace with your NewsAPI key
API_KEY = "642687b49ace4572aa5dfd74ccf7b8b7"

# Ask user for company or keyword
query = input("Enter company or keyword (e.g., Reliance, HDFC, TCS): ").strip()

# 🧠 NewsAPI endpoint
url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&apiKey={API_KEY}"

try:
    response = requests.get(url)
    response.raise_for_status()  # Raise error if bad status code

    data = response.json()

    # 🧾 Print formatted JSON
    print(json.dumps(data, indent=4))

except requests.exceptions.RequestException as e:
    print("⚠️ Network or API error:", e)
except json.JSONDecodeError:
    print("⚠️ Failed to decode JSON response.")
