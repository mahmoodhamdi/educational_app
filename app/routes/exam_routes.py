from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import User, UserLevel, ExamResult
from app.auth import client_required

exam_bp = Blueprint('exam', __name__)

@exam_bp.route('/exams/<int:level_id>/initial', methods=['POST'])
@client_required
def submit_initial_exam(level_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    user_level = UserLevel.query.filter_by(user_id=current_user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    total_words = data['correct_words'] + data['wrong_words']
    percentage = (data['correct_words'] / total_words * 100) if total_words > 0 else 0
    
    exam_result = ExamResult(
        user_id=current_user_id,
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
        'user_id': current_user_id,
        'level_id': level_id,
        'correct_words': data['correct_words'],
        'wrong_words': data['wrong_words'],
        'percentage': percentage,
        'type': 'initial'
    }), 201

@exam_bp.route('/exams/<int:level_id>/final', methods=['POST'])
@client_required
def submit_final_exam(level_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    user_level = UserLevel.query.filter_by(user_id=current_user_id, level_id=level_id).first()
    if not user_level:
        return jsonify({'message': 'Level not purchased'}), 400
    
    if not user_level.can_take_final_exam:
        return jsonify({'message': 'Final exam not available yet. Complete all videos first.'}), 400
    
    total_words = data['correct_words'] + data['wrong_words']
    percentage = (data['correct_words'] / total_words * 100) if total_words > 0 else 0
    
    exam_result = ExamResult(
        user_id=current_user_id,
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
        'user_id': current_user_id,
        'level_id': level_id,
        'correct_words': data['correct_words'],
        'wrong_words': data['wrong_words'],
        'percentage': percentage,
        'type': 'final'
    }), 201

@exam_bp.route('/exams/<int:level_id>/user/<int:user_id>', methods=['GET'])
@client_required
def get_user_exam_results(level_id, user_id):
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
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