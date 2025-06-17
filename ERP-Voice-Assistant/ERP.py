# main_erp_vue_final.py

from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO
import pandas as pd
import json
from datetime import datetime, date, timedelta
import uuid
from typing import Dict, List, Any, Optional
import os

# ==================== DATA MODELS ====================
# In main_erp_vue_final.py, replace the whole DataManager class

# In main_erp_vue_final.py, replace the ENTIRE DataManager class

class DataManager:
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        # Customers
        customer_data = [
            {'id': 'cust001', 'name': 'Acme Corporation', 'email': 'contact@acme.com', 'phone': '+1-555-0123', 'company': 'Acme Corp', 'address': '123 Business Ave, NYC', 'status': 'Active', 'lead_score': 85, 'created_date': '2024-01-15', 'last_contact': '2024-05-20', 'notes': 'Premium customer'},
            {'id': 'cust002', 'name': 'TechStart LLC', 'email': 'hello@techstart.com', 'phone': '+1-555-0456', 'company': 'TechStart LLC', 'address': '456 Innovation Blvd, SF', 'status': 'Active', 'lead_score': 72, 'created_date': '2024-02-10', 'last_contact': '2024-05-28', 'notes': 'Startup client'}
        ]
        self.customers = pd.DataFrame(customer_data)
        
        # ... (rest of your sample data initializations) ...
        product_data = [
            {'id': 'prod001', 'name': 'Wireless Headphones Pro', 'sku': 'WH-PRO-001', 'category': 'Electronics', 'price': 299.99, 'cost': 150.00, 'stock_quantity': 150, 'reorder_level': 25, 'supplier_id': 'supp001', 'warehouse_location': 'A-1-15', 'created_date': '2024-01-01', 'description': 'High-fidelity wireless headphones with noise cancellation.'},
            {'id': 'prod002', 'name': 'Ergonomic Office Chair', 'sku': 'CHAIR-ERG-001', 'category': 'Furniture', 'price': 449.99, 'cost': 200.00, 'stock_quantity': 45, 'reorder_level': 10, 'supplier_id': 'supp002', 'warehouse_location': 'B-2-08', 'created_date': '2024-01-05', 'description': 'Comfortable ergonomic chair for long working hours.'},
            {'id': 'prod003', 'name': 'Smart Water Bottle', 'sku': 'BOTTLE-SMRT-01', 'category': 'Gadgets', 'price': 79.99, 'cost': 30.00, 'stock_quantity': 8, 'reorder_level': 15, 'supplier_id': 'supp001', 'warehouse_location': 'C-1-02', 'created_date': '2024-02-10', 'description': 'Tracks water intake and glows to remind you to drink.'}
        ]
        self.products = pd.DataFrame(product_data)

        employee_data = [
            {'id': 'emp001', 'employee_id': 'E001', 'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@company.com', 'phone': '+1-555-4001', 'department': 'Sales', 'position': 'Sales Manager', 'hire_date': '2023-03-15', 'salary': 75000, 'status': 'Active', 'manager_id': ''},
            {'id': 'emp002', 'employee_id': 'E002', 'first_name': 'Emily', 'last_name': 'Davis', 'email': 'emily.davis@company.com', 'phone': '+1-555-4002', 'department': 'Marketing', 'position': 'Marketing Specialist', 'hire_date': '2023-06-01', 'salary': 65000, 'status': 'Active', 'manager_id': 'emp001'}
        ]
        self.employees = pd.DataFrame(employee_data)

        order_data = [
            {'id': 'ord001', 'customer_id': 'cust001', 'order_date': '2024-05-25', 'status': 'Processing', 'total_amount': 1499.95, 'shipping_address': '123 Business Ave, NYC', 'notes': 'Bulk order'},
            {'id': 'ord002', 'customer_id': 'cust002', 'order_date': '2024-05-28', 'status': 'Pending', 'total_amount': 899.97, 'shipping_address': '456 Innovation Blvd, SF', 'notes': 'Standard delivery'}
        ]
        self.sales_orders = pd.DataFrame(order_data)

        invoice_data = [
            {'id': 'inv001', 'invoice_number': 'INV001', 'order_id': 'ord001', 'customer_id': 'cust001', 'issue_date': '2024-05-25', 'due_date': '2024-06-24', 'total_amount': 1499.95, 'status': 'Paid', 'paid_amount': 1499.95},
            {'id': 'inv002', 'invoice_number': 'INV002', 'order_id': 'ord002', 'customer_id': 'cust002', 'issue_date': '2024-05-28', 'due_date': '2024-06-27', 'total_amount': 899.97, 'status': 'Pending', 'paid_amount': 0.00}
        ]
        self.invoices = pd.DataFrame(invoice_data)
        
        self.suppliers = pd.DataFrame(columns=['id', 'name', 'contact_person', 'email', 'phone'])
        self.contracts = pd.DataFrame(columns=['id', 'contract_number', 'type', 'title', 'start_date', 'end_date', 'value'])

    def generate_id(self, prefix=''):
        return prefix + str(uuid.uuid4())[:8]

    def _broadcast_update(self, event_type: str, data: Dict):
        # Ensure data is clean before broadcasting
        cleaned_data = {k: (v if pd.notna(v) else None) for k, v in data.items()}
        try:
            self.socketio.emit('data_update', {'type': event_type, 'data': cleaned_data, 'timestamp': datetime.now().isoformat()}, namespace='/')
            print(f"Broadcasted data_update: {event_type}")
        except Exception as e:
            print(f"Broadcast data_update error: {e}")

    def broadcast_ui_instruction(self, instruction: Dict):
        try:
            self.socketio.emit('ui_instruction', instruction, namespace='/')
            print(f"Broadcasted ui_instruction: {instruction.get('action')}")
        except Exception as e:
            print(f"Broadcast ui_instruction error: {e}")

    def _add_item(self, df_name: str, data: Dict, prefix: str, required_fields: List[str] = None) -> Optional[Dict]:
        if required_fields and any(not data.get(f) for f in required_fields):
            return None
        
        df = getattr(self, df_name)
        new_id = self.generate_id(prefix)
        
        # Create a full record with all possible columns, setting defaults for missing values
        full_record = {}
        for col in df.columns:
            if col == 'id':
                full_record[col] = new_id
            elif col in data and data[col] is not None and data[col] != '':
                full_record[col] = data[col]
            else:
                # Set intelligent defaults to prevent NaN
                if df[col].dtype in ['int64', 'float64']:
                    full_record[col] = 0
                else:
                    full_record[col] = None # Use None for missing object/string types
        
        if 'created_date' not in data and 'created_date' in df.columns:
            full_record['created_date'] = datetime.now().strftime('%Y-%m-%d')
        
        new_row = pd.DataFrame([full_record])
        setattr(self, df_name, pd.concat([df, new_row], ignore_index=True))
        
        self._broadcast_update(f'{prefix}_added', full_record)
        return full_record

    def _update_item(self, df_name: str, item_id: str, data: Dict, prefix: str, lookup_col: str = 'id') -> Optional[Dict]:
        df = getattr(self, df_name)
        idx = df[df[lookup_col] == item_id].index
        if not idx.empty:
            cleaned_data = {k: (v if pd.notna(v) and v != '' else None) for k, v in data.items()}
            for key, value in cleaned_data.items():
                if key in df.columns and key != 'id':
                    df.loc[idx[0], key] = value
            updated_data = df.loc[idx[0]].to_dict()
            self._broadcast_update(f'{prefix}_updated', updated_data)
            return updated_data
        return None
    
    def _delete_item(self, df_name: str, item_id: str, prefix: str, lookup_col: str = 'id') -> Optional[Dict]:
        df = getattr(self, df_name)
        idx = df[df[lookup_col] == item_id].index
        if not idx.empty:
            deleted_item_data = df.loc[idx[0]].to_dict()
            setattr(self, df_name, df.drop(idx).reset_index(drop=True))
            self._broadcast_update(f'{prefix}_deleted', deleted_item_data)
            return deleted_item_data
        return None

    # ... (the rest of the specific add/update/delete methods like add_customer, update_product, etc. are the same) ...
    def add_customer(self, data: Dict) -> Optional[Dict]: return self._add_item('customers', data, 'customer', ['name', 'email'])
    def update_customer(self, id: str, data: Dict) -> Optional[Dict]: return self._update_item('customers', id, data, 'customer')
    def delete_customer(self, id: str) -> Optional[Dict]: return self._delete_item('customers', id, 'customer')
    def add_product(self, data: Dict) -> Optional[Dict]: return self._add_item('products', data, 'product', ['name', 'sku', 'price'])
    def update_product(self, id: str, data: Dict) -> Optional[Dict]: return self._update_item('products', id, data, 'product')
    def delete_product(self, id: str) -> Optional[Dict]: return self._delete_item('products', id, 'product')
    def add_employee(self, data: Dict) -> Optional[Dict]: return self._add_item('employees', data, 'employee', ['first_name', 'email'])
    def update_employee(self, id: str, data: Dict) -> Optional[Dict]: return self._update_item('employees', id, data, 'employee', 'employee_id')
    def delete_employee(self, id: str) -> Optional[Dict]: return self._delete_item('employees', id, 'employee', 'employee_id')
    def add_order(self, data: Dict) -> Optional[Dict]: return self._add_item('sales_orders', data, 'order', ['customer_id', 'total_amount'])
    def update_order(self, id: str, data: Dict) -> Optional[Dict]: return self._update_item('sales_orders', id, data, 'order')
    def delete_order(self, id: str) -> Optional[Dict]: return self._delete_item('sales_orders', id, 'order')
    def add_invoice(self, data: Dict) -> Optional[Dict]: return self._add_item('invoices', data, 'invoice', ['customer_id', 'total_amount'])
    def update_invoice(self, id: str, data: Dict) -> Optional[Dict]: return self._update_item('invoices', id, data, 'invoice')
    def delete_invoice(self, id: str) -> Optional[Dict]: return self._delete_item('invoices', id, 'invoice')
    
    def get_dashboard_metrics(self) -> Dict:
        return {
            'total_customers': len(self.customers) if not self.customers.empty else 0,
            'total_products': len(self.products) if not self.products.empty else 0,
            'total_orders': len(self.sales_orders) if not self.sales_orders.empty else 0,
            'total_employees': len(self.employees) if not self.employees.empty else 0,
            'total_invoices': len(self.invoices) if not self.invoices.empty else 0,
        }
    

