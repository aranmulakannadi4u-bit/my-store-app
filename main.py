import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="AK Store Manager", layout="wide")

# --- INITIALIZE DATABASE (Session State) ---
if 'suppliers' not in st.session_state: st.session_state.suppliers = []
if 'customers' not in st.session_state: st.session_state.customers = []
if 'inventory' not in st.session_state: st.session_state.inventory = []
if 'purchases' not in st.session_state: st.session_state.purchases = []
if 'bill_items' not in st.session_state: st.session_state.bill_items = []

# --- APP HEADER ---
st.title("AK Store Management System")
st.markdown("---")

# MAIN HEADS AS TABS
tab_profile, tab_supp, tab_cust, tab_purch, tab_sale, tab_enq = st.tabs([
    "🏪 Store Profile", "🤝 Suppliers", "👥 Customers", "🛒 Purchase Entry", "🧾 Sale Panel", "📱 Enquiry"
])

# --- 1. STORE PROFILE TAB ---
with tab_profile:
    st.header("Store Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state['store_name'] = st.text_input("Name of the Store", "AK Store")
        st.session_state['store_addr'] = st.text_area("Address", "Main Road, City")
        st.session_state['store_cont'] = st.text_input("Contact Number")
    with col2:
        st.session_state['store_font'] = st.selectbox("Selection Font", ["Arial", "Courier", "Times"])
        uploaded_logo = st.file_uploader("Upload Store Logo", type=['png', 'jpg', 'jpeg'])
        if uploaded_logo: st.session_state['logo_data'] = uploaded_logo

# --- 2. SUPPLIERS TAB (All Fields Restored) ---
with tab_supp:
    st.header("Supplier Management")
    with st.form("supp_form", clear_on_submit=True):
        col_s1, col_s2 = st.columns(2)
        s_store = col_s1.text_input("Store Name*")
        s_name = col_s1.text_input("Supplier Name")
        s_c1 = col_s1.text_input("Contact 1")
        s_c2 = col_s1.text_input("Contact 2")
        s_addr = col_s2.text_area("Address")
        s_bank = col_s2.text_input("Bank Details")
        s_upi = col_s2.text_input("UPI ID")
        
        if st.form_submit_button("Save Supplier"):
            if s_store:
                st.session_state.suppliers.append({
                    "Store": s_store, "Name": s_name, "C1": s_c1, "C2": s_c2, 
                    "Addr": s_addr, "Bank": s_bank, "UPI": s_upi
                })
                st.success(f"Supplier {s_store} Added!")

    if st.session_state.suppliers:
        df_s = pd.DataFrame(st.session_state.suppliers)
        st.subheader("Supplier List (Edit/Delete)")
        st.dataframe(df_s)
        if st.button("Delete All Suppliers"):
            st.session_state.suppliers = []
            st.rerun()

# --- 3. CUSTOMER TAB ---
with tab_cust:
    st.header("Customer Details")
    with st.form("cust_form", clear_on_submit=True):
        c_name = st.text_input("Customer Name*")
        c_a1 = st.text_input("Address Line 1")
        c_a2 = st.text_input("Address Line 2")
        c_place = st.text_input("Place")
        c_phone = st.text_input("Contact Number")
        if st.form_submit_button("Save Customer"):
            st.session_state.customers.append({"Name": c_name, "A1": c_a1, "A2": c_a2, "Place": c_place, "Phone": c_phone})
            st.success("Customer Saved")

# --- 4. PURCHASE TAB (All Fields Restored) ---
with tab_purch:
    st.header("Purchase Entry & Inventory")
    if not st.session_state.suppliers:
        st.warning("Add a Supplier first!")
    else:
        with st.form("pur_form", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            p_store = col_p1.selectbox("Select Purchase Store", [s['Store'] for s in st.session_state.suppliers])
            p_code = col_p1.text_input("Product Code*")
            p_name = col_p1.text_input("Product Name*")
            p_price = col_p1.number_input("Product Purchase Price (₹)", min_value=0.0)
            p_margin = col_p2.number_input("Product Margin Price to Sell (₹)", min_value=0.0)
            p_disc = col_p2.number_input("Product Discount Price (₹)", min_value=0.0)
            p_qty = col_p2.number_input("Quantity of Purchase", min_value=1)
            p_date = col_p2.date_input("Date of Purchase")
            p_paid = col_p2.number_input("Amount Paid (₹)", min_value=0.0)
            
            total_pay = p_qty * p_price
            balance = total_pay - p_paid
            
            if st.form_submit_button("Add Purchase"):
                purchase_entry = {
                    "Code": p_code, "Name": p_name, "S_Price": p_margin, "Disc": p_disc,
                    "Qty": p_qty, "Total": total_pay, "Paid": p_paid, "Balance": balance, "Store": p_store
                }
                st.session_state.purchases.append(purchase_entry)
                # Update Inventory for Sale Panel
                st.session_state.inventory.append(purchase_entry)
                st.success(f"Added! Balance to Pay: ₹{balance}")

# --- 5. SALE PANEL (Multiple Products + Professional Invoice) ---
with tab_sale:
    # Header Layout
    col_l, col_r = st.columns([1, 4])
    with col_l:
        if 'logo_data' in st.session_state: st.image(st.session_state['logo_data'], width=100)
    with col_r:
        st.markdown(f"<h2 style='text-align: center;'>{st.session_state.get('store_name', 'AK STORE')}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>{st.session_state.get('store_addr', '')}<br>Contact: {st.session_state.get('store_cont', '')}</p>", unsafe_allow_html=True)

    st.divider()
    
    # Bill & Customer Info
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        if st.session_state.customers:
            sel_c = st.selectbox("Select Customer (To Address)", [c['Name'] for c in st.session_state.customers])
            cust_data = [c for c in st.session_state.customers if c['Name'] == sel_c][0]
            st.write(f"**TO:** {cust_data['Name']}\n{cust_data['A1']}, {cust_data['A2']}, {cust_data['Place']}")
        else: st.warning("Add Customers first!")
    
    with c_col2:
        bill_no = st.text_input("Bill Number", f"AK/01/{datetime.now().year}")
        sale_date = st.date_input("Date", datetime.now())

    # Add Products Row-wise
    st.subheader("Add Products to Bill")
    if not st.session_state.inventory:
        st.info("No stock in inventory. Add via Purchase tab.")
    else:
        col_i1, col_i2, col_i3, col_i4 = st.columns([2, 1, 1, 1])
        item_code = col_i1.selectbox("Select Product Code", [i['Code'] for i in st.session_state.inventory])
        item_data = [i for i in st.session_state.inventory if i['Code'] == item_code][0]
        
        col_i1.write(f"Product: **{item_data['Name']}**")
        s_price = col_i2.number_input("Price (₹)", value=item_data['S_Price'])
        s_qty = col_i3.number_input("Qty", min_value=1)
        s_disc = col_i4.number_input("Disc (₹)", value=item_data['Disc'])
        
        if st.button("➕ Add Product to Row"):
            total_item = (s_price - s_disc) * s_qty
            st.session_state.bill_items.append({
                "SN": len(st.session_state.bill_items)+1,
                "Code": item_code,
                "Name": item_data['Name'],
                "Price": s_price,
                "Disc": s_disc,
                "Qty": s_qty,
                "Total": total_item
            })

    # Display Table & Totals
    if st.session_state.bill_items:
        df_bill = pd.DataFrame(st.session_state.bill_items)
        st.table(df_bill)
        
        grand_total = df_bill['Total'].sum()
        total_before = (df_bill['Price'] * df_bill['Qty']).sum()
        
        st.write(f"**Total Before Discount:** ₹{total_before}")
        st.write(f"### **Final Price: ₹{grand_total}**")
        words = num2words(grand_total, lang='en_IN').capitalize()
        st.write(f"**Final Price in Words:** {words} Rupees Only")
        st.write(f"**Proprietor:** Suraj.M")

        # PDF GENERATION
        if st.button("💾 Save Bill as PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, st.session_state['store_name'], ln=True, align='C')
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, st.session_state['store_addr'], align='C')
            pdf.ln(10)
            
            # To Address
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 5, f"TO: {cust_data['Name']}", ln=False)
            pdf.cell(0, 5, f"Bill No: {bill_no}", ln=True, align='R')
            pdf.set_font("Arial", size=10)
            pdf.cell(100, 5, f"{cust_data['A1']}, {cust_data['Place']}", ln=False)
            pdf.cell(0, 5, f"Date: {sale_date}", ln=True, align='R')
            pdf.ln(
