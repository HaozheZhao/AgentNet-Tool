import threading
import os

from queue import Queue
import json
# from flask import request

from core.utils import (
    RECORDING_DIR,
    get_hk_time,
    check_recording_completeness,
    read_encrypted_jsonl,
    get_task_name_from_folder,
    get_description_from_folder,
    get_apps,
)
from core.logger import logger
from core.constants import SUCCEED, FAILED


def upload_recording(recording_name, annotator_info=None):

    from core.cloud_v2 import upload_folder_concurrent
    from datetime import datetime

    try:
        timestamp = get_hk_time()
        recording_path = os.path.join(RECORDING_DIR, recording_name)

        task_name = ""
        path = os.path.join(RECORDING_DIR, recording_name, "task_name.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                task_name = data.get("task_name", "")
        if not task_name and annotator_info:
            # Build task name from annotator info (matches Local page auto-generation)
            uname = annotator_info.get("username", "").strip()
            tid = annotator_info.get("task_id", "").strip()
            if uname and tid:
                task_name = f"{uname}_{tid}"
            elif uname:
                task_name = uname
        if not task_name:
            task_name = recording_name

        upload_folder = annotator_info.get("upload_folder", "recordings_new") if annotator_info else "recordings_new"

        # Include username in upload folder name if annotator_info is provided
        username = ""
        if annotator_info and annotator_info.get("username"):
            username = annotator_info["username"]
            upload_recording_name = timestamp + "_" + task_name + "_" + username + "_" + recording_name
        else:
            upload_recording_name = timestamp + "_" + task_name + "_" + recording_name

        oss_path = upload_folder + "/" + upload_recording_name

        # Write annotator_info.json to recording folder before uploading
        if annotator_info:
            annotator_info_path = os.path.join(recording_path, "annotator_info.json")
            info_data = {
                "username": annotator_info.get("username", ""),
                "task_id": annotator_info.get("task_id", ""),
                "query": annotator_info.get("query", ""),
                "step_by_step_instruction": annotator_info.get("step_by_step_instruction", ""),
                "upload_timestamp": datetime.now().isoformat(),
                "oss_upload_folder": oss_path,
            }
            with open(annotator_info_path, "w", encoding="utf-8") as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Written annotator_info.json to {annotator_info_path}")

        try:
            upload_folder_concurrent(
                local_folder_path=recording_path,
                remote_folder_path=oss_path
            )

        except Exception as e:
            logger.exception("upload_recording: upload_file failed.")
            return {
                "status": FAILED,
                "recording_name": recording_name,
                "message": f"Upload_recording failed: \n{str(e)}.",
            }

        logger.info(f"Successfully upload {recording_name}.")

        return {
            "status": SUCCEED,
            "recording_name": recording_name,
            "message": "Upload_recording succeed.",
        }

    except Exception as e:
        logger.exception(f"Upload_recording failed: \n{str(e)}")
        return {
            "status": FAILED,
            "recording_name": recording_name,
            "message": f"Upload_recording failed: \n{str(e)}.",
        }


class UploadService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.upload_queue = Queue()
        self.upload_thread = threading.Thread(
            target=self._process_upload_queue, daemon=True
        )
        self.upload_thread.start()

    def enqueue_upload(self, data):
        recording_name = data.get("recording_name", "")
        annotator_info = data.get("annotator_info", None)
        self.upload_queue.put((recording_name, annotator_info))

    def _process_upload_queue(self):
        while True:
            item = self.upload_queue.get()
            if item is None:
                self.upload_queue.task_done()
                continue

            recording_name, annotator_info = item

            try:
                result = upload_recording(recording_name, annotator_info)
                self.socketio.emit("upload_recording", result)
            except Exception as e:
                logger.exception(f"Upload_recording failed: {str(e)}")
                self.socketio.emit(
                    "upload_recording",
                    {
                        "status": FAILED,
                        "recording_name": recording_name,
                        "message": f"Upload_recording failed: {str(e)}.",
                    },
                )
