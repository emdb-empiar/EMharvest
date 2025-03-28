import sys
import logging
from emharvest.emharvest_main import main

def run():
    """Entry point for the emharvest package."""
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run()
