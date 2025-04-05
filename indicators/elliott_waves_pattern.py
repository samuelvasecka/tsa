import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from indicators.technical_indicator import TechnicalIndicator, check_columns, create_time_numeric_column, get_segments, \
    fibonacci_sequence_up_to, IndicatorEnums, get_trend_line

# Metóda na filtrovanie extrémov. Odfiltruje menšie pohyby aby sme dostali zig-zag vzor medzi maximami a minimami
def filter_extremes(peaks_idx, troughs_idx, price_segment):

    # Spojíme maximá a minimá
    all_extremes = sorted(list(peaks_idx) + list(troughs_idx))
    filtered_extremes = []

    # Prejdeme celým listom extrémov a odfiltrujeme menšie pohyby aby sme dostali zig-zag vzor a teda striedanie maxím a miním
    for i in range(len(all_extremes)):
        if i > 0 and ((all_extremes[i] in peaks_idx) == (all_extremes[i - 1] in peaks_idx) or
                      (all_extremes[i] in troughs_idx) == (all_extremes[i - 1] in troughs_idx)):
            if (all_extremes[i] in peaks_idx and price_segment[all_extremes[i]] > price_segment[all_extremes[i - 1]]) or \
                    (all_extremes[i] in troughs_idx and price_segment[all_extremes[i]] < price_segment[
                        all_extremes[i - 1]]):
                filtered_extremes.pop()
                filtered_extremes.append(all_extremes[i])
        else:
            filtered_extremes.append(all_extremes[i])

    # Nastavíme odfiltrované maximá
    filtered_peaks_idx = [idx for idx in filtered_extremes if idx in peaks_idx]

    # Nastavíme odfiltrované minimáa
    filtered_troughs_idx = [idx for idx in filtered_extremes if idx in troughs_idx]

    return filtered_peaks_idx, filtered_troughs_idx

# Metóda na validovanie vlnového vzoru
def validate_wave_pattern(wave_points):

    # Ak máme menej ako 6 bodov (5 vĺn), nedetkovali sme vzor
    if len(wave_points) < 6:
        return False

    # Určíme či sú splnené podmienky pre stúapnie prvých piatich vĺn
    increasing = wave_points[0][1] < wave_points[2][1] < wave_points[1][1] < wave_points[4][1] < wave_points[3][1] < \
                 wave_points[5][1]

    # Určíme či sú splnené podmienky pre klesanie prvých piatich vĺn
    # Nie je pravidlo, že pokiaľ nie sú splnené podmienky stúpania tak ide o klesanie
    decreasing = wave_points[0][1] > wave_points[2][1] > wave_points[1][1] > wave_points[4][1] > wave_points[3][1] > \
                 wave_points[5][1]

    # Ak máme 7 bodov (6 vĺn)
    if len(wave_points) == 7:

        # Určíme či sú splnené podmienky pre klesanie korekčných vĺn
        second_part_decreasing = increasing and wave_points[5][1] > wave_points[6][1]

        # Určíme či sú splnené podmienky pre stúpanie korekčných vĺn
        second_part_increasing = decreasing and wave_points[5][1] < wave_points[6][1]
        return (increasing and second_part_decreasing) or (decreasing and second_part_increasing)

    # Ak máme 8 bodov (7 vĺn)
    elif len(wave_points) == 8:

        # Určíme či sú splnené podmienky pre klesanie korekčných vĺn
        second_part_decreasing = increasing and wave_points[5][1] > wave_points[7][1] > wave_points[6][1]

        # Určíme či sú splnené podmienky pre stúpanie korekčných vĺn
        second_part_increasing = decreasing and wave_points[5][1] < wave_points[7][1] < wave_points[6][1]
        return (increasing and second_part_decreasing) or (decreasing and second_part_increasing)
    return increasing or decreasing

# Metóda na detekovanie Elliottových vĺn
def detect_elliott_waves(price_segment, time_numeric_segment):
    fib_numbers = fibonacci_sequence_up_to(int(len(price_segment) * 0.5))
    while fib_numbers and fib_numbers[-1] < 5:
        fib_numbers.pop()

    # Cyklus pre nastavenie veľkosti okna pre hľadanie maxím a miním pomocou Fibonačiho postupnosti
    for order_value in reversed(fib_numbers):
        data_for_maxima = price_segment.copy()
        data_for_minima = price_segment.copy()

        new_maxima_values = data_for_maxima[-order_value:] - np.arange(1, order_value + 1)
        new_minima_values = data_for_minima[-order_value:] + np.arange(1, order_value + 1)

        # Rozšírime data na konci o ďalšie falošné body, kvôi detekcii extrémov aj na konci dát
        data_for_maxima = np.concatenate([data_for_maxima, new_maxima_values])
        data_for_minima = np.concatenate([data_for_minima, new_minima_values])

        # Nájdené maximá a minimá
        peaks_idx = argrelextrema(data_for_maxima, np.greater, order=order_value)[0]
        troughs_idx = argrelextrema(data_for_minima, np.less, order=order_value)[0]

        # Odfiltrujeme menšie pohyby aby sme dostali zig-zag vzor
        filtered_peaks_idx, filtered_troughs_idx = filter_extremes(peaks_idx, troughs_idx, price_segment)
        filtered_extremes = sorted(filtered_peaks_idx + filtered_troughs_idx)

        # Cyklom skúšame, či zavlidujeme vzor pre posledných num_points bodov (num_points - 1 vĺn)
        for num_points in [8, 7, 6]:
            if len(filtered_extremes) >= num_points:
                wave_points = [(idx, price_segment[idx], time_numeric_segment[idx]) for idx in
                               filtered_extremes[-num_points:]]

                filtered_extremes = filtered_extremes[-num_points:]
                filtered_peaks_idx = [idx for idx in filtered_peaks_idx if idx in set(filtered_extremes)]
                filtered_troughs_idx = [idx for idx in filtered_troughs_idx if idx in set(filtered_extremes)]

                # Validácia vzoru
                if validate_wave_pattern(wave_points):
                    trend_type = IndicatorEnums.GLOBAL_UP.value if wave_points[1][1] < wave_points[3][
                        1] and 6 > len(wave_points) > 8 else IndicatorEnums.GLOBAL_DOWN.value

                    local_trend = IndicatorEnums.LOCAL_DOWN.value if wave_points[-2][1] < wave_points[-1][
                        1] else IndicatorEnums.LOCAL_UP.value
                    return trend_type, local_trend, filtered_peaks_idx[-num_points:], filtered_troughs_idx[
                                                                                      -num_points:], wave_points, filtered_extremes[
                                                                                                                  -num_points:]
    return None, None, None, None, None, None

