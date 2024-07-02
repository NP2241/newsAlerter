import requests
from dotenv import load_dotenv
import os
import sys
from langdetect import detect, DetectorFactory

# Ensure consistent results from langdetect
DetectorFactory.seed = 0

# Load environment variables from .env file located one directory above
load_dotenv('../keys.env')

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

# Print article information to the terminal
def print_article_info(article):
    print(f"Title: {article['title']}")
    print(f"URL: {article['url']}")
    print('-' * 80)

# Filter articles to ensure they are in English and contain the exact keyword phrase
def is_relevant_article(article, keyword):
    title = article.get('title', '').lower()
    description = article.get('description', '').lower()
    keyword = keyword.lower()

    try:
        if detect(title) != 'en':
            return False
        if description and detect(description) != 'en':
            return False
    except:
        return False

    if keyword in title or keyword in description:
        return True

    return False

# Main function to run the analysis
def main(keyword, start_date, end_date):
    # Fetch articles from GDELT
    articles = fetch_articles_from_gdelt(keyword, start_date, end_date)

    if not articles:
        print("No articles to analyze.")
        return

    # Filter and print all articles that meet the conditions
    for article in articles:
        if is_relevant_article(article, keyword):
            print_article_info(article)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python articleAnalysis.py <keyword> <start_date> <end_date>")
        print("Dates should be in YYYYMMDD format.")
    else:
        keyword = sys.argv[1]
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        main(keyword, start_date, end_date)
