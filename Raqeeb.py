# -*- coding: utf-8 -*-
"""
Baseera - Integrated Attendance & Security System
Description: A comprehensive system for managing employee attendance using real-time
             face recognition, liveness detection, and a secure database.
             Features include multi-language support, a management dashboard,
             email alerts, and customizable settings.
Version: 2.2
Last Modified: 2025-07-23
"""

import cv2
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, filedialog
from PIL import Image, ImageTk
from deepface import DeepFace
import threading
import time
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame # Correct import for ScrolledFrame
from datetime import datetime, date
import shutil
import sqlite3
import smtplib
from email.message import EmailMessage
import dlib
from scipy.spatial import distance as dist
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import logging
import csv
import hashlib # For password hashing

# --- Logging Setup (إعداد التسجيل) ---
# Configures logging to save application events to a file for debugging.
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants (الثوابت) ---
DB_PATH = 'known_faces'
UNKNOWN_PATH = 'unknown_visitors'
MODEL_NAME = "ArcFace"  # Recommended model for high accuracy
DATABASE_FILE = 'attendance_system.db'
SHAPE_PREDICTOR_PATH = 'shape_predictor_68_face_landmarks.dat' # dlib model for facial landmarks
EAR_CONSEC_FRAMES = 3  # Number of consecutive frames the eye must be below the threshold for a "blink"

