from flask import Flask, render_template, url_for, redirect, request, send_file
from models import *
import time
import os
import datetime
from werkzeug.utils import secure_filename
import random
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

app.config["IMAGE_UPLOADS"] = "static/uploads"

handler = RotatingFileHandler('clinic.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

db = Database()

session_id = gen_session_id()
session_user = []
admin_name = None

@app.template_filter()
def getdate(string):
	return datetime.datetime.strptime(string, "%Y-%m-%d").date()

@app.errorhandler(500)
def error():
    return render_template('500.html')

@app.errorhandler(404)
def nopage(e):
	return render_template('404.html')

@app.route('/', methods=['GET', 'POST'])
def index():
	data = {
		"error": "Incorrect username or password"
	}
	global admin_name
	global session_user
	admin_name = request.form.get('username')
	session_user.append(db.select_validate_login(admin_name))
	if request.method == 'POST':
		if db.validate_login(admin_name, f"{request.form.get('password')}"):
			for i in session_user:
				try:
				    if i[3] == admin_name:
				        user = i
				        app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} logged in from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session_id}")
				except:
					user = 'NULL'
			return redirect(f'/home/{session_id}')
		app.logger.info(f"LOG INFO: User tried to log in from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} with credentials (usernme: {admin_name}, password: {request.form.get('password')})  at {datetime.datetime.today()}")
		return render_template('index.html', **data)
	return render_template('index.html')

@app.route('/logs/<session>')
def log(session):
    if session == session_id:
        data = {
            "lines" : [],
            "dept": db.retrieve_department(),
            "session": session_id
        }
        lines = []
        with open('clinic.log', 'r') as f:
            for line in f:
                lines.append(line)
        data['lines'] = lines
        try:
            return render_template('log.html', **data)
        except:
            return render_template('500.html')
    return render_template('404.html')

@app.route('/home/<session>')
def home(session):
    if session == session_id:
        global admin_name
        category = [
            'Antipyretics',
    		'Analgesics',
    		'Antimalarial',
    		'Antibiotics',
    		'Antiseptics',
    		'Oral contraceptives',
    		'Stimulants',
    		'Mood Stabilizers',
    		'Tranquilizers',
    		'Statins'
        ]

        data = {
            "patients": len(db.retrieve_patient(None, True)),
    		"appointment": len(db.retrieve_appointment(None, True)),
    		"stay": len(db.retrieve_stay()),
    		"med": len(db.retrieve_medication()),
    		"dept": db.retrieve_department(),
    		"staff": db.retrieve_len_staff(),
    		"count_med": [i for i in zip(category, [db.count_medicines(x) for x in category])],
    		"session": session_id,
    		"user": db.retrieve_auth_pwd(admin_name),
        }

        for i in session_user:
        	try:
        		if i[3] == admin_name:
        			user = i
        			app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited home page from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session_id}")
        	except:
        		user = 'NULL'

        	continue
        return render_template('home.html', **data)
    return render_template('404.html')

@app.route('/logout/<session>', methods=['GET', 'POST'])
def logout(session):
	if session == session_id:
		data = {
			"error": "Incorrect username or password"
		}

		global admin_name
		for i in session_user:
			try:
				if i[3] == admin_name:
					user = i
					app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} logged out from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session_id}")
			except:
				user = 'NULL'
		return redirect('/')
	return render_template('404.html')

@app.route('/ask_patient/<session>', methods=['GET', 'POST'])
def patient(session):
	data = {
		"dept": db.retrieve_department(),
		"session": session_id
	}

	dept = {
		"session": session_id
	}

	if session == session_id:
		global admin_name
		for i in session_user:
			try:
				if i[3] == admin_name:
					user = i
					app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited page ask_patient from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			except:
				user = 'NULL'
		if request.method == 'POST':
			patient_id = request.form.get("id")
			if db.validate_patient(patient_id):
				# admin_name = session_user[0]
				app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} searched patient with id {patient_id} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
				return redirect(f'/patient/{patient_id}/{session_id}')
			app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} tried to search patient with id {patient_id} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			data['msg'] = 'error'
			return render_template('ask_patient.html', **data)
		return render_template('ask_patient.html', **dept)
	return render_template('404.html')

