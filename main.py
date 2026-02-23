from app.services import ingest
from app.utils.systemTools import setup_logging, logging

def main():
    ingest.ingest_to_files()


if __name__ == "__main__":
    setup_logging()
    main()
    
    logging.info("Scrapping for today is Done!")
    
