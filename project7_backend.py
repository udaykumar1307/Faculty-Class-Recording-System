import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import threading
from datetime import datetime, date
from database import Database
from dotenv import load_dotenv
import subprocess
import whisper
import openai

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
RECORDINGS_FOLDER = 'recordings'
TRANSCRIPTS_FOLDER = 'transcripts'
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPTS_FOLDER, exist_ok=True)

# Global variables
recording_active = False
current_recording = None
video_writer = None
recording_thread = None

# Initialize
db = Database()
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-api-key')
whisper_model = None

def load_whisper_model():
    """Load Whisper model for transcription"""
    global whisper_model
    try:
        print("Loading Whisper model...")
        whisper_model = whisper.load_model("base")  # base, small, medium, large
        print("✅ Whisper model loaded!")
    except Exception as e:
        print(f"❌ Error loading Whisper: {e}")

# Load on startup
load_whisper_model()

class RecordingSession:
    def __init__(self, recording_id, faculty_id, subject):
        self.recording_id = recording_id
        self.faculty_id = faculty_id
        self.subject = subject
        self.start_time = datetime.now()
        self.video_path = None
        self.audio_path = None
        
def start_recording_thread(recording_id, faculty_id, subject):
    """Background thread for recording"""
    global recording_active, current_recording, video_writer
    
    try:
        # Initialize camera
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Video writer
        filename = f"{recording_id}_{faculty_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        video_path = os.path.join(RECORDINGS_FOLDER, filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, (1920, 1080))
        
        current_recording.video_path = video_path
        
        # Face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        print(f"🎥 Recording started: {filename}")
        
        while recording_active:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Face detection (optional - for presence tracking)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Draw face rectangles (optional)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            video_writer.write(frame)
        
        # Cleanup
        cap.release()
        video_writer.release()
        
        print(f"✅ Recording stopped: {filename}")
        
        # Update database
        end_time = datetime.now()
        duration = int((end_time - current_recording.start_time).total_seconds())
        
        db.update_recording_status(
            recording_id,
            'completed',
            video_path,
            duration
        )
        
    except Exception as e:
        print(f"❌ Recording error: {e}")
        recording_active = False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'message': 'Faculty Class Recording API running',
        'whisper_loaded': whisper_model is not None,
        'recording_active': recording_active
    })

