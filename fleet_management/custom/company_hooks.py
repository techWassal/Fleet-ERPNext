import frappe
import json
from frappe.model.document import Document
import requests  # use Python requests instead of frappe.make_*

TRACCAR_URL = "https://traccar.mdm-wassal.shop/api/groups"
HEADERS = {
    "Authorization": "Basic YWRtaW46YWRtaW4=",
    "Content-Type": "application/json"
}

@frappe.whitelist()
def sync_all_companies_to_traccar():
    companies = frappe.get_all("Company", fields=["name", "company_name", "traccar_group_id"])
    try:
        existing_groups = requests.get(TRACCAR_URL, headers=HEADERS).json()
        existing_group_names = [g.get("name", "").lower() for g in existing_groups]

        created = 0
        skipped = 0
        failed = 0

        for company in companies:
            name = company.name
            group_id = company.traccar_group_id
            company_name = company.company_name.strip() if company.company_name else name

            if group_id:
                skipped += 1
                continue

            if company_name.lower() in existing_group_names:
                skipped += 1
                continue

            payload = {
                "name": company_name,
                "attributes": {
                    "company": company_name
                }
            }

            try:
                res = requests.post(TRACCAR_URL, headers=HEADERS, data=json.dumps(payload))
                res.raise_for_status()
                created_group = res.json()
                group_id = created_group.get("id")

                if group_id:
                    frappe.db.set_value("Company", name, "traccar_group_id", group_id)
                    created += 1
                else:
                    failed += 1

            except Exception:
                failed += 1

        return f"✅ {created} companies synced, ❌ {failed} failed, ⏭️ {skipped} skipped"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Traccar Bulk Company Sync Failed")
        return f"❌ Error: {str(e)}"

def traccar_group_create(doc, method):
    frappe.log_error("Trigger Hit", "Traccar Hook Triggered")

    company_name = doc.company_name.strip()
    if not company_name:
        frappe.throw("Company Name is required to sync with Traccar.")

    try:
        # Get existing groups to check for duplicates
        res = requests.get(TRACCAR_URL, headers=HEADERS)
        res.raise_for_status()
        existing_groups = res.json()

        for group in existing_groups:
            if group.get("name", "").strip().lower() == company_name.lower():
                doc.db_set("traccar_group_id", group.get("id"))
                frappe.msgprint(f"✅ Group '{company_name}' already exists in Traccar. Synced ID: {group.get('id')}")
                return

        # Create new group
        payload = {
            "name": company_name,
            "attributes": {
                "company": company_name
            }
        }
        create_res = requests.post(TRACCAR_URL, headers=HEADERS, data=json.dumps(payload))
        create_res.raise_for_status()
        created_group = create_res.json()

        group_id = created_group.get("id")
        if group_id:
            doc.db_set("traccar_group_id", group_id)
            frappe.msgprint(f"✅ Traccar group created with ID: {group_id}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Traccar Group Creation Failed")
        frappe.msgprint(f"❌ Error Occurred: {str(e)}")

def traccar_group_rename(doc, method, *args):
    group_id = doc.traccar_group_id
    new_name = doc.company_name.strip()

    if not group_id:
        frappe.msgprint("No Traccar Group ID found to rename.")
        return

    try:
        payload = {
            "id": int(group_id),
            "name": new_name,
            "attributes": {
                "company": new_name
            } 
        }
        update_url = f"{TRACCAR_URL}/{group_id}"
        res = requests.put(update_url, headers=HEADERS, data=json.dumps(payload))
        res.raise_for_status()

        frappe.msgprint(f"Traccar group renamed successfully to '{new_name}'.")

    except requests.exceptions.HTTPError as e:
        if res.status_code == 404:
            frappe.msgprint(f"Group with ID {group_id} not found in Traccar.")
        else:
            frappe.msgprint(f"Traccar Rename Failed: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Traccar Rename Failed")




