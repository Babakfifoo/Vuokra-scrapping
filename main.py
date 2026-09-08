from app.services import ingest
from app.utils.systemTools import setup_logging, logging
from app.utils import Storage

def main():
    ingest.ingest_to_files()
    Storage.load_and_merge_jsons()


if __name__ == "__main__":
    setup_logging()
    main()

    logging.info("Scrapping for today is Done!")
