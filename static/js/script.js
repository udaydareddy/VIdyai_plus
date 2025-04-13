document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const setupScreen = document.getElementById('setup-screen');
    const quizScreen = document.getElementById('quiz-screen');
    const resultsScreen = document.getElementById('results-screen');
    const loadingElement = document.getElementById('loading');
    const loadingRecommendations = document.getElementById('loading-recommendations');
    
    const classSelect = document.getElementById('class-select');
    const subjectSelect = document.getElementById('subject-select');
    const difficultySelect = document.getElementById('difficulty-select');
    const startQuizBtn = document.getElementById('start-quiz-btn');
    const newQuizBtn = document.getElementById('new-quiz-btn');
    
    const subjectHeader = document.getElementById('subject-header');
    const classInfo = document.getElementById('class-info');
    const difficultyInfo = document.getElementById('difficulty-info');
    const questionCounter = document.getElementById('question-counter');
    const questionText = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');
    
    const feedbackContainer = document.getElementById('feedback-container');
    const feedbackResult = document.getElementById('feedback-result');
    const feedbackExplanation = document.getElementById('feedback-explanation');
    const nextBtn = document.getElementById('next-btn');
    
    const finalScore = document.getElementById('final-score');
    const scoreMessage = document.getElementById('score-message');
    const recommendationsContainer = document.getElementById('recommendations-container');
    
    const youtubeRecommendations = document.getElementById('youtube-recommendations');
    const ncertRecommendations = document.getElementById('ncert-recommendations');
    const resourceRecommendations = document.getElementById('resource-recommendations');
    const tipsRecommendations = document.getElementById('tips-recommendations');
    
    // Quiz State
    let quizQuestions = [];
    let currentQuestionIndex = 0;
    let userScore = 0;
    let userAnswers = [];
    let weakAreas = [];
    
    // Event Listeners
    startQuizBtn.addEventListener('click', startQuiz);
    nextBtn.addEventListener('click', showNextQuestion);
    newQuizBtn.addEventListener('click', resetQuiz);
    
    // Form validation
    function validateForm() {
        const isValid = classSelect.value && subjectSelect.value && difficultySelect.value;
        startQuizBtn.disabled = !isValid;
    }
    
    classSelect.addEventListener('change', validateForm);
    subjectSelect.addEventListener('change', validateForm);
    difficultySelect.addEventListener('change', validateForm);
    
    // Start Quiz
    async function startQuiz() {
        if (!classSelect.value || !subjectSelect.value || !difficultySelect.value) {
            alert('Please select all required fields to start the quiz');
            return;
        }
        
        // Show loading
        loadingElement.classList.remove('hidden');
        startQuizBtn.disabled = true;
        
        try {
            const response = await fetch('/generate_questions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    'class': classSelect.value,
                    'subject': subjectSelect.value,
                    'difficulty': difficultySelect.value
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert('Error: ' + data.error);
                loadingElement.classList.add('hidden');
                startQuizBtn.disabled = false;
                return;
            }
            
            quizQuestions = data.questions;
            
            // Hide setup screen, show quiz screen
            setupScreen.classList.add('hidden');
            quizScreen.classList.remove('hidden');
            
            // Set quiz info
            subjectHeader.textContent = subjectSelect.value;
            classInfo.textContent = `Class ${classSelect.value}`;
            difficultyInfo.textContent = `${difficultySelect.value.charAt(0).toUpperCase() + difficultySelect.value.slice(1)}`;
            
            // Reset quiz state
            currentQuestionIndex = 0;
            userScore = 0;
            userAnswers = [];
            weakAreas = [];
            
            // Show first question
            showQuestion(0);
            
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            loadingElement.classList.add('hidden');
            startQuizBtn.disabled = false;
        }
    }
    
    // Display Question
    function showQuestion(index) {
        const question = quizQuestions[index];
        questionCounter.textContent = `Question ${index + 1}/10`;
        questionText.textContent = question.question;
        
        // Clear previous options
        optionsContainer.innerHTML = '';
        
        // Create options
        question.options.forEach((option, i) => {
            const optionElement = document.createElement('div');
            optionElement.classList.add('option');
            optionElement.textContent = option;
            optionElement.dataset.index = i;
            optionElement.addEventListener('click', () => selectOption(optionElement, i));
            optionsContainer.appendChild(optionElement);
        });
        
        // Hide feedback
        feedbackContainer.classList.add('hidden');
    }
    
    // Handle option selection
    function selectOption(optionElement, optionIndex) {
        // Prevent selecting after answer is shown
        if (!feedbackContainer.classList.contains('hidden')) {
            return;
        }
        
        // Remove selection from all options
        const options = optionsContainer.querySelectorAll('.option');
        options.forEach(opt => opt.classList.remove('selected'));
        
        // Mark selected option
        optionElement.classList.add('selected');
        
        const currentQuestion = quizQuestions[currentQuestionIndex];
        const correctOptionIndex = ['A', 'B', 'C', 'D'].indexOf(currentQuestion.correctAnswer);
        
        // Show feedback
        feedbackContainer.classList.remove('hidden');
        
        // Check if answer is correct
        if (optionIndex === correctOptionIndex) {
            feedbackResult.textContent = '✓ Correct!';
            feedbackContainer.classList.add('correct');
            feedbackContainer.classList.remove('incorrect');
            userScore++;
            
            // Mark option as correct
            optionElement.classList.add('correct');
        } else {
            feedbackResult.textContent = '✗ Incorrect';
            feedbackContainer.classList.add('incorrect');
            feedbackContainer.classList.remove('correct');
            
            // Mark options as correct/incorrect
            optionElement.classList.add('incorrect');
            options[correctOptionIndex].classList.add('correct');
            
            // Add to weak areas
            const questionText = currentQuestion.question.toLowerCase();
            const potentialTopics = {
                'math': ['equation', 'algebra', 'geometry', 'calculus', 'trigonometry', 'arithmetic'],
                'physics': ['force', 'motion', 'energy', 'electricity', 'magnetism', 'optics'],
                'chemistry': ['reaction', 'element', 'compound', 'molecule', 'acid', 'base'],
                'biology': ['cell', 'organism', 'evolution', 'ecology', 'genetics']
            };
            
            const subject = subjectSelect.value.toLowerCase();
            if (potentialTopics[subject]) {
                for (const topic of potentialTopics[subject]) {
                    if (questionText.includes(topic) && !weakAreas.includes(topic)) {
                        weakAreas.push(topic);
                        break;
                    }
                }
            }
            
            if (weakAreas.length === 0 && currentQuestionIndex === 9) {
                weakAreas.push(subject + ' fundamentals');
            }
        }
        
        // Display explanation
        feedbackExplanation.textContent = currentQuestion.explanation;
        
        // Store user's answer
        userAnswers.push({
            questionIndex: currentQuestionIndex,
            userOption: optionIndex,
            correctOption: correctOptionIndex,
            isCorrect: optionIndex === correctOptionIndex
        });
    }
    
    // Show Next Question
    function showNextQuestion() {
        if (currentQuestionIndex < quizQuestions.length - 1) {
            currentQuestionIndex++;
            showQuestion(currentQuestionIndex);
        } else {
            showResults();
        }
    }
    
    // Show Results
    async function showResults() {
        quizScreen.classList.add('hidden');
        resultsScreen.classList.remove('hidden');
        
        // Update score
        finalScore.textContent = userScore;
        
        // Show score message
        if (userScore === 10) {
            scoreMessage.textContent = 'Perfect score! Excellent job!';
        } else if (userScore >= 8) {
            scoreMessage.textContent = 'Great job! You have a strong understanding of the subject.';
        } else if (userScore >= 6) {
            scoreMessage.textContent = 'Good effort! Keep practicing to improve.';
        } else if (userScore >= 4) {
            scoreMessage.textContent = 'You\'re making progress. More practice will help.';
        } else {
            scoreMessage.textContent = 'Keep studying. You\'ll improve with more practice.';
        }
        
        // Generate recommendations
        loadingRecommendations.classList.remove('hidden');
        
        try {
            const response = await fetch('/get_recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    'class': classSelect.value,
                    'subject': subjectSelect.value,
                    'difficulty': difficultySelect.value,
                    'score': userScore,
                    'weakAreas': weakAreas
                })
            });
            
            const recommendations = await response.json();
            
            if (recommendations.error) {
                alert('Error loading recommendations: ' + recommendations.error);
                loadingRecommendations.classList.add('hidden');
                return;
            }
            
            // Display recommendations
            youtubeRecommendations.innerHTML = '';
            recommendations.youtube.forEach(video => {
                const li = document.createElement('li');
                li.textContent = video;
                youtubeRecommendations.appendChild(li);
            });
            
            ncertRecommendations.innerHTML = '';
            recommendations.ncert.forEach(book => {
                const li = document.createElement('li');
                li.textContent = book;
                ncertRecommendations.appendChild(li);
            });
            
            resourceRecommendations.innerHTML = '';
            recommendations.resources.forEach(resource => {
                const li = document.createElement('li');
                li.textContent = resource;
                resourceRecommendations.appendChild(li);
            });
            
            tipsRecommendations.innerHTML = '';
            recommendations.tips.forEach(tip => {
                const li = document.createElement('li');
                li.textContent = tip;
                tipsRecommendations.appendChild(li);
            });
            
            // Hide loading, show recommendations
            loadingRecommendations.classList.add('hidden');
            recommendationsContainer.classList.remove('hidden');
            
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while loading recommendations.');
            loadingRecommendations.classList.add('hidden');
        }
    }
    
    // Reset Quiz
    function resetQuiz() {
        resultsScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
        recommendationsContainer.classList.add('hidden');
        
        // Clear selections
        classSelect.value = '';
        subjectSelect.value = '';
        difficultySelect.value = '';
        startQuizBtn.disabled = true;
    }
    
    // Initialize
    validateForm();
}); 