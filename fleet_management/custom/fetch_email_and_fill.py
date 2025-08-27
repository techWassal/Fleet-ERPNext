import frappe
import requests

SUPABASE_URL = "https://ifhgdipxetfordemdlyw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmaGdkaXB4ZXRmb3JkZW1kbHl3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMyNDU0MzIsImV4cCI6MjA1ODgyMTQzMn0.mN5TR5BALux0JOE4HSy4AfnhOQ-tcnBak5WeRbwaBoY"  # Keep it secure

@frappe.whitelist()
def sync_supabase_users_to_employee():
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Fetch Supabase users
        response = requests.get(f"{SUPABASE_URL}/rest/v1/auth_users?select=iqama_no,email", headers=headers)
        response.raise_for_status()
        users = response.json()

        updated = 0
        skipped = 0

        for user in users:
            iqama = user.get("iqama_no")
            email = user.get("email")

            if not iqama or not email:
                continue

            # Find employee with matching iqama
            employee = frappe.db.get_value("Employee", {"linked_employee_registration": iqama}, "name")

            if employee:
                emp_doc = frappe.get_doc("Employee", employee)

                # Only update if personal_email is empty
                if not emp_doc.personal_email:
                    emp_doc.personal_email = email
                    emp_doc.save(ignore_permissions=True)
                    updated += 1
                else:
                    skipped += 1

        return {
            "status": "success",
            "message": f"✅ Updated {updated} employee(s), skipped {skipped} already having emails."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to sync Supabase users to Employee")
        return {"status": "error", "message": str(e)}


