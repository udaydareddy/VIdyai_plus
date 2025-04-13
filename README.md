# VIdyai_plus
# 🎓 VidyAI++ – Multilingual AI Tutoring & Mentorship Platform for BPL Government School Students

![VidyAI++ Banner](./screenshots/banner.png)

**Empowering India's underprivileged students with AI-driven, personalized, and inclusive education in their native languages.**

---

## 📌 Overview

**VidyAI++** is a multilingual, AI-powered tutoring and mentorship web platform designed to assist underprivileged (BPL) students in Indian government schools. Aligned with the **National Education Policy (NEP)**, it provides a personalized, gamified, and inclusive learning environment that supports regional languages, learning styles, and limited internet connectivity.

---

## 🧠 Core Features

### 🌐 Multilingual AI Tutoring
- Uses GPT/Gemini APIs to generate real-time lessons and quizzes in **multiple Indian languages**.
- Offers **text-to-speech** and **speech-to-text** for accessibility.
- Customizes content based on regional syllabus and class level.

### 🧩 Adaptive Learning Engine
- Detects student struggles and adjusts lesson difficulty using **reinforcement learning**.
- Provides on-demand support via **explainer videos**, **hints**, and **alternate strategies**.

### 🧑‍🏫 AI Mentor Matchmaking
- Matches students with local/virtual mentors using an ML model.
- Considers emotional state, subject need, availability, and language compatibility.

### 👁️ Persona Intelligence Engine
- Detects learning styles (visual, auditory, kinesthetic).
- Adapts lesson delivery format accordingly.

### 🕹️ Gamified Learning Experience
- Skill heatmaps, digital badges, micro-certifications, and streaks to boost motivation.

### 🌐 Offline-First Architecture
- PWA-based design to work seamlessly in **low/no internet zones**.
- AI inference handled on-device using **TensorFlow Lite**.

### 🔊 Zero Literacy Barrier Interface
- Voice navigation and large visual cues.
- Speech-based interaction for students/parents with reading challenges.

> ⚠️ *Webcam-based emotion detection and eye tracking for learning level estimation is under development.*

---

## 🧰 Tech Stack

| Layer         | Tools & Frameworks                                           |
|---------------|--------------------------------------------------------------|
| **Frontend**  | React.js, Tailwind CSS, Progressive Web App (PWA)            |
| **Backend**   | Node.js, Express.js                                          |
| **Database**  | MongoDB Atlas                                                |
| **AI/ML**     | OpenAI GPT / Gemini API, TensorFlow Lite, Scikit-learn       |
| **Speech**    | Google Text-to-Speech, Web Speech API, IndicTrans            |
| **Gamification** | Custom engine for rewards, badges, streaks               |
| **Mentorship** | Custom ML model (Logistic Regression + KNN)                |
| **Deployment**| Vercel (Frontend), Render/Railway (Backend), MongoDB Atlas   |

---

## 🖼️ Screenshots

> Add your actual screenshots in the `/screenshots` folder and reference them below.

### 📚 Multilingual Tutoring
![Multilingual Tutoring](./screenshots/multilingual.png)

### 🔧 Adaptive Content Engine
![Adaptive Engine](./screenshots/adaptive.png)

### 🧑‍🏫 Mentor Matchmaking
![Mentorship](./screenshots/mentorship.png)

### 🎮 Gamified Learning Dashboard
![Gamification](./screenshots/gamification.png)

### 🌐 Offline Mode
![Offline Mode](./screenshots/offline.png)

### 🎙️ Voice Interface
![Voice Interface](./screenshots/voice.png)

---

## 🛠️ How to Run Locally

### Prerequisites
- Node.js (v16+)
- MongoDB (cloud/local)
- OpenAI API Key or Gemini API key

### Clone the Repo

```bash
git clone https://github.com/yourusername/VidyAI-PlusPlus.git
cd VidyAI-PlusPlus
