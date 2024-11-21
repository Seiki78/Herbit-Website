from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.tree import export_graphviz
import matplotlib.pyplot as plt
import pydotplus
from graphviz import Source

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

######################################################################## Train

# ดึงข้อมูลจาก MongoDB เตรียมเทรน
data = list(trains_collection.find())

# แปลงข้อมูล MongoDB เป็น DataFrame เตรียมเทรน
df = pd.DataFrame(data)

# ตรวจสอบข้อมูลที่ได้
print(df.head())

# กำหนด feature_cols (ฟีเจอร์ที่ใช้ในการทำนาย)
feature_cols = ['pregnant', 'dizziness1', 'Palpitations', 'squeamish', 'vomit', 
                'dizziness2', 'dizziness3', 'dizziness4', 'colic1', 'tired', 
                'cannot_sleep', 'flatulence', 'stomach_ache', 'constipation1', 
                'diarrhea1', 'hemorrhoids', 'menstruation', 'Menstrual_cramps', 
                'postpartum_woman', 'Lochia', 'Vaginal_Discharge', 'Nourish_blood',
                'fever1', 'inner_heat', 'Measles', 'Chickenpox', 'fever2', 'fever3', 
                'cough', 'phlegm', 'cold', 'Allergic_Rhinitis', 'body_aches', 'tendon', 
                'Tight_numb', 'muscles_tendons', 'dizziness5', 'balancing']

# กำหนด target (ผลลัพธ์ที่ต้องการทำนาย)
target_col = 'hm_id'

# สร้าง DataFrame สำหรับ feature (X) และ target (y)
X = df[feature_cols]
y = df[target_col]

# แบ่งข้อมูลเป็นชุดเทรนและชุดทดสอบ
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# สร้างโมเดล Random Forest
clf = RandomForestClassifier(n_estimators=100, random_state=42)

# ฝึกโมเดลด้วยข้อมูลเทรน
clf.fit(X_train, y_train)

# ทำนายผลลัพธ์กับข้อมูลทดสอบ
y_pred = clf.predict(X_test)

# คำนวณความแม่นยำของโมเดล
accuracy = accuracy_score(y_test, y_pred)
print("ความแม่นยำของโมเดล: ", accuracy)

######################################################################## Train

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

def get_bmiResult(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})  # ค้นหาจาก _id

    if user is not None:
        weight = user.get('weight')
        height = user.get('height')

        if weight and height and weight > 0 and height > 0:
            # แปลงจากซม. เป็นเมตร
            height = height / 100

            bmi = weight / (height * height)

            if bmi >= 30:
                bmiResult = '(30.0 ขึ้นไป)<br>อ้วนมาก'
            elif bmi >= 25 and bmi < 30:
                bmiResult = '(25.0 - 29.9)<br>อ้วน'
            elif bmi >= 18.5 and bmi < 25:
                bmiResult = '(18.5 - 24.9)<br>น้ำหนักปกติ เหมาะสม'
            else:
                bmiResult = '(น้อยกว่า 18.5)<br>ผอมเกินไป'

            return bmiResult
        
        return 'เพิ่มข้อมูลน้ำหนัก/ส่วนสูงที่โปรไฟล์'

    return "เพิ่มข้อมูลน้ำหนัก/ส่วนสูงที่โปรไฟล์"

def get_waterResult(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})  # ค้นหาจาก _id

    if user is not None:
        weight = user.get('weight')

        if weight and weight > 0:

            recommendedWaterIntake  = weight * 2.2 * 30/2

            waterResult = 'ปริมาณดื่มน้ำที่แนะนำต่อวัน<br>' + str(recommendedWaterIntake) + ' มล.'

            return waterResult
        
        return 'เพิ่มข้อมูลน้ำหนักที่โปรไฟล์'

    return "เพิ่มข้อมูลน้ำหนักที่โปรไฟล์"

