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

- Python 3.8+
- Required packages listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Web-Srapper-Dirac.git
cd Web-Srapper-Dirac
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

## License

MIT License 
