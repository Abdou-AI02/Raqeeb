<div align="center">

<br/>
<img src="https://www.google.com/search?q=https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Face%2520with%2520Monocle.png" alt="Raqeeb Logo" width="120" height="120"/>
<br/>

Raqeeb: AI Attendance & Security System
نظام رقيب: نظام الحضور والأمان المدعوم بالذكاء الاصطناعي
<p>
An advanced, real-time facial recognition system built with Python to automate employee attendance and enhance security, featuring liveness detection, a detailed management dashboard, and a bilingual interface.
</p>

<p>
<a href="#-table-of-contents"><strong>Table of Contents</strong></a> •
<a href="https://www.google.com/search?q=https://github.com/Abdou-AI02/[YOUR-REPO-NAME]/issues">Report Bug</a> •
<a href="https://www.google.com/search?q=https://github.com/Abdou-AI02/[YOUR-REPO-NAME]/issues">Request Feature</a>
</p>

</div>

📋 <a name="-table-of-contents"></a>Table of Contents
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

🎯 <a name="-project-overview"></a>Project Overview
Traditional attendance systems like fingerprint scanners or ID cards can be inefficient, pose hygiene risks (especially post-pandemic), and are often costly to maintain. Furthermore, they are susceptible to fraudulent activities like "buddy punching," where one employee clocks in for another, leading to inaccurate payroll and productivity tracking.

Raqeeb addresses these challenges by providing a touchless, highly secure, and fully automated solution. It leverages the power of modern artificial intelligence to ensure that attendance is marked accurately and effortlessly. The system not only streamlines the attendance process but also bolsters on-site security by actively identifying and flagging unauthorized individuals. It is an ideal solution for small to medium-sized businesses, educational institutions, and any organization looking to modernize its operational management.

✨ <a name="-core-features"></a>Core Features
<table width="100%">
<tr>
<td width="50%" valign="top">
<h3>Security & Accuracy</h3>
<ul>
<li><strong>👁️ Liveness Detection:</strong> An essential security layer that prevents spoofing attacks. By analyzing eye blinks, the system ensures it's interacting with a real, live person, not a static photo or a video playback on a screen.</li>
<li><strong>📸 Real-Time Face Recognition:</strong> Utilizes the state-of-the-art ArcFace model via the DeepFace library for high-accuracy recognition, minimizing false positives and ensuring employees are correctly identified every time.</li>
<li><strong>📧 Email Security Alerts:</strong> Instantly notifies the designated administrator via email the moment an unrecognized face is detected. The email includes a timestamp and a snapshot of the individual for immediate review and action.</li>
</ul>
</td>
<td width="50%" valign="top">
<h3>Management & Usability</h3>
<ul>
<li><strong>👥 Comprehensive Employee Management:</strong> A secure, password-protected admin panel provides full control over employee data (CRUD operations). Admins can add new employees, capture their photos, update details, and securely delete profiles.</li>
<li><strong>📊 Advanced Dashboard:</strong> Offers valuable insights into attendance patterns. Admins can visualize data through monthly summary reports and weekly attendance charts, and export all data to CSV for integration with payroll or HR systems.</li>
<li><strong>🌍 Bilingual Interface:</strong> With a single click, the entire user interface toggles between <strong>English</strong> and <strong>Arabic</strong>, making the system accessible and user-friendly for a diverse range of users.</li>
</ul>
</td>
</tr>
</table>

<details>
<summary><h3>⚙️ <a name="️-how-it-works-the-technical-pipeline"></a>How It Works: The Technical Pipeline</h3></summary>

The system follows a sophisticated, multi-stage pipeline to ensure accurate, secure, and real-time recognition:

Camera Activation & Frame Grabbing: The system initializes the default webcam using OpenCV. It continuously captures video frames at a standard rate, preparing them for analysis.

Face Detection: Each captured frame is converted to grayscale and processed to detect faces. The dlib library's highly efficient frontal face detector is used to identify the coordinates of any human faces present in the frame.

Liveness Check (Anti-Spoofing): This is a critical security step to prevent fraud.

Once a face is detected, the system employs dlib's shape predictor model to map 68 specific facial landmarks (the corners of the eyes, nose, mouth, etc.).

It then calculates the Eye Aspect Ratio (EAR) for both eyes. The EAR is a mathematical ratio derived from the distances between these landmarks. The value is relatively constant when an eye is open and drops sharply towards zero when an eye closes.

The system monitors this EAR value. If it drops below a configurable threshold for a set number of consecutive frames, it registers a "blink." This successful blink verifies the person as "live" and not a static image.

Face Recognition:

After a successful liveness check, the detected face region is cropped from the original color frame and passed to the DeepFace library.

DeepFace computes a "facial embedding"—a unique numerical vector (like a digital fingerprint) that represents the distinct features of the face.

