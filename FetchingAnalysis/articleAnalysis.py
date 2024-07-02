import requests
import sys
from langdetect import detect, DetectorFactory
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from transformers import pipeline, AutoTokenizer

# Ensure consistent results from langdetect
DetectorFactory.seed = 0

# Initialize sentiment analysis pipeline
sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')

# Fetch articles using GDELT
def fetch_articles_from_gdelt(query, start_date, end_date):
    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=artlist&"
        f"startdatetime={start_date}000000&enddatetime={end_date}235959&"
        f"maxrecords=250&format=json&sourcelang=english"
    )
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching articles from GDELT: {response.status_code}")
        return []

    try:
        articles = response.json().get('articles', [])
    except requests.exceptions.JSONDecodeError:
        print("Error decoding JSON response from GDELT.")
        print("Response content:", response.content)
        return []

    return articles

# Extract full text from article URL asynchronously
async def fetch_full_text(session, url):
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return ""
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            paragraphs = soup.find_all('p')
            full_text = ' '.join([para.get_text() for para in paragraphs])
            return full_text
    except Exception as e:
        print(f"Error fetching full text from {url}: {e}")
        return ""

# Print article information to the terminal
def print_article_info(article, sentiment):
    print(f"Title: {article['title']}")
    print(f"URL: {article['url']}")
    print(f"Sentiment: {sentiment}")
    print('-' * 80)

# Filter articles to ensure they are in English and contain the keyword
async def is_relevant_article(session, article, keyword):
    title = article.get('title', '').lower()
    description = article.get('description', '').lower()
    keyword = keyword.lower()

    try:
        if title and detect(title) != 'en':
            return False
        if description and detect(description) != 'en':
            return False
    except:
        return False

    # Check if keyword is in title or description
    if keyword in title or keyword in description:
        return True

    # Fetch full text and check if keyword is present
    full_text = await fetch_full_text(session, article['url'])
    if keyword in full_text.lower():
        return True

    return False

# Analyze sentiment of the article text, splitting into chunks if it exceeds max length
def analyze_sentiment(text):
    max_length = 500
    tokens = tokenizer.encode(text, truncation=False)
    chunks = [tokens[i:i + max_length] for i in range(0, len(tokens), max_length)]

    sentiments = []
    for chunk in chunks:
        chunk_text = tokenizer.decode(chunk, skip_special_tokens=True)
        result = sentiment_analyzer(chunk_text)
        sentiments.append(result[0]['label'])

    # Return 'NEGATIVE' if any chunk is negative
    return 'NEGATIVE' if 'NEGATIVE' in sentiments else 'POSITIVE'

# Main function to run the analysis
async def main(keyword, start_date, end_date):
    # Fetch articles from GDELT
    articles = fetch_articles_from_gdelt(keyword, start_date, end_date)

    print(f"Total articles fetched: {len(articles)}")  # Debug information

    if not articles:
        print("No articles to analyze.")
        return

    async with aiohttp.ClientSession() as session:
        tasks = [is_relevant_article(session, article, keyword) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        relevant_articles = [article for article, is_relevant in zip(articles, results) if is_relevant is True]

        if not relevant_articles:
            print("No relevant articles found.")
        else:
            full_text_tasks = [fetch_full_text(session, article['url']) for article in relevant_articles]
            full_texts = await asyncio.gather(*full_text_tasks, return_exceptions=True)
            for article, full_text in zip(relevant_articles, full_texts):
                if full_text:
                    sentiment = analyze_sentiment(full_text)
                    if sentiment == 'NEGATIVE':
                        print_article_info(article, sentiment)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python articleAnalysis.py <keyword> <start_date> <end_date>")
        print("Dates should be in YYYYMMDD format.")
    else:
        keyword = sys.argv[1]
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        asyncio.run(main(keyword, start_date, end_date))
