import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient

app = Flask(__name__)

# เชื่อมต่อกับ MongoDB Atlas
client = MongoClient("mongodb+srv://mongodb:mg12345678@cluster0.fvpxm.mongodb.net/nobita_database?retryWrites=true&w=majority")
db = client['nobita_database']
collection = db['users']

@app.route('/')
def index():
    # ดึงข้อมูลผู้ใช้ทั้งหมดจาก Collection
    users = collection.find()  # `find()` จะดึงเอกสารทั้งหมด
    user_count = collection.count_documents({})  # ใช้ count_documents เพื่อนับจำนวนเอกสารใน Collection
    return render_template('index.html', users=users, user_count=user_count)

@app.route('/add', methods=['POST'])
def add_user():
    username = request.form['username']
    email = request.form['email']
    
    # เพิ่มข้อมูลใหม่ลงใน MongoDB
    collection.insert_one({'username': username, 'email': email})
    
    flash('Herbal added successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # อ่านพอร์ตจาก environment variables
    port = int(os.environ.get("PORT", 5000))
    # รันแอปโดยฟังที่ 0.0.0.0 และพอร์ตที่ถูกกำหนดโดย Render
    app.run(host="0.0.0.0", port=port, debug=True)