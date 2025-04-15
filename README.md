# Vitajte na projekte TSA (*Time Series Analyser*)

Tento projekt je zameraný na detekciu technických ukazovateľov v časových radoch a následnú predikciu budúceho smeru dát - *trendu*. Viac o používaní si môžete prečítať v časti *Používteľská príručka*.

### Spustenie projektu

Projekt sa spúšťa cez hlavný súbor `app.py`

### Spustenie skriptu na porovnanie geometrikého algoritmu a ML

Skript sa spúšťa cez súbor `/scripts/metrics.py`

### Štruktúra projektu

Projekt je rozdelený do viacero priečinkov, ktoré sú zodpovedné za konkrétne úlohy:

1. **Gui** - obsahuje súbory zodpovedné za používateľské rozhranie a vykreslovanie grafov.
1. **Data** - obsahuje súbor, ktorý popisuje ako sú štruktúrované dáta, s ktorými projekt pracuje a sú zdieľané naprieš všetkými technickými ukazovateľmi. Okrem toho je tu aj súbor `example.csv`, pomocou ktorého je možné aplikáciu testovať.
1. **Utils** - obsahuje súbor zodpovedný za prvotné spracovanie datového CSV súboru a taktiež jeho validáciu.
1. **Indicators** - tento priečinok obsahuje inteface pre technické indikátory a aj implementáciu konkrétnych ukazovateľov, konkrétne:
   1. *Trojuholníkový vzor*
   1. *Vlajkový vzor*
   1. *Vzor Elliottových vĺn*
   1. *Trojuholníkový vzor pomocou ML*
   
    Aplíkacia zároveň funguje tak, že načítava všetky dostupné ukazovateľe v tomto priečinku, preto ak doplníme nový indikátor, ktorý je naimplementovaný správne, bude v aplikácii priamo dostupný.
1. **Models** - obsahuje natrénované modely na detekciu vzorov.
1. **Scripts** - obsahuje scripty na testovanie algoritmov na detekciu vzorov. Porovnanie detekcie trojuholníkového vzoru pomocou geometrického algoritmu a ML - dostaneme výsledky na základe rôznych metrík ako:
   1. *Precision*
   1. *Recall*
   1. *F1 score*
   1. *ROC krivka a AUC*

    Pričom výsledky sa nám vypíšu v konzole a samotná krivka sa zobrazí v grafe.
1. **Ostatné súbory** - tu patrí hlavný súbor na spúšťanie `app.py` a `README.md`

### Používateľská príručka

1. Na prvej obrazovke si používateľ nahrá súbor, ktorý chce spracovať. K dispozícii je prechádzanie lokálnych súborov, ale aj *drag and drop* funkcionalita, na pohodlnejšie fungovanie. Okrem toho je tu stále možnosť si vybrať testové data, v prípade, že používateľ sa chce s aplikáciou zoznámiť a nemá iné data. Aplikácia podporuje prácu so súbormi s koncovkou `.csv`.
    <br/><br/>
    ![img.png](readme_images/img.png)
    <br/><br/>
1. Po nahraní súboru sa používateľovi zobrazí obrazovka, kde vidí náhľad dát v súbore (prvých 5 riadkov). Zároveň prebehne aj validácia súboru a pokiaľ by bol súbor nesprávny, používateľ bude informovaný. Na tejto obrazovke je možné, pokiaľ je v súbore viacero stĺpcov, vybrať, ktorý z nich budeme analyzovať. Taktiež si vieme nastaviť, či priložený súbor obsahuje hlavičku alebo nie. Zaujímavá je aj funkcia, ktorá zabezpečí, že pokiaľ bol nahraný súbor bez stĺpca s časovými údajmi, takýto stĺpec automaticky vytvoríme.
    <br/><br/>
    ![img_1.png](readme_images/img_1.png)
    <br/><br/>
    ![img_2.png](readme_images/img_2.png)
    <br/><br/>
1. Na ďalšej obrazovke používateľ môže vidieť svoje data zobrazené v grafe. Okrem toho má možnosť pustiť tzv. *testový mód*, ktorý mu dovolí si rozdeliť dataset na dve časti:
    1. Časť určenú na analýzu
    1. Časť určenú na verifikáciu 

    Toto je veľmi vhodné pokiaľ chceme overiť schopnosť algoritmov nájsť vybrané technické ukazovateľe a zároveň aj presnosť odhadov.
    <br/><br/>
    ![img_3.png](readme_images/img_3.png)
    <br/><br/>
1. Po prechode do ďalšieho okna používateľ dostane na výber zoznam dostupných technických ukazovateľov, ktoré chce v dátach vyhľadať. Môže si tak buď zvoliť konkrétne alebo všetky ukazovatele.
    <br/><br/>
    ![img_4.png](readme_images/img_4.png)
    <br/><br/>
1. Finálna obrazovka slúži na zobrazenie výsledkov nájdených technických ukazovateľov, ktoré sa zobrazia v grafe. Používateľ si môže zvoliť, ktoré výsledky sa mu zobrazia a ktoré nie.
    <br/><br/>
    ![img_5.png](readme_images/img_5.png)
    <br/><br/>

### Používateľská príručka pre skript metrics

Fungovanie tohto skriptu je jednoduché a priblížime si ho vo viacerých krokorch:

1. Ak v priečinku `/models` nemáme potrebný natrénovaný model, spustí sa tréning na 10000 vygenerovaných tréningových dátach,
2. Násedne si vygenerujeme 100 testových dát.
3. Tieto dáta cyklicky prejdeme a nad každým z nich spustíme detekciu pomocou geometrického algoritmua aj pomocou natrénovaného modelu.
4. V prípade, že detekujeme vzor správne zvýši sa nám počet *True positives*
5. V prípade, že sme vzor nedetkovali správne, naskytnú sa nám dve možnosti:
    1. Detekovali sme vzor správne, pretože v dátach, ktoré nemali vzor obsahovať sa vzor naozaj našiel
    2. Vzor sme nedetekovali a ide teda o chybu
6. Na overenie toho, ktorý z dvoch scenárov sa nám vyskytol, sa nám data zobrazia v grafe a musíme manuálne označiť, či šlo o chybu alebo správnu detekciu.
7. Po skončení cyklu sa nám vypočítajú všetky potrebné metriky a vypíšu sa do konzoly a taktiež sa nám zobrazia grafy zobrazujúce ROC krivku.


