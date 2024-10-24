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
chronics_data_collection = db['chronics_data']
trains_collection = db['trains']
herbals_data_collection = db['herbals_data']

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
    users = users_collection.find()

    return render_template('manage_members.html', users=users)

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)