class MainApp:
    """
    The main application class that initializes the UI, database, camera,
    and face recognition models.
    (الفئة الرئيسية للتطبيق التي تهيئ واجهة المستخدم وقاعدة البيانات والكاميرا ونماذج التعرف على الوجوه)
    """
    def __init__(self, window):
        self.window = window
        self.style = ttk.Style(theme='superhero') # Default theme, will be updated from settings
        self.window.geometry("1366x768")
        self.window.resizable(True, True)

        self.setup_translation()
        self.current_lang = 'ar'

        # --- Initialize dlib components for liveness detection (تهيئة مكونات dlib) ---
        self.face_detector_dlib = dlib.get_frontal_face_detector()
        if not os.path.exists(SHAPE_PREDICTOR_PATH):
            messagebox.showerror("Fatal Error", f"Shape predictor file not found: '{SHAPE_PREDICTOR_PATH}'. Please download it and place it in the application folder.")
            logging.critical(f"Shape predictor file not found: {SHAPE_PREDICTOR_PATH}")
            self.window.destroy(); return
        self.landmark_predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
        (self.lStart, self.lEnd) = (42, 48); (self.rStart, self.rEnd) = (36, 42)

        self.setup_ui()
        
        self.is_running = True
        self.setup_database_and_folders()
        self.load_settings() # Load settings including theme
        self.style.theme_use(self.selected_theme) # Apply loaded theme
        self.load_todays_attendance()
        self.update_ui_text()
        self.update_clock()
        
        # --- Load DeepFace model once at startup for better performance (تحميل نموذج DeepFace مرة واحدة) ---
        self.set_status(self.T('status_loading_models'))
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)
        self.progress_bar.start()
        try:
            # This can take a few moments on the first run
            self.deepface_model = DeepFace.build_model(MODEL_NAME)
            logging.info(f"DeepFace model '{MODEL_NAME}' loaded successfully.")
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            messagebox.showerror("Fatal Error", f"Could not load the AI model: {e}\n\nPlease check your internet connection for the first-time setup.")
            logging.critical(f"Error loading DeepFace model: {e}")
            self.window.destroy(); return

        self.window.after(100, self.start_processing_thread)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Initializes all the user interface elements."""
        # Header Frame
        self.header_frame = ttk.Frame(self.window, padding=15, bootstyle="dark")
        self.header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.app_title = ttk.Label(self.header_frame, text="", font=("Helvetica", 24, "bold"), bootstyle="inverse-dark")
        self.app_title.pack(side=tk.LEFT, padx=15)
        
        self.lang_button = ttk.Button(self.header_frame, text="EN/AR", command=self.toggle_language, bootstyle=(OUTLINE, LIGHT), width=8)
        self.lang_button.pack(side=tk.LEFT, padx=25)
        
        self.clock_label = ttk.Label(self.header_frame, text="", font=("Helvetica", 18), bootstyle="inverse-dark")
        self.clock_label.pack(side=tk.RIGHT, padx=15)

        # Main Paned Window (for resizable sections)
        self.main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        self.main_paned.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        # Video Frame
        self.video_frame = ttk.Frame(self.main_paned, bootstyle="secondary")
        self.canvas = tk.Canvas(self.video_frame, bg="black", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.main_paned.add(self.video_frame, weight=3)

        # Attendance Frame
        self.attendance_frame = ttk.Frame(self.main_paned, bootstyle="secondary")
        self.attendance_label = ttk.Label(self.attendance_frame, text="", font=("Helvetica", 18, "bold"), bootstyle="inverse-secondary", anchor=tk.CENTER)
        self.attendance_label.pack(pady=15, fill=tk.X)
        self.setup_attendance_tree()
        self.main_paned.add(self.attendance_frame, weight=1)

        # Footer Frame
        self.footer_frame = ttk.Frame(self.window, padding=15, bootstyle="dark")
        self.footer_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(self.footer_frame, text="", font=("Helvetica", 14), bootstyle="inverse-dark")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Add icons to buttons for better UX
        self.settings_button = ttk.Button(self.footer_frame, text="", command=self.open_settings_window, bootstyle=INFO, width=15)
        self.settings_button.pack(side=tk.RIGHT, padx=5)
        
        self.manage_users_button = ttk.Button(self.footer_frame, text="", command=self.open_manage_users_window, bootstyle=SUCCESS, width=15)
        self.manage_users_button.pack(side=tk.RIGHT, padx=5)
        
        self.dashboard_button = ttk.Button(self.footer_frame, text="", command=self.open_dashboard_window, bootstyle=WARNING, width=15)
        self.dashboard_button.pack(side=tk.RIGHT, padx=5)

        # Progress Bar (for model loading)
        self.progress_bar = ttk.Progressbar(self.window, orient=tk.HORIZONTAL, length=300, mode='indeterminate', bootstyle="info")

    def setup_translation(self):
        """Sets up the dictionary for multi-language support."""
        self.texts = {
            'ar': {
                'window_title': "نظام بصيرة للإدارة المتكاملة", 'main_title': "نظام الحضور والأمان",
                'attendance_log': "سجل الحضور اليومي", 'col_name': "الاسم", 'col_time': "وقت التسجيل", 'col_email': "البريد الإلكتروني",
                'status_init': "جاري تهيئة النظام...", 'manage_users': "👤 إدارة الموظفين", 'dashboard': "📊 لوحة المعلومات",
                'settings': "⚙️ الإعدادات", 'status_loading_models': "جاري تحميل نماذج الذكاء الاصطناعي، يرجى الانتظار...",
                'status_camera_ok': "الكاميرا تعمل...", 'status_liveness_check': "الرجاء الرمش بعينيك للتحقق...",
                'status_liveness_success': "تم التحقق. جاري التعرف...", 'status_recognized': "تم التعرف على: {}",
                'status_unknown': "وجه غير معروف!", 'status_searching': "البحث عن وجوه...",
                'status_email_sent': "تنبيه أمني: تم إرسال بريد إلكتروني.", 'status_email_fail': "فشل إرسال الإيميل: {}",
                'add_user_title': "موظف جديد", 'add_user_prompt': "الرجاء إدخال اسم الموظف:",
                'email_prompt': "الرجاء إدخال إيميل الموظف:", 'add_user_cancelled': "تم إلغاء الإضافة.",
                'capture_title': "التقاط صورة", 'capture_prompt': "التقاط الصورة {}/3.\nانظر للكاميرا واضغط OK.",
                'add_user_success_no_restart': "تم حفظ {}. تم تحديث قاعدة بيانات الوجوه.", 'export_success_title': "نجاح",
                'export_success_msg': "تم تصدير التقرير بنجاح:\n{}", 'export_fail_title': "خطأ",
                'export_fail_msg': "فشل العملية: {}", 'dashboard_title': "لوحة المعلومات",
                'monthly_report_tab': "تقرير شهري", 'weekly_chart_tab': "رسم بياني أسبوعي",
                'db_col_name': "اسم الموظف", 'db_col_days': "أيام الحضور", 'chart_title': "الحضور حسب اليوم",
                'chart_title_short': "العدد", 'settings_title': "إعدادات النظام", 'sender_email': "إيميل المرسل:",
                'app_password': "كلمة مرور التطبيقات (Gmail):", 'receiver_email': "إيميل مستقبل التنبيهات:",
                'save_settings': "حفظ الإعدادات", 'camera_index_label': "فهرس الكاميرا (عادةً 0 أو 1):",
                'ear_threshold_label': "عتبة الرمش (EAR Threshold):", 'confidence_threshold_label': "عتبة الثقة (Confidence Threshold):",
                'detector_backend_label': "نموذج الكشف عن الوجه (Detector Backend):", 'process_interval_label': "فاصل معالجة الإطار (أقل = أسرع):",
                'theme_label': "مظهر الواجهة:", 'email_subject_label': "عنوان بريد التنبيه (وجه غير معروف):",
                'email_body_label': "نص بريد التنبيه:", 'settings_saved': "تم حفظ الإعدادات بنجاح.",
                'all_employees': "كل الموظفين", 'absent_today': "المتغيبون اليوم", 'add': "إضافة", 'edit': "تعديل",
                'delete': "حذف", 'notify_absentees': "إرسال إيميل للمتغيبين", 'confirm_delete': "هل أنت متأكد من حذف الموظف {}؟",
                'no_absentees': "لا يوجد متغيبون اليوم.", 'absentee_email_sent': "تم إرسال إيميلات للمتغيبين.",
                'absentee_email_subject': "تذكير بخصوص الحضور", 'absentee_email_body': "مرحباً {name},\n\nنود تذكيركم بأنكم لم تسجلوا حضوركم لليوم. نرجو إعلامنا في حال وجود أي طارئ.\n\nمع تحيات،\nالإدارة.",
                'capture_photos_btn': "التقاط الصور والحفظ", 'export_monthly_btn': "تصدير التقرير الشهري (CSV)",
                'export_weekly_btn': "تصدير بيانات الرسم البياني (CSV)", 'backup_db_btn': "نسخ احتياطي لقاعدة البيانات",
                'backup_success': "تم إنشاء نسخة احتياطية من قاعدة البيانات:\n{}", 'backup_fail': "فشل إنشاء النسخة الاحتياطية: {}",
                'smtp_server_label': "خادم SMTP:", 'smtp_port_label': "منفذ SMTP:",
                'password_warning': "تحذير: يتم حفظ كلمة المرور في قاعدة البيانات. استخدم كلمة مرور خاصة بالتطبيقات.",
                'admin_password_label': "كلمة مرور المسؤول:", 'password_prompt_title': "مطلوب كلمة المرور",
                'password_prompt_text': "الرجاء إدخال كلمة مرور المسؤول للوصول.", 'password_incorrect': "كلمة المرور غير صحيحة.",
                'profile_window_title': "ملف الموظف: {}", 'profile_attendance_log': "سجل الحضور الكامل",
                'profile_col_date': "التاريخ", 'profile_col_time': "الوقت"
            },
            'en': {
                'window_title': "Baseera Integrated Management System", 'main_title': "Attendance & Security System",
                'attendance_log': "Today's Attendance Log", 'col_name': "Name", 'col_time': "Check-in Time", 'col_email': "Email",
                'status_init': "Initializing system...", 'manage_users': "👤 Manage Employees", 'dashboard': "📊 Dashboard",
                'settings': "⚙️ Settings", 'status_loading_models': "Loading AI models, please wait...",
                'status_camera_ok': "Camera is active...", 'status_liveness_check': "Please blink to verify liveness...",
                'status_liveness_success': "Liveness verified. Recognizing...", 'status_recognized': "Recognized: {}",
                'status_unknown': "Unknown face detected!", 'status_searching': "Searching for faces...",
                'status_email_sent': "Security Alert: Email sent.", 'status_email_fail': "Failed to send email: {}",
                'add_user_title': "New Employee", 'add_user_prompt': "Please enter the employee's name:",
                'email_prompt': "Please enter the employee's email:", 'add_user_cancelled': "Add operation cancelled.",
                'capture_title': "Capture Image", 'capture_prompt': "Capturing image {}/3.\nLook at the camera and press OK.",
                'add_user_success_no_restart': "{} saved successfully. Face database has been updated.", 'export_success_title': "Success",
                'export_success_msg': "Report exported successfully:\n{}", 'export_fail_title': "Error",
                'export_fail_msg': "Operation failed: {}", 'dashboard_title': "Dashboard",
                'monthly_report_tab': "Monthly Report", 'weekly_chart_tab': "Weekly Chart",
                'db_col_name': "Employee Name", 'db_col_days': "Attendance Days", 'chart_title': "Attendees per Day",
                'chart_title_short': "Count", 'settings_title': "System Settings", 'sender_email': "Sender Email:",
                'app_password': "App Password (Gmail):", 'receiver_email': "Alerts Receiver Email:",
                'save_settings': "Save Settings", 'camera_index_label': "Camera Index (usually 0 or 1):",
                'ear_threshold_label': "EAR Threshold:", 'confidence_threshold_label': "Confidence Threshold:",
                'detector_backend_label': "Detector Backend:", 'process_interval_label': "Frame Processing Interval (Lower = Faster):",
                'theme_label': "UI Theme:", 'email_subject_label': "Alert Email Subject (Unknown Face):",
                'email_body_label': "Alert Email Body:", 'settings_saved': "Settings saved successfully.",
                'all_employees': "All Employees", 'absent_today': "Absent Today", 'add': "Add", 'edit': "Edit",
                'delete': "Delete", 'notify_absentees': "Notify Absentees", 'confirm_delete': "Are you sure you want to delete {}?",
                'no_absentees': "No absentees today.", 'absentee_email_sent': "Emails sent to absentees.",
                'absentee_email_subject': "Attendance Reminder", 'absentee_email_body': "Dear {name},\n\nThis is a reminder that you have not checked in today. Please let us know if there are any issues.\n\nBest regards,\nManagement.",
                'capture_photos_btn': "Capture Photos & Save", 'export_monthly_btn': "Export Monthly Report (CSV)",
                'export_weekly_btn': "Export Weekly Chart Data (CSV)", 'backup_db_btn': "Backup Database",
                'backup_success': "Database backup created:\n{}", 'backup_fail': "Failed to create backup: {}",
                'smtp_server_label': "SMTP Server:", 'smtp_port_label': "SMTP Port:",
                'password_warning': "Warning: Password is saved in the database. Use an app-specific password.",
                'admin_password_label': "Admin Password:", 'password_prompt_title': "Password Required",
                'password_prompt_text': "Please enter the admin password to continue.", 'password_incorrect': "Incorrect password.",
                'profile_window_title': "Employee Profile: {}", 'profile_attendance_log': "Full Attendance Log",
                'profile_col_date': "Date", 'profile_col_time': "Time"
            }
        }

    def T(self, key, *args):
        """Fetches a text string for the current language."""
        return self.texts[self.current_lang].get(key, key).format(*args)

    def toggle_language(self):
        """Switches the application language between English and Arabic."""
        self.current_lang = 'en' if self.current_lang == 'ar' else 'ar'
        self.update_ui_text()

    def update_ui_text(self):
        """Updates all UI text elements to the current language."""
        self.window.title(self.T('window_title'))
        self.app_title.config(text=self.T('main_title'))
        self.attendance_label.config(text=self.T('attendance_log'))
        self.status_label.config(text=self.T('status_init'))
        self.manage_users_button.config(text=self.T('manage_users'))
        self.dashboard_button.config(text=self.T('dashboard'))
        self.settings_button.config(text=self.T('settings'))
        self.attendance_tree.heading('name', text=self.T('col_name'))
        self.attendance_tree.heading('time', text=self.T('col_time'))

    def setup_database_and_folders(self):
        """Creates necessary folders and initializes the SQLite database and tables."""
        os.makedirs(DB_PATH, exist_ok=True)
        os.makedirs(UNKNOWN_PATH, exist_ok=True)
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, name TEXT, timestamp TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT UNIQUE, email TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        self.conn.commit()

        # Initialize default settings if not present
        default_settings = {
            'camera_index': '0', 'ear_threshold': '0.25', 'confidence_threshold': '0.4',
            'detector_backend': 'mtcnn', 'process_frame_interval': '1', 'selected_theme': 'superhero',
            'absentee_email_subject': self.texts['en']['absentee_email_subject'],
            'absentee_email_body': self.texts['en']['absentee_email_body'],
            'smtp_server': 'smtp.gmail.com', 'smtp_port': '465',
            'admin_password': hashlib.sha256('admin'.encode()).hexdigest() # Default password is 'admin'
        }
        for key, value in default_settings.items():
            self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def load_settings(self):
        """Loads all settings from the database into application variables."""
        self.cursor.execute("SELECT key, value FROM settings")
        settings = dict(self.cursor.fetchall())
        self.SENDER_EMAIL = settings.get('sender_email', '')
        self.EMAIL_PASSWORD = settings.get('email_password', '')
        self.RECEIVER_EMAIL = settings.get('receiver_email', '')
        self.SMTP_SERVER = settings.get('smtp_server', 'smtp.gmail.com')
        self.SMTP_PORT = int(settings.get('smtp_port', 465))
        self.CAMERA_INDEX = int(settings.get('camera_index', 0)) 
        self.EAR_THRESHOLD = float(settings.get('ear_threshold', 0.25))
        self.CONFIDENCE_THRESHOLD = float(settings.get('confidence_threshold', 0.4))
        self.DETECTOR_BACKEND = settings.get('detector_backend', 'mtcnn')
        self.PROCESS_FRAME_INTERVAL = int(settings.get('process_frame_interval', 1))
        self.selected_theme = settings.get('selected_theme', 'superhero')
        self.ALERT_EMAIL_SUBJECT = settings.get('email_subject_label', 'Security Alert: Unknown Person Detected')
        self.ALERT_EMAIL_BODY = settings.get('email_body_label', 'An unknown person was detected by the security system.')
        self.ADMIN_PASSWORD_HASH = settings.get('admin_password', hashlib.sha256('admin'.encode()).hexdigest())
        
        default_subject = self.texts[self.current_lang].get('absentee_email_subject', 'Attendance Reminder')
        default_body = self.texts[self.current_lang].get('absentee_email_body', 'Dear {name}, ...')
        self.ABSENTEE_EMAIL_SUBJECT = settings.get('absentee_email_subject', default_subject)
        self.ABSENTEE_EMAIL_BODY = settings.get('absentee_email_body', default_body)

        logging.info(f"Settings loaded successfully.")

    def check_password(self):
        """Prompts for the admin password and verifies it."""
        password = simpledialog.askstring(self.T('password_prompt_title'), self.T('password_prompt_text'), show='*')
        if password and hashlib.sha256(password.encode()).hexdigest() == self.ADMIN_PASSWORD_HASH:
            return True
        elif password is not None: # User entered something, but it was wrong
            messagebox.showerror(self.T('export_fail_title'), self.T('password_incorrect'))
        return False

    def open_settings_window(self):
        if self.check_password():
            SettingsWindow(self.window, self)

    def open_manage_users_window(self):
        if self.check_password():
            ManagementWindow(self.window, self)
        
    def open_dashboard_window(self):
        DashboardWindow(self.window, self)

    def setup_attendance_tree(self): 
        """Sets up the Treeview widget for displaying daily attendance."""
        self.attendance_tree = ttk.Treeview(self.attendance_frame, columns=('name', 'time'), show='headings', bootstyle=DARK)
        self.attendance_tree.heading('name', text=self.T('col_name'))
        self.attendance_tree.heading('time', text=self.T('col_time'))
        self.attendance_tree.column('name', width=150, anchor=tk.CENTER)
        self.attendance_tree.column('time', width=150, anchor=tk.CENTER)
        self.attendance_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    def update_clock(self): 
        """Updates the clock in the header every second."""
        self.clock_label.config(text=time.strftime('%Y-%m-%d %H:%M:%S'))
        self.window.after(1000, self.update_clock)

    def load_todays_attendance(self): 
        """Loads and displays attendance records for the current day from the database."""
        today_str = str(date.today())
        self.cursor.execute("SELECT name, strftime('%H:%M:%S', timestamp) FROM attendance WHERE date(timestamp) = ?", (today_str,))
        for i in self.attendance_tree.get_children(): self.attendance_tree.delete(i)
        for record in self.cursor.fetchall():
            self.attendance_tree.insert('', tk.END, values=record)
        logging.info("Today's attendance loaded.")

    def start_processing_thread(self): 
        """Starts the main video processing loop in a separate thread to avoid freezing the UI."""
        if hasattr(self, 'video_thread') and self.video_thread.is_alive():
            logging.warning("Processing thread is already running.")
            return
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
        logging.info("Video processing thread started.")

    def eye_aspect_ratio(self, eye): 
        """Calculates the Eye Aspect Ratio (EAR) for liveness detection."""
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    def mark_attendance(self, name):
        """Records attendance for a recognized employee if not already marked today."""
        today_str = str(date.today())
        self.cursor.execute("SELECT * FROM attendance WHERE name = ? AND date(timestamp) = ?", (name, today_str))
        if self.cursor.fetchone() is None:
            timestamp = datetime.now()
            self.cursor.execute("INSERT INTO attendance (name, timestamp) VALUES (?, ?)", (name, timestamp.strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            self.attendance_tree.insert('', tk.END, values=(name, timestamp.strftime('%H:%M:%S')))
            self.set_status(self.T('status_recognized', name))
            logging.info(f"Attendance marked for: {name} at {timestamp.strftime('%H:%M:%S')}")
        else:
            logging.info(f"Attendance already marked for: {name} today.")

    def send_email(self, receiver, subject, body, image_path=None):
        """Sends an email alert. Can optionally attach an image."""
        if not self.SENDER_EMAIL or not self.EMAIL_PASSWORD: 
            logging.warning("Email not sent: Sender email or password not configured in settings.")
            return False
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.SENDER_EMAIL
            msg['To'] = receiver
            msg.set_content(body)
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename=os.path.basename(image_path))
            
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT) as smtp:
                smtp.login(self.SENDER_EMAIL, self.EMAIL_PASSWORD)
                smtp.send_message(msg)
            
            logging.info(f"Email sent to {receiver} with subject: {subject}")
            return True
        except Exception as e: 
            self.set_status(self.T('status_email_fail', e))
            logging.error(f"Failed to send email to {receiver}: {e}")
            return False

    def save_unknown_visitor(self, face_crop):
        """Saves an image of an unknown person and sends an email alert."""
        current_time = time.time()
        # Throttle saving to prevent spamming with images of the same person
        if (current_time - getattr(self, 'last_unknown_saved_time', 0)) > 15:
            self.last_unknown_saved_time = current_time
            filename = os.path.join(UNKNOWN_PATH, f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            try:
                cv2.imwrite(filename, face_crop)
                logging.info(f"Unknown visitor image saved: {filename}")
                if self.RECEIVER_EMAIL:
                    threading.Thread(target=self.send_email, args=(self.RECEIVER_EMAIL, self.ALERT_EMAIL_SUBJECT, self.ALERT_EMAIL_BODY, filename), daemon=True).start()
                    self.set_status(self.T('status_email_sent'))
            except Exception as e:
                logging.error(f"Failed to save unknown visitor image or send email: {e}")

    def video_loop(self):
        """The main loop for capturing video, processing frames, and performing recognition."""
        video_capture = cv2.VideoCapture(self.CAMERA_INDEX)
        if not video_capture.isOpened():
            messagebox.showerror(self.T('export_fail_title'), self.T('export_fail_msg', f"Could not open camera with index {self.CAMERA_INDEX}. Check settings."))
            logging.error(f"Could not open camera with index {self.CAMERA_INDEX}.")
            return
        
        self.set_status(self.T('status_camera_ok'))
        logging.info(f"Camera opened with index: {self.CAMERA_INDEX}")

        blink_counter = 0; liveness_verified = False; last_recognition_time = 0
        frame_count = 0
        while self.is_running:
            ret, frame = video_capture.read()
            if not ret: 
                logging.warning("Failed to grab frame from camera.")
                time.sleep(0.1); continue
            
            frame_count += 1
            if self.PROCESS_FRAME_INTERVAL > 1 and frame_count % self.PROCESS_FRAME_INTERVAL != 0:
                photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                self.canvas.create_image(0, 0, image=photo, anchor=tk.NW); self.canvas.image = photo 
                time.sleep(0.01)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces_dlib = self.face_detector_dlib(gray, 0)

            current_frame_has_face = False
            if len(faces_dlib) > 0:
                current_frame_has_face = True
                face = max(faces_dlib, key=lambda rect: rect.width() * rect.height())
                
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                face_crop_color = frame[y:y+h, x:x+w]

                if face_crop_color.size == 0:
                    logging.warning("Face crop is empty, skipping processing for this face.")
                    continue

                if not liveness_verified:
                    self.set_status(self.T('status_liveness_check'))
                    shape = self.landmark_predictor(gray, face)
                    shape = shape_to_np(shape)
                    ear = (self.eye_aspect_ratio(shape[self.lStart:self.lEnd]) + self.eye_aspect_ratio(shape[self.rStart:self.rEnd])) / 2.0
                    
                    if ear < self.EAR_THRESHOLD: blink_counter += 1
                    else:
                        if blink_counter >= EAR_CONSEC_FRAMES:
                            liveness_verified = True
                            self.set_status(self.T('status_liveness_success'))
                            logging.info("Liveness verified!")
                        blink_counter = 0
                    
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    cv2.putText(frame, "Blink!", (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)

                if liveness_verified and time.time() - last_recognition_time > 5:
                    logging.info("Attempting DeepFace recognition...")
                    try:
                        dfs = DeepFace.find(img_path=face_crop_color, db_path=DB_PATH, model_name=MODEL_NAME, detector_backend=self.DETECTOR_BACKEND, enforce_detection=False, silent=True)
                        
                        if isinstance(dfs, list) and len(dfs) > 0 and not dfs[0].empty:
                            instance = dfs[0].iloc[0]
                            distance = instance[f'{MODEL_NAME}_cosine']
                            logging.info(f"DeepFace result: Identity: {instance['identity']}, Distance: {distance:.4f}")

                            if distance < self.CONFIDENCE_THRESHOLD:
                                recognized_name = os.path.basename(os.path.dirname(instance['identity']))
                                self.mark_attendance(recognized_name)
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                cv2.putText(frame, recognized_name, (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
                            else: 
                                self.save_unknown_visitor(face_crop_color)
                                self.set_status(self.T('status_unknown'))
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                                cv2.putText(frame, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 255), 2)
                        else: 
                            self.save_unknown_visitor(face_crop_color)
                            self.set_status(self.T('status_unknown'))
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                            cv2.putText(frame, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 255), 2)
                    except Exception as e: 
                        logging.error(f"DeepFace recognition error: {e}")
                    
                    liveness_verified = False
                    last_recognition_time = time.time()
            
            if not current_frame_has_face:
                self.set_status(self.T('status_searching'))
                liveness_verified = False
                blink_counter = 0

            photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=photo, anchor=tk.NW); self.canvas.image = photo 
            time.sleep(0.01)

        video_capture.release()
        logging.info("Video loop stopped.")

    def set_status(self, text): 
        """Updates the status bar text."""
        self.status_label.config(text=text)

    def on_closing(self): 
        """Handles the application closing event gracefully."""
        logging.info("Closing application...")
        self.is_running = False
        if hasattr(self, 'video_thread') and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.0)
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logging.info("Database connection closed.")
        self.window.destroy()

class SettingsWindow(Toplevel):
    """A Toplevel window for configuring application settings."""
    def __init__(self, master_tk_window, master_app):
        super().__init__(master_tk_window)
        self.master_app = master_app
        self.title(self.master_app.T('settings_title'))
        self.geometry("600x750")
        self.transient(master_tk_window)
        self.grab_set()

        self.scrolled_frame = ScrolledFrame(self, bootstyle="secondary", autohide=True)
        self.scrolled_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame = ttk.Frame(self.scrolled_frame, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Security Settings ---
        security_frame = ttk.LabelFrame(main_frame, text="Security", bootstyle=DANGER)
        security_frame.pack(fill=tk.X, pady=10)
        ttk.Label(security_frame, text=self.master_app.T('admin_password_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.password_var = tk.StringVar()
        ttk.Entry(security_frame, textvariable=self.password_var, show="*").pack(fill=tk.X, padx=10, pady=5)


        # --- Email Settings ---
        email_frame = ttk.LabelFrame(main_frame, text="Email Configuration", bootstyle=INFO)
        email_frame.pack(fill=tk.X, pady=10)
        ttk.Label(email_frame, text=self.master_app.T('sender_email')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.sender_email_var = tk.StringVar(value=self.master_app.SENDER_EMAIL)
        ttk.Entry(email_frame, textvariable=self.sender_email_var).pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(email_frame, text=self.master_app.T('app_password')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.email_password_var = tk.StringVar(value=self.master_app.EMAIL_PASSWORD)
        ttk.Entry(email_frame, textvariable=self.email_password_var, show="*").pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(email_frame, text=self.master_app.T('password_warning'), bootstyle=WARNING).pack(pady=(0,5), anchor=tk.W, padx=10)
        ttk.Label(email_frame, text=self.master_app.T('receiver_email')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.receiver_email_var = tk.StringVar(value=self.master_app.RECEIVER_EMAIL)
        ttk.Entry(email_frame, textvariable=self.receiver_email_var).pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(email_frame, text=self.master_app.T('smtp_server_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.smtp_server_var = tk.StringVar(value=self.master_app.SMTP_SERVER)
        ttk.Entry(email_frame, textvariable=self.smtp_server_var).pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(email_frame, text=self.master_app.T('smtp_port_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.smtp_port_var = tk.StringVar(value=str(self.master_app.SMTP_PORT))
        ttk.Entry(email_frame, textvariable=self.smtp_port_var).pack(fill=tk.X, padx=10, pady=5)

        # --- Technical Settings ---
        tech_frame = ttk.LabelFrame(main_frame, text="Technical Configuration", bootstyle=INFO)
        tech_frame.pack(fill=tk.X, pady=10)
        ttk.Label(tech_frame, text=self.master_app.T('camera_index_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.camera_index_var = tk.StringVar(value=str(self.master_app.CAMERA_INDEX))
        ttk.Entry(tech_frame, textvariable=self.camera_index_var).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(tech_frame, text=self.master_app.T('ear_threshold_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.ear_threshold_var = tk.StringVar(value=str(self.master_app.EAR_THRESHOLD))
        ttk.Entry(tech_frame, textvariable=self.ear_threshold_var).pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(tech_frame, text=self.master_app.T('confidence_threshold_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.confidence_threshold_var = tk.StringVar(value=str(self.master_app.CONFIDENCE_THRESHOLD))
        ttk.Entry(tech_frame, textvariable=self.confidence_threshold_var).pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(tech_frame, text=self.master_app.T('detector_backend_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.detector_backend_var = tk.StringVar(value=self.master_app.DETECTOR_BACKEND)
        self.detector_backend_options = ["opencv", "ssd", "dlib", "mtcnn", "retinaface", "mediapipe"]
        ttk.OptionMenu(tech_frame, self.detector_backend_var, self.master_app.DETECTOR_BACKEND, *self.detector_backend_options, bootstyle="info").pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(tech_frame, text=self.master_app.T('process_interval_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.process_interval_var = tk.StringVar(value=str(self.master_app.PROCESS_FRAME_INTERVAL))
        ttk.Entry(tech_frame, textvariable=self.process_interval_var).pack(fill=tk.X, padx=10, pady=5)

        # --- UI and Email Content Settings ---
        content_frame = ttk.LabelFrame(main_frame, text="Content & Appearance", bootstyle=INFO)
        content_frame.pack(fill=tk.X, pady=10)
        ttk.Label(content_frame, text=self.master_app.T('theme_label')).pack(pady=(5,0), anchor=tk.W, padx=10)
        self.theme_var = tk.StringVar(value=self.master_app.selected_theme)
        self.available_themes = self.master_app.style.theme_names()
        ttk.OptionMenu(content_frame, self.theme_var, self.master_app.selected_theme, *self.available_themes, bootstyle="info").pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(main_frame, text=self.master_app.T('save_settings'), command=self.save, bootstyle=SUCCESS).pack(pady=25, fill=tk.X)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def save(self):
        """Validates and saves all settings to the database."""
        try:
            settings_to_save = {
                'sender_email': self.sender_email_var.get(), 'email_password': self.email_password_var.get(),
                'receiver_email': self.receiver_email_var.get(), 'smtp_server': self.smtp_server_var.get(),
                'smtp_port': str(int(self.smtp_port_var.get())), 'camera_index': str(int(self.camera_index_var.get())),
                'ear_threshold': str(float(self.ear_threshold_var.get())), 'confidence_threshold': str(float(self.confidence_threshold_var.get())),
                'detector_backend': self.detector_backend_var.get(), 'process_frame_interval': str(int(self.process_interval_var.get())),
                'selected_theme': self.theme_var.get()
            }
            # Only update password if a new one is entered
            new_password = self.password_var.get()
            if new_password:
                settings_to_save['admin_password'] = hashlib.sha256(new_password.encode()).hexdigest()

        except ValueError:
            messagebox.showerror(self.master_app.T('export_fail_title'), "Invalid input for numeric fields. Please enter numbers.", parent=self)
            return

        for key, value in settings_to_save.items():
            self.master_app.cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.master_app.conn.commit()
        self.master_app.load_settings()
        self.master_app.style.theme_use(self.master_app.selected_theme)
        messagebox.showinfo(self.master_app.T('export_success_title'), self.master_app.T('settings_saved'), parent=self)
        self.destroy()
        logging.info("Settings saved successfully.")

    def on_closing(self):
        self.master_app.window.focus_set()
        self.destroy()

class ManagementWindow(Toplevel):
    """A Toplevel window for managing employees, viewing absentees, and creating backups."""
    def __init__(self, master_tk_window, master_app):
        super().__init__(master_tk_window)
        self.master_app = master_app
        self.title(self.master_app.T('manage_users'))
        self.geometry("950x700")
        self.transient(master_tk_window)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill=tk.BOTH)

        all_emp_frame = ttk.LabelFrame(paned_window, text=self.master_app.T('all_employees'), bootstyle=PRIMARY)
        paned_window.add(all_emp_frame, weight=2)
        self.emp_tree = ttk.Treeview(all_emp_frame, columns=('name', 'email'), show='headings', bootstyle=DARK)
        self.emp_tree.heading('name', text=self.master_app.T('col_name'))
        self.emp_tree.heading('email', text=self.master_app.T('col_email'))
        self.emp_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        # Bind double-click event to open profile
        self.emp_tree.bind("<Double-1>", self.open_employee_profile)
        
        btn_frame = ttk.Frame(all_emp_frame)
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        ttk.Button(btn_frame, text=self.master_app.T('add'), command=self.add_employee_dialog, bootstyle=SUCCESS).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(btn_frame, text=self.master_app.T('edit'), command=self.edit_employee, bootstyle=INFO).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(btn_frame, text=self.master_app.T('delete'), command=self.delete_employee, bootstyle=DANGER).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tools_frame_container = ttk.Frame(paned_window)
        paned_window.add(tools_frame_container, weight=1)

        absent_frame = ttk.LabelFrame(tools_frame_container, text=self.master_app.T('absent_today'), bootstyle=WARNING)
        absent_frame.pack(expand=True, fill=tk.BOTH, pady=(0, 10))
        self.absent_list = tk.Listbox(absent_frame, font=("Helvetica", 12))
        self.absent_list.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        ttk.Button(absent_frame, text=self.master_app.T('notify_absentees'), command=self.notify_absentees, bootstyle=WARNING).pack(fill=tk.X, padx=10, pady=10)
        
        backup_frame = ttk.LabelFrame(tools_frame_container, text="Utilities", bootstyle=SECONDARY)
        backup_frame.pack(fill=tk.X)
        ttk.Button(backup_frame, text=self.master_app.T('backup_db_btn'), command=self.backup_database, bootstyle=PRIMARY).pack(fill=tk.X, padx=10, pady=10)

        self.refresh_data()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def open_employee_profile(self, event):
        """Opens the detailed profile window for the double-clicked employee."""
        selected_item = self.emp_tree.focus()
        if not selected_item: return
        employee_name = self.emp_tree.item(selected_item)['values'][0]
        EmployeeProfileWindow(self, self.master_app, employee_name)

    def refresh_data(self):
        """Refreshes the employee and absentee lists with current data from the database."""
        for i in self.emp_tree.get_children(): self.emp_tree.delete(i)
        self.absent_list.delete(0, tk.END)

        self.master_app.cursor.execute("SELECT name, email FROM employees ORDER BY name")
        all_employees = self.master_app.cursor.fetchall()
        for emp in all_employees: self.emp_tree.insert('', tk.END, values=emp)

        today_str = str(date.today())
        self.master_app.cursor.execute("SELECT name FROM attendance WHERE date(timestamp) = ?", (today_str,))
        present_today = {row[0] for row in self.master_app.cursor.fetchall()}
        all_emp_names = {emp[0] for emp in all_employees}
        absent_today = sorted(list(all_emp_names - present_today))
        
        if not absent_today: self.absent_list.insert(tk.END, self.master_app.T('no_absentees'))
        else:
            for name in absent_today: self.absent_list.insert(tk.END, name)
        logging.info("Management data refreshed.")

    def add_employee_dialog(self):
        """Opens a dialog to add a new employee."""
        add_window = Toplevel(self)
        add_window.title(self.master_app.T('add_user_title'))
        add_window.geometry("450x250")
        add_window.transient(self); add_window.grab_set()

        frame = ttk.Frame(add_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=self.master_app.T('add_user_prompt')).pack(pady=(5,0), anchor=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=40).pack(fill=tk.X, pady=5)

        ttk.Label(frame, text=self.master_app.T('email_prompt')).pack(pady=(10,0), anchor=tk.W)
        email_var = tk.StringVar()
        ttk.Entry(frame, textvariable=email_var, width=40).pack(fill=tk.X, pady=5)

        ttk.Button(frame, text=self.master_app.T('capture_photos_btn'), bootstyle=PRIMARY,
                   command=lambda: self._capture_and_save_employee(name_var.get(), email_var.get(), add_window)).pack(pady=25, fill=tk.X)

    def _capture_and_save_employee(self, name, email, add_window):
        """Handles the logic for capturing photos and saving a new employee."""
        if not name or name.isspace() or not email or email.isspace():
            messagebox.showerror(self.master_app.T('export_fail_title'), "Name and email cannot be empty.", parent=add_window)
            return

        try:
            self.master_app.cursor.execute("INSERT INTO employees (name, email) VALUES (?, ?)", (name, email))
            self.master_app.conn.commit()
            logging.info(f"Employee '{name}' added to database.")
            
            self.master_app.is_running = False
            if self.master_app.video_thread.is_alive():
                self.master_app.video_thread.join(timeout=1.0)
            
            employee_dir = os.path.join(DB_PATH, name)
            os.makedirs(employee_dir, exist_ok=True)

            cap = cv2.VideoCapture(self.master_app.CAMERA_INDEX) 
            if not cap.isOpened():
                raise Exception(f"Could not open camera {self.master_app.CAMERA_INDEX}")

            for i in range(3):
                messagebox.showinfo(self.master_app.T('capture_title'), self.master_app.T('capture_prompt', i+1), parent=add_window)
                ret, frame = cap.read()
                if ret: 
                    cv2.imwrite(os.path.join(employee_dir, f"{name}_{i+1}.jpg"), frame)
                    logging.info(f"Captured image {i+1} for {name}.")
                else:
                    raise Exception("Failed to capture image from camera.")
            
            cap.release()
            
            pickle_file = os.path.join(DB_PATH, f"representations_{MODEL_NAME}.pkl")
            if os.path.exists(pickle_file):
                try:
                    os.remove(pickle_file)
                    logging.info(f"Removed DeepFace cache file: {pickle_file}")
                except Exception as e:
                    logging.error(f"Could not remove cache file {pickle_file}: {e}")
                    messagebox.showwarning("Cache Warning", "Could not clear the face model cache. A manual restart might be required for the new user to be recognized.", parent=add_window)

            messagebox.showinfo(self.master_app.T('export_success_title'), self.master_app.T('add_user_success_no_restart', name), parent=add_window)
            self.refresh_data()
            
        except sqlite3.IntegrityError:
            messagebox.showerror(self.master_app.T('export_fail_title'), self.master_app.T('export_fail_msg', f"Employee '{name}' already exists."), parent=add_window)
            logging.warning(f"Attempted to add existing employee: {name}")
        except Exception as e:
            messagebox.showerror(self.master_app.T('export_fail_title'), self.master_app.T('export_fail_msg', e), parent=add_window)
            logging.error(f"Error during employee add/capture: {e}")
            self.master_app.cursor.execute("DELETE FROM employees WHERE name = ?", (name,))
            self.master_app.conn.commit()
        finally:
            self.master_app.is_running = True
            self.master_app.start_processing_thread()
            add_window.destroy()

    def edit_employee(self):
        """Edits the selected employee's email."""
        selected_item = self.emp_tree.focus()
        if not selected_item: return
        item_details = self.emp_tree.item(selected_item)
        name, current_email = item_details['values']
        
        new_email = simpledialog.askstring("Edit Email", f"Enter new email for {name}:", initialvalue=current_email, parent=self)
        if new_email and not new_email.isspace():
            self.master_app.cursor.execute("UPDATE employees SET email = ? WHERE name = ?", (new_email, name))
            self.master_app.conn.commit()
            self.refresh_data()
            logging.info(f"Employee '{name}' email updated to {new_email}.")

    def delete_employee(self):
        """Deletes an employee from the database and removes their images."""
        selected_item = self.emp_tree.focus()
        if not selected_item: return
        name = self.emp_tree.item(selected_item)['values'][0]
        
        if messagebox.askyesno(self.master_app.T('delete'), self.master_app.T('confirm_delete', name), parent=self):
            self.master_app.cursor.execute("DELETE FROM employees WHERE name = ?", (name,))
            self.master_app.cursor.execute("DELETE FROM attendance WHERE name = ?", (name,))
            self.master_app.conn.commit()
            logging.info(f"Employee '{name}' deleted from database.")
            
            employee_dir = os.path.join(DB_PATH, name)
            if os.path.isdir(employee_dir):
                shutil.rmtree(employee_dir)
                logging.info(f"Deleted image directory: {employee_dir}")
            
            pickle_file = os.path.join(DB_PATH, f"representations_{MODEL_NAME}.pkl")
            if os.path.exists(pickle_file):
                os.remove(pickle_file)
                logging.info("Removed DeepFace cache file due to user deletion.")

            self.refresh_data()

    def notify_absentees(self):
        """Sends a reminder email to all employees marked as absent today."""
        absent_employees = [self.absent_list.get(i) for i in range(self.absent_list.size())]
        if not absent_employees or absent_employees[0] == self.master_app.T('no_absentees'):
            messagebox.showinfo(self.master_app.T('export_success_title'), self.master_app.T('no_absentees'), parent=self)
            return

        q_marks = ','.join('?'*len(absent_employees))
        self.master_app.cursor.execute(f"SELECT name, email FROM employees WHERE name IN ({q_marks})", absent_employees)
        absentees_with_emails = self.master_app.cursor.fetchall()
        
        sent_count = 0
        for name, email in absentees_with_emails:
            if email:
                body = self.master_app.ABSENTEE_EMAIL_BODY.format(name=name)
                threading.Thread(target=self.master_app.send_email, args=(email, self.master_app.ABSENTEE_EMAIL_SUBJECT, body), daemon=True).start()
                sent_count += 1
        
        messagebox.showinfo(self.master_app.T('export_success_title'), self.master_app.T('absentee_email_sent'), parent=self)
        logging.info(f"Sent {sent_count} notification emails to absentees.")

    def backup_database(self):
        """Creates a safe, timestamped backup of the SQLite database using the online backup API."""
        backup_dir = "db_backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = os.path.join(backup_dir, f"attendance_system_backup_{timestamp}.db")
        try:
            backup_conn = sqlite3.connect(backup_filename)
            with backup_conn:
                self.master_app.conn.backup(backup_conn)
            backup_conn.close()
            messagebox.showinfo(self.master_app.T('export_success_title'), self.master_app.T('backup_success', backup_filename), parent=self)
            logging.info(f"Database backed up to: {backup_filename}")
        except Exception as e:
            messagebox.showerror(self.master_app.T('export_fail_title'), self.master_app.T('backup_fail', e), parent=self)
            logging.error(f"Failed to backup database: {e}")

    def on_closing(self):
        self.master_app.window.focus_set()
        self.destroy()

