import nltk

def download_nltk_data():
    """Download necessary NLTK data for the project."""
    resources = [
        'punkt',
        'punkt_tab',
        'stopwords',
        'wordnet',
        'omw-1.4',
    ]
    
    print("Downloading NLTK data...")
    for resource in resources:
        try:
            nltk.download(resource)
            print(f"Successfully downloaded {resource}")
        except Exception as e:
            print(f"Error downloading {resource}: {e}")
            
if __name__ == "__main__":
    download_nltk_data()
