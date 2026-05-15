# CollegeHub Database ER Diagram

This document contains the Entity-Relationship (ER) diagram for the College Management System database. You can view this diagram visually by viewing this file in a Markdown previewer that supports Mermaid (like VS Code or GitHub).

```mermaid
erDiagram
    departments ||--o{ students : "has many"
    departments ||--o{ teachers : "employs"
    departments ||--o{ courses : "offers"
    
    students ||--o{ enrollments : "registers for"
    courses ||--o{ enrollments : "includes"
    
    students ||--o{ attendance : "has"
    courses ||--o{ attendance : "tracked for"
    
    students ||--o{ marks : "receives"
    courses ||--o{ marks : "awarded in"
    
    students ||--o{ fees : "pays"

    departments {
        INTEGER department_id PK
        TEXT department_name
        TEXT hod_name
    }
    students {
        INTEGER student_id PK
        TEXT roll_no
        TEXT name
        TEXT email
        TEXT phone
        TEXT gender
        TEXT date_of_birth
        TEXT address
        INTEGER department_id FK
        INTEGER semester
        TEXT admission_date
    }
    teachers {
        INTEGER teacher_id PK
        TEXT name
        TEXT email
        TEXT phone
        INTEGER department_id FK
        TEXT designation
        TEXT qualification
    }
    courses {
        INTEGER course_id PK
        TEXT course_code
        TEXT course_name
        INTEGER credits
        INTEGER department_id FK
        INTEGER semester
    }
    enrollments {
        INTEGER enrollment_id PK
        INTEGER student_id FK
        INTEGER course_id FK
        TEXT session_year
    }
    attendance {
        INTEGER attendance_id PK
        INTEGER student_id FK
        INTEGER course_id FK
        TEXT attendance_date
        TEXT status
    }
    marks {
        INTEGER mark_id PK
        INTEGER student_id FK
        INTEGER course_id FK
        INTEGER marks
        TEXT grade
    }
    fees {
        INTEGER fee_id PK
        INTEGER student_id FK
        REAL total_fee
        REAL paid_amount
        REAL due_amount
        TEXT payment_date
        TEXT status
    }
```
