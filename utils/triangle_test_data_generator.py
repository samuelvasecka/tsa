import random
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from scipy.signal import find_peaks
import pickle
import os

# Funkcia na generovanie dát
def generate_triangle_data(n_samples=1, length=50, with_random_data=False, noise_level=0.05):
    X = []
    y = []
    for _ in range(n_samples):

        if with_random_data:
            pattern_type = np.random.choice(['ascending', 'descending', 'random'])
        else:
            pattern_type = np.random.choice(['ascending', 'descending'])

        periods = np.random.randint(5, 12)
        t = np.linspace(0, periods * np.pi, length)

        if pattern_type == 'ascending':
            high_val = 1.0
            low_start = np.random.uniform(0.0, 0.7)
            lows = np.linspace(low_start, high_val, length)
            highs = np.ones(length) * high_val
            values = lows + (highs - lows) * 0.5 * (1 + np.sin(t))
            values += np.random.normal(0, noise_level, length)
            y.append(1)

        elif pattern_type == 'descending':
            low_val = 0.0
            high_start = np.random.uniform(0.3, 1.0)
            highs = np.linspace(high_start, low_val, length)
            lows = np.ones(length) * low_val
            values = lows + (highs - lows) * 0.5 * (1 + np.sin(t))
            values += np.random.normal(0, noise_level, length)
            y.append(2)
        else:
            pattern_variant = np.random.choice([
                'random_noise', 'normal', 'line_up', 'line_down', 'exp_up', 'exp_down',
                'both_up', 'both_down',
                'widening', 'narrowing',
                'flat'
            ])

            if pattern_variant == 'both_up':
                low_start = np.random.uniform(0.0, 0.2)
                low_end = np.random.uniform(0.6, 0.8)
                high_start = np.random.uniform(0.2, 0.4)
                high_end = np.random.uniform(0.8, 1.0)
                lows = np.linspace(low_start, low_end, length)
                highs = np.linspace(high_start, high_end, length)

                values = lows + (highs - lows) * 0.5 * (1 + np.sin(t))
                values += np.random.normal(0, noise_level, length)
                y.append(0)
            elif pattern_variant == 'both_down':
                low_start = np.random.uniform(0.6, 0.8)
                low_end = np.random.uniform(0.0, 0.2)
                high_start = np.random.uniform(1.0, 0.8)
                high_end = np.random.uniform(0.2, 0.4)
                lows = np.linspace(low_start, low_end, length)
                highs = np.linspace(high_start, high_end, length)

                values = lows + (highs - lows) * 0.5 * (1 + np.sin(t))
                values += np.random.normal(0, noise_level, length)
                y.append(0)
            elif pattern_variant == 'widening':
                low_start = np.random.uniform(0.3, 0.5)
                low_end = np.random.uniform(0.0, 0.2)
                high_start = np.random.uniform(0.5, 0.7)
                high_end = np.random.uniform(0.8, 1.0)
                lows = np.linspace(low_start, low_end, length)
                highs = np.linspace(high_start, high_end, length)

                values = lows + (highs - lows) * 0.5 * (1 + np.sin(t))
                values += np.random.normal(0, noise_level, length)
                y.append(0)
            elif pattern_variant == 'narrowing':
                low_start = np.random.uniform(0.0, 0.2)
                low_end = np.random.uniform(0.3, 0.5)
                high_start = np.random.uniform(0.8, 1.0)
                high_end = np.random.uniform(0.5, 0.7)
                lows = np.linspace(low_start, low_end, length)
                highs = np.linspace(high_start, high_end, length)

                values = lows + (highs - lows) * 0.5 * (1 + np.sin(t))
                values += np.random.normal(0, noise_level, length)
                y.append(0)
            elif pattern_variant == 'flat':
                lows = np.ones(length) * 0.3
                highs = np.ones(length) * 0.7

                values = lows + (highs - lows) * 0.5 * (1 + np.sin(t))
                values += np.random.normal(0, noise_level, length)
                y.append(0)
            else:

                base = random.choice([
                    np.random.rand(length),
                    (np.random.normal(loc=0.5, scale=0.15, size=length)).clip(0, 1),
                    np.linspace(random.uniform(0.0, 0.5), random.uniform(0.5, 1.0), length) + np.random.normal(0,
                                                                                                               noise_level,
                                                                                                               length),
                    np.linspace(random.uniform(0.5, 1.0), random.uniform(0.0, 0.5), length) + np.random.normal(0,
                                                                                                               noise_level,
                                                                                                               length),
                    ((np.power(random.uniform(1.01, 1.1), np.arange(length)) - 1) /
                     (np.power(random.uniform(1.01, 1.1), length - 1) - 1)) + np.random.normal(0, noise_level, length),
                    (1 - ((np.power(random.uniform(1.01, 1.1), np.arange(length)) - 1) /
                          (np.power(random.uniform(1.01, 1.1), length - 1) - 1))) + np.random.normal(0, noise_level,
                                                                                                     length),
                ])
                scale = np.random.uniform(0.5, 3.0)
                offset = np.random.uniform(-2, 2)
                signal = base * scale + offset

                min_val = np.min(signal)
                max_val = np.max(signal)
                if max_val - min_val == 0:
                    return np.zeros(length)
                values = (signal - min_val) / (max_val - min_val)
                y.append(0)

        X.append(values)

    return np.array(X), np.array(y)

# Metóda na získanie vlastností, ktoré sú podstatné pre detekciu trojuholníkov
def extract_features(segment):
    segment_norm = (segment - np.min(segment)) / (np.max(segment) - np.min(segment)) * len(segment)

    peaks, _ = find_peaks(segment_norm)
    troughs, _ = find_peaks(-segment_norm)

    peak_values = segment_norm[peaks] if len(peaks) > 1 else []
    trough_values = segment_norm[troughs] if len(troughs) > 1 else []

    upper_slope = (
        np.polyfit(peaks, peak_values, 1)[0]
        if len(peaks) > 1 else 0.0
    )
    lower_slope = (
        np.polyfit(troughs, trough_values, 1)[0]
        if len(troughs) > 1 else 0.0
    )

    # Podstatné vlastnosti sú horná a dolná hranica trojuholníka
    features = {
        'upper_slope': upper_slope,
        'lower_slope': lower_slope,
    }

    return list(features.values())

# Metóda na tréning modelu
def train_model():

    base_dir = os.path.dirname(__file__)
    model_dir = os.path.abspath(os.path.join(base_dir, '..', 'models'))
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, 'triangle_model.pkl')

    if not os.path.exists(model_path):
        X_raw, y = generate_triangle_data(n_samples=10000, with_random_data=True)
        X_feat = [extract_features(x) for x in X_raw]

        model = make_pipeline(StandardScaler(), RandomForestClassifier())
        model.fit(X_feat, y)

        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        print("Model natrénovaný a uložený ako triangle_model.pkl")

# Metóda na detekciu trojuholníka na základe strojového učenia
def detect_triangle(price_segment):
    base_dir = os.path.dirname(__file__)
    model_dir = os.path.abspath(os.path.join(base_dir, '..', 'models'))
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, 'triangle_model.pkl')

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    best_result = {"type": 0, "confidence": 0.0}

    features = extract_features(price_segment)
    prediction = model.predict([features])[0]

    probs = model.predict_proba([features])[0]
    confidence = probs[prediction]

    if prediction != 0:
        best_result = {"type": prediction, "confidence": confidence}

    return best_result