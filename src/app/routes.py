from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models import User, Level, Video, UserLevel, UserVideoProgress, ExamResult
from app.auth import admin_required, client_required, authenticate_user, create_user_token, get_current_user
import json
from flask import send_from_directory
import os
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint('main', __name__)

@bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('Uploads', filename)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not all(key in data for key in ['name', 'email', 'password', 'role']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400
    
    role = data['role']
    if role not in ['admin', 'client']:
        return jsonify({'message': 'Invalid role specified. Must be "admin" or "client"'}), 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        role=role,
        picture=data.get('picture', '')
    )
    
    db.session.add(user)
    db.session.commit()
    
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
    current_user = get_current_user()
    if current_user.role != 'admin' and current_user.id != user_id:
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
    current_user = get_current_user()
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    target_user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    target_user.name = data.get('name', target_user.name)
    target_user.picture = data.get('picture', target_user.picture)
    
    if current_user.role == 'admin' and 'role' in data:
        if data['role'] in ['admin', 'client']:
            target_user.role = data['role']
        else:
            return jsonify({'message': 'Invalid role'}), 400
    
    db.session.commit()
    
    return jsonify({
        'id': target_user.id,
        'name': target_user.name,
        'email': target_user.email,
        'role': target_user.role,
        'picture': target_user.picture
    }), 200

@bp.route('/levels', methods=['POST'])
@admin_required
def create_level():
    data = request.get_json()
    
    if not all(key in data for key in ['name', 'price']):
        return jsonify({'message': 'Missing required fields'}), 400
    
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
    current_user = get_current_user()
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
        
        user_level = UserLevel.query.filter_by(user_id=current_user.id, level_id=level.id).first()
        if user_level:
            level_data['is_completed'] = user_level.is_completed
            level_data['can_take_final_exam'] = user_level.can_take_final_exam
            for video in level.videos:
                video_progress = UserVideoProgress.query.filter_by(
                    user_level_id=user_level.id, video_id=video.id).first()
                video_data = {
                    'id': video.id,
                    'youtube_link': video.youtube_link,
                    'questions': json.loads(video.questions) if video.questions else [],
                    'is_opened': video_progress.is_opened if video_progress else False
                }
                level_data['videos'].append(video_data)
        else:
            level_data['videos'] = [{'id': v.id, 'youtube_link': '', 'questions': [], 'is_opened': False} for v in level.videos]
        
        result.append(level_data)
    
    return jsonify(result), 200

@bp.route('/levels/<int:level_id>', methods=['GET'])
@client_required
def get_level(level_id):
    current_user = get_current_user()
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
    
    user_level = UserLevel.query.filter_by(user_id=current_user.id, level_id=level.id).first()
    if user_level:
        level_data['is_completed'] = user_level.is_completed
        level_data['can_take_final_exam'] = user_level.can_take_final_exam
        for video in level.videos:
            video_progress = UserVideoProgress.query.filter_by(
                user_level_id=user_level.id, video_id=video.id).first()
            video_data = {
                'id': video.id,
                'youtube_link': video.youtube_link,
                'questions': json.loads(video.questions) if video.questions else [],
                'is_opened': video_progress.is_opened if video_progress else False
            }
            level_data['videos'].append(video_data)
        else:
            level_data['videos'] = [{'id': v.id, 'youtube_link': '', 'questions': [], 'is_opened': False} for v in level.videos]
    
    return jsonify(level_data), 200

