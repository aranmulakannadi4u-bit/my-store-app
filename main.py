import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import urllib.parse
from PIL import Image

# --- PAGE CONFIG ---
st.set_page_config(page_title="AK Store Manager", layout="wide")

# --- DATABASE SIMULATION ---
if 'suppliers' not in st.session_state:
    st.session_state.suppliers = []
if 'customers' not in st.session_state:
    st.session_state.customers = []
if 'purchases' not in st.session_state:
    st.session_state.purchases = []

# --- APP HEADER ---
st.title("AK Store Management System")
st.markdown("---")

# Create Tabs
tab_profile, tab_supp, tab_cust, tab_purch, tab_sale, tab_enq = st.tabs([
    "Store Profile", "Suppliers", "Customers", "Purchase", "Sale Panel", "Enquiry"
])

# --- 1. STORE PROFILE (Logo & Details) ---
with tab_profile:
    st.header("Store Details")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state['store_name'] = st.text_input("Name of the Store", "AK Store")
        st.session_state['store_address'] = st.text_area("Store Address", "Shop No 1, Main Road, City")
        st.session_state['store_contact'] = st.text_input("Store Contact Number", "91XXXXXXXX")
    with col2:
        st.session_state['store_font'] = st.selectbox("Select Invoice Font", ["Arial", "Courier", "Times"])
        uploaded_logo = st.file_uploader("Upload Store Logo", type=['png', 'jpg', 'jpeg'])
        if uploaded_logo:
            st.session_state['logo_data'] = uploaded_logo
            st.image(uploaded_logo, width=150)

# --- 2. SUPPLIERS ---
with tab_supp:
    st.header("Add New Supplier")
    with st.form("supp_form", clear_on_submit=True):
        s_store = st.text_input("Supplier Store Name*")
        s_name = st.text_input("Supplier Person Name")
        s_c1 = st.text_input("Contact 1")
        s_bank = st.text_input("Bank Details")
        s_upi = st.text_input("UPI ID")
        if st.form_submit_button("Save Supplier"):
            if s_store:
                st.session_state.suppliers.append({"Store": s_store, "Name": s_name, "UPI": s_upi})
                st.success(f"Supplier {s_store} Saved!")

# --- 3. CUSTOMER TAB (NEW) ---
with tab_cust:
    st.header("Customer Management")
    with st.form("cust_form", clear_on_submit=True):
        c_name = st.text_input("Customer Name*")
        c_addr1 = st.text_input("Address Line 1")
        c_addr2 = st.text_input("Address Line 2")
        c_place = st.text_input("Place/City")
        c_phone = st.text_input("Contact Number")
        
        if st.form_submit_button("Save Customer"):
            if c_name and c_phone:
                st.session_state.customers.append({
                    "Name": c_name,
                    "Addr1": c_addr1,
                    "Addr2": c_addr2,
                    "Place": c_place,
                    "Phone": c_phone
                })
                st.success(f"Customer {c_name} Added!")
            else:
                st.error("Name and Contact are required!")
    
    if st.session_state.customers:
        st.subheader("Customer List")
        st.table(pd.DataFrame(st.session_state.customers))

# --- 4. PURCHASE TAB ---
with tab_purch:
    st.header("Purchase Entry")
    if not st.session_state.suppliers:
        st.warning("Please add a Supplier first!")
    else:
        with st.form("pur_form"):
            p_supp = st.selectbox("Select Supplier", [s['Store'] for s in st.session_state.suppliers])
            p_code = st.text_input("Product Code*")
            p_name = st.text_input("Product Name*")
            p_qty = st.number_input("Quantity", min_value=1)
            p_cost = st.number_input("Purchase Price (₹)", min_value=0.0)
            p_paid = st.number_input("Amount Paid (₹)", min_value=0.0)
            p_date = st.date_input("Purchase Date")
            
            total_cost = p_qty * p_cost
            balance = total_cost - p_paid
            
            if st.form_submit_button("Save Purchase"):
                st.session_state.purchases.append({
                    "Code": p_code, "Name": p_name, "Qty": p_qty, "Total": total_cost, "Balance": balance
                })
                st.success(f"Purchase Saved! Balance: ₹{balance}")

