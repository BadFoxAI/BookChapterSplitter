import streamlit as st
import os
import random
import uuid
import tempfile
from PIL import Image
import shutil
import numpy as np
import imageio

class SlideshowGenerator:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.image_dir = os.path.join(self.temp_dir, 'images')
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def process_uploaded_files(self, uploaded_files):
        """Process uploaded files and save them to the temporary directory."""
        saved_files = []
        for uploaded_file in uploaded_files:
            try:
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if file_extension not in ['.jpg', '.jpeg', '.png']:
                    continue
                    
                unique_filename = f"{uuid.uuid4().hex[:6]}{file_extension}"
                filepath = os.path.join(self.image_dir, unique_filename)
                
                # Process image
                image = Image.open(uploaded_file)
                if image.mode in ('RGBA', 'P'):
                    image = image.convert('RGB')
                
                # Save processed image
                image.save(filepath, 'JPEG', quality=95)
                saved_files.append(filepath)
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
        return saved_files

    def cleanup(self):
        """Clean up temporary files."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            st.error(f"Error cleaning up: {e}")

    def generate_video(self, image_files, settings):
        if not image_files:
            raise ValueError("No images provided")

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            writer = imageio.get_writer(
                os.path.join(self.output_dir, f"{settings['filename']}.mp4"),
                fps=24,
                codec='h264',
                quality=8  # 0-10, where 10 is highest quality
            )

            for idx, img_path in enumerate(image_files):
                status_text.text(f"Processing image {idx + 1}/{len(image_files)} ✨")
                
                # Read and process image
                img = Image.open(img_path)
                img = img.resize((1024, 512), Image.Resampling.LANCZOS)
                img = np.array(img)
                
                # Write frames for duration
                frames_per_image = int(24 * settings['image_duration'])  # 24 fps
                for _ in range(frames_per_image):
                    writer.append_data(img)
                
                progress = (idx + 1) / len(image_files)
                progress_bar.progress(progress)

            writer.close()
            return os.path.join(self.output_dir, f"{settings['filename']}.mp4")

        except Exception as e:
            raise e

def main():
    st.set_page_config(
        page_title="Visual Sequence Generator",
        page_icon="🎨",
        layout="wide"
    )

    st.title("🎨 Visual Sequence Generator v0.02 ✨")
    
    st.markdown("""
    ### Create stunning visual sequences for your performances and events 🎭
    
    ⚡ Tips for best results:
    - Upload JPG or PNG images 📸
    - Maximum file size: 200MB total 💾
    - Recommended: 5-10 images for optimal processing time ⚡
    """)

    st.write("")  # Add some spacing
    
    if 'generator' not in st.session_state:
        st.session_state.generator = SlideshowGenerator()

    uploaded_files = st.file_uploader(
        "Upload Your Images 🎬",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Select multiple images to create your sequence"
    )

    if uploaded_files:
        st.write("")  # Add spacing
        total_size = sum([file.size for file in uploaded_files])
        if total_size > 200 * 1024 * 1024:
            st.warning("⚠️ Total file size exceeds 200MB. This may cause issues in the cloud environment.")

        st.write(f"📁 Number of images uploaded: {len(uploaded_files)}")
        st.write("")  # Add spacing

        with st.form("video_settings"):
            st.header("Sequence Settings 🎛️")
            st.write("")  # Add spacing
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                filename = st.text_input(
                    "Video Name 📝",
                    value="my_sequence",
                    help="Enter a name for your video file"
                )
                st.write("")  # Add spacing

            with col2:
                image_duration = st.slider(
                    "Image Duration ⏱️",
                    min_value=1.0,
                    max_value=30.0,
                    value=15.0,
                    step=0.5,
                    help="How long each image is displayed"
                )
                st.write("")  # Add spacing

            with col3:
                quality = st.selectbox(
                    "Video Quality 🎥",
                    options=[
                        '350k',
                        '500k',
                        '750k',
                        '1000k'
                    ],
                    format_func=lambda x: {
                        '350k': 'Light (350k)',
                        '500k': 'Standard (500k)',
                        '750k': 'High (750k)',
                        '1000k': 'Ultra (1000k)'
                    }[x],
                    help="Higher quality = larger file size"
                )

            st.write("")  # Add spacing
            randomize = st.checkbox(
                "Randomize Image Order 🎲",
                value=True,
                help="Randomly shuffle the order of images"
            )
            
            st.write("")  # Add spacing
            generate_button = st.form_submit_button(
                "Generate Sequence 🎬",
                help="Click to create your video",
                use_container_width=True
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
                            'quality': quality,
                        }

                        output_path = st.session_state.generator.generate_video(image_files, settings)

                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="Download Video 📥",
                                data=f,
                                file_name=f"{filename}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                        
                        st.session_state.generator.cleanup()
                        st.session_state.generator = SlideshowGenerator()

                except Exception as e:
                    st.error(f"Error generating video: {e}")
                    st.session_state.generator.cleanup()
                    st.session_state.generator = SlideshowGenerator()

if __name__ == "__main__":
    main()