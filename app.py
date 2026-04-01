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
    conn = sqlite3.connect('ak_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS store (name TEXT, addr TEXT, contact TEXT, owner TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, buy_price REAL, sell_price REAL, disc_price REAL, qty INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS suppliers (name TEXT, contact TEXT, bank TEXT, upi TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- APP UI ---
st.set_page_config(page_title="AK Store Manager", layout="wide")
st.title("🏬 AK Store Purchase & Sale Manager")

menu = st.sidebar.selectbox("Menu", ["Sale Panel", "Purchase Inventory", "Customer Enquiry", "Suppliers", "Store Settings"])

# --- 1. STORE SETTINGS ---
if menu == "Store Settings":
    st.header("⚙️ Store Settings")
    with st.form("store_form"):
        name = st.text_input("Store Name", "AK Stores")
        addr = st.text_area("Address", "Main Road, City")
        cont = st.text_input("Contact")
        owner = st.text_input("Proprietor", "Suraj.M")
        if st.form_submit_button("Save"):
            conn.execute("DELETE FROM store")
            conn.execute("INSERT INTO store VALUES (?,?,?,?)", (name, addr, cont, owner))
            st.success("Saved!")

# --- 2. PURCHASE INVENTORY ---
elif menu == "Purchase Inventory":
    st.header("📦 Add Purchase")
    with st.form("p_form"):
        col1, col2 = st.columns(2)
        p_code = col1.text_input("Product Code")
        p_name = col1.text_input("Product Name")
        p_buy = col2.number_input("Purchase Price")
        p_sell = col2.number_input("Margin Price")
        p_disc = col2.number_input("Discount Price")
        p_qty = col1.number_input("Quantity", step=1)
        if st.form_submit_button("Add to Stock"):
            conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?)", (p_code, p_name, p_buy, p_sell, p_disc, p_qty))
            st.success(f"Added {p_name}")

# --- 3. SALE PANEL (INVOICE) ---
elif menu == "Sale Panel":
    st.header("🧾 Sale Invoice")
    
    # Get Store Info
    store_info = conn.execute("SELECT * FROM store").fetchone()
    s_name = store_info[0] if store_info else "AK STORE"
    s_addr = store_info[1] if store_info else "Address"

    st.markdown(f"<h1 style='text-align: center;'>{s_name}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>{s_addr}</p>", unsafe_allow_True=True)
    
    bill_no = f"AK/{datetime.now().strftime('%H%M')}/2024"
    st.subheader(f"Bill No: {bill_no}")
    
    # Select Product
    prods = pd.read_sql("SELECT code, name, disc_price FROM products", conn)
    selected = st.multiselect("Select Products", prods['code'].tolist())
    
    if selected:
        items = prods[prods['code'].isin(selected)]
        st.table(items)
        total = items['disc_price'].sum()
        st.write(f"### Total: ₹{total}")
        
        words = num2words(total, lang='en_IN').capitalize() + " Rupees Only"
        st.write(f"**In Words:** {words}")

        if st.button("Generate PDF Bill"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=s_name, ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(200, 10, txt=s_addr, ln=True, align='C')
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"Bill No: {bill_no}", ln=True)
            pdf.cell(200, 10, txt=f"Total: Rs.{total}", ln=True)
            pdf.cell(200, 10, txt=f"Proprietor: Suraj.M", ln=True)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("Download PDF", pdf_bytes, "bill.pdf")

# --- 4. ENQUIRY ---
elif menu == "Customer Enquiry":
    st.header("🔍 Enquiry")
    search = st.text_input("Enter Product Code")
    if search:
        res = conn.execute("SELECT * FROM products WHERE code=?", (search,)).fetchone()
        if res:
            st.write(f"Product: {res[1]}")
            st.write(f"Original Price: ₹{res[3]}")
            st.write(f"Discount Price: ₹{res[4]}")
            msg = f"Product: {res[1]} | Price: Rs.{res[4]} at {s_name}"
            st.link_button("Share via WhatsApp", f"https://wa.me/?text={msg}")