# Trieda pre technický indikátor Elliottove vlny
class ElliottWavesPattern(TechnicalIndicator):

    # Metóda na detekciu vzoru
    def detect(self, df: pd.DataFrame, price_column: str = "0", time_column: str = "1"):

        # Kontrola, či máme všetky potrebné stĺpce
        if not check_columns(df, price_column, time_column):
            return {"pattern": "Elliott Waves", "detected": False, "return": 1}

        # Pokiaľ máme časový údaj v dátumovom formáte, skonvertujeme ho na čoasový údaj
        df = create_time_numeric_column(df, time_column)
        n = len(df)

        # Určenie segmentov dát, nad ktorými budeme vzor hľadať
        price_segment, time_numeric_segment, time_segment = get_segments(df, n, price_column, time_column)

        # Detekujeme Elliottove vlny
        trend_type, local_trend, filtered_peaks_idx, filtered_troughs_idx, wave_points, filtered_extremes = detect_elliott_waves(
            price_segment, time_numeric_segment)

        # Ak sme nenašli trend, nedetekovali sme vzor
        if trend_type is None:
            return {"pattern": "Elliott Waves", "detected": False, "return": 2}

        peaks = price_segment[filtered_peaks_idx]
        troughs = price_segment[filtered_troughs_idx]
        peak_numeric_times = time_numeric_segment[filtered_peaks_idx]
        trough_numeric_times = time_numeric_segment[filtered_troughs_idx]
        peak_times = time_segment[filtered_peaks_idx]
        trough_times = time_segment[filtered_troughs_idx]
        waves = price_segment[filtered_extremes]
        wave_times = time_segment[filtered_extremes]

        # Vrátenie výsledkov nájdeného vzoru
        return {
            "pattern": "Elliott Waves",
            "detected": True,
            "waves": {"time": wave_times, "price": waves},
            "peaks": {"time_numeric": peak_numeric_times, "time": peak_times, "price": peaks},
            "troughs": {"time_numeric": trough_numeric_times, "time": trough_times, "price": troughs},
            "trend_type": trend_type,
            "local_trend": local_trend,
            "df": df
        }

    # Metóda na vykreslenie nájdených výsledkov vzoru
    def show(self, result, main_window, df):

        # Ak sme vzor našli
        if result["detected"]:

            # Vykreslíme maximá a minimá
            main_window.ax.scatter(result["peaks"]["time"], result["peaks"]["price"], color="blue",
                                   label="Elliott Waves Peaks and Troughs",
                                   zorder=5)
            main_window.ax.scatter(result["troughs"]["time"], result["troughs"]["price"], color="blue", zorder=5)

            split_index = 5

            # Vykreslenie prvých piatich Elliottových vĺn
            main_window.ax.plot(result["waves"]["time"][:split_index + 1], result["waves"]["price"][:split_index + 1],
                                linestyle='-', color='blue', label="Elliott Impulse Waves ")

            # Vykreslenie odhadovaného trendu po počte 6, 7 a 8 bodov (5, 6 a 7 vĺn)
            if len(result["waves"]["time"]) == 6:
                x = result["waves"]["time"][-1] + (result["waves"]["time"][-1] - result["waves"]["time"][-2])
                main_window.ax.plot([result["waves"]["time"][-1], x],
                                    [result["waves"]["price"][-1], result["waves"]["price"][-2]], color="pink",
                                    label="Extended Elliott Waves Trend Line", linestyle='dashed')
            if len(result["waves"]["time"]) == 7:
                x = result["waves"]["time"][-1] + ((result["waves"]["time"][-1] - result["waves"]["time"][-2]) / 2)
                y = result["waves"]["price"][-1] - ((result["waves"]["price"][-1] - result["waves"]["price"][-2]) / 2)

                main_window.ax.plot([result["waves"]["time"][-1], x],
                                    [result["waves"]["price"][-1], y], color="pink",
                                    label="Extended Elliott Waves Trend Line", linestyle='dashed')
            if len(result["waves"]["time"]) == 8:

                x = result["waves"]["time"][-1]
                y = result["waves"]["price"][-1]

                x2 = result["waves"]["time"][-2] + (x - result["waves"]["time"][-3])
                y2 = result["waves"]["price"][-2] + (y - result["waves"]["price"][-3])

                main_window.ax.plot([x, x2],
                                    [y, y2], color="pink",
                                    label="Extended Elliott Waves Trend Line", linestyle='dashed')

            # Vykreslenie korektývnych Elliottových vĺn
            if split_index + 1 < len(result["waves"]["time"]):
                main_window.ax.plot(result["waves"]["time"][split_index:], result["waves"]["price"][split_index:],
                                    color='pink', label="Elliott Corrective Waves ")
