import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)

app.secret_key = os.urandom(24)

# เชื่อมต่อกับ MongoDB Atlas
client = MongoClient("mongodb+srv://mongodb:mg12345678@cluster0.fvpxm.mongodb.net/nobita_database?retryWrites=true&w=majority")
db = client['nobita_database']
users_collection = db['users']
chronics_data_collection = db['chronics_data']

# ตั้งค่า Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'  # เส้นทางสำหรับหน้าlogin พอเด้งไป index จะเปิดpop login ขึ้นมาเลย #เซ็ต alert ไว้แล้ว

# โมเดลผู้ใช้ โดยใช้ UserMixin
class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

# โหลดผู้ใช้จาก session
@login_manager.user_loader
def load_user(user_id):
    users = users_collection.find_one({'_id': ObjectId(user_id)})
    if users:
        return User(user_id=users['_id'], username=users['username'], role=users['role'])
    return None

@app.route('/')
def index():
    # ดึงข้อมูลผู้ใช้ทั้งหมดจาก Collection
    users = users_collection.find()  # `find()` จะดึงเอกสารทั้งหมด
    user_count = users_collection.count_documents({})  # ใช้ count_documents เพื่อนับจำนวนเอกสารใน Collection
    return render_template('index.html', users=users, user_count=user_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ดึงข้อมูลผู้ใช้จาก MongoDB โดยใช้ username
        users = users_collection.find_one({'username': username})
        
        if users and check_password_hash(users['password'], password):
            # สร้างอ็อบเจกต์ User จากคลาส UserMixin
            user_obj = User(user_id=users['_id'], username=users['username'], role=users['role'])
            login_user(user_obj)  # ล็อกอินผู้ใช้

            flash('เข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger')
            return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # ตรวจสอบบทบาทของผู้ใช้ผ่าน current_user | current_user คือ object ของผู้ใช้ที่ login อยู่ /มาจาก object ของ UserMixin
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'member':
        return render_template('member_dashboard.html')
    else:
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()  # ออกจากระบบผู้ใช้
    flash('ออกจากระบบสำเร็จ', 'success')
    return redirect(url_for('index'))

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    # แฮชรหัสผ่าน และให้ผลลัพธ์เป็น string
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    # เพิ่มข้อมูลใหม่ลงใน MongoDB
    users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password, 'role': 'member'})
    
    flash('เพิ่มผู้ใช้สำเร็จ!', 'success')
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

@app.route('/manage_chronics')
def manage_chronics():

    # ดึงข้อมูลทั้งหมดจาก Collection
    chronics = chronics_data_collection.find()  # `find()` จะดึงเอกสารทั้งหมด

    return render_template('manage_chronics.html', chronics=chronics)

@app.route('/add_chronic', methods=['POST'])
def add_chronic():

    # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
    last_chronic = chronics_data_collection.find_one(sort=[("cn_id", -1)])
    
    # ถ้ามีเอกสารอยู่ ให้เอา cn_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 101
    if last_chronic:
        cn_id = last_chronic['cn_id'] + 1
    else:
        cn_id = 101  # กำหนดค่าเริ่มต้นเป็น 101 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
    cn_n = request.form['cn_n']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection chronic
    chronics_data_collection.insert_one({'cn_id': cn_id, 'cn_n': cn_n})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_chronics'))

@app.route('/delete_chronic/<chronic_id>', methods=['POST'])
def delete_chronic(chronic_id):
    # ลบข้อมูลโรคออกจาก MongoDB โดยใช้ ObjectId
    chronics_data_collection.delete_one({'_id': ObjectId(chronic_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_chronics'))

@app.route('/edit_chronic/<chronic_id>', methods=['GET', 'POST'])
def edit_chronic(chronic_id):
    if request.method == 'POST':
        cn_n = request.form['cn_n']
        
        # อัปเดตเฉพาะชื่อโรคใน MongoDB
        chronics_data_collection.update_one({'_id': ObjectId(chronic_id)}, {'$set': {'cn_n': cn_n}})
        
        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_chronics'))
    
    # ดึงข้อมูลโรคที่ต้องการแก้ไข
    chronic = chronics_data_collection.find_one({'_id': ObjectId(chronic_id)})
    return render_template('edit_chronics.html', chronic=chronic)


if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)