app = Flask(__name__)
app.secret_key = 'your-very-secret-key-for-vue-erp-final'
socketio = SocketIO(app, cors_allowed_origins="*")
data_manager = DataManager(socketio)

# ==================== BASE HTML PAGE TEMPLATE (Refined) ====================
def create_base_html_page(vue_app_script="", page_specific_content="", current_page_path="", voice_backend_url="ws://127.0.0.1:7861/"):
    global_socket_script = """
    <script>
        const globalSocket = io();
        globalSocket.on('connect', () => {
            console.log('Global Socket: Connected! Firing ready event.');
            // Dispatch a custom event on the document to signal that the socket is ready
            document.dispatchEvent(new CustomEvent('globalSocketReady', { detail: globalSocket }));
        });
        // The rest of the global listeners remain the same...
        
        // Initialize pending navigation storage
        window.pendingNavigation = null;
        globalSocket.on('data_update', (msg) => {
            console.log('Global Socket: data_update:', msg);
            const notifications = document.getElementById('notifications');
            if (!notifications) return;
            const item = document.createElement('div');
            item.className = 'notification-item';
            let itemName = msg.data ? (msg.data.name || msg.data.first_name || msg.data.invoice_number || msg.data.id || '') : '';
            item.textContent = `Update: ${(msg.type || 'Unknown').replace(/_/g, ' ')} (${itemName}) at ${new Date(msg.timestamp || Date.now()).toLocaleTimeString()}`;
            notifications.prepend(item);
            setTimeout(() => item.remove(), 7000);
        });
        globalSocket.on('ui_instruction', (instruction) => {
            console.log('Global Socket: ui_instruction:', instruction);
            if (instruction.action === 'navigate' && instruction.url) {
                if (window.location.pathname !== instruction.url.split('?')[0]) {
                    console.log(`⏳ Queueing navigation to ${instruction.url} until TTS completes`);
                    window.pendingNavigation = instruction;
                } else if (window.vueApp && typeof window.vueApp.handleGlobalInstruction === 'function') {
                    window.vueApp.handleGlobalInstruction(instruction);
                }
            } else if (window.vueApp && typeof window.vueApp.handleGlobalInstruction === 'function') {
                window.vueApp.handleGlobalInstruction(instruction);
            }
        });

        // Voice assistant functionality with WebSocket reconnection
        const voiceBtn = document.getElementById('voice-btn');
        let mediaRecorder;
        let audioChunks = [];
        let voiceSocket;

        // Function to create/recreate WebSocket connection
        function createVoiceSocket() {
            if (voiceSocket && voiceSocket.readyState !== WebSocket.CLOSED) {
                voiceSocket.close();
            }
            
            // voiceSocket = new WebSocket('ws://127.0.0.1:7861/');
            voiceSocket = new WebSocket('{voice_backend_url}');

            voiceSocket.onopen = () => {
                console.log('🔌 Voice WebSocket CONNECTED');
            };
            
            voiceSocket.onclose = (event) => {
                console.log(`🔌 Voice WebSocket CLOSED: ${event.code} - ${event.reason}`);
                
                // Only attempt to reconnect for non-normal closures
                if (event.code !== 1000) {
                    setTimeout(() => {
                        console.log('🔄 Attempting to reconnect voice WebSocket...');
                        createVoiceSocket();
                    }, 1000);
                }
            };
            
            voiceSocket.onerror = (error) => {
                console.error('❌ Voice WebSocket ERROR:', error);
            };
            
            // Handle backend responses - both audio and navigation commands
            voiceSocket.onmessage = event => {
                // Handle navigation commands
                if (typeof event.data === 'string') {
                    console.log('💬 Received text message:', event.data);
                    if (event.data === 'NAVIGATE_NOW' && window.pendingNavigation) {
                        const instruction = window.pendingNavigation;
                        window.pendingNavigation = null;
                        
                        let targetUrl = instruction.url;
                        if (instruction.params) {
                            targetUrl += `?${new URLSearchParams(instruction.params).toString()}`;
                        }
                        console.log('🚀 Executing navigation to', targetUrl);
                        window.location.href = targetUrl;
                    }
                    return;
                }
                
                // Handle audio data
                console.log('🎵 RECEIVED audio response from server:', event.data.size, 'bytes');
                const audioBlob = new Blob([event.data], { type: 'audio/mp3' });
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                
                console.log('🔊 Attempting to play audio...');
                audio.play().then(() => {
                    console.log('✅ Audio played successfully');
                    
                    // Execute navigation after audio completes
                    audio.onended = () => {
                        console.log('✅ Finished playing audio');
                        URL.revokeObjectURL(audioUrl);
                        console.log('🗑️ Audio URL cleaned up');
                        
                        // Check if we have a pending navigation
                        if (window.pendingNavigation) {
                            const instruction = window.pendingNavigation;
                            window.pendingNavigation = null;
                            
                            console.log('🚀 Executing queued navigation');
                            let targetUrl = instruction.url;
                            if (instruction.params) {
                                targetUrl += `?${new URLSearchParams(instruction.params).toString()}`;
                            }
                            window.location.href = targetUrl;
                        }
                    };
                }).catch(error => {
                    console.error('❌ Error playing audio:', error);
                });
            };
            
        }

        // Initialize WebSocket connection
        createVoiceSocket();

        voiceBtn.addEventListener('click', async () => {
            if (!mediaRecorder) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        
                        console.log('🎤 Audio recorded, checking WebSocket state:', voiceSocket.readyState);
                        
                        // Only send audio if WebSocket is open
                        if (voiceSocket.readyState === WebSocket.OPEN) {
                            console.log('📤 Sending audio to server');
                            voiceSocket.send(audioBlob);
                        } else {
                            console.log('ℹ️ WebSocket closed during recording, discarding audio');
                        }
                        
                        audioChunks = [];
                    };
                    
                    mediaRecorder.start();
                    voiceBtn.textContent = '🛑 Stop';
                } catch (error) {
                    console.error('Error accessing microphone:', error);
                }
            } else {
                mediaRecorder.stop();
                mediaRecorder = null;
                voiceBtn.textContent = '🎤 Voice Assistant';
            }
        });

        // Test log to confirm the script is loaded
        console.log("🧪 WebSocket code loaded!");
        
    </script>
    """
    nav_items = [
        {"path": "/", "name": "Dashboard"}, {"path": "/crm_vue", "name": "CRM"},
        {"path": "/inventory_vue", "name": "Inventory"}, {"path": "/orders_vue", "name": "Orders"},
        {"path": "/hr_vue", "name": "HR"}, {"path": "/finance_vue", "name": "Finance"},
    ]
    nav_html = "".join([f'<a href="{item["path"]}" class="{ "active" if item["path"] == current_page_path else ""}">{item["name"]}</a>' for item in nav_items])

    return f"""
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERP Vue System</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background-color: #f0f2f5; color: #1f2937; line-height: 1.6; }}
        .header {{ background: #ffffff; padding: 0.8rem 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-bottom: 1px solid #e5e7eb; }}
        .header h1 {{ margin: 0; color: #111827; font-size: 1.75rem; }}
        .nav-container {{ padding: 0.5rem 0; display: flex; gap: 0.5rem; flex-wrap: wrap; }}
        .nav-container a {{ text-decoration: none; color: #374151; font-weight: 500; padding: 0.5rem 1rem; border-radius: 6px; transition: background-color 0.2s ease, color 0.2s ease; }}
        .nav-container a:hover {{ background-color: #eef2ff; color: #4f46e5; }}
        .nav-container a.active {{ background-color: #4f46e5; color: white; }}
        .content {{ padding: 1.5rem 2rem; }}
        .module-container {{ }} /* Container for each Vue app's content */
        .form-section, .table-section {{ background: #ffffff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06); margin-bottom: 2rem; }}
        h2 {{ font-size: 1.5rem; color: #111827; margin-top:0; margin-bottom:1rem; }}
        h3 {{ font-size: 1.25rem; color: #1f2937; margin-top:0; margin-bottom:1rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.5rem; }}
        .form-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.25rem; }}
        .form-group {{ margin-bottom: 1rem; }}
        .form-group label {{ display: block; margin-bottom: 0.4rem; font-weight: 500; color: #374151; font-size: 0.875rem; }}
        .form-group input, .form-group select, .form-group textarea {{ width: 100%; padding: 0.6rem 0.75rem; border: 1px solid #d1d5db; border-radius: 6px; box-sizing: border-box; font-size: 0.875rem; transition: border-color 0.2s ease, box-shadow 0.2s ease; }}
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {{ border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2); outline: none;}}
        textarea {{ min-height: 80px; resize: vertical; }}
        button, .btn {{ padding: 0.6rem 1.25rem; background-color: #4f46e5; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 500; transition: background-color 0.2s ease; display: inline-flex; align-items: center; justify-content: center; }}
        button:hover, .btn:hover {{ background-color: #4338ca; }}
        .btn-secondary {{ background-color: #6b7280; }} .btn-secondary:hover {{ background-color: #4b5563; }}
        .btn-warning {{ background-color: #f59e0b; color: #1f2937; }} .btn-warning:hover {{ background-color: #d97706; }}
        .table-container {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 1rem; font-size: 0.875rem; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }} /* nowrap with overflow-x on container */
        td {{ white-space: normal; word-wrap: break-word; overflow-wrap: break-word; }} /* Allow content in td to wrap */
        th {{ background-color: #f9fafb; font-weight: 600; color: #374151; white-space: nowrap; }}
        tr:hover > td {{ background-color: #f3f4f6; }}
        .status-badge {{ padding: 0.25em 0.6em; border-radius: 100px; font-size: 0.75rem; font-weight: 500; color: white; display: inline-block; }}
        .status-active {{ background-color: #10b981; }} .status-lead {{ background-color: #f59e0b; color: #1f2937;}} .status-inactive {{ background-color: #6b7280; }}
        .status-pending {{ background-color: #3b82f6; }} .status-processing {{ background-color: #8b5cf6; }} .status-paid {{ background-color: #10b981; }} .status-shipped {{ background-color: #ef4444; }} .status-delivered {{ background-color: #10b981; }}
        #notifications {{ position: fixed; top: 20px; right: 20px; width: 320px; z-index: 10000; }}
        .notification-item {{ background-color: #1f2937; color: #f3f4f6; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-size: 0.875rem; }}
        [v-cloak] > * {{ display:none !important; }}
        [v-cloak]::before {{ content: "Loading application component..."; display: block; padding: 1rem; text-align: center; font-style: italic; color: #6b7280; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; }}
        .metric-card {{ background: #fff; padding: 1.25rem; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .metric-card h4 {{ margin-top:0; margin-bottom:0.5rem; color: #6b7280; font-size: 0.9rem; text-transform: capitalize; }}
        .metric-card p {{ font-size: 2.25em; color: #4f46e5; font-weight: 600; margin:0; }}
    </style>
</head>
<body>
    <div class="header"><h1>ERP Management System</h1><nav class="nav-container">{nav_html}</nav></div>
    <button id="voice-btn" class="btn" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">🎤 Voice Assistant</button>
    <div class="content"><div class="module-container">{page_specific_content}</div></div>
    <div id="notifications"></div>
    {global_socket_script}
    {vue_app_script}
</body></html>
"""

