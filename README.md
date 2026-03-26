# Smart Company Info Scraper

A Python-based web scraper that takes a company name, uses SerpApi to find its official website, and then crawls that website to extract the contact email and physical location.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your SerpApi key to the `.env` file

## Usage

Run the scraper with a company name:

```bash
python scraper.py "Company Name"
```

The script will:
1. Find the official website using SerpApi
2. Crawl the website to find contact information
3. Extract email and location
4. Save the results to `results.json`
