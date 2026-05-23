import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="Smart Attendance Dashboard", layout="wide")

st.markdown("## 📊 Smart Attendance Ultimate Multi-Branch Dashboard")

# --- Google Sheets Connection Magic ---
@st.cache_data(ttl=60)
def load_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("Smart_Attendance_Database").sheet1
        data = sheet.get_all_records()
        
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=['ID', 'Name', 'Designation', 'Date', 'Branch', 'Shift', 'In Time', 'Out Time', 'Status'])
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return pd.DataFrame(columns=['ID', 'Name', 'Designation', 'Date', 'Branch', 'Shift', 'In Time', 'Out Time', 'Status'])

df = load_data()

# CEO Live Refresh Button
st.sidebar.markdown("### 🔄 রিয়েল-টাইম আপডেট")
if st.sidebar.button("লাইভ ডেটা রিফ্রেশ করুন"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### 💰 স্যালারি ও পেনাল্টি সেটিংস")
base_salary = st.sidebar.number_input("অফিস কর্মীদের মূল বেতন (BDT):", min_value=0, value=15000, step=1000)
late_count_for_deduction = st.sidebar.number_input("কতদিন লেট হলে ১ দিনের বেতন কাটবে?:", min_value=1, value=3)

tab1, tab2, tab3 = st.tabs(["📅 দৈনিক রিপোর্ট (Daily)", "📆 মাসিক রিপোর্ট ও স্যালারি (Monthly)", "👤 প্রোফাইল অ্যানালিটিক্স (Profile)"])

# ================= TAB 1 : দৈনিক রিপোর্ট =================
with tab1:
    st.markdown("### 🔍 দৈনিক ফিল্টার অপশন")
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        if not df.empty:
            dates = df['Date'].unique().tolist()
            selected_date = st.selectbox("তারিখ সিলেক্ট করুন:", dates, index=len(dates)-1)
            filtered_df = df[df['Date'] == selected_date]
        else:
            st.selectbox("তারিখ সিলেক্ট করুন:", ["No Data"])
            filtered_df = df
            selected_date = "No Data"

    with col_f2:
        branch_opts = ['All Branches', 'Sohor', 'Betagi', 'Potiya', 'Online', 'Sohor (Temp)']
        selected_branch = st.selectbox("ব্রাঞ্চ সিলেক্ট করুন:", branch_opts)
        if selected_branch != 'All Branches':
            filtered_df = filtered_df[filtered_df['Branch'] == selected_branch]

    with col_f3:
        shift_opts = ['All Shifts', 'Day', 'Evening', 'Morning', 'Afternoon', 'Online']
        selected_shift = st.selectbox("শিফট সিলেক্ট করুন:", shift_opts)
        if selected_shift != 'All Shifts':
            filtered_df = filtered_df[filtered_df['Shift'] == selected_shift]

    with col_f4:
        desig_opts = ['All Designations'] + filtered_df['Designation'].unique().tolist() if not filtered_df.empty else ['All Designations']
        selected_desig = st.selectbox("পদবি সিলেক্ট করুন:", desig_opts)
        if selected_desig != 'All Designations':
            filtered_df = filtered_df[filtered_df['Designation'] == selected_desig]

    with col_f5:
        employees = ['All Employees'] + filtered_df['Name'].unique().tolist() if not filtered_df.empty else ['All Employees']
        selected_emp = st.selectbox("নির্দিষ্ট কর্মী খুঁজুন:", employees, key="daily_emp")
        if selected_emp != 'All Employees':
            filtered_df = filtered_df[filtered_df['Name'] == selected_emp]

    total_emp = len(filtered_df)
    present = len(filtered_df[filtered_df['Status'] == 'P'])
    late = len(filtered_df[filtered_df['Status'] == 'LC'])
    absent = len(filtered_df[filtered_df['Status'] == 'A'])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("মোট কর্মী", total_emp)
    c2.metric("উপস্থিত (P)", present)
    c3.metric("লেট (LC)", late)
    c4.metric("অনুপস্থিত (A)", absent)

    st.markdown("---")
    col_chart, col_table = st.columns([1, 2])
    with col_chart:
        st.markdown("### 📈 Attendance Chart")
        if total_emp > 0:
            status_counts = filtered_df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.pie(status_counts, values='Count', names='Status', hole=0.4, color='Status', color_discrete_map={'P': '#28a745', 'LC': '#ffc107', 'A': '#dc3545'})
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("কোনো ডেটা নেই!")

    with col_table:
        st.markdown("### 📝 Detailed Report")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# ================= TAB 2 : মাসিক রিপোর্ট ও স্যালারি =================
with tab2:
    st.markdown("### 📊 মাসিক উপস্থিতির সারসংক্ষেপ ও স্যালারি")
    if not df.empty:
        df['Month_Year'] = df['Date'].apply(lambda x: "-".join(x.split('-')[1:]))
        months = df['Month_Year'].unique().tolist()
        selected_month = st.selectbox("মাস সিলেক্ট করুন:", months, key="monthly_month")
        
        monthly_df = df[df['Month_Year'] == selected_month].copy()
        month_dates = monthly_df['Date'].unique().tolist()
        
        st.markdown("#### 🌴 ছুটির দিনের সেটিংস (Holiday Settings)")
        hol_col1, hol_col2 = st.columns(2)
        with hol_col1:
            holiday_dates = st.multiselect("এই মাসের সাপ্তাহিক বা সরকারী ছুটির তারিখগুলো সিলেক্ট করুন:", month_dates)
        with hol_col2:
            holiday_allowance = st.number_input("ছুটির দিনে ডিউটির জন্য এক্সট্রা ভাতা (BDT):", min_value=0, value=0, step=100)
        
        monthly_df['Calc_Status'] = monthly_df.apply(
            lambda row: 'H_A' if (row['Date'] in holiday_dates and row['Status'] == 'A') else
                        'H_P' if (row['Date'] in holiday_dates and row['Status'] in ['P', 'LC']) else
                        row['Status'], axis=1
        )
        
        summary = monthly_df.groupby(['ID', 'Name', 'Designation'])['Calc_Status'].value_counts().unstack(fill_value=0).reset_index()
        for col in ['P', 'LC', 'A', 'H_A', 'H_P']:
            if col not in summary.columns: summary[col] = 0
        
        def calc_payroll(row):
            emp_id = str(row['ID'])
            if emp_id.startswith('OPRON') or (emp_id.startswith('BG') and len(emp_id) == 6):
                return 0, 0, 0, 0, 0 
            
            emp_base = base_salary
            per_day = emp_base / 30
            late_ded = (row['LC'] // late_count_for_deduction) * per_day
            abs_ded = row['A'] * per_day 
            holiday_bonus = row['H_P'] * holiday_allowance
            
            net = emp_base - late_ded - abs_ded + holiday_bonus
            return emp_base, round(late_ded, 2), round(abs_ded, 2), round(holiday_bonus, 2), max(0, round(net, 2))

        summary['payroll'] = summary.apply(calc_payroll, axis=1)
        summary['মূল বেতন (BDT)'] = summary['payroll'].apply(lambda x: x[0])
        summary['লেট জরিমানা (BDT)'] = summary['payroll'].apply(lambda x: x[1])
        summary['অনুপস্থিতি কর্তন (BDT)'] = summary['payroll'].apply(lambda x: x[2])
        summary['হলিডে বোনাস (BDT)'] = summary['payroll'].apply(lambda x: x[3])
        summary['চূড়ান্ত বেতন (BDT)'] = summary['payroll'].apply(lambda x: x[4])
        
        summary = summary.drop(columns=['payroll'])
        display_summary = summary.rename(columns={
            'P': 'সাধারণ উপস্থিত', 'LC': 'লেট (LC)', 'A': 'অনুপস্থিত', 
            'H_A': 'ছুটি (টাকা কাটা হবে না)', 'H_P': 'ছুটির দিনে ডিউটি'
        })
        st.dataframe(display_summary, use_container_width=True, hide_index=True)
        
        csv_monthly = display_summary.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 মাসিক স্যালারি রিপোর্ট ডাউনলোড করুন (CSV)", data=csv_monthly, file_name=f"Monthly_Salary_Report_{selected_month}.csv", mime="text/csv")
    else: st.info("পর্যাপ্ত ডেটা নেই।")

# ================= TAB 3 : প্রোফাইল অ্যানালিটিক্স =================
with tab3:
    st.markdown("### 👤 ইন্ডিভিজুয়াল কর্মী পারফরম্যান্স ট্র্যাক")
    if not df.empty:
        emp_list = df['Name'].unique().tolist()
        selected_prof_emp = st.selectbox("कर्मীর নাম সিলেক্ট করুন:", emp_list)
        emp_df = df[df['Name'] == selected_prof_emp]
        
        if not emp_df.empty:
            st.markdown(f"**পদবি (Designation):** {emp_df.iloc[0]['Designation']}")
        
        prof_c1, prof_c2, prof_c3 = st.columns(3)
        prof_c1.metric("মোট উপস্থিতি", len(emp_df[emp_df['Status'].isin(['P', 'LC'])]))
        prof_c2.metric("মোট লেট", len(emp_df[emp_df['Status'] == 'LC']))
        prof_c3.metric("মোট অনুপস্থিতি", len(emp_df[emp_df['Status'] == 'A']))
        
        perf_counts = emp_df['Status'].value_counts().reset_index()
        perf_counts.columns = ['স্ট্যাটাস', 'দিন সংখ্যা']
        fig_perf = px.bar(perf_counts, x='স্ট্যাটাস', y='দিন সংখ্যা', color='স্ট্যাটাস', color_discrete_map={'P': '#28a745', 'LC': '#ffc107', 'A': '#dc3545'})
        st.plotly_chart(fig_perf, use_container_width=True)
    else: st.info("প্রোফাইল দেখার জন্য সিস্টেমে কোনো ডেটা নেই।")
# =====================================================================
# ------------ NEW SECTION : PRODUCTION & INCOME (KS) -----------------
# =====================================================================
import gspread

st.markdown("---") # একটি লম্বা দাগ বা ডিভাইডার দেওয়ার জন্য
st.title("💰 প্রোডাকশন ও ইনকাম (KS) ড্যাশবোর্ড")

# Google Sheet theke fresh data niye asha
@st.cache_data(ttl=60)  # Protity 60 second por por refresh hobe
def load_production_data():
    client = gspread.service_account(filename='credentials.json')
    sheet = client.open("Smart_Attendance_Database")
    ws = sheet.worksheet("Production_Data")
    data = ws.get_all_records()
    return pd.DataFrame(data)

try:
    df_prod = load_production_data()
    
    if not df_prod.empty:
        # Date column-ke sothik format-e neya
        df_prod['Date'] = pd.to_datetime(df_prod['Date'], format='%d-%m-%Y').dt.date
        
        # --- FEATURE 1: Custom Date Range Filter ---
        st.subheader("🗓️ তারিখ সিলেক্ট করুন (Date Range)")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", value=df_prod['Date'].min(), key='start_date_prod')
        with col2:
            end_date = st.date_input("To Date", value=df_prod['Date'].max(), key='end_date_prod')
            
        # Date range onujayi data filter kora
        mask = (df_prod['Date'] >= start_date) & (df_prod['Date'] <= end_date)
        df_filtered = df_prod.loc[mask]
        
        # --- FEATURE 2: Key Performance Indicators (KPI Cards) ---
        total_images = df_filtered['Total Images'].sum()
        total_income = df_filtered['Income'].sum()
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric(label="মোট ইমেজ (Total Images)", value=f"{total_images:,.0f}")
        with m_col2:
            st.metric(label="মোট ইনকাম (Total Revenue)", value=f"৳ {total_income:,.2f}")
            
        # --- FEATURE 3: Branch/Type Onujayi Overview Chart ---
        st.subheader("📊 ব্রাঞ্চ অনুযায়ী কাজের চিত্র")
        
        # ID check kore branch aladha kora
        def assign_branch(emp_id):
            emp_id = str(emp_id).upper()
            if emp_id.startswith('OPRON'): return 'Office Online'
            elif any(k in emp_id for k in ['BGLB', 'JESMIN', 'RUBI', 'PUJA', 'MUKTA', 'BGBL', 'BGFCT', 'JONE', 'CHOP', 'BTLB', 'MEHARAZ']): return 'Little Boss Online'
            else: return 'Regular Branch (BG/Evening/Betagi/Potiya)'
            
        df_filtered['Branch'] = df_filtered['Operator ID'].apply(assign_branch)
        branch_summary = df_filtered.groupby('Branch')['Income'].sum().reset_index()
        
        # Streamlit Bar Chart
        st.bar_chart(data=branch_summary, x='Branch', y='Income')
        
        # --- FEATURE 4: Individual Operator Search System ---
        st.subheader("🔍 ইন্ডিভিজ্যুয়াল অপারেটর ইনকাম ট্র্যাক")
        search_id = st.text_input("অপারেটর আইডি লিখুন (যেমন: BG00175, OPRON001):").strip().upper()
        
        if search_id:
            df_ops = df_filtered[df_filtered['Operator ID'] == search_id]
            if not df_ops.empty:
                st.success(f"আইডি: {search_id} এর ডেটা পাওয়া গেছে!")
                st.dataframe(df_ops[['Date', 'Total Images', 'Rate', 'Income']].sort_values(by='Date', ascending=False), use_container_width=True)
                
                ops_total_img = df_ops['Total Images'].sum()
                ops_total_inc = df_ops['Income'].sum()
                st.info(f"সিলেক্ট করা তারিখে এই অপারেটরের: মোট ইমেজ = {ops_total_img:,.0f} | মোট ইনকাম = ৳ {ops_total_inc:,.2f}")
            else:
                st.warning("এই আইডির কোনো ডেটা সিলেক্ট করা তারিখে নেই!")
                
        # --- FEATURE 5: Total Data Table ---
        st.subheader("📋 ফিল্টার করা সম্পূর্ণ ডেটাশিট")
        st.dataframe(df_filtered[['Date', 'Operator ID', 'Branch', 'Total Images', 'Rate', 'Income']].sort_values(by='Date', ascending=False), use_container_width=True)
        
    else:
        st.warning("Google Sheet-এ কোনো প্রোডাকশন ডেটা পাওয়া যায়নি!")
except Exception as e:
    st.error(f"ড্যাশবোর্ডে ডেটা লোড করতে সমস্যা হচ্ছে: {e}")
# একদম ফাইলের শেষে এই অংশটুকু পেস্ট করুন:
import gspread  # যদি আগে ইমপোর্ট করা না থাকে
import json

st.markdown("---")
st.title("💰 প্রোডাকশন ও ইনকাম (KS) ড্যাশবোর্ড")

@st.cache_data(ttl=60)
@st.cache_data(ttl=60)
def load_production_data():
    try:
        # প্রথমে চেষ্টা করবে লোকাল পিসির credentials.json ফাইল থেকে ডাটা নেওয়ার
        client = gspread.service_account(filename='credentials.json')
    except Exception:
        # যদি লোকাল ফাইল না পায় (মানে Streamlit Cloud-এ রান হচ্ছে), তখন Secrets থেকে নেবে
        try:
            creds_dict = json.loads(st.secrets["google_credentials"])
            client = gspread.service_account_from_dict(creds_dict)
        except Exception:
            # যদি পুরনো Secrets কাজ না করে, তবে নতুন Secrets ফরম্যাট ট্রাই করবে
            try:
                creds_dict = json.loads(st.secrets["GOOGLE_SHEETS"]["json"])
                client = gspread.service_account_from_dict(creds_dict)
            except Exception as e:
                st.error(f"Authentication Error: Could not load credentials. Details: {e}")
                return pd.DataFrame()
                
    try:
        sheet = client.open("Smart_Attendance_Database")
        ws = sheet.worksheet("Production_Data")
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Database Error: Could not open sheet. Details: {e}")
        return pd.DataFrame()