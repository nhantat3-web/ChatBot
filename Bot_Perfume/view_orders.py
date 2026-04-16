import sqlite3

conn = sqlite3.connect("orders.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM orders")
rows = cursor.fetchall()

print("--- DANH SÁCH ĐƠN HÀNG ---")
for row in rows:
    print(f"SĐT: {row[0]} | Tên: {row[1]} | Địa chỉ: {row[2]} | Sản phẩm: {row[3]} | Trạng thái: {row[4]}")

conn.close()