# ==================== VUE APP TEMPLATES AND SCRIPTS (Strings) ====================

# --- Dashboard (Fixed) ---
# In main_erp_vue_final.py

# --- Dashboard Vue App ---
DASHBOARD_APP_HTML = """
<div id="dashboard-app" v-cloak>
    <h2>{{ title }}</h2>
    <div class="metrics-grid">
        <div class="metric-card" v-for="(value, key) in metrics" :key="key">
            <template v-if="displayMetricKeys.includes(key)">
                 <h4>{{ formatMetricKey(key) }}</h4>
                 <p>{{ value !== undefined ? value : 'N/A' }}</p>
            </template>
        </div>
    </div>
    <p style="margin-top: 2rem; font-size: 0.9rem; color: #4b5563;"><em>This dashboard provides a quick overview.</em></p>
</div>
"""

# And ensure the corresponding DASHBOARD_VUE_SCRIPT has displayMetricKeys available
# (which it already does from the previous version). The script itself was likely fine,
# the template parsing was the issue.

DASHBOARD_VUE_SCRIPT = """
<script>
    const { createApp, ref, onMounted, computed } = Vue;
    const dashboardAppElement = document.getElementById('dashboard-app');

    if (dashboardAppElement) {
        window.vueApp = createApp({
            setup() {
                const title = ref('System Dashboard');
                const metrics = ref({}); // Initialize as empty
                const displayMetricKeys = ref(['total_customers', 'total_products', 'total_orders', 'total_employees', 'total_invoices']);

                const fetchMetrics = async () => {
                    try {
                        console.log("Dashboard: Fetching initial metrics...");
                        const response = await fetch('/api/dashboard');
                        if (response.ok) {
                            metrics.value = await response.json();
                            console.log("Dashboard: Metrics loaded successfully.");
                        } else {
                            console.error("Dashboard: Failed to fetch metrics, status:", response.status);
                            title.value = 'System Dashboard (Error Loading Data)';
                        }
                    } catch (e) {
                        console.error("Dashboard: Network or parsing error fetching metrics:", e);
                        title.value = 'System Dashboard (Network Error)';
                    }
                };

                const formatMetricKey = (key) => {
                    if (!key) return '';
                    return key.replace(/_/g, ' ').replace('total ', '');
                };
                
                const handleGlobalInstruction = (instruction) => {
                    console.log("Dashboard VueApp: Received global instruction:", instruction);
                };

                // This is the new, more direct onMounted logic
                onMounted(async () => {
                    console.log("Dashboard: Vue app mounted. Waiting for globalSocketReady event.");
                    await fetchMetrics(); // Fetch initial data

                    const setupSocketListeners = (socketInstance) => {
                        console.log("Dashboard: globalSocket is ready, setting up data_update listener.");
                        socketInstance.on('data_update', (msg) => {
                            const relevantMetricTypes = ['customer', 'product', 'order', 'employee', 'invoice'];
                            if (relevantMetricTypes.some(type => msg.type.includes(type))) {
                                console.log("Dashboard: Relevant data_update received, fetching metrics again.");
                                fetchMetrics();
                            }
                        });
                    };

                    // Listen for the custom event that signals the socket is ready
                    document.addEventListener('globalSocketReady', (event) => {
                        setupSocketListeners(event.detail);
                    }, { once: true }); // { once: true } ensures the listener is removed after it runs

                    // This handles the case where the socket was already connected from a previous page
                    if (window.globalSocket && window.globalSocket.connected) {
                        setupSocketListeners(window.globalSocket);
                    }
                });

                return { title, metrics, displayMetricKeys, formatMetricKey, handleGlobalInstruction };
            }
        }).mount('#dashboard-app');
    }
</script>
"""

# Replace CRM_APP_HTML
CRM_APP_HTML = """
<div id="crm-app" v-cloak>
    <div class="form-section"><h3>{{ formTitle }}</h3><form @submit.prevent="submitCustomerForm" id="crm_customer_form"><div class="form-grid"> <div class="form-group"><label for="crm-name">Name *</label><input type="text" id="crm-name" v-model="currentCustomer.name" required></div> <div class="form-group"><label for="crm-company">Company</label><input type="text" id="crm-company" v-model="currentCustomer.company"></div> <div class="form-group"><label for="crm-email">Email *</label><input type="email" id="crm-email" v-model="currentCustomer.email" required></div> <div class="form-group"><label for="crm-phone">Phone</label><input type="tel" id="crm-phone" v-model="currentCustomer.phone"></div> <div class="form-group"><label for="crm-address">Address</label><input type="text" id="crm-address" v-model="currentCustomer.address"></div> <div class="form-group"><label for="crm-status">Status</label><select id="crm-status" v-model="currentCustomer.status"><option value="Active">Active</option><option value="Lead">Lead</option><option value="Inactive">Inactive</option></select></div> <div class="form-group"><label for="crm-lead_score">Lead Score</label><input type="number" id="crm-lead_score" v-model.number="currentCustomer.lead_score"></div> <div class="form-group" style="grid-column: span 2;"><label for="crm-notes">Notes</label><textarea id="crm-notes" v-model="currentCustomer.notes"></textarea></div></div><button type="submit">{{ isEditing ? 'Update' : 'Add' }} Customer</button> <button type="button" @click="resetForm" v-if="isEditing || currentCustomer.name" class="btn-secondary" style="margin-left: 10px;">Cancel</button></form></div>
    <div class="table-section"><div class="table-container">
        <h3>Customer List</h3>
        <table>
            <thead><tr><th>ID</th><th>Name</th><th>Company</th><th>Email</th><th>Phone</th><th>Actions</th></tr></thead>
            <tbody>
                <tr v-for="customer in customers" :key="customer.id">
                    <td>{{ customer.id }}</td><td>{{ customer.name }}</td><td>{{ customer.company }}</td><td>{{ customer.email }}</td><td>{{ customer.phone }}</td>
                    <td style="white-space: nowrap;">
                        <button @click="editCustomer(customer)" class="btn-warning" style="font-size: 0.8em; padding: 0.4em 0.8em; margin-right: 5px;">Edit</button>
                        <button @click="deleteCustomer(customer.id)" class="btn-secondary" style="background-color: #ef4444; font-size: 0.8em; padding: 0.4em 0.8em;">Delete</button>
                    </td>
                </tr>
                <tr v-if="customers.length === 0"><td colspan="6" style="text-align:center; padding: 1rem;">No customers found.</td></tr>
            </tbody>
        </table>
    </div></div>
</div>
"""
# Replace CRM_VUE_SCRIPT
# In your main Python file, find and replace the CRM_VUE_SCRIPT variable

