"""
Evaluation Utilities Module
Simple evaluation metrics and placeholders.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple


def accuracy(y_true: List[int], y_pred: List[int]) -> float:
    """
    Calculate classification accuracy.

    Args:
        y_true: True labels
        y_pred: Predicted labels

    Returns:
        Accuracy score (0-1)
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")

    if len(y_true) == 0:
        return 0.0

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)


def precision_recall_f1(
    y_true: List[int],
    y_pred: List[int],
    average: str = 'macro'
) -> Dict[str, float]:
    """
    Calculate precision, recall, and F1 score.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        average: 'macro', 'micro', or 'weighted'

    Returns:
        Dictionary with precision, recall, f1 scores
    """
    classes = set(y_true) | set(y_pred)

    precisions = []
    recalls = []

    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)

    # Calculate F1 for each class
    f1s = []
    for p, r in zip(precisions, recalls):
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
        f1s.append(f1)

    if average == 'macro':
        return {
            'precision': np.mean(precisions),
            'recall': np.mean(recalls),
            'f1': np.mean(f1s)
        }
    elif average == 'micro':
        total_tp = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        total_fp = sum(1 for t, p in zip(y_true, y_pred) if t != p)
        total_fn = total_fp
        p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0
        return {'precision': p, 'recall': r, 'f1': f1}
    else:  # weighted
        weights = [sum(1 for t in y_true if t == c) for c in classes]
        total = sum(weights)
        if total == 0:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        weights = [w / total for w in weights]
        return {
            'precision': sum(p * w for p, w in zip(precisions, weights)),
            'recall': sum(r * w for r, w in zip(recalls, weights)),
            'f1': sum(f * w for f, w in zip(f1s, weights))
        }


def confusion_matrix(
    y_true: List[int],
    y_pred: List[int],
    labels: Optional[List[int]] = None
) -> np.ndarray:
    """
    Compute confusion matrix.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        labels: Optional list of labels

    Returns:
        Confusion matrix array
    """
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))

    n_classes = len(labels)
    label_to_idx = {label: idx for idx, label in enumerate(labels)}

    matrix = np.zeros((n_classes, n_classes), dtype=int)

    for t, p in zip(y_true, y_pred):
        if t in label_to_idx and p in label_to_idx:
            matrix[label_to_idx[t], label_to_idx[p]] += 1

    return matrix


def mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
    """
    Calculate Mean Squared Error.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        MSE value
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")

    if len(y_true) == 0:
        return 0.0

    errors = [(t - p) ** 2 for t, p in zip(y_true, y_pred)]
    return sum(errors) / len(errors)


def mean_absolute_error(y_true: List[float], y_pred: List[float]) -> float:
    """
    Calculate Mean Absolute Error.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        MAE value
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")

    if len(y_true) == 0:
        return 0.0

    errors = [abs(t - p) for t, p in zip(y_true, y_pred)]
    return sum(errors) / len(errors)


def evaluate_report_quality(
    report: str,
    required_sections: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluate generated report quality.

    Args:
        report: Generated report text
        required_sections: List of required section names

    Returns:
        Dictionary with quality metrics
    """
    metrics = {
        'length': len(report),
        'word_count': len(report.split()),
        'has_headers': False,
        'sections_found': [],
        'sections_missing': [],
        'quality_score': 0.0
    }

    # Check for markdown headers
    import re
    headers = re.findall(r'^#+\s+(.+)$', report, re.MULTILINE)
    metrics['has_headers'] = len(headers) > 0
    metrics['header_count'] = len(headers)

    # Check for required sections
    if required_sections:
        report_lower = report.lower()
        for section in required_sections:
            if section.lower() in report_lower:
                metrics['sections_found'].append(section)
            else:
                metrics['sections_missing'].append(section)

    # Calculate quality score
    score = 0.0

    # Length score (max 25 points)
    if metrics['length'] >= 500:
        score += 25
    elif metrics['length'] >= 200:
        score += 15
    elif metrics['length'] >= 100:
        score += 5

    # Headers score (max 25 points)
    if metrics['has_headers']:
        score += min(25, metrics['header_count'] * 5)

    # Sections score (max 50 points)
    if required_sections:
        total_sections = len(required_sections)
        found_sections = len(metrics['sections_found'])
        score += (found_sections / total_sections) * 50
    else:
        score += 25  # Default if no sections specified

    metrics['quality_score'] = round(score, 2)

    return metrics


def entity_extraction_metrics(
    predicted_entities: List[Dict[str, str]],
    true_entities: List[Dict[str, str]],
    match_key: str = 'text'
) -> Dict[str, float]:
    """
    Calculate metrics for entity extraction.

    Args:
        predicted_entities: List of predicted entities
        true_entities: List of true entities
        match_key: Key to use for matching ('text' or 'label')

    Returns:
        Dictionary with precision, recall, f1
    """
    pred_set = set(e.get(match_key, '') for e in predicted_entities)
    true_set = set(e.get(match_key, '') for e in true_entities)

    # Filter empty strings
    pred_set = {p for p in pred_set if p}
    true_set = {t for t in true_set if t}

    tp = len(pred_set & true_set)
    fp = len(pred_set - true_set)
    fn = len(true_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn
    }


# Example usage
if __name__ == "__main__":
    print("=== Evaluation Utilities Test ===")

    # Classification metrics
    y_true = [0, 1, 2, 0, 1, 2]
    y_pred = [0, 1, 1, 0, 2, 2]

    print(f"Accuracy: {accuracy(y_true, y_pred):.3f}")

    prf = precision_recall_f1(y_true, y_pred, average='macro')
    print(f"Precision: {prf['precision']:.3f}")
    print(f"Recall: {prf['recall']:.3f}")
    print(f"F1: {prf['f1']:.3f}")

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion matrix:\n{cm}")

    # Regression metrics
    y_true_reg = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_pred_reg = [1.1, 1.9, 3.2, 3.8, 5.1]

    print(f"MSE: {mean_squared_error(y_true_reg, y_pred_reg):.4f}")
    print(f"MAE: {mean_absolute_error(y_true_reg, y_pred_reg):.4f}")

    # Report quality
    sample_report = """
    # Clinical Summary
    ## Introduction
    Patient data analysis.
    ## Results
    Findings presented.
    """
    quality = evaluate_report_quality(sample_report, required_sections=['Introduction', 'Results'])
    print(f"Report quality score: {quality['quality_score']}")

    # Entity metrics
    pred_entities = [{'text': 'cancer', 'label': 'DISEASE'}, {'text': 'drug', 'label': 'THERAPY'}]
    true_entities = [{'text': 'cancer', 'label': 'DISEASE'}, {'text': 'tumor', 'label': 'DISEASE'}]
    entity_metrics = entity_extraction_metrics(pred_entities, true_entities)
    print(f"Entity extraction F1: {entity_metrics['f1']:.3f}")
