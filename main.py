#!/usr/bin/env python3
import argparse
import csv
import os
import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# =========================
# USER SETTINGS (EDIT THIS)
# =========================
TAX_YEAR = "2024"
PERIOD_START = f"{TAX_YEAR}-01-01"
PERIOD_END = f"{TAX_YEAR}-12-31"

TAX_NUMBER = "12345678"
FULL_NAME = "Full name"
ADDRESS = "Address"
CITY = "City"
POST_NUMBER = "1000"
BIRTH_DATE = "1995-12-31"
EMAIL = "your-email@should-go.here"
PHONE = "069240240"

# =========================
# SCRIPT SETTINGS
# =========================
INPUT_FOLDER = "input"
RATE_FOLDER = "rate"
OUTPUT_FOLDER = "output"
OUTPUT_FILENAME = "output.xml"

# Supported actions (Trading 212 export)
SUPPORTED_ACTIONS = {"Market sell", "Market buy", "Limit sell", "Limit buy", "Stop sell"}

# We only include tickers that have at least one sell (KDVP is about disposals)
SELL_ACTIONS = {"Market sell", "Limit sell", "Stop sell"}

# eDavki supports up to 8 decimals for these fields (XSD patterns)
DECIMAL_RULES = {
    # Positive decimal, max 14 digits before '.', max 8 after
    "typeDecimalPos14_8": {"int_digits": 14, "scale": 8, "allow_negative": False},
    # Positive decimal, max 12 digits before '.', max 8 after
    "typeDecimalPos12_8": {"int_digits": 12, "scale": 8, "allow_negative": False},
    # Signed decimal, max 12 digits before '.', max 8 after
    "typeDecimalNeg12_8": {"int_digits": 12, "scale": 8, "allow_negative": True},
}

# One step at 8 decimals
Q8 = Decimal("0.00000001")


# =========================
# HELPERS
# =========================
def get_files(folder: str) -> list[str]:
    """Return a list of files in a folder."""
    if not os.path.exists(folder):
        raise FileNotFoundError(f"Folder '{folder}' does not exist.")
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]


def save_file(data: str, output_folder: str = OUTPUT_FOLDER, filename: str = OUTPUT_FILENAME) -> str:
    """Save XML string into output folder."""
    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)
    return path


def prettify(elem) -> str:
    """Return a pretty formatted XML string."""
    rough_string = tostring(elem, "utf-8")
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ")


def to_decimal(value) -> Decimal:
    """Convert value into Decimal (safe for money/quantities)."""
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid number: {value}. Details: {e}")


def quantize_8(d: Decimal) -> Decimal:
    """Round to 8 decimals with HALF_UP."""
    return d.quantize(Q8, rounding=ROUND_HALF_UP)


def fmt_decimal(value, xsd_type: str) -> str:
    """
    Format a decimal number so it matches eDavki limits:
    - fixed-point number (no exponent)
    - max digits before decimal point
    - max 8 decimals
    - no negative zero
    """
    if xsd_type not in DECIMAL_RULES:
        raise ValueError(f"Unknown XSD decimal type: {xsd_type}")

    rule = DECIMAL_RULES[xsd_type]
    d = to_decimal(value)

    if not rule["allow_negative"] and d < 0:
        raise ValueError(f"Negative value not allowed for {xsd_type}: {value}")

    scale = rule["scale"]
    q = Decimal("1").scaleb(-scale)  # 10^-scale

    d = d.quantize(q, rounding=ROUND_HALF_UP)

    # Fix "-0.00000000" -> "0.00000000"
    if d == 0:
        d = Decimal("0").quantize(q)

    s = format(d, "f")

    # Remove trailing zeros (keeps values shorter, still valid)
    if "." in s:
        s = s.rstrip("0").rstrip(".")

    # Check max digits before decimal
    int_part = s.split(".", 1)[0].lstrip("-")
    if len(int_part) > rule["int_digits"]:
        raise ValueError(f"Too many digits before decimal for {xsd_type}: {s}")

    return s


def parse_date(time_value: str) -> str:
    """Get YYYY-MM-DD from a Trading 212 'Time' value."""
    return time_value.split()[0]


