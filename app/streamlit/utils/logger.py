"""
ロギングの設定を行い、ログをGoogle Cloud Loggingに送信するためのハンドラを追加するモジュール"""

import json
import os

# ------------------------------------------------------------------------------
# logger設定
# ------------------------------------------------------------------------------
PLATFORM = os.getenv("PLATFORM")
if PLATFORM in ["GCP", "local"]:
    from google.cloud.logging.handlers import StructuredLogHandler
    from google.cloud.logging_v2.handlers import setup_logging

import logging

import streamlit.logger

streamlit.logger.get_logger = logging.getLogger
streamlit.logger.setup_formatter = None
streamlit.logger.update_formatter = lambda *a, **k: None
streamlit.logger.set_log_level = lambda *a, **k: None
logging.basicConfig(
    #    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    force=True,
)
logger_ = logging.getLogger("streamlit")
logger_.propagate = False
if PLATFORM in ["GCP", "local"]:
    handler = StructuredLogHandler()
    #        handler = CloudLoggingHandler(client)
    setup_logging(handler)
    logger_.addHandler(handler)


# logger wrapper
def logger_info(
    source: str,
    prompt: str | None = None,
    response: str | None = None,
    model_name: str | None = None,
    model_type: str | None = None,
    files: str | None = None,
    real_time: float | None = None,
):
    data_dict = {
        "app": "sxgpt",
        "source": source,
        "prompt": prompt,
        "response": response,
        "type": model_type,
        "model": model_name,
        "files": files,
        "real_time": get_str_hms_from(real_time) if real_time else None,
    }
    logger_.info(json.dumps(data_dict, ensure_ascii=False))


def logger_error(
    source,
    prompt=None,
    model_name=None,
    model_type=None,
    msg=None,
    files=None,
    traceback=None,
    real_time=None,
):
    data_dict = {
        "app": "sxgpt",
        "source": source,
        "type": model_type,
        "model": model_name,
        "msg": msg,
        "prompt": prompt,
        "traceback": f"{traceback}",
        "files": files,
        real_time: get_str_hms_from(real_time) if real_time else None,
    }
    logger_.error(json.dumps(data_dict, ensure_ascii=False))


def get_str_hms_from(sec: float):
    if not isinstance(sec, float):
        return None
    m, s = divmod(sec, 60)
    h, m = divmod(int(m), 60)
    return f"{int(h):0>2}:{int(m):0>2}:{s:06.3f}s"
