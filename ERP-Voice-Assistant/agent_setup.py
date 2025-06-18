import requests
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from loguru import logger
from typing import Literal, Optional
import json

# --- Agent Configuration ---
model = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens=1024, # Increased for more complex reasoning
)

memory = InMemorySaver()

# --- ERP API Configuration ---
BASE_URL = "http://127.0.0.1:5000/api"

# --- Tool Definitions for ERP Co-Pilot ---

def navigate_to_page(target_app: Literal["crm", "inventory", "orders", "hr", "finance", "dashboard"]):
    """
    Navigates the user to a specific module page in the ERP system's UI.
    Call this first when a user wants to start a new task, like creating a new customer or product.
    For example, if the user says 'I want to add a new customer', navigate to 'crm'.
    """
    if target_app == 'dashboard':
        page_url = '/'
    else:
        page_url = f"/{target_app}_vue"
    url = f"{BASE_URL}/ui_command"
    payload = {
        "action": "navigate",
        "target_app": target_app,
        "url": page_url
    }
    # === START CHANGE ===
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    # === END CHANGE ===
    
    logger.info(f"▶️ Navigating to {target_app} module at {page_url}...")
    try:
        # === CHANGE THIS LINE ===
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        logger.success(f"✅ Navigation to {target_app} successful.")
        return f"Okay, I have navigated to the {target_app} page."
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to navigate: {e}")
        return "Sorry, I couldn't navigate to that page right now."

def fill_form_field(target_app: str, field_id: str, value: str):
    """
    Fills a specific field in a form on the current ERP page for immediate user feedback.
    Use this repeatedly as the user provides information for a new record.
    """
    url = f"{BASE_URL}/ui_command"
    payload = {
        "action": "fill_field",
        "target_app": target_app,
        "field_id": field_id,
        "value": value
    }
    # === START CHANGE ===
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    # === END CHANGE ===

    logger.info(f"📝 Filling field '{field_id}' with value '{value}' in {target_app}...")
    try:
        # === CHANGE THIS LINE ===
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        logger.debug(f"🔍 Server response: {response.text}")
        logger.success(f"✅ Field '{field_id}' filled.")
        return f"Field {field_id} filled."
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Server error response: {e.response.text if e.response else 'No response'}")
        logger.error(f"❌ Failed to fill field: {e}")
        return "There was an error filling that field."

