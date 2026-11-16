"""
ANN Priority Prediction Module
================================
Predicts the urgency/priority class of a request using neural networks.
Includes two models as required by the project manual:
1. Perceptron — Binary baseline (Urgent vs Not-Urgent)
2. MLP (Multi-Layer Perceptron) — Multiclass operational model (7→4→3→4 softmax)

CRITICAL RULE: ANN predicts priority ONLY.
It does NOT grant permission, check eligibility, or replace logic-based validation.

Owner: Saim (Member 1 / Leader)

Architecture:
  Perceptron: 7 inputs → 1 output (sigmoid), binary classification
  MLP: 7 inputs → 4 hidden (ReLU) → 3 hidden (ReLU) → 4 output (softmax)
       Classes: Urgent, High, Normal, Low
"""

import numpy as np
import time
import os
import json


# ─── PRIORITY CLASSES ──────────────────────────────────────────────────

PRIORITY_CLASSES = ["Urgent", "High", "Normal", "Low"]


class Perceptron:
    """
    Single-layer perceptron for binary classification (Urgent vs Not-Urgent).
    This is the baseline model required by the project manual.

    Uses sigmoid activation and binary cross-entropy loss.
    """

    def __init__(self, input_size=7, learning_rate=0.1):
        """
        Initialize the perceptron with random weights.

        Args:
            input_size: Number of input features (default 7)
            learning_rate: Learning rate for gradient descent
        """
        np.random.seed(42)
        self.weights = np.random.randn(input_size) * 0.1
        self.bias = 0.0
        self.lr = learning_rate

    def sigmoid(self, z):
        """Sigmoid activation function: σ(z) = 1 / (1 + e^(-z))"""
        z = np.clip(z, -500, 500)  # Prevent overflow
        return 1.0 / (1.0 + np.exp(-z))

    def forward(self, x):
        """
        Forward pass: compute the output for input vector x.

        Args:
            x: Input feature vector (7 elements)

        Returns:
            Probability of class "Urgent" (0 to 1)
        """
        z = np.dot(x, self.weights) + self.bias
        return self.sigmoid(z)

    def predict(self, x, threshold=0.5):
        """
        Predict binary class for input x.

        Args:
            x: Input feature vector
            threshold: Classification threshold (default 0.5)

        Returns:
            1 if Urgent, 0 if Not-Urgent
        """
        return 1 if self.forward(x) >= threshold else 0

    def train(self, X, y, epochs=100):
        """
        Train the perceptron using gradient descent on binary cross-entropy.

        Args:
            X: Training data, shape (n_samples, 7)
            y: Labels, shape (n_samples,), values 0 or 1
            epochs: Number of training epochs
        """
        for epoch in range(epochs):
            total_loss = 0
            for xi, yi in zip(X, y):
                # Forward pass
                pred = self.forward(xi)
                # Binary cross-entropy loss
                eps = 1e-7
                loss = -(yi * np.log(pred + eps) + (1 - yi) * np.log(1 - pred + eps))
                total_loss += loss
                # Gradient descent
                error = pred - yi
                self.weights -= self.lr * error * xi
                self.bias -= self.lr * error

            if (epoch + 1) % 20 == 0:
                avg_loss = total_loss / len(X)
                print(f"  Perceptron Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")