# =========================
# FX RATES
# =========================
def read_rate_file(filename: str, rate_folder: str, usd_eur: dict) -> None:
    """Read one USD/EUR CSV rate file into dict: {YYYY-MM-DD: rate}."""
    path = os.path.join(rate_folder, filename)
    with open(path, "r", newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)  # skip header
        for row in reader:
            if row and len(row) >= 2:
                usd_eur[row[0]] = row[1]


def load_usd_eur_rates(rate_folder: str, state: dict) -> None:
    """Load all USD/EUR CSV files from /rate folder."""
    usd_eur = state["usd_eur"]
    rate_files = [f for f in get_files(rate_folder) if f.lower().endswith(".csv")]
    if not rate_files:
        raise FileNotFoundError(f"No exchange rate CSV files found in {rate_folder} folder.")
    for filename in sorted(rate_files):
        read_rate_file(filename, rate_folder, usd_eur)


def find_usd_eur_rate(date: str, usd_eur: dict) -> Decimal:
    """
    Find USD/EUR rate for a date.
    If missing, search backwards day by day until found.
    """
    dt = date
    while dt not in usd_eur:
        dt_dt = datetime.datetime.strptime(dt, "%Y-%m-%d") - datetime.timedelta(days=1)
        dt = dt_dt.strftime("%Y-%m-%d")
    return to_decimal(usd_eur[dt])


def convert_to_base(price, rate) -> Decimal:
    """Convert a value using exchange rate (Trading 212 export helper)."""
    p = to_decimal(price)
    r = to_decimal(rate)
    if r == 0:
        raise ValueError(f"Invalid exchange rate: {rate}")
    return p / r


def convert_usd_to_eur(price_usd: Decimal, date: str, usd_eur: dict) -> Decimal:
    """Convert USD price into EUR using USD/EUR rate for that date."""
    rate = find_usd_eur_rate(date, usd_eur)
    return price_usd * rate


# =========================
# CSV INPUT
# =========================
def validate_header(header: list[str], state: dict) -> bool:
    """
    Find needed columns in Trading 212 CSV.
    Trading 212 headers can differ between years, so we search by column prefix.
    """
    required_columns = {
        "Action": None,
        "Time": None,
        "Ticker": None,
        "No. of shares": None,
        "Price / share": None,
        "Currency (Price / share)": None,
        "Exchange rate": None,
        "Result": None,  # older export format
        "Total": None,   # newer export format
    }

    for index, column_name in enumerate(header):
        for required_column in required_columns:
            if required_columns[required_column] is None and column_name.startswith(required_column):
                required_columns[required_column] = index

                # Detect export base currency from "Result (EUR)" or "Total (USD)" etc.
                if required_column in ("Result", "Total"):
                    parts = column_name.split()
                    if len(parts) > 1:
                        state["base_currency"] = parts[1].strip("()")
                    else:
                        state["base_currency"] = "EUR"

    if all(value is None for key, value in required_columns.items() if key in ("Result", "Total")):
        return False

    state["header_indices"] = {k: v for k, v in required_columns.items() if v is not None}
    return True


