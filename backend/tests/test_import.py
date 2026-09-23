from datetime import date

import pytest

from importer import CSVFormatError, clean_title, parse_amount, parse_bank_csv


def test_negative_amounts_are_spending_and_positive_rows_are_skipped():
    rows, skipped, _ = parse_bank_csv(
        "Date,Description,Amount\n2026-09-01,TIM HORTONS #123,-4.50\n2026-09-02,PAYROLL,1000.00\n")
    assert [(r.title, r.amount, r.date) for r in rows] == [("Tim Hortons", 4.5, date(2026, 9, 1))]
    assert skipped == 1


def test_all_positive_amounts_are_treated_as_spending():
    rows, skipped, _ = parse_bank_csv("Date,Merchant,Amount\n2026-09-01,Shop,12\n2026-09-02,Cafe,3\n")
    assert [r.amount for r in rows] == [12, 3]
    assert skipped == 0


def test_rbc_style_export():
    text = ("Account Type,Account Number,Transaction Date,Cheque Number,Description 1,Description 2,CAD$,USD$\n"
            "Chequing,123,9/16/2026,,STARBUCKS,,-6.45,\n"
            "Chequing,123,9/17/2026,,PAYROLL,,900.00,\n")
    rows, skipped, _ = parse_bank_csv(text)
    assert [(r.title, r.amount, r.date) for r in rows] == [("Starbucks", 6.45, date(2026, 9, 16))]
    assert skipped == 1


def test_td_style_headerless_debit_credit():
    rows, skipped, fmt = parse_bank_csv("09/14/2026,NETFLIX.COM,16.99,,1200.00\n09/15/2026,E-TRANSFER,,50.00,1250.00\n")
    assert [(r.title, r.amount) for r in rows] == [("Netflix.Com", 16.99)]
    assert skipped == 1
    assert "No header" in fmt


def test_day_first_dates_detected_from_the_whole_file():
    rows, _, _ = parse_bank_csv("Date,Description,Amount\n01/09/2026,A,-1\n13/09/2026,B,-2\n")
    assert [r.date for r in rows] == [date(2026, 9, 1), date(2026, 9, 13)]


@pytest.mark.parametrize("raw,expected", [
    ("-12.50", -12.5), ("(12.00)", -12.0), ("$1,234.56", 1234.56), ("  ", None), ("abc", None),
])
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected


def test_clean_title():
    assert clean_title("TIM HORTONS #4521  HAMILTON") == "Tim Hortons Hamilton"
    assert clean_title("Already Nice") == "Already Nice"
    assert clean_title("#123") == "Imported transaction"


@pytest.mark.parametrize("text", ["", "Date,Description\n2026-01-01,x\n", "Date,Description,Amount\nnot-a-date,x,-1\n"])
def test_unreadable_files_raise(text):
    with pytest.raises(CSVFormatError):
        parse_bank_csv(text)


def upload(client, auth, text, name="bank.csv"):
    return client.post("/import/preview", files={"file": (name, text.encode(), "text/csv")}, headers=auth)


def test_preview_learns_categories_and_flags_duplicates(client, auth, add_expense):
    add_expense(title="Starbucks", amount=6.45, category="Entertainment", date="2026-09-16")
    r = upload(client, auth, "Date,Description,Amount\n2026-09-16,STARBUCKS,-6.45\n"
                             "2026-09-17,STARBUCKS,-3.10\n2026-09-18,PRESTO,-40\n2026-09-19,ZZZ,-1\n")
    assert r.status_code == 200, r.text
    rows = r.json()["rows"]
    assert [(x["category"], x["category_source"], x["duplicate"]) for x in rows] == [
        ("Entertainment", "history", True),   # your own past choice beats the keyword list
        ("Entertainment", "history", False),
        ("Transportation", "keyword", False),
        ("Other", "default", False),
    ]


def test_preview_rejects_bad_and_oversized_files(client, auth):
    assert upload(client, auth, "hello").status_code == 422
    assert upload(client, auth, "x" * (2 * 1024 * 1024 + 10)).status_code == 413


def test_commit_saves_all_rows_or_none(client, auth):
    good = {"title": "A", "amount": 1, "category": "Other", "date": "2026-09-01"}
    r = client.post("/import/commit", json={"rows": [good, {**good, "title": "B"}]}, headers=auth)
    assert r.json() == {"created": 2}
    r = client.post("/import/commit", json={"rows": [good, {**good, "category": "Nope"}]}, headers=auth)
    assert r.status_code == 422
    assert len(client.get("/expenses/", headers=auth).json()) == 2
