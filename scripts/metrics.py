import os
import pickle
import threading

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.widgets import Button
from scipy.signal import find_peaks
from sklearn.metrics import roc_curve, auc

from indicators.technical_indicator import fibonacci_sequence_up_to, IndicatorEnums
from indicators.triangle_pattern import TrianglePattern
from utils.triangle_test_data_generator import train_model, generate_triangle_data, detect_triangle, extract_features

button_event = threading.Event()
action_result = None

def test_metrics():
    # Ak nemáme model tak sa natrénuje
    train_model()

    result = None

    # Testové simulácie
    for simulation in range(1):
        X_test, y_test = generate_triangle_data(n_samples=100, length=50, with_random_data=True)

        # Hodnoty na zaznamenávanie správnosti detekcie
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        true_positives_geometric = 0
        false_positives_geometric = 0
        false_negatives_geometric = 0

        # Prejdenie cez všetky testové data
        for i in range(len(X_test)):

            # Vytvorenie testového datasetu
            df_test = pd.DataFrame({
                'time': np.arange(len(X_test[i])),
                'value': X_test[i]
            })

            triangle_pattern = TrianglePattern()

            # Detekcia trojuholníka na základe geometrického algoritmu
            geometric_result = triangle_pattern.detect(df_test, 'value', 'time')

            # Cyhodnotenie detekcie
            if geometric_result["detected"]:

                if geometric_result["breakout"] == IndicatorEnums.GLOBAL_UP.value and y_test[i] == 1 or \
                        geometric_result["breakout"] == IndicatorEnums.GLOBAL_DOWN.value and y_test[i] == 2:
                    true_positives_geometric += 1
                else:
                    user_result_geometric = visual_validation_geometric(df_test, geometric_result, y_test, i,
                                                                        True)

                    if user_result_geometric is not None:
                        if user_result_geometric:
                            false_negatives_geometric += 1
                        elif not user_result_geometric:
                            false_positives_geometric += 1

            else:
                if y_test[i] == 0:
                    true_positives_geometric += 1
                else:
                    user_result_geometric = visual_validation_geometric(df_test, geometric_result, y_test, i,
                                                                        False)

                    if user_result_geometric is not None:
                        if user_result_geometric:
                            false_negatives_geometric += 1
                        elif not user_result_geometric:
                            false_positives_geometric += 1

            check_index = 0
            result = {"type": 0, "confidence": 0.0}
            window = 0

            value_segment = df_test['value'].values

            fib_numbers = fibonacci_sequence_up_to(len(value_segment))
            while fib_numbers[-1] < 5:
                fib_numbers.pop()

            fib_numbers.insert(0, len(value_segment))

            #  Detekcia trojuholníka na základe strojového učenia
            for fib_number in reversed(fib_numbers):
                new_result = detect_triangle(value_segment[-fib_number:])

                if new_result["type"] == 0 and result["type"] != 0:
                    if check_index < 3:
                        check_index += 1
                    else:
                        break
                else:
                    result = new_result
                    check_index = 0
                    window = fib_number

            if result["type"] == y_test[i]:
                true_positives += 1
            else:
                user_result = visual_validation_machine_learning(df_test, window, result, y_test, i)

                if user_result is not None:
                    if user_result:
                        false_negatives += 1
                    elif not user_result:
                        false_positives += 1

        # Výpis metrík do konzoly
        print_metrics(true_positives, false_positives, false_negatives, label="(ML)")
        print_metrics(true_positives_geometric, false_positives_geometric, false_negatives_geometric, label="(Geometric)")

        print("Total: ", len(X_test))

        base_dir = os.path.dirname(__file__)
        model_dir = os.path.abspath(os.path.join(base_dir, '..', 'models'))
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, 'triangle_model.pkl')

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        X_feat = [extract_features(x) for x in X_test]

        y_pred_proba_all = model.predict_proba(X_feat)

        # Vykreslnie ROC krivky pre rastúci a klesajúci trojuholník
        for i in range(1,3):

            target_class = i
            y_pred_probs = y_pred_proba_all[:, target_class]

            y_test_binary = (y_test == target_class).astype(int)

            fpr, tpr, thresholds = roc_curve(y_test_binary, y_pred_probs)
            roc_auc = auc(fpr, tpr)

            plt.figure(figsize=(8, 6))
            plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve { "(Ascending triangle)" if i == 1 else "(Descending triangle)"} (AUC = {roc_auc:.4f})')
            plt.plot([0, 1], [0, 1], color='gray', linestyle='--', lw=1)
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('ROC Curve')
            plt.legend(loc="lower right")
            plt.grid(True)
            plt.tight_layout()
            plt.draw()
            plt.waitforbuttonpress()

            plt.close()

# Metóda na akceptovanie detekcie
def on_accept(event):
    global action_result
    action_result = True
    button_event.set()

