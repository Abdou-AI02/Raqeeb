<div align="center">

Raqeeb: AI Attendance & Security System
نظام رقيب: نظام الحضور والأمان المدعوم بالذكاء الاصطناعي
<p>
An advanced, real-time facial recognition system built with Python to automate employee attendance and enhance security, featuring liveness detection, a detailed management dashboard, and a bilingual interface.
</p>

<p>
<a href="#-table-of-contents"><strong>Table of Contents</strong></a>
</p>

</div>

📋 Table of Contents
Project Overview

Core Features

How It Works: The Technical Pipeline

Tech Stack

Project Structure

Installation & Setup

How to Run

Usage Guide

Configuration Options

Future Work

Contributing

License

Arabic Version (النسخة العربية)

🎯 Project Overview
Traditional attendance systems like fingerprint scanners or ID cards can be inefficient and pose hygiene risks. They are also susceptible to "buddy punching," where one employee clocks in for another. Raqeeb addresses these challenges by providing a touchless, secure, and automated solution. It leverages the power of AI to ensure that attendance is marked accurately and effortlessly, while also bolstering on-site security by identifying unauthorized individuals.

✨ Core Features
📸 Real-Time Face Recognition: Automatically clocks in employees by identifying their faces from a live video stream.

👁️ Liveness Detection: Prevents spoofing attacks (e.g., using a photo or video) by requiring users to blink, ensuring the subject is a real, live person.

🌍 Bilingual Interface: Seamlessly switch between English and Arabic with a single click to cater to different users.

🔑 Secure Admin Access: Password protection for sensitive sections like Settings and Employee Management to prevent unauthorized access.

👥 Comprehensive Employee Management: A dedicated panel to add new employees, capture their photos, edit their details (email), and delete profiles securely.

📊 Advanced Dashboard: Visualize attendance data with monthly reports and weekly charts. Export all reports to CSV files for further analysis or record-keeping.

📧 Email Security Alerts: Automatically sends an email notification—with a snapshot of the unrecognized person—to the system administrator.

👤 Detailed Employee Profiles: Double-click any employee to view their profile, including their photo and a complete, timestamped attendance history.

💾 Database Backup: A one-click utility to create a secure, timestamped backup of the entire system database.

⚙️ How It Works: The Technical Pipeline
The system follows a sophisticated pipeline to ensure accurate and secure recognition:

Camera Activation & Frame Grabbing: The system initializes the webcam using OpenCV and continuously captures video frames.

Face Detection: Each frame is processed to detect faces. The dlib library's frontal face detector is used for its efficiency and accuracy in locating human faces within the frame.

Liveness Check (Anti-Spoofing): This is a critical security step.

If a face is detected, the system uses dlib's shape predictor to identify 68 facial landmarks (eyes, nose, mouth, etc.).

It calculates the Eye Aspect Ratio (EAR) for both eyes. The EAR is a ratio of distances between facial landmarks of the eye. It is nearly constant when an eye is open and drops to zero when it closes.

The system monitors the EAR value. If it drops below a certain threshold for a consecutive number of frames (indicating a blink), the person is verified as "live."

Face Recognition:

Once liveness is verified, the detected face is cropped and passed to the DeepFace library.

DeepFace computes a facial embedding (a vector of numbers representing the face) and compares it against a pre-computed database of embeddings for all registered employees.

The comparison is done using a distance metric (e.g., Cosine Distance). If the distance is below a pre-defined confidence threshold, the face is considered a match.

Database Interaction & Action:

If Recognized: The system logs the employee's name and the current timestamp into the SQLite database, but only if they haven't already been marked present for the day.

If Unknown: If the face does not match any known employee, the system saves a snapshot of the person to the unknown_visitors folder and triggers an email alert to the administrator.

Real-Time UI Update: The application's main interface, built with ttkbootstrap, is updated in real-time to reflect the latest attendance logs and system status messages.

💻 Tech Stack
Category

Technology

Core Language

🐍 Python 3.8+

User Interface

🖼️ Tkinter (with ttkbootstrap for modern styling)

AI & Computer Vision

🧠 DeepFace, dlib, OpenCV

Data & Reporting

🗃️ SQLite, Pandas, Matplotlib

Image Handling

🎨 Pillow (PIL)

📁 Project Structure
To provide a clear understanding of the project's architecture, here is a detailed breakdown of each file and directory:

Path

Type

Description

known_faces/

Directory

Employee Image Database. When a new employee is added, a sub-directory with their name is created here, and their photos are stored inside. The system uses these images for recognition.

unknown_visitors/

Directory

Log of Unrecognized Visitors. When the system detects a face that doesn't match any employee, a snapshot is saved here. This is useful for security and reviewing access attempts.

