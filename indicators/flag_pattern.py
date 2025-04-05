import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from data.data import get_time_column
from indicators.technical_indicator import TechnicalIndicator, check_columns, create_time_numeric_column, get_segments, \
    find_extremes, get_normalized_data, IndicatorEnums, calculate_average_slope, get_trend_line, \
    fibonacci_sequence_up_to

# Metóda na výpočet sklonu segementu dát
def calculate_slope(segment):
    x = np.arange(len(segment))
    y = np.array(segment)
    slope, _ = np.polyfit(x, y, 1)
    return slope

# Metóda na nájdenie vrcholu tyče
def find_flag_transition_fib(price_segment, time_numeric_segment, time_segment, min_percentage=0.2):
    n = len(price_segment)
    fib_numbers = fibonacci_sequence_up_to(int(n * 0.5))
    last_20_percent = int(n * min_percentage)

    best_idx = None
    best_slope_change = 0
    before_segment = None
    before_segment_time_numeric = None
    before_segment_time = None
    number_of_checks = 0
    up = None

    while fib_numbers[-1] < 5:
        fib_numbers.pop()

    # Cyklus pre nastavenie veľkosti okna pre hľadanie maxím a miním pomocou Fibonačiho postupnosti
    for order_value in reversed(fib_numbers):

        # Nájdené maximá a minimá
        peaks_idx = argrelextrema(price_segment, np.greater, order=order_value)[0]
        troughs_idx = argrelextrema(price_segment, np.less, order=order_value)[0]

        # Hľadáme extrémy v posledných 20% dát
        valid_peaks = [idx for idx in peaks_idx if idx >= n - last_20_percent]
        valid_troughs = [idx for idx in troughs_idx if idx >= n - last_20_percent]

        if not valid_peaks and not valid_troughs:
            continue

        # Nájdeme najväčší extrém
        if valid_peaks and valid_troughs:
            peak_idx = max(valid_peaks)
            trough_idx = max(valid_troughs)
            if peak_idx > trough_idx:
                up = True
            else:
                up = False
            extreme_idx = max(peak_idx, trough_idx)
        elif valid_peaks:
            extreme_idx = max(valid_peaks)
            up = True
        else:
            extreme_idx = max(valid_troughs)
            up = False

        # Určenie segemntu dát pred a po nájdenom extréme (vrchole tyče)
        before_length = int((len(price_segment) - extreme_idx) * 1.5)
        before_segment = price_segment[max(0, extreme_idx - before_length):extreme_idx]
        before_segment_time_numeric = time_numeric_segment[max(0, extreme_idx - before_length):extreme_idx]
        before_segment_time = time_segment[max(0, extreme_idx - before_length):extreme_idx]
        after_segment = price_segment[extreme_idx:]

        if len(before_segment) < 2 or len(after_segment) < 2:
            continue

        # Výpočet sklonov obidvoch segmentov
        before_slope = calculate_slope(before_segment)
        after_slope = calculate_slope(after_segment)

        # Ak je sklon pred extrémom (vrcholom tyče) výraznejší ako sklon po extréme, je možné že sme našli vzor
        if abs(before_slope) > abs(after_slope):
            slope_change = abs(before_slope) - abs(after_slope)

            # Ak sme našli lepší sklon, uložíme si ho
            if slope_change > best_slope_change:
                best_slope_change = slope_change
                best_idx = extreme_idx

        # Po poslednom nájdenom sklone, prehľadáme vzor ešte 3x s väčším oknom na hľadanie vrcholu tyče
        if best_idx is not None:
            number_of_checks += 1
            if number_of_checks >= 3:
                return best_idx, up, before_segment, before_segment_time_numeric, before_segment_time

    return best_idx, up, before_segment, before_segment_time_numeric, before_segment_time

