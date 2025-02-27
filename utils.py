import requests
from bs4 import BeautifulSoup

def scrape_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title, content, and image URL based on the website structure
        title = soup.find('h1').text if soup.find('h1') else "Title Not Found"
        content = ""
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            content += p.text + "\n"
        image_url = soup.find('img')['src'] if soup.find('img') else None

        return {
            'title': title,
            'content': content,
            'image_url': image_url
        }
    except requests.exceptions.RequestException as e:
        print(f"Error during scraping: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
