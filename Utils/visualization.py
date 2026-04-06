"""
Visualization Utilities Module
Simple plotting functions for data and results visualization.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple


def plot_confusion_matrix(
    matrix: np.ndarray,
    class_names: Optional[List[str]] = None,
    title: str = 'Confusion Matrix',
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate confusion matrix visualization data.

    Note: Actual plotting requires matplotlib. This function returns
    data that can be used for plotting.

    Args:
        matrix: Confusion matrix array
        class_names: Optional list of class names
        title: Plot title
        save_path: Optional path to save figure

    Returns:
        Dictionary with plot data and metadata
    """
    result = {
        'matrix': matrix.tolist(),
        'title': title,
        'class_names': class_names,
        'shape': matrix.shape,
        'can_plot': False,
        'message': 'Matplotlib not available'
    }

    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(matrix, interpolation='nearest', cmap=plt.cm.Blues)
        ax.figure.colorbar(im, ax=ax)

        ax.set(title=title, ylabel='True label', xlabel='Predicted label')

        if class_names:
            ax.set_xticks(np.arange(len(class_names)))
            ax.set_yticks(np.arange(len(class_names)))
            ax.set_xticklabels(class_names)
            ax.set_yticklabels(class_names)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        # Add text annotations
        thresh = matrix.max() / 2.0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, format(matrix[i, j], 'd'),
                       ha='center', va='center',
                       color='white' if matrix[i, j] > thresh else 'black')

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        result['can_plot'] = True
        result['message'] = 'Plot generated successfully'
        plt.close(fig)

    except ImportError:
        result['message'] = 'Matplotlib not available - returning data only'

    return result


def plot_training_history(
    history: Dict[str, List[float]],
    metrics: Optional[List[str]] = None,
    title: str = 'Training History',
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate training history visualization.

    Args:
        history: Dictionary with metric lists (e.g., {'loss': [...], 'accuracy': [...]})
        metrics: Optional list of metrics to plot
        title: Plot title
        save_path: Optional path to save figure

    Returns:
        Dictionary with plot data
    """
    result = {
        'history': history,
        'title': title,
        'can_plot': False,
        'message': 'Matplotlib not available'
    }

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        if metrics is None:
            metrics = list(history.keys())

        n_metrics = len(metrics)
        fig, axes = plt.subplots(1, n_metrics, figsize=(6 * n_metrics, 5))

        if n_metrics == 1:
            axes = [axes]

        for ax, metric in zip(axes, metrics):
            if metric in history:
                values = history[metric]
                epochs = range(1, len(values) + 1)
                ax.plot(epochs, values, 'b-', label=metric)
                ax.set_xlabel('Epoch')
                ax.set_ylabel(metric)
                ax.set_title(f'{metric} over Epochs')
                ax.legend()
                ax.grid(True, alpha=0.3)

        fig.suptitle(title, fontsize=14)
        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        result['can_plot'] = True
        result['message'] = 'Plot generated successfully'
        plt.close(fig)

    except ImportError:
        result['message'] = 'Matplotlib not available - returning data only'

    return result


def plot_entity_distribution(
    entities: List[Dict[str, str]],
    label_key: str = 'label',
    top_n: int = 10,
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate entity distribution visualization.

    Args:
        entities: List of entity dictionaries
        label_key: Key to group by
        top_n: Number of top categories to show
        save_path: Optional path to save figure

    Returns:
        Dictionary with plot data
    """
    # Count entities by label
    label_counts: Dict[str, int] = {}
    for entity in entities:
        label = entity.get(label_key, 'unknown')
        label_counts[label] = label_counts.get(label, 0) + 1

    # Sort and get top_n
    sorted_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
    top_labels = sorted_labels[:top_n]

    labels = [item[0] for item in top_labels]
    counts = [item[1] for item in top_labels]

    result = {
        'labels': labels,
        'counts': counts,
        'total_entities': len(entities),
        'can_plot': False,
        'message': 'Matplotlib not available'
    }

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        bars = ax.bar(range(len(labels)), counts, color=colors)

        ax.set_xlabel('Entity Type')
        ax.set_ylabel('Count')
        ax.set_title(f'Top {top_n} Entity Types')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')

        # Add value labels on bars
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                   str(count), ha='center', va='bottom', fontsize=9)

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        result['can_plot'] = True
        result['message'] = 'Plot generated successfully'
        plt.close(fig)

    except ImportError:
        result['message'] = 'Matplotlib not available - returning data only'

    return result


def plot_prediction_probs(
    probabilities: Dict[str, float],
    title: str = 'Prediction Probabilities',
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate prediction probability bar chart.

    Args:
        probabilities: Dictionary mapping class names to probabilities
        title: Plot title
        save_path: Optional path to save figure

    Returns:
        Dictionary with plot data
    """
    labels = list(probabilities.keys())
    probs = list(probabilities.values())

    result = {
        'labels': labels,
        'probabilities': probs,
        'predicted_class': labels[np.argmax(probs)] if probs else None,
        'can_plot': False,
        'message': 'Matplotlib not available'
    }

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 5))

        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(labels)))
        bars = ax.bar(range(len(labels)), probs, color=colors)

        ax.set_xlabel('Class')
        ax.set_ylabel('Probability')
        ax.set_title(title)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_ylim(0, 1.1)

        # Add value labels
        for bar, prob in zip(bars, probs):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                   f'{prob:.2%}', ha='center', va='bottom', fontsize=10)

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        result['can_plot'] = True
        result['message'] = 'Plot generated successfully'
        plt.close(fig)

    except ImportError:
        result['message'] = 'Matplotlib not available - returning data only'

    return result


def create_ascii_bar_chart(
    data: Dict[str, float],
    width: int = 50,
    title: str = ''
) -> str:
    """
    Create ASCII bar chart for terminal display.

    Args:
        data: Dictionary mapping labels to values
        width: Maximum bar width
        title: Optional title

    Returns:
        ASCII bar chart string
    """
    if not data:
        return "No data to display"

    max_value = max(data.values())
    lines = []

    if title:
        lines.append(f"=== {title} ===")
        lines.append("")

    for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
        bar_length = int((value / max_value) * width) if max_value > 0 else 0
        bar = '#' * bar_length + '-' * (width - bar_length)
        lines.append(f"{label:15} |{bar}| {value:.4f}")

    return '\n'.join(lines)


# Example usage
if __name__ == "__main__":
    print("=== Visualization Utilities Test ===")

    # Test ASCII bar chart
    sample_probs = {
        'normal': 0.15,
        'benign': 0.45,
        'malignant': 0.35,
        'uncertain': 0.05
    }

    ascii_chart = create_ascii_bar_chart(sample_probs, title='Prediction Probabilities')
    print(ascii_chart)

    # Test confusion matrix data
    cm = np.array([[50, 5, 2],
                   [3, 45, 7],
                   [1, 4, 38]])
    cm_result = plot_confusion_matrix(cm, class_names=['A', 'B', 'C'])
    print(f"\nConfusion matrix data: {cm_result['message']}")

    # Test entity distribution
    entities = [
        {'text': 'cancer', 'label': 'DISEASE'},
        {'text': 'tumor', 'label': 'DISEASE'},
        {'text': 'drug', 'label': 'THERAPY'},
        {'text': 'dose', 'label': 'MEASUREMENT'},
        {'text': 'patient', 'label': 'PATIENT'},
    ] * 3
    entity_result = plot_entity_distribution(entities)
    print(f"Entity distribution: {entity_result['labels']}")

    # Test prediction probs
    prob_result = plot_prediction_probs(sample_probs)
    print(f"Predicted class: {prob_result['predicted_class']}")
