"""
SX-GPTアプリケーションメイン
"""

import datetime

import streamlit as st
# pylint: disable=E0401,E0611
from streamlit.components.v1 import html

import app.streamlit.plugins as plugins
from app.streamlit.utils.common import ParameterSession, hello
from app.streamlit.utils.display import (clipboard_buttom_HTML,
                                         display_all_messages,
                                         set_common_style)
from app.streamlit.utils.sessions import CommonSession
from sx_agents.utils import ChatMessage, Model
from sx_agents.utils.common import crawring_message

set_common_style()
params = ParameterSession.get()
session = CommonSession.get()


def display_sidebar(is_disabled, placeholder_messages, placeholder_selector):
    # Streamlit v1.30.0の時点ではwidgetのkeyによるsession_statは
    # page間遷移によって破壊され永続性がないため、手動でモデル選択の状態を保存
    #
    model = session.model
    with st.container():
        st.title("SX版GPT & 文書要約")
        st.caption(f"ver. {params.VERSION}@{session.model.type}環境")

        # ポータルへのリンク
        st.link_button(
            "マニュアル",
            "https://storage.cloud.google.com/manual-genaiapp/SXGPT_manual.pdf",
            disabled=is_disabled,
        )

        if st.button("この会話をダウンロード", disabled=is_disabled):
            session.status = "download"
            session.is_selector_activate = False
            session.is_sidebar_disabled = True

        st.header("設定")

        # モデル選択
        
        available_models = [
            model_name for model_name, config in params.MODEL_CONFIG.items()
            if config.get("visible", True)
        ]
        name = st.selectbox(
            "言語モデル",
            available_models,
            disabled=is_disabled,
        )
        if name != model.name:
            model_params = params.MODEL_CONFIG[name]
            session.model = Model(name=name, **model_params)
        # # ポータルへのリンク
        st.link_button(
            "ポータルへ戻る",
            "https://genai-portal.sxai.app/",
            disabled=is_disabled,
        )

        def event_reset():
            session.status = "reset"

        st.button("Reset", type="primary", on_click=event_reset)


def generate_download_messages(
    messages: list[ChatMessage], roles=["user", "assistant"]
):
    download_messages = []
    for message in messages:
        if message.role in roles:
            download_messages.append(f"#{message.role}\n{message.content}\n")
    return "\n".join(download_messages)


def download_message():
    with st.chat_message("assistant"):
        col_l, col_c, col_r = st.columns([0.6, 0.2, 0.2])
        with col_l:
            st.markdown(
                "準備ができました。このチャットをダウンロードしますか？"
            )

        def callback_download():
            session.status = "simplechat"
            session.is_selector_activate = True
            session.is_sidebar_disabled = False

        col_c.download_button(
            "はい",
            data=generate_download_messages(session.memory.messages),
            key="download_yes",
            file_name=f"""sxgpt_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt""",
            type="primary",
            on_click=callback_download,
        )

        if col_r.button("いいえ", key="download_no"):
            session.status = "simplechat"
            session.is_selector_activate = True
            session.is_sidebar_disabled = False
            st.rerun()


def display_selector() -> None:
    """プラグインセレクターを表示する"""

    placeholder = st.empty()
    with placeholder:
        with st.chat_message("user"):
            # placeholderを分割して左側にセレクター、右側に実行ボタンを表示
            col_l, col_r = st.columns([0.7, 0.3])
            with col_l:
                # プラグインセレクター
                aveilable_plugins = session.plugins[session.model.name]
                selector_message = (
                    "プラグイン選択..."
                    if aveilable_plugins
                    else f"{session.model.name}はプラグインに対応していません"
                )
                selected_plugin = st.selectbox(
                    "plugin_selector",
                    aveilable_plugins,
                    placeholder=selector_message,
                    index=None,
                    label_visibility="collapsed",
                )

                def event_select_plugin():
                    # プラグインが選択されたなら、ステータスをそのプラグインにして再実行
                    if selected_plugin is not None:
                        session.status = params.PLUGINS[selected_plugin]
                        session.is_wellcom_message_enable = False
                        session.is_selector_activate = False
                        session.is_sidebar_disabled = True

            with col_r:
                # 実行ボタン
                st.button(
                    "実行",
                    on_click=event_select_plugin,
                )


