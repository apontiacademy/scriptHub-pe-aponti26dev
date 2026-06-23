"""Módulo de automação de exportação de frequências do Moodle."""

MENU_CMD = ("frequencias",)

from .main import ESCOPOS, get_config

__all__ = ["get_config", "ESCOPOS"]
