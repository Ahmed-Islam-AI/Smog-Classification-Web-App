import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np

# Load environment variables
load_dotenv()

# API Keys from environment variables
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Initialize Flask App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit for uploads
app.secret_key = os.getenv('SECRET_KEY')

# Allowed image extensions for fog classification
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Load the fog classification model only once at app startup
try:
    model = load_model(os.path.join('saved-model', 'mblnet_model.keras'))  # Corrected path
except Exception as e:
    model = None
    print(f"Error loading model: {str(e)}")  # Log the error and handle gracefully

# Helper function to check for allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to preprocess the image for prediction
def preprocess_image(img_path, target_size=(224, 224)):
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    img_array /= 255.0  # Normalize the image (adjust if required by your model)
    return img_array

# Route for Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Route to get weather data by city and country using Weatherstack API
@app.route('/weather', methods=['POST', 'GET'])
def get_weather():
    if request.method == 'POST':
        city = request.form.get('city')
        country = request.form.get('country', '')  # Default to empty if not provided

        if not city:
            flash('City field is required!')
            return redirect(url_for('index'))

        base_url = "http://api.weatherstack.com/current"
        query = f"{city},{country}" if country else city
        params = {
            'access_key': WEATHER_API_KEY,
            'query': query
        }

        try:
            response = requests.get(base_url, params=params)
            weather_response = response.json()

            if response.status_code == 200:
                # Check if the response contains weather data
                if 'error' in weather_response:
                    flash(f"Error: {weather_response['error']['info']}")
                    return redirect(url_for('index'))

                # Extract weather condition information
                weather_condition = weather_response['current']['weather_descriptions'][0].lower()
                is_foggy = 'fog' in weather_condition

                # Render weather data
                return render_template('weather.html', weather=weather_response, is_foggy=is_foggy)
            else:
                flash('Unable to fetch weather data.')
                return redirect(url_for('index'))

        except requests.exceptions.RequestException as e:
            flash(f"Network error: {str(e)}")
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

# Route to classify fog from an uploaded image using the model
@app.route('/classify', methods=['POST', 'GET'])
def classify_fog():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Preprocess the image for the model
        img = preprocess_image(file_path)

        try:
            # Use the model to predict if the image contains fog
            prediction = model.predict(img)

            # Assuming the model returns a probability where fog is predicted if > 0.5
            is_foggy = prediction[0][0] > 0.5  # Adjust threshold if necessary

            # Render the result template with prediction result
            return render_template('classify.html', filename=filename, is_foggy=is_foggy)
        
        except Exception as e:
            flash(f"Error processing the image: {str(e)}")
            return redirect(url_for('index'))

    flash('File not allowed or missing')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
