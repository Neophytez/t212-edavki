import csv
import os
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom
import datetime

usd_eur = {}
rows = []
tickers_with_sell = []
base_currency = ''


def save_file(data):
    f = open("output/output.xml", "w")
    f.write(data)
    f.close()


def get_files(folder):
    return os.listdir(folder)


# 2021: Action,Time,ISIN,Ticker,Name,No. of shares,Price / share,Currency (Price / share),Exchange rate,Result (EUR),Total (EUR),Charge amount (EUR),Notes,ID
# 2022: Action,Time,ISIN,Ticker,Name,No. of shares,Price / share,Currency (Price / share),Exchange rate,Total (EUR),Withholding tax,Currency (Withholding tax),Charge amount (EUR),Notes,ID,Currency conversion fee (EUR)

def validate_header(h):
    if h[0] != 'Action':
        return False
    if h[1] != 'Time':
        return False
    if h[3] != 'Ticker':
        return False
    if h[5] != 'No. of shares':
        return False
    if h[6] != 'Price / share':
        return False
    if h[7] != 'Currency (Price / share)':
        return False
    if h[8] != 'Exchange rate':
        return False

    global base_currency
    base_currency = h[9].split()[1].replace('(', '').replace(')', '')

    return True


def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ")


def convert_to_base(p, r):
    return str(round(float(p)/float(r), 4))


def convert_usd_to_eur(p, d):
    return str(round(float(p) * float(find_usd_eur_rate(d)), 4))


def find_usd_eur_rate(d):
    while d not in usd_eur:
        d = datetime.datetime.strptime(d, '%Y-%m-%d') - datetime.timedelta(1)
        d = d.strftime('%Y-%m-%d')
    return usd_eur[d]


def sale(root, d, q, p):
    child = SubElement(root, 'Sale')
    s_child = SubElement(child, 'F6')
    s_child.text = d
    s_child = SubElement(child, 'F7')
    s_child.text = q
    s_child = SubElement(child, 'F9')
    s_child.text = p
    s_child = SubElement(child, 'F10')
    s_child.text = 'true'


def purchase(root, d, q, p):
    child = SubElement(root, 'Purchase')
    s_child = SubElement(child, 'F1')
    s_child.text = d
    s_child = SubElement(child, 'F2')
    s_child.text = 'B'
    s_child = SubElement(child, 'F3')
    s_child.text = q
    s_child = SubElement(child, 'F4')
    s_child.text = p


def KDVP(root):
    top = SubElement(root, 'KDVP')
    child = SubElement(top, 'DocumentWorkflowID')
    child.text = "O"
    child = SubElement(top, 'Year')
    child.text = "2022"
    child = SubElement(top, 'PeriodStart')
    child.text = "2022-01-01"
    child = SubElement(top, 'PeriodEnd')
    child.text = "2022-12-31"
    child = SubElement(top, 'IsResident')
    child.text = "true"
    child = SubElement(top, 'TelephoneNumber')
    child.text = "069240240"
    child = SubElement(top, 'SecurityCount')
    child.text = "0"
    child = SubElement(top, 'SecurityShortCount')
    child.text = "0"
    child = SubElement(top, 'SecurityWithContractCount')
    child.text = "0"
    child = SubElement(top, 'SecurityWithContractShortCount')
    child.text = "0"
    child = SubElement(top, 'ShareCount')
    child.text = "0"
    child = SubElement(top, 'Email')
    child.text = "your-email@should-go.here"


def KVDP_item(root, t):
    child = SubElement(root, 'KDVPItem')
    s_child = SubElement(child, 'InventoryListType')
    s_child.text = 'PLVP'
    s_child = SubElement(child, 'Name')
    s_child.text = t
    s_child = SubElement(child, 'HasForeignTax')
    s_child.text = 'false'
    s_child = SubElement(child, 'HasLossTransfer')
    s_child.text = 'true'
    s_child = SubElement(child, 'ForeignTransfer')
    s_child.text = 'false'
    s_child = SubElement(child, 'TaxDecreaseConformance')
    s_child.text = 'false'
    s_child = SubElement(child, 'Securities')
    ss_child = SubElement(s_child, 'Code')
    ss_child.text = t
    ss_child = SubElement(s_child, 'IsFond')
    ss_child.text = 'false'
    ss_child = SubElement(s_child, 'Row')
    sss_child = SubElement(ss_child, 'ID')
    sss_child.text = '0'
    return ss_child


