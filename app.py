from datetime import datetime
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
hm_wn_collection = db['hm_wn']
hm_st_collection = db['hm_st']
u_cn_collection = db['u_cn']
u_md_collection = db['u_md']
u_ag_collection = db['u_ag']

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

def get_breastfeeding_name(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user is not None:
        breastfeeding = user.get('breastfeeding')  # ดึงค่า breastfeeding จาก user
        if breastfeeding == 0:
            return '-'
        elif breastfeeding == 1:
            return 'ให้นมบุตร'
    
    return "(ไม่มีข้อมูล)"

def get_pregnant_name(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user is not None:
        pregnant = user.get('pregnant')  # ดึงค่า pregnant จาก user
        if pregnant == 0:
            return '-'
        elif pregnant == 1:
            return 'ตั้งครรภ์'
    
    return "(ไม่มีข้อมูล)"

def get_gender_name(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})  # ค้นหาจาก _id

    if user is not None:
        gender = user.get('gender')  # ดึงค่า gender จาก user ที่ได้มา
        if gender == 0:
            return 'ชาย'
        elif gender == 1:
            return 'หญิง'
    
    return "(ไม่มีข้อมูล)"

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
        # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
        last_user = users_collection.find_one(sort=[("u_id", -1)])
        
        # ถ้ามีเอกสารอยู่ ให้เอา u_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 201
        if last_user:
            u_id = last_user['u_id'] + 1
        else:
            u_id = 201  # กำหนดค่าเริ่มต้นเป็น 201 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']

        # แปลงวันเกิดเป็น datetime object
        dob_str = request.form['dob']
        dob = datetime.strptime(dob_str, '%Y-%m-%d')

        gender = int(request.form['gender'])
        pregnant = int(request.form.get('pregnant', 0)) # ถ้าไม่ส่งค่ามา กำหนดค่าเริ่มต้นเป็น 0
        breastfeeding = int(request.form.get('breastfeeding', 0))
        weight = int(request.form['weight'])
        height = int(request.form['height'])

        # แฮชรหัสผ่าน และให้ผลลัพธ์เป็น string
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # เพิ่มข้อมูลใหม่ลงใน MongoDB / role member
        users_collection.insert_one({'u_id': u_id, 'username': username, 'email': email, 'password': hashed_password, 'role': 'member',
                                     'fname': fname, 'lname': lname, 'dob': dob, 'gender': gender, 'pregnant': pregnant,
                                     'breastfeeding': breastfeeding, 'weight': weight, 'height': height})

        flash('สมัครสมาชิกสำเร็จ!', 'success')
        return redirect(url_for('index'))

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

    Age = int(request.form.get('Age'))
    pregnant = int(request.form.get('pregnant', 0))
    dizziness1 = int(request.form.get('dizziness1', 0))
    Palpitations = int(request.form.get('Palpitations', 0))
    squeamish = int(request.form.get('squeamish', 0))
    vomit = int(request.form.get('vomit', 0))
    dizziness2 = int(request.form.get('dizziness2', 0))
    dizziness3 = int(request.form.get('dizziness3', 0))
    dizziness4 = int(request.form.get('dizziness4', 0))
    colic1 = int(request.form.get('colic1', 0))
    tired = int(request.form.get('tired', 0))
    cannot_sleep = int(request.form.get('cannot_sleep', 0))
    flatulence = int(request.form.get('flatulence', 0))
    stomach_ache = int(request.form.get('stomach_ache', 0))
    constipation1 = int(request.form.get('constipation1', 0))
    diarrhea1 = int(request.form.get('diarrhea1', 0))
    hemorrhoids = int(request.form.get('hemorrhoids', 0))
    menstruation = int(request.form.get('menstruation', 0))
    Menstrual_cramps = int(request.form.get('Menstrual_cramps', 0))
    postpartum_woman = int(request.form.get('postpartum_woman', 0))
    Lochia = int(request.form.get('Lochia', 0))
    Vaginal_Discharge = int(request.form.get('Vaginal_Discharge', 0))
    Nourish_blood = int(request.form.get('Nourish_blood', 0))
    fever1 = int(request.form.get('fever1', 0))
    inner_heat = int(request.form.get('inner_heat', 0))
    Measles = int(request.form.get('Measles', 0))
    Chickenpox = int(request.form.get('Chickenpox', 0))
    fever2 = int(request.form.get('fever2', 0))
    fever3 = int(request.form.get('fever3', 0))
    cough = int(request.form.get('cough', 0))
    phlegm = int(request.form.get('phlegm', 0))
    cold = int(request.form.get('cold', 0))
    Allergic_Rhinitis = int(request.form.get('Allergic_Rhinitis', 0))
    body_aches = int(request.form.get('body_aches', 0))
    tendon = int(request.form.get('tendon', 0))
    Tight_numb = int(request.form.get('Tight_numb', 0))
    muscles_tendons = int(request.form.get('muscles_tendons', 0))
    dizziness5 = int(request.form.get('dizziness5', 0))
    hm_id = int(request.form.get('hm_id'))  # hm_id ที่เลือกจาก select

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
    # ลบข้อมูล train ออกจาก MongoDB โดยใช้ ObjectId
    trains_collection.delete_one({'_id': ObjectId(train_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_trains'))

@app.route('/edit_trains/<train_id>', methods=['GET', 'POST'])
def edit_trains(train_id):
    if request.method == 'POST':

        Age = int(request.form.get('Age'))
        pregnant = int(request.form.get('pregnant', 0))
        dizziness1 = int(request.form.get('dizziness1', 0))
        Palpitations = int(request.form.get('Palpitations', 0))
        squeamish = int(request.form.get('squeamish', 0))
        vomit = int(request.form.get('vomit', 0))
        dizziness2 = int(request.form.get('dizziness2', 0))
        dizziness3 = int(request.form.get('dizziness3', 0))
        dizziness4 = int(request.form.get('dizziness4', 0))
        colic1 = int(request.form.get('colic1', 0))
        tired = int(request.form.get('tired', 0))
        cannot_sleep = int(request.form.get('cannot_sleep', 0))
        flatulence = int(request.form.get('flatulence', 0))
        stomach_ache = int(request.form.get('stomach_ache', 0))
        constipation1 = int(request.form.get('constipation1', 0))
        diarrhea1 = int(request.form.get('diarrhea1', 0))
        hemorrhoids = int(request.form.get('hemorrhoids', 0))
        menstruation = int(request.form.get('menstruation', 0))
        Menstrual_cramps = int(request.form.get('Menstrual_cramps', 0))
        postpartum_woman = int(request.form.get('postpartum_woman', 0))
        Lochia = int(request.form.get('Lochia', 0))
        Vaginal_Discharge = int(request.form.get('Vaginal_Discharge', 0))
        Nourish_blood = int(request.form.get('Nourish_blood', 0))
        fever1 = int(request.form.get('fever1', 0))
        inner_heat = int(request.form.get('inner_heat', 0))
        Measles = int(request.form.get('Measles', 0))
        Chickenpox = int(request.form.get('Chickenpox', 0))
        fever2 = int(request.form.get('fever2', 0))
        fever3 = int(request.form.get('fever3', 0))
        cough = int(request.form.get('cough', 0))
        phlegm = int(request.form.get('phlegm', 0))
        cold = int(request.form.get('cold', 0))
        Allergic_Rhinitis = int(request.form.get('Allergic_Rhinitis', 0))
        body_aches = int(request.form.get('body_aches', 0))
        tendon = int(request.form.get('tendon', 0))
        Tight_numb = int(request.form.get('Tight_numb', 0))
        muscles_tendons = int(request.form.get('muscles_tendons', 0))
        dizziness5 = int(request.form.get('dizziness5', 0))
        
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

@app.route('/detail_users/<user_id>')
def detail_users(user_id):
    # ดึงข้อมูลสมาชิกตาม _id ของ MongoDB
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        gender_name = get_gender_name(user_id)
        pregnant_name = get_pregnant_name(user_id)
        breastfeeding_name = get_breastfeeding_name(user_id)

        dob = user.get('dob')
        if dob:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        else:
            age = None

        # ตรวจสอบว่า user มี 'u_id' หรือไม่
        if 'u_id' in user:
            user_u_id = user['u_id']
            
            # ดึงข้อมูลโรคประจำตัว ยาที่ใช้ และข้อมูลการแพ้ตาม u_id แทน _id
            existing_cn_ids = [rel['cn_id'] for rel in u_cn_collection.find({'u_id': user_u_id})]
            existing_md_ids = [rel['md_id'] for rel in u_md_collection.find({'u_id': user_u_id})]
            existing_ag_ids = [rel['ag_id'] for rel in u_ag_collection.find({'u_id': user_u_id})]

            chronics = list(chronics_data_collection.find({'cn_id': {'$in': existing_cn_ids}}))
            medicines = list(medicines_data_collection.find({'md_id': {'$in': existing_md_ids}}))
            allergys = list(allergys_data_collection.find({'ag_id': {'$in': existing_ag_ids}}))

            return render_template(
                'view_users.html', 
                user=user, 
                age=age, 
                gender_name=gender_name, 
                pregnant_name=pregnant_name, 
                breastfeeding_name=breastfeeding_name, 
                chronics=chronics, 
                medicines=medicines, 
                allergys=allergys
            )
        else:
            flash('ไม่พบข้อมูล', 'danger')
            return redirect(url_for('manage_members'))

    flash('ไม่พบข้อมูลสมาชิก', 'danger')
    return redirect(url_for('manage_members'))

@app.route('/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    # ดึงข้อมูลผู้ใช้ ที่ต้องการแก้ไขเพื่อแสดงในฟอร์ม
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        new_password = request.form['new_password']

        if new_password:
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        else:
            hashed_password = user['password']

        fname = request.form['fname']
        lname = request.form['lname']
        gender = int(request.form['gender'])
        pregnant = int(request.form.get('pregnant', 0))
        breastfeeding = int(request.form.get('breastfeeding', 0))
        
        # อัปเดตข้อมูลผู้ใช้ใน MongoDB
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'username': username, 'email': email, 'password': hashed_password, 'fname': fname, 
                                                                          'lname': lname, 'gender': gender, 'pregnant': pregnant, 'breastfeeding': breastfeeding}})
        
        # ดึง u_id ของ user ปัจจุบัน
        u_id = user['u_id']

        # รับค่า cn_ids ที่เลือกมาใหม่
        cn_ids = request.form.getlist('cn_ids')
        # ลบความสัมพันธ์โรคประจำตัว ที่มีอยู่ใน u_cn ก่อนแล้วเพิ่มใหม่ตามที่เลือก
        if cn_ids:
            u_cn_collection.delete_many({'u_id': int(u_id)})
            for cn_id in cn_ids:
                u_cn_collection.insert_one({'u_id': int(u_id), 'cn_id': int(cn_id)})

        # รับค่า md_ids ที่เลือกมาใหม่
        md_ids = request.form.getlist('md_ids')
        # ลบความสัมพันธ์ยาที่ใช้ ที่มีอยู่ใน u_md ก่อนแล้วเพิ่มใหม่ตามที่เลือก
        if md_ids:
            u_md_collection.delete_many({'u_id': int(u_id)})
            for md_id in md_ids:
                u_md_collection.insert_one({'u_id': int(u_id), 'md_id': int(md_id)})

        # รับค่า ag_ids ที่เลือกมาใหม่
        ag_ids = request.form.getlist('ag_ids')
        # ลบความสัมพันธ์ยาที่ใช้ ที่มีอยู่ใน u_ag ก่อนแล้วเพิ่มใหม่ตามที่เลือก
        if ag_ids:
            u_ag_collection.delete_many({'u_id': int(u_id)})
            for ag_id in ag_ids:
                u_ag_collection.insert_one({'u_id': int(u_id), 'ag_id': int(ag_id)})

        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_members'))

    existing_cn_ids = [rel['cn_id'] for rel in u_cn_collection.find({'u_id': user['u_id']})]
    existing_md_ids = [rel['md_id'] for rel in u_md_collection.find({'u_id': user['u_id']})]
    existing_ag_ids = [rel['ag_id'] for rel in u_ag_collection.find({'u_id': user['u_id']})]

    # ดึงข้อมูล collection chronics_data และแปลงเป็น list
    chronics = list(chronics_data_collection.find())

    # ดึงข้อมูล collection medicines_data และแปลงเป็น list
    medicines = list(medicines_data_collection.find())

    # ดึงข้อมูล collection allergys_data และแปลงเป็น list
    allergys = list(allergys_data_collection.find())

    return render_template('edit_users.html', user=user, chronics=chronics, medicines=medicines, allergys=allergys, existing_cn_ids=existing_cn_ids, existing_md_ids=existing_md_ids, existing_ag_ids=existing_ag_ids)

@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    # ลบข้อมูลผู้ใช้ออกจาก MongoDB โดยใช้ ObjectId ใน users_collection
    users = users_collection.find_one({'_id': ObjectId(user_id)})

    # ตรวจสอบว่ามีข้อมูลใน users_collection หรือไม่
    if users:
        u_id = users['u_id']  # ได้ u_id ของผู้ใช้นั้น

        # ลบข้อมูลใน users_collection
        users_collection.delete_one({'_id': ObjectId(user_id)})

        # ลบข้อมูลคำเตือนและอาการที่เกี่ยวข้องกับ u_id ของสมุนไพรนี้
        u_cn_collection.delete_many({'u_id': u_id})
        u_md_collection.delete_many({'u_id': u_id})
        u_ag_collection.delete_many({'u_id': u_id})
        
        flash('ลบข้อมูลสำเร็จ!', 'success')
    else:
        flash('ไม่พบข้อมูลสมาชิกที่ต้องการลบ', 'error')
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_members'))

@app.route('/admin_signup', methods=['POST','GET'])
def admin_signup():
    if request.method == 'POST':
        # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
        last_user = users_collection.find_one(sort=[("u_id", -1)])
        
        # ถ้ามีเอกสารอยู่ ให้เอา u_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 201
        if last_user:
            u_id = last_user['u_id'] + 1
        else:
            u_id = 201  # กำหนดค่าเริ่มต้นเป็น 201 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # แฮชรหัสผ่าน และให้ผลลัพธ์เป็น string
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # เพิ่มข้อมูลใหม่ลงใน MongoDB / role member
        users_collection.insert_one({'u_id': u_id, 'username': username, 'email': email, 'password': hashed_password, 'role': 'admin'})

        flash('เพิ่มผู้ดูแลระบบสำเร็จ!', 'success')
        return redirect(url_for('manage_members'))
    
    return render_template('add_admin.html')

@app.route('/member_signup', methods=['POST','GET'])
def member_signup():
    if request.method == 'POST':

        # ค้นหาเอกสาร(เอกสาร=ข้อมูลแถวล่าสุด)ที่มี cn_id มากที่สุด
        last_user = users_collection.find_one(sort=[("u_id", -1)])
        
        # ถ้ามีเอกสารอยู่ ให้เอา u_id ล่าสุดมาบวก 1, ถ้าไม่มีให้ตั้งค่าเป็น 201
        if last_user:
            u_id = last_user['u_id'] + 1
        else:
            u_id = 201  # กำหนดค่าเริ่มต้นเป็น 201 ถ้ายังไม่มีเอกสารใด ๆ (ซึ่งก็ไม่หรอก เพราะมีข้อมูลแล้ว)
            
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']

        # แปลงวันเกิดเป็น datetime object
        dob_str = request.form['dob']
        dob = datetime.strptime(dob_str, '%Y-%m-%d')

        gender = int(request.form['gender'])
        pregnant = int(request.form.get('pregnant', 0)) # ถ้าไม่ส่งค่ามา กำหนดค่าเริ่มต้นเป็น 0
        breastfeeding = int(request.form.get('breastfeeding', 0))
        weight = int(request.form['weight'])
        height = int(request.form['height'])

        # แฮชรหัสผ่าน และให้ผลลัพธ์เป็น string
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # เพิ่มข้อมูลใหม่ลงใน MongoDB / role member
        users_collection.insert_one({'u_id': u_id,'username': username, 'email': email, 'password': hashed_password, 'role': 'member',
                                     'fname': fname, 'lname': lname, 'dob': dob, 'gender': gender, 'pregnant': pregnant,
                                     'breastfeeding': breastfeeding, 'weight': weight, 'height': height})

        # ดึงคำเตือนที่เลือกมา
        cn_ids = request.form.getlist('chronics')

        # ดึงอาการที่เลือกมา
        md_ids = request.form.getlist('medicines')

        # ดึงการแพ้ที่เลือกมา
        ag_ids = request.form.getlist('allergys')

        # สร้างเอกสารความสัมพันธ์ระหว่าง u_id และ cn_id แต่ละรายการใน collection u_cn
        for cn_id in cn_ids:
            u_cn_collection.insert_one({'u_id': int(u_id), 'cn_id': int(cn_id)})

        # สร้างเอกสารความสัมพันธ์ระหว่าง u_id และ md_id แต่ละรายการใน collection u_md
        for md_id in md_ids:
            u_md_collection.insert_one({'u_id': int(u_id), 'md_id': int(md_id)})

        # สร้างเอกสารความสัมพันธ์ระหว่าง u_id และ ag_id แต่ละรายการใน collection u_ag
        for ag_id in ag_ids:
            u_ag_collection.insert_one({'u_id': int(u_id), 'ag_id': int(ag_id)})
        
        

        flash('เพิ่มสมาชิกสำเร็จ!', 'success')
        return redirect(url_for('manage_members'))
    
    chronics = chronics_data_collection.find()
    medicines = medicines_data_collection.find()
    allergys = allergys_data_collection.find()
    
    return render_template('add_member.html', chronics=chronics, medicines=medicines, allergys=allergys)

@app.route('/manage_herbals')
def manage_herbals():
    page = request.args.get('page', 1, type=int)  # รับค่าหน้าจาก URL หรือกำหนดเป็นหน้า 1 ถ้าไม่มีการส่งมา
    per_page = 10  # กำหนดจำนวนข้อมูลต่อหน้า
    herbals_count = herbals_data_collection.count_documents({})  # นับจำนวนเอกสารทั้งหมด
    total_pages = (herbals_count + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด

    # ดึงข้อมูลจาก MongoDB และแปลงให้เป็นลิสต์ก่อน
    herbals = list(herbals_data_collection.find().skip((page - 1) * per_page).limit(per_page))

    # ดึงคำเตือน ที่เกี่ยวข้องกับแต่ละสมุนไพร
    for herbal in herbals:
        hm_id = herbal['hm_id']
        
        # ค้นหาเอกสารใน hm_wn ที่เชื่อมโยงกับ hm_id ปัจจุบัน
        related_warnings = list(hm_wn_collection.find({'hm_id': hm_id}))
        
        # ดึงคำเตือนจาก warnings_data_collection ตาม wn_id ที่พบ
        warning_texts = []
        for rel in related_warnings:
            wn_id = rel['wn_id']
            warning = warnings_data_collection.find_one({'wn_id': wn_id})
            if warning:
                warning_texts.append(warning['wn_name'])
        
        # เก็บคำเตือนเป็นสตริงในฟิลด์ warnings_text ของ herbal
        herbal['warnings_text'] = ", ".join(warning_texts) if warning_texts else "-"

    # ดึงอาการ ที่เกี่ยวข้องกับแต่ละสมุนไพร
    for herbal in herbals:
        hm_id = herbal['hm_id']
        
        # ค้นหาเอกสารใน hm_st ที่เชื่อมโยงกับ hm_id ปัจจุบัน
        related_symptoms = list(hm_st_collection.find({'hm_id': hm_id}))
        
        # ดึงคำเตือนจาก symptoms_data_collection ตาม st_id ที่พบ
        symptom_texts = []
        for rel in related_symptoms:
            st_id = rel['st_id']
            symptom = symptoms_data_collection.find_one({'st_id': st_id})
            if symptom:
                symptom_texts.append(symptom['st_name'])
        
        # เก็บคำเตือนเป็นสตริงในฟิลด์ symptoms_text ของ herbal
        herbal['symptoms_text'] = ", ".join(symptom_texts) if symptom_texts else "-"

    # ดึงข้อมูล collection warnings_data
    warnings = warnings_data_collection.find()

    # ดึงข้อมูล collection warnings_data
    symptoms = symptoms_data_collection.find()

    return render_template('manage_herbals.html', herbals=herbals, page=page, total_pages=total_pages, warnings=warnings, symptoms=symptoms)

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

    # ดึงคำเตือนที่เลือกมา
    wn_ids = request.form.getlist('warnings')

    # ดึงอาการที่เลือกมา
    st_ids = request.form.getlist('symptoms')
    
    # สร้างเอกสารความสัมพันธ์ระหว่าง hm_id และ wn_id แต่ละรายการใน collection hm_wn
    for wn_id in wn_ids:
        hm_wn_collection.insert_one({'hm_id': int(hm_id), 'wn_id': int(wn_id)})

    # สร้างเอกสารความสัมพันธ์ระหว่าง hm_id และ st_id แต่ละรายการใน collection hm_st
    for st_id in st_ids:
        hm_st_collection.insert_one({'hm_id': int(hm_id), 'st_id': int(st_id)})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_herbals'))

@app.route('/delete_herbal/<herbal_id>', methods=['POST'])
def delete_herbal(herbal_id):
    # ลบข้อมูลยาสมุนไพรออกจาก MongoDB โดยใช้ ObjectId ใน herbals_data_collection
    herbals_data = herbals_data_collection.find_one({'_id': ObjectId(herbal_id)})
    
    # ตรวจสอบว่ามีข้อมูลใน herbals_data_collection หรือไม่
    if herbals_data:
        hm_id = herbals_data['hm_id']  # ได้ hm_id ของสมุนไพรนั้น

        # ลบข้อมูลใน herbals_data_collection
        herbals_data_collection.delete_one({'_id': ObjectId(herbal_id)})

        # ลบข้อมูลคำเตือนและอาการที่เกี่ยวข้องกับ hm_id ของสมุนไพรนี้
        hm_wn_collection.delete_many({'hm_id': hm_id})
        hm_st_collection.delete_many({'hm_id': hm_id})
        
        flash('ลบข้อมูลสำเร็จ!', 'success')
    else:
        flash('ไม่พบข้อมูลยาสมุนไพรที่ต้องการลบ', 'error')

    return redirect(url_for('manage_herbals'))

@app.route('/edit_herbal/<herbal_id>', methods=['GET', 'POST'])
def edit_herbal(herbal_id):
    if request.method == 'POST':
        # รับข้อมูลใหม่จากฟอร์ม
        hm_name = request.form['hm_name']
        hm_dosage = request.form['hm_dosage']
        hm_recipe = request.form['hm_recipe']

        # อัปเดตข้อมูลใน MongoDB
        herbals_data_collection.update_one({'_id': ObjectId(herbal_id)}, {'$set': {'hm_name': hm_name, 'hm_dosage': hm_dosage, 'hm_recipe': hm_recipe}})

        # รับค่า wn_ids ที่เลือกมาใหม่
        wn_ids = request.form.getlist('wn_ids')

        # รับค่า st_ids ที่เลือกมาใหม่
        st_ids = request.form.getlist('st_ids')

        # ดึง hm_id ของสมุนไพรปัจจุบัน
        herbal = herbals_data_collection.find_one({'_id': ObjectId(herbal_id)})
        hm_id = herbal['hm_id']

        # ลบความสัมพันธ์คำเตือนที่มีอยู่ใน hm_wn ก่อนแล้วเพิ่มใหม่ตามที่เลือก
        hm_wn_collection.delete_many({'hm_id': int(hm_id)})  # ลบรายการที่มี hm_id ตรงกับยานี้
        for wn_id in wn_ids:
            hm_wn_collection.insert_one({'hm_id': int(hm_id), 'wn_id': int(wn_id)})

        # ลบความสัมพันธ์คำเตือนที่มีอยู่ใน hm_wn ก่อนแล้วเพิ่มใหม่ตามที่เลือก
        hm_st_collection.delete_many({'hm_id': int(hm_id)})  # ลบรายการที่มี hm_id ตรงกับยานี้
        for st_id in st_ids:
            hm_st_collection.insert_one({'hm_id': int(hm_id), 'st_id': int(st_id)})

        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_herbals'))

    # ดึงข้อมูลที่ต้องการแก้ไขเพื่อแสดงในฟอร์ม
    herbal = herbals_data_collection.find_one({'_id': ObjectId(herbal_id)})
    existing_wn_ids = [rel['wn_id'] for rel in hm_wn_collection.find({'hm_id': herbal['hm_id']})]
    existing_st_ids = [rel['st_id'] for rel in hm_st_collection.find({'hm_id': herbal['hm_id']})]

    # ดึงข้อมูล collection warnings_data และแปลงเป็น list
    warnings = list(warnings_data_collection.find())

    # ดึงข้อมูล collection warnings_data และแปลงเป็น list
    symptoms = list(symptoms_data_collection.find())

    return render_template('edit_herbals.html', herbal=herbal, warnings=warnings, existing_wn_ids=existing_wn_ids, symptoms=symptoms, existing_st_ids=existing_st_ids)

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
    return redirect(url_for('manage_warnings'))

@app.route('/profile/<user_id>')
def profile(user_id):

    # ดึงข้อมูลทั้งหมดจาก Collection
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        gender_name = get_gender_name(user_id)
        pregnant_name = get_pregnant_name(user_id)
        breastfeeding_name = get_breastfeeding_name(user_id)
        
        dob = user['dob']
        if dob:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        else:
            age = None

        return render_template(
                'member_profile.html', 
                user=user, 
                age=age, 
                gender_name=gender_name, 
                pregnant_name=pregnant_name, 
                breastfeeding_name=breastfeeding_name
            )
    else:
        flash('ไม่พบข้อมูล', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/profile')
@login_required
def profile():
    # ดึงข้อมูลของผู้ใช้ที่ล็อกอินอยู่จาก current_user
    user = users_collection.find_one({'_id': ObjectId(str(current_user.id))})

    if user:
        # ดึงข้อมูลเกี่ยวกับเพศ, การตั้งครรภ์, และการให้นมบุตร
        gender_name = get_gender_name(str(current_user.id))
        pregnant_name = get_pregnant_name(str(current_user.id))
        breastfeeding_name = get_breastfeeding_name(str(current_user.id))
        
        # คำนวณอายุจากวันเกิด
        dob = user['dob']
        if dob:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        else:
            age = None
        
        # ดึงข้อมูล u_id ของสมาชิก
        user_u_id = user['u_id']
        
        # ดึงข้อมูลโรคประจำตัวจาก u_cn_collection โดยใช้ u_id
        existing_cn_ids = [rel['cn_id'] for rel in u_cn_collection.find({'u_id': user_u_id})]
        
        # ดึงข้อมูลยาที่ใช้จาก u_md_collection โดยใช้ u_id
        existing_md_ids = [rel['md_id'] for rel in u_md_collection.find({'u_id': user_u_id})]
        
        # ดึงข้อมูลการแพ้จาก u_ag_collection โดยใช้ u_id
        existing_ag_ids = [rel['ag_id'] for rel in u_ag_collection.find({'u_id': user_u_id})]
        
        # ดึงข้อมูลโรคประจำตัวจาก collection chronics_data
        chronics = list(chronics_data_collection.find({'cn_id': {'$in': existing_cn_ids}}))
        
        # ดึงข้อมูลยาที่ใช้จาก collection medicines_data
        medicines = list(medicines_data_collection.find({'md_id': {'$in': existing_md_ids}}))
        
        # ดึงข้อมูลการแพ้จาก collection allergys_data
        allergys = list(allergys_data_collection.find({'ag_id': {'$in': existing_ag_ids}}))

        return render_template(
            'member_profile.html', 
            user=user, 
            age=age, 
            gender_name=gender_name, 
            pregnant_name=pregnant_name, 
            breastfeeding_name=breastfeeding_name,
            chronics=chronics,  # ส่งข้อมูลโรคประจำตัวไปยัง template
            medicines=medicines,  # ส่งข้อมูลยาที่ใช้ไปยัง template
            allergys=allergys  # ส่งข้อมูลการแพ้ไปยัง template
        )
    else:
        flash('ไม่พบข้อมูลผู้ใช้', 'danger')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)