def get_sleepResult(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})  # ค้นหาจาก _id

    if user is not None:
        dob = user.get('dob')

        if dob:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            if age < 1 :
                sleeResult = 'ชั่วโมงนอนที่เหมาะสม<br>12 - 16 ชั่วโมง/ วัน (รวมนอนกลางวัน)​'
            elif age >= 1 and age <= 2 :
                sleeResult = 'ชั่วโมงนอนที่เหมาะสม<br>11 - 14 ชั่วโมง/ วัน (รวมนอนกลางวัน)​'
            elif age >= 3 and age <= 5 :
                sleeResult = 'ชั่วโมงนอนที่เหมาะสม<br>9 - 12 ชั่วโมง/ วัน​​'
            elif age >= 13 and age <= 18 :
                sleeResult = 'ชั่วโมงนอนที่เหมาะสม<br>8 - 10 ชั่วโมง/ วัน​​'
            elif age >18 :
                sleeResult = 'ชั่วโมงนอนที่เหมาะสม<br>7 - 9 ชั่วโมง/ วัน​​'

            return sleeResult
        
        return 'เพิ่มข้อมูล วัน/เดือน/ปีเกิด ที่โปรไฟล์'

    return "เพิ่มข้อมูล วัน/เดือน/ปีเกิด ที่โปรไฟล์"

def get_hm_name(hm_id):
    hm_id = int(hm_id)
    herbal = herbals_data_collection.find_one({'hm_id': hm_id})
    
    if herbal:
        return herbal.get('hm_name', 'ไม่พบชื่อยาสมุนไพร')
    
    return 'ไม่พบชื่อยาสมุนไพร'

def get_hm_dosage(hm_id):
    hm_id = int(hm_id)
    herbal = herbals_data_collection.find_one({'hm_id': hm_id})
    
    if herbal:
        return herbal.get('hm_dosage', 'ไม่พบวิธีใช้')
    
    return 'ไม่พบวิธีใช้'

def get_hm_recipe(hm_id):
    hm_id = int(hm_id)
    herbal = herbals_data_collection.find_one({'hm_id': hm_id})
    
    if herbal:
        return herbal.get('hm_recipe', 'ไม่พบตำรับยา')

    return 'ไม่พบตำรับยา'

def get_symptoms_for_herbal(hm_id):
    hm_id = int(hm_id)
    related_symptoms = hm_st_collection.find({'hm_id': hm_id})
    
    symptoms = []
    for rel in related_symptoms:
        st_id = rel['st_id']
        symptom = symptoms_data_collection.find_one({'st_id': st_id})
        if symptom:
            symptom_name = symptom['st_name'].strip()  # ใช้ strip() เพื่อให้มั่นใจว่าไม่มีช่องว่างส่วนเกิน
            if symptom_name:  # ตรวจสอบให้แน่ใจว่าไม่เป็นค่าว่าง
                symptoms.append(symptom_name)
    
    return symptoms

def get_warnings_for_herbal(hm_id):
    hm_id = int(hm_id)
    related_warnings = hm_wn_collection.find({'hm_id': hm_id})
    
    warnings = []
    for rel in related_warnings:
        wn_id = rel['wn_id']
        warning = warnings_data_collection.find_one({'wn_id': wn_id})
        if warning:
            warning_name = warning['wn_name'].strip()  # ใช้ strip() เพื่อให้มั่นใจว่าไม่มีช่องว่างส่วนเกิน
            if warning_name:  # ตรวจสอบให้แน่ใจว่าไม่เป็นค่าว่าง
                warnings.append(warning_name)
    
    # แปลงคำเตือนแต่ละข้อให้แสดงในบรรทัดใหม่
    formatted_warnings = "<br>".join(warnings)
    
    return formatted_warnings

@app.route('/')
def index():

    return redirect(url_for('type_predict'))

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
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'member':
        return redirect(url_for('member_dashboard'))
    else:
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()  # ออกจากระบบผู้ใช้
    flash('ออกจากระบบสำเร็จ', 'success')
    return redirect(url_for('index'))

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
    balancing = int(request.form.get('balancing', 0))
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
        'balancing': balancing,
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
        balancing = int(request.form.get('balancing', 0))
        
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
                                                                            'dizziness5': dizziness5, 'balancing': balancing}})
        
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

        role = request.form['role']
        fname = request.form['fname']
        lname = request.form['lname']
        gender = int(request.form['gender'])
        pregnant = int(request.form.get('pregnant', 0))
        breastfeeding = int(request.form.get('breastfeeding', 0))
        
        # อัปเดตข้อมูลผู้ใช้ใน MongoDB
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'username': username, 'email': email, 'password': hashed_password, 'role': role, 'fname': fname, 
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

