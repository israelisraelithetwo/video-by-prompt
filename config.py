import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Script Generator Configuration
SCRIPT_MODEL_PROVIDER = os.environ.get("SCRIPT_MODEL_PROVIDER", "openai")
SCRIPT_MODEL_URL = os.environ.get("SCRIPT_MODEL_URL", "https://api.openai.com/v1/chat/completions")
SCRIPT_MODEL_KEY = os.environ.get("OPENAI_API_KEY", "")
SCRIPT_MODEL_NAME = os.environ.get("SCRIPT_MODEL_NAME", "gpt-4o")

# Image Generator Configuration
IMAGE_API_PROVIDER = os.environ.get("IMAGE_API_PROVIDER", "huggingface")
IMAGE_API_ENDPOINT = os.environ.get("IMAGE_API_ENDPOINT", "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5")
IMAGE_API_KEY = os.environ.get("IMAGE_API_KEY", "")

# TTS Generator Configuration
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "gtts")
TTS_LANGUAGE = os.environ.get("TTS_LANGUAGE", "he")  # Default to Hebrew
TTS_API_KEY = os.environ.get("TTS_API_KEY", "")

# Video Configuration
VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1280"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "720"))
VIDEO_FPS = int(os.environ.get("VIDEO_FPS", "30"))
