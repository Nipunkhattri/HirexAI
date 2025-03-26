# AI Interview Platform  

## 🚀 Overview  
The **AI Interview Platform** is an advanced AI-powered interview system that dynamically generates interview questions based on the user's resume and evaluates responses in real-time. The system integrates **Deepgram's Speech-to-Text (STT) model** to transcribe recorded answers accurately. Additionally, it incorporates **cheating detection** mechanisms, including **multi-face detection, object detection (phone), and eye tracking**, using **CNN and YOLO models** to ensure interview integrity. After completing the interview, users receive a **detailed performance analysis** with insights on **score, question-wise evaluation, cheating detection, and skill-based knowledge assessment** via an interactive dashboard.  

## ✨ Features  
- 🔐 **User Authentication:** Secure login and resume upload.  
- 📝 **AI-Powered Interview Generation:** Generates domain-specific interview questions dynamically.  
- 🎙️ **Live Answer Recording:** Users can record their responses in real-time using Deepgram (STT Model).  
- 🔍 **Cheating Detection:**  
  - Multi-face detection  
  - Object detection (phone)  
  - Eye tracking using CNN & YOLO  
- 📊 **Detailed Analysis Dashboard:**  
  - Interview score  
  - Question-wise performance  
  - Cheating detection insights  
  - Skill-based knowledge evaluation  

## 🏗️ Tech Stack  
- **Backend:** FastAPI
- **AI Models:** YOLO, CNN, OpenAI  
- **Database:** MongoDB  
- **Frontend:** React.js

## 🔧 Installation  

### 1️⃣ Clone the Repository  
```sh
git clone https://github.com/Nipunkhattri/HirexAI
cd HirexAI
```

### 2️⃣ Create a Virtual Environment
```sh
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```

### 3️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 4️⃣ Run the Backend Server
```sh
uvicorn app:app --reload
```