@app.route('/edit_medicine/<medicine_id>', methods=['GET', 'POST'])
def edit_medicine(medicine_id):
    if request.method == 'POST':
        md_nameEN = request.form['md_nameEN']
        md_nameTH = request.form['md_nameTH']
        
        # อัปเดตเฉพาะชื่อโรคใน MongoDB
        medicines_data_collection.update_one({'_id': ObjectId(medicine_id)}, {'$set': {'md_nameEN': md_nameEN, 'md_nameTH': md_nameTH}})
        
        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_medicines'))
    
    # ดึงข้อมูลโรคที่ต้องการแก้ไข
    medicine = medicines_data_collection.find_one({'_id': ObjectId(medicine_id)})

    return render_template('edit_medicines.html', medicine=medicine)

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

@app.route('/edit_allergy/<allergy_id>', methods=['GET', 'POST'])
def edit_allergy(allergy_id):
    if request.method == 'POST':
        ag_name = request.form['ag_name']
        ag_detail = request.form['ag_detail']
        
        # อัปเดตเฉพาะชื่อโรคใน MongoDB
        allergys_data_collection.update_one({'_id': ObjectId(allergy_id)}, {'$set': {'ag_name': ag_name, 'ag_detail': ag_detail}})
        
        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_allergys'))
    
    # ดึงข้อมูลโรคที่ต้องการแก้ไข
    allergy = allergys_data_collection.find_one({'_id': ObjectId(allergy_id)})

    return render_template('edit_allergys.html', allergy=allergy)

