import sys
import os
import logging

# Add the current directory to sys.path to allow absolute imports from 'src'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.orchestrator.pipeline import ContentPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "app.log"))
    ]
)

def main():
    print("AI Financial News Engine - Starting Restructured Pipeline")
    pipeline = ContentPipeline()
    try:
        pipeline.run()
    except KeyboardInterrupt:
        print("\nPipeline stopped by user.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    main()
