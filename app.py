import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time
import os
import tempfile
from moviepy.editor import *
import numpy as np

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="ComicCrafter AI – Action Video",
    page_icon="🎬",
    layout="wide"
)

# ========== TITLE ==========
st.title("🎬 ComicCrafter AI – Action Video")
st.markdown("Turn your idea into a **short animated video** with sound effects!")

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🎬 Mode")
    st.info("Generates a 3‑scene animated video with background music and action sounds.")
    
    st.markdown("---")
    st.markdown("### 🎨 Art Style")
    art_style = st.selectbox(
        "Choose Art Style",
        ["Anime", "Manga", "American", "Belgian"],
        help="Select the visual style for your video"
    )
    
    st.markdown("---")
    st.markdown("### 🔑 API Status")
    st.info("✅ Pollinations.ai (no API key)")
    st.info("🎵 Sound effects from Google's free sound library")
    
    st.markdown("---")
    st.markdown("### 💡 Example Prompts")
    examples = [
        "A superhero cat blows up an alien ship",
        "A robot fights a giant monster in the city",
        "A pirate and ninja battle on a sinking ship",
        "A dragon breathes fire on a castle",
        "Two cars racing and one explodes"
    ]
    for ex in examples:
        if st.button(ex, key=f"example_{ex[:20]}"):
            st.session_state.prompt = ex
            st.rerun()

# ========== GENERATE IMAGE ==========
def generate_image(prompt, style="Anime", max_retries=3):
    style_prompts = {
        "Manga": "manga style, black and white",
        "Anime": "anime style, colorful",
        "American": "american comic style, vibrant",
        "Belgian": "belgian comic style, clear line"
    }
    style_text = style_prompts.get(style, "")
    full_prompt = f"{prompt}, {style_text}, high quality"
    formatted = full_prompt.replace(" ", "+")
    url = f"https://image.pollinations.ai/prompt/{formatted}?width=512&height=512&model=sdxl"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 429:
                wait = (2 ** attempt) * 1.5
                st.warning(f"⏳ Rate limit – waiting {wait:.1f}s...")
                time.sleep(wait)
            else:
                time.sleep(0.5)
        except:
            time.sleep(1)
    return None