CRM_VUE_SCRIPT = """
<script>
    const { createApp, ref, onMounted } = Vue;
    if(document.getElementById('crm-app')) {
        window.vueApp = createApp({
            setup() {
                const initialCustomerForm = () => ({ id: null, name: '', company: '', email: '', phone: '', address: '', status: 'Lead', lead_score: 0, notes: '' });
                const currentCustomer = ref(initialCustomerForm());
                const customers = ref([]);
                const isEditing = ref(false);
                const formTitle = ref('Add New Customer');
                const initialIntentMessage = ref('');
                const socket = window.globalSocket || io();

                const fetchCustomers = async () => { /* This function remains the same */
                    try {
                        const r = await fetch('/api/customers');
                        if (!r.ok) {
                            // Try to get more detailed error from server
                            let errorText = `Failed to fetch customers. Status: ${r.status}`;
                            try {
                                const errJson = await r.json();
                                errorText = errJson.error || errorText;
                            } catch (e) { /* ignore if response is not json */ }
                            throw new Error(errorText);
                        }
                        customers.value = await r.json();
                    } catch (e) {
                        console.error("Fetch customers error:", e);
                        customers.value = []; // Clear list on error
                    }
                };

                // *** UPDATED submitCustomerForm with client-side validation ***
                const submitCustomerForm = async () => {
                    // 1. Client-side validation check
                    if (!currentCustomer.value.name || !currentCustomer.value.email) {
                        alert('Please fill in both Name and Email, as they are required fields.');
                        return; // Stop the function if validation fails
                    }

                    const url = isEditing.value ? `/api/customers/${currentCustomer.value.id}` : '/api/customers';
                    const method = isEditing.value ? 'PUT' : 'POST';
                    
                    try {
                        const response = await fetch(url, {
                            method: method,
                            headers: {'Content-Type':'application/json'},
                            body: JSON.stringify(currentCustomer.value)
                        });
                        if (!response.ok) {
                            const errData = await response.json();
                            throw new Error(errData.error || 'An API error occurred.');
                        }
                        resetForm(); // Reset form on success
                    } catch (e) {
                        console.error("Submit customer error:", e);
                        alert("Error: " + e.message);
                    }
                };

                // *** UPDATED editCustomer with a console.log for debugging ***
                const editCustomer = (customer) => {
                    console.log("Edit button clicked. Populating form with customer:", customer.id); // Debugging log
                    // Create a deep copy for editing to avoid mutating the list item directly
                    currentCustomer.value = JSON.parse(JSON.stringify(customer));
                    isEditing.value = true;
                    formTitle.value = 'Edit Customer';
                    // Scroll to the form to make it visible
                    document.getElementById('crm_customer_form').scrollIntoView({ behavior: 'smooth' });
                };

                const resetForm = () => { /* This function remains the same */
                    currentCustomer.value = initialCustomerForm();
                    isEditing.value = false;
                    formTitle.value = 'Add New Customer';
                    initialIntentMessage.value = '';
                };
                
                const deleteCustomer = async (customerId) => { /* This function remains the same */
                    if (!confirm(`Are you sure you want to delete customer ${customerId}?`)) return;
                    try {
                        const response = await fetch(`/api/customers/${customerId}`, { method: 'DELETE' });
                        if (!response.ok) {
                            const errData = await response.json();
                            throw new Error(errData.message || `HTTP error ${response.status}`);
                        }
                        // UI will update automatically via Socket.IO
                    } catch (error) {
                        console.error("Delete customer error:", error);
                        alert("Error: " + error.message);
                    }
                };
                
                const handleGlobalInstruction = (i) => { /* This function remains the same */
                    console.log("CRM App instruction:", i);
                    if(i.target_app && i.target_app !== 'crm') return;
                    if (i.action === 'navigate' && i.url === '/crm_vue' && i.params && i.params.intent === 'new_customer_entry') {
                        resetForm();
                        initialIntentMessage.value = "Provide customer details.";
                        document.getElementById('crm-name')?.focus();
                    } else if (i.action === 'fill_field' && currentCustomer.value.hasOwnProperty(i.field_id)) {
                        currentCustomer.value[i.field_id] = i.value;
                    } else if (i.action === 'clear_form_fields' && (!i.form_id || i.form_id === 'crm_customer_form')) {
                        resetForm();
                    }
                };
                
                const checkUrlParams = () => { /* This function remains the same */
                     const p = new URLSearchParams(window.location.search);
                     if (p.get('intent')==='new_customer_entry') {
                        handleGlobalInstruction({action:'navigate', url:'/crm_vue', params:{intent:'new_customer_entry'}});
                        window.history.replaceState({},'',window.location.pathname);
                     }
                };

                onMounted(() => { /* This onMounted hook pattern is the correct one */
                    console.log("CRM: Vue app mounted. Waiting for globalSocketReady event.");
                    fetchCustomers();
                    checkUrlParams();

                    const setupSocketListeners = (socketInstance) => {
                        console.log("CRM: globalSocket is ready, setting up listeners.");
                        socketInstance.on('data_update', (msg) => {
                            if (['customer_added', 'customer_updated', 'customer_deleted'].includes(msg.type)) {
                                fetchCustomers();
                            }
                        });
                        socketInstance.on('ui_instruction', handleGlobalInstruction);
                    };

                    document.addEventListener('globalSocketReady', (event) => {
                        setupSocketListeners(event.detail);
                    }, { once: true });

                    if (window.globalSocket && window.globalSocket.connected) {
                        setupSocketListeners(window.globalSocket);
                    }
                });
                
                return { currentCustomer, customers, isEditing, formTitle, initialIntentMessage, submitCustomerForm, editCustomer, resetForm, deleteCustomer, handleGlobalInstruction };
            }
        }).mount('#crm-app');
    }
</script>
"""

# In main_erp_vue_final.py

# Replace INVENTORY_APP_HTML
INVENTORY_APP_HTML = """
<div id="inventory-app" v-cloak>
    <div class="form-section">
        <h3>{{ formTitle }}</h3>
        <form @submit.prevent="submitProductForm" id="inventory_product_form">
            <div class="form-grid">
                <div class="form-group"><label for="inv-name">Product Name *</label><input type="text" id="inv-name" v-model="currentProduct.name" required></div>
                <div class="form-group"><label for="inv-sku">SKU *</label><input type="text" id="inv-sku" v-model="currentProduct.sku" required></div>
                <div class="form-group"><label for="inv-category">Category</label><input type="text" id="inv-category" v-model="currentProduct.category"></div>
                <div class="form-group"><label for="inv-price">Price *</label><input type="number" step="0.01" id="inv-price" v-model.number="currentProduct.price" required></div>
                <div class="form-group"><label for="inv-cost">Cost</label><input type="number" step="0.01" id="inv-cost" v-model.number="currentProduct.cost"></div>
                <div class="form-group"><label for="inv-stock_quantity">Stock Qty *</label><input type="number" id="inv-stock_quantity" v-model.number="currentProduct.stock_quantity" required></div>
                <div class="form-group"><label for="inv-reorder_level">Reorder Level</label><input type="number" id="inv-reorder_level" v-model.number="currentProduct.reorder_level"></div>
                <div class="form-group" style="grid-column: span 2;"><label for="inv-description">Description</label><textarea id="inv-description" v-model="currentProduct.description"></textarea></div>
            </div>
            <button type="submit">{{ isEditing ? 'Update' : 'Add' }} Product</button>
            <button type="button" @click="resetForm" v-if="isEditing || currentProduct.name" class="btn-secondary" style="margin-left: 10px;">Cancel</button>
        </form>
    </div>
    <div class="table-section"><div class="table-container">
        <h3>Product List</h3>
        <table>
            <thead><tr><th>ID</th><th>Name</th><th>SKU</th><th>Category</th><th>Price</th><th>Stock</th><th>Reorder Lvl</th><th>Actions</th></tr></thead>
            <tbody>
                <tr v-for="product in products" :key="product.id">
                    <td>{{ product.id }}</td><td>{{ product.name }}</td><td>{{ product.sku }}</td><td>{{ product.category }}</td>
                    <td>${{ product.price ? product.price.toFixed(2) : '0.00' }}</td><td>{{ product.stock_quantity }}</td><td>{{ product.reorder_level }}</td>
                    <td style="white-space: nowrap;">
                        <button @click="editProduct(product)" class="btn-warning" style="font-size: 0.8em; padding: 0.4em 0.8em; margin-right: 5px;">Edit</button>
                        <button @click="deleteProduct(product.id)" class="btn-secondary" style="background-color: #ef4444; font-size: 0.8em; padding: 0.4em 0.8em;">Delete</button>
                    </td>
                </tr>
                <tr v-if="products.length === 0"><td colspan="8" style="text-align:center; padding: 1rem;">No products found.</td></tr>
            </tbody>
        </table>
    </div></div>
    <p v-if="initialIntentMessage" style="margin-top:1rem; padding:0.5rem; background-color: #e9ecef; border-radius:4px;">{{ initialIntentMessage }}</p>
</div>
"""

