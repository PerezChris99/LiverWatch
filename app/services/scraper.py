"""
Web Scraper Service
===================

Scrapes medical news and articles about liver health.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


def scrape_medical_news() -> List[Dict[str, str]]:
    """
    Scrapes medical news related to liver health from reliable sources.
    
    Returns:
        List of article dictionaries with title, summary, link, and image_url
    """
    articles = []
    
    # Try multiple sources for redundancy
    sources = [
        scrape_medical_news_today,
        scrape_healthline_liver,
        scrape_webmd_liver
    ]
    
    for source_func in sources:
        try:
            source_articles = source_func()
            articles.extend(source_articles)
        except Exception as e:
            print(f"Error scraping from source: {e}")
            continue
    
    # Remove duplicates based on title
    seen_titles = set()
    unique_articles = []
    for article in articles:
        if article.get('title') and article['title'] not in seen_titles:
            seen_titles.add(article['title'])
            unique_articles.append(article)
    
    return unique_articles[:20]  # Limit to 20 articles


def scrape_medical_news_today() -> List[Dict[str, str]]:
    """Scrape from Medical News Today"""
    URL = "https://www.medicalnewstoday.com/categories/liver_disease"
    articles = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find article cards
        for item in soup.select('li.css-kbq0t'):
            title_elem = item.select_one('h2 a') or item.select_one('h3 a')
            link_elem = item.select_one('a')
            summary_elem = item.select_one('p')
            image_elem = item.select_one('img')
            
            if title_elem:
                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '') if link_elem else ''
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                image_url = image_elem.get('src') if image_elem else None
                
                if not link.startswith('http'):
                    link = f"https://www.medicalnewstoday.com{link}"
                
                articles.append({
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'image_url': image_url,
                    'source': 'Medical News Today'
                })
    except Exception as e:
        print(f"Error scraping Medical News Today: {e}")
    
    return articles


def scrape_healthline_liver() -> List[Dict[str, str]]:
    """Scrape from Healthline"""
    URL = "https://www.healthline.com/health/liver-diseases"
    articles = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        for item in soup.select('article'):
            title_elem = item.select_one('h2') or item.select_one('h3')
            link_elem = item.select_one('a')
            image_elem = item.select_one('img')
            
            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')
                image_url = image_elem.get('src') if image_elem else None
                
                if not link.startswith('http'):
                    link = f"https://www.healthline.com{link}"
                
                articles.append({
                    'title': title,
                    'summary': '',
                    'link': link,
                    'image_url': image_url,
                    'source': 'Healthline'
                })
    except Exception as e:
        print(f"Error scraping Healthline: {e}")
    
    return articles


def scrape_webmd_liver() -> List[Dict[str, str]]:
    """Scrape from WebMD"""
    URL = "https://www.webmd.com/digestive-disorders/liver-diseases"
    articles = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        for item in soup.select('.article-card'):
            title_elem = item.select_one('h3') or item.select_one('h4')
            link_elem = item.select_one('a')
            
            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')
                
                if not link.startswith('http'):
                    link = f"https://www.webmd.com{link}"
                
                articles.append({
                    'title': title,
                    'summary': '',
                    'link': link,
                    'image_url': None,
                    'source': 'WebMD'
                })
    except Exception as e:
        print(f"Error scraping WebMD: {e}")
    
    return articles


def scrape_single_article(url: str) -> Optional[Dict[str, str]]:
    """
    Scrapes a single article from a given URL.
    
    Args:
        url: The URL of the article to scrape
        
    Returns:
        Dictionary with title, content, and image_url, or None if scraping fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Try to find title
        title = None
        for selector in ['h1', 'article h1', '.article-title', '.post-title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        # Try to find content
        content = None
        for selector in ['article', '.article-body', '.post-content', '.entry-content', 'main']:
            elem = soup.select_one(selector)
            if elem:
                # Remove scripts and styles
                for script in elem.select('script, style, nav, footer, header'):
                    script.decompose()
                content = elem.get_text(separator='\n', strip=True)
                break
        
        # Try to find main image
        image_url = None
        for selector in ['article img', '.article-image img', 'main img', '.featured-image img']:
            elem = soup.select_one(selector)
            if elem and elem.get('src'):
                image_url = elem.get('src')
                if not image_url.startswith('http'):
                    # Make relative URL absolute
                    from urllib.parse import urljoin
                    image_url = urljoin(url, image_url)
                break
        
        if not title:
            title = "Untitled Article"
        
        if not content:
            # Fallback: get all paragraph text
            paragraphs = soup.find_all('p')
            content = '\n'.join(p.get_text(strip=True) for p in paragraphs[:10])
        
        return {
            'title': title,
            'content': content[:5000] if content else '',  # Limit content length
            'image_url': image_url
        }
        
    except Exception as e:
        print(f"Error scraping article from {url}: {e}")
        return None


def run_scheduled_scraper(app):
    """Run the scraper as a scheduled task"""
    with app.app_context():
        from app.models import Post
        from app import db
        
        articles = scrape_medical_news()
        new_count = 0
        
        for article_data in articles:
            try:
                # Check if article already exists
                existing = Post.query.filter_by(source_url=article_data.get('link')).first()
                
                if not existing and article_data.get('link'):
                    post = Post(
                        title=article_data.get('title', 'Untitled'),
                        content=article_data.get('summary', ''),
                        source_url=article_data.get('link'),
                        image_url=article_data.get('image_url')
                    )
                    db.session.add(post)
                    new_count += 1
            except Exception as e:
                print(f"Error saving article: {e}")
                continue
        
        if new_count > 0:
            db.session.commit()
            print(f"Scraper: Added {new_count} new articles")