def header(root):
    child = SubElement(root, 'edp:Header')
    s_child = SubElement(child, 'edp:taxpayer')
    ss_child = SubElement(s_child, 'edp:taxNumber')
    ss_child.text = "12345678"
    ss_child = SubElement(s_child, 'edp:taxpayerType')
    ss_child.text = "FO"
    ss_child = SubElement(s_child, 'edp:name')
    ss_child.text = "Full name"
    ss_child = SubElement(s_child, 'edp:address1')
    ss_child.text = "Address"
    ss_child = SubElement(s_child, 'edp:city')
    ss_child.text = "City"
    ss_child = SubElement(s_child, 'edp:postNumber')
    ss_child.text = "1000"
    ss_child = SubElement(s_child, 'edp:birthDate')
    ss_child.text = "1995-12-31"


def read_input_file(name):
    csv_file = open("input/"+name)
    csvreader = csv.reader(csv_file)

    if not validate_header(next(csvreader)):
        print('CSV header is invalid')
        exit(0)

    global rows
    for r in csvreader:
        if not r:
            continue
        rows.append(r)

    csv_file.close()


def load_input_files():
    files = get_files("input/")
    valid_files = []

    for file in files:
        if file.endswith(".csv"):
            valid_files.append(file)

    if not valid_files:
        print('Input folder does not contain CSV files')
        exit(0)

    for file in valid_files:
        read_input_file(file)


def read_rate_file(name):
    csv_file = open("rate/"+name)
    csvreader = csv.reader(csv_file)

    next(csvreader)

    global usd_eur
    for r in csvreader:
        usd_eur[r[0]] = r[1]

    csv_file.close()


def load_usd_eur_rates():
    files = get_files("rate/")
    for file in files:
        if not file.endswith(".csv"):
            continue
        read_rate_file(file)


def find_tickers_with_sell():
    sell_actions = {'Market sell', 'Limit sell'}

    for row in rows:
        if not row:
            continue
        action = row[0]
        if action in sell_actions and action not in tickers_with_sell:
            ticker = row[3]
            tickers_with_sell.append(ticker)


if __name__ == '__main__':
    load_input_files()
    load_usd_eur_rates()
    print('Base currency: ' + base_currency)

    name_space = {
        "xmlns": "http://edavki.durs.si/Documents/Schemas/Doh_KDVP_9.xsd",
        "xmlns:edp": "http://edavki.durs.si/Documents/Schemas/EDP-Common-1.xsd",
    }

    envelope = Element('Envelope', name_space)
    header(envelope)
    SubElement(envelope, 'edp:AttachmentList')
    SubElement(envelope, 'edp:Signatures')
    body = SubElement(envelope, 'body')
    SubElement(body, 'edp:bodyContent')
    doh = SubElement(body, 'Doh_KDVP')
    KDVP(doh)

    find_tickers_with_sell()

    supported_actions = {'Market sell', 'Market buy', 'Limit sell', 'Limit buy'}

    for row in rows:
        if not row:
            continue
        
        action = row[0]

        if action not in supported_actions:
            continue

        ticker = row[3]

        if ticker not in tickers_with_sell:
            continue

        date = row[1].split()[0]
        price = row[6]
        currency = row[7]
        rate = row[8]

        if currency == 'EUR':
            calculated_price = price
        elif base_currency == 'EUR':
            calculated_price = convert_to_base(price, rate)
        elif base_currency == 'USD':
            calculated_price = convert_usd_to_eur(convert_to_base(price, rate), date)
        else:
            calculated_price = 0
            print('Unsupported base currency: ' + base_currency)
            exit(0)

        quantity = str(round(float(row[5]), 4))
        item = KVDP_item(doh, ticker)

        action = action.split()[1]

        if action == 'buy':
            purchase(item, date, quantity, calculated_price)
        elif action == 'sell':
            sale(item, date, quantity, calculated_price)

        f8 = SubElement(item, 'F8')
        f8.text = '0.0000'

    save_file(prettify(envelope))

    print('Your XML file is located inside output folder.')
