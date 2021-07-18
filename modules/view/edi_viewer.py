import os
import sys

import PyQt5.QtWidgets as qWidget
import PyQt5.QtCore as qCore

from modules.utility import Utility


class ApplicationWindow(qWidget.QMainWindow):
    app = qWidget.QApplication([])  # no cmdline args accepted
    transaction_list = []
    transaction_detail = []
    current_transaction_id = 0
    current_transaction_name = ''
    current_file_name = ''
    hasChanges = False
    file_options = ['Open File', 'Open Folder', 'Exit Viewer', 'Exit']
    themes = ['Light Blue', 'Dark Rye']
    files_loaded = []
    header = []
    trailer = []
    file_widget = qWidget.QListWidget()
    last_file_row = 0
    central_widget = qWidget.QWidget()
    transaction_list_widget = qWidget.QListWidget()
    transaction_list_label = qWidget.QLabel('Transaction List')
    transaction_detail_label = qWidget.QLabel('Detail Area')
    transaction_detail_text = qWidget.QPlainTextEdit()
    open_file_button = qWidget.QPushButton(file_options[0])
    exit_button = qWidget.QPushButton(file_options[2])
    search_button = qWidget.QPushButton('Search File')
    extract_file_button = qWidget.QPushButton('Extract to File')
    extract_button_box = qWidget.QDialogButtonBox()
    extract_dialog_box = qWidget.QDialog()
    progress_bar = qWidget.QProgressBar()
    window = qWidget.QGridLayout()
    test_layout = qWidget.QVBoxLayout()
    default_theme = qWidget.QAction()
    dark_theme = qWidget.QAction()
    home_directory = qCore.QDir.homePath()
    preferred_directory = home_directory
    modal_search_window = qWidget.QDialog()
    name_line_edit = qWidget.QLineEdit()
    transaction_line_edit = qWidget.QLineEdit()
    transaction_search_result_cnt = 0

    central_grid_layout = qWidget.QGridLayout()

    def __init__(self, parent=None):
        super().__init__(parent)
        # title
        self.setWindowTitle('EDI File Viewer')
        self.setWindowIcon(Utility.get_icon('edi_app_icon.png'))
        self.setContentsMargins(0, 0, 0, 5)
        self.setCentralWidget(self.central_widget)

        self.central_widget.setLayout(self.central_grid_layout)
        self.setGeometry(350, 200, 900, 400)

        # menu and tool bars
        self.create_menu_bar()
        self.create_tool_bar()

        # self.transaction_detail_text.setReadOnly(True)
        self.transaction_detail_text.setLineWrapMode(qWidget.QPlainTextEdit.NoWrap)
        self.transaction_detail_text.setBackgroundVisible(True)
        self.central_grid_layout.addWidget(self.transaction_detail_text, 1, 2)
        self.progress_tool = qWidget.QToolBar('Status')

        # event listeners
        self.set_event_listeners()

        # set stylesheet
        self.app.setStyleSheet(self.read_file('styles', self.get_user_theme()))
        # self.transaction_detail_text.appendHtml(self.read_file('html', 'instructions.html'))

    def set_event_listeners(self):
        try:
            self.file_widget.itemClicked.connect(self.on_file_list_single_click)
            self.file_widget.currentItemChanged.connect(self.on_file_list_click)
            self.file_widget.itemDoubleClicked.connect(self.create_search_dialog)
            # self.transaction_widget.itemClicked.connect(self.on_transaction_click)
            self.transaction_list_widget.currentItemChanged.connect(self.reload_transaction_dtl)
            self.search_button.clicked.connect(self.create_search_dialog)
            self.transaction_list_widget.itemDoubleClicked.connect(self.extract_current_transaction)
            self.exit_button.clicked.connect(self.exit_application)
            self.extract_file_button.clicked.connect(self.extract_current_transaction)
            self.open_file_button.clicked.connect(self.open_file)
            self.extract_button_box.accepted.connect(self.extract_transaction)
            self.extract_button_box.rejected.connect(self.reload_transaction_dtl)
            self.transaction_detail_text.textChanged.connect(self.text_changed)
        except Exception as e:
            Utility.show_error('Event Listener Error', e)

    def extract_current_transaction(self):
        self.extract_dialog_box = qWidget.QDialog(self)
        self.extract_dialog_box.setWindowTitle('Extract File')
        dialog_buttons = qWidget.QDialogButtonBox.Ok | qWidget.QDialogButtonBox.Cancel
        self.extract_button_box = qWidget.QDialogButtonBox(dialog_buttons)
        self.extract_button_box.accepted.connect(self.extract_transaction)
        self.extract_button_box.rejected.connect(self.close_dialog_box)
        dialog_layout = qWidget.QVBoxLayout()
        dialog_layout.addWidget(self.extract_button_box)
        self.extract_dialog_box.setLayout(dialog_layout)
        self.extract_dialog_box.exec_()

    def text_changed(self):
        try:
            self.hasChanges = True
        except Exception as e:
            Utility.show_error('Error', e)

    def enable_context_buttons(self, state):
        self.search_button.setEnabled(state)
        self.extract_file_button.setEnabled(state)

    def reload_transaction_dtl(self, current_item, item):
        try:
            self.check_for_updates()
            if current_item is not None:
                self.current_transaction_id = current_item.text()[0:current_item.text().find('.')]
                self.current_transaction_name = current_item.text()[current_item.text().find('.')
                                                                    + 1:len(current_item.text()) - 1]
            self.enable_context_buttons(True)
        except Exception as e:
            Utility.show_error('Transaction Click', e)

    def create_search_dialog(self):
        try:
            self.modal_search_window = qWidget.QDialog()
            dialog_buttons = qWidget.QDialogButtonBox.Ok | qWidget.QDialogButtonBox.Cancel
            search_button_box = qWidget.QDialogButtonBox(dialog_buttons)
            self.modal_search_window.setWindowTitle('Search File')
            search_layout = qWidget.QFormLayout()
            # search_dialog = QtW.QInputDialog()
            instruction = qWidget.QLabel('Search in file ' + self.current_file_name)
            find_by_name_label = qWidget.QLabel('Name Contains:')
            self.name_line_edit = qWidget.QLineEdit()
            find_by_transaction_word_lbl = qWidget.QLabel('Transaction Contains: ')
            self.transaction_line_edit = qWidget.QLineEdit()

            # add rows
            search_layout.addRow(instruction)
            search_layout.addRow(find_by_name_label, self.name_line_edit)
            search_layout.addRow(find_by_transaction_word_lbl, self.transaction_line_edit)
            search_layout.addWidget(search_button_box)
            # search_dialog.
            # search_dialog.isSizeGripEnabled()
            self.modal_search_window.setLayout(search_layout)

            # local event listener
            search_button_box.accepted.connect(self.search_file)
            search_button_box.rejected.connect(self.modal_search_window.close)
            self.modal_search_window.exec_()
        except Exception as e:
            Utility.show_error('Search Error', e)

    def search_file(self):
        try:
            transaction_name = self.name_line_edit.text()
            contains = self.transaction_line_edit.text()

            if not transaction_name and not contains:
                Utility.show_message('Search Criteria Missing', 'Type Search Parameters or cancel the dialog')
            else:
                # Utility.show_message('Search Criteria Missing', 'Type Search Parameters or cancel the dialog')
                self.modal_search_window.close()
                self.clear_previous_transaction()
                self.load_transactions(self.current_file_name, transaction_name, contains)
                self.update_transaction_list_label(str(self.transaction_search_result_cnt)
                                                   + ' of ' + str(self.get_transaction_count(self.current_file_name)))
        except Exception as e:
            Utility.show_error('Search Error', e)

    def clear_previous_transaction(self):
        self.transaction_detail_text.clear()
        self.update_detail_display_label('')
        self.hasChanges = False

    def on_file_list_click(self, current_item, previous_item):
        try:
            if current_item is not None:
                # previous_item not being used
                self.current_file_name = current_item.text()
            self.enable_context_buttons(False)  # but enable search
            self.search_button.setEnabled(True)
            self.load_transactions(self.current_file_name, '', '')
            self.clear_previous_transaction()
            self.get_transaction_count(self.current_file_name)
            self.update_transaction_list_label(str(self.get_transaction_count(self.current_file_name)))
        except Exception as e:
            Utility.show_error('File Click', e)

    def on_file_list_single_click(self, current_item):
        self.on_file_list_click(current_item, '')
        self.extract_file_button.setEnabled(False)

    def create_menu_bar(self):
        try:
            menu_bar = qWidget.QMenuBar()
            menu_bar.setObjectName('tool_bar')
            # Creating menus using a QMenu object
            file_menu = qWidget.QMenu("&File", self)
            file_menu.addAction('Open File')  # .setIcon(Utility.get_icon('open_file_icon.svg'))
            file_menu.addAction('Exit')  # .setIcon(Utility.get_icon('exit_icon.png'))
            # menu_bar.addMenu(file_menu)
            self.menuBar().addMenu(file_menu)

            preferences_menu = qWidget.QMenu('&Preferences', self)
            themes_menu = qWidget.QMenu('Themes', self)
            self.default_theme = qWidget.QAction(self.themes[0], self)
            self.dark_theme = qWidget.QAction(self.themes[1], self)
            themes_menu.addAction(self.default_theme)
            themes_menu.addAction(self.dark_theme)
            preferences_menu.addMenu(themes_menu)
            self.menuBar().addMenu(preferences_menu)

            help_menu = qWidget.QMenu("&Help", self)
            help_menu.addAction('&Help')
            help_menu.addAction('About')

            # menu_bar.addMenu(help_menu)
            self.menuBar().addMenu(help_menu)

            file_menu.triggered.connect(lambda action: self.get_file_action(action.text()))
            preferences_menu.triggered.connect(lambda action: self.update_current_theme(action.text()))
            help_menu.triggered.connect(lambda action: self.show_help_option(action.text()))
        except Exception as e:
            Utility.show_error('Menu Widget Error', e)

    def get_file_action(self, file_action):
        try:
            index = self.file_options.index(file_action)
            if index == 0:  # Open file
                self.open_file()
            else:  # exit application
                self.exit_application()
        except ValueError as v:
            Utility.show_message('No Implementation', v)
        except Exception as e:
            Utility.show_error('File Action Error', e)

    def open_file(self):  # intention was to have a open folder option as well
        self.create_progress_bar()
        filename = qWidget.QFileDialog.getOpenFileName(self, 'Open file', self.preferred_directory, '')
        if filename[0]:
            self.add_file([filename[0]])
        self.remove_progress_bar()

    def add_file(self, file_list):
        try:
            for item in file_list:
                index = item.rfind('/')
                if index < 0:
                    index = item.rfind('\\')
                self.preferred_directory = item[0:index]
                self.current_file_name = item[index + 1:len(item)]
                if self.get_transaction_count(self.current_file_name) is None:
                    self.last_file_row += 1
                    self.update_file_list_widget()
                    self.load_file(item, self.current_file_name)
                self.load_transactions(self.current_file_name, '', '')
                # self.current_transaction_id = 1  # load the first transaction into the display area
                self.search_button.setEnabled(True)  # enable search file

        except Exception as e:
            Utility.show_error('Error Adding File', e)

    def save_to_file(self, filename):
        extract = open(filename, 'w')  # write anew
        details = self.transaction_detail_text.toPlainText()  # get details from the text editor
        extract.write(details)
        extract.close()

    def get_transaction_count(self, filename):
        for f_loaded in self.files_loaded:
            # print(f_loaded)
            if f_loaded[0] == filename:
                return f_loaded[1]

    def load_transaction_details(self):
        try:
            self.clear_previous_transaction()
            details = self.get_transaction_detail()
            i = 0
            while i < len(details):
                self.transaction_detail_text.appendPlainText(details.pop(i)[0])
                i += i
            detail_scrollbar = self.transaction_detail_text.verticalScrollBar()
            detail_scrollbar.setValue(0)  # move slider to the beginning of the transaction
            self.central_grid_layout.addWidget(self.transaction_detail_text, 1, 2)
            self.update_detail_display_label(self.current_file_name + ' > ' + self.current_transaction_name)
            self.hasChanges = False
        except Exception as e:
            Utility.show_error('Transaction Detail Error', e)

    def update_detail_display_label(self, label):
        try:
            self.window.removeWidget(self.transaction_detail_label)
            self.window.update()
            self.transaction_detail_label = qWidget.QLabel(label)
            self.transaction_detail_label.setObjectName('details_label')
            # self.window.addWidget(self.transaction_detail_label, 2, 2)
            self.central_grid_layout.addWidget(self.transaction_detail_label, 0, 2)
        except Exception as e:
            Utility.show_error('Display Header', e)

    def close_dialog_box(self):
        try:
            self.extract_dialog_box.close()
        except Exception as e:
            Utility.show_error('Dialog Box Error', e)

    def extract_transaction(self):
        try:
            extract_dialog = qWidget.QFileDialog(self)
            extract_dialog.setFileMode(qWidget.QFileDialog.Directory)
            extract_dialog.setAcceptMode(qWidget.QFileDialog.AcceptSave)
            filename = extract_dialog.getSaveFileName()
            filename = filename[0]
            if filename:
                self.save_to_file(filename)
            self.extract_dialog_box.close()
        except Exception as e:
            Utility.show_error('Transaction Extract Error', e)

    def create_tool_bar(self):
        try:
            # context buttons
            context_tool_bar = qWidget.QToolBar('Context Tool bar')
            context_tool_bar.setObjectName('context_buttons_toolbar')
            self.search_button.setObjectName('search_file_button')
            self.open_file_button.setIcon(Utility.get_icon('open_file_icon.svg'))
            self.open_file_button.setObjectName('open_file')
            context_tool_bar.addWidget(self.open_file_button)
            context_tool_bar.addSeparator().setObjectName('separator')
            self.search_button.setObjectName('search')
            self.search_button.setIcon(Utility.get_icon('search.png'))
            context_tool_bar.addWidget(self.search_button)
            context_tool_bar.addSeparator()
            self.extract_file_button.setIcon(Utility.get_icon('extract_file_icon.svg'))
            self.extract_file_button.setObjectName('extract')
            context_tool_bar.addWidget(self.extract_file_button)
            self.exit_button.setObjectName('exit')
            self.exit_button.setIcon(Utility.get_icon('exit_icon.png'))
            context_tool_bar.addSeparator()
            context_tool_bar.addWidget(self.exit_button)
            self.addToolBar(context_tool_bar)
            self.enable_context_buttons(False)
        except Exception as e:
            Utility.show_error('Context Button Error', e)

    def update_file_list_widget(self):
        try:
            file_label = qWidget.QLabel('Files  ')
            file_label.setObjectName('files_loaded_label')
            self.file_widget.insertItem(self.last_file_row, self.current_file_name)
            self.central_grid_layout.addWidget(file_label, 0, 0)
            self.central_grid_layout.addWidget(self.file_widget, 1, 0)
            self.file_widget.setMaximumWidth(self.file_widget.sizeHintForColumn(0))
        except Exception as e:
            Utility.show_error('File List Error', e)

    def update_transaction_list_label(self, new_label):
        try:
            # print(new_label)
            self.transaction_list_label.clear()
            self.transaction_list_label = qWidget.QLabel('Total Transactions: ' + str(new_label))
            self.transaction_list_label.setObjectName('transact_list_label')
            self.central_grid_layout.addWidget(self.transaction_list_label, 0, 1)
        except Exception as e:
            Utility.show_error('Transaction List Error', e)

    def remove_progress_bar(self):
        self.window.removeWidget(self.statusBar())

    def create_progress_bar(self):
        try:
            self.progress_tool = qWidget.QToolBar('Status')
            self.progress_tool.setContentsMargins(0, 0, 0, 0)
            self.progress_tool.setObjectName('progress_tool_bar')
            self.progress_bar = qWidget.QProgressBar(self)
            self.progress_bar.setObjectName('progress_bar')
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_tool.addWidget(self.progress_bar)
            self.statusBar().addWidget(self.progress_tool, 3)
        except Exception as e:
            Utility.show_error('Progress Bar Error', e)

    def extract_change_dialog(self):
        try:
            self.extract_dialog_box = qWidget.QDialog(self)
            self.extract_dialog_box.setWindowTitle('Extract to File')
            label = qWidget.QLabel()
            label.setText(
                'You made changes to ' + self.current_transaction_name +
                '. \n\n Would you like to extract it? '
                '\n\n Changes are never saved to the original file')
            dialog_buttons = qWidget.QDialogButtonBox.Ok | qWidget.QDialogButtonBox.Cancel
            self.extract_button_box = qWidget.QDialogButtonBox(dialog_buttons)
            self.extract_button_box.accepted.connect(self.extract_transaction)
            self.extract_button_box.rejected.connect(self.close_dialog_box)
            dialog_layout = qWidget.QVBoxLayout()
            dialog_layout.addWidget(label)
            dialog_layout.addWidget(self.extract_button_box)
            self.extract_dialog_box.setLayout(dialog_layout)
            self.extract_dialog_box.exec_()
            self.hasChanges = False
        except Exception as e:
            Utility.show_error('Extract Dialog', e)

    def update_current_theme(self, selection):
        try:
            message = 'You need to restart the application ' \
                      'for the Theme to be applied.'
            context = 'Requires Application Restart'
            Utility.show_message(context, message)
        except Exception as e:
            Utility.show_error('Theme Selection Error', e)

    def set_style_sheet(self, stylesheet):
        try:
            stylesheet = os.path.join(os.getcwd(), 'styles', stylesheet)
            # print(stylesheet)
            if os.path.exists(stylesheet):
                with open(stylesheet, 'r') as style:
                    stylesheet = style.read()
                    self.app.setStyleSheet(stylesheet)
        except Exception as e:
            Utility.show_error('Error Styling', e)

    def show_help_option(self, action):
        try:
            if action == '&Help':
                self.show_instructions()
            elif action == 'About':
                self.show_about()
            else:
                Utility.show_message('Unimplemented Action',action + ' has not been implemented yet.')
        except Exception as e:
            Utility.show_error('Help Option Error',e)

    @staticmethod
    def show_about():
        msg = '''\nEdi Viewer Version 1.5.0\n
        Thank you for using EdiViewer.\n
        The software is provided "as is", 
        without warranty of any kind, 
        express or implied, including but not 
        limited to the warranties of merchantability, 
        fitness for a particular purpose and non-infringement. 
         
        That being said, you can visit the repository @ for more information
        or contact the publisher of the software @ email address'''
        try:
            Utility.show_message('About EdiViewer', msg)
        except Exception as e:
            Utility.show_error('Error => About', e)

    @staticmethod
    def show_instructions():
        try:
            url = os.path.join(os.getcwd(), 'html', 'instructions.html')
            # print(url)
            Utility.open_in_browser(url)
        except Exception as e:
            Utility.show_error('Error Opening Page', e)

    @staticmethod
    def read_file(location, filename):
        try:
            file = os.path.join(os.getcwd(), location, filename)
            # print(file)
            if os.path.exists(file):
                with open(file, 'r') as file_out:
                    file = file_out.read()
                return file
            return file
        except Exception as e:
            Utility.show_error('Error opening ' + file, e)

    @staticmethod
    def exit_application():
        sys.exit()
