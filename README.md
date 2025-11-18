# 🎥 Faculty Class Recording System

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![React](https://img.shields.io/badge/React-18.0+-61dafb.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red.svg)
![Whisper](https://img.shields.io/badge/Whisper-OpenAI-green.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An intelligent automated class recording system that captures audio-visual lectures, performs **speech-to-text transcription** using Whisper, generates **GPT-powered summaries**, and enables natural language search for past lectures. Built for educational institutions to enhance learning accessibility and archival.

## 🎯 Key Features

- **Automated Recording**: Capture video + audio lectures automatically
- **Face + Audio Detection**: Smart recording triggered by faculty presence
- **Speech-to-Text**: OpenAI Whisper for accurate transcription
- **AI Summarization**: GPT-powered lecture summaries and key points
- **Natural Language Search**: "Find lectures about machine learning"
- **Multi-format Support**: MP4 video, audio extraction, SRT subtitles
- **Cloud Storage Integration**: AWS S3 / Google Drive backup
- **Faculty Dashboard**: Manage, edit, and share recordings
- **Student Portal**: Search and access lecture archives

## 🏗️ Architecture

```
Camera/Mic → Face Detection → Recording → Whisper Transcription → GPT Summary → Storage + Search
```

### Workflow:
1. **Detection**: Faculty enters classroom → Face + audio detection activated
2. **Recording**: Capture HD video + clear audio
3. **Transcription**: Whisper converts speech to text with timestamps
4. **Summarization**: GPT generates lecture summary and key points
5. **Indexing**: Store in database with searchable metadata
6. **Search**: Natural language queries retrieve relevant lectures

## 💻 Tech Stack

### Backend
- **Python 3.8+**
- **Flask** - RESTful API server
- **OpenCV** - Video processing and face detection
- **PyAudio** - Audio capture
- **OpenAI Whisper** - Speech-to-text transcription
- **OpenAI GPT-4** - Lecture summarization
- **FFmpeg** - Video/audio processing
- **PostgreSQL** - Database for lecture metadata
- **AWS S3 / Google Drive API** - Cloud storage

### Frontend
- **React 18** with Hooks
- **Video.js** - Video player
- **Axios** - HTTP client
- **TailwindCSS** - Modern styling
- **Lucide React** - Icons

## 📦 Installation

### Prerequisites

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y ffmpeg portaudio19-dev python3-pyaudio

# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib
```

### Backend Setup

```bash
# Clone repository
git clone https://github.com/udaykumar1307/faculty-class-recording.git
cd faculty-class-recording

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_db.py

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## 🗄️ Database Setup

```sql
CREATE DATABASE class_recordings;

CREATE TABLE recordings (
    id SERIAL PRIMARY KEY,
    faculty_id VARCHAR(50),
    faculty_name VARCHAR(100),
    subject VARCHAR(100),
    date DATE,
    start_time TIME,
    end_time TIME,
    duration INT,
    video_path VARCHAR(255),
    audio_path VARCHAR(255),
    transcript_path VARCHAR(255),
    summary TEXT,
    key_points TEXT[],
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transcripts (
    id SERIAL PRIMARY KEY,
    recording_id INT REFERENCES recordings(id),
    timestamp_start FLOAT,
    timestamp_end FLOAT,
    text TEXT,
    confidence FLOAT
);

CREATE INDEX idx_recording_date ON recordings(date);
CREATE INDEX idx_recording_faculty ON recordings(faculty_id);
CREATE INDEX idx_transcript_recording ON transcripts(recording_id);
```

## 🚀 Usage

### Start Backend Server
```bash
python app.py
# Server runs on http://localhost:5000
```

### Start Frontend
```bash
cd frontend
npm start
# App runs on http://localhost:3000
```

## 📁 Project Structure

```
faculty-class-recording/
├── app.py                    # Flask backend server
├── recorder.py               # Recording logic
├── transcription.py          # Whisper integration
├── summarizer.py             # GPT summarization
├── database.py               # PostgreSQL operations
├── setup_db.py               # Database initialization
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .gitignore
├── README.md
├── recordings/              # Stored video files
├── transcripts/             # Transcript files
└── frontend/
    ├── package.json
    ├── public/
    └── src/
        ├── App.js
        ├── components/
        │   ├── RecordingControl.js
        │   ├── LectureSearch.js
        │   ├── VideoPlayer.js
        │   └── Dashboard.js
        ├── App.css
        └── index.js
```

## 🔧 API Endpoints

### POST /start-recording
Start new lecture recording
- **Request**: `{"faculty_id": "F001", "subject": "Machine Learning"}`
- **Response**: `{"recording_id": 123, "status": "recording"}`

### POST /stop-recording
Stop current recording
- **Request**: `{"recording_id": 123}`
- **Response**: `{"status": "processing", "duration": 3600}`

### POST /transcribe/:id
Transcribe recorded lecture
- **Response**: `{"transcript": "...", "status": "completed"}`

### POST /summarize/:id
Generate lecture summary
- **Response**: `{"summary": "...", "key_points": [...]}`

### GET /recordings
Get all recordings with filters
- **Query**: `?faculty_id=F001&subject=ML&date=2025-01-15`
- **Response**: `{"recordings": [...]}`

### POST /search
Natural language search
- **Request**: `{"query": "lectures about neural networks"}`
- **Response**: `{"results": [...]}`

### GET /recording/:id
Get specific recording details
- **Response**: `{"id": 123, "video_url": "...", "transcript": "..."}`

### DELETE /recording/:id
Delete recording and associated files
- **Response**: `{"message": "Recording deleted"}`

## 🎓 Features in Detail

### 1. Automated Recording
- Motion detection using OpenCV
- Audio level monitoring for speech detection
- Auto-start when faculty enters
- Auto-stop after 5 minutes of silence

### 2. Speech-to-Text (Whisper)
- High accuracy transcription (95%+)
- Timestamp alignment
- Speaker diarization support
- Multi-language support (English, Hindi, etc.)

### 3. AI Summarization (GPT-4)
```python
# Generate structured summaries
{
  "summary": "This lecture covered neural networks...",
  "key_points": [
    "Introduction to backpropagation",
    "Activation functions explained",
    "Practical implementation in PyTorch"
  ],
  "topics": ["Neural Networks", "Deep Learning"],
  "difficulty": "Intermediate"
}
```

### 4. Natural Language Search
```
Query: "Show me lectures about convolutional neural networks from last week"
Results: 3 lectures found with relevance scores
```

## 📊 Performance Metrics

- **Recording Quality**: 1080p HD @ 30fps
- **Transcription Accuracy**: 95%+ (Whisper large model)
- **Processing Time**: ~10 minutes for 1-hour lecture
- **Storage**: ~500MB per hour (H.264 compressed)
- **Search Speed**: <500ms for complex queries

## 🔒 Security & Privacy

- **Access Control**: Role-based permissions (Admin, Faculty, Student)
- **Data Encryption**: AES-256 for stored videos
- **GDPR Compliance**: Data retention policies and deletion
- **Audit Logs**: Track all access and modifications
- **Secure Streaming**: Token-based video access

## 🤝 Use Cases

- **Universities**: Lecture archival and accessibility
- **Online Education**: Course content creation
- **Corporate Training**: Meeting recordings and documentation
- **Research**: Seminar and conference recordings
- **Accessibility**: Auto-subtitles for hearing impaired

## 🎯 Faculty Features

- **Schedule Recordings**: Set automatic recording times
- **Edit Transcripts**: Correct any transcription errors
- **Add Annotations**: Insert notes at specific timestamps
- **Share Lectures**: Generate shareable links
- **Analytics**: View student engagement metrics

## 📱 Student Features

- **Browse Lectures**: Filter by subject, date, faculty
- **Smart Search**: Natural language queries
- **Watch with Subtitles**: Auto-generated captions
- **Take Notes**: Timestamp-linked notes
- **Download**: Offline viewing support

## 🔮 Future Enhancements

- [ ] Real-time live streaming during lectures
- [ ] AI-generated quiz questions from lectures
- [ ] Automatic slide extraction and OCR
- [ ] Multi-camera angle support
- [ ] Integration with LMS (Moodle, Canvas)
- [ ] Mobile app for iOS and Android
- [ ] Gesture recognition for slide navigation
- [ ] Emotion analytics for engagement tracking

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=class_recordings
DB_USER=postgres
DB_PASSWORD=your_password

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Recording Settings
VIDEO_RESOLUTION=1920x1080
VIDEO_FPS=30
AUDIO_SAMPLE_RATE=44100
RECORDING_FORMAT=mp4

# Storage
STORAGE_PATH=./recordings
CLOUD_STORAGE=s3  # or 'gdrive'
AWS_BUCKET=your-s3-bucket
AWS_REGION=us-east-1

# Application
FLASK_ENV=production
SECRET_KEY=your_secret_key
```

## 📈 System Requirements

### Server
- **CPU**: 4+ cores (Intel i5 or better)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 500GB+ SSD for recordings
- **Network**: 100Mbps+ for streaming

### Client
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+
- **Internet**: 5Mbps+ for HD playback

## 🎓 Technical Implementation

### Recording Pipeline
```python
1. Detect faculty presence (face detection)
2. Start video + audio capture
3. Store frames in buffer
4. Encode to H.264 (GPU accelerated)
5. Save to disk with metadata
```

### Transcription Pipeline
```python
1. Extract audio from video (FFmpeg)
2. Load Whisper model (base/medium/large)
3. Process audio in chunks
4. Generate timestamps
5. Save as SRT and JSON
```

### Search System
```python
1. User query → Embedding (OpenAI)
2. Semantic search in transcript database
3. Rank by relevance score
4. Return top matches with context
```

## 👨‍💻 Author

**Uday Kumar Badugu**
- Email: uday19c61a0401@gmail.com
- Location: Hyderabad, India
- GitHub: [@udaykumar1307](https://github.com/udaykumar1307)
- Experience: 2 years at Adiverse Technology building production ML systems

## 📄 License

MIT License - Free for educational and commercial use

## 🙏 Acknowledgments

- OpenAI for Whisper and GPT models
- OpenCV community
- FFmpeg project
- React and Flask communities
- PostgreSQL team

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Email: uday19c61a0401@gmail.com

---

⭐ **Star this repo if you find it helpful!**

## 🔗 Related Projects

Check out my other AI/ML projects:
1. [PDF Q&A Chatbot (RAG + FAISS)](https://github.com/udaykumar1307/pdf-qa-chatbot-rag-faiss)
2. [Face Recognition Attendance](https://github.com/udaykumar1307/face-recognition-attendance)
3. [Fish Disease Classifier](https://github.com/udaykumar1307/fish-disease-classifier)
