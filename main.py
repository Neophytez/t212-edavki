#!/usr/bin/env python3
import csv
import os
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Supported actions
SUPPORTED_ACTIONS = {'Market sell', 'Market buy', 'Limit sell', 'Limit buy'}

def get_files(folder):
    """Returns a list of files in the specified folder."""
    if not os.path.exists(folder):
        raise FileNotFoundError(f"Folder '{folder}' does not exist.")
    return [file for file in os.listdir(folder) if os.path.isfile(os.path.join(folder, file))]

def save_file(data, output_folder="output"):
    """Saves XML data to a file in the output folder."""
    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder, "output.xml")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        print("XML file saved successfully at", path)
    except Exception as e:
        raise IOError(f"Failed to save XML file. Details: {e}")

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ")

def convert_to_base(price, rate):
    """Converts the given price to the base currency using the exchange rate."""
    try:
        return str(round(float(price) / float(rate), 4))
    except (ValueError, ZeroDivisionError) as e:
        raise ValueError(f"Invalid price or rate: {price}, {rate}. Details: {e}")

def find_usd_eur_rate(date, usd_eur):
    """Finds the USD/EUR exchange rate for a given date.
       If an exact date is not found, the function searches backwards one day at a time."""
    dt = date
    while dt not in usd_eur:
        dt_dt = datetime.datetime.strptime(dt, '%Y-%m-%d') - datetime.timedelta(days=1)
        dt = dt_dt.strftime('%Y-%m-%d')
    return usd_eur[dt]

def convert_usd_to_eur(price, date, usd_eur):
    """Converts price from USD to EUR using the exchange rate for the given date."""
    try:
        rate = find_usd_eur_rate(date, usd_eur)
        return str(round(float(price) * float(rate), 4))
    except (ValueError, ZeroDivisionError) as e:
        raise ValueError(f"Failed to convert USD price {price} to EUR on date {date}. Details: {e}")

def sale(root, date, quantity, price):
    """Adds a sale transaction to the XML structure."""
    sale_elem = SubElement(root, 'Sale')
    SubElement(sale_elem, 'F6').text = date
    SubElement(sale_elem, 'F7').text = quantity
    SubElement(sale_elem, 'F9').text = price
    SubElement(sale_elem, 'F10').text = 'true'

def purchase(root, date, quantity, price):
    """Adds a purchase transaction to the XML structure."""
    purchase_elem = SubElement(root, 'Purchase')
    SubElement(purchase_elem, 'F1').text = date
    SubElement(purchase_elem, 'F2').text = 'B'
    SubElement(purchase_elem, 'F3').text = quantity
    SubElement(purchase_elem, 'F4').text = price

def KDVP_metadata(root):
    """Adds KDVP metadata to the XML structure."""
    kdvp_elem = SubElement(root, 'KDVP')
    SubElement(kdvp_elem, 'DocumentWorkflowID').text = "O"
    SubElement(kdvp_elem, 'Year').text = "2024"
    SubElement(kdvp_elem, 'PeriodStart').text = "2024-01-01"
    SubElement(kdvp_elem, 'PeriodEnd').text = "2024-12-31"
    SubElement(kdvp_elem, 'IsResident').text = "true"
    SubElement(kdvp_elem, 'TelephoneNumber').text = "069240240"
    SubElement(kdvp_elem, 'SecurityCount').text = "0"
    SubElement(kdvp_elem, 'SecurityShortCount').text = "0"
    SubElement(kdvp_elem, 'SecurityWithContractCount').text = "0"
    SubElement(kdvp_elem, 'SecurityWithContractShortCount').text = "0"
    SubElement(kdvp_elem, 'ShareCount').text = "0"
    SubElement(kdvp_elem, 'Email').text = "your-email@should-go.here"

