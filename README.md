# Web Scraper for Product Data

A Python-based web scraper that automatically logs into a website, navigates to product pages, and extracts product information including names, prices, packaging details, and barcodes. The scraper includes features for handling pagination, rate limiting, and translating product information from French to English.

## Features

- Automatic login detection and handling
- Product listing page identification using LLM
- Multi-page product scraping with pagination support
- Barcode extraction from product detail pages
- French to English translation of product information
- Rate limiting and request delays to prevent server overload
- CSV export of scraped data

## Requirements

- Required packages listed in `requirements.txt`
- Python version I used - Python 3.12.8

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Web-Scrapper-Dirac.git
cd Web-Scrapper-Dirac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your credentials:
```
EMAIL=your_email@example.com
PASSWORD=your_password
OPENAI_API_KEY=your_openai_api_key
```

## Usage

Run the scraper:
```bash
python web_scrapper.py
```

The script will:
1. Log in to the website
2. Find and navigate to product pages
3. Scrape product information
4. Translate French content to English
5. Save results to `product_data.csv`

## Project Structure

- `web_scrapper.py`: Main scraping script
- `french_to_english.py`: Translation from the website being in French to English
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not included in repo)

## My Thoughts

1) I enjoyed the project, it was very fun hacking around all the different things in the webiste like finding the login page, sending the post request to login, finding which tags had the correct information like barcodes etc - brought out my inner nerd which was awesome.
2) I tried to keep the code as general as possible to work with other websites. I understand that for the hardcoded things usch as the tags and regex patterns used that this won't be able to extrapolate to other websites very well if at all. My thoughts for how to address this would be using a large context window LLM like the new Gemini model to be able to analyse full pages and return the answers in json structured format as we did.
3) The reason for more hardcoding in t his project is the goal was to scrape this website and also I did not want to absolutely kill my credit card with API calls. Hence why I only have a small demo of the translation feature in the english csv to show this is possible for the translation.
4) Overall fun project! :)

