# Trading212 CSV to eDavki XML

## OBVESTILO: Z UPORABO SKRIPTE SOGLAŠAŠ, DA ZA MOREBITNE NAPAKE PRI VNOSU ODGOVARJAŠ SAM! PO UVOZU JE POTREBNO ROČNO PREGLEDATI VSE VNOSE!

## Kako deluje skripta?
Skripta prebere vse vrstice CSV datotek. Na podlagi glave prepozna, kakšna je base valuta (EUR, USD). Za vsako vrstico preveri, ali je market/limit buy/sell. Če ni, vrstico spusti. Če imamo T212 račun v base valuti EUR, je konverzija zelo preprosta, v primeru USD pa si skripta pomaga s podatki iz Yahoo Finance (dnevni tečaji so shranjeni v CSV datotekah znotraj mape "rate"), kjer najprej pretvori ceno v base USD, nato pa še v EUR. Na koncu dobimo XML datoteko, ki jo lahko uvozimo, ko ustvarimo nov Doh-KDVP dokument ("Uvoz popisnih listov").

## Podpira:
### - Market/limit sell/buy
### - rate conversion v base EUR
### - rate conversion iz base USD v EUR (podatke bere iz [Yahoo Finance](https://finance.yahoo.com/quote/EUR%3DX/history?p=EUR%3DX))

### Dividende in ostale zadeve skripta ignorira.

## Navodila za uporabo:
Pred zagonom skripte je potrebno naložiti [Phyton](https://www.python.org/downloads/windows/)

1. Zgoraj pritisnemo zeleni gumb "Code" in izberemo "Download ZIP"
2. Razširimo arhivsko datoteko
3. V T212 izvozimo CSV datoteke in jih prestavimo v mapo "input" (program podpira več CSV datotek)
4. Poženemo skripto (python main.py)
5. Če se izpiše: "Your XML file is located inside output folder.", smo uspešno zgenerirali XML datoteko, pripravljeno na uvoz v eDavki
6. V nasprotnem primeru je šlo nekaj narobe

## Ti je skripta prišparala nekaj časa?
Lahko mi častiš pivo.
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=HP6Z34ASADB4Y)

## Ti skripta ne deluje?
V primeru, da ti skripta ne deluje, lahko odpreš "New issue" (klikni zgoraj "Issues" in nato zeleni gumb desno) ali pa mi pišeš na [mail](mailto:lenar.rahmatullin@gmail.com).
