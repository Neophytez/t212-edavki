import csv
import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.etree import ElementTree as ElTr
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


if __name__ == '__main__':
    files = get_files()

    for file in files:
        read_files(file)

    name_space = {
        "xmlns": "http://edavki.durs.si/Documents/Schemas/Doh_KDVP_9.xsd",
        "xmlns:edp": "http://edavki.durs.si/Documents/Schemas/EDP-Common-1.xsd",
    }

    envelope = Element('Envelope', name_space)
    SubElement(envelope, 'edp:AttachmentList')
    SubElement(envelope, 'edp:Signatures')
    body = SubElement(envelope, 'body')
    SubElement(body, 'edp:bodyContent')
    doh = SubElement(body, 'Doh_KDVP')

    save_file(prettify(envelope))