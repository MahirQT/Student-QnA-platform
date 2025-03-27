from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///askly.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(300), nullable=True)
    answer = db.Column(db.Text, nullable=True)
    answer_image_path = db.Column(db.String(300), nullable=True)  # New field for image answers
    answered_by = db.Column(db.String(100), nullable=True)  # Name of the person who answered
    role = db.Column(db.String(50), nullable=True)  # 'Teacher' or 'Senior'
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='question', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

# Routes
@app.route('/')
def student_page():
    questions = Question.query.order_by(Question.upvotes.desc()).all()
    return render_template('student.html', questions=questions)

@app.route('/submit_question', methods=['POST'])
def submit_question():
    text = request.form['text']
    image = request.files.get('image')

    image_path = None
    if image and image.filename:
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        image_filename = image.filename
        image_path = os.path.join('static/uploads', image_filename)
        image.save(image_path)

    new_question = Question(text=text, image_path=image_path)
    db.session.add(new_question)
    db.session.commit()
    return redirect(url_for('student_page'))

@app.route('/add_comment', methods=['POST'])
def add_comment():
    text = request.form['text']
    question_id = request.form['question_id']
    new_comment = Comment(text=text, question_id=question_id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('student_page'))

@app.route('/upvote/<int:question_id>', methods=['POST'])
def upvote(question_id):
    question = Question.query.get(question_id)
    if question:
        question.upvotes += 1
        db.session.commit()
    return jsonify({'upvotes': question.upvotes})

@app.route('/downvote/<int:question_id>', methods=['POST'])
def downvote(question_id):
    question = Question.query.get(question_id)
    if question:
        question.downvotes += 1
        db.session.commit()
    return jsonify({'downvotes': question.downvotes})

@app.route('/teacher')
def teacher_page():
    questions = Question.query.filter(Question.answer == None).all()
    return render_template('teacher.html', questions=questions)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    question_id = request.form['question_id']
    answer = request.form['answer']
    name = request.form['name']
    role = request.form['role']
    answer_image = request.files.get('answer_image')

    question = Question.query.get(question_id)
    
    if question:
        question.answer = answer
        question.answered_by = name
        question.role = role
        
        if answer_image and answer_image.filename:
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            image_filename = answer_image.filename
            answer_image_path = os.path.join('static/uploads', image_filename)
            answer_image.save(answer_image_path)
            question.answer_image_path = answer_image_path

        db.session.commit()

    return redirect(url_for('teacher_page'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)  
