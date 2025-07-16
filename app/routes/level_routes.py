from flask import Blueprint, request, jsonify, current_app
from flask_wtf import FlaskForm
from wtforms import FileField, StringField, FloatField, IntegerField
from wtforms.validators import DataRequired
from app import db
from app.models import Level
from app.auth import admin_required
import os
import uuid

level_bp = Blueprint('level', __name__)

# Define LevelForm within level_routes.py (assuming no separate forms.py)
class LevelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    level_number = IntegerField('Level Number', validators=[DataRequired()])
    welcome_video_url = StringField('Welcome Video URL')
    price = FloatField('Price', validators=[DataRequired()])
    initial_exam_question = StringField('Initial Exam Question')
    final_exam_question = StringField('Final Exam Question')
    file = FileField('Image File', validators=[DataRequired()])

@level_bp.route('/levels', methods=['POST'])
@admin_required
def create_level():
    form = LevelForm()
    if not form.validate_on_submit():
        return jsonify({'message': 'Invalid form data'}), 400

    file = form.file.data
    if not file:
        return jsonify({'message': 'Image file required'}), 400

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'levels', unique_filename)

    level = Level(
        name=form.name.data,
        description=form.description.data,
        level_number=form.level_number.data,
        welcome_video_url=form.welcome_video_url.data,
        price=form.price.data,
        initial_exam_question=form.initial_exam_question.data,
        final_exam_question=form.final_exam_question.data
    )

    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)
    level.image_path = f"/Uploads/levels/{unique_filename}"

    db.session.add(level)
    db.session.commit()

    return jsonify({
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'level_number': level.level_number,
        'welcome_video_url': level.welcome_video_url,
        'image_path': level.image_path,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question
    }), 201

@level_bp.route('/levels', methods=['GET'])
def get_all_levels():
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
        'level_number': level.level_number,
        'welcome_video_url': level.welcome_video_url,
        'image_path': level.image_path,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question,
        'videos_count': len(level.videos)
    } for level in levels]

    return jsonify(result), 200

@level_bp.route('/levels/<int:level_id>', methods=['GET'])
def get_level(level_id):
    level = Level.query.get_or_404(level_id)

    return jsonify({
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'level_number': level.level_number,
        'welcome_video_url': level.welcome_video_url,
        'image_path': level.image_path,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question,
        'videos': [{
            'id': video.id,
            'youtube_link': video.youtube_link
        } for video in level.videos]
    }), 200

@level_bp.route('/levels/<int:level_id>', methods=['PUT'])
@admin_required
def update_level(level_id):
    level = Level.query.get_or_404(level_id)
    form = LevelForm()

    if not form.validate_on_submit():
        return jsonify({'message': 'Invalid form data'}), 400

    level.name = form.name.data
    level.description = form.description.data
    level.level_number = form.level_number.data
    level.welcome_video_url = form.welcome_video_url.data
    level.price = form.price.data
    level.initial_exam_question = form.initial_exam_question.data
    level.final_exam_question = form.final_exam_question.data

    file = form.file.data
    if file:
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'levels', unique_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        level.image_path = f"/Uploads/levels/{unique_filename}"

    db.session.commit()

    return jsonify({
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'level_number': level.level_number,
        'welcome_video_url': level.welcome_video_url,
        'image_path': level.image_path,
        'price': level.price,
        'initial_exam_question': level.initial_exam_question,
        'final_exam_question': level.final_exam_question
    }), 200

@level_bp.route('/levels/<int:level_id>', methods=['DELETE'])
@admin_required
def delete_level(level_id):
    level = Level.query.get_or_404(level_id)

    db.session.delete(level)
    db.session.commit()

    return jsonify({'message': 'Level deleted successfully'}), 200