@app.route('/patient_record/<session>')
def records(session):
	data = {
		"records": db.retrieve_patient(None, True),
		"dept": db.retrieve_department(),
		"session": session_id
	}
	if session == session_id:
		global admin_name
		for i in session_user:
			try:
				if i[3] == admin_name:
					user = i
					app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited patient records from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			except:
				user = 'NULL'
		return render_template('patient_record.html', **data)
	return render_template('404.html')

@app.route('/add_patient/<session>', methods=['GET', 'POST'])
def add_patient(session):
	data = {
		"dept": db.retrieve_department(),
		"session": session_id
	}

	dept = {
		"dept": db.retrieve_department(),
		"session":session_id
	}

	if session == session_id:
		global admin_name
		for i in session_user:
			try:
				if i[3] == admin_name:
					user = i
					app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited page add_patient from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			except:
				user = 'NULL'
		if request.method == 'POST':
			image = request.files['img']
			patient_id = gen_id(1)
			if db.add_patient(request.form.get("f_name"), request.form.get("l_name"), int(request.form.get("age")), request.form.get("sex"), request.form.get("address"), patient_id):
				app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} added patient with id {patient_id} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
				image.save(f'/home/truepygod/mysite/static/uploads/{patient_id}.png')
				data['msg'] = "success"
				return render_template('add_patient.html', **data)
			data['msg'] = "error"
			render_template('add_patient.html', **data)
		return render_template('add_patient.html', **dept)
	return render_template('404.html')

@app.route('/patient/<patient_id>/<session>')
def patient_info(patient_id, session):
	data = {
		"info": db.retrieve_patient_info(patient_id),
		"pat": db.retrieve_patient(patient_id),
		"dept": db.retrieve_department(),
		"session": session_id
	}
	if session == session_id:
		global admin_name
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
					app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited patient record {patient_id} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			except:
				user = 'NULL'
		return render_template('patient.html', **data)
	return render_template('404.html')

@app.route('/department/<dept_id>/<session>', methods=['GET', 'POST'])
def department(dept_id, session):
	data = {
		"dept": db.retrieve_dept(dept_id),
		"staff": db.retrieve_dept_staff(dept_id),
		"depts": db.retrieve_department(),
		"session": session_id
	}

	if session == session_id:
		global admin_name
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
					app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited department {data['dept'][0][1]} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			except:
				user = 'NULL'
		if request.method == 'POST':
			image = request.files['img']
			staff_id= gen_id(4)
			f_name = request.form.get('f_name')
			l_name = request.form.get('l_name')
			title = request.form.get('title')
			admin_name = session_user[0]

			if db.validate_admin(user[3]):
				if db.add_staff(f_name, l_name, dept_id, title, staff_id):
					if db.add_auth(staff_id):
						#app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited patient record {patient_id} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
						app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} added {title} {f_name} {l_name} to department {data['dept'][0][1]} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
						image.save(os.path.join(app.config['IMAGE_UPLOADS'], f'{staff_id}.png'))
						return redirect(f'/department/{dept_id}/{session}')
				data['msg'] = "error"
				return render_template('department.html', **data)
			app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} tried to add {title} {f_name} {l_name} to department {data['dept'][0][1]} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			data['msg'] = "auth"
			return render_template('department.html', **data)

		return render_template('department.html', **data)
	return render_template('404.html')

@app.route('/appointment/<session>')
def appointment(session):
	data = {
		"info": db.retrieve_appointment(None, True),
		"dept": db.retrieve_department(),
		"today": datetime.datetime.today().date(),
		"session": session_id
	}

	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited appointment page from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
		return render_template('appointment.html', **data)
	return render_template('404.html')

