import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time
import os
import tempfile
from gtts import gTTS
from moviepy.editor import *
import numpy as np

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="ComicCrafter AI – Cartoon & Anime Video",
    page_icon="🎨",
    layout="wide"
)

# ========== TITLE ==========
st.title("🎨 ComicCrafter AI")
st.markdown("Turn your ideas into a **comic strip** or an **anime video** with sound!")

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🎬 Mode")
    mode = st.radio(
        "Select output type:",
        ["Comic Strip", "Anime Video"],
        help="Comic: static 3-panel comic. Anime: video with 5 frames, voiceover, and subtitles."
    )
    
    st.markdown("---")
    st.markdown("### 🎨 Art Style")
    art_style = st.selectbox(
        "Choose Art Style",
        ["Manga", "Anime", "American", "Belgian"],
        help="Select the visual style for your comic/video"
    )
    
    st.markdown("---")
    st.markdown("### 🔑 API Status")
    st.info("✅ Using Pollinations.ai (no API key required)")
    st.info("🎤 Using gTTS (free, no API key)")
    
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

# ========== GENERATE IMAGE (with retries) ==========
def generate_image_with_retry(prompt, style="Anime", max_retries=3):
    style_prompts = {
        "Manga": "manga style, black and white, japanese comic",
        "Anime": "anime style, colorful, japanese animation",
        "American": "american comic style, superhero, vibrant colors",
        "Belgian": "belgian comic style, clear line, tintin style"
    }
    style_text = style_prompts.get(style, "")
    full_prompt = f"{prompt}, {style_text}, high quality"
    formatted = full_prompt.replace(" ", "+")
    url = f"https://image.pollinations.ai/prompt/{formatted}?width=512&height=512&model=flux"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 429:
                wait = (2 ** attempt) * 2
                st.warning(f"Rate limit – waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
        except Exception:
            time.sleep(2)
    return None

def generate_placeholder(panel_num, text):
    img = Image.new('RGB', (512, 512), color=(30, 30, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    draw.rectangle([10, 10, 502, 502], outline=(200,200,200), width=3)
    draw.text((20, 20), f"Panel {panel_num}\n\n{text[:50]}...", fill=(255,255,255), font=font)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

# ========== COMIC MODE ==========
def generate_comic(prompt, style):
    panel_prompts = [
        f"{prompt} - panel 1: beginning",
        f"{prompt} - panel 2: middle, action",
        f"{prompt} - panel 3: ending, conclusion"
    ]
    images = []
    for i, p in enumerate(panel_prompts):
        st.progress((i+1)/3, text=f"Generating panel {i+1}/3...")
        img = generate_image_with_retry(p, style)
        images.append(img if img else generate_placeholder(i+1, p))
        time.sleep(2)
    return images

# ========== ANIME VIDEO MODE ==========
def generate_video_frames(prompt, style, num_frames=5):
    # Create a story arc with 5 frames
    prompts = [
        f"{prompt} - frame 1: opening scene",
        f"{prompt} - frame 2: rising action",
        f"{prompt} - frame 3: climax",
        f"{prompt} - frame 4: falling action",
        f"{prompt} - frame 5: resolution"
    ]
    images = []
    for i, p in enumerate(prompts):
        st.progress((i+1)/num_frames, text=f"Generating frame {i+1}/{num_frames}...")
        img = generate_image_with_retry(p, style)
        images.append(img if img else generate_placeholder(i+1, p))
        time.sleep(2)
    return images

def create_video(images, prompt, style):
    # 1. Generate voiceover narration using gTTS
    narration = f"This is a story about {prompt}. In the first scene, the adventure begins. As the story unfolds, exciting events happen. The climax brings a thrilling moment. Finally, the story reaches a satisfying conclusion."
    tts = gTTS(text=narration, lang='en', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_audio:
        tts.save(tmp_audio.name)
        audio_path = tmp_audio.name
    
    # 2. Create video frames with subtitles
    clips = []
    duration = 3.0  # seconds per frame
    total_duration = duration * len(images)
    
    for idx, img_data in enumerate(images):
        # Convert image to numpy array
        img = Image.open(BytesIO(img_data))
        img = img.resize((640, 480))  # Resize for video
        frame = np.array(img)
        
        # Create a clip from the frame
        clip = ImageClip(frame).set_duration(duration)
        
        # Add subtitle (optional) – a simple text overlay
        txt_clip = TextClip(f"Scene {idx+1}", fontsize=24, color='white', font='Arial', stroke_color='black', stroke_width=2)
        txt_clip = txt_clip.set_position(('center', 0.85), relative=True).set_duration(duration)
        clip = CompositeVideoClip([clip, txt_clip])
        clips.append(clip)
    
    # Concatenate all clips
    final = concatenate_videoclips(clips, method="compose")
    
    # Add audio
    audio = AudioFileClip(audio_path)
    # If audio is shorter than video, loop it; if longer, trim
    if audio.duration < total_duration:
        audio = audio.loop(duration=total_duration)
    else:
        audio = audio.subclip(0, total_duration)
    final = final.set_audio(audio)
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_video:
        final.write_videofile(tmp_video.name, fps=24, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        video_path = tmp_video.name
    
    # Clean up audio temp file
    os.unlink(audio_path)
    return video_path

# ========== MAIN UI ==========
if "prompt" not in st.session_state:
    st.session_state.prompt = ""

prompt = st.text_area(
    "📝 Enter your story idea",
    value=st.session_state.prompt,
    height=100,
    placeholder="Describe your story..."
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_btn = st.button("🎨 Generate", use_container_width=True, type="primary")

if generate_btn and prompt:
    st.divider()
    if mode == "Comic Strip":
        st.markdown(f"### 🖼️ Comic Strip – *{art_style}* style")
        st.markdown(f"**Story:** {prompt}")
        st.divider()
        images = generate_comic(prompt, art_style)
        cols = st.columns(3)
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"**Panel {i+1}**")
                try:
                    img = Image.open(BytesIO(images[i]))
                    st.image(img, use_container_width=True)
                except:
                    st.error("Could not display image")
                st.caption(f"Scene {i+1}/3")
        st.success("✅ Comic generated!")
        st.info("Right-click each image to save.")

    else:  # Anime Video
        st.markdown(f"### 🎬 Anime Video – *{art_style}* style")
        st.markdown(f"**Story:** {prompt}")
        st.divider()
        
        with st.spinner("Generating frames and creating video (this may take 1-2 minutes)..."):
            # Generate frames
            frames = generate_video_frames(prompt, art_style, num_frames=5)
            # Create video
            video_path = create_video(frames, prompt, art_style)
            # Display video
            video_file = open(video_path, 'rb')
            video_bytes = video_file.read()
            video_file.close()
            st.video(video_bytes)
            # Download button
            st.download_button(
                label="⬇️ Download Video",
                data=video_bytes,
                file_name="anime_video.mp4",
                mime="video/mp4"
            )
            # Clean up temp video file
            os.unlink(video_path)
            st.success("✅ Video created successfully!")

elif generate_btn and not prompt:
    st.warning("⚠️ Please enter a story idea first.")

# ========== FOOTER ==========
st.divider()
st.caption("Powered by Pollinations.ai (image) + gTTS (voice) + MoviePy (video) | Built with Streamlit")
