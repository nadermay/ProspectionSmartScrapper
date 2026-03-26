import requests
from bs4 import BeautifulSoup
from typing import Optional

# Common directory websites we want to ignore in search results
SKIP_DOMAINS = [
    'linkedin.com', 'facebook.com', 'yelp.com', 'yellowpages.com', 
    'bbb.org', 'glassdoor.com', 'simplyhired.com', 'indeed.com',
    'manta.com', 'mapquest.com', 'angi.com', 'houzz.com', 'zoominfo.com'
]

def search_clearbit(company_name: str) -> Optional[str]:
    """Hits the free Clearbit autocomplete API to find the exact official company domain."""
    url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={company_name}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                domain = data[0].get('domain')
                if domain:
                    return f"https://www.{domain}"
    except Exception as e:
        print(f"[Clearbit Error] {e}")
    return None

def search_duckduckgo(company_name: str) -> Optional[str]:
    """Scrapes DuckDuckGo HTML results as a fallback if Clearbit fails to find a small business."""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://duckduckgo.com/"
    }
    data = {"q": f"{company_name} official website"}
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=15)
        soup = BeautifulSoup(response.text, 'lxml')
        
        for a in soup.find_all('a', class_='result__url'):
            link = a.get('href', '')
            if link and link.startswith('http'):
                # Ignore directories
                is_directory = any(domain in link.lower() for domain in SKIP_DOMAINS)
                if not is_directory:
                    return link
    except Exception as e:
        print(f"[DuckDuckGo Error] {e}")
        
    return None

def find_official_website(company_name: str) -> Optional[str]:
    """
    Combined discovery pipeline:
    1. Try Clearbit API (instant, 100% accurate, free)
    2. Try DuckDuckGo parsing (fallback)
    """
    print(f"[*] Discovering domain for {company_name}")
    
    domain = search_clearbit(company_name)
    if domain:
        return domain
        
    print(f"[!] Clearbit failed. Falling back to DuckDuckGo search...")
    domain = search_duckduckgo(company_name)
    if domain:
        return domain
        
    return None
