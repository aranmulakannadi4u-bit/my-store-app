import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import urllib.parse
from PIL import Image
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="AK Store Manager", layout="wide")

# --- INITIALIZE DATABASE (Session State) ---
if 'suppliers' not in st.session_state: st.session_state.suppliers = []
if 'customers' not in st.session_state: st.session_state.customers = []
if 'purchases' not in st.session_state: st.session_state.purchases = []
if 'bill_items' not in st.session_state: st.session_state.bill_items = []
if 'edit_index' not in st.session_state: st.session_state.edit_index = -1

# --- APP HEADER ---
st.title("AK Store Management System")
st.markdown("---")

tab_profile, tab_supp, tab_cust, tab_purch, tab_sale, tab_enq = st.tabs([
    "🏪 Store Profile", "🤝 Suppliers", "👥 Customers", "🛒 Purchase Entry", "🧾 Sale Panel", "📱 Enquiry"
])

# --- 1. STORE PROFILE ---
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

# --- 2. SUPPLIERS ---
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
                st.session_state.suppliers.append({"Store": s_store, "Name": s_name, "C1": s_c1, "C2": s_c2, "Addr": s_addr, "Bank": s_bank, "UPI": s_upi})
                st.success("Supplier Added!")

# --- 3. CUSTOMERS ---
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

# --- 4. PURCHASE ENTRY & HISTORY ---
with tab_purch:
    st.header("Purchase Entry & Inventory")
    
    # Logic for Editing
    edit_idx = st.session_state.edit_index
    edit_data = st.session_state.purchases[edit_idx] if edit_idx != -1 else None

    if not st.session_state.suppliers:
        st.warning("Please add a Supplier first!")
    else:
        # PURCHASE FORM
        with st.expander("➕ Click to Add / Edit Purchase Entry", expanded=(edit_idx != -1)):
            with st.form("pur_form", clear_on_submit=(edit_idx == -1)):
                col_p1, col_p2 = st.columns(2)
                p_store = col_p1.selectbox("Select Purchase Store", [s['Store'] for s in st.session_state.suppliers], 
                                           index=0 if not edit_data else [s['Store'] for s in st.session_state.suppliers].index(edit_data['Store']))
                p_code = col_p1.text_input("Product Code*", value="" if not edit_data else edit_data['Code'])
                p_name = col_p1.text_input("Product Name*", value="" if not edit_data else edit_data['Name'])
                p_photo = col_p1.file_uploader("Upload Product Photo", type=['jpg', 'png', 'jpeg'])
                
                p_price = col_p2.number_input("Purchase Price (₹)", min_value=0.0, value=0.0 if not edit_data else edit_data['P_Price'])
                p_margin = col_p2.number_input("Margin Price to Sell (₹)", min_value=0.0, value=0.0 if not edit_data else edit_data['S_Price'])
                p_disc = col_p2.number_input("Discount Price (₹)", min_value=0.0, value=0.0 if not edit_data else edit_data['Disc'])
                p_qty = col_p2.number_input("Quantity", min_value=1, value=1 if not edit_data else edit_data['Qty'])
                p_paid = col_p2.number_input("Amount Paid (₹)", min_value=0.0, value=0.0 if not edit_data else edit_data['Paid'])
                p_date = col_p2.date_input("Date", datetime.now() if not edit_data else edit_data['Date'])
                
                submit_text = "Update Entry" if edit_idx != -1 else "Add Purchase"
                if st.form_submit_button(submit_text):
                    total_val = p_qty * p_price
                    new_entry = {
                        "Code": p_code, "Name": p_name, "Store": p_store, "P_Price": p_price,
                        "S_Price": p_margin, "Disc": p_disc, "Qty": p_qty, "Date": p_date,
                        "Paid": p_paid, "Balance": total_val - p_paid, "Photo": p_photo
                    }
                    if edit_idx == -1:
                        st.session_state.purchases.append(new_entry)
                        st.success("Entry Added!")
                    else:
                        st.session_state.purchases[edit_idx] = new_entry
                        st.session_state.edit_index = -1 # Reset to Add mode
                        st.success("Entry Updated!")
                        st.rerun()

    # PURCHASE HISTORY TABLE
    st.markdown("---")
    st.subheader("📦 Purchase History & Inventory")
    if st.session_state.purchases:
        for i, item in enumerate(st.session_state.purchases):
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1, 1])
                # Show Image
                if item['Photo']:
                    c1.image(item['Photo'], width=60)
                else:
                    c1.write("No Image")
                
                c2.write(f"**{item['Name']}** ({item['Code']})\nStore: {item['Store']}")
                c3.write(f"Qty: {item['Qty']} | Bal: ₹{item['Balance']}\nDate: {item['Date']}")
                
                # Edit/Delete Buttons
                if c4.button("📝 Edit", key=f"edit_{i}"):
                    st.session_state.edit_index = i
                    st.rerun()
                if c5.button("🗑️ Delete", key=f"del_{i}"):
                    st.session_state.purchases.pop(i)
                    st.rerun()
                st.divider()

# --- 5. SALE PANEL ---
with tab_sale:
    # Header
    col_l, col_r = st.columns([1, 4])
    with col_l:
        if 'logo_data' in st.session_state: st.image(st.session_state['logo_data'], width=100)
    with col_r:
        st.markdown(f"<h2 style='text-align: center;'>{st.session_state.get('store_name', 'AK STORE')}</h2>", unsafe_allow_html=True)
    
    st.divider()

    # Selection
    if st.session_state.customers and st.session_state.purchases:
        sel_c = st.selectbox("Customer", [c['Name'] for c in st.session_state.customers])
        cust = [c for c in st.session_state.customers if c['Name'] == sel_c][0]
        
        st.subheader("Add Products")
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        item_code = col_s1.selectbox("Product Code", [p['Code'] for p in st.session_state.purchases])
        item_data = [p for p in st.session_state.purchases if p['Code'] == item_code][0]
        
        s_qty = col_s2.number_input("Qty to Sell", min_value=1)
        if col_s3.button("➕ Add Row"):
            st.session_state.bill_items.append({
                "SN": len(st.session_state.bill_items)+1,
                "Name": item_data['Name'], "Price": item_data['S_Price'], 
                "Qty": s_qty, "Total": item_data['S_Price'] * s_qty
            })
        
        if st.session_state.bill_items:
            st.table(pd.DataFrame(st.session_state.bill_items))
            if st.button("🗑️ Clear Bill"):
                st.session_state.bill_items = []
                st.rerun()
    else:
        st.info("Please ensure you have added Customers and Purchases first.")

# --- 6. ENQUIRY ---
with tab_enq:
    st.header("Enquiry Sharing")
    if st.session_state.purchases:
        e_p = st.selectbox("Select Product for Enquiry", [p['Code'] for p in st.session_state.purchases])
        e_data = [p for p in st.session_state.purchases if p['Code'] == e_p][0]
        if e_data['Photo']: st.image(e_data['Photo'], width=150)
        st.write(f"Price: ₹{e_data['S_Price']}")
        e_ph = st.text_input("WhatsApp No")
        if st.button("Share"):
            msg = f"Check out {e_data['Name']} at ₹{e_data['S_Price']}!"
            st.markdown(f"[Send WhatsApp](https://wa.me/{e_ph}?text={urllib.parse.quote(msg)})")
