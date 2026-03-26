import os
import sys
import json
import csv
import argparse
import concurrent.futures

from discovery import find_official_website
from crawler import fetch_page, find_contact_page
from extractor import extract_emails, extract_phones, extract_socials, extract_location

def scrape_company(company_name: str) -> dict:
    """
    Orchestrates the scraping process for a single company.
    Phase A: Find website
    Phase B: Crawl homepage
    Phase C: Extract data & potentially crawl contact page
    """
    result = {
        "company_name": company_name,
        "website_link": "Not Found",
        "email": "Not Found",
        "phone": "Not Found",
        "location": "Not Found",
        "socials": {
            "LinkedIn": "Not Found",
            "Facebook": "Not Found",
            "Instagram": "Not Found",
            "Twitter": "Not Found"
        },
        "status": "Failed"
    }
        
    print(f"\n--- Scraping info for: {company_name} ---")
    
    # Phase A: Discovery
    print("[Phase A] Looking for official website...")
    website = find_official_website(company_name)
    if not website:
        print("Could not find official website.")
        return result
        
    print(f"Found website: {website}")
    result["website_link"] = website # Keep the bug fix as it's essential data
    
    # Phase B: Crawling Homepage
    print("[Phase B] Fetching homepage...")
    soup = fetch_page(website)
    if not soup:
        print("Failed to fetch homepage HTML.")
        return result
        
    emails = []
    phones = []
    location = None
    socials = {}
    contact_url = None
    
    # Phase C: Extraction on Homepage
    print("[Phase C] Extracting data from homepage...")
    emails.extend(extract_emails(soup))
    phones.extend(extract_phones(soup))
    socials = extract_socials(soup)
    location = extract_location(soup)
    
    # If missing data, try to find and crawl a contact page
    if not emails or not phones or not location:
        print("Missing some data, looking for a Contact page...")
        contact_url = find_contact_page(soup, website)
        
        if contact_url:
            print(f"Found contact page: {contact_url}. Fetching...")
            contact_soup = fetch_page(contact_url)
            if contact_soup:
                print("Extracting data from contact page...")
                if not emails:
                    emails.extend(extract_emails(contact_soup))
                if not phones:
                    phones.extend(extract_phones(contact_soup))
                
                # Check for missing socials on contact page
                contact_socials = extract_socials(contact_soup)
                for platform, link in contact_socials.items():
                    if link != "Not Found" and socials.get(platform, "Not Found") == "Not Found":
                        socials[platform] = link
                        
                if not location:
                    location = extract_location(contact_soup)
                    
    # Format results
    if emails:
        emails = list(set(emails))
        result["email"] = emails[0] if emails else "Not Found"
        
    if phones:
        phones = list(set(phones))
        result["phone"] = phones[0] if phones else "Not Found"
    
    if socials:
        result["socials"] = socials
        
    if location:
        result["location"] = location
        
    result["status"] = "Success"
    print("Scraping completed!")
    
    return result

def process_single_row(row: dict, business_col: str = 'Business Name') -> dict:
    """Worker function for threading: scrapes one company and updates its row."""
    company_name = row.get(business_col, '').strip()
    if not company_name:
        return row
        
    print(f"[*] Scraping: {company_name}...")
    scraped_data = scrape_company(company_name)
    
    # Enrich the original row
    if scraped_data.get('email') != "Not Found":
        row['Email'] = scraped_data['email']
        
    if scraped_data.get('phone') != "Not Found":
        row['Phone'] = scraped_data['phone']
        
    if scraped_data.get('location') != "Not Found":
        row['Location'] = scraped_data['location']
        
    if scraped_data.get('website_link') != "Not Found":
        row['Website'] = scraped_data['website_link']
        
    if 'socials' in scraped_data:
        socials = scraped_data['socials']
        for platform in ['LinkedIn', 'Facebook', 'Twitter', 'Instagram']:
            if socials.get(platform, "Not Found") != "Not Found":
                row[platform] = socials[platform]
                
    print(f"[+] Finished: {company_name}")
    return row

def process_csv(input_csv: str, output_csv: str, max_workers: int = 5):
    """
    Reads a CSV file, extracts the 'Business Name', scrapes the data,
    and writes an enriched row to the output CSV.
    """
    if not os.path.exists(input_csv):
        print(f"Error: Could not find CSV file at {input_csv}")
        return
        
    # Read the original CSV
    with open(input_csv, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        rows = list(reader)
        
    # Define the specific columns to keep in the final output
    final_fieldnames = [
        'Business Name', 'Phone', 'Email', 'Location', 'Website', 
        'LinkedIn', 'Facebook', 'Twitter', 'Instagram'
    ]
    
    print(f"Found {len(rows)} companies to process in {input_csv}.")
    print(f"Starting concurrent scraping with {max_workers} threads...\n")
    
    # Pre-populate dictionary to preserve original order and data if interrupted
    enriched_rows = {i: row.copy() for i, row in enumerate(rows)}
    
    try:
        # Use ThreadPoolExecutor for concurrent scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_idx = {executor.submit(process_single_row, row): i for i, row in enumerate(rows)}
            
            # Process as they complete
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    enriched_row = future.result()
                    enriched_rows[idx] = enriched_row
                except Exception as e:
                    print(f"[!] Error processing row {idx}: {e}")
                
                # Write incrementally so we don't lose data on crash
                with open(output_csv, mode='w', encoding='utf-8', newline='') as outfile:
                    # Filter only the fields we want to keep
                    writer = csv.DictWriter(outfile, fieldnames=final_fieldnames, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows([enriched_rows[i] for i in range(len(rows))])
                    
    except KeyboardInterrupt:
        print("\n\n[!] Scraping interrupted by user (Ctrl+C). Saving current progress safely...")
        with open(output_csv, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=final_fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows([enriched_rows[i] for i in range(len(rows))])
        print(f"--- Partial progress saved to {output_csv}. Exiting... ---")
        sys.exit(1)
            
    print(f"\n--- Batch processing complete! Results saved to {output_csv} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Company Info Scraper")
    parser.add_argument("company", nargs='?', help="The name of the company to scrape")
    parser.add_argument("--csv", help="Path to input CSV file for batch processing", dest="input_csv")
    parser.add_argument("--out", help="Path to output CSV file", default="enriched_prospects.csv", dest="output_csv")
    parser.add_argument("--threads", help="Number of concurrent threads (default: 5)", type=int, default=5, dest="threads")
    args = parser.parse_args()
    
    if args.input_csv:
        process_csv(args.input_csv, args.output_csv, max_workers=args.threads)
    elif args.company:
        final_result = scrape_company(args.company)
        
        # Output to console
        print("\n--- Final Result ---")
        print(json.dumps(final_result, indent=2))
        
        # Save to file
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=2)
        print("\nResult saved to results.json")
    else:
        parser.print_help()
