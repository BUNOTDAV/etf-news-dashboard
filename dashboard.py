
import streamlit as st
import yfinance as yf
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from datetime import datetime, timedelta

# Configuration
st.set_page_config(page_title="News-Based ETF Predictor", layout="wide")
st.title("📈 Dashboard Prédictif - Actualités & ETF (SPY, QQQ)")

# Sélection ETF
selected_etf = st.selectbox("Choisir un ETF à analyser :", ["SPY", "QQQ"])

# Téléchargement données boursières
@st.cache_data(ttl=3600)
def load_market_data(ticker):
    df = yf.download(ticker, period="7d", interval="1d")
    df.reset_index(inplace=True)
    return df

# Chargement actualités via Google News RSS
@st.cache_data(ttl=1800)
def load_news(query):
    url = f"https://news.google.com/rss/search?q={query}+stock&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    news = []
    cutoff = datetime.now() - timedelta(days=3)
    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6])
        if published >= cutoff:
            news.append({
                'title': entry.title,
                'link': entry.link,
                'published': published
            })
    return pd.DataFrame(news)

# Analyse de sentiment
def analyze_sentiment(df):
    analyzer = SentimentIntensityAnalyzer()
    df['sentiment'] = df['title'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    df['sentiment_label'] = df['sentiment'].apply(lambda s: '🟢 Achat' if s > 0.2 else ('🔴 Vente' if s < -0.2 else '⚪ Neutre'))
    return df

# Chargement données
market_df = load_market_data(selected_etf)
news_df = load_news(selected_etf)

# Analyse sentiment
if not news_df.empty:
    news_df = analyze_sentiment(news_df)

    st.subheader("📰 Dernières actualités")
    for _, row in news_df.iterrows():
        st.markdown(f"- [{row['title']}]({row['link']}) — *{row['published'].strftime('%Y-%m-%d %H:%M')}* — {row['sentiment_label']}")
else:
    st.warning("Aucune actualité récente trouvée.")

# Données de marché
st.subheader(f"📊 Données de marché - {selected_etf}")
st.dataframe(market_df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(5))

# Recommandation globale du jour
if not news_df.empty:
    mean_sentiment = news_df['sentiment'].mean()
    if mean_sentiment > 0.2:
        st.success("✅ Recommandation du jour : Achat")
    elif mean_sentiment < -0.2:
        st.error("🚫 Recommandation du jour : Vente")
    else:
        st.info("📌 Recommandation du jour : Neutre")
else:
    st.info("📌 Recommandation indisponible (pas assez d'actualités)")
