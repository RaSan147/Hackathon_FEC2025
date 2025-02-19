import hashlib
import os
import re
import shutil
import sys
import time
import json
from http import HTTPStatus
import traceback
from collections import Counter

import requests

from pyroboxCore import config as CoreConfig, logger, DealPostData as DPD, runner as pyroboxRunner, tools, reload_server, __version__, SimpleHTTPRequestHandler as SH
from pyroDB import PickleTable

from tools import xpath, make_dir, os_scan_walk
from print_text3 import xprint

from emergency_protocols import emergency

DATA_DIR = make_dir('data')

Dusers = PickleTable(xpath(DATA_DIR, 'users.pdb'))
Dusers.add_columns(['uid', 'username', 'passwordHash', 'email', 'previllage', 'api_key'], exist_ok=True)

Dexam_rooms = PickleTable(xpath(DATA_DIR, 'exam_rooms.pdb'))
Dexam_rooms.add_columns(["uid", "room_number", "seat_number"], exist_ok=True)


Dstudents = PickleTable(xpath(DATA_DIR, 'students.pdb'))
Dstudents.add_columns(['uid', 'dept', 'student_id', 'wifi_login_count', 'last_wifi_login'], exist_ok=True)

Dwifi_logins = PickleTable(xpath(DATA_DIR, 'wifi_logins.pdb'))
Dwifi_logins.add_columns(['uid', 'timestamp'], exist_ok=True)

Dbooks = PickleTable(xpath(DATA_DIR, 'books.pdb'))
Dbooks.add_columns(['isbn', 'title', 'stock', 'borrower_uid'], exist_ok=True)

Dcanteen_orders = PickleTable(xpath(DATA_DIR, 'canteen_orders.pdb'))
Dcanteen_orders.add_columns(['order_id', 'student_id', 'items', 'total_price', 'order_time', "order_items"], exist_ok=True)

Dattendance = PickleTable(xpath(DATA_DIR, 'attendance.pdb'))
Dattendance.add_columns(['class_id', 'date', 'present_students'], exist_ok=True)

DnoticeBoard = PickleTable(xpath(DATA_DIR, 'notice_board.pdb'))
DnoticeBoard.add_columns(['title', 'content', 'date', 'id'], exist_ok=True)


def gen_timestamp_to_z(time_now=None, utc=True):
	"""
	converts timestamp (UTC) to "YYYY-MM-DDTHH:MM:SSZ"
	- time_now: timestamp (UTC)
	- utc: the provided timestamp is in UTC
	"""
	# format "YYYY-MM-DDTHH:MM:SSZ (UTC)"
	if time_now is None:
		time_now = time.time()
		utc = False

	if not utc:
		time_now = time.gmtime(time_now)

	return time.strftime("%Y-%m-%dT%H:%M:%SZ", time_now)


def gen_z_to_timestamp(z_time):
	"""
	converts "YYYY-MM-DDTHH:MM:SSZ" to timestamp (UTC)
	"""
	return time.mktime(time.strptime(z_time, "%Y-%m-%dT%H:%M:%SZ"))

# print(gen_timestamp_to_z())
# print(gen_z_to_timestamp(gen_timestamp_to_z()))

def type_check(data, types, self:SH):
	"""
	Checks the type of the data
	- data: data to be checked
	- types: expected types
	"""
	if not isinstance(data, types):
		self.send_json({"error": f"Invalid data type: {type(data)}, Expected: {types}"}, code=HTTPStatus.BAD_REQUEST)
		raise Exception(f"Invalid data type: {type(data)}, Expected: {types}")

def types_check(data:list, types, self:SH):
	"""
	Checks the type of the data
	- data: data to be checked
	- types: expected types
	"""
	for d in data:
		type_check(d, types, self)

