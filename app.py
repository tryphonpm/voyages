from flask import Flask, render_template, send_from_directory, jsonify, request
import json
import os

app = Flask(__name__)

# Configuration
IMAGE_DIR = r"E:\202507_Lres"
METADATA_FILE = "images_metadata.json"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/images')
def get_images_data():
    date_filter = request.args.get('date')
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if date_filter:
            data = [img for img in data if img.get('date') == date_filter]
            
        return jsonify(data)
    return jsonify([])

@app.route('/api/dates')
def get_dates():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Extract unique dates and sort them
        dates = sorted(list(set(img.get('date') for img in data if img.get('date'))))
        return jsonify(dates)
    return jsonify([])

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)

