import frappe
import requests
import json
from datetime import date, datetime

SUPABASE_URL = "https://ifhgdipxetfordemdlyw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmaGdkaXB4ZXRmb3JkZW1kbHl3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzI0NTQzMiwiZXhwIjoyMDU4ODIxNDMyfQ.eXi20s2f8utoN6_q57Yqf5i0hzaJc6reWFtXM-VjvJ8"

def default_serializer(obj):
    """Convert date/datetime to ISO string for JSON serialization"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def sync_vehicle_data_to_supabase():
    try:
        # Fetch records from ERPNext Doctype
        records = frappe.get_all(
            "Vehicle Data",
            fields=[
                "plate_number",
                "plate_type",
                "vehicle_status",
                "branch_name",
                "vehicle_maker",
                "vehicle_model",
                "model_year",
                "sequence_number",
                "chassis_number",
                "major_color",
                "body_type",
                "actual_driver_id",
                "actual_driver_name",
                "license_expiry_date",
                "inspection_expiry_date",
                "istemarah_issue_date",
                "ownership_date",
                "vehicle_status2",
                "mvpi_status",
                "insurance_status",
                "restriction_status"
            ]
        )

        print(f"🔍 Found {len(records)} Vehicle Data records in ERPNext")

        if not records:
            print("⚠️ No records found to sync.")
            return

        # Prepare headers
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json"
        }

        # Send to Supabase (insert in bulk)
        url = f"{SUPABASE_URL}/rest/v1/vehicle_data"

        # Debugging: print payload before sending
        print("📦 Payload to be sent:")
        print(json.dumps(records, indent=2, default=default_serializer))

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(records, default=default_serializer)
        )

        # Debugging: print response details
        print(f"✅ Status Code: {response.status_code}")
        try:
            print("🔍 Supabase Response:", response.json())
        except Exception:
            print("🔍 Raw Supabase Response:", response.text)

    except Exception as e:
        print(f"❌ Error in sync_vehicle_data_to_supabase: {e}")

