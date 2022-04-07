import sys

from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
from time import sleep
import os
import ctypes
import pyperclip
import keyboard
from win10toast import ToastNotifier
import pyautogui
import cv2
import pytesseract
import threading
import webbrowser

import datetime
import random
import json

# Global ========================================
THREAD_MESSAGE_TEST = True
THREAD_STOP = False
START_STOP = False
MESSAGE_INFO = "no message."
# ===============================================


def test_message():
    global THREAD_MESSAGE_TEST
    THREAD_MESSAGE_TEST = False
    t1 = ToastNotifier()
    t1.show_toast("Бот kad.arbitr.ru",
                  "Тестируем всплывающее окно и звук оповещения (Если нет звука перезагрузите Windows)",
                  duration=10)
    THREAD_MESSAGE_TEST = True

def read_code(code, password):
    return True


def read_file(file_name, password):
    test_done = False
    try:
        with open(file_name, 'r', encoding="utf-8") as file:
            data = json.load(file)
            test_done = read_code(data, password)
    except:
        print("Error open file key")

    return test_done

# Проверка управление мышкой для левши.
def isLeft():
    get_state = 23  # 0x0017 for SM_SWAPBUTTON
    is_left = ctypes.windll.user32.GetSystemMetrics(get_state)
    return bool(is_left)


def special_simbol(char, spec_simbol):
    if spec_simbol == False:
        return False
    elif char == '.' or char == ':':
        return True
    else:
        return False


def find_word_per(line_1, line_2, percent=100, spec_simbol=False):
    max_found = 0

    for item_1 in range(len(line_1)):

        for item_2 in range(len(line_2)):
            index_found = 0

            if line_1[item_1] == line_2[item_2]:
                for index in range(len(line_2) - item_2):

                    if item_1 + index >= len(line_1):
                        break
                    elif line_1[item_1 + index] == line_2[item_2 + index] or special_simbol(line_1[item_1 + index],
                                                                                            spec_simbol):
                        index_found += 1
            if max_found < index_found:
                max_found = index_found

    result_per = (100 / len(line_1)) * max_found

    return result_per >= percent

# -------------------------------------------------------------------------
# ------- Start program text_recogtion --------------------------------------
# -------------------------------------------------------------------------


def text_tesseract(file_path, param='', percent=65, spec_simbol=False):
    pytesseract.pytesseract.tesseract_cmd = "Tesseract-OCR\\tesseract.exe"

    img = cv2.imread(file_path)
    config = r"--oem 3 --psm 6"
    data = pytesseract.image_to_data(img, lang="rus", config=config)

    result = list()

    for index, it in enumerate(data.splitlines()):
        if index == 0:
            # print(it.split())
            continue
        str = it.split()
        try:
            if len(str[11]) > 1:
                if find_word_per(param, str[11], percent, spec_simbol):
                    result.append(dict({"line": str[4], "left": str[6], "top": str[7], "text": str[11]}))
        except IndexError:
            continue
    return result


def find_data_time(time, data, screen):
    result_data = text_tesseract(screen, param=time, percent=100, spec_simbol=True)

    result_time = text_tesseract(screen, param=data, percent=100, spec_simbol=True)

    x = 1
    y = 1

    for it_1 in result_data:
        for it_2 in result_time:
            if it_1["line"] == it_2["line"]:
                text = "text"
                # print(it_1["line"])
                time_test = find_word_per(time, it_1[text], spec_simbol=True)
                data_test = find_word_per(data, it_2[text], spec_simbol=True)
                # print(f"test_time: {time_test}")
                # print(f"test_data: {data_test}")
                if time_test and data_test:
                    # print("Successful")
                    x = it_1["top"]
                    y = it_1["left"]
    if x == 1 and y == 1:
        return False
    else:
        result = dict({"x": x, "y": y})

    return result


def find_word(word, screen):  # screen = "Screens\\scr01.png"
    result = text_tesseract(screen, param=word, percent=80)

    try:
        x = result[0]["top"]
        y = result[0]["left"]
        return dict({"x": x, "y": y})

    except IndexError:
        print("IndexError: Can't find button")
        return False


