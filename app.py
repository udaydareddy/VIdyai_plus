from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime, timedelta
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import session, redirect, url_for, render_template
from datetime import datetime, timedelta

# app.py
from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
import os
import json
import re
import random
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import uuid

# Import your custom modules
# If these modules don't exist yet, you'll need to create them
try:
    from models.student import Student
    from models.content import LearningContent
    from services.ai_service import GeminiService
    from services.vision_service import EngagementTracker
    from services.language_service import LanguageService
    from services.adaptive_service import AdaptiveService
except ImportError:
    # Handle missing modules gracefully for development
    print("Warning: Some modules could not be imported. Make sure they exist or create them.")
    # Create stub classes to prevent errors
    class Student:
        @staticmethod
        def load(student_id):
            return None
        def to_dict(self):
            return {}
        def save(self):
            pass
    
    class LearningContent:
        def get_lesson_content(self, subject, grade, topic, language, learning_style):
            return {"content": "Sample content"}
    
    class EngagementTracker:
        def start_tracking(self):
            return True
        def stop_tracking(self):
            return {"score": 0.5}
        def get_current_engagement(self):
            return 0.5
    
    class LanguageService:
        def translate_text(self, text, language):
            return text
        def text_to_speech(self, text, language):
            return None
    
    class AdaptiveService:
        pass

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
CORS(app)

# Configure Gemini API
try:
    genai.configure(api_key="AIzaSyB9u_DjHIUNRrMH0lLEhK4iSb0ZQRPcjyo")
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    print("Successfully initialized Gemini model")
except Exception as e:
    print(f"Error initializing Gemini model: {str(e)}")
    model = None

