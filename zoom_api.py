import logging
import requests
import json
import time
import base64
from datetime import datetime, timedelta
from config import ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID, ZOOM_USER_ID
from app import db
from models import Log

logger = logging.getLogger(__name__)

class ZoomAPI:
    """Class to handle Zoom API interactions using OAuth authentication"""
    
    def __init__(self):
        """Initialize the Zoom API with OAuth credentials"""
        self.client_id = ZOOM_CLIENT_ID
        self.client_secret = ZOOM_CLIENT_SECRET
        self.account_id = ZOOM_ACCOUNT_ID
        self.user_id = ZOOM_USER_ID
        self.access_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("Zoom API credentials not found. Zoom integration will be simulated.")
        else:
            logger.info("Zoom API initialized with OAuth")
    
    def _get_oauth_token(self):
        """
        Get an OAuth access token for Zoom API authentication.
        
        Returns:
            str: OAuth access token or None if failed
        """
        # Return existing token if it's still valid
        if self.access_token and self.token_expires_at and datetime.utcnow() < self.token_expires_at:
            return self.access_token
            
        if not self.client_id or not self.client_secret:
            return None
            
        # Prepare authentication string
        auth_string = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        # OAuth token endpoint
        endpoint = "https://zoom.us/oauth/token"
        
        # Headers
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Request body
        data = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }
        
        try:
            # Make request to get OAuth token
            response = requests.post(endpoint, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info("Successfully obtained Zoom OAuth token")
                return self.access_token
            else:
                logger.error(f"Failed to get Zoom OAuth token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception when getting Zoom OAuth token: {str(e)}")
            return None
    
    def create_meeting(self, course):
        """
        Create a Zoom meeting for a course.
        
        Args:
            course (Course): Course object containing meeting details
            
        Returns:
            dict: Dictionary with meeting details including join_url
        """
        # If missing API credentials, return a simulated response
        if not self.client_id or not self.client_secret:
            logger.warning("Using simulated Zoom meeting creation")
            # Create a simulated meeting link
            simulated_id = f"{int(time.time())}-{course.id}"
            return {
                "id": simulated_id,
                "join_url": f"https://zoom.us/j/{simulated_id}",
                "simulated": True
            }
        
        token = self._get_oauth_token()
        if not token:
            logger.error("Failed to obtain OAuth token for Zoom API")
            # Create a simulated meeting link as fallback
            simulated_id = f"{int(time.time())}-{course.id}"
            return {
                "id": simulated_id,
                "join_url": f"https://zoom.us/j/{simulated_id}",
                "simulated": True
            }
            
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
        # If missing API credentials or meeting ID, return False
        if not self.client_id or not self.client_secret or not meeting_id:
            return False
            
        token = self._get_oauth_token()
        if not token:
            logger.error("Failed to obtain OAuth token for Zoom API")
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