This embedding is then compared against a pre-computed database of embeddings for all registered employees. The comparison uses a mathematical metric called Cosine Distance, which measures the similarity between the two vectors. If the calculated distance is below a pre-defined confidence threshold, the face is considered a positive match.

Database Interaction & Action:

If Recognized: The system queries the SQLite database to check if the identified employee has already been marked present for the current day. If not, it inserts a new record into the attendance table with the employee's name and the current timestamp.

If Unknown: If the face does not match any known employee with sufficient confidence, the system saves a snapshot of the person to the unknown_visitors directory and triggers an email alert to the administrator.

Real-Time UI Update: The application's main interface, built with ttkbootstrap, is updated instantly to reflect the new attendance log and display relevant system status messages (e.g., "Liveness Verified", "Recognized: [Name]").

</details>

<details>
<summary><h3>💻 <a name="-tech-stack"></a>Tech Stack</h3></summary>

Category

Technology

Why This Stack?

Core Language

🐍 Python 3.8+

Chosen for its extensive AI/ML libraries, readability, and rapid development capabilities.

User Interface

🖼️ Tkinter (with ttkbootstrap)

ttkbootstrap provides a collection of modern, professional themes on top of Python's standard Tkinter library, enabling a great-looking UI with minimal effort.

AI & Computer Vision

🧠 DeepFace, dlib, OpenCV

A powerful combination: OpenCV for camera interaction, dlib for high-speed face detection and landmark prediction, and DeepFace for state-of-the-art face recognition.

Data & Reporting

🗃️ SQLite, Pandas, Matplotlib

SQLite is a lightweight, serverless database perfect for standalone desktop apps. Pandas and Matplotlib are the industry standard for data manipulation and visualization in Python.

Image Handling

🎨 Pillow (PIL)

The essential library for opening, manipulating, and saving image files, and for integrating images into the Tkinter UI.

</details>

<details>
<summary><h3>📁 <a name="-project-structure"></a>Project Structure</h3></summary>

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

</details>

🛠️ <a name="-installation--setup"></a>Installation & Setup
Follow these steps to get the project up and running on your local machine.

Prerequisites:
Python 3.8 or newer. You can download it from python.org.

A webcam connected to your system.

Step 1: Clone & Set Up a Virtual Environment
A virtual environment is highly recommended to avoid conflicts with other Python projects.

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
This command reads the requirements.txt file and installs all the necessary libraries. This may take a few minutes, as some libraries like tensorflow are large.

pip install -r requirements.txt

Step 3: Download the dlib Shape Predictor Model
This pre-trained model is essential for the liveness detection feature.

Download the model from http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2.

Extract the shape_predictor_68_face_landmarks.dat file from the downloaded archive and place it in the root directory of the project.

🚀 <a name="-how-to-run"></a>How to Run
Once everything is set up, run the application with the following command from your terminal:

python Raqeeb.py

Upon successful launch, the main application window will appear, and the camera feed should activate.

Default Password: The default admin password is admin. It is highly recommended to change it immediately from the Settings window for security purposes.

<details>
<summary><h3>📖 <a name="-usage-guide"></a>Usage Guide</h3></summary>

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

</details>

<details>
<summary><h3>🔧 <a name="-configuration-options"></a>Configuration Options</h3></summary>

You can customize the system's behavior from the Settings window:

Admin Password: Change the password required to access sensitive areas. A new password must be entered to update it.

Email Settings: Configure the sender/receiver emails, app password (use an app-specific password for services like Gmail), and SMTP server details for security alerts.

Technical Parameters:

Camera Index: Change the default camera (e.g., from 0 to 1 if you have multiple cameras).

Confidence Threshold: Lower this value (e.g., to 0.3) to make recognition stricter, or raise it (e.g., to 0.5) to be more lenient. The default is 0.4.

EAR Threshold: Adjust the Eye Aspect Ratio threshold for liveness detection based on your camera and lighting conditions. A lower value requires a more pronounced blink.

Theme: Change the visual theme of the application from a dropdown list of available ttkbootstrap themes.

</details>

💡 <a name="-future-work"></a>Future Work
This project has a solid foundation, but there are many potential areas for expansion:

[ ] Web-Based Interface: Develop a web dashboard using a framework like Flask or Django for remote management and viewing reports from any device.

[ ] Dockerization: Containerize the application with Docker for easier, cross-platform deployment and scalability.

[ ] Advanced Analytics: Add more detailed reports, such as tracking late arrivals, calculating work hours, or generating payroll summaries.

[ ] Mobile Application: A companion mobile app for employees to view their own attendance history and receive notifications.

[ ] Multi-Camera Support: Enhance the system to monitor multiple video streams simultaneously from different entry points.

[ ] Integration with HR Systems: Add functionality to export data in formats compatible with popular HR and payroll software.

🤝 <a name="-contributing"></a>Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 <a name="-license"></a>License
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
