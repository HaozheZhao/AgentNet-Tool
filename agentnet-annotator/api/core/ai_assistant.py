import os

import requests
from flask import jsonify, request

from .constants import FAILED, SERVER_URL
from .logger import logger
from .utils import RECORDING_DIR, REVIEW_RECORDING_DIR, read_encrypted_jsonl


def polish_task_name_and_description():
    try:
        data = request.json
        task_name = data.get("task_name")
        task_description = data.get("task_description")
        if not task_name:
            return (
                jsonify({"status": FAILED, "message": "Error: Task_name is empty or None"}),
                400,
            )

        recording_name = data.get("recording_name", None)
        verifying = data.get("verifying", False)
        actions = []
        if recording_name:
            recording_path = os.path.join(RECORDING_DIR, recording_name) if not verifying else\
                os.path.join(REVIEW_RECORDING_DIR, recording_name)
            action_jsonl_path = os.path.join(recording_path, "reduced_events_vis.jsonl")
            raw_actions = read_encrypted_jsonl(action_jsonl_path)
            info_names = ["id", "action", "description", "time_stamp", "target"]
            
            for raw_action in raw_actions:
                action = {}
                for info_name in info_names:
                    if info_name in raw_action:
                        action[info_name] = raw_action[info_name]
                actions.append(action)
            
        response = requests.post(
            f"{SERVER_URL}/polish_task_name_and_description",
            json={
                "task_name": task_name,
                "task_description": task_description,
                "actions": actions
            },
            timeout=40,
        )

        response.raise_for_status()
        result = response.json()

        return jsonify(result), response.status_code

    except Exception as e:
        logger.exception(f"Unexpected error in polish_task_name_and_description: {e}")
        return (
            jsonify(
                {"status": FAILED, "message": f"An unexpected error occurred: {str(e)}"}
            ),
            500,
        )


