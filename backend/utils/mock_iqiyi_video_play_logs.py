import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import random
from datetime import datetime, timedelta
import uuid
from config.constants import INITIAL_DATA_DIR

def generate_iqiyi_data(num_records=1000, start_date="2025-03-10", end_date="2025-03-25", video_id_list=None):
    """
    Generate synthetic data for iQiYi video play logs
    
    Args:
        num_records: Number of records to generate
        start_date: Start date for dt partition (YYYY-MM-DD)
        end_date: End date for dt partition (YYYY-MM-DD)
        video_id_list: List of video IDs to use
    
    Returns:
        Dictionary containing the generated data
    """
    if video_id_list is None:
        video_id_list = [5001234579, 5001234580, 5001234581, 5001234582, 5001234583, 
                         5001234584, 5001234585, 5001234586, 5001234587, 5001234588, 
                         5001234589, 5001234590]
    
    # Convert dates to datetime objects
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Define possible values for enum fields
    playback_qualities = ["240p", "360p", "480p", "720p", "1080p"]
    network_types = ["wifi", "4g", "5g"]
    device_types = ["mobile", "tablet", "pc", "tv", "other"]
    
    # App versions
    app_versions = ["9.8.5", "9.9.0", "10.0.0", "10.0.1", "10.1.0", "10.2.0"]
    
    # Generate user_ids (simulate a user base of about 500 users)
    user_ids = [random.randint(10000000, 99999999) for _ in range(500)]
    
    # Generate device_ids (simulate about 700 unique devices)
    device_ids = [str(uuid.uuid4())[:16] for _ in range(700)]
    
    # Video durations for each video_id (in seconds)
    video_durations = {vid: random.choice([1800, 2400, 3000, 3600, 4500, 5400, 6000, 7200]) for vid in video_id_list}
    
    # Generate logs
    logs = []
    for i in range(num_records):
        # Generate a random date within the range
        days_diff = (end_dt - start_dt).days
        random_day = random.randint(0, days_diff)
        log_date = start_dt + timedelta(days=random_day)
        dt = log_date.strftime("%Y-%m-%d")
        
        # Select a random user and device
        user_id = random.choice(user_ids)
        device_id = random.choice(device_ids)
        
        # Select a random video
        video_id = random.choice(video_id_list)
        video_duration = video_durations[video_id]
        
        # Generate viewing time details
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        start_time = datetime(
            log_date.year, log_date.month, log_date.day, 
            hour, minute, second
        )
        
        # Duration is typically less than or equal to the video duration
        # Some users watch partial videos, some watch full videos
        completion_rate = random.choice([0.1, 0.25, 0.5, 0.75, 0.9, 1.0])
        duration = int(video_duration * completion_rate)
        
        # Add some randomness to duration to make it more realistic
        duration = max(10, min(video_duration, int(duration * random.uniform(0.95, 1.05))))
        
        # Calculate end time based on start time and duration
        end_time = start_time + timedelta(seconds=duration)
        
        # Select playback quality (higher probability for higher qualities)
        quality_weights = [0.05, 0.15, 0.25, 0.35, 0.2]  # Favoring HD content
        playback_quality = random.choices(playback_qualities, weights=quality_weights)[0]
        
        # Select network type (wifi more common)
        network_weights = [0.6, 0.25, 0.15]  # WiFi is most common
        network_type = random.choices(network_types, weights=network_weights)[0]
        
        # Select device type (mobile most common)
        device_weights = [0.5, 0.15, 0.2, 0.1, 0.05]
        device_type = random.choices(device_types, weights=device_weights)[0]
        
        # App version (newer versions more common)
        app_version = random.choices(app_versions, weights=[0.05, 0.1, 0.2, 0.25, 0.3, 0.1])[0]
        
        # Create log entry
        log = {
            "log_id": 1000000000 + i,
            "user_id": user_id,
            "video_id": video_id,
            "device_id": device_id,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration,
            "video_duration": video_duration,
            "playback_quality": playback_quality,
            "network_type": network_type,
            "device_type": device_type,
            "app_version": app_version,
            "dt": dt
        }
        logs.append(log)
    
    return {"video_play_logs": logs}
