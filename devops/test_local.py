#!/usr/bin/env python3
"""
Скрыпт для тэставання Lambda функцыі лакальна
"""

import os
import sys
import json
from pathlib import Path

# Дадаем бацькоўскую дырэкторыю ў Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Загружаем зменныя асяроддзя
from dotenv import load_dotenv

load_dotenv()

# Імпартуем нашу функцыю
from verti_conversion import lambda_handler


def test_lambda_function():
    """Тэстуе Lambda функцыю з тэставымі дадзенымі"""

    # Тэставы event (можна змяніць пасля)
    test_event = {"source": "aws.events", "detail-type": "Scheduled Event", "detail": {}}

    # Тэставы context
    class TestContext:
        function_name = "verti-converter-test"
        function_version = "$LATEST"
        invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:verti-converter-test"
        memory_limit_in_mb = 1024
        aws_request_id = "test-request-id"
        log_group_name = "/aws/lambda/verti-converter-test"
        log_stream_name = "2024/01/01/[$LATEST]test-stream"
        remaining_time_in_millis = lambda: 900000  # 15 хвілін

    context = TestContext()

    print("Пачынаем тэставанне Lambda функцыі...")
    print(f"INPUT_BUCKET: {os.environ.get('INPUT_BUCKET')}")
    print(f"OUTPUT_BUCKET: {os.environ.get('OUTPUT_BUCKET')}")
    print(f"LOG_LEVEL: {os.environ.get('LOG_LEVEL', 'INFO')}")

    try:
        # Выклікаем функцыю
        result = lambda_handler(test_event, context)

        print("\n=== РЕЗУЛЬТАТ ===")
        print(f"Status Code: {result['statusCode']}")
        print(f"Body: {result['body']}")

        if result["statusCode"] == 200:
            print("✅ Функцыя выканалася паспяхова!")
        else:
            print("❌ Функцыя завершылася з памылкай")

    except Exception as e:
        print(f"❌ Памылка пры выкананні: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_lambda_function()
