import os

# =============================================================================
# КАНФІГУРАЦЫЯ ДЛЯ ЛАКАЛЬНАГА ТЭСТАВАННЯ
# =============================================================================

# Налады для лакальнага тэставання
LOCAL_AWS_PROFILE = "ibm-lambda-local-dev"
LOCAL_INPUT_BUCKET = "ibm-editor-dev"
LOCAL_OUTPUT_BUCKET = "ibm-vert-dev"

# Прыклад выкарыстання параметра process_all_files:
# - Звычайны выклік (толькі змененыя файлы): {}
# - Апрацоўка ўсіх файлаў: {"process_all_files": True}
#
# Git інфармацыя дадаецца аўтаматычна ў response для адсочвання версіі кода
# Інфармацыя перадаецца праз build args у Docker і захоўваецца ў git_info.json

if __name__ == "__main__":
    # Для лакальнага тэставання
    os.environ["AWS_PROFILE"] = LOCAL_AWS_PROFILE

import json
import boto3
import logging
import tempfile
import traceback
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from automations.vert_io import VertIO

s3_client = boto3.client("s3")


def get_git_info() -> Dict[str, str]:
    """Атрымлівае git інфармацыю з файла git_info.json"""
    try:
        git_info_path = os.path.join(os.path.dirname(__file__), "git_info.json")
        if os.path.exists(git_info_path):
            with open(git_info_path, "r", encoding="utf-8") as f:
                git_info = json.load(f)
                return git_info
        else:
            return {"git_commit_hash": "unknown", "git_commit_date": "unknown", "git_branch": "unknown", "build_time": "unknown"}
    except Exception:
        return {"git_commit_hash": "unknown", "git_commit_date": "unknown", "git_branch": "unknown", "build_time": "unknown"}


