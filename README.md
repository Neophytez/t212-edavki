# Trading212 CSV to eDavki XML (Doh-KDVP)

Skripta za pretvorbo Trading212 CSV datotek v eDavki XML pripomore k hitrejšemu in bolj organiziranemu ustvarjanju XML datotek za oddajo davčne napovedi.

## Izjava o omejitvi odgovornosti

**OPOZORILO:**  
Ta skripta je zgolj pripomoček, ki poenostavi generiranje XML datoteke za oddajo davčne napovedi. Pred oddajo XML datoteke **obvezno ročno preveri** vse vnose. Z uporabo skripte sprejemaš popolno odgovornost za morebitne napake, izgube ali škodo, ki bi nastale zaradi nepravilno generiranih podatkov. Avtor skripte ne sprejema odgovornosti za kakršnekoli posledice.

## Posodobitve
- **11.01.2026:**  
  - Dodana podpora za **Stop sell**.
  - Dodana opcija `--fix-rounding-error`
  - Popravljeno formatiranje decimal (skladno z eDavki – max. 8 decimalk)
- **10.01.2026:**  
  - Posodobljena tečajnica USD/EUR 1999-2025.
- **28.02.2025:**
  - Dodana validacija za starejše CSV headerje (credits: [trideetztz](https://github.com/trideetztz))
- **15.01.2025:**  
  - Dinamična validacija headerja.
  - Popravek XML strukture.
- **11.01.2025:**  
  - Popravek za nov header.
- **06.01.2025:**  
  - Posodobljena tečajnica USD/EUR 1999-2024.
- **13.10.2023:**  
  - Popravek za nov header.
- **10.02.2023:**  
  - Popravek za nov header.
  - Uporabljena tečajnica [ECB Europa](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml) namesto [Yahoo Finance](https://finance.yahoo.com/quote/EUR%3DX/history?p=EUR%3DX).
- **17.02.2023:**  
  - Ignoriranje tickerjev brez odsvojitve (prodaje: market sell in limit sell).
- **26.02.2023:**  
  - Popravek za nov format.
  - Dodani informativni izpisi.

## Kako deluje skripta?

1. **Uvoz CSV datotek**  
   Skripta prebere vse CSV datoteke iz mape `input`.
   
2. **Prepoznava osnovne valute**  
   Iz glave CSV datoteke se zazna, ali je “base currency” **EUR** ali **USD**.

3. **Filtriranje transakcij**  
   Upoštevajo se samo naslednje vrste:
   - **market buy**
   - **market sell**
   - **limit buy**
   - **limit sell**  
   - **stop sell**  
   
   Ostale vrstice (dividende, obresti ipd.) se ignorirajo.

4. **Pretvorba cen v EUR**  
   - Če je osnovna valuta **EUR**, se cena uporabi neposredno.
   - Če je osnovna valuta **USD**, se uporabi dnevni tečaj iz mape `rate` (tečajnica iz [ECB Europa](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml)).
   
5. **Generiranje XML**  
   - Za vsak ticker, ki ima vsaj eno prodajo, se ustvari KDVPItem.
   - XML je pripravljen za uvoz v eDavki → Doh-KDVP → Uvoz popisnih listov.

## Decimalke in zaokroževanje (pomembno)

Trading212 lahko izvozi količine z **več kot 8 decimalkami**, eDavki pa dovoljuje **največ 8**.

Če se vsaka transakcija zaokroži ločeno, lahko eDavki po seštevku pokaže zelo majhen presežek, npr.:
```
-0.00000001
```

To **ni dejanska negativna zaloga**, ampak posledica zaokroževanja.

### Opcija --fix-rounding-error

Če skripto zaženeš z:
```
python main.py --fix-rounding-error
```

skripta:
- zazna to razliko po posameznem tickerju
- popravi eno samo transakcijo za najmanjši možni korak (0.00000001)
- vedno izpiše, kaj je bilo popravljeno

Primer izpisa:
```
[rounding-fix] AAPL: applied -0.00000001 via Market sell on 2024-06-12
```

Privzeto je ta opcija **izklopljena**.

## Podprte funkcionalnosti

- **Podprte transakcije**  
  - market sell
  - market buy
  - limit sell
  - limit buy
  - stop sell
- **Pretvorba valut**  
  - EUR → EUR
  - USD → EUR (tečajnica iz [ECB Europa](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml))
- **Ignoriranje**  
  - tickerjev brez prodaje
  - dividend, obresti in drugih vrst transakcij
- **XML**  
  - format skladen z **Doh-KDVP** (8 decimalk, brez znanstvenega zapisa)

## Navodila za uporabo

1. **Namesti Python**  
   - Prenesi [Python](https://www.python.org/downloads/windows/) (sledi [navodilom za namestitev](https://realpython.com/installing-python/))
   - Med namestitvijo obkljukaj *"Add Python to PATH"*

2. **Prenesi repozitorij**  
   - Klikni **Code** → **Download ZIP**
   - Razširi arhiv

3. **Pripravi CSV datoteke**  
   - Iz Trading212 izvozi CSV datoteke (označi vse 4 opcije: Orders, Dividends, Transactions, Interest)
   - Kopiraj CSV datoteke v mapo `t212-edavki-main/input` (skripta podpira več CSV datotek hkrati)

4. **Uredi osebne podatke**
   - Odpri `main.py`
   - Na vrhu skripte izpolni razdelek **USER SETTINGS**

5. **Zaženi skripto**  
   - Odpri mapo `t212-edavki-main`
   - Pritisni kombinacijo tipk **ALT + F** (odpre se meni), nato **S** (odpre se podmeni) in nato **R** (odpre se PowerShell).
   - Osnovni zagon:

     ```
     python main.py
     ```
     Z vključenim popravkom za zaokroževanje:
     ```
     python main.py --fix-rounding-error
     ```

6. **Rezultat** 
- Če se izpiše sporočilo:
  ```
  Your XML file is located inside output folder.
  ```
  si uspešno ustvaril XML datoteko, pripravljeno na uvoz v eDavki.
- XML datoteka se ustvari v mapi `output`
- Datoteko uvoziš v eDavki (Doh-KDVP)
- Če se pojavi kakšna napaka, preveri sporočila v terminalu.

## Podpri delo

Če ti je skripta prihranila čas in trud, mi lahko častiš pivo.

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=HP6Z34ASADB4Y)

## Prišlo do težav?

Če skripta ne deluje:
- odpri **New issue** na GitHubu
- priloži izpis napake in opis problema

Na e-pošto ne odgovarjam, zato prosim, da težave prijaviš preko GitHub issue sistema.



