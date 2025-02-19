# import requests
# from bs4 import BeautifulSoup

# url = "https://www.the-numbers.com/movie/budgets"
# response = requests.get(url)
# soup = BeautifulSoup(response.text, 'html.parser')


# # Find the table containing the data
# table = soup.find('table')

# # Iterate over table rows
# for row in table.find_all('tr')[1:]:  # Skipping the header row
#     cells = row.find_all('td')
#     if len(cells) > 5:
#         release_date = cells[0].get_text(strip=True)
#         movie_title = cells[1].get_text(strip=True)
#         production_budget = cells[2].get_text(strip=True)
#         domestic_gross = cells[3].get_text(strip=True)
#         worldwide_gross = cells[4].get_text(strip=True)
        
#         print(f"Title: {movie_title}, Budget: {production_budget}, Domestic Gross: {domestic_gross}, Worldwide Gross: {worldwide_gross}")


# base_url = "https://www.the-numbers.com/movie/budgets/{}"
# for page in range(1, total_pages + 1):  # Replace total_pages with the actual number
#     url = base_url.format(page)
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
#     # Repeat the data extraction process

import requests
from bs4 import BeautifulSoup
import re
import unicodedata
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Import your model (adjust the import based on your project structure)
from database.db_tables import TMDBMovieBase  # Replace with the actual module name


def slugify(title: str) -> str:
    """
    Convert a movie title into a slug suitable for a URL.
    
    This function:
      - Normalizes Unicode characters to ASCII.
      - Removes punctuation.
      - Replaces whitespace with hyphens.
    """
    # Normalize and convert to ASCII
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    # Remove characters that aren't alphanumeric, whitespace, or hyphen
    title = re.sub(r'[^\w\s-]', '', title)
    # Replace any group of whitespace with a single hyphen
    title = re.sub(r'\s+', '-', title)
    return title


def extract_financial_data(soup: BeautifulSoup) -> dict:
    """
    Given a BeautifulSoup object for a movie page on The Numbers,
    search for a table containing financial data (like production budget,
    domestic and worldwide grosses) and return the data in a dictionary.
    
    The extraction logic here is an example—it looks for a table that 
    contains the text "Production Budget" and then maps each label/value pair.
    Adjust the selectors as needed.
    """
    tables = soup.find_all('table')
    for table in tables:
        # Check if this table contains our expected label
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


def scrape_the_numbers(movie_title: str, release_year: int = None) -> (dict, str):
    """
    Attempt to scrape financial data for a movie from The Numbers website.
    
    Given a movie title (and optionally a release year), build candidate URLs:
      - One with the year included (if provided)
      - One without the year
    The function returns a tuple (data, url) if successful or (None, None) if not.
    """
    slug = slugify(movie_title)
    candidate_urls = []
    if release_year:
        candidate_urls.append(f"https://www.the-numbers.com/movie/{slug}-({release_year})")
    candidate_urls.append(f"https://www.the-numbers.com/movie/{slug}")

    for url in candidate_urls:
        print(f"Trying URL: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            data = extract_financial_data(soup)
            if data:
                return data, url
            else:
                print(f"Page found at {url} but no financial data was detected.")
        else:
            print(f"Failed to retrieve {url} (Status code: {response.status_code})")
    return None, None


def main():
    # Replace with your actual database URL/connection string
    engine = create_engine('sqlite:///your_database.db')
    
    with Session(engine) as session:
        movies = session.query(TMDBMovieBase).all()
        for movie in movies:
            # Extract release year if available
            release_year = movie.release_date.year if movie.release_date else None
            print(f"\nScraping data for: {movie.title} ({release_year})")
            
            data, url = scrape_the_numbers(movie.title, release_year)
            if data:
                print(f"Data for '{movie.title}' found at {url}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                # Here you might decide to update your database model
                # with the scraped data if you wish.
            else:
                print(f"No data could be scraped for '{movie.title}'.")


if __name__ == '__main__':
    main()