@app.route('/start-recording', methods=['POST'])
def start_recording():
    """Start new recording session"""
    global recording_active, current_recording, recording_thread
    
    try:
        if recording_active:
            return jsonify({'error': 'Recording already in progress'}), 400
        
        data = request.get_json()
        faculty_id = data.get('faculty_id')
        faculty_name = data.get('faculty_name')
        subject = data.get('subject')
        
        if not faculty_id or not subject:
            return jsonify({'error': 'Faculty ID and subject required'}), 400
        
        # Create recording entry
        recording_id = db.create_recording(faculty_id, faculty_name, subject)
        
        # Initialize session
        current_recording = RecordingSession(recording_id, faculty_id, subject)
        recording_active = True
        
        # Start recording thread
        recording_thread = threading.Thread(
            target=start_recording_thread,
            args=(recording_id, faculty_id, subject)
        )
        recording_thread.start()
        
        return jsonify({
            'recording_id': recording_id,
            'status': 'recording',
            'message': 'Recording started successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    """Stop current recording"""
    global recording_active
    
    try:
        if not recording_active:
            return jsonify({'error': 'No active recording'}), 400
        
        recording_active = False
        
        # Wait for thread to finish
        if recording_thread:
            recording_thread.join(timeout=5)
        
        return jsonify({
            'status': 'stopped',
            'message': 'Recording stopped successfully',
            'recording_id': current_recording.recording_id if current_recording else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe/<int:recording_id>', methods=['POST'])
def transcribe_recording(recording_id):
    """Transcribe recorded lecture using Whisper"""
    try:
        recording = db.get_recording(recording_id)
        
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404
        
        video_path = recording['video_path']
        
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Extract audio from video
        audio_path = video_path.replace('.mp4', '.wav')
        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            audio_path, '-y'
        ], check=True, capture_output=True)
        
        # Transcribe with Whisper
        print(f"🎤 Transcribing: {recording_id}")
        result = whisper_model.transcribe(audio_path, language='en')
        
        # Save transcript
        transcript_filename = f"transcript_{recording_id}.txt"
        transcript_path = os.path.join(TRANSCRIPTS_FOLDER, transcript_filename)
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        
        # Save segments to database
        for segment in result['segments']:
            db.add_transcript_segment(
                recording_id,
                segment['start'],
                segment['end'],
                segment['text'],
                segment.get('confidence', 0.9)
            )
        
        # Update recording
        db.update_recording_transcript(recording_id, transcript_path, result['text'])
        
        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return jsonify({
            'status': 'completed',
            'transcript': result['text'],
            'segments': len(result['segments'])
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/summarize/<int:recording_id>', methods=['POST'])
def summarize_lecture(recording_id):
    """Generate lecture summary using GPT"""
    try:
        recording = db.get_recording(recording_id)
        
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404
        
        if not recording['transcript_text']:
            return jsonify({'error': 'Transcript not available. Please transcribe first.'}), 400
        
        transcript = recording['transcript_text']
        
        # Generate summary with GPT
        prompt = f"""Analyze this lecture transcript and provide:
1. A concise summary (2-3 paragraphs)
2. Key points covered (bullet points)
3. Main topics discussed
4. Difficulty level (Beginner/Intermediate/Advanced)

Transcript:
{transcript[:3000]}  # Limit for token usage
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational content analyzer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content
        
        # Extract key points (simple parsing)
        lines = summary.split('\n')
        key_points = [line.strip('- ') for line in lines if line.strip().startswith('-')]
        
        # Update database
        db.update_recording_summary(recording_id, summary, key_points)
        
        return jsonify({
            'summary': summary,
            'key_points': key_points,
            'status': 'completed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recordings', methods=['GET'])
def get_recordings():
    """Get all recordings with filters"""
    try:
        faculty_id = request.args.get('faculty_id')
        subject = request.args.get('subject')
        date_str = request.args.get('date')
        
        recordings = db.get_recordings(faculty_id, subject, date_str)
        
        return jsonify({
            'total': len(recordings),
            'recordings': recordings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recording/<int:recording_id>', methods=['GET'])
def get_recording(recording_id):
    """Get specific recording details"""
    try:
        recording = db.get_recording(recording_id)
        
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404
        
        # Get transcript segments
        segments = db.get_transcript_segments(recording_id)
        recording['transcript_segments'] = segments
        
        return jsonify(recording), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search_lectures():
    """Natural language search in lectures"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        # Simple keyword search (can be enhanced with semantic search)
        results = db.search_recordings(query)
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recording/<int:recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    """Delete recording and files"""
    try:
        recording = db.get_recording(recording_id)
        
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404
        
        # Delete files
        if recording['video_path'] and os.path.exists(recording['video_path']):
            os.remove(recording['video_path'])
        
        if recording['transcript_path'] and os.path.exists(recording['transcript_path']):
            os.remove(recording['transcript_path'])
        
        # Delete from database
        db.delete_recording(recording_id)
        
        return jsonify({'message': 'Recording deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/video/<int:recording_id>', methods=['GET'])
def stream_video(recording_id):
    """Stream video file"""
    try:
        recording = db.get_recording(recording_id)
        
        if not recording or not recording['video_path']:
            return jsonify({'error': 'Video not found'}), 404
        
        return send_file(recording['video_path'], mimetype='video/mp4')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🎥 Faculty Class Recording System")
    print("=" * 60)
    print(f"📡 API: http://localhost:5000")
    print(f"🎤 Whisper: {'Loaded ✅' if whisper_model else 'Not Loaded ❌'}")
    print(f"🗄️  Database: {'Connected ✅' if db.test_connection() else 'Disconnected ❌'}")
    print(f"📁 Recordings: {RECORDINGS_FOLDER}")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)