class DashboardWindow(Toplevel):
    """A Toplevel window for visualizing attendance data with reports and charts."""
    def __init__(self, master_tk_window, master_app):
        super().__init__(master_tk_window)
        self.master_app = master_app
        self.title(self.master_app.T('dashboard_title'))
        self.geometry("900x650")
        self.transient(master_tk_window)
        self.grab_set()

        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)

        try:
            conn = sqlite3.connect(DATABASE_FILE)
            self.df_attendance = pd.read_sql_query("SELECT name, timestamp FROM attendance", conn)
            conn.close()
            self.df_attendance['timestamp'] = pd.to_datetime(self.df_attendance['timestamp'])
            self.df_attendance['attendance_date'] = self.df_attendance['timestamp'].dt.date
        except Exception as e:
            messagebox.showerror(self.master_app.T('export_fail_title'), f"Could not load data from database: {e}", parent=self)
            logging.error(f"Error loading dashboard data: {e}")
            self.df_attendance = pd.DataFrame()

        f1 = ttk.Frame(notebook)
        notebook.add(f1, text=self.master_app.T('monthly_report_tab'))
        self.create_monthly_report_tab(f1)

        f2 = ttk.Frame(notebook)
        notebook.add(f2, text=self.master_app.T('weekly_chart_tab'))
        self.create_weekly_chart_tab(f2)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_monthly_report_tab(self, parent_frame):
        """Creates the content for the monthly report tab."""
        tree = ttk.Treeview(parent_frame, columns=('name', 'days'), show='headings', bootstyle=DARK)
        tree.heading('name', text=self.master_app.T('db_col_name'))
        tree.heading('days', text=self.master_app.T('db_col_days'))
        tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        if not self.df_attendance.empty:
            current_month_df = self.df_attendance[self.df_attendance['timestamp'].dt.month == datetime.now().month]
            monthly_counts = current_month_df.groupby('name')['attendance_date'].nunique().reset_index(name='days')
            for _, row in monthly_counts.iterrows():
                tree.insert('', tk.END, values=(row['name'], row['days']))
        
        ttk.Button(parent_frame, text=self.master_app.T('export_monthly_btn'), 
                   command=lambda: self.export_report(tree, "monthly_report"), bootstyle=INFO).pack(pady=10)

    def create_weekly_chart_tab(self, parent_frame):
        """Creates the content for the weekly attendance chart tab."""
        try:
            fig = Figure(figsize=(6, 5), dpi=100)
            ax = fig.add_subplot(111)
            
            if not self.df_attendance.empty:
                weekly_counts = self.df_attendance.groupby(self.df_attendance['timestamp'].dt.day_name())['name'].nunique()
                all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekly_counts = weekly_counts.reindex(all_days, fill_value=0)
                weekly_counts.plot(kind='bar', ax=ax, title=self.master_app.T('chart_title'), color=self.master_app.style.colors.get("primary"))
                ax.set_ylabel("Unique Employees")
                ax.set_xlabel("")
                ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)
            
            ttk.Button(parent_frame, text=self.master_app.T('export_weekly_btn'), 
                       command=lambda: self.export_report(None, "weekly_chart"), bootstyle=INFO).pack(pady=10)
        except Exception as e:
            ttk.Label(parent_frame, text=f"Chart Error: {e}", bootstyle="danger").pack(pady=20)
            logging.error(f"Error loading weekly chart: {e}")

    def export_report(self, tree_data, report_type):
        """Exports data from the dashboard to a CSV file."""
        export_dir = "reports"
        os.makedirs(export_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if report_type == "monthly_report" and tree_data:
                filename = os.path.join(export_dir, f"monthly_attendance_{timestamp}.csv")
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.master_app.T('db_col_name'), self.master_app.T('db_col_days')])
                    for item in tree_data.get_children():
                        writer.writerow(tree_data.item(item)['values'])
            elif report_type == "weekly_chart" and not self.df_attendance.empty:
                filename = os.path.join(export_dir, f"weekly_chart_data_{timestamp}.csv")
                weekly_counts = self.df_attendance.groupby(self.df_attendance['timestamp'].dt.day_name())['name'].nunique()
                all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekly_counts = weekly_counts.reindex(all_days, fill_value=0)
                weekly_counts.to_csv(filename, encoding='utf-8-sig', header=[self.master_app.T('chart_title_short')])
            else:
                raise ValueError("Invalid report type or missing data.")
            
            messagebox.showinfo(self.master_app.T('export_success_title'), self.master_app.T('export_success_msg', filename), parent=self)
            logging.info(f"Report exported to: {filename}")
        except Exception as e:
            messagebox.showerror(self.master_app.T('export_fail_title'), self.master_app.T('export_fail_msg', e), parent=self)
            logging.error(f"Failed to export report: {e}")

    def on_closing(self):
        self.master_app.window.focus_set()
        self.destroy()

