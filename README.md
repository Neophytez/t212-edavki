# Trading212 CSV to eDavki XML

### Izjava o omejitvi odgovornosti
Skripta je pripomoček, ki nam pomaga pri generiranju XML datoteke za oddajo davčne napovedi. Po uvozu XML datoteke je potrebno ročno pregledati vse vnose. Z uporabo skripte sprejemaš vso odgovornost za kakršno koli izgubo ali škodo, ki bi lahko nastala zaradi morebitnih napak pri generaciji XML datoteke. Avtor te skripte ne sprejema nikakršne odgovornosti.

---

### Posodobitve
#### 13.10.2023:
- popravek za nov header
#### 10.02.2023:
- popravek za nov header
- uporabljena tečajnica [ECB Europa](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml) namesto [Yahoo Finance](https://finance.yahoo.com/quote/EUR%3DX/history?p=EUR%3DX)
#### 17.02.2023:
- ignoriranje tickerjev brez odsvojitve (prodaje: market sell in limit sell)
#### 26.02.2023:
- popravek za nov format
- dodani informativni izpisi
---

### Kako deluje skripta?
Skripta prebere vse vrstice CSV datotek. Na podlagi glave prepozna, kakšna je "base" valuta (EUR, USD). Za vsako vrstico preveri, ali je: market buy, market sell, limit buy ali limit sell. V kolikor ni nič od tega, vrstico ignorira. Če imamo T212 račun v "base" valuti EUR, je konverzija zelo preprosta, v primeru, da je "base" valuta USD, si skripta pomaga s podatki iz ECB Europe (dnevni tečaji so shranjeni v CSV datoteki znotraj mape "rate"), kjer najprej pretvori ceno v "base" USD, nato pa še z uporabo tečajnice v EUR. Na koncu dobimo XML datoteko, ki jo lahko uvozimo, ko ustvarimo nov Doh-KDVP dokument ("Uvoz popisnih listov").

---

### Podpira:
 - market sell, market buy, limit sell, limit buy
 - rate conversion v base EUR
 - rate conversion iz base USD v EUR (uporabljena tečajnica iz [ECB Europa](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml))
 - ignoriranje tickerjev brez odsvojitve (prodaje: market sell in limit sell)
Dividende in ostale zadeve skripta ignorira.

---

### Navodila za uporabo:
Pred zagonom skripte je potrebno naložiti [Phyton](https://www.python.org/downloads/windows/) ([navodila za namestitev](https://realpython.com/installing-python/)).

1. Zgoraj pritisnemo zeleni gumb "Code" in izberemo "Download ZIP"
2. Razširimo arhivsko datoteko in se prestavimo v mapo "t212-edavki-main"
3. V Trading212 izvozimo CSV datoteke in jih skopiramo v mapo "t212-edavki-main/input" (program podpira več CSV datotek)
4. Ko smo v mapi "t212-edavki-main", pritisnemo kombinacijo tipk ALT + F (odpre se meni). Pritisnemo S (odpre se podmeni). Pritisnemo R (odpre se PowerShell)
5. Poženemo skripto z ukazom: python main.py
 
Če se izpiše: "Your XML file is located inside output folder.", smo uspešno zgenerirali XML datoteko, pripravljeno na uvoz v eDavki. V nasprotnem primeru je šlo nekaj narobe.

---

### Ti je skripta prišparala nekaj časa?
Lahko mi častiš pivo.
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=HP6Z34ASADB4Y)

### Ti skripta ne deluje?
V primeru, da ti skripta ne deluje, lahko odpreš "New issue" (klikni zgoraj "Issues" in nato zeleni gumb desno) ali pa mi pišeš na [mail](mailto:lenar.rahmatullin@gmail.com).