@bp.route('/levels/<int:level_id>/videos', methods=['POST'])
@admin_required
def add_video_to_level(level_id):
    Level.query.get_or_404(level_id)
    data = request.get_json()
    
    video = Video(
        level_id=level_id,
        youtube_link=data['youtube_link'],
        questions=json.dumps(data.get('questions', [])),
        order_index=data.get('order_index', 0)
    )
    
    db.session.add(video)
    db.session.commit()
    
    return jsonify({
        'id': video.id,
        'youtube_link': video.youtube_link,
        'questions': json.loads(video.questions) if video.questions else [],
        'order_index': video.order_index,
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
    user_progresses = UserVideoProgress.query.filter_by(video_id=video_id).all()
    for progress in user_progresses:
        db.session.delete(progress)
    
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({'message': 'Video deleted successfully'}), 200

@bp.route('/users/<int:user_id>/levels/<int:level_id>/videos/<int:video_id>/complete', methods=['PATCH'])
@client_required
def complete_video(user_id, level_id, video_id):
    current_user = get_current_user()
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    video_progress = UserVideoProgress.query.filter_by(user_level_id=user_level.id, video_id=video_id).first()
    if not video_progress:
        return jsonify({'message': 'Video not accessible'}), 400
    
    video_progress.is_completed = True
    
    level_videos = Video.query.filter_by(level_id=level_id).order_by(Video.order_index).all()
    current_video_index = next((i for i, v in enumerate(level_videos) if v.id == video_id), None)
    
    if current_video_index is not None and current_video_index + 1 < len(level_videos):
        next_video = level_videos[current_video_index + 1]
        next_video_progress = UserVideoProgress.query.filter_by(
            user_level_id=user_level.id, video_id=next_video.id).first()
        if next_video_progress:
            next_video_progress.is_opened = True
    
    all_videos_completed = all(
        UserVideoProgress.query.filter_by(user_level_id=user_level.id, video_id=v.id).first().is_completed
        for v in level_videos
    )
    if all_videos_completed:
        user_level.can_take_final_exam = True
    
    db.session.commit()
    
    return jsonify({'message': 'Video completed successfully'}), 200

@bp.route('/levels/<int:level_id>/upload_image', methods=['POST'])
@admin_required
def upload_level_image(level_id):
    level = Level.query.get_or_404(level_id)
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    upload_dir = os.path.join('Uploads', 'levels')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    upload_path = os.path.join(upload_dir, unique_filename)
    file.save(upload_path)
    
    image_url = f"/Uploads/levels/{unique_filename}"
    level.image_url = image_url
    db.session.commit()
    
    return jsonify({'success': True, 'image_url': image_url}), 200

@bp.route('/exams/<int:level_id>/initial', methods=['POST'])
@client_required
def submit_initial_exam(level_id):
    current_user = get_current_user()
    data = request.get_json()
    
    if not all(key in data for key in ['correct_words', 'wrong_words']):
        return jsonify({'message': 'Missing exam data'}), 400
    
    user_level = UserLevel.query.filter_by(user_id=current_user.id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    total_words = data['correct_words'] + data['wrong_words']
    if total_words == 0:
        return jsonify({'message': 'No words provided'}), 400
    percentage = (data['correct_words'] / total_words) * 100
    
    exam_result = ExamResult(
        user_id=current_user.id,
        level_id=level_id,
        correct_words=data['correct_words'],
        wrong_words=data['wrong_words'],
        percentage=percentage,
        type='initial'
    )
    
    user_level.initial_exam_score = percentage
    db.session.add(exam_result)
    db.session.commit()
    
    return jsonify({
        'user_id': current_user.id,
        'level_id': level_id,
        'correct_words': data['correct_words'],
        'wrong_words': data['wrong_words'],
        'percentage': percentage,
        'type': 'initial'
    }), 201

@bp.route('/exams/<int:level_id>/final', methods=['POST'])
@client_required
def submit_final_exam(level_id):
    current_user = get_current_user()
    data = request.get_json()
    
    if not all(key in data for key in ['correct_words', 'wrong_words']):
        return jsonify({'message': 'Missing exam data'}), 400
    
    user_level = UserLevel.query.filter_by(user_id=current_user.id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    if not user_level.can_take_final_exam:
        return jsonify({'message': 'Final exam not available yet'}), 400
    
    total_words = data['correct_words'] + data['wrong_words']
    if total_words == 0:
        return jsonify({'message': 'No words provided'}), 400
    percentage = (data['correct_words'] / total_words) * 100
    
    exam_result = ExamResult(
        user_id=current_user.id,
        level_id=level_id,
        correct_words=data['correct_words'],
        wrong_words=data['wrong_words'],
        percentage=percentage,
        type='final'
    )
    
    user_level.final_exam_score = percentage
    if user_level.initial_exam_score is not None:
        user_level.score_difference = percentage - user_level.initial_exam_score
    user_level.is_completed = True
    
    db.session.add(exam_result)
    db.session.commit()
    
    return jsonify({
        'user_id': current_user.id,
        'level_id': level_id,
        'correct_words': data['correct_words'],
        'wrong_words': data['wrong_words'],
        'percentage': percentage,
        'type': 'final'
    }), 201

@bp.route('/exams/<int:level_id>/user/<int:user_id>', methods=['GET'])
@client_required
def get_user_exam_results(level_id, user_id):
    current_user = get_current_user()
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    exam_results = ExamResult.query.filter_by(user_id=user_id, level_id=level_id).all()
    results = [{
        'user_id': exam.user_id,
        'level_id': exam.level_id,
        'correct_words': exam.correct_words,
        'wrong_words': exam.wrong_words,
        'percentage': exam.percentage,
        'type': exam.type,
        'timestamp': exam.timestamp.isoformat()
    } for exam in exam_results]
    
    return jsonify(results), 200

@bp.route('/users/<int:user_id>/levels', methods=['GET'])
@client_required
def get_user_levels(user_id):
    current_user = get_current_user()
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    user_levels = UserLevel.query.filter_by(user_id=user_id).all()
    result = []
    for user_level in user_levels:
        level = user_level.level
        videos_progress = []
        completed_videos_count = 0
        
        for video in level.videos:
            video_progress = UserVideoProgress.query.filter_by(
                user_level_id=user_level.id, video_id=video.id).first()
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
        
        result.append({
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
        })
    
    return jsonify(result), 200

@bp.route('/users/<int:user_id>/levels/<int:level_id>/purchase', methods=['POST'])
@client_required
def purchase_level(user_id, level_id):
    current_user = get_current_user()
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    level = Level.query.get_or_404(level_id)
    if UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first():
        return jsonify({'message': 'Level already purchased'}), 400
    
    user_level = UserLevel(user_id=user_id, level_id=level_id)
    db.session.add(user_level)
    db.session.flush()
    
    level_videos = Video.query.filter_by(level_id=level_id).order_by(Video.id).all()
    for i, video in enumerate(level_videos):
        video_progress = UserVideoProgress(
            user_level_id=user_level.id,
            video_id=video.id,
            is_opened=(i == 0),
            is_completed=False
        )
        db.session.add(video_progress)
    
    db.session.commit()
    
    return jsonify({'message': 'Level purchased successfully'}), 201

@bp.route('/users/<int:user_id>/levels/<int:level_id>/update_progress', methods=['PATCH'])
@client_required
def update_level_progress(user_id, level_id):
    current_user = get_current_user()
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    completed_videos = UserVideoProgress.query.filter_by(
        user_level_id=user_level.id, is_completed=True).count()
    total_videos = Video.query.filter_by(level_id=level_id).count()
    
    if completed_videos == total_videos:
        user_level.can_take_final_exam = True
    
    db.session.commit()
    
    return jsonify({
        'completed_videos_count': completed_videos,
        'total_videos_count': total_videos,
        'can_take_final_exam': user_level.can_take_final_exam
    }), 200

@bp.route('/admin/statistics', methods=['GET'])
@admin_required
def get_admin_statistics():
    total_users = User.query.filter_by(role='client').count()
    total_levels = Level.query.count()
    total_purchases = UserLevel.query.count()
    completed_levels = UserLevel.query.filter_by(is_completed=True).count()
    completion_rate = (completed_levels / total_purchases * 100) if total_purchases > 0 else 0
    
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
        'popular_levels': [{'name': level.name, 'purchases': level.purchases} for level in popular_levels]
    }), 200

@bp.route('/admin/users/<int:user_id>/statistics', methods=['GET'])
@admin_required
def get_user_statistics(user_id):
    user = User.query.get_or_404(user_id)
    purchased_levels = UserLevel.query.filter_by(user_id=user_id).count()
    completed_levels = UserLevel.query.filter_by(user_id=user_id, is_completed=True).count()
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