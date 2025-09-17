# -*- coding: utf-8 -*-
import streamlit as st
import pyodbc
import datetime
import pandas as pd

# =================== HÀM XỬ LÝ DATABASE ===================
def get_connection():
    return pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=LEDINHHUY\SQLEXPRESS;"
        r"DATABASE=QLNhanVien;"
        r"Trusted_Connection=yes;"
    )

def cham_cong_database(ma_nv):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.datetime.now()
        today = now.date()
        current_time = now.strftime("%H:%M:%S")

        cursor.execute("SELECT HoTen FROM NhanVien WHERE MaNV = ?", (ma_nv,))
        row = cursor.fetchone()
        if not row:
            return False, f"Không tìm thấy nhân viên {ma_nv}"
        ho_ten = row[0]

        cursor.execute("""
            SELECT MaChamCong, GioVao, GioRa 
            FROM ChamCong 
            WHERE MaNV = ? AND NgayLamViec = ?
        """, (ma_nv, today))
        record = cursor.fetchone()

        if record is None:
            cursor.execute("SELECT ISNULL(MAX(MaChamCong), 0) + 1 FROM ChamCong")
            ma_cham_cong = cursor.fetchone()[0]
            ma_ca = 1 if now.hour < 12 else 2

            cursor.execute("""
                INSERT INTO ChamCong (MaChamCong, MaNV, MaCa, NgayLamViec, GioVao, TrangThai)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ma_cham_cong, ma_nv, ma_ca, today, now.time(), "Đã chấm công (vào)"))
            msg = f"{ho_ten} đã chấm công giờ vào lúc {current_time}"
        else:
            ma_cham_cong, gio_vao, gio_ra = record
            if gio_ra is None:
                cursor.execute("""
                    UPDATE ChamCong 
                    SET GioRa = ?, TrangThai = ?
                    WHERE MaChamCong = ?
                """, (now.time(), "Đã chấm công (ra)", ma_cham_cong))
                msg = f"{ho_ten} đã chấm công giờ ra lúc {current_time}"
            else:
                msg = f"{ho_ten} hôm nay đã chấm công đủ!"

        conn.commit()
        conn.close()
        return True, msg

    except Exception as e:
        return False, str(e)

def get_danh_sach_cham_cong():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.datetime.now().date()

        cursor.execute("""
            SELECT c.MaChamCong, n.MaNV, n.HoTen, c.NgayLamViec, c.GioVao, c.GioRa,
                   ISNULL(c.TrangThai, N'Chưa chấm công') as TrangThai
            FROM NhanVien n
            LEFT JOIN ChamCong c ON n.MaNV = c.MaNV AND c.NgayLamViec = ?
            ORDER BY n.MaNV
        """, (today,))

        rows = cursor.fetchall()
        conn.close()

        # Convert to DataFrame
        data = []
        for r in rows:
            data.append([
                r[0], r[1], r[2],
                r[3].strftime("%Y-%m-%d") if r[3] else "",
                r[4].strftime("%H:%M:%S") if r[4] else "",
                r[5].strftime("%H:%M:%S") if r[5] else "",
                r[6]
            ])
        return pd.DataFrame(data, columns=["Mã CC", "Mã NV", "Họ tên", "Ngày làm việc", "Giờ vào", "Giờ ra", "Trạng thái"])
    except Exception as e:
        st.error(str(e))
        return pd.DataFrame()

# =================== GIAO DIỆN STREAMLIT ===================
st.title("📊 BẢNG CHẤM CÔNG")

# Nhập mã nhân viên
ma_nv = st.text_input("Nhập mã nhân viên (ví dụ: NV001):")

if st.button("Chấm công"):
    if ma_nv:
        ok, msg = cham_cong_database(ma_nv)
        if ok:
            st.success(msg)
        else:
            st.error(msg)
    else:
        st.warning("Vui lòng nhập Mã NV!")

# Hiển thị bảng chấm công
st.subheader("Danh sách chấm công hôm nay")
df = get_danh_sach_cham_cong()
st.dataframe(df, use_container_width=True)
