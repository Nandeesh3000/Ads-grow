from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import io
import base64
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline
import matplotlib.pyplot as plt
import torch
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

model_id1 = "dreamlike-art/dreamlike-diffusion-1.0"
pipe = StableDiffusionPipeline.from_pretrained(model_id1, torch_dtype=torch.float32)

# Function to create SQLite3 database and table
def create_user_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 email TEXT UNIQUE NOT NULL, 
                 password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

create_user_table()

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['user_id']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]  # Save user ID in session
            return redirect(url_for('generator'))
        else:
            return 'Invalid email or password'

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
            conn.commit()
            conn.close()

            session['email'] = email

            app.logger.info("User successfully registered: %s", email)

            return redirect(url_for('login'))

        except Exception as e:
            app.logger.error("Error occurred during signup: %s", str(e))
            return "An error occurred during signup. Please try again later."

    return render_template('signup.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/generator', methods=['GET', 'POST'])
def generator():
    if request.method == 'POST':
        prompt = request.form.get('prompt', '')

        if not prompt:
            return render_template('generator.html', error="Prompt is required")

        processed_prompt = "[PROMPT]: " + prompt

        with torch.no_grad():
            image = pipe(processed_prompt)

        image_array = image.cpu().numpy()

        plt.imshow(image_array)
        plt.axis('off')

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        img_str = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

        return render_template('generator.html', image=img_str)

    return render_template('generator.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True)
