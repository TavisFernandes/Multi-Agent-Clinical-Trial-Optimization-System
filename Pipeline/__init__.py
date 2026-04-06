"""
Pipeline Package
Task classification and processing pipelines.
"""

from .task_classifier import TaskClassifier, detect_input_type
from .text_pipeline import TextPipeline, process_text
from .image_pipeline import ImagePipeline, process_image
from .main_pipeline import MainPipeline, run_pipeline, PipelineResult

__all__ = [
    'TaskClassifier',
    'detect_input_type',
    'TextPipeline',
    'process_text',
    'ImagePipeline',
    'process_image',
    'MainPipeline',
    'run_pipeline',
    'PipelineResult'
]
