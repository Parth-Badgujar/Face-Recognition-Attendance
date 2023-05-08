import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import time
import torch
import hashlib
import mysql.connector
import numpy as np
import cv2
from hdpitkinter import HdpiTk
import tkinter as tk
from scipy.spatial import distance
from PIL import Image
from PIL import ImageTk
import pickle
import sys


sf = 2

class Model():
    def __init__(self, p):
        self.p = p
        self.extra = []
        self.face_features_list = pickle.load(open(r'Data/face_features.bin', 'rb'))
        self.enrollment_lis = pickle.load(open(r'Data/enrollment.bin', 'rb'))
        self.haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') 
        self.CNN = torch.load('Data/VGG16_pretrained_torch.pth')
    def predict(self, img):
        with torch.no_grad():
            res = self.CNN(torch.from_numpy(img).float().unsqueeze(0).permute(0, 3, 1, 2)).reshape(-1).numpy()
        return res
    def destroy_stuff(self):
        self.p.recog_label.destroy()
        self.p.name_label.destroy()
        self.p.enrollment_label.destroy()
    def recognise(self):
        course = self.p.course_code_txt
        date = self.p.date_txt
        self.labels_created = True
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        a = 0
        end_time = time.time() + 5
        while time.time() < end_time:
            (ret, frame) = camera.read()
            faces = self.haar_cascade.detectMultiScale(frame, 1.3, 5, minSize = (90, 90))
            if len(faces) != 0:
                (x, y, w, h) = faces[0]
                face_cropped = frame[y:y+h, x:x+w]
                face_cropped = cv2.resize(face_cropped, (224, 224))
                face_cropped = face_cropped / 225
                prediction = self.predict(face_cropped)
                for i in range(len(self.face_features_list)):
                    cosine = distance.cosine(self.face_features_list[i], prediction)
                    if cosine < 0.38 :
                        a = 1
                        enrollment = self.enrollment_lis[i]
                        print(enrollment)
                        camera.release()
                        name = self.p.get(f"SELECT NAME FROM STUDENTS WHERE ENROLLMENT_NO = '{enrollment}'")[0][0]
                        print(name)
                        self.p.attendance_recorded = np.array(Image.open(r"Images/Attendance Recorded.png"))
                        self.p.attendance_recorded = ImageTk.PhotoImage(Image.fromarray(self.p.attendance_recorded))
                        self.p.recog_label = tk.Label(self.p.root, image = self.p.attendance_recorded, relief = 'flat', bg = 'white')
                        self.p.recog_label.place(x = 848, y = 94)
                        self.p.name_label = tk.Label(self.p.root, text = name, **self.p.text_format)
                        print(name)
                        self.p.enrollment_label = tk.Label(self.p.root, text = enrollment, **self.p.text_format)
                        self.p.enrollment_label.place(x = 874, y = 534)
                        self.p.name_label.place(x = 874, y = 351)
                        self.p.root.update_idletasks()
                        self.p.execute(f"UPDATE STUDENTS SET {course + '_' + date} = 'P' WHERE ENROLLMENT_NO = '{enrollment}'")
                        self.p.root.after(3000, lambda : [self.destroy_stuff()])
                        break
                k = cv2.waitKey(30) & 0xFF
                if k == 27: 
                    camera.release() 
                    cv2.destroyAllWindows() 
                    break
            if a == 1:
                break 
        if a == 0:
            self.p.not_recognised = np.array(Image.open(r"Images/Unable_to_recognise.png"))
            self.p.not_recognised = ImageTk.PhotoImage(Image.fromarray(self.p.not_recognised))
            self.p.not_recog_label = tk.Label(self.p.root, image = self.p.not_recognised, relief = 'flat', bg = 'white')
            self.p.root.update_idletasks()
            self.p.root.after(2000, lambda : [self.p.not_recog_label.destroy()])
            self.p.not_recog_label.place(x = 848, y = 94)
        cv2.destroyAllWindows()
    
    def add(self, name, enrollment_no, department):
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        j=0
        time_end = time.time() + 3
        while True :
            (ret,frame) = camera.read() 
            faces = self.haar_cascade.detectMultiScale(frame, 1.3, 5, minSize = (90, 90))
            cv2.imshow("Face Input", frame)
            if len(faces) != 0 and time.time() > time_end:   
                (x,y,w,h) = faces[0]
                face = frame[y : y + h, x : x + w] / 255 
                face = cv2.resize(face, (224, 224)) 
                self.face_features_list.append(self.predict(face))
                self.enrollment_lis.append(enrollment_no)
                pickle.dump(self.face_features_list, open(r'Data/face_features.bin', 'wb'))
                pickle.dump(self.enrollment_lis, open(r'Data/enrollment.bin', 'wb'))
                self.p.execute(f"INSERT INTO STUDENTS (NAME, ENROLLMENT_NO, DEPARTMENT) VALUES ('{name}', '{enrollment_no}', '{department}')")
                j += 1
            if j == 1:
                break
            k = cv2.waitKey(30) & 0xFF
            if k == 27: 
                camera.release() 
                cv2.destroyAllWindows()
                break
        camera.release()
        cv2.destroyAllWindows()
        if j == 0 :
            self.try_again = np.array(Image.open(r"Images/Try_Again.png"))
            self.try_again = ImageTk.PhotoImage(Image.fromarray(self.try_again))
            error = tk.Label(self.p.root, image = self.try_again, **self.p.text_format)
            error.place(x = 943, y = 836)
            self.p.root.update_idletasks()
            self.p.root.after(2000, lambda : [error.destroy()])
            self.p._continue = np.array(Image.open(r"Images/Continue.png"))
            self.p._continue = ImageTk.PhotoImage(Image.fromarray(self.p._continue))
            self.p._continue_btn = tk.Button(self.p.root, image = self.p._continue, relief = 'flat', bg = 'white', command = lambda : [self.add(self.p.name_txt.get(), self.p.enrollment_txt.get(), self.p.department_txt.get()), self.p._continue_btn.destroy()])
            self.p._continue_btn.place(x = int(984), y = int(836))
        else :
            self.p.background_label.destroy()
            self.p.get_name.destroy()
            self.p.get_enrollment.destroy()
            self.p.get_department.destroy()
            self.p.second_page()

