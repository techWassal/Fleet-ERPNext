# fleet_management/custom/create_user_traccar.py

import frappe
import json
import requests
from frappe import _

@frappe.whitelist()
def bulk_register_users_to_traccar():
    # Get all users except system ones
    users = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "email", "full_name", "first_name"])

    url = "https://traccar.mdm-wassal.shop/api/users"
    headers = {
        "Authorization": "Basic YWRtaW46YWRtaW4=",  # Replace with env variable or secure method in production
        "Content-Type": "application/json"
    }

    success = 0
    fail = 0
    skipped = 0

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        existing_users = res.json()
        existing_emails = [u.get("email") for u in existing_users if u.get("email")]
    except Exception as e:
        frappe.throw(_("❌ Failed to fetch existing users from Traccar: {0}").format(str(e)))

    for user in users:
        email = user.email
        if not email or email in ["Administrator", "Guest"]:
            skipped += 1
            continue
        if email in existing_emails:
            skipped += 1
            continue

        name = user.full_name or user.first_name or email

        payload = {
            "name": name,
            "email": email,
            "password": "user@1234",  # Consider generating unique passwords or syncing from Frappe
            "readonly": True,
            "administrator": False
        }

        try:
            post_res = requests.post(url, headers=headers, data=json.dumps(payload))
            post_res.raise_for_status()
            success += 1
        except Exception as e:
            fail += 1

    return f"✅ {success} registered, ❌ {fail} failed, ⏭️ {skipped} skipped."

def create_traccar_user(doc, method):
    import requests
    import json

    # Skip system users
    if doc.email in ["Administrator", "Guest"]:
        print("System user skipped.")
        return

    base_url = "https://traccar.mdm-wassal.shop/api"
    headers = {
        "Authorization": "Basic YWRtaW46YWRtaW4=",  # Replace if needed
        "Content-Type": "application/json"
    }

    email_exists = 0
    user_id = None

    # Step 1: Check if user already exists
    try:
        res = requests.get(base_url + "/users", headers=headers)
        if res.status_code == 200:
            users = res.json()
            for u in users:
                if u.get("email") == doc.email:
                    email_exists = 1
                    user_id = u.get("id")
                    print("User already exists in Traccar. ID:", user_id)
                    break
        else:
            print("Failed to fetch users from Traccar. Code:", res.status_code)
            return
    except Exception as e:
        print("Traccar user fetch failed:", str(e))
        return

    # Step 2: If user doesn't exist, create new one
    if email_exists == 0:
        full_name = doc.full_name or doc.first_name or doc.email

        data = {
            "name": full_name,
            "email": doc.email,
            "password": "user@1234",
            "readonly": True,
            "administrator": False
        }

        try:
            res = requests.post(base_url + "/users", headers=headers, data=json.dumps(data))
            if res.status_code == 200 or res.status_code == 201:
                print("✅ User created in Traccar.")
                user_id = res.json().get("id")
            else:
                print("❌ Traccar user creation failed. Code:", res.status_code, "Response:", res.text)
                return
        except Exception as e:
            print("❌ Exception during user creation:", str(e))
            return

    # Step 3: Get all group IDs from ERPNext's Company Doctype
    try:
        companies = frappe.get_all("Company", fields=["name", "traccar_group_id"])
    except Exception as e:
        print("❌ Failed to fetch Company Doctype:", str(e))
        return

    # Step 4: Link user to each group using Traccar's /permissions API
    success = 0
    fail = 0

    for c in companies:
        group_id = c.get("traccar_group_id")
        if group_id:
            try:
                res = requests.post(
                    base_url + "/permissions",
                    headers=headers,
                    data=json.dumps({
                        "userId": user_id,
                        "groupId": int(group_id)
                    })
                )
                if res.status_code == 200 or res.status_code == 204:
                    print("✅ Linked user to group:", group_id)
                    success = success + 1
                else:
                    print("❌ Failed to link group:", group_id, "Code:", res.status_code)
                    fail = fail + 1
            except Exception as e:
                print("❌ Exception while linking group:", group_id, str(e))
                fail = fail + 1
        else:
            print("⚠️ Skipped company without traccar_group_id:", c["name"])

    print(str(success) + " groups linked successfully, " + str(fail) + " failed.")


def delete_traccar_user(doc, method):
    import requests
    import frappe

    if doc.email in ["Administrator", "Guest"]:
        frappe.msgprint("⏩ Skipped system user: " + doc.email)
    else:
        url = "https://traccar.mdm-wassal.shop/api/users"
        headers = {
            "Authorization": "Basic YWRtaW46YWRtaW4=",
            "Content-Type": "application/json"
        }

        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                traccar_users = res.json()
                for u in traccar_users:
                    if u.get("email") == doc.email:
                        user_id = str(u.get("id"))
                        delete_url = url + "/" + user_id
                        try:
                            delete_res = requests.delete(delete_url, headers=headers)
                            if delete_res.status_code in [200, 204]:
                                frappe.msgprint("🗑️ Traccar user deleted successfully: " + doc.email)
                            else:
                                frappe.msgprint("❌ Could not delete from Traccar [" + str(delete_res.status_code) + "]: " + delete_res.text)
                        except Exception as e:
                            frappe.msgprint("❌ Exception during Traccar deletion: " + str(e))
                        break
            else:
                frappe.msgprint("❌ Failed to fetch Traccar users [" + str(res.status_code) + "]")
        except Exception as e:
            frappe.msgprint("❌ Error contacting Traccar: " + str(e))

