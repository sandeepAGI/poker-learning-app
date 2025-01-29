from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def home():
    return "Hello, Poker App!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

