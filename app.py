from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import boto3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
table = dynamodb.Table('Users')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        try:
            table.put_item(
               Item={
                    'email': email,
                    'password': password
                }
            )
        except Exception as e:
            return f"An error occurred: {e}"
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        response = table.get_item(
            Key={'email': email}
        )
        user = response.get('Item')
        if user and check_password_hash(user['password'], password):
            session['user_email'] = user['email']
            return redirect(url_for('chat'))
        else:
            return "Invalid username or password"
    return render_template('login.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user_email = session.get('user_email')
    if not user_email:
        return jsonify({'error': 'User not logged in'}), 401

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            if 'answer' not in data:
                return jsonify({'error': 'Bad Request, no answer provided'}), 400

            questions = ["What is your name?", "How old are you?", "What is your sex?", "What are your interests?"]
            answers = ["name", "age", "sex", "interests"]

            index = session.get('question_index', 0)
            response = table.get_item(Key={'email': user_email})
            user = response.get('Item')
            user[answers[index]] = data['answer']
            table.put_item(Item=user)
            index += 1

            if index < len(questions):
                session['question_index'] = index
                return jsonify(question=questions[index])
            else:
                session.pop('question_index', None)
                return jsonify(message="All your information is saved.")
        else:
            return jsonify({'error': 'Request must be JSON'}), 415  
    else:  
        return render_template('chat.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