class VertiConverter:
    def __init__(self, input_bucket: str, output_bucket: str, logger: logging.Logger):
        self.input_bucket = input_bucket
        self.output_bucket = output_bucket
        self.info_file_key = "_info.txt"
        self.logger = logger

    def get_last_updated_on(self) -> Optional[datetime]:
        try:
            response = s3_client.get_object(Bucket=self.output_bucket, Key=self.info_file_key)
            info_data = json.loads(response["Body"].read().decode("utf-8"))
            return datetime.fromisoformat(info_data["last_updated_on"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                self.logger.info("Info файл не існуе, пачынаем з нуля")
                return None
            else:
                raise

    def update_info_file(self, last_updated_on: datetime) -> None:
        info_data = {"last_updated_on": last_updated_on.isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()}
        s3_client.put_object(Bucket=self.output_bucket, Key=self.info_file_key, Body=json.dumps(info_data, ensure_ascii=False, indent=2), ContentType="application/json")
        self.logger.info(f"Абноўлены info файл з last_updated_on: {last_updated_on}")

    def list_modified_files(self, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        modified_files = []
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.input_bucket)
        for page in pages:
            if "Contents" not in page:
                continue
            for obj in page["Contents"]:
                key = obj["Key"]
                if not key.endswith(".verti"):
                    continue
                last_modified = obj["LastModified"]
                if since_date is None or last_modified > since_date:
                    modified_files.append({"key": key, "last_modified": last_modified, "size": obj["Size"]})
        return modified_files

    def download_file(self, key: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".verti")
        temp_file_path = temp_file.name
        temp_file.close()
        s3_client.download_file(self.input_bucket, key, temp_file_path)
        return temp_file_path

    def convert_verti_to_vert(self, input_path: str) -> str:
        document = VertIO.read_verti(input_path)
        vert_path = input_path.replace(".verti", ".vert")
        VertIO.write_vert(document, vert_path)
        return vert_path

    def upload_file(self, local_path: str, output_key: str) -> None:
        s3_client.upload_file(local_path, self.output_bucket, output_key)

    def cleanup_temp_files(self, *file_paths: str) -> None:
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                self.logger.warning(f"Не ўдалося выдаліць файл {file_path}: {e}")

    def process_files(self, process_all_files: bool = False) -> Dict[str, Any]:
        # Калі process_all_files=True, то апрацоўваем усе файлы незалежна ад last_updated_on
        last_updated_on = None if process_all_files else self.get_last_updated_on()

        if process_all_files:
            self.logger.info("Апрацоўка ўсіх файлаў (process_all_files=True)")
        else:
            self.logger.info(f"Апрацоўка файлаў змененых пасля: {last_updated_on}")

        modified_files = self.list_modified_files(last_updated_on)
        if not modified_files:
            self.logger.info("Няма новых файлаў для апрацоўкі")
            return {"processed_files": 0, "last_updated_on": last_updated_on.isoformat() if last_updated_on else None, "process_all_files": process_all_files, "has_errors": False}
        max_last_modified = None
        processed_count = 0
        failed_count = 0
        temp_files = []
        try:
            for file_info in modified_files:
                key = file_info["key"]
                self.logger.info(f"Апрацоўка файла {key}")
                output_key = key.replace(".verti", ".vert")
                try:
                    temp_verti_path = self.download_file(key)
                    temp_files.append(temp_verti_path)
                    temp_vert_path = self.convert_verti_to_vert(temp_verti_path)
                    temp_files.append(temp_vert_path)
                    self.upload_file(temp_vert_path, output_key)
                    processed_count += 1
                    if max_last_modified is None or file_info["last_modified"] > max_last_modified:
                        max_last_modified = file_info["last_modified"]
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Памылка пры апрацоўцы файла {key}: {e}")
                    self.logger.error(traceback.format_exc())
                    continue
        finally:
            self.cleanup_temp_files(*temp_files)

        # Абнаўляем info файл толькі калі не апрацоўваем усе файлы
        if max_last_modified:
            self.update_info_file(max_last_modified)

        has_errors = failed_count > 0
        return {
            "processed_files": processed_count,
            "failed_files": failed_count,
            "last_updated_on": max_last_modified.isoformat() if max_last_modified else None,
            "total_files_found": len(modified_files),
            "process_all_files": process_all_files,
            "has_errors": has_errors,
        }


def lambda_handler(event, context):

    # У AWS Lambda выкарыстоўваем убудаваны логер
    logger = logging.getLogger(__name__)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    try:
        input_bucket = os.environ.get("INPUT_BUCKET")
        output_bucket = os.environ.get("OUTPUT_BUCKET")
        if not input_bucket or not output_bucket:
            raise ValueError("Патрабуюцца пераменныя асяроддзя INPUT_BUCKET і OUTPUT_BUCKET")

        # Атрымліваем параметр process_all_files з event
        process_all_files = False
        if event and isinstance(event, dict):
            process_all_files = event.get("process_all_files", False)

        git_info = get_git_info()
        logger.info(f"Канвэртацыя файлаў з {input_bucket} у {output_bucket}. Git хэш: {git_info['git_commit_hash']}")
        logger.info(f"Параметр process_all_files: {process_all_files}")

        converter = VertiConverter(input_bucket, output_bucket, logger)
        result = converter.process_files(process_all_files=process_all_files)
        logger.info(f"Апрацоўка завершана. Апрацаваных файлаў: {result['processed_files']}, памылак: {result.get('failed_files', 0)}")

        # Дадаем git інфармацыю ў response
        result.update(git_info)
        result["executed_at"] = datetime.now(timezone.utc).isoformat()

        # Вяртаем статус памылкі калі былі памылкі пры апрацоўцы файлаў
        if result.get("has_errors", False):
            logger.warning(f"Апрацоўка завершана з памылкамі. Памылак: {result.get('failed_files', 0)}")
            return {"statusCode": 500, "body": json.dumps(result, ensure_ascii=False, indent=2)}
        else:
            return {"statusCode": 200, "body": json.dumps(result, ensure_ascii=False, indent=2)}
    except Exception as e:
        logger.error(f"Памылка ў Lambda функцыі: {e}")
        logger.error(traceback.format_exc())

        # Дадаем git інфармацыю нават у выпадку памылкі
        git_info = get_git_info()
        error_response = {"error": str(e), "traceback": traceback.format_exc(), "executed_at": datetime.now(timezone.utc).isoformat()}
        error_response.update(git_info)
        return {"statusCode": 500, "body": json.dumps(error_response, ensure_ascii=False)}


if __name__ == "__main__":
    # Для лакальнага тэставання
    load_dotenv()
    os.environ["INPUT_BUCKET"] = LOCAL_INPUT_BUCKET
    os.environ["OUTPUT_BUCKET"] = LOCAL_OUTPUT_BUCKET

    # Прыклад выкліку з параметрам для апрацоўкі ўсіх файлаў
    # event = {"process_all_files": True}
    # Прыклад звычайнага выкліку (толькі змененыя файлы)
    event = {}

    print(lambda_handler(event, None))
