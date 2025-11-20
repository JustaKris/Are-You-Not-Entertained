import requests
import certifi
from bs4 import BeautifulSoup
import re
import unicodedata
import json

def slugify(title: str) -> str:
    """
    Convert a movie title into a slug suitable for a URL.
    - Normalizes Unicode to ASCII.
    - Removes punctuation.
    - Replaces whitespace with hyphens.
    """
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'\s+', '-', title)
    return title

def extract_financial_data(soup: BeautifulSoup) -> dict:
    """
    Extract financial data from a The Numbers movie page.
    This example function looks for a table that contains "Production Budget" 
    and extracts key/value pairs from that table.
    Adjust the logic if the page structure is different.
    """
    tables = soup.find_all('table')
    for table in tables:
        if "Production Budget" in table.get_text():
            data = {}
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) == 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    data[label] = value
            return data
    return {}

def scrape_the_numbers(movie_title: str, release_year: int | None = None) -> tuple[dict, str]:
    """
    Try scraping financial data for a movie from The Numbers.
    It builds candidate URLs using a slugified movie title and an optional release year.
    
    Returns:
      - data: A dictionary of financial information if found, else an empty dict.
      - url: The URL where data was found.
    """
    slug = slugify(movie_title)
    candidate_urls = []
    
    if release_year:
        candidate_urls.append(f"https://www.the-numbers.com/movie/{slug}-({release_year})")
    candidate_urls.append(f"https://www.the-numbers.com/movie/{slug}#tab=summary")
    
    for url in candidate_urls:
        print(f"Trying URL: {url}")
        response = requests.get(url, verify=certifi.where())
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            data = extract_financial_data(soup)
            if data:
                return data, url
            else:
                print(f"Page found at {url} but no financial data detected.")
        else:
            print(f"Failed to retrieve {url} (Status code: {response.status_code})")
    return {}, ""

def main():
    # Get movie title (and optional release year) from user input.
    # movie_title = input("Enter movie title: ").strip()
    movie_title = "Avengers: Infinity War"
    # year_input = input("Enter release year (optional): ").strip()
    year_input = ""
    release_year = int(year_input) if year_input.isdigit() else None
    
    data, url = scrape_the_numbers(movie_title, release_year)
    if data:
        print("\nFinancial data found:")
        print(json.dumps(data, indent=4))
        
        # Save the data to a file using the slugified title as filename.
        filename = f"{slugify(movie_title)}_data.json"
        with open(filename, "w") as f:
            json.dump({"source_url": url, "financial_data": data}, f, indent=4)
        print(f"\nData saved to {filename}")
    else:
        print(f"\nNo data could be scraped for '{movie_title}'.")

if __name__ == '__main__':
    main()