# Replace INVENTORY_VUE_SCRIPT
INVENTORY_VUE_SCRIPT = """
<script>
    const { createApp, ref, onMounted } = Vue;
    if(document.getElementById('inventory-app')) {
        window.vueApp = createApp({
            setup() {
                const initialProductForm = () => ({ id: null, name: '', sku: '', category: '', price: 0, cost: 0, stock_quantity: 0, reorder_level: 0, description: '' });
                const currentProduct = ref(initialProductForm());
                const products = ref([]);
                const isEditing = ref(false);
                const formTitle = ref('Add New Product');
                const initialIntentMessage = ref('');
                const socket = window.globalSocket || io();

                const fetchProducts = async () => { try { const r = await fetch('/api/products'); if(!r.ok) throw Error('Failed to fetch'); products.value = await r.json(); } catch(e){console.error(e);}};
                
                const submitProductForm = async () => {
                    const url = isEditing.value ? `/api/products/${currentProduct.value.id}` : '/api/products';
                    const method = isEditing.value ? 'PUT' : 'POST';
                    try {
                        const response = await fetch(url, {method:method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(currentProduct.value)});
                        if(!response.ok){ const ed = await response.json(); throw Error(ed.message || 'HTTP Error');}
                        resetForm();
                    } catch(e){console.error(e); alert('Error: '+e.message);}};

                const editProduct = (p) => { currentProduct.value = JSON.parse(JSON.stringify(p)); isEditing.value = true; formTitle.value = 'Edit Product'; document.getElementById('inventory_product_form').scrollIntoView({behavior:'smooth'});};
                
                const resetForm = () => { currentProduct.value = initialProductForm(); isEditing.value = false; formTitle.value = 'Add New Product'; initialIntentMessage.value = '';};

                const deleteProduct = async (productId) => {
                    if (!confirm(`Are you sure you want to delete product ${productId}?`)) return;
                    try {
                        const response = await fetch(`/api/products/${productId}`, { method: 'DELETE' });
                        if (!response.ok) {
                            const errData = await response.json();
                            throw new Error(errData.message || `HTTP error ${response.status}`);
                        }
                    } catch (error) { console.error("Delete product error:", error); alert("Error: " + error.message); }
                };
                
                const handleGlobalInstruction = (i) => { console.log("Inv App instruction:", i); if(i.target_app && i.target_app !== 'inventory') return; if(i.action === 'navigate' && i.url === '/inventory_vue' && i.params && i.params.intent === 'new_product_entry'){resetForm(); initialIntentMessage.value = "Provide product details."; document.getElementById('inv-name')?.focus(); } else if (i.action === 'fill_field' && currentProduct.value.hasOwnProperty(i.field_id)) { currentProduct.value[i.field_id] = i.value; } else if (i.action === 'clear_form_fields' && (!i.form_id || i.form_id === 'inventory_product_form')) { resetForm();}};
                
                const checkUrlParams = () => { const p = new URLSearchParams(window.location.search); if(p.get('intent')==='new_product_entry'){handleGlobalInstruction({action:'navigate',url:'/inventory_vue',params:{intent:'new_product_entry'}}); window.history.replaceState({},'',window.location.pathname);}};
                
                onMounted(() => {
                    console.log("Inventory: Vue app mounted. Waiting for globalSocketReady event.");
                    fetchProducts();
                    checkUrlParams();

                    const setupSocketListeners = (socketInstance) => {
                        console.log("Inventory: globalSocket is ready, setting up listeners.");
                        socketInstance.on('data_update', (msg) => {
                            if (['product_added', 'product_updated', 'product_deleted'].includes(msg.type)) {
                                fetchProducts();
                            }
                        });
                    };

                    document.addEventListener('globalSocketReady', (event) => {
                        setupSocketListeners(event.detail);
                    }, { once: true });

                    if (window.globalSocket && window.globalSocket.connected) {
                        setupSocketListeners(window.globalSocket);
                    }
                });
                
                return { currentProduct, products, isEditing, formTitle, initialIntentMessage, submitProductForm, editProduct, deleteProduct, resetForm, handleGlobalInstruction };
            }
        }).mount('#inventory-app');
    }
</script>
"""

# Replace ORDERS_APP_HTML
ORDERS_APP_HTML = """
<div id="orders-app" v-cloak>
    <div class="form-section">
        <h3>{{ formTitle }}</h3>
        <form @submit.prevent="submitOrderForm" id="orders_order_form">
            <div class="form-grid">
                <div class="form-group"><label for="ord-customer_id">Customer *</label><select id="ord-customer_id" v-model="currentOrder.customer_id" required><option disabled value="">Please select one</option><option v-for="customer in customers" :value="customer.id" :key="customer.id">{{customer.name}} ({{customer.id}})</option></select></div>
                <div class="form-group"><label for="ord-order_date">Order Date *</label><input type="date" id="ord-order_date" v-model="currentOrder.order_date" required></div>
                <div class="form-group"><label for="ord-total_amount">Total Amount *</label><input type="number" step="0.01" id="ord-total_amount" v-model.number="currentOrder.total_amount" required></div>
                <div class="form-group"><label for="ord-status">Status</label><select id="ord-status" v-model="currentOrder.status"><option value="Pending">Pending</option><option value="Processing">Processing</option><option value="Shipped">Shipped</option><option value="Delivered">Delivered</option></select></div>
                <div class="form-group" style="grid-column: span 2;"><label for="ord-shipping_address">Shipping Address</label><textarea id="ord-shipping_address" v-model="currentOrder.shipping_address"></textarea></div>
                <div class="form-group" style="grid-column: span 2;"><label for="ord-notes">Notes</label><textarea id="ord-notes" v-model="currentOrder.notes"></textarea></div>
            </div>
            <button type="submit">{{ isEditing ? 'Update' : 'Add' }} Order</button>
            <button type="button" @click="resetForm" v-if="isEditing || currentOrder.customer_id" class="btn-secondary" style="margin-left: 10px;">Cancel</button>
        </form>
    </div>
    <div class="table-section"><div class="table-container">
        <h3>Order List</h3>
        <table>
            <thead><tr><th>ID</th><th>Cust. ID</th><th>Order Date</th><th>Total Amt</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
                <tr v-for="order in orders" :key="order.id">
                    <td>{{ order.id }}</td><td>{{ order.customer_id }}</td><td>{{ order.order_date }}</td>
                    <td>${{ order.total_amount ? order.total_amount.toFixed(2) : '0.00' }}</td>
                    <td><span :class="['status-badge', 'status-' + (order.status || 'pending').toLowerCase()]">{{ order.status }}</span></td>
                    <td style="white-space: nowrap;">
                        <button @click="editOrder(order)" class="btn-warning" style="font-size: 0.8em; padding: 0.4em 0.8em; margin-right: 5px;">Edit</button>
                        <button @click="deleteOrder(order.id)" class="btn-secondary" style="background-color: #ef4444; font-size: 0.8em; padding: 0.4em 0.8em;">Delete</button>
                    </td>
                </tr>
                <tr v-if="orders.length === 0"><td colspan="6" style="text-align:center; padding: 1rem;">No orders found.</td></tr>
            </tbody>
        </table>
    </div></div>
</div>
"""
# Replace ORDERS_VUE_SCRIPT
# In main_erp_vue_final.py, replace ORDERS_VUE_SCRIPT