class EmployeeProfileWindow(Toplevel):
    """A Toplevel window to display a single employee's details and full attendance history."""
    def __init__(self, master, main_app, employee_name):
        super().__init__(master)
        self.main_app = main_app
        self.employee_name = employee_name
        self.title(self.main_app.T('profile_window_title', employee_name))
        self.geometry("700x500")
        self.transient(master)
        self.grab_set()

        # Main frame
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Top frame for photo and details
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=10)

        # Photo
        self.photo_label = ttk.Label(top_frame)
        self.photo_label.pack(side=tk.LEFT, padx=10)
        self.load_employee_photo()

        # Details
        details_frame = ttk.Frame(top_frame)
        details_frame.pack(side=tk.LEFT, padx=10, anchor=tk.N)
        ttk.Label(details_frame, text=employee_name, font=("Helvetica", 16, "bold")).pack(anchor=tk.W)
        
        email = self.get_employee_email()
        ttk.Label(details_frame, text=email, font=("Helvetica", 12)).pack(anchor=tk.W)

        # Attendance Log
        log_frame = ttk.LabelFrame(main_frame, text=self.main_app.T('profile_attendance_log'), bootstyle=INFO)
        log_frame.pack(expand=True, fill=tk.BOTH, pady=10)

        tree = ttk.Treeview(log_frame, columns=('date', 'time'), show='headings', bootstyle=DARK)
        tree.heading('date', text=self.main_app.T('profile_col_date'))
        tree.heading('time', text=self.main_app.T('profile_col_time'))
        tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Load all attendance records for this employee
        self.main_app.cursor.execute(
            "SELECT strftime('%Y-%m-%d', timestamp), strftime('%H:%M:%S', timestamp) FROM attendance WHERE name = ? ORDER BY timestamp DESC",
            (self.employee_name,)
        )
        for record in self.main_app.cursor.fetchall():
            tree.insert('', tk.END, values=record)

    def get_employee_email(self):
        """Fetches the employee's email from the database."""
        self.main_app.cursor.execute("SELECT email FROM employees WHERE name = ?", (self.employee_name,))
        result = self.main_app.cursor.fetchone()
        return result[0] if result else "N/A"

    def load_employee_photo(self):
        """Loads and displays the first available photo of the employee."""
        employee_dir = os.path.join(DB_PATH, self.employee_name)
        if os.path.isdir(employee_dir):
            image_files = [f for f in os.listdir(employee_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                try:
                    img_path = os.path.join(employee_dir, image_files[0])
                    img = Image.open(img_path)
                    img.thumbnail((150, 150)) # Resize for display
                    self.photo = ImageTk.PhotoImage(img)
                    self.photo_label.config(image=self.photo)
                    return
                except Exception as e:
                    logging.error(f"Could not load photo for {self.employee_name}: {e}")
        # Fallback if no image is found
        self.photo_label.config(text="No Image")


# --- Helper Functions (وظائف مساعدة) ---
def shape_to_np(shape, dtype="int"):
    """Converts dlib's shape object to a NumPy array."""
    coords = np.zeros((68, 2), dtype=dtype)
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords

if __name__ == "__main__":
    # Use a modern ttkbootstrap window
    root = ttk.Window(themename="superhero")
    app = MainApp(root)
    root.mainloop()
