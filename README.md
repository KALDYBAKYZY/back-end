#  Fitness Center Management

##  Project Description

This is a web application for managing a fitness center, supporting roles such as **administrator**, **trainer**, and **client**.

##  Features

- **User Registration:** Register as a trainer or client.  
- **Login System:** Log in with your credentials.  
- **Trainer Management (Admin):** Add, edit, and delete trainers.  
- **Client Management (Admin):** Add, edit, and delete clients.  
- **Training Booking (Client):** Book training sessions.  
- **Schedule Viewing:**
  - Trainers can view their training schedule.
  - Clients can view available slots.
- **Profile Management:** View and edit personal profiles.  
- **Client Progress (Trainer):** View client progress.  
- **Workout Creation (Trainer):** Create training sessions.  
- **Assignment Creation (Trainer):** Assign personalized tasks to clients.  
- **Training Schedule:** View training schedule (Trainer/Client).  
- **Personal Notes (Client):** Write and manage personal notes.  
- **Assignment Tracking (Client):** View and mark assignments as completed.  
- **Achievements (Client):** View personal achievements.  
- **Training Enrollment (Client):** Book available sessions at convenient times.

## Tech Stack

- **Back-end:** Python, Flask  
- **Database:** PostgreSQL  
- **Front-end:** HTML, CSS, JavaScript (as needed)  
- **Libraries:**  
  - SQLAlchemy  
  - bcrypt  
  - Flask-SQLAlchemy  
  - Flask-WTF  
  - Jinja2  
- **Version Control:** Git, GitHub

## Getting Started

### 1. Create the Database

- Install PostgreSQL and create a database (e.g., `fitness_center_db`).  
- Create tables using SQL scripts or with SQLAlchemy models.  
- Add initial data (e.g., roles, example users).

### 2. Configure the Project

- Open the project folder.  
- In `app.py`, configure the database URI:
  ```python
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/fitness_center_db'
