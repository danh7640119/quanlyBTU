import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Cấu hình quyền truy cập
scopes = ["https://www.googleapis.com/auth/spreadsheets"]

# Lấy thông tin từ Secret của Streamlit (An toàn)
skey = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(skey, scopes=scopes)
client = gspread.authorize(creds)

# Đọc Sheet
@st.cache_data(ttl=300) # Lưu bộ nhớ đệm 5 phút
def get_data():
    sh = client.open("Tên_File_Google_Sheet_Của_Bạn")
    worksheet = sh.worksheet("ThongTin")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

df = get_data()
st.write("Dữ liệu đã được bảo mật qua API!")
st.dataframe(df)
