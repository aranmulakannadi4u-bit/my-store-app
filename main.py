import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="AK Store Manager", layout="wide")

# --- DATABASE SIMULATION ---
if 'suppliers' not in st.session_state: st.session_state.suppliers = []
if 'customers' not in st.session_state: st.session_state.customers = []
if 'purchases' not in st.session_state: st.session_state.purchases = []
if 'current_bill_items' not in st.session_state: st.session_state.current_bill_items = []

# --- APP HEADER ---
st.title("AK Store Management System")
st.markdown("---")

# Create Tabs
tab_profile, tab_supp, tab_cust, tab_purch, tab_sale, tab_enq = st.tabs([
    "Store Profile", "Suppliers", "Customers", "Purchase", "Sale Panel", "Enquiry"
])

# --- 1. STORE PROFILE ---
with tab_profile:
    st.header("Store Details")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state['store_name'] = st.text_input("Name of the Store", "AK Store")
        st.session_state['store_address'] = st.text_area("Store Address", "Shop No 1, Main Road, City")
        st.session_state['store_contact'] = st.text_input("Store Contact Number", "91XXXXXXXX")
    with col2:
        uploaded_logo = st.file_uploader("Upload Store Logo", type=['png', 'jpg', 'jpeg'])
        if uploaded_logo: st.session_state['logo_data'] = uploaded_logo

# --- 2. SUPPLIERS & 3. CUSTOMERS (Simplified for brevity) ---
with tab_supp:
    st.header("Add Supplier")
    s_store = st.text_input("Supplier Store Name")
    if st.button("Save Supplier"):
        st.session_state.suppliers.append(s_store)
        st.success("Saved")

with tab_cust:
    st.header("Add Customer")
    with st.form("c_form"):
        c_name = st.text_input("Customer Name")
        c_a1 = st.text_input("Address Line 1")
        c_a2 = st.text_input("Address Line 2")
        c_place = st.text_input("Place")
        c_phone = st.text_input("Contact")
        if st.form_submit_button("Save Customer"):
            st.session_state.customers.append({"Name": c_name, "Addr1": c_a1, "Addr2": c_a2, "Place": c_place, "Phone": c_phone})
            st.success("Customer Added")

# --- 4. PURCHASE ---
with tab_purch:
    st.header("Purchase Entry")
    with st.form("p_form"):
        p_code = st.text_input("Product Code")
        p_name = st.text_input("Product Name")
        p_m_price = st.number_input("Selling Price (Margin Price)", min_value=0.0)
        if st.form_submit_button("Save Product"):
            st.session_state.purchases.append({"Code": p_code, "Name": p_name, "Price": p_m_price})
            st.success("Product Saved to Inventory")

