import datetime
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
trains_collection = db['trains']
herbals_data_collection = db['herbals_data']
medicines_data_collection = db['medicines_data']
allergys_data_collection = db['allergys_data']
chronics_data_collection = db['chronics_data']
symptoms_data_collection = db['symptoms_data']
warnings_data_collection = db['warnings_data']

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

def calculateAge(date_of_birth):
    # แปลงวันที่เกิดจาก string เป็น object ของ datetime
    date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    return age

@app.route('/')
def index():
    # ดึงข้อมูลผู้ใช้ทั้งหมดจาก Collection
    users = users_collection.find()  # `find()` จะดึงเอกสารทั้งหมด
    user_count = users_collection.count_documents({})  # ใช้ count_documents เพื่อนับจำนวนเอกสารใน Collection
    return render_template('index.html', users=users, user_count=user_count)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
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

# @app.route('/add_user', methods=['POST'])
# def add_user():
#     username = request.form['username']
#     email = request.form['email']
#     password = request.form['password']

#     # แฮชรหัสผ่าน และให้ผลลัพธ์เป็น string
#     hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
#     # เพิ่มข้อมูลใหม่ลงใน MongoDB
#     users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password, 'role': 'member'})
    
#     flash('เพิ่มผู้ใช้สำเร็จ!', 'success')
#     return redirect(url_for('index'))

@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # แฮชรหัสผ่าน และให้ผลลัพธ์เป็น string
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # เพิ่มข้อมูลใหม่ลงใน MongoDB
        users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password, 'role': 'member'})

        flash('สมัครสมาชิกสำเร็จ!', 'success')
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