def KVDP_item(root, ticker):
    """Adds a KDVP item for a specific ticker."""
    item_elem = SubElement(root, 'KDVPItem')
    SubElement(item_elem, 'InventoryListType').text = 'PLVP'
    SubElement(item_elem, 'Name').text = ticker
    SubElement(item_elem, 'HasForeignTax').text = 'false'
    SubElement(item_elem, 'HasLossTransfer').text = 'true'
    SubElement(item_elem, 'ForeignTransfer').text = 'false'
    SubElement(item_elem, 'TaxDecreaseConformance').text = 'false'
    securities = SubElement(item_elem, 'Securities')
    SubElement(securities, 'Code').text = ticker
    SubElement(securities, 'IsFond').text = 'false'
    row_elem = SubElement(securities, 'Row')
    SubElement(row_elem, 'ID').text = '0'
    return securities

def header_xml(root):
    """Adds the header to the XML structure."""
    header_elem = SubElement(root, 'edp:Header')
    taxpayer = SubElement(header_elem, 'edp:taxpayer')
    SubElement(taxpayer, 'edp:taxNumber').text = "12345678"
    SubElement(taxpayer, 'edp:taxpayerType').text = "FO"
    SubElement(taxpayer, 'edp:name').text = "Full name"
    SubElement(taxpayer, 'edp:address1').text = "Address"
    SubElement(taxpayer, 'edp:city').text = "City"
    SubElement(taxpayer, 'edp:postNumber').text = "1000"
    SubElement(taxpayer, 'edp:birthDate').text = "1995-12-31"

def validate_header(header, state):
    """Dynamically validates the CSV header by searching for relevant columns.
       Also updates base_currency in state based on header data."""
    required_columns = {
        'Action': None,
        'Time': None,
        'Ticker': None,
        'No. of shares': None,
        'Price / share': None,
        'Currency (Price / share)': None,
        'Exchange rate': None,
        'Result': None
    }

    for index, column_name in enumerate(header):
        for required_column in required_columns:
            if required_columns[required_column] is None and column_name.startswith(required_column):
                required_columns[required_column] = index
                if required_column == 'Result':
                    parts = column_name.split()
                    if len(parts) > 1:
                        state['base_currency'] = parts[1].strip("()")
                    else:
                        state['base_currency'] = 'EUR'

    if None in required_columns.values():
        return False

    state['header_indices'] = required_columns

    return True

def read_input_file(filename, input_folder, state):
    """Reads a CSV file and processes its rows."""
    path = os.path.join(input_folder, filename)
    try:
        with open(path, 'r', newline='') as csv_file:
            reader = csv.reader(csv_file)
            header_row = next(reader)
            if not validate_header(header_row, state):
                raise ValueError(f"CSV header in {filename} is invalid.")
            for row in reader:
                if row and row[state['header_indices']['Action']] in SUPPORTED_ACTIONS:
                    state['rows'].append(row)
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{filename}' not found in folder '{input_folder}'.")

def load_input_files(input_folder, state):
    """Loads and reads all CSV input files from the specified folder."""
    input_files = [file for file in get_files(input_folder) if file.endswith(".csv")]
    if not input_files:
        raise FileNotFoundError(f'No CSV files found in {input_folder} folder.')
    for filename in input_files:
        print(f"Parsing file: {filename}")
        read_input_file(filename, input_folder, state)

def read_rate_file(filename, rate_folder, usd_eur):
    """Reads a single exchange rate CSV file."""
    path = os.path.join(rate_folder, filename)
    try:
        with open(path, 'r', newline='') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Skip header
            for row in reader:
                if row:
                    usd_eur[row[0]] = row[1]
    except FileNotFoundError:
        raise FileNotFoundError(f"Rate file '{filename}' not found in folder '{rate_folder}'.")
    except Exception as e:
        raise IOError(f"Unable to read the rate file '{filename}'. Details: {e}")

