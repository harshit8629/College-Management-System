-- =============================================================================
--  COLLEGEHUB — COLLEGE MANAGEMENT SYSTEM
--  MySQL Database Setup Script
--  Run this once: mysql -u root -p < database.sql
-- =============================================================================

DROP DATABASE IF EXISTS college_management;
CREATE DATABASE college_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE college_management;


-- =============================================================================
--  TABLES
-- =============================================================================

CREATE TABLE departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    hod_name        VARCHAR(100)
);

-- -----------------------------------------------------------------------------

CREATE TABLE students (
    student_id     INT AUTO_INCREMENT PRIMARY KEY,
    roll_no        VARCHAR(20)  NOT NULL UNIQUE,
    name           VARCHAR(100) NOT NULL,
    email          VARCHAR(100) UNIQUE,
    phone          VARCHAR(15),
    gender         ENUM('Male', 'Female', 'Other'),
    date_of_birth  DATE,
    address        TEXT,
    department_id  INT NULL,
    semester       INT,
    admission_date DATE,
    CONSTRAINT fk_students_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------

CREATE TABLE teachers (
    teacher_id    INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(100) UNIQUE,
    phone         VARCHAR(15),
    department_id INT NULL,
    designation   VARCHAR(100),
    qualification VARCHAR(100),
    CONSTRAINT fk_teachers_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------

CREATE TABLE courses (
    course_id   INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20)  NOT NULL UNIQUE,
    course_name VARCHAR(100) NOT NULL,
    credits     INT DEFAULT 4,
    department_id INT NULL,
    semester    INT,
    CONSTRAINT fk_courses_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------

CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id    INT         NOT NULL,
    course_id     INT         NOT NULL,
    session_year  VARCHAR(10) NOT NULL,
    CONSTRAINT unique_enroll UNIQUE (student_id, course_id),
    CONSTRAINT fk_enrollments_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_enrollments_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------

CREATE TABLE attendance (
    attendance_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT  NOT NULL,
    course_id       INT  NOT NULL,
    attendance_date DATE NOT NULL,
    status          ENUM('Present', 'Absent') NOT NULL DEFAULT 'Present',
    CONSTRAINT unique_attend UNIQUE (student_id, course_id, attendance_date),
    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_attendance_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------

CREATE TABLE marks (
    mark_id    INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id  INT NOT NULL,
    marks      INT NOT NULL CHECK (marks BETWEEN 0 AND 100),
    grade      VARCHAR(3),
    CONSTRAINT unique_marks UNIQUE (student_id, course_id),
    CONSTRAINT fk_marks_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_marks_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -----------------------------------------------------------------------------

CREATE TABLE fees (
    fee_id       INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT            NOT NULL,
    total_fee    DECIMAL(10,2)  NOT NULL,
    paid_amount  DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    due_amount   DECIMAL(10,2)  GENERATED ALWAYS AS (total_fee - paid_amount) STORED,
    payment_date DATE,
    status       ENUM('Paid', 'Partial', 'Unpaid') NOT NULL DEFAULT 'Unpaid',
    CONSTRAINT fk_fees_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


-- =============================================================================
--  INDEXES
-- =============================================================================

CREATE INDEX idx_student_name  ON students(name);
CREATE INDEX idx_student_email ON students(email);
CREATE INDEX idx_student_roll  ON students(roll_no);
CREATE INDEX idx_teacher_name  ON teachers(name);
CREATE INDEX idx_course_code   ON courses(course_code);
CREATE INDEX idx_course_name   ON courses(course_name);


-- =============================================================================
--  VIEW — ReportCard
--  Used directly by the Flask report_card route
-- =============================================================================

CREATE VIEW ReportCard AS
SELECT
    s.student_id,
    s.name  AS student_name,
    c.course_name,
    m.marks,
    m.grade
FROM students s
JOIN marks   m ON s.student_id = m.student_id
JOIN courses c ON m.course_id  = c.course_id;


-- =============================================================================
--  TRIGGERS — Auto-assign grade on INSERT / UPDATE of marks
-- =============================================================================

DELIMITER //

CREATE TRIGGER before_insert_marks
BEFORE INSERT ON marks
FOR EACH ROW
BEGIN
    SET NEW.grade =
        CASE
            WHEN NEW.marks >= 90 THEN 'A+'
            WHEN NEW.marks >= 80 THEN 'A'
            WHEN NEW.marks >= 70 THEN 'B'
            WHEN NEW.marks >= 60 THEN 'C'
            WHEN NEW.marks >= 50 THEN 'D'
            ELSE 'F'
        END;
END //

CREATE TRIGGER before_update_marks
BEFORE UPDATE ON marks
FOR EACH ROW
BEGIN
    SET NEW.grade =
        CASE
            WHEN NEW.marks >= 90 THEN 'A+'
            WHEN NEW.marks >= 80 THEN 'A'
            WHEN NEW.marks >= 70 THEN 'B'
            WHEN NEW.marks >= 60 THEN 'C'
            WHEN NEW.marks >= 50 THEN 'D'
            ELSE 'F'
        END;
END //

DELIMITER ;


-- =============================================================================
--  STORED PROCEDURE — Full student report
--  Returns 4 result sets: student info, marks, attendance, fees
--  Usage: CALL get_student_report(1);
-- =============================================================================

DELIMITER //

CREATE PROCEDURE get_student_report(IN p_student_id INT)
BEGIN
    -- 1. Student profile
    SELECT
        s.student_id, s.roll_no, s.name, s.email, s.phone,
        s.gender, s.date_of_birth, s.address, s.semester,
        s.admission_date, d.department_name
    FROM students s
    LEFT JOIN departments d ON s.department_id = d.department_id
    WHERE s.student_id = p_student_id;

    -- 2. Marks & grades for enrolled courses
    SELECT
        c.course_code,
        c.course_name,
        c.credits,
        COALESCE(m.marks, 0)     AS marks,
        COALESCE(m.grade, 'N/A') AS grade
    FROM enrollments e
    JOIN  courses c ON e.course_id = c.course_id
    LEFT JOIN marks m
        ON e.student_id = m.student_id
       AND e.course_id  = m.course_id
    WHERE e.student_id = p_student_id
    ORDER BY c.course_name;

    -- 3. Attendance summary per course
    SELECT
        c.course_name,
        COUNT(a.attendance_id) AS total_classes,
        SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
        CASE
            WHEN COUNT(a.attendance_id) = 0 THEN 0
            ELSE ROUND(
                SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END)
                / COUNT(a.attendance_id) * 100, 2)
        END AS attendance_percentage
    FROM enrollments e
    JOIN  courses c ON e.course_id = c.course_id
    LEFT JOIN attendance a
        ON e.student_id = a.student_id
       AND e.course_id  = a.course_id
    WHERE e.student_id = p_student_id
    GROUP BY c.course_id, c.course_name
    ORDER BY c.course_name;

    -- 4. Fee details
    SELECT
        fee_id, student_id, total_fee,
        paid_amount, due_amount, payment_date, status
    FROM fees
    WHERE student_id = p_student_id
    ORDER BY payment_date DESC, fee_id DESC;
END //

DELIMITER ;


-- =============================================================================
--  SAMPLE DATA
-- =============================================================================

INSERT INTO departments (department_name, hod_name) VALUES
('Computer Science',       'Dr. Rajesh Sharma'),
('Mechanical Engineering', 'Dr. Priya Patel'),
('Civil Engineering',      'Prof. Amit Verma');

INSERT INTO students
    (roll_no, name, email, phone, gender, date_of_birth, address, department_id, semester, admission_date)
VALUES
('CS2023001', 'Aarav Singh',   'aarav@example.com',  '9876543210', 'Male',   '2005-03-15', 'Ludhiana, Punjab', 1, 4, CURDATE()),
('ME2023002', 'Ishita Sharma', 'ishita@example.com', '9876543211', 'Female', '2005-07-20', 'Ludhiana, Punjab', 2, 3, CURDATE());

INSERT INTO teachers (name, email, phone, department_id, designation, qualification) VALUES
('Dr. Neha Gupta', 'neha@college.edu', '9876543212', 1, 'Professor', 'PhD Computer Science');

INSERT INTO courses (course_code, course_name, credits, department_id, semester) VALUES
('CS101',  'Introduction to Programming',    4, 1, 1),
('CS301',  'Data Structures & Algorithms',   4, 1, 3),
('CS302',  'Database Management Systems',    4, 1, 4),
('CS401',  'Operating Systems',              4, 1, 4),
('CS501',  'Machine Learning',               4, 1, 6),
('ME201',  'Thermodynamics',                 4, 2, 3),
('ME301',  'Fluid Mechanics',                4, 2, 5),
('CE101',  'Engineering Mechanics',          3, 3, 1),
('CE201',  'Strength of Materials',          4, 3, 4),
('MA101',  'Engineering Mathematics I',      4, 1, 1),
('MA102',  'Engineering Mathematics II',     4, 1, 2),
('HS101',  'Professional Communication',     2, 2, 1);

INSERT INTO enrollments (student_id, course_id, session_year) VALUES
(1, 1, '2025-26'),
(2, 6, '2025-26');

-- marks triggers will auto-set the grade column
INSERT INTO marks (student_id, course_id, marks) VALUES
(1, 1, 86),
(2, 6, 74);

INSERT INTO fees (student_id, total_fee, paid_amount, payment_date, status) VALUES
(1, 50000, 30000, CURDATE(), 'Partial'),
(2, 50000, 50000, CURDATE(), 'Paid');