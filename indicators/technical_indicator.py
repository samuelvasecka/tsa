from abc import abstractmethod, ABC
from enum import Enum
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from data.data import get_max_item

# Enum trieda na zjednotenie smeru trendov v nájdených ukazovateľoch
class IndicatorEnums(Enum):
    ABSTRACT_INDICATOR = "technical_indicator.py"
    GLOBAL_UP = "Up"
    GLOBAL_DOWN = "Down"
    GLOBAL_UNCERTAIN = "Uncertain"
    LOCAL_UP = "Local Up"
    LOCAL_DOWN = "Local Down"
    LOCAL_UNCERTAIN = "Local Uncertain"

# Metóda na kontrolu, či máme v dátach časový a hodnotový stĺpec
def check_columns(df: pd.DataFrame, price_column: str, time_column: str):
    if price_column not in df.columns or time_column not in df.columns:
        return False
    return True

# Ak je časový stĺpec v dátumovom formáte, konvertujeme ho na číselné údaje
def create_time_numeric_column(df: pd.DataFrame, time_column: str):
    df = df.copy()

    if "time_numeric" not in df.columns:

        # Máme dátumový formát
        if isinstance(df[time_column].iloc[0], pd.Timestamp):
            datetime_column = pd.to_datetime(df[time_column])

            # Číselné hodnoty budú rozdiely medzi dňami v sekundách
            df["time_numeric"] = (datetime_column - datetime_column.min()).dt.total_seconds()
        else:
            df["time_numeric"] = df[time_column]
    return get_test_data(df)

# Pokiaľ je zapnutý testivý réžim, ako dáta nastavíme len časť určenú na analýzu
def get_test_data(df):
    max_item = get_max_item()

    if max_item is not None:
        return df.head(max_item).copy()
    return df

# Metóda na určenie segmentov dát, nad ktorými budeme vzor hľadať
def get_segments(df: pd.DataFrame, n: int, price_column: str, time_column: str):
    df_segment = df.iloc[-n:]

    time_numeric_segment = df_segment["time_numeric"].values
    price_segment = df_segment[price_column].values
    time_segment = df_segment[time_column].values

    return price_segment, time_numeric_segment, time_segment

# Metóda na výpočet priemerného sklonu bodov
def calculate_average_slope(values, times):
    slopes = (np.diff(values) / np.diff(times))
    return np.mean(slopes) if len(slopes) > 0 else 0

# Metóda na výpočet trendovej čiary nad množinou bodov
def get_trend_line(values, times, times_numeric):
    if len(values) < 2:
        return values, times, times_numeric

    a = np.vstack([times_numeric, np.ones(len(times_numeric))]).T
    m, b = np.linalg.lstsq(a, values, rcond=None)[0]

    x_min, x_max = times_numeric[0], times_numeric[-1]
    y_min, y_max = m * x_min + b, m * x_max + b

    return np.array([y_min, y_max]), np.array([times[0], times[-1]]), np.array([times_numeric[0], times_numeric[-1]])

# Metóda na generovanie Fibonačiho postupnosti po číslo n
def fibonacci_sequence_up_to(n):
    n = max(21, n)
    fib_numbers = [1, 1]
    while fib_numbers[-1] <= n:
        fib_numbers.append(fib_numbers[-1] + fib_numbers[-2])

    if fib_numbers[-1] > n:
        fib_numbers.pop()

    return fib_numbers[::-1]

# Metóda na hľadanie extrémov, pričom vieme určiť minimálny počet maxím a miním a či chcem hľadať tieto extrémy na konci alebo na začiatku dát
def find_extremes(price_segment, n: int, min_peaks_count: int, min_troughs_count: int, start=False, end=False, percent=0.1):
    peaks_idx = None
    troughs_idx = None
    segment_len = len(price_segment)

    fib_numbers = fibonacci_sequence_up_to(int(n * 0.5))

    # Cyklus pre nastavenie veľkosti okna pre hľadanie maxím a miním pomocou Fibonačiho postupnosti (zostupne)
    for order_value in fib_numbers:
        order_value = max(1, order_value)

        peaks_idx = argrelextrema(price_segment, np.greater, order=order_value)[0]
        troughs_idx = argrelextrema(price_segment, np.less, order=order_value)[0]

        if len(peaks_idx) >= min_peaks_count and len(troughs_idx) >= min_troughs_count:

            if start and end:
                valid_range = np.concatenate([np.arange(0, int(segment_len * percent)),
                                              np.arange(int(segment_len * (1 - percent)), segment_len)])
            elif start:
                valid_range = np.arange(0, int(segment_len * percent))
            elif end:
                valid_range = np.arange(int(segment_len * (1 - percent)), segment_len)
            else:
                valid_range = np.arange(segment_len)

            # Kontrola či sa extrémy nachádzajú v x percentách dát na začiatku, resp. na konci dát
            peaks_idx_in_range = peaks_idx[np.isin(peaks_idx, valid_range)]
            troughs_idx_in_range = troughs_idx[np.isin(troughs_idx, valid_range)]

            if len(peaks_idx_in_range) >= min_peaks_count and len(troughs_idx_in_range) >= min_troughs_count:
                break

    if peaks_idx is None or troughs_idx is None or len(peaks_idx) < min_peaks_count or len(
            troughs_idx) < min_troughs_count:
        return None, None

    return peaks_idx, troughs_idx

# Metóda na normalizáciu dát
def get_normalized_data(peaks, troughs, peak_times, trough_times):

    time_min = min(min(peak_times), min(trough_times))
    time_max = max(max(peak_times), max(trough_times))
    normalized_peak_times = [(t - time_min) / (time_max - time_min) for t in peak_times]
    normalized_trough_times = [(t - time_min) / (time_max - time_min) for t in trough_times]

    price_min = min(min(peaks), min(troughs))
    price_max = max(max(peaks), max(troughs))
    normalized_peaks = [(p - price_min) / (price_max - price_min) for p in peaks]
    normalized_troughs = [(p - price_min) / (price_max - price_min) for p in troughs]

    return normalized_peaks, normalized_peak_times, normalized_troughs, normalized_trough_times

# Abstraktná trieda slúžiaca ako interface pre technické indikátory
class TechnicalIndicator(ABC):

    # Metóda na detekciu vzoru
    @abstractmethod
    def detect(self, df: pd.DataFrame, price_column: str, time_column: str):
        pass

    # Metóda na vykreslenie nájdených výsledkov vzoru
    @abstractmethod
    def show(self, result, main_window, df):
        pass

