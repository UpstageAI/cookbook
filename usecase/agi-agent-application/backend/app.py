"""
Main application entry point for FinanceGuard
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Import the Flask app after logging configuration
        from src.api.routes import app
        
        # Run the server
        port = int(os.environ.get("PORT", 5000))
        host = os.environ.get("HOST", "127.0.0.1")
        
        logger.info(f"Starting web server on http://{host}:{port}")
        app.run(host=host, port=port, debug=os.environ.get("DEBUG", "False").lower() == "true")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        import traceback
        logger.error(traceback.format_exc())
