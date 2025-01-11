# Trading212 CSV to eDavki XML

Skripta za pretvorbo Trading212 CSV datotek v eDavki XML pripomore k hitrejšemu in bolj organiziranemu ustvarjanju XML datotek za oddajo davčne napovedi.

## Izjava o omejitvi odgovornosti

**OPOZORILO:**  
Ta skripta je zgolj pripomoček, ki poenostavi generiranje XML datoteke za oddajo davčne napovedi. Pred oddajo XML datoteke **obvezno ročno preveri** vse vnose. Z uporabo skripte sprejemaš popolno odgovornost za morebitne napake, izgube ali škodo, ki bi nastale zaradi nepravilno generiranih podatkov. Avtor skripte ne sprejema odgovornosti za kakršnekoli posledice.

## Posodobitve

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

1. **Uvoz CSV datotek:**  
   Skripta prebere vse vrstice CSV datotek, pridobljenih iz Trading212.
   
2. **Določitev osnovne valute:**  
   Na podlagi glave CSV datoteke skripta prepozna "base" valuto (EUR ali USD).

3. **Identifikacija transakcij:**  
   Za vsako vrstico preveri, ali gre za eno od naslednjih vrstic:
   - **market buy**
   - **market sell**
   - **limit buy**
   - **limit sell**  
   Vrstice, ki ne ustrezajo tem pogojem, se ignorirajo.

4. **Pretvorba valut:**  
   - Če je Trading212 račun v osnovni valuti **EUR**, je pretvorba preprosta.
   - Če je osnovna valuta **USD**, skripta uporabi dnevne tečaje iz datoteke v mapi `rate` (tečajnica iz [ECB Europa](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml)). Najprej se cena pretvori v USD, nato pa v EUR.
   
5. **Generiranje XML:**  
   Na koncu se iz dobljenih podatkov ustvari XML datoteka, pripravljena za uvoz v nov Doh-KDVP dokument ("Uvoz popisnih listov") v eDavkih.

## Podprte funkcionalnosti

- **Podprte transakcije:**  
  - *market sell*, *market buy*, *limit sell*, *limit buy*
- **Pretvorba valut:**  
  - Pretvorba v osnovno valuto (EUR).
  - Pretvorba iz USD v EUR (uporabljena tečajnica iz [ECB Europa](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml)).
- **Ignoriranje:**  
  - Tickerji brez odsvojitve (prodaje: *market sell* in *limit sell*).
- **Opombe:**  
  - Dividende in druge vrste transakcij se ne upoštevajo.

## Navodila za uporabo

1. **Namestitev Python-a:**  
   Pred zagonom skripte naloži [Python](https://www.python.org/downloads/windows/) (sledi [navodilom za namestitev](https://realpython.com/installing-python/)).

2. **Prenos repozitorija:**  
   - Klikni gumb **"Code"** in izberi **"Download ZIP"**.
   - Razširi arhivsko datoteko in se prestavi v mapo `t212-edavki-main`.

3. **Priprava CSV datotek:**  
   - Iz Trading212 izvozi CSV datoteke.
   - Kopiraj jih v mapo `t212-edavki-main/input` (skripta podpira več CSV datotek hkrati).

4. **Zagon skripte:**  
   - Odpri mapo `t212-edavki-main`.
   - Pritisni kombinacijo tipk **ALT + F** (odpre se meni), nato **S** (odpre se podmeni) in nato **R** (odpre se PowerShell).
   - Poženi skripto z ukazom:

     ```bash
     python main.py
     ```

5. **Preverjanje rezultata:** 
 
Če se izpiše sporočilo: "Your XML file is located inside output folder.", si uspešno ustvaril XML datoteko, pripravljeno na uvoz v eDavki. Če se pojavi kakšna napaka, preveri sporočila v terminalu.

## Podpri delo

Če ti skripta prihrani čas in trud, mi lahko častiš pivo.
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=HP6Z34ASADB4Y)

## Prišlo do težav?

Če skripta ne deluje, odpri **"New issue"** (klikni na zavihek **"Issues"** in nato zeleni gumb desno). Na e-pošto ne odgovarjam, zato prosim, da težave prijaviš preko GitHub issue sistema.
