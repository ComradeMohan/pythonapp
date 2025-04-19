import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from rq import Queue
from rq.job import Job
from redis import Redis
import datetime
import time
from models import db, Enrollment
from tasks import check_course_availability

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///enrollments.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize Redis and RQ
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)
queue = Queue('enrollment_queue', connection=redis_conn)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/enroll', methods=['POST'])
def enroll():
    # Get form data
    course_name = request.form['course_name']
    slot = request.form['slot']
    phone_number = request.form['phone_number']
    
    # Create enrollment record
    enrollment = Enrollment(
        course_name=course_name,
        slot=slot,
        phone_number=phone_number,
        status="pending"
    )
    db.session.add(enrollment)
    db.session.commit()
    
    # Queue background job
    job = queue.enqueue(
        check_course_availability,
        enrollment.id,
        course_name,
        slot,
        phone_number,
        job_timeout=3600  # 1 hour timeout
    )
    
    # Update enrollment with job ID
    enrollment.job_id = job.id
    db.session.commit()
    
    return render_template('success.html', course_name=course_name, phone_number=phone_number)

@app.route('/status/<int:enrollment_id>')
def status(enrollment_id):
    """Check the status of an enrollment"""
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    return jsonify({
        'id': enrollment.id,
        'course_name': enrollment.course_name,
        'status': enrollment.status,
        'created_at': enrollment.created_at.isoformat(),
        'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
        'vacancies': enrollment.vacancies
    })

@app.route('/enrollments')
def enrollments():
    """View all enrollments"""
    enrollments = Enrollment.query.order_by(Enrollment.created_at.desc()).all()
    return render_template('enrollments.html', enrollments=enrollments)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
