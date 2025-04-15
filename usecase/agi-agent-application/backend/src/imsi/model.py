from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()


class PDFFile(db.Model):
    __tablename__ = 'pdf_files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    file_url = db.Column(db.String(512), nullable=False)  # 저장 경로나 URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)