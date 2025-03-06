import requests
from bs4 import BeautifulSoup
import os

def scrape_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Example scraping logic (this will vary based on the website structure)
        title = soup.find('h1').get_text()
        content = soup.find('div', class_='content').get_text()
        image_url = soup.find('img')['src']

        return {
            'title': title,
            'content': content,
            'image_url': image_url
        }
    except requests.exceptions.RequestException as e:
        print(f"Error scraping data: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_google_maps_api_key():
    return os.environ.get('GOOGLE_MAPS_API_KEY')

def fetch_nearby_liver_specialists(location):
    api_key = get_google_maps_api_key()
    if not api_key:
        print("Google Maps API key not set.")
        return None

    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=10000&type=hospital&keyword=liver%20specialist&key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['results']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching nearby specialists: {e}")
        return None

def fetch_medical_news(source='WHO'):
    if source == 'WHO':
        url = "https://www.who.int/rss-feeds/news-english.xml"
    elif source == 'CDC':
        url = "https://tools.cdc.gov/podcasts/rss.xml?s=10537"
    else:
        print("Invalid news source.")
        return None

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')  # Use 'lxml' parser
        news_items = []
        for item in soup.find_all('item'):
            title = item.find('title').text
            description = item.find('description').text
            link = item.find('link').text
            news_items.append({'title': title, 'description': description, 'link': link})
        return news_items
    except requests.exceptions.RequestException as e:
        print(f"Error fetching medical news: {e}")
        return None