# Metóda na odmietnutie detekcie
def on_reject(event):
    global action_result
    action_result = False
    button_event.set()

# Metóda na vizualizáciu konkrétnej detekcie strojovým učením
def visual_validation_machine_learning(df_test, window, result, y_test, i):
    label_map = {0: 'Random data', 1: 'Ascending triangle', 2: 'Descending triangle'}

    plt.ion()
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)

    global button_event
    button_event.clear()

    ax_accept = plt.axes([0.7, 0.05, 0.1, 0.075])
    btn_accept = Button(ax_accept, 'Correct')
    btn_accept.on_clicked(on_accept)

    ax_reject = plt.axes([0.81, 0.05, 0.1, 0.075])
    btn_reject = Button(ax_reject, 'Incorrect')
    btn_reject.on_clicked(on_reject)

    ax.clear()
    ax.plot(df_test.tail(window), marker='o')

    value_segment = df_test['value'].tail(window)
    time_segment = df_test['time'].tail(window)

    length = len(value_segment)
    distance = max(1, int(length * 0.3))

    peaks, _ = find_peaks(value_segment, distance=distance)
    troughs, _ = find_peaks(-value_segment, distance=distance)

    if len(peaks) > 1:
        peak_times = time_segment.iloc[peaks].astype(float)
        peak_values = value_segment.iloc[peaks]
        coeffs_upper = np.polyfit(peak_times, peak_values, 1)
        y_upper = coeffs_upper[0] * peak_times + coeffs_upper[1]
        ax.plot(peak_times, y_upper, color='red', linestyle='--', label='Upper slope')

    if len(troughs) > 1:
        trough_times = time_segment.iloc[troughs].astype(float)
        trough_values = value_segment.iloc[troughs]
        coeffs_lower = np.polyfit(trough_times, trough_values, 1)
        y_lower = coeffs_lower[0] * trough_times + coeffs_lower[1]
        ax.plot(trough_times, y_lower, color='green', linestyle='--', label='Lower slope')

    ax.set_title(
        f'Window size: {window}\nDetekovaný tvar: {label_map[result["type"]]}\nTestové data: {label_map[y_test[i]]}')
    ax.set_ylim(-0.2, 1.2)
    ax.legend()
    plt.draw()

    plt.ioff()
    plt.show(block=False)

    while not button_event.is_set():
        plt.pause(0.1)

    plt.close(fig)

    return action_result

# Metóda na vizualizáciu konkrétnej detekcie geometrickým algoritmom
def visual_validation_geometric(df_test, result, y_test, i, is_detected):
    label_map = {IndicatorEnums.GLOBAL_UP.value: 'Ascending triangle', IndicatorEnums.GLOBAL_DOWN.value: 'Descending triangle', 0: 'Not Detected'}
    label_map_test = {0: 'Random data', 1: 'Ascending triangle', 2: 'Descending triangle'}

    plt.ion()
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)

    global button_event
    button_event.clear()

    ax_accept = plt.axes([0.7, 0.05, 0.1, 0.075])
    btn_accept = Button(ax_accept, 'Correct')
    btn_accept.on_clicked(on_accept)

    ax_reject = plt.axes([0.81, 0.05, 0.1, 0.075])
    btn_reject = Button(ax_reject, 'Incorrect')
    btn_reject.on_clicked(on_reject)

    ax.clear()

    ax.clear()
    ax.plot(df_test, marker='o', label='Data')

    if is_detected:
        ax.plot([result["peaks"]["avg_time"][0], result["peaks"]["avg_time"][-1]],
                [result["peaks"]["avg_price"][0], result["peaks"]["avg_price"][-1]],
                color="green", label="Triangle Upper Trend Line")
        ax.plot([result["troughs"]["avg_time"][0], result["troughs"]["avg_time"][-1]],
                [result["troughs"]["avg_price"][0], result["troughs"]["avg_price"][-1]],
                color="green", linestyle='dashed', label="Triangle Lower Trend Line")

    if is_detected:
        detected = label_map[result["breakout"]]
    else:
        detected = label_map[0]

    ax.set_title(
        f'Window size: {result["window"]}\nDetekovaný tvar: {detected}\nTestové data: {label_map_test[y_test[i]]}')
    ax.set_ylim(-0.2, 1.2)
    ax.legend()
    plt.draw()

    plt.ioff()
    plt.show(block=False)

    while not button_event.is_set():
        plt.pause(0.1)

    plt.close(fig)

    return action_result

# Metóda na výpis metrík
def print_metrics(tp, fp, fn, label=""):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f"--- Metrics {label} ---")
    print(f"True Positives:  {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"Precision:       {precision:.4f}")
    print(f"Recall:          {recall:.4f}")
    print(f"F1 Score:        {f1:.4f}")
    print()

test_metrics()