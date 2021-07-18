import PyQt5.QtWidgets as QtW
import PyQt5.QtGui as qGui
import os
import webbrowser


class Utility:

    @staticmethod
    def is_empty(items):
        if items:
            return False
        else:
            return True

    @staticmethod
    def read_file(file_path):
        with open(file_path, 'rb') as f:
            return f.read()

    @staticmethod
    def show_error(context, message):
        try:
            error_box = QtW.QMessageBox()
            error_box.setIcon(QtW.QMessageBox.Critical)
            error_box.setText(context)
            error_box.setInformativeText(str(message))
            error_box.setIcon(Utility.get_icon('app_icon.gif'))
            error_box.setWindowTitle('Error')
            error_box.exec()
        except Exception as e:
            print(str(e))

    @staticmethod
    def show_message(context, message):
        try:
            message_box = QtW.QMessageBox()
            message_box.setIcon(QtW.QMessageBox.Information)
            message_box.setText(context)
            message_box.setInformativeText(str(message))
            message_box.setWindowTitle('Info')
            message_box.exec()
        except Exception as e:
            print(str(e))

    @staticmethod
    def get_icon(icon_name):
        try:
            icon = os.path.join(os.getcwd(), 'icons', icon_name)
            return qGui.QIcon(icon)
        except Exception as e:
            Utility.show_error('Error Creating Icon', e)

    @staticmethod
    def open_in_browser(url):
        webbrowser.open(url)
