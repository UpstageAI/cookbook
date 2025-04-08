import os
import shutil
from flask import Flask
from flask_cors import CORS 
from routes.standardize import standardize_bp
import logging

app = Flask(__name__)
CORS(app)
app.register_blueprint(standardize_bp)  # Route split using blueprint

logging.getLogger('flask_cors').level = logging.DEBUG

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'DELETE, GET, OPTIONS, POST, PUT')
    return response

if __name__ == "__main__":
    app.run(debug=True)
