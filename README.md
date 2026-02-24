# Face Attendance System

A comprehensive web application for managing student attendance using facial recognition.

## Features
- **Roles**: Admin, Professor, Student.
- **Admin**: Create professors, courses, and add students with photos (auto-encoding).
- **Professor**: Real-time face recognition for attendance, session management, absence history.
- **Student**: View absence stats and warnings.
- **Tech Stack**: Django, OpenCV, dlib, face_recognition, Bootstrap 5.

## Setup Instructions

### Prerequisites
1.  **Python 3.8+**
2.  **MySQL Server** running.
3.  **Visual Studio Build Tools** (for C++ compilation of dlib) - *Already assumed installed.*

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install django dlib face_recognition opencv-python mysqlclient
```

### 2. Configure Database
Ensure your MySQL server is running and updated `settings.py` with your credentials calling the database `face_attendance_db` (or create it):
```sql
CREATE DATABASE face_attendance_db CHARACTER SET utf8mb4;
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Admin)
```bash
python manage.py createsuperuser
# Email: admin@gmail.com
# Password: admin
```

### 5. Run Server
```bash
python manage.py runserver
```

## Usage
1.  **Login** at `http://127.0.0.1:8000/login/`.
2.  **Admin**:
    -   Go to dashboard.
    -   Create a Professor.
    -   Create a Course (assign to Prof).
    -   Add a Student (Upload Photo -> Encoding is generated automatically).
3.  **Professor**:
    -   Login using credentials created by Admin.
    -   Select Course -> "Record Attendance".
    -   "Start Camera" -> Face Recognition marks students in real-time.
    -   "Stop Camera" -> Save Session.
4.  **Student**:
    -   Login to view status.