def read_input_file(filename: str, input_folder: str, state: dict) -> None:
    """Read one CSV file and store only supported actions."""
    path = os.path.join(input_folder, filename)
    with open(path, "r", newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        header_row = next(reader)
        if not validate_header(header_row, state):
            raise ValueError(f"CSV header in {filename} is invalid.")

        hi = state["header_indices"]

        for row in reader:
            if row and row[hi["Action"]] in SUPPORTED_ACTIONS:
                state["rows"].append(row)


def load_input_files(input_folder: str, state: dict) -> None:
    """Load all CSV files from /input folder."""
    input_files = [f for f in get_files(input_folder) if f.lower().endswith(".csv")]
    if not input_files:
        raise FileNotFoundError(f"No CSV files found in {input_folder} folder.")
    for filename in sorted(input_files):
        print(f"Parsing file: {filename}")
        read_input_file(filename, input_folder, state)


def find_tickers_with_sell(state: dict) -> None:
    """Find tickers that have at least one sell action."""
    hi = state["header_indices"]
    tickers = set()
    for row in state["rows"]:
        if row[hi["Action"]] in SELL_ACTIONS:
            tickers.add(row[hi["Ticker"]])
    state["tickers_with_sell"] = tickers


def compute_eur_unit_price(row: list[str], state: dict) -> Decimal:
    """
    Compute unit price in EUR.
    Trading 212 can export prices in EUR or another currency + exchange rate.
    """
    hi = state["header_indices"]

    date = parse_date(row[hi["Time"]])
    price = row[hi["Price / share"]]
    currency = row[hi["Currency (Price / share)"]]
    rate = row[hi["Exchange rate"]]

    base_currency = state["base_currency"]
    usd_eur = state["usd_eur"]

    if currency == "EUR":
        return to_decimal(price)

    # Export base is EUR => exchange rate converts directly into EUR
    if base_currency == "EUR":
        return convert_to_base(price, rate)

    # Export base is USD => first convert into USD base, then USD -> EUR by date
    if base_currency == "USD":
        usd = convert_to_base(price, rate)
        return convert_usd_to_eur(usd, date, usd_eur)

    raise ValueError(f"Unsupported base currency: {base_currency}")


# =========================
# ROUNDING FIX (OPTIONAL)
# =========================
def apply_rounding_reconciliation(state: dict) -> None:
    """
    Optional fix for tiny leftovers due to rounding.

    Broker can export quantities with 10 decimals.
    eDavki accepts only 8 decimals.
    When eDavki sums the rounded numbers, final holdings can show e.g. -0.00000001.

    This function:
    - works per ticker
    - adjusts only ONE transaction per ticker (minimal step 0.00000001)
    - prints exactly what was changed
    """
    hi = state["header_indices"]
    tickers = state["tickers_with_sell"]

    # Stable order ensures the "last buy/sell" choice is always the same
    rows_sorted = sorted(state["rows"], key=lambda r: r[hi["Time"]])

    # Group rows by ticker (only tickers we will include in XML)
    rows_by_ticker: dict[str, list[list[str]]] = {}
    for r in rows_sorted:
        action_full = r[hi["Action"]]
        if action_full not in SUPPORTED_ACTIONS:
            continue
        ticker = r[hi["Ticker"]]
        if ticker not in tickers:
            continue
        rows_by_ticker.setdefault(ticker, []).append(r)

    adjustments = 0

    for ticker, rows in rows_by_ticker.items():
        buys_idx: list[int] = []
        sells_idx: list[int] = []

        # Totals at full broker precision
        sum_buy_full = Decimal("0")
        sum_sell_full = Decimal("0")

        # Totals after rounding each row to 8 decimals
        sum_buy_8 = Decimal("0")
        sum_sell_8 = Decimal("0")

        for idx, r in enumerate(rows):
            action = r[hi["Action"]].split()[1].lower()  # buy / sell
            qty_full = to_decimal(r[hi["No. of shares"]])
            qty_8 = quantize_8(qty_full)

            if action == "buy":
                buys_idx.append(idx)
                sum_buy_full += qty_full
                sum_buy_8 += qty_8
            elif action == "sell":
                sells_idx.append(idx)
                sum_sell_full += qty_full
                sum_sell_8 += qty_8

        # What the net should be in an 8-decimal world (based on full precision)
        net_target = quantize_8(sum_buy_full - sum_sell_full)

        # What eDavki will get when summing already-rounded rows
        net_rounded = quantize_8(sum_buy_8 - sum_sell_8)

        # Rounding drift
        diff = quantize_8(net_target - net_rounded)
        if diff == 0:
            continue

        # Apply diff to exactly one row (deterministic rule)
        chosen = None
        new_qty = None

        if diff > 0:
            # Need to increase net
            if buys_idx:
                chosen = buys_idx[-1]  # last buy
                old = quantize_8(to_decimal(rows[chosen][hi["No. of shares"]]))
                new_qty = quantize_8(old + diff)
            elif sells_idx:
                chosen = sells_idx[-1]  # last sell
                old = quantize_8(to_decimal(rows[chosen][hi["No. of shares"]]))
                new_qty = quantize_8(old - diff)
        else:
            # Need to decrease net
            need = -diff
            if sells_idx:
                chosen = sells_idx[-1]  # last sell
                old = quantize_8(to_decimal(rows[chosen][hi["No. of shares"]]))
                new_qty = quantize_8(old + need)
            elif buys_idx:
                chosen = buys_idx[-1]  # last buy
                old = quantize_8(to_decimal(rows[chosen][hi["No. of shares"]]))
                new_qty = quantize_8(old - need)

        if chosen is None or new_qty is None:
            continue

        if new_qty <= 0:
            raise ValueError(f"[rounding-fix] {ticker}: adjustment would make quantity <= 0 ({new_qty})")

        # Store adjusted quantity back into the row
        rows[chosen][hi["No. of shares"]] = format(new_qty, "f")
        adjustments += 1

        action = rows[chosen][hi["Action"]]
        when = parse_date(rows[chosen][hi["Time"]])
        print(f"[rounding-fix] {ticker}: applied {format(diff, 'f')} via {action} on {when}")

    if adjustments == 0:
        print("[rounding-fix] no adjustments were needed")
    else:
        print(f"[rounding-fix] applied adjustments: {adjustments}")


# =========================
# XML BUILDING
# =========================
def header_xml(root) -> None:
    """Add EDP header with taxpayer information."""
    header_elem = SubElement(root, "edp:Header")
    taxpayer = SubElement(header_elem, "edp:taxpayer")
    SubElement(taxpayer, "edp:taxNumber").text = TAX_NUMBER
    SubElement(taxpayer, "edp:taxpayerType").text = "FO"
    SubElement(taxpayer, "edp:name").text = FULL_NAME
    SubElement(taxpayer, "edp:address1").text = ADDRESS
    SubElement(taxpayer, "edp:city").text = CITY
    SubElement(taxpayer, "edp:postNumber").text = POST_NUMBER
    SubElement(taxpayer, "edp:birthDate").text = BIRTH_DATE


def KDVP_metadata(root) -> None:
    """Add KDVP metadata required by eDavki."""
    kdvp_elem = SubElement(root, "KDVP")
    SubElement(kdvp_elem, "DocumentWorkflowID").text = "O"
    SubElement(kdvp_elem, "Year").text = TAX_YEAR
    SubElement(kdvp_elem, "PeriodStart").text = PERIOD_START
    SubElement(kdvp_elem, "PeriodEnd").text = PERIOD_END
    SubElement(kdvp_elem, "IsResident").text = "true"
    SubElement(kdvp_elem, "TelephoneNumber").text = PHONE
    SubElement(kdvp_elem, "SecurityCount").text = "0"
    SubElement(kdvp_elem, "SecurityShortCount").text = "0"
    SubElement(kdvp_elem, "SecurityWithContractCount").text = "0"
    SubElement(kdvp_elem, "SecurityWithContractShortCount").text = "0"
    SubElement(kdvp_elem, "ShareCount").text = "0"
    SubElement(kdvp_elem, "Email").text = EMAIL


def KVDP_item(root, ticker: str):
    """
    Create one KDVPItem + Securities + one Row (ID=0).
    This matches the original structure of the script.
    """
    item_elem = SubElement(root, "KDVPItem")
    SubElement(item_elem, "InventoryListType").text = "PLVP"
    SubElement(item_elem, "Name").text = ticker
    SubElement(item_elem, "HasForeignTax").text = "false"
    SubElement(item_elem, "HasLossTransfer").text = "true"
    SubElement(item_elem, "ForeignTransfer").text = "false"
    SubElement(item_elem, "TaxDecreaseConformance").text = "false"

    securities = SubElement(item_elem, "Securities")
    SubElement(securities, "Code").text = ticker
    SubElement(securities, "IsFond").text = "false"

    row_elem = SubElement(securities, "Row")
    SubElement(row_elem, "ID").text = "0"
    return row_elem


def sale(root, date: str, quantity: str, price: str) -> None:
    """Add a Sale transaction into current Row."""
    sale_elem = SubElement(root, "Sale")
    SubElement(sale_elem, "F6").text = date
    SubElement(sale_elem, "F7").text = fmt_decimal(quantity, "typeDecimalPos12_8")
    SubElement(sale_elem, "F9").text = fmt_decimal(price, "typeDecimalPos14_8")
    SubElement(sale_elem, "F10").text = "true"


def purchase(root, date: str, quantity: str, price: str) -> None:
    """Add a Purchase transaction into current Row."""
    purchase_elem = SubElement(root, "Purchase")
    SubElement(purchase_elem, "F1").text = date
    SubElement(purchase_elem, "F2").text = "B"
    SubElement(purchase_elem, "F3").text = fmt_decimal(quantity, "typeDecimalPos12_8")
    SubElement(purchase_elem, "F4").text = fmt_decimal(price, "typeDecimalPos14_8")


def process_transactions(state: dict):
    """
    Build XML structure and write all transactions.
    We include only tickers that have at least one sell action.
    """
    count = 0

    # Namespaces required by eDavki
    ns = {
        "xmlns": "http://edavki.durs.si/Documents/Schemas/Doh_KDVP_9.xsd",
        "xmlns:edp": "http://edavki.durs.si/Documents/Schemas/EDP-Common-1.xsd",
    }

    envelope = Element("Envelope", ns)
    header_xml(envelope)
    SubElement(envelope, "edp:AttachmentList")
    SubElement(envelope, "edp:Signatures")

    body = SubElement(envelope, "body")
    SubElement(body, "edp:bodyContent")

    doh = SubElement(body, "Doh_KDVP")
    KDVP_metadata(doh)

    # Decide which tickers we include
    find_tickers_with_sell(state)
    tickers = state["tickers_with_sell"]
    print("Tickers with sale:", ", ".join(sorted(tickers)) if tickers else "/")

    hi = state["header_indices"]

    # Stable output order
    rows_sorted = sorted(state["rows"], key=lambda r: r[hi["Time"]])

    for row in rows_sorted:
        action_full = row[hi["Action"]]
        if action_full not in SUPPORTED_ACTIONS:
            continue

        ticker = row[hi["Ticker"]]
        if ticker not in tickers:
            continue

        date = parse_date(row[hi["Time"]])

        eur_unit_price = compute_eur_unit_price(row, state)
        price_str = fmt_decimal(eur_unit_price, "typeDecimalPos14_8")

        qty_str = fmt_decimal(row[hi["No. of shares"]], "typeDecimalPos12_8")

        item = KVDP_item(doh, ticker)

        # "Market sell" -> sell, "Limit buy" -> buy, "Stop sell" -> sell
        action = action_full.split()[1].lower()
        if action == "buy":
            purchase(item, date, qty_str, price_str)
        elif action == "sell":
            sale(item, date, qty_str, price_str)
        else:
            continue

        # F8 is included as 0 (eDavki UI calculates holdings itself)
        SubElement(item, "F8").text = fmt_decimal("0", "typeDecimalNeg12_8")

        count += 1

    return envelope, count


# =========================
# CLI
# =========================
def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Convert Trading212 CSV exports into eDavki Doh_KDVP XML.")
    parser.add_argument(
        "--fix-rounding-error",
        action="store_true",
        help="Fix tiny leftovers caused by rounding to 8 decimals (prints what was changed).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    state = {
        "usd_eur": {},
        "rows": [],
        "tickers_with_sell": set(),
        "base_currency": "EUR",
        "header_indices": {},
        "fix_rounding_error": bool(args.fix_rounding_error),
    }

    # Load input CSV files and rate files
    load_input_files(INPUT_FOLDER, state)
    load_usd_eur_rates(RATE_FOLDER, state)
    print("Base currency:", state["base_currency"])

    # Optional rounding fix
    if state["fix_rounding_error"]:
        print("Rounding fix: ENABLED")
        apply_rounding_reconciliation(state)
    else:
        print("Rounding fix: DISABLED (use --fix-rounding-error to enable)")

    # Build XML and write file
    envelope, count = process_transactions(state)
    xml_output = prettify(envelope)
    output_path = save_file(xml_output, OUTPUT_FOLDER, OUTPUT_FILENAME)

    print("Count:", count)
    print("XML saved to:", output_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("Error:", err)
