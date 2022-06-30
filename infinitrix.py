#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import time
try:
    from ctypes import windll  # Only exists on Windows.
    myappid = u'smallcms.infinitrix.app.current'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass
import configparser
from html.parser import HTMLParser
from PyQt5.Qt import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import (QLabel, QWidget, QVBoxLayout, QApplication,
                             QLineEdit, QPushButton, QDialog, QMessageBox)
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, \
    QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp
from PyQt5.QtCore import (QSize, QRectF, Qt, QPropertyAnimation, pyqtProperty, 
                          QPoint, QParallelAnimationGroup, QEasingCurve)
from PyQt5.QtGui import QIcon, QDesktopServices, QPainter, QPainterPath, QColor, QPen
from PyQt5 import QtCore, QtWidgets

#Get config from file in user home path
class CheckConfig():
    home_path = os.path.expanduser("~")
    ini_path = home_path + '/.infinitrix.ini'
    ini_contents = configparser.ConfigParser()
    if os.path.exists(ini_path):
        ini_contents.read(ini_path)
        if ini_contents.has_option("main", "url"):
            print("Connecting to " + ini_contents['main']['url'])
        else:
            print("Error in config file!")
            quit()
    else:
        ini_contents['main'] = {}
        ini_contents['main']['url'] = ''
        ini_contents['main']['closetotray'] = '1'
        ini_contents['main']['sysnotify'] = '0'
        with open(ini_path, 'w') as ini_contentsfile:
            ini_contents.write(ini_contentsfile)
            print("Default configuration file not found, created new one in " + ini_path)
    app_url = (ini_contents['main']['url'] + '/desktop_app/?IFRAME=Y')

#Configuration options window class
class ConfigWindow(QWidget):
    def __init__(self):
        super(ConfigWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.resize(300, 150)
        self.center()
        self.inputLabel = QLabel("Input bitrix24 URL")
        if CheckConfig.ini_contents.has_option("main", "url"):
            self.url_editLine = QLineEdit(CheckConfig.ini_contents['main']['url'])
        else:
            self.url_editLine = QLineEdit("")

        self.url_editLine.setFixedWidth(300)

        self.minimize_check_box = QCheckBox('&Minimize to Tray')
        if CheckConfig.ini_contents.has_option("main", "closetotray"):
            if CheckConfig.ini_contents['main']['closetotray'] == '1':
                self.minimize_check_box.setChecked(True)
            else:
                self.minimize_check_box.setChecked(False)
        else:
            self.minimize_check_box.setChecked(True)

        self.systray_check_box = QCheckBox('&Legacy notifications')
        if CheckConfig.ini_contents.has_option("main", "sysnotify"):
            if CheckConfig.ini_contents['main']['sysnotify'] == '1':
                self.systray_check_box.setChecked(True)
            else:
                self.systray_check_box.setChecked(False)
        else:
            self.systray_check_box.setChecked(True)

        self.printButton = QPushButton("&Save")
        self.clearButton = QPushButton("&Cancel")

        self.printButton.clicked.connect(self.saveSettings)
        self.clearButton.clicked.connect(self.cancelSettings)

        url_Label_Layout = QHBoxLayout()
        url_Label_Layout.addWidget(self.inputLabel)
        url_Value_Layout = QHBoxLayout()
        url_Value_Layout.addWidget(self.url_editLine)

        minimize_Value_Layout = QHBoxLayout()
        minimize_Value_Layout.addWidget(self.minimize_check_box)

        systray_Value_Layout = QHBoxLayout()
        systray_Value_Layout.addWidget(self.systray_check_box)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.printButton)
        buttonLayout.addWidget(self.clearButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(url_Label_Layout)
        mainLayout.addLayout(url_Value_Layout)
        mainLayout.addLayout(minimize_Value_Layout)
        mainLayout.addLayout(systray_Value_Layout)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.setWindowTitle('Infinitrix options')
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def saveSettings(self):
        url_Value_Layout = self.url_editLine.text()

        if url_Value_Layout == '':
            QMessageBox.information(self, "Empty url", "Please enter the bitrix24 url.")
            return None

        home_path = os.path.expanduser("~")
        ini_path = home_path + '/.infinitrix.ini'
        ini_contents = configparser.ConfigParser()
        ini_contents['main'] = {}
        ini_contents['main']['url'] = url_Value_Layout
        if self.minimize_check_box.isChecked():
            ini_contents['main']['closetotray'] = '1'
        else:
            ini_contents['main']['closetotray'] = '0'
        if self.systray_check_box.isChecked():
            ini_contents['main']['sysnotify'] = '1'
        else:
            ini_contents['main']['sysnotify'] = '0'
        with open(CheckConfig.ini_path, 'w') as ini_contentsfile:
            ini_contents.write(ini_contentsfile)
        self.close()
        MainWindow.restart()

    def cancelSettings(self):
        self.close()


#Class to allow audio and camera
class WebEnginePage(QWebEnginePage):
    external_windows = []

    #Open urls in default browser
    def createWindow(self, _type):
        page = WebEnginePage(self)
        page.urlChanged.connect(self.open_browser)
        return page

    #Open urls in default browser (callback)
    def open_browser(self, url):
        self.page = self.sender()
        QDesktopServices.openUrl(url)
        #print("ext:",url)
        return False
        #self.page.deleteLater()

    #allow audio and camera
    def __init__(self, *args, **kwargs):
        QWebEnginePage.__init__(self, *args, **kwargs)
        self.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

    def onFeaturePermissionRequested(self, url, feature):
        if feature in (QWebEnginePage.MediaAudioCapture, 
            QWebEnginePage.MediaVideoCapture, 
            QWebEnginePage.MediaAudioVideoCapture):
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionDeniedByUser)

    #Javascript logging to console
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print("javaScriptConsoleMessage: ", level, message, lineNumber, sourceID)

