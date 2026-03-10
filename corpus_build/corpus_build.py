import json
import boto3
import os
import logging
import unicodedata
import re
import base64
from typing import Dict, Any, List
from datetime import datetime
from belorthography import convert as belorthography_convert, Orthography


logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# AWS кліенты
s3_client = boto3.client("s3")
codebuild_client = boto3.client("codebuild")
lambda_client = boto3.client("lambda")

# Канстанта для "усе тэксты" корпуса
ALL_CORPUS_DISPLAY_NAME = "Усе тэксты"


def clear_concatenated_folder(bucket: str) -> int:
    """Выдаляе ўсе аб'екты ў тэчцы concatenated/"""
    deleted_count = 0
    error_count = 0
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix="concatenated/")
    
    for page in pages:
        if "Contents" not in page:
            continue
        objects_to_delete = [{"Key": obj["Key"]} for obj in page["Contents"]]
        if objects_to_delete:
            logger.info(f"Выдаляем {len(objects_to_delete)} аб'ектаў: {[o['Key'] for o in objects_to_delete[:10]]}...")
            response = s3_client.delete_objects(Bucket=bucket, Delete={"Objects": objects_to_delete})
            
            # Check for errors in delete response
            if "Errors" in response and response["Errors"]:
                for err in response["Errors"]:
                    logger.error(f"Памылка выдалення {err['Key']}: {err['Code']} - {err['Message']}")
                    error_count += 1
            
            deleted_count += len(response.get("Deleted", []))
    
    logger.info(f"Выдалена {deleted_count} аб'ектаў з concatenated/ (памылак: {error_count})")
    return deleted_count


def get_corpus_from_metadata(bucket: str, key: str) -> str | None:
    """Атрымлівае значэнне corpus з метададзеных S3 аб'екта (Base64 декадаванае)"""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = response.get("Metadata", {})
        corpus_encoded = metadata.get("corpus")
        if corpus_encoded:
            # Decode Base64 to get original UTF-8 corpus name
            return base64.b64decode(corpus_encoded).decode("utf-8")
        return None
    except Exception as e:
        logger.warning(f"Не ўдалося атрымаць метададзеныя для {key}: {e}")
        return None


def group_files_by_corpus(bucket: str, file_keys: List[str]) -> Dict[str, List[str]]:
    """Групуе файлы па значэнні corpus з метададзеных"""
    corpus_files: Dict[str, List[str]] = {}
    
    for key in file_keys:
        corpus = get_corpus_from_metadata(bucket, key)
        # Skip empty, None or whitespace-only corpus values
        if corpus and corpus.strip():
            corpus = corpus.strip()
            if corpus not in corpus_files:
                corpus_files[corpus] = []
            corpus_files[corpus].append(key)
    
    return corpus_files


def convert_to_lacinka(display_name: str) -> str:
    """
    Канвертуе кірылічную назву ў лацінку.
    Выдаляе дыякрытыкі, ł -> l, прабелы -> падкрэсліванні.
    """
    if not display_name or not display_name.strip():
        raise ValueError(f"Empty display_name provided to convert_to_lacinka")
    
    lacinka = belorthography_convert(display_name, Orthography.CLASSICAL, Orthography.LATIN_NO_DIACTRIC)

    # Прабелы -> падкрэсліванні, толькі ASCII літары, лічбы і падкрэсліванні
    lacinka = re.sub(r"\s+", "_", lacinka)
    lacinka = re.sub(r"[^a-zA-Z0-9_]", "", lacinka)
    lacinka = lacinka.lower().strip("_")
    
    if not lacinka:
        raise ValueError(f"convert_to_lacinka produced empty result for '{display_name}'")

    return lacinka


