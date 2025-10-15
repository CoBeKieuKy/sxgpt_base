"""シンプルなチャットのプラグイン"""

import time
import traceback

import streamlit as st

# pylint: disable=E0401,E0611
from streamlit.delta_generator import DeltaGenerator

from app.streamlit.utils.logger import logger_info, logger_error
from sx_agents.utils import ChatMemory, Model
from sx_agents.utils.common import crawring_message_from_response


def execute(
    placeholder: DeltaGenerator,
    model: Model,
    memory: ChatMemory,
    prompt: str,
) -> None:
    """simplechatのメイン処理
    Args:
        placeholder (DeltaGenerator): プレースホルダ
        model: (Model): モデル
        memory (ChatMemory): チャットのメモリ
        prompt (str): プロンプト
    """
    with placeholder:
        with st.spinner("プロンプトを調整中..."):
            prompt_w_sys_role = memory.prompt_with_system_role(
                "user", prompt, vision=model.vision
            )
            # 長すぎるプロンプトはエラー
            if not model.is_less_than_token_limit(prompt_w_sys_role):
                memory.append_error("プロンプトが長すぎます。")
                st.rerun()
            # メッセージ作成
            messages = memory.prompt_with_all_messages(
                "user", prompt, vision=model.vision
            )
            messages = model.reduce_messages(messages)
    #
    with placeholder:
        with st.container():
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.spinner("回答しています...", show_time=True):
                with st.chat_message("assistant"):
                    with st.container():
                        try:
                            stime = time.time()
                            response = model.create_chat(
                                messages,
                                stream=True,
                            )
                            full_response = st.write_stream(
                                crawring_message_from_response(response)
                            )
                            etime = time.time()
                        except Exception as e:
                            err_message = (
                                f"APIとの通信に失敗しました。 Error: {str(e)}"
                            )
                            memory.append_error(content=err_message)
                            logger_error(
                                __name__,
                                prompt=prompt,
                                msg=err_message,
                                traceback=traceback.format_exc(),
                                model_name=model.name,
                                model_type=model.type,
                            )
                            st.rerun()

    # 終了処理
    memory.append_user(prompt)
    memory.append_assistant(str(full_response))
    logger_info(
        __name__,
        prompt=prompt,
        response=str(full_response),
        model_name=model.name,
        model_type=model.type,
        real_time=(etime - stime),
    )
