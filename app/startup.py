import nltk
import os
from nltk.tokenize import sent_tokenize

APP_DIR = os.path.dirname(__file__)
LOCAL_NLTK_DATA = os.path.join(APP_DIR, 'nltk_data')

nltk.data.path.insert(0, LOCAL_NLTK_DATA)

def check_local_nltk_data():
    """
    Verifies that the local NLTK 'punkt' data is available in the project.
    If not, it raises a clear error with instructions for the developer.
    """
    try:
        sent_tokenize("This is a test sentence. It ensures all data is loaded.")
    except LookupError:
        raise LookupError(
            "\n" + "*"*70 +
            "\nFATAL ERROR: The required NLTK 'punkt' data is missing or incomplete." +
            "\n\nPlease run the following command from the project's root directory to download it:" +
            "\n\n  python download_data.py\n" +
            "*"*70
        )