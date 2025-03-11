import logging
import requests
import json
import time
import jwt
from datetime import datetime, timedelta
from config import ZOOM_API_KEY, ZOOM_API_SECRET, ZOOM_USER_ID
from app import db
from models import Log

logger = logging.getLogger(__name__)

class ZoomAPI:
    """Class to handle Zoom API interactions"""
    
    def __init__(self):
        """Initialize the Zoom API with credentials"""
        self.api_key = ZOOM_API_KEY
        self.api_secret = ZOOM_API_SECRET
        self.user_id = ZOOM_USER_ID
        
        if not self.api_key or not self.api_secret:
            logger.warning("Zoom API credentials not found. Zoom integration will be simulated.")
        else:
            logger.info("Zoom API initialized")
    
    def _generate_jwt_token(self):
        """
        Generate a JWT token for Zoom API authentication.
        
        Returns:
            str: JWT token
        """
        if not self.api_key or not self.api_secret:
            return None
            
        # Set token expiration time (1 hour)
        token_exp = datetime.utcnow() + timedelta(hours=1)
        
        # Create payload
        payload = {
            'iss': self.api_key,
            'exp': int(token_exp.timestamp())
        }
        
        # Generate token
        token = jwt.encode(payload, self.api_secret, algorithm='HS256')
        
        # If token is bytes, convert to string (depends on jwt version)
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
    
    def create_meeting(self, course):
        """
        Create a Zoom meeting for a course.
        
        Args:
            course (Course): Course object containing meeting details
            
        Returns:
            dict: Dictionary with meeting details including join_url
        """
        # If missing API credentials, return a simulated response
        if not self.api_key or not self.api_secret:
            logger.warning("Using simulated Zoom meeting creation")
            # Create a simulated meeting link
            simulated_id = f"{int(time.time())}-{course.id}"
            return {
                "id": simulated_id,
                "join_url": f"https://zoom.us/j/{simulated_id}",
                "simulated": True
            }
        
        token = self._generate_jwt_token()
        if not token:
            logger.error("Failed to generate JWT token for Zoom API")
            return None
            
        # Format the meeting details
        start_time = datetime.combine(course.schedule_date, course.start_time)
        formatted_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Duration in minutes
        duration = int((datetime.combine(course.schedule_date, course.end_time) - 
                     datetime.combine(course.schedule_date, course.start_time)).total_seconds() / 60)
        
        # Meeting request data
        meeting_data = {
            "topic": f"{course.course_name} with {course.teacher_name}",
            "type": 2,  # Scheduled meeting
            "start_time": formatted_time,
            "duration": duration,
            "timezone": "UTC",
            "agenda": f"Course session for {course.course_name}",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": True,
                "waiting_room": False,
                "auto_recording": "none"
            }
        }
        
        # API endpoint
        endpoint = f"https://api.zoom.us/v2/users/{self.user_id}/meetings"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make request to Zoom API
            response = requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(meeting_data)
            )
            
            # Check if request was successful
            if response.status_code == 201:
                meeting_info = response.json()
                logger.info(f"Successfully created Zoom meeting for course {course.id}")
                return {
                    "id": meeting_info.get('id'),
                    "join_url": meeting_info.get('join_url')
                }
            else:
                logger.error(f"Failed to create Zoom meeting: {response.text}")
                # Log the error to the database
                log_entry = Log(
                    level="ERROR", 
                    scenario="zoom_creation", 
                    message=f"Failed to create Zoom meeting for course {course.id}: {response.text}"
                )
                db.session.add(log_entry)
                db.session.commit()
                return None
                
        except Exception as e:
            error_msg = f"Exception when creating Zoom meeting: {str(e)}"
            logger.error(error_msg)
            # Log the error to the database
            log_entry = Log(
                level="ERROR", 
                scenario="zoom_creation", 
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()
            return None
    
    def check_meeting_exists(self, meeting_id):
        """
        Check if a Zoom meeting exists.
        
        Args:
            meeting_id (str): Zoom meeting ID
            
        Returns:
            bool: True if meeting exists, False otherwise
        """
        # If missing API credentials, return True for testing
        if not self.api_key or not self.api_secret or not meeting_id:
            return False
            
        token = self._generate_jwt_token()
        if not token:
            logger.error("Failed to generate JWT token for Zoom API")
            return False
            
        # API endpoint
        endpoint = f"https://api.zoom.us/v2/meetings/{meeting_id}"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            # Make request to Zoom API
            response = requests.get(endpoint, headers=headers)
            
            # Check if meeting exists
            return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Exception when checking Zoom meeting: {str(e)}")
            return False

# Create a global instance of the Zoom API
zoom_api = ZoomAPI()
