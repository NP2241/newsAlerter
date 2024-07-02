import requests
import sys
from langdetect import detect, DetectorFactory
from bs4 import BeautifulSoup
import aiohttp
import asyncio

# Ensure consistent results from langdetect
DetectorFactory.seed = 0

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
def print_article_info(article):
    print(f"Title: {article['title']}")
    print(f"URL: {article['url']}")
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
        for article in relevant_articles:
            print_article_info(article)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python articleAnalysis.py <keyword> <start_date> <end_date>")
        print("Dates should be in YYYYMMDD format.")
    else:
        keyword = sys.argv[1]
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        asyncio.run(main(keyword, start_date, end_date))
