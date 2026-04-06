"""
Utils Package
Utility functions for preprocessing, evaluation, and visualization.
"""

from .preprocessing import (
    clean_text,
    normalize_text,
    extract_numbers,
    extract_measurements,
    tokenize_text,
    preprocess_image,
    one_hot_encode,
    pad_sequence,
    batch_generator
)
from .evaluation import (
    accuracy,
    precision_recall_f1,
    confusion_matrix,
    mean_squared_error,
    mean_absolute_error,
    evaluate_report_quality,
    entity_extraction_metrics
)
from .visualization import (
    plot_confusion_matrix,
    plot_training_history,
    plot_entity_distribution,
    plot_prediction_probs,
    create_ascii_bar_chart
)
from .model_registry import ModelRegistry, get_model_registry

__all__ = [
    # Preprocessing
    'clean_text',
    'normalize_text',
    'extract_numbers',
    'extract_measurements',
    'tokenize_text',
    'preprocess_image',
    'one_hot_encode',
    'pad_sequence',
    'batch_generator',
    # Evaluation
    'accuracy',
    'precision_recall_f1',
    'confusion_matrix',
    'mean_squared_error',
    'mean_absolute_error',
    'evaluate_report_quality',
    'entity_extraction_metrics',
    # Visualization
    'plot_confusion_matrix',
    'plot_training_history',
    'plot_entity_distribution',
    'plot_prediction_probs',
    'create_ascii_bar_chart',
    'ModelRegistry',
    'get_model_registry'
]
