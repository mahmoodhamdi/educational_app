from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import User, Level, Video, UserLevel, UserVideoProgress
from app.auth import admin_required, client_required
import json

video_bp = Blueprint('video', __name__)

@video_bp.route('/levels/<int:level_id>/videos', methods=['POST'])
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

@video_bp.route('/videos/<int:video_id>', methods=['PUT'])
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

@video_bp.route('/videos/<int:video_id>', methods=['DELETE'])
@admin_required
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    
    user_progresses = UserVideoProgress.query.filter_by(video_id=video_id).all()
    for progress in user_progresses:
        db.session.delete(progress)
    
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({'message': 'Video deleted successfully'}), 200

@video_bp.route('/users/<int:user_id>/levels/<int:level_id>/videos/<int:video_id>/complete', methods=['PATCH'])
@client_required
def complete_video(user_id, level_id, video_id):
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    user_level = UserLevel.query.filter_by(user_id=user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    video_progress = UserVideoProgress.query.filter_by(
        user_level_id=user_level.id, 
        video_id=video_id
    ).first()
    
    if not video_progress:
        return jsonify({'message': 'Video not accessible'}), 400
    
    video_progress.is_completed = True
    
    level_videos = Video.query.filter_by(level_id=level_id).order_by(Video.id).all()
    
    current_video_index = None
    for i, video in enumerate(level_videos):
        if video.id == video_id:
            current_video_index = i
            break
    
    if current_video_index is not None and (current_video_index + 1) < len(level_videos):
        next_video = level_videos[current_video_index + 1]
        next_video_progress = UserVideoProgress.query.filter_by(
            user_level_id=user_level.id, 
            video_id=next_video.id
        ).first()
        
        if next_video_progress:
            next_video_progress.is_opened = True
    
    all_videos_completed = all(
        UserVideoProgress.query.filter_by(
            user_level_id=user_level.id, 
            video_id=video.id
        ).first().is_completed
        for video in level_videos
    )
    
    if all_videos_completed:
        user_level.can_take_final_exam = True
    
    db.session.commit()
    
    return jsonify({'message': 'Video completed successfully'}), 200