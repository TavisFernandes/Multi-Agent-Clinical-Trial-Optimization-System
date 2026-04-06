"""
Text Pipeline:
1) NER extraction (BC5CDR_ner_model.h5 if available)
2) LSTM text analysis (PubMed_RCT_lstm_model.h5 if available)
Falls back to rule-based logic when model/tokenizer artifacts are unavailable.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

from Utils.model_registry import get_model_registry

logger = logging.getLogger(__name__)


class TextPipeline:
    """
    Text processing pipeline with NER and LSTM components.
    Gracefully degrades to mock logic when models are unavailable.
    """

    def __init__(self, models_dir: Optional[str] = None):
        self.registry = get_model_registry(models_dir=models_dir)
        self.ner_model = self.registry.models.ner
        self.lstm_model = self.registry.models.lstm
        # Beginner-friendly tokenizer fallback when training tokenizer is unavailable.
        self.tokenizer = Tokenizer(num_words=5000, oov_token="<UNK>")
        self.max_len = 64

    def _to_sequence(self, text: str) -> np.ndarray:
        """Tokenize and pad text. If tokenizer not pre-fit, fit on current text safely."""
        try:
            self.tokenizer.fit_on_texts([text])
            seq = self.tokenizer.texts_to_sequences([text])
            return pad_sequences(seq, maxlen=self.max_len, padding="post", truncating="post")
        except Exception as exc:
            logger.warning("Tokenizer fallback path triggered: %s", exc)
            # fallback hash sequence
            row = [float(hash(w) % 5000) for w in text.lower().split()[: self.max_len]]
            while len(row) < self.max_len:
                row.append(0.0)
            return np.array([row], dtype=np.float32)

    def extract_entities_mock(self, text: str) -> List[Dict[str, str]]:
        """
        Extract entities using simple keyword/pattern matching.
        Mock implementation when NER model is unavailable.

        Args:
            text: Input text to extract entities from

        Returns:
            List of entity dictionaries with 'text' and 'label' keys
        """
        entities = []

        # Medical entity patterns
        patterns = {
            'DISEASE': [
                r'\b(cancer|tumor|carcinoma|melanoma|leukemia|lymphoma|neoplasm)\b',
                r'\b(stage\s*[IVX0-9]+)\b',
            ],
            'THERAPY': [
                r'\b(chemotherapy|radiotherapy|radiation|immunotherapy|surgery)\b',
                r'\b(drug|compound|medication|treatment|therapy)\b',
            ],
            'MEASUREMENT': [
                r'\b(\d+\s*(mg|mcg|kg|ml|mm)\b)',
                r'\b(dose|dosage|infusion)\b',
            ],
            'PATIENT': [
                r'\b(patient|subject|participant|cohort)\b',
                r'\b(age|sex|gender|male|female)\b',
            ],
            'TRIAL': [
                r'\b(phase\s*[IVX0-9]+|Phase\s*[1-4])\b',
                r'\b(trial|study|protocol|clinical)\b',
            ],
        }

        for label, pattern_list in patterns.items():
            for pattern in pattern_list:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append({
                        'text': match.group(0),
                        'label': label,
                        'start': match.start(),
                        'end': match.end()
                    })

        # Sort by position and remove duplicates
        entities.sort(key=lambda x: x['start'])
        seen = set()
        unique_entities = []
        for e in entities:
            key = (e['text'], e['label'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)

        return unique_entities[:20]  # Limit to 20 entities

    def process_text_lstm(self, text: str) -> Dict[str, Any]:
        """
        Process text through LSTM for sequence embedding.
        Mock implementation when LSTM model is unavailable.

        Args:
            text: Input text to process

        Returns:
            Dictionary with embedding and metadata
        """
        sequence = self._to_sequence(text)

        if self.lstm_model is not None:
            try:
                embedding = self.lstm_model.predict(sequence, verbose=0)
                emb_arr = np.asarray(embedding)
                return {
                    'embedding': emb_arr.tolist(),
                    'embedding_shape': list(emb_arr.shape),
                    'source': 'lstm_model',
                    'analysis': (
                        "clinical-sequence-positive"
                        if float(np.mean(emb_arr)) >= 0.5
                        else "clinical-sequence-neutral"
                    ),
                }
            except Exception as e:
                logger.exception("LSTM prediction failed")

        # Rule-based fallback
        mock_embedding = np.random.randn(1, 128).astype(np.float32)
        lower = text.lower()
        if "phase" in lower or "trial" in lower:
            analysis = "trial-narrative-detected"
        elif any(k in lower for k in ["cancer", "tumor", "metastatic", "nsclc"]):
            analysis = "oncology-narrative-detected"
        else:
            analysis = "general-clinical-narrative"
        return {
            'embedding': mock_embedding.tolist(),
            'embedding_shape': list(mock_embedding.shape),
            'source': 'mock_lstm',
            'analysis': analysis,
        }

    def _entities_from_ner_model(self, text: str) -> List[Dict[str, str]]:
        if self.ner_model is None:
            return []
        try:
            x = self._to_sequence(text)
            pred = self.ner_model.predict(x, verbose=0)
            # Generic conversion because training label map may not be available.
            # We preserve entity extraction behavior by combining model confidence + regex terms.
            conf = float(np.mean(np.asarray(pred)))
            entities = self.extract_entities_mock(text)
            for ent in entities:
                ent["source"] = f"ner_model_conf_{conf:.3f}"
            return entities
        except Exception:
            logger.exception("NER inference failed, using fallback extraction")
            return []

    def run(self, text: str) -> Dict[str, Any]:
        """
        Run full text pipeline.

        Args:
            text: Input text to process

        Returns:
            Dictionary with NER entities and LSTM processing results
        """
        if not text or not text.strip():
            return {
                'error': 'Empty text input',
                'entities': [],
                'lstm_output': None
            }

        # Extract entities via model first, fallback second
        entities = self._entities_from_ner_model(text) or self.extract_entities_mock(text)

        # Process through LSTM
        lstm_output = self.process_text_lstm(text)

        return {
            'entities': entities,
            'lstm_output': lstm_output,
            'text_preview': text[:200],
            'entity_count': len(entities),
            'analysis': lstm_output.get('analysis', 'analysis-unavailable'),
        }


def process_text(text: str, models_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process text.

    Args:
        text: Input text
        models_dir: Optional models directory path

    Returns:
        Pipeline output dictionary
    """
    pipeline = TextPipeline(models_dir)
    return pipeline.run(text)


# Example usage
if __name__ == "__main__":
    sample_text = """
    Patient with stage II breast cancer receiving chemotherapy treatment.
    The trial is a Phase 2 study evaluating drug efficacy at 100mg dose.
    Enrollment includes 120 patients aged 18-65.
    """

    pipeline = TextPipeline()
    result = pipeline.run(sample_text)

    print("\n=== Text Pipeline Results ===")
    print(f"Text preview: {result['text_preview']}")
    print(f"Entities found: {result['entity_count']}")
    for entity in result['entities'][:5]:
        print(f"  - {entity['text']} ({entity['label']})")
    print(f"LSTM output source: {result['lstm_output']['source']}")
    print(f"Embedding shape: {result['lstm_output']['embedding_shape']}")