reports/

Directory

Exported Reports Folder. When you export attendance reports from the dashboard, they are saved here as CSV files, making them easy to analyze or use in other programs like Excel.

db_backups/

Directory

Database Backups. Contains timestamped backup copies of the database. It is crucial to create backups regularly to protect your data from loss.

Raqeeb.py

Python File

Main Executable Script. This is the file you run to start the application. It contains the code for the user interface, face recognition logic, and system management.

requirements.txt

Text File

Required Libraries List. This file lists all the Python libraries the project depends on. Use pip install -r requirements.txt to install them all at once.

attendance_system.db

Database

SQLite Database. This file stores all application data in an organized manner, including employee information, attendance records, and system settings.

app.log

Log File

System Event Log. This file automatically records important operations and errors that occur while the program is running, which is very useful for diagnosing and fixing problems.

shape_predictor_68_face_landmarks.dat

Model File

dlib Facial Landmark Model. An essential, pre-trained file used by the system to identify 68 points on a face (like eyes, nose, and mouth), which is necessary for the liveness detection feature.

README.md

Markdown

Documentation File. The file you are currently reading. It provides a comprehensive explanation of the project, how to install it, use it, and contribute to its development.

🛠️ Installation & Setup
Follow these steps to get the project up and running on your local machine.

Prerequisites:
Python 3.8 or newer.

A webcam connected to your system.