def find_start_meeting(x_test, status, screen):  # x_test = x
    result_status = text_tesseract(screen, param=status)
    # print(result_status)
    x = 1
    y = 1

    if len(result_status) == 0:
        return False

    for it_1 in result_status:

        if x_test - 10 <= int(it_1["top"]) <= x_test + 90:

            text = "text"
            online_status = find_word_per(status, it_1[text], percent=80)
            # print(online_status)
            if online_status:
                x = it_1["top"]
                y = it_1["left"]

    if x == 1 and y == 1:
        return False
    else:
        result = dict({"x": x, "y": y})

    return result


# -------------------------------------------------------------------------
# ------- Start program Push_message --------------------------------------
# -------------------------------------------------------------------------


def push():
    global THREAD_STOP
    global MESSAGE_INFO
    MESSAGE_INFO = "Online status found."
    for _ in range(5):
        if THREAD_STOP:
            break
        toaster = ToastNotifier()
        toaster.show_toast("Бот kad.arbitr.ru",
                           "Онлайн-заседание! Начало!",
                           duration=5)


# -------------------------------------------------------------------------
# ------- Start program BOt -----------------------------------------------
# -------------------------------------------------------------------------

URL_TEST = "https://kad.arbitr.ru/"


def start_control_card(time, data, status_f, param="auto"):
    global MESSAGE_INFO
    global START_STOP
    MESSAGE_INFO = f"Start control card in {param}"

    if param == "auto":
        pyautogui.press("F11")
        sleep(0.5)
        pyautogui.hotkey("ctrl", "0")
        sleep(0.5)
        pyautogui.hotkey("ctrl", "+")

    not_find_it = True
    index_data_error = 0
    index_status_error = 0
    index = 0

    global THREAD_STOP

    while not_find_it:

        if THREAD_STOP:
            break   # Stop search card and off program

        case_time = True
        index += 1

        # ============= find coordination for data ================================
        pyautogui.screenshot(r"Screens\scr04.png")
        x_time = find_data_time(time, data, r"Screens\scr04.png")

        # collision control in scrolling ---------
        user32 = ctypes.windll.user32
        screensize_x = user32.GetSystemMetrics(1)

        if int(x_time["x"]) > screensize_x / 2:
            move_scroll = int(screensize_x / 2) - int(x_time["x"])
            pyautogui.scroll(move_scroll - 100)
            continue
        # ----------------------------------------

        while case_time:
            if THREAD_STOP:
                break  # Stop search card and off program
            try:
                int(x_time["x"])
                MESSAGE_INFO = f"Index: {index}. Case data ok."
                print(f"Index: {index}. Case data ok.")
                case_time = False
            except:
                index_data_error += 1
                MESSAGE_INFO = f"Index: {index}. Empty case - data: {index_data_error}."
                print(f"Index: {index}. Empty case - data: {index_data_error}.")
                pyautogui.screenshot(r"Screens\scr04.png")
                x_time = find_data_time(time, data, r"Screens\scr04.png")
        # =============================================================================

        # ============== re-find coordination for online-status =======================
        # pyautogui.screenshot(r"Screens\scr04.png")
        sleep(0.5)
        result_f = find_start_meeting(int(x_time["x"]), status_f, r"Screens\scr04.png")

        if result_f != False:
            pyautogui.moveTo(int(result_f["y"]), int(result_f["x"]), duration=0.5)

            sleep(0.5)
            if param == "auto":
                pyautogui.hotkey("ctrl", "0")
            push()
            break
        index_status_error += 1
        MESSAGE_INFO = f"Index: {index}. Empty case - status: {index_status_error}."
        print(f"Index: {index}. Empty case - status: {index_status_error}.")
        # =============================================================================
    MESSAGE_INFO = "Case status: Found."
    START_STOP = False


def test_language():
    # LangRU = 419
    # LangEN = 409
    u1 = ctypes.windll.LoadLibrary("user32.dll")
    pf1 = getattr(u1, "GetKeyboardLayout")
    if hex(pf1(0)) == '0x4190419':
        pyautogui.hotkey("alt", 'shift')
        pyautogui.hotkey("ctrl", 'shift')
        print('Keyboard Layout change to = EN')
    elif hex(pf1(0)) == '0x4090409':
        print('Keyboard Layout = EN')
    else:
        print("Change language to ENG")