@app.route('/manage_chrosymps')
def manage_chrosymps():
    # กำหนดค่าหน้าปัจจุบัน
    page = request.args.get('page', 1, type=int)
    per_page = 25  # กำหนดจำนวนข้อมูลต่อหน้า

    # นับจำนวนเอกสารทั้งหมดในแต่ละ collection
    chronics_count = chronics_data_collection.count_documents({})
    symptoms_count = symptoms_data_collection.count_documents({})

    # คำนวณจำนวนหน้าทั้งหมด
    total_pages = max((chronics_count + per_page - 1) // per_page, (symptoms_count + per_page - 1) // per_page)

    # ดึงข้อมูลจาก MongoDB สำหรับทั้งสอง collection โดยใช้ skip และ limit
    chronics = chronics_data_collection.find().skip((page - 1) * per_page).limit(per_page)
    symptoms = symptoms_data_collection.find().skip((page - 1) * per_page).limit(per_page)

    return render_template('manage_chrosymps.html', chronics=chronics, symptoms=symptoms, page=page, total_pages=total_pages)

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
    cn_nameEN = request.form['cn_nameEN']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection chronic
    chronics_data_collection.insert_one({'cn_id': cn_id, 'cn_name': cn_name, 'cn_nameEN': cn_nameEN})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_chrosymps'))

@app.route('/delete_chronic/<chronic_id>', methods=['POST'])
def delete_chronic(chronic_id):
    # ลบข้อมูลโรคออกจาก MongoDB โดยใช้ ObjectId
    chronics_data_collection.delete_one({'_id': ObjectId(chronic_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_chrosymps'))

@app.route('/edit_chronic/<chronic_id>', methods=['GET', 'POST'])
def edit_chronic(chronic_id):
    if request.method == 'POST':
        cn_name = request.form['cn_name']
        cn_nameEN = request.form['cn_nameEN']
        
        # อัปเดตเฉพาะชื่อโรคใน MongoDB
        chronics_data_collection.update_one({'_id': ObjectId(chronic_id)}, {'$set': {'cn_name': cn_name, 'cn_nameEN': cn_nameEN}})
        
        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_chrosymps'))
    
    # ดึงข้อมูลโรคที่ต้องการแก้ไข
    chronic = chronics_data_collection.find_one({'_id': ObjectId(chronic_id)})

    return render_template('edit_chronics.html', chronic=chronic)

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
    st_nameEN = request.form['st_nameEN']
    
    # เพิ่มข้อมูลใหม่ลงใน Collection chronic
    symptoms_data_collection.insert_one({'st_id': st_id, 'st_name': st_name, 'st_nameEN': st_nameEN})
    
    flash('เพิ่มข้อมูลสำเร็จ', 'success')
    return redirect(url_for('manage_chrosymps'))

@app.route('/delete_symptom/<symptom_id>', methods=['POST'])
def delete_symptom(symptom_id):
    # ลบข้อมูลโรคออกจาก MongoDB โดยใช้ ObjectId
    symptoms_data_collection.delete_one({'_id': ObjectId(symptom_id)})
    
    flash('ลบข้อมูลสำเร็จ!', 'success')
    return redirect(url_for('manage_chrosymps'))

@app.route('/edit_symptom/<symptom_id>', methods=['GET', 'POST'])
def edit_symptom(symptom_id):
    if request.method == 'POST':
        st_name = request.form['st_name']
        st_nameEN = request.form['st_nameEN']
        
        # อัปเดตเฉพาะชื่อโรคใน MongoDB
        symptoms_data_collection.update_one({'_id': ObjectId(symptom_id)}, {'$set': {'st_name': st_name, 'st_nameEN': st_nameEN}})
        
        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('manage_chrosymps'))
    
    # ดึงข้อมูลอาการที่ต้องการแก้ไข
    symptom = symptoms_data_collection.find_one({'_id': ObjectId(symptom_id)})

    return render_template('edit_symptoms.html', symptom=symptom)

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

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # ใช้ current_user.id เพื่อดึงข้อมูลผู้ใช้ที่ล็อกอินอยู่
    user = users_collection.find_one({'_id': ObjectId(str(current_user.id))})

    if request.method == 'POST':
        # รับข้อมูลจากฟอร์ม
        username = request.form['username']
        email = request.form['email']
        new_password = request.form['new_password']

        # ถ้ามีการเปลี่ยนแปลงรหัสผ่าน, แฮชรหัสผ่านใหม่
        if new_password:
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        else:
            hashed_password = user['password']  # ใช้รหัสผ่านเดิมหากไม่ได้เปลี่ยน

        fname = request.form['fname']
        lname = request.form['lname']
        gender = int(request.form['gender'])
        pregnant = int(request.form.get('pregnant', 0))  # ถ้าไม่ส่งค่ามา ให้ค่าเป็น 0
        breastfeeding = int(request.form.get('breastfeeding', 0))  # ถ้าไม่ส่งค่ามา ให้ค่าเป็น 0
        weight = int(request.form['weight'])
        height = int(request.form['height'])

        # อัปเดตข้อมูลใน MongoDB
        users_collection.update_one(
            {'_id': ObjectId(str(current_user.id))},
            {'$set': {'username': username, 'email': email, 'password': hashed_password, 'fname': fname,
                      'lname': lname, 'gender': gender, 'pregnant': pregnant, 'breastfeeding': breastfeeding, 
                      'weight': weight, 'height': height}}
        )

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
        return redirect(url_for('profile'))  # ไปยังหน้าข้อมูลส่วนตัว

    # ดึงข้อมูลการโรคประจำตัว, ยาที่ใช้ และข้อมูลการแพ้ที่มีอยู่
    existing_cn_ids = [rel['cn_id'] for rel in u_cn_collection.find({'u_id': user['u_id']})]
    existing_md_ids = [rel['md_id'] for rel in u_md_collection.find({'u_id': user['u_id']})]
    existing_ag_ids = [rel['ag_id'] for rel in u_ag_collection.find({'u_id': user['u_id']})]

    # ดึงข้อมูลจาก collection ต่างๆ ที่จะใช้แสดงในฟอร์ม
    chronics = list(chronics_data_collection.find())
    medicines = list(medicines_data_collection.find())
    allergys = list(allergys_data_collection.find())

    return render_template('edit_profile.html', user=user, chronics=chronics, medicines=medicines, allergys=allergys,
                           existing_cn_ids=existing_cn_ids, existing_md_ids=existing_md_ids, existing_ag_ids=existing_ag_ids)

@app.route('/member_dashboard')
@login_required
def member_dashboard():
    # ดึงข้อมูลของผู้ใช้ที่ล็อกอินอยู่จาก current_user
    user = users_collection.find_one({'_id': ObjectId(str(current_user.id))})

    if user:
        # ดึงข้อมูล
        bmi_result = get_bmiResult(str(current_user.id))
        water_result = get_waterResult(str(current_user.id))
        sleep_result = get_sleepResult(str(current_user.id))

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

        return render_template('member_dashboard.html', user=user, bmi_result=bmi_result, water_result=water_result, sleep_result=sleep_result, chronics=chronics, medicines=medicines, allergys=allergys)
    else:
        return redirect(url_for('dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():

    herbals_count = herbals_data_collection.count_documents({})
    trains_count = trains_collection.count_documents({})
    admins_count = users_collection.count_documents({'role': 'admin'})
    members_count = users_collection.count_documents({'role': 'member'})
    chronics_count = chronics_data_collection.count_documents({})
    medicines_count = medicines_data_collection.count_documents({})
    allergies_count = allergys_data_collection.count_documents({})
    warnings_count = warnings_data_collection.count_documents({})

    return render_template('admin_dashboard.html', herbals_count=herbals_count, trains_count=trains_count,
                           admins_count=admins_count, members_count=members_count, chronics_count=chronics_count,
                           medicines_count=medicines_count, allergies_count=allergies_count, warnings_count=warnings_count)

@app.route('/type_predict')
def type_predict():

    # ตรวจสอบว่าผู้ใช้ล็อกอินหรือไม่
    if current_user.is_authenticated:
        return redirect(url_for('member_predict', user_id=current_user.id))
    else:
        return redirect(url_for('general_predict'))

@app.route('/general_predict')
def general_predict():
    # โค้ดของหน้า predict สำหรับคนที่ไม่ได้ล็อกอิน

    chronics = chronics_data_collection.find()
    medicines = medicines_data_collection.find()
    allergys = allergys_data_collection.find()

    return render_template('general_predict.html', chronics=chronics, medicines=medicines, allergys=allergys)

@app.route('/member_predict/<user_id>')
@login_required
def member_predict(user_id):
    # โค้ดของหน้า predict สำหรับคนที่ล็อกอิน

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    gender_name = get_gender_name(str(current_user.id))
    pregnant_name = get_pregnant_name(str(current_user.id))
    breastfeeding_name = get_breastfeeding_name(str(current_user.id))

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

    if not user:
        return redirect(url_for('index'))

    return render_template('member_predict.html', user=user, gender_name=gender_name, pregnant_name=pregnant_name, age=age,
                           breastfeeding_name=breastfeeding_name, chronics=chronics, medicines=medicines, allergys=allergys)

@app.route('/mb_predict/<user_id>', methods=['POST'])
@login_required
def mb_predict(user_id):

    # predict สำหรับสมาชิกที่ล็อกอินแล้ว

    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if not user:
        return redirect(url_for('index'))

    dob = user.get('dob')
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    pregnant = user.get('pregnant')
    breastfeeding = user.get('breastfeeding')

    user_u_id = user['u_id']
    print(f'user_u_id: {user_u_id}')

    # ตรวจสอบค่า (ที่ดึงมา)
    selected_chronics = [rel['cn_id'] for rel in u_cn_collection.find({'u_id': user_u_id})]
    print(f'existing_cn_ids: {selected_chronics}')

    selected_medicines = [rel['md_id'] for rel in u_md_collection.find({'u_id': user_u_id})]
    print(f'existing_md_ids: {selected_medicines}')

    selected_allergys = [rel['ag_id'] for rel in u_ag_collection.find({'u_id': user_u_id})]
    print(f'existing_ag_ids: {selected_allergys}')

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
    balancing = int(request.form.get('balancing', 0))

    input_data = pd.DataFrame({
        'pregnant': [pregnant],
        'dizziness1': [dizziness1],
        'Palpitations': [Palpitations],
        'squeamish': [squeamish],
        'vomit': [vomit],
        'dizziness2': [dizziness2],
        'dizziness3': [dizziness3],
        'dizziness4': [dizziness4],
        'colic1': [colic1],
        'tired': [tired],
        'cannot_sleep': [cannot_sleep],
        'flatulence': [flatulence],
        'stomach_ache': [stomach_ache],
        'constipation1': [constipation1],
        'diarrhea1': [diarrhea1],
        'hemorrhoids': [hemorrhoids],
        'menstruation': [menstruation],
        'Menstrual_cramps': [Menstrual_cramps],
        'postpartum_woman': [postpartum_woman],
        'Lochia': [Lochia],
        'Vaginal_Discharge': [Vaginal_Discharge],
        'Nourish_blood': [Nourish_blood],
        'fever1': [fever1],
        'inner_heat': [inner_heat],
        'Measles': [Measles],
        'Chickenpox': [Chickenpox],
        'fever2': [fever2],
        'fever3': [fever3],
        'cough': [cough],
        'phlegm': [phlegm],
        'cold': [cold],
        'Allergic_Rhinitis': [Allergic_Rhinitis],
        'body_aches': [body_aches],
        'tendon': [tendon],
        'Tight_numb': [Tight_numb],
        'muscles_tendons': [muscles_tendons],
        'dizziness5': [dizziness5],
        'balancing': [balancing]
    })

    # ทำนายความน่าจะเป็น
    probabilities = clf.predict_proba(input_data)[0]

    # สร้างลิสต์ของ hm_id ที่ต้องการลบออกจากผลทำนาย
    hm_ids_to_remove = set()

    # ถ้า อายุ < 1 ลบ
    if age < 1:
        hm_ids_to_remove.update([312, 315, 316, 317, 340, 342, 343])

    # ถ้า อายุ < 12 ลบ
    if age < 12:
        hm_ids_to_remove.update([315, 316, 340, 342, 343])

    # ถ้า ตั้งครรภ์ ลบ
    if pregnant == 1:
        hm_ids_to_remove.update([303, 305, 306, 309, 310, 311, 312, 313, 314, 316, 317,
                                 321, 322, 323, 324, 325, 340, 341, 342, 343, 344, 346])
    
    # ถ้า มีไข้ ลบ
    if fever1 == 1:
        hm_ids_to_remove.update([303, 306, 309, 310, 311, 312, 313, 314, 315, 316, 317,
                                 321, 322, 323, 324, 325, 326, 340, 341, 343, 344, 346])
    
    # ถ้า คลื่นไส้ ลบ
    if squeamish == 1:
        hm_ids_to_remove.add(315)

    # ถ้า อาเจียน ลบ
    if vomit == 1:
        hm_ids_to_remove.add(315)

    # ถ้า ให้นมบุตร ลบ
    if breastfeeding == 1:
        hm_ids_to_remove.add(342)

    # ถ้า cn_id = 101 (เบาหวาน) ลบ
    if 101 in selected_chronics:
        hm_ids_to_remove.add(334)

    # ถ้า cn_id = 111 (ไซนัส) ลบ
    if 111 in selected_chronics:
        hm_ids_to_remove.add(340)

    # ถ้า cn_id = 113 (ภาวะลำไส้อุดตัน) ลบ
    if 113 in selected_chronics:
        hm_ids_to_remove.add(315)

    # ถ้า cn_id = 114 (โรคหัวใจ) ลบ
    if 114 in selected_chronics:
        hm_ids_to_remove.add(346)

    # ถ้า cn_id = 115 (โรคแผลเปื่อยเพปติก) ลบ
    if 115 in selected_chronics:
        hm_ids_to_remove.add(346)

    # ถ้า cn_id = 116 (กรดไหลย้อน) ลบ
    if 116 in selected_chronics:
        hm_ids_to_remove.add(346)

    # ถ้า ag_id = 601 (แพ้ละอองเกสรดอกไม้) ลบ
    if 601 in selected_allergys:
        hm_ids_to_remove.update([301, 302, 303, 304, 305, 326, 327, 329, 330, 341, 342])

    # ถ้า md_id = 401 (anticoagulant-ยาในกลุ่มสารกันเลือดเป็นลิ่ม) ลบ
    if 401 in selected_medicines:
        hm_ids_to_remove.update([301, 302, 303, 304, 305, 306, 312, 313, 314, 316, 317, 326,
                                 330, 341, 342])
    
    # ถ้า md_id = 402 (antiplatelets-ยาต้านการจับตัวของเกล็ดเลือด) ลบ
    if 402 in selected_medicines:
        hm_ids_to_remove.update([301, 302, 303, 304, 305, 306, 312, 313, 314, 316, 317, 326,
                                 330, 341, 342])
        
    # ถ้า md_id = 403 (phenytoin-ยาต้านชัก) ลบ
    if 403 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])

    # ถ้า md_id = 404 (propranolol-ยารักษาภาวะที่เกี่ยวกับหัวใจและระบบไหลเวียนโลหิต) ลบ
    if 404 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])

    # ถ้า md_id = 405 (theophylline-ยาในกลุ่มยารักษาโรคหอบหืด) ลบ
    if 405 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])

    # ถ้า md_id = 406 (rifampicin-ยารักษาวัณโรค รักษาการติดเชื้อในจมูกและลำคอ) ลบ
    if 406 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])


    # กรองผลลัพธ์ที่มีความน่าจะเป็นมากกว่า 0
    predictions = []
    for i, prob in enumerate(probabilities):
        if prob > 0:
            hm_id = clf.classes_[i]
            hm_name = get_hm_name(hm_id)
            hm_dosage = get_hm_dosage(hm_id)
            hm_recipe = get_hm_recipe(hm_id)
            symptoms = get_symptoms_for_herbal(hm_id)
            warnings = get_warnings_for_herbal(hm_id)

            # ตรวจสอบว่า hm_id อยู่ในลิสต์ที่ต้องการลบหรือไม่
            if hm_id in hm_ids_to_remove:
                # ถ้าอยู่ในลิสต์ที่ต้องการลบ ให้ข้ามไปยังผลทำนายถัดไป
                continue

            # เพิ่มข้อมูลยาลงใน list
            predictions.append({
                'hm_id': hm_id,
                'probability': prob,
                'hm_name': hm_name,
                'hm_dosage': hm_dosage,
                'hm_recipe': hm_recipe,
                'symptoms': symptoms,
                'warnings': warnings
            })

    return render_template('member_result.html', predictions=predictions)

