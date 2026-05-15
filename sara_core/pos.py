"""
CORE — Point of Sale terminal backend.
Product catalog, cart, transactions, receipts, inventory, end-of-day.
Ties into accountant.py for automatic ledger entries.
All data stored as JSON in ~/sara_nbs/pos/ for portability.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


_POS_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs", "pos")


def _ensure_dir(subdir: str = "") -> str:
    path = os.path.join(_POS_DIR, subdir) if subdir else _POS_DIR
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


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Product Catalog ────────────────────────────────────────────────────────

def _products_path() -> str:
    return os.path.join(_ensure_dir("catalog"), "products.json")


def product_add(
    name: str,
    price: float,
    sku: str = "",
    category: str = "general",
    tax_rate: float = 0.0,
    stock: int = -1,
    barcode: str = "",
    description: str = "",
    cost: float = 0.0,
) -> Dict[str, Any]:
    product = {
        "product_id": f"PRD-{uuid.uuid4().hex[:8].upper()}",
        "sku": sku or f"SKU-{uuid.uuid4().hex[:6].upper()}",
        "barcode": barcode,
        "name": name,
        "description": description,
        "category": category,
        "price": round(float(price), 2),
        "cost": round(float(cost), 2),
        "tax_rate": float(tax_rate),
        "stock": int(stock),
        "active": True,
        "created": _now(),
    }
    products = _load_json(_products_path())
    products.append(product)
    _save_json(_products_path(), products)
    return {"success": True, "product": product}


def product_update(product_id: str, **fields) -> Dict[str, Any]:
    products = _load_json(_products_path())
    for p in products:
        if p["product_id"] == product_id:
            for k, v in fields.items():
                if k in p:
                    p[k] = v
            p["updated"] = _now()
            _save_json(_products_path(), products)
            return {"success": True, "product": p}
    return {"success": False, "error": f"Product {product_id} not found"}


def product_list(category: Optional[str] = None, active_only: bool = True) -> Dict[str, Any]:
    products = _load_json(_products_path())
    if active_only:
        products = [p for p in products if p.get("active", True)]
    if category:
        products = [p for p in products if p.get("category") == category]
    return {"success": True, "count": len(products), "products": products}


def product_lookup(query: str) -> Dict[str, Any]:
    """Find by product_id, sku, barcode, or name substring."""
    products = _load_json(_products_path())
    q = query.strip().lower()
    matches = [
        p for p in products
        if q in p.get("product_id", "").lower()
        or q in p.get("sku", "").lower()
        or q in p.get("barcode", "").lower()
        or q in p.get("name", "").lower()
    ]
    return {"success": True, "count": len(matches), "products": matches}


def product_deactivate(product_id: str) -> Dict[str, Any]:
    return product_update(product_id, active=False)


# ── Inventory ──────────────────────────────────────────────────────────────

def inventory_adjust(product_id: str, quantity_change: int, reason: str = "") -> Dict[str, Any]:
    products = _load_json(_products_path())
    for p in products:
        if p["product_id"] == product_id:
            if p["stock"] < 0:
                return {"success": True, "note": "Unlimited stock item", "product": p}
            p["stock"] = max(0, p["stock"] + quantity_change)
            p["updated"] = _now()
            _save_json(_products_path(), products)

            log = _load_json(os.path.join(_ensure_dir("inventory"), "adjustments.json"))
            log.append({
                "product_id": product_id,
                "change": quantity_change,
                "new_stock": p["stock"],
                "reason": reason,
                "timestamp": _now(),
            })
            _save_json(os.path.join(_ensure_dir("inventory"), "adjustments.json"), log)
            return {"success": True, "product": p}
    return {"success": False, "error": f"Product {product_id} not found"}


def inventory_low_stock(threshold: int = 5) -> Dict[str, Any]:
    products = _load_json(_products_path())
    low = [p for p in products if p.get("active", True) and 0 <= p.get("stock", -1) <= threshold]
    return {"success": True, "count": len(low), "products": low}


# ── Cart / Active Transaction ──────────────────────────────────────────────

_active_carts: Dict[str, Dict[str, Any]] = {}


def cart_create(register_id: str = "REG-1", cashier: str = "") -> Dict[str, Any]:
    cart_id = f"CART-{uuid.uuid4().hex[:8].upper()}"
    _active_carts[cart_id] = {
        "cart_id": cart_id,
        "register_id": register_id,
        "cashier": cashier,
        "items": [],
        "created": _now(),
    }
    return {"success": True, "cart": _active_carts[cart_id]}


def cart_add_item(cart_id: str, product_id: str, quantity: int = 1, price_override: Optional[float] = None) -> Dict[str, Any]:
    cart = _active_carts.get(cart_id)
    if not cart:
        return {"success": False, "error": f"Cart {cart_id} not found"}

    products = _load_json(_products_path())
    product = next((p for p in products if p["product_id"] == product_id), None)
    if not product:
        return {"success": False, "error": f"Product {product_id} not found"}

    if 0 <= product.get("stock", -1) < quantity:
        return {"success": False, "error": f"Insufficient stock ({product['stock']} available)"}

    unit_price = price_override if price_override is not None else product["price"]

    for item in cart["items"]:
        if item["product_id"] == product_id and item["unit_price"] == unit_price:
            item["quantity"] += quantity
            item["line_total"] = round(item["quantity"] * item["unit_price"], 2)
            item["tax"] = round(item["line_total"] * item["tax_rate"], 2)
            return {"success": True, "cart": cart}

    cart["items"].append({
        "product_id": product_id,
        "name": product["name"],
        "sku": product.get("sku", ""),
        "quantity": quantity,
        "unit_price": round(unit_price, 2),
        "tax_rate": product.get("tax_rate", 0),
        "line_total": round(quantity * unit_price, 2),
        "tax": round(quantity * unit_price * product.get("tax_rate", 0), 2),
        "cost": product.get("cost", 0),
    })
    return {"success": True, "cart": cart}


def cart_remove_item(cart_id: str, product_id: str) -> Dict[str, Any]:
    cart = _active_carts.get(cart_id)
    if not cart:
        return {"success": False, "error": f"Cart {cart_id} not found"}
    cart["items"] = [i for i in cart["items"] if i["product_id"] != product_id]
    return {"success": True, "cart": cart}


def cart_apply_discount(cart_id: str, discount_type: str = "percent", value: float = 0, reason: str = "") -> Dict[str, Any]:
    cart = _active_carts.get(cart_id)
    if not cart:
        return {"success": False, "error": f"Cart {cart_id} not found"}
    cart["discount"] = {"type": discount_type, "value": value, "reason": reason}
    return {"success": True, "cart": cart}


def cart_total(cart_id: str) -> Dict[str, Any]:
    cart = _active_carts.get(cart_id)
    if not cart:
        return {"success": False, "error": f"Cart {cart_id} not found"}

    subtotal = sum(i["line_total"] for i in cart["items"])
    tax = sum(i["tax"] for i in cart["items"])
    cost_total = sum(i.get("cost", 0) * i["quantity"] for i in cart["items"])

    discount_amount = 0.0
    disc = cart.get("discount")
    if disc:
        if disc["type"] == "percent":
            discount_amount = round(subtotal * (disc["value"] / 100), 2)
        elif disc["type"] == "flat":
            discount_amount = round(min(disc["value"], subtotal), 2)

    grand_total = round(subtotal + tax - discount_amount, 2)

    return {
        "success": True,
        "cart_id": cart_id,
        "item_count": sum(i["quantity"] for i in cart["items"]),
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "discount": round(discount_amount, 2),
        "grand_total": grand_total,
        "cost_total": round(cost_total, 2),
        "margin": round(grand_total - cost_total, 2) if cost_total > 0 else None,
    }


def cart_void(cart_id: str) -> Dict[str, Any]:
    if cart_id in _active_carts:
        del _active_carts[cart_id]
        return {"success": True, "voided": cart_id}
    return {"success": False, "error": f"Cart {cart_id} not found"}


# ── Checkout / Transaction ─────────────────────────────────────────────────

def _transactions_path() -> str:
    return os.path.join(_ensure_dir("transactions"), "transactions.json")


def checkout(
    cart_id: str,
    payment_method: str = "cash",
    amount_tendered: float = 0.0,
    customer_name: str = "",
    customer_email: str = "",
    note: str = "",
) -> Dict[str, Any]:
    cart = _active_carts.get(cart_id)
    if not cart:
        return {"success": False, "error": f"Cart {cart_id} not found"}
    if not cart["items"]:
        return {"success": False, "error": "Cart is empty"}

    totals = cart_total(cart_id)

    if payment_method == "cash" and amount_tendered < totals["grand_total"]:
        return {
            "success": False,
            "error": f"Insufficient payment: ${amount_tendered:.2f} < ${totals['grand_total']:.2f}",
        }

    change = round(amount_tendered - totals["grand_total"], 2) if payment_method == "cash" else 0.0

    txn = {
        "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "date": _today(),
        "timestamp": _now(),
        "register_id": cart.get("register_id", ""),
        "cashier": cart.get("cashier", ""),
        "customer_name": customer_name,
        "customer_email": customer_email,
        "items": cart["items"],
        "subtotal": totals["subtotal"],
        "tax": totals["tax"],
        "discount": totals["discount"],
        "grand_total": totals["grand_total"],
        "cost_total": totals["cost_total"],
        "margin": totals.get("margin"),
        "payment_method": payment_method,
        "amount_tendered": round(amount_tendered, 2),
        "change_due": change,
        "status": "completed",
        "note": note,
    }

    transactions = _load_json(_transactions_path())
    transactions.append(txn)
    _save_json(_transactions_path(), transactions)

    _deduct_inventory(cart["items"])
    _post_sale_to_ledger(txn)

    del _active_carts[cart_id]

    return {"success": True, "transaction": txn, "change_due": change}


def _deduct_inventory(items: List[Dict]) -> None:
    products = _load_json(_products_path())
    product_map = {p["product_id"]: p for p in products}
    for item in items:
        p = product_map.get(item["product_id"])
        if p and p.get("stock", -1) >= 0:
            p["stock"] = max(0, p["stock"] - item["quantity"])
            p["updated"] = _now()
    _save_json(_products_path(), products)


def _post_sale_to_ledger(txn: Dict) -> None:
    """Auto-post a journal entry to the Accountant ledger."""
    try:
        from sara_core.accountant import post_journal_entry
        post_journal_entry(
            date=txn["date"],
            description=f"POS Sale {txn['transaction_id']} — {txn.get('customer_name', 'walk-in')}",
            debits=[{"account": "1000", "amount": txn["grand_total"]}],
            credits=[{"account": "4100", "amount": txn["grand_total"]}],
        )
    except Exception:
        pass


def refund(transaction_id: str, reason: str = "") -> Dict[str, Any]:
    transactions = _load_json(_transactions_path())
    for txn in transactions:
        if txn["transaction_id"] == transaction_id:
            if txn.get("status") == "refunded":
                return {"success": False, "error": "Already refunded"}
            txn["status"] = "refunded"
            txn["refund_reason"] = reason
            txn["refund_date"] = _now()
            _save_json(_transactions_path(), transactions)

            _restore_inventory(txn["items"])

            try:
                from sara_core.accountant import post_journal_entry
                post_journal_entry(
                    date=_today(),
                    description=f"POS Refund {txn['transaction_id']}",
                    debits=[{"account": "4100", "amount": txn["grand_total"]}],
                    credits=[{"account": "1000", "amount": txn["grand_total"]}],
                )
            except Exception:
                pass

            return {"success": True, "transaction": txn}
    return {"success": False, "error": f"Transaction {transaction_id} not found"}


def _restore_inventory(items: List[Dict]) -> None:
    products = _load_json(_products_path())
    product_map = {p["product_id"]: p for p in products}
    for item in items:
        p = product_map.get(item["product_id"])
        if p and p.get("stock", -1) >= 0:
            p["stock"] += item["quantity"]
            p["updated"] = _now()
    _save_json(_products_path(), products)


# ── Receipts ───────────────────────────────────────────────────────────────

def generate_receipt(transaction_id: str, store_name: str = "SARA POS") -> Dict[str, Any]:
    transactions = _load_json(_transactions_path())
    txn = next((t for t in transactions if t["transaction_id"] == transaction_id), None)
    if not txn:
        return {"success": False, "error": f"Transaction {transaction_id} not found"}

    lines = []
    lines.append(f"{'=' * 40}")
    lines.append(f"{store_name:^40}")
    lines.append(f"{'=' * 40}")
    lines.append(f"TXN: {txn['transaction_id']}")
    lines.append(f"Date: {txn['timestamp'][:19]}")
    if txn.get("cashier"):
        lines.append(f"Cashier: {txn['cashier']}")
    if txn.get("customer_name"):
        lines.append(f"Customer: {txn['customer_name']}")
    lines.append(f"{'-' * 40}")

    for item in txn["items"]:
        name = item["name"][:22]
        qty = item["quantity"]
        total = item["line_total"]
        lines.append(f"{name:<22} {qty:>3} x ${item['unit_price']:>7.2f}")
        lines.append(f"{'':>22} ${total:>10.2f}")
        if item.get("tax", 0) > 0:
            lines.append(f"{'':>22}  tax ${item['tax']:>7.2f}")

    lines.append(f"{'-' * 40}")
    lines.append(f"{'Subtotal':>22} ${txn['subtotal']:>10.2f}")
    if txn.get("discount", 0) > 0:
        lines.append(f"{'Discount':>22} -${txn['discount']:>9.2f}")
    lines.append(f"{'Tax':>22} ${txn['tax']:>10.2f}")
    lines.append(f"{'TOTAL':>22} ${txn['grand_total']:>10.2f}")
    lines.append(f"{'-' * 40}")
    lines.append(f"{'Paid (' + txn['payment_method'] + ')':>22} ${txn['amount_tendered']:>10.2f}")
    if txn.get("change_due", 0) > 0:
        lines.append(f"{'Change':>22} ${txn['change_due']:>10.2f}")
    lines.append(f"{'=' * 40}")

    if txn.get("status") == "refunded":
        lines.append(f"{'*** REFUNDED ***':^40}")

    receipt_text = "\n".join(lines)
    return {"success": True, "receipt": receipt_text, "transaction_id": transaction_id}


# ── Sales Reporting ────────────────────────────────────────────────────────

def sales_today() -> Dict[str, Any]:
    return sales_by_date(_today())


def sales_by_date(date: str) -> Dict[str, Any]:
    transactions = _load_json(_transactions_path())
    day_txns = [t for t in transactions if t.get("date") == date and t.get("status") == "completed"]
    total_sales = sum(t["grand_total"] for t in day_txns)
    total_tax = sum(t["tax"] for t in day_txns)
    total_cost = sum(t.get("cost_total", 0) for t in day_txns)
    total_items = sum(sum(i["quantity"] for i in t["items"]) for t in day_txns)

    return {
        "success": True,
        "date": date,
        "transaction_count": len(day_txns),
        "total_items": total_items,
        "total_sales": round(total_sales, 2),
        "total_tax": round(total_tax, 2),
        "total_cost": round(total_cost, 2),
        "gross_margin": round(total_sales - total_cost, 2),
    }


def sales_range(start_date: str, end_date: str) -> Dict[str, Any]:
    transactions = _load_json(_transactions_path())
    txns = [
        t for t in transactions
        if t.get("status") == "completed"
        and start_date <= t.get("date", "") <= end_date
    ]
    total_sales = sum(t["grand_total"] for t in txns)
    total_tax = sum(t["tax"] for t in txns)
    total_cost = sum(t.get("cost_total", 0) for t in txns)
    refund_txns = [
        t for t in transactions
        if t.get("status") == "refunded"
        and start_date <= t.get("date", "") <= end_date
    ]
    total_refunds = sum(t["grand_total"] for t in refund_txns)

    return {
        "success": True,
        "period": {"start": start_date, "end": end_date},
        "transaction_count": len(txns),
        "total_sales": round(total_sales, 2),
        "total_tax": round(total_tax, 2),
        "total_cost": round(total_cost, 2),
        "gross_margin": round(total_sales - total_cost, 2),
        "refund_count": len(refund_txns),
        "total_refunds": round(total_refunds, 2),
        "net_sales": round(total_sales - total_refunds, 2),
    }


def top_products(start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    transactions = _load_json(_transactions_path())
    txns = [t for t in transactions if t.get("status") == "completed"]
    if start_date:
        txns = [t for t in txns if t.get("date", "") >= start_date]
    if end_date:
        txns = [t for t in txns if t.get("date", "") <= end_date]

    product_totals: Dict[str, Dict[str, Any]] = {}
    for t in txns:
        for item in t["items"]:
            pid = item["product_id"]
            if pid not in product_totals:
                product_totals[pid] = {"product_id": pid, "name": item["name"], "units_sold": 0, "revenue": 0.0}
            product_totals[pid]["units_sold"] += item["quantity"]
            product_totals[pid]["revenue"] += item["line_total"]

    ranked = sorted(product_totals.values(), key=lambda x: -x["revenue"])[:limit]
    for r in ranked:
        r["revenue"] = round(r["revenue"], 2)
    return {"success": True, "products": ranked}


def end_of_day(register_id: str = "REG-1", expected_cash: Optional[float] = None) -> Dict[str, Any]:
    """End-of-day register close: reconcile cash, summarize sales."""
    today = _today()
    report = sales_by_date(today)

    transactions = _load_json(_transactions_path())
    day_txns = [t for t in transactions if t.get("date") == today and t.get("status") == "completed"]

    by_method: Dict[str, float] = {}
    for t in day_txns:
        m = t.get("payment_method", "unknown")
        by_method[m] = round(by_method.get(m, 0) + t["grand_total"], 2)

    result = {
        "success": True,
        "date": today,
        "register_id": register_id,
        "sales_summary": report,
        "by_payment_method": by_method,
        "cash_expected": by_method.get("cash", 0),
    }

    if expected_cash is not None:
        result["cash_counted"] = round(expected_cash, 2)
        result["cash_variance"] = round(expected_cash - by_method.get("cash", 0), 2)
        result["cash_status"] = "balanced" if abs(result["cash_variance"]) < 0.01 else "variance"

    return result
