import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def fetch_page(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch a webpage using Playwright (headless Chromium) and return a parsed BeautifulSoup object.
    Bypasses JavaScript-only blockers and Cloudflare basic challenges.
    """
    if not url.startswith('http'):
        url = 'https://' + url

    try:
        with sync_playwright() as p:
            # Launch Chromium in headless mode
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            
            # Go to the URL and wait until the DOM is fully loaded
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # Wait a tiny bit extra for dynamic content to populate
            page.wait_for_timeout(2000)
            
            html_content = page.content()
            browser.close()
            
            # Parse with BeautifulSoup
            return BeautifulSoup(html_content, 'lxml')
            
    except PlaywrightTimeoutError:
        print(f"Error fetching {url}: Page load timed out after 20 seconds.")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def find_contact_page(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """
    Look for a contact or about page link in the HTML.
    Returns the absolute URL if found.
    """
    if not soup:
        return None
        
    # Common keywords in contact page URLs or link text
    keywords = ['contact', 'about', 'reach-us', 'get-in-touch']
    
    # Check all links
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].lower()
        text = a_tag.get_text(strip=True).lower()
        
        # Check if href or link text contains contact keywords
        if any(keyword in href for keyword in keywords) or \
           any(keyword in text for keyword in keywords):
            
            # Construct absolute URL
            return urljoin(base_url, a_tag['href'])
            
    return None

if __name__ == "__main__":
    # Test block
    test_url = "https://www.google.com"
    print(f"Testing fetch_page for {test_url}...")
    soup = fetch_page(test_url)
    
    if soup:
        print(f"Successfully fetched! Page title: {soup.title.string if soup.title else 'No Title'}")
        
        print(f"Looking for contact page...")
        contact_url = find_contact_page(soup, test_url)
        print(f"Contact page found: {contact_url}")
    else:
        print("Failed to fetch page.")