def find_online_start(time, data, status_f):
    global THREAD_STOP
    wait_but_found = True
    index_move = 0
    sleep(0.3)
    pyautogui.hotkey("ctrl", "0")
    sleep(0.5)
    pyautogui.hotkey("ctrl", "+")

    while wait_but_found:
        if THREAD_STOP:
            break

        sleep(0.3)
        pyautogui.screenshot(r"Screens\scr03.png")

        find_card = find_data_time(time, data, r"Screens\scr03.png")

        if find_card != False:
            pyautogui.moveTo(int(find_card["y"]) + 100, int(find_card["x"]), duration=0.5)

            # collision control in scrolling ---------
            user32 = ctypes.windll.user32
            screensize_x = user32.GetSystemMetrics(1)

            if int(find_card["x"]) > screensize_x/2:
                pyautogui.scroll(-200)
            # ----------------------------------------
            # ---------------------- START CONTROL ONLINE STATUS --------------------------------------------------
            start_control_card(time, data, status_f)
            # -----------------------------------------------------------------------------------------------------
            wait_but_found = False

        else:
            print(f"Couldn't find: card")

            if index_move <= 15:
                index_move += 1
                pyautogui.scroll(-600)
            elif index_move <= 30:
                index_move += 1
                pyautogui.scroll(600)
            else:
                index_move = 0

            continue

    return True


def start_func(url, time, data, status_f):
    global MESSAGE_INFO
    global THREAD_STOP
    # проверяем какой диск содержит папку windows (полагается там же Program Files)
    prog_file_dir = os.getenv("SystemDrive")
    path_x64 = f"{prog_file_dir}\Program Files\Google\Chrome\Application\chrome.exe"
    path_x86 = f"{prog_file_dir}\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(path_x64))
    webbrowser.get('chrome').open_new(url)

    if os.path.isfile(path_x64):
        # os.startfile(path_x64)
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(path_x64))
        webbrowser.get('chrome').open_new(url)
        MESSAGE_INFO = "Start Chrome x64 version."
    elif os.path.isfile(path_x86):
        # os.startfile(path_x86)
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(path_x86))
        webbrowser.get('chrome').open_new(url)
        MESSAGE_INFO = "Start Chrome x86 version."
    else:
        MESSAGE_INFO = "Can't find Chrome in system."
        return

    # Счетчик времени загрузки браузера ------------------
    for it in range(59):
        MESSAGE_INFO = "Waiting for the launch of the page."
        sleep(1)
        program_list = pyautogui.getAllTitles()
        # print(program_list)
        str1 = ''.join(program_list)
        if find_word_per('- Google Chrome', str1, percent=80):
            MESSAGE_INFO = f"Load in {it + 1} sec."
            print(f"Load in {it + 1} sec.")
            break
        elif THREAD_STOP:
            return
        sleep(1)
    # ----------------------------------------------------

    pyautogui.press("F11")

    not_found_but01 = True

    step_intex = 0
    Online_but_found = False
    error_info = "None"
    sleep(0.3)
    pyautogui.hotkey("ctrl", "0")

    while not_found_but01:
        sleep(5)
        if(step_intex == 50):
            return -1
        elif THREAD_STOP:
            return
        try:
            step_intex += 1
            x, y = 1, 1

            if Online_but_found == False:
                error_info = "Попытка загрузить скриншот."
                pyautogui.screenshot(r"Screens\scr01.png")
                error_info = "Попытка найти кнопку."

                result_button = find_word("Онлайн-заседания", r"Screens\scr01.png")

                if result_button:
                    x = int(result_button['y'])
                    y = int(result_button["x"])
                else:
                    x, y = pyautogui.locateCenterOnScreen(r"Screens\online_but_1080.png")

                error_info = "Попытка переместить указатель мыши."
                pyautogui.moveTo(x, y, duration=0.5)
                Online_but_found = True

                sleep(1)

                if isLeft():
                    pyautogui.click(x, y, button='right')
                else:
                    pyautogui.click(x, y, button='left')
        except:
            print(f"Couldn't find: {error_info}")
            continue

        not_found_but01 = False

    find_online_start(time, data, status_f)

    global START_STOP
    START_STOP = False

    return 1


def enter_hello():
    pyautogui.PAUSE = 1.5
    pyautogui.FAILSAFE = True
    size_screen = pyautogui.size()

    y_size = size_screen[0]
    x_size = size_screen[1]

    pyautogui.moveTo(y_size / 2, x_size / 2, duration=0.2)
    pyautogui.move(-500, -300, duration=0.5)
    pyautogui.click()
    sleep(0.5)
    pyautogui.typewrite("Hello!", interval=0.2)
    sleep(0.5)
    pyautogui.press("R")