# --- 5. SALE PANEL (PROFESSIONAL MULTI-PRODUCT) ---
with tab_sale:
    # --- INVOICE HEADER VIEW ---
    col_l, col_r = st.columns([1, 3])
    with col_l:
        if 'logo_data' in st.session_state: st.image(st.session_state['logo_data'], width=100)
    with col_r:
        st.subheader(st.session_state.get('store_name', 'AK Store'))
        st.write(st.session_state.get('store_address', ''))

    st.divider()

    # Customer & Bill Info
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.customers:
            cust_list = {c['Name']: c for c in st.session_state.customers}
            sel_c = st.selectbox("Select Customer (To Address)", options=list(cust_list.keys()))
            customer = cust_list[sel_c]
            st.info(f"**TO:** {customer['Name']}, {customer['Addr1']}, {customer['Place']}")
        else:
            st.warning("Add a customer first!")
    
    with c2:
        bill_no = st.text_input("Bill Number", f"AK/{len(st.session_state.get('sales_history', []))+1:02d}/{datetime.now().year}")
        bill_date = st.date_input("Bill Date", datetime.now())

    st.divider()

    # --- PRODUCT SELECTION AREA ---
    st.subheader("Add Products to Bill")
    if st.session_state.purchases:
        prod_list = {p['Code']: p for p in st.session_state.purchases}
        col_p1, col_p2, col_p3, col_p4 = st.columns([2,1,1,1])
        
        with col_p1:
            sel_p_code = st.selectbox("Select Product", options=list(prod_list.keys()))
            sel_p_name = prod_list[sel_p_code]['Name']
            st.caption(f"Name: {sel_p_name}")
        
        with col_p2:
            u_price = st.number_input("Price (₹)", value=prod_list[sel_p_code]['Price'])
        
        with col_p3:
            u_qty = st.number_input("Quantity", min_value=1, step=1)
        
        with col_p4:
            u_disc = st.number_input("Discount per Unit (₹)", min_value=0.0)

        if st.button("➕ Add Item to Bill"):
            total_item = (u_price - u_disc) * u_qty
            st.session_state.current_bill_items.append({
                "SN": len(st.session_state.current_bill_items) + 1,
                "Code": sel_p_code,
                "Name": sel_p_name,
                "Price": u_price,
                "Discount": u_disc,
                "Qty": u_qty,
                "Total": total_item
            })
    
    # --- BILL TABLE VIEW ---
    if st.session_state.current_bill_items:
        df_bill = pd.DataFrame(st.session_state.current_bill_items)
        st.table(df_bill)

        # Totals Calculation
        grand_total = df_bill['Total'].sum()
        total_before_disc = (df_bill['Price'] * df_bill['Qty']).sum()
        
        c_t1, c_t2 = st.columns(2)
        with c_t2:
            st.write(f"**Total Before Discount:** ₹{total_before_disc}")
            st.markdown(f"## **Final Price: ₹{grand_total}**")
            words = num2words(grand_total, lang='en_IN').capitalize()
            st.write(f"*In Words: {words} Rupees Only*")
        
        with c_t1:
            st.write("")
            st.write("")
            st.write(f"**Proprietor:** Suraj.M")
            if st.button("🗑️ Clear Bill"):
                st.session_state.current_bill_items = []
                st.rerun()

        # --- GENERATE PDF ---
        if st.button("📄 Save & Download Invoice (PDF)"):
            pdf = FPDF()
            pdf.add_page()
            
            # Professional Header
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, st.session_state['store_name'], ln=True, align='C')
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 5, st.session_state['store_address'], ln=True, align='C')
            pdf.ln(10)
            
            # Customer Details
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 5, "TO (CUSTOMER):", ln=False)
            pdf.cell(0, 5, f"BILL NO: {bill_no}", ln=True, align='R')
            pdf.set_font("Arial", size=10)
            pdf.cell(100, 5, customer['Name'], ln=False)
            pdf.cell(0, 5, f"DATE: {bill_date}", ln=True, align='R')
            pdf.cell(100, 5, f"{customer['Addr1']}, {customer['Place']}", ln=True)
            pdf.cell(100, 5, f"Contact: {customer['Phone']}", ln=True)
            pdf.ln(5)
            
            # Table Header
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(10, 8, "SN", 1, 0, 'C', True)
            pdf.cell(80, 8, "Product Description", 1, 0, 'L', True)
            pdf.cell(25, 8, "Price", 1, 0, 'C', True)
            pdf.cell(20, 8, "Qty", 1, 0, 'C', True)
            pdf.cell(20, 8, "Disc", 1, 0, 'C', True)
            pdf.cell(35, 8, "Total", 1, 1, 'C', True)
            
            # Table Body
            pdf.set_font("Arial", size=9)
            for item in st.session_state.current_bill_items:
                pdf.cell(10, 8, str(item['SN']), 1, 0, 'C')
                pdf.cell(80, 8, item['Name'], 1, 0, 'L')
                pdf.cell(25, 8, str(item['Price']), 1, 0, 'C')
                pdf.cell(20, 8, str(item['Qty']), 1, 0, 'C')
                pdf.cell(20, 8, str(item['Discount']), 1, 0, 'C')
                pdf.cell(35, 8, str(item['Total']), 1, 1, 'C')
            
            # Footer
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(155, 8, "Grand Total:", 0, 0, 'R')
            pdf.cell(35, 8, f"Rs. {grand_total}", 1, 1, 'C')
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(0, 10, f"Amount in words: {words} Rupees Only", ln=True)
            
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 10, "For " + st.session_state['store_name'], ln=True, align='R')
            pdf.ln(5)
            pdf.cell(0, 10, "Authorized Signatory (Suraj.M)", ln=True, align='R')

            file_name = f"Bill_{bill_no.replace('/', '_')}.pdf"
            pdf.output(file_name)
            with open(file_name, "rb") as f:
                st.download_button("Click to Download PDF", f, file_name=file_name)

# --- 6. ENQUIRY ---
with tab_enq:
    st.header("WhatsApp Sharing")
    if st.session_state.purchases:
        e_p = st.selectbox("Product for Enquiry", [p['Name'] for p in st.session_state.purchases])
        e_ph = st.text_input("WhatsApp Number")
        if st.button("Share"):
            msg = f"Check out {e_p} at {st.session_state['store_name']}!"
            st.markdown(f"[Send WhatsApp](https://wa.me/{e_ph}?text={urllib.parse.quote(msg)})")
