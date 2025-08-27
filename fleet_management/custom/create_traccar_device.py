import frappe
import requests
import json

@frappe.whitelist()
def bulk_register_employees_to_traccar():
    url = "https://traccar.mdm-wassal.shop/api/devices"
    headers = {
        "Authorization": "Basic YWRtaW46YWRtaW4=",  # Replace with env token if needed
        "Content-Type": "application/json"
    }

    # Fetch all employees with IQAMA (linked_employee_registration)
    employees = frappe.get_all("Employee", filters={"linked_employee_registration": ["!=", ""]},
                               fields=["name", "first_name", "linked_employee_registration", "company"])

    try:
        # Get already existing devices
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        existing_devices = res.json()
        existing_unique_ids = {device.get("uniqueId") for device in existing_devices}
    except Exception as e:
        frappe.throw(_("❌ Failed to fetch existing devices from Traccar: {0}").format(str(e)))

    success = 0
    fail = 0
    skipped = 0

    for emp in employees:
        name = emp.first_name
        unique_id = emp.linked_employee_registration
        company = emp.company

        if not (name and unique_id and company):
            skipped += 1
            continue

        if unique_id in existing_unique_ids:
            skipped += 1
            continue

        group_id = frappe.db.get_value("Company", company, "traccar_group_id")
        if not group_id:
            frappe.msgprint(f"❌ Traccar Group ID missing for company: {company}")
            skipped += 1
            continue

        payload = {
            "name": name,
            "uniqueId": unique_id,
            "groupId": int(group_id)
        }

        try:
            post_res = requests.post(url, headers=headers, json=payload)
            post_res.raise_for_status()
            success += 1
        except Exception as e:
            frappe.logger().error(f"❌ Failed to register device for {name}: {str(e)}")
            fail += 1

    msg = f"✅ {success} registered, ❌ {fail} failed, ⏭️ {skipped} skipped."
    frappe.msgprint(msg)


def create_traccar_device(doc, method):
    import json
    import requests
    import frappe

    employee_name = doc.first_name
    unique_id = doc.linked_employee_registration
    company = doc.company

    if not (employee_name and unique_id and company):
        frappe.msgprint("❌ Missing: name / IQAMA / company")
        return

    group_id = frappe.db.get_value("Company", company, "traccar_group_id")

    if not group_id:
        frappe.msgprint("❌ Traccar Group ID missing in company: " + company)
        return

    payload = {
        "name": employee_name,
        "uniqueId": unique_id,
        "groupId": int(group_id)
    }

    url = "https://traccar.mdm-wassal.shop/api/devices"
    headers = {
        "Authorization": "Basic YWRtaW46YWRtaW4=",  # Replace with your actual Base64 token
        "Content-Type": "application/json"
    }

    frappe.logger().info("🚀 Sending Traccar payload: " + json.dumps(payload))

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200 or response.status_code == 201:
            frappe.msgprint("✅ Device created in Traccar for: " + employee_name)
        else:
            frappe.logger().error(f"❌ Traccar API error [{response.status_code}]: {response.text}")
            frappe.msgprint(f"❌ Traccar API error [{response.status_code}]: {response.text}")
    except Exception as e:
        frappe.logger().error("❌ Request error: " + repr(e))
        frappe.msgprint("❌ Failed to create device for: " + employee_name + "<br>" + str(e))



