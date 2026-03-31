-- ====================== COLLEGE MANAGEMENT SYSTEM DATABASE ======================

DROP DATABASE IF EXISTS college_management;
CREATE DATABASE college_management;
USE college_management;


CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    hod_name VARCHAR(100)
);

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    gender ENUM('Male', 'Female', 'Other'),
    date_of_birth DATE,
    address TEXT,
    department_id INT NULL,
    semester INT,
    admission_date DATE,
    CONSTRAINT fk_students_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE SET NULL
);

CREATE TABLE teachers (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    department_id INT NULL,
    designation VARCHAR(50),
    qualification VARCHAR(100),
    CONSTRAINT fk_teachers_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE SET NULL
);

CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_name VARCHAR(100) NOT NULL,
    credits INT DEFAULT 4,
    department_id INT NULL,
    semester INT,
    CONSTRAINT fk_courses_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE SET NULL
);

CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    session_year VARCHAR(10) NOT NULL,
    CONSTRAINT unique_enroll UNIQUE (student_id, course_id),
    CONSTRAINT fk_enrollments_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_enrollments_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE CASCADE
);

CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL DEFAULT 'Present',
    CONSTRAINT unique_attend UNIQUE (student_id, course_id, attendance_date),
    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_attendance_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE CASCADE
);

CREATE TABLE marks (
    mark_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    marks INT NOT NULL,
    grade VARCHAR(3),
    CONSTRAINT unique_marks UNIQUE (student_id, course_id),
    CONSTRAINT fk_marks_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_marks_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE CASCADE
);

CREATE TABLE fees (
    fee_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    total_fee DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    due_amount DECIMAL(10,2) GENERATED ALWAYS AS (total_fee - paid_amount) STORED,
    payment_date DATE,
    status ENUM('Paid', 'Partial', 'Unpaid') NOT NULL DEFAULT 'Unpaid',
    CONSTRAINT fk_fees_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
);



CREATE INDEX idx_student_name ON students(name);
CREATE INDEX idx_student_email ON students(email);
CREATE INDEX idx_student_roll ON students(roll_no);
CREATE INDEX idx_teacher_name ON teachers(name);
CREATE INDEX idx_course_code ON courses(course_code);
CREATE INDEX idx_course_name ON courses(course_name);


DELIMITER //

CREATE TRIGGER before_insert_marks
BEFORE INSERT ON marks
FOR EACH ROW
BEGIN
    IF NEW.marks >= 90 THEN
        SET NEW.grade = 'A+';
    ELSEIF NEW.marks >= 80 THEN
        SET NEW.grade = 'A';
    ELSEIF NEW.marks >= 70 THEN
        SET NEW.grade = 'B';
    ELSEIF NEW.marks >= 60 THEN
        SET NEW.grade = 'C';
    ELSEIF NEW.marks >= 50 THEN
        SET NEW.grade = 'D';
    ELSE
        SET NEW.grade = 'F';
    END IF;
END //

CREATE TRIGGER before_update_marks
BEFORE UPDATE ON marks
FOR EACH ROW
BEGIN
    IF NEW.marks >= 90 THEN
        SET NEW.grade = 'A+';
    ELSEIF NEW.marks >= 80 THEN
        SET NEW.grade = 'A';
    ELSEIF NEW.marks >= 70 THEN
        SET NEW.grade = 'B';
    ELSEIF NEW.marks >= 60 THEN
        SET NEW.grade = 'C';
    ELSEIF NEW.marks >= 50 THEN
        SET NEW.grade = 'D';
    ELSE
        SET NEW.grade = 'F';
    END IF;
END //

DELIMITER ;


DELIMITER //

CREATE PROCEDURE get_student_report(IN p_student_id INT)
BEGIN
    SELECT *
    FROM students
    WHERE student_id = p_student_id;

    SELECT
        c.course_code,
        c.course_name,
        c.credits,
        COALESCE(m.marks, 0) AS marks,
        COALESCE(m.grade, 'N/A') AS grade
    FROM enrollments e
    JOIN courses c ON e.course_id = c.course_id
    LEFT JOIN marks m
        ON e.student_id = m.student_id
       AND e.course_id = m.course_id
    WHERE e.student_id = p_student_id;

    SELECT
        c.course_name,
        COUNT(a.attendance_id) AS total_classes,
        SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
        CASE
            WHEN COUNT(a.attendance_id) = 0 THEN 0
            ELSE ROUND(
                SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id) * 100,
                2
            )
        END AS attendance_percentage
    FROM enrollments e
    JOIN courses c ON e.course_id = c.course_id
    LEFT JOIN attendance a
        ON e.student_id = a.student_id
       AND e.course_id = a.course_id
    WHERE e.student_id = p_student_id
    GROUP BY c.course_id, c.course_name;

    SELECT
        fee_id,
        student_id,
        total_fee,
        paid_amount,
        due_amount,
        payment_date,
        status
    FROM fees
    WHERE student_id = p_student_id
    ORDER BY payment_date DESC, fee_id DESC;
END //

DELIMITER ;


INSERT INTO departments (department_name, hod_name) VALUES
('Computer Science', 'Dr. Rajesh Sharma'),
('Mechanical Engineering', 'Dr. Priya Patel'),
('Civil Engineering', 'Prof. Amit Verma');

INSERT INTO students
(roll_no, name, email, phone, gender, date_of_birth, address, department_id, semester, admission_date)
VALUES
('CS2023001', 'Aarav Singh', 'aarav@example.com', '9876543210', 'Male', '2005-03-15', 'Ludhiana, Punjab', 1, 4, CURDATE()),
('ME2023002', 'Ishita Sharma', 'ishita@example.com', '9876543211', 'Female', '2005-07-20', 'Ludhiana, Punjab', 2, 3, CURDATE());

INSERT INTO teachers
(name, email, phone, department_id, designation, qualification)
VALUES
('Dr. Neha Gupta', 'neha@college.edu', '9876543212', 1, 'Professor', 'PhD Computer Science');

INSERT INTO courses
(course_code, course_name, credits, department_id, semester)
VALUES
('CS101', 'Introduction to Programming', 4, 1, 1),
('ME201', 'Thermodynamics', 4, 2, 3);

INSERT INTO enrollments (student_id, course_id, session_year) VALUES
(1, 1, '2025-26'),
(2, 2, '2025-26');
-- you have to add more data by yourself

INSERT INTO marks (student_id, course_id, marks) VALUES
(1, 1, 86),
(2, 2, 74);

INSERT INTO fees (student_id, total_fee, paid_amount, payment_date, status) VALUES
(1, 50000, 30000, CURDATE(), 'Partial'),
(2, 50000, 50000, CURDATE(), 'Paid');
