"""
Utility Functions
=================

Helper functions for LiverWatch application.
"""

import os
import requests
from typing import List, Dict, Optional


def get_google_maps_api_key() -> Optional[str]:
    """Get Google Maps API key from environment"""
    return os.environ.get('GOOGLE_MAPS_API_KEY')


def fetch_nearby_liver_specialists(location: str) -> List[Dict]:
    """
    Fetch nearby liver specialists using Google Places API.
    
    Args:
        location: Location string (e.g., "lat,lng" or "city name")
        
    Returns:
        List of specialist dictionaries
    """
    api_key = get_google_maps_api_key()
    if not api_key:
        print("Google Maps API key not configured")
        return get_sample_specialists()
    
    try:
        # If location is not coordinates, geocode it first
        if ',' not in location or not location.replace(',', '').replace('.', '').replace('-', '').isdigit():
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
            geocode_resp = requests.get(geocode_url, timeout=10)
            geocode_data = geocode_resp.json()
            
            if geocode_data.get('results'):
                loc = geocode_data['results'][0]['geometry']['location']
                location = f"{loc['lat']},{loc['lng']}"
            else:
                return get_sample_specialists()
        
        # Search for liver specialists
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': location,
            'radius': 15000,  # 15km radius
            'type': 'hospital',
            'keyword': 'liver specialist gastroenterologist hepatologist',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        specialists = []
        for place in data.get('results', [])[:10]:
            specialists.append({
                'name': place.get('name'),
                'address': place.get('vicinity'),
                'rating': place.get('rating'),
                'user_ratings_total': place.get('user_ratings_total', 0),
                'open_now': place.get('opening_hours', {}).get('open_now'),
                'place_id': place.get('place_id'),
                'lat': place['geometry']['location']['lat'],
                'lng': place['geometry']['location']['lng']
            })
        
        return specialists if specialists else get_sample_specialists()
        
    except Exception as e:
        print(f"Error fetching specialists: {e}")
        return get_sample_specialists()


def get_sample_specialists() -> List[Dict]:
    """Return sample specialist data when API is unavailable"""
    return [
        {
            'name': 'Mulago National Referral Hospital',
            'address': 'Mulago Hill, Kampala, Uganda',
            'rating': 4.2,
            'user_ratings_total': 1250,
            'open_now': True,
            'specialty': 'Gastroenterology & Hepatology',
            'lat': 0.3476,
            'lng': 32.5825
        },
        {
            'name': 'Uganda Heart Institute',
            'address': 'Mulago Complex, Kampala',
            'rating': 4.5,
            'user_ratings_total': 890,
            'open_now': True,
            'specialty': 'Internal Medicine',
            'lat': 0.3480,
            'lng': 32.5830
        },
        {
            'name': 'Nakasero Hospital',
            'address': 'Plot 14, Akii Bua Road, Kampala',
            'rating': 4.3,
            'user_ratings_total': 650,
            'open_now': True,
            'specialty': 'Gastroenterology',
            'lat': 0.3156,
            'lng': 32.5842
        },
        {
            'name': 'International Hospital Kampala',
            'address': 'Plot 4686, St. Barnabas Road, Namuwongo',
            'rating': 4.6,
            'user_ratings_total': 520,
            'open_now': True,
            'specialty': 'Hepatology',
            'lat': 0.3050,
            'lng': 32.6050
        },
        {
            'name': 'Nsambya Hospital',
            'address': 'Nsambya, Kampala',
            'rating': 4.1,
            'user_ratings_total': 780,
            'open_now': True,
            'specialty': 'Internal Medicine',
            'lat': 0.2996,
            'lng': 32.5917
        }
    ]


def fetch_medical_news() -> List[Dict]:
    """
    Fetch medical news from the database.
    
    Returns:
        List of news article dictionaries
    """
    from app.models import Post
    
    news_items = []
    posts = Post.query.filter_by(is_published=True)\
                     .order_by(Post.date_posted.desc())\
                     .limit(20)\
                     .all()
    
    for post in posts:
        news_items.append({
            'id': post.id,
            'title': post.title,
            'description': post.excerpt,
            'link': post.source_url or f'/post/{post.id}',
            'source': extract_domain(post.source_url) if post.source_url else 'LiverWatch',
            'date': post.date_posted.strftime('%Y-%m-%d'),
            'image_url': post.image_url
        })
    
    # If no posts, return fallback news
    if not news_items:
        return get_fallback_news()
    
    return news_items


def get_fallback_news() -> List[Dict]:
    """Return fallback news when database is empty"""
    return [
        {
            'id': 0,
            'title': 'Understanding Liver Disease Prevention',
            'description': 'Learn about the latest research on preventing liver disease through lifestyle changes, diet modifications, and regular health monitoring.',
            'link': 'https://www.liverfoundation.org/for-patients/about-the-liver/health-wellness/',
            'source': 'American Liver Foundation',
            'date': '',
            'image_url': None
        },
        {
            'id': 1,
            'title': 'Nutrition for Optimal Liver Health',
            'description': 'Discover the best foods and dietary patterns to maintain optimal liver function and prevent fatty liver disease.',
            'link': 'https://www.hopkinsmedicine.org/health/conditions-and-diseases/liver-health',
            'source': 'Johns Hopkins Medicine',
            'date': '',
            'image_url': None
        },
        {
            'id': 2,
            'title': 'Advances in Liver Disease Treatment',
            'description': 'Recent advances in medical treatments for various liver conditions including hepatitis, cirrhosis, and liver cancer.',
            'link': 'https://www.mayoclinic.org/diseases-conditions/liver-problems/diagnosis-treatment/drc-20374502',
            'source': 'Mayo Clinic',
            'date': '',
            'image_url': None
        },
        {
            'id': 3,
            'title': 'Biliary Atresia in Children',
            'description': 'Important information about biliary atresia, a rare liver disease affecting infants, and its treatment options.',
            'link': 'https://www.chop.edu/conditions-diseases/biliary-atresia',
            'source': "Children's Hospital of Philadelphia",
            'date': '',
            'image_url': None
        }
    ]


def extract_domain(url: str) -> str:
    """Extract domain name from URL"""
    if not url:
        return 'Unknown'
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return 'Unknown'


def format_date_relative(date) -> str:
    """Format date as relative time (e.g., '2 days ago')"""
    from datetime import datetime
    
    if not date:
        return ''
    
    now = datetime.now(date.tzinfo) if date.tzinfo else datetime.now()
    diff = now - date
    
    if diff.days == 0:
        if diff.seconds < 60:
            return 'Just now'
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        else:
            hours = diff.seconds // 3600
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif diff.days == 1:
        return 'Yesterday'
    elif diff.days < 7:
        return f'{diff.days} days ago'
    elif diff.days < 30:
        weeks = diff.days // 7
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    elif diff.days < 365:
        months = diff.days // 30
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = diff.days // 365
        return f'{years} year{"s" if years != 1 else ""} ago'


def sanitize_html(html: str) -> str:
    """Remove potentially dangerous HTML tags"""
    from bs4 import BeautifulSoup
    
    if not html:
        return ''
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style tags
    for tag in soup.find_all(['script', 'style', 'iframe', 'object', 'embed']):
        tag.decompose()
    
    # Remove dangerous attributes
    dangerous_attrs = ['onclick', 'onerror', 'onload', 'onmouseover', 'javascript:']
    for tag in soup.find_all(True):
        for attr in list(tag.attrs.keys()):
            if attr.lower() in dangerous_attrs or str(tag.attrs[attr]).lower().startswith('javascript:'):
                del tag.attrs[attr]
    
    return str(soup)
