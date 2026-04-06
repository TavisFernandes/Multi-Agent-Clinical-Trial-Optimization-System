"""
Central model loading and inference utilities.
Loads models once from /models and provides safe prediction helpers.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
from tensorflow.keras.models import load_model

logger = logging.getLogger(__name__)


@dataclass
class LoadedModels:
    ner: Any = None
    lstm: Any = None
    survival: Any = None
    cnn: Any = None
    resnet: Any = None


class ModelRegistry:
    """Shared registry that loads all known models once."""

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = Path(models_dir or os.environ.get("MODELS_DIR", "/models"))
        self.models = LoadedModels()
        self.load_errors: dict[str, str] = {}
        self.loaded = False

    def _load_single(self, name: str, filename: str) -> Any:
        path = self.models_dir / filename
        if not path.exists():
            self.load_errors[name] = f"missing: {path}"
            logger.warning("Model %s not found at %s", name, path)
            return None
        try:
            model = load_model(str(path))
            logger.info("Loaded %s model from %s", name, path)
            return model
        except Exception as exc:
            self.load_errors[name] = str(exc)
            logger.exception("Failed loading %s model from %s", name, path)
            return None

    def load_all(self) -> None:
        if self.loaded:
            return
        logger.info("Loading models from %s", self.models_dir)
        self.models.ner = self._load_single("ner", "BC5CDR_ner_model.h5")
        self.models.lstm = self._load_single("lstm", "PubMed_RCT_lstm_model.h5")
        self.models.survival = self._load_single(
            "survival", "clinical_survival_model.h5"
        )
        # Optional image models (best effort)
        self.models.cnn = self._load_single("cnn", "cnn_model.h5")
        self.models.resnet = self._load_single("resnet", "resnet_model.h5")
        self.loaded = True

    def any_loaded(self) -> bool:
        m = self.models
        return any([m.ner, m.lstm, m.survival, m.cnn, m.resnet])

    @staticmethod
    def safe_predict(model: Any, data: Any, model_name: str) -> tuple[Optional[Any], str]:
        if model is None:
            return None, f"{model_name} unavailable"
        try:
            out = model.predict(data, verbose=0)
            return out, ""
        except Exception as exc:
            logger.exception("Inference failed for %s", model_name)
            return None, f"{model_name} inference failed: {exc}"


_REGISTRY: Optional[ModelRegistry] = None


def get_model_registry(models_dir: Optional[str] = None) -> ModelRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ModelRegistry(models_dir=models_dir)
        _REGISTRY.load_all()
    return _REGISTRY
