import frappe
import requests
import json
from datetime import date, datetime
from decimal import Decimal

SUPABASE_URL = "https://ifhgdipxetfordemdlyw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmaGdkaXB4ZXRmb3JkZW1kbHl3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzI0NTQzMiwiZXhwIjoyMDU4ODIxNDMyfQ.eXi20s2f8utoN6_q57Yqf5i0hzaJc6reWFtXM-VjvJ8"

def default_serializer(obj):
    """Convert date/datetime/Decimal to JSON-safe values."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def sync_employee_registration_info_to_supabase():
    try:
        # Fetch records from ERPNext Doctype
        records = frappe.get_all(
            "Employee Registration",
            fields=[
                "full_name",
                "identity_number",
                "iqama_number",
                "worker_id",
                "gender",
                "nationality",
                "occupation",
                "company_id",
                "company_name",
                "border_number",
                "worker_type",
                "date_of_birth",
                "joining_date",
                "entry_date_ksa",
                "iqama_expiry",
                "basic_salary",
                "housing",
                "commissions",
                "other_allowances",
                "total_salary",
                "contributable_salary",
                "in_gosi_data",
                "in_worker_data",
                "gosi_worker_data",
                "worker_data",
                "ready_to_register",
                "registered_employee",
                "gosi_status",
                "hrsd_status",
            ]
        )

        print(f"🔍 Found {len(records)} Employee Registration records in ERPNext")
        if not records:
            print("⚠️ No records found to sync.")
            return

        # Prepare headers
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json"
        }

        # Supabase table endpoint
        url = f"{SUPABASE_URL}/rest/v1/employee_registration_info"

        # Debug: payload preview
        print("📦 Payload to be sent:")
        print(json.dumps(records, indent=2, default=default_serializer))

        # Send to Supabase (bulk insert)
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(records, default=default_serializer)
        )

        # Debug: response details
        print(f"✅ Status Code: {response.status_code}")
        try:
            print("🔍 Supabase Response:", response.json())
        except Exception:
            print("🔍 Raw Supabase Response:", response.text)

    except Exception as e:
        print(f"❌ Error in sync_employee_registration_info_to_supabase: {e}")

