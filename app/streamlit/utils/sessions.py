"""Streamlitのセッション管理を行うモジュール"""

from abc import ABCMeta
from dataclasses import dataclass
from typing import Any, Self

import streamlit as st

from app.streamlit import plugins
from app.streamlit.utils.common import ParameterSession
from sx_agents.utils import ChatMemory, Model


# ------------------------------------------------------------------------------
# main session設定
# ------------------------------------------------------------------------------
class CommonSession:
    env: str
    model: Model
    memory: ChatMemory
    status: str = "simplechat"
    #
    plugins: dict[str, list[str]]
    prompt: str = ""
    kwargs: dict[str, Any] = {}
    #
    is_selector_activate: bool = True
    is_sidebar_disabled: bool = False
    idx_selected_plugin: int = 0
    is_selector_activate: bool = True
    is_wellcom_message_enable: bool = True
    #

    def __init__(self, env: str, name: str | None = None):
        params = ParameterSession.get()
        self.set_env(env)
        if name is not None:
            self.set_model(name)
        self.memory = ChatMemory(
            params.SYSTEM_ROLE,
            params.DISPLAY_PIC_HEIGHT,
            params.DISPLAY_PIC_BACKGROUND_COLOR,
        )

    @classmethod
    def get(cls) -> Self:
        if "common" not in st.session_state:
            params = ParameterSession.get()
            model_config = params.MODEL_CONFIG[params.DEFUALT_ENV]
            name = list(model_config["models"].keys())[0]
            session = cls(params.DEFUALT_ENV, name)
            session.set_env(params.DEFUALT_ENV)
            st.session_state["common"] = session
        return st.session_state["common"]

    @property
    def available_models(self) -> list[str]:
        params = ParameterSession.get()
        model_config = params.MODEL_CONFIG[self.env]
        return list(model_config["models"].keys())

    @property
    def available_plugins(self) -> dict[str, list[str]]:
        params = ParameterSession.get()
        available_plugins = {}
        for model_name in self.available_models:
            available_plugins[model_name] = []
            for plugin_name, module_name in params.PLUGINS.items():
                module = getattr(plugins, module_name, None)
                if module is None:
                    continue
                if hasattr(module, "WHITE_LIST"):
                    if ("all" in module.WHITE_LIST) or (
                        model_name in module.WHITE_LIST
                    ):
                        available_plugins[model_name].append(plugin_name)
                else:
                    available_plugins[model_name].append(plugin_name)
        return available_plugins

    def set_env(self, env: str):
        params = ParameterSession.get()
        if env not in params.MODEL_CONFIG:
            raise ValueError(f"Invalid environment: {env}")
        self.env = env
        self.plugins = self.available_plugins
        name = self.available_models[0]
        self.set_model(name)

    def set_model(self, name: str):
        params = ParameterSession.get()
        model_config = params.MODEL_CONFIG[self.env]
        model_params = model_config["config"] | model_config["models"][name]
        self.model = Model(**model_params)

    @classmethod
    def delete(cls) -> None:
        if "common" in st.session_state:
            del st.session_state["common"]

    @classmethod
    def reset(cls) -> None:
        cls.delete()
        st.cache_data.clear()


# ------------------------------------------------------------------------------
# Plugin Session Abstract
# ------------------------------------------------------------------------------
@dataclass
class PluginSession(metaclass=ABCMeta):
    @classmethod
    def get(cls) -> Self:
        if cls.__name__ not in st.session_state:
            st.session_state[cls.__name__] = cls()
        session = st.session_state[cls.__name__]
        return session

    @classmethod
    def delete(cls) -> None:
        if cls.__name__ in st.session_state:
            if cls.__name__ in st.session_state:
                del st.session_state[cls.__name__]

    def update(self, data) -> None:
        for k, v in data.items():
            setattr(self, k, v)

    @classmethod
    def exit_plugin(cls):
        cls.delete()
        session = CommonSession.get()
        session.status = "simplechat"
        session.kwargs = {}
        session.is_selector_activate = True
        session.is_sidebar_disabled = False

    @classmethod
    def jump_to(cls, plugin_name, kwargs={}):
        session = CommonSession.get()
        session.status = plugin_name
        session.is_selector_activate = False
        session.kwargs = kwargs
        session.is_sidebar_disabled = False
