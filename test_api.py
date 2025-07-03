#!/usr/bin/env python3
"""
API Testing Script for Educational App
This script tests all the main endpoints of the educational app API
"""

import requests
import json
import time

BASE_URL = "http://192.168.1.5:5000"

def test_register_and_login():
    """Test user registration and login"""
    print("🔐 Testing User Registration and Login...")
    
    import random
    random_suffix = random.randint(1000, 9999)
    
    # Test Admin Registration
    admin_data = {
        "name": "Admin User",
        "email": f"admin{random_suffix}@test.com",
        "password": "admin123",
        "role": "admin",
        "picture": "https://example.com/admin.jpg"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=admin_data)
    print(f"Admin Registration: {response.status_code}")
    if response.status_code == 201:
        admin_token = response.json()['token']
        print("✅ Admin registered successfully")
    else:
        print(f"❌ Admin registration failed: {response.text}")
        return None, None
    
    # Test Client Registration
    client_data = {
        "name": "Student User",
        "email": f"student{random_suffix}@test.com",
        "password": "student123",
        "role": "client",
        "picture": "https://example.com/student.jpg"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=client_data)
    print(f"Client Registration: {response.status_code}")
    if response.status_code == 201:
        client_token = response.json()['token']
        client_id = response.json()['id']
        print("✅ Client registered successfully")
    else:
        print(f"❌ Client registration failed: {response.text}")
        return admin_token, None
    
    # Test Login
    login_data = {
        "email": f"admin{random_suffix}@test.com",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"Admin Login: {response.status_code}")
    if response.status_code == 200:
        print("✅ Admin login successful")
    else:
        print(f"❌ Admin login failed: {response.text}")
    
    return admin_token, client_token, client_id

