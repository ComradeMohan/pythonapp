import sys
import os

# Add your project directory to the sys.path
project_home = '/home/comrademohan143/course_enrollment'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Activate the virtual environment
activate_this = '/home/comrademohan143/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), dict(__file__=activate_this))
else:
    print(f"Error: Virtual environment file {activate_this} not found.")

# Import Flask app but need to call it "application" for WSGI to work
from app import app as application  # noqa