def copy_button():
    """コピーボタンを作成"""
    message_assistant = session.memory.fetch_recent_message("assistant")
    # クリップボードにコピーするために改行をエスケープ
    # しないと改行が入ってしまう
    message_assistant = message_assistant.replace("\n", "\\n")
    html(clipboard_buttom_HTML(message_assistant), height=40, width=150)


def index():
    """SX-GPTアプリケーションメイン"""
    # -------------------------------------------------------------------------
    # 画面構成の初期化
    # -------------------------------------------------------------------------
    # サイドバー設定
    placeholder_sidebar = st.sidebar.empty()
    # -------------------------------------------------------------------------
    # メッセージ表示用のplaceholderを作成
    placeholder_messages = st.empty()
    # セレクター表示用のplaceholderを作成
    placeholder_selector = st.empty()
    # placeholder_selector.empty()
    # プロンプト入力用のplaceholderを作成
    placeholder_prompt = st.empty()

    if session.status == "reset":
        # セッションがリセットされた場合は、メッセージとセレクターを空にする
        placeholder_messages.empty()
        placeholder_selector.empty()
        placeholder_prompt.empty()
        session.delete()
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    # -------------------------------------------------------------------------
    # サイドバーの表示
    # -------------------------------------------------------------------------
    with placeholder_sidebar:
        display_sidebar(
            session.is_sidebar_disabled,
            placeholder_messages,
            placeholder_selector,
        )

    # -------------------------------------------------------------------------
    # メッセージの表示
    # -------------------------------------------------------------------------
    if session.status:
        with placeholder_messages:
            message_container = st.container()
            with message_container:
                # 初回のみウェルカムメッセージを表示
                if session.is_wellcom_message_enable:
                    with st.chat_message("assistant"):
                        st.write_stream(
                            crawring_message(
                                params.WELLCOME_MESSAGE.format(hello=hello())
                            )
                        )
                    session.is_wellcom_message_enable = False
                # メッセージを表示
                display_all_messages(session.memory.messages[1:])

                # コピーボタンの表示
                if len(session.memory.messages) > 2:
                    _, col_r = st.columns([0.8, 0.2])
                    with col_r:
                        copy_button()
        # すでに表示したステータス系のメッセージをメモリから削除
        session.memory.remove_temporary_messages()

    # -------------------------------------------------------------------------
    # プラグイン実行
    # -------------------------------------------------------------------------
    # config.pyに記載されたプラグインを実行
    if session.status in list(params.PLUGINS.values()):
        # チャットインプット先に表示しておくとテキストが勝手にスクロールする
        placeholder_prompt.chat_input(
            f"{session.status}を実行中", disabled=True
        )
        # プラグイン実行用の画面
        placeholder_plugin = message_container.empty()
        module = getattr(plugins, session.status)

        # プラグインの実行
        module.execute(
            placeholder_plugin, session.memory, session.model, **session.kwargs
        )

        # プラグイン実行終了処理
        placeholder_plugin.empty()
        session.is_selector_activate = True
        session.is_sidebar_disabled = False
        session.status = "simplechat"
        session.prompt = ""
        st.rerun()

    # デフォルトのシンプルチャット実行
    if session.status == "simplechat":
        # プロンプト入力ウィジェット表示
        placeholder_prompt = st.empty()
        with placeholder_prompt:

            prompt = st.chat_input("ここにプロンプトを入力")
        # プロンプトの入力があればシンプルチャットを実行
        if prompt:
            placeholder_simplechat = message_container.empty()
            plugins.simplechat.execute(
                placeholder_simplechat,
                session.model,
                session.memory,
                prompt,
            )
            # 終了後の処理
            session.is_selector_activate = True
            session.prompt = None
            st.rerun()

    # テキストダウンロードを実行
    elif session.status == "download":
        placeholder_prompt.chat_input(
            f"{session.status}を実行中", disabled=True
        )
        placeholder_download = st.empty()
        with placeholder_download:
            download_message()

    # -------------------------------------------------------------------------
    # セレクター表示
    # -------------------------------------------------------------------------
    if session.is_selector_activate:
        with placeholder_selector:
            display_selector()


if __name__ == "__main__":
    index()