class Project():
    def __init__(self):
        self.m = Model(self)
        self.database_password
        try :
            self.mycon = mysql.connector.connect(host = 'localhost', user = 'root', database = sys.argv[1], password = sys.argv[2])
            if self.mycon:
                print('Connected to Database')
        except Exception as e:
            print('Error connecting to database : ', e)
            exit()
        self.date_format = dict(font = ('Calibri', 33), fg = 'black', bg = 'white')
        self.text_format = dict(font = ('Calibri', 30), fg = 'black', bg = 'white')
        self.password_format = dict(fg = 'black', bg = 'white', font = ('Calibri', 28), relief = 'flat')
        self.root = HdpiTk()
        self.root.geometry(f'{int(800 * sf)}x{int(500 * sf)}')
        self.root.resizable(False, False)
        self.root.title('Student Attendance')
        self.root.bind('<Button-1>', self.keep_flat)
        self.first_page()
        self.root.mainloop()
    def keep_flat(self, event):
        event.widget.config(relief = 'flat', bg = 'white') 
    def first_page(self):
        self.background_img = np.array(Image.open(r"Images/Login_Page_ Background.png"))
        self.background_img = ImageTk.PhotoImage(Image.fromarray(self.background_img))
        self.background_label = tk.Label(self.root, image = self.background_img)
        self.background_label.place(x = 0, y = 0, relheight = 1, relwidth = 1)
        
        self.email_txt = tk.StringVar()
        self.email = tk.Entry(self.root, width = 24, textvariable = self.email_txt, **self.text_format, relief = 'flat')
        self.email.place(x = 993 + 20, y = 450)

        self.password_txt = tk.StringVar()
        self.password = tk.Entry(self.root, width = 27, show = '*', textvariable = self.password_txt, **self.password_format)
        self.password.place(x = 993 + 20, y = 560)

        self.login = np.array(Image.open(r"Images/Login Button.png"))
        self.login = ImageTk.PhotoImage(Image.fromarray(self.login))
        self.login_btn = tk.Button(self.root, image = self.login, relief = 'flat', bg = 'white', command = self.check_password)
        self.login_btn.place(x = 1026, y = 674)

        self.exit = np.array(Image.open(r"Images/Exit Button.png"))
        self.exit = ImageTk.PhotoImage(Image.fromarray(self.exit))
        self.exit_btn = tk.Button(self.root, image = self.exit, relief = 'flat', bg = 'white', command = exit)
        self.exit_btn.place(x = 1320, y = 674)
        self.root.bind('<Return>', lambda x : self.check_password())
    def check_password(self):
        self.email_text = self.email_txt.get()
        salt = self.get(f"SELECT SALT FROM ACCOUNTS WHERE EMAIL_ID = '{self.email_text}'")
        if len(salt) != 0 :
            self.hash = self.get(f"SELECT HASH FROM ACCOUNTS WHERE EMAIL_ID = '{self.email_text}'")[0][0]
            self.salt = salt[0][0]
            self.password_hash = hashlib.sha256((self.password_txt.get() + self.salt).encode()).hexdigest()
            if self.password_hash == self.hash :
                self.destroy_first_page()
                self.root.unbind('<Return>')
            else :
                self.password.delete(0, tk.END)
        else :
            self.email.delete(0, tk.END)
            self.password.delete(0, tk.END)
    def destroy_first_page(self):
        self.background_label.destroy()
        self.email.destroy()
        self.login_btn.destroy()
        self.exit_btn.destroy()
        self.password.destroy()
        self.second_page()
    def get(self, command):
        cursor = self.mycon.cursor()
        cursor.execute(command)
        x = cursor.fetchall()
        cursor.close()
        return x
    def execute(self, command):
        cursor = self.mycon.cursor()
        cursor.execute(command)
        cursor.execute('commit')
        cursor.close()
    def second_page(self):
        self.root.bind('<Escape>', lambda x: [self.destroy_second_page(), self.first_page()])
        self.background_img = np.array(Image.open(r"Images/Second Page.png"))
        self.background_img = ImageTk.PhotoImage(Image.fromarray(self.background_img))
        self.background_label = tk.Label(self.root, image = self.background_img)
        self.background_label.place(x = 0, y = 0, relheight = 1, relwidth = 1)

        self.attendance = np.array(Image.open(r"Images/New Attendance Button.png"))
        self.attendance = ImageTk.PhotoImage(Image.fromarray(self.attendance))
        self.attendance_btn = tk.Button(self.root, image = self.attendance, relief = 'flat', bg = 'white', command = lambda : [self.destroy_second_page(), self.new_attendance()])
        self.attendance_btn.place(x = int(864 * 1.0), y = int(385 * 1.0))

        self.name = self.get(f"SELECT NAME FROM ACCOUNTS WHERE EMAIL_ID = '{self.email_text}'")[0][0]
        self.department = self.get(f"SELECT DEPARTMENT FROM ACCOUNTS WHERE EMAIL_ID = '{self.email_text}'")[0][0]

        self.name_label = tk.Label(self.root, text = self.name, **self.text_format)
        self.name_label.place(x = int(102 * 1.0), y = int(520 * 1.0))
        self.department_label = tk.Label(self.root, text = self.department, **self.text_format)
        self.department_label.place(x = int(100 * 1.0), y = int(660* 1.0))

        self.change_passwod = np.array(Image.open(r"Images/Change Password.png"))
        self.change_passwod = ImageTk.PhotoImage(Image.fromarray(self.change_passwod))
        self.change_passwod_btn = tk.Button(self.root, image = self.change_passwod, bg = 'white', relief = 'flat', command = lambda : [self.destroy_second_page(), self.change_password()])
        self.change_passwod_btn.place(x = int(864), y = int((520)))

        self.add_student = np.array(Image.open(r"Images/Add Students.png"))
        self.add_student = ImageTk.PhotoImage(Image.fromarray(self.add_student))
        self.add_student_btn = tk.Button(self.root, image = self.add_student, relief = 'flat', bg = 'white', command = lambda : [self.destroy_second_page(), self.add_students()] )
        self.add_student_btn.place(x = int(864), y = int((655)))

    def destroy_second_page(self, event = None):
        self.name_label.destroy()
        self.department_label.destroy()
        self.change_passwod_btn.destroy()
        self.background_label.destroy()
        self.attendance_btn.destroy()
        self.add_student_btn.destroy()

    def add_students(self):
        self.root.bind('<Escape>', lambda x : [self.second_page(), self.add_students_destroy()])
        self.background_img = np.array(Image.open(r"Images/Adding Page.png"))
        self.background_img = ImageTk.PhotoImage(Image.fromarray(self.background_img))
        self.background_label = tk.Label(self.root, image = self.background_img)
        self.background_label.place(x = 0, y = 0, relheight = 1, relwidth = 1)
        
        self.name_txt = tk.StringVar()
        self.get_name = tk.Entry(self.root, width = 27, relief = 'flat',font = ('Calibri', 26), fg = 'black', bg = 'white', textvariable = self.name_txt)
        self.get_name.place(x = 882, y = 296)

        self.enrollment_txt = tk.StringVar()
        self.get_enrollment = tk.Entry(self.root, width = 27, relief = 'flat',font = ('Calibri', 26), fg = 'black', bg = 'white', textvariable = self.enrollment_txt)
        self.get_enrollment.place(x = 882, y = 465)

        self.department_txt = tk.StringVar()
        self.get_department = tk.Entry(self.root, width = 27, relief = 'flat',font = ('Calibri', 26), fg = 'black', bg = 'white', textvariable = self.department_txt)
        self.get_department.place(x = 882, y = 635)

        self._continue = np.array(Image.open(r"Images/Continue.png"))
        self._continue = ImageTk.PhotoImage(Image.fromarray(self._continue))
        self._continue_btn = tk.Button(self.root, image = self._continue, relief = 'flat', bg = 'white', command = lambda : [self.m.add(self.name_txt.get(), self.enrollment_txt.get(), self.department_txt.get()), self._continue_btn.destroy()])
        self._continue_btn.place(x = int(984), y = int(836))
        self.root.bind('<Escape>', lambda x : [self.add_students_destroy(), self.second_page()])

    def add_students_destroy(self):
        self._continue_btn.destroy()
        self.get_department.destroy()
        self.get_name.destroy()
        self.get_enrollment.destroy()
        self.background_label.destroy()

    def change_password(self):
        self.background_img = np.array(Image.open(r"Images/Password_Change_Page.png"))
        self.background_img = ImageTk.PhotoImage(Image.fromarray(self.background_img))
        self.background_label = tk.Label(self.root, image = self.background_img)
        self.background_label.place(x = 0, y = 0, relheight = 1, relwidth = 1)

        self.change_passwod_submit = np.array(Image.open(r"Images/Password_Submit.png"))
        self.change_passwod_submit = ImageTk.PhotoImage(Image.fromarray(self.change_passwod_submit))
        self.change_passwod_submit_btn = tk.Button(self.root, image = self.change_passwod_submit, relief = 'flat', bg = 'white', command = self.check_changed_password)
        self.change_passwod_submit_btn.place(x = int(984), y = int(836))
    
        self.old_password_txt = tk.StringVar()
        self.old_password = tk.Entry(self.root, width = 24, show = '*', textvariable = self.old_password_txt, **self.password_format)
        self.old_password.place(x = int(798), y = int(191))

        self.new_password_txt = tk.StringVar()
        self.new_password = tk.Entry(self.root, width = 24, show = '*', textvariable = self.new_password_txt, **self.password_format)
        self.new_password.place(x = int(798), y = int(430))

        self.new_password_again_txt = tk.StringVar()
        self.new_password_again = tk.Entry(self.root, width = 24, show = '*', textvariable = self.new_password_again_txt, **self.password_format)
        self.new_password_again.place(x = int(798), y = int(685))

        self.root.bind('<Escape>', lambda x : [self.change_password_destroy(), self.second_page()])
    def check_changed_password(self):
        curr_hash = hashlib.sha256((self.old_password_txt.get() + self.salt).encode()).hexdigest()
        if curr_hash == self.hash :
            if self.new_password_txt.get() == self.new_password_again_txt.get() :
                new_hash = hashlib.sha256((self.new_password_txt.get() + self.salt).encode()).hexdigest()
                self.execute(f"UPDATE ACCOUNTS SET HASH = '{new_hash}' where EMAIL_ID = '{self.email_text}'")
                self.hash = new_hash
                self.change_password_destroy()
                self.second_page()
            else :
                self.new_password.delete(0, tk.END)
                self.new_password_again.delete(0, tk.END)
        else :
            self.old_password.delete(0, tk.END)
            self.new_password.delete(0, tk.END)
            self.new_password_again.delete(0, tk.END)
    
    def change_password_destroy(self):
        self.old_password.destroy()
        self.new_password.destroy()
        self.new_password_again.destroy()
        self.background_label.destroy()
        self.change_passwod_submit_btn.destroy()

    def new_attendance(self):
        self.root.bind('<Escape>', lambda x: [self.new_attendance_destroy(), self.second_page()])
        self.background_img = np.array(Image.open(r"Images/New Attendance.png"))
        self.background_img = ImageTk.PhotoImage(Image.fromarray(self.background_img))
        self.background_label = tk.Label(self.root, image = self.background_img)
        self.background_label.place(x = 0, y = 0, relheight = 1, relwidth = 1)

        self.course_code = tk.StringVar()
        self.date = tk.StringVar()

        self.course_code_entry = tk.Entry(self.root, width = 9, justify = 'center', textvariable = self.course_code, **self.text_format, relief = 'flat')
        self.course_code_entry.place(x = 1305, y = 167)

        self.date_entry = tk.Entry(self.root, width = 15, justify = 'center', textvariable = self.date, **self.text_format, relief = 'flat')
        self.date_entry.place(x = 1190, y = 367)

        self.start_recognising = np.array(Image.open(r"Images/Start.png"))
        self.start_recognising = ImageTk.PhotoImage(Image.fromarray(self.start_recognising))
        self.start_recognising_btn = tk.Button(self.root, image = self.start_recognising, relief = 'flat', bg = 'white', command = self.start_recognition)
        self.start_recognising_btn.place(x = int(1072 * 1.0), y = int(670 * 1.0))

    def start_recognition(self):
        self.date_txt = self.date.get().replace('-', '_')
        self.course_code_txt = self.course_code.get().replace('-', '_')
        self.execute(f'ALTER TABLE STUDENTS ADD COLUMN {self.course_code_txt}_{self.date_txt} varchar(255)')
        self.date_entry.destroy()
        self.course_code_entry.destroy()
        self.background_label.destroy()
        self.recognise_layout()
    def recognise_layout(self):
        self.root.bind('<Escape>', lambda x : [self.new_attendance(), self.recognise_destroy()])
        self.background_img = np.array(Image.open(r"Images/Recognition.png"))
        self.background_img = ImageTk.PhotoImage(Image.fromarray(self.background_img))
        self.background_label = tk.Label(self.root, image = self.background_img)
        self.background_label.place(x = 0, y = 0, relheight = 1, relwidth = 1)
        
        self.back = np.array(Image.open(r"Images/Back.png"))
        self.back = ImageTk.PhotoImage(Image.fromarray(self.back))
        self.back_btn = tk.Button(self.root, image = self.back, relief = 'flat', bg = 'white', command = self.new_attendance)
        self.back_btn.place(x = 1226, y = 797)
        self.recognise = np.array(Image.open(r"Images/Recognise.png"))
        self.recognise = ImageTk.PhotoImage(Image.fromarray(self.recognise))
        self.recognise_btn = tk.Button(self.root, image = self.recognise ,relief = 'flat', bg = 'white', command = self.m.recognise)
        self.recognise_btn.place(x = 864, y = 797)
    def recognise_destroy(self):
        self.background_label.destroy()

    def new_attendance_destroy(self):
        self.background_label.destroy()
        self.course_code_entry.destroy()
        self.date_entry.destroy()
        self.start_recognising_btn.destroy()
p = Project()
