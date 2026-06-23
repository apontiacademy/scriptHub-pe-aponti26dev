"""Módulo de automação de extração e processamento."""

MENU_CMD = ("relatorios", "auditar")

from .main import ESCOPOS, get_config

__all__ = ["get_config", "ESCOPOS"]
