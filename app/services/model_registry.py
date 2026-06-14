import os
import json
import logging
from typing import Optional, Dict, Any
from prophet import Prophet
from prophet.serialize import model_from_json

logger = logging.getLogger(__name__)

# Path to the pre-trained Prophet model
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models", "prophet_model.json")

# In-memory cache for the loaded Prophet model
_prophet_model: Optional[Prophet] = None


def load_prophet_model() -> Optional[Prophet]:
    """
    Loads the pre-trained Prophet model from disk into memory.
    """
    global _prophet_model
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"Pre-trained Prophet model not found at: {MODEL_PATH}")
        _prophet_model = None
        return None

    try:
        logger.info(f"Loading pre-trained Prophet model from {MODEL_PATH}...")
        with open(MODEL_PATH, "r") as f:
            model_json = f.read()
            _prophet_model = model_from_json(model_json)
        logger.info("Pre-trained Prophet model loaded successfully.")
        return _prophet_model
    except Exception as e:
        logger.error(f"Failed to load pre-trained Prophet model: {str(e)}", exc_info=True)
        _prophet_model = None
        return None


def get_prophet_model() -> Optional[Prophet]:
    """
    Retrieves the cached Prophet model, loading it first if necessary.
    """
    global _prophet_model
    if _prophet_model is None:
        return load_prophet_model()
    return _prophet_model


def reload_prophet_model() -> Optional[Prophet]:
    """
    Clears the cache and reloads the Prophet model from disk.
    """
    global _prophet_model
    _prophet_model = None
    return load_prophet_model()


def get_model_info() -> Dict[str, Any]:
    """
    Returns metadata and stats of the currently loaded Prophet model.
    """
    model = get_prophet_model()
    if model is None:
        return {
            "status": "not_loaded",
            "error": f"Model file not found or failed to load at {MODEL_PATH}"
        }

    info = {
        "status": "loaded",
        "growth": getattr(model, "growth", None),
        "seasonality_mode": getattr(model, "seasonality_mode", None),
        "yearly_seasonality": getattr(model, "yearly_seasonality", None),
        "weekly_seasonality": getattr(model, "weekly_seasonality", None),
        "daily_seasonality": getattr(model, "daily_seasonality", None),
        "extra_regressors": list(model.extra_regressors.keys()) if hasattr(model, "extra_regressors") else [],
        "interval_width": getattr(model, "interval_width", None),
    }

    if hasattr(model, "history") and model.history is not None:
        info["history_points"] = len(model.history)
        if "ds" in model.history.columns:
            info["history_start"] = str(model.history["ds"].min())
            info["history_end"] = str(model.history["ds"].max())

    return info
