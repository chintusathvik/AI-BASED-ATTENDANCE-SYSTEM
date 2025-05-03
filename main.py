import customtkinter as ctk
import cv2
import os
import numpy as np
import pandas as pd
import smtplib
import pyttsx3
from datetime import datetime
from tkinter import messagebox
from email.message import EmailMessage
import mysql.connector


engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()


SENDER_EMAIL = "chintusathvik02@gmail.com"
SENDER_PASSWORD = "qfqcwkenzkoccadd"

# Database connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="august22004",
        database="attendance_db"
    )

# Email sending to student
def send_email_to_student(email, name):
    msg = EmailMessage()
    msg['Subject'] = "Attendance Confirmation"
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg.set_content(f"Dear {name},\n\nYour attendance has been marked successfully.\n\nThank you.")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

# Email daily CSV report to admin
def send_csv_to_admin(file_path):
    msg = EmailMessage()
    msg['Subject'] = "Daily Attendance Report"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.set_content("Please find the attached daily attendance report.")
    with open(file_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=os.path.basename(file_path))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending CSV to admin: {e}")

# Train images
def train_images():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    path = 'TrainingImage'
    faces, ids = [], []
    for image in os.listdir(path):
        img_path = os.path.join(path, image)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        np_img = np.array(img, 'uint8')
        id = int(image.split('.')[1])
        faces.append(np_img)
        ids.append(id)
    recognizer.train(faces, np.array(ids))
    recognizer.save("trainer.yml")
    messagebox.showinfo("Training Complete", "Images trained successfully!")
    speak("Training complete. Images trained successfully.")

# Face recognition and attendance
def track_faces():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer.yml")
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    conn = get_connection()
    cursor = conn.cursor()
    cam = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    col_names = ['ID', 'Name', 'Date', 'Time']
    attendance = pd.DataFrame(columns=col_names)
    recognized_ids = set()

    while True:
        ret, frame = cam.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            id, conf = recognizer.predict(gray[y:y + h, x:x + w])
            cursor.execute("SELECT name, email FROM students WHERE id=%s", (id,))
            result = cursor.fetchone()
            if result and conf < 70 and id not in recognized_ids:
                name, email = result
                ts = datetime.now()
                date = ts.strftime('%Y-%m-%d')
                time = ts.strftime('%H:%M:%S')
                attendance.loc[len(attendance)] = [id, name, date, time]
                recognized_ids.add(id)
                send_email_to_student(email, name)
                speak(f"Attendance marked successfully for {name}")
                cv2.putText(frame, f"{name}", (x, y - 10), font, 1, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Automatically stop after first successful recognition
                cam.release()
                cv2.destroyAllWindows()

                # Save attendance
                ts = datetime.now().strftime('%Y-%m-%d')
                file_path = f"Attendance_{ts}.csv"
                attendance.to_csv(file_path, index=False)
                send_csv_to_admin(file_path)
                conn.close()

                messagebox.showinfo("Attendance Complete", f"Attendance marked for {name}. Camera closed.")
                speak("Attendance complete. Camera turned off.")
                return
            else:
                cv2.putText(frame, "Unknown", (x, y - 10), font, 1, (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        cv2.putText(frame, "Face Recognition Running...", (10, 30), font, 0.7, (255, 255, 0), 2)
        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) == 13:  # Press Enter to quit
            break

    cam.release()
    cv2.destroyAllWindows()
    conn.close()

# Save new student
def save_student():
    id = id_entry.get()
    name = name_entry.get()
    email = email_entry.get()
    if not id or not name or not email:
        messagebox.showerror("Input Error", "All fields are required")
        return
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (id, name, email) VALUES (%s, %s, %s)", (id, name, email))
        conn.commit()
        conn.close()
        cam = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        sample_count = 0
        while True:
            ret, frame = cam.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                sample_count += 1
                cv2.imwrite(f"TrainingImage/{name}.{id}.{sample_count}.jpg", gray[y:y + h, x:x + w])
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.imshow('Register Face', frame)
            if cv2.waitKey(1) == 13 or sample_count >= 30:
                break
        cam.release()
        cv2.destroyAllWindows()
        messagebox.showinfo("Success", "Student added and images captured")
        speak(f"Successfully registered {name}")
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to insert: {e}")

# GUI Setup
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
window = ctk.CTk()
window.title("AI Face Recognition Attendance System")
window.geometry("850x500")

ctk.CTkLabel(window, text="Student ID").pack(pady=5)
id_entry = ctk.CTkEntry(window)
id_entry.pack(pady=5)

ctk.CTkLabel(window, text="Student Name").pack(pady=5)
name_entry = ctk.CTkEntry(window)
name_entry.pack(pady=5)

ctk.CTkLabel(window, text="Student Email").pack(pady=5)
email_entry = ctk.CTkEntry(window)
email_entry.pack(pady=5)

ctk.CTkButton(window, text="Save Student & Capture Images", command=save_student).pack(pady=10)
ctk.CTkButton(window, text="Train Images", command=train_images).pack(pady=10)
ctk.CTkButton(window, text="Track Faces & Mark Attendance", command=track_faces).pack(pady=10)

window.mainloop()
