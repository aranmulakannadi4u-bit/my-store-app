import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="AK Store Manager", layout="wide")

# --- DATABASE SIMULATION (Session State) ---
# This keeps data active while the browser is open
if 'suppliers' not in st.session_state:
    st.session_state.suppliers = []
if 'purchases' not in st.session_state:
    st.session_state.purchases = []
if 'inventory' not in st.session_state:
    st.session_state.inventory = []

# --- APP HEADER ---
st.title("AK Store Management System")
st.markdown("---")

# Create Tabs
tab_profile, tab_supp, tab_purch, tab_sale, tab_enq = st.tabs([
    "Store Profile", "Manage Suppliers", "Purchase / Inventory", "Sale Panel", "Enquiry"
])

# --- 1. STORE PROFILE ---
with tab_profile:
    st.header("Store Details")
    col1, col2 = st.columns(2)
    with col1:
        store_name = st.text_input("Name of the Store", "AK Store")
        store_font = st.selectbox("Select Invoice Font", ["Arial", "Courier", "Times", "Helvetica"])
        store_address = st.text_area("Address", "Shop No 1, Main Road, City")
    with col2:
        store_contact = st.text_input("Contact Number", "91XXXXXXXX")
        store_logo = st.file_uploader("Upload Store Logo", type=['png', 'jpg'])
    
    if st.button("Save Store Settings"):
        st.success("Store Profile Updated Successfully!")

# --- 2. MANAGE SUPPLIERS ---
with tab_supp:
    st.header("Add New Supplier")
    with st.form("supplier_form", clear_on_submit=True):
        s_store_name = st.text_input("Supplier Store Name")
        s_person = st.text_input("Supplier Name")
        c1, c2 = st.columns(2)
        s_contact1 = c1.text_input("Contact 1")
        s_contact2 = c2.text_input("Contact 2")
        s_bank = st.text_input("Bank Account Details")
        s_upi = st.text_input("UPI ID")
        
        if st.form_submit_button("Save Supplier"):
            if s_store_name:
                st.session_state.suppliers.append(s_store_name)
                st.success(f"Supplier '{s_store_name}' added!")
            else:
                st.error("Please enter Supplier Store Name")

    st.subheader("Existing Suppliers")
    st.write(st.session_state.suppliers)

# --- 3. PURCHASE TAB (NOW WORKING) ---
with tab_purch:
    st.header("New Purchase Entry")
    
    # Selection of Supplier from the list created in Tab 2
    if not st.session_state.suppliers:
        st.warning("Please add a Supplier in the 'Manage Suppliers' tab first!")
    else:
        with st.form("purchase_form"):
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                selected_supp = st.selectbox("Select Supplier", st.session_state.suppliers)
                p_code = st.text_input("Product Code (SKU)")
                p_name = st.text_input("Product Name")
                p_date = st.date_input("Date of Purchase", datetime.now())
            
            with col_p2:
                p_qty = st.number_input("Quantity of Purchase", min_value=1, step=1)
                p_cost = st.number_input("Unit Purchase Price (₹)", min_value=0.0)
                p_paid = st.number_input("Amount Paid to Supplier (₹)", min_value=0.0)
            
            # Calculations
            total_amount = p_qty * p_cost
            balance_due = total_amount - p_paid
            
            st.markdown(f"### Total Amount: ₹{total_amount}")
            st.markdown(f"### Balance to Pay: :red[₹{balance_due}]")
            
            if st.form_submit_button("Add to Inventory & Save"):
                # Save data to session state
                purchase_data = {
                    "Date": p_date,
                    "Code": p_code,
                    "Product": p_name,
                    "Supplier": selected_supp,
                    "Qty": p_qty,
                    "Total": total_amount,
                    "Paid": p_paid,
                    "Balance": balance_due
                }
                st.session_state.purchases.append(purchase_data)
                st.success("Purchase recorded and inventory updated!")

    # Show History
    if st.session_state.purchases:
        st.subheader("Purchase History")
        df_purch = pd.DataFrame(st.session_state.purchases)
        st.dataframe(df_purch, use_container_width=True)

# --- 4. SALE PANEL ---
with tab_sale:
    st.header("Invoice Generation")
    
    # Bill Format: AK/Serial/Year
    bill_year = datetime.now().year
    bill_no = st.text_input("Bill Number", f"AK/01/{bill_year}")
    
    # Standard Invoice Layout
    st.markdown(f"<h2 style='text-align: center;'>{store_name}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>{store_address}<br>Contact: {store_contact}</p>", unsafe_allow_html=True)
    
    sale_col1, sale_col2 = st.columns(2)
    p_to_sell = sale_col1.selectbox("Select Product Code", [p['Code'] for p in st.session_state.purchases] if st.session_state.purchases else ["No Stock"])
    sale_qty = sale_col2.number_input("Sale Quantity", min_value=1)
    
    # Example Price Logic
    unit_price = 1500.0
    discount = 100.0
    final_total = (unit_price - discount) * sale_qty
    
    st.divider()
    st.write(f"**Proprietor:** Suraj.M")
    st.write(f"**Final Price:** ₹{final_total}")
    
    # PDF Generator
    if st.button("Download Invoice as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font(store_font, 'B', 16)
        pdf.cell(200, 10, txt=store_name, ln=True, align='C')
        pdf.set_font(store_font, size=10)
        pdf.multi_cell(0, 5, txt=store_address, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Bill No: {bill_no} | Date: {datetime.now().date()}", ln=True)
        pdf.line(10, 50, 200, 50)
        pdf.ln(10)
        pdf.cell(100, 10, txt=f"Product Code: {p_to_sell}")
        pdf.cell(100, 10, txt=f"Total: Rs. {final_total}", ln=True)
        pdf.ln(10)
        word_price = num2words(final_total, lang='en_IN').capitalize()
        pdf.cell(200, 10, txt=f"Amount in Words: {word_price} Rupees Only", ln=True)
        pdf.ln(20)
        pdf.cell(200, 10, txt="Signature: Suraj.M", ln=True, align='R')
        
        pdf_name = f"Bill_{bill_no.replace('/', '_')}.pdf"
        pdf.output(pdf_name)
        with open(pdf_name, "rb") as f:
            st.download_button("Download PDF Now", f, file_name=pdf_name)

# --- 5. ENQUIRY TAB (WhatsApp) ---
with tab_enq:
    st.header("Customer WhatsApp Enquiry")
    enq_product = st.text_input("Product Name for Enquiry")
    enq_price = st.number_input("Quote Price (₹)")
    enq_phone = st.text_input("Customer Phone (with country code, e.g., 919999...)")
    
    if st.button("Share on WhatsApp"):
        msg = f"Hello! Details for {enq_product}: Price is ₹{enq_price}. Regards, {store_name}."
        encoded_msg = urllib.parse.quote(msg)
        st.markdown(f"[Click to Open WhatsApp Chat](https://wa.me/{enq_phone}?text={encoded_msg})")
