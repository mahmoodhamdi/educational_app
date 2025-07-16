import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db, bcrypt
from app.models import User, Level, UserVideoProgress, Video, ExamResult, WelcomeVideo, UserLevel
from app.auth import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/welcome_video', methods=['POST'])
@admin_required
def set_welcome_video():
    data = request.get_json()
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({'message': 'Video URL required'}), 400
    
    WelcomeVideo.query.delete()
    welcome_video = WelcomeVideo(video_url=video_url)
    db.session.add(welcome_video)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'video_url': video_url
    }), 200

@admin_bp.route('/welcome_video', methods=['GET'])
def get_welcome_video():
    welcome_video = WelcomeVideo.query.first()
    
    if not welcome_video:
        return jsonify({'message': 'No welcome video set'}), 404
    
    return jsonify({
        'video_url': welcome_video.video_url
    }), 200

@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.all()
    result = [{
        'id': user.idcompress,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'picture': user.picture,
        'level_count': len(user.levels)
    } for user in users]
    return jsonify(result), 200

@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    UserLevel.query.filter_by(user_id=user_id).delete()
    ExamResult.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@admin_bp.route('/admin/users/<int:user_id>/reset_password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    new_password = data.get('new_password')
    if not new_password:
        return jsonify({'message': 'New password required'}), 400
    
    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200

@admin_bp.route('/admin/users/<int:user_id>/assign_level/<int:level_id>', methods=['POST'])
@admin_required
def assign_level_to_user(user_id, level_id):
    user = User.query.get_or_404(user_id)
    level = Level.query.get_or_404(level_id)
    
    existing_user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if existing_user_level:
        return jsonify({'message': 'Level already assigned'}), 400
    
    user_level = UserLevel(
        user_id=user_id,
        level_id=level_id,
        is_completed=False,
        can_take_final_exam=False
    )
    
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
    
    return jsonify({'message': 'Level assigned successfully'}), 201

@admin_bp.route('/admin/levels', methods=['GET'])
@admin_required
def admin_get_all_levels():
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    name = request.args.get('name')
    
    query = Level.query
    
    if min_price is not None:
        query = query.filter(Level.price >= min_price)
    if max_price is not None:
        query = query.filter(Level.price <= max_price)
    if name:
        query = query.filter(Level.name.ilike(f'%{name}%'))
    
    levels = query.order_by(Level.name).all()
    result = [{
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'welcome_video_url': level.welcome_video_url,
        'image_path': level.image_path,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question,
        'videos_count': len(level.videos),
        'videos': [{
            'id': v.id,
            'youtube_link': v.youtube_link,
            'questions': json.loads(v.questions) if v.questions else []
        } for v in level.videos],
        'user_count': len(level.user_levels)
    } for level in levels]
    return jsonify(result), 200

@admin_bp.route('/admin/videos', methods=['GET'])
@admin_required
def get_all_videos():
    videos = Video.query.all()
    result = [{
        'id': video.id,
        'level_id': video.level_id,
        'level_name': video.level.name if video.level else '',
        'youtube_link': video.youtube_link,
        'questions': json.loads(video.questions) if video.questions else [],
        'user_progress_count': UserVideoProgress.query.filter_by(video_id=video.id).count()
    } for video in videos]
    return jsonify(result), 200

@admin_bp.route('/admin/exams', methods=['GET'])
@admin_required
def get_all_exam_results():
    exam_results = ExamResult.query.all()
    result = [{
        'id': exam.id,
        'user_id': exam.user_id,
        'user_name': exam.user.name if exam.user else '',
        'level_id': exam.level_id,
        'level_name': exam.level.name if exam.level else '',
        'correct_words': exam.correct_words,
        'wrong_words': exam.wrong_words,
        'percentage': exam.percentage,
        'type': exam.type,
        'timestamp': exam.timestamp.isoformat()
    } for exam in exam_results]
    return jsonify(result), 200

@admin_bp.route('/admin/statistics', methods=['GET'])
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
        'popular_levels': [{'name': level, 'purchases': purchases} for level, purchases in popular_levels]
    }), 200

@admin_bp.route('/admin/users/<int:user_id>/statistics', methods=['GET'])
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