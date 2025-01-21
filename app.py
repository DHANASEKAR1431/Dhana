import streamlit as st
import google.generativeai as genai
from pathlib import Path
from PIL import Image
import os
import time
import mimetypes
import google.api_core.exceptions  # Handle API quota errors

# Configure API Key 
API_KEY = "AIzaSyDOfdCfv2y1byZp2yS_4y7MgNToCdUeEGg"
genai.configure(api_key=API_KEY)

# Model configuration
MODEL_CONFIG = {
    "temperature": 0.2,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

# Safety settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Initialize the Gemini model
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    generation_config=MODEL_CONFIG,
    safety_settings=safety_settings,
)

# Directory for automatic image upload
IMAGE_DIR = r"C:\Users\Admin\Pictures\images"

# Ensure directory exists
os.makedirs(IMAGE_DIR, exist_ok=True)

# Cache processed images
@st.cache_data
def get_processed_images():
    return set()

# Function to get all unprocessed images
def get_unprocessed_images():
    processed_images = get_processed_images()
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    
    # Return only images that haven't been processed
    return [os.path.join(IMAGE_DIR, img) for img in image_files if img not in processed_images]

# Function to format file input for Gemini
def file_format(file_path):
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        st.warning("Could not determine MIME type. Defaulting to 'image/png'.")
        mime_type = "image/png"

    return [{
        "mime_type": mime_type,
        "data": file.read_bytes()
    }]

# Function to generate Gemini output with error handling
def gemini_output(file_path, system_prompt):
    file_info = file_format(file_path)
    input_prompt = [system_prompt, file_info[0]]
    
    try:
        response = model.generate_content(input_prompt)
        return response.text  
    except google.api_core.exceptions.ResourceExhausted:
        st.error("⚠️ API quota exceeded. Waiting 1 minute before retrying...")
        time.sleep(60)  # Wait 1 minute before retrying
        return "⚠️ API quota exceeded. Please try again later."

# UI
st.title("📊 Gemini Candlestick Pattern Detector")
st.write("This tool automatically detects candlestick patterns from chart images.")

# Trading bot prompt
system_prompt = "You are a trading bot. Analyze the image for engulfing, bearish, pinbar, hammer, inverted hammer, and insidebar candlestick patterns and provide their locations."

# Process all unprocessed images
image_paths = get_unprocessed_images()

if image_paths:
    for idx, file_path in enumerate(image_paths, start=1):
        # Display image
        image = Image.open(file_path)
        st.image(image, caption=f"📌 Processing {idx}/{len(image_paths)}: {Path(file_path).name}", use_column_width=True)

        # Generate Gemini output
        with st.spinner(f"🤖 Analyzing {idx}/{len(image_paths)}..."):
            output = gemini_output(file_path, system_prompt)
        
        st.write("### 📢 Gemini Model Output:")
        st.markdown(output)

        # Mark the image as processed
        processed_images = get_processed_images()
        processed_images.add(Path(file_path).name)
        st.cache_data.clear()  # Clear cache to update processed images

        # ADD A DELAY TO PREVENT API OVERLOAD
        st.info("⏳ Waiting 5 seconds before processing the next image...")
        time.sleep(5)  # Adjust time as needed

    # ✅ FINAL SUCCESS MESSAGE
    st.success("🎉 All images have been collected and processed successfully!")
else:
    st.info("📂 No new images found. Please upload a candlestick chart.")

