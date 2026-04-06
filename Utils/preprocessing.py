"""
Preprocessing Utilities Module
Basic text and image cleaning functions.
"""

import re
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters.

    Args:
        text: Raw text input

    Returns:
        Cleaned text string
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def normalize_text(text: str, lowercase: bool = True) -> str:
    """
    Normalize text for processing.

    Args:
        text: Input text
        lowercase: Whether to convert to lowercase

    Returns:
        Normalized text
    """
    cleaned = clean_text(text)
    if lowercase:
        cleaned = cleaned.lower()
    return cleaned


def extract_numbers(text: str) -> List[float]:
    """
    Extract numeric values from text.

    Args:
        text: Input text

    Returns:
        List of extracted numbers
    """
    # Match integers and decimals
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches if m]


def extract_measurements(text: str) -> List[Dict[str, str]]:
    """
    Extract measurements with units from text.

    Args:
        text: Input text

    Returns:
        List of dictionaries with 'value' and 'unit' keys
    """
    pattern = r'(\d+\.?\d*)\s*(mg|mcg|kg|ml|mm|cm|hz|khz|mhz)'
    matches = re.findall(pattern, text, re.IGNORECASE)

    return [
        {'value': match[0], 'unit': match[1].lower()}
        for match in matches
    ]


def tokenize_text(text: str, remove_stopwords: bool = False) -> List[str]:
    """
    Tokenize text into words.

    Args:
        text: Input text
        remove_stopwords: Whether to remove common stopwords

    Returns:
        List of tokens
    """
    # Simple tokenization
    tokens = re.findall(r'\b\w+\b', text.lower())

    if remove_stopwords:
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'as', 'if', 'then', 'than'
        }
        tokens = [t for t in tokens if t not in stopwords]

    return tokens


def preprocess_image(
    image: Union[np.ndarray, List],
    target_size: Optional[Tuple[int, int]] = None,
    normalize: bool = True
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Preprocess image data for model input.

    Args:
        image: Input image array
        target_size: Optional (height, width) for resizing
        normalize: Whether to normalize to [0, 1]

    Returns:
        Tuple of (preprocessed array, metadata dict)
    """
    arr = np.asarray(image, dtype=np.float32)
    metadata = {
        'original_shape': arr.shape,
        'original_dtype': str(arr.dtype),
        'min_value': float(arr.min()),
        'max_value': float(arr.max()),
        'mean_value': float(arr.mean()),
        'std_value': float(arr.std())
    }

    # Reshape if 1D (flattened image)
    if arr.ndim == 1:
        side = int(np.sqrt(arr.size))
        if side * side == arr.size:
            arr = arr.reshape(side, side, 1)
            metadata['reshaped'] = True
        else:
            metadata['reshaped'] = False

    # Resize if target_size specified
    if target_size and arr.ndim >= 2:
        # Simple resize using numpy (nearest neighbor)
        from skimage.transform import resize
        try:
            arr = resize(arr, (*target_size, arr.shape[-1] if arr.ndim == 3 else 1),
                        mode='reflect', anti_aliasing=True)
            metadata['resized'] = True
        except ImportError:
            metadata['resized'] = False
            metadata['resize_error'] = 'scikit-image not available'

    # Normalize
    if normalize and arr.max() > 1.0:
        arr = arr / 255.0
        metadata['normalized'] = True
    else:
        metadata['normalized'] = False

    metadata['final_shape'] = arr.shape
    metadata['final_min'] = float(arr.min())
    metadata['final_max'] = float(arr.max())

    return arr, metadata


def one_hot_encode(labels: List[int], num_classes: int) -> np.ndarray:
    """
    One-hot encode integer labels.

    Args:
        labels: List of integer labels
        num_classes: Total number of classes

    Returns:
        One-hot encoded array
    """
    encoded = np.zeros((len(labels), num_classes), dtype=np.float32)
    for i, label in enumerate(labels):
        if 0 <= label < num_classes:
            encoded[i, label] = 1.0
    return encoded


def pad_sequence(
    sequence: Union[List, np.ndarray],
    max_length: int,
    pad_value: float = 0.0,
    padding: str = 'post'
) -> np.ndarray:
    """
    Pad sequence to fixed length.

    Args:
        sequence: Input sequence
        max_length: Target length
        pad_value: Value to use for padding
        padding: 'post' (pad at end) or 'pre' (pad at beginning)

    Returns:
        Padded numpy array
    """
    arr = np.asarray(sequence, dtype=np.float32)

    if len(arr) >= max_length:
        return arr[:max_length]

    pad_width = max_length - len(arr)

    if padding == 'pre':
        return np.pad(arr, (pad_width, 0), constant_values=pad_value)
    else:  # 'post'
        return np.pad(arr, (0, pad_width), constant_values=pad_value)


def batch_generator(
    data: Union[List, np.ndarray],
    batch_size: int,
    shuffle: bool = False
):
    """
    Generate batches from data.

    Args:
        data: Input data
        batch_size: Size of each batch
        shuffle: Whether to shuffle data

    Yields:
        Batches of data
    """
    arr = np.asarray(data)
    indices = np.arange(len(arr))

    if shuffle:
        np.random.shuffle(indices)

    for start in range(0, len(arr), batch_size):
        end = min(start + batch_size, len(arr))
        batch_indices = indices[start:end]
        yield arr[batch_indices]


# Example usage
if __name__ == "__main__":
    print("=== Preprocessing Utilities Test ===")

    # Text cleaning
    sample_text = "  Patient with   stage II cancer...  "
    print(f"Original: '{sample_text}'")
    print(f"Cleaned: '{clean_text(sample_text)}'")

    # Number extraction
    text_with_numbers = "Dosage: 100mg, frequency: 2 times daily for 14 days"
    numbers = extract_numbers(text_with_numbers)
    print(f"Numbers extracted: {numbers}")

    # Measurements
    measurements = extract_measurements(text_with_numbers)
    print(f"Measurements: {measurements}")

    # Tokenization
    tokens = tokenize_text("The patient received treatment", remove_stopwords=True)
    print(f"Tokens (no stopwords): {tokens}")

    # Image preprocessing
    test_image = np.random.rand(28, 28).astype(np.float32) * 255
    processed, meta = preprocess_image(test_image, normalize=True)
    print(f"Image preprocessing: {meta}")

    # One-hot encoding
    labels = [0, 2, 1, 3]
    encoded = one_hot_encode(labels, num_classes=4)
    print(f"One-hot encoded:\n{encoded}")

    # Padding
    sequence = [1, 2, 3]
    padded = pad_sequence(sequence, max_length=5, padding='post')
    print(f"Padded sequence: {padded}")
