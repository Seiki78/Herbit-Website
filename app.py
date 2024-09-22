from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient

app = Flask(__name__)

# เชื่อมต่อกับ MongoDB Atlas
client = MongoClient("mongodb+srv://mongodb:mg12345678@cluster0.fvpxm.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client['herb']
collection = db['herbals_info']

@app.route('/')
def index():
    herbals_info = collection.find()  # ดึงข้อมูลผู้ใช้ทั้งหมดจาก MongoDB
    return render_template('general_pretest.html', herbals_info=herbals_info)

@app.route('/add', methods=['POST'])
def add_user():
    h_name = request.form['h_name']
    
    # เพิ่มข้อมูลใหม่ลงใน MongoDB
    collection.insert_one({'h_name': h_name})
    
    flash('Herbal added successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