ORDERS_VUE_SCRIPT = """
<script>
    const { createApp, ref, onMounted } = Vue;
    if(document.getElementById('orders-app')) {
        window.vueApp = createApp({
            setup() {
                const initialOrderForm = () => ({ id: null, customer_id: '', order_date: new Date().toISOString().slice(0,10), total_amount: 0, status: 'Pending', shipping_address: '', notes: '' });
                const currentOrder = ref(initialOrderForm());
                const orders = ref([]); const customers = ref([]);
                const isEditing = ref(false); const formTitle = ref('Add New Order');
                const socket = window.globalSocket || io();

                const fetchOrders = async () => { try { const r = await fetch('/api/orders'); if(!r.ok) throw Error('Failed to fetch orders'); orders.value = await r.json(); } catch(e){console.error(e);}};
                const fetchCustomersForDropdown = async () => { try { const r = await fetch('/api/customers'); if(!r.ok) throw Error('Failed to fetch customers'); customers.value = await r.json(); } catch(e){console.error(e);}};
                
                const submitOrderForm = async () => {
                    const url = isEditing.value ? `/api/orders/${currentOrder.value.id}` : '/api/orders';
                    const method = isEditing.value ? 'PUT' : 'POST';
                    try {
                        const response = await fetch(url, {method:method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(currentOrder.value)});
                        if(!response.ok){ const ed = await response.json(); throw Error(ed.message || 'HTTP Error'); }
                        resetForm();
                    } catch(e){console.error(e); alert('Error: '+e.message); }
                };
                const editOrder = (order) => { currentOrder.value = JSON.parse(JSON.stringify(order)); isEditing.value = true; formTitle.value = 'Edit Order'; document.getElementById('orders_order_form').scrollIntoView({behavior:'smooth'});};
                const resetForm = () => { currentOrder.value = initialOrderForm(); isEditing.value = false; formTitle.value = 'Add New Order';};
                const deleteOrder = async (orderId) => { if (!confirm(`Delete order ${orderId}?`)) return; try { const r = await fetch(`/api/orders/${orderId}`,{method:'DELETE'}); if(!r.ok) throw Error('Delete failed'); } catch (e) {console.error(e); alert('Error: '+e.message);}};

                const handleGlobalInstruction = (i) => { console.log("Orders App instruction:", i); if(i.target_app && i.target_app !== 'orders') return; if(i.action === 'navigate' && i.url === '/orders_vue' && i.params && i.params.intent === 'new_order_entry'){resetForm(); document.getElementById('ord-customer_id')?.focus(); } else if (i.action === 'fill_field' && currentOrder.value.hasOwnProperty(i.field_id)) { currentOrder.value[i.field_id] = i.value; } else if (i.action === 'clear_form_fields' && (!i.form_id || i.form_id === 'orders_order_form')) { resetForm();}};
                const checkUrlParams = () => { const p = new URLSearchParams(window.location.search); if(p.get('intent')==='new_order_entry'){handleGlobalInstruction({action:'navigate',url:'/orders_vue',params:{intent:'new_order_entry'}}); window.history.replaceState({},'',window.location.pathname);}};
                
                onMounted(() => {
                    console.log("Orders: Vue app mounted. Waiting for globalSocketReady event.");
                    fetchOrders();
                    fetchCustomersForDropdown(); // This one has a second fetch call
                    checkUrlParams();

                    const setupSocketListeners = (socketInstance) => {
                        console.log("Orders: globalSocket is ready, setting up listeners.");
                        socketInstance.on('data_update', (msg) => {
                            if (['order_added', 'order_updated', 'order_deleted'].includes(msg.type)) {
                                fetchOrders();
                            }
                            // Also refresh the customer dropdown if customers are changed
                            if (['customer_added', 'customer_updated', 'customer_deleted'].includes(msg.type)) {
                                fetchCustomersForDropdown();
                            }
                        });
                    };

                    document.addEventListener('globalSocketReady', (event) => {
                        setupSocketListeners(event.detail);
                    }, { once: true });

                    if (window.globalSocket && window.globalSocket.connected) {
                        setupSocketListeners(window.globalSocket);
                    }
                });
                return { currentOrder, orders, customers, isEditing, formTitle, submitOrderForm, editOrder, deleteOrder, resetForm, handleGlobalInstruction };
            }
        }).mount('#orders-app');
    }
</script>
"""

# --- HR (Employees) Vue App (New) ---
# Replace HR_APP_HTML
HR_APP_HTML = """
<div id="hr-app" v-cloak>
    <div class="form-section">
        <h3>{{ formTitle }}</h3>
        <form @submit.prevent="submitEmployeeForm" id="hr_employee_form">
            <div class="form-grid">
                <div class="form-group"><label for="hr-employee_id">Employee ID *</label><input type="text" id="hr-employee_id" v-model="currentEmployee.employee_id" required></div>
                <div class="form-group"><label for="hr-first_name">First Name *</label><input type="text" id="hr-first_name" v-model="currentEmployee.first_name" required></div>
                <div class="form-group"><label for="hr-last_name">Last Name *</label><input type="text" id="hr-last_name" v-model="currentEmployee.last_name" required></div>
                <div class="form-group"><label for="hr-email">Email *</label><input type="email" id="hr-email" v-model="currentEmployee.email" required></div>
                <div class="form-group"><label for="hr-phone">Phone</label><input type="tel" id="hr-phone" v-model="currentEmployee.phone"></div>
                <div class="form-group"><label for="hr-department">Department</label><input type="text" id="hr-department" v-model="currentEmployee.department"></div>
                <div class="form-group"><label for="hr-position">Position</label><input type="text" id="hr-position" v-model="currentEmployee.position"></div>
                <div class="form-group"><label for="hr-hire_date">Hire Date</label><input type="date" id="hr-hire_date" v-model="currentEmployee.hire_date"></div>
                <div class="form-group"><label for="hr-salary">Salary</label><input type="number" step="1000" id="hr-salary" v-model.number="currentEmployee.salary"></div>
                <div class="form-group"><label for="hr-status">Status</label><select id="hr-status" v-model="currentEmployee.status"><option value="Active">Active</option><option value="On Leave">On Leave</option><option value="Terminated">Terminated</option></select></div>
            </div>
            <button type="submit">{{ isEditing ? 'Update' : 'Add' }} Employee</button>
            <button type="button" @click="resetForm" v-if="isEditing || currentEmployee.employee_id" class="btn-secondary" style="margin-left: 10px;">Cancel</button>
        </form>
    </div>
    <div class="table-section"><div class="table-container">
        <h3>Employee List</h3>
        <table>
            <thead><tr><th>Emp. ID</th><th>Name</th><th>Email</th><th>Department</th><th>Position</th><th>Hire Date</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
                <tr v-for="employee in employees" :key="employee.id">
                    <td>{{ employee.employee_id }}</td><td>{{ employee.first_name }} {{ employee.last_name }}</td><td>{{ employee.email }}</td>
                    <td>{{ employee.department }}</td><td>{{ employee.position }}</td><td>{{ employee.hire_date }}</td>
                    <td><span :class="['status-badge', 'status-' + (employee.status || 'active').toLowerCase().replace(' ', '-')]">{{ employee.status }}</span></td>
                    <td style="white-space: nowrap;">
                        <button @click="editEmployee(employee)" class="btn-warning" style="font-size: 0.8em; padding: 0.4em 0.8em; margin-right: 5px;">Edit</button>
                        <button @click="deleteEmployee(employee.employee_id)" class="btn-secondary" style="background-color: #ef4444; font-size: 0.8em; padding: 0.4em 0.8em;">Delete</button>
                    </td>
                </tr>
                <tr v-if="employees.length === 0"><td colspan="8" style="text-align:center; padding: 1rem;">No employees found.</td></tr>
            </tbody>
        </table>
    </div></div>
</div>
"""
# In main_erp_vue_final.py, replace HR_VUE_SCRIPT

