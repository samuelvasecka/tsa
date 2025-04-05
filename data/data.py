# Štruktúra dát využívaná naprieč celou aplikáciou - najmä v techických ukazovateľoch
processed_data = {
    "time_column": None,
    "value_column": None,
    "data": None,
    "max_item": None,
    "indicators": [],
    "results": []
}

# Setter na nastavenie názvu časového a hodnotového stĺpca a datasetu
def set_data(time_col, value_col, df):
    global processed_data
    processed_data["time_column"] = time_col
    processed_data["value_column"] = value_col
    processed_data["data"] = df

# Setter na nastavenie pola ukazovateľov, ktoré sa budeme snažiť detekovať
def set_indicators(indicators):
    global processed_data
    processed_data["indicators"] = indicators

# Getter na pole ukazovateľov, ktoré sa budeme snažiť detekovať
def get_indicators():
    return processed_data["indicators"]

# Setter na nastavenie pola nájdených výsledkov jednotlivých ukazovateľov
def set_results(results):
    global processed_data
    processed_data["results"] = results

# Getter na pole nájdených výsledkov jednotlivých ukazovateľov
def get_results():
    return processed_data["results"]

# Setter na nastavenie maximálneho bodu, ktorý chceme spracovať v testovom móde
def set_max_item(max_item):
    global processed_data
    if max_item is None:
        processed_data["max_item"] = None
    else:
        processed_data["max_item"] = int(max_item)

# Getter na maximálny bod, ktorý chceme spracovať v testovom móde
def get_max_item():
    return processed_data["max_item"]

# Getter na dataset
def get_data():
    return processed_data

# Getter na názov časového stĺpca
def get_time_column():
    return processed_data["time_column"]
