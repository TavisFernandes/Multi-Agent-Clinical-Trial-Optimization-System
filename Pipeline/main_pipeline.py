"""
Main Pipeline Module
Integrates task classifier, text/image pipelines, and agent system.
Provides unified interface for processing user input.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
import numpy as np

from .task_classifier import TaskClassifier
from .text_pipeline import TextPipeline
from .image_pipeline import ImagePipeline
from Utils.model_registry import get_model_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Container for pipeline execution results."""
    route: str
    model_outputs: Dict[str, Any] = field(default_factory=dict)
    ner_entities: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_input_preview: str = ""
    image_predictions: Optional[Dict[str, Any]] = None
    analysis: str = ""
    survival_prediction: Optional[Dict[str, Any]] = None


class MainPipeline:
    """
    Main pipeline orchestrator that:
    1. Classifies input type (text/image)
    2. Routes to appropriate processing pipeline
    3. Returns structured results for agent system
    """

    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize main pipeline.

        Args:
            models_dir: Optional path to models directory
        """
        self.classifier = TaskClassifier()
        self.text_pipeline = TextPipeline(models_dir)
        self.image_pipeline = ImagePipeline(models_dir)
        self.models_dir = models_dir
        self.registry = get_model_registry(models_dir=models_dir)

    def _predict_survival(self, entity_count: int, analysis_signal: float) -> Dict[str, Any]:
        model = self.registry.models.survival
        # Build features with dynamic width expected by trained survival model.
        width = 2
        if model is not None:
            try:
                ishape = getattr(model, "input_shape", None)
                if isinstance(ishape, tuple) and len(ishape) >= 2 and ishape[-1]:
                    width = int(ishape[-1])
            except Exception:
                width = 2
        x = np.zeros((1, max(2, width)), dtype=np.float32)
        x[0, 0] = float(entity_count)
        x[0, 1] = float(analysis_signal)
        if model is not None:
            pred, err = self.registry.safe_predict(model, x, "survival_model")
            if err:
                return {"source": "fallback", "error": err, "prediction": 0}
            p = np.asarray(pred).reshape(-1)
            score = float(p[0]) if p.size else 0.0
            return {
                "source": "clinical_survival_model.h5",
                "prediction": int(score >= 0.5),
                "score": score,
            }
        # Rule fallback
        score = max(0.0, min(1.0, 0.65 - entity_count * 0.02 + analysis_signal * 0.1))
        return {"source": "rule_fallback", "prediction": int(score >= 0.5), "score": score}

    def run(
        self,
        user_input: Union[str, List, Any],
        log_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> PipelineResult:
        """
        Run complete pipeline on user input.

        Args:
            user_input: Text string or image array
            log_callback: Optional callback for logging events

        Returns:
            PipelineResult with processed outputs
        """
        # Classify input
        input_type = self.classifier.classify(user_input)

        if log_callback:
            log_callback({
                'type': 'classification',
                'input_type': input_type,
                'message': f'Input classified as: {input_type}'
            })

        logger.info(f"Processing {input_type} input")

        if input_type == 'text':
            return self._run_text_pipeline(str(user_input), log_callback)
        elif input_type == 'image':
            return self._run_image_pipeline(user_input, log_callback)
        else:
            return PipelineResult(
                route='unknown',
                warnings=[f'Unsupported input type: {type(user_input).__name__}']
            )

    def _run_text_pipeline(
        self,
        text: str,
        log_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> PipelineResult:
        """Run text processing pipeline."""
        if log_callback:
            log_callback({
                'type': 'pipeline_start',
                'pipeline': 'text',
                'message': 'Starting text pipeline (NER + LSTM)'
            })

        # Run text pipeline
        text_result = self.text_pipeline.run(text)

        # Extract results
        entities = text_result.get('entities', [])
        lstm_output = text_result.get('lstm_output', {})

        if log_callback:
            log_callback({
                'type': 'pipeline_complete',
                'pipeline': 'text',
                'entities_found': len(entities),
                'message': f'Extracted {len(entities)} entities'
            })

        analysis = lstm_output.get("analysis", "analysis-unavailable")
        emb_shape = lstm_output.get("embedding_shape", [])
        analysis_signal = 0.5 if emb_shape else 0.3
        survival = self._predict_survival(len(entities), analysis_signal)

        return PipelineResult(
            route='text',
            model_outputs={
                'lstm_source': lstm_output.get('source', 'unknown'),
                'embedding_shape': emb_shape,
                'survival_source': survival.get("source"),
            },
            ner_entities=entities,
            raw_input_preview=text[:500],
            analysis=analysis,
            survival_prediction=survival,
        )

    def _run_image_pipeline(
        self,
        image_data: Union[List, Any],
        log_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> PipelineResult:
        """Run image processing pipeline."""
        if log_callback:
            log_callback({
                'type': 'pipeline_start',
                'pipeline': 'image',
                'message': 'Starting image pipeline (CNN/ResNet)'
            })

        # Run image pipeline
        image_result = self.image_pipeline.run(image_data)

        # Extract results
        predictions = {}
        if 'error' not in image_result:
            predictions = {
                'predicted_class': image_result.get('predicted_class'),
                'confidence': image_result.get('confidence'),
                'source': image_result.get('source')
            }

        if log_callback:
            log_callback({
                'type': 'pipeline_complete',
                'pipeline': 'image',
                'prediction': image_result.get('predicted_class'),
                'message': f'Classification: {image_result.get("predicted_class")}'
            })

        survival = self._predict_survival(0, 0.5)
        analysis = (
            f"image-classification:{predictions.get('predicted_class', 'unknown')}"
            if predictions
            else "image-analysis-unavailable"
        )
        return PipelineResult(
            route='image',
            model_outputs={
                'input_shape': image_result.get('input_shape'),
                'predictions': predictions,
                'survival_source': survival.get("source"),
            },
            image_predictions=predictions,
            raw_input_preview=f"array_shape={image_result.get('input_shape')}",
            analysis=analysis,
            survival_prediction=survival,
        )


def run_pipeline(
    user_input: Union[str, List],
    models_dir: Optional[str] = None,
    log_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> PipelineResult:
    """
    Convenience function to run the main pipeline.

    Args:
        user_input: Text or image input
        models_dir: Optional models directory
        log_callback: Optional logging callback

    Returns:
        PipelineResult with processed outputs
    """
    pipeline = MainPipeline(models_dir)
    return pipeline.run(user_input, log_callback)


# Example usage and demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("MULTI-AGENT CLINICAL TRIAL OPTIMIZATION SYSTEM")
    print("Pipeline Demonstration")
    print("=" * 60)

    # Initialize pipeline
    pipeline = MainPipeline()

    # Text Examples (required demo inputs)
    print("\n--- Test 1: Text Input ---")
    sample_text = "Patient with stage III lung cancer treated with chemotherapy"

    result = pipeline.run(sample_text)
    print(f"Route: {result.route}")
    print(f"Entities found: {len(result.ner_entities)}")
    for entity in result.ner_entities[:5]:
        print(f"  - {entity['text']} ({entity['label']})")
    print(f"Model outputs: {result.model_outputs}")
    print(f"Analysis: {result.analysis}")
    print(f"Survival prediction: {result.survival_prediction}")

    print("\n--- Test 2: Text Input ---")
    sample_text_2 = "EGFR mutation positive NSCLC treated with gefitinib"
    result = pipeline.run(sample_text_2)
    print(f"Route: {result.route}")
    print(f"Entities found: {len(result.ner_entities)}")
    print(f"Analysis: {result.analysis}")
    print(f"Survival prediction: {result.survival_prediction}")

    # Image Example (dummy placeholder)
    print("\n--- Test 3: Image Input ---")
    import numpy as np
    sample_image = np.random.rand(28, 28).astype(np.float32)

    result = pipeline.run(sample_image)
    print(f"Route: {result.route}")
    print(f"Input shape: {result.model_outputs.get('input_shape')}")
    print(f"Predictions: {result.image_predictions}")

    print(f"Survival prediction: {result.survival_prediction}")

    print("\n--- Test 4: Flattened Image (784 elements) ---")
    flat_image = np.random.rand(784).astype(np.float32)
    result = pipeline.run(flat_image)
    print(f"Route: {result.route}")
    print(f"Input shape: {result.model_outputs.get('input_shape')}")
    print(f"Prediction: {result.image_predictions}")

    print("\n" + "=" * 60)
    print("Pipeline demonstration complete!")
    print("=" * 60)