HR_VUE_SCRIPT = """
<script>
    const { createApp, ref, onMounted } = Vue;
    if(document.getElementById('hr-app')) {
        window.vueApp = createApp({
            setup() {
                const initialEmployeeForm = () => ({ id: null, employee_id: '', first_name: '', last_name: '', email: '', phone: '', department: '', position: '', hire_date: new Date().toISOString().slice(0,10), salary:0, status:'Active' });
                const currentEmployee = ref(initialEmployeeForm());
                const employees = ref([]);
                const isEditing = ref(false); const formTitle = ref('Add New Employee');
                const socket = window.globalSocket || io();

                const fetchEmployees = async () => { try { const r = await fetch('/api/employees'); if(!r.ok) throw Error('Failed to fetch'); employees.value = await r.json(); } catch(e){console.error(e);}};
                const submitEmployeeForm = async () => {
                    const url = isEditing.value ? `/api/employees/${currentEmployee.value.employee_id}` : '/api/employees';
                    const method = isEditing.value ? 'PUT' : 'POST';
                    try {
                        const response = await fetch(url, {method:method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(currentEmployee.value)});
                        if(!response.ok){ const ed = await response.json(); throw Error(ed.message || 'HTTP Error'); }
                        resetForm();
                    } catch(e){console.error(e); alert('Error: '+e.message); }
                };
                const editEmployee = (emp) => { currentEmployee.value = JSON.parse(JSON.stringify(emp)); isEditing.value = true; formTitle.value = 'Edit Employee'; document.getElementById('hr_employee_form').scrollIntoView({behavior:'smooth'});};
                const resetForm = () => { currentEmployee.value = initialEmployeeForm(); isEditing.value = false; formTitle.value = 'Add New Employee';};
                const deleteEmployee = async (employeeId) => { if (!confirm(`Delete employee ${employeeId}?`)) return; try { const r = await fetch(`/api/employees/${employeeId}`,{method:'DELETE'}); if(!r.ok) throw Error('Delete failed');} catch(e){console.error(e); alert('Error: '+e.message);}};

                const handleGlobalInstruction = (i) => { console.log("HR App instruction:",i); if(i.target_app && i.target_app !== 'hr') return; if(i.action === 'navigate' && i.url === '/hr_vue' && i.params && i.params.intent === 'new_employee_entry'){resetForm(); document.getElementById('hr-employee_id')?.focus(); } else if (i.action === 'fill_field' && currentEmployee.value.hasOwnProperty(i.field_id)) { currentEmployee.value[i.field_id] = i.value; } else if (i.action === 'clear_form_fields' && (!i.form_id || i.form_id === 'hr_employee_form')) { resetForm();}};
                const checkUrlParams = () => { const p = new URLSearchParams(window.location.search); if(p.get('intent')==='new_employee_entry'){handleGlobalInstruction({action:'navigate',url:'/hr_vue',params:{intent:'new_employee_entry'}}); window.history.replaceState({},'',window.location.pathname);}};
                
                onMounted(() => {
                    console.log("HR: Vue app mounted. Waiting for globalSocketReady event.");
                    fetchEmployees();
                    checkUrlParams();

                    const setupSocketListeners = (socketInstance) => {
                        console.log("HR: globalSocket is ready, setting up listeners.");
                        socketInstance.on('data_update', (msg) => {
                            if (['employee_added', 'employee_updated', 'employee_deleted'].includes(msg.type)) {
                                fetchEmployees();
                            }
                        });
                    };

                    document.addEventListener('globalSocketReady', (event) => {
                        setupSocketListeners(event.detail);
                    }, { once: true });

                    if (window.globalSocket && window.globalSocket.connected) {
                        setupSocketListeners(window.globalSocket);
                    }
                });
                return { currentEmployee, employees, isEditing, formTitle, submitEmployeeForm, editEmployee, deleteEmployee, resetForm, handleGlobalInstruction };
            }
        }).mount('#hr-app');
    }
</script>
"""
# Replace FINANCE_APP_HTML
FINANCE_APP_HTML = """
<div id="finance-app" v-cloak>
    <div class="form-section">
        <h3>{{ formTitle }}</h3>
        <form @submit.prevent="submitInvoiceForm" id="finance_invoice_form">
            <div class="form-grid">
                <div class="form-group"><label for="fin-invoice_number">Invoice #</label><input type="text" id="fin-invoice_number" v-model="currentInvoice.invoice_number" placeholder="Auto-generated if blank"></div>
                <div class="form-group"><label for="fin-customer_id">Customer *</label><select id="fin-customer_id" v-model="currentInvoice.customer_id" required><option disabled value="">Select Customer</option><option v-for="customer in customers" :value="customer.id" :key="customer.id">{{customer.name}} ({{customer.id}})</option></select></div>
                <div class="form-group"><label for="fin-order_id">Order ID (Optional)</label><select id="fin-order_id" v-model="currentInvoice.order_id"><option value="">N/A</option><option v-for="order in orders" :value="order.id" :key="order.id">{{order.id}} (Cust: {{order.customer_id}})</option></select></div>
                <div class="form-group"><label for="fin-issue_date">Issue Date *</label><input type="date" id="fin-issue_date" v-model="currentInvoice.issue_date" required></div>
                <div class="form-group"><label for="fin-due_date">Due Date *</label><input type="date" id="fin-due_date" v-model="currentInvoice.due_date" required></div>
                <div class="form-group"><label for="fin-total_amount">Total Amount *</label><input type="number" step="0.01" id="fin-total_amount" v-model.number="currentInvoice.total_amount" required></div>
                <div class="form-group"><label for="fin-paid_amount">Paid Amount</label><input type="number" step="0.01" id="fin-paid_amount" v-model.number="currentInvoice.paid_amount"></div>
                <div class="form-group"><label for="fin-status">Status</label><select id="fin-status" v-model="currentInvoice.status"><option value="Pending">Pending</option><option value="Paid">Paid</option><option value="Overdue">Overdue</option><option value="Cancelled">Cancelled</option></select></div>
            </div>
            <button type="submit">{{ isEditing ? 'Update' : 'Create' }} Invoice</button>
            <button type="button" @click="resetForm" v-if="isEditing || currentInvoice.customer_id" class="btn-secondary" style="margin-left: 10px;">Cancel</button>
        </form>
    </div>
    <div class="table-section"><div class="table-container">
        <h3>Invoice List</h3>
        <table>
            <thead><tr><th>Inv #</th><th>Cust. ID</th><th>Order ID</th><th>Issue Date</th><th>Due Date</th><th>Total</th><th>Paid</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
                <tr v-for="invoice in invoices" :key="invoice.id">
                    <td>{{ invoice.invoice_number }}</td><td>{{ invoice.customer_id }}</td><td>{{ invoice.order_id }}</td>
                    <td>{{ invoice.issue_date }}</td><td>{{ invoice.due_date }}</td>
                    <td>${{ invoice.total_amount ? invoice.total_amount.toFixed(2) : '0.00' }}</td>
                    <td>${{ invoice.paid_amount ? invoice.paid_amount.toFixed(2) : '0.00' }}</td>
                    <td><span :class="['status-badge', 'status-' + (invoice.status || 'pending').toLowerCase()]">{{ invoice.status }}</span></td>
                    <td style="white-space: nowrap;">
                        <button @click="editInvoice(invoice)" class="btn-warning" style="font-size: 0.8em; padding: 0.4em 0.8em; margin-right: 5px;">Edit</button>
                        <button @click="deleteInvoice(invoice.id)" class="btn-secondary" style="background-color: #ef4444; font-size: 0.8em; padding: 0.4em 0.8em;">Delete</button>
                    </td>
                </tr>
                <tr v-if="invoices.length === 0"><td colspan="9" style="text-align:center; padding: 1rem;">No invoices found.</td></tr>
            </tbody>
        </table>
    </div></div>
</div>
"""
# Replace FINANCE_VUE_SCRIPT
# In main_erp_vue_final.py, replace FINANCE_VUE_SCRIPT

FINANCE_VUE_SCRIPT = """
<script>
    const { createApp, ref, onMounted } = Vue;
    if(document.getElementById('finance-app')) {
        window.vueApp = createApp({
            setup() {
                const defaultDueDate = () => { const d = new Date(); d.setDate(d.getDate() + 30); return d.toISOString().slice(0,10); };
                const initialInvoiceForm = () => ({ id: null, invoice_number: '', customer_id: '', order_id: '', issue_date: new Date().toISOString().slice(0,10), due_date: defaultDueDate(), total_amount: 0, paid_amount: 0, status: 'Pending' });
                const currentInvoice = ref(initialInvoiceForm());
                const invoices = ref([]); const customers = ref([]); const orders = ref([]);
                const isEditing = ref(false); const formTitle = ref('Create New Invoice');
                const socket = window.globalSocket || io();

                const fetchData = async () => {
                    try {
                        const [invRes, custRes, ordRes] = await Promise.all([fetch('/api/invoices'), fetch('/api/customers'), fetch('/api/orders')]);
                        if(invRes.ok) invoices.value = await invRes.json(); else console.error('Failed to fetch invoices');
                        if(custRes.ok) customers.value = await custRes.json(); else console.error('Failed to fetch customers for dropdown');
                        if(ordRes.ok) orders.value = await ordRes.json(); else console.error('Failed to fetch orders for dropdown');
                    } catch(e){console.error("Fetch finance data error:", e);}
                };
                const submitInvoiceForm = async () => {
                    const url = isEditing.value ? `/api/invoices/${currentInvoice.value.id}` : '/api/invoices';
                    const method = isEditing.value ? 'PUT' : 'POST';
                    try {
                        const response = await fetch(url, {method:method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(currentInvoice.value)});
                        if(!response.ok){ const ed = await response.json(); throw Error(ed.message || 'HTTP Error'); }
                        resetForm();
                    } catch(e){console.error(e); alert('Error: '+e.message); }
                };
                const editInvoice = (inv) => { currentInvoice.value = JSON.parse(JSON.stringify(inv)); isEditing.value = true; formTitle.value = 'Edit Invoice'; document.getElementById('finance_invoice_form').scrollIntoView({behavior:'smooth'});};
                const resetForm = () => { currentInvoice.value = initialInvoiceForm(); isEditing.value = false; formTitle.value = 'Create New Invoice';};
                const deleteInvoice = async (invoiceId) => { if (!confirm(`Delete invoice ${invoiceId}?`)) return; try { const r = await fetch(`/api/invoices/${invoiceId}`,{method:'DELETE'}); if(!r.ok) throw Error('Delete failed'); } catch(e){console.error(e); alert('Error: '+e.message);}};

                const handleGlobalInstruction = (i) => { console.log("Finance App instruction:", i); if(i.target_app && i.target_app !== 'finance') return; if(i.action === 'navigate' && i.url === '/finance_vue' && i.params && i.params.intent === 'new_invoice_entry'){resetForm(); document.getElementById('fin-customer_id')?.focus(); } else if (i.action === 'fill_field' && currentInvoice.value.hasOwnProperty(i.field_id)) { currentInvoice.value[i.field_id] = i.value; } else if (i.action === 'clear_form_fields' && (!i.form_id || i.form_id === 'finance_invoice_form')) { resetForm();}};
                const checkUrlParams = () => { const p = new URLSearchParams(window.location.search); if(p.get('intent')==='new_invoice_entry'){handleGlobalInstruction({action:'navigate',url:'/finance_vue',params:{intent:'new_invoice_entry'}}); window.history.replaceState({},'',window.location.pathname);}};
                
                onMounted(() => {
                    console.log("Finance: Vue app mounted. Waiting for globalSocketReady event.");
                    fetchData(); // This page fetches invoices, customers, and orders
                    checkUrlParams();

                    const setupSocketListeners = (socketInstance) => {
                        console.log("Finance: globalSocket is ready, setting up listeners.");
                        socketInstance.on('data_update', (msg) => {
                            // Re-fetch all data for this page if any relevant item changes
                            if (['invoice_added', 'invoice_updated', 'invoice_deleted', 'customer_added', 'order_added'].includes(msg.type)) {
                                fetchData();
                            }
                        });
                    };

                    document.addEventListener('globalSocketReady', (event) => {
                        setupSocketListeners(event.detail);
                    }, { once: true });

                    if (window.globalSocket && window.globalSocket.connected) {
                        setupSocketListeners(window.globalsocket);
                    }
                });
                return { currentInvoice, invoices, customers, orders, isEditing, formTitle, submitInvoiceForm, editInvoice, deleteInvoice, resetForm, handleGlobalInstruction };
            }
        }).mount('#finance-app');
    }
</script>
"""

