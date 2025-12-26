from mcp.server.fastmcp import FastMCP
from mcp_server.tools import (
    get_unprocessed_employees,
    get_all_employees,
    update_employee_row,
    update_experience_from_doj,
    reset_processed_flag_for_reprocessing,
)

mcp = FastMCP("excel-mcp-server")


# Tool 1: fetch_unprocessed
@mcp.tool()
def fetch_unprocessed():
    """
    Fetch all unprocessed rows from Excel.
    """
    return get_unprocessed_employees()


# Tool 1b: fetch_all_employees
@mcp.tool()
def fetch_all_employees():
    """
    Fetch ALL employee rows from Excel for comprehensive scanning and updating.
    This includes both processed and unprocessed employees.
    """
    return get_all_employees()



# Tool 2: apply_employee_update
@mcp.tool()
def apply_employee_update(
    row_id: int,
    updates: dict,
    reason: str,
    confidence: float,
):
    """
    Apply agent decision safely to Excel.
    """
    return update_employee_row(
        row_id=row_id,
        updates=updates,
        reason=reason,
        confidence=confidence,
    )


# Tool 3: update_experience
@mcp.tool()
def update_experience():
    """
    Recalculate Experience_Years for all employees based on their DOJ (Date of Joining).
    Run this periodically (e.g., once a year) to update experience automatically.
    """
    return update_experience_from_doj()


# Tool 4: reset_processed_flag
@mcp.tool()
def reset_processed_flag():
    """
    Reset Is_Processed flag to "No" for all employees to allow reprocessing.
    Use this after updating experience to reprocess all employees with new experience values.
    """
    return reset_processed_flag_for_reprocessing()


if __name__ == "__main__":
    mcp.run()
