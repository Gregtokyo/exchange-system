
import streamlit as st
import sqlite3
import pdfplumber
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

DB = "data.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS rates(currency TEXT, rate REAL)")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency TEXT,
                amount REAL,
                rate REAL,
                profit REAL)""")
    conn.commit()
    conn.close()

init_db()

st.title("Exchange Management System")

# Upload PDF
st.header("1️⃣ Upload Rate PDF")
pdf_file = st.file_uploader("Upload Partner PDF", type="pdf")

if pdf_file:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM rates")

    with pdfplumber.open("temp.pdf") as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split("\n")
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    code = parts[0]
                    try:
                        rate = float(parts[-1])
                        c.execute("INSERT INTO rates VALUES(?,?)", (code, rate))
                    except:
                        pass

    conn.commit()
    conn.close()
    st.success("Rates Imported Successfully")

# Add Transaction
st.header("2️⃣ Add Transaction")

conn = sqlite3.connect(DB)
rates = pd.read_sql_query("SELECT * FROM rates", conn)
conn.close()

if not rates.empty:
    currency = st.selectbox("Currency", rates["currency"])
    amount = st.number_input("Foreign Amount", min_value=0.0)

    if st.button("Submit Transaction"):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        rate = rates[rates["currency"] == currency]["rate"].values[0]
        markup = 0.003
        my_rate = rate * (1 + markup)
        profit = amount * (my_rate - rate)

        c.execute("INSERT INTO transactions(currency,amount,rate,profit) VALUES(?,?,?,?)",
                  (currency, amount, my_rate, profit))
        conn.commit()
        conn.close()
        st.success(f"Transaction Added. Profit: {profit:.2f} JPY")

# Show Transactions
st.header("3️⃣ Transactions")

conn = sqlite3.connect(DB)
tx = pd.read_sql_query("SELECT * FROM transactions", conn)
conn.close()

if not tx.empty:
    st.dataframe(tx)
    st.write("Total Profit:", tx["profit"].sum())
