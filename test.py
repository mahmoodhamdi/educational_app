"""
API Testing Script for Educational App
This script tests all the main endpoints of the educational app API
"""

import requests
import json
import time
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL: Replace with your actual base URL (e.g., https://<your-domain>.pythonanywhere.com)
BASE_URL = "https://<your-domain>.pythonanywhere.com"

def test_register_and_login():
    """Test user registration and login"""
    logger.info("🔐 Testing User Registration and Login...")
    
    random_suffix = random.randint(1000, 9999)
    
    # Test Admin Registration
    admin_data = {
        "name": "Admin User",
        "email": f"admin{random_suffix}@test.com",
        "password": "admin123",
        "role": "admin",
        "picture": "https://example.com/admin.jpg"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=admin_data, timeout=5)
        logger.info(f"Admin Registration: {response.status_code}")
        if response.status_code == 201:
            admin_token = response.json()['token']
            admin_id = response.json()['id']
            logger.info("✅ Admin registered successfully")
        else:
            logger.error(f"❌ Admin registration failed: {response.text}")
            return None, None, None
    except requests.RequestException as e:
        logger.error(f"❌ Admin registration error: {str(e)}")
        return None, None, None
    
    # Test Client Registration
    client_data = {
        "name": "Student User",
        "email": f"student{random_suffix}@test.com",
        "password": "student123",
        "role": "client",
        "picture": "https://example.com/student.jpg"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=client_data, timeout=5)
        logger.info(f"Client Registration: {response.status_code}")
        if response.status_code == 201:
            client_token = response.json()['token']
            client_id = response.json()['id']
            logger.info("✅ Client registered successfully")
        else:
            logger.error(f"❌ Client registration failed: {response.text}")
            return admin_token, None, None
    except requests.RequestException as e:
        logger.error(f"❌ Client registration error: {str(e)}")
        return admin_token, None, None
    
    # Test Login
    login_data = {
        "email": f"admin{random_suffix}@test.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data, timeout=5)
        logger.info(f"Admin Login: {response.status_code}")
        if response.status_code == 200:
            logger.info("✅ Admin login successful")
        else:
            logger.error(f"❌ Admin login failed: {response.text}")
    except requests.RequestException as e:
        logger.error(f"❌ Admin login error: {str(e)}")
    
    return admin_token, client_token, client_id

def test_level_management(admin_token):
    """Test level creation and management"""
    logger.info("\n📖 Testing Level Management...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    level_data = {
        "name": "Test Level 1",
        "description": "This is a test level for API testing",
        "welcome_video_url": "https://youtube.com/watch?v=test123",
        "price": 49.99,
        "initial_exam_question": "What do you expect to learn?",
        "final_exam_question": "What did you learn from this level?"
    }
    
    # Path to a test image file (replace with actual path)
    files = {
        "file": ("test-level.jpg", open("/path/to/your/test-level.jpg", "rb"), "image/jpeg")
    }
    
    try:
        response = requests.post(f"{BASE_URL}/levels", data=level_data, files=files, headers=headers, timeout=5)
        logger.info(f"Create Level: {response.status_code}")
        if response.status_code == 201:
            level_id = response.json()['id']
            logger.info(f"✅ Level created successfully with ID: {level_id}")
            return level_id
        else:
            logger.error(f"❌ Level creation failed: {response.text}")
            return None
    except requests.RequestException as e:
        logger.error(f"❌ Level creation error: {str(e)}")
        return None
    finally:
        if files["file"] and not files["file"][1].closed:
            files["file"][1].close()

def test_video_management(admin_token, level_id):
    """Test video creation and management"""
    logger.info("\n🎥 Testing Video Management...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    videos = [
        {
            "youtube_link": "https://youtube.com/watch?v=video1",
            "questions": ["What is the main concept in video 1?", "How does this apply?"]
        },
        {
            "youtube_link": "https://youtube.com/watch?v=video2",
            "questions": ["What is the main concept in video 2?", "Can you give an example?"]
        },
        {
            "youtube_link": "https://youtube.com/watch?v=video3",
            "questions": ["What is the main concept in video 3?", "How does this relate to previous videos?"]
        }
    ]
    
    video_ids = []
    for i, video_data in enumerate(videos):
        try:
            response = requests.post(f"{BASE_URL}/levels/{level_id}/videos", json=video_data, headers=headers, timeout=5)
            logger.info(f"Create Video {i+1}: {response.status_code}")
            if response.status_code == 201:
                video_id = response.json()['id']
                video_ids.append(video_id)
                logger.info(f"✅ Video {i+1} created successfully with ID: {video_id}")
            else:
                logger.error(f"❌ Video {i+1} creation failed: {response.text}")
        except requests.RequestException as e:
            logger.error(f"❌ Video {i+1} creation error: {str(e)}")
    
    return video_ids

def test_level_purchase_and_progress(client_token, client_id, level_id):
    """Test level purchase and progress tracking"""
    logger.info("\n🛒 Testing Level Purchase and Progress...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/users/{client_id}/levels/{level_id}/purchase", headers=headers, timeout=5)
        logger.info(f"Purchase Level: {response.status_code}")
        if response.status_code == 201:
            logger.info("✅ Level purchased successfully")
        else:
            logger.error(f"❌ Level purchase failed: {response.text}")
            return
    except requests.RequestException as e:
        logger.error(f"❌ Level purchase error: {str(e)}")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/users/{client_id}/levels", headers=headers, timeout=5)
        logger.info(f"Get User Levels: {response.status_code}")
        if response.status_code == 200:
            levels = response.json()
            logger.info(f"✅ User has {len(levels)} purchased level(s)")
            if levels:
                logger.info(f"   Level: {levels[0]['level_name']}")
                logger.info(f"   Progress: {levels[0]['completed_videos_count']}/{levels[0]['total_videos_count']} videos")
        else:
            logger.error(f"❌ Get user levels failed: {response.text}")
    except requests.RequestException as e:
        logger.error(f"❌ Get user levels error: {str(e)}")

def test_exam_system(client_token, client_id, level_id):
    """Test exam submission"""
    logger.info("\n📝 Testing Exam System...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    initial_exam_data = {
        "correct_words": 15,
        "wrong_words": 5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/exams/{level_id}/initial", json=initial_exam_data, headers=headers, timeout=5)
        logger.info(f"Submit Initial Exam: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            logger.info(f"✅ Initial exam submitted successfully")
            logger.info(f"   Score: {result['percentage']}% ({result['correct_words']}/{result['correct_words'] + result['wrong_words']})")
        else:
            logger.error(f"❌ Initial exam submission failed: {response.text}")
    except requests.RequestException as e:
        logger.error(f"❌ Initial exam submission error: {str(e)}")

def test_video_completion(client_token, client_id, level_id, video_ids):
    """Test video completion and progression"""
    logger.info("\n▶️ Testing Video Completion...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    for i, video_id in enumerate(video_ids):
        try:
            response = requests.patch(f"{BASE_URL}/users/{client_id}/levels/{level_id}/videos/{video_id}/complete", headers=headers, timeout=5)
            logger.info(f"Complete Video {i+1}: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"✅ Video {i+1} completed successfully")
            else:
                logger.error(f"❌ Video {i+1} completion failed: {response.text}")
        except requests.RequestException as e:
            logger.error(f"❌ Video {i+1} completion error: {str(e)}")
        
        time.sleep(0.5)

def test_final_exam(client_token, client_id, level_id):
    """Test final exam submission"""
    logger.info("\n🎓 Testing Final Exam...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    final_exam_data = {
        "correct_words": 18,
        "wrong_words": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/exams/{level_id}/final", json=final_exam_data, headers=headers, timeout=5)
        logger.info(f"Submit Final Exam: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            logger.info(f"✅ Final exam submitted successfully")
            logger.info(f"   Score: {result['percentage']}% ({result['correct_words']}/{result['correct_words'] + result['wrong_words']})")
        else:
            logger.error(f"❌ Final exam submission failed: {response.text}")
    except requests.RequestException as e:
        logger.error(f"❌ Final exam submission error: {str(e)}")

def test_admin_statistics(admin_token, client_id):
    """Test admin statistics endpoints"""
    logger.info("\n📊 Testing Admin Statistics...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/admin/statistics", headers=headers, timeout=5)
        logger.info(f"Get Admin Statistics: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            logger.info("✅ Admin statistics retrieved successfully")
            logger.info(f"   Total Users: {stats['total_users']}")
            logger.info(f"   Total Levels: {stats['total_levels']}")
            logger.info(f"   Total Purchases: {stats['total_purchases']}")
            logger.info(f"   Completion Rate: {stats['completion_rate']}%")
        else:
            logger.error(f"❌ Admin statistics failed: {response.text}")
    except requests.RequestException as e:
        logger.error(f"❌ Admin statistics error: {str(e)}")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/users/{client_id}/statistics", headers=headers, timeout=5)
        logger.info(f"Get User Statistics: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            logger.info("✅ User statistics retrieved successfully")
            logger.info(f"   User: {stats['user_name']}")
            logger.info(f"   Purchased Levels: {stats['purchased_levels']}")
            logger.info(f"   Completed Levels: {stats['completed_levels']}")
            logger.info(f"   Average Improvement: {stats['average_improvement']}%")
        else:
            logger.error(f"❌ User statistics failed: {response.text}")
    except requests.RequestException as e:
        logger.error(f"❌ User statistics error: {str(e)}")

def main():
    """Run all API tests"""
    logger.info("🚀 Starting Educational App API Tests...\n")
    
    result = test_register_and_login()
    if not result or len(result) < 3:
        logger.error("❌ Authentication tests failed. Stopping.")
        return
    
    admin_token, client_token, client_id = result
    
    level_id = test_level_management(admin_token)
    if not level_id:
        logger.error("❌ Level management tests failed. Stopping.")
        return
    
    video_ids = test_video_management(admin_token, level_id)
    if not video_ids:
        logger.error("❌ Video management tests failed. Stopping.")
        return
    
    test_level_purchase_and_progress(client_token, client_id, level_id)
    test_exam_system(client_token, client_id, level_id)
    test_video_completion(client_token, client_id, level_id, video_ids)
    test_final_exam(client_token, client_id, level_id)
    test_admin_statistics(admin_token, client_id)
    
    logger.info("\n🎉 All API tests completed!")

if __name__ == "__main__":
    main()