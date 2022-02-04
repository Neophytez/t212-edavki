import csv
import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.etree import ElementTree
from xml.dom import minidom


rows = []


def save_file(data):
    f = open("output/output.xml", "w")
    f.write(data)
    f.close()


def get_files():
    return os.listdir("input/")


def read_files(name):
    csv_file = open("input/"+name)
    csvreader = csv.reader(csv_file)

    header = next(csvreader)

    global rows
    for row in csvreader:
        rows.append(row)

    csv_file.close()


def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def convert_to_eur(price, rate):
    return str(round(float(price)/float(rate), 4))


def sale(root, date, quantity, price):
    child = SubElement(root, 'Sale')
    s_child = SubElement(child, 'F6')
    s_child.text = date
    s_child = SubElement(child, 'F7')
    s_child.text = quantity
    s_child = SubElement(child, 'F9')
    s_child.text = price
    s_child = SubElement(child, 'F10')
    s_child.text = 'true'


def purchase(root, date, quantity, price):
    child = SubElement(root, 'Purchase')
    s_child = SubElement(child, 'F1')
    s_child.text = date
    s_child = SubElement(child, 'F2')
    s_child.text = 'B'
    s_child = SubElement(child, 'F3')
    s_child.text = quantity
    s_child = SubElement(child, 'F4')
    s_child.text = price


def kdvp(root):
    top = SubElement(root, 'KDVP')
    child = SubElement(top, 'DocumentWorkflowID')
    child.text = "O"
    child = SubElement(top, 'Year')
    child.text = "2021"
    child = SubElement(top, 'PeriodStart')
    child.text = "2021-01-01"
    child = SubElement(top, 'PeriodEnd')
    child.text = "2021-12-31"
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


def kdvp_item(root, ticker):
    child = SubElement(root, 'KDVPItem')
    s_child = SubElement(child, 'InventoryListType')
    s_child.text = 'PLVP'
    s_child = SubElement(child, 'Name')
    s_child.text = ticker
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
    ss_child.text = ticker
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


if __name__ == '__main__':
    files = get_files()

    for file in files:
        if file == '.gitkeep':
            continue
        read_files(file)

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
    kdvp(doh)

    for row in rows:
        if row[0].split()[1] != 'buy' and row[0].split()[1] != 'sell':
            continue

        date = row[1].split()[0]
        ticker = row[3]
        quantity = str(round(float(row[5]), 4))
        price = convert_to_eur(row[6], row[8])

        item = kdvp_item(doh, ticker)

        if row[0].split()[1] == 'buy':
            purchase(item, date, quantity, price)
        elif row[0].split()[1] == 'sell':
            sale(item, date, quantity, price)

        f8 = SubElement(item, 'F8')
        f8.text = '0.0000'

    save_file(prettify(envelope))

    print('Your XML file is located inside output folder.')