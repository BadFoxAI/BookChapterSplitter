import streamlit as st
import os
import random
from moviepy.editor import *
import uuid
import tempfile
import warnings
from PIL import Image, ImageOps
import io
import shutil
warnings.filterwarnings('ignore', category=SyntaxWarning, module='moviepy')

class SlideshowGenerator:
    def __init__(self):
        """Initialize the slideshow generator with default settings."""
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
                # Create unique filename
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if file_extension not in ['.jpg', '.jpeg', '.png']:
                    continue
                    
                unique_filename = f"{uuid.uuid4().hex[:6]}{file_extension}"
                filepath = os.path.join(self.image_dir, unique_filename)
                
                # Optimize image before saving
                image = Image.open(uploaded_file)
                
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'P'):
                    image = image.convert('RGB')
                    
                # Resize if too large
                max_size = (2048, 2048)
                if max(image.size) > max(max_size):
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                image.save(filepath, 'JPEG', quality=85, optimize=True)
                saved_files.append(filepath)
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
        return saved_files

    def create_seamless_sequence(self, clips, transition_duration, transition_type):
        """Creates a seamless sequence with proper transitions between clips."""
        if not clips:
            raise ValueError("No clips provided")
        
        if transition_duration <= 0:
            return concatenate_videoclips(clips, method="compose")
        
        working_clips = clips + [clips[0]]
        
        if transition_type == 'crossfade':
            final_clips = []
            for i in range(len(working_clips)):
                current_clip = working_clips[i]
                start_time = i * (current_clip.duration - transition_duration)
                if i > 0:
                    current_clip = current_clip.crossfadein(transition_duration)
                current_clip = current_clip.set_start(start_time)
                final_clips.append(current_clip)
            final = CompositeVideoClip(final_clips)
        else:  # fade_black
            final_clips = []
            for i in range(len(working_clips)):
                if i < len(working_clips) - 1:
                    clip = working_clips[i]
                    clip = clip.fadeout(transition_duration/2)
                    next_clip = working_clips[i + 1].fadein(transition_duration/2)
                    
                    if i > 0:
                        clip = clip.set_start(i * clip.duration)
                    next_clip = next_clip.set_start((i * clip.duration) + clip.duration - transition_duration/2)
                    
                    final_clips.append(clip)
                    if i == len(working_clips) - 2:
                        final_clips.append(next_clip)
            final = concatenate_videoclips(final_clips, method="compose")
        
        return final

    def cleanup(self):
        """Clean up temporary files."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            st.error(f"Error cleaning up temporary files: {e}")

    def generate_video(self, image_files, settings):
        """Generate video from uploaded images with given settings."""
        if not image_files:
            raise ValueError("No images provided")

        clips = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            for idx, img_path in enumerate(image_files):
                clip = ImageClip(img_path)
                
                target_width, source_height, mode = settings['resolution']
                clip = clip.resize((target_width, source_height))
                
                if mode == 'anamorphic':
                    clip = clip.resize((target_width, target_width))
                
                clip = clip.set_duration(settings['image_duration'])
                clips.append(clip)
                
                progress = (idx + 1) / len(image_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing image {idx + 1}/{len(image_files)}")

            if not clips:
                raise ValueError("No clips were created")

            status_text.text("Creating video sequence...")
            final_video = self.create_seamless_sequence(
                clips, 
                settings['transition_duration'],
                settings['transition_type']
            )
            final_video = final_video.set_fps(24)

            output_path = os.path.join(self.output_dir, f"{settings['filename']}.mp4")

            status_text.text("Generating final video...")
            if not os.access(self.temp_dir, os.W_OK):
                raise PermissionError("No write access to temporary directory. Please try again.")
            final_video.write_videofile(
                output_path,
                codec='libx264',
                bitrate=settings['quality'],
                audio_codec=None,
                threads=2,
                preset='ultrafast',
                ffmpeg_params=[
                    '-profile:v', 'baseline',
                    '-level', '3.0',
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    '-tune', 'animation',
                    '-x264opts', 'no-cabac:ref=1:bframes=0:weightp=0:8x8dct=0:trellis=0:me=dia',
                    '-crf', '30'
                ]
            )

            return output_path

        except Exception as e:
            raise e
        finally:
            # Clean up clips
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass

def main():
    st.set_page_config(
        page_title="TribeXR Visuals Toolkit",
        page_icon="🎛️",
        layout="wide"
    )

    st.title("🎛️ TribeXR Visuals Toolkit")
    st.markdown("""
    Professional visual sequence generator for [TribeXR](https://www.tribexr.com) performances and events 🎧
    
    ⚡ Tips for best results:
    - Upload JPG or PNG images
    - Maximum file size: 200MB total
    - Recommended: 5-10 images for optimal processing time
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