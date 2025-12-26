import asyncio
import json
import os
import time
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv  # type: ignore
from openai import OpenAI  # type: ignore

from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
from mcp.client.session import ClientSession  # type: ignore

from utils.config_loader import load_config
from utils.logger import setup_logger

# Load configuration
load_dotenv()
config = load_config()
logger = setup_logger(
    "excel_mcp.agent",
    log_file=config.get("logging", {}).get("file"),
    level=config.get("logging", {}).get("level", "INFO")
)

# Initialize OpenAI client
openai_config = config.get("openai", {})
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def llm_decide(employee_row: dict, retry_count: int = 0) -> dict:
    """
    Get AI decision for employee classification with retry logic.
    
    Args:
        employee_row: Employee data dictionary
        retry_count: Current retry attempt number
    
    Returns:
        Decision dictionary with Department, Designation, Salary_Band, Reason, Confidence
    """
    rules = config.get("rules", {})
    desig_rules = rules.get("designation", {})
    salary_rules = rules.get("salary_band", {})
    
    prompt = f"""
You are an HR classification agent.

CRITICAL RULES:
- You MUST provide values for ALL three fields: Department, Designation, and Salary_Band
- Use only allowed dropdown values. Do not use empty strings or leave fields blank.
- Do not invent values outside the allowed lists.

Designation rules (based on Experience_Years):
- Less than {desig_rules.get('intern_max_years', 2)} years → Intern
- {desig_rules.get('intern_max_years', 2)}-{desig_rules.get('junior_max_years', 4)} years → Junior
- {desig_rules.get('junior_max_years', 4)+1}-{desig_rules.get('senior_max_years', 7)} years → Senior
- {desig_rules.get('lead_min_years', 8)}+ years → Lead

Department selection:
- Look at the employee's Role, Department (if already exists), or infer from context
- If unclear, choose the most appropriate from: Web, AI, HR, Finance, Operations

Salary_Band selection:
- L1: Entry level (Intern, Junior with <{salary_rules.get('l1_max_years', 3)} years)
- L2: Mid level (Junior with {salary_rules.get('l1_max_years', 3)}-{salary_rules.get('l2_max_years', 6)} years, Senior)
- L3: Senior level (Lead, Senior with {salary_rules.get('l3_min_years', 7)}+ years)

Allowed values:
- Departments: Web, AI, HR, Finance, Operations
- Designations: Intern, Junior, Senior, Lead
- Salary_Band: L1, L2, L3

Employee data:
{json.dumps(employee_row, indent=2)}

Return STRICT JSON (ALL fields must have valid values, NO empty strings):
{{
  "Department": "Web",
  "Designation": "Junior",
  "Salary_Band": "L1",
  "Reason": "Explanation of your decisions",
  "Confidence": 0.95
}}
"""

    max_retries = openai_config.get("max_retries", 3)
    retry_delay = openai_config.get("retry_delay", 2)
    model = openai_config.get("model", "gpt-4o-mini")
    temperature = openai_config.get("temperature", 0)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        content = response.choices[0].message.content
        
        # Strip markdown code blocks if present (```json ... ```)
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        elif content.startswith("```"):
            content = content[3:]   # Remove ```
        
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        
        content = content.strip()
        
        try:
            decision = json.loads(content)
            logger.debug(f"LLM decision: {decision}")
            return decision
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response as JSON: {e}")
            logger.error(f"Response content: {content}")
            if retry_count < max_retries:
                logger.info(f"Retrying LLM call (attempt {retry_count + 1}/{max_retries})...")
                time.sleep(retry_delay)
                return llm_decide(employee_row, retry_count + 1)
            raise
    except Exception as e:
        if retry_count < max_retries:
            logger.warning(f"LLM call failed (attempt {retry_count + 1}/{max_retries}): {e}")
            time.sleep(retry_delay)
            return llm_decide(employee_row, retry_count + 1)
        logger.error(f"LLM call failed after {max_retries} attempts: {e}")
        raise


