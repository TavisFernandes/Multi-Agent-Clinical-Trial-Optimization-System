"""
Image Pipeline:
- Uses /models CNN or ResNet (loaded once via model registry)
- Falls back to heuristic simulation when model missing/fails
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union

from Utils.model_registry import get_model_registry


class ImagePipeline:
    """
    Image processing pipeline for clinical image classification.
    Gracefully degrades to mock predictions when models are unavailable.
    """

    # Class labels for clinical image classification
    DEFAULT_CLASSES = [
        'normal',
        'benign',
        'malignant',
        'uncertain'
    ]

    def __init__(self, models_dir: Optional[str] = None):
        self.registry = get_model_registry(models_dir=models_dir)
        self.cnn_model = self.registry.models.cnn
        self.resnet_model = self.registry.models.resnet
        self.model_classes = self.DEFAULT_CLASSES.copy()

    def preprocess_image(
        self,
        image_data: Union[np.ndarray, List]
    ) -> Tuple[Optional[np.ndarray], Optional[str]]:
        """
        Preprocess image data for model input.

        Args:
            image_data: Raw image data (array or list)

        Returns:
            Tuple of (preprocessed_array, error_message)
        """
        try:
            arr = np.asarray(image_data, dtype=np.float32)

            # Handle 1D flattened input
            if arr.ndim == 1:
                side = int(np.sqrt(arr.size))
                if side * side == arr.size:
                    arr = arr.reshape(1, side, side, 1)
                else:
                    # Try common sizes
                    if arr.size == 784:  # MNIST size
                        arr = arr.reshape(1, 28, 28, 1)
                    elif arr.size == 1024:
                        arr = arr.reshape(1, 32, 32, 1)
                    else:
                        return None, f"Cannot reshape 1D array of size {arr.size}"

            # Handle 2D input (single grayscale image)
            elif arr.ndim == 2:
                arr = arr.reshape(1, *arr.shape, 1)

            # Handle 3D input (add batch dimension)
            elif arr.ndim == 3:
                arr = np.expand_dims(arr, 0)

            # 4D is already batched
            elif arr.ndim == 4:
                pass

            else:
                return None, f"Unsupported array dimensions: {arr.ndim}"

            # Normalize if values appear to be in 0-255 range
            if arr.max() > 1.5:
                arr = arr / 255.0

            return arr, None

        except Exception as e:
            return None, f"Preprocessing error: {e}"

    def predict_mock(
        self,
        image_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Generate mock prediction when model is unavailable.

        Args:
            image_data: Preprocessed image array

        Returns:
            Dictionary with mock prediction results
        """
        batch_size = image_data.shape[0]
        num_classes = len(self.model_classes)

        # Generate pseudo-realistic predictions
        # Use image statistics to influence predictions
        img_mean = float(np.mean(image_data))
        img_std = float(np.std(image_data))

        # Create probability distribution influenced by image stats
        probs = np.ones((batch_size, num_classes), dtype=np.float32)

        # Simple heuristic: higher mean -> more likely benign
        if img_mean > 0.5:
            probs[0, 1] = 0.6  # benign
        else:
            probs[0, 0] = 0.5  # normal

        # Higher std -> more uncertainty
        if img_std > 0.3:
            probs[0, 3] = 0.3  # uncertain

        # Normalize to probabilities
        probs = probs / probs.sum(axis=1, keepdims=True)

        # Get top prediction
        top_idx = int(np.argmax(probs[0]))
        top_prob = float(probs[0, top_idx])

        return {
            'predictions': probs.tolist(),
            'predicted_class': self.model_classes[top_idx],
            'predicted_class_index': top_idx,
            'confidence': top_prob,
            'all_probabilities': dict(zip(self.model_classes, probs[0].tolist())),
            'source': 'mock_prediction'
        }

    def run(self, image_data: Union[np.ndarray, List]) -> Dict[str, Any]:
        """
        Run full image pipeline.

        Args:
            image_data: Raw image data

        Returns:
            Dictionary with prediction results
        """
        # Preprocess
        preprocessed, error = self.preprocess_image(image_data)
        if error:
            return {
                'error': error,
                'predictions': None
            }

        result = {
            'input_shape': list(preprocessed.shape),
        }

        # Use ResNet first, fallback to CNN
        model = self.resnet_model if self.resnet_model is not None else self.cnn_model
        model_name = "resnet_model" if self.resnet_model is not None else "cnn_model"
        if model is not None:
            try:
                predictions = model.predict(preprocessed, verbose=0)

                # Handle different output shapes
                if predictions.ndim == 1:
                    predictions = predictions.reshape(1, -1)

                top_idx = int(np.argmax(predictions[0]))
                num_classes = predictions.shape[-1]
                classes = self.model_classes[:num_classes]

                result.update({
                    'predictions': predictions.tolist(),
                    'predicted_class': classes[top_idx] if top_idx < len(classes) else f"class_{top_idx}",
                    'predicted_class_index': top_idx,
                    'confidence': float(predictions[0, top_idx]),
                    'all_probabilities': dict(zip(classes, predictions[0].tolist())),
                    'source': model_name
                })

            except Exception as e:
                print(f"{model_name} prediction failed: {e}")
                # Fall back to mock
                mock_result = self.predict_mock(preprocessed)
                mock_result['source'] = 'mock_fallback'
                result.update(mock_result)
        else:
            # Use mock prediction
            mock_result = self.predict_mock(preprocessed)
            result.update(mock_result)

        return result


def process_image(
    image_data: Union[np.ndarray, List],
    models_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to process image.

    Args:
        image_data: Image data array
        models_dir: Optional models directory

    Returns:
        Pipeline output dictionary
    """
    pipeline = ImagePipeline(models_dir)
    return pipeline.run(image_data)


# Example usage
if __name__ == "__main__":
    print("=== Image Pipeline Test ===")

    # Test with random image data
    test_image = np.random.rand(28, 28).astype(np.float32)

    pipeline = ImagePipeline()
    result = pipeline.run(test_image)

    print(f"Input shape: {result.get('input_shape')}")
    if 'error' not in result:
        print(f"Predicted class: {result.get('predicted_class')}")
        print(f"Confidence: {result.get('confidence', 0):.2%}")
        print(f"Source: {result.get('source')}")
        print(f"All probabilities:")
        for cls, prob in result.get('all_probabilities', {}).items():
            print(f"  {cls}: {prob:.2%}")

    # Test with flattened input
    print("\n=== Testing Flattened Input ===")
    flat_image = np.random.rand(784).astype(np.float32)
    result2 = pipeline.run(flat_image)
    print(f"Input shape: {result2.get('input_shape')}")
    print(f"Predicted class: {result2.get('predicted_class')}")