def create_customer(
    name: str,
    email: str,
    company: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    status: Literal["Active", "Lead", "Inactive"] = "Lead",
    lead_score: Optional[int] = None,
    notes: Optional[str] = None
):
    """Creates a new customer record."""
    url = f"{BASE_URL}/customers"
    customer_data = {
        "name": name, "email": email, "company": company, "phone": phone,
        "address": address, "status": status, "lead_score": lead_score, "notes": notes
    }
    payload = {k: v for k, v in customer_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Customer '{name}' created."
    except requests.exceptions.RequestException as e:
        return f"Error creating customer: {e}"

def update_customer(
    customer_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    company: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    status: Optional[Literal["Active", "Lead", "Inactive"]] = None,
    lead_score: Optional[int] = None,
    notes: Optional[str] = None
):
    """Updates an existing customer's details using their ID."""
    url = f"{BASE_URL}/customers/{customer_id}"
    update_data = {
        "name": name, "email": email, "company": company, "phone": phone,
        "address": address, "status": status, "lead_score": lead_score, "notes": notes
    }
    payload = {k: v for k, v in update_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Customer ID '{customer_id}' updated."
    except requests.exceptions.RequestException as e:
        return f"Error updating customer: {e}"

def delete_customer(customer_id: str):
    """Deletes a customer using their ID."""
    url = f"{BASE_URL}/customers/{customer_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return f"Success: Customer ID '{customer_id}' has been deleted."
    except requests.exceptions.RequestException as e:
        return f"Error deleting customer: {e}"

# --- Product Tools (Inventory) ---

def create_product(
    name: str,
    sku: str,
    price: float,
    stock_quantity: int,
    category: Optional[str] = None,
    cost: Optional[float] = None,
    reorder_level: Optional[int] = None,
    description: Optional[str] = None
):
    """Creates a new product in the inventory."""
    url = f"{BASE_URL}/products"
    product_data = {
        "name": name, "sku": sku, "price": price, "stock_quantity": stock_quantity,
        "category": category, "cost": cost, "reorder_level": reorder_level, "description": description
    }
    payload = {k: v for k, v in product_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Product '{name}' created."
    except requests.exceptions.RequestException as e:
        return f"Error creating product: {e}"

def update_product(
    product_id: str,
    name: Optional[str] = None,
    sku: Optional[str] = None,
    price: Optional[float] = None,
    stock_quantity: Optional[int] = None,
    category: Optional[str] = None,
    cost: Optional[float] = None,
    reorder_level: Optional[int] = None,
    description: Optional[str] = None
):
    """Updates an existing product's details using its ID."""
    url = f"{BASE_URL}/products/{product_id}"
    update_data = {
        "name": name, "sku": sku, "price": price, "stock_quantity": stock_quantity,
        "category": category, "cost": cost, "reorder_level": reorder_level, "description": description
    }
    payload = {k: v for k, v in update_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Product ID '{product_id}' updated."
    except requests.exceptions.RequestException as e:
        return f"Error updating product: {e}"

def delete_product(product_id: str):
    """Deletes a product from inventory using its ID."""
    url = f"{BASE_URL}/products/{product_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return f"Success: Product ID '{product_id}' has been deleted."
    except requests.exceptions.RequestException as e:
        return f"Error deleting product: {e}"

# --- Employee Tools (HR) ---

def create_employee(
    employee_id: str, # This is the user-facing ID like "E001"
    first_name: str,
    last_name: str,
    email: str,
    position: str,
    department: Optional[str] = None,
    phone: Optional[str] = None,
    hire_date: Optional[str] = None,
    salary: Optional[float] = None,
    status: Literal["Active", "On Leave"] = "Active"
):
    """Creates a new employee record."""
    url = f"{BASE_URL}/employees"
    employee_data = {
        "employee_id": employee_id, "first_name": first_name, "last_name": last_name, "email": email,
        "position": position, "department": department, "phone": phone, "hire_date": hire_date,
        "salary": salary, "status": status
    }
    payload = {k: v for k, v in employee_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Employee '{first_name} {last_name}' created."
    except requests.exceptions.RequestException as e:
        return f"Error creating employee: {e}"

def update_employee(
    employee_id_custom: str, # This is the user-facing ID like "E001"
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    position: Optional[str] = None,
    department: Optional[str] = None,
    phone: Optional[str] = None,
    hire_date: Optional[str] = None,
    salary: Optional[float] = None,
    status: Optional[Literal["Active", "On Leave"]] = None
):
    """Updates an existing employee's details using their custom employee ID."""
    url = f"{BASE_URL}/employees/{employee_id_custom}"
    update_data = {
        "first_name": first_name, "last_name": last_name, "email": email, "position": position,
        "department": department, "phone": phone, "hire_date": hire_date, "salary": salary, "status": status
    }
    payload = {k: v for k, v in update_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Employee ID '{employee_id_custom}' updated."
    except requests.exceptions.RequestException as e:
        return f"Error updating employee: {e}"

def delete_employee(employee_id_custom: str):
    """Deletes an employee using their custom employee ID (e.g., 'E001')."""
    url = f"{BASE_URL}/employees/{employee_id_custom}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return f"Success: Employee ID '{employee_id_custom}' has been deleted."
    except requests.exceptions.RequestException as e:
        return f"Error deleting employee: {e}"

# --- Order Tools ---

def create_order(
    customer_id: str,
    order_date: str,
    total_amount: float,
    status: Literal["Pending", "Processing", "Shipped", "Delivered"] = "Pending",
    shipping_address: Optional[str] = None,
    notes: Optional[str] = None
):
    """Creates a new customer order."""
    url = f"{BASE_URL}/orders"
    order_data = {
        "customer_id": customer_id, "order_date": order_date, "total_amount": total_amount,
        "status": status, "shipping_address": shipping_address, "notes": notes
    }
    payload = {k: v for k, v in order_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Order created for customer '{customer_id}'."
    except requests.exceptions.RequestException as e:
        return f"Error creating order: {e}"

def update_order(
    order_id: str,
    customer_id: Optional[str] = None,
    order_date: Optional[str] = None,
    total_amount: Optional[float] = None,
    status: Optional[Literal["Pending", "Processing", "Shipped", "Delivered"]] = None,
    shipping_address: Optional[str] = None,
    notes: Optional[str] = None
):
    """Updates an existing order using its ID."""
    url = f"{BASE_URL}/orders/{order_id}"
    update_data = {
        "customer_id": customer_id, "order_date": order_date, "total_amount": total_amount,
        "status": status, "shipping_address": shipping_address, "notes": notes
    }
    payload = {k: v for k, v in update_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Order ID '{order_id}' updated."
    except requests.exceptions.RequestException as e:
        return f"Error updating order: {e}"

def delete_order(order_id: str):
    """Deletes an order using its ID."""
    url = f"{BASE_URL}/orders/{order_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return f"Success: Order ID '{order_id}' has been deleted."
    except requests.exceptions.RequestException as e:
        return f"Error deleting order: {e}"

# --- Invoice Tools (Finance) ---

def create_invoice(
    customer_id: str,
    issue_date: str,
    due_date: str,
    total_amount: float,
    order_id: Optional[str] = None,
    paid_amount: float = 0.0,
    status: Literal["Pending", "Paid", "Overdue", "Cancelled"] = "Pending"
):
    """Creates a new invoice."""
    url = f"{BASE_URL}/invoices"
    invoice_data = {
        "customer_id": customer_id, "issue_date": issue_date, "due_date": due_date,
        "total_amount": total_amount, "order_id": order_id, "paid_amount": paid_amount, "status": status
    }
    payload = {k: v for k, v in invoice_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        # The response from a POST might contain the new invoice number
        new_invoice = response.json()
        inv_num = new_invoice.get('invoice_number', '')
        return f"Success: Invoice {inv_num} created for customer '{customer_id}'."
    except requests.exceptions.RequestException as e:
        return f"Error creating invoice: {e}"

def update_invoice(
    invoice_id: str,
    customer_id: Optional[str] = None,
    issue_date: Optional[str] = None,
    due_date: Optional[str] = None,
    total_amount: Optional[float] = None,
    order_id: Optional[str] = None,
    paid_amount: Optional[float] = None,
    status: Optional[Literal["Pending", "Paid", "Overdue", "Cancelled"]] = None
):
    """Updates an existing invoice using its ID."""
    url = f"{BASE_URL}/invoices/{invoice_id}"
    update_data = {
        "customer_id": customer_id, "issue_date": issue_date, "due_date": due_date,
        "total_amount": total_amount, "order_id": order_id, "paid_amount": paid_amount, "status": status
    }
    payload = {k: v for k, v in update_data.items() if v is not None}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload)
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        return f"Success: Invoice ID '{invoice_id}' updated."
    except requests.exceptions.RequestException as e:
        return f"Error updating invoice: {e}"

def delete_invoice(invoice_id: str):
    """Deletes an invoice using its ID."""
    url = f"{BASE_URL}/invoices/{invoice_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return f"Success: Invoice ID '{invoice_id}' has been deleted."
    except requests.exceptions.RequestException as e:
        return f"Error deleting invoice: {e}"
    
# ==============================================================================
# AGENT "SEARCH" TOOL DEFINITIONS
#
# Add these functions to agent_setup.py and update the 'tools' list.
# ==============================================================================

def search_customers(query: str):
    """
    Searches for existing customers by name, email, or company.
    Returns a list of matching customers or a not found message.
    """
    url = f"{BASE_URL}/customers"
    logger.info(f"🔎 Searching for customer matching '{query}'...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_customers = response.json()
        query_lower = query.lower()
        
        matches = [
            c for c in all_customers if
            query_lower in c.get('name', '').lower() or
            query_lower in c.get('email', '').lower() or
            query_lower in c.get('company', '').lower()
        ]
        
        if not matches:
            return "No customer found matching that query."
        return json.dumps(matches)
    except requests.exceptions.RequestException as e:
        return f"Error searching customers: {e}"

def search_products(query: str):
    """
    Searches for existing products by name or SKU.
    Returns a list of matching products or a not found message.
    """
    url = f"{BASE_URL}/products"
    logger.info(f"🔎 Searching for product matching '{query}'...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_products = response.json()
        query_lower = query.lower()

        matches = [
            p for p in all_products if
            query_lower in p.get('name', '').lower() or
            query_lower in p.get('sku', '').lower()
        ]

        if not matches:
            return "No product found matching that query."
        return json.dumps(matches)
    except requests.exceptions.RequestException as e:
        return f"Error searching products: {e}"

def search_employees(query: str):
    """
    Searches for existing employees by first name, last name, or email.
    Returns a list of matching employees or a not found message.
    """
    url = f"{BASE_URL}/employees"
    logger.info(f"🔎 Searching for employee matching '{query}'...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_employees = response.json()
        query_lower = query.lower()

        matches = [
            e for e in all_employees if
            query_lower in e.get('first_name', '').lower() or
            query_lower in e.get('last_name', '').lower() or
            query_lower in e.get('email', '').lower()
        ]

        if not matches:
            return "No employee found matching that query."
        return json.dumps(matches)
    except requests.exceptions.RequestException as e:
        return f"Error searching employees: {e}"
    
def search_invoices(query: str):
    """
    Searches for existing invoices by invoice number or customer ID.
    Returns a list of matching invoices or a not found message.
    """
    url = f"{BASE_URL}/invoices"
    logger.info(f"🔎 Searching for invoice matching '{query}'...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_invoices = response.json()
        query_lower = query.lower()

        matches = [
            i for i in all_invoices if
            query_lower in i.get('invoice_number', '').lower() or
            query_lower in i.get('customer_id', '').lower()
        ]

        if not matches:
            return "No invoice found matching that query."
        return json.dumps(matches)
    except requests.exceptions.RequestException as e:
        return f"Error searching invoices: {e}"
    
def search_orders(query: str):
    """
    Searches for existing orders by customer ID or status.
    Returns a list of matching orders or a not found message.
    """
    url = f"{BASE_URL}/orders"
    logger.info(f"🔎 Searching for order matching '{query}'...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_orders = response.json()
        query_lower = query.lower()

        matches = [
            o for o in all_orders if
            query_lower in o.get('customer_id', '').lower() or
            query_lower in o.get('status', '').lower()
        ]

        if not matches:
            return "No order found matching that query."
        return json.dumps(matches)
    except requests.exceptions.RequestException as e:
        return f"Error searching orders: {e}"

# Note: Search for Orders and Invoices can be added here if needed,
# though they are less commonly searched by simple text queries.

# --- Tool & System Prompt Definition ---

tools = [navigate_to_page, fill_form_field, 
         create_customer, update_customer, delete_customer, search_customers,
         create_employee, update_employee, delete_employee, search_employees,
         create_order, update_order, delete_order,search_orders,
         create_product, update_product, delete_product, search_products,
         create_invoice, update_invoice, delete_invoice,search_invoices]

# In agent_setup.py, replace the entire system_prompt string with this:

system_prompt_1 = """You are an expert ERP Co-Pilot, a voice assistant designed to help users interact with a complex business management system.

Your primary goal is to make the user's workflow seamless and intuitive. You will achieve this by translating their voice commands into API calls.

**Core Principles:**

1.  **Wait for Explicit Commands:** Do NOT take any action, especially navigation, unless the user explicitly asks you to. If the user says something conversational like "hello" or "can you hear me?", simply respond something like "How can I help you". Do not assume they want to start a task.

2.  **UI First:** Once the user gives an explicit command (e.g., "add a new product" or "I want to create an invoice"), your FIRST action should be to use the `Maps_to_page` tool.

3.  **Conversational Data Collection:** After navigating, guide the user through creating new records. If you know required fields (like a customer's name and email), ask for them conversationally. Use the `fill_form_field` tool for each piece of information as it's provided.

4.  **Finalize with Confirmation:** After you have collected all necessary information and the user has confirmed they want to save, use the appropriate creation tool (e.g., `create_new_customer`).

5.  **Handle Ambiguity:** Your transcription service may sometimes provide weird or non-English input. If you receive a confusing message, do not act on it. Instead, state that you are an English-speaking assistant and ask the user to repeat themselves.

6.  **Clarity and Brevity:** Keep your responses friendly, to the point and most importantly talk as less as possible. You talk only the necessary things or ask specific question. Remember, your voice will be synthesized, so avoid complex symbols or formatting.

7. There are tools available for every CRUD operation, so there are create_, update_ and delete_ functions for customers, employee, orders, products and invoice. Upon user's requests and intent, use them accordingly.

8. Before any DELETE operation (delete_), you must ask for confirmation, you might say something like "Are you sure you want delete this or that..."

**Workflow for Updating or Deleting:**

When the user asks to update or delete a record (e.g., "delete customer Global Tech" or "update product X-01's price"), always remember the UI-first approach, for any operation, always go to the relevant pages, for customer, go to crm, for invoice, go to hr, etc.
Then you MUST follow this two-step process:

1.  **Search First:** The user will provide a name or other detail, not an ID. Your first action MUST be to use the appropriate search tool (`search_customers`, `search_products`, etc.) to find the record.
2.  **Act Second:**
    * If the search tool returns one result, state what you found and ask the user for confirmation before you use the corresponding `update_` or `delete_` tool with the ID from the search result.
    * If the search tool returns multiple results, present the options to the user so they can clarify which one they mean.
    * If the search tool returns no results, inform the user that you could not find the record.
"""

system_prompt_2 = """You are an ERP Voice Assistant that helps users perform business operations through voice commands.

**CRITICAL RULES - ALWAYS FOLLOW:**

1. **You are a Voice Assistant, NOT a Code Generator**
   - Never write, display, or execute code
   - When user asks you to "generate" an ID, create a simple alphanumeric ID yourself
   - Respond in natural language only

2. **Only Act on Explicit Commands**
   - Wait for clear action requests like "create customer" or "delete invoice"
   - For greetings/casual talk, just respond "How can I help you?"
   - Never assume what the user wants

2. **Always Navigate First**
   - Before ANY operation, use `navigate_to_page` to go to the relevant section
   - Customers → CRM, Employees → HR, Products/Orders/Invoices → respective pages

3. **Search Before Update/Delete**
   - User gives names, you need IDs
   - ALWAYS use search tools first (search_customers, search_products, etc.)
   - If no exact matches found, try variations for common STT errors:
     * Similar sounding words (wick→wig, john→joan, smith→smyth)
     * Missing letters (john→jon, mike→mic)
     * Extra letters (sara→sarah, tom→tommy)
   - Present all possible matches and ask user to confirm which record

4. **Mandatory Confirmations**
   - CREATE operations: After collecting required fields, ask "Would you like to fill any optional fields before saving?" List available optional fields, then ask "Should I create this [customer/product/etc.] now?"
   - DELETE operations: ALWAYS ask "Are you sure you want to delete [specific item]?"
   - UPDATE operations: ALWAYS ask "Should I update [specific item] with these changes?"
   - Wait for explicit "yes" before proceeding

5. **Data Collection Process**
   - Ask for required fields one at a time
   - Use `fill_form_field` for each piece of data
   - For ID fields: If user says "generate random" or "you create it", generate a simple random ID (e.g., "EMP001", "CUST123", "PROD456")
   - After required fields: Ask about optional fields before saving
   - Only use create/update tools after collecting data AND getting final confirmation

**Response Style:**
- Keep responses short and clear
- Ask specific questions only
- Avoid complex formatting (voice synthesis friendly)
- If input is unclear/non-English, ask user to repeat
- When no search results found, ask user to spell out the name or provide more details
- NEVER generate or display code - you are a voice assistant, not a code generator

**Operation Flow:**
1. Navigate to appropriate page
2. For Create: Ask for required fields one at a time → Fill each field → Ask about optional fields → Fill optional fields if requested → Confirm creation → Create
3. For Update/Delete: Search → If no results, try STT variations → Present options → Confirm selection → Confirm action → Execute

Remember: Every operation requires explicit user confirmation before execution."""

agent = create_react_agent(
    model=model,
    tools=tools,
    prompt=system_prompt_2, # Use messages_modifier for newer LangGraph versions
    checkpointer=memory,
)

agent_config = {"configurable": {"thread_id": "default_user"}}