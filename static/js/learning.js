document.addEventListener('DOMContentLoaded', function () {
    const subjectButtons = document.querySelectorAll('#subject-list .list-group-item');
    const topicList = document.getElementById('topic-list');
    const contentTitle = document.getElementById('content-title');
    const contentArea = document.getElementById('content-area');
    const loadingSpinner = document.getElementById('content-loading');
    const interactionSection = document.getElementById('content-interaction');
    const engagementBar = document.getElementById('engagement-bar');
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');
    const quizArea = document.getElementById('quiz-area');
    const takeQuizBtn = document.getElementById('take-quiz-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const voiceBtn = document.getElementById('voice-control-btn');
    const translateBtn = document.getElementById('translate-btn');
    const ttsToggle = document.getElementById('text-to-speech');
    const ttsAudio = document.getElementById('tts-audio');
    const audioModal = new bootstrap.Modal(document.getElementById('audio-modal'));
  
    let currentSubject = 'mathematics';
  
    const topics = {
        mathematics: ['Addition', 'Subtraction', 'Multiplication'],
        science: ['Photosynthesis', 'Electricity', 'Water Cycle', 'Plants'],
        english: ['Grammar', 'Vocabulary', 'Reading Skills'],
        socialstudies: ['History', 'Geography', 'Civics']
    };
  
    // Subject switching
    subjectButtons.forEach(button => {
        button.addEventListener('click', () => {
            subjectButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            currentSubject = button.getAttribute('data-subject');
            contentTitle.textContent = currentSubject.charAt(0).toUpperCase() + currentSubject.slice(1);
            updateTopics(currentSubject);
        });
    });
  
    // Load topics on sidebar
    function updateTopics(subject) {
        topicList.innerHTML = '';
        topics[subject].forEach(topic => {
            const btn = document.createElement('button');
            btn.classList.add('list-group-item', 'list-group-item-action');
            btn.textContent = topic;
            btn.addEventListener('click', () => loadContent(topic));
            topicList.appendChild(btn);
        });
    }
  
    // Load content from backend
    function loadContent(topic) {
        loadingSpinner.classList.remove('d-none');
        interactionSection.classList.add('d-none');
        contentTitle.textContent = topic;
  
        fetch('/generate_content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        })
        .then(response => response.json())
        .then(data => {
            loadingSpinner.classList.add('d-none');
            interactionSection.classList.remove('d-none');
            contentArea.textContent = data.content || Sorry, no content found for "${topic}".;
            
            simulateEngagement();
  
            if (ttsToggle.checked && data.content) {
                speakContent(data.content);
            }
        })
        .catch(error => {
            loadingSpinner.classList.add('d-none');
            contentArea.textContent = "Error fetching content. Please try again.";
            console.error("Error fetching content:", error);
        });
    }
  
    function performSearch(query) {
        if (!query.trim()) return;
        loadContent(query.trim());
    }
  
    searchButton.addEventListener('click', () => {
        performSearch(searchInput.value);
    });
  
    searchInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') performSearch(searchInput.value);
    });
  
    function simulateEngagement() {
        const percent = Math.floor(Math.random() * 100) + 1;
        engagementBar.style.width = percent + "%";
        engagementBar.setAttribute('aria-valuenow', percent);
    }
  
    function speakContent(text) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }
  
    takeQuizBtn.addEventListener('click', () => {
        quizArea.innerHTML = '<p class="text-center">Loading quiz...</p>';
        quizArea.classList.remove('d-none');
  
        fetch('/generate_quiz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject: currentSubject })
        })
        .then(response => response.json())
        .then(data => {
            quizArea.innerHTML = renderQuiz(data.quiz);
        })
        .catch(() => {
            quizArea.innerHTML = '<p class="text-danger">Failed to load quiz.</p>';
        });
    });
  
    function renderQuiz(questions) {
        if (!questions || questions.length === 0) return '<p>No quiz available.</p>';
        return questions.map((q, i) => `
            <div class="mb-3">
                <strong>Q${i + 1}. ${q.question}</strong>
                ${q.options.map(opt => `
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="q${i}" value="${opt}">
                        <label class="form-check-label">${opt}</label>
                    </div>`).join('')}
            </div>
        `).join('');
    }
  
    logoutBtn.addEventListener('click', () => {
        window.location.href = "/logout";
    });
  
    voiceBtn.addEventListener('click', () => {
      const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
  
      recognition.start();
      voiceBtn.innerText = "🎙 Listening...";
  
      recognition.onresult = function (event) {
        const speechResult = event.results[0][0].transcript;
        console.log("Recognized Speech:", speechResult);
  
        voiceBtn.innerText = "🎤 Voice Control";
  
        searchInput.value = speechResult;
        performSearch(speechResult);
      };
  
      recognition.onerror = function (event) {
        console.error("Speech recognition error:", event.error);
        voiceBtn.innerText = "🎤 Voice Control";
        alert("Voice recognition failed. Please try again.");
      };
    });
    const ttsButton = document.getElementById('text-to-speech-btn');
  
    ttsButton.addEventListener('click', () => {
        const text = contentArea.textContent.trim();
        if (text) {
            speakContent(text);
        } else {
            alert("No content to read.");
        }
    });
    
    // Optional Pause/Resume/Stop controls:
    document.getElementById('pause-tts-btn')?.addEventListener('click', () => {
        window.speechSynthesis.pause();
    });
    
    document.getElementById('resume-tts-btn')?.addEventListener('click', () => {
        window.speechSynthesis.resume();
    });
    
    document.getElementById('stop-tts-btn')?.addEventListener('click', () => {
        window.speechSynthesis.cancel();
    });
    
    // Translate placeholder
    translateBtn.addEventListener('click', () => {
        const text = contentArea.textContent.trim();
        if (!text) {
            alert("No content to translate");
            return;
        }
        
        const targetLang = prompt("Enter language (English, Hindi, Telugu, etc):");
        if (!targetLang) return;
        
        translateBtn.innerHTML = <i class="bi bi-translate text-primary"></i> Translating...;
        
        fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                language: targetLang.toLowerCase()
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(HTTP error! Status: ${response.status});
            }
            return response.json();
        })
        .then(data => {
            console.log("Translation response:", data); // Debug output
            
            if (data.translated) {
                contentArea.textContent = data.translated;
                translateBtn.innerHTML = <i class="bi bi-translate"></i> Translated;
                
                // Optional: TTS after translation
                if (document.getElementById('text-to-speech').checked) {
                    const utterance = new SpeechSynthesisUtterance(data.translated);
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(utterance);
                }
            } else if (data.error) {
                console.error("Translation API error:", data.error);
                alert(Translation error: ${data.error});
                translateBtn.innerHTML = <i class="bi bi-translate"></i> Translate;
            } else {
                console.error("Unexpected response format:", data);
                alert("Unexpected response from translation service");
                translateBtn.innerHTML = <i class="bi bi-translate"></i> Translate;
            }
        })
        .catch(error => {
            console.error("Translation request error:", error);
            alert(Error translating content: ${error.message});
            translateBtn.innerHTML = <i class="bi bi-translate"></i> Translate;
        });
    });
    // Initial setup
    updateTopics(currentSubject);
    loadContent('Addition');
  });
  document.getElementById("download-button").addEventListener("click", () => {
      const content = document.getElementById("content-area").innerText.trim();
    
      if (!content) {
        alert("No content to download.");
        return;
      }
    
      const blob = new Blob([content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
    
      const a = document.createElement("a");
      a.href = url;
      a.download = "generated_prompt.txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });