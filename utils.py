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

def fetch_medical_news():
    sources = [
         "https://liverdiseasenews.com/",
        "https://www.sciencedaily.com/news/health_medicine/liver_disease/",
        "https://www.medscape.com/viewarticle/glp-1-ras-cut-cardiovascular-risk-metabolic-liver-disease-2025a10005jk?form=fpf",
        "https://www.news-medical.net/news/20250306/Asah1-gene-plays-key-role-in-preventing-progression-of-nonalcoholic-fatty-liver-disease.aspx",
        "https://bmcgastroenterol.biomedcentral.com/articles/10.1186/s12876-025-03719-z",
        "https://www.news-medical.net/news/20250305/New-drug-candidate-may-help-combat-metabolic-dysfunction-associated-steatotic-liver-disease.aspx",
        "https://my.clevelandclinic.org/health/diseases/17179-liver-disease"
        # Add more reputable sources here
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    news_items = []
    for url in sources:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')  # Use 'lxml' parser
            for item in soup.find_all('item'):
                title = item.find('title').text
                description = item.find('description').text
                link = item.find('link').text
                news_items.append({'title': title, 'description': description, 'link': link})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching medical news from {url}: {e}")
    
    return news_items
