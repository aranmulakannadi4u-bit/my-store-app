import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
from num2words import num2words
from fpdf import FPDF
import io

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('ak_store_final.db', check_same_thread=False)
    cursor = conn.cursor()
    # Create tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS store (name TEXT, addr TEXT, contact TEXT, logo BLOB, owner TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers (name TEXT, contact1 TEXT, contact2 TEXT, bank TEXT, upi TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, buy_price REAL, margin_price REAL, disc_price REAL, qty INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("AK Store Manager")
menu = st.sidebar.selectbox("Go to:", ["Sale Panel", "Purchase Inventory", "Customer Enquiry", "Suppliers", "Store Settings", "Reports"])

# --- 1. STORE SETTINGS ---
if menu == "Store Settings":
    st.header("🏪 Store Details")
    with st.form("store_settings"):
        name = st.text_input("Store Name", "AK STORES")
        addr = st.text_area("Store Address")
        cont = st.text_input("Contact Number")
        logo_file = st.file_uploader("Upload Store Logo", type=['jpg','png'])
        owner = st.text_input("Proprietor Name", "Suraj.M")
        
        if st.form_submit_button("Save Details"):
            logo_data = logo_file.read() if logo_file else None
            conn.execute("DELETE FROM store")
            conn.execute("INSERT INTO store VALUES (?,?,?,?,?)", (name, addr, cont, logo_data, owner))
            conn.commit()
            st.success("Store Details Saved!")

# --- 2. PURCHASE INVENTORY ---
elif menu == "Purchase Inventory":
    st.header("📥 Stock Entry")
    with st.form("purchase_form"):
        col1, col2 = st.columns(2)
        p_code = col1.text_input("Product Code (Unique)")
        p_name = col1.text_input("Product Name")
        p_buy = col2.number_input("Purchase Price (₹)")
        p_margin = col2.number_input("Selling Price (₹)")
        p_disc = col2.number_input("Discounted Price (₹)")
        p_qty = col1.number_input("Quantity", step=1)
        
        if st.form_submit_button("Add Product"):
            if p_code:
                conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?)", 
                             (p_code, p_name, p_buy, p_margin, p_disc, p_qty))
                conn.commit()
                st.success(f"Product {p_name} added/updated!")
            else:
                st.error("Product Code is required!")

# --- 3. SALE PANEL ---
elif menu == "Sale Panel":
    st.header("🧾 Generate Invoice")
    
    # Load Store Header
    store = conn.execute("SELECT * FROM store").fetchone()
    if store:
        col_l, col_r = st.columns([1, 4])
        if store[3]: col_l.image(store[3], width=100)
        col_r.markdown(f"<h1 style='text-align: center;'>{store[0]}</h1>", unsafe_allow_html=True)
        col_r.markdown(f"<p style='text-align: center;'>{store[1]}<br>Contact: {store[2]}</p>", unsafe_allow_html=True)
    
    st.divider()
    
    # Bill details
    bill_no = f"AK/{datetime.now().strftime('%M%S')}/{datetime.now().year}"
    st.subheader(f"Bill No: {bill_no}")
    
    # Product Selection
    all_p = pd.read_sql("SELECT code, name, disc_price FROM products", conn)
    selected_codes = st.multiselect("Select Product Codes", all_p['code'].tolist())
    
    if selected_codes:
        bill_items = all_p[all_p['code'].isin(selected_codes)]
        st.table(bill_items)
        
        total = bill_items['disc_price'].sum()
        st.metric("Final Price", f"₹{total}")
        
        # Word Conversion
        words = num2words(total, lang='en_IN').capitalize() + " Rupees Only"
        st.write(f"**Amount in Words:** {words}")
        st.write(f"**Proprietor:** Suraj.M")

        # PDF Generator
        if st.button("Download Invoice PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 20)
            pdf.cell(190, 10, txt=store[0] if store else "AK STORE", ln=True, align='C')
            pdf.set_font("Helvetica", '', 10)
            pdf.cell(190, 5, txt=store[1] if store else "", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(190, 10, txt=f"Bill No: {bill_no}      Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True)
            pdf.ln(5)
            pdf.cell(190, 10, txt="Items List:", ln=True)
            for index, row in bill_items.iterrows():
                pdf.set_font("Helvetica", '', 11)
                pdf.cell(190, 8, txt=f"- {row['name']} : Rs.{row['disc_price']}", ln=True)
            pdf.ln(5)
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(190, 10, txt=f"Total: Rs.{total}", ln=True)
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(190, 10, txt=f"Words: {words}", ln=True)
            pdf.ln(10)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(190, 10, txt="Proprietor: Suraj.M", ln=True, align='R')
            
            pdf_bytes = pdf.output()
            st.download_button("Click here to Download PDF", pdf_bytes, file_name=f"AK_Bill_{bill_no.replace('/','_')}.pdf")

# --- 4. CUSTOMER ENQUIRY ---
elif menu == "Customer Enquiry":
    st.header("🔍 Product Enquiry & WhatsApp Share")
    p_to_find = st.selectbox("Select Product to Enquire", pd.read_sql("SELECT code FROM products", conn))
    
    if p_to_find:
        res = conn.execute("SELECT * FROM products WHERE code=?", (p_to_find,)).fetchone()
        st.subheader(f"Product: {res[1]}")
        st.write(f"Standard Price: ₹{res[3]}")
        st.write(f"Special Price: ₹{res[5]}")
        
        # WhatsApp Share link
        msg = f"Check out this product at {store[0] if store else 'AK Store'}:\nProduct: {res[1]}\nPrice: Rs.{res[5]}"
        wa_url = f"https://wa.me/?text={msg.replace(' ', '%20').replace(':','%3A').replace('/','%2F')}"
        st.link_button("Share on WhatsApp", wa_url)

# --- 5. SUPPLIERS ---
elif menu == "Suppliers":
    st.header("🤝 Supplier Management")
    with st.form("sup_form"):
        sname = st.text_input("Supplier Name")
        sc1 = st.text_input("Contact 1")
        sc2 = st.text_input("Contact 2")
        sbank = st.text_area("Bank Details")
        supi = st.text_input("UPI ID")
        if st.form_submit_button("Add Supplier"):
            conn.execute("INSERT INTO suppliers VALUES (?,?,?,?,?)", (sname, sc1, sc2, sbank, supi))
            conn.commit()
            st.success("Supplier Added!")
    
    st.subheader("Current Suppliers")
    st.dataframe(pd.read_sql("SELECT * FROM suppliers", conn))

# --- 6. REPORTS ---
elif menu == "Reports":
    st.header("📊 Inventory Report")
    df = pd.read_sql("SELECT * FROM products", conn)
    st.dataframe(df)