def load_usd_eur_rates(rate_folder, state):
    """Loads all USD/EUR exchange rate CSV files from the specified rate folder."""
    usd_eur = state['usd_eur']
    rate_files = [file for file in get_files(rate_folder) if file.endswith(".csv")]
    if not rate_files:
        raise FileNotFoundError(f'No exchange rate CSV files found in {rate_folder} folder.')
    for filename in rate_files:
        read_rate_file(filename, rate_folder, usd_eur)

def find_tickers_with_sell(state):
    """Identifies all tickers that have sell actions."""
    sell_actions = {'Market sell', 'Limit sell'}
    tickers = state['tickers_with_sell']
    header_indices = state['header_indices']
    for row in state['rows']:
        if row[header_indices['Action']] in sell_actions and row[header_indices['Ticker']] not in tickers:
            tickers.append(row[header_indices['Ticker']])

def process_transactions(state):
    """Processes transactions and builds the XML structure.
       Returns the XML element and a count of processed items."""
    count = 0

    # Set up XML structure with required namespaces.
    ns = {
        "xmlns": "http://edavki.durs.si/Documents/Schemas/Doh_KDVP_9.xsd",
        "xmlns:edp": "http://edavki.durs.si/Documents/Schemas/EDP-Common-1.xsd",
    }
    envelope = Element('Envelope', ns)
    header_xml(envelope)
    SubElement(envelope, 'edp:AttachmentList')
    SubElement(envelope, 'edp:Signatures')
    body = SubElement(envelope, 'body')
    SubElement(body, 'edp:bodyContent')
    doh = SubElement(body, 'Doh_KDVP')
    KDVP_metadata(doh)

    # Identify tickers with sell actions.
    find_tickers_with_sell(state)
    tickers = state['tickers_with_sell']
    print("Tickers with sale:", ', '.join(tickers) if tickers else '/')

    header_indices = state['header_indices']

    for row in state['rows']:
        action_full = row[header_indices['Action']]
        # Process only rows with supported actions and tickers with sell actions.
        if action_full not in SUPPORTED_ACTIONS:
            continue

        ticker = row[header_indices['Ticker']]
        if ticker not in state['tickers_with_sell']:
            continue

        date = row[header_indices['Time']].split()[0]
        price = row[header_indices['Price / share']]
        currency = row[header_indices['Currency (Price / share)']]
        rate = row[header_indices['Exchange rate']]
        base_currency = state['base_currency']
        usd_eur = state['usd_eur']

        if currency == 'EUR':
            calculated_price = price
        elif base_currency == 'EUR':
            calculated_price = convert_to_base(price, rate)
        elif base_currency == 'USD':
            base_price = convert_to_base(price, rate)
            calculated_price = convert_usd_to_eur(base_price, date, usd_eur)
        else:
            raise ValueError(f"Unsupported base currency: {base_currency}")

        quantity = str(round(float(row[header_indices['No. of shares']]), 4))
        item = KVDP_item(doh, ticker)
        # Extract the buy/sell part from the action string (e.g., "Market sell" -> "sell")
        action = action_full.split()[1].lower()
        if action == 'buy':
            purchase(item, date, quantity, calculated_price)
        elif action == 'sell':
            sale(item, date, quantity, calculated_price)
        else:
            # Skip unsupported actions
            continue

        # Add extra field F8
        f8 = SubElement(item, 'F8')
        f8.text = '0.0000'
        count += 1

    return envelope, count

def main():
    # Shared state dictionary to hold parameters and data
    state = {
        'usd_eur': {},
        'rows': [],
        'tickers_with_sell': [],
        'base_currency': 'EUR',
        'header_indices': {}
    }
    input_folder = "input"
    rate_folder = "rate"
    output_folder = "output"

    # Load input CSV files and rate files.
    load_input_files(input_folder, state)
    load_usd_eur_rates(rate_folder, state)
    print('Base currency:', state['base_currency'])

    # Process transactions and build XML.
    envelope, count = process_transactions(state)
    xml_output = prettify(envelope)
    save_file(xml_output, output_folder)
    print('Count:', count)
    print('Your XML file is located inside the output folder.')

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print("Error:", err)
