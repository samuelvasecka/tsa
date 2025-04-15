import pandas as pd
from scipy.signal import find_peaks

from data.data import get_time_column
from indicators.technical_indicator import TechnicalIndicator, fibonacci_sequence_up_to, check_columns, \
    create_time_numeric_column, get_segments, get_trend_line, IndicatorEnums
from utils.triangle_test_data_generator import train_model, detect_triangle


class TrianglePatternMachineLearning(TechnicalIndicator):

    # Metóda na detekciu vzoru
    def detect(self, df: pd.DataFrame, price_column: str = "0", time_column: str = "1"):

        # Kontrola, či máme všetky potrebné stĺpce
        if not check_columns(df, price_column, time_column):
            return {"pattern": "Triangle", "detected": False}

        # Metóda natrénuje model na detekciu trojuholníkov v prípa
        train_model()

        # Pokiaľ máme časový údaj v dátumovom formáte, skonvertujeme ho na čoasový údaj
        df = create_time_numeric_column(df, time_column)
        n = len(df)

        # Určenie segmentov dát, nad ktorými budeme vzor hľadať
        price_segment, time_numeric_segment, time_segment = get_segments(df, n, price_column, time_column)

        fib_numbers = fibonacci_sequence_up_to(len(price_segment))
        while fib_numbers[-1] < 5:
            fib_numbers.pop()

        fib_numbers.insert(0, len(price_segment))

        check_index = 0
        result = {"type": 0, "confidence": 0.0}
        window = fib_numbers[-1]

        # Cyklus pre detekovanie trojuholníkového vzoru v okne na konci dát o veľkosti hodnoty z Fibonačiho postupnosti
        for fib_number in reversed(fib_numbers):
            new_result = detect_triangle(price_segment[-fib_number:])

            # Ak sme nedetekovali trojuholník v aktuálnom okne, ale pred tým sme už trojuholmník našli, skúsime okno zväčšiť ešte tri krát
            if new_result["type"] == 0 and result["type"] != 0:
                if check_index < 3:
                    check_index += 1
                else:
                    break
            else:
                if new_result["confidence"] >= result["confidence"]:
                    result = new_result
                    window = fib_number
                    check_index = 0

        if result["type"] == 0:
            return {
                "pattern": "Triangle",
                "detected": False
            }

        # Data na vykreslenie nájdeného trojuholníka
        triangle_segment = price_segment[-window:]

        length = len(triangle_segment)
        distance = max(1, int(length * 0.3))

        peaks_idx, _ = find_peaks(price_segment, distance=distance)
        troughs_idx, _ = find_peaks(-price_segment, distance=distance)

        start_idx = len(price_segment) - window

        filtered_peaks_idx = [idx for idx in peaks_idx if idx >= start_idx]
        filtered_troughs_idx = [idx for idx in troughs_idx if idx >= start_idx]

        peaks = price_segment[filtered_peaks_idx]
        troughs = price_segment[filtered_troughs_idx]
        peak_numeric_times = time_numeric_segment[filtered_peaks_idx]
        trough_numeric_times = time_numeric_segment[filtered_troughs_idx]
        peak_times = time_segment[filtered_peaks_idx]
        trough_times = time_segment[filtered_troughs_idx]

        new_peaks, new_peak_times, new_peak_times_numeric = get_trend_line(peaks, peak_times, peak_numeric_times)
        new_troughs, new_trough_times, new_trough_times_numeric = get_trend_line(troughs, trough_times,
                                                                                 trough_numeric_times)

        # Vrátenie výsledkov nájdeného vzoru
        return {
            "pattern": "Triangle",
            "detected": True,
            "breakout": IndicatorEnums.GLOBAL_UP.value if result["type"] == 1 else IndicatorEnums.GLOBAL_DOWN.value,
            "confidence": result["confidence"],
            "peaks": {
                "time_numeric": peak_numeric_times,
                "time": peak_times,
                "price": peaks,
                "avg_time_numeric": new_peak_times_numeric,
                "avg_time": new_peak_times,
                "avg_price": new_peaks,
            },
            "troughs": {
                "time_numeric": trough_numeric_times,
                "time": trough_times,
                "price": troughs,
                "avg_time_numeric": new_trough_times_numeric,
                "avg_time": new_trough_times,
                "avg_price": new_troughs,
            },
            "df": df
        }

    # Metóda na vykreslenie nájdených výsledkov vzoru
    def show(self, result, main_window, df):
        # Ak sme vzor našli
        if result["detected"]:

            # Vykreslíme maximá a minimá valjkovej časti vzoru
            main_window.ax.scatter(result["peaks"]["time"], result["peaks"]["price"], color="green",
                                   label="Triangle Peaks and Troughs",
                                   zorder=5)
            main_window.ax.scatter(result["troughs"]["time"], result["troughs"]["price"], color="green",
                                   zorder=5)

            # Vykreslíme hornú a dolnú hranicu trojuholníku
            main_window.ax.plot([result["peaks"]["avg_time"][0], result["peaks"]["avg_time"][-1]],
                                [result["peaks"]["avg_price"][0], result["peaks"]["avg_price"][-1]],
                                color="green", label="Triangle Upper Trend Line")
            main_window.ax.plot([result["troughs"]["avg_time"][0], result["troughs"]["avg_time"][-1]],
                                [result["troughs"]["avg_price"][0], result["troughs"]["avg_price"][-1]],
                                color="green", linestyle='dashed', label="Triangle Lower Trend Line")

            # Ak je odhadovaný smer rast, tak ho vykreslíme
            if result["breakout"] == IndicatorEnums.GLOBAL_UP.value:
                x1, x2 = result["troughs"]["avg_time_numeric"][0], result["troughs"]["avg_time_numeric"][-1]
                y1, y2 = result["troughs"]["avg_price"][0], result["troughs"]["avg_price"][-1]

                slope = (y2 - y1) / (x2 - x1)

                length = (x2 - x1) * 4

                x3 = x2 + length
                y3 = slope * (x3 - x2) + y2

                x2 = result["troughs"]["avg_time"][-1]
                x3 = df[get_time_column()].min() + pd.to_timedelta(x3, unit="s")

                main_window.ax.plot([x2, x3], [y2, y3], color="lime", linestyle='dashed',
                                    label="Extended Triangle Trend Line")

            # Ak je odhadovaný smer klesanie, tak ho vykreslíme
            elif result["breakout"] == IndicatorEnums.GLOBAL_DOWN.value:
                x1, x2 = result["peaks"]["avg_time_numeric"][0], result["peaks"]["avg_time_numeric"][-1]
                y1, y2 = result["peaks"]["avg_price"][0], result["peaks"]["avg_price"][-1]

                slope = (y2 - y1) / (x2 - x1)

                length = (x2 - x1) * 4

                x3 = x2 + length
                y3 = slope * (x3 - x2) + y2

                x2 = result["peaks"]["avg_time"][-1]
                x3 = df[get_time_column()].min() + pd.to_timedelta(x3, unit="s")

                main_window.ax.plot([x2, x3], [y2, y3], color="lime", label="Extended Triangle Trend Line")