def generate_placeholder(panel_num, text):
    img = Image.new('RGB', (512, 512), color=(30, 30, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    draw.rectangle([10, 10, 502, 502], outline=(200,200,200), width=3)
    draw.text((20, 20), f"Scene {panel_num}\n\n{text[:50]}...", fill=(255,255,255), font=font)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

# ========== GENERATE FRAMES ==========
def generate_video_frames(prompt, style, num_frames=3):
    prompts = [
        f"{prompt} - scene 1: the beginning",
        f"{prompt} - scene 2: action, explosion, fight",
        f"{prompt} - scene 3: the end, resolution"
    ]
    images = []
    for i, p in enumerate(prompts):
        st.progress((i+1)/num_frames, text=f"Generating scene {i+1}/{num_frames}...")
        img = generate_image(p, style)
        images.append(img if img else generate_placeholder(i+1, p))
        time.sleep(1.5)
    return images

# ========== CREATE VIDEO WITH SOUND ==========
def create_video(images, prompt):
    total_duration = 4.0 * len(images)  # 4 seconds per scene
    # 1. Sound effect selection based on prompt keywords
    sound_map = {
        "explosion": "https://actions.google.com/sounds/v1/explosion/explosion_short_001.mp3",
        "battle": "https://actions.google.com/sounds/v1/impact/impact_medium_001.mp3",
        "fight": "https://actions.google.com/sounds/v1/impact/impact_medium_001.mp3",
        "fire": "https://actions.google.com/sounds/v1/fire/fire_roar_001.mp3",
        "crash": "https://actions.google.com/sounds/v1/crash/crash_metal_001.mp3",
        "explode": "https://actions.google.com/sounds/v1/explosion/explosion_short_001.mp3"
    }
    selected_url = None
    for keyword, url in sound_map.items():
        if keyword in prompt.lower():
            selected_url = url
            break
    if selected_url is None:
        selected_url = "https://actions.google.com/sounds/v1/impact/impact_medium_001.mp3"  # default

    # 2. Create video clips
    duration_per_frame = 4.0
    clips = []
    for idx, img_data in enumerate(images):
        img = Image.open(BytesIO(img_data))
        img = img.resize((640, 480))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        text = f"Scene {idx+1}"
        tw = draw.textlength(text, font=font)
        x = (640 - tw) // 2
        y = 480 - 60
        draw.text((x-1, y-1), text, fill='black', font=font)
        draw.text((x+1, y-1), text, fill='black', font=font)
        draw.text((x-1, y+1), text, fill='black', font=font)
        draw.text((x+1, y+1), text, fill='black', font=font)
        draw.text((x, y), text, fill='white', font=font)
        frame = np.array(img)
        clip = ImageClip(frame).set_duration(duration_per_frame)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    # 3. Download sound effect
    audio_clips = []
    try:
        response = requests.get(selected_url, timeout=10)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_sfx:
                tmp_sfx.write(response.content)
                sfx_path = tmp_sfx.name
            # Load as audio clip
            sfx_audio = AudioFileClip(sfx_path)
            # Place it at the beginning of scene 2 (if we have at least 2 scenes)
            if len(images) >= 2:
                start_time = duration_per_frame * 1 + 1.0  # 1 second into scene 2
                sfx_audio = sfx_audio.set_start(start_time)
                audio_clips.append(sfx_audio)
            else:
                # Only one scene? Place it at the end
                sfx_audio = sfx_audio.set_start(total_duration - sfx_audio.duration)
                audio_clips.append(sfx_audio)
            st.info("🔊 Sound effect loaded.")
        else:
            st.warning("⚠️ Could not download sound effect.")
    except Exception as e:
        st.warning(f"⚠️ Sound download failed: {e}")

    # 4. Compose audio
    if audio_clips:
        final_audio = CompositeAudioClip(audio_clips)
        video = video.set_audio(final_audio)
    else:
        st.warning("No audio added. Video will be silent.")

    # 5. Write video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_video:
        video.write_videofile(tmp_video.name, fps=24, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        video_path = tmp_video.name

    # Clean up temp sfx file
    if 'sfx_path' in locals() and os.path.exists(sfx_path):
        os.unlink(sfx_path)
    return video_path

# ========== MAIN UI ==========
if "prompt" not in st.session_state:
    st.session_state.prompt = ""

prompt = st.text_area(
    "📝 Enter your story idea",
    value=st.session_state.prompt,
    height=100,
    placeholder="e.g., A superhero cat blows up an alien ship..."
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_btn = st.button("🎬 Generate Action Video", use_container_width=True, type="primary")

if generate_btn and prompt:
    st.divider()
    st.markdown(f"### 🎬 Action Video – *{art_style}* style")
    st.markdown(f"**Story:** {prompt}")
    st.divider()
    
    with st.spinner("🎨 Generating scenes and adding sound effects (may take 1-2 minutes)..."):
        # Generate frames (3 scenes)
        frames = generate_video_frames(prompt, art_style, num_frames=3)
        # Create video with sounds
        video_path = create_video(frames, prompt)
        # Display video
        video_file = open(video_path, 'rb')
        video_bytes = video_file.read()
        video_file.close()
        st.video(video_bytes)
        # Download button
        st.download_button(
            label="⬇️ Download Video (MP4)",
            data=video_bytes,
            file_name="action_video.mp4",
            mime="video/mp4"
        )
        # Clean up
        os.unlink(video_path)
        st.success("✅ Video created successfully!")

elif generate_btn and not prompt:
    st.warning("⚠️ Please enter a story idea first.")

# ========== FOOTER ==========
st.divider()
st.caption("Powered by Pollinations.ai (images) + Google Sound Effects + MoviePy (video) | Built with Streamlit")
