import os
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    slot = db.Column(db.String(2), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, running, completed, failed
    job_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    vacancies = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Enrollment {self.course_name} for {self.phone_number}>'
