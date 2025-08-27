import frappe
import requests
import json
from datetime import date, datetime

SUPABASE_URL = "https://ifhgdipxetfordemdlyw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmaGdkaXB4ZXRmb3JkZW1kbHl3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzI0NTQzMiwiZXhwIjoyMDU4ODIxNDMyfQ.eXi20s2f8utoN6_q57Yqf5i0hzaJc6reWFtXM-VjvJ8"  # replace with actual key

SUPABASE_HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

def safe_date(value):
    """Convert date/datetime to string if not None"""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value if value else None

@frappe.whitelist()
def sync_employees_to_supabase():
    try:
        employees = frappe.get_all(
            "Employee",
            fields=[
                "name",
                "first_name",
                "gender",
                "date_of_birth",
                "date_of_joining",
                "status",
                "company",
                "linked_employee_registration"
            ]
        )

        print(f"📌 Employees fetched from ERPNext: {len(employees)}")

        formatted_employees = []
        for emp in employees:
            mapped = {
                "employee_id": emp.get("name"),
                "first_name": emp.get("first_name"),
                "gender": emp.get("gender"),
                "date_of_birth": safe_date(emp.get("date_of_birth")),
                "date_of_joining": safe_date(emp.get("date_of_joining")),
                "status": emp.get("status"),
                "company": emp.get("company"),
                "iqama_number": emp.get("linked_employee_registration")
            }
            formatted_employees.append(mapped)

        print("📦 Payload to send to Supabase:")
        print(json.dumps(formatted_employees, indent=2))

        url = f"{SUPABASE_URL}/rest/v1/employee"
        response = requests.post(url, headers=SUPABASE_HEADERS, data=json.dumps(formatted_employees))

        print("🔄 Supabase response:")
        print("Status:", response.status_code)
        print("Body:", response.text)

        if response.status_code in [200, 201]:
            frappe.msgprint(f"✅ Synced {len(formatted_employees)} employees to Supabase")
        else:
            frappe.msgprint(f"❌ Sync failed → {response.status_code}\n{response.text}")

    except Exception as e:
        print("🚨 Exception occurred:", str(e))
        frappe.msgprint(f"🚨 Exception: {str(e)}")

