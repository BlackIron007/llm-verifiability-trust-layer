import nltk
import logging

def download_nltk_data():
    """
    Downloads the NLTK 'punkt' package if it is not found.
    """
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logging.info("NLTK 'punkt' package not found. Downloading...")
        nltk.download('punkt', quiet=True)
        logging.info("NLTK 'punkt' package downloaded.")