#Modern notify class
class BubbleLabel(QWidget):

    BackgroundColor = QColor(255,255,255)
    BorderColor = QColor(72,194,249,255)

    def __init__(self, *args, **kwargs):
        self.animationGroup = None

        text = kwargs.pop("text", "")
        super(BubbleLabel, self).__init__(*args, **kwargs)
        self.setWindowFlags(
            Qt.Window | Qt.Tool | Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        # Set minimum width and height
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        self.setMinimumHeight(58)
        self.setMaximumHeight(400)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        layout = QVBoxLayout(self)
        # Top left and bottom right margins (16 below because triangles are included)
        layout.setContentsMargins(8, 8, 8, 16)
        self.label = QLabel(self)
        self.label.setStyleSheet('color: rgb(0,0,0);')
        layout.addWidget(self.label)
        self.setText(text)
        # Get screen height and width
        self._desktop = QApplication.instance().desktop()

    def setText(self, text):
        self.label.setText(text)

    def text(self):
        return self.label.text()

    def stop(self):
        self.hide()
        self.animationGroup.stop()
        self.close()

    def show(self):
        super(BubbleLabel, self).show()
        # Window start position
        startPos = QPoint(
            self._desktop.screenGeometry().width() - self.width() - 50,
            self._desktop.availableGeometry().height() - self.height())
        endPos = QPoint(
            self._desktop.screenGeometry().width() - self.width() - 50,
            self._desktop.availableGeometry().height() - self.height() * 3 - 5)
        self.move(startPos)
        # Initialization animation
        self.initAnimation(startPos, endPos)

    def initAnimation(self, startPos, endPos):
        # Transparency animation
        opacityAnimation = QPropertyAnimation(self, b"opacity")
        opacityAnimation.setStartValue(1.0)
        opacityAnimation.setEndValue(0.0)
        # Set the animation curve
        opacityAnimation.setEasingCurve(QEasingCurve.InQuad)
        opacityAnimation.setDuration(6000)  
        # Moving up animation
        moveAnimation = QPropertyAnimation(self, b"pos")
        moveAnimation.setStartValue(startPos)
        moveAnimation.setEndValue(endPos)
        moveAnimation.setEasingCurve(QEasingCurve.InQuad)
        moveAnimation.setDuration(7000)  
        # Parallel animation group (the purpose is to make the two animations above simultaneously)
        self.animationGroup = QParallelAnimationGroup(self)
        self.animationGroup.addAnimation(opacityAnimation)
        self.animationGroup.addAnimation(moveAnimation)
        # Close window at the end of the animation
        self.animationGroup.finished.connect(self._close)
        self.animationGroup.start()

    def _close(self):
        self.close()

    def paintEvent(self, event):
        super(BubbleLabel, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Antialiasing

        rectPath = QPainterPath()                     # Rounded Rectangle
        triPath = QPainterPath()                      # Bottom triangle

        height = self.height() - 8                    # Offset up 8
        rectPath.addRoundedRect(QRectF(0, 0, self.width(), height), 5, 5)
        x = self.width() - 20  # tripath crest 20px left from the farthest right end of the widget
        triPath.moveTo(x - 10, height)                     # Move to the bottom horizontal line 4/5
        # Draw triangle
        triPath.lineTo(x + 6, height + 8)
        triPath.lineTo(x + 12, height)

        rectPath.addPath(triPath)                     # Add a triangle to the previous rectangle

        # Border brush
        painter.setPen(QPen(self.BorderColor, 1, Qt.SolidLine,
                            Qt.RoundCap, Qt.RoundJoin))
        # Background brush
        painter.setBrush(self.BackgroundColor)
        # Draw shape
        painter.drawPath(rectPath)
        # Draw a line on the bottom of the triangle to ensure the same color as the background
        painter.setPen(QPen(self.BackgroundColor, 1,
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(x, height, x + 12, height)

    def windowOpacity(self):
        return super(BubbleLabel, self).windowOpacity()

    def setWindowOpacity(self, opacity):
        super(BubbleLabel, self).setWindowOpacity(opacity)

    # Since the opacity property is not in QWidget, you need to redefine one
    opacity = pyqtProperty(float, windowOpacity, setWindowOpacity)


class MainWindow(QMainWindow):

    #System tray icons.
    #Will initialize in the constructor.
    tray_icon = None
    notify_saved_message = ""
 
    # Override the class constructor
    def __init__(self, *args, **kwargs):
        # Be sure to call the super class method
        #QMainWindow.__init__(self)
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.setMinimumSize(QSize(410, 500))             # Set sizes
        self.setWindowTitle("Infinitrix Desktop App")  # Set a title

        self.web = WebEngineView()
        self.web.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        #call to allow audio and camera
        page = WebEnginePage(self.web)
        self.web.setPage(page)

        #Load bitrix24 url
        self.web.load(QUrl(CheckConfig.app_url))
        self.setCentralWidget(self.web)
 
        # Adding an icon
        if QFile.exists('/usr/share/pixmaps/infinitrix.png'):
            icon = QIcon("/usr/share/pixmaps/infinitrix.png")
            self.setWindowIcon(icon)
        else:
            icon = QIcon("infinitrix.png")
            self.setWindowIcon(icon)

        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip('Infinitrix Desktop App')
 
        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''

        def app_about(self):
            app_about_msg = QMessageBox(
                self,
                "About Infinitrix",
                "<p>An open source Bitrix24 messenger client,</p>"
                "<p>Powered by Python, PyQt5 and <a href=\"https://hoster.by\">HOSTER.BY</a> team</p>"
                "<p>Engineering:</p>"
                "<p>&nbsp;<a href=\"https://github.com/smallcms/\">smallcms</a></p>"
                "<p>Graphics:</p>"
                "<p>&nbsp;<a href=\"https://github.com/mashokk\">mashokk</a></p>"
                "<p>Testing:</p>"
                "<p>&nbsp;Internal team of HOSTER.BY</p>"
                "<p>Thanks to:</p>"
                "<p><a href=\"https://github.com/892768447\">ヽoo悾絔℅o。</a> for BubbleLabel notifications</p>",
            )
            app_about_msg.setIcon(QMessageBox.Information)
            x = app_about_msg.exec_()

        def app_logout():
            QWebEngineProfile.defaultProfile().cookieStore().deleteAllCookies()
            self.web.load(QUrl(CheckConfig.app_url))

        def quit_total():
                print("quit")
                #app.quit()
                del self.web
                del self.tray_icon
                quit()
                print("sys quit")
                sys.exit(app.exec_())


        about_action = QAction("About", self)
        settings_action = QAction("Settings", self)
        logout_action = QAction("Logout", self)
        show_action = QAction("Show", self)
        hide_action = QAction("Hide", self)
        quit_action = QAction("Exit", self)
        about_action.triggered.connect(app_about)
        settings_action.triggered.connect(self.show_settings_window)
        logout_action.triggered.connect(app_logout)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(quit_total)
        tray_menu = QMenu()
        tray_menu.addAction(about_action)
        tray_menu.addAction(settings_action)
        tray_menu.addAction(logout_action)
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        # Add the double clicked behavior
        def window_show():
            self.show()
            self.raise_()

        def on_tray_activated(reason):
            if reason == QtWidgets.QSystemTrayIcon.Context:
                return

            if self.isVisible():
                self.hide()

            elif reason == QtWidgets.QSystemTrayIcon.Trigger:
                window_show()

        self.tray_icon.activated.connect(on_tray_activated)
        # Add the double clicked behavior

        #show tray icon
        self.tray_icon.show()

        if CheckConfig.ini_contents['main']['url'] == '':
            self.show_settings_window()
        else:
            #show MainWindow, resize to 401x501 (bug in QT5 with resizing)
            #now commented, incorrect size in Linux
            #self.resize(411, 501)
            self.showMaximized()
            self.web.page().loadFinished.connect(self.run_js_start)

        #Fix maximized window width (not elegant solution)
        #QTimer.singleShot(5000, lambda: self.web.page().runJavaScript('window.location.reload(false);'))

        #Poller to check notifications
        timer = QTimer(self)
        timer.timeout.connect(self.run_js_callback)
        timer.start(1000)


    # MainWindow functions

    #Restart function
    def restart():
        return QApplication.exit( app_exit_code )

    # Override closeEvent, to intercept the window closing event
    # The window will be closed only if there is no check mark in the check box
    def closeEvent(self, event):
        if CheckConfig.ini_contents.has_option("main", "closetotray"):
            if CheckConfig.ini_contents['main']['closetotray'] == '1':
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "Infinitrix",
                    "Infinitrix was minimized to Tray",
                    QSystemTrayIcon.Information,
                    10000
                )
            else:
                event.accept()
                print("quit")
                #app.quit()
                del self.web
                del self.tray_icon
                quit()
                print("sys quit")
                sys.exit(app.exec_())

    #Show settings window
    def show_settings_window(self):
        #Settings window defininition
        self.settings_window = ConfigWindow()
        self.settings_window.show()


    #Javascript at start app
    def run_js_start(self):
        js_string = '''

        var countredirect = 0;

        var interval = setInterval(function () {
            addElement();
            clearInterval(interval);
        }, 1000);

        var intervalredirect = setInterval(function () {
            tryRedirect();
            countredirect++;
            if (countredirect >= 10) {
                clearInterval(intervalredirect);
            }
        }, 1000);

        function tryRedirect() {
            if (window.location.href.indexOf("/stream/") > -1) {
                window.location.replace(window.location.origin + '/desktop_app/?IFRAME=Y');
            }
        }

        function addElement() {
            var helloClasses = document.getElementsByClassName("bx-messenger-box-hello");
            if (helloClasses.length > 0) {
                helloClasses[0].innerHTML = "Welcome to Infinitrix!";
                helloClasses[0].insertAdjacentHTML('beforeend', '<div><span style="font-size: x-small;">Powered by Python, PyQt5 and HOSTER.BY team<span></div>');
            }

        }
        '''

        self.web.page().runJavaScript(js_string)

    #Javascript with callback to check notifications
    def run_js_callback(self):
        js_string = '''
       elements_infinitrix = document.getElementsByClassName('bx-notifier-item-content');
       data = [].map.call(elements_infinitrix, elem_infinitrix => elem_infinitrix.innerHTML);
        '''
        self.web.page().runJavaScript(js_string , self.js_callback)

    def js_callback(self, result):
        global notify_saved_message
        notify_str = result
        if notify_str:
             notify_message = notify_str[-1]
             if notify_message != self.notify_saved_message:
                 self.notify_saved_message = notify_message
                 notify_message = notify_message.replace("</span>", "</span> \n")
                 def strip_html(text):
                     parts = []
                     parser = HTMLParser()
                     parser.handle_data = parts.append
                     parser.feed(text)
                     return ''.join(parts)
                 notify_message_html = strip_html(notify_message)

                 msg = notify_message_html.strip()
                 if not msg:
                     return
                 if CheckConfig.ini_contents.has_option("main", "sysnotify"):
                     if CheckConfig.ini_contents['main']['sysnotify'] == '1':
                         self.tray_icon.showMessage(
                             "Infinitrix",
                             strip_html(msg),
                             QSystemTrayIcon.Information,
                             5000
                             )
                     else:
                         if hasattr(self, "_blabel"):
                             self._blabel.stop()
                             self._blabel.deleteLater()
                             del self._blabel
                         self._blabel = BubbleLabel()
                         self._blabel.setText(msg)
                         self._blabel.show()


class WebEngineView(QWebEngineView):
    windowList = []

 
if __name__ == "__main__":
    app_exit_code = -123456781
    exit_code = 0
    while True:
        try:
            app = QApplication(sys.argv)
        except RuntimeError:
            app = QCoreApplication.instance()
        app.setApplicationName("infinitrix")
        app.setDesktopFileName("infinitrix")
        CheckConfig()
        mainwindow=MainWindow()
        exit_code = app.exec_()
        del app
        os.execl(sys.executable, 'python', __file__, *sys.argv[1:])
        if exit_code != app_exit_code:
            break 
    del app
    sys.exit(app.exec_())
