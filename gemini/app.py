from flask import Flask, render_template, request, session
import os
# from werkzeug.utils import secure_filename
from IPython.display import Markdown
import textwrap
from PyPDF2 import PdfReader
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Flask app
app = Flask(__name__)

# Configure Google Generative AI
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# model = genai.GenerativeModel('gemini-pro')
# chat = model.start_chat(history=[])
app.secret_key="AIzaSyDZEMVPe"
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])

def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# Function to process PDF and generate summary
def process_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        text1 = ""
        for page in reader.pages:
            text1 += page.extract_text()
    response = chat.send_message(["summrize the text", text1])
    summary = response.text
    return summary

# Function to generate quiz questions
def generate_quiz(text):
    prompt = """"return a json file which actaully contains 10 questions generated based on the given text with 4 options(1,2,3,4) and answer(option number) for it.example format 
{
    "questions":[
    {
        "question_number": 1,
        "question": "What is the capital of France?",
        "options": [
          {"a" : "London"},
          {"b" : "Paris"},
          {"c" : "Berlin"},
          {"d" : "Rome"}
        ],
        "answer": "b"
      }
    ]
}
"""
    response = chat.send_message([prompt,text])
    json_str = response.text[response.text.find('{'):response.text.rfind('}')+1]
    jsond = json.loads(json_str)
    return jsond['questions']

# Function to calculate score
def calculate_score(answers, quiz_questions):
    score = 0
    for i, question in enumerate(quiz_questions):
        if answers.get(str(i)) == question['answer']:
            score += 1
    return score

# Routes
@app.route('/')
def index():
    return render_template('index.html')
print("Hello")
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        summary = process_pdf(file_path)
        session['summary'] = summary
        return render_template('summary.html', summary=summary)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        quiz_questions = session.get('quiz_questions')
        if quiz_questions:
            score = calculate_score(request.form, quiz_questions)
            return render_template('score.html', score=score)
        else:
            return "No quiz questions available"
    else:
        text = session.get('summary')
        if text:
            quiz_questions = generate_quiz(text)
            session['quiz_questions'] = quiz_questions
            return render_template('quiz.html', questions=quiz_questions)
        else:
            return "No text available for quiz"

if __name__ == '__main__':
    app.run(debug=True)
