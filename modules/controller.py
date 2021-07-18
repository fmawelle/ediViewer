import sys

import modules.model.db_connection as model
import modules.view.edi_viewer as view
from modules.utility import Utility
from modules.model.transaction import Transaction
from modules.model.segment import Segment


class EdiViewerController(model.Connection, view.ApplicationWindow):
    def __init__(self):
        self._model = model.Connection
        self._view = view.ApplicationWindow
        self._view.__init__(self, parent=None)
        self._model.__init__(self)

    def start_application(self):
        self.show()
        sys.exit(self.app.exec())

    def load_transactions(self, filename, transaction_name, contains):
        self.transaction_list_widget.clear()
        self.transaction_search_result_cnt = 0
        for transaction in self._model.get_transaction_list(self, filename, transaction_name, contains):
            # print(transaction)
            self.transaction_search_result_cnt += 1
            self.transaction_list_widget.insertItem(transaction[0] - 1, str(transaction[0]) + '. ' + transaction[1])
            self.transaction_list = []
        self.transaction_list_widget.setMaximumWidth(self.transaction_list_widget.sizeHintForColumn(0))
        self.central_grid_layout.addWidget(self.transaction_list_widget, 1, 1)

    def load_file(self, file_path, filename):
        file = open(file_path, 'r')
        self.current_file_name = filename
        segment_object = Segment()
        transaction = Transaction()
        # ql_connection = Connection()
        self._model.delete_old_rows(self, [filename])
        add_line = False
        new_transaction = []
        transaction_count = 0
        uncommitted_transactions = 0
        values = []
        transaction_details = []
        segment_id_number = 0
        delimiter = ''
        terminator = ''
        isa_header = ''
        gs_header = ''
        starting_start_transact = 0
        ge_trailer = ''
        try:
            for line in file:
                if line != '\n':
                    if line[0:3] == 'ISA':
                        delimiter = line[3:4]
                        terminator = line[len(line) - 2:len(line)]

                    if not delimiter:
                        Utility.show_error('Invalid File', 'The file selected is not currently supported')
                        break

                    # print(line[0:2])
                    segment_object.get_elements(line, delimiter, terminator)
                    # Header info
                    if segment_object.segment_id == 'ISA' or segment_object.segment_id == 'GS':
                        if segment_object.segment_id == 'ISA':
                            isa_header = line
                            starting_start_transact = transaction_count + 1
                        else:
                            gs_header = line

                    # footer info
                    if segment_object.segment_id == 'GE' or segment_object.segment_id == 'IEA':
                        if segment_object.segment_id == 'IEA':  # end of section
                            iea_trailer = line
                            while starting_start_transact <= transaction_count:
                                self.trailer.append([filename, ge_trailer, starting_start_transact])
                                self.trailer.append([filename, iea_trailer, starting_start_transact])
                                starting_start_transact += 1
                            # insert header into database
                            # insert footer into db
                        else:
                            ge_trailer = line

                    # start of new transaction
                    if segment_object.segment_id == 'ST':
                        segment_id_number = 0
                        transaction_count += 1  # increment number of transactions
                        self.header.append([filename, isa_header, transaction_count])
                        self.header.append([filename, gs_header, transaction_count])
                        add_line = True

                    if add_line:
                        new_transaction.append(line)
                        segment_id_number += 1
                        transaction_dtl_row = [filename, transaction_count, segment_id_number, line]
                        # print(segment_id_number)

                        # print(transaction_dtl_row)
                        transaction_details.append(transaction_dtl_row)
                    if segment_object.segment_id == 'SE':
                        add_line = False

                        # print(line)
                        complete = transaction.process_transaction(new_transaction, delimiter, terminator)
                        # complete = False
                        new_transaction = []
                        # print(complete)
                        if complete:
                            if transaction.identification != '':
                                uncommitted_transactions += 1
                                value = [filename, transaction_count, transaction.identification]
                                values.append(value)
                                if uncommitted_transactions % 100 == 0:
                                    uncommitted_transactions = 0
                                    self._model.insert_transaction(self, values)
                                    self._model.insert_transaction_details(self, 1, transaction_details)
                                    values = []
                                    transaction_details = []
                                # update count of loaded transactions
                                self.update_transaction_list_label(str(transaction_count))
                            else:
                                temp = []
                                for t in transaction_details:
                                    if t[1] != transaction_count + 1:
                                        temp.append(t)
                                transaction_details = temp.copy()
                        else:
                            temp = []
                            for t in transaction_details:
                                if t[1] != transaction_count:
                                    temp.append(t)
                            transaction_details = temp.copy()
                        transaction = Transaction()  # create new transaction object

                        percent_completed = transaction_count
                        # if percent_completed >= 99:
                        percent_completed = int((percent_completed / 100) * 50)
                        # print(str(percent_completed) + ' - ' + str(transaction_count))
                        self.progress_bar.setValue(percent_completed)
            if uncommitted_transactions > 0:
                self._model.insert_transaction(self, values)
                self._model.insert_transaction_details(self, 1, transaction_details)
            self.files_loaded.append([filename, transaction_count])
            self.progress_bar.setValue(100)
            self.progress_bar.reset()
            self.remove_progress_bar()
        except Exception as e:
            Utility.show_error('Error Loading File', e)

    def get_transaction_detail(self):
        details = [['Looks like we had trouble loading data for ' + self.current_transaction_name]]
        try:
            data = self._model.get_transaction_detail(self, self.current_file_name, self.current_transaction_id)
            if data:
                details = []
                #   header
                for h in self.header:
                    if h[0] == self.current_file_name and int(h[2]) == int(self.current_transaction_id):
                        details.append([h[1]])

                # transaction body
                for segment in data:
                    details.append(segment)

                # footer/trailer
                for f in self.trailer:
                    if f[0] == self.current_file_name and int(self.current_transaction_id) == int(f[2]):
                        details.append([f[1]])
            return details
        except Exception as e:
            Utility.show_error('Details', e)

    def check_for_updates(self):
        try:
            if self.hasChanges:
                self.extract_change_dialog()
        except Exception as e:
            Utility.show_error('Checking Updates' , e)

    def reload_transaction_dtl(self, current_item, item):
        try:
            self._view.reload_transaction_dtl(self, current_item, item)
            self.transaction_detail = self._model.get_transaction_detail(self, self.current_file_name,
                                                                         self.current_transaction_id)
            self._view.load_transaction_details(self)
        except Exception as e:
            Utility.show_error('Transaction Click', e)

    def update_current_theme(self, selection):
        try:
            self._view.update_current_theme(self, selection)
            theme_id = self.themes.index(selection)
            self._model.update_current_theme(self, theme_id)
        except Exception as e:
            Utility.show_error('Theme Selection Error', e)

    def get_user_theme(self):
        try:
            # connection = Connection()
            theme = self._model.get_current_theme(self)
            if theme[0] == 0:
                self.default_theme.setIcon(Utility.get_icon('check-mark.svg'))
            elif theme[0] == 1:
                self.dark_theme.setIcon(Utility.get_icon('check-mark.svg'))
            return theme[1]  # returns associated stylesheet
        except Exception as e:
            Utility.show_error('User Theme Error', e)
