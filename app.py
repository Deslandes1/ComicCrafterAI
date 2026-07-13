import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time
import json
import re
import random

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="ComicCrafter AI – Cartoon Generator",
    page_icon="🎨",
    layout="wide"
)

# ========== TITLE ==========
st.title("🎨 ComicCrafter AI")
st.markdown("Turn your ideas into a comic strip! Enter a prompt and choose your style.")

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🎬 Settings")
    
    # Art style selection
    art_style = st.selectbox(
        "Choose Art Style",
        ["Manga", "Anime", "American", "Belgian"],
        help="Select the visual style for your comic"
    )
    
    st.markdown("---")
    st.markdown("### 🔑 API Status")
    st.info("✅ Using Pollinations.ai (no API key required)")
    
    st.markdown("---")
    st.markdown("### 📖 How It Works")
    st.markdown("""
    1. Enter a story prompt below
    2. Choose your art style
    3. Click **Generate Comic**
    4. The AI creates a 3-panel comic strip
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Example Prompts")
    examples = [
        "A superhero cat saving a city from alien invasion",
        "A robot learning to bake cookies with a grandma",
        "A pirate and a ninja teaming up to find treasure",
        "A dragon who wants to become a chef",
        "Two friends building a time machine from a washing machine"
    ]
    for ex in examples:
        if st.button(ex, key=f"example_{ex[:20]}"):
            st.session_state.prompt = ex
            st.rerun()

# ========== GENERATE IMAGE FUNCTION WITH RETRIES ==========
def generate_image_with_retry(prompt, style="American", max_retries=3):
    """
    Generate an image using Pollinations.ai with retry logic.
    """
    # Enhance prompt with style information
    style_prompts = {
        "Manga": "manga style, black and white, japanese comic",
        "Anime": "anime style, colorful, japanese animation",
        "American": "american comic style, superhero, vibrant colors",
        "Belgian": "belgian comic style, clear line, tintin style"
    }
    
    style_text = style_prompts.get(style, "")
    full_prompt = f"{prompt}, {style_text}, comic panel"
    
    # Format for URL
    formatted_prompt = full_prompt.replace(" ", "+")
    
    # Pollinations.ai endpoint with parameters
    url = f"https://image.pollinations.ai/prompt/{formatted_prompt}"
    url += "?width=512&height=512&model=flux"
    
    # Retry logic
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=60)  # Increased timeout
            if response.status_code == 200:
                return response.content
            elif response.status_code == 429:
                # Rate limit – wait and retry
                wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                st.warning(f"Rate limit hit. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                st.error(f"Image generation failed (status {response.status_code})")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
                continue
        except requests.exceptions.Timeout:
            st.warning(f"Timeout on attempt {attempt+1}. Retrying...")
            time.sleep(2)
            continue
        except Exception as e:
            st.error(f"Error generating image: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2)
            continue
    
    return None

# ========== GENERATE PLACEHOLDER IMAGE (fallback) ==========
def generate_placeholder(panel_num, prompt):
    """Create a local placeholder image when generation fails."""
    img = Image.new('RGB', (512, 512), color=(30, 30, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    # Draw border
    draw.rectangle([10, 10, 502, 502], outline=(200, 200, 200), width=3)
    
    # Draw text
    text = f"Panel {panel_num}\n\n{prompt[:50]}..."
    draw.text((20, 20), text, fill=(255, 255, 255), font=font)
    
    # Convert to bytes
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

# ========== GENERATE STORY PANELS ==========
def generate_story_panels(prompt, style):
    """
    Break the prompt into 3 story panels using Pollinations.ai.
    """
    panel_prompts = [
        f"{prompt} - panel 1: beginning of the story",
        f"{prompt} - panel 2: middle of the story, action scene",
        f"{prompt} - panel 3: ending of the story, conclusion"
    ]
    
    images = []
    for i, panel_prompt in enumerate(panel_prompts):
        panel_num = i + 1
        progress = (i + 1) / 3
        st.progress(progress, text=f"Generating panel {panel_num}/3...")
        
        # Generate with retry
        img_data = generate_image_with_retry(panel_prompt, style)
        
        if img_data:
            images.append(img_data)
        else:
            # Fallback: generate placeholder
            st.warning(f"Panel {panel_num} generation failed after retries. Using placeholder.")
            placeholder = generate_placeholder(panel_num, panel_prompt)
            images.append(placeholder)
        
        # Add delay between panels to avoid rate limiting
        if i < 2:
            time.sleep(2)
    
    return images

# ========== MAIN PROMPT INPUT ==========
if "prompt" not in st.session_state:
    st.session_state.prompt = ""

prompt = st.text_area(
    "📝 Enter your story idea",
    value=st.session_state.prompt,
    height=100,
    placeholder="e.g., A superhero cat saving a city from alien invasion...",
    help="Describe the comic you want to create"
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_btn = st.button("🎨 Generate Comic", use_container_width=True, type="primary")

# ========== GENERATE COMIC ==========
if generate_btn and prompt:
    st.divider()
    st.markdown(f"### 🎭 Your Comic – *{art_style}* style")
    st.markdown(f"**Story:** {prompt}")
    st.divider()
    
    # Generate the 3 panels
    images = generate_story_panels(prompt, art_style)
    
    # Display as 3 columns
    cols = st.columns(3)
    for i, col in enumerate(cols):
        panel_num = i + 1
        with col:
            st.markdown(f"**Panel {panel_num}**")
            try:
                img = Image.open(BytesIO(images[i]))
                st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"Could not display panel {panel_num}")
                # Show fallback text
                st.markdown(f"*Placeholder for panel {panel_num}*")
            st.caption(f"Scene {panel_num}/3")
    
    st.divider()
    st.success("✅ Comic generated successfully!")
    
    # Download option
    st.info("💡 To download, right-click each image and select 'Save image as...'")

elif generate_btn and not prompt:
    st.warning("⚠️ Please enter a story idea first.")

# ========== FOOTER ==========
st.divider()
st.caption("Powered by Pollinations.ai (free image generation) | Built with Streamlit")

# ========== ERROR HANDLING ==========
if "error" in st.session_state:
    st.error(st.session_state.error)
    del st.session_state.error
