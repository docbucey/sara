"""
CORE — Accountant: invoicing, expense tracking, ledger, reporting.
All data stored as JSON in ~/sara_nbs/accountant/ for portability.
Excel export uses openpyxl. PDF invoices use fpdf2.
"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


_ACCT_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs", "accountant")


def _ensure_dir(subdir: str = "") -> str:
    path = os.path.join(_ACCT_DIR, subdir) if subdir else _ACCT_DIR
    os.makedirs(path, exist_ok=True)
    return path


def _load_json(filepath: str) -> list:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_json(filepath: str, data: list) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Invoicing ──────────────────────────────────────────────────────────────

def _invoices_path() -> str:
    return os.path.join(_ensure_dir("invoices"), "invoices.json")


def create_invoice(
    client_name: str,
    items: List[Dict[str, Any]],
    due_days: int = 30,
    tax_rate: float = 0.0,
    notes: str = "",
    from_name: str = "",
    from_address: str = "",
) -> Dict[str, Any]:
    subtotal = sum(float(i.get("qty", 1)) * float(i.get("rate", 0)) for i in items)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    invoice = {
        "invoice_id": f"INV-{uuid.uuid4().hex[:8].upper()}",
        "created": _now(),
        "due_date": (datetime.now(timezone.utc) + timedelta(days=due_days)).strftime("%Y-%m-%d"),
        "status": "draft",
        "from_name": from_name,
        "from_address": from_address,
        "client_name": client_name,
        "items": items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
        "notes": notes,
        "payments": [],
    }

    invoices = _load_json(_invoices_path())
    invoices.append(invoice)
    _save_json(_invoices_path(), invoices)
    return {"success": True, "invoice": invoice}


def list_invoices(status: Optional[str] = None) -> Dict[str, Any]:
    invoices = _load_json(_invoices_path())
    if status:
        invoices = [i for i in invoices if i.get("status") == status]
    return {"success": True, "count": len(invoices), "invoices": invoices}


def get_invoice(invoice_id: str) -> Dict[str, Any]:
    for inv in _load_json(_invoices_path()):
        if inv["invoice_id"] == invoice_id:
            return {"success": True, "invoice": inv}
    return {"success": False, "error": f"Invoice {invoice_id} not found"}


def update_invoice_status(invoice_id: str, status: str) -> Dict[str, Any]:
    invoices = _load_json(_invoices_path())
    for inv in invoices:
        if inv["invoice_id"] == invoice_id:
            inv["status"] = status
            inv["updated"] = _now()
            _save_json(_invoices_path(), invoices)
            return {"success": True, "invoice": inv}
    return {"success": False, "error": f"Invoice {invoice_id} not found"}


def record_payment(invoice_id: str, amount: float, method: str = "check", note: str = "") -> Dict[str, Any]:
    invoices = _load_json(_invoices_path())
    for inv in invoices:
        if inv["invoice_id"] == invoice_id:
            payment = {"amount": amount, "method": method, "date": _now(), "note": note}
            inv.setdefault("payments", []).append(payment)
            paid_total = sum(p["amount"] for p in inv["payments"])
            if paid_total >= inv["total"]:
                inv["status"] = "paid"
            elif paid_total > 0:
                inv["status"] = "partial"
            inv["updated"] = _now()
            _save_json(_invoices_path(), invoices)
            return {"success": True, "invoice": inv, "paid_total": paid_total}
    return {"success": False, "error": f"Invoice {invoice_id} not found"}


def export_invoice_pdf(invoice_id: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    result = get_invoice(invoice_id)
    if not result.get("success"):
        return result
    inv = result["invoice"]

    try:
        import fpdf
    except ImportError:
        return {"success": False, "error": "fpdf2 not installed"}

    if not output_path:
        output_path = os.path.join(_ensure_dir("invoices"), f"{invoice_id}.pdf")

    pdf = fpdf.FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "INVOICE", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Invoice #: {inv['invoice_id']}", ln=True)
    pdf.cell(0, 7, f"Date: {inv['created'][:10]}", ln=True)
    pdf.cell(0, 7, f"Due: {inv['due_date']}", ln=True)
    pdf.cell(0, 7, f"Status: {inv['status'].upper()}", ln=True)
    if inv.get("from_name"):
        pdf.cell(0, 7, f"From: {inv['from_name']}", ln=True)
    pdf.cell(0, 7, f"Bill To: {inv['client_name']}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 8, "Description", border=1)
    pdf.cell(25, 8, "Qty", border=1, align="R")
    pdf.cell(35, 8, "Rate", border=1, align="R")
    pdf.cell(35, 8, "Amount", border=1, align="R")
    pdf.ln()

    pdf.set_font("Helvetica", "", 11)
    for item in inv.get("items", []):
        desc = str(item.get("description", ""))[:40]
        qty = float(item.get("qty", 1))
        rate = float(item.get("rate", 0))
        amt = qty * rate
        pdf.cell(80, 7, desc, border=1)
        pdf.cell(25, 7, f"{qty:g}", border=1, align="R")
        pdf.cell(35, 7, f"${rate:,.2f}", border=1, align="R")
        pdf.cell(35, 7, f"${amt:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(140, 7, "Subtotal:", align="R")
    pdf.cell(35, 7, f"${inv['subtotal']:,.2f}", align="R", ln=True)
    if inv.get("tax", 0) > 0:
        pdf.cell(140, 7, f"Tax ({inv['tax_rate']*100:.1f}%):", align="R")
        pdf.cell(35, 7, f"${inv['tax']:,.2f}", align="R", ln=True)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(140, 9, "TOTAL:", align="R")
    pdf.cell(35, 9, f"${inv['total']:,.2f}", align="R", ln=True)

    if inv.get("notes"):
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, f"Notes: {inv['notes']}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    pdf.output(output_path)
    return {"success": True, "path": output_path, "invoice_id": invoice_id}


# ── Expenses ───────────────────────────────────────────────────────────────

def _expenses_path() -> str:
    return os.path.join(_ensure_dir("expenses"), "expenses.json")


EXPENSE_CATEGORIES = [
    "supplies", "software", "hardware", "internet", "phone",
    "utilities", "rent", "insurance", "travel", "food",
    "medical", "education", "subscriptions", "marketing",
    "contractor", "taxes", "other",
]


def add_expense(
    amount: float,
    category: str,
    description: str = "",
    date: Optional[str] = None,
    recurring: bool = False,
    recurring_interval: str = "monthly",
    vendor: str = "",
) -> Dict[str, Any]:
    expense = {
        "expense_id": f"EXP-{uuid.uuid4().hex[:8].upper()}",
        "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "amount": round(float(amount), 2),
        "category": category if category in EXPENSE_CATEGORIES else "other",
        "description": description,
        "vendor": vendor,
        "recurring": recurring,
        "recurring_interval": recurring_interval if recurring else None,
        "created": _now(),
    }
    expenses = _load_json(_expenses_path())
    expenses.append(expense)
    _save_json(_expenses_path(), expenses)
    return {"success": True, "expense": expense}


def list_expenses(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    expenses = _load_json(_expenses_path())
    if category:
        expenses = [e for e in expenses if e.get("category") == category]
    if start_date:
        expenses = [e for e in expenses if e.get("date", "") >= start_date]
    if end_date:
        expenses = [e for e in expenses if e.get("date", "") <= end_date]
    total = sum(e.get("amount", 0) for e in expenses)
    return {"success": True, "count": len(expenses), "total": round(total, 2), "expenses": expenses}


def expense_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    result = list_expenses(start_date=start_date, end_date=end_date)
    expenses = result["expenses"]
    by_category: Dict[str, float] = {}
    for e in expenses:
        cat = e.get("category", "other")
        by_category[cat] = round(by_category.get(cat, 0) + e.get("amount", 0), 2)
    return {
        "success": True,
        "total": result["total"],
        "count": result["count"],
        "by_category": dict(sorted(by_category.items(), key=lambda x: -x[1])),
        "period": {"start": start_date, "end": end_date},
    }


# ── Ledger (double-entry) ─────────────────────────────────────────────────

def _ledger_path() -> str:
    return os.path.join(_ensure_dir("ledger"), "ledger.json")


def _accounts_path() -> str:
    return os.path.join(_ensure_dir("ledger"), "chart_of_accounts.json")


DEFAULT_ACCOUNTS = [
    {"code": "1000", "name": "Cash", "type": "asset"},
    {"code": "1100", "name": "Accounts Receivable", "type": "asset"},
    {"code": "1200", "name": "Equipment", "type": "asset"},
    {"code": "2000", "name": "Accounts Payable", "type": "liability"},
    {"code": "2100", "name": "Credit Card", "type": "liability"},
    {"code": "3000", "name": "Owner's Equity", "type": "equity"},
    {"code": "4000", "name": "Service Revenue", "type": "revenue"},
    {"code": "4100", "name": "Product Revenue", "type": "revenue"},
    {"code": "5000", "name": "Cost of Goods Sold", "type": "expense"},
    {"code": "6000", "name": "Operating Expenses", "type": "expense"},
    {"code": "6100", "name": "Rent", "type": "expense"},
    {"code": "6200", "name": "Utilities", "type": "expense"},
    {"code": "6300", "name": "Software/Subscriptions", "type": "expense"},
    {"code": "6400", "name": "Supplies", "type": "expense"},
    {"code": "6500", "name": "Insurance", "type": "expense"},
    {"code": "6600", "name": "Contractor Fees", "type": "expense"},
]


def get_chart_of_accounts() -> Dict[str, Any]:
    path = _accounts_path()
    accounts = _load_json(path)
    if not accounts:
        accounts = list(DEFAULT_ACCOUNTS)
        _save_json(path, accounts)
    return {"success": True, "accounts": accounts}


def add_account(code: str, name: str, acct_type: str) -> Dict[str, Any]:
    accounts = get_chart_of_accounts()["accounts"]
    if any(a["code"] == code for a in accounts):
        return {"success": False, "error": f"Account {code} already exists"}
    account = {"code": code, "name": name, "type": acct_type}
    accounts.append(account)
    _save_json(_accounts_path(), accounts)
    return {"success": True, "account": account}


def post_journal_entry(
    date: str,
    description: str,
    debits: List[Dict[str, Any]],
    credits: List[Dict[str, Any]],
) -> Dict[str, Any]:
    debit_total = sum(float(d.get("amount", 0)) for d in debits)
    credit_total = sum(float(c.get("amount", 0)) for c in credits)
    if abs(debit_total - credit_total) > 0.01:
        return {"success": False, "error": f"Debits ({debit_total}) != Credits ({credit_total})"}

    entry = {
        "entry_id": f"JE-{uuid.uuid4().hex[:8].upper()}",
        "date": date,
        "description": description,
        "debits": debits,
        "credits": credits,
        "total": round(debit_total, 2),
        "posted": _now(),
    }
    ledger = _load_json(_ledger_path())
    ledger.append(entry)
    _save_json(_ledger_path(), ledger)
    return {"success": True, "entry": entry}


def get_account_balance(account_code: str) -> Dict[str, Any]:
    ledger = _load_json(_ledger_path())
    debit_sum = 0.0
    credit_sum = 0.0
    for entry in ledger:
        for d in entry.get("debits", []):
            if d.get("account") == account_code:
                debit_sum += float(d.get("amount", 0))
        for c in entry.get("credits", []):
            if c.get("account") == account_code:
                credit_sum += float(c.get("amount", 0))

    accounts = get_chart_of_accounts()["accounts"]
    acct = next((a for a in accounts if a["code"] == account_code), None)
    acct_type = acct["type"] if acct else "unknown"

    if acct_type in ("asset", "expense"):
        balance = debit_sum - credit_sum
    else:
        balance = credit_sum - debit_sum

    return {
        "success": True,
        "account": account_code,
        "name": acct["name"] if acct else "Unknown",
        "type": acct_type,
        "debits": round(debit_sum, 2),
        "credits": round(credit_sum, 2),
        "balance": round(balance, 2),
    }


# ── Reports ────────────────────────────────────────────────────────────────

def trial_balance() -> Dict[str, Any]:
    accounts = get_chart_of_accounts()["accounts"]
    rows = []
    total_debits = 0.0
    total_credits = 0.0
    for acct in accounts:
        bal = get_account_balance(acct["code"])
        if bal["debits"] == 0 and bal["credits"] == 0:
            continue
        rows.append(bal)
        total_debits += bal["debits"]
        total_credits += bal["credits"]
    return {
        "success": True,
        "accounts": rows,
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "balanced": abs(total_debits - total_credits) < 0.01,
    }


def profit_and_loss(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    ledger = _load_json(_ledger_path())
    if start_date:
        ledger = [e for e in ledger if e.get("date", "") >= start_date]
    if end_date:
        ledger = [e for e in ledger if e.get("date", "") <= end_date]

    accounts = {a["code"]: a for a in get_chart_of_accounts()["accounts"]}
    revenue = {}
    expenses = {}

    for entry in ledger:
        for c in entry.get("credits", []):
            acct = accounts.get(c.get("account", ""))
            if acct and acct["type"] == "revenue":
                revenue[acct["name"]] = round(revenue.get(acct["name"], 0) + float(c.get("amount", 0)), 2)
        for d in entry.get("debits", []):
            acct = accounts.get(d.get("account", ""))
            if acct and acct["type"] == "expense":
                expenses[acct["name"]] = round(expenses.get(acct["name"], 0) + float(d.get("amount", 0)), 2)

    total_revenue = sum(revenue.values())
    total_expenses = sum(expenses.values())

    return {
        "success": True,
        "period": {"start": start_date, "end": end_date},
        "revenue": revenue,
        "total_revenue": round(total_revenue, 2),
        "expenses": expenses,
        "total_expenses": round(total_expenses, 2),
        "net_income": round(total_revenue - total_expenses, 2),
    }


def balance_sheet() -> Dict[str, Any]:
    accounts = get_chart_of_accounts()["accounts"]
    assets = {}
    liabilities = {}
    equity = {}

    for acct in accounts:
        bal = get_account_balance(acct["code"])
        if bal["balance"] == 0:
            continue
        bucket = {"name": acct["name"], "balance": bal["balance"]}
        if acct["type"] == "asset":
            assets[acct["code"]] = bucket
        elif acct["type"] == "liability":
            liabilities[acct["code"]] = bucket
        elif acct["type"] == "equity":
            equity[acct["code"]] = bucket

    total_assets = sum(a["balance"] for a in assets.values())
    total_liabilities = sum(l["balance"] for l in liabilities.values())
    total_equity = sum(e["balance"] for e in equity.values())

    pnl = profit_and_loss()
    retained = pnl["net_income"]

    return {
        "success": True,
        "assets": assets,
        "total_assets": round(total_assets, 2),
        "liabilities": liabilities,
        "total_liabilities": round(total_liabilities, 2),
        "equity": equity,
        "retained_earnings": round(retained, 2),
        "total_equity": round(total_equity + retained, 2),
        "balanced": abs(total_assets - (total_liabilities + total_equity + retained)) < 0.01,
    }


def cash_flow_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Simple cash flow: income received minus expenses paid in period."""
    pnl = profit_and_loss(start_date, end_date)
    inv_result = list_invoices(status="paid")
    paid_invoices = [i for i in inv_result["invoices"]
                     if (not start_date or i.get("created", "")[:10] >= start_date)
                     and (not end_date or i.get("created", "")[:10] <= end_date)]
    invoiced_income = sum(i.get("total", 0) for i in paid_invoices)

    exp_result = list_expenses(start_date=start_date, end_date=end_date)

    return {
        "success": True,
        "period": {"start": start_date, "end": end_date},
        "income_from_invoices": round(invoiced_income, 2),
        "total_expenses": exp_result["total"],
        "net_cash_flow": round(invoiced_income - exp_result["total"], 2),
        "ledger_net_income": pnl["net_income"],
    }
