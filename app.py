from flask import Flask, render_template, Response, jsonify, request
import pymongo
import gridfs
import face_recognition
import cv2
import numpy as np
import logging
from fer import FER
import datetime
import os
import sqlite3
import requests
import base64
import datetime

app = Flask(__name__)

# MongoDB setup
client = pymongo.MongoClient('mongodb+srv://carlo-faria:chs200400@cluster0.2ltkg1a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0', serverSelectionTimeoutMS=500000)
db = client['Dbuam']
fs = gridfs.GridFS(db)
users_collection = db['users']

# SQLite setup
DATABASE = 'logs.db'

def init_sqlite_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_sqlite_db()

capture = cv2.VideoCapture(0)

# Carregar o classificador Haar para detecção de rosto
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    while True:
        success, frame = capture.read()
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/login', methods=['POST'])
def login():
    try:
        success, frame = capture.read()
        if not success:
            return jsonify({'message': 'Could not read frame from camera.'}), 500

        unknown_encodings = face_recognition.face_encodings(frame)
        if len(unknown_encodings) == 0:
            return jsonify({'message': 'No face detected. Please try again.'}), 400

        unknown_encoding = unknown_encodings[0]

        users = users_collection.find()
        known_encodings = []
        names = []

        for user in users:
            known_encodings.append(np.frombuffer(user['encoding'], dtype=np.float64))
            names.append(user['name'])

        results = face_recognition.compare_faces(known_encodings, unknown_encoding)

        if True in results:
            index = results.index(True)
            name = names[index]
        else:
            name = 'unknown_person'

        if name == 'unknown_person':
            return jsonify({'message': 'Unknown user. Please register new user or try again.'}), 400
        else:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_log_to_db(name, timestamp)
            return jsonify({'message': f'Welcome, {name}', 'name': name, 'timestamp': timestamp}), 200

    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({'message': 'An error occurred during login.'}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    image_data = data.get('image')

    if not name:
        return jsonify({'message': 'Name is required.'}), 400

    try:
        success, frame = capture.read()
        if not success:
            return jsonify({'message': 'Could not read frame from camera.'}), 500

        encodings = face_recognition.face_encodings(frame)
        if len(encodings) == 0:
            return jsonify({'message': 'No face detected. Please try again.'}), 400

        encoding = encodings[0]
        users_collection.insert_one({'name': name, 'encoding': encoding.tobytes()})

        _, img_encoded = cv2.imencode(".jpg", frame)
        fs.put(img_encoded.tobytes(), filename=f'{name}.jpg')

        return jsonify({'message': 'User registered successfully!'}), 200

    except Exception as e:
        logging.error(f"Error during user registration: {e}")
        return jsonify({'message': 'An error occurred during registration.'}), 500

@app.route('/logs')
def get_logs():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name, timestamp FROM logs")
        logs = cursor.fetchall()
        conn.close()
        if logs:
            return jsonify({'logs': [{'name': log[0], 'timestamp': datetime.datetime.strptime(log[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")} for log in logs]}), 200
        else:
            return jsonify({'message': 'No logs found.'}), 404
    except Exception as e:
        logging.error(f"Error retrieving logs: {e}")
        return jsonify({'message': 'An error occurred retrieving logs.'}), 500

@app.route('/last_login')
def last_login():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name, timestamp FROM logs ORDER BY timestamp DESC LIMIT 1")
        last_log = cursor.fetchone()
        conn.close()
        if last_log:
            formatted_timestamp = datetime.datetime.strptime(last_log[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            return jsonify({'name': last_log[0], 'timestamp': formatted_timestamp}), 200
        else:
            return jsonify({'message': 'No logs found.'}), 404
    except Exception as e:
        logging.error(f"Error retrieving last login: {e}")
        return jsonify({'message': 'An error occurred retrieving last login.'}), 500

def save_log_to_db(name, timestamp):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (name, timestamp) VALUES (?, ?)", (name, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving log to SQLite: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
