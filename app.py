import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import time
import json
import re

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

# ========== GENERATE IMAGE FUNCTION ==========
def generate_image(prompt, style="American"):
    """
    Generate an image using Pollinations.ai (free, no API key required)
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
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Image generation failed (status {response.status_code})")
            return None
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None

# ========== GENERATE STORY PANELS ==========
def generate_story_panels(prompt, style):
    """
    Break the prompt into 3 story panels using AI via Pollinations.
    Since Pollinations is an image generator, we use it to create each panel.
    """
    panel_prompts = [
        f"{prompt} - panel 1: beginning of the story",
        f"{prompt} - panel 2: middle of the story, action scene",
        f"{prompt} - panel 3: ending of the story, conclusion"
    ]
    
    images = []
    with st.spinner("🎨 Creating your comic..."):
        for i, panel_prompt in enumerate(panel_prompts):
            progress = (i + 1) / 3
            st.progress(progress, text=f"Generating panel {i+1}/3...")
            
            img_data = generate_image(panel_prompt, style)
            if img_data:
                images.append(img_data)
            else:
                # Fallback: generate a simple placeholder
                st.warning(f"Panel {i+1} generation failed. Using placeholder.")
                images.append(None)
            time.sleep(0.5)  # Small delay to avoid rate limiting
    
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
            if images[i] is not None:
                try:
                    img = Image.open(BytesIO(images[i]))
                    st.image(img, use_container_width=True)
                except Exception:
                    st.image("https://via.placeholder.com/512x512/222/FFF?text=Panel+{panel_num}", use_container_width=True)
            else:
                st.image("https://via.placeholder.com/512x512/222/FFF?text=Panel+{panel_num}", use_container_width=True)
            st.caption(f"Scene {panel_num}/3")
    
    st.divider()
    st.success("✅ Comic generated successfully!")
    
    # Download option
    if all(images):
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