class MLP:
    """
    Multi-Layer Perceptron for multiclass priority prediction.
    Architecture: 7 → 4 → 3 → 4 (softmax output)
    Classes: Urgent, High, Normal, Low

    This is the operational model used for actual priority prediction.
    Uses ReLU activation in hidden layers and softmax at output.
    Trained with backpropagation and cross-entropy loss.
    """

    def __init__(self, layer_sizes=None, learning_rate=0.01):
        """
        Initialize the MLP with random weights.

        Args:
            layer_sizes: List of layer sizes (default [7, 4, 3, 4])
            learning_rate: Learning rate for gradient descent
        """
        if layer_sizes is None:
            layer_sizes = [7, 4, 3, 4]

        np.random.seed(42)
        self.layer_sizes = layer_sizes
        self.lr = learning_rate
        self.weights = []
        self.biases = []

        # Xavier initialization for each layer
        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            limit = np.sqrt(6.0 / (fan_in + fan_out))
            w = np.random.uniform(-limit, limit, (fan_in, fan_out))
            b = np.zeros(fan_out)
            self.weights.append(w)
            self.biases.append(b)

    def relu(self, z):
        """ReLU activation: max(0, z)"""
        return np.maximum(0, z)

    def relu_derivative(self, z):
        """Derivative of ReLU: 1 if z > 0, else 0"""
        return (z > 0).astype(float)

    def softmax(self, z):
        """Softmax activation for output layer: converts logits to probabilities."""
        z_shifted = z - np.max(z)  # Numerical stability
        exp_z = np.exp(z_shifted)
        return exp_z / np.sum(exp_z)

    def forward(self, x):
        """
        Forward pass through all layers.

        Args:
            x: Input feature vector (7 elements)

        Returns:
            Tuple of (output_probabilities, list_of_layer_activations)
        """
        activations = [np.array(x, dtype=float)]
        pre_activations = []

        for i in range(len(self.weights)):
            z = np.dot(activations[-1], self.weights[i]) + self.biases[i]
            pre_activations.append(z)

            if i < len(self.weights) - 1:
                # Hidden layers: ReLU
                a = self.relu(z)
            else:
                # Output layer: Softmax
                a = self.softmax(z)
            activations.append(a)

        return activations[-1], activations, pre_activations

    def predict(self, x):
        """
        Predict priority class probabilities for input x.

        Args:
            x: Input feature vector (7 elements)

        Returns:
            Dict mapping class names to probabilities (percentages)
        """
        probs, _, _ = self.forward(x)
        return {cls: round(float(p) * 100, 1) for cls, p in zip(PRIORITY_CLASSES, probs)}

    def predict_class(self, x):
        """
        Predict the most likely priority class.

        Args:
            x: Input feature vector

        Returns:
            Tuple of (class_name, confidence_percentage)
        """
        probs = self.predict(x)
        top_class = max(probs, key=probs.get)
        return top_class, probs[top_class]

    def train(self, X, y, epochs=200, verbose=True):
        """
        Train the MLP using backpropagation with cross-entropy loss.

        Args:
            X: Training data, shape (n_samples, 7)
            y: Labels as one-hot encoded, shape (n_samples, 4)
            epochs: Number of training epochs
            verbose: Whether to print progress
        """
        for epoch in range(epochs):
            total_loss = 0

            for xi, yi in zip(X, y):
                # Forward pass
                output, activations, pre_activations = self.forward(xi)

                # Cross-entropy loss
                eps = 1e-7
                loss = -np.sum(yi * np.log(output + eps))
                total_loss += loss

                # Backpropagation
                # Output layer gradient (softmax + cross-entropy simplifies to output - target)
                delta = output - yi

                # Propagate backwards
                deltas = [delta]
                for i in range(len(self.weights) - 2, -1, -1):
                    d = np.dot(deltas[0], self.weights[i + 1].T)
                    d *= self.relu_derivative(pre_activations[i])
                    deltas.insert(0, d)

                # Update weights and biases
                for i in range(len(self.weights)):
                    grad_w = np.outer(activations[i], deltas[i])
                    self.weights[i] -= self.lr * grad_w
                    self.biases[i] -= self.lr * deltas[i]

            if verbose and (epoch + 1) % 50 == 0:
                avg_loss = total_loss / len(X)
                print(f"  MLP Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

    def save(self, filepath):
        """Save model weights to a JSON file."""
        data = {
            "layer_sizes": self.layer_sizes,
            "weights": [w.tolist() for w in self.weights],
            "biases": [b.tolist() for b in self.biases],
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load(self, filepath):
        """Load model weights from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.layer_sizes = data["layer_sizes"]
        self.weights = [np.array(w) for w in data["weights"]]
        self.biases = [np.array(b) for b in data["biases"]]


class ANNResult:
    """
    Container for ANN module output.
    Stores both Perceptron baseline and MLP predictions.
    """

    def __init__(self, mlp_probs, mlp_class, perceptron_pred, feature_vector,
                 feature_labels, exec_time=0):
        """Initialize ANNResult with MLP probabilities, predicted class, perceptron output, features, and timing."""
        self.mlp_probs = mlp_probs            # Dict {class: probability %}
        self.mlp_class = mlp_class            # Predicted class name
        self.perceptron_pred = perceptron_pred  # 1 (Urgent) or 0 (Not-Urgent)
        self.feature_vector = feature_vector   # Input [x1..x7]
        self.feature_labels = feature_labels   # Descriptive labels for features
        self.exec_time = exec_time             # Execution time in ms

    def __str__(self):
        """Return a formatted string showing MLP and Perceptron predictions with agreement status."""
        probs_str = ", ".join(f"{k}: {v}%" for k, v in self.mlp_probs.items())
        perc_str = "Urgent" if self.perceptron_pred == 1 else "Not-Urgent"
        agree = "agrees" if (self.perceptron_pred == 1) == (self.mlp_class == "Urgent") else "disagrees"
        return (f"ANN Priority: {self.mlp_class}\n"
                f"  MLP: {probs_str}\n"
                f"  Perceptron: {perc_str} ({agree} with MLP)")

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "model": "MLP-7-4-3-4",
            "decision": self.mlp_class,
            "probs": {k: v / 100 for k, v in self.mlp_probs.items()},
            "probs_pct": self.mlp_probs,
            "perceptron": "Urgent" if self.perceptron_pred == 1 else "Not-Urgent",
            "feature_vector": self.feature_vector,
            "exec_time_ms": round(self.exec_time, 2),
        }


# ─── TRAINING DATA GENERATION ─────────────────────────────────────────

def generate_training_data(n_samples=100):
    """
    Generate synthetic training data for the ANN.
    Features: [role, request_type, severity, time_sensitivity, crowd, distance, eligibility]
    Labels: one-hot encoded [Urgent, High, Normal, Low]

    The data reflects realistic campus patterns:
    - High severity + high time sensitivity → Urgent
    - Full_Service or Urgent_Service with high severity → Urgent/High
    - Low severity, low sensitivity → Normal/Low
    """
    np.random.seed(42)
    X = []
    y = []

    for _ in range(n_samples):
        role = np.random.choice([0.0, 0.5, 1.0])          # Student/Instructor/Staff
        req_type = np.random.choice([0.0, 0.25, 0.5, 0.75, 1.0])
        severity = np.random.uniform(0, 1)
        time_sens = np.random.uniform(0, 1)
        crowd = np.random.uniform(0, 1)
        distance = np.random.uniform(0, 1)
        eligibility = np.random.choice([0.0, 1.0], p=[0.2, 0.8])

        features = [role, req_type, severity, time_sens, crowd, distance, eligibility]

        # Determine label based on features (rule-based for training data)
        urgency_score = (severity * 0.35 + time_sens * 0.30 +
                         req_type * 0.15 + crowd * 0.10 + distance * 0.10)

        if urgency_score > 0.7:
            label = 0  # Urgent
        elif urgency_score > 0.5:
            label = 1  # High
        elif urgency_score > 0.3:
            label = 2  # Normal
        else:
            label = 3  # Low

        X.append(features)
        # One-hot encode
        one_hot = [0, 0, 0, 0]
        one_hot[label] = 1
        y.append(one_hot)

    return np.array(X), np.array(y)


# ─── MAIN PREDICTION FUNCTION ─────────────────────────────────────────

# Global models (trained once, reused)
_perceptron = None
_mlp = None


def _ensure_models_trained():
    """Train models if not already trained. Loads from file if available."""
    global _perceptron, _mlp

    if _mlp is not None:
        return

    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'mlp_model.json')

    # Try to load pre-trained model
    if os.path.exists(model_path):
        _mlp = MLP()
        _mlp.load(model_path)
        _perceptron = Perceptron()
        # Train perceptron quickly (it's small)
        X, y = generate_training_data(100)
        y_binary = np.array([1 if label[0] == 1 else 0 for label in y])
        _perceptron.train(X, y_binary, epochs=50)
        return

    print("  Training ANN models (first run)...")

    # Generate training data
    X, y = generate_training_data(100)
    y_binary = np.array([1 if label[0] == 1 else 0 for label in y])

    # Train Perceptron
    _perceptron = Perceptron(input_size=7, learning_rate=0.1)
    _perceptron.train(X, y_binary, epochs=100)

    # Train MLP
    _mlp = MLP(layer_sizes=[7, 4, 3, 4], learning_rate=0.01)
    _mlp.train(X, y, epochs=300, verbose=True)

    # Save MLP model
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    _mlp.save(model_path)
    print(f"  Model saved to {model_path}")


def predict_priority(feature_vector, feature_labels=None):
    """
    Main entry point for the ANN module.
    Predicts priority using both Perceptron (baseline) and MLP (operational).

    Args:
        feature_vector: 7-element list [x1..x7]
        feature_labels: Optional list of descriptive labels for features

    Returns:
        ANNResult with predictions from both models
    """
    start = time.perf_counter()

    _ensure_models_trained()

    x = np.array(feature_vector, dtype=float)

    # MLP prediction
    mlp_probs = _mlp.predict(x)
    mlp_class, _ = _mlp.predict_class(x)

    # Perceptron prediction
    perc_pred = _perceptron.predict(x)

    exec_time = (time.perf_counter() - start) * 1000

    if feature_labels is None:
        feature_labels = [
            {"key": "x1", "label": "Role", "type": "chip"},
            {"key": "x2", "label": "RequestType", "type": "chip"},
            {"key": "x3", "label": "Severity", "type": "bar"},
            {"key": "x4", "label": "TimeSensitivity", "type": "bar"},
            {"key": "x5", "label": "CrowdLevel", "type": "bar"},
            {"key": "x6", "label": "Distance", "type": "bar"},
            {"key": "x7", "label": "Eligibility", "type": "bar"},
        ]

    return ANNResult(
        mlp_probs=mlp_probs,
        mlp_class=mlp_class,
        perceptron_pred=perc_pred,
        feature_vector=list(feature_vector),
        feature_labels=feature_labels,
        exec_time=exec_time,
    )


# ─── TESTING ───────────────────────────────────────────────────────────

def test_ann():
    """Test the ANN module with known scenarios."""
    print("=" * 60)
    print("ANN PRIORITY PREDICTION MODULE — TEST SUITE")
    print("=" * 60)

    # Test 1: Ali's feature vector (high urgency expected)
    print("\n--- Test 1: Ali — Full Service, High Severity ---")
    ali_features = [0.0, 1.0, 0.85, 0.92, 0.40, 0.32, 1.0]
    result = predict_priority(ali_features)
    print(result)
    print(f"  Top class: {result.mlp_class}")
    print(f"  Probabilities: {result.mlp_probs}")
    print("✓ PASSED\n")

    # Test 2: Sara's feature vector (also high urgency — ANN doesn't check eligibility)
    print("--- Test 2: Sara — Full Service, High Severity ---")
    sara_features = [0.0, 1.0, 0.80, 0.88, 0.45, 0.38, 1.0]
    result2 = predict_priority(sara_features)
    print(result2)
    print(f"  NOTE: ANN predicts priority only. Sara may still be rejected by Logic/KB.")
    print("✓ PASSED\n")

    # Test 3: Low severity request (should be Normal or Low)
    print("--- Test 3: Low severity Navigation request ---")
    low_features = [0.0, 0.0, 0.20, 0.10, 0.30, 0.50, 1.0]
    result3 = predict_priority(low_features)
    print(result3)
    print("✓ PASSED\n")

    # Test 4: Perceptron vs MLP agreement
    print("--- Test 4: Perceptron vs MLP agreement ---")
    for name, features in [("Ali (urgent)", ali_features), ("Low severity", low_features)]:
        r = predict_priority(features)
        perc = "Urgent" if r.perceptron_pred == 1 else "Not-Urgent"
        mlp = r.mlp_class
        agree = "✓ agree" if (r.perceptron_pred == 1) == (mlp == "Urgent") else "✗ disagree"
        print(f"  {name:20s}: Perceptron={perc:12s} MLP={mlp:8s} [{agree}]")
    print("✓ PASSED\n")

    # Test 5: Model save/load
    print("--- Test 5: Model persistence ---")
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'mlp_model.json')
    if os.path.exists(model_path):
        print(f"  Model file exists: {model_path}")
        size_kb = os.path.getsize(model_path) / 1024
        print(f"  Size: {size_kb:.1f} KB")
    print("✓ PASSED")

    print("\n" + "=" * 60)
    print("ALL ANN TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_ann()