async def run_agent():
    """Run the employee classification agent."""
    logger.info("=" * 60)
    logger.info("Starting MCP Employee Classification Agent")
    logger.info("=" * 60)
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
        cwd=os.getcwd(),
    )

    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "start_time": time.time()
    }

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session first
                await session.initialize()
                
                # List available tools for debugging
                tools = await session.list_tools()
                logger.info(f"Available MCP tools: {[tool.name for tool in tools.tools]}")
                
                # Fetch ALL employees for comprehensive scanning
                logger.info("Fetching ALL employees for comprehensive scanning...")
                result = await session.call_tool("fetch_all_employees", arguments={})
                
                # Parse the result content (MCP returns CallToolResult with content as list of text)
                if result.isError:
                    logger.error(f"Error calling fetch_all_employees tool: {result.content}")
                    employees = []
                elif result.content and len(result.content) > 0:
                    # FastMCP serializes dict returns as JSON in content[0].text
                    content_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                    result_data = json.loads(content_text)
                    employees = result_data.get("employees", [])
                else:
                    logger.info("No employees found")
                    employees = []

                stats["total"] = len(employees)
                
                if stats["total"] == 0:
                    logger.info("No employees to process. Exiting.")
                    return

                logger.info(f"Found {stats['total']} unprocessed employees")
                logger.info("-" * 60)

                # Process each employee
                for idx, item in enumerate(employees, 1):
                    try:
                        row_id = item["row_id"]
                        data = item["data"]
                        emp_name = data.get("Name", f"Row {row_id}")

                        logger.info(f"[{idx}/{stats['total']}] Processing {emp_name} (row {row_id})...")
                        
                        # Initialize updates dict
                        updates = {}
                        needs_update = False
                        
                        # Calculate Experience_Years from DOJ - ALWAYS update to keep it current
                        doj = data.get("DOJ")
                        current_experience = data.get("Experience_Years")
                        
                        calculated_experience = None
                        if doj:
                            try:
                                # Parse DOJ
                                doj_date = None
                                if isinstance(doj, str):
                                    doj_date = pd.to_datetime(doj).date()
                                elif hasattr(doj, 'date'):
                                    doj_date = doj.date()
                                elif isinstance(doj, datetime):
                                    doj_date = doj.date()
                                elif isinstance(doj, pd.Timestamp):
                                    doj_date = doj.date()
                                
                                # Calculate experience if we have a valid date
                                if doj_date:
                                    today = datetime.now().date()
                                    years_diff = today - doj_date
                                    calculated_experience = round(years_diff.days / 365.25, 1)
                                    
                                    # ALWAYS update experience to ensure it's current
                                    updates["Experience_Years"] = calculated_experience
                                    needs_update = True
                                    logger.debug(f"Updating experience for row {row_id}: {current_experience} -> {calculated_experience} years")
                            except Exception as e:
                                logger.warning(f"Could not calculate experience for row {row_id}: {e}")
                        
                        # Use calculated experience for decision-making if available
                        experience_for_decision = calculated_experience if calculated_experience is not None else current_experience
                        if experience_for_decision is not None:
                            # Update data with current experience for better decision-making
                            data["Experience_Years"] = experience_for_decision
                        
                        # Get AI decision based on current data (including updated experience)
                        decision = llm_decide(data)
                        
                        # Extract and validate decision values
                        dept = str(decision.get("Department", "")).strip()
                        designation = str(decision.get("Designation", "")).strip()
                        salary_band = str(decision.get("Salary_Band", "")).strip()
                        
                        # Check ALL columns for empty values and update them
                        # Check Department
                        current_dept = data.get("Department")
                        if (not current_dept or pd.isna(current_dept) or str(current_dept).strip() == "") and dept:
                            updates["Department"] = dept
                            needs_update = True
                        elif current_dept and dept and str(current_dept).strip() != str(dept).strip():
                            # Re-evaluate if designation changed (e.g., Junior to Senior)
                            updates["Department"] = dept
                            needs_update = True
                            logger.info(f"Updating Department for row {row_id}: {current_dept} -> {dept}")
                        
                        # Check Designation - auto-update if experience changed significantly
                        current_designation = data.get("Designation")
                        if (not current_designation or pd.isna(current_designation) or str(current_designation).strip() == "") and designation:
                            updates["Designation"] = designation
                            needs_update = True
                        elif current_designation and designation and str(current_designation).strip() != str(designation).strip():
                            # Auto-update designation if it should change (e.g., Junior -> Senior as experience grows)
                            updates["Designation"] = designation
                            needs_update = True
                            logger.info(f"Auto-updating Designation for row {row_id}: {current_designation} -> {designation} (Experience: {experience_for_decision} years)")
                        
                        # Check Salary_Band
                        current_salary = data.get("Salary_Band")
                        if (not current_salary or pd.isna(current_salary) or str(current_salary).strip() == "") and salary_band:
                            updates["Salary_Band"] = salary_band
                            needs_update = True
                        elif current_salary and salary_band and str(current_salary).strip() != str(salary_band).strip():
                            # Update salary band if designation changed
                            updates["Salary_Band"] = salary_band
                            needs_update = True
                            logger.info(f"Updating Salary_Band for row {row_id}: {current_salary} -> {salary_band}")
                        
                        # Check ALL columns for empty values (comprehensive scanning)
                        for col_name, col_value in data.items():
                            # Skip system columns and already processed columns
                            if col_name in ["Is_Processed", "AI_Decision_Reason", "Confidence_Score", "Last_Processed_On", 
                                          "Processing_Version", "Rule_Applied", "Emp_ID", "Name", "DOJ", "Role", "Status"]:
                                continue
                            
                            # Check if column is empty and we have a value to fill
                            is_empty = (col_value is None or pd.isna(col_value) or str(col_value).strip() == "")
                            
                            if is_empty:
                                # For dropdown columns, we can't auto-fill without AI decision
                                # But we log it for visibility
                                if col_name not in updates:
                                    logger.debug(f"Column {col_name} is empty for row {row_id} but no value available to fill")
                        
                        # Skip if no valid updates needed
                        if not needs_update and not updates:
                            logger.debug(f"No updates needed for row {row_id}, skipping")
                            stats["skipped"] += 1
                            continue
                        
                        logger.debug(f"Updating row {row_id} with: {updates}")
                        result = await session.call_tool(
                            "apply_employee_update",
                            arguments={
                                "row_id": int(row_id),
                                "updates": updates,
                                "reason": str(decision.get("Reason", "")),
                                "confidence": float(decision.get("Confidence", 0.0)),
                            },
                        )
                        if result.isError:
                            logger.error(f"ERROR: Error updating row {row_id}: {result.content}")
                            stats["failed"] += 1
                        else:
                            logger.info(f"SUCCESS: Updated row {row_id} - {dept}/{designation}/{salary_band}")
                            stats["success"] += 1
                    except Exception as e:
                        logger.error(f"ERROR: Error processing row {row_id}: {e}", exc_info=True)
                        stats["failed"] += 1
                        continue

    except Exception as e:
        logger.error(f"Fatal error in agent: {e}", exc_info=True)
        raise
    finally:
        # Print summary statistics
        elapsed_time = time.time() - stats["start_time"]
        logger.info("=" * 60)
        logger.info("Processing Summary")
        logger.info("=" * 60)
        logger.info(f"Total employees:     {stats['total']}")
        logger.info(f"Successfully processed: {stats['success']}")
        logger.info(f"Failed:             {stats['failed']}")
        logger.info(f"Skipped:            {stats['skipped']}")
        logger.info(f"Time elapsed:       {elapsed_time:.2f} seconds")
        if stats['total'] > 0:
            logger.info(f"Success rate:       {(stats['success']/stats['total']*100):.1f}%")
        logger.info("=" * 60)




if __name__ == "__main__":
    asyncio.run(run_agent())
