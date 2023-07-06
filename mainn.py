
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from json.tool import main

import scipy.sparse
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QWidget, QMessageBox, QFileSystemModel, QTreeView, QVBoxLayout, QProgressBar, QLabel, QFrame, QSplashScreen
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QFont
import sqlite3
import time
from datetime import datetime, date
import cv2
import xlsxwriter

from validator.validate import *
from src.align_dataset_mtcnn import *
from src.classifier import *
import keyring
import base64
import os
import sys
from src import align
import tensorflow as tf
from imutils.video import VideoStream
import argparse
import facenet
import imutils
import os
import sys
import math
import pickle
import src.align.detect_face
import numpy as np
import cv2
import collections
from src import facenet
from sklearn.svm import SVC
from validator.validate import *
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QWidget, QMessageBox, QFileSystemModel, QTreeView, QVBoxLayout, QProgressBar, QLabel, QFrame, QSplashScreen
import pandas as pd
from openpyxl import load_workbook
from tkinter import filedialog as fd
import bcrypt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        loadUi("./qt designer/welcomescreen.ui",self)
        self.login.clicked.connect(self.gotologin)
        self.create.clicked.connect(self.gotocreate)

    def gotologin(self):
        login = LoginScreen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex()+1)

    def gotocreate(self):
        create = CreateAccScreen()
        widget.addWidget(create)
        widget.setCurrentIndex(widget.currentIndex() + 1)
     
class ForgotPassword(QDialog):
    def __init__(self, username):
        super(ForgotPassword, self).__init__()
        loadUi("./qt designer/forgotpassword.ui",self)
        self.btnReset.clicked.connect(self.reset)
        self.tfPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.username = username
    def reset(self):
        # get question and answer of user
        CbQuestion = self.cbQuestion.currentText()
        tfAnswer = self.tfAnswer.text()
        password = self.tfPassword.text()
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT question,answer from account where username = ?", (self.username,))
        
            sqliteConnection.commit()
            record = cursor.fetchone()
            question = record[0]
            answer = record[1]
            cursor.close()         
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # insert new password
        if CbQuestion == question:
            if tfAnswer == answer:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")
                    encrypt = base64.b85encode(password.encode("utf-8"))
                    cursor.execute("UPDATE account set password = ? where username = ?", (encrypt, self.username))
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Password reset successfully")
                except sqlite3.Error as error:
                   print("Failed to get data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
            else:
                self.showdialog("Answer is incorrect")
        else:
            self.showdialog("Incorrect question")    
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
       
class LoginScreen(QDialog):
    def __init__(self):
        super(LoginScreen, self).__init__()
        loadUi("./qt designer/login.ui",self)
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)
        self.lbForgot.mousePressEvent = self.forgotpassword
        self.MAGIC_USERNAME_KEY = 'im_the_magic_username_key'
        self.service_id = 'IM_YOUR_APP!'
        self.keyring = keyring.get_keyring()
    def loginfunction(self):
        user = self.usernamefield.text()
        password = self.passwordfield.text()
        if len(user)==0 or len(password)==0:
            self.error.setText("Please input all fields.")
        else:
            try:
                conn = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cur = conn.cursor()
                query = 'SELECT password FROM account WHERE username =\''+user+"\'"
                cur.execute(query)
                result_pass =cur.fetchone()[0]
                decrypt = base64.b85decode(result_pass).decode("utf-8")
                conn.close()
                if decrypt == password:
                    print("Successfully logged in.")
                    self.error.setText("")
                    self.keyring.set_password(self.service_id, self.MAGIC_USERNAME_KEY, user)

                    main = Main()
                    widget.addWidget(main)
                    widget.setCurrentIndex(widget.currentIndex()+1)

                else:
                    self.error.setText("Invalid username or password")
            except sqlite3.Error as error:
                print("Failed to get data into sqlite table", error)
            finally:
                if conn:
                    conn.close()
                print("The SQLite connection is closed")
    def forgotpassword(self, event):
        username = self.usernamefield.text()
        # get all username
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT username FROM account")
        
            sqliteConnection.commit()
            records = cursor.fetchall()
            cursor.close()
            if (username,) in records:
                self.error.setText("")
                forgot = ForgotPassword(username)
                widget.addWidget(forgot)
                widget.setCurrentIndex(widget.currentIndex()+1)
            else:
                self.error.setText("Invalid username")
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

class CreateAccScreen(QDialog):
    def __init__(self):
        super(CreateAccScreen, self).__init__()
        loadUi("./qt designer/createacc.ui",self)
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpasswordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.signup.clicked.connect(self.signupfunction)

    def signupfunction(self):
        user = self.usernamefield.text()
        password = self.passwordfield.text()
        confirmpassword = self.confirmpasswordfield.text()

        if len(user)==0 or len(password)==0 or len(confirmpassword)==0:
            self.error.setText("Please fill in all inputs.")

        elif password!=confirmpassword:
            self.error.setText("Passwords do not match.")
        else:
            try:
                conn = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cur = conn.cursor()
                encrypt = base64.b85encode(password.encode("utf-8"))
                user_info = [user, encrypt]
                cur.execute('INSERT INTO account (username, password) VALUES (?,?)', user_info)

                conn.commit()
                conn.close()

                login = LoginScreen()
                widget.addWidget(login)
                widget.setCurrentIndex(widget.currentIndex()+1)
            except sqlite3.Error as error:
                print("Failed to get data into sqlite table", error)
            finally:
                if conn:
                    conn.close()
                print("The SQLite connection is closed")



class Main(QDialog):
    def __init__(self):
        super(Main, self).__init__()
        loadUi("./qt designer/interface.ui", self)
        self.styleSheet()
        self.role = self.getRole()
        self.btnStudent.clicked.connect(self.gotostudent)
        self.btnTeacher.clicked.connect(self.gototeacher)
        self.btnSubject.clicked.connect(self.gotosubject)
        self.btnExit.clicked.connect(self.exit)
        self.btnClass.clicked.connect(self.gotoclass)
        self.btnProfile.clicked.connect(self.gotoprofile)
        self.btnSchedule.clicked.connect(self.gotoschedule)
        self.btnRecognize.clicked.connect(self.gotorecognize)
        self.btnAttendence.clicked.connect(self.gotoattendence)
        self.btnAnalyst.clicked.connect(self.gotoanalyst)
        
        if self.role == "ROLE_USER":
            self.btnStudent.setDisabled(True)
            self.btnTeacher.setDisabled(True)
            self.btnSubject.setDisabled(True)
            self.btnClass.setDisabled(True)
            self.btnSchedule.setDisabled(True)
            self.btnAnalyst.setDisabled(True)

        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start()

    def styleSheet(self):
        leftHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/BestFacialRecognition.jpg')
        self.label.setPixmap(leftHeaderPixmap)
        centerHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/facialrecognition.png')
        self.label_2.setPixmap(centerHeaderPixmap)
        rightHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/images.jpg')
        self.label_3.setPixmap(rightHeaderPixmap)
        bodyCSS = "QFrame#frame_2{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/backgroud.jpg');}"
        self.frame_2.setStyleSheet(bodyCSS)
        recognizeCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/face_detector1.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnRecognize.setStyleSheet(recognizeCSS)
        studentCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/gettyimages-1022573162.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnStudent.setStyleSheet(studentCSS)
        attendanceCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/attendace.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnAttendence.setStyleSheet(attendanceCSS)
        teacherCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/teacher.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnTeacher.setStyleSheet(teacherCSS)
        subjectCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/subject.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnSubject.setStyleSheet(subjectCSS)
        classCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/class.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnClass.setStyleSheet(classCSS)
        scheduleCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/schedule.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnSchedule.setStyleSheet(scheduleCSS)
        analystCSS = "QPushButton {border-image: url('D:/code/.vscode/python/simple_facenet/Resources/analyst.jpg')} QPushButton:hover{border:1px solid red;}"
        self.btnAnalyst.setStyleSheet(analystCSS)
        profileCSS = "QPushButton {border-image: url('D:/code/.vscode/python/simple_facenet/Resources/help-desk-customer-care-team-icon-blue-square-button-isolated-reflected-abstract-illustration-89657179.jpg')} QPushButton:hover{border:1px solid red;}"
        self.btnProfile.setStyleSheet(profileCSS)
        exitCSS = "QPushButton {border-image: url('D:/code/.vscode/python/simple_facenet/Resources/exit.jpg')} QPushButton:hover{border:1px solid red;}"
        self.btnExit.setStyleSheet(exitCSS)
        self.lbDate.setFont(QFont('Arial', 10))

    def showTime(self):
        now = datetime.now()

        dt_string = now.strftime("%d/%m/%Y")
        t_string = now.strftime("%H:%M:%S")
        self.lbDate.setText(dt_string + "\n " + t_string)

    def getRole(self):
        login = LoginScreen()
        username = login.keyring.get_password(login.service_id, login.MAGIC_USERNAME_KEY)
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT role FROM account WHERE username = ?", (username,))

            sqliteConnection.commit()
            role = cursor.fetchone()[0]
            cursor.close()

            return role
        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def exit(self):
        login = LoginScreen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex()+1)
        login.keyring.delete_password(login.service_id, login.MAGIC_USERNAME_KEY)
    def gotostudent(self):
        student = Student()
        widget.addWidget(student)
        widget.setCurrentIndex(widget.currentIndex() + 1)
    def gotoprofile(self):
        profile = Profile()
        widget.addWidget(profile)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoclass(self):
        lopHoc = LopHoc()
        widget.addWidget(lopHoc)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gototeacher(self):
        teacher = Teacher()
        widget.addWidget(teacher)
        widget.setCurrentIndex(widget.currentIndex() + 1)
    def gotosubject(self):
        subject = Subject()
        widget.addWidget(subject)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoschedule(self):
        schedule = Schedule()
        widget.addWidget(schedule)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotorecognize(self):
        recognize = Recognize()
        widget.addWidget(recognize)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoattendence(self):
        attendence = Attendence()
        widget.addWidget(attendence)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoanalyst(self):
        analyst = Analyst()
        widget.addWidget(analyst)
        widget.setCurrentIndex(widget.currentIndex()+1)
