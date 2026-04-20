import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, today, date_diff, nowdate
from frappe.utils.nestedset import get_descendants_of

from erpnext.stock.report.batch_wise_balance_history.batch_wise_balance_history import (
    get_stock_ledger_entries_for_batch_no,
    get_stock_ledger_entries_for_batch_bundle,
)


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def _precision():
    return cint(frappe.db.get_default("float_precision")) or 3


def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},
        {"label": _("Parent Item Group"), "fieldname": "parent_item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": _("Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 140},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 120},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 110, "precision": 2},
        {"label": _("Balance Value"), "fieldname": "balance_value", "fieldtype": "Currency", "width": 130},
        {"label": _("Entered Via"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 140},
        {"label": _("Document"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 170},
        {"label": _("Entry Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": _("Age (Days)"), "fieldname": "age", "fieldtype": "Int", "width": 90},
        {"label": _("Supplier"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 220},
        {"label": _("Supplier Group"), "fieldname": "supplier_group", "fieldtype": "Link", "options": "Supplier Group", "width": 160},
    ]


def get_data(filters):
    filters.setdefault("from_date", "1900-01-01")
    filters.setdefault("to_date", filters.get("as_on_date") or nowdate())

    movements = get_stock_ledger_entries_for_batch_no(filters) + get_stock_ledger_entries_for_batch_bundle(filters)
    if not movements:
        return []

    precision = _precision()

    balances = {}
    for m in movements:
        if not m.get("batch_no"):
            continue
        key = (m["item_code"], m["batch_no"])
        b = balances.setdefault(key, {"qty": 0.0, "value": 0.0})
        b["qty"] += flt(m["actual_qty"])
        b["value"] += flt(m["stock_value_difference"])

    positive = {k: v for k, v in balances.items() if flt(v["qty"], precision) > 0}
    if not positive:
        return []

    item_filter = filters.get("item_group")
    item_map = get_item_info({k[0] for k in positive.keys()})
    if item_filter:
        allowed = set(get_descendants_of("Item Group", item_filter)) | {item_filter}
        positive = {k: v for k, v in positive.items() if item_map.get(k[0], {}).get("item_group") in allowed}
        if not positive:
            return []

    origin_map = get_batch_origins(set(positive.keys()))
    supplier_map = get_supplier_map(origin_map.values())

    today_d = getdate(today())
    rows = []
    for (item_code, batch_no), bal in positive.items():
        origin = origin_map.get((item_code, batch_no)) or {}
        item = item_map.get(item_code) or {}
        v_type = origin.get("voucher_type")
        v_no = origin.get("voucher_no")
        posting_date = origin.get("posting_date")
        valuation_rate = (bal["value"] / bal["qty"]) if bal["qty"] else 0
        balance_value = bal["qty"] * valuation_rate
        supplier = supplier_map.get((v_type, v_no)) or {}

        rows.append({
            "item_code": item_code,
            "item_name": item.get("item_name"),
            "item_group": item.get("item_group"),
            "parent_item_group": item.get("parent_item_group"),
            "batch_no": batch_no,
            "valuation_rate": flt(valuation_rate, precision),
            "balance_qty": flt(bal["qty"], precision),
            "balance_value": flt(balance_value, precision),
            "voucher_type": v_type,
            "voucher_no": v_no,
            "posting_date": posting_date,
            "age": date_diff(today_d, posting_date) if posting_date else None,
            "supplier_name": supplier.get("supplier_name") or supplier.get("supplier"),
            "supplier": supplier.get("supplier"),
            "supplier_group": supplier.get("supplier_group"),
        })

    rows = apply_supplier_filters(rows, filters)
    rows.sort(key=lambda r: (r["item_code"] or "", r["posting_date"] or getdate("1900-01-01")))
    return rows


def apply_supplier_filters(rows, filters):
    s = filters.get("supplier")
    sg = filters.get("supplier_group")
    if not s and not sg:
        return rows
    out = []
    for r in rows:
        if s and r.get("supplier") != s:
            continue
        if sg and r.get("supplier_group") != sg:
            continue
        out.append(r)
    return out


def get_batch_origins(batch_keys):
    """Return the earliest INWARD movement per (item_code, batch_no) along with
    voucher_type, voucher_no, posting_date, incoming_rate. Used to populate the
    "Entered Via / Document / Entry Date / Supplier" columns.
    """
    if not batch_keys:
        return {}

    by_item = {}
    for ic, bn in batch_keys:
        by_item.setdefault(ic, set()).add(bn)

    origins = {}
    for item_code, batches in by_item.items():
        legacy = frappe.db.sql(
            """
            SELECT item_code, batch_no, posting_date, posting_time, creation,
                   voucher_type, voucher_no, incoming_rate
            FROM `tabStock Ledger Entry`
            WHERE is_cancelled = 0
              AND docstatus < 2
              AND actual_qty > 0
              AND item_code = %(ic)s
              AND batch_no IN %(batches)s
            """,
            {"ic": item_code, "batches": tuple(batches)},
            as_dict=True,
        )
        bundled = frappe.db.sql(
            """
            SELECT sle.item_code, e.batch_no, sle.posting_date, sle.posting_time, sle.creation,
                   sle.voucher_type, sle.voucher_no, e.incoming_rate
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabSerial and Batch Entry` e ON e.parent = sle.serial_and_batch_bundle
            WHERE sle.is_cancelled = 0
              AND sle.docstatus < 2
              AND sle.has_batch_no = 1
              AND e.qty > 0
              AND sle.item_code = %(ic)s
              AND e.batch_no IN %(batches)s
            """,
            {"ic": item_code, "batches": tuple(batches)},
            as_dict=True,
        )
        for r in legacy + bundled:
            key = (r["item_code"], r["batch_no"])
            sort_key = (r["posting_date"], r["posting_time"], r["creation"])
            existing = origins.get(key)
            if existing is None or sort_key < existing["_sort"]:
                origins[key] = {
                    "voucher_type": r["voucher_type"],
                    "voucher_no": r["voucher_no"],
                    "posting_date": r["posting_date"],
                    "incoming_rate": r["incoming_rate"],
                    "_sort": sort_key,
                }
    return origins


def get_item_info(item_codes):
    if not item_codes:
        return {}
    rows = frappe.db.sql(
        """
        SELECT i.name AS item_code, i.item_name, i.item_group
        FROM `tabItem` i
        WHERE i.name IN %(items)s
        """,
        {"items": list(item_codes)},
        as_dict=True,
    )
    top_parent_map = build_top_parent_map({r["item_group"] for r in rows if r.get("item_group")})
    for r in rows:
        r["parent_item_group"] = top_parent_map.get(r["item_group"])
    return {r["item_code"]: r for r in rows}


def build_top_parent_map(item_groups):
    """For each item_group, return its top-level ancestor (a node with no parent).

    Walks `parent_item_group` upward until a root (parent IS NULL) is reached.
    A root maps to itself.
    """
    if not item_groups:
        return {}

    rows = frappe.db.sql(
        """SELECT name, parent_item_group FROM `tabItem Group`""",
        as_dict=True,
    )
    parent_of = {r["name"]: r["parent_item_group"] for r in rows}

    cache = {}

    def walk(name):
        if name in cache:
            return cache[name]
        chain = []
        cur = name
        while cur is not None:
            if cur in cache:
                result = cache[cur]
                break
            parent = parent_of.get(cur)
            if not parent:
                result = cur
                break
            chain.append(cur)
            cur = parent
        else:
            result = name
        for n in chain:
            cache[n] = result
        cache[name] = result
        return result

    return {ig: walk(ig) for ig in item_groups}


def get_supplier_map(origins):
    by_type = {}
    for o in origins:
        v_type = o.get("voucher_type")
        v_no = o.get("voucher_no")
        if v_type and v_no:
            by_type.setdefault(v_type, set()).add(v_no)

    supplier_doctypes = {
        "Purchase Receipt": "supplier",
        "Purchase Invoice": "supplier",
        "Stock Entry": "supplier",
        "Subcontracting Receipt": "supplier",
    }

    voucher_to_supplier = {}
    all_supplier_codes = set()
    for v_type, vouchers in by_type.items():
        field = supplier_doctypes.get(v_type)
        if not field or not frappe.db.exists("DocType", v_type):
            continue
        meta = frappe.get_meta(v_type)
        if not meta.has_field(field):
            continue
        rows = frappe.db.sql(
            f"""SELECT name, `{field}` AS supplier FROM `tab{v_type}` WHERE name IN %(v)s""",
            {"v": list(vouchers)},
            as_dict=True,
        )
        for r in rows:
            voucher_to_supplier[(v_type, r["name"])] = r["supplier"]
            if r["supplier"]:
                all_supplier_codes.add(r["supplier"])

    info_map = {}
    if all_supplier_codes:
        for r in frappe.db.sql(
            """SELECT name, supplier_name, supplier_group FROM `tabSupplier` WHERE name IN %(v)s""",
            {"v": list(all_supplier_codes)},
            as_dict=True,
        ):
            info_map[r["name"]] = r

    return {
        key: {
            "supplier": code,
            "supplier_name": (info_map.get(code) or {}).get("supplier_name") or code,
            "supplier_group": (info_map.get(code) or {}).get("supplier_group"),
        }
        for key, code in voucher_to_supplier.items()
    }