def generate_config_files(bucket: str, corpora: Dict[str, str]) -> int:
    """
    Генеруе config файлы для NoSke з шаблону.
    
    Args:
        bucket: S3 bucket
        corpora: Dict[name, displayName] - слоўнік з lacinka назвамі і displayName
    
    Returns:
        Колькасць створаных config файлаў
    """
    # Чытаем шаблон з лакальнага файла (пакаваны разам з Lambda)
    template_path = os.path.join(os.path.dirname(__file__), "template.conf")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
    
    created_count = 0
    for name, display_name in corpora.items():
        info_href = "/kultura/" if name == "kultura" else ""
        config_content = (
            template_content
            .replace("%name%", name)
            .replace("%displayName%", display_name)
            .replace("%infoHref%", info_href)
        )
        config_key = f"concatenated/registry/{name}.conf"
        
        s3_client.put_object(
            Bucket=bucket,
            Key=config_key,
            Body=config_content.encode("utf-8"),
            ContentType="text/plain; charset=utf-8"
        )
        logger.info(f"Створаны config: {config_key}")
        created_count += 1
    
    return created_count


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler для запуску зборкі корпуса па распісанні
    Правярае _info.json файл і параўноўвае дату processed з датай апошняга білду
    """
    logger.info(f"Пачатак апрацоўкі падзеі: {json.dumps(event)}")

    try:
        # Вызначаем асяроддзе
        environment = os.environ.get("ENVIRONMENT", "dev")
        input_bucket = f"instytutbelmovy-vert-{environment}" if environment == "dev" else "instytutbelmovy-vert"

        logger.info(f"Асяроддзе: {environment}")
        logger.info(f"Input bucket: {input_bucket}")

        force_build = False
        if event and isinstance(event, dict):
            force_build = event.get("force_build", False)

        # 1. Правяраем ці павінна запускацца зборка
        should_build = force_build or should_trigger_build(input_bucket, environment)

        if not should_build:
            logger.info("Зборка не патрэбна - няма новых апрацаваных файлаў")
            return {"statusCode": 200, "body": json.dumps({"message": "Зборка не патрэбна - няма новых апрацаваных файлаў", "environment": environment, "triggered": False})}

        # 2. Сканаваць усе .vert файлы ў bucket
        vert_files = list_vert_files(input_bucket)

        if not vert_files:
            logger.info("Няма .vert файлаў для апрацоўкі")
            return {"statusCode": 200, "body": json.dumps({"message": "Няма .vert файлаў для апрацоўкі"})}

        logger.info(f"Знойдзена {len(vert_files)} .vert файлаў")

        # 3. Ачысціць тэчку concatenated/
        clear_concatenated_folder(input_bucket)

        # 4. Згрупаваць файлы па корпусах
        corpus_files = group_files_by_corpus(input_bucket, vert_files)
        logger.info(f"Знойдзена {len(corpus_files)} корпусаў: {list(corpus_files.keys())}")

        # 5. Стварыць канкатэнаваныя файлы для кожнага корпуса
        corpora_config: Dict[str, str] = {}  # name -> displayName
        
        # "Усе тэксты" - усе файлы
        all_name = convert_to_lacinka(ALL_CORPUS_DISPLAY_NAME)
        all_vert_key = f"concatenated/{all_name}/{all_name}.vert"
        concatenate_files_in_s3(input_bucket, vert_files, all_vert_key)
        corpora_config[all_name] = ALL_CORPUS_DISPLAY_NAME
        logger.info(f"Створаны агульны файл: {all_vert_key}")

        # Па-корпусныя файлы
        for display_name, files in corpus_files.items():
            name = convert_to_lacinka(display_name)
            vert_key = f"concatenated/{name}/{name}.vert"
            concatenate_files_in_s3(input_bucket, files, vert_key)
            corpora_config[name] = display_name
            logger.info(f"Створаны файл корпуса '{display_name}': {vert_key} ({len(files)} файлаў)")

        # 6. Згенераваць config файлы
        configs_created = generate_config_files(input_bucket, corpora_config)
        logger.info(f"Створана {configs_created} config файлаў")

        # 7. Запісаць інфармацыю пра зборку ў лагі
        logger.info(
            f"""
