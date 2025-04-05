import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from data.data import get_time_column
from indicators.technical_indicator import TechnicalIndicator, IndicatorEnums, check_columns, \
    create_time_numeric_column, get_segments, get_normalized_data, calculate_average_slope, \
    get_trend_line, fibonacci_sequence_up_to

# Metóda na určenie či sú body približne horizontálne
def is_horizontal(values, threshold=0.02):
    return max(values) - min(values) < threshold

# Metóda na kontrolu trojuholníkového vzoru
def check_triangle_pattern(peaks, troughs, peak_times, trough_times):
    valid_peaks_idx, valid_troughs_idx, breakout = [], [], None

    # V cykle prechádzame dáta od 2 do dĺžky maxím, resp. miním
    for i in range(2, min(len(peaks), len(troughs)) + 1):

        # Data prehľadávame od konca
        current_peaks = peaks[-i:]
        current_troughs = troughs[-i:]
        current_peak_times = peak_times[-i:]
        current_trough_times = trough_times[-i:]

        # Výpočet sklonu hornej a dolnej hranice
        upper_slope = calculate_average_slope(current_peaks, current_peak_times)
        lower_slope = calculate_average_slope(current_troughs, current_trough_times)

        # Ak je horná hranica horizontálna a dolná hranica rastie
        if is_horizontal(current_peaks) and lower_slope > 0:
            valid_peaks_idx = list(range(len(peaks) - i, len(peaks)))
            valid_troughs_idx = list(range(len(troughs) - i, len(troughs)))
            breakout = IndicatorEnums.GLOBAL_UP.value

        # Ak je dolná hranica horizontálna a horná hranica klesá
        elif is_horizontal(current_troughs) and upper_slope < 0:
            valid_peaks_idx = list(range(len(peaks) - i, len(peaks)))
            valid_troughs_idx = list(range(len(troughs) - i, len(troughs)))
            breakout = IndicatorEnums.GLOBAL_DOWN.value

    return valid_peaks_idx, valid_troughs_idx, breakout

# Metóda na nájdenie trojuholníkového vzoru
def find_triangle_pattern(price_segment, time_numeric_segment):
    fib_numbers = fibonacci_sequence_up_to(int(len(price_segment) * 0.5))
    while fib_numbers[-1] < 5:
        fib_numbers.pop()

    # Cyklus pre nastavenie veľkosti okna pre hľadanie maxím a miním pomocou Fibonačiho postupnosti
    for order_value in reversed(fib_numbers):

        # Nájdené maximá a minimá
        peaks_idx = argrelextrema(price_segment, np.greater, order=order_value)[0]
        troughs_idx = argrelextrema(price_segment, np.less, order=order_value)[0]

        peaks = price_segment[peaks_idx]
        troughs = price_segment[troughs_idx]
        peak_numeric_times = time_numeric_segment[peaks_idx]
        trough_numeric_times = time_numeric_segment[troughs_idx]

        # Ak máme aspoň 2 maximá a 2 minimá
        if len(peaks) >= 2 and len(troughs) >= 2:
            norm_peaks, norm_peak_numeric_times, norm_troughs, norm_trough_numeric_times = get_normalized_data(peaks,
                                                                                                               troughs,
                                                                                                               peak_numeric_times,
                                                                                                               trough_numeric_times)

            # Skontrolujeme či ide o trojuholníkový vzor
            valid_peaks_idx, valid_troughs_idx, breakout = check_triangle_pattern(norm_peaks, norm_troughs,
                                                                                  norm_peak_numeric_times,
                                                                                  norm_trough_numeric_times)
            if valid_peaks_idx and valid_troughs_idx:
                return breakout, peaks_idx[valid_peaks_idx], troughs_idx[
                    valid_troughs_idx], norm_peaks, norm_peak_numeric_times, norm_troughs, norm_trough_numeric_times

    return None, None, None, None, None, None, None

# Trieda pre technický indikátor Trojuholník
class TrianglePattern(TechnicalIndicator):

    # Metóda na detekciu vzoru
    def detect(self, df: pd.DataFrame, price_column: str = "0", time_column: str = "1"):

        # Kontrola, či máme všetky potrebné stĺpce
        if not check_columns(df, price_column, time_column):
            return {"pattern": "Triangle", "detected": False}

        # Pokiaľ máme časový údaj v dátumovom formáte, skonvertujeme ho na čoasový údaj
        df = create_time_numeric_column(df, time_column)
        n = len(df)

        # Určenie segmentov dát, nad ktorými budeme vzor hľadať
        price_segment, time_numeric_segment, time_segment = get_segments(df, n, price_column, time_column)

        # Nájdeme trojuholníkový vzor
        breakout, peaks_idx, troughs_idx, norm_peaks, norm_peak_numeric_times, norm_troughs, norm_trough_numeric_times = find_triangle_pattern(
            price_segment, time_numeric_segment)

        # Ak sme nenašli maximá a minimá, nenašli sme vzor
        if peaks_idx is None or troughs_idx is None:
            return {
                "pattern": "Triangle",
                "detected": False
            }

        peaks = price_segment[peaks_idx]
        troughs = price_segment[troughs_idx]
        peak_numeric_times = time_numeric_segment[peaks_idx]
        trough_numeric_times = time_numeric_segment[troughs_idx]
        peak_times = time_segment[peaks_idx]
        trough_times = time_segment[troughs_idx]

        new_peaks, new_peak_times, new_peak_times_numeric = get_trend_line(peaks, peak_times, peak_numeric_times)
        new_troughs, new_trough_times, new_trough_times_numeric = get_trend_line(troughs, trough_times,
                                                                                 trough_numeric_times)

        # Vrátenie výsledkov nájdeného vzoru
        return {
            "pattern": "Triangle",
            "detected": True,
            "breakout": breakout,
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

                main_window.ax.plot([x2, x3], [y2, y3], color="lime", linestyle='dashed', label="Extended Triangle Trend Line")

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