class Student(QDialog):
    def __init__(self):
        super(Student, self).__init__()
        loadUi("./qt designer/thongtinsv.ui",self)
        self.loadData()
        self.UiComponents()
        self.btnExit.clicked.connect(self.exit)
        self.btnLoadAll.clicked.connect(self.loadData)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnSave.clicked.connect(self.save)
        self.btnDelete.clicked.connect(self.delete)
        self.btnGetPics.clicked.connect(self.getPics)
        self.btnEdit.clicked.connect(self.edit)
        self.btnTrain.clicked.connect(self.processImage)
        self.btnLoadAll.clicked.connect(self.loadData)
        self.btnSearch.clicked.connect(self.seach)
        self.btnImport.clicked.connect(self.importExcel)
    def importExcel(self):
        filename = fd.askopenfilename()
        # print(filename)
        # if(len(filename) == 0):
        #     ret = QMessageBox.question(self, 'MessageBox', "Chưa chọn file ?",
        #                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
        #     if ret == QMessageBox.Yes:
                
        #     else:
               
        df = pd.read_excel(filename)
        print(df)
        try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")
                for index, row in df.iterrows():
                    cursor.execute("SELECT id FROM COURSE WHERE he = ? and nganh = ?",(row[8], row[9]))
                    course_id = cursor.fetchone()
                    print(course_id[0])
                    cursor.execute(
                    "INSERT INTO students (ten, cmnd, ngaySinh, sdt ,gioiTinh, email, diaChi, nienKhoa, course_id) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (row[0], row[1], row[2].strftime("%Y-%m-%d"), row[3], row[4], row[5], row[6], row[7], course_id[0]))
                sqliteConnection.commit()
                cursor.close()
                self.loadData()
                self.refresh()

        except sqlite3.Error as error:
                print("Failed to select data into sqlite table", error)
        finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def UiComponents(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM students order by id")

            sqliteConnection.commit()
            rows = cursor.fetchall()
            for row in rows:
                self.cbId.addItem(str(row[0]))
            cursor.close()
            self.cbId.activated.connect(self.getInfor)
        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")


    def getInfor(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT * FROM students WHERE id = ?", (self.cbId.currentText(),))

            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenSV.setText(results[1])
            self.tfCMND.setText(results[2])
            self.tfNgaySinh.setText(results[3])
            self.tfSDT.setText(results[4])
            self.cbGioiTinh.setCurrentText(str(results[5]))
            self.tfEmail.setText(results[6])
            self.tfDiaChi.setText(results[7])
            self.tfNienKhoa.setText(results[8])
        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)


    def loadData(self):
        connection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select * from students as s inner join course as c on s.course_id = c.id"

        self.tableWidget.setRowCount(50)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
            self.tableWidget.setItem(tablerow,9,QtWidgets.QTableWidgetItem(row[11]))
            self.tableWidget.setItem(tablerow,10,QtWidgets.QTableWidgetItem(row[12]))
            tablerow+=1
        connection.close()
    def refresh(self):
        self.cbId.clear()
        self.tfNienKhoa.setText("")
        self.cbGioiTinh.setCurrentText("Nam")
        self.cbNganh.setCurrentText("CNTT")
        self.cbHe.setCurrentText("Dân sự")
        self.tfTenSV.setText("")
        self.tfCMND.setText("")
        self.tfNgaySinh.setText("")
        self.tfEmail.setText("")
        self.tfSDT.setText("")
        self.tfDiaChi.setText("")
        self.UiComponents()
        self.tfModel.setText("")

    def save(self):
        ten = self.tfTenSV.text()
        nienKhoa = self.tfNienKhoa.text()
        cmnd = self.tfCMND.text()
        gioiTinh = self.cbGioiTinh.currentText()
        ngaySinh = self.tfNgaySinh.text()
        email = self.tfEmail.text()
        sdt = self.tfSDT.text()
        diaChi = self.tfDiaChi.text()
        cbNganh = self.cbNganh.currentText()
        cbHe = self.cbHe.currentText()
        if isRequiredFiled(ten) == False or isRequiredFiled(nienKhoa) == False or isRequiredFiled(
                cmnd) == False or isRequiredFiled(ngaySinh) == False or isRequiredFiled(
                email) == False or isRequiredFiled(sdt) == False or isRequiredFiled(diaChi) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidID(cmnd) == False:
            self.showdialog("CMND không hợp lệ.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidDate(ngaySinh) == False:
            self.showdialog("Ngày sinh không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        else:
            # lay id cua bang Khoa
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("SELECT id FROM COURSE WHERE he = ? and nganh = ?", (cbHe, cbNganh))
                course_id = cursor.fetchone()

                sqliteConnection.commit()

                cursor.close()
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to select data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute(
                    "INSERT INTO students (ten, cmnd, ngaySinh, sdt ,gioiTinh, email, diaChi, nienKhoa, course_id) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (ten, cmnd, ngaySinh, sdt, gioiTinh, email, diaChi, nienKhoa, course_id[0]))

                sqliteConnection.commit()
                print("Record inserted successfully into SqliteDb_developers table ", cursor.rowcount)
                cursor.close()
                self.showdialog("Lưu thành công.")
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
        self.from_address = "thanhtrungkma@gmail.com"
        self.password = "tdjojstbkjyoxadm"
        # Cấu hình thông tin email
        to_address = "nguyenvanthaind73@gmail.com"
        subject = "Tieu de"
        body = "alo alo"

        # Tạo đối tượng MIMEMultipart để đính kèm nội dung email
        msg = MIMEMultipart()
        msg['From'] = self.from_address
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Tạo kết nối đến máy chủ email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Đăng nhập vào tài khoản email
        server.login(self.from_address, self.password)

        # Gửi email
        text = msg.as_string()
        server.sendmail(self.from_address, to_address, text)

        # Đóng kết nối
        server.quit()

        # Hiển thị thông báo khi gửi email thành công
        QtWidgets.QMessageBox.information(self, "Success", "Email sent successfully!")
    

    def delete(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?",
                                   QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbId.currentText()
            if (isRequiredFiled(id) == False):
                self.showdialog("Vui lòng chọn sinh viên cần xóa.")
            else:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")
                    cursor.execute("DELETE FROM models WHERE student_id = ?", [id])

                    cursor.execute("DELETE FROM students WHERE id = ?", [id])

                    sqliteConnection.commit()
                    cursor.close()
                    self.deleteModel(id)
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table", error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def deleteModel(self, student_id):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("DELETE FROM models WHERE student_id = ?", [student_id])

            sqliteConnection.commit()
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def edit(self):
        id = self.cbId.currentText()
        ten = self.tfTenSV.text()
        nienKhoa = self.tfNienKhoa.text()
        cmnd = self.tfCMND.text()
        gioiTinh = self.cbGioiTinh.currentText()
        ngaySinh = self.tfNgaySinh.text()
        email = self.tfEmail.text()
        sdt = self.tfSDT.text()
        diaChi = self.tfDiaChi.text()
        if (isRequiredFiled(id) == False):
            self.showdialog("Chọn sinh viên cần sửa.")
        elif isRequiredFiled(ten) == False or isRequiredFiled(nienKhoa) == False or isRequiredFiled(
                cmnd) == False or isRequiredFiled(ngaySinh) == False or isRequiredFiled(
                email) == False or isRequiredFiled(sdt) == False or isRequiredFiled(diaChi) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidID(cmnd) == False:
            self.showdialog("CMND không hợp lệ.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidDate(ngaySinh) == False:
            self.showdialog("Ngày sinh không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute(
                    "UPDATE students SET ten = ?, cmnd = ?, ngaySinh = ?, sdt = ?, gioiTinh = ?, email = ?, diaChi = ?, nienKhoa = ? WHERE id = ?",
                    (ten, cmnd, ngaySinh, sdt, gioiTinh, email, diaChi, nienKhoa, id,))

                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công.")
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

    def createFolder(self, model):
        directory = model
        parent_dir = "C:/Users/thanh/OneDrive/Desktop/facee/DataSet/FaceData/raw/"
        path = os.path.join(parent_dir, directory)

        os.mkdir(path)
    def getPics(self):
        model = self.tfModel.text()
        id = self.cbId.currentText()
        if isRequiredFiled(model) == False or isRequiredFiled(id) == False:
            self.showdialog("Vui lòng nhập model và ID sinh viên")
        elif isValidString(model) == False:
            self.showdialog("Model không hợp lệ")
        elif self.checkIfStudentExist() == False:
            self.showdialog("Sinh viên đã có ảnh")
        else:
            # create folder
            print("1")
            self.createFolder(model)
            print("2")
            # open cam and take pics
            cam = cv2.VideoCapture(0)

            cv2.namedWindow("Screenshot")

            img_counter = 1

            while True:
                ret, frame = cam.read()
                if not ret:
                    print("failed to grab frame")
                    break
                cv2.imshow("test", frame)

                k = cv2.waitKey(1)
                if k%256 == 27:
                    # ESC pressed
                    if img_counter == 1:
                        self.showdialog("Vui lòng chụp ảnh")
                    else:
                        print("Escape hit, closing...")
                        break
                elif k%256 == 32:
                    # SPACE pressed
                    number_str = str(img_counter)
                    zero_filled_number = number_str.zfill(4)
                    img_name = "C:/Users/thanh/OneDrive/Desktop/facee/DataSet/FaceData/raw/{folder}/{folder}_{counter}.jpg".format(folder=model, counter = zero_filled_number)
                    cv2.imwrite(img_name, frame)
                    img_counter += 1

            cam.release()

            cv2.destroyAllWindows()
            # save to db
            self.insertModel(model, id)

    def checkIfStudentExist(self):
        id = self.cbId.currentText()
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute(
                "select s.id from students as s inner join models as m on s.id = m.student_id where s.id = ?", (id,))

            sqliteConnection.commit()
            rows = cursor.fetchone()
            if rows == None:
                return True
            else:
                return False
        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

    def insertModel(self, model, id):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("INSERT INTO models (ten, student_id) VALUES (?, ?)", (model, id))

            sqliteConnection.commit()
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def processImage(self):
        align_mtcnn('DataSet/FaceData/raw', 'DataSet/FaceData/processed')
        trainClassifier('DataSet/FaceData/processed', 'Models/20180402-114759.pb', 'Models/facemodel.pkl')
        self.showdialog("Training completed.")
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)

    def seach(self):
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Chọn trường cần tìm.")
        else:
            if criteria == "ID sinh viên":
                # self.tableWidget.setRowCount(0)
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Nhập ID sinh viên.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID sinh viên phải là số.")
                else:
                    try:
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM students as s inner join course as c on s.course_id = c.id WHERE s.id = ?" + id
                        self.tableWidget.setRowCount(1)
                        tablerow = 0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow, 5, QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow, 6, QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow, 7, QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow, 8, QtWidgets.QTableWidgetItem(row[8]))
                            self.tableWidget.setItem(tablerow, 9, QtWidgets.QTableWidgetItem(row[11]))
                            self.tableWidget.setItem(tablerow, 10, QtWidgets.QTableWidgetItem(row[12]))
                        sqliteConnection.commit()
                        print(row)

                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table", error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên sinh viên":
                self.tableWidget.setRowCount(0)
                name = self.tfSearch.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Nhập tên sinh viên.")
                elif isValidString(name) == False:
                    self.showdialog("Tên sinh viên không hợp lệ.")
                else:
                    try:
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        self.tableWidget.setRowCount(20)
                        tablerow = 0
                        for row in cursor.execute(
                                "SELECT * FROM students as s inner join course as c on s.course_id = c.id WHERE s.ten like ?",
                                ("%" + name + "%",)):
                            self.tableWidget.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow, 5, QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow, 6, QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow, 7, QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow, 8, QtWidgets.QTableWidgetItem(row[8]))
                            self.tableWidget.setItem(tablerow, 9, QtWidgets.QTableWidgetItem(row[11]))
                            self.tableWidget.setItem(tablerow, 10, QtWidgets.QTableWidgetItem(row[12]))
                            tablerow += 1
                        sqliteConnection.commit()

                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table", error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")

class Profile(QDialog):
    def __init__(self):
        super(Profile, self).__init__()
        loadUi("./qt designer/profile.ui", self)
        login = LoginScreen()
        self.username = login.keyring.get_password(login.service_id, login.MAGIC_USERNAME_KEY)
        self.styleSheet()
        self.getUserInfor()
        self.btnUpdate.clicked.connect(self.update)
        self.btnExit.clicked.connect(self.exit)
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start()

    def getUserInfor(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute(
                "select * from teachers as t inner join account as a on t.id = a.teacher_id where a.username = ?",
                (self.username,))

            sqliteConnection.commit()
            record = cursor.fetchone()
            self.tfTen.setText(record[1])
            self.tfSDT.setText(record[2])
            self.tfDiaChi.setText(record[3])
            self.tfEmail.setText(record[4])
            self.cbQuestion.setCurrentText(record[9])
            self.tfAnswer.setText(record[10])
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

    def update(self):
        if isRequiredFiled(self.tfTen.text()) == False or isRequiredFiled(
                self.tfSDT.text()) == False or isRequiredFiled(self.tfDiaChi.text()) == False or isRequiredFiled(
                self.tfEmail.text()) == False or isRequiredFiled(
                self.cbQuestion.currentText()) == False or isRequiredFiled(self.tfAnswer) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isValidEmail(self.tfEmail.text()) == False:
            self.showdialog("Email không hợp lệ")
        elif isValidPhone(self.tfSDT.text()) == False:
            self.showdialog("Số điện thoại không hợp lệ")
        else:
            # update profile
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute(
                    "UPDATE teachers SET ten = ?, sdt = ?, diaChi = ?, email = ?  WHERE id = (SELECT teacher_id FROM account WHERE username = ?)",
                    (self.tfTen.text(), self.tfSDT.text(), self.tfDiaChi.text(), self.tfEmail.text(), self.username))

                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            # update secret question
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE account SET question = ?, answer = ? WHERE username = ?",
                               (self.cbQuestion.currentText(), self.tfAnswer.text(), self.username))

                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Cập nhật thành công")
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def styleSheet(self):
        leftHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/BestFacialRecognition.jpg')
        self.label.setPixmap(leftHeaderPixmap)
        centerHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/facialrecognition.png')
        self.label_2.setPixmap(centerHeaderPixmap)
        rightHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/images.jpg')
        self.label_3.setPixmap(rightHeaderPixmap)
        bodyCSS = "QFrame#frame_2{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/backgroud.jpg');}"
        self.frame_2.setStyleSheet(bodyCSS)
        self.lbDate.setFont(QFont('Arial', 10))

    def showTime(self):
        now = datetime.now()

        dt_string = now.strftime("%d/%m/%Y")
        t_string = now.strftime("%H:%M:%S")

        self.lbDate.setText(dt_string + "\n " + t_string)

    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
class Teacher(QDialog):
    def __init__(self):
        super(Teacher, self).__init__()
        loadUi("./qt designer/thongtingiangvien.ui", self)
        self.btnSave.clicked.connect(self.save)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnEdit.clicked.connect(self.edit)
        self.btnLoadAll.clicked.connect(self.loadData)
        self.btnSearch.clicked.connect(self.search)
        self.btnDelete.clicked.connect(self.delete)
        self.btnExit.clicked.connect(self.exit)
        self.tfPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.loadData()
        self.UiComponents()

    def UiComponents(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM teachers order by id")

            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbId.addItem(str(row[0]))
            cursor.close()
            self.cbId.activated.connect(self.getInfor)
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

    def getInfor(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select * from teachers as t inner join account as a on t.id = a.teacher_id where t.id = ?",
                           (self.cbId.currentText(),))


            sqliteConnection.commit()
            results = cursor.fetchone()
            print(results)
            decrypt = base64.b85decode(results[12]).decode("utf-8")
            cursor.close()

            self.tfTen.setText(results[1])
            self.tfSDT.setText(results[2])
            self.tfDiaChi.setText(results[3])
            self.tfEmail.setText(results[4])
            self.cbLoai.setCurrentText(str(results[5]))
            self.tfUsername.setText(results[7])
            self.tfPassword.setText(decrypt)
            self.cbRole.setCurrentText(str(results[9]))
        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

    def exit(self):
        # detection()
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def loadData(self):
        connection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery = "select * from teachers"

        self.tableWidget.setRowCount(20)
        tablerow = 0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow, 5, QtWidgets.QTableWidgetItem(row[5]))
            tablerow += 1
        connection.close()

    def refresh(self):
        self.tfTen.setText("")
        self.tfSDT.setText("")
        self.tfEmail.setText("")
        self.tfDiaChi.setText("")
        self.cbLoai.setCurrentText("")
        self.cbId.clear()
        self.tfUsername.setText("")
        self.tfPassword.setText("")
        self.cbRole.setCurrentText("")
        self.UiComponents()

    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)

    def save(self):
        ten = self.tfTen.text()
        sdt = self.tfSDT.text()
        email = self.tfEmail.text()
        diaChi = self.tfDiaChi.text()
        loai = self.cbLoai.currentText()
        username = self.tfUsername.text()
        password = self.tfPassword.text()
        role = self.cbRole.currentText()
        if isRequiredFiled(ten) == False or isRequiredFiled(sdt) == False or isRequiredFiled(
                email) == False or isRequiredFiled(diaChi) == False or isRequiredFiled(
                username) == False or isRequiredFiled(password) == False or isRequiredFiled(role) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        elif isValidUsername(username) == False:
            self.showdialog("Tên tài khoản không hợp lệ.")
        elif self.checkIfUsernameExist(username) == True:
            self.showdialog("Tên tài khoản đã tồn tại.")
        elif isValidPassword(password) == False:
            self.showdialog("Mật khẩu không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO teachers (ten, sdt, diaChi, email, loai) values(?, ?, ?, ?, ?)",
                               (ten, sdt, diaChi, email, loai))

                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            # save account
            try:
                id = self.getTeacherId(ten)
                encrypt = base64.b85encode(password.encode("utf-8"))
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO account (username, password, role, teacher_id) values(?, ?, ?, ?)",
                               (username, encrypt, role, id))

                sqliteConnection.commit()
                self.showdialog("Thêm thành công")
                self.loadData()
                self.refresh()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

    def edit(self):
        id = self.cbId.currentText()
        ten = self.tfTen.text()
        sdt = self.tfSDT.text()
        email = self.tfEmail.text()
        diaChi = self.tfDiaChi.text()
        loai = self.cbLoai.currentText()
        username = self.tfUsername.text()
        password = self.tfPassword.text()
        role = self.cbRole.currentText()
        if (isRequiredFiled(id) == False):
            self.showdialog("Chọn giảng viên cần sửa.")
        if isRequiredFiled(ten) == False or isRequiredFiled(sdt) == False or isRequiredFiled(
                email) == False or isRequiredFiled(diaChi) == False or isRequiredFiled(
                username) == False or isRequiredFiled(password) == False or isRequiredFiled(role) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        elif isValidUsername(username) == False:
            self.showdialog("Tên tài khoản không hợp lệ.")
        elif self.checkIfUsernameExist(username):
            self.showdialog("Tên tài khoản đã tồn tại.")
        elif isValidPassword(password) == False:
            self.showdialog("Mật khẩu không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE teachers SET ten = ?, sdt = ?, diaChi = ?, email = ?, loai = ? WHERE id = ?",
                               (ten, sdt, diaChi, email, loai, id))

                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            # edit account
            try:
                
                encrypt = base64.b85encode(password.encode("utf-8"))
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE account SET username = ?, password = ?, role = ? WHERE teacher_id = ?",
                               (username, encrypt, role, id))

                sqliteConnection.commit()
                self.showdialog("Sửa thành công")
                self.loadData()
                self.refresh()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table", error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

    def search(self):
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Chọn cột cần tìm.")
        else:
            if criteria == "ID giáo viên":
                self.tableWidget.setRowCount(0)
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Nhập ID giáo viên.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID giáo viên không hợp lệ.")
                else:
                    try:
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM teachers WHERE id =" + id
                        self.tableWidget.setRowCount(20)
                        tablerow = 0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow, 5, QtWidgets.QTableWidgetItem(row[5]))
                            tablerow += 1
                        sqliteConnection.commit()

                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table", error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên giáo viên":
                self.tableWidget.setRowCount(0)
                name = self.tfSearch.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Nhập tên giáo viên.")
                elif isValidString(name) == False:
                    self.showdialog("Tên giáo viên không hợp lệ.")
                else:
                    try:
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM teachers WHERE ten = '" + name + "'"
                        self.tableWidget.setRowCount(20)
                        tablerow = 0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow, 5, QtWidgets.QTableWidgetItem(row[5]))
                            tablerow += 1
                        sqliteConnection.commit()

                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table", error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")

    def delete(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?",
                                   QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbId.currentText()
            if (isRequiredFiled(id) == False):
                self.showdialog("Vui lòng chọn giảng viên cần xóa.")
            else:
                # delete account
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM account WHERE teacher_id = ?", (id,))

                    sqliteConnection.commit()
                    cursor.close()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table", error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
                # delete teacher
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM teachers WHERE id = ?", (id,))

                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table", error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")

    def checkIfUsernameExist(self, username):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select id from account where username = ?", [username])

            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()
            if results is None:
                return False
            else:
                return True
        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

    def getTeacherId(self, name):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select id from teachers where ten = ?", (name,))

            sqliteConnection.commit()
            rows = cursor.fetchone()
            cursor.close()
            return rows[0]
        except sqlite3.Error as error:
            print("Failed to get data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

class Subject(QDialog):
    def __init__(self):
        super(Subject, self).__init__()
        loadUi("./qt designer/quanlymonhoc.ui", self)
        self.tableWidget1.setColumnWidth(0,100)
        self.tableWidget1.setColumnWidth(1,270)
        self.tableWidget1.setColumnWidth(2,180)
        self.tableWidget1.setColumnWidth(3,180)
        self.btnSave1.clicked.connect(self.save1)
        self.btnRefresh1.clicked.connect(self.refresh1)
        self.btnEdit1.clicked.connect(self.edit1)
        self.btnLoadAll1.clicked.connect(self.loadData1)
        self.btnSearch1.clicked.connect(self.search1)
        self.btnDelete1.clicked.connect(self.delete1)
        self.btnExit.clicked.connect(self.exit)
        self.loadData1()
        self.UiComponents()
    def UiComponents(self):
        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        cursor.execute("SELECT id FROM subjects order by id")
        
        sqliteConnection.commit()
        rows = cursor.fetchall()

        for row in rows:
            self.cbId1.addItem(str(row[0]))
        cursor.close()
        self.cbId1.activated.connect(self.getInfor1)
    def getInfor1(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT * FROM subjects WHERE id = ?", (self.cbId1.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone();
            cursor.close()

            self.tfTenMon.setText(results[1])
            self.tfSoBuoi.setText(str(results[2]))
            self.cbKi.setCurrentText(str(results[3]))
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def loadData1(self):
        try:          
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            query = "SELECT * FROM subjects"
            self.tableWidget1.setRowCount(20)
            tablerow=0
            for row in cursor.execute(query):
                self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                tablerow+=1
            sqliteConnection.commit()
        
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def save1(self):
        tenMon = self.tfTenMon.text()
        soBuoi = self.tfSoBuoi.text()
        ki = self.cbKi.currentText()
        if isRequiredFiled(tenMon) == False or isRequiredFiled(soBuoi) == False:
            self.showdialog("Nhập đầy đủ thông tin.")
        elif isValidString(tenMon) == False:
            self.showdialog("Tên môn học không hợp lệ.")
        elif isValidInteger(soBuoi) == False:
            self.showdialog("Số buổi không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO subjects(ten, soBuoi, semester_id) VALUES(?,?,?)", (tenMon, soBuoi, int(ki)))   
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Thêm môn học thành công.")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def refresh1(self):
        self.tfTenMon.setText("")
        self.tfSoBuoi.setText("")
        self.cbKi.setCurrentText("1")
        self.cbId1.clear()
        self.UiComponents()
    def edit1(self):
        id = self.cbId1.currentText()
        tenMon = self.tfTenMon.text()
        soBuoi = self.tfSoBuoi.text()
        ky = self.cbKi.currentText()
        if isRequiredFiled(id):
            self.showdialog("Chọn môn học cần sửa.")
        elif isRequiredFiled(tenMon) == False or isRequiredFiled(soBuoi) == False:
            self.showdialog("Nhập đầy đủ thông tin.")
        elif isValidString(tenMon) == False:
            self.showdialog("Tên môn học không hợp lệ.")
        elif isValidInteger(soBuoi) == False:
            self.showdialog("Số buổi không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE subjects SET ten = ?, soBuoi = ?, semester_id = ? WHERE id = ?", (tenMon, soBuoi, int(ky), id))   
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa môn học thành công.")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete1(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbId1.currentText()
            if isRequiredFiled(id) == False:
                self.showdialog("Chọn môn học cần xóa.")
            else:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM subjects WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa môn học thành công.")
                    self.tableWidget1.setRowCount(0)
                    self.loadData1()
                    self.refresh1()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def search1(self):
        criteria = self.cbSearch1.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Chọn tiêu chí tìm kiếm.")
        else:
            if criteria == "ID môn học":
                self.tableWidget1.setRowCount(0)
                id = self.tfSearch1.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Nhập ID môn học.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID môn học không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM subjects WHERE id =" + id
                        self.tableWidget1.setRowCount(20)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget1.setColumnWidth(0,100)
                            self.tableWidget1.setColumnWidth(1,270)
                            self.tableWidget1.setColumnWidth(2,180)
                            self.tableWidget1.setColumnWidth(3,180)
                            self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên môn học":
                self.tableWidget1.setRowCount(0)
                name = self.tfSearch1.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Nhập tên môn học.")
                elif isValidString(name) == False:
                    self.showdialog("Tên môn học không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM subjects WHERE ten = '" + name + "'"
                        print(query)
                        self.tableWidget1.setRowCount(20)
                        tablerow=0
                        for row in cursor.execute(query):
                            print(row)
                            self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Kì":
                self.tableWidget1.setRowCount(0)
                ki = self.tfSearch1.text()
                if isRequiredFiled(ki) == False:
                    self.showdialog("Chọn kì.")
                elif isValidInteger(ki) == False:
                    self.showdialog("Kì không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM subjects WHERE semester_id =" + ki 
                        self.tableWidget1.setRowCount(20)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
class LopHoc(QDialog):
    def __init__(self):
        super(LopHoc, self).__init__()
        loadUi("./qt designer/quanlylophoc.ui",self)
        self.tableWidget.setColumnWidth(0,250)
        self.tableWidget.setColumnWidth(1,250)
        self.tableWidget.setColumnWidth(2,250)
        self.tableWidget2.setColumnWidth(0,100)
        self.tableWidget2.setColumnWidth(1,100)
        self.tableWidget2.setColumnWidth(2,250)
        self.tableWidget2.setColumnWidth(3,250)
        self.btnRefresh1.clicked.connect(self.refresh1)
        self.btnAdd1.clicked.connect(self.add1)
        self.btnUpdate1.clicked.connect(self.update1)
        self.btnLoadAll1.clicked.connect(self.loadData1)
        self.btnDel1.clicked.connect(self.delete1)
        self.btnRefresh2.clicked.connect(self.refresh2)
        self.btnAdd2.clicked.connect(self.add2)
        self.btnUpdate2.clicked.connect(self.update2)
        self.btnLoadAll2.clicked.connect(self.loadData2)
        self.btnDel2.clicked.connect(self.delete2)
        self.btnSearch1.clicked.connect(self.search1)
        self.btnSearch2.clicked.connect(self.search2)
        self.btnExit.clicked.connect(self.Exit)
        self.loadData1()
        self.loadData2()
        self.UiComponents()
    def Exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def UiComponents(self):
        # lay id class
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM class order by id")
            
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbIdLopHoc.addItem(str(row[0]))
                self.cbIdLopHoc2.addItem(str(row[0]))
            cursor.close()
            self.cbIdLopHoc.activated.connect(self.getInfor)
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # lay id sinh vien
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM students order by id")
            
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbIdSv.addItem(str(row[0]))
            cursor.close()
            self.cbIdSv.activated.connect(self.getInfor2)
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInfor(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT * FROM class WHERE id = ?", (self.cbIdLopHoc.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenLop.setText(results[1])
            self.tfDiaDiem.setText(results[2])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInfor2(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM students WHERE id = ?", (self.cbIdSv.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenSV.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def loadData1(self):
        connection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select * from class"

        self.tableWidget.setRowCount(10)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            tablerow+=1
        connection.close()
    def loadData2(self):
        connection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select * from classMember"

        self.tableWidget2.setRowCount(10)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[1])))
            self.tableWidget2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[2])))
            self.tableWidget2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[4]))
            tablerow+=1
        connection.close()
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def add1(self):
        tenLop = self.tfTenLop.text()
        diaDiem = self.tfDiaDiem.text()
        if isRequiredFiled(tenLop) == False or isRequiredFiled(diaDiem) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO class (ten, diaDiem) values(?, ?)", (tenLop, diaDiem))
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Thêm thành công")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def refresh1(self):
        self.tfTenLop.setText("")
        self.tfDiaDiem.setText("")
        self.cbIdLopHoc.clear()
        self.UiComponents()
    def update1(self):
        id = self.cbIdLopHoc.currentText()
        tenLop = self.tfTenLop.text()
        diaDiem = self.tfDiaDiem.text()
        if isRequiredFiled(id) == False:
            self.showdialog("Vui lòng chọn lớp học cần sửa.")
        elif isRequiredFiled(tenLop) == False or isRequiredFiled(diaDiem) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE class SET ten = ?, diaDiem = ? WHERE id = ?", (tenLop,diaDiem , id))
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")   
    def delete1(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbIdLopHoc.currentText()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng chọn lớp học cần xóa.")
            else:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM class WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData1()
                    self.refresh1()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def search1(self):
        criteria = self.cbSearch1.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng chọn tiêu chí cần tìm.")
        else:
            if criteria == "ID lớp học":
                id = self.tfSearch1.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID lớp học cần tìm.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID lớp học phải là số nguyên.")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM class WHERE id =" + id
                        self.tableWidget.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên lớp":
                name = self.tfSearch1.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Vui lòng nhập tên lớp học cần tìm.")
                elif isValidString(name) == False:
                    self.showdialog("Tên lớp học phải là chuỗi.")
                else:
                    try:          
                        self.tableWidget.setRowCount(0)
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM class WHERE ten LIKE '%"+ name + "%'"
                        self.tableWidget.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")

    def add2(self):
        idSV = self.cbIdSv.currentText()
        idLopHoc = self.cbIdLopHoc2.currentText()
        ngayVao = self.dateIn.text()
        ngayRa = self.dateOut.text()
        if isRequiredFiled(idSV) == False:
            self.showdialog("Vui lòng chọn sinh viên cần thêm.")
        elif isRequiredFiled(idLopHoc) == False:
            self.showdialog("Vui lòng chọn lớp học cần thêm.")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO classMember (student_id,class_id, ngayRa, ngayVao) values(?,?, ?, ?)", (idSV,idLopHoc,ngayRa,ngayVao))
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Thêm thành công")
                self.loadData2()
                self.refresh2()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def update2(self):
        idSV = self.cbIdSv.currentText()
        idLopHoc = self.cbIdLopHoc2.currentText()
        ngayVao = self.dateIn.text()
        ngayRa =self.dateOut.text()
        if isRequiredFiled(idSV) == False:
            self.showdialog("Vui lòng chọn sinh viên cần sửa.")
        elif isRequiredFiled(idLopHoc) == False:
            self.showdialog("Vui lòng chọn lớp học cần sửa.")
        else:
            # lay id bang classMember
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("SELECT id FROM classMember WHERE student_id=? AND class_id=?",(idSV,idLopHoc))
                id=cursor.fetchone()
                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            # sua ban ghi
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE classMember set student_id = ?, class_id = ?, ngayRa = ?, ngayVao = ? where id = ?",(idSV,idLopHoc,ngayRa, ngayVao,id[0]))
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công")
                self.loadData2()
                self.refresh2()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete2(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            idSV = self.cbIdSv.currentText()
            idLopHoc = self.cbIdLopHoc2.currentText()
            if isRequiredFiled(idSV) == False:
                self.showdialog("Vui lòng chọn sinh viên cần xóa.")
            elif isRequiredFiled(idLopHoc) == False:
                self.showdialog("Vui lòng chọn lớp học cần xóa.")
            else:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM classMember WHERE  student_id=? AND class_id=?", (idSV,idLopHoc))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData2()
                    self.refresh2()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def refresh2(self):
        qDate=QDate(2015,1,1)
        self.cbIdSv.clear()
        self.cbIdLopHoc2.clear()
        self.tfTenSV.setText("")
        self.dateIn.setDate(qDate)
        self.dateOut.setDate(qDate)
        self.UiComponents()
    def search2(self):
        criteria = self.cbSearch2.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng chọn tiêu chí tìm kiếm.")
        else:
            if criteria == "ID SV":
                id = self.tfSearch2.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID sinh viên.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID sinh viên phải là số.")
                else:
                    self.tableWidget2.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                
                        self.tableWidget2.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute("SELECT * FROM classMember WHERE student_id =?",(id,)):
                            self.tableWidget2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[4]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "ID lớp học":
                idLopHoc = self.tfSearch2.text()
                if isRequiredFiled(idLopHoc) == False:
                    self.showdialog("Vui lòng nhập ID lớp học.")
                elif isValidInteger(idLopHoc) == False:
                    self.showdialog("ID lớp học phải là số.")
                else:
                    self.tableWidget2.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM classMember WHERE class_id =" + idLopHoc
                        self.tableWidget2.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[4]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")

class Schedule(QDialog):

    def __init__(self):
        super(Schedule, self).__init__()
        loadUi("./qt designer/thongtinlichhoc.ui",self)
        self.btnAdd.clicked.connect(self.add)
        self.btnLoadAll.clicked.connect(self.loadData)
        self.btnUpdate.clicked.connect(self.update)
        self.btnDelete.clicked.connect(self.delete)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnSearch.clicked.connect(self.search)
        self.btnExit.clicked.connect(self.exit)
        # self.tableWidget.itemDoubleClicked.connect(self.on_click)
        self.UiComponents()
        self.loadData()
    def UiComponents(self):
        # lay id giao vien
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM teachers order by id")
        
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbIdGV.addItem(str(row[0]))
            cursor.close()
            self.cbIdGV.activated.connect(self.getInforGV)
        except sqlite3.Error as error:
              print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # lay id lop hoc
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM class order by id")
        
            sqliteConnection.commit()
            rows = cursor.fetchall()
           
            for row in rows:
                self.cbIdLop.addItem(str(row[0]))
            cursor.close()
            self.cbIdLop.activated.connect(self.getInforClass)
        except sqlite3.Error as error:
                print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # lay id mon hoc
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM subjects order by id")
        
            sqliteConnection.commit()
            rows = cursor.fetchall()
       
            for row in rows:
                self.cbIdMon.addItem(str(row[0]))
            cursor.close()
            self.cbIdMon.activated.connect(self.getInforSubject)
        except sqlite3.Error as error:
                print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforGV(self) :
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM teachers WHERE id = ?", (self.cbIdGV.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfGV.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforSubject(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM subjects WHERE id = ?", (self.cbIdMon.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenMon.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforClass(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM class WHERE id = ?", (self.cbIdLop.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenLop.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def loadData(self):
        self.tfSearch.clear()
        connection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id "

        self.tableWidget.setRowCount(50)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
            tablerow+=1
        connection.close()
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def add(self):
        start = self.deStart.text()
        end = self.deEnd.text()
        idGV = self.cbIdGV.currentText()
        idLopHoc = self.cbIdLop.currentText()
        idMon = self.cbIdMon.currentText()
        if isRequiredFiled(idGV) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isRequiredFiled(idLopHoc) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isRequiredFiled(idMon) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO schedule (teacher_id, subject_id, class_id, batDau, ketThuc) values(?, ?, ?, ?, ?)", (idGV,idMon,idLopHoc,start,end))
            
                sqliteConnection.commit()
                print("Record inserted successfully into SqliteDb_developers table ", cursor.rowcount)
                cursor.close()
                self.showdialog("Thêm thành công")
                self.tableWidget.setRowCount(0)
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def update(self):
        id = self.tfId.text()
        idGV = self.cbIdGV.currentText()
        idLopHoc = self.cbIdLop.currentText()
        idMon = self.cbIdMon.currentText()
        start = self.deStart.text()
        end = self.deEnd.text()
        if isRequiredFiled(id) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isRequiredFiled(idGV) == False or isRequiredFiled(idLopHoc) == False or isRequiredFiled(idMon) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE schedule set teacher_id = ?, subject_id = ?, class_id = ?, batDau = ?, ketThuc = ? where id = ?", (idGV, idMon, idLopHoc,start ,end , id,))
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công")
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.tfId.text()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng nhập đầy đủ thông tin")
            else:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM schedule WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.tableWidget.setRowCount(0)
                    self.loadData()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def refresh(self):
        self.tfId.clear()
        self.cbIdGV.clear()
        self.cbIdLop.clear()
        self.cbIdMon.clear()
        self.tfGV.setText("")
        self.tfTenMon.setText("")
        self.tfTenLop.setText("")
        self.UiComponents() 
    def search(self):
        self.tableWidget.setRowCount(0)
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            if criteria == "ID giáo viên":
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập đầy đủ thông tin")
                elif isValidInteger(id) == False:
                    self.showdialog("Vui lòng nhập số")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        self.tableWidget.setRowCount(50)
                        tablerow=0
                        for row in cursor.execute("select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id where s.teacher_id = ?" , (id,)):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "ID môn":
                idMon = self.tfSearch.text()
                if isRequiredFiled(idMon) == False:
                    self.showdialog("Vui lòng nhập đầy đủ thông tin")
                elif isValidInteger(idMon) == False:
                    self.showdialog("Vui lòng nhập số")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        self.tableWidget.setRowCount(50)
                        tablerow=0
                        for row in cursor.execute("select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id where s.subject_id = ?" , (idMon,)):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "ID lớp":
                idClass = self.tfSearch.text()
                if isRequiredFiled(idClass) == False:
                    self.showdialog("Vui lòng nhập đầy đủ thông tin")
                elif isValidInteger(idClass) == False:
                    self.showdialog("Vui lòng nhập số")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        self.tableWidget.setRowCount(50)
                        tablerow=0
                        for row in cursor.execute("select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id where s.class_id = ?" , (idClass,)):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)

class Recognize(QDialog):
    def __init__(self):
        super(Recognize, self).__init__()
        loadUi("./qt designer/hethongdiemdanhkhuonmat.ui",self)
        self.btnExit.clicked.connect(self.exit)
        self.btnDetection.clicked.connect(self.detection)
        self.UiComponents()
    def UiComponents(self):
        try:
            date = datetime.today().strftime('%Y-%m-%d')
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT m.ten from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + date + "'"
            cursor.execute(sqlite_select_query)
            rows = cursor.fetchall()
            for row in rows:
                self.cbMon.addItem(str(row[0]))
            self.cbMon.activated.connect(self.getInforSubject)
            # self.cbMon.activated.connect(self.getNumberLessonForSubject)
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforSubject(self):
        try:
            tenMon = self.cbMon.currentText()
            date = datetime.today().strftime('%Y-%m-%d')

            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT s.class_id, m.ten, TIME(s.batDau), TIME(s.ketThuc) from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + date + "'" + "and m.ten = " + "'" + tenMon + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            print(record)
            self.tfIdLop.setText(str(record[0]))
            self.tfTenMon.setText(str(record[1]))
            self.tfThoiGian.setText(str(record[2]) + " - " + str(record[3]))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def exit(self):
         main = Main()
         widget.addWidget(main)
         widget.setCurrentIndex(widget.currentIndex()+1)
    def detection(self):
        mon = self.cbMon.currentText()
        endTime = self.tfEnd.text()
        # buoi = self.cbSoBuoi.currentText()
        if isRequiredFiled(mon) == False:
           self.showdialog("chưa chọn buổi học")
        # elif isRequiredFiled(buoi) == False:
        #     self.showdialog("Bạn chưa chọn buổi học")
        elif isRequiredFiled(endTime) == False:
            self.showdialog("Bạn chưa nhập thời gian kết thúc")
        else:
            parser = argparse.ArgumentParser()
            parser.add_argument('--path', help='Path of the video you want to test on.', default=0)
            args = parser.parse_args()

            MINSIZE = 20
            THRESHOLD = [0.6, 0.7, 0.7]
            FACTOR = 0.709
            IMAGE_SIZE = 182
            INPUT_IMAGE_SIZE = 160
            CLASSIFIER_PATH = 'Models/facemodel.pkl'
            VIDEO_PATH = args.path
            FACENET_MODEL_PATH = 'Models/20180402-114759.pb'

            # Load The Custom Classifier
            with open(CLASSIFIER_PATH, 'rb') as file:
                model, class_names = pickle.load(file)
            print("Custom Classifier, Successfully loaded")

            with tf.Graph().as_default():

                # Cai dat GPU neu co
                gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.6)
                sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(gpu_options=gpu_options, log_device_placement=False))

                with sess.as_default():

                    # Load the model
                    print('Loading feature extraction model')
                    facenet.load_model(FACENET_MODEL_PATH)

                    # Get input and output tensors
                    images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
                    embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
                    phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
                    embedding_size = embeddings.get_shape()[1]

                    pnet, rnet, onet = src.align.detect_face.create_mtcnn(sess, "src/align")

                    # people_detected = set()
                    # person_detected = collections.Counter()

                    cap  = VideoStream(src=0).start()
                    
                    list = []

                    while (True):
                        frame = cap.read()
                        frame = imutils.resize(frame, width=600)
                        frame = cv2.flip(frame, 1)

                        bounding_boxes, _ = src.align.detect_face.detect_face(frame, MINSIZE, pnet, rnet, onet, THRESHOLD, FACTOR)

                        faces_found = bounding_boxes.shape[0]
                        try:
                            if faces_found > 0:
                                det = bounding_boxes[:, 0:4]
                                bb = np.zeros((faces_found, 4), dtype=np.int32)
                                for i in range(faces_found):
                                    bb[i][0] = det[i][0]
                                    bb[i][1] = det[i][1]
                                    bb[i][2] = det[i][2]
                                    bb[i][3] = det[i][3]
                                    if (bb[i][3]-bb[i][1])/frame.shape[0]>0.25:
                                        cropped = frame[bb[i][1]:bb[i][3], bb[i][0]:bb[i][2], :]
                                        scaled = cv2.resize(cropped, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE),
                                                        interpolation=cv2.INTER_CUBIC)
                                        scaled = facenet.prewhiten(scaled)
                                        scaled_reshape = scaled.reshape(-1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE, 3)
                                        feed_dict = {images_placeholder: scaled_reshape, phase_train_placeholder: False}
                                        emb_array = sess.run(embeddings, feed_dict=feed_dict)

                                        predictions = model.predict_proba(emb_array)
                                        best_class_indices = np.argmax(predictions, axis=1)
                                        best_class_probabilities = predictions[
                                            np.arange(len(best_class_indices)), best_class_indices]
                                        best_name = class_names[best_class_indices[0]]
                                        print("Name: {}, Probability: {}".format(best_name, best_class_probabilities))

                                        if best_class_probabilities > 0.4:
                                            cv2.rectangle(frame, (bb[i][0], bb[i][1]), (bb[i][2], bb[i][3]), (0, 255, 0), 2)
                                            text_x = bb[i][0]
                                            text_y = bb[i][3] + 20

                                            name = class_names[best_class_indices[0]]
                                            cv2.putText(frame, name, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                                    1, (255, 255, 255), thickness=1, lineType=2)
                                            # cv2.putText(frame, str(round(best_class_probabilities[0], 3)), (text_x, text_y + 17),
                                            #         cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                            #         1, (255, 255, 255), thickness=1, lineType=2)
                                            # person_detected[best_name] += 1
                                            if best_name != 'Unknow' and best_name not in list:
                                                count = self.getScheduleId()
                                                print(type(count)) 
                                                list.append(best_name)
                                                path = "./image/Photo"  + str(int(count[0]) + 1) +  ".jpg"
                                                cv2.imwrite(path, frame)
                                                self.photo.setPixmap(QtGui.QPixmap(path))
                                                self.photo.setMinimumSize(1, 1)
                                                self.photo.setScaledContents(True)
                                                now = datetime.now().time()
                                                self.markAttendance(best_name, path, now)
                                        else:
                                            name = "Unknown"
                        except:
                            pass
                        cv2.imshow('Face Recognition', frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            self.absent()
                            break

    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def markAttendance(self, name, path, now):
        check = "X"
        # lay id sinh vien
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")
            sqlite_select_query = "SELECT s.id, s.ten from students as s inner join models as m on s.id = m.student_id where m.ten =" + "'" + name + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            student_id = record[0]
            student_name = record[1]  
            self.tfIdSV.setText(str(record[0]))
            self.tfTenSV.setText(str(record[1]))
            self.tfDD.setText(str(now))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
         # lay id, thoi gian ket thuc schedule        
        try:
            tenMon = self.cbMon.currentText()
            today = datetime.today().strftime('%Y-%m-%d')

            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT s.id, TIME(s.ketThuc) from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + today + "'" + "and m.ten = " + "'" + tenMon + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            schedule_id = record[0]  
            end = record[1]
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        endTime = self.tfEnd.text()
        current_time = now.strftime("%H:%M:%S")
        stdPhoto =  base64.b85encode(path.encode("utf-8"))
        if(current_time < endTime):
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                sqlite_insert_blob_query = """insert into attendance (schedule_id, student_id, ngayDiemDanh, trangThai, image)  values(?, ?, ?, ?, ?)"""

                # Convert data into tuple format
                data_tuple = (schedule_id, student_id, today + " " + current_time, check, stdPhoto)
                cursor.execute(sqlite_insert_blob_query, data_tuple)
                sqliteConnection.commit()
                print("Record inserted successfully into table ")
                cursor.close()

            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                    print("The SQLite connection is closed")
        elif current_time > endTime and current_time < end:
            try:
                sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")
                time_object = datetime.strptime(endTime, '%H:%M:%S').time()

                duration = datetime.combine(date.min, now) - datetime.combine(date.min, time_object)
                cursor.execute("INSERT INTO attendance (schedule_id, student_id, ngayDiemDanh, trangThai, image) values(?, ?, ?, ?, ?)", (schedule_id, student_id, today + " " + current_time, "Muộn " + str(round(duration.total_seconds() / 60)) + " phút", stdPhoto))

                sqliteConnection.commit()
                print("Record inserted successfully into table ")
                cursor.close()

            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                    print("The SQLite connection is closed")
    def getScheduleId(self):
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT id from attendance"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchall()    
            # get max id
            if record :
                max_id = max(record)
            else:
                max_id = 1
            cursor.close()
            print(max_id)
            return max_id
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def absent(self):
        try:
            tenMon = self.cbMon.currentText()
            today = datetime.today().strftime('%Y-%m-%d')

            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT s.id  from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + today + "'" + "and m.ten = " + "'" + tenMon + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            schedule_id = record[0]  # id of schedule
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # lay sinh vien khong diem danh
        try:
            data = ()
            list = []

            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sql = "select cm.student_id from schedule as sc inner join class as c on sc.class_id = c.id inner join classMember as cm on cm.class_id = c.id inner join subjects as m on sc.subject_id = m.id  where  DATE(sc.batDau) ='" + today + "'" + "and m.ten = '" + tenMon + "'" + "EXCEPT select student_id from attendance as a inner join schedule as s on a.schedule_id = s.id  inner join subjects as m on s.subject_id = m.id  where  DATE(s.batDau) = '" + today + "'" + "and m.ten = '" + tenMon + "'"
                                                
            for row in cursor.execute(sql):
                data = data + (schedule_id, row[0], today, "Vắng")
                list.append(data)
                data = ()
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # insert vao bang attendance
        try:
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            cursor.executemany('INSERT INTO attendance (schedule_id, student_id, ngayDiemDanh, trangThai) VALUES(?,?,?,?);', list)
			
            sqliteConnection.commit()
            sqliteConnection.close()

        except sqlite3.Error as error:
            print("Failed to inseart data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def refresh(self):
        self.photo.setPixmap(QtGui.QPixmap(""))
        self.tfIdSV.setText("")
        self.tfTenSV.setText("")
        self.tfDD.setText("")
        self.tfIdLop.setText("")
        self.tfTenMon.setText("")
        self.tfThoiGian.setText("")
class Popup(QDialog):
    def __init__(self, id, parent):
        super().__init__(parent)
        self.resize(600, 300)
        self.label = QLabel(self)
        self.showImage(id)
    def showImage(self, id):
        try:          
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
             
            cursor.execute("select image from attendance where id = ?", (id,))
            record = cursor.fetchone()[0]
            if record is not None:
                path = base64.b85decode(record).decode("utf-8")
                sqliteConnection.commit()
                self.label.setPixmap(QtGui.QPixmap(path))
                self.label.setMinimumSize(1, 1)
                self.label.setScaledContents(True)

            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
class Attendence(QDialog):
    def __init__(self):
        super(Attendence, self).__init__()
        loadUi("./qt designer/quanlythongtindiemdanh.ui",self)
        self.btnExit.clicked.connect(self.exit)
        self.btnDelete.clicked.connect(self.delete)
        self.btnImage.clicked.connect(self.launchPopup)   
        self.btnLoadAll.clicked.connect(self.UiComponents)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnExport.clicked.connect(self.export)
        self.btnFilter.clicked.connect(self.filter)  
        self.tableWidget.itemDoubleClicked.connect(self.on_click)
        self.btnUpdate.clicked.connect(self.update)
        self.btnSearch.clicked.connect(self.search)
        self.UiComponents()
    def on_click(self, item):
        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        cursor.execute("select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where a.id = ?", (item.text(),))
        
        sqliteConnection.commit()
        rows = cursor.fetchall()

        for row in rows:
            self.tfIdDiemDanh.setText(str(row[0]))
            self.tfIdSV.setText(str(row[1]))
            self.tfTenSV.setText(row[2])
            self.tfLop.setText(row[3])
            self.tfGioVao.setText(row[4])
            self.tfGioRa.setText(row[5])
            self.tfNgay.setText(row[6])
            self.tfDiemDanh.setText(row[7])
        cursor.close()
    def filter(self):
        self.tableWidget.setRowCount(0)
        today = date.today()
        d1 = today.strftime("%Y-%m-%d")
        try:          
            sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
             
            self.tableWidget.setRowCount(100)
            sql = "select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where  DATE(a.ngayDiemDanh) = '" + d1 + "'"
            tablerow=0
            for row in cursor.execute(sql):
                self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                tablerow+=1
            sqliteConnection.commit()
            
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def launchPopup(self):
        id = self.tfIdDiemDanh.text()
        if isRequiredFiled(id) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            self.popup = Popup(id, self)
            self.popup.show()
    def UiComponents(self):
        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        sql = ("select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id")
        
        self.tableWidget.setRowCount(50)
        tablerow = 0
        for row in cursor.execute(sql):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))      
            tablerow+=1
        sqliteConnection.close()
    def delete(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.tfIdDiemDanh.text()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng nhập id")
            else:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM attendance WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.tableWidget.setRowCount(0)
                    self.UiComponents()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def refresh(self):
        self.tfIdDiemDanh.setText("")
        self.tfIdSV.setText("")
        self.tfTenSV.setText("")
        self.tfLop.setText("")
        self.tfGioVao.setText("")
        self.tfGioRa.setText("")
        self.tfNgay.setText("")
        self.tfDiemDanh.setText("")    
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)   
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)  
    def export(self):
        rowCount  = self.tableWidget.rowCount()
        columnCount  = self.tableWidget.columnCount()
        list = []
        for row in range(rowCount):
            rowData = []
            for column in range(columnCount):
                widgetItem = self.tableWidget.item(row, column)
                if(widgetItem and widgetItem.text):
                    rowData.append(widgetItem.text())
            if(len(rowData) != 0):
                list.append(rowData)
        row = 1
        col = 0
        workbook = xlsxwriter.Workbook("C:\\Users\\thanh\\Downloads\\diemdanh.xlsx")
 
        worksheet = workbook.add_worksheet("My sheet")
        worksheet.write('A1', 'ID')
        worksheet.write('B1', 'ID sinh viên')
        worksheet.write('C1', 'Tên')
        worksheet.write('D1', 'Lớp')
        worksheet.write('E1', 'Giờ vào')
        worksheet.write('F1', 'Giờ ra')
        worksheet.write('G1', 'Ngày')
        worksheet.write('H1', 'Điểm danh')
        # Iterate over the data and write it out row by row.
        for j in (list):
            print(j)
            worksheet.write(row, col, j[0])
            worksheet.write(row, col + 1, j[1])
            worksheet.write(row, col + 2, j[2])
            worksheet.write(row, col + 3, j[3])
            worksheet.write(row, col + 4, j[4])
            worksheet.write(row, col + 5, j[5]) 
            worksheet.write(row, col + 6, j[6])
            worksheet.write(row, col + 7, j[7])
            row += 1
        workbook.close()
        self.showdialog("Tạo file excel thành công")
    def search(self):
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng chọn tiêu chí tìm kiếm")
        else:
            if criteria == "ID sinh viên":
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID sinh viên")
                elif isValidInteger(id) == False:
                    self.showdialog("ID sinh viên phải là số")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        self.tableWidget.setRowCount(100)
                        tablerow=0
                        for row in cursor.execute("select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where a.student_id = ?", [id]):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên sinh viên":
                ten = self.tfSearch.text()
                if isRequiredFiled(ten) == False:
                    self.showdialog("Vui lòng nhập tên sinh viên")
                elif isValidString(ten) == False:
                    self.showdialog("Tên sinh viên không hợp lệ")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                        sql = "select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where st.ten like '%" + ten +  "%'"
                        self.tableWidget.setRowCount(100)
                        tablerow=0
                        for row in cursor.execute(sql):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Lớp":
                lop = self.tfSearch.text()
                if isRequiredFiled(lop) == False:
                    self.showdialog("Vui lòng nhập lớp")
                elif isValidString(lop) == False:
                    self.showdialog("Lớp không hợp lệ")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                        sql = "select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where c.ten like '%" + lop+  "%'"
                        self.tableWidget.setRowCount(100)
                        tablerow=0
                        for row in cursor.execute(sql):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def update(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn sửa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.tfIdDiemDanh.text()
            time = self.tfNgay.text()
            diemDanh = self.tfDiemDanh.text()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng nhập id")
            elif isRequiredFiled(time) == False:
                self.showdialog("Vui lòng nhập ngày")
            elif isValidDateTime(time) == False:
                self.showdialog("Ngày giờ không hợp lệ")
            elif isRequiredFiled(diemDanh) == False:
                self.showdialog("Vui lòng nhập trạng thái")
            else:
                try:
                    sqliteConnection = sqlite3.connect("C:\\Users\\thanh\\OneDrive\\Desktop\\facee\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("UPDATE attendance set ngayDiemDanh = ?, trangThai = ? where id = ?", (time, diemDanh, id))
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Sửa thành công")
                    self.tableWidget.setRowCount(0)
                    self.UiComponents()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to update data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
class Analyst(QDialog):
    def __init__(self):
        super(Analyst, self).__init__()
        loadUi("./qt designer/thongke.ui",self)
        self.btnExit.clicked.connect(self.exit)
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
app = QApplication(sys.argv)
login = LoginScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(login)
widget.setFixedHeight(841)
widget.setFixedWidth(1291)
widget.show()
app.exec_()