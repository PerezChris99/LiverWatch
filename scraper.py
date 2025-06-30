
import requests
from bs4 import BeautifulSoup

def scrape_medical_news():
    """
    Scrapes medical news related to liver health from a target website.
    """
    URL = "https://www.medicalnewstoday.com/categories/liver_disease"
    
    try:
        response = requests.get(URL)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    
    articles = []
    
    # Updated selectors for medicalnewstoday.com
    for item in soup.select('div.css-183gwh4'): # This selector targets the main article container
        title_element = item.select_one('h2.css-1m6tt1a') # Title is usually an h2 within this container
        summary_element = item.select_one('div.css-1m6tt1a') # Summary is often a div
        link_element = item.select_one('a.css-1m6tt1a') # Link is usually an anchor tag
        image_element = item.select_one('img.css-1m6tt1a') # Image element
        
        if title_element and summary_element and link_element:
            title = title_element.get_text(strip=True)
            summary = summary_element.get_text(strip=True)
            link = link_element.get("href")
            image_url = image_element.get("src") if image_element else None
            
            if not link.startswith("http"):
                link = f"https://www.medicalnewstoday.com{link}"
            
            articles.append({
                "title": title,
                "summary": summary,
                "link": link,
                "image_url": image_url
            })
            
    return articles

def scrape_single_article(url):
    """
    Scrapes a single article from a given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.find('h1')
    content = soup.find('div', class_='article-body') or soup.find('article')
    image = soup.find('img', class_='article-image') or soup.find('img')

    return {
        'title': title.get_text(strip=True) if title else "No Title",
        'content': content.get_text(strip=True) if content else "No Content",
        'image_url': image.get('src') if image else None
    }
