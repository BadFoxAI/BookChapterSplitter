import streamlit as st
import os
import random
import uuid
import tempfile
import warnings
from PIL import Image, ImageOps
import io
import shutil
import subprocess
warnings.filterwarnings('ignore', category=SyntaxWarning, module='moviepy')

class SlideshowGenerator:
    def __init__(self):
        """Initialize the slideshow generator with default settings."""
        self.temp_dir = tempfile.mkdtemp()
        self.image_dir = os.path.join(self.temp_dir, 'images')
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_video(self, image_files, settings):
        """Generate video from uploaded images using FFmpeg directly."""
        if not image_files:
            raise ValueError("No images provided")

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Prepare images with consistent naming for FFmpeg
            prepared_images = []
            for idx, img_path in enumerate(image_files):
                status_text.text(f"Processing image {idx + 1}/{len(image_files)} ✨")
                
                # Open and resize the image with PIL
                img = Image.open(img_path)
                target_width, source_height, mode = settings['resolution']
                
                if mode == 'anamorphic':
                    img = img.resize((target_width, target_width), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((target_width, source_height), Image.Resampling.LANCZOS)
                
                # Save the resized image with sequential naming
                output_path = os.path.join(self.image_dir, f'image_{idx:04d}.jpg')
                img.save(output_path, 'JPEG', quality=95)
                prepared_images.append(output_path)
                
                progress = (idx + 1) / len(image_files)
                progress_bar.progress(progress)

            status_text.text("Creating video sequence...")
            output_path = os.path.join(self.output_dir, f"{settings['filename']}.mp4")

            # Calculate total duration including transitions
            total_duration = (len(image_files) * settings['image_duration']) + (settings['transition_duration'] * (len(image_files) - 1))
            
            # Prepare FFmpeg command
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-framerate', '24',
                '-pattern_type', 'sequence',
                '-i', os.path.join(self.image_dir, 'image_%04d.jpg'),
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-profile:v', 'baseline',
                '-level', '3.0',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-tune', 'animation',
                '-b:v', settings['quality'],
                '-x264opts', 'no-cabac:ref=1:bframes=0:weightp=0:8x8dct=0:trellis=0:me=dia',
                '-crf', '30',
                '-vf', f'fps=24,format=yuv420p,fade=t=in:st=0:d={settings["transition_duration"]},fade=t=out:st={total_duration-settings["transition_duration"]}:d={settings["transition_duration"]}',
                output_path
            ]

            # Run FFmpeg
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")

            return output_path

        except Exception as e:
            raise e

def main():
    st.set_page_config(
        page_title="TribeXR Visuals Toolkit",
        page_icon="🎛️",
        layout="wide"
    )

    st.title("🎛️ TribeXR Visuals Toolkit v0.01 ⚡🎨✨")
    st.markdown("""
    Professional visual sequence generator for [TribeXR](https://www.tribexr.com) performances and events 🎧
    
    ✨ NEW: Improved image processing and transitions! 
    
    ⚡ Tips for best results:
    - Upload JPG or PNG images 📸
    - Maximum file size: 200MB total 💾
    - Recommended: 5-10 images for optimal processing time ⚡
    """)

    # Initialize session state
    if 'generator' not in st.session_state:
        st.session_state.generator = SlideshowGenerator()

    uploaded_files = st.file_uploader(
        "Upload Images 🎬",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Select multiple images to create your sequence"
    )

    if uploaded_files:
        total_size = sum([file.size for file in uploaded_files])
        if total_size > 200 * 1024 * 1024:  # 200MB
            st.warning("⚠️ Total file size exceeds 200MB. This may cause issues in the cloud environment.")

        st.write(f"Number of images uploaded: {len(uploaded_files)}")

        with st.form("video_settings"):
            st.subheader("Sequence Settings 🎛️")
            
            col1, col2 = st.columns(2)
            
            with col1:
                filename = st.text_input(
                    "Video Name 📝",
                    value="my_slideshow",
                    help="Enter a name for your video file"
                )
                image_duration = st.slider(
                    "Image Duration ⏱️",
                    min_value=1.0,
                    max_value=30.0,
                    value=15.0,
                    step=0.5,
                    help="How long each image is displayed"
                )
                transition_type = st.selectbox(
                    "Transition Type 🎭",
                    options=['crossfade', 'fade_black'],
                    format_func=lambda x: "Crossfade" if x == "crossfade" else "Fade to Black",
                    help="Choose the transition effect between images"
                )

            with col2:
                quality = st.selectbox(
                    "Quality 🎥",
                    options=[
                        '350k',
                        '500k',
                        '750k',
                        '1000k'
                    ],
                    format_func=lambda x: {
                        '350k': 'Ultra Light (350k)',
                        '500k': 'Light (500k)',
                        '750k': 'Standard (750k)',
                        '1000k': 'High (1000k)'
                    }[x],
                    help="Higher quality = larger file size"
                )
                
                resolution_options = {
                    'Square 1024x1024 (from 1024x512)': (1024, 512, 'anamorphic'),
                    'Square 2048x2048 (from 2048x1024)': (2048, 1024, 'anamorphic'),
                    'Square 512x512': (512, 512, 'square'),
                    'Square 1024x1024': (1024, 1024, 'square'),
                    'Square 2048x2048': (2048, 2048, 'square')
                }
                
                resolution = st.selectbox(
                    "Resolution 📐",
                    options=list(resolution_options.keys()),
                    help="Select output resolution"
                )

                transition_duration = st.slider(
                    "Transition Duration 🔄",
                    min_value=0.0,
                    max_value=10.0,
                    value=3.0,
                    step=0.25,
                    help="Duration of transition effect between images"
                )

            randomize = st.checkbox(
                "Randomize Images 🎲",
                value=True,
                help="Randomly shuffle the order of images"
            )
            
            generate_button = st.form_submit_button(
                "Generate Sequence 🎛️",
                help="Click to create your video"
            )

            if generate_button:
                try:
                    with st.spinner("Processing your images..."):
                        image_files = st.session_state.generator.process_uploaded_files(uploaded_files)
                        
                        if randomize:
                            random.shuffle(image_files)

                        settings = {
                            'filename': filename,
                            'image_duration': image_duration,
                            'transition_duration': transition_duration,
                            'transition_type': transition_type,
                            'quality': quality,
                            'resolution': resolution_options[resolution]
                        }

                        output_path = st.session_state.generator.generate_video(image_files, settings)

                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="Download Video 📥",
                                data=f,
                                file_name=f"{filename}.mp4",
                                mime="video/mp4"
                            )
                        
                        # Clean up after successful generation
                        st.session_state.generator.cleanup()
                        st.session_state.generator = SlideshowGenerator()

                except Exception as e:
                    st.error(f"Error generating video: {e}")
                    st.session_state.generator.cleanup()
                    st.session_state.generator = SlideshowGenerator()

if __name__ == "__main__":
    main()