def authenticate(self: SH, minimum_previllage=9, exact_previllage=None):
	"""
	Authentication function for the server (Uses both Bearer token and x-api-key)
	- minimum_previllage: minimum previllage level required to access the API
	- exact_previllage: exact previllage level required to access the API
	"""
	AUTH = self.headers.get('Authorization')
	if not AUTH:
		API_KEY = self.headers.get('x-api-key')

	else:
		AUTH = AUTH.split()
		if len(AUTH) != 2:
			return False

		if AUTH[0].lower() != 'bearer':
			return False

		API_KEY = AUTH[1]

	if not API_KEY:
		return False

	user = Dusers.find_1st_row(
		kw=API_KEY,
		column='api_key',
		full_match=True
	)

	if not user:
		return False

	if exact_previllage:
		if user['previllage'] != exact_previllage:
			return False

	if user['previllage'] < minimum_previllage:
		return False

	return True


def invalid_uid(uid:str):
	"""
	invalid cases:
	- 1: uid is not provided
	- 2: uid is not a number
	- 3: user not found
	"""
	if not uid:
		return 1

	# DDOS protection
	if isinstance(uid, str) and (len(uid) > 6 or not uid.isdigit()):
		return 2

	uid = int(uid)

	user = Dusers.find_1st_row(
		kw=uid,
		column='uid',
		full_match=True
	)

	if not user:
		return 3

	return user

def invalid_student_id(student_id:str):
	"""
	invalid cases:
	- 1: student_id is not provided
	- 2: student_id is not a number
	- 3: student not found
	"""
	if not student_id:
		return 1

	# DDOS protection
	if isinstance(student_id, str) and (len(student_id) > 8 or not student_id.isdigit()):
		return 2

	student_id = int(student_id)

	user = Dstudents.find_1st_row(
		kw=student_id,
		column='student_id',
		full_match=True
	)

	if not user:
		return 3

	return user


@SH.on_req("GET", url="/")
def index(self: SH, *args, **kwargs):
	DOC = open("./Doc.html").read()
	self.send_text(DOC)

@SH.on_req("GET", url="/api/health")
def health(self: SH, *args, **kwargs):
	return self.send_json(
		{
			"status": "ok",
			"server_time": gen_timestamp_to_z()
		}
	)

