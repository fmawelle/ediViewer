import os
import sqlite3
from sqlite3 import Error
from modules.utility import Utility


class Connection:
    conn = None

    def create_connection(self):
        database_absolute_path = ''
        connection_successful = False
        conn = None
        databases_dir = os.path.join(os.getcwd(), 'databases')
        try:
            if os.path.exists(databases_dir):  # dir exists
                database_absolute_path = os.path.join(databases_dir, 'data.db')
                if os.path.exists(database_absolute_path):  # perform sql operations
                    # print(database_absolute_path + ' exists.')
                    connection_successful = True
                else:  # create database and perform sql operations
                    # print(database_absolute_path + ' does NOT exist.')
                    print('Creating one')
                    connection_successful = True
            else:
                print('The path does not exist')
                connection_successful = False
            if connection_successful:
                self.conn = sqlite3.connect(database_absolute_path)
                return self.conn
        except Error as e:
            Utility.show_error('Database Connection', e)  # print(e)

    def insert_transaction(self, values):
        try:
            self.conn = self.create_connection()
            qry = '''INSERT INTO TRANSACTION_LIST(FILE_NAME, TRANSACTION_ID, NAME) VALUES(?, ?, ?)'''
            cursor = self.conn.cursor()
            # for value in values:
            cursor.executemany(qry, values)
            self.conn.commit()
            # print(values)
            # self.commit()
        except Error as e:
            Utility.show_error('Database Error', e)
            print(e)
        finally:
            self.conn.close()

    def insert_transaction_details(self, table, transaction_dtls):
        ''' Acceptable values 0 = header, 1 = details, 2 = trailer '''
        if table == 0:
            table = 'TRANSACTION_HDR'
        elif table == 1:
            table = 'TRANSACTION_DTL'
        else:
            table = 'TRANSACTION_TRL'

        try:
            self.conn = self.create_connection()
            qry = '''INSERT INTO {} (FILE_NAME, TRANSACTION_ID, SEGMENT_ID, SEGMENT) VALUES(?, ?, ?, ?)'''.format(table)
            # print(qry)
            cursor = self.conn.cursor()
            # for value in values:
            # qry.format('TRANSACTION_DTL')
            cursor.executemany(qry, transaction_dtls)
            self.conn.commit()
        except Error as e:
            Utility.show_error('Database Insert', e)
        finally:
            self.conn.close()

    def delete_old_rows(self, file_name):
        try:
            self.conn = self.create_connection()
            qry = '''DELETE FROM TRANSACTION_LIST WHERE FILE_NAME = ?'''
            cursor = self.conn.cursor()
            cursor.execute(qry, file_name)
            qry = '''DELETE FROM TRANSACTION_DTL WHERE FILE_NAME = ?'''
            cursor.execute(qry, file_name)
            qry = '''DELETE FROM TRANSACTION_TRL WHERE FILE_NAME = ?'''
            cursor.execute(qry, file_name)
            qry = '''DELETE FROM TRANSACTION_HDR WHERE FILE_NAME = ?'''
            cursor.execute(qry, file_name)
            self.conn.commit()
            # print('Successfully deleted old rows.')
        except Error as e:
            Utility.show_error('Database delete', e)
        finally:
            self.conn.close()

    def get_transaction_list(self, file_name, transaction_name, contains):
        try:
            self.conn = self.create_connection()
            cursor = self.conn.cursor()
            qry = '''SELECT TRANSACTION_ID , NAME FROM TRANSACTION_LIST WHERE FILE_NAME = ?'''
            name_only_qry = '''SELECT TL.TRANSACTION_ID, TL.NAME 
                            FROM TRANSACTION_LIST TL WHERE TL.FILE_NAME = ? AND UPPER(TL.NAME) LIKE UPPER(?) '''
            transaction_only_qry = ''' SELECT TL2.TRANSACTION_ID, TL2.NAME FROM TRANSACTION_LIST TL2 
                        WHERE TL2.FILE_NAME = ? AND TL2.TRANSACTION_ID IN (SELECT TD.TRANSACTION_ID 
                        FROM TRANSACTION_DTL TD 
                        WHERE TD.FILE_NAME = TL2.FILE_NAME AND TD.TRANSACTION_ID = TL2.TRANSACTION_ID
                        AND UPPER(TD.SEGMENT) LIKE UPPER(?) )'''

            if (not transaction_name) and (not contains):  # most common operation
                cursor.execute(qry, [file_name])
            elif transaction_name and contains:
                search_name = Connection.create_search_string(transaction_name)
                transaction_content = Connection.create_search_string(contains)

                qry = name_only_qry + ' UNION ' + transaction_only_qry
                # print(qry)
                cursor.execute(qry, [file_name, search_name, file_name, transaction_content])
            elif transaction_name:
                search_name = Connection.create_search_string(transaction_name)
                cursor.execute(name_only_qry, [file_name, search_name])
            else:
                transaction_content = Connection.create_search_string(contains)
                cursor.execute(transaction_only_qry, [file_name, transaction_content])
            return cursor.fetchall()
        except Error as e:
            Utility.show_error('Database Transaction List', e)
            return []  # return empty list
        finally:
            self.conn.close()

    def get_transaction_detail(self, file_name, transact_id):
        try:
            self.conn = self.create_connection()
            qry = '''SELECT SEGMENT FROM TRANSACTION_DTL WHERE FILE_NAME = ? 
            AND TRANSACTION_ID = ? ORDER BY SEGMENT_ID ASC'''
            cursor = self.conn.cursor()
            cursor.execute(qry, [file_name, transact_id])
            return cursor.fetchall()
        except Error as e:
            Utility.show_error('Database Error', e)
            return []  # return empty detail list
        finally:
            self.conn.close()

    def header_trailer_rows(self, details):
        try:
            self.conn = self.create_connection()
            qry = '''INSERT INTO TRANSACTION_HDR(FILE_NAME, TRANSACTION_ID, SEGMENT_ID, SEGMENT) VALUES(?, ?, ?, ?)'''
            cursor = self.conn.cursor()
            # for value in values:
            cursor.executemany(qry, details)
            self.conn.commit()
        except Error as e:
            Utility.show_error('Database Error', e)
            print(e)
        finally:
            self.conn.close()

    def update_current_theme(self, theme_id):
        try:
            self.conn = self.create_connection()
            qry = '''UPDATE THEME_TBL SET IS_SELECTED = 0'''
            cursor = self.conn.cursor()
            cursor.execute(qry)
            qry = '''UPDATE THEME_TBL SET IS_SELECTED = 1 WHERE THEME_ID = ?'''
            cursor.execute(qry, [theme_id])
            self.conn.commit()
        except Exception as e:
            Utility.show_error('Updating Theme', e)
        finally:
            self.conn.close()

    def get_current_theme(self):
        try:
            self.conn = self.create_connection()
            qry = '''SELECT THEME_ID, THEME FROM THEME_TBL WHERE IS_SELECTED = 1'''
            cursor = self.conn.cursor()
            cursor.execute(qry)
            return cursor.fetchone()
        except Exception as e:
            Utility.show_error('Error Getting Theme', e)
        finally:
            self.conn.close()

    @staticmethod
    def create_search_string(search_string):
        if search_string:
            try:
                index = search_string.find('%')
                if index < 0:  # no wild card, add one to search string
                    _search_string = search_string.split()
                    new_search_string = '%'
                    for search_item in _search_string:
                        new_search_string += search_item + '%'
                    return new_search_string
                else:   # search as typed
                    return search_string
            except Exception as e:
                Utility.show_error('String Concat Error', e)
        return ''
