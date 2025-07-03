from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models import User, Level, Video, UserLevel, UserVideoProgress, ExamResult
from app.auth import admin_required, client_required, authenticate_user, create_user_token
import json

bp = Blueprint('main', __name__)

# Authentication Routes
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400
    
    # Hash password
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Create new user
    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        role=data.get('role', 'client'),
        picture=data.get('picture', '')
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Create token
    token = create_user_token(user)
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'picture': user.picture,
        'token': token
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = authenticate_user(data['email'], data['password'])
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = create_user_token(user)
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'picture': user.picture,
        'token': token
    }), 200

@bp.route('/users/<int:user_id>', methods=['GET'])
@client_required
def get_user(user_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only access their own data unless they're admin
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    target_user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': target_user.id,
        'name': target_user.name,
        'email': target_user.email,
        'role': target_user.role,
        'picture': target_user.picture
    }), 200

@bp.route('/users/<int:user_id>', methods=['PUT'])
@client_required
def update_user(user_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only update their own data unless they're admin
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    target_user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    target_user.name = data.get('name', target_user.name)
    target_user.picture = data.get('picture', target_user.picture)
    
    # Only admin can change roles
    if user.role == 'admin':
        target_user.role = data.get('role', target_user.role)
    
    db.session.commit()
    
    return jsonify({
        'id': target_user.id,
        'name': target_user.name,
        'email': target_user.email,
        'role': target_user.role,
        'picture': target_user.picture
    }), 200



# Level Management Routes
@bp.route('/levels', methods=['POST'])
@admin_required
def create_level():
    data = request.get_json()
    
    level = Level(
        name=data['name'],
        description=data.get('description', ''),
        welcome_video_url=data.get('welcome_video_url', ''),
        image_url=data.get('image_url', ''),
        price=data['price'],
        initial_exam_question=data.get('initial_exam_question', ''),
        final_exam_question=data.get('final_exam_question', '')
    )
    
    db.session.add(level)
    db.session.commit()
    
    return jsonify({
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'welcome_video_url': level.welcome_video_url,
        'image_url': level.image_url,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question,
        'videos_count': 0,
        'videos': []
    }), 201

@bp.route('/levels/<int:level_id>', methods=['PUT'])
@admin_required
def update_level(level_id):
    level = Level.query.get_or_404(level_id)
    data = request.get_json()
    
    level.name = data.get('name', level.name)
    level.description = data.get('description', level.description)
    level.welcome_video_url = data.get('welcome_video_url', level.welcome_video_url)
    level.image_url = data.get('image_url', level.image_url)
    level.price = data.get('price', level.price)
    level.initial_exam_question = data.get('initial_exam_question', level.initial_exam_question)
    level.final_exam_question = data.get('final_exam_question', level.final_exam_question)
    
    db.session.commit()
    
    return jsonify({
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'welcome_video_url': level.welcome_video_url,
        'image_url': level.image_url,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question,
        'videos_count': len(level.videos),
        'videos': [{'id': v.id, 'youtube_link': v.youtube_link, 'questions': json.loads(v.questions) if v.questions else []} for v in level.videos]
    }), 200

@bp.route('/levels/<int:level_id>', methods=['DELETE'])
@admin_required
def delete_level(level_id):
    level = Level.query.get_or_404(level_id)
    
    # Delete associated videos and user progress
    for video in level.videos:
        db.session.delete(video)
    
    for user_level in level.user_levels:
        db.session.delete(user_level)
    
    db.session.delete(level)
    db.session.commit()
    
    return jsonify({'message': 'Level deleted successfully'}), 200

@bp.route('/levels', methods=['GET'])
@client_required
def get_levels():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    levels = Level.query.all()
    result = []
    
    for level in levels:
        level_data = {
            'id': level.id,
            'name': level.name,
            'description': level.description,
            'welcome_video_url': level.welcome_video_url,
            'image_url': level.image_url,
            'price': level.price,
            'initial_exam_question': level.initial_exam_question,
            'final_exam_question': level.final_exam_question,
            'videos_count': len(level.videos),
            'videos': [],
            'is_completed': False,
            'can_take_final_exam': False
        }
        
        # Check if user has purchased this level
        user_level = UserLevel.query.filter_by(user_id=current_user_id, level_id=level.id).first()
        if user_level:
            level_data['is_completed'] = user_level.is_completed
            level_data['can_take_final_exam'] = user_level.can_take_final_exam
            
            # Add video progress for purchased levels
            for video in level.videos:
                video_progress = UserVideoProgress.query.filter_by(
                    user_level_id=user_level.id, 
                    video_id=video.id
                ).first()
                
                video_data = {
                    'id': video.id,
                    'youtube_link': video.youtube_link,
                    'questions': json.loads(video.questions) if video.questions else [],
                    'is_opened': video_progress.is_opened if video_progress else False
                }
                level_data['videos'].append(video_data)
        else:
            # For non-purchased levels, don't show video details
            level_data['videos'] = [{'id': v.id, 'youtube_link': '', 'questions': [], 'is_opened': False} for v in level.videos]
        
        result.append(level_data)
    
    return jsonify(result), 200

@bp.route('/levels/<int:level_id>', methods=['GET'])
@client_required
def get_level(level_id):
    current_user_id = int(get_jwt_identity())
    level = Level.query.get_or_404(level_id)
    
    level_data = {
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'welcome_video_url': level.welcome_video_url,
        'image_url': level.image_url,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question,
        'videos_count': len(level.videos),
        'videos': [],
        'is_completed': False,
        'can_take_final_exam': False
    }
    
    # Check if user has purchased this level
    user_level = UserLevel.query.filter_by(user_id=current_user_id, level_id=level.id).first()
    if user_level:
        level_data['is_completed'] = user_level.is_completed
        level_data['can_take_final_exam'] = user_level.can_take_final_exam
        
        # Add video progress for purchased levels
        for video in level.videos:
            video_progress = UserVideoProgress.query.filter_by(
                user_level_id=user_level.id, 
                video_id=video.id
            ).first()
            
            video_data = {
                'id': video.id,
                'youtube_link': video.youtube_link,
                'questions': json.loads(video.questions) if video.questions else [],
                'is_opened': video_progress.is_opened if video_progress else False
            }
            level_data['videos'].append(video_data)
    else:
        # For non-purchased levels, don't show video details
        level_data['videos'] = [{'id': v.id, 'youtube_link': '', 'questions': [], 'is_opened': False} for v in level.videos]
    
    return jsonify(level_data), 200


# Video Management Routes
@bp.route('/levels/<int:level_id>/videos', methods=['POST'])
@admin_required
def add_video_to_level(level_id):
    level = Level.query.get_or_404(level_id)
    data = request.get_json()
    
    video = Video(
        level_id=level_id,
        youtube_link=data['youtube_link'],
        questions=json.dumps(data.get('questions', []))
    )
    
    db.session.add(video)
    db.session.commit()
    
    return jsonify({
        'id': video.id,
        'youtube_link': video.youtube_link,
        'questions': json.loads(video.questions) if video.questions else [],
        'is_opened': False
    }), 201

@bp.route('/videos/<int:video_id>', methods=['PUT'])
@admin_required
def update_video(video_id):
    video = Video.query.get_or_404(video_id)
    data = request.get_json()
    
    video.youtube_link = data.get('youtube_link', video.youtube_link)
    video.questions = json.dumps(data.get('questions', json.loads(video.questions) if video.questions else []))
    
    db.session.commit()
    
    return jsonify({
        'id': video.id,
        'youtube_link': video.youtube_link,
        'questions': json.loads(video.questions) if video.questions else []
    }), 200

@bp.route('/videos/<int:video_id>', methods=['DELETE'])
@admin_required
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    
    # Delete associated user progress
    user_progresses = UserVideoProgress.query.filter_by(video_id=video_id).all()
    for progress in user_progresses:
        db.session.delete(progress)
    
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({'message': 'Video deleted successfully'}), 200

@bp.route('/users/<int:user_id>/levels/<int:level_id>/videos/<int:video_id>/complete', methods=['PATCH'])
@client_required
def complete_video(user_id, level_id, video_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only update their own progress unless they're admin
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    # Check if user has purchased the level
    user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    # Get or create video progress
    video_progress = UserVideoProgress.query.filter_by(
        user_level_id=user_level.id, 
        video_id=video_id
    ).first()
    
    if not video_progress:
        return jsonify({'message': 'Video not accessible'}), 400
    
    # Mark current video as completed
    video_progress.is_completed = True
    
    # Get all videos in this level ordered by ID
    level_videos = Video.query.filter_by(level_id=level_id).order_by(Video.id).all()
    
    # Find next video and open it
    current_video_index = None
    for i, video in enumerate(level_videos):
        if video.id == video_id:
            current_video_index = i
            break
    
    if current_video_index is not None and current_video_index + 1 < len(level_videos):
        next_video = level_videos[current_video_index + 1]
        next_video_progress = UserVideoProgress.query.filter_by(
            user_level_id=user_level.id, 
            video_id=next_video.id
        ).first()
        
        if next_video_progress:
            next_video_progress.is_opened = True
    
    # Check if all videos are completed
    all_videos_completed = True
    for video in level_videos:
        video_prog = UserVideoProgress.query.filter_by(
            user_level_id=user_level.id, 
            video_id=video.id
        ).first()
        if not video_prog or not video_prog.is_completed:
            all_videos_completed = False
            break
    
    # If all videos completed, allow final exam
    if all_videos_completed:
        user_level.can_take_final_exam = True
    
    db.session.commit()
    
    return jsonify({'message': 'Video completed successfully'}), 200


# Image Upload Route
@bp.route('/levels/<int:level_id>/upload_image', methods=['POST'])
@admin_required
def upload_level_image(level_id):
    level = Level.query.get_or_404(level_id)
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if file:
        import os
        import uuid
        from werkzeug.utils import secure_filename
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save file
        upload_path = os.path.join('uploads', 'levels', unique_filename)
        file.save(upload_path)
        
        # Update level image URL
        image_url = f"/uploads/levels/{unique_filename}"
        level.image_url = image_url
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': image_url
        }), 200
    
    return jsonify({'message': 'File upload failed'}), 400


