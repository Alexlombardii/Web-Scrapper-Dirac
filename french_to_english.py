import json
import logging
import threading
import time
from queue import Queue
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure OpenAI client
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=openai_api_key)

def translate_product_to_english(product: dict, result_queue: Queue) -> None:
    """Translate a single product to English and put result in queue."""
    try:
        # Prepare the prompt with the product data
        prompt = f"""
        Translate the following product information from French to English. 
        Keep the numbers and URLs exactly as they are, only translate the text fields.
        Return the data in the same format but with English translations.

        Product Data:
        {json.dumps(product, indent=2, ensure_ascii=False)}

        Return ONLY the translated JSON object, no additional text or explanation.
        """

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in e-commerce product descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent output
            max_tokens=500
        )

        # Parse the response and convert back to dict
        translated_product = json.loads(response.choices[0].message.content.strip())
        result_queue.put((product, translated_product))

    except Exception as e:
        logging.error(f"Error translating product: {str(e)}")
        result_queue.put((product, product))  # Return original if translation fails

def translate_products_to_english(products: List[Dict]) -> List[Dict]:
    """Translate all products to English using multiple threads."""
    logging.info("Translating products to English using parallel processing...")
    
    # Create a queue to collect results
    result_queue = Queue()
    threads = []
    translated_products = [None] * len(products)  # Pre-allocate list
    
    # Create and start threads
    for i, product in enumerate(products):
        thread = threading.Thread(
            target=translate_product_to_english,
            args=(product, result_queue)
        )
        thread.start()
        threads.append(thread)
        
        # Add a small delay between thread starts to avoid rate limits
        time.sleep(0.5)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Collect results from queue
    while not result_queue.empty():
        original_product, translated_product = result_queue.get()
        # Find the index of the original product
        idx = products.index(original_product)
        translated_products[idx] = translated_product
    
    # Log completion
    logging.info(f"Completed translation of {len(translated_products)} products")
    return translated_products