@app.route('/predict', methods=['POST'])
def predict():
    # ดึงข้อมูลจากฟอร์ม

    dob_str = request.form['dob']    # แปลงวันเกิดเป็น datetime object
    dob = datetime.strptime(dob_str, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

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
    balancing = int(request.form.get('balancing', 0))

    selected_chronics = request.form.getlist('chronics')
    selected_allergys = request.form.getlist('allergys')
    selected_medicines = request.form.getlist('medicines')
    breastfeeding = int(request.form.get('breastfeeding', 0))

    # สร้าง DataFrame จากข้อมูลที่ได้รับ
    input_data = pd.DataFrame({
        'pregnant': [pregnant],
        'dizziness1': [dizziness1],
        'Palpitations': [Palpitations],
        'squeamish': [squeamish],
        'vomit': [vomit],
        'dizziness2': [dizziness2],
        'dizziness3': [dizziness3],
        'dizziness4': [dizziness4],
        'colic1': [colic1],
        'tired': [tired],
        'cannot_sleep': [cannot_sleep],
        'flatulence': [flatulence],
        'stomach_ache': [stomach_ache],
        'constipation1': [constipation1],
        'diarrhea1': [diarrhea1],
        'hemorrhoids': [hemorrhoids],
        'menstruation': [menstruation],
        'Menstrual_cramps': [Menstrual_cramps],
        'postpartum_woman': [postpartum_woman],
        'Lochia': [Lochia],
        'Vaginal_Discharge': [Vaginal_Discharge],
        'Nourish_blood': [Nourish_blood],
        'fever1': [fever1],
        'inner_heat': [inner_heat],
        'Measles': [Measles],
        'Chickenpox': [Chickenpox],
        'fever2': [fever2],
        'fever3': [fever3],
        'cough': [cough],
        'phlegm': [phlegm],
        'cold': [cold],
        'Allergic_Rhinitis': [Allergic_Rhinitis],
        'body_aches': [body_aches],
        'tendon': [tendon],
        'Tight_numb': [Tight_numb],
        'muscles_tendons': [muscles_tendons],
        'dizziness5': [dizziness5],
        'balancing': [balancing]
    })

    # ทำนายความน่าจะเป็น
    probabilities = clf.predict_proba(input_data)[0]

    # สร้างลิสต์ของ hm_id ที่ต้องการลบออกจากผลทำนาย
    hm_ids_to_remove = set()

    # ถ้า อายุ < 1 ลบ
    if age < 1:
        hm_ids_to_remove.update([312, 315, 316, 317, 340, 342, 343])

    # ถ้า อายุ < 12 ลบ
    if age < 12:
        hm_ids_to_remove.update([315, 316, 340, 342, 343])

    # ถ้า ตั้งครรภ์ ลบ
    if pregnant == 1:
        hm_ids_to_remove.update([303, 305, 306, 309, 310, 311, 312, 313, 314, 316, 317,
                                 321, 322, 323, 324, 325, 340, 341, 342, 343, 344, 346])
    
    # ถ้า มีไข้ ลบ
    if fever1 == 1:
        hm_ids_to_remove.update([303, 306, 309, 310, 311, 312, 313, 314, 315, 316, 317,
                                 321, 322, 323, 324, 325, 326, 340, 341, 343, 344, 346])
    
    # ถ้า คลื่นไส้ ลบ
    if squeamish == 1:
        hm_ids_to_remove.add(315)

    # ถ้า อาเจียน ลบ
    if vomit == 1:
        hm_ids_to_remove.add(315)

    # ถ้า ให้นมบุตร ลบ
    if breastfeeding == 1:
        hm_ids_to_remove.add(342)

    # ถ้า cn_id = 101 (เบาหวาน) ลบ
    if 101 in selected_chronics:
        hm_ids_to_remove.add(334)

    # ถ้า cn_id = 111 (ไซนัส) ลบ
    if 111 in selected_chronics:
        hm_ids_to_remove.add(340)

    # ถ้า cn_id = 113 (ภาวะลำไส้อุดตัน) ลบ
    if 113 in selected_chronics:
        hm_ids_to_remove.add(315)

    # ถ้า cn_id = 114 (โรคหัวใจ) ลบ
    if 114 in selected_chronics:
        hm_ids_to_remove.add(346)

    # ถ้า cn_id = 115 (โรคแผลเปื่อยเพปติก) ลบ
    if 115 in selected_chronics:
        hm_ids_to_remove.add(346)

    # ถ้า cn_id = 116 (กรดไหลย้อน) ลบ
    if 116 in selected_chronics:
        hm_ids_to_remove.add(346)

    # ถ้า ag_id = 601 (แพ้ละอองเกสรดอกไม้) ลบ
    if 601 in selected_allergys:
        hm_ids_to_remove.update([301, 302, 303, 304, 305, 326, 327, 329, 330, 341, 342])

    # ถ้า md_id = 401 (anticoagulant-ยาในกลุ่มสารกันเลือดเป็นลิ่ม) ลบ
    if 401 in selected_medicines:
        hm_ids_to_remove.update([301, 302, 303, 304, 305, 306, 312, 313, 314, 316, 317, 326,
                                 330, 341, 342])
    
    # ถ้า md_id = 402 (antiplatelets-ยาต้านการจับตัวของเกล็ดเลือด) ลบ
    if 402 in selected_medicines:
        hm_ids_to_remove.update([301, 302, 303, 304, 305, 306, 312, 313, 314, 316, 317, 326,
                                 330, 341, 342])
        
    # ถ้า md_id = 403 (phenytoin-ยาต้านชัก) ลบ
    if 403 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])

    # ถ้า md_id = 404 (propranolol-ยารักษาภาวะที่เกี่ยวกับหัวใจและระบบไหลเวียนโลหิต) ลบ
    if 404 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])

    # ถ้า md_id = 405 (theophylline-ยาในกลุ่มยารักษาโรคหอบหืด) ลบ
    if 405 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])

    # ถ้า md_id = 406 (rifampicin-ยารักษาวัณโรค รักษาการติดเชื้อในจมูกและลำคอ) ลบ
    if 406 in selected_medicines:
        hm_ids_to_remove.update([313, 315, 316, 322, 340, 344, 346])


    # กรองผลลัพธ์ที่มีความน่าจะเป็นมากกว่า 0
    predictions = []
    for i, prob in enumerate(probabilities):
        if prob > 0:
            hm_id = clf.classes_[i]
            hm_name = get_hm_name(hm_id)
            hm_dosage = get_hm_dosage(hm_id)
            hm_recipe = get_hm_recipe(hm_id)
            symptoms = get_symptoms_for_herbal(hm_id)
            warnings = get_warnings_for_herbal(hm_id)

            # ตรวจสอบว่า hm_id อยู่ในลิสต์ที่ต้องการลบหรือไม่
            if hm_id in hm_ids_to_remove:
                # ถ้าอยู่ในลิสต์ที่ต้องการลบ ให้ข้ามไปยังผลทำนายถัดไป
                continue

            # เพิ่มข้อมูลยาลงใน list
            predictions.append({
                'hm_id': hm_id,
                'probability': prob,
                'hm_name': hm_name,
                'hm_dosage': hm_dosage,
                'hm_recipe': hm_recipe,
                'symptoms': symptoms,
                'warnings': warnings
            })

    # สร้างแผนผังของ Random Forest (เลือกต้นไม้หนึ่ง)
    # ดึงต้นไม้แรกจาก RandomForestClassifier
    tree = clf.estimators_[0]

    # สร้างแผนผังด้วย export_graphviz
    dot_data = export_graphviz(tree, out_file=None, 
                               feature_names=feature_cols,  
                               class_names=[str(i) for i in clf.classes_],  
                               filled=True, rounded=True,  
                               special_characters=True)

    # ใช้ pydotplus เพื่อสร้างกราฟจาก dot_data
    graph = pydotplus.graph_from_dot_data(dot_data)

    # บันทึกกราฟลงในไฟล์ .png
    plot_filename = 'static/plots/tree_plot.png'
    graph.write_png(plot_filename)
    
    return render_template('general_result.html', predictions=predictions)

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)