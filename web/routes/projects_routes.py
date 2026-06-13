"""GitHub projects showcase routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from app.core.projects import list_github_projects

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/projects', methods=['GET'])
def projects_page():
    return render_template('projects.html', show_integrity_check=False)


@projects_bp.route('/api/projects', methods=['GET'])
def projects_api():
    refresh = request.args.get('refresh', '').lower() in {'1', 'true', 'yes'}
    payload = list_github_projects(refresh=refresh)
    return jsonify(payload)
