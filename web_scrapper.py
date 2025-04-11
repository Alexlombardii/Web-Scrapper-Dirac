import requests
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
import os
from openai import OpenAI 
import re
import time
import random
import csv
from french_to_english import translate_products_to_english

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=openai_api_key)

def find_login_links(url: str):
    """Find potential login links on the main page"""
    try:
        response = requests.get(url) 
        soup = BeautifulSoup(response.text, 'html.parser') 
        
        # Look for common login link patterns
        login_keywords = ['login', 'sign in', 'account', 'my account']
        potential_links = []
        
        for link in soup.find_all('a'): # link - <a href="https://pali.plus/login">Login</a>
            href = link.get('href', '').lower() # href - https://pali.plus/login
            text = link.get_text().lower() # text - Login  
            
            if any(keyword in href or keyword in text for keyword in login_keywords):
                potential_links.append({
                    'text': link.get_text().strip(),
                    'href': link.get('href')
                })
        
        logging.info("Found potential login links:")
        for link in potential_links:
            if not link['href'].startswith('http'):
                link['href'] = 'https:' + link['href']
            logging.info(f"Text: {link['text']}, URL: {link['href']}")
            
        return potential_links
        
    except Exception as e:
        logging.error(f"Error finding login links: {str(e)}")
        return []

def analyze_forms(soup):
    """
    Find all forms and their fields:
        
    e.g.
    form - <form action="https://pali.plus/connexion" method="post">
    input - <input type="email" name="email" id="email" value="" placeholder="Email" class="form-control">
    """
    forms_data = []
    for form in soup.find_all('form'):
        form_data = {
            'action': form.get('action'), 
            'method': form.get('method', 'GET'), 
            'inputs': [] 
        }
        
        # Get all input fields
        for input_field in form.find_all('input'): # input_field - <input type="email" name="email" id="email" value="" placeholder="Email" class="form-control">
            form_data['inputs'].append({
                'name': input_field.get('name'),
                'type': input_field.get('type'),
                'value': input_field.get('value', '')
            })
        
        forms_data.append(form_data) # form_data - {'action': 'https://pali.plus/connexion', 'method': 'POST', 'inputs': [{'name': 'email', 'type': 'email', 'value': ''}, {'name': 'password', 'type': 'password', 'value': ''}]}
    
    return forms_data

def find_login_form(forms_data):
    """Find the form that looks like a login form
    
    e.g.
    form - <form action="https://pali.plus/connexion" method="post">
    input - <input type="email" name="email" id="email" value="" placeholder="Email" class="form-control">
    """
    for form in forms_data: # form - {'action': 'https://pali.plus/connexion', 'method': 'POST', 'inputs': [{'name': 'email', 'type': 'email', 'value': ''}, {'name': 'password', 'type': 'password', 'value': ''}]}
        has_email = False
        has_password = False
        
        for input_field in form['inputs']: # input_field - {'name': 'email', 'type': 'email', 'value': ''}
            if input_field['type'] in ['email', 'text'] and 'email' in input_field['name'].lower(): 
                has_email = True
            if input_field['type'] == 'password':
                has_password = True
        
        if has_email and has_password: 
            return form
    
    return None