@app.route('/add_appointment/<session>', methods=['GET', 'POST'])
def add_appointment(session):
	data = {
		"dept": db.retrieve_department(),
		"dept": db.retrieve_department(),
		"staff": db.retrieve_only_staff(),
		"session": session_id
	}

	dept = {
		"dept": db.retrieve_department(),
		"staff": db.retrieve_only_staff(),
		"session": session_id
	}

	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited add_appointment page from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
		if request.method == 'POST':
			if db.validate_staff(request.form.get('officer')):
				if db.validate_patient(request.form.get('patient')):
				    if db.add_appointment(request.form.get('patient'), request.form.get('officer'), request.form.get('date'), request.form.get('time')):
				    	app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} booked appointment between staff {request.form.get('officer')} and patient {request.form.get('patient')} on date {request.form.get('date')} and time {request.form.get('time')} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
				    	data['msg'] = 'success'
				    	return render_template('add_appointment.html', **data)
				    app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} tried to book an appointment between staff {request.form.get('officer')} and patient {request.form.get('patient')} on date {request.form.get('date')} and time {request.form.get('time')} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
				    data['msg'] = 'error'
				    return render_template('add_appointment.html', **data)
				data['msg'] = 'nopat'
				return render_template('add_appointment.html', **data)
			data['msg'] = 'nostaff'
			return render_template('add_appointment.html', **data)
		return render_template('add_appointment.html', **dept)
	return render_template('404.html')

@app.route('/hospitalization/<session>')
def stay(session):
	data = {
		"info": db.retrieve_stay(),
		"dept": db.retrieve_department(),
		"session": session_id
	}
	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited hospitalization records page from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")

		return render_template('hospitalization.html', **data)
	return render_template('404.html')

@app.route('/add_hospitalization/<session>', methods=['GET', 'POST'])
def add_hospitalization(session):
	data = {
		"dept": db.retrieve_department(),
		"session": session_id
	}

	dept = {
		"dept": db.retrieve_department(),
		"session": session_id
	}

	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		if request.method == 'POST':
			if db.add_stay(request.form.get('ward'), int(request.form.get('bed')), request.form.get('in'), request.form.get('out'), request.form.get('id')):
				app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} booked hospitalization for patient {request.form.get('id')} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
				data['success'] = "Added record successfully"
				return render_template('add_hospitalization.html', **data)
			app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} tried to book hospitalization for patient {request.form.get('id')} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			data['error'] = "Error, try again"
			return render_template('add_hospitalization.html', **data)
		return render_template('add_hospitalization.html', **dept)
	return render_template('404.html')

@app.route('/staff/<staff_id>/<session>')
def staff(staff_id, session):
    data = {
    	"dept": db.retrieve_department(),
    	"info": db.retrieve_staff_info(staff_id),
    	"staff": db.retrieve_staff(staff_id),
    	"count": db.retrieve_date_count,
    	"pres": db.retrieve_pres_count,
    	"today": datetime.datetime.today().date(),
    	"session": session_id,
    	"stf": db.retrieve_auth_pwd(staff_id),
    }

    if session == session_id:
        for i in session_user:
            try:
                global admin_name
                if i[3] == admin_name:
                    user = i
            except:
                user = 'NULL'

        data['session_user'] = user[3]
        print(data['session_user'])
        data["user"] = db.retrieve_auth_pwd(user[3])
        #print(data['session_user'])
        print(data['user'])
        return render_template('staff.html', **data)
    return render_template('404.html')

@app.route('/medications/<session>', methods=['GET','POST'])
def medication(session):
	data = {
		"info": db.retrieve_medication(),
		"dept": db.retrieve_department(),
		"count_med": db.count_medicines,
		"category": [
			'Antipyretics',
			'Analgesics',
			'Antimalarial',
			'Antibiotics',
			'Antiseptics',
			'Oral contraceptives',
			'Stimulants',
			'Mood Stabilizers',
			'Tranquilizers',
			'Statins'
		],
		"session": session_id
	}

	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited medications page from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")

		return render_template('medications.html', **data)
	return render_template('404.html')

