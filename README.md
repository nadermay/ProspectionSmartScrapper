# Prospection Smart Scraper CLI

A powerful, concurrent Python-based lead enrichment tool that extracts contact data (Email, Phone, Location, Socials) from company websites.

## Key Features
- **Zero-Cost Discovery:** Uses Clearbit Autocomplete and DuckDuckGo for domain finding (No API keys required).
- **Playwright Crawler:** Uses headless Chromium to handle JS-heavy websites.
- **Concurrent Processing:** Multi-threaded batch scraping from CSV files.
- **Clean Output:** Generates focused lead lists with only essential columns.

## Setup

1. **Create and Activate Virtual Environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```

## Usage

### Single Company Scrape
```powershell
python scraper.py "Company Name"
```

### Batch Processing (CSV)
```powershell
python scraper.py --csv "path/to/your/leads.csv" --threads 10 --out enriched_prospects.csv
```

The CSV must contain a **'Business Name'** column. The output will include:
- Business Name
- Phone
- Email
- Location
- Website
- Socials (LinkedIn, Facebook, Twitter, Instagram)

## Output
The results are saved to `enriched_prospects.csv` by default.
