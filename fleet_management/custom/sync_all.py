import frappe

@frappe.whitelist()
def run_all_traccar_syncs():
    try:
        from fleet_management.custom.create_traccar_device import bulk_register_employees_to_traccar
        from fleet_management.custom.create_user_traccar import bulk_register_users_to_traccar
        from fleet_management.custom.company_hooks import sync_all_companies_to_traccar

        results = {}

        # Step 1: Register Users
        try:
            results["users"] = bulk_register_users_to_traccar()
            frappe.logger().info("✅ Users registered successfully.")
        except Exception as e:
            results["users"] = {"error": str(e)}
            frappe.logger().error(f"❌ Failed user sync: {str(e)}")
            frappe.log_error(frappe.get_traceback(), "User Sync Error")

        # Step 2: Sync Companies
        try:
            results["companies"] = sync_all_companies_to_traccar()
            frappe.logger().info("✅ Companies synced successfully.")
        except Exception as e:
            results["companies"] = {"error": str(e)}
            frappe.logger().error(f"❌ Failed company sync: {str(e)}")
            frappe.log_error(frappe.get_traceback(), "Company Sync Error")

        # Step 3: Register Employees (Devices)
        try:
            results["employees"] = bulk_register_employees_to_traccar()
            frappe.logger().info("✅ Employees (devices) registered successfully.")
        except Exception as e:
            results["employees"] = {"error": str(e)}
            frappe.logger().error(f"❌ Failed employee/device sync: {str(e)}")
            frappe.log_error(frappe.get_traceback(), "Employee/Device Sync Error")

        return {
            "status": "success",
            "message": "All Traccar syncs attempted.",
            "details": results
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Traccar Sync Critical Error")
        return {"status": "error", "message": f"Failed to run syncs: {str(e)}"}

