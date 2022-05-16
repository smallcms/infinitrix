import sys
import os
import time
from PyQt5.Qt import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, \
    QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5 import QtCore, QtWidgets

#
# Deplist Ubuntu: sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine
# Deplist Fedora: sudo dnf install python3-qt5 python3-qt5-webengine
# Deplist openSUSE sudo zypper install python3-qt5 python3-qtwebengine-qt5
# Deplist ArchLinux: sudo pacman -S python-pyqt5 python-pyqt5-webengine
#

app_url = ('https://YOUR_BITRIX_URL/desktop_app/?IFRAME=Y')

HTML = """
<!DOCTYPE html>
<html>
<head>
</head>
<body>

<h1>Loading...</h1>
<p>Please, wait</p>

</body>
</html>
"""

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

class MainWindow(QMainWindow):

    #System tray icons.
    #Will initialize in the constructor.
    tray_icon = None
 
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

        #self.web.setHtml(HTML)

        #web.page().profile().setHttpUserAgent(
        #    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.81 BitrixDesktop/13.0.24.666 Safari/537.36"
        #)

        self.web.load(QUrl(app_url))
        self.setCentralWidget(self.web)
 
        # Adding an icon
        icon = QIcon("icon.png")
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
        def app_logout():
            QWebEngineProfile.defaultProfile().cookieStore().deleteAllCookies()
            self.web.load(QUrl(app_url))

        def quit_total():
                print("quit")
                #app.quit()
                del self.web
                quit()
                print("sys quit")
                sys.exit(app.exec_())


        logout_action = QAction("Logout", self)
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        logout_action.triggered.connect(app_logout)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(quit_total)
        tray_menu = QMenu()
        tray_menu.addAction(logout_action)
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        # Add the double clicked behavior
        def window_show():
            self.show()
            self.raise_()
            #self.requestActivate()

        def on_tray_activated(reason):
            if reason == QtWidgets.QSystemTrayIcon.Context:
                return

            if self.isVisible():
                self.hide()

            elif reason == QtWidgets.QSystemTrayIcon.Trigger:
                window_show()

        self.tray_icon.activated.connect(on_tray_activated)
        # Add the double clicked behavior

        self.tray_icon.show()
        self.showMaximized()
        self.web.page().loadFinished.connect(self.run_js_start)
        #self.web.page().loadFinished.connect(self.run_js_callback)
        #QMessageBox.information (self, "hint", str ("The window will be closed only if there is no check mark in the check box"))

        #Fix maximized window width
        #QTimer.singleShot(5000, lambda: self.web.page().runJavaScript('window.location.reload(false);'))

        #Poller to check notifications
        timer = QTimer(self)
        timer.timeout.connect(self.run_js_callback)
        timer.start(1000)


    # Override closeEvent, to intercept the window closing event
    # The window will be closed only if there is no check mark in the check box
    def closeEvent(self, event):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Infinitrix",
                "Infinitrix was minimized to Tray",
                QSystemTrayIcon.Information,
                2000
            )

    #Javascript at start app
    def run_js_start(self):
        js_string = '''

        if (window.location.href.indexOf("/stream/") > -1) {
            window.location.replace(window.location.origin + '/desktop_app/?IFRAME=Y');
          }

        var interval = setInterval(function () {
            addElement();
            clearInterval(interval);
        }, 1000);

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
        //BX.PopupWindowManager.isPopupExists();
        //Math.floor(Date.now() / 1000);

       //elements_infinitrix = document.getElementsByClassName('popup-window');
       //elements_infinitrix = document.getElementsByClassName('bx-notifier-item-content');
       elements_infinitrix_date = document.getElementsByClassName('bx-notifier-item-date');
       elements_infinitrix_name = document.getElementsByClassName('bx-notifier-item-name');
       elements_infinitrix_text = document.getElementsByClassName('bx-notifier-item-text');
       [[].map.call(elements_infinitrix_date, elem_infinitrix_date => elem_infinitrix_date.innerHTML),[].map.call(elements_infinitrix_name, elem_infinitrix_name => elem_infinitrix_name.innerHTML),[].map.call(elements_infinitrix_text, elem_infinitrix_text => elem_infinitrix_text.innerHTML)];

        '''
        self.web.page().runJavaScript(js_string , self.js_callback)

    def js_callback(self, result):
        notify_str = str(result)
        notify_array = []
        notify_brackets=notify_str.replace("[[","").replace("]]","")
        for notify_line in notify_brackets.split('], ['):
            notify_row =list(map(str,notify_line.split(", ")))
            notify_array.append(notify_row)
        print("PyArray:", notify_array)

        print("js: infinitrix callback is ",notify_str)
        #QMessageBox.information (self, "Hint", str(result))
        #if str(result) != '[]':
                #self.tray_icon.showMessage(
                        #"Infinitrix",
                        #str(result),
                        #QSystemTrayIcon.Information,
                        #2000
                    #)


class WebEngineView(QWebEngineView):
    windowList = []

 
if __name__ == "__main__":
    import sys
 
    app = QApplication(sys.argv)
    app.setApplicationName("infinitrix")
    mw = MainWindow()
    mw.show()
    #app.quit()
    del mw
    sys.exit(app.exec())