# ==================== FLASK ROUTES ====================
@app.route('/')
def dashboard_page(): 
    voice_url = os.environ.get("VOICE_BACKEND_URL", "ws://127.0.0.1:7861/")
    return create_base_html_page(DASHBOARD_VUE_SCRIPT, DASHBOARD_APP_HTML, '/', voice_backend_url=voice_url)
@app.route('/crm_vue')
def crm_page(): 
    voice_url = os.environ.get("VOICE_BACKEND_URL", "ws://127.0.0.1:7861/")
    return create_base_html_page(CRM_VUE_SCRIPT, CRM_APP_HTML, '/crm_vue', voice_backend_url=voice_url)
@app.route('/inventory_vue')
def inventory_page(): 
    voice_url = os.environ.get("VOICE_BACKEND_URL", "ws://127.0.0.1:7861/")
    return create_base_html_page(INVENTORY_VUE_SCRIPT, INVENTORY_APP_HTML, '/inventory_vue', voice_backend_url=voice_url)
@app.route('/orders_vue')
def orders_page(): 
    voice_url = os.environ.get("VOICE_BACKEND_URL", "ws://127.0.0.1:7861/")
    return create_base_html_page(ORDERS_VUE_SCRIPT, ORDERS_APP_HTML, '/orders_vue', voice_backend_url=voice_url)
@app.route('/hr_vue')
def hr_page(): 
    voice_url = os.environ.get("VOICE_BACKEND_URL", "ws://127.0.0.1:7861/")
    return create_base_html_page(HR_VUE_SCRIPT, HR_APP_HTML, '/hr_vue', voice_backend_url=voice_url)
@app.route('/finance_vue')
def finance_page(): 
    voice_url = os.environ.get("VOICE_BACKEND_URL", "ws://127.0.0.1:7861/")
    return create_base_html_page(FINANCE_VUE_SCRIPT, FINANCE_APP_HTML, '/finance_vue', voice_backend_url=voice_url)

# ==================== API ENDPOINTS (Ensure all are implemented) ====================
@app.route('/api/dashboard', methods=['GET'])
def api_dashboard(): return jsonify(data_manager.get_dashboard_metrics())

# Customers
# NEW version to put in your file
# In main_erp_vue_final.py, replace the api_customers function with this:

# In main_erp_vue_final.py, replace the api_customers function

@app.route('/api/customers', methods=['GET', 'POST'])
def api_customers():
    if request.method == 'GET':
        # This is now safe because DataManager prevents NaN from being stored
        return jsonify(data_manager.customers.to_dict('records'))
        
    elif request.method == 'POST':
        item = data_manager.add_customer(request.get_json())
        return jsonify(item), 201 if item else (jsonify({"error": "Missing required fields"}), 400)
        
    
@app.route('/api/customers/<customer_id>', methods=['PUT', 'DELETE'])
def api_customer_detail(customer_id):
    if request.method == 'PUT':
        item = data_manager.update_customer(customer_id, request.get_json())
        return jsonify(item) if item else (jsonify({'error': 'Not found or update failed'}), 404)
    elif request.method == 'DELETE':
        item = data_manager.delete_customer(customer_id)
        return jsonify(item) if item else (jsonify({'error': 'Not found or delete failed'}), 404)

# Products
# In main_erp_vue_final.py

@app.route('/api/products', methods=['GET', 'POST'])
def api_products():
    if request.method == 'GET':
        product_df = data_manager.products
        if product_df.empty:
            return jsonify([])
        # Replace pandas NaN with Python's None for valid JSON
        records_df = product_df.where(pd.notnull(product_df), None)
        records = records_df.to_dict('records')
        return jsonify(records)
        
    elif request.method == 'POST':
        item = data_manager.add_product(request.get_json())
        return jsonify(item), 201 if item else (jsonify({"error": "Missing required fields"}), 400)
    
@app.route('/api/products/<product_id>', methods=['PUT', 'DELETE'])
def api_product_detail(product_id):
    if request.method == 'PUT':
        item = data_manager.update_product(product_id, request.get_json())
        return jsonify(item) if item else (jsonify({'error': 'Not found or update failed'}), 404)
    elif request.method == 'DELETE':
        item = data_manager.delete_product(product_id)
        return jsonify(item) if item else (jsonify({'error': 'Not found or delete failed'}), 404)

# Employees
# In main_erp_vue_final.py

@app.route('/api/employees', methods=['GET', 'POST'])
def api_employees():
    if request.method == 'GET':
        employees_df = data_manager.employees
        if employees_df.empty:
            return jsonify([])
        # Replace pandas NaN with Python's None for valid JSON
        records_df = employees_df.where(pd.notnull(employees_df), None)
        records = records_df.to_dict('records')
        return jsonify(records)
        
    elif request.method == 'POST': 
        new_emp = data_manager.add_employee(request.get_json())
        return jsonify(new_emp), 201
    
@app.route('/api/employees/<employee_id_custom>', methods=['PUT', 'DELETE'])
def api_employee_detail(employee_id_custom):
    if request.method == 'PUT':
        item = data_manager.update_employee(employee_id_custom, request.get_json())
        return jsonify(item) if item else (jsonify({'error': 'Not found or update failed'}), 404)
    elif request.method == 'DELETE':
        item = data_manager.delete_employee(employee_id_custom)
        return jsonify(item) if item else (jsonify({'error': 'Not found or delete failed'}), 404)
    
# Orders
# In main_erp_vue_final.py

@app.route('/api/orders', methods=['GET', 'POST'])
def api_orders():
    if request.method == 'GET':
        orders_df = data_manager.sales_orders
        if orders_df.empty:
            return jsonify([])
        # Replace pandas NaN with Python's None for valid JSON
        records_df = orders_df.where(pd.notnull(orders_df), None)
        records = records_df.to_dict('records')
        return jsonify(records)
        
    elif request.method == 'POST':
        item = data_manager.add_order(request.get_json())
        return jsonify(item), 201 if item else (jsonify({"error": "Missing required fields"}), 400)
    
@app.route('/api/orders/<order_id>', methods=['PUT', 'DELETE'])
def api_order_detail(order_id):
    if request.method == 'PUT':
        item = data_manager.update_order(order_id, request.get_json())
        return jsonify(item) if item else (jsonify({'error': 'Not found or update failed'}), 404)
    elif request.method == 'DELETE':
        item = data_manager.delete_order(order_id)
        return jsonify(item) if item else (jsonify({'error': 'Not found or delete failed'}), 404)

# Invoices
# In main_erp_vue_final.py

@app.route('/api/invoices', methods=['GET', 'POST'])
def api_invoices():
    if request.method == 'GET':
        invoices_df = data_manager.invoices
        if invoices_df.empty:
            return jsonify([])
        # Replace pandas NaN with Python's None for valid JSON
        records_df = invoices_df.where(pd.notnull(invoices_df), None)
        records = records_df.to_dict('records')
        return jsonify(records)
        
    elif request.method == 'POST':
        new_invoice = data_manager.add_invoice(request.get_json())
        return jsonify(new_invoice), 201
    
@app.route('/api/invoices/<invoice_id>', methods=['PUT', 'DELETE'])
def api_invoice_detail(invoice_id):
    if request.method == 'PUT':
        item = data_manager.update_invoice(invoice_id, request.get_json())
        return jsonify(item) if item else (jsonify({'error': 'Not found or update failed'}), 404)
    elif request.method == 'DELETE':
        item = data_manager.delete_invoice(invoice_id)
        return jsonify(item) if item else (jsonify({'error': 'Not found or delete failed'}), 404)

# UI Command API
@app.route('/api/ui_command', methods=['POST'])
def api_ui_command():
    instruction = request.get_json()
    if not instruction or 'action' not in instruction: return jsonify({'error': 'Invalid payload'}), 400
    data_manager.broadcast_ui_instruction(instruction)
    return jsonify({'message': 'UI instruction sent', 'instruction': instruction}), 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)