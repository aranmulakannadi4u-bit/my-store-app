import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import urllib.parse

# Page Config
st.set_page_config(page_title="AK Store Manager", layout="wide")

# --- App Header ---
st.title("AK Store Management System")

# Create Tabs
tab_profile, tab_supp, tab_cust, tab_purch, tab_sale, tab_enq, tab_rep = st.tabs([
    "Store Profile", "Suppliers", "Customers", "Purchase", "Sale Panel", "Enquiry", "Reports"
])

# --- 1. Store Profile ---
with tab_profile:
    st.header("Store Details")
    store_name = st.text_input("Name of the Store", "AK General Store")
    font_choice = st.selectbox("Select Invoice Font", ["Arial", "Courier", "Times"])
    address = st.text_area("Address", "Line 1, City, State")
    contact = st.text_input("Contact Number")
    logo = st.file_uploader("Upload Store Logo", type=['png', 'jpg'])
    if st.button("Save Profile"):
        st.success("Profile Updated!")

# --- 2. Suppliers ---
with tab_supp:
    st.header("Supplier Details")
    col1, col2 = st.columns(2)
    with col1:
        s_store = st.text_input("Supplier Store Name")
        s_name = st.text_input("Supplier Person Name")
        s_c1 = st.text_input("Contact 1")
    with col2:
        s_bank = st.text_input("Bank Details (A/c, IFSC)")
        s_upi = st.text_input("UPI ID")
    if st.button("Add Supplier"):
        st.info("Supplier Saved to Database")

# --- 3. Sale Panel (The Main Part) ---
with tab_sale:
    st.subheader("Invoice Generation")
    
    # Bill Branding
    c1, c2 = st.columns([1, 4])
    with c1: st.write("LOGO HERE")
    with c2: st.markdown(f"### {store_name}\n{address}")

    col_a, col_b = st.columns(2)
    bill_no = col_a.text_input("Bill Number", f"AK/{datetime.now().strftime('%H%M')}/2026")
    sale_date = col_b.date_input("Sale Date")

    # Product Row
    st.divider()
    p_code = st.text_input("Select Product Code")
    # Mock data for demo
    p_name = "Sample Product"
    p_price = 1200.00
    p_disc = 200.00
    final = p_price - p_disc

    st.write(f"**Product:** {p_name} | **Price:** ₹{p_price} | **Discount:** ₹{p_disc}")
    st.write(f"### Total to Pay: ₹{final}")
    
    # Generate Invoice PDF
    if st.button("Download PDF Bill"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=store_name, ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=address, ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Invoice No: {bill_no}", ln=True)
        pdf.cell(200, 10, txt=f"Total Amount: Rs. {final}", ln=True)
        pdf.cell(200, 10, txt=f"In Words: {num2words(final, lang='en_IN')} Only", ln=True)
        pdf.ln(20)
        pdf.cell(200, 10, txt="Proprietor: Suraj.M", ln=True, align='R')
        
        pdf.output("invoice.pdf")
        with open("invoice.pdf", "rb") as f:
            st.download_button("Click here to Download", f, "AK_Bill.pdf")

# --- 4. Customer Enquiry ---
with tab_enq:
    st.header("Send Price via WhatsApp")
    enq_p = st.selectbox("Select Product", ["Product A", "Product B"])
    enq_price = 1500
    enq_phone = st.text_input("Customer WhatsApp Number (with country code)")
    
    msg = f"Hello! Price for {enq_p} is ₹{enq_price}. Best Regards, {store_name}"
    encoded_msg = urllib.parse.quote(msg)
    wa_url = f"https://wa.me/{enq_phone}?text={encoded_msg}"
    
    if st.button("Share on WhatsApp"):
        st.markdown(f'<a href="{wa_url}" target="_blank">Open WhatsApp Chat</a>', unsafe_allow_html=True)

# Note: In a real app, we would connect this to a Database (SQLite).
