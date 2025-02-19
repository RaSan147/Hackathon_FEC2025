# University API Documentation

Welcome to the **University API**! This API allows students and administrators to interact with various university services, such as checking exam rooms, borrowing books, placing canteen orders, and more.

## **Endpoints Overview**

### **Health Check**
**GET** `/api/health`  
*Check the health of the API server.*  
#### **Response:**
```json
{
    "status": "ok",
    "server_time": "2024-05-16T10:30:00Z"
}
```

---
### **Exam Room Details**
**GET** `/api/exam-rooms/{student_id}`  
*Retrieve the exam room and seat number for a student.*  
#### **Parameters:**
- `student_id` (integer) – ID of the student

#### **Response:**
```json
{
    "student_id": 20222005,
    "exam_room": "Room 101",
    "seat_number": "A12"
}
```

---
### **WiFi Login Entry**
**POST** `/api/wifi-login`  
*Record a WiFi login entry for a student.*  
#### **Request Body:**
```json
{
    "student_id": 20222001,
    "timestamp": "2021-09-01T12:00:00Z"
}
```
#### **Response:**
```json
{
    "message": "Login recorded",
    "student_id": 20222001,
    "login_count": 5
}
```

---
### **Library Services**
#### **Get Book Details**
**GET** `/api/library/book/{isbn}`  
*Retrieve details of a book.*  
#### **Response:**
```json
{
    "isbn": "978-0061120084",
    "title": "The Alchemist",
    "available": true,
    "copies_left": 3
}
```

#### **Borrow a Book**
**POST** `/api/library/book/borrow`  
#### **Request Body:**
```json
{
    "uid": 1005,
    "isbn": "978-0061120084"
}
```
#### **Response:**
```json
{
    "message": "Book borrowed",
    "user_id": 1005,
    "isbn": "978-0061120084",
    "copies_left": 2
}
```

#### **Return a Book**
**POST** `/api/library/book/return`  
#### **Request Body:**
```json
{
    "uid": 1005,
    "isbn": "978-0061120084"
}
```
#### **Response:**
```json
{
    "message": "Book returned",
    "user_id": 1005,
    "isbn": "978-0061120084",
    "copies_left": 3
}
```

---
### **Canteen Orders**
**POST** `/api/canteen/order`  
*Place an order in the canteen.*  
#### **Request Body:**
```json
{
    "student_id": 20222001,
    "items": [
        { "item_id": "burger", "quantity": 2, "price": 100 },
        { "item_id": "pizza", "quantity": 1, "price": 200 }
    ],
    "order_time": "2021-09-01T12:00:00Z"
}
```
#### **Response:**
```json
{
    "order_id": 1,
    "status": "Order placed",
    "total_price": 400
}
```

---
### **Attendance Management**
#### **Mark Attendance**
**POST** `/api/attendance`  
#### **Request Body:**
```json
{
    "class_id": "CSE101",
    "date": "2025-02-11",
    "present_students": [20222001, 20222002, 20222003]
}
```
#### **Response:**
```json
{
    "status": "Attendance recorded",
    "total_present": 3
}
```

#### **Get Attendance Report**
**GET** `/api/attendance/report/{class_id}`  
#### **Response:**
```json
{
    "class_id": "CSE101",
    "total_classes": 10,
    "students_attendance_rate": {
        "20222001": "90%",
        "20222002": "80%",
        "20222003": "100%"
    }
}
```

---
### **Emergency Contact**
**POST** `/api/emergency-contact`  
#### **Request Body:**
```json
{
    "type": "Medical",
    "location": "Building A",
    "details": "Urgent medical attention needed"
}
```
#### **Response:**
```json
{
    "message": "Emergency alert sent",
    "response_team": "Medical team"
}
```

---
### **Notices Management**
#### **Publish Notices**
**POST** `/api/notices`  
#### **Request Body:**
```json
[
    { "title": "Pitha Utshob", "content": "Pitha Utshob will be held on 28th February 2025", "date": "2025-02-11" },
    { "title": "Holiday Notice", "content": "The university will remain closed on 21st February 2025", "date": "2025-02-11" }
]
```
#### **Response:**
```json
{
    "message": "Notices published",
    "new_notices": 2
}
```

#### **Get Notices**
**GET** `/api/notices`  
*Retrieve notices with optional filters.*

---
### **Student Management (Admin Only)**
#### **Create Student**
**POST** `/api/students`  
#### **Request Body:**
```json
{
    "name": "Student Name",
    "student_id": "20222001",
    "dept": "CSE",
    "email": "",
    "password": "password"
}
```
#### **Response:**
```json
{
    "status": "Created",
    "id": 123,
    "name": "Student Name",
    "student_id": "20222001",
    "department": "CSE"
}
```

#### **Update Student Information**
**PUT** `/api/students/{student_id}`  
#### **Request Body:**
```json
{
    "name": "Updated Student Name",
    "student_id": "20222099",
    "dept": "EEE",
    "email": "updated.student@example.com",
    "password": "new_password"
}
```

#### **Delete Student**
**DELETE** `/api/students/{student_id}`  
#### **Response:**
```json
{
    "status": "Deleted",
    "id": 123,
    "student_id": "20222001"
}
```

---
### **Enjoy using the University API! 🚀**

