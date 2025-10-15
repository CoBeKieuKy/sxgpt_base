import os
import time
import traceback
from io import BytesIO

import PIL
import PIL.Image
import streamlit as st

from streamlit.delta_generator import DeltaGenerator

from app.streamlit.utils.logger import logger_info, logger_error
from app.streamlit.utils.sessions import PluginSession
from sx_agents.utils import ChatMemory, Model
from sx_agents.utils.common import (
    crawring_message_from_response,
    to_normalized_pic,
    to_thumbnail_pic,
)

type Image = PIL.Image.Image

WHITE_LIST = ["gpt-4o"]


def back_to_home():
    session = PictureSession.get()
    session.status = "exit"


class PictureSession(PluginSession):
    status = "upload"
    filename: str = ""
    suffix: str = ""
    image: Image | None = None
    thumbnail: Image | None = None
    docs: list[str] = []


def upload_files(placeholder: DeltaGenerator):
    with placeholder.container():
        with st.chat_message("assistant"):
            st.markdown("画像をアップロードしてください。")
        placeholder_uploader = st.empty()
        with placeholder_uploader:
            uploaded_file = st.file_uploader(
                "対応ファイル: png, jpg, jpeg, gif, pdf",
                type=["png", "jpg", "jpeg", "gif"],
                key="picture_file_uploaded",
            )
        placeholder_cancel = st.empty()
        with placeholder_cancel:
            st.button(
                "Cancel",
                on_click=back_to_home,
                key="picture_upload_cancel",
            )
    if uploaded_file:
        placeholder_cancel.empty()
        placeholder_uploader.empty()
        return uploaded_file
    else:
        st.stop()


def preprocessing(placeholder: DeltaGenerator, uploaded_file: BytesIO):
    with placeholder.container():
        with st.chat_message("assistant"):
            with st.status(
                "読込んだファイルの前処理を行っています...", expanded=True
            ):
                suffix = os.path.splitext(uploaded_file.name)[-1]
                filename = uploaded_file.name
                images_ = PIL.Image.open(uploaded_file)
                rawdata = to_normalized_pic(images_)
        placeholder_cancel = st.empty()
        with placeholder_cancel:
            st.button(
                "Cancel",
                on_click=PictureSession.exit_plugin,
                key="picture_preprocessing_cancel",
            )
    placeholder_cancel.empty()
    placeholder.empty()
    return filename, suffix, rawdata


def input_prompt(placeholder: DeltaGenerator, thumbnail: Image):
    with placeholder.container():
        st.image(thumbnail)
        with st.chat_message("assistant"):
            st.markdown("画像と共に送るプロンプトを入力してください。\n\n")
        #
        with st.chat_message("user"):
            with st.container():
                st.markdown("ここにプロンプトを入力")
                prompt = st.chat_input(
                    "プロンプト入力を待っています...",
                    key="picture_input",
                )
        placeholder_cancel = st.empty()
        with placeholder_cancel:
            st.button(
                "Cancel",
                on_click=back_to_home,
                key="picture_input_prompt",
            )
    if prompt:
        placeholder_cancel.empty()
        return prompt
    else:
        st.stop()


def output_streaming(
    placeholder: DeltaGenerator,
    memory: ChatMemory,
    model: Model,
    prompt: str,
    image: Image | None,
    thumbnail: Image | None,
):
    with placeholder:

        with st.container():
            with st.chat_message("user"):
                with st.container():
                    st.markdown(prompt)
                    if thumbnail:
                        st.image(thumbnail)
            with st.spinner("プロンプトを準備しています...", show_time=True):
                messages = memory.prompt_with_all_messages(
                    "user", prompt, image
                )
                messages = model.reduce_messages(messages)
                if len(messages) < 2:
                    memory.append_warning("プロンプトが長すぎます")
                    st.rerun()
            with st.chat_message("assistant"):

                placeholder_streaming = st.empty()
            st.button(
                "Cancel",
                on_click=back_to_home,
                key="picture_straming_cancel",
            )
        with placeholder_streaming:
            with st.container():
                with st.spinner("回答しています..."):
                    response_chunks = model.create_chat(messages, stream=True)
                    full_response = st.write_stream(
                        crawring_message_from_response(response_chunks)
                    )
            st.markdown(full_response)
    return full_response


def execute(
    placeholder: DeltaGenerator, memory: ChatMemory, model: Model, **kwargs
):
    session: PictureSession = PictureSession.get()
    if "Session" in kwargs:
        session.update(kwargs["Session"])

    if session.status == "exit":
        # セッション終了
        placeholder.empty()
        session.exit_plugin()
        st.rerun()

    if session.status == "upload":
        # ファイルのアップロード
        uploaded_file = upload_files(placeholder)
        session.filename, session.suffix, rawdata = preprocessing(
            placeholder, uploaded_file
        )
        session.image = rawdata
        session.thumbnail = to_thumbnail_pic(rawdata)
        placeholder.empty()
        session.status = "input"
        st.rerun()

    if session.status == "input":
        # プロンプト入力待ち
        prompt = input_prompt(placeholder, session.thumbnail)
        if prompt:
            try:
                stime = time.time()
                full_response = output_streaming(
                    placeholder,
                    memory,
                    model,
                    prompt,
                    session.image,
                    session.thumbnail,
                )
                etime = time.time()
            except Exception as e:
                memory.append_error(
                    f"APIとの通信に失敗しました。 Error: {str(e)}"
                )
                logger_error(
                    __name__,
                    prompt=prompt,
                    msg=f"APIとの通信に失敗しました。 Error: {str(e)}",
                    traceback=traceback.format_exc(),
                    model_name=model.name,
                    model_type=model.type,
                )
                PictureSession.exit_plugin()
                st.rerun()
            # 終了処理
            tdiff = etime - stime
            memory.append_user(prompt, session.image)
            memory.append_assistant(str(full_response))
            logger_info(
                __name__,
                prompt=prompt,
                response=str(full_response),
                files=session.filename,
                model_name=model.name,
                model_type=model.type,
                real_time=tdiff,
            )
            session.status = "exit"
            st.rerun()
    st.stop()
