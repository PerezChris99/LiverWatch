import requests
import os
from models import Post

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
    # Retrieve news articles from the database (Post model)
    news_items = []
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    for i, post in enumerate(posts):
        news_items.append({
            'id': i,
            'title': post.title,
            'description': post.content[:200] + '...' if post.content else 'Click to read more about this liver health article.',
            'link': post.source_url,
            'source': post.source_url.split('/')[2] if post.source_url else 'Unknown'
        })
    return news_items