# Trieda pre technický indikátor Vlajka
class FlagPattern(TechnicalIndicator):

    # Metóda na detekciu vzoru
    def detect(self, df: pd.DataFrame, price_column: str = "0", time_column: str = "1"):

        # Kontrola, či máme všetky potrebné stĺpce
        if not check_columns(df, price_column, time_column):
            return {
                "pattern": "Flag",
                "detected": False,
                "return": 1,
            }

        # Pokiaľ máme časový údaj v dátumovom formáte, skonvertujeme ho na čoasový údaj
        df = create_time_numeric_column(df, time_column)
        n = len(df)

        # Určenie segmentov dát, nad ktorými budeme vzor hľadať
        price_segment, time_numeric_segment, time_segment = get_segments(df, n, price_column, time_column)

        # Nájdeme vrchol tyče
        large_move_idx, up, before_segment, before_segment_time_numeric, before_segment_time = find_flag_transition_fib(
            price_segment,
            time_numeric_segment, time_segment)

        # Ak sme nenašli vrchol, tak sme nedetkovali vzor
        if large_move_idx is None or large_move_idx < n * 0.1:
            return {
                "pattern": "Flag",
                "detected": False,
                "return": 2,
            }

        flag_price = price_segment[large_move_idx]
        flag_time = time_segment[large_move_idx]

        # Určíme si segemtny pre vlajkovú časť vzoru (bez tyče a zvyšných dát)
        price_segment = price_segment[large_move_idx:]
        time_segment = time_segment[large_move_idx:]
        time_numeric_segment = time_numeric_segment[large_move_idx:]

        n = len(price_segment)

        # Nájdeme extrémy (maximá a minimá) pre vlajkovú časť vzoru
        peaks_idx, troughs_idx = find_extremes(price_segment, n, 2, 2, True, True, 0.4)

        if up:
            peaks_idx = np.insert(peaks_idx, 0, 0)
        else:
            troughs_idx = np.insert(troughs_idx, 0, 0)

        # Ak sme extrémy pre vlajkovú časť vzoru nenašli, nedetekovali sme vzor
        if peaks_idx is None or troughs_idx is None:
            return {
                "pattern": "Flag",
                "detected": False,
                "return": 3,
            }

        peaks = price_segment[peaks_idx]
        troughs = price_segment[troughs_idx]
        peak_numeric_times = time_numeric_segment[peaks_idx]
        trough_numeric_times = time_numeric_segment[troughs_idx]
        peak_times = time_segment[peaks_idx]
        trough_times = time_segment[troughs_idx]

        # Normalizujeme si dáta
        norm_peaks, norm_peak_numeric_times, norm_troughs, norm_trough_numeric_times = get_normalized_data(peaks,
                                                                                                           troughs,
                                                                                                           peak_numeric_times,
                                                                                                           trough_numeric_times)
        # Vypočítame sklon pre hornú a dolnú hranicu vlajkovej časti vzoru
        upper_slope = calculate_average_slope(norm_peaks, norm_peak_numeric_times)
        lower_slope = calculate_average_slope(norm_troughs, norm_trough_numeric_times)

        # Vypočítame si rozdiel sklonu medzi hornou a dolnou hranicou
        slope_diff = abs(upper_slope - lower_slope)

        # Ak je rozdiel sklonou priveľký, nedetkovali sme vzor
        if slope_diff > 0.5:
            return {
                "pattern": "Flag",
                "detected": False,
                "return": 4,
            }

        new_peaks, new_peak_times, new_peak_times_numeric = get_trend_line(peaks, peak_times, peak_numeric_times)
        new_troughs, new_trough_times, new_trough_times_numeric = get_trend_line(troughs, trough_times,
                                                                                 trough_numeric_times)

        pattern_type = IndicatorEnums.GLOBAL_UP.value if upper_slope < 0 else IndicatorEnums.GLOBAL_DOWN.value

        # Vrátenie výsledkov nájdeného vzoru
        return {
            "pattern": "Flag",
            "detected": True,
            "type": pattern_type,
            "upper_slope": upper_slope,
            "lower_slope": lower_slope,
            "flag_start": large_move_idx,
            "slope_diff": slope_diff,
            "price_column": price_column,
            "before_segment": before_segment,
            "before_segment_time_numeric": before_segment_time_numeric,
            "before_segment_time": before_segment_time,
            "flag": {
                "price": flag_price,
                "time": flag_time,
            },
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
            main_window.ax.scatter(result["peaks"]["time"], result["peaks"]["price"], color="red",
                                   label="Flag Peaks and Troughs",
                                   zorder=5)
            main_window.ax.scatter(result["troughs"]["time"], result["troughs"]["price"], color="red", zorder=5)

            min_time = df[result["price_column"]].min()
            max_time = df[result["price_column"]].max()

            # Vykreslíme začiatok vlajkovej časti vzoru zvislou čiarou
            main_window.ax.vlines(result["flag"]["time"], ymin=min_time, ymax=max_time, color="orange", linestyle="--",
                                  label="Flag Start", zorder=5)

            # Vykreslíme hornú a dolnú hranicu vlajkovej časti vzoru
            main_window.ax.plot([result["peaks"]["avg_time"][0], result["peaks"]["avg_time"][-1]],
                                [result["peaks"]["avg_price"][0], result["peaks"]["avg_price"][-1]],
                                color="red", label="Flag Upper Trend Line")
            main_window.ax.plot([result["troughs"]["avg_time"][0], result["troughs"]["avg_time"][-1]],
                                [result["troughs"]["avg_price"][0], result["troughs"]["avg_price"][-1]],
                                color="red", linestyle="dashed", label="Flag Lower Trend Line")

            # Vykreslíme trend tyčovej časti vzoru
            main_window.ax.plot([result["before_segment_time"][0], result["before_segment_time"][-1]],
                                [result["before_segment"][0], result["before_segment"][-1]],
                                color="orange", label="Flag pole")

            # vykreslíme predpokladaný trend po konci vlajkovej časti
            x1, x2 = result["before_segment_time_numeric"][0], result["before_segment_time_numeric"][-1]
            y1, y2 = result["before_segment"][0], result["before_segment"][-1]

            if result["peaks"]["time_numeric"][-1] > result["troughs"]["time_numeric"][-1]:
                flag_x = result["peaks"]["avg_time_numeric"][-1]
            else:
                flag_x = result["troughs"]["avg_time_numeric"][-1]

            flag_y = (result["peaks"]["avg_price"][-1] + result["troughs"]["avg_price"][-1]) / 2

            slope = (y2 - y1) / (x2 - x1)

            length = (x2 - x1)

            x2 = flag_x
            x3 = x2 + length
            y2 = flag_y
            y3 = slope * (x3 - x2) + y2

            x2 = df[get_time_column()].min() + pd.to_timedelta(x2, unit="s")
            x3 = df[get_time_column()].min() + pd.to_timedelta(x3, unit="s")

            main_window.ax.plot([x2, x3], [y2, y3], color="orange",
                                label="Extended Flag Trend Line")