@app.route('/manage_trains')
def manage_trains():

    page = request.args.get('page', 1, type=int)  # รับค่าหน้าจาก URL หรือกำหนดเป็นหน้า 1 ถ้าไม่มีการส่งมา
    per_page = 25  # กำหนดจำนวนข้อมูลต่อหน้า
    trains_count = trains_collection.count_documents({})  # นับจำนวนเอกสารทั้งหมด
    total_pages = (trains_count + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด

    # ดึงข้อมูลจาก MongoDB โดยใช้ skip และ limit เพื่อแบ่งข้อมูลตามหน้า
    trains = trains_collection.find().skip((page - 1) * per_page).limit(per_page)

    # ดึงข้อมูล collection herbals_data
    herbals = herbals_data_collection.find()

    return render_template('manage_trains.html', trains=trains, page=page, total_pages=total_pages, herbals=herbals)

@app.route('/add_trains', methods=['POST'])
def add_trains():

    Age = request.form.get('Age')
    pregnant = request.form.get('pregnant')
    dizziness1 = request.form.get('dizziness1')
    Palpitations = request.form.get('Palpitations')
    squeamish = request.form.get('squeamish')
    vomit = request.form.get('vomit')
    dizziness2 = request.form.get('dizziness2')
    dizziness3 = request.form.get('dizziness3')
    dizziness4 = request.form.get('dizziness4')
    colic1 = request.form.get('colic1')
    tired = request.form.get('tired')
    cannot_sleep = request.form.get('cannot_sleep')
    flatulence = request.form.get('flatulence')
    stomach_ache = request.form.get('stomach_ache')
    constipation1 = request.form.get('constipation1')
    diarrhea1 = request.form.get('diarrhea1')
    hemorrhoids = request.form.get('hemorrhoids')
    menstruation = request.form.get('menstruation')
    Menstrual_cramps = request.form.get('Menstrual_cramps')
    postpartum_woman = request.form.get('postpartum_woman')
    Lochia = request.form.get('Lochia')
    Vaginal_Discharge = request.form.get('Vaginal_Discharge')
    Nourish_blood = request.form.get('Nourish_blood')
    fever1 = request.form.get('fever1')
    inner_heat = request.form.get('inner_heat')
    Measles = request.form.get('Measles')
    Chickenpox = request.form.get('Chickenpox')
    fever2 = request.form.get('fever2')
    fever3 = request.form.get('fever3')
    cough = request.form.get('cough')
    phlegm = request.form.get('phlegm')
    cold = request.form.get('cold')
    Allergic_Rhinitis = request.form.get('Allergic_Rhinitis')
    body_aches = request.form.get('body_aches')
    tendon = request.form.get('tendon')
    Tight_numb = request.form.get('Tight_numb')
    muscles_tendons = request.form.get('muscles_tendons')
    dizziness5 = request.form.get('dizziness5')
    hm_id = request.form.get('hm_id')  # hm_id ที่เลือกจาก select

    # ถ้าไม่เลือก checkbox ให้ตั้งค่าเป็น 0
    pregnant = 0 if pregnant is None else 1
    dizziness1 = 0 if dizziness1 is None else 1
    Palpitations = 0 if Palpitations is None else 1
    squeamish = 0 if squeamish is None else 1
    vomit = 0 if vomit is None else 1
    dizziness2 = 0 if dizziness2 is None else 1
    dizziness3 = 0 if dizziness3 is None else 1
    dizziness4 = 0 if dizziness4 is None else 1
    colic1 = 0 if colic1 is None else 1
    tired = 0 if tired is None else 1
    cannot_sleep = 0 if cannot_sleep is None else 1
    flatulence = 0 if flatulence is None else 1
    stomach_ache = 0 if stomach_ache is None else 1
    constipation1 = 0 if constipation1 is None else 1
    diarrhea1 = 0 if diarrhea1 is None else 1
    hemorrhoids = 0 if hemorrhoids is None else 1
    menstruation = 0 if menstruation is None else 1
    Menstrual_cramps = 0 if Menstrual_cramps is None else 1
    postpartum_woman = 0 if postpartum_woman is None else 1
    Lochia = 0 if Lochia is None else 1
    Vaginal_Discharge = 0 if Vaginal_Discharge is None else 1
    Nourish_blood = 0 if Nourish_blood is None else 1
    fever1 = 0 if fever1 is None else 1
    inner_heat = 0 if inner_heat is None else 1
    Measles = 0 if Measles is None else 1
    Chickenpox = 0 if Chickenpox is None else 1
    fever2 = 0 if fever2 is None else 1
    fever3 = 0 if fever3 is None else 1
    cough = 0 if cough is None else 1
    phlegm = 0 if phlegm is None else 1
    cold = 0 if cold is None else 1
    Allergic_Rhinitis = 0 if Allergic_Rhinitis is None else 1
    body_aches = 0 if body_aches is None else 1
    tendon = 0 if tendon is None else 1
    Tight_numb = 0 if Tight_numb is None else 1
    muscles_tendons = 0 if muscles_tendons is None else 1
    dizziness5 = 0 if dizziness5 is None else 1

    # เพิ่มข้อมูลใหม่ลงใน Collection trains
    trains_collection.insert_one({
        'Age': Age,
        'pregnant': pregnant,
        'dizziness1': dizziness1,
        'Palpitations': Palpitations,
        'squeamish': squeamish,
        'vomit': vomit,
        'dizziness2': dizziness2,
        'dizziness3': dizziness3,
        'dizziness4': dizziness4,
        'colic1': colic1,
        'tired': tired,
        'cannot_sleep': cannot_sleep,
        'flatulence': flatulence,
        'stomach_ache': stomach_ache,
        'constipation1': constipation1,
        'diarrhea1': diarrhea1,
        'hemorrhoids': hemorrhoids,
        'menstruation': menstruation,
        'Menstrual_cramps': Menstrual_cramps,
        'postpartum_woman': postpartum_woman,
        'Lochia': Lochia,
        'Vaginal_Discharge': Vaginal_Discharge,
        'Nourish_blood': Nourish_blood,
        'fever1': fever1,
        'inner_heat': inner_heat,
        'Measles': Measles,
        'Chickenpox': Chickenpox,
        'fever2': fever2,
        'fever3': fever3,
        'cough': cough,
        'phlegm': phlegm,
        'cold': cold,
        'Allergic_Rhinitis': Allergic_Rhinitis,
        'body_aches': body_aches,
        'tendon': tendon,
        'Tight_numb': Tight_numb,
        'muscles_tendons': muscles_tendons,
        'dizziness5': dizziness5,
        'hm_id': hm_id  # hm_id ที่ได้จาก select
    })

    # ดึงข้อมูล collection herbals_data
    herbals = herbals_data_collection.find()
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_trains', herbals=herbals))

@app.route('/delete_trains/<train_id>', methods=['POST'])
def delete_trains(train_id):
    # ลบข้อมูลโรคออกจาก MongoDB โดยใช้ ObjectId
    trains_collection.delete_one({'_id': ObjectId(train_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_trains'))

@app.route('/edit_trains/<train_id>', methods=['GET', 'POST'])
def edit_trains(train_id):
    if request.method == 'POST':
        Age = request.form['Age']
        pregnant = 1 if request.form.get('pregnant') else 0
        dizziness1 = 1 if request.form.get('dizziness1') else 0
        Palpitations = 1 if request.form.get('Palpitations') else 0
        squeamish = 1 if request.form.get('squeamish') else 0
        vomit = 1 if request.form.get('vomit') else 0
        dizziness2 = 1 if request.form.get('dizziness2') else 0
        dizziness3 = 1 if request.form.get('dizziness3') else 0
        dizziness4 = 1 if request.form.get('dizziness4') else 0
        colic1 = 1 if request.form.get('colic1') else 0
        tired = 1 if request.form.get('tired') else 0
        cannot_sleep = 1 if request.form.get('cannot_sleep') else 0
        flatulence = 1 if request.form.get('flatulence') else 0
        stomach_ache = 1 if request.form.get('stomach_ache') else 0
        constipation1 = 1 if request.form.get('constipation1') else 0
        diarrhea1 = 1 if request.form.get('diarrhea1') else 0
        hemorrhoids = 1 if request.form.get('hemorrhoids') else 0
        menstruation = 1 if request.form.get('menstruation') else 0
        Menstrual_cramps = 1 if request.form.get('Menstrual_cramps') else 0
        postpartum_woman = 1 if request.form.get('postpartum_woman') else 0
        Lochia = 1 if request.form.get('Lochia') else 0
        Vaginal_Discharge = 1 if request.form.get('Vaginal_Discharge') else 0
        Nourish_blood = 1 if request.form.get('Nourish_blood') else 0
        fever1 = 1 if request.form.get('fever1') else 0
        inner_heat = 1 if request.form.get('inner_heat') else 0
        Measles = 1 if request.form.get('Measles') else 0
        Chickenpox = 1 if request.form.get('Chickenpox') else 0
        fever2 = 1 if request.form.get('fever2') else 0
        fever3 = 1 if request.form.get('fever3') else 0
        cough = 1 if request.form.get('cough') else 0
        phlegm = 1 if request.form.get('phlegm') else 0
        cold = 1 if request.form.get('cold') else 0
        Allergic_Rhinitis = 1 if request.form.get('Allergic_Rhinitis') else 0
        body_aches = 1 if request.form.get('body_aches') else 0
        tendon = 1 if request.form.get('tendon') else 0
        Tight_numb = 1 if request.form.get('Tight_numb') else 0
        muscles_tendons = 1 if request.form.get('muscles_tendons') else 0
        dizziness5 = 1 if request.form.get('dizziness5') else 0
        
        # อัปเดตข้อมูลทุกอย่างใน MongoDB
        trains_collection.update_one({'_id': ObjectId(train_id)}, {'$set': {'Age': Age, 'pregnant': pregnant, 'dizziness1': dizziness1, 'Palpitations': Palpitations,
                                                                            'squeamish': squeamish, 'vomit': vomit, 'dizziness2': dizziness2, 'dizziness3': dizziness3,
                                                                            'dizziness4': dizziness4, 'colic1': colic1, 'tired': tired, 'cannot_sleep': cannot_sleep,
                                                                            'flatulence': flatulence, 'stomach_ache': stomach_ache, 'constipation1': constipation1,
                                                                            'diarrhea1': diarrhea1, 'hemorrhoids': hemorrhoids, 'menstruation': menstruation,
                                                                            'Menstrual_cramps': Menstrual_cramps, 'postpartum_woman': postpartum_woman, 'Lochia': Lochia,
                                                                            'Vaginal_Discharge': Vaginal_Discharge, 'Nourish_blood': Nourish_blood, 'fever1': fever1,
                                                                            'inner_heat': inner_heat, 'Measles': Measles, 'Chickenpox': Chickenpox, 'fever2': fever2,
                                                                            'fever3': fever3, 'cough': cough, 'phlegm': phlegm, 'cold': cold, 'Allergic_Rhinitis': Allergic_Rhinitis,
                                                                            'body_aches': body_aches, 'tendon': tendon, 'Tight_numb': Tight_numb, 'muscles_tendons': muscles_tendons,
                                                                             'dizziness5': dizziness5}})
        
        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_trains'))
    
    # ดึงข้อมูล trains ที่ต้องการแก้ไข
    train = trains_collection.find_one({'_id': ObjectId(train_id)})

    # ดึง hm_id จาก train นั้นๆ และหา herbal ที่เกี่ยวข้อง
    selected_herbal = herbals_data_collection.find_one({'hm_id': int(train['hm_id'])})
    
    return render_template('edit_trains.html', train=train, selected_herbal=selected_herbal)

@app.route('/manage_members')
def manage_members():

    # ดึงข้อมูลทั้งหมดจาก Collection
    users = list(users_collection.find())

    return render_template('manage_members.html', users=users)

@app.route('/delete_member/<user_id>', methods=['POST'])
def delete_member(user_id):
    # ลบข้อมูลยาสมุนไพรออกจาก MongoDB โดยใช้ ObjectId
    users_collection.delete_one({'_id': ObjectId(user_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_members'))

@app.route('/manage_herbals')
def manage_herbals():

    page = request.args.get('page', 1, type=int)  # รับค่าหน้าจาก URL หรือกำหนดเป็นหน้า 1 ถ้าไม่มีการส่งมา
    per_page = 25  # กำหนดจำนวนข้อมูลต่อหน้า
    herbals_count = herbals_data_collection.count_documents({})  # นับจำนวนเอกสารทั้งหมด
    total_pages = (herbals_count + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด

    # ดึงข้อมูลจาก MongoDB โดยใช้ skip และ limit เพื่อแบ่งข้อมูลตามหน้า
    herbals = herbals_data_collection.find().skip((page - 1) * per_page).limit(per_page)

    # ดึงข้อมูล collection herbals_data
    warnings = warnings_data_collection.find()


    return render_template('manage_herbals.html', herbals=herbals, page=page, total_pages=total_pages, warnings=warnings)

@app.route('/add_herbal', methods=['POST'])
def add_herbal():

    # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
    last_herbal = herbals_data_collection.find_one(sort=[("hm_id", -1)])
    
    # ถ้ามีเอกสารอยู่ ให้เอา hm_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 301
    if last_herbal:
        hm_id = last_herbal['hm_id'] + 1
    else:
        hm_id = 301  # กำหนดค่าเริ่มต้นเป็น 301 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
    hm_name = request.form['hm_name']
    hm_dosage = request.form['hm_dosage']
    hm_recipe  = request.form['hm_recipe']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection chronic
    herbals_data_collection.insert_one({'hm_id': hm_id, 'hm_name': hm_name, 'hm_dosage': hm_dosage, 'hm_recipe': hm_recipe})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_herbals'))

@app.route('/delete_herbal/<herbal_id>', methods=['POST'])
def delete_herbal(herbal_id):
    # ลบข้อมูลยาสมุนไพรออกจาก MongoDB โดยใช้ ObjectId
    herbals_data_collection.delete_one({'_id': ObjectId(herbal_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_herbals'))

@app.route('/edit_herbal/<herbal_id>', methods=['GET', 'POST'])
def edit_herbal(herbal_id):
    if request.method == 'POST':
        # รับข้อมูลใหม่จากฟอร์ม
        hm_name = request.form['hm_name']
        hm_dosage = request.form['hm_dosage']
        hm_recipe  = request.form['hm_recipe']
        
        # อัปเดตข้อมูลใน MongoDB
        herbals_data_collection.update_one({'_id': ObjectId(herbal_id)}, {'$set': {'hm_name': hm_name, 'hm_dosage': hm_dosage, 'hm_recipe': hm_recipe}})
        
        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_herbals'))
    
    # ดึงข้อมูลที่ต้องการแก้ไขเพื่อแสดงในฟอร์ม
    herbal = herbals_data_collection.find_one({'_id': ObjectId(herbal_id)})

    return render_template('edit_herbals.html', herbal=herbal)

@app.route('/manage_medicines')
def manage_medicines():

    page = request.args.get('page', 1, type=int)  # รับค่าหน้าจาก URL หรือกำหนดเป็นหน้า 1 ถ้าไม่มีการส่งมา
    per_page = 25  # กำหนดจำนวนข้อมูลต่อหน้า
    medicines_count = medicines_data_collection.count_documents({})  # นับจำนวนเอกสารทั้งหมด
    total_pages = (medicines_count + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด

    # ดึงข้อมูลจาก MongoDB โดยใช้ skip และ limit เพื่อแบ่งข้อมูลตามหน้า
    medicines = medicines_data_collection.find().skip((page - 1) * per_page).limit(per_page)

    return render_template('manage_medicines.html', medicines=medicines, page=page, total_pages=total_pages)

@app.route('/add_medicine', methods=['POST'])
def add_medicine():

    # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
    last_medicine = medicines_data_collection.find_one(sort=[("md_id", -1)])
    
    # ถ้ามีเอกสารอยู่ ให้เอา md_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 401
    if last_medicine:
        md_id = last_medicine['md_id'] + 1
    else:
        md_id = 401  # กำหนดค่าเริ่มต้นเป็น 401 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
    md_nameEN = request.form['md_nameEN']
    md_nameTH = request.form['md_nameTH']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection medicine
    medicines_data_collection.insert_one({'md_id': md_id, 'md_nameEN': md_nameEN, 'md_nameTH': md_nameTH})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_medicines'))

@app.route('/delete_medicine/<medicine_id>', methods=['POST'])
def delete_medicine(medicine_id):
    # ลบข้อมูลยาสมุนไพรออกจาก MongoDB โดยใช้ ObjectId
    medicines_data_collection.delete_one({'_id': ObjectId(medicine_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_medicines'))

@app.route('/manage_allergys')
def manage_allergys():

    page = request.args.get('page', 1, type=int)  # รับค่าหน้าจาก URL หรือกำหนดเป็นหน้า 1 ถ้าไม่มีการส่งมา
    per_page = 25  # กำหนดจำนวนข้อมูลต่อหน้า
    allergys_count = allergys_data_collection.count_documents({})  # นับจำนวนเอกสารทั้งหมด
    total_pages = (allergys_count + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด

    # ดึงข้อมูลจาก MongoDB โดยใช้ skip และ limit เพื่อแบ่งข้อมูลตามหน้า
    allergys = allergys_data_collection.find().skip((page - 1) * per_page).limit(per_page)

    return render_template('manage_allergys.html', allergys=allergys, page=page, total_pages=total_pages)

@app.route('/add_allergy', methods=['POST'])
def add_allergy():

    # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
    last_allergy = allergys_data_collection.find_one(sort=[("ag_id", -1)])
    
    # ถ้ามีเอกสารอยู่ ให้เอา ag_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 601
    if last_allergy:
        ag_id = last_allergy['ag_id'] + 1
    else:
        ag_id = 601  # กำหนดค่าเริ่มต้นเป็น 601 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
    ag_name = request.form['ag_name']
    ag_detail = request.form['ag_detail']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection allergy
    allergys_data_collection.insert_one({'ag_id': ag_id, 'ag_name': ag_name, 'ag_detail': ag_detail})

    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_allergys'))

@app.route('/delete_allergy/<allergy_id>', methods=['POST'])
def delete_allergy(allergy_id):
    # ลบข้อมูลยาสมุนไพรออกจาก MongoDB โดยใช้ ObjectId
    allergys_data_collection.delete_one({'_id': ObjectId(allergy_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_allergys'))

@app.route('/manage_chrosymps')
def manage_chrosymps():

    # ดึงข้อมูลทั้งหมดจาก Collection
    chronics = chronics_data_collection.find()
    symptoms = symptoms_data_collection.find()

    return render_template('manage_chrosymps.html', chronics=chronics, symptoms=symptoms)

@app.route('/add_chronic', methods=['POST'])
def add_chronic():

    # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
    last_chronic = chronics_data_collection.find_one(sort=[("cn_id", -1)])
    
    # ถ้ามีเอกสารอยู่ ให้เอา cn_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 101
    if last_chronic:
        cn_id = last_chronic['cn_id'] + 1
    else:
        cn_id = 101  # กำหนดค่าเริ่มต้นเป็น 101 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
    cn_name = request.form['cn_name']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection chronic
    chronics_data_collection.insert_one({'cn_id': cn_id, 'cn_name': cn_name})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_chrosymps'))

@app.route('/delete_chronic/<chronic_id>', methods=['POST'])
def delete_chronic(chronic_id):
    # ลบข้อมูลโรคออกจาก MongoDB โดยใช้ ObjectId
    chronics_data_collection.delete_one({'_id': ObjectId(chronic_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_chrosymps'))

# @app.route('/edit_chronic/<chronic_id>', methods=['GET', 'POST'])
# def edit_chronic(chronic_id):
#     if request.method == 'POST':
#         cn_n = request.form['cn_n']
        
#         # อัปเดตเฉพาะชื่อโรคใน MongoDB
#         chronics_data_collection.update_one({'_id': ObjectId(chronic_id)}, {'$set': {'cn_n': cn_n}})
        
#         flash('อัปเดตข้อมูลสำเร็จ!', 'success')
#         return redirect(url_for('manage_chronics'))
    
#     # ดึงข้อมูลโรคที่ต้องการแก้ไข
#     chronic = chronics_data_collection.find_one({'_id': ObjectId(chronic_id)})
#     return render_template('edit_chronics.html', chronic=chronic)

# @app.route('/manage_symptoms')
# def manage_symptoms():

#     # ดึงข้อมูลทั้งหมดจาก Collection
#     symptoms = symptoms_data_collection.find()  # `find()` จะดึงเอกสารทั้งหมด

#     return render_template('manage_chrosymps.html', symptoms=symptoms)

@app.route('/add_symptom', methods=['POST'])
def add_symptom():

    # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี st_id มากที่สุด
    last_symptom = symptoms_data_collection.find_one(sort=[("st_id", -1)])
    
    # ถ้ามีเอกสารอยู่ ให้เอา st_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 501
    if last_symptom:
        st_id = last_symptom['st_id'] + 1
    else:
        st_id = 501  # กำหนดค่าเริ่มต้นเป็น 501 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
    st_name = request.form['st_name']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection chronic
    symptoms_data_collection.insert_one({'st_id': st_id, 'st_name': st_name})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_chrosymps'))

@app.route('/delete_symptom/<symptom_id>', methods=['POST'])
def delete_symptom(symptom_id):
    # ลบข้อมูลโรคออกจาก MongoDB โดยใช้ ObjectId
    symptoms_data_collection.delete_one({'_id': ObjectId(symptom_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_chrosymps'))

@app.route('/manage_warnings')
def manage_warnings():

    page = request.args.get('page', 1, type=int)  # รับค่าหน้าจาก URL หรือกำหนดเป็นหน้า 1 ถ้าไม่มีการส่งมา
    per_page = 25  # กำหนดจำนวนข้อมูลต่อหน้า
    warnings_count = warnings_data_collection.count_documents({})  # นับจำนวนเอกสารทั้งหมด
    total_pages = (warnings_count + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด

    # ดึงข้อมูลจาก MongoDB โดยใช้ skip และ limit เพื่อแบ่งข้อมูลตามหน้า
    warnings = warnings_data_collection.find().skip((page - 1) * per_page).limit(per_page)

    return render_template('manage_warnings.html', warnings=warnings, page=page, total_pages=total_pages)

@app.route('/delete_warning/<warning_id>', methods=['POST'])
def delete_warning(warning_id):
    # ลบข้อมูลคำเตือนออกจาก MongoDB โดยใช้ ObjectId
    warnings_data_collection.delete_one({'_id': ObjectId(warning_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_warnings'))

@app.route('/add_warning', methods=['POST'])
def add_warning():

    # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
    last_warning = warnings_data_collection.find_one(sort=[("wn_id", -1)])
    
    # ถ้ามีเอกสารอยู่ ให้เอา cn_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 701
    if last_warning:
        wn_id = last_warning['wn_id'] + 1
    else:
        wn_id = 701  # กำหนดค่าเริ่มต้นเป็น 701 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
    wn_name = request.form['wn_name']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection warnings
    warnings_data_collection.insert_one({'wn_id': wn_id, 'wn_name': wn_name})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_chrosymps'))

# @app.route('/general_predict', methods=['POST'])
# def general_predict():

#     Age = request.form.get('Age')
#     pregnant = request.form.get('pregnant')
#     dizziness1 = request.form.get('dizziness1')
#     Palpitations = request.form.get('Palpitations')
#     squeamish = request.form.get('squeamish')
#     vomit = request.form.get('vomit')
#     dizziness2 = request.form.get('dizziness2')
#     dizziness3 = request.form.get('dizziness3')
#     dizziness4 = request.form.get('dizziness4')
#     colic1 = request.form.get('colic1')
#     tired = request.form.get('tired')
#     cannot_sleep = request.form.get('cannot_sleep')
#     flatulence = request.form.get('flatulence')
#     stomach_ache = request.form.get('stomach_ache')
#     constipation1 = request.form.get('constipation1')
#     diarrhea1 = request.form.get('diarrhea1')
#     hemorrhoids = request.form.get('hemorrhoids')
#     menstruation = request.form.get('menstruation')
#     Menstrual_cramps = request.form.get('Menstrual_cramps')
#     postpartum_woman = request.form.get('postpartum_woman')
#     Lochia = request.form.get('Lochia')
#     Vaginal_Discharge = request.form.get('Vaginal_Discharge')
#     Nourish_blood = request.form.get('Nourish_blood')
#     fever1 = request.form.get('fever1')
#     inner_heat = request.form.get('inner_heat')
#     Measles = request.form.get('Measles')
#     Chickenpox = request.form.get('Chickenpox')
#     fever2 = request.form.get('fever2')
#     fever3 = request.form.get('fever3')
#     cough = request.form.get('cough')
#     phlegm = request.form.get('phlegm')
#     cold = request.form.get('cold')
#     Allergic_Rhinitis = request.form.get('Allergic_Rhinitis')
#     body_aches = request.form.get('body_aches')
#     tendon = request.form.get('tendon')
#     Tight_numb = request.form.get('Tight_numb')
#     muscles_tendons = request.form.get('muscles_tendons')
#     dizziness5 = request.form.get('dizziness5')

#     # ถ้าไม่เลือก checkbox ให้ตั้งค่าเป็น 0
#     pregnant = 0 if pregnant is None else 1
#     dizziness1 = 0 if dizziness1 is None else 1
#     Palpitations = 0 if Palpitations is None else 1
#     squeamish = 0 if squeamish is None else 1
#     vomit = 0 if vomit is None else 1
#     dizziness2 = 0 if dizziness2 is None else 1
#     dizziness3 = 0 if dizziness3 is None else 1
#     dizziness4 = 0 if dizziness4 is None else 1
#     colic1 = 0 if colic1 is None else 1
#     tired = 0 if tired is None else 1
#     cannot_sleep = 0 if cannot_sleep is None else 1
#     flatulence = 0 if flatulence is None else 1
#     stomach_ache = 0 if stomach_ache is None else 1
#     constipation1 = 0 if constipation1 is None else 1
#     diarrhea1 = 0 if diarrhea1 is None else 1
#     hemorrhoids = 0 if hemorrhoids is None else 1
#     menstruation = 0 if menstruation is None else 1
#     Menstrual_cramps = 0 if Menstrual_cramps is None else 1
#     postpartum_woman = 0 if postpartum_woman is None else 1
#     Lochia = 0 if Lochia is None else 1
#     Vaginal_Discharge = 0 if Vaginal_Discharge is None else 1
#     Nourish_blood = 0 if Nourish_blood is None else 1
#     fever1 = 0 if fever1 is None else 1
#     inner_heat = 0 if inner_heat is None else 1
#     Measles = 0 if Measles is None else 1
#     Chickenpox = 0 if Chickenpox is None else 1
#     fever2 = 0 if fever2 is None else 1
#     fever3 = 0 if fever3 is None else 1
#     cough = 0 if cough is None else 1
#     phlegm = 0 if phlegm is None else 1
#     cold = 0 if cold is None else 1
#     Allergic_Rhinitis = 0 if Allergic_Rhinitis is None else 1
#     body_aches = 0 if body_aches is None else 1
#     tendon = 0 if tendon is None else 1
#     Tight_numb = 0 if Tight_numb is None else 1
#     muscles_tendons = 0 if muscles_tendons is None else 1
#     dizziness5 = 0 if dizziness5 is None else 1


#     input_data = db.DataFrame({
#         'Age': Age,
#         'pregnant': pregnant,
#         'dizziness1': dizziness1,
#         'Palpitations': Palpitations,
#         'squeamish': squeamish,
#         'vomit': vomit,
#         'dizziness2': dizziness2,
#         'dizziness3': dizziness3,
#         'dizziness4': dizziness4,
#         'colic1': colic1,
#         'tired': tired,
#         'cannot_sleep': cannot_sleep,
#         'flatulence': flatulence,
#         'stomach_ache': stomach_ache,
#         'constipation1': constipation1,
#         'diarrhea1': diarrhea1,
#         'hemorrhoids': hemorrhoids,
#         'menstruation': menstruation,
#         'Menstrual_cramps': Menstrual_cramps,
#         'postpartum_woman': postpartum_woman,
#         'Lochia': Lochia,
#         'Vaginal_Discharge': Vaginal_Discharge,
#         'Nourish_blood': Nourish_blood,
#         'fever1': fever1,
#         'inner_heat': inner_heat,
#         'Measles': Measles,
#         'Chickenpox': Chickenpox,
#         'fever2': fever2,
#         'fever3': fever3,
#         'cough': cough,
#         'phlegm': phlegm,
#         'cold': cold,
#         'Allergic_Rhinitis': Allergic_Rhinitis,
#         'body_aches': body_aches,
#         'tendon': tendon,
#         'Tight_numb': Tight_numb,
#         'muscles_tendons': muscles_tendons,
#         'dizziness5': dizziness5,
#     })

#     class_names=[str(i) for i in y_train.unique()]

#     dot_data = StringIO()
#     export_graphviz(clf.estimators_[0], out_file=dot_data, filled=True, rounded=True, special_characters=True, feature_names=feature_cols, class_names=class_names)
#     graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
#     graph.write_png('random_forest_tree_pre_00.png')
#     Image(graph.create_png())

#     try:
#         print(input_data)
        
#         # ทำนายความน่าจะเป็นของทุกคลาส
#         probabilities = clf.predict_proba(input_data)[0]

#         for i, prob in enumerate(probabilities):
#             h_id = clf.classes_[i]
#             print(f"ผลการทำนายก่อนเข้าเงื่อนไขตรวจสอบ คลาส: {h_id}, ความน่าจะเป็น: {prob}")

#         # เรียกใช้ฟังก์ชัน check_conditions
#         new_probabilities = check_conditions(probabilities, pregnant, Age, fever1, squeamish, vomit)

#         print("ผลการทำนายหลังเข้าเงื่อนไขตรวจสอบ: ", new_probabilities)

#         # จัดเรียง index จากความน่าจะเป็นที่มากไปน้อย
#         sorted_indices = np.argsort(-new_probabilities)

#         # สร้าง list ที่จะถูกส่งไปที่ template
#         data_to_template = []

#         added_h_ids = set()  # ใช้ set นี้เพื่อตรวจสอบว่า h_id ใด ๆ ถูกเพิ่มแล้ว
        
#         # เพิ่มข้อมูลที่ต้องการแสดงใน template 
#         for index in sorted_indices:
#             prob = new_probabilities[index]
#             h_id = clf.classes_[index]
#             if hm_id not in added_h_ids and prob > 0.0 :  # ตรวจสอบว่า h_id นี้ยังไม่ได้ถูกเพิ่ม # เช็คว่าความน่าจะเป็นมากกว่า 0
#                 hm_name = get_hm_name(h_id)
#                 wn_name = get_wn_name(h_id)
#                 hm_dosage = get_hm_dosage(h_id)

#             # สร้าง dictionary ใหม่สำหรับ class นี้ ในแต่ละรอบของ loop
#             class_data = {
#                 "class": h_id,
#                 "probability": prob,
#                 "hm_name": hm_name,
#                 "wn_name": wn_name,
#                 "hm_dosage": hm_dosage,
#             }

#             # เพิ่ม class_data ลงใน data_to_template
#             data_to_template.append(class_data)

#             # เพิ่ม h_id นี้ลงใน set
#             added_h_ids.add(h_id)
        
#         # ดึงข้อมูล Chronic
#         chronics = chronics_data_collection.find()

#         # ดึงข้อมูล Allergies
        
#         allergys = allergys_data_collection.find()

#     except Exception as e:
#         print(f"เกิดข้อผิดพลาด: {e}")

#     return render_template("general_predict.html", prediction=class_data['hm_name'], probabilities=data_to_template, chronics=chronics, allergys=allergys)


if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)