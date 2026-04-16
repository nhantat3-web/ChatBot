# Sử dụng Python image nhẹ để tiết kiệm dung lượng
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file danh sách thư viện vào trước để cache
COPY requirements.txt .

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code và file database vào container
COPY . .

# Chạy bot khi container khởi động
CMD ["python", "bot_perfume.py"]