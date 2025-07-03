# 🎯 Educational App Backend API Documentation

## 📋 Overview

This is a comprehensive Flask-based backend API for an educational application that supports user authentication, level management, video content, exams, and progress tracking.

## 🔧 Base URL

```
http://localhost:5000
```

## 🔑 Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

---

## 📚 API Endpoints

### 🔐 Authentication Endpoints

#### Register User

```http
POST /register
```

**Request Body:**

```json
{
  "name": "Ahmed Ali",
  "email": "ahmed@example.com",
  "password": "password123",
  "role": "client",
  "picture": "https://example.com/avatar.jpg"
}
```

**Response:**

```json
{
  "id": 1,
  "name": "Ahmed Ali",
  "email": "ahmed@example.com",
  "role": "client",
  "picture": "https://example.com/avatar.jpg",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Login User

```http
POST /login
```

**Request Body:**

```json
{
  "email": "ahmed@example.com",
  "password": "password123"
}
```

**Response:**

```json
{
  "id": 1,
  "name": "Ahmed Ali",
  "email": "ahmed@example.com",
  "role": "client",
  "picture": "https://example.com/avatar.jpg",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### 👤 User Management Endpoints

#### Get User Details

```http
GET /users/{user_id}
```

**Auth Required:** Yes  
**Permissions:** Users can only access their own data unless they're admin

#### Update User

```http
PUT /users/{user_id}
```

**Auth Required:** Yes  
**Permissions:** Users can only update their own data unless they're admin

**Request Body:**

```json
{
  "name": "Ahmed Ali Updated",
  "picture": "https://example.com/new-avatar.jpg",
  "role": "admin"
}
```

---

### 📖 Level Management Endpoints

#### Create Level (Admin Only)

```http
POST /levels
```

**Request Body:**

```json
{
  "name": "Level 1: Basics",
  "description": "Introduction to the fundamentals",
  "welcome_video_url": "https://youtube.com/watch?v=abc123",
  "image_url": "https://example.com/level1.jpg",
  "price": 99.99,
  "initial_exam_question": "What is the main topic of this level?",
  "final_exam_question": "Summarize what you learned in this level."
}
```

#### Update Level (Admin Only)

```http
PUT /levels/{level_id}
```

#### Delete Level (Admin Only)

```http
DELETE /levels/{level_id}
```

#### Get All Levels

```http
GET /levels
```

**Auth Required:** Yes

**Response:**

```json
[
  {
    "id": 1,
    "name": "Level 1: Basics",
    "description": "Introduction to the fundamentals",
    "welcome_video_url": "https://youtube.com/watch?v=abc123",
    "image_url": "https://example.com/level1.jpg",
    "price": 99.99,
    "initial_exam_question": "What is the main topic of this level?",
    "final_exam_question": "Summarize what you learned in this level.",
    "videos_count": 5,
    "videos": [...],
    "is_completed": false,
    "can_take_final_exam": false
  }
]
```

#### Get Single Level

```http
GET /levels/{level_id}
```

**Auth Required:** Yes

---

### 🎥 Video Management Endpoints

#### Add Video to Level (Admin Only)

```http
POST /levels/{level_id}/videos
```

**Request Body:**

```json
{
  "youtube_link": "https://youtube.com/watch?v=xyz789",
  "questions": ["What is the main concept?", "How does this apply?"]
}
```

#### Update Video (Admin Only)

```http
PUT /videos/{video_id}
```

#### Delete Video (Admin Only)

```http
DELETE /videos/{video_id}
```

#### Complete Video

```http
PATCH /users/{user_id}/levels/{level_id}/videos/{video_id}/complete
```

**Auth Required:** Yes  
**Description:** Marks a video as completed and opens the next video in sequence

---

### 🖼️ Image Upload Endpoints

#### Upload Level Image (Admin Only)

```http
POST /levels/{level_id}/upload_image
```

**Request:** Form Data

```
file: [image file]
```

**Response:**

```json
{
  "success": true,
  "image_url": "/uploads/levels/unique-filename.jpg"
}
```

---

### 📝 Exam Endpoints

#### Submit Initial Exam

```http
POST /exams/{level_id}/initial
```

**Request Body:**

```json
{
  "correct_words": 18,
  "wrong_words": 2
}
```

**Response:**

```json
{
  "user_id": 1,
  "level_id": 1,
  "correct_words": 18,
  "wrong_words": 2,
  "percentage": 90.0,
  "type": "initial"
}
```

#### Submit Final Exam

```http
POST /exams/{level_id}/final
```

**Note:** Only available after completing all videos in the level

#### Get User Exam Results

```http
GET /exams/{level_id}/user/{user_id}
```

---

### 📊 Progress Tracking Endpoints

#### Get User's Purchased Levels

```http
GET /users/{user_id}/levels
```

**Response:**

```json
[
  {
    "user_id": 1,
    "level_id": 1,
    "level_name": "Level 1: Basics",
    "completed_videos_count": 3,
    "total_videos_count": 5,
    "videos_progress": [
      {
        "video_id": 1,
        "is_opened": true,
        "is_completed": true
      },
      {
        "video_id": 2,
        "is_opened": true,
        "is_completed": true
      },
      {
        "video_id": 3,
        "is_opened": true,
        "is_completed": false
      }
    ],
    "is_completed": false,
    "can_take_final_exam": false,
    "initial_exam_score": 85.0,
    "final_exam_score": null,
    "score_difference": null
  }
]
```

#### Purchase Level

```http
POST /users/{user_id}/levels/{level_id}/purchase
```

#### Update Level Progress

```http
PATCH /users/{user_id}/levels/{level_id}/update_progress
```

---

### 📈 Statistics Endpoints (Admin Only)

#### Get Admin Statistics

```http
GET /admin/statistics
```

**Response:**

```json
{
  "total_users": 150,
  "total_levels": 10,
  "total_purchases": 450,
  "completed_levels": 320,
  "completion_rate": 71.11,
  "popular_levels": [
    {
      "name": "Level 1: Basics",
      "purchases": 89
    }
  ]
}
```

#### Get User Statistics

```http
GET /admin/users/{user_id}/statistics
```

---

## 🔒 Role-Based Access Control

### Admin Permissions

- Create, update, delete levels
- Create, update, delete videos
- Upload images
- View all user statistics
- Access all user data

### Client Permissions

- View levels (purchased levels show full details)
- Purchase levels
- Complete videos
- Submit exams
- View own progress and statistics
- Update own profile

---

## 🎯 Key Features

### 📹 Progressive Video Unlocking

- First video in each level is automatically opened upon purchase
- Subsequent videos unlock only after completing the previous video
- Final exam becomes available only after completing all videos

### 🎓 Exam System

- Initial exam can be taken immediately after purchase
- Final exam unlocks after completing all videos
- Automatic calculation of improvement percentage
- Score tracking and progress monitoring

### 📊 Progress Tracking

- Real-time tracking of video completion
- Level completion status
- Exam scores and improvements
- Comprehensive statistics for admins

### 🖼️ Image Management

- Secure image upload for level thumbnails
- Support for both file uploads and direct URL links
- Automatic file naming and storage

---

## 🛠️ Technical Details

### Database Models

- **User**: Authentication and profile data
- **Level**: Course level information
- **Video**: YouTube video links and questions
- **UserLevel**: User's level purchase and progress
- **UserVideoProgress**: Individual video completion tracking
- **ExamResult**: Exam scores and results

### Security Features

- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- CORS support for frontend integration

### File Structure

```
educational_app/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   └── auth.py
├── uploads/
│   └── levels/
├── app.py
├── requirements.txt
└── API_Documentation.md
```

---

## 🚀 Getting Started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python app.py
```

3. The API will be available at `http://localhost:5000`

---

## 📞 Support

For any questions or issues, please refer to this documentation or contact the development team.
