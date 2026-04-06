"""
Task Classifier Module
Detects if input is text or image and routes to appropriate pipeline.
"""

import numpy as np
from typing import Any, Tuple, Union


class TaskClassifier:
    """
    Simple task classifier that detects input type and routes accordingly.
    """

    def classify(self, data: Any) -> str:
        """
        Classify input type and return route name.

        Args:
            data: Input data to classify

        Returns:
            str: Route type ('text', 'image', or 'unknown')
        """
        if isinstance(data, str) and len(data.strip()) > 0:
            return 'text'
        elif isinstance(data, (np.ndarray, list)):
            # Check if it looks like image data (numeric array)
            try:
                arr = np.asarray(data)
                if np.issubdtype(arr.dtype, np.number):
                    return 'image'
            except (ValueError, TypeError):
                pass
            return 'image'
        else:
            return 'unknown'

    def route(self, data: Any) -> Tuple[str, Any]:
        """
        Classify and return route with processed data.

        Args:
            data: Input data to classify

        Returns:
            Tuple of (route_type, processed_data)
        """
        route_type = self.classify(data)

        if route_type == 'text':
            return route_type, str(data).strip()
        elif route_type == 'image':
            return route_type, np.asarray(data)
        else:
            return route_type, data


def detect_input_type(data: Any) -> str:
    """
    Quick helper function to detect input type.

    Args:
        data: Input data

    Returns:
        str: Input type ('text', 'image', or 'unknown')
    """
    classifier = TaskClassifier()
    return classifier.classify(data)


# Example usage
if __name__ == "__main__":
    classifier = TaskClassifier()

    # Test text input
    text_input = "Patient with stage II cancer receiving treatment"
    print(f"Text input route: {classifier.classify(text_input)}")

    # Test image input (2D array)
    image_input = [[0.1, 0.2], [0.3, 0.4]]
    print(f"Image input route: {classifier.classify(image_input)}")

    # Test flattened image
    flat_image = [0.1, 0.2, 0.3, 0.4]
    print(f"Flat image route: {classifier.classify(flat_image)}")

    # Test unknown
    unknown_input = {"key": "value"}
    print(f"Dict input route: {classifier.classify(unknown_input)}")
