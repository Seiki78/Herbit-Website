import pandas as pd
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId  # ต้องใช้ ObjectId เพื่อจัดการกับ MongoDB IDs

app = Flask(__name__)

app.secret_key = os.urandom(24)

# เชื่อมต่อกับ MongoDB Atlas
client = MongoClient("mongodb+srv://mongodb:mg12345678@cluster0.fvpxm.mongodb.net/nobita_database?retryWrites=true&w=majority")
db = client['nobita_database']
users_collection = db['users']
chronics_data_collection = db['chronics_data']

@app.route('/')
def index():
    # ดึงข้อมูลผู้ใช้ทั้งหมดจาก Collection
    users = users_collection.find()  # `find()` จะดึงเอกสารทั้งหมด
    user_count = users_collection.count_documents({})  # ใช้ count_documents เพื่อนับจำนวนเอกสารใน Collection
    return render_template('index.html', users=users, user_count=user_count)

@app.route('/add', methods=['POST'])
def add_user():
    username = request.form['username']
    email = request.form['email']
    
    # เพิ่มข้อมูลใหม่ลงใน MongoDB
    users_collection.insert_one({'username': username, 'email': email})
    
    flash('User added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<user_id>', methods=['POST'])
def delete_user(user_id):
    # ลบผู้ใช้จาก MongoDB โดยใช้ ObjectId
    users_collection.delete_one({'_id': ObjectId(user_id)})
    flash('User deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        # รับข้อมูลใหม่จากฟอร์ม
        username = request.form['username']
        email = request.form['email']
        
        # อัปเดตข้อมูลผู้ใช้ใน MongoDB
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'username': username, 'email': email}})
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('index'))
    
    # ดึงข้อมูลผู้ใช้ที่ต้องการแก้ไขเพื่อแสดงในฟอร์ม
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('edit.html', user=user)

@app.route('/general_pre')
def general_pre():

    # ดึงข้อมูลทั้งหมดจาก Collection
    chronics = chronics_data_collection.find()  # `find()` จะดึงเอกสารทั้งหมด

    return render_template('general_predict.html', chronics=chronics)

if __name__ == '__main__':
    # อ่านพอร์ตจาก environment variables
    port = int(os.environ.get("PORT", 5000))
    # รันแอปโดยฟังที่ 0.0.0.0 และพอร์ตที่ถูกกำหนดโดย Render
    app.run(host="0.0.0.0", port=port, debug=True)