# Exam Routes
@bp.route('/exams/<int:level_id>/initial', methods=['POST'])
@client_required
def submit_initial_exam(level_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Check if user has purchased the level
    user_level = UserLevel.query.filter_by(user_id=current_user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    # Calculate percentage
    total_words = data['correct_words'] + data['wrong_words']
    percentage = (data['correct_words'] / total_words * 100) if total_words > 0 else 0
    
    # Create exam result
    exam_result = ExamResult(
        user_id=current_user_id,
        level_id=level_id,
        correct_words=data['correct_words'],
        wrong_words=data['wrong_words'],
        percentage=percentage,
        type='initial'
    )
    
    # Update user level with initial exam score
    user_level.initial_exam_score = percentage
    
    db.session.add(exam_result)
    db.session.commit()
    
    return jsonify({
        'user_id': current_user_id,
        'level_id': level_id,
        'correct_words': data['correct_words'],
        'wrong_words': data['wrong_words'],
        'percentage': percentage,
        'type': 'initial'
    }), 201

@bp.route('/exams/<int:level_id>/final', methods=['POST'])
@client_required
def submit_final_exam(level_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Check if user has purchased the level and can take final exam
    user_level = UserLevel.query.filter_by(user_id=current_user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    if not user_level.can_take_final_exam:
        return jsonify({'message': 'Final exam not available yet. Complete all videos first.'}), 400
    
    # Calculate percentage
    total_words = data['correct_words'] + data['wrong_words']
    percentage = (data['correct_words'] / total_words * 100) if total_words > 0 else 0
    
    # Create exam result
    exam_result = ExamResult(
        user_id=current_user_id,
        level_id=level_id,
        correct_words=data['correct_words'],
        wrong_words=data['wrong_words'],
        percentage=percentage,
        type='final'
    )
    
    # Update user level with final exam score and calculate difference
    user_level.final_exam_score = percentage
    if user_level.initial_exam_score is not None:
        user_level.score_difference = percentage - user_level.initial_exam_score
    
    # Mark level as completed
    user_level.is_completed = True
    
    db.session.add(exam_result)
    db.session.commit()
    
    return jsonify({
        'user_id': current_user_id,
        'level_id': level_id,
        'correct_words': data['correct_words'],
        'wrong_words': data['wrong_words'],
        'percentage': percentage,
        'type': 'final'
    }), 201

@bp.route('/exams/<int:level_id>/user/<int:user_id>', methods=['GET'])
@client_required
def get_user_exam_results(level_id, user_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only access their own exam results unless they're admin
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    exam_results = ExamResult.query.filter_by(user_id=user_id, level_id=level_id).all()
    
    results = []
    for exam in exam_results:
        results.append({
            'user_id': exam.user_id,
            'level_id': exam.level_id,
            'correct_words': exam.correct_words,
            'wrong_words': exam.wrong_words,
            'percentage': exam.percentage,
            'type': exam.type,
            'timestamp': exam.timestamp.isoformat()
        })
    
    return jsonify(results), 200


# User Progress Routes
@bp.route('/users/<int:user_id>/levels', methods=['GET'])
@client_required
def get_user_levels(user_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only access their own progress unless they're admin
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    user_levels = UserLevel.query.filter_by(user_id=user_id).all()
    
    result = []
    for user_level in user_levels:
        level = user_level.level
        
        # Get video progress
        videos_progress = []
        completed_videos_count = 0
        
        for video in level.videos:
            video_progress = UserVideoProgress.query.filter_by(
                user_level_id=user_level.id, 
                video_id=video.id
            ).first()
            
            if video_progress:
                videos_progress.append({
                    'video_id': video.id,
                    'is_opened': video_progress.is_opened,
                    'is_completed': video_progress.is_completed
                })
                if video_progress.is_completed:
                    completed_videos_count += 1
            else:
                videos_progress.append({
                    'video_id': video.id,
                    'is_opened': False,
                    'is_completed': False
                })
        
        level_data = {
            'user_id': user_id,
            'level_id': level.id,
            'level_name': level.name,
            'completed_videos_count': completed_videos_count,
            'total_videos_count': len(level.videos),
            'videos_progress': videos_progress,
            'is_completed': user_level.is_completed,
            'can_take_final_exam': user_level.can_take_final_exam,
            'initial_exam_score': user_level.initial_exam_score,
            'final_exam_score': user_level.final_exam_score,
            'score_difference': user_level.score_difference
        }
        
        result.append(level_data)
    
    return jsonify(result), 200

@bp.route('/users/<int:user_id>/levels/<int:level_id>/purchase', methods=['POST'])
@client_required
def purchase_level(user_id, level_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only purchase for themselves unless they're admin
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    # Check if level exists
    level = Level.query.get_or_404(level_id)
    
    # Check if already purchased
    existing_user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if existing_user_level:
        return jsonify({'message': 'Level already purchased'}), 400
    
    # Create user level
    user_level = UserLevel(
        user_id=user_id,
        level_id=level_id,
        is_completed=False,
        can_take_final_exam=False
    )
    
    db.session.add(user_level)
    db.session.flush()  # To get the user_level.id
    
    # Create video progress for all videos in the level
    level_videos = Video.query.filter_by(level_id=level_id).order_by(Video.id).all()
    
    for i, video in enumerate(level_videos):
        video_progress = UserVideoProgress(
            user_level_id=user_level.id,
            video_id=video.id,
            is_opened=(i == 0),  # First video is opened by default
            is_completed=False
        )
        db.session.add(video_progress)
    
    db.session.commit()
    
    return jsonify({'message': 'Level purchased successfully'}), 201

@bp.route('/users/<int:user_id>/levels/<int:level_id>/update_progress', methods=['PATCH'])
@client_required
def update_level_progress(user_id, level_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only update their own progress unless they're admin
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    # Check if user has purchased the level
    user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    # Count completed videos
    completed_videos = UserVideoProgress.query.filter_by(
        user_level_id=user_level.id,
        is_completed=True
    ).count()
    
    total_videos = Video.query.filter_by(level_id=level_id).count()
    
    # Update can_take_final_exam status
    if completed_videos == total_videos:
        user_level.can_take_final_exam = True
    
    db.session.commit()
    
    return jsonify({
        'completed_videos_count': completed_videos,
        'total_videos_count': total_videos,
        'can_take_final_exam': user_level.can_take_final_exam
    }), 200

# Statistics Routes (Admin only)
@bp.route('/admin/statistics', methods=['GET'])
@admin_required
def get_admin_statistics():
    # Total users
    total_users = User.query.filter_by(role='client').count()
    
    # Total levels
    total_levels = Level.query.count()
    
    # Total purchases
    total_purchases = UserLevel.query.count()
    
    # Completed levels
    completed_levels = UserLevel.query.filter_by(is_completed=True).count()
    
    # Average completion rate
    completion_rate = (completed_levels / total_purchases * 100) if total_purchases > 0 else 0
    
    # Most popular levels
    popular_levels = db.session.query(
        Level.name,
        db.func.count(UserLevel.id).label('purchases')
    ).join(UserLevel).group_by(Level.id).order_by(db.desc('purchases')).limit(5).all()
    
    return jsonify({
        'total_users': total_users,
        'total_levels': total_levels,
        'total_purchases': total_purchases,
        'completed_levels': completed_levels,
        'completion_rate': round(completion_rate, 2),
        'popular_levels': [{'name': level, 'purchases': purchases} for level, purchases in popular_levels]
    }), 200

@bp.route('/admin/users/<int:user_id>/statistics', methods=['GET'])
@admin_required
def get_user_statistics(user_id):
    user = User.query.get_or_404(user_id)
    
    # User's purchased levels
    purchased_levels = UserLevel.query.filter_by(user_id=user_id).count()
    
    # User's completed levels
    completed_levels = UserLevel.query.filter_by(user_id=user_id, is_completed=True).count()
    
    # User's average exam scores
    exam_results = ExamResult.query.filter_by(user_id=user_id).all()
    
    initial_scores = [exam.percentage for exam in exam_results if exam.type == 'initial']
    final_scores = [exam.percentage for exam in exam_results if exam.type == 'final']
    
    avg_initial_score = sum(initial_scores) / len(initial_scores) if initial_scores else 0
    avg_final_score = sum(final_scores) / len(final_scores) if final_scores else 0
    avg_improvement = avg_final_score - avg_initial_score if initial_scores and final_scores else 0
    
    return jsonify({
        'user_id': user_id,
        'user_name': user.name,
        'purchased_levels': purchased_levels,
        'completed_levels': completed_levels,
        'completion_rate': round((completed_levels / purchased_levels * 100) if purchased_levels > 0 else 0, 2),
        'average_initial_score': round(avg_initial_score, 2),
        'average_final_score': round(avg_final_score, 2),
        'average_improvement': round(avg_improvement, 2),
        'total_exams_taken': len(exam_results)
    }), 200