def attempt_login(potential_links: list[dict], email: str, password: str):
    """Attempt to login using each potential login form, return session on success."""
    session = requests.Session()
    # Add browser-like headers, strongly preferring English
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',  # Strongly prefer English - Yeah hates me and doesn't work :(
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    logging.info(f"Attempting to login with email: {email} and password: {password}")
    logging.info(f"Potential links: {potential_links}")
    """Attempt to login using each potential login form"""
    for link in potential_links: # link - {'text': 'Login', 'href': 'https://pali.plus/connexion?back=my-account'}
        logging.info(f"Attempting to login with link: {link}")
        try:
            login_url = link['href'] # login_url - https://pali.plus/connexion?back=my-account
            response = session.get(login_url)  # Use session.get instead of requests.get
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get all forms and their fields
            forms_data = analyze_forms(soup) # forms_data - [{'action': 'https://pali.plus/connexion', 'method': 'POST', 'inputs': [{'name': 'email', 'type': 'email', 'value': ''}, {'name': 'password', 'type': 'password', 'value': ''}]}]
            login_form = find_login_form(forms_data) # login_form - {'action': 'https://pali.plus/connexion', 'method': 'POST', 'inputs': [{'name': 'email', 'type': 'email', 'value': ''}, {'name': 'password', 'type': 'password', 'value': ''}]}
            
            if login_form:
                logging.info("Found login form!") 
                logging.info(f"Form action: {login_form['action']}") # Form action: https://pali.plus/connexion
                logging.info(f"Form method: {login_form['method']}") # Form method: POST
                logging.info(f"Input fields: {login_form['inputs']}") # Input fields: [{'name': 'email', 'type': 'email', 'value': ''}, {'name': 'password', 'type': 'password', 'value': ''}]
                
                # Now we can prepare the login data
                login_data = {} # login_data - {'email': 'test@test.com', 'password': 'our_password'}
                for input_field in login_form['inputs']: # input_field - {'name': 'email', 'type': 'email', 'value': ''}
                    if input_field['type'] in ['email', 'text'] and 'email' in input_field['name'].lower():
                        login_data[input_field['name']] = email # login_data - {'email': 'test@test.com'}
                    elif input_field['type'] == 'password':
                        login_data[input_field['name']] = password # login_data - {'email': 'test@test.com', 'password': 'our_password'}
                    elif input_field['type'] == 'hidden':
                        login_data[input_field['name']] = input_field['value']
                
                # Submit the form
                if login_form['method'].lower() == 'post':
                    response = session.post(login_form['action'], data=login_data)
                else:
                    response = session.get(login_form['action'], params=login_data)
                
                # Check if login was successful
                if 'logout' in response.text.lower() or 'my account' in response.text.lower():
                    logging.info("Login successful!")
                    return session  # Return the session object on success
                else:
                    # Log the form action URL correctly
                    form_action = login_form['action']
                    if form_action.startswith('//'):
                        form_action = 'https:' + form_action
                    logging.warning(f"Login submission to {form_action} seemed successful (status {response.status_code}) but couldn't confirm login.")
            
        except Exception as e:
            logging.error(f"Error attempting login at {link['href']}: {str(e)}")
    
    logging.error("Failed to login using any of the potential links")
    return None # Return None if login fails

def find_next_level_urls(session, base_url):
    """
    Find all URLs that are one level deeper than the base URL from <a> and <button> tags.
    """
    try:
        response = session.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        next_level_urls = set() # Use a set to automatically handle duplicates

        # Look for both links (a) and buttons
        for element in soup.find_all(['a', 'button']): # element - <a href="https://pali.plus/login">Login</a>
            href = None
            element_type = element.name # 'a' or 'button'

            if element_type == 'a':
                href = element.get('href')
            elif element_type == 'button':
                # Simplest case: Check if button is wrapped in an <a> tag
                parent_a = element.find_parent('a')
                if parent_a:
                    href = parent_a.get('href')

            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue # Skip empty, anchor, or javascript links

            # Skip if external link
            if href.startswith('http') and base_url not in href:
                continue

            # Handle relative URLs
            full_url = href
            if href.startswith('/'):
                # Ensure we don't double the slashes if base_url ends with /
                full_url = base_url.rstrip('/') + href
            elif not href.startswith('http'):
                 full_url = base_url.rstrip('/') + '/' + href

            # --- Check depth --- 
            try:
                # Get path relative to base_url domain
                base_domain = base_url.split('//')[1].split('/')[0]  # base_domain - pali.plus
                path = full_url.split(base_domain)[-1]  # path - /login
                # Remove leading slash if present for counting 
                path = path.lstrip('/')  # path - login
                # Check if path is not empty and has no slashes (one level deep)
                if path and '/' not in path:
                    next_level_urls.add(full_url) # next_level_urls - {'https://pali.plus/login'}
            except IndexError:
                 pass # Ignore errors during splitting

        logging.info(f"Found {len(next_level_urls)} URLs one level deeper:")
        for url in sorted(list(next_level_urls)):
            logging.info(url)

        return list(next_level_urls) # return - ['https://pali.plus/login',...]

    except Exception as e:
        logging.error(f"Error finding next level URLs: {str(e)}")
        return []

def select_product_page_with_llm(url_list: list[str]) -> str | None:
    """Select the most likely product listing page from a list of URLs using an ChatGPT"""

    logging.info("Selecting product page from the list using LLM...")

    # Prepare the list of URLs for the prompt
    url_list_str = "\n".join(url_list)

    prompt = f"""
    From the following list of URLs found on an e-commerce website, identify the main product listing page (the page that shows multiple products, often the main category or shop page).

    URL List:
    {url_list_str}

    Please return ONLY the single URL that is most likely the main product listing page. Do not include any other text, explanation, or formatting.
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4", 
            messages=[
                {"role": "system", "content": "You are an expert web analyst helping identify specific page types from a list of URLs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # Low temperature for deterministic output
            max_tokens=100
        )

        selected_url = response.choices[0].message.content.strip() # selected_url - https://pali.plus/login

        return selected_url
        
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {str(e)}")
        return None

def extract_product_name(container) -> tuple[str, str | None]:
    """Extract product name and detail URL from container."""
    name_element = container.select_one('h3.product-title a')
    name = name_element.get_text().strip() if name_element else "Unknown Product"
    detail_url = name_element.get('href') if name_element else None
    return name, detail_url

def extract_price_info(container) -> tuple[str, str | None]:
    """Extract price per carton and price per unit from container."""
    # Price per carton
    price_element = container.select_one('div.product-price-and-shipping span.price')
    price_per_carton_str = price_element.get_text().strip() if price_element else "0,00 €"
    price_per_carton = re.sub(r'[^\d,.]', '', price_per_carton_str).replace(',', '.')
    
    # Price per unit
    short_desc_element = container.select_one('p.an_short_description')
    short_desc = short_desc_element.get_text().strip() if short_desc_element else ""
    price_per_unit_match = re.search(r'(\d+[,.]\d+)\s*€?\s*/\s*pcs', short_desc)
    price_per_unit = price_per_unit_match.group(1).replace(',', '.') if price_per_unit_match else None
    
    return price_per_carton, price_per_unit

def extract_packaging_info(container) -> tuple[str | None, str | None]:
    """Extract units per carton and packaging type from container."""
    short_desc_element = container.select_one('p.an_short_description')
    short_desc = short_desc_element.get_text().strip() if short_desc_element else ""
    
    packaging_match = re.search(r'(\d+)\s*pcs\s*/\s*(carton|boite|box|paquet|pack|package)', short_desc, re.IGNORECASE)
    if packaging_match:
        return packaging_match.group(1), packaging_match.group(2)
    return None, None

def get_next_page_url(soup) -> str | None:
    """Find the URL for the next page of products."""
    next_page_link = soup.select_one('nav.pagination a.next')
    return next_page_link.get('href') if next_page_link else None

def wait_between_requests():
    """Add a random delay between page requests."""
    delay = 2 + random.random()  # 2-3 seconds
    logging.info(f"Waiting {delay:.2f} seconds before next request...")
    time.sleep(delay)

def scrape_product_listings(session: requests.Session, start_url: str, max_pages: int = 999) -> list[dict]:
    """Scrape all products from the listing pages, following pagination links."""
    all_products = []
    current_url = start_url
    page_count = 0
    
    logging.info(f"Starting product listing scraping from {start_url}")
    
    while current_url and page_count < max_pages:
        page_count += 1
        logging.info(f"Scraping listing page {page_count}: {current_url}")
        
        try:
            # Get the current page
            response = session.get(current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all product containers
            product_containers = soup.select('article.product-miniature')
            logging.info(f"Found {len(product_containers)} products on page {page_count}")
            
            # Extract info from each product
            for container in product_containers:
                try:
                    name, detail_url = extract_product_name(container)
                    price_per_carton, price_per_unit = extract_price_info(container)
                    units_per_carton, packaging_type = extract_packaging_info(container)
                    
                    product_data = {
                        'name': name,
                        'price_per_unit': price_per_unit,
                        'price_per_carton': price_per_carton,
                        'units_per_carton': units_per_carton,
                        'packaging_type': packaging_type,
                        'detail_url': detail_url,
                        'barcode': None # We will find this after using the detail_url link
                    }
                    all_products.append(product_data)
                except Exception as e:
                    logging.error(f"Error extracting product data: {str(e)}")
            
            # Handle pagination
            current_url = get_next_page_url(soup)
            if current_url:
                wait_between_requests()
            else:
                logging.info("No next page link found. Reached the last page.")
                break
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while scraping page {current_url}: {str(e)}")
            break
        except Exception as e:
            logging.error(f"Error scraping listing page {current_url}: {str(e)}")
            break
    
    logging.info(f"Completed scraping {len(all_products)} products from {page_count} pages")
    return all_products

def scrape_product_barcode(session: requests.Session, all_products: list[dict]):
    """
    Scrape the barcode for each product from the detail page.
    """
    for product in all_products:
        if product['detail_url']:
            logging.info(f"Scraping barcode for {product['name']} from {product['detail_url']}")
            try:
                response = session.get(product['detail_url'])
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Directly find the barcode element
                barcode_element = soup.find('dd', class_='value')
                if barcode_element:
                    barcode = barcode_element.get_text().strip()
                    product['barcode'] = barcode
                    logging.info(f"Found barcode for {product['name']}: {barcode}")
                else:
                    logging.warning(f"Barcode not found for {product['name']}")
            except Exception as e:
                logging.error(f"Error scraping barcode for {product['name']}: {str(e)}")
            
            # Add a delay between requests
            delay = 2 + random.random()  # 2-3 seconds
            logging.info(f"Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)

def save_products_to_csv(products: list[dict], filename: str):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'price_per_unit', 'price_per_carton', 'units_per_carton', 'packaging_type', 'detail_url', 'barcode']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for product in products:
            writer.writerow(product)

def main():
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    
    # First find login links and attempt login
    potential_links = find_login_links('https://pali.plus')
    session = attempt_login(potential_links, email, password)

    if session:
        logging.info("Login successful, now finding next level URLs...")
        next_level_urls = find_next_level_urls(session, 'https://pali.plus')

        if next_level_urls:
            # Select the product page from the list using LLM
            product_page_url = select_product_page_with_llm(next_level_urls)

            if product_page_url:
                logging.info(f"Proceeding with product page: {product_page_url}")
                
                # Scrape products from the listing pages
                products = scrape_product_listings(session, product_page_url, max_pages=1)
                
                # Scrape barcodes from detail pages
                scrape_product_barcode(session, products)
                
                # Translate products to English
                products = translate_products_to_english(products)
                
                # Save products to CSV
                save_products_to_csv(products, 'product_data.csv')
                logging.info(f"Saved {len(products)} products to product_data.csv")
                
            else:
                logging.error("Could not determine the product page URL using LLM.")
        else:
             logging.warning("No next level URLs found after login.")
    else:
        logging.error("Login failed, cannot proceed")

if __name__ == "__main__":
    main()
