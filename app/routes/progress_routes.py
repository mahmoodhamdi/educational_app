from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import User, Level, Video, UserLevel, UserVideoProgress
from app.auth import client_required

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/users/<int:user_id>/levels', methods=['GET'])
@client_required
def get_user_levels(user_id):
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    user_levels = UserLevel.query.filter_by(user_id=user_id).all()
    
    result = []
    for user_level in user_levels:
        level = user_level.level
        
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

@progress_bp.route('/users/<int:user_id>/levels/<int:level_id>/purchase', methods=['POST'])
@client_required
def purchase_level(user_id, level_id):
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    level = Level.query.get_or_404(level_id)
    
    existing_user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if existing_user_level:
        return jsonify({'message': 'Level already purchased'}), 400
    
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
    
    return jsonify({'message': 'Level purchased successfully'}), 201

@progress_bp.route('/users/<int:user_id>/levels/<int:level_id>/update_progress', methods=['PATCH'])
@client_required
def update_level_progress(user_id, level_id):
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    completed_videos = UserVideoProgress.query.filter_by(
        user_level_id=user_level.id,
        is_completed=True
    ).count()
    
    total_videos = Video.query.filter_by(level_id=level_id).count()
    
    if completed_videos == total_videos:
        user_level.can_take_final_exam = True
    
    db.session.commit()
    
    return jsonify({
        'completed_videos_count': completed_videos,
        'total_videos_count': total_videos,
        'can_take_final_exam': user_level.can_take_final_exam
    }), 200