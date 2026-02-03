# 🎬 StreamLab — Cinema Engine v2.0

StreamLab is a Flask-based video streaming web app that streams local videos or Google Drive links directly in your browser using FFmpeg real-time transcoding.

Works on Android (Termux), Windows, Linux, and macOS.

---

## 🚀 Features

- Stream videos in browser without downloading
- Accept local video file path
- Accept Google Drive public video links
- Live conversion using FFmpeg
- Simple web UI with Flask

---

## 📁 Project Files

- `app.py` — Main Flask server
- `requirements.txt` — Python dependencies
- `templates/` — HTML frontend
- `.gitignore`

---

## ⚙️ Requirements (All Platforms)

You must have:

- Python 3.7+
- FFmpeg
- Git
- Internet (for Drive links)

---

# 💻 Desktop Setup (Windows / Linux / Mac)

### Clone Repository

git clone https://github.com/Sourav1138/StreamLab.git  
cd StreamLab

### Install FFmpeg

Linux:
sudo apt install ffmpeg

Mac:
brew install ffmpeg

Windows:
Download FFmpeg and add to PATH

Check:
ffmpeg -version

### Create Virtual Environment (Recommended)

python -m venv venv

Activate:

Windows:
venv\Scripts\activate

Linux/Mac:
source venv/bin/activate

### Install Python Packages

pip install -r requirements.txt

### Run Server

python app.py

Open browser:
http://127.0.0.1:5000

---

# 📱 Android Setup (Termux) — Recommended Way

> If you face Termux problems, report at: https://termux.dev/issues

### 1️⃣ Install Required Packages

pkg update && pkg upgrade -y  
pkg install git python ffmpeg -y

### 2️⃣ Clone the Repository

git clone https://github.com/Sourav1138/StreamLab.git

cd StreamLab

### 3️⃣ Create Virtual Environment (Important)

python -m venv venv

Activate it:

source venv/bin/activate

### 4️⃣ Install Dependencies

pip install --upgrade pip  
pip install -r requirements.txt

### 5️⃣ Run the App

python app.py

### 6️⃣ Open in Android Browser (Chrome)

http://127.0.0.1:5000

---

## ▶️ How To Use

1. Open the webpage
2. Paste local video path or Google Drive link
3. Click Play
4. Video streams in browser

---

## 🛠 Troubleshooting

FFmpeg error → check ffmpeg installation with `ffmpeg -version`  
Module error → activate venv and reinstall requirements  
Video not playing → check file path or Drive permission  
Slow streaming → device CPU limitation

---

## 🧠 Tech Used

Python, Flask, FFmpeg, HTML5 Video

---

## 👤 Author

Sourav Kumar  
https://github.com/Sourav1138
