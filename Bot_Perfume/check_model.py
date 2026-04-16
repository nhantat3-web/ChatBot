import google.generativeai as genai

# Dán API Key của bạn vào đây
genai.configure(api_key='AIzaSyCy0WZFcsUzylUW6UrJmQrqMKG7raedY8s')

print("Danh sách các model bạn có thể dùng:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)