def generate_questions_for_quiz(prompt):
    """
    Generate quiz questions using the Gemini model.
    Returns a list of question objects in the required format.
    """
    if not model:
        raise Exception("Gemini model not initialized")
        
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to extract JSON from the response
        try:
            # First try direct JSON parsing
            questions = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code blocks
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                # Try to find JSON array markers
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                if start_idx >= 0 and end_idx > 0:
                    json_str = response_text[start_idx:end_idx]
                else:
                    print(f"Could not find JSON content in response: {response_text}")
                    raise ValueError("Could not find JSON content in response")
            
            questions = json.loads(json_str)
        
        # Validate question format
        if not isinstance(questions, list):
            raise ValueError("Questions must be a list")
        
        for q in questions:
            if not isinstance(q, dict):
                raise ValueError("Each question must be an object")
            if not all(key in q for key in ['question', 'options', 'correct_answer', 'explanation']):
                raise ValueError("Question missing required fields")
            if not isinstance(q['options'], list) or len(q['options']) != 4:
                raise ValueError("Each question must have exactly 4 options")
            if not isinstance(q['correct_answer'], int) or q['correct_answer'] < 0 or q['correct_answer'] > 3:
                raise ValueError("correct_answer must be an integer between 0 and 3")
        
        return questions
        
    except Exception as e:
        print(f"Error in generate_questions_for_quiz: {str(e)}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        raise

# Initialize services
content_service = LearningContent()
language_service = LanguageService()
app.jinja_env.globals.update(min=min)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('instance/learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
    finally:
        conn.close()

# Create instance directory if it doesn't exist
if not os.path.exists('instance'):
    os.makedirs('instance')

# Initialize the database
init_db()

# Add this configuration after app creation
app.config['AUDIO_FOLDER'] = os.path.join('static', 'audio')
if not os.path.exists(app.config['AUDIO_FOLDER']):
    os.makedirs(app.config['AUDIO_FOLDER'])

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))

    conn = get_db_connection()

    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    # Fetch streak and points
    streak_data = conn.execute('''
        SELECT streak_days, last_activity_date, total_points 
        FROM user_progress 
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()

    if streak_data:
        last_activity = datetime.strptime(streak_data['last_activity_date'], '%Y-%m-%d')
        today = datetime.now().date()
        yesterday = (datetime.now() - timedelta(days=1)).date()

        if last_activity.date() == yesterday:
            conn.execute('''
                UPDATE user_progress 
                SET streak_days = streak_days + 1, last_activity_date = ? 
                WHERE user_id = ?
            ''', (today.strftime('%Y-%m-%d'), session['user_id']))
            conn.commit()
        elif last_activity.date() < yesterday:
            conn.execute('''
                UPDATE user_progress 
                SET streak_days = 1, last_activity_date = ? 
                WHERE user_id = ?
            ''', (today.strftime('%Y-%m-%d'), session['user_id']))
            conn.commit()

        # Refresh streak_data after update
        streak_data = conn.execute('''
            SELECT streak_days, last_activity_date, total_points 
            FROM user_progress 
            WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()

        streak_progress = min(streak_data['streak_days'] * 10, 100)
    else:
        streak_data = {'streak_days': 0, 'total_points': 0}
        streak_progress = 0

    # Prepare 'progress' object for template
    progress = {
        'total_points': streak_data['total_points'],
        'streak_days': streak_data['streak_days']
    }

    # Fetch courses
    courses = conn.execute('''
        SELECT c.id, c.title, c.description, 
               COUNT(DISTINCT m.id) as total_modules,
               COUNT(DISTINCT cm.module_id) as completed_modules
        FROM courses c
        LEFT JOIN modules m ON m.course_id = c.id
        LEFT JOIN completed_modules cm ON cm.module_id = m.id AND cm.user_id = ?
        GROUP BY c.id
    ''', (session['user_id'],)).fetchall()

    # Fetch badges
    badges = conn.execute('''
        SELECT b.id, b.name, b.description, b.image_url 
        FROM badges b
        JOIN user_badges ub ON ub.badge_id = b.id
        WHERE ub.user_id = ?
    ''', (session['user_id'],)).fetchall()

    # Fetch certificates (this is new — adjust if your DB schema differs)
    certificates = conn.execute('''
        SELECT * FROM certificates
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return render_template('dashboard.html', 
                           user=user, 
                           courses=courses, 
                           badges=badges,
                           certificates=certificates,
                           streak_data=streak_data,
                           streak_progress=streak_progress,
                           progress=progress
                           )

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Get user progress
    progress = conn.execute('''
        SELECT * FROM user_progress WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    # Get skill heatmap data
    skills = conn.execute('''
        SELECT s.category, s.name, us.proficiency 
        FROM skills s
        LEFT JOIN user_skills us ON us.skill_id = s.id AND us.user_id = ?
    ''', (session['user_id'],)).fetchall()
    
    # Organize skills by category
    skill_map = {}
    for skill in skills:
        category = skill['category']
        if category not in skill_map:
            skill_map[category] = []
        skill_map[category].append({
            'name': skill['name'],
            'proficiency': skill['proficiency'] or 0
        })
    
    # Get certificates
    certificates = conn.execute('''
        SELECT c.id, c.course_id, co.title as course_name, c.issue_date
        FROM certificates c
        JOIN courses co ON co.id = c.course_id
        WHERE c.user_id = ?
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('profile.html', 
                           user=user, 
                           progress=progress,
                           skill_map=skill_map,
                           certificates=certificates)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    # Get modules for the course
    modules = conn.execute('''
        SELECT m.*, 
               CASE WHEN cm.module_id IS NOT NULL THEN 1 ELSE 0 END as completed
        FROM modules m
        LEFT JOIN completed_modules cm ON cm.module_id = m.id AND cm.user_id = ?
        WHERE m.course_id = ?
        ORDER BY m.order_num
    ''', (session['user_id'], course_id)).fetchall()
    
    conn.close()
    
    return render_template('course_detail.html', course=course, modules=modules)

@app.route('/complete_module/<int:module_id>', methods=['POST'])
def complete_module(module_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    conn = get_db_connection()
    
    # Record module completion
    conn.execute('''
        INSERT INTO completed_modules (user_id, module_id, completed_date)
        VALUES (?, ?, ?)
    ''', (session['user_id'], module_id, datetime.now().strftime('%Y-%m-%d')))
    
    # Update points
    conn.execute('''
        UPDATE user_progress 
        SET total_points = total_points + 10
        WHERE user_id = ?
    ''', (session['user_id'],))
    
    # Check if all modules in a course are completed
    module = conn.execute('SELECT course_id FROM modules WHERE id = ?', (module_id,)).fetchone()
    course_id = module['course_id']
    
    total_modules = conn.execute('''
        SELECT COUNT(*) as count FROM modules WHERE course_id = ?
    ''', (course_id,)).fetchone()['count']
    
    completed_modules = conn.execute('''
        SELECT COUNT(DISTINCT m.id) as count
        FROM modules m
        JOIN completed_modules cm ON cm.module_id = m.id
        WHERE m.course_id = ? AND cm.user_id = ?
    ''', (course_id, session['user_id'])).fetchone()['count']
    
    # If course completed, issue certificate
    if total_modules == completed_modules:
        conn.execute('''
            INSERT INTO certificates (user_id, course_id, issue_date)
            VALUES (?, ?, ?)
        ''', (session['user_id'], course_id, datetime.now().strftime('%Y-%m-%d')))
        
        # Award course completion badge
        badge_id = conn.execute('''
            SELECT id FROM badges WHERE trigger_type = 'course_completion' AND trigger_id = ?
        ''', (course_id,)).fetchone()
        
        if badge_id:
            conn.execute('''
                INSERT INTO user_badges (user_id, badge_id, award_date)
                VALUES (?, ?, ?)
            ''', (session['user_id'], badge_id['id'], datetime.now().strftime('%Y-%m-%d')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/update_skill', methods=['POST'])
def update_skill():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    data = request.json
    skill_id = data.get('skill_id')
    proficiency = data.get('proficiency')
    
    conn = get_db_connection()
    
    # Update or insert skill proficiency
    existing = conn.execute('''
        SELECT * FROM user_skills WHERE user_id = ? AND skill_id = ?
    ''', (session['user_id'], skill_id)).fetchone()
    
    if existing:
        conn.execute('''
            UPDATE user_skills SET proficiency = ? WHERE user_id = ? AND skill_id = ?
        ''', (proficiency, session['user_id'], skill_id))
    else:
        conn.execute('''
            INSERT INTO user_skills (user_id, skill_id, proficiency)
            VALUES (?, ?, ?)
        ''', (session['user_id'], skill_id, proficiency))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# Login and registration routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            if not username or not password:
                flash('Please enter both username and password')
                return render_template('login.html')
            
            conn = get_db_connection()
            try:
                user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
                
                if user is None:
                    print(f"Login attempt failed: User '{username}' not found")
                    flash('Invalid username or password')
                    return render_template('login.html')
                
                if not check_password_hash(user['password'], password):
                    print(f"Login attempt failed: Invalid password for user '{username}'")
                    flash('Invalid username or password')
                    return render_template('login.html')
                
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['name'] = user['name']
                print(f"Login successful for user '{username}'")
                flash('Login successful!')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                print(f"Database error during login: {str(e)}")
                flash('An error occurred during login. Please try again.')
                return render_template('login.html')
            finally:
                conn.close()
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        grade = request.form['grade']
        school = request.form['school']
        
        conn = get_db_connection()
        
        # Check if username exists
        existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        cursor = conn.execute('''
            INSERT INTO users (username, password, name, grade, school)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, generate_password_hash(password), name, grade, school))
        
        user_id = cursor.lastrowid
        
        # Initialize user progress
        conn.execute('''
            INSERT INTO user_progress (user_id, streak_days, total_points, last_activity_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, 1, 0, datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
        
        session['user_id'] = user_id
        session['username'] = username
        session['name'] = name
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        flash('Please login to take a quiz', 'error')
        return redirect(url_for('login'))
    
    if 'quiz_data' not in session:
        return redirect(url_for('quiz_setup'))
        
    return render_template('quiz.html')

@app.route('/get_questions')
def get_questions():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to take a quiz'}), 401
    
    if 'quiz_data' not in session:
        return jsonify({'error': 'No quiz data found. Please set up a quiz first.'}), 404
    
    quiz_data = session['quiz_data']
    questions = []
    
    for q in quiz_data['questions']:
        questions.append({
            'question': q['question'],
            'options': q['options'],
            'correct_answer': q['correct_answer'],
            'explanation': q['explanation']
        })
    
    return jsonify({'questions': questions})

def generate_question_recommendations(question, user_answer, is_correct, subject, class_level):
    """Generate personalized recommendations for a question using Gemini AI."""
    try:
        prompt = f"""
        For a class {class_level} student studying {subject}, provide targeted recommendations for this question:

        Question: {question['question']}
        Student's Answer: {question['options'][user_answer]}
        Correct Answer: {question['options'][question['correct_answer']]}
        Answer was: {'Correct' if is_correct else 'Incorrect'}
        Explanation: {question['explanation']}

        Return ONLY a JSON object with this exact structure:
        {{
            "video": {{
                "title": "Clear, descriptive video title",
                "url": "YouTube search query for relevant content"
            }},
            "material": {{
                "title": "Study material title",
                "description": "Brief, helpful description of what to study"
            }},
            "tip": {{
                "title": "Practice tip title",
                "description": "Actionable advice for improvement"
            }}
        }}

        Make recommendations:
        1. Specific to the question's topic
        2. Appropriate for class {class_level}
        3. Focus on {'reinforcement' if is_correct else 'improvement'}
        4. Include actual educational resources
        5. Keep descriptions concise and actionable
        """

        response = model.generate_content(prompt)
        recommendations = json.loads(response.text.strip())
        return recommendations
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return None

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in to generate questions'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['class', 'subject', 'difficulty']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        print(f'Generating questions for class {data["class"]}, subject {data["subject"]}, difficulty {data["difficulty"]}')

        prompt = f"""Generate 10 multiple choice questions for a {data['class']} grade student in {data['subject']} at {data['difficulty']} level.

Return ONLY a JSON array of questions with this exact structure:
[
    {{
        "question": "Clear, well-formed question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "Detailed explanation of why the answer is correct",
        "topic": "Specific topic or concept being tested"
    }}
]

Important guidelines:
1. Each question must be grade-appropriate for class {data['class']}
2. Questions should be clear and unambiguous
3. All 4 options must be plausible but only one correct
4. correct_answer must be the index (0-3) of the correct option
5. Explanation should be detailed and educational
6. Include the specific topic being tested
7. For {data['subject']}, focus on core concepts from the curriculum
8. Difficulty should be appropriate for {data['difficulty']} level
9. Use proper formatting and avoid special characters"""

        try:
            questions = generate_questions_for_quiz(prompt)
            
            if not questions or len(questions) != 10:
                print('Failed to generate the required number of questions')
                return jsonify({'error': 'Failed to generate a complete set of questions'}), 500

            # Store questions in session for later use
            session['current_quiz'] = {
                'questions': questions,
                'class': data['class'],
                'subject': data['subject'],
                'difficulty': data['difficulty']
            }

            # Add initial recommendations for each question
            for question in questions:
                # Generate initial recommendations (for when answer is incorrect)
                recommendations = generate_question_recommendations(
                    question=question,
                    user_answer=0,  # Dummy answer for initial recommendations
                    is_correct=False,
                    subject=data['subject'],
                    class_level=data['class']
                )
                question['recommendations'] = recommendations

            return jsonify({'questions': questions})

        except Exception as e:
            print(f'Error in question generation: {str(e)}')
            return jsonify({'error': 'Failed to generate questions. Please try again.'}), 500

    except Exception as e:
        print(f'Error processing request: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/get_question_recommendations', methods=['POST'])
def get_question_recommendations():
    """Generate new recommendations based on the user's answer to a question."""
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401

    try:
        data = request.get_json()
        if not data or 'questionIndex' not in data or 'userAnswer' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        current_quiz = session.get('current_quiz')
        if not current_quiz or not current_quiz.get('questions'):
            return jsonify({'error': 'No active quiz found'}), 400

        question = current_quiz['questions'][data['questionIndex']]
        is_correct = data['userAnswer'] == question['correct_answer']

        recommendations = generate_question_recommendations(
            question=question,
            user_answer=data['userAnswer'],
            is_correct=is_correct,
            subject=current_quiz['subject'],
            class_level=current_quiz['class']
        )

        return jsonify({'recommendations': recommendations})

    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return jsonify({'error': 'Failed to generate recommendations'}), 500

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        answers = data.get('answers', [])
        time_taken = data.get('time_taken', 0)
        subject = data.get('subject')
        class_level = data.get('class')
        difficulty = data.get('difficulty')
        
        # Get quiz details from session
        current_quiz = session.get('current_quiz')
        if not current_quiz or not current_quiz.get('questions'):
            return jsonify({'error': 'No active quiz found'}), 400
            
        questions = current_quiz['questions']
        
        # Calculate score and collect explanations
        correct_answers = 0
        question_results = []
        
        for i, (answer, question) in enumerate(zip(answers, questions)):
            is_correct = answer == question['correct_answer']
            if is_correct:
                correct_answers += 1
                
            question_results.append({
                'question_number': i + 1,
                'question': question['question'],
                'user_answer': answer,
                'correct_answer': question['correct_answer'],
                'is_correct': is_correct,
                'explanation': question['explanation'],
                'options': question['options']
            })
                
        score_percentage = (correct_answers / len(questions)) * 100
        
        # Determine performance level
        performance_level = (
            'advanced' if score_percentage >= 80
            else 'intermediate' if score_percentage >= 60
            else 'beginner'
        )

        # Generate recommendations using Gemini AI
        prompt = f"""
        For a class {class_level} student studying {subject} at {difficulty} level 
        who scored {correct_answers}/{len(questions)} ({score_percentage:.1f}%) on a quiz, provide detailed learning recommendations.
        
        Performance Level: {performance_level}
        
        Return ONLY a JSON object with this exact structure:
        {{
            "videos": [
                {{
                    "title": "Video title",
                    "url": "Video URL or search query",
                    "description": "Brief description"
                }}
            ],
            "study_material": [
                {{
                    "title": "Resource title",
                    "description": "Brief description of the material"
                }}
            ],
            "practice_areas": [
                {{
                    "topic": "Topic to practice",
                    "difficulty": "easy/medium/hard"
                }}
            ]
        }}
        
        Important guidelines:
        1. Recommendations should be specific to {subject} for class {class_level}
        2. Focus on topics that match the {performance_level} level
        3. Include actual educational resources and channels
        4. Make all suggestions actionable and specific
        """
        
        try:
            response = model.generate_content(prompt)
            recommendations = json.loads(response.text.strip())
            
            # Save quiz result to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insert quiz result
            cursor.execute('''
                INSERT INTO quiz_results 
                (user_id, subject, class, difficulty, score, time_taken, date_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'], 
                subject,
                class_level, 
                difficulty, 
                score_percentage,
                time_taken,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            quiz_id = cursor.lastrowid
            
            # Save detailed results
            cursor.execute('''
                INSERT INTO quiz_details 
                (quiz_id, question_data, recommendations)
                VALUES (?, ?, ?)
            ''', (
                quiz_id,
                json.dumps(question_results),
                json.dumps(recommendations)
            ))
            
            # Update user progress
            cursor.execute('''
                UPDATE user_progress 
                SET total_points = total_points + ?,
                    last_activity_date = ?
                WHERE user_id = ?
            ''', (
                int(score_percentage / 10),  # Points based on score
                datetime.now().strftime('%Y-%m-%d'),
                session['user_id']
            ))
            
            conn.commit()
            conn.close()
            
            # Clear the quiz from session
            session.pop('current_quiz', None)
            
            return jsonify({
                'success': True,
                'quiz_id': quiz_id,
                'score': score_percentage,
                'correct_answers': correct_answers,
                'total_questions': len(questions),
                'performance_level': performance_level,
                'question_results': question_results,
                'recommendations': recommendations,
                'time_taken': time_taken
            })
            
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return jsonify({
                'success': True,
                'score': score_percentage,
                'correct_answers': correct_answers,
                'total_questions': len(questions),
                'performance_level': performance_level,
                'question_results': question_results,
                'time_taken': time_taken,
                'error': 'Failed to generate recommendations'
            })
            
    except Exception as e:
        print(f"Error submitting quiz: {str(e)}")
        return jsonify({'error': 'Failed to submit quiz. Please try again.'}), 500

@app.route('/quiz_results/<int:quiz_id>')
def quiz_results(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        db = get_db_connection()
        # Get quiz result with user progress and quiz details
        result = db.execute('''
            SELECT qr.*, 
                   up.streak_days,
                   up.total_points,
                   up.last_activity_date,
                   u.grade as student_class
            FROM quiz_results qr
            JOIN user_progress up ON up.user_id = qr.user_id
            JOIN users u ON u.id = qr.user_id
            WHERE qr.id = ? AND qr.user_id = ?
        ''', (quiz_id, session['user_id'])).fetchone()
        
        if result is None:
            flash('Quiz result not found', 'error')
            return redirect(url_for('dashboard'))

        # Calculate performance level and areas for improvement
        score_percentage = (result['score'] / 10) * 100
        performance_level = (
            'beginner' if score_percentage < 60
            else 'intermediate' if score_percentage < 80
            else 'advanced'
        )

        # Get recommendations based on quiz performance
        prompt = f"""
        For a class {result['student_class']} student studying {result['subject']} at {result['difficulty']} level 
        who scored {result['score']}/10 ({score_percentage}%) on a quiz, provide detailed learning recommendations.
        
        Performance Level: {performance_level}
        
        Return ONLY a JSON object with this exact structure:
        {{
          "youtube": [
            {{
              "title": "Video title",
              "channel": "Channel name",
              "description": "Brief description of video content",
              "url": "Suggested YouTube search query"
            }},
            {{
              "title": "Video title",
              "channel": "Channel name",
              "description": "Brief description of video content",
              "url": "Suggested YouTube search query"
            }},
            {{
              "title": "Video title",
              "channel": "Channel name",
              "description": "Brief description of video content",
              "url": "Suggested YouTube search query"
            }}
          ],
          "ncert": [
            {{
              "chapter": "Chapter name and number",
              "topics": ["Key topic 1", "Key topic 2"],
              "pages": "Page range (e.g., 45-52)"
            }},
            {{
              "chapter": "Chapter name and number",
              "topics": ["Key topic 1", "Key topic 2"],
              "pages": "Page range (e.g., 45-52)"
            }}
          ],
          "practice": [
            {{
              "topic": "Specific topic to practice",
              "resources": ["Resource 1", "Resource 2"],
              "difficulty": "beginner/intermediate/advanced"
            }},
            {{
              "topic": "Specific topic to practice",
              "resources": ["Resource 1", "Resource 2"],
              "difficulty": "beginner/intermediate/advanced"
            }}
          ],
          "tips": [
            {{
              "title": "Tip title",
              "description": "Detailed explanation of the study tip",
              "actionItems": ["Action 1", "Action 2"]
            }},
            {{
              "title": "Tip title",
              "description": "Detailed explanation of the study tip",
              "actionItems": ["Action 1", "Action 2"]
            }}
          ]
        }}
        
        Important:
        1. Recommendations should be specific to {result['subject']} for class {result['student_class']}
        2. For beginner level (score < 60%), focus on foundational concepts and basic practice
        3. For intermediate level (score 60-80%), focus on practice and specific topic improvement
        4. For advanced level (score > 80%), focus on challenging content and advanced topics
        5. Include only real, relevant educational resources
        6. For YouTube videos, suggest actual channels known for {result['subject']} education
        7. For NCERT chapters, reference actual chapters from the appropriate textbook
        8. Make all suggestions actionable and specific
        """
        
        try:
            response = model.generate_content(prompt)
            recommendations = json.loads(response.text.strip())
            
            # Validate recommendations structure
            required_keys = ['youtube', 'ncert', 'practice', 'tips']
            if not all(key in recommendations for key in required_keys):
                raise ValueError("Missing required fields in recommendations")
            
            # Update user progress with recommendation data
            db.execute('''
                INSERT INTO learning_recommendations 
                (user_id, quiz_id, subject, performance_level, recommendations, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (
                session['user_id'], 
                quiz_id, 
                result['subject'], 
                performance_level,
                json.dumps(recommendations)
            ))
            db.commit()
            
            return render_template('quiz_results.html', 
                                result=result, 
                                recommendations=recommendations,
                                performance_level=performance_level)
            
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            # If recommendations fail, still show results without recommendations
            return render_template('quiz_results.html', 
                                result=result,
                                recommendations=None,
                                performance_level=performance_level)
        
    except Exception as e:
        print(f"Error retrieving quiz results: {str(e)}")
        flash('Failed to retrieve quiz results', 'error')
        return redirect(url_for('dashboard'))
    finally:
        db.close()

@app.route('/learning')
def learning():
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get selected subject and topic from query parameters
    selected_subject = request.args.get('subject')
    selected_topic_id = request.args.get('topic_id')
    
    # Get all subjects from topics
    subjects = conn.execute('''
        SELECT DISTINCT subject FROM topics
    ''').fetchall()
    
    # Get topics for the selected subject
    topics = []
    if selected_subject:
        topics = conn.execute('''
            SELECT * FROM topics 
            WHERE subject = ?
        ''', (selected_subject,)).fetchall()
    
    # Get selected topic details if a topic is selected
    selected_topic = None
    if selected_topic_id:
        selected_topic = conn.execute('''
            SELECT * FROM topics 
            WHERE id = ?
        ''', (selected_topic_id,)).fetchone()
    
    # Get user's current streak and points
    progress = conn.execute('''
        SELECT streak_days, total_points 
        FROM user_progress 
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    conn.close()
    
    return render_template('learning.html', 
                         subjects=subjects,
                         topics=topics,
                         selected_subject=selected_subject,
                         selected_topic=selected_topic,
                         progress=progress)

@app.route('/generate_learning_content', methods=['POST'])
def generate_learning_content():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    topic_id = data.get('topic_id')
    
    if not topic_id:
        return jsonify({'error': 'Topic ID is required'}), 400
    
    conn = get_db_connection()
    topic = conn.execute('SELECT * FROM topics WHERE id = ?', (topic_id,)).fetchone()
    conn.close()
    
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404
    
    try:
        # Generate content using Gemini AI
        prompt = f"""
        Create an engaging and educational content about {topic['title']} for students.
        The content should be:
        1. Clear and easy to understand
        2. Include examples and explanations
        3. Be interactive and engaging
        4. Include practice questions
        
        Format the response as JSON with the following structure:
        {{
            "content": "Main educational content",
            "examples": ["Example 1", "Example 2", "Example 3"],
            "practice_questions": [
                {{
                    "question": "Question text",
                    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                    "correct_answer": 0
                }}
            ]
        }}
        
        Make sure to:
        1. Use proper JSON formatting
        2. Escape any special characters
        3. Use double quotes for strings
        4. Use numbers for correct_answer (0-based index)
        """
        
        response = model.generate_content(prompt)
        
        # Extract JSON from the response
        try:
            # Find JSON content in the response
            json_str = response.text
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0]
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0]
            
            content = json.loads(json_str)
            
            # Validate the content structure
            if not all(key in content for key in ['content', 'examples', 'practice_questions']):
                raise ValueError("Missing required fields in generated content")
            
            # Validate practice questions
            for question in content['practice_questions']:
                if not all(key in question for key in ['question', 'options', 'correct_answer']):
                    raise ValueError("Invalid practice question format")
                if not isinstance(question['correct_answer'], int):
                    raise ValueError("correct_answer must be an integer")
            
            return jsonify(content)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response text: {response.text}")
            return jsonify({
                'error': 'Failed to parse AI response',
                'details': str(e)
            }), 500
            
    except Exception as e:
        print(f"Error in generate_learning_content: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/quiz_setup')
def quiz_setup():
    if 'user_id' not in session:
        flash('Please log in to take a quiz', 'warning')
        return redirect(url_for('login'))
    return render_template('quiz-setup.html')

@app.route('/learning')
def learning_page():
    subject = request.args.get('subject')
    topic = request.args.get('topic', '')

    valid_subjects = ['math', 'science', 'english', 'socialstudies', 'assessment']

    if subject not in valid_subjects:
        return render_template('404.html', message=f"Subject '{subject}' not found."), 404

    return render_template('learning.html', subject=subject, topic=topic)

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.json
    student_class = data.get('class')
    subject = data.get('subject')
    difficulty = data.get('difficulty')
    score = data.get('score')
    weak_areas = data.get('weakAreas', [])
    
    weak_areas_text = ", ".join(weak_areas) if weak_areas else "general topics"
    
    prompt = f"""
    For a class {student_class} student studying {subject} at {difficulty} level who scored {score}/10 on a quiz,
    provide personalized learning recommendations for improving in these areas: {weak_areas_text}.
    
    Return ONLY a JSON object with this exact structure:
    {{
      "youtube": [
        "Title 1 (Channel name)",
        "Title 2 (Channel name)",
        "Title 3 (Channel name)"
      ],
      "ncert": [
        "Chapter name and number from appropriate textbook",
        "Chapter name and number from appropriate textbook"
      ],
      "resources": [
        "Resource 1 description",
        "Resource 2 description"
      ],
      "tips": [
        "Study tip 1",
        "Study tip 2",
        "Study tip 3"
      ]
    }}

    Important:
    1. Return ONLY the JSON object, no other text
    2. Do not include any markdown formatting or code blocks
    3. Use proper JSON formatting with double quotes
    4. Each array must have the exact number of items shown above
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        try:
            # Try to parse the response directly first
            recommendations = json.loads(response_text)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON
            # Look for object start/end
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("Could not find JSON object in response")
            
            json_str = response_text[start_idx:end_idx]
        recommendations = json.loads(json_str)
        
        # Validate recommendations structure
        required_keys = ['youtube', 'ncert', 'resources', 'tips']
        if not all(key in recommendations for key in required_keys):
            raise ValueError("Missing required fields in recommendations")
        
        # Validate array lengths
        expected_lengths = {
            'youtube': 3,
            'ncert': 2,
            'resources': 2,
            'tips': 3
        }
        
        for key, length in expected_lengths.items():
            if not isinstance(recommendations[key], list):
                raise ValueError(f"{key} must be an array")
            if len(recommendations[key]) != length:
                # Pad or trim arrays to match expected length
                if len(recommendations[key]) < length:
                    recommendations[key].extend([f"Additional {key} item"] * (length - len(recommendations[key])))
                else:
                    recommendations[key] = recommendations[key][:length]
        
        return jsonify(recommendations)
    
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return jsonify({
            "error": "Failed to generate recommendations",
            "details": str(e)
        }), 500

# Engagement API Routes


# Content Generation API Routes
@app.route('/generate_content', methods=['POST'])
def generate_content():
    if not session.get('user_id'):
        return jsonify({'error': 'Please log in first'}), 401

    data = request.get_json()
    subject = data.get('subject', '')
    topic = data.get('topic', '')

    if not subject:
        return jsonify({'error': 'No subject provided'}), 400

    try:
        prompt = f"""
        Create an engaging educational content about {topic if topic else 'introduction to'} {subject}.
        The content should be:
        1. Clear and easy to understand for students
        2. Include relevant examples
        3. End with a brief summary
        
        Format the response in this exact JSON structure:
        {{
            "title": "Topic title",
            "content": "Main educational content with proper formatting",
            "examples": ["Example 1", "Example 2", "Example 3"],
            "summary": "Brief summary of key points"
        }}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        try:
            content = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON if direct parsing fails
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > 0:
                json_str = response_text[start_idx:end_idx]
                content = json.loads(json_str)
            else:
                raise ValueError("Invalid content format")
        
        # Validate content structure
        required_fields = ['title', 'content', 'examples', 'summary']
        if not all(field in content for field in required_fields):
            raise ValueError("Missing required fields in content")
        
        return jsonify(content)
    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return jsonify({'error': 'Failed to generate content'}), 500

@app.route('/api/translate', methods=['POST'])
def translate_text():
    if not session.get('user_id'):
        return jsonify({'error': 'Please log in first'}), 401

    data = request.get_json()
    text = data.get('text')
    target_language = data.get('language', 'english').lower()
    source_language = data.get('source_language', 'auto')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        prompt = f"""
        Translate the following text to {target_language}.
        If the text contains mixed languages (like Telugu and English), preserve any technical terms, 
        mathematical symbols, and numbers in their original form.
        
        Text to translate:
        {text}
        
        Rules for translation:
        1. Keep mathematical symbols (π, √, etc.) unchanged
        2. Keep numbers in their original form
        3. Keep technical mathematical terms in English
        4. Preserve formatting (bold, italics) if present
        5. Maintain paragraph structure
        
        Return ONLY the translated text, no explanations or additional content.
        """
        
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
        
        # Clean up any markdown or code block formatting that might have been added
        if translated_text.startswith('```'):
            translated_text = translated_text.split('```')[1]
            if translated_text.startswith('text'):
                translated_text = translated_text[4:]
        translated_text = translated_text.strip()
        
        return jsonify({'translated': translated_text})
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return jsonify({'error': 'Translation failed'}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    if not session.get('user_id'):
        return jsonify({'error': 'Please log in first'}), 401
    
    data = request.get_json()
    text = data.get('text')
    language = data.get('language', 'en')  # Default to English

    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Map common language names to gTTS language codes
        language_map = {
            'english': 'en',
            'telugu': 'te',
            'hindi': 'hi',
            'tamil': 'ta',
            'kannada': 'kn',
            'malayalam': 'ml',
            'bengali': 'bn',
            'marathi': 'mr',
            'gujarati': 'gu'
        }
        
        # Convert language name to code
        lang_code = language_map.get(language.lower(), language)
        
        # Generate unique filename
        filename = f"tts_{uuid.uuid4()}.mp3"
        filepath = os.path.join(app.config['AUDIO_FOLDER'], filename)
        
        # Create gTTS object and save to file
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(filepath)
        
        # Return the URL to the audio file
        audio_url = url_for('static', filename=f'audio/{filename}')
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
        
    except Exception as e:
        print(f"TTS error: {str(e)}")
        return jsonify({
            'error': 'Text-to-speech failed',
            'details': str(e)
        }), 500

@app.route('/quiz/<int:quiz_id>')
def take_quiz(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get quiz details
    quiz = conn.execute('''
        SELECT q.*, m.title as module_title, m.points
        FROM quizzes q
        JOIN modules m ON m.id = q.module_id
        WHERE q.id = ?
    ''', (quiz_id,)).fetchone()
    
    if not quiz:
        flash('Quiz not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if user has exceeded max attempts
    attempts = conn.execute('''
        SELECT COUNT(*) as count
        FROM quiz_attempts
        WHERE user_id = ? AND quiz_id = ?
    ''', (session['user_id'], quiz_id)).fetchone()['count']
    
    if attempts >= quiz['max_attempts']:
        flash('You have exceeded the maximum number of attempts for this quiz', 'error')
        return redirect(url_for('dashboard'))
    
    # Get questions and options
    questions = conn.execute('''
        SELECT q.*, GROUP_CONCAT(o.id || '|' || o.option_text || '|' || o.is_correct, '||') as options
        FROM questions q
        LEFT JOIN question_options o ON o.question_id = q.id
        WHERE q.quiz_id = ?
        GROUP BY q.id
    ''', (quiz_id,)).fetchall()
    
    # Process options for each question
    for question in questions:
        if question['options']:
            options = []
            for opt in question['options'].split('||'):
                opt_id, opt_text, is_correct = opt.split('|')
                options.append({
                    'id': opt_id,
                    'text': opt_text,
                    'is_correct': is_correct == '1'
                })
            question['options'] = options
    else:
            question['options'] = []
    
    conn.close()
    
    return render_template('quiz.html', 
                         quiz=quiz,
                         questions=questions)

if __name__ == '__main__':
    if not os.path.exists('instance'):
        os.mkdir('instance')
    init_db()  # ← runs your schema.sql
    app.run(debug=True)
