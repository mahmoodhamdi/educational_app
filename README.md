# 🎓 Educational App Backend API

## 📋 Overview

This is a comprehensive Flask-based backend API for an educational application that supports user authentication, level management, video content, exams, and progress tracking with role-based access control.

## 🚀 Live Demo

**API Base URL:** `https://5001-imkguih89b0dht2oyikr0-d23adca2.manusvm.computer`

## ✨ Features

### 🔐 Authentication & Authorization

- JWT-based authentication
- Role-based access control (Admin/Client)
- Secure password hashing with bcrypt
- Token-based API access

### 📚 Level Management

- Create, update, delete educational levels
- Level pricing and descriptions
- Welcome videos and thumbnails
- Initial and final exam questions

### 🎥 Video Management

- YouTube video integration
- Progressive video unlocking system
- Video-specific questions
- Completion tracking

### 📝 Exam System

- Initial and final exams per level
- Automatic score calculation
- Progress tracking and improvement metrics
- Percentage-based scoring

### 📊 Progress Tracking

- Real-time video completion tracking
- Level completion status
- User statistics and analytics
- Admin dashboard with comprehensive metrics

### 🖼️ File Management

- Secure image upload for level thumbnails
- Support for both file uploads and URL links
- Automatic file naming and storage

## 🛠️ Technical Stack

- **Framework:** Flask 2.3.3
- **Database:** SQLAlchemy with SQLite
- **Authentication:** Flask-JWT-Extended
- **Password Hashing:** Flask-Bcrypt
- **CORS:** Flask-CORS
- **File Handling:** Werkzeug

## 📁 Project Structure

```structure
educational_app/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── config.py            # Configuration settings
│   ├── models.py            # Database models
│   ├── routes.py            # API endpoints
│   └── auth.py              # Authentication helpers
├── uploads/
│   └── levels/              # Uploaded level images
├── src/                     # Deployment source
├── venv/                    # Virtual environment
├── app.py                   # Main application file
├── requirements.txt         # Python dependencies
├── test_api.py             # API testing script
├── API_Documentation.md     # Detailed API docs
└── README.md               # This file
```

## 🗄️ Database Models

### User

- Authentication and profile data
- Role-based permissions (admin/client)
- Relationship with purchased levels

### Level

- Course level information
- Pricing and content details
- Associated videos and user progress

### Video

- YouTube video links
- Associated questions
- Sequential ordering within levels

### UserLevel

- User's level purchase records
- Progress tracking
- Exam scores and completion status

### UserVideoProgress

- Individual video completion tracking
- Progressive unlocking system

### ExamResult

- Exam scores and results
- Initial vs final exam tracking
- Improvement calculations

## 🔑 API Endpoints

### Authentication

- `POST /register` - User registration
- `POST /login` - User login

### User Management

- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user profile

### Level Management

- `POST /levels` - Create level (Admin)
- `PUT /levels/{id}` - Update level (Admin)
- `DELETE /levels/{id}` - Delete level (Admin)
- `GET /levels` - Get all levels
- `GET /levels/{id}` - Get single level

### Video Management

- `POST /levels/{id}/videos` - Add video (Admin)
- `PUT /videos/{id}` - Update video (Admin)
- `DELETE /videos/{id}` - Delete video (Admin)
- `PATCH /users/{user_id}/levels/{level_id}/videos/{video_id}/complete` - Complete video

### File Upload

- `POST /levels/{id}/upload_image` - Upload level image (Admin)

### Exams

- `POST /exams/{level_id}/initial` - Submit initial exam
- `POST /exams/{level_id}/final` - Submit final exam
- `GET /exams/{level_id}/user/{user_id}` - Get exam results

### Progress Tracking

- `GET /users/{user_id}/levels` - Get user's levels
- `POST /users/{user_id}/levels/{level_id}/purchase` - Purchase level
- `PATCH /users/{user_id}/levels/{level_id}/update_progress` - Update progress

### Statistics (Admin)

- `GET /admin/statistics` - General statistics
- `GET /admin/users/{user_id}/statistics` - User-specific statistics

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip package manager

### Installation

1. Clone or download the project
2. Navigate to the project directory
3. Create virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Testing the API

Run the comprehensive test suite:

```bash
python test_api.py
```

## 🔒 Security Features

### Authentication

- JWT tokens with configurable expiration
- Secure password hashing with bcrypt
- Role-based access control

### Authorization

- Admin-only endpoints for content management
- User-specific data access restrictions
- Protected routes with JWT verification

### Data Validation

- Input validation for all endpoints
- SQL injection prevention with SQLAlchemy ORM
- CORS configuration for frontend integration

## 📊 Key Business Logic

### Progressive Video Unlocking

1. First video in each level is automatically unlocked upon purchase
2. Subsequent videos unlock only after completing the previous video
3. Final exam becomes available only after completing all videos

### Exam System

1. Initial exam can be taken immediately after level purchase
2. Final exam unlocks after completing all videos
3. Automatic calculation of improvement percentage
4. Score tracking and progress monitoring

### Progress Tracking

1. Real-time tracking of video completion
2. Level completion status updates
3. Comprehensive statistics for both users and admins
4. Performance analytics and improvement metrics

## 🧪 Testing Results

The API has been thoroughly tested with the following results:

- ✅ User registration and authentication
- ✅ Level creation and management
- ✅ Video management and progression
- ✅ Level purchase and progress tracking
- ✅ Exam system (initial and final)
- ✅ Video completion and unlocking
- ✅ Statistics and analytics
- ✅ Role-based access control

## 📚 API Documentation

For detailed API documentation with request/response examples, see [API_Documentation.md](API_Documentation.md)

## 🔧 Configuration

Key configuration options in `app/config.py`:

- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT signing key
- `JWT_ACCESS_TOKEN_EXPIRES`: Token expiration time
- `SQLALCHEMY_DATABASE_URI`: Database connection string
- `UPLOAD_FOLDER`: File upload directory

## 🚀 Deployment

The application is configured for deployment with:

- CORS enabled for frontend integration
- Host binding to `0.0.0.0` for external access
- Production-ready configuration options
- Virtual environment support

## 📞 Support

For questions, issues, or feature requests, please refer to the API documentation or contact the development team.

## 📄 License

This project is developed for educational purposes and includes comprehensive features for learning management systems.

---

**Built with ❤️ using Flask and modern web technologies**
