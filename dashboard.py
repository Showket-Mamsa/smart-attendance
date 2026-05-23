import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import json

# ==========================================
# ১. পেজ কনফিগারেশন
# ==========================================
st.set_page_config(page_title="Smart Attendance Dashboard", layout="wide")
st.markdown("## 📊 Smart Attendance Ultimate Multi-Branch Dashboard")

# ==========================================
# ২. ডাটাবেস কানেকশন (মূল অ্যাটেনডেন্স ডাটা)
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    try:
        # প্রথমে লোকাল পিসির credentials.json থেকে ট্রাই করবে
        try:
            client = gspread.service_account(filename='credentials.json')
        except Exception:
            # লোকাল ফাইল না পেলে ক্লাউড Secrets থেকে নেবে
            creds_dict = json.loads(st.secrets["google_credentials"])
            client = gspread.service_account_from_dict(creds_dict)
            
        sheet = client.open("Smart_Attendance_Database").sheet1
        data = sheet.get_all_records()
        
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=['ID', 'Name', 'Designation', 'Date', 'Branch', 'Shift', 'In Time', 'Out Time', 'Status'])
            
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return pd.DataFrame(columns=['ID', 'Name', 'Designation', 'Date', 'Branch', 'Shift', 'In Time', 'Out Time', 'Status'])

# ==========================================
# ৩. ডাটাবেস কানেকশন (প্রোডাকশন ডাটা)
# ==========================================
@st.cache_data(ttl=60)
def load_production_data():
    try:
        try:
            client = gspread.service_account(filename='credentials.json')
        except Exception:
            creds_dict = json.loads(st.secrets["google_credentials"])
            client = gspread.service_account_from_dict(creds_dict)
            
        sheet = client.open("Smart_Attendance_Database")
        ws = sheet.worksheet("Production_Data")
        data = ws.get_all_records()
        
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# ডাটা লোড করা হচ্ছে
df = load_data()

# ==========================================
# ৪. সাইডবার অপশন (Sidebar)
# ==========================================
st.sidebar.markdown("### 🔄 রিয়ে-টাইম আপডেট")
if st.sidebar.button("লাইভ ডেটা রিফ্রেশ করুন"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### 💰 স্যালারি ও পেনাল্টি সেটিংস")
base_salary = st.sidebar.number_input("অফিস কর্মীদের মূল বেতন (BDT):", value=15000, step=500)
late_penalty_days = st.sidebar.number_input("কতদিন লেট হলে ১ দিনের বেতন কাটবে?:", value=3, step=1)

# ==========================================
# ৫. মূল ড্যাশবোর্ড (Tabs)
# ==========================================
tabs = st.tabs(["🗓️ দৈনিক রিপোর্ট (Daily)", "📊 মাসিক রিপোর্ট ও স্যালারি (Monthly)", "👤 প্রোফাইল অ্যানালিটিক্স (Profile)"])

# --- Tab 1: Daily Report ---
with tabs[0]:
    st.markdown("### 🔍 দৈনিক ফিল্টার অপশন")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        date_list = ["No Data"] if df.empty else df['Date'].unique().tolist()
        selected_date = st.selectbox("তারিখ সিলেক্ট করুন:", date_list)
        
    with col2:
        branch_list = ["All Branches"] + (df['Branch'].dropna().unique().tolist() if not df.empty else [])
        selected_branch = st.selectbox("ব্রাঞ্চ সিলেক্ট করুন:", branch_list)
        
    with col3:
        shift_list = ["All Shifts"] + (df['Shift'].dropna().unique().tolist() if not df.empty else [])
        selected_shift = st.selectbox("শিফট সিলেক্ট করুন:", shift_list)
        
    with col4:
        desig_list = ["All Designations"] + (df['Designation'].dropna().unique().tolist() if not df.empty else [])
        selected_desig = st.selectbox("পদবি সিলেক্ট করুন:", desig_list)
        
    with col5:
        emp_list = ["All Employees"] + (df['Name'].dropna().unique().tolist() if not df.empty else [])
        selected_emp = st.selectbox("নির্দিষ্ট কর্মী খুঁজুন:", emp_list)

    # Filtering Logic
    filtered_df = df.copy()
    if not filtered_df.empty:
        if selected_date != "No Data":
            filtered_df = filtered_df[filtered_df['Date'] == selected_date]
        if selected_branch != "All Branches":
            filtered_df = filtered_df[filtered_df['Branch'] == selected_branch]
        if selected_shift != "All Shifts":
            filtered_df = filtered_df[filtered_df['Shift'] == selected_shift]
        if selected_desig != "All Designations":
            filtered_df = filtered_df[filtered_df['Designation'] == selected_desig]
        if selected_emp != "All Employees":
            filtered_df = filtered_df[filtered_df['Name'] == selected_emp]

    # Metrics Display
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    
    total_emp = len(filtered_df)
    present_emp = len(filtered_df[filtered_df['Status'] == 'P']) if not filtered_df.empty else 0
    late_emp = len(filtered_df[filtered_df['Status'] == 'LC']) if not filtered_df.empty else 0
    absent_emp = len(filtered_df[filtered_df['Status'] == 'A']) if not filtered_df.empty else 0
    
    m1.metric("মোট কর্মী", total_emp)
    m2.metric("উপস্থিত (P)", present_emp)
    m3.metric("লেট (LC)", late_emp)
    m4.metric("অনুপস্থিত (A)", absent_emp)
    
    st.markdown("---")
    
    # Charts & Table
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 📈 Attendance Chart")
        if total_emp > 0 and (present_emp > 0 or late_emp > 0 or absent_emp > 0):
            pie_data = pd.DataFrame({
                'Status': ['Present', 'Late', 'Absent'],
                'Count': [present_emp, late_emp, absent_emp]
            })
            pie_data = pie_data[pie_data['Count'] > 0]
            fig = px.pie(pie_data, values='Count', names='Status', hole=0.4, 
                         color='Status', color_discrete_map={'Present':'#28a745', 'Late':'#ffc107', 'Absent':'#dc3545'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("কোনো ডেটা নেই!")
            
    with c2:
        st.markdown("#### 📝 Detailed Report")
        if not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.info("empty")

# --- Tab 2 & 3: Monthly & Profile ---
with tabs[1]:
    st.markdown("### 📊 মাসিক রিপোর্ট ও স্যালারি")
    st.info("এই সেকশনের কাজ চলছে...")

with tabs[2]:
    st.markdown("### 👤 প্রোফাইল অ্যানালিটিক্স")
    st.info("এই সেকশনের কাজ চলছে...")

# ==========================================
# ৬. প্রোডাকশন ড্যাশবোর্ড
# ==========================================
st.markdown("---")
st.markdown("## 💰 প্রোডাকশন ও ইনকাম (KS) ড্যাশবোর্ড")
prod_df = load_production_data()
if not prod_df.empty:
    st.dataframe(prod_df, use_container_width=True, hide_index=True)
else:
    st.info("প্রোডাকশন ডেটা এখনো যোগ করা হয়নি বা লোড হচ্ছে না।")