# -------------------------------------------------------------------------
# ------- Start program Ui_Dialog -----------------------------------------
# -------------------------------------------------------------------------


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(800, 500)
        Dialog.setMinimumSize(QtCore.QSize(800, 500))
        Dialog.setMaximumSize(QtCore.QSize(800, 500))
        self.stackedWidget = QtWidgets.QStackedWidget(Dialog)
        self.stackedWidget.setGeometry(QtCore.QRect(0, 0, 800, 500))
        self.stackedWidget.setMinimumSize(QtCore.QSize(800, 500))
        self.stackedWidget.setMaximumSize(QtCore.QSize(800, 500))
        self.stackedWidget.setStyleSheet(".QWidget {image: url(background.png);}")
        self.stackedWidget.setObjectName("stackedWidget")
        self.page_1 = QtWidgets.QWidget()
        self.page_1.setStyleSheet("")
        self.page_1.setObjectName("page_1")
        self.EXIT_but = QtWidgets.QPushButton(self.page_1)
        self.EXIT_but.setGeometry(QtCore.QRect(500, 350, 70, 40))
        self.EXIT_but.setObjectName("EXIT_but")
        self.START_but = QtWidgets.QPushButton(self.page_1)
        self.START_but.setGeometry(QtCore.QRect(230, 350, 70, 40))
        self.START_but.setObjectName("START_but")
        self.label = QtWidgets.QLabel(self.page_1)
        self.label.setGeometry(QtCore.QRect(160, 130, 31, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.page_1)
        self.label_2.setGeometry(QtCore.QRect(160, 190, 41, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.page_1)
        self.label_3.setGeometry(QtCore.QRect(150, 290, 51, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.URL_text = QtWidgets.QLineEdit(self.page_1)
        self.URL_text.setGeometry(QtCore.QRect(210, 130, 381, 31))
        self.URL_text.setObjectName("URL_text")
        self.Data_text = QtWidgets.QLineEdit(self.page_1)
        self.Data_text.setGeometry(QtCore.QRect(210, 190, 381, 31))
        self.Data_text.setObjectName("Data_text")
        self.STATUS_text = QtWidgets.QLineEdit(self.page_1)
        self.STATUS_text.setGeometry(QtCore.QRect(210, 290, 381, 31))
        self.STATUS_text.setStyleSheet("")
        self.STATUS_text.setObjectName("STATUS_text")
        self.Time_text = QtWidgets.QLineEdit(self.page_1)
        self.Time_text.setGeometry(QtCore.QRect(210, 240, 381, 31))
        self.Time_text.setObjectName("Time_text")
        self.label_4 = QtWidgets.QLabel(self.page_1)
        self.label_4.setGeometry(QtCore.QRect(160, 240, 41, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.MANUAL_but = QtWidgets.QPushButton(self.page_1)
        self.MANUAL_but.setGeometry(QtCore.QRect(365, 350, 70, 40))
        self.MANUAL_but.setStyleSheet("")
        self.MANUAL_but.setObjectName("MANUAL_but")
        self.label_5 = QtWidgets.QLabel(self.page_1)
        self.label_5.setGeometry(QtCore.QRect(350, 450, 100, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_5.setFont(font)
        self.label_5.setStyleSheet("")
        self.label_5.setObjectName("label_5")
        self.label_info = QtWidgets.QLabel(self.page_1)
        self.label_info.setGeometry(QtCore.QRect(30, 400, 741, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_info.setFont(font)
        self.label_info.setStyleSheet("border: 1px solid;\n"
"border-color: rgb(245, 245, 245);\n"
"border-radius: 5px;")
        self.label_info.setText("")
        self.label_info.setObjectName("label_info")
        self.PROFILE_but = QtWidgets.QPushButton(self.page_1)
        self.PROFILE_but.setGeometry(QtCore.QRect(30, 30, 50, 50))
        self.PROFILE_but.setStyleSheet("QPushButton {\n"
"    image: url(account-48.png);\n"
"    border: 0px solid;\n"
"}\n"
"QPushButton:hover {\n"
"    image: url(account-48-target.png);\n"
"    border: 0px solid;\n"
"}\n"
"QPushButton:pressed {    \n"
"    border: 0px solid;\n"
"}")
        self.PROFILE_but.setText("")
        self.PROFILE_but.setIconSize(QtCore.QSize(50, 50))
        self.PROFILE_but.setObjectName("PROFILE_but")
        self.SETTING_but = QtWidgets.QPushButton(self.page_1)
        self.SETTING_but.setGeometry(QtCore.QRect(720, 30, 50, 50))
        self.SETTING_but.setAutoFillBackground(False)
        self.SETTING_but.setStyleSheet("QPushButton {\n"
"    image: url(settings-47.png);\n"
"    border: 0px solid;\n"
"    color: rgb(255, 255, 255);\n"
"}\n"
"QPushButton:pressed {    \n"
"    border: 0px solid;\n"
"}")
        self.SETTING_but.setText("")
        self.SETTING_but.setObjectName("SETTING_but")
        self.stackedWidget.addWidget(self.page_1)
        self.Account_manger = QtWidgets.QWidget()
        self.Account_manger.setObjectName("Account_manger")
        self.Return_but = QtWidgets.QPushButton(self.Account_manger)
        self.Return_but.setGeometry(QtCore.QRect(30, 30, 50, 50))
        self.Return_but.setStyleSheet("QPushButton {\n"
"    image: url(icon-go-back.png);\n"
"    border: 0px solid;\n"
"}\n"
"QPushButton:hover {\n"
"    image: url(icon-go-back_target.png);\n"
"    border: 0px solid;\n"
"}\n"
"QPushButton:pressed {    \n"
"    border: 0px solid;\n"
"}")
        self.Return_but.setText("")
        self.Return_but.setObjectName("Return_but")
        self.label_6 = QtWidgets.QLabel(self.Account_manger)
        self.label_6.setGeometry(QtCore.QRect(180, 160, 41, 31))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.Account_manger)
        self.label_7.setGeometry(QtCore.QRect(180, 210, 41, 31))
        self.label_7.setObjectName("label_7")
        self.Update_key_but = QtWidgets.QPushButton(self.Account_manger)
        self.Update_key_but.setGeometry(QtCore.QRect(180, 280, 91, 31))
        self.Update_key_but.setObjectName("Update_key_but")
        self.Name_label = QtWidgets.QLabel(self.Account_manger)
        self.Name_label.setGeometry(QtCore.QRect(240, 160, 371, 31))
        self.Name_label.setText("")
        self.Name_label.setObjectName("Name_label")
        self.Number_label = QtWidgets.QLabel(self.Account_manger)
        self.Number_label.setGeometry(QtCore.QRect(240, 210, 371, 31))
        self.Number_label.setText("")
        self.Number_label.setObjectName("Number_label")
        self.Change_User_but = QtWidgets.QPushButton(self.Account_manger)
        self.Change_User_but.setGeometry(QtCore.QRect(700, 30, 50, 50))
        self.Change_User_but.setStyleSheet("QPushButton {\n"
"    image: url(icon-user-64.png);\n"
"    border: 0px solid;\n"
"}\n"
"QPushButton:hover {\n"
"    image: url(icon-user-64-target.png);\n"
"    border: 0px solid;\n"
"}\n"
"QPushButton:pressed {    \n"
"    border: 0px solid;\n"
"}")
        self.Change_User_but.setText("")
        self.Change_User_but.setObjectName("Change_User_but")
        self.stackedWidget.addWidget(self.Account_manger)
        self.Log_in_page = QtWidgets.QWidget()
        self.Log_in_page.setObjectName("Log_in_page")
        self.label_8 = QtWidgets.QLabel(self.Log_in_page)
        self.label_8.setGeometry(QtCore.QRect(150, 140, 61, 31))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(self.Log_in_page)
        self.label_9.setGeometry(QtCore.QRect(150, 190, 61, 31))
        self.label_9.setObjectName("label_9")
        self.Rem_me_check = QtWidgets.QCheckBox(self.Log_in_page)
        self.Rem_me_check.setGeometry(QtCore.QRect(500, 240, 91, 21))
        self.Rem_me_check.setObjectName("Rem_me_check")
        self.Name_lineEdit = QtWidgets.QLineEdit(self.Log_in_page)
        self.Name_lineEdit.setGeometry(QtCore.QRect(210, 140, 381, 31))
        self.Name_lineEdit.setObjectName("Name_lineEdit")
        self.Password_lineEdit = QtWidgets.QLineEdit(self.Log_in_page)
        self.Password_lineEdit.setGeometry(QtCore.QRect(210, 190, 381, 31))
        self.Password_lineEdit.setObjectName("Password_lineEdit")
        self.ENTER_but = QtWidgets.QPushButton(self.Log_in_page)
        self.ENTER_but.setGeometry(QtCore.QRect(210, 310, 111, 41))
        self.ENTER_but.setObjectName("ENTER_but")
        self.EXIT_log_but = QtWidgets.QPushButton(self.Log_in_page)
        self.EXIT_log_but.setGeometry(QtCore.QRect(480, 310, 111, 41))
        self.EXIT_log_but.setObjectName("EXIT_log_but")
        self.for_password = QtWidgets.QPushButton(self.Log_in_page)
        self.for_password.setGeometry(QtCore.QRect(350, 450, 121, 23))
        self.for_password.setObjectName("for_password")
        self.ERROR_label = QtWidgets.QLabel(self.Log_in_page)
        self.ERROR_label.setGeometry(QtCore.QRect(210, 270, 381, 21))
        self.ERROR_label.setText("")
        self.ERROR_label.setObjectName("ERROR_label")
        self.stackedWidget.addWidget(self.Log_in_page)

        self.retranslateUi(Dialog)
        self.stackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.EXIT_but.setText(_translate("Dialog", "Exit"))
        self.START_but.setText(_translate("Dialog", "Auto"))
        self.label.setText(_translate("Dialog", "URL:"))
        self.label_2.setText(_translate("Dialog", "Data:"))
        self.label_3.setText(_translate("Dialog", "Status:"))
        self.URL_text.setText(_translate("Dialog", "https://kad.arbitr.ru/Card/f0d53425-8362-4767-9e95-f99c85530b3d"))
        self.Data_text.setText(_translate("Dialog", "20.10.2020"))
        self.STATUS_text.setText(_translate("Dialog", "Онлайн-заседание"))
        self.Time_text.setText(_translate("Dialog", "15:00"))
        self.label_4.setText(_translate("Dialog", "Time:"))
        self.MANUAL_but.setText(_translate("Dialog", "Manual"))
        self.label_5.setText(_translate("Dialog", "Waiter_Bot_ARB."))
        self.label_6.setText(_translate("Dialog", "Name:"))
        self.label_7.setText(_translate("Dialog", "№:"))
        self.Update_key_but.setText(_translate("Dialog", "Update Key"))
        self.label_8.setText(_translate("Dialog", "Name:"))
        self.label_9.setText(_translate("Dialog", "Password:"))
        self.Rem_me_check.setText(_translate("Dialog", "Remember me"))
        self.ENTER_but.setText(_translate("Dialog", "Enter"))
        self.EXIT_log_but.setText(_translate("Dialog", "Exit"))
        self.for_password.setText(_translate("Dialog", "forgotten password"))


# -------------------------------------------------------------------------
# ------- Start program ImageDialog ---------------------------------------
# -------------------------------------------------------------------------


class ProgressHandler(QtCore.QThread):
    def bot_start(self, url, time, data, status):
        global THREAD_STOP
        THREAD_STOP = False
        t1 = threading.Thread(target=start_func, args=(url, time, data, status))
        t1.start()
        # start_func(url, time, data, status)

    def bot_manual_start(self, time, data, status):
        global THREAD_STOP
        THREAD_STOP = False
        t1 = threading.Thread(target=start_control_card, args=(time, data, status, "manual"))
        t1.start()
        # start_control_card(time, data, status, param="manual")


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)
#  Styles:
#  0 : OK
#  1 : OK | Cancel
#  2 : Abort | Retry | Ignore
#  3 : Yes | No | Cancel
#  4 : Yes | No
#  5 : Retry | Cancel
#  6 : Cancel | Try Again | Continue


class ImageDialog(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # self.setStyleSheet(".QWidget {background-image: url(background.png);}")
        self.setFixedSize(QtCore.QSize(800, 500))

        self.appWin = QApplication(sys.argv)
        self.uiMwin = Ui_Dialog()
        self.uiMwin.setupUi(self)
        self.bot = ProgressHandler()

        # -----------------------------------------------------------
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, False)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.press = False
        self.last_pos = QtCore.QPoint(0, 0)
        # -----------------------------------------------------------

        self.uiMwin.stackedWidget.setCurrentIndex(2)
        self.name = ''
        self.password = ''

        # Buttons -----------------------------------
        self.uiMwin.EXIT_but.clicked.connect(self.bt_exit)
        self.uiMwin.EXIT_log_but.clicked.connect(self.bt_exit)
        self.uiMwin.START_but.clicked.connect(self.bt_start)
        self.uiMwin.MANUAL_but.clicked.connect(self.bt_manual)
        self.uiMwin.PROFILE_but.clicked.connect(self.bt_account)
        self.uiMwin.ENTER_but.clicked.connect(self.bt_login)
        self.uiMwin.Return_but.clicked.connect(self.bt_return)
        self.uiMwin.Change_User_but.clicked.connect(self.bt_change_user)
        self.uiMwin.SETTING_but.clicked.connect(self.bt_test_message)
        # -------------------------------------------

    # ---------------------------- перемещение окна -------------------------------------------
    def mouseMoveEvent(self, event):
        if self.press:
            self.move(event.globalPos() - self.last_pos)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.press = True

        self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.press = False

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 50))
        painter.drawRect(self.rect())
    # -----------------------------------------------------------------------------------------

    def bt_test_message(self):
        global THREAD_MESSAGE_TEST
        if THREAD_MESSAGE_TEST:
            t_mess = threading.Thread(target=test_message)
            t_mess.start()

    def bt_account(self):
        self.uiMwin.stackedWidget.setCurrentIndex(1)

    def bt_return(self):
        self.uiMwin.stackedWidget.setCurrentIndex(0)

    def bt_login(self):
        name = self.uiMwin.Name_lineEdit.text()
        password = self.uiMwin.Password_lineEdit.text()

        if password == "********":
            pass
        else:
            self.password = password

        if self.name == '':
            self.name = name

        if read_file(f"{name}_key.json", self.password):
            self.uiMwin.ERROR_label.setText("Success.")
            self.uiMwin.Name_label.setText(name)
            self.uiMwin.Password_lineEdit.setText("********")
            sleep(0.5)
            self.uiMwin.stackedWidget.setCurrentIndex(0)
        else:
            self.uiMwin.ERROR_label.setText("Error User or Password.")

    def bt_change_user(self):
        self.uiMwin.stackedWidget.setCurrentIndex(2)

    def status_info(self):
        global THREAD_STOP
        global MESSAGE_INFO
        while True:
            self.uiMwin.label_info.setText(MESSAGE_INFO)
            if THREAD_STOP:
                break
            sleep(0.05)

    def bt_exit(self):
        global THREAD_STOP
        global MESSAGE_INFO
        MESSAGE_INFO = "Stop program"

        THREAD_STOP = True
        raise SystemExit(1)

    def take_data(self):
        return self.uiMwin.Data_text.text()

    def take_time(self):
        return self.uiMwin.Time_text.text()

    def take_status(self):
        return self.uiMwin.STATUS_text.text()

    def take_url(self):
        return self.uiMwin.URL_text.text()

    def bt_start(self):
        global START_STOP
        if START_STOP:
            return
        else:
            START_STOP = True

        t_m = threading.Thread(target=self.status_info)
        t_m.start()

        time = self.take_time()
        data = self.take_data()
        url = self.take_url()
        status = self.take_status()

        self.bot.bot_start(url, time, data, status)

    def bt_manual(self):
        global START_STOP
        if START_STOP:
            return
        else:
            START_STOP = True

        t_m = threading.Thread(target=self.status_info)
        t_m.start()

        Mbox("Информация", "Увеличьте масштаб страницы в Chrome до 110% (ctrl и +)", 0)

        time = self.take_time()
        data = self.take_data()
        status = self.take_status()

        self.showMinimized()
        self.bot.bot_manual_start(time, data, status)


# -------------------------------------------------------------------------
# ------- Start program Main ----------------------------------------------
# -------------------------------------------------------------------------


def create_main_window():

    """ pyuic6 -x untitled.ui -o graphic_main.py """

    """ creating the graphic window class """

    app = QApplication(sys.argv)

    window = ImageDialog()
    window.setWindowTitle("Bot ARB")
    window.show()

    sys.exit(app.exec())


# -------------------------------------------------------------------------
# ------- Start program ---------------------------------------------------
# -------------------------------------------------------------------------

if __name__ == "__main__":
    create_main_window()