def test_level_management(admin_token):
    """Test level creation and management"""
    print("\n📖 Testing Level Management...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a level
    level_data = {
        "name": "Test Level 1",
        "description": "This is a test level for API testing",
        "welcome_video_url": "https://youtube.com/watch?v=test123",
        "image_url": "https://example.com/test-level.jpg",
        "price": 49.99,
        "initial_exam_question": "What do you expect to learn?",
        "final_exam_question": "What did you learn from this level?"
    }
    
    response = requests.post(f"{BASE_URL}/levels", json=level_data, headers=headers)
    print(f"Create Level: {response.status_code}")
    if response.status_code == 201:
        level_id = response.json()['id']
        print(f"✅ Level created successfully with ID: {level_id}")
        return level_id
    else:
        print(f"❌ Level creation failed: {response.text}")
        return None

def test_video_management(admin_token, level_id):
    """Test video creation and management"""
    print("\n🎥 Testing Video Management...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Add videos to the level
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
        response = requests.post(f"{BASE_URL}/levels/{level_id}/videos", json=video_data, headers=headers)
        print(f"Create Video {i+1}: {response.status_code}")
        if response.status_code == 201:
            video_id = response.json()['id']
            video_ids.append(video_id)
            print(f"✅ Video {i+1} created successfully with ID: {video_id}")
        else:
            print(f"❌ Video {i+1} creation failed: {response.text}")
    
    return video_ids

def test_level_purchase_and_progress(client_token, client_id, level_id):
    """Test level purchase and progress tracking"""
    print("\n🛒 Testing Level Purchase and Progress...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    # Purchase level
    response = requests.post(f"{BASE_URL}/users/{client_id}/levels/{level_id}/purchase", headers=headers)
    print(f"Purchase Level: {response.status_code}")
    if response.status_code == 201:
        print("✅ Level purchased successfully")
    else:
        print(f"❌ Level purchase failed: {response.text}")
        return
    
    # Check user levels
    response = requests.get(f"{BASE_URL}/users/{client_id}/levels", headers=headers)
    print(f"Get User Levels: {response.status_code}")
    if response.status_code == 200:
        levels = response.json()
        print(f"✅ User has {len(levels)} purchased level(s)")
        if levels:
            print(f"   Level: {levels[0]['level_name']}")
            print(f"   Progress: {levels[0]['completed_videos_count']}/{levels[0]['total_videos_count']} videos")
    else:
        print(f"❌ Get user levels failed: {response.text}")

def test_exam_system(client_token, client_id, level_id):
    """Test exam submission"""
    print("\n📝 Testing Exam System...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    # Submit initial exam
    initial_exam_data = {
        "correct_words": 15,
        "wrong_words": 5
    }
    
    response = requests.post(f"{BASE_URL}/exams/{level_id}/initial", json=initial_exam_data, headers=headers)
    print(f"Submit Initial Exam: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Initial exam submitted successfully")
        print(f"   Score: {result['percentage']}% ({result['correct_words']}/{result['correct_words'] + result['wrong_words']})")
    else:
        print(f"❌ Initial exam submission failed: {response.text}")

def test_video_completion(client_token, client_id, level_id, video_ids):
    """Test video completion and progression"""
    print("\n▶️ Testing Video Completion...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    # Complete videos one by one
    for i, video_id in enumerate(video_ids):
        response = requests.patch(f"{BASE_URL}/users/{client_id}/levels/{level_id}/videos/{video_id}/complete", headers=headers)
        print(f"Complete Video {i+1}: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Video {i+1} completed successfully")
        else:
            print(f"❌ Video {i+1} completion failed: {response.text}")
        
        # Small delay between completions
        time.sleep(0.5)

def test_final_exam(client_token, client_id, level_id):
    """Test final exam submission"""
    print("\n🎓 Testing Final Exam...")
    
    headers = {"Authorization": f"Bearer {client_token}"}
    
    # Submit final exam
    final_exam_data = {
        "correct_words": 18,
        "wrong_words": 2
    }
    
    response = requests.post(f"{BASE_URL}/exams/{level_id}/final", json=final_exam_data, headers=headers)
    print(f"Submit Final Exam: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Final exam submitted successfully")
        print(f"   Score: {result['percentage']}% ({result['correct_words']}/{result['correct_words'] + result['wrong_words']})")
    else:
        print(f"❌ Final exam submission failed: {response.text}")

def test_admin_statistics(admin_token, client_id):
    """Test admin statistics endpoints"""
    print("\n📊 Testing Admin Statistics...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get general statistics
    response = requests.get(f"{BASE_URL}/admin/statistics", headers=headers)
    print(f"Get Admin Statistics: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print("✅ Admin statistics retrieved successfully")
        print(f"   Total Users: {stats['total_users']}")
        print(f"   Total Levels: {stats['total_levels']}")
        print(f"   Total Purchases: {stats['total_purchases']}")
        print(f"   Completion Rate: {stats['completion_rate']}%")
    else:
        print(f"❌ Admin statistics failed: {response.text}")
    
    # Get user-specific statistics
    response = requests.get(f"{BASE_URL}/admin/users/{client_id}/statistics", headers=headers)
    print(f"Get User Statistics: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print("✅ User statistics retrieved successfully")
        print(f"   User: {stats['user_name']}")
        print(f"   Purchased Levels: {stats['purchased_levels']}")
        print(f"   Completed Levels: {stats['completed_levels']}")
        print(f"   Average Improvement: {stats['average_improvement']}%")
    else:
        print(f"❌ User statistics failed: {response.text}")

def main():
    """Run all API tests"""
    print("🚀 Starting Educational App API Tests...\n")
    
    # Test authentication
    result = test_register_and_login()
    if not result or len(result) < 3:
        print("❌ Authentication tests failed. Stopping.")
        return
    
    admin_token, client_token, client_id = result
    
    # Test level management
    level_id = test_level_management(admin_token)
    if not level_id:
        print("❌ Level management tests failed. Stopping.")
        return
    
    # Test video management
    video_ids = test_video_management(admin_token, level_id)
    if not video_ids:
        print("❌ Video management tests failed. Stopping.")
        return
    
    # Test level purchase and progress
    test_level_purchase_and_progress(client_token, client_id, level_id)
    
    # Test exam system
    test_exam_system(client_token, client_id, level_id)
    
    # Test video completion
    test_video_completion(client_token, client_id, level_id, video_ids)
    
    # Test final exam
    test_final_exam(client_token, client_id, level_id)
    
    # Test admin statistics
    test_admin_statistics(admin_token, client_id)
    
    print("\n🎉 All API tests completed!")

if __name__ == "__main__":
    main()