@app.route('/category/<name>/<session>')
def category(name, session):
	data = {
		"info": db.get_med_cat(name),
		"dept": db.retrieve_department(),
		"session": session_id
	}

	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} visited medicine category {name} page from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
		return render_template('category.html', **data)
	return render_template('404.html')

@app.route('/search_medication/<session>', methods=['GET', 'POST'])
def search_med(session):
	data = {
		"len": len,
		"dept": db.retrieve_department(),
		"session": session_id
	}

	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		if request.method == 'POST':
			data['search'] = request.form.get("search")
			data['all'] = db.search_medication(request.form.get("search"))
			app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} searched for medication {data['search']} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")

		return render_template('search_medication.html', **data)
	return render_template('404.html')

@app.route('/add_medication/<session>', methods=['GET', 'POST'])
def add_medication(session):
	data = {
		"dept": db.retrieve_department(),
		"session": session_id
	}

	dept = {
		"dept": db.retrieve_department(),
		"session": session_id
	}

	if session == session_id:
		if request.method == 'POST':
			bat = gen_id(3)
			if db.add_medication(request.form.get("category"), request.form.get('name'), request.form.get('expiry'), request.form.get('stock'), bat):
				for i in session_user:
					try:
						global admin_name
						if i[3] == admin_name:
							user = i
					except:
						user = 'NULL'
				app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} added medication batch number {bat} and name {request.form.get('name')} with amount {request.form.get('stock')}from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
				data['msg'] = 'success'
				return render_template('add_medication.html', **data)
			app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} tried to add medication with batch number {bat} and name {request.form.get('name')} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
			data['msg'] = 'error'
			return render_template('add_medication.html', **data)
		return render_template('add_medication.html', **dept)
	return render_template('404.html')

@app.route('/add_prescription/<session>', methods=['GET', 'POST'])
def add_prescription(session):
	data = {
		"dept": db.retrieve_department(),
		"staff": db.retrieve_only_staff(),
		"session": session_id
	}
	dept = {
		"dept": db.retrieve_department(),
		"staff": db.retrieve_only_staff(),
		"session": session_id
	}

	if session == session_id:
		for i in session_user:
			try:
				global admin_name
				if i[3] == admin_name:
					user = i
			except:
				user = 'NULL'
		if request.method == 'POST':
			staff = request.form.get('staff')
			patient = request.form.get('patient')
			name = request.form.get('name')
			batch = request.form.get('batch')

			if db.validate_staff(request.form.get('staff')):
				if db.validate_patient(request.form.get('patient')):
					if db.validate_batch(request.form.get('batch')):
						if db.add_prescription(patient, staff, name):
							if db.update_stock(batch) != 'empty':
								app.logger.info(f"LOG INFO: {user[0]} {user[1]} {user[2]} prescribed medicine with batch {batch} and name {name} for patient {patient} by officer {staff} from IP : {request.environ.get('HTTP_X_REAL_IP', request.remote_addr)} at {datetime.datetime.today()} with session ID: {session}")
								data['msg'] = 'success'
								return render_template('add_prescription.html', **data)
							data['msg'] = 'empty'
							return render_template('add_prescription.html', **data)
						data['msg'] = "error"
						return render_template('add_prescription.html', **data)
					data['msg'] = 'nobat'
					return render_template('add_prescription.html', **data)
				data['msg'] = 'nopat'
				return render_template('add_prescription.html', **data)
			data['msg'] = 'nostaff'
			return render_template('add_prescription.html', **data)
		return render_template('add_prescription.html', **dept)
	return render_template('404.html')

#app.run(debug=True)