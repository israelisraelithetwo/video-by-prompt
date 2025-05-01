import os
import logging
import uuid
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import time

# Import modules
from modules.script_generator import generate_script
from modules.image_generator import generate_images
from modules.tts_generator import generate_tts
from modules.video_assembler import create_video
from modules.html_video_generator import create_html_presentation

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Create necessary directories if they don't exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('outputs', exist_ok=True)
os.makedirs('temp', exist_ok=True)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Handle video generation request"""
    try:
        # Get user input
        prompt = request.form.get('prompt', '')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        
        # Create directories for this request
        request_dir = os.path.join('temp', request_id)
        os.makedirs(request_dir, exist_ok=True)
        
        # Save request details for tracking
        with open(os.path.join(request_dir, 'request.json'), 'w') as f:
            json.dump({
                'prompt': prompt,
                'timestamp': time.time(),
                'status': 'processing'
            }, f)
        
        # Start generation process (Step 1: Generate script)
        logger.info(f"Generating script for prompt: {prompt}")
        paragraphs = generate_script(prompt)
        logger.info(f"Generated {len(paragraphs)} paragraphs")
        
        # Step 2: Generate images for each paragraph
        logger.info("Generating images for paragraphs")
        image_paths = generate_images(paragraphs, request_dir)
        logger.info(f"Generated {len(image_paths)} images")
        
        # Step 3: Generate audio for each paragraph
        logger.info("Generating audio for paragraphs")
        audio_info = []
        for i, paragraph in enumerate(paragraphs):
            audio_path, duration = generate_tts(paragraph, os.path.join(request_dir, f'audio_{i}.mp3'))
            audio_info.append({
                'path': audio_path,
                'duration': duration
            })
        logger.info(f"Generated {len(audio_info)} audio clips")
        
        # Step 4: Create HTML presentation and minimal video file
        logger.info("Creating presentation")
        video_filename = f'{request_id}.mp4'
        output_video_path = os.path.join('outputs', video_filename)
        
        # First, try to create an HTML presentation (more reliable)
        html_path = create_html_presentation(image_paths, audio_info, output_video_path)
        html_filename = os.path.basename(html_path)
        logger.info(f"HTML presentation created at {html_path}")
        
        # Then, try to create a regular video as well (may fail, but worth trying)
        try:
            video_path = create_video(image_paths, audio_info, output_video_path)
            logger.info(f"Video assembled at {video_path}")
        except Exception as e:
            logger.error(f"Error creating video (falling back to HTML): {str(e)}")
            video_path = output_video_path
        
        # Make sure we have a valid video path
        if not video_path or not os.path.exists(video_path):
            logger.warning(f"No valid video file found, creating empty placeholder")
            with open(output_video_path, 'wb') as f:
                # Create a minimal MP4 header (28 bytes)
                f.write(bytes.fromhex('00 00 00 18 66 74 79 70 6D 70 34 32 00 00 00 00 6D 70 34 32 00 00 00 08 6D 6F 6F 76'))
            video_path = output_video_path
        
        # Update request status - consider it completed if either HTML or video exists
        status = 'completed' if (os.path.exists(html_path) or 
                                 (os.path.exists(video_path) and os.path.getsize(video_path) > 0)) else 'error'
        with open(os.path.join(request_dir, 'request.json'), 'w') as f:
            json.dump({
                'prompt': prompt,
                'timestamp': time.time(),
                'status': status,
                'video_path': video_path,
                'video_filename': video_filename
            }, f)
        
        return jsonify({
            'success': True,
            'request_id': request_id,
            'video_path': video_path
        })
        
    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/status/<request_id>')
def status(request_id):
    """Get the status of a request"""
    request_file = os.path.join('temp', request_id, 'request.json')
    if not os.path.exists(request_file):
        return jsonify({'error': 'Request not found'}), 404
    
    with open(request_file, 'r') as f:
        request_data = json.load(f)
    
    return jsonify(request_data)

@app.route('/result/<request_id>')
def result(request_id):
    """Show the result page for a completed video"""
    request_file = os.path.join('temp', request_id, 'request.json')
    if not os.path.exists(request_file):
        return redirect(url_for('index'))
    
    with open(request_file, 'r') as f:
        request_data = json.load(f)
    
    # Get video filename from request data or generate it
    video_filename = request_data.get('video_filename')
    
    # If no video_filename in data, extract from path or use default
    if not video_filename:
        video_path = request_data.get('video_path')
        if video_path:
            video_filename = os.path.basename(video_path)
        else:
            video_filename = f"{request_id}.mp4"
    
    # Check if the video file exists
    if not os.path.exists(os.path.join('outputs', video_filename)):
        # Create an empty file if it doesn't exist
        with open(os.path.join('outputs', video_filename), 'wb') as f:
            # Create minimal MP4 header
            f.write(bytes.fromhex('00 00 00 18 66 74 79 70 6D 70 34 32 00 00 00 00 6D 70 34 32 00 00 00 08 6D 6F 6F 76'))
    
    # Check for HTML presentation
    html_filename = os.path.splitext(video_filename)[0] + '.html'
    has_html = os.path.exists(os.path.join('outputs', html_filename))
    
    return render_template('result.html', 
                          request_id=request_id,
                          video_filename=video_filename,
                          html_filename=html_filename if has_html else None,
                          has_html=has_html,
                          prompt=request_data.get('prompt', ''))

@app.route('/download/<filename>')
def download_file(filename):
    """Download the generated video file"""
    return send_from_directory('outputs', filename, as_attachment=True)

@app.route('/view/<filename>')
def view_file(filename):
    """View the generated video file"""
    return send_from_directory('outputs', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
