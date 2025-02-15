from flask import Blueprint,jsonify, request, make_response, abort
from app.models.task import Task
from app import db
from sqlalchemy import asc, desc
from datetime import datetime
import requests
import os
from .helper import validate_task

tasks_bp = Blueprint("task", __name__,url_prefix="/tasks")

@tasks_bp.route('', methods=['POST'])
def create_one_task():
    request_body = request.get_json()
    if "title" not in request_body or "description" not in request_body:
        return jsonify({
            "details": "Invalid data"
        }), 400
    new_task = Task(title=request_body["title"],
                  description=request_body["description"])

    if "completed_at" in request_body:
        new_task.completed_at = request_body["completed_at"]

    db.session.add(new_task)
    db.session.commit()

    return jsonify(new_task.to_dict()), 201

@tasks_bp.route('', methods=['GET'])
def get_all_tasks():
    sort_query = request.args.get("sort")

    if sort_query == "asc":
        tasks = Task.query.order_by(asc(Task.title))
    elif sort_query == "desc":
        tasks = Task.query.order_by(desc(Task.title))

    else:
        tasks= Task.query.all()

    task_response = []
    for task in tasks:
        task_response.append({
            'id':task.task_id,
            'title':task.title,
            'description':task.description,
            'is_complete': bool(task.completed_at)
        })
    return jsonify(task_response),200
    

# get one task
@tasks_bp.route("/<task_id>", methods=["GET"])
def get_one_task(task_id):
    chosen_task = validate_task(task_id)

    request_body = request.get_json()
    return jsonify(chosen_task.to_dict()), 200


# update chosen task
@tasks_bp.route("/<task_id>", methods=["PUT"])
def update_one_task(task_id):
    chosen_task = validate_task(task_id)

    request_body = request.get_json()

    try:
        chosen_task.title = request_body["title"]
        chosen_task.description = request_body["description"]

    except KeyError:
        return {
            "msg": "title, and description are required"
        },404

    db.session.commit()
    return jsonify(chosen_task.to_dict()), 200



# delete chosen task
@tasks_bp.route("/<task_id>", methods=["DELETE"])
def delete_one_task(task_id):
    chosen_task = validate_task(task_id)

    db.session.delete(chosen_task)
    db.session.commit()

    response_body = { 
        "details":f'Task {chosen_task.task_id} "{chosen_task.title}" successfully deleted'
    }

    return jsonify(response_body), 200


# update chosen task is completed
@tasks_bp.route("/<task_id>/mark_complete", methods=["PATCH"])
def update_task_is_complete(task_id):
    chosen_task = validate_task(task_id)

    chosen_task.completed_at = datetime.utcnow()
    db.session.commit()

    path = "https://slack.com/api/chat.postMessage"
    SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
    data={
        "channel": "task-notifications",
        "text": f"{chosen_task.title} is completed",
        "format":"json"
    }

    headers = { "Authorization": f"Bearer { SLACK_TOKEN }"
    }

    requests.post(path, params=data, headers=headers )
    return jsonify(chosen_task.to_dict()), 200


# update chosen task is Incompleted
@tasks_bp.route("/<task_id>/mark_incomplete", methods=["PATCH"])
def update_task_is_incomplete(task_id):
    chosen_task = validate_task(task_id)

    chosen_task.completed_at = None

    db.session.commit()
    return jsonify(chosen_task.to_dict()), 200



