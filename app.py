import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient

app = Flask(__name__)

# เชื่อมต่อกับ MongoDB Atlas
client = MongoClient("mongodb+srv://mongodb:mg12345678@cluster0.fvpxm.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client['nobita_database']
collection = db['users']

@app.route('/')
def index():
    herbals_info = collection.find()  # ดึงข้อมูลผู้ใช้ทั้งหมดจาก MongoDB
    return render_template('general_pretest.html', herbals_info=herbals_info)

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