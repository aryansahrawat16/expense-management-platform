import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime

MAX_ROWS = 2000

DATE_FORMATS = [
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%y",
    "%d-%b-%Y", "%b %d, %Y", "%d %b %Y", "%Y%m%d",
]
DATE_HEADERS = {"transaction date", "date", "posted date", "posting date", "trans date", "trans. date"}
DESC_HEADERS = {"description", "description 1", "merchant", "name", "payee", "details", "memo", "transaction"}
AMOUNT_HEADERS = {"amount", "cad$", "amount (cad)", "transaction amount"}
DEBIT_HEADERS = {"debit", "withdrawal", "withdrawals", "money out", "debit amount"}
CREDIT_HEADERS = {"credit", "deposit", "deposits", "money in", "credit amount"}


class CSVFormatError(ValueError):
    pass


@dataclass
class ParsedRow:
    title: str
    amount: float
    date: date


def parse_amount(raw: str) -> float | None:
    s = raw.strip().replace("$", "").replace(",", "").replace("CAD", "").strip()
    if not s:
        return None
    negative = s.startswith("(") and s.endswith(")")
    try:
        value = float(s.strip("()"))
    except ValueError:
        return None
    return -value if negative else value


def pick_date_format(values: list[str]) -> str | None:
    # use one format for the whole file so 03/04 vs 04/03 is consistent
    values = [v.strip() for v in values if v.strip()]
    for fmt in DATE_FORMATS:
        try:
            for v in values:
                datetime.strptime(v, fmt)
            return fmt
        except ValueError:
            continue
    return None


def clean_title(raw: str) -> str:
    title = re.sub(r"#\s*\d+", "", raw)
    title = re.sub(r"\s{2,}", " ", title).strip(" -*")
    if title.isupper():
        title = title.title()
    return title[:200] or "Imported transaction"


def _find(header: list[str], names: set[str]) -> int | None:
    return next((i for i, h in enumerate(header) if h in names), None)


def _cell(row: list[str], i: int | None) -> str:
    return row[i] if i is not None and i < len(row) else ""


def parse_bank_csv(text: str) -> tuple[list[ParsedRow], int, str]:
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if not rows:
        raise CSVFormatError("The file is empty.")
    if len(rows) > MAX_ROWS + 1:
        raise CSVFormatError(f"Files are limited to {MAX_ROWS} transactions.")

    header = [h.strip().lower() for h in rows[0]]
    date_i = _find(header, DATE_HEADERS)
    if date_i is not None:
        desc_i = _find(header, DESC_HEADERS)
        amount_i = _find(header, AMOUNT_HEADERS)
        debit_i, credit_i = _find(header, DEBIT_HEADERS), _find(header, CREDIT_HEADERS)
        if desc_i is None or (amount_i is None and debit_i is None):
            raise CSVFormatError("Couldn't find description and amount columns in this file.")
        data, fmt_name = rows[1:], "Header row"
    else:
        # TD exports have no header row: date, description, debit, credit, balance
        if len(rows[0]) < 3:
            raise CSVFormatError("Couldn't recognise this file's columns.")
        date_i, desc_i, amount_i, debit_i, credit_i = 0, 1, None, 2, 3
        data, fmt_name = rows, "No header (date, description, debit, credit)"

    date_fmt = pick_date_format([_cell(r, date_i) for r in data])
    if not date_fmt:
        raise CSVFormatError("Couldn't read the dates in this file.")

    if amount_i is not None:
        amounts = [parse_amount(_cell(r, amount_i)) for r in data]
        # if spending is negative, the positive rows are deposits/refunds
        spending_is_negative = any(a is not None and a < 0 for a in amounts)
        fmt_name += ", single amount column"
    else:
        fmt_name += ", separate debit/credit columns"

    parsed, skipped = [], 0
    for idx, row in enumerate(data):
        raw_date = _cell(row, date_i).strip()
        if amount_i is not None:
            a = amounts[idx]
            if a is None or a == 0 or (spending_is_negative and a > 0):
                skipped += 1
                continue
            amount = abs(a)
        else:
            debit = parse_amount(_cell(row, debit_i))
            if debit is None or debit == 0:
                skipped += 1
                continue
            amount = abs(debit)
        if not raw_date:
            skipped += 1
            continue
        parsed.append(ParsedRow(
            title=clean_title(_cell(row, desc_i)),
            amount=round(amount, 2),
            date=datetime.strptime(raw_date, date_fmt).date(),
        ))
    return parsed, skipped, fmt_name
