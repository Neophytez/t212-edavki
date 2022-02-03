import csv
import os


rows = []


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


if __name__ == '__main__':
    files = get_files()

    for file in files:
        read_files(file)