@SH.on_req("GET", url_regex="/api/exam-rooms/[^/]*")
def exam_rooms(self: SH, *args, **kwargs):
	"""
	From students to teachers, everyone can see their exam room number and seat number

	- expected URL: /api/exam-rooms/<student_id> (e.g. /api/exam-rooms/20222005)
	"""
	if not authenticate(self, minimum_previllage=1):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	student_id = re.search(r'/api/exam-rooms/([^/]*)', self.path).group(1)

	student = invalid_student_id(student_id)
	if student == 1:
		return self.send_json({"error": "Please provide the user ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 2:
		return self.send_json({"error": "Invalid user ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 3:
		return self.send_json({"error": "Student not found"}, code=HTTPStatus.NOT_FOUND)

	room_data = Dexam_rooms.find_1st_row(
		kw=student['student_id'],
		column='student_id',
		full_match=True
	)

	if not room_data:
		return self.send_json({"error": "No exam room assigned"}, code=HTTPStatus.NOT_FOUND)

	return self.send_json({
		"student_id": student['student_id'],
		"exam_room": f"Room {room_data['room_number']}",
		"seat_number": room_data['seat_number']
	})	


@SH.on_req("POST", url="/api/wifi-login")
def wifi_login_entry(self: SH, *args, **kwargs):
	"""
	For wifi login, the system will keep track of the number of logins and the last login time

	expected JSON data:
	{
		"student_id": 20222001,
		"timestamp": "2021-09-01T12:00:00Z"
	}
	"""
	# only admin/system can access this
	if not authenticate(self, exact_previllage=9):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	student_id = json_data.get('student_id', None)
	type_check(student_id, (int, str), self)
	last_login = json_data.get('timestamp', '')
	type_check(last_login, str, self)

	if not last_login:
		return self.send_json({"error": "Please provide the timestamp"}, code=HTTPStatus.BAD_REQUEST)

	try:
		last_login = gen_z_to_timestamp(last_login)
	except Exception as e:
		return self.send_json({"error": "Invalid timestamp format"}, code=HTTPStatus.BAD_REQUEST)


	student = invalid_student_id(student_id)
	if student == 1:
		return self.send_json({"error": "Please provide the student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 2:
		return self.send_json({"error": "Invalid student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 3:
		return self.send_json({"error": "Student not found"}, code=HTTPStatus.NOT_FOUND)

	Dwifi_logins.add_row(
		{
			'uid': student['uid'],
			'timestamp': round(last_login, 2)
		}
	)
	student["wifi_login_count"] += 1

	return self.send_json({
		"message": "Login recorded",
		"student_id": student['student_id'],
		"login_count": student['wifi_login_count']
	})


@SH.on_req("GET", url_regex="/api/library/book/[^/]*")
def library_book(self: SH, *args, **kwargs):
	"""
	Everyone can see the details of a book in the library

	- expected URL: /api/library/book/<isbn> (e.g. /api/library/book/978-0061120084)
	"""
	if not authenticate(self, minimum_previllage=1):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)


	isbn = re.search(r'/api/library/book/([^/]*)', self.path).group(1)

	book = Dbooks.find_1st_row(
		kw=isbn,
		column='isbn',
		full_match=True
	)

	if not book:
		return self.send_json({"error": "Book not found"}, code=HTTPStatus.NOT_FOUND)

	return self.send_json({
		"isbn": book['isbn'],
		"title": book['title'],
		"available": book['stock'] > 0,
		"copies_left": book['stock']
	})

@SH.on_req("POST", url="/api/library/book/borrow")
def library_borrow_book(self: SH, *args, **kwargs):
	"""
	Everyone can borrow a book from the library

	expected JSON data:
	{
		"uid": 1005,
		"isbn": "978-0061120084"
	}
	"""
	if not authenticate(self, minimum_previllage=9): 
		# only admin/system can access this
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	uid = json_data.get('uid', None)
	type_check(uid, (int, str), self)
	isbn = json_data.get('isbn', None)
	type_check(isbn, str, self)

	user = invalid_uid(uid)
	if user == 1:
		return self.send_json({"error": "Please provide the user ID"}, code=HTTPStatus.BAD_REQUEST)
	if user == 2:
		return self.send_json({"error": "Invalid user ID"}, code=HTTPStatus.BAD_REQUEST)
	if user == 3:
		return self.send_json({"error": "User not found"}, code=HTTPStatus.NOT_FOUND)


	book = Dbooks.find_1st_row(
		kw=isbn,
		column='isbn',
		full_match=True
	)


	if not book:
		return self.send_json({"error": "Book not found"}, code=HTTPStatus.NOT_FOUND)

	if book['stock'] == 0:
		return self.send_json({"error": "Book not available"}, code=HTTPStatus.BAD_REQUEST)

	book['stock'] -= 1
	borrowers = book['borrower_uid']
	if not borrowers:
		borrowers = []

	if user['uid'] in borrowers:
		return self.send_json({"error": "Book already borrowed by the user"}, code=HTTPStatus.BAD_REQUEST)

	borrowers.append(user['uid'])
	book['borrower_uid'] = borrowers


	return self.send_json({
		"message": "Book borrowed",
		"user_id": user['uid'],
		"isbn": book['isbn'],
		"copies_left": book['stock']
	})

@SH.on_req("POST", url="/api/library/book/return")
def library_return_book(self: SH, *args, **kwargs):
	"""
	Everyone can return a book to the library

	expected JSON data:
	{
		"uid": 1005,
		"isbn": "978-0061120084"
	}
	"""
	if not authenticate(self, minimum_previllage=9):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)
	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	uid = json_data.get('uid', '')
	type_check(uid, (int, str), self)
	isbn = json_data.get('isbn', '')
	type_check(isbn, str, self)

	user = invalid_uid(uid)
	if user == 1:
		return self.send_json({"error": "Please provide the user ID"}, code=HTTPStatus.BAD_REQUEST)
	if user == 2:
		return self.send_json({"error": "Invalid user ID"}, code=HTTPStatus.BAD_REQUEST)
	if user == 3:
		return self.send_json({"error": "User not found"}, code=HTTPStatus.NOT_FOUND)

	book = Dbooks.find_1st_row(
		kw=isbn,
		column='isbn',
		full_match=True
	)

	if not book:
		return self.send_json({"error": "Book not found"}, code=HTTPStatus.NOT_FOUND)

	borrowers = book['borrower_uid']
	if not borrowers:
		borrowers = []

	if user['uid'] not in borrowers:
		return self.send_json({"error": "Book not borrowed by the user"}, code=HTTPStatus.BAD_REQUEST)

	borrowers.remove(user['uid'])
	book['borrower_uid'] = json.dumps(borrowers)
	book['stock'] += 1

	return self.send_json({
		"message": "Book returned",
		"user_id": user['uid'],
		"isbn": book['isbn'],
		"copies_left": book['stock']
	})

@SH.on_req("POST", url="/api/canteen/order")
def canteen_order(self: SH, *args, **kwargs):
	"""
	Everyone can order food from the canteen

	expected JSON data:
	{
		"student_id": 20222001,
		"items": [
			{
				"item_id": "burger", "quantity": 2, "price": 100
			},
			{
				"item_id": "pizza", "quantity": 1, "price": 200
			}
		],
		"order_time": "2021-09-01T12:00:00Z"
	}
	"""
	if not authenticate(self, minimum_previllage=9):
		# System can enter the canteen order
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	student_id = json_data.get('student_id', '')
	type_check(student_id, (int, str), self)
	items = json_data.get('items', [])
	types_check(items, dict, self)
	order_time = json_data.get('order_time', '')
	type_check(order_time, str, self)

	try:
		order_time = gen_z_to_timestamp(order_time)
	except Exception as e:
		return self.send_json({"error": "Invalid timestamp format"}, code=HTTPStatus.BAD_REQUEST)

	if not items:
		return self.send_json({"error": "Please provide the items"}, code=HTTPStatus.BAD_REQUEST)

	student = invalid_student_id(student_id)
	if student == 1:
		return self.send_json({"error": "Please provide the student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 2:
		return self.send_json({"error": "Invalid student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 3:
		return self.send_json({"error": "Student not found"}, code=HTTPStatus.NOT_FOUND)

	total_price = 0
	for item in items:
		if not item.get('item_id') or not item.get('quantity') or not item.get('price'):
			return self.send_json({"error": "Please provide the item_id, quantity and price for each item"}, code=HTTPStatus.BAD_REQUEST)

		total_price += item['quantity'] * item['price']

	order_id = 1 if not Dcanteen_orders else Dcanteen_orders[-1]['order_id'] + 1

	Dcanteen_orders.add_row(
		{
			'order_id': order_id,
			'student_id': student['student_id'],
			'items': items,
			'total_price': total_price,
			'order_time': round(order_time, 2),
			'order_items': items
		}
	)

	return self.send_json({
		"order_id": order_id,
		"status": "Order placed",
		"total_price": total_price
	})


@SH.on_req("POST", url="/api/attendance")
def attendance(self: SH, *args, **kwargs):
	"""
	Teacher can mark attendance for students
	
	expected JSON data:
	{
		"class_id": "CSE101",
		"date": "2025-02-11",
		"present_students": [20222001, 20222002, 20222003]
	}
	"""

	if not authenticate(self, minimum_previllage=3):
		# only teachers can access this
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	class_id = json_data.get('class_id', '')
	type_check(class_id, str, self)
	date = json_data.get('date', '')
	type_check(date, str, self)
	present_students = json_data.get('present_students', None)
	type_check(present_students, list, self)

	if not class_id:
		return self.send_json({"error": "Please provide the `class_id`"}, code=HTTPStatus.BAD_REQUEST)

	if not re.search(r'^\d{4}-\d{2}-\d{2}$', date):
		return self.send_json({"error": "Invalid `date` format, please provide in YYYY-MM-DD"}, code=HTTPStatus.BAD_REQUEST)

	if present_students is None:
		return self.send_json({"error": "Invalid `present_students` list"}, code=HTTPStatus.BAD_REQUEST)

	for student_id in present_students:
		student = invalid_student_id(student_id)
		if student == 1:
			return self.send_json({"error": "A blank student ID found"}, code=HTTPStatus.BAD_REQUEST)
		if student == 2:
			return self.send_json({"error": f"Invalid student ID: {student_id}"}, code=HTTPStatus.BAD_REQUEST)
		if student == 3:
			return self.send_json({"error": f"Student not found with ID: {student_id}"}, code=HTTPStatus.NOT_FOUND)

	row = Dattendance.add_row(
		{
			'class_id': class_id,
			'date': date,
			'present_students': present_students
		}
	)

	print(row)

	return self.send_json({
		"status": "Attendance recorded",
		"total_present": len(present_students)
	})

@SH.on_req("GET", url_regex="/api/attendance/[^/]*")
def attendance_mark(self: SH, *args, **kwargs):
	"""
	Teacher can see the attendance of a class

	- expected URL: /api/attendance/<class_id> (e.g. /api/attendance/CSE101)
	"""
	if not authenticate(self, minimum_previllage=3):
		# only teachers can access this
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	class_id = re.search(r'/api/attendance/([^/]*)', self.path).group(1)

	attendance = Dattendance.search(
		kw=class_id,
		column='class_id',
		return_row=True,
		full_match=True
	)

	if not attendance:
		return self.send_json({"error": "No attendance recorded"}, code=HTTPStatus.NOT_FOUND)

	total_classes = len(attendance)
	students_attendance_overall = []
	for row in attendance:
		students_attendance_overall.extend(row['present_students'])

	students_attendance_overall = dict(Counter(students_attendance_overall))

	students_attendance_rate = {student_id: f"{round(students_attendance_overall[student_id]*100 / total_classes, 2)}%" for student_id in students_attendance_overall}

	return self.send_json({
		"class_id": class_id,
		"total_classes": total_classes,
		"students_attendance_rate": students_attendance_rate
	})

@SH.on_req("POST", url="/api/emergency")
def emergency(self: SH, *args, **kwargs):
	"""
	Everyone can report an emergency

	- expected JSON data: 
	{
		"type": "Medical",
		"location": "Building A",
		"details": "Ratul is sleepy and dying"
	}
	"""
	if not authenticate(self, minimum_previllage=1):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	issue = json_data.get('type', '')
	type_check(issue, str, self)
	location = json_data.get('location', '')
	type_check(location, str, self)
	details = json_data.get('details', '')
	type_check(details, str, self)

	if not issue:
		return self.send_json({"error": "Please provide the issue type"}, code=HTTPStatus.BAD_REQUEST)

	return self.send_json({
		"message": "Emergency alert sent",
		"response_team": emergency(issue, location, details)
	})

@SH.on_req("Post", url="/api/notices")
def publish_notices(self: SH, *args, **kwargs):
	"""
	Teachers can publish notices for students

	expected JSON data:
	[
		{
			"title": "Pitha Utshob",
			"content": "Pitha Utshob will be held on 28th February 2025",
			"date": "2025-02-11"
		},
		{
			"title": "Holiday Notice",
			"content": "The university will remain closed on 21st February 2025",
			"date": "2025-02-11"
		}
	]
	"""
	if not authenticate(self, minimum_previllage=5):
		# assistant principal and above can access this
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	for notice in json_data:
		title = notice.get('title', None)
		content = notice.get('content', None)
		date = notice.get('date', None)
		if not title or not content or not date:
			return self.send_json({"error": "Please provide the title, content and date for each notice"}, code=HTTPStatus.BAD_REQUEST)

		types_check([title, content, date], str, self)

	for notice in json_data:
		last_id = 1 if not DnoticeBoard else DnoticeBoard[-1]['id'] + 1

		DnoticeBoard.add_row(
			{
				'title': notice['title'],
				'content': notice['content'],
				'date': notice['date'],
				'id': last_id
			}
		)

	return self.send_json({
		"message": "Notices published",
		"new_notices": len(json_data)
	})

@SH.on_req("GET", url="/api/notices")
def get_notices(self: SH, *args, **kwargs):
	"""
	Everyone can see the notices

	- expected URL: /api/notices
	- expected output: list of notices
	- optional query parameter: ?date=2025-02-11
	- optional query parameter: ?per_page=10&page=1
	- optional query parameter: ?sort=asc
	"""

	if not authenticate(self, minimum_previllage=1):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	date = self.query.get('date', '')
	per_page = self.query.get('per_page', 10)
	page = self.query.get('page', 1)
	sort = self.query.get('sort', 'desc') # newest first

	types_check([per_page, page], int, self)
	types_check([sort, date], str, self)

	if date:
		notices = DnoticeBoard.search_iter_row(
			kw=date,
			column='date',
			full_match=True
		)
	else:
		notices = DnoticeBoard.rows()

	if sort == 'asc':
		notices = sorted(notices, key=lambda x: x['date'])
	else:
		notices = sorted(notices, key=lambda x: x['date'], reverse=True)

	start = (page - 1) * per_page
	end = start + per_page

	return self.send_json(notices[start:end])


@SH.on_req("GET", url_regex="/api/students/[0-9]*")
def get_student(self: SH, *args, **kwargs):
	"""
	Everyone can see the details of a student.

	- expected URL: /api/students/<student_id> (e.g. /api/students/20222001)
	"""

	if not authenticate(self, minimum_previllage=1):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	student_id = re.search(r'/api/students/([0-9]*)', self.path).group(1)

	print("student_id", student_id)

	student = invalid_student_id(student_id)
	if student == 1:
		return self.send_json({"error": "Please provide the student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 2:
		return self.send_json({"error": "Invalid student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 3:
		return self.send_json({"error": "Student not found"}, code=HTTPStatus.NOT_FOUND)

	print("student", student)

	user = Dusers.find_1st_row(
		kw=student['uid'],
		column='uid',
		full_match=True
	)

	if not user:
		return self.send_json({"error": "User not found"}, code=HTTPStatus.NOT_FOUND)

	return self.send_json({
		"id": student['uid'],
		"name": user['username'],
		"student_id": student['student_id'],
		"department": student['dept']
	})

@SH.on_req("POST", url="/api/students")
def add_student(self: SH, *args, **kwargs):
	"""
	Only admin can add a student

	expected JSON data:
	{
		"name": "Ratul",
		"student_id": 20222001,
		"dept": "CSE",
		"password": "12345",
		"email": "e@mail.com"
	}
	"""
	if not authenticate(self, minimum_previllage=9):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	name = json_data.get('name', '')
	student_id = json_data.get('student_id', '')
	dept = json_data.get('dept', '')
	password = json_data.get('password', '')
	email = json_data.get('email', '')

	types_check([name, dept, email, password], str, self)

	student = invalid_student_id(student_id)
	if student == 1:
		return self.send_json({"error": "Please provide the student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 2:
		return self.send_json({"error": "Invalid student ID"}, code=HTTPStatus.BAD_REQUEST)
	if isinstance(student, dict):
		return self.send_json({"error": "Student already exists"}, code=HTTPStatus.BAD_REQUEST)
	
	if not dept:
		return self.send_json({"error": "Please provide the department"}, code=HTTPStatus.BAD_REQUEST)

	if not password:
		return self.send_json({"error": "Please provide a password with at least 5 characters"}, code=HTTPStatus.BAD_REQUEST)


	last_id = 1 if not Dstudents else Dstudents[-1]['uid'] + 1

	Dstudents.add_row(
		{
			'uid': last_id,
			'student_id': student_id,
			'dept': dept,
			'wifi_login_count': 0,
			'last_wifi_login': None
		}
	)

	Dusers.add_row(
		{
			'uid': last_id,
			'username': name,
			'passwordHash': hashlib.md5(password.encode()).hexdigest(),
			'email': email,
			'previllage': 1,
			'api_key': hashlib.md5(f"student_{student_id}{password}".encode()).hexdigest()
		}
	)

	return self.send_json({
		"status": "Created",
		"id": last_id,
		"name": name,
		"student_id": student_id,
		"department": dept
	})

@SH.on_req("PUT", url_regex="/api/students/[0-9]*")
def update_student(self: SH, *args, **kwargs):
	"""
	Only admin can update a student

	expected JSON data:
	{
		"name": "Ratul", # optional
		"student_id": 20222001, # optional
		"dept": "CSE", # optional
		"password": "12345", # optional
		"email": "" # optional
	}

	- expected URL: /api/students/<student_id> (e.g. /api/students/20222001)
	"""

	if not authenticate(self, minimum_previllage=9):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	try:
		post = DPD(self)
		post.start()
		json_data = post.get_json()
	except Exception as e:
		return self.send_json({"error": "Invalid JSON data"}, code=HTTPStatus.BAD_REQUEST)

	student_id = re.search(r'/api/students/([0-9]*)', self.path).group(1)

	student = invalid_student_id(student_id)
	if student == 1:
		return self.send_json({"error": "Please provide the student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 2:
		return self.send_json({"error": "Invalid student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 3:
		return self.send_json({"error": "Student not found"}, code=HTTPStatus.NOT_FOUND)

	dept = json_data.get('dept', student['dept'])

	user = Dusers.find_1st_row(
		kw=student['uid'],
		column='uid',
		full_match=True
	)
	name = json_data.get('name', user['username'])
	password = json_data.get('password', None)
	email = json_data.get('email', user['email'])

	types_check([name, dept, email], str, self)
	type_check(password, (str, type(None)), self)


	if not name:
		return self.send_json({"error": "Please provide the name"}, code=HTTPStatus.BAD_REQUEST)
	if not dept:
		return self.send_json({"error": "Please provide the department"}, code=HTTPStatus.BAD_REQUEST)
	if not email:
		return self.send_json({"error": "Please provide the email"}, code=HTTPStatus.BAD_REQUEST)
	if password is not None and len(password) < 5:
		return self.send_json({"error": "Password must be at least 5 characters long"}, code=HTTPStatus.BAD_REQUEST)

	if not user:
		return self.send_json({"error": "User not found"}, code=HTTPStatus.NOT_FOUND)



	student["dept"] = dept

	if password:
		hashedPassword = hashlib.md5(password.encode()).hexdigest()
	else:
		hashedPassword = user['passwordHash']

	user['passwordHash'] = hashedPassword
	user['username'] = name
	user['email'] = email




	return self.send_json({
		"status": "Updated",
		"id": student['uid'],
		"name": name,
		"student_id": student_id,
		"department": dept
	})

@SH.on_req("DELETE", url_regex="/api/students/[0-9]*")
def delete_student(self: SH, *args, **kwargs):
	"""
	Only admin can delete a student

	- expected URL: /api/students/<student_id> (e.g. /api/students/20222001)
	"""
	if not authenticate(self, minimum_previllage=9):
		return self.send_json({"error": "Unauthorized"}, code=HTTPStatus.UNAUTHORIZED)

	student_id = re.search(r'/api/students/([0-9]*)', self.path).group(1)

	student = invalid_student_id(student_id)
	if student == 1:
		return self.send_json({"error": "Please provide the student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 2:
		return self.send_json({"error": "Invalid student ID"}, code=HTTPStatus.BAD_REQUEST)
	if student == 3:
		return self.send_json({"error": "Student not found"}, code=HTTPStatus.NOT_FOUND)

	uid = student['uid']

	user = Dusers.find_1st_row(
		kw=uid,
		column='uid',
		full_match=True
	)

	if not user:
		return self.send_json({"error": "User not found"}, code=HTTPStatus.NOT_FOUND)

	student.del_row()
	user.del_row()

	return self.send_json({
		"status": "Deleted",
		"id": uid,
		"student_id": student_id
	})





pyroboxRunner(
	port=8080,
	directory='../').run()