# --- 5. SALE PANEL (Logo & To Address Fixed) ---
with tab_sale:
    st.header("Invoice Generation")
    
    # 1. Logo Display (Left Side)
    col_logo, col_shop = st.columns([1, 3])
    with col_logo:
        if 'logo_data' in st.session_state:
            st.image(st.session_state['logo_data'], width=120)
        else:
            st.write("[No Logo]")
    
    with col_shop:
        st.subheader(st.session_state.get('store_name', 'AK Store'))
        st.write(st.session_state.get('store_address', 'Address not set'))

    st.divider()

    # 2. To Address Selection
    if not st.session_state.customers:
        st.warning("Please add a Customer in the 'Customers' tab first!")
    else:
        c_options = {c['Name']: c for c in st.session_state.customers}
        selected_c_name = st.selectbox("Select Customer (To Address)", options=list(c_options.keys()))
        cust = c_options[selected_c_name]
        
        # Displaying the "To Address" on Screen
        st.markdown(f"""
        **TO:**  
        {cust['Name']}  
        {cust['Addr1']}, {cust['Addr2']}  
        {cust['Place']}  
        Contact: {cust['Phone']}
        """)

        # Bill Details
        bill_year = datetime.now().year
        bill_no = st.text_input("Bill Number", f"AK/01/{bill_year}")
        
        # Product Selection (from Purchase)
        if st.session_state.purchases:
            p_options = {p['Code']: p for p in st.session_state.purchases}
            sel_p_code = st.selectbox("Select Product Code", options=list(p_options.keys()))
            sel_p = p_options[sel_p_code]
            
            sale_price = st.number_input("Sale Price (₹)", value=100.0)
            sale_qty = st.number_input("Qty", min_value=1)
            total_bill = sale_price * sale_qty
            
            st.write(f"### Final Price: ₹{total_bill}")
            st.write(f"**Proprietor:** Suraj.M")

            # PDF GENERATION
            if st.button("Generate & Download Bill"):
                pdf = FPDF()
                pdf.add_page()
                
                # Header
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, st.session_state['store_name'], ln=True, align='C')
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 5, st.session_state['store_address'], align='C')
                pdf.ln(5)
                
                # To Address in PDF
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 10, "TO (Customer Details):", ln=True)
                pdf.set_font("Arial", size=10)
                pdf.cell(0, 5, f"Name: {cust['Name']}", ln=True)
                pdf.cell(0, 5, f"Address: {cust['Addr1']}, {cust['Addr2']}", ln=True)
                pdf.cell(0, 5, f"Place: {cust['Place']}", ln=True)
                pdf.cell(0, 5, f"Contact: {cust['Phone']}", ln=True)
                
                pdf.ln(10)
                pdf.cell(0, 10, f"Bill No: {bill_no} | Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                
                # Item Table
                pdf.ln(5)
                pdf.cell(80, 10, "Product Name", 1)
                pdf.cell(30, 10, "Qty", 1)
                pdf.cell(40, 10, "Price", 1)
                pdf.cell(40, 10, "Total", 1, ln=True)
                
                pdf.cell(80, 10, sel_p['Name'], 1)
                pdf.cell(30, 10, str(sale_qty), 1)
                pdf.cell(40, 10, str(sale_price), 1)
                pdf.cell(40, 10, str(total_bill), 1, ln=True)
                
                # Total in Words
                pdf.ln(10)
                words = num2words(total_bill, lang='en_IN').capitalize()
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 10, f"Total Amount: Rs. {total_bill} ({words} Rupees Only)", ln=True)
                
                pdf.ln(20)
                pdf.cell(0, 10, "Proprietor: Suraj.M", ln=True, align='R')
                
                file_name = f"Bill_{bill_no.replace('/','_')}.pdf"
                pdf.output(file_name)
                with open(file_name, "rb") as f:
                    st.download_button("Download PDF", f, file_name=file_name)

# --- 6. ENQUIRY ---
with tab_enq:
    st.header("WhatsApp Enquiry")
    e_phone = st.text_input("Customer WhatsApp (e.g. 91999...)")
    e_msg = st.text_area("Message", "Hello, the price of the product is...")
    if st.button("Send WhatsApp"):
        encoded_msg = urllib.parse.quote(e_msg)
        st.markdown(f"[Click to Chat](https://wa.me/{e_phone}?text={encoded_msg})")