Пачатак зборкі корпуса
Дата: {datetime.now().isoformat()}
Асяроддзе: {environment}
Колькасць .vert файлаў: {len(vert_files)}
Колькасць корпусаў: {len(corpora_config)}
        """.strip()
        )

        # 8. Запусьціць CodeBuild праект
        build_project_name = f"corpus-build-{environment}"
        build_id = start_codebuild_project(build_project_name, environment)

        logger.info(f"CodeBuild праект запушаны: {build_id}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Зборка корпуса запушана", "environment": environment, "files_processed": len(vert_files), "corpora_count": len(corpora_config), "build_id": build_id, "build_project": build_project_name, "triggered": True}
            ),
        }

    except Exception as e:
        logger.error(f"Памылка пры запуску зборкі корпуса: {str(e)}")
        raise


def should_trigger_build(bucket: str, environment: str) -> bool:
    """
    Правярае ці павінна запускацца зборка корпуса

    Правярае:
    1. Ці ёсць _info.json файл у bucket
    2. Ці дата processed ў _info.json больш за дату апошняга пасьпяховага білду
    """
    try:
        # Правяраем ці ёсць _info.json файл
        try:
            response = s3_client.get_object(Bucket=bucket, Key="_info.json")
            info_content = response["Body"].read().decode("utf-8")
            info_data = json.loads(info_content)

            processed_date_str = info_data.get("processed")
            if not processed_date_str:
                logger.warning("_info.json не змяшчае поле 'processed'")
                return False

            # Парсім дату processed
            processed_date = datetime.fromisoformat(processed_date_str.replace("Z", "+00:00"))
            logger.info(f"Дата processed: {processed_date}")

        except s3_client.exceptions.NoSuchKey:
            logger.warning("_info.json файл не знойдзены")
            return False
        except Exception as e:
            logger.error(f"Памылка пры чытанні _info.json: {str(e)}")
            return False

        # Атрымліваем дату апошняга пасьпяховага білду
        last_build_date = get_last_successful_build_date(environment)

        if last_build_date is None:
            logger.info("Няма апошняга пасьпяховага білду, запускаем зборку")
            return True

        logger.info(f"Дата апошняга білду: {last_build_date}")

        # Параўноўваем даты
        if processed_date > last_build_date:
            logger.info("Дата processed больш за дату апошняга білду, запускаем зборку")
            return True
        else:
            logger.info("Дата processed не больш за дату апошняга білду, зборка не патрэбна")
            return False

    except Exception as e:
        logger.error(f"Памылка пры праверцы ўмоў для зборкі: {str(e)}")
        # У выпадку памылкі не запускаем зборку
        return False


def get_last_successful_build_date(environment: str) -> datetime:
    """
    Атрымлівае дату апошняга пасьпяховага білду з CodeBuild
    """
    try:
        project_name = f"corpus-build-{environment}"

        # Атрымліваем апошнія білды
        response = codebuild_client.list_builds_for_project(projectName=project_name, sortOrder="DESCENDING")

        if not response.get("ids"):
            logger.info("Няма білдаў для праекта")
            return None

        # Атрымліваем дэталі апошніх білдаў
        build_ids = response["ids"][:10]  # Апошнія 10 білдаў
        builds_response = codebuild_client.batch_get_builds(ids=build_ids)

        # Шукаем апошні пасьпяховы білд
        for build in builds_response.get("builds", []):
            if build.get("buildStatus") == "SUCCEEDED":
                build_timestamp = build.get("endTime")
                if build_timestamp:
                    logger.info(f"Знойдзены апошні пасьпяховы білд: {build.get('id')} ад {build_timestamp}")
                    return build_timestamp

        logger.info("Няма пасьпяховых білдаў")
        return None

    except Exception as e:
        logger.error(f"Памылка пры атрыманні даты апошняга білду: {str(e)}")
        return None


def list_vert_files(bucket: str) -> List[str]:
    """Сканаваць усе .vert файлы ў bucket (акрамя concatenated/)"""
    try:
        vert_files = []
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix="")
        
        for page in pages:
            if "Contents" not in page:
                continue
            for obj in page["Contents"]:
                key = obj["Key"]
                # Ігнаруем файлы ў concatenated/ і старыя all.vert
                if key.endswith(".vert") and not key.startswith("concatenated/") and key != "all.vert":
                    vert_files.append(key)
        
        return vert_files
    except Exception as e:
        logger.error(f"Памылка пры сканаванні файлаў: {str(e)}")
        raise


def concatenate_files_in_s3(bucket: str, file_keys: List[str], output_key: str):
    """
    Канкатэнаваць файлы непасрэдна ў S3 з выкарыстаннем Multipart Upload

    Перавагі:
    - Не выкарыстоўвае памяць Lambda
    - Эфектыўна для любога памеру файлаў
    - Выкарыстоўвае S3 Multipart Upload для вялікіх файлаў
    - Аўтаматычна апрацоўвае памылкі і скасоўвае upload
    """
    try:
        logger.info(f"Пачатак S3 канкатэнацыі {len(file_keys)} файлаў")

        # Пачаць Multipart Upload
        mpu = s3_client.create_multipart_upload(Bucket=bucket, Key=output_key)
        upload_id = mpu["UploadId"]

        parts = []
        part_number = 1

        # Аб'яднаць файлы ў групы па 5MB (мінімальны памер часткі)
        chunk_size = 5 * 1024 * 1024  # 5MB
        current_chunk = b""

        for i, key in enumerate(file_keys, 1):
            try:
                # Скачаць файл
                response = s3_client.get_object(Bucket=bucket, Key=key)
                file_content = response["Body"].read()

                # Дадаць змест да бягучага чанка
                current_chunk += file_content + b"\n"

                # Калі чанк дасягнуў памеру, загрузіць яго
                if len(current_chunk) >= chunk_size:
                    # Загрузіць частку
                    part_response = s3_client.upload_part(Bucket=bucket, Key=output_key, PartNumber=part_number, UploadId=upload_id, Body=current_chunk)

                    parts.append({"ETag": part_response["ETag"], "PartNumber": part_number})

                    current_chunk = b""
                    part_number += 1

                    logger.info(f"Загружана частка {part_number-1} для файла {i}/{len(file_keys)}")

            except Exception as e:
                logger.error(f"Памылка пры апрацоўцы файла {key}: {str(e)}")
                continue

        # Загрузіць апошні чанк, калі ён не пусты
        if current_chunk:
            part_response = s3_client.upload_part(Bucket=bucket, Key=output_key, PartNumber=part_number, UploadId=upload_id, Body=current_chunk)

            parts.append({"ETag": part_response["ETag"], "PartNumber": part_number})

        # Завершыць Multipart Upload
        s3_client.complete_multipart_upload(Bucket=bucket, Key=output_key, UploadId=upload_id, MultipartUpload={"Parts": parts})

        logger.info(f"S3 канкатэнацыя завершана. Загружана {len(parts)} часткаў")

    except Exception as e:
        # Скасаваць Multipart Upload у выпадку памылкі
        try:
            s3_client.abort_multipart_upload(Bucket=bucket, Key=output_key, UploadId=upload_id)
        except:
            pass
        logger.error(f"Памылка пры S3 канкатэнацыі: {str(e)}")
        raise


def start_codebuild_project(project_name: str, environment: str) -> str:
    """Запусьціць CodeBuild праект"""
    try:
        # Параметры зборкі
        build_params = {
            "projectName": project_name,
            "environmentVariablesOverride": [{"name": "ENVIRONMENT", "value": environment, "type": "PLAINTEXT"}, {"name": "BUILD_TIMESTAMP", "value": datetime.now().isoformat(), "type": "PLAINTEXT"}],
        }

        # Запусьціць зборку
        response = codebuild_client.start_build(**build_params)
        build_id = response["build"]["id"]

        logger.info(f"CodeBuild зборка запушана: {build_id}")
        return build_id

    except Exception as e:
        logger.error(f"Памылка пры запуску CodeBuild: {str(e)}")
        raise
