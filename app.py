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

st.title("🎬 ComicCrafter AI – Action Video")
st.markdown("Turn your idea into a **short animated video** with built‑in sound effects!")

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🎬 Mode")
    st.info("Generates a 3‑scene animated video with background music and action sounds.")
    st.markdown("---")
    st.markdown("### 🎨 Art Style")
    art_style = st.selectbox("Choose Art Style", ["Anime", "Manga", "American", "Belgian"])
    st.markdown("---")
    st.markdown("### 🔑 API Status")
    st.info("✅ Pollinations.ai (no API key)")
    st.info("🎵 Built‑in sound generation (no external files)")
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

# ========== IMAGE GENERATION ==========
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

# ========== GENERATE VIDEO FRAMES (3 scenes) ==========
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

# ========== SYNTHESIZE SOUND EFFECTS ==========
def make_background_music(duration):
    sr = 22050
    t = np.linspace(0, duration, int(sr * duration))
    freq1, freq2, freq3 = 220, 261.63, 329.63
    wave = (0.3 * np.sin(2 * np.pi * freq1 * t) +
            0.3 * np.sin(2 * np.pi * freq2 * t) +
            0.3 * np.sin(2 * np.pi * freq3 * t))
    attack = 0.05
    release = 0.05
    env = np.ones_like(t)
    env[:int(sr*attack)] = np.linspace(0, 1, int(sr*attack))
    env[-int(sr*release):] = np.linspace(1, 0, int(sr*release))
    wave *= env
    wave *= 0.3
    return wave.astype(np.float32)

def make_explosion_sound(duration=1.0):
    sr = 22050
    samples = int(sr * duration)
    noise = np.random.normal(0, 1, samples)
    t = np.linspace(0, duration, samples)
    env = np.exp(-6 * t)
    wave = noise * env * 0.2
    return wave.astype(np.float32)

def make_impact_sound(duration=0.3):
    sr = 22050
    samples = int(sr * duration)
    t = np.linspace(0, duration, samples)
    sine = np.sin(2 * np.pi * 800 * t) * np.exp(-10 * t)
    noise = np.random.normal(0, 1, samples) * np.exp(-12 * t)
    wave = (sine * 0.5 + noise * 0.3) * 0.5
    return wave.astype(np.float32)

def make_audio_clip(wave, sr=22050):
    """Convert a numpy wave array to an AudioClip with safe indexing."""
    duration = len(wave) / sr
    def make_frame(t):
        # t is in seconds; compute index, clamp to valid range
        idx = int(round(t * sr))
        if idx < 0:
            idx = 0
        if idx >= len(wave):
            idx = len(wave) - 1
        return np.array([wave[idx]])
    clip = AudioClip(make_frame, duration=duration)
    clip.fps = sr
    return clip

# ========== CREATE VIDEO WITH BUILT-IN SOUNDS ==========
def create_video(images, prompt):
    duration_per_frame = 4.0
    total_duration = duration_per_frame * len(images)
    
    # 1. Build video clips
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
    
    # 2. Background music
    bgm_wave = make_background_music(total_duration)
    bgm_clip = make_audio_clip(bgm_wave, 22050)
    bgm_clip = bgm_clip.set_duration(total_duration)
    
    # 3. Choose sound effect based on prompt
    keywords = {
        "explosion": make_explosion_sound(1.0),
        "fire": make_explosion_sound(0.8),
        "battle": make_impact_sound(0.5),
        "fight": make_impact_sound(0.5),
        "crash": make_impact_sound(0.6),
    }
    selected_wave = None
    for kw, func in keywords.items():
        if kw in prompt.lower():
            selected_wave = func
            break
    if selected_wave is None:
        selected_wave = make_impact_sound(0.5)
    
    # 4. Place sound effect in the middle of scene 2 (approx 1.5s into scene 2)
    start_time = duration_per_frame * 1 + 1.0
    sfx_duration = len(selected_wave) / 22050
    # Make sure sfx doesn't exceed total video duration
    if start_time + sfx_duration > total_duration:
        sfx_duration = total_duration - start_time
        if sfx_duration > 0:
            selected_wave = selected_wave[:int(sfx_duration * 22050)]
        else:
            selected_wave = np.array([0.0])
    
    sfx_clip = make_audio_clip(selected_wave, 22050)
    sfx_clip = sfx_clip.set_start(start_time)
    sfx_clip = sfx_clip.set_duration(sfx_duration)
    
    # 5. Combine audio
    final_audio = CompositeAudioClip([bgm_clip, sfx_clip])
    video = video.set_audio(final_audio)
    
    # 6. Write video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_video:
        video.write_videofile(tmp_video.name, fps=24, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        video_path = tmp_video.name
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
        frames = generate_video_frames(prompt, art_style, num_frames=3)
        video_path = create_video(frames, prompt)
        video_file = open(video_path, 'rb')
        video_bytes = video_file.read()
        video_file.close()
        st.video(video_bytes)
        st.download_button(
            label="⬇️ Download Video (MP4)",
            data=video_bytes,
            file_name="action_video.mp4",
            mime="video/mp4"
        )
        os.unlink(video_path)
        st.success("✅ Video created successfully!")

elif generate_btn and not prompt:
    st.warning("⚠️ Please enter a story idea first.")

st.divider()
st.caption("Powered by Pollinations.ai (images) + built‑in sound synthesis (MoviePy) | Built with Streamlit")
