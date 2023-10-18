from bs4 import BeautifulSoup
import requests
import re

# Function to scrape all URLs from Learning Center Page
def get_article_urls(vdb):
    # Get request
    r = requests.get('https://www.alpinehomeair.com/learning-center/')
    # Soup object
    soup = BeautifulSoup(r.content, 'lxml')

    # Pattern to match the articles URLs
    pattern = re.compile(r'https://www.alpinehomeair.com/viewproduct.cfm?productID=\d+')

    # Get only the href attribute value if it matches the pattern
    urls = [link.get('href') for link in soup.find_all('a') if pattern.match(str(link.get('href')))]
    return urls

# Function to scrape content from single article
def get_article_content(url):
    # Send Request
    r = requests.get(url)
    # Soup object
    soup = BeautifulSoup(r.content, 'lxml')

    # Find the article based on its HTML tag and class
    article = soup.find('div', class_='blogText')

    # Extract the text from the article
    if article:
        return article.text
    else:
        return None