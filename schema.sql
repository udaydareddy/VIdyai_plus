DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS modules;
DROP TABLE IF EXISTS completed_modules;
DROP TABLE IF EXISTS user_progress;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS user_badges;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS user_skills;
DROP TABLE IF EXISTS certificates;
DROP TABLE IF EXISTS quizzes;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS question_options;
DROP TABLE IF EXISTS quiz_attempts;
DROP TABLE IF EXISTS quiz_responses;
DROP TABLE IF EXISTS adaptive_content;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS completed_quizzes;
DROP TABLE IF EXISTS quiz_results;
DROP TABLE IF EXISTS quiz_details;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    grade INTEGER NOT NULL,
    school TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    difficulty_level INTEGER
);

CREATE TABLE modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    order_num INTEGER NOT NULL,
    points INTEGER DEFAULT 10,
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

CREATE TABLE completed_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    completed_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (module_id) REFERENCES modules (id),
    UNIQUE(user_id, module_id)
);

CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    streak_days INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    last_activity_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    trigger_type TEXT,
    trigger_id INTEGER,
    trigger_value INTEGER
);

CREATE TABLE user_badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    badge_id INTEGER NOT NULL,
    award_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (badge_id) REFERENCES badges (id),
    UNIQUE(user_id, badge_id)
);

CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE user_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (skill_id) REFERENCES skills (id),
    UNIQUE(user_id, skill_id)
);

CREATE TABLE certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    issue_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (course_id) REFERENCES courses (id),
    UNIQUE(user_id, course_id)
);

CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER,
    topic_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    time_limit INTEGER, -- in minutes
    passing_score INTEGER DEFAULT 70,
    max_attempts INTEGER DEFAULT 3,
    FOREIGN KEY (module_id) REFERENCES modules (id),
    FOREIGN KEY (topic_id) REFERENCES topics (id)
);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL, -- 'multiple_choice', 'true_false', 'short_answer'
    points INTEGER DEFAULT 1,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);

CREATE TABLE question_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (question_id) REFERENCES questions (id)
);

CREATE TABLE quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score INTEGER,
    time_taken INTEGER, -- in seconds
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);

CREATE TABLE quiz_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    response_text TEXT,
    is_correct BOOLEAN,
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts (id),
    FOREIGN KEY (question_id) REFERENCES questions (id)
);

CREATE TABLE adaptive_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);

CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    subject TEXT NOT NULL,
    difficulty_level TEXT NOT NULL,
    points INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE completed_quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);

CREATE TABLE quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    class TEXT NOT NULL,
    subject TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    score INTEGER NOT NULL,
    time_taken INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE quiz_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_data TEXT NOT NULL,  -- JSON string containing detailed question results
    recommendations TEXT,         -- JSON string containing recommendations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quiz_results(id)
);

-- Add a trigger to update user points when completing a quiz
CREATE TRIGGER update_points_after_quiz
AFTER INSERT ON quiz_attempts
WHEN NEW.score >= (SELECT passing_score FROM quizzes WHERE id = NEW.quiz_id)
BEGIN
    UPDATE user_progress
    SET total_points = total_points + (
        SELECT points FROM modules m
        JOIN quizzes q ON q.module_id = m.id
        WHERE q.id = NEW.quiz_id
    )
    WHERE user_id = NEW.user_id;
END;

-- Insert some initial data
INSERT INTO badges (name, description, image_url, trigger_type, trigger_value)
VALUES 
('First Day', 'Completed your first day of learning', '/static/images/badges/first_day.png', 'login', 1),
('Week Warrior', 'Maintained a 7-day streak', '/static/images/badges/week_warrior.png', 'streak', 7),
('Month Master', 'Maintained a 30-day streak', '/static/images/badges/month_master.png', 'streak', 30),
('Quiz Ace', 'Got 100% on a quiz', '/static/images/badges/quiz_ace.png', 'quiz_score', 100),
('Point Collector', 'Earned 1000 points', '/static/images/badges/point_collector.png', 'points', 1000);

-- Insert some skill categories
INSERT INTO skills (name, category)
VALUES
('Addition', 'Math'),
('Subtraction', 'Math'),
('Multiplication', 'Math'),
('Division', 'Math'),
('Fractions', 'Math'),
('Planets', 'Science'),
('Animals', 'Science'),
('Plants', 'Science'),
('Weather', 'Science'),
('Energy', 'Science'),
('Nouns', 'English'),
('Verbs', 'English'),
('Adjectives', 'English'),
('Sentence Structure', 'English'),
('Reading Comprehension', 'English');

-- Insert some initial topics
INSERT INTO topics (title, description, subject, difficulty_level, points)
VALUES
('Basic Arithmetic', 'Introduction to addition, subtraction, multiplication, and division', 'Mathematics', 'Beginner', 10),
('Algebra Basics', 'Introduction to variables, equations, and expressions', 'Mathematics', 'Intermediate', 15),
('Geometry Fundamentals', 'Basic shapes, angles, and measurements', 'Mathematics', 'Intermediate', 15),
('Physics Basics', 'Introduction to motion, force, and energy', 'Science', 'Beginner', 10),
('Chemistry Elements', 'Understanding elements, compounds, and reactions', 'Science', 'Intermediate', 15),
('Biology Basics', 'Introduction to cells, organisms, and ecosystems', 'Science', 'Beginner', 10),
('Grammar Essentials', 'Basic grammar rules and sentence structure', 'English', 'Beginner', 10),
('Reading Comprehension', 'Understanding and analyzing texts', 'English', 'Intermediate', 15),
('World History', 'Major events and civilizations in world history', 'Social Studies', 'Intermediate', 15),
('Geography Basics', 'Understanding maps, continents, and countries', 'Social Studies', 'Beginner', 10);

-- Insert some initial quizzes
INSERT INTO quizzes (topic_id, title, description, time_limit, passing_score)
VALUES
(1, 'Basic Arithmetic Quiz', 'Test your knowledge of basic arithmetic operations', 30, 70),
(2, 'Algebra Basics Quiz', 'Test your understanding of basic algebra concepts', 30, 70),
(3, 'Geometry Fundamentals Quiz', 'Test your knowledge of basic geometry', 30, 70),
(4, 'Physics Basics Quiz', 'Test your understanding of basic physics concepts', 30, 70),
(5, 'Chemistry Elements Quiz', 'Test your knowledge of chemical elements', 30, 70),
(6, 'Biology Basics Quiz', 'Test your understanding of basic biology', 30, 70),
(7, 'Grammar Essentials Quiz', 'Test your knowledge of basic grammar rules', 30, 70),
(8, 'Reading Comprehension Quiz', 'Test your reading comprehension skills', 30, 70),
(9, 'World History Quiz', 'Test your knowledge of world history', 30, 70),
(10, 'Geography Basics Quiz', 'Test your understanding of basic geography', 30, 70);