Step 1: Clone & Set Up a Virtual Environment
# Clone the repository (replace [YOUR-REPO-NAME] with your repository name)
git clone [https://github.com/Abdou-AI02/](https://github.com/Abdou-AI02/)[YOUR-REPO-NAME].git
cd [YOUR-REPO-NAME]

# Create and activate a virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

Step 2: Install Dependencies
Install all the required libraries from the requirements.txt file.

pip install -r requirements.txt

Step 3: Download the dlib Shape Predictor Model
The facial landmark detection requires a pre-trained model.

Download the model from http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2.

Extract the shape_predictor_68_face_landmarks.dat file and place it in the root directory of the project.

🚀 How to Run
Once everything is set up, run the application with the following command:

python Raqeeb.py

Default Password: The default admin password is admin. It is highly recommended to change it immediately from the Settings window for security purposes.

📖 Usage Guide
The application is divided into several intuitive sections:

Main Window: This is the central hub. It displays the live camera feed on the left and a real-time log of today's attendance on the right. The status bar at the bottom provides feedback on the system's current operation (e.g., "Searching for faces...", "Liveness verified...", "Recognized: [Name]").

👤 Manage Employees Panel: (Password Protected) This is the control center for employee data.

Add: Opens a window to register a new employee by entering their name and email, then capturing 3 photos for their profile.

Edit: Allows you to update the email address of a selected employee.

Delete: Securely removes an employee from the database and deletes their associated images.

View Profile: Double-click any employee in the list to open a detailed profile window showing their photo and a complete, scrollable log of all their past attendance records.

📊 Dashboard: This section provides insights into attendance trends.

Monthly Report: A table showing the total number of days each employee was present during the current month.

Weekly Chart: A bar chart visualizing the number of unique employees present on each day of the week.

Export: Both views have a button to export the displayed data to a CSV file for archiving or further analysis.

⚙️ Settings Panel: (Password Protected) This window allows you to customize the system's core functionality. See the configuration section below for more details.

🔧 Configuration Options
You can customize the system's behavior from the Settings window:

Admin Password: Change the password required to access sensitive areas. A new password must be entered to update it.

Email Settings: Configure the sender/receiver emails, app password (use an app-specific password for services like Gmail), and SMTP server details for security alerts.

Technical Parameters:

Camera Index: Change the default camera (e.g., from 0 to 1 if you have multiple cameras).

Confidence Threshold: Lower this value to make recognition stricter, or raise it to be more lenient.

EAR Threshold: Adjust the Eye Aspect Ratio threshold for liveness detection based on your camera and lighting conditions.

Theme: Change the visual theme of the application from a dropdown list of available ttkbootstrap themes.

💡 Future Work
This project has a solid foundation, but there are many potential areas for expansion:

[ ] Web-Based Interface: Develop a web dashboard using a framework like Flask or Django for remote management.

[ ] Dockerization: Containerize the application with Docker for easier deployment and scalability.

[ ] Advanced Analytics: Add more detailed reports, such as tracking late arrivals or generating payroll summaries.

[ ] Mobile Application: A companion mobile app for employees to view their attendance.

[ ] Multi-Camera Support: Enhance the system to monitor multiple video streams simultaneously.

🤝 Contributing
Contributions are welcome! If you have ideas for improvements or want to add new features, please feel free to fork the repository and submit a pull request.

📄 License
This project is distributed under the MIT License. See the LICENSE file for more information.

<details>
<summary><h2><a name="-arabic-version"></a>النسخة العربية (Arabic Version)</h2></summary>

<div dir="rtl" align="center">

نظام رقيب: نظام الحضور والأمان المدعوم بالذكاء الاصطناعي
<p>
نظام ذكي ومتقدم للتعرف على الوجوه في الوقت الفعلي، تم تطويره باستخدام Python لأتمتة حضور الموظفين وتعزيز الأمان، مع ميزة التحقق من الحيوية، لوحة تحكم مفصلة، وواجهة ثنائية اللغة.
</p>

</div>

✨ المميزات الرئيسية
📸 التعرف على الوجوه في الوقت الفعلي: تسجيل حضور الموظفين تلقائيًا عند التعرف على وجوههم من بث الفيديو المباشر.

👁️ التحقق من الحيوية: يمنع هجمات التحايل (مثل استخدام صورة أو فيديو) عن طريق مطالبة المستخدمين بالرمش، مما يضمن أن الشخص حقيقي وموجود بالفعل.

🌍 واجهة ثنائية اللغة: التبديل بسلاسة بين اللغتين الإنجليزية و العربية بنقرة واحدة لتلبية احتياجات المستخدمين المختلفين.

🔑 وصول آمن للمسؤول: حماية بكلمة مرور للأقسام الحساسة مثل الإعدادات و إدارة الموظفين لمنع الوصول غير المصرح به.

👥 إدارة شاملة للموظفين: لوحة مخصصة لإضافة موظفين جدد، التقاط صورهم، تعديل تفاصيلهم (البريد الإلكتروني)، وحذف ملفاتهم بشكل آمن.

📊 لوحة معلومات متقدمة: عرض بيانات الحضور مع تقارير شهرية ورسوم بيانية أسبوعية. يمكن تصدير جميع التقارير إلى ملفات CSV لمزيد من التحليل أو حفظ السجلات.

📧 تنبيهات أمنية عبر البريد الإلكتروني: إرسال إشعار تلقائي عبر البريد الإلكتروني—مع لقطة للشخص غير المعروف—إلى مسؤول النظام.

👤 ملفات تعريف مفصلة للموظفين: انقر نقرًا مزدوجًا على أي موظف لعرض ملفه الشخصي، بما في ذلك صورته وسجل الحضور الكامل والمؤرخ.

💾 نسخ احتياطي لقاعدة البيانات: أداة بنقرة واحدة لإنشاء نسخة احتياطية آمنة ومؤرخة لقاعدة بيانات النظام بأكملها.

💻 التقنيات المستخدمة
الفئة

التقنية

لغة البرمجة الأساسية

🐍 Python 3.8+

واجهة المستخدم

🖼️ Tkinter (مع ttkbootstrap لتصميم عصري)

الذكاء الاصطناعي والرؤية الحاسوبية

🧠 DeepFace, dlib, OpenCV

البيانات والتقارير

🗃️ SQLite, Pandas, Matplotlib

معالجة الصور

🎨 Pillow (PIL)

🛠️ التثبيت والإعداد
اتبع هذه الخطوات لتشغيل المشروع على جهازك.

المتطلبات الأساسية:
Python 3.8 أو أحدث.

كاميرا ويب متصلة بجهازك.

الخطوة 1: استنساخ المشروع وإعداد بيئة افتراضية
# استنساخ المستودع (استبدل [YOUR-REPO-NAME] باسم المستودع الخاص بك)
git clone [https://github.com/Abdou-AI02/](https://github.com/Abdou-AI02/)[YOUR-REPO-NAME].git
cd [YOUR-REPO-NAME]

# إنشاء وتفعيل بيئة افتراضية
python -m venv venv
# على نظام Windows
venv\Scripts\activate
# على نظام macOS/Linux
source venv/bin/activate

الخطوة 2: تثبيت المكتبات المطلوبة
pip install -r requirements.txt

الخطوة 3: تحميل نموذج dlib
يتطلب اكتشاف معالم الوجه نموذجًا مدربًا مسبقًا.

قم بتنزيل النموذج من http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2.

استخرج ملف shape_predictor_68_face_landmarks.dat وضعه في المجلد الرئيسي للمشروع.

🚀 كيفية التشغيل
بعد إتمام الإعدادات، قم بتشغيل التطبيق بالأمر التالي:

python Raqeeb.py

كلمة المرور الافتراضية: كلمة مرور المسؤول الافتراضية هي admin. يوصى بشدة بتغييرها فورًا من نافذة الإعدادات لأغراض أمنية.

</details>