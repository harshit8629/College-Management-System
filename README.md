# College-Management-System

A complete **College Management System Web Application** built using **Python Flask, MySQL, HTML, CSS, and Bootstrap**.
This project is designed to manage all major academic and administrative operations of a college in a simple, efficient, and user-friendly way.

---

## 🚀 Features

### 📊 Dashboard

* Displays total number of students, teachers, courses, departments, enrollments, and fees
* Shows recent student records for quick overview

### 👨‍🎓 Student Management

* Add, view, update, and delete student records
* Search students by name, roll number, email, or ID
* Department and semester-wise organization

### 👩‍🏫 Teacher Management

* Add, edit, and delete teachers
* Assign teachers to departments
* Store designation and qualification details

### 🏢 Department Management

* Create and manage departments
* Assign Head of Department (HOD)

### 📚 Course Management

* Add and manage courses
* Assign courses to departments and semesters
* Store course credits and codes

### 📝 Marks Management

* Add marks for students
* Automatic grade calculation using MySQL triggers
* Prevent duplicate entries using unique constraints

### 💰 Fees Management

* Add and update student fee records
* Automatically calculate due amount using generated columns
* Track payment status (Paid / Partial / Unpaid)

## 🛠️ Technologies Used

* **Frontend:** HTML, CSS, Bootstrap
* **Backend:** Python Flask
* **Database:** MySQL
* **Tools:** MySQL Workbench, VS Code

---

## 🗄️ Database Features

* Relational database design with foreign keys
* Indexed fields for fast searching
* MySQL Triggers for automatic grade calculation
* Stored Procedures for report generation
* Generated columns for fee calculation

---

## ⚡ Performance Optimizations

* Efficient SQL queries
* Indexed columns for faster search
* Clean and modular backend code
* Optimized CRUD operations

---

## 📁 Project Structure

```
college-management-system/
│
├── app.py
├── config.py
├── database.sql
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── students.html
│   ├── teachers.html
│   ├── courses.html
│   ├── departments.html
│   ├── marks.html
│   ├── fees.html
│   ├── report_card.html
│
├── static/
│   ├── css/
│   ├── js/
```

---

## ▶️ How to Run the Project

1. Clone the repository:

```
git clone https://github.com/your-username/college-management-system.git
cd college-management-system
```

2. Install dependencies:

```
pip install flask mysql-connector-python
```

3. Setup MySQL Database:

* Open MySQL Workbench
* Run `database.sql`

4. Configure database in `config.py`:

```python
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_password'
DB_NAME = 'college_management'
```

5. Run the application:

```
python app.py
```

6. Open browser:

```
http://127.0.0.1:5000/
```

---

## 🎯 Key Highlights

* Beginner-friendly and easy to understand
* Fully functional CRUD operations
* Real-world database design
* Clean UI with responsive design
* Perfect for **college mini project submission**

---

## 📌 Future Enhancements

* User authentication (Admin/Student login)
* Attendance analytics dashboard
* Export reports to PDF
* API integration

---

## 👨‍💻 Author

Developed as a college mini project using Flask and MySQL.

---

## ⭐ Conclusion

This project demonstrates how a real-world **College Management System** can be built using Python Flask and MySQL with proper database design, clean UI, and efficient backend logic.
