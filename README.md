#  BrainByte LMS

A full-featured **Learning Management System** built with Flask and SQLite, deployed on Render.

🌐 **Live Demo:** [https://brainbyte-22r7.onrender.com](https://brainbyte-22r7.onrender.com)

---

## Features

### 👨‍💼 Admin
- Add, edit, and delete courses
- Upload learning materials (PDFs, Videos)
- Create and manage quiz questions
- Dashboard with course and material stats

### 👩‍🎓 Student
- Browse and search available courses
- Watch videos and download PDFs
- Take interactive quizzes
- View quiz results with score breakdown and chart

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | SQLite |
| Frontend | HTML, CSS, Bootstrap 5 |
| Auth | Flask Sessions |
| Deployment | Render |
| Version Control | Git + GitHub |

---

## Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/ruchikaa-6/brainbyte.git
cd brainbyte
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python main.py
```

### 4. Open in browser
```
http://localhost:5000
```

---

## Project Structure

```
brainbyte/
├── main.py              # Flask application & all routes
├── final.db             # SQLite database
├── requirements.txt     # Python dependencies
├── Procfile             # Render deployment config
├── frontend/            # HTML templates
│   ├── frontpage.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── manage_course.html
│   ├── student_home.html
│   ├── course_details.html
│   ├── quiz.html
│   ├── quiz_result.html
│   └── add_question.html
├── static/
│   └── images/          # Logo and profile images
└── uploads/             # Uploaded course materials
```

---

## Roles

| Role | Access |
|------|--------|
| Admin | Manage courses, materials, quizzes |
| Student | View courses, take quizzes |

Register at `/register` and select your role.
