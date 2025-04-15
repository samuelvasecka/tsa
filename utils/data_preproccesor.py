import pandas as pd
from data.data import set_data

# Metóda na detekciu časového stĺpca
def detect_time_column(df):
    for col in df.columns:
        try:

            # Skúška či vieme dáta konvertovať na datetime
            series = pd.to_datetime(df[col], errors='coerce')

            # Ak séria dát rastie, našli sme časový stĺpec
            if series.notna().sum() > len(series) * 0.8 and series.is_monotonic_increasing:
                return col
        except:
            pass

        try:
            # Skúška či vieme dáta konvertovať na čísla
            series = pd.to_numeric(df[col], errors='coerce')

            # Ak séria dát rastie, našli sme časový stĺpec
            if series.is_monotonic_increasing:
                return col
        except:
            pass
    return None

# Metóda na na nájdenie stĺpcov s hodnotami (musia obsahovať len číselné hodnoty)
def get_numeric_columns(df, time_col):
    for col in df.columns:
        if col == time_col:
            continue
        try_convert = pd.to_numeric(df[col], errors='coerce')
        if try_convert.notna().sum() == len(df[col]):
            df[col] = try_convert

    numeric_columns = [
        col for col in df.columns
        if col != time_col and pd.api.types.is_numeric_dtype(df[col])
    ]
    return numeric_columns

# Metóda na spracovanie dát
def process_data(file_path, header):

    # Načítame si data z daného súboru
    df = pd.read_csv(file_path, header=header)

    # Ak máme menej ako dva stĺpce
    if df.shape[1] < 2:

        # Pridáme virtuálny stĺpec s časom
        df.insert(0, '0', range(1, len(df) + 1))

        # Pokúsime sa nájsť stĺpce s hodnotam
        numeric_columns = get_numeric_columns(df, '0')

        # Ak sme stĺpce s hodnotami nenašli, súbor je nevalidný
        if not numeric_columns:
            return False, df, '0', None, True, numeric_columns

        # Ak sme stĺpce s hodnotami našli, uložíme si data
        set_data('0', df.columns[1], df[['0', df.columns[1]]])
        return True, df, '0', df.columns[1], True, numeric_columns

    # Pokúsime sa detekovať časový stĺpec
    time_col = detect_time_column(df)
    virtual_time_added = False

    # Ak časový stĺpec neexistuje
    if time_col is None:

        # Pridáme stĺpec s virtuálnym časom
        df.insert(0, '0', range(1, len(df) + 1))
        time_col = '0'
        virtual_time_added = True

    # Pokúsime sa nájsť stĺpce s hodnotam
    numeric_columns = get_numeric_columns(df, time_col)

    # Ak sme stĺpce s hodnotami nenašli, súbor je nevalidný
    if not numeric_columns:
        return False, df, time_col, None, virtual_time_added, numeric_columns

    # Určíme prvý nájdený stĺpec s hodnotami
    value_col = None
    for col in numeric_columns:
        if col != time_col:
            value_col = col
            break

    # Uložíme si data
    set_data(time_col, value_col, df[[time_col, value_col]])
    return True, df, time_col, value_col, virtual_time_added, numeric_columns
