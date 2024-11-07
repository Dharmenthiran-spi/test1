import json
import os
import re
import sqlite3
import threading
from datetime import datetime

connection = sqlite3.connect("ChemDB.db")


def create_connection(database_file):
    """Create a connection to the SQLite database."""
    try:
        connection = sqlite3.connect(database_file)
        print(f"Connected to SQLite database: {database_file}")
        return connection
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None


def close_connection(connection):
    """Close the database connection."""
    if connection:
        connection.close()
        print("Connection closed.")


class Chemical:

    def create_Chemical_table(self, connection):
        """Create the 'Chemical' table if it doesn't exist."""
        try:
            with connection:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Chemical (
                        ValveNo INTEGER NOT NULL UNIQUE,
                        Name TEXT NOT NULL,
                        Stock REAL DEFAULT 0,
                        MinStock REAL DEFAULT 0,
                        MaxStock INTEGER ,
                        LastUpdated TEXT NOT NULL,
                        InputLayoutPath TEXT NOT NULL,
                        Station1 INTEGER ,
                        Station2 INTEGER ,
                        Station3 INTEGER ,
                        Station4 INTEGER

                    )
                ''')
                max_stock = self.get_max_tank()
                # Insert default values for ValveNo, Stock, MinStock, Name, LastUpdated, and InputLayoutPath for rows 1 to 50
                for valve_no in range(1, 61):
                    cursor.execute('''
                        INSERT OR IGNORE INTO Chemical (ValveNo, Name, Stock, MinStock,MaxStock, LastUpdated, InputLayoutPath, Station1 , Station2 , Station3 , Station4)
                        VALUES (?, '','0','0' , ?, '','', '', '', '', '')
                    ''', (valve_no, max_stock,))

                connection.commit()
                print("Table 'Chemical' created or already exists.")

        except Exception as e:
            print(f"Error: {e}")

    def get_max_stock_for_valve(self, connection, valve_no):

        with connection:
            cursor = connection.cursor()
            cursor.execute('SELECT MaxStock FROM Chemical WHERE ValveNo = ?', (valve_no,))
            max_stock_result = cursor.fetchone()
            return max_stock_result[0] if max_stock_result else self.get_max_tank()

    def get_max_tank_valve(self, valve):

        with connection:
            cursor = connection.cursor()
            cursor.execute('SELECT MaxStock FROM Chemical WHERE ValveNo = ?', (valve,))
            max_stock_result = cursor.fetchone()
            return max_stock_result[0]

    def fetch_max_stock_settings(self):
        with sqlite3.connect("ChemDB.db") as connection:
            cursor = connection.cursor()
            max_stocks = []
            for valve_no in range(1, 6):
                cursor.execute('SELECT MaxStock FROM Chemical WHERE ValveNo = ?', (valve_no,))
                stock = cursor.fetchone()  # Use fetchone() to get a single row
                if stock:  # Check if the stock is not None
                    max_stocks.append(stock[0])  # Append the stock value to the list
                else:
                    max_stocks.append(None)  # If no record found, append None or handle it as needed
            print(max_stocks)
            return max_stocks

    def get_max_tank(self):

        try:
            with open('form_data.json', 'r') as json_file:
                login_info = json.load(json_file)
                return login_info.get('max_tank_capacity', '')
        except (FileNotFoundError, json.JSONDecodeError):
            return ''

    def get_total_valve_count(self, connection):
        try:
            with connection:
                cursor = connection.cursor()
                cursor.execute('SELECT COUNT(DISTINCT ValveNo) FROM Chemical')
                total_valve_count = cursor.fetchone()[0]
                return total_valve_count
        except sqlite3.Error as e:
            print(f"SQLite error during valve count fetch: {e}")
            return 0

    def fetch_max_stock_value(self):

        database_file = "ChemDB.db"
        data = []

        try:
            with sqlite3.connect(database_file) as connection:
                cursor = connection.cursor()

                # Fetch data from the 'Chemical' table
                cursor.execute('SELECT MaxStock FROM Chemical')
                data = cursor.fetchall()

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")
        print(data)
        return data

    def insert_the_max_stock(self):
        database_file = "ChemDB.db"

        with sqlite3.connect(database_file) as connection:
            cursor = connection.cursor()
            max_stock = self.get_max_tank()
            print('maxstock', max_stock)
            for valve_no in range(1, 61):
                cursor.execute('''
                    UPDATE Chemical
                    SET MaxStock = ?
                    WHERE ValveNo = ?
                ''', (max_stock, valve_no))

            connection.commit()
            print("MaxStock values updated in the 'Chemical' table.")

    def fetch_chemical_data(self):
        database_file = "ChemDB.db"
        data = []

        try:
            with sqlite3.connect(database_file) as connection:
                cursor = connection.cursor()

                # Fetch data from the 'Chemical' table
                cursor.execute('SELECT * FROM Chemical')
                data = cursor.fetchall()

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

        return data

    def fetch_original_chemical(self, valve_number):
        # Fetch the original data before the update
        connection = sqlite3.connect("ChemDB.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Chemical WHERE ValveNo=?", (valve_number,))
        original_data = cursor.fetchone()
        connection.close()
        return original_data

    def fetch_and_store_chemical_data(self, connection, chemical_data_file):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM Chemical')
                rows = cursor.fetchall()
                chemical_data_file = 'ChemicalData.json'

                # Convert rows to a list of dictionaries
                data_list = []
                for row in rows:
                    data_dict = {
                        'ValveNo': row[0],
                        'Name': row[1],
                        'Stock': row[2],
                        'MinStock': row[3],
                        'MaxStock': row[4],
                        'LastUpdated': row[5],
                        'InputLayoutPath': row[6],
                        'Station1': row[7],
                        'Station2': row[8],
                        'Station3': row[9],
                        'Station4': row[10]
                    }
                    data_list.append(data_dict)

                # Store the data in a JSON file
                with open(chemical_data_file, 'w') as json_file:
                    json.dump(data_list, json_file, indent=2)

                print(f"Data from 'Chemical' table successfully stored in '{chemical_data_file}'.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def update_from_chemical(self, connection, json_filename):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Read data from the JSON file
                with open(json_filename, 'r') as json_file:
                    data_list = json.load(json_file)

                for data in data_list:
                    chemical_name = data.get('Name')
                    stock = data.get('Stock', 0)
                    min_stock = data.get('MinStock', 0)
                    max_stock = data.get('MaxStock', '')
                    last_updated = data.get('LastUpdated', '')
                    input_path = data.get('InputLayoutPath', '')
                    valve_no = data['ValveNo']
                    station1_value = data.get('Station1', '')
                    station2_value = data.get('Station2', '')
                    station3_value = data.get('Station3', '')
                    station4_value = data.get('Station4', '')

                    # Fetch existing LastUpdated value for the given ValveNo
                    cursor.execute('SELECT LastUpdated FROM Chemical WHERE ValveNo = ?', (valve_no,))
                    existing_last_updated = cursor.fetchone()
                    existing_last_updated = existing_last_updated[0] if existing_last_updated else ''

                    # Check if other columns are being updated (excluding 'LastUpdated') and LastUpdated is empty
                    if any([chemical_name, stock, min_stock, input_path]) and not existing_last_updated:
                        # If any of the specified columns are being updated and LastUpdated is empty,
                        # set 'LastUpdated' to current date and time
                        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        cursor.execute('''
                            UPDATE Chemical
                            SET Name = ?, Stock = ?, MinStock = ?, MaxStock = ?,LastUpdated = ?, InputLayoutPath = ?, Station1 =?, Station2=?, Station3=?, Station4=?
                            WHERE ValveNo = ?
                        ''', (chemical_name, stock, min_stock, max_stock, last_updated, input_path, station1_value,
                              station2_value, station3_value, station4_value, valve_no))
                    else:
                        cursor.execute('''
                            UPDATE Chemical
                            SET Name = ?, Stock = ?, MinStock = ?,MaxStock = ?, LastUpdated = ?, InputLayoutPath = ?, Station1 =?, Station2=?, Station3=?, Station4=?
                            WHERE ValveNo = ?
                        ''', (chemical_name, stock, min_stock, max_stock, last_updated, input_path, station1_value,
                              station2_value, station3_value, station4_value, valve_no))

                connection.commit()
                print("Data updated in 'Chemical' successfully.")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_chemical_names(self):
        database_file = "ChemDB.db"
        names = []

        try:
            with sqlite3.connect(database_file) as connection:
                cursor = connection.cursor()

                # Fetch only the 'Name' column from the 'Chemical' table
                cursor.execute('SELECT Name FROM Chemical')
                names = [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

        return names

    def fetch_valve_details_from_database(self, valve_no):
        """Fetch details for a specific valve from the 'Chemical' table."""

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM Chemical WHERE ValveNo = ?', (valve_no,))
                data = cursor.fetchone()

                if data:
                    valve_details = {
                        'ValveNo': data[0],
                        'Name': data[1],
                        'Stock': data[2],
                        'MinStock': data[3],
                        'LastUpdated': data[4],
                        'InputLayoutPath': data[5],
                        # Add other columns as needed
                    }
                    # print(valve_details)
                    return valve_details
                else:
                    print(f"Valve details not found for ValveNo {valve_no}")
                    return None

        except Exception as e:
            print(f"Error fetching valve details: {e}")
            return None

    def fetch_stock_for_valve(self, connection, valve_number):
        """Fetch the stock value for a specific valve from the 'Chemical' table."""
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT Stock FROM Chemical WHERE ValveNo = ?', (valve_number,))
                stock_value = cursor.fetchone()

                if stock_value is not None:
                    return stock_value[0]
                else:
                    print(f"Stock value not found for ValveNo {valve_number}")
                    return None

        except Exception as e:
            print(f"Error fetching stock value: {e}")
            return None

    def fetch_min_stock_for_valve(self, connection, valve_no):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT MinStock FROM Chemical WHERE ValveNo = ?", (valve_no,))
                result = cursor.fetchone()

                if result is not None and len(result) > 0:
                    return result[0]
                else:
                    return None
        except Exception as e:
            print(f"Error fetching min_stock for valve {valve_no}: {e}")
            return None

    def update_chemical_data(self, connection, valve_number, chemical_name, stock, min_stock):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    UPDATE Chemical
                    SET Name = ?,
                        Stock = ?,
                        MinStock = ?,
                        LastUpdated = ?
                    WHERE ValveNo = ?
                """, (chemical_name, stock, min_stock, last_updated, valve_number))

                # Commit the changes
                connection.commit()
                print("Data updated successfully.")

                # Fetch the updated data
                updated_data = self.fetch_chemical_data_for_valve(connection, valve_number)
                print("Updated data:", updated_data)

        except Exception as e:
            print(f"Error updating data: {e}")

    def fetch_chemical_data_for_valve(self, connection, valve_number):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM Chemical WHERE ValveNo = ?', (valve_number,))
                data = cursor.fetchone()
                return data
        except Exception as e:
            print(f"Error fetching data: {e}")


class BatchChemicalData:
    def create_BatchChemicalData_table(self, connection):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS BatchChemicalData (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT ,
                        BatchID INTEGER NOT NULL,
                        BatchName TEXT NOT NULL,
                        SeqNo INTEGER NOT NULL,
                        TargetTank TEXT NOT NULL,
                        ValveNo INTEGER NOT NULL,
                        Chemical TEXT NOT NULL,
                        TargetWeight REAL NOT NULL DEFAULT 0 ,
                        DispensedWeight REAL NOT NULL,
                        UserName TEXT NOT NULL DEFAULT 0,
                        Status TEXT NOT NULL DEFAULT 0,
                        Date TEXT DEFAULT CURRENT_DATE,
                        DispDate TEXT DEFAULT CURRENT_DATE,
                        DispTime TEXT DEFAULT CURRENT_TIME,    
                        WaterAddition REAL NOT NULL,
                        DispenseWhen TEXT NOT NULL
                    )
                ''')
                connection.commit()
                print("Table 'BatchChemicalData' created or already exists.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def insert_into_BatchChemicalData(self, connection, batch_id, batch_name, seq_no, tank_spinner, chemical,
                                      target_weight, user_name, status, dispense_when):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                date = datetime.now().strftime("%Y-%m-%d")
                disp_date = datetime.now().strftime("%Y-%m-%d")
                disp_time = datetime.now().strftime("%H:%M:%S")

                # Fetch ValveNo based on Chemical name from the 'Chemical' table
                cursor.execute('SELECT ValveNo FROM Chemical WHERE Name = ?', (chemical,))
                result = cursor.fetchone()

                if result:
                    valve_no = result[0]
                else:
                    print(f"Chemical '{chemical}' not found in the 'Chemical' table.")
                    return
                # Check if data with the same batch_id and seq_no already exists
                cursor.execute('''SELECT * FROM BatchChemicalData WHERE BatchID = ? AND SeqNo = ?''',
                               (batch_id, seq_no))
                existing_data = cursor.fetchone()

                if existing_data:
                    cursor.execute('''
                                    UPDATE BatchChemicalData
                                    SET SeqNo = SeqNo + 1
                                    WHERE BatchID = ? AND SeqNo >= ? AND typeof(SeqNo) = 'integer'
                                ''', (batch_id, seq_no))

                    cursor.execute('''
                        INSERT INTO BatchChemicalData (
                            BatchID, BatchName, SeqNo, TargetTank, ValveNo, Chemical, TargetWeight, DispensedWeight, UserName,
                            Status, DispenseWhen, Date, DispDate, DispTime, WaterAddition
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, '0', ?, ?, ?, ?, ?, ?, '0')
                    ''', (batch_id, batch_name, seq_no, tank_spinner, valve_no, chemical, target_weight,
                          user_name, status, dispense_when, date, disp_date, disp_time))
                    print("Data Updated Successfully")


                else:
                    # Ensure that date, disp_date, and disp_time have appropriate default values
                    date = datetime.now().strftime("%Y-%m-%d")
                    disp_date = datetime.now().strftime("%Y-%m-%d")
                    disp_time = datetime.now().strftime("%H:%M:%S")

                    # Fetch ValveNo based on Chemical name from the 'Chemical' table
                    cursor.execute('SELECT ValveNo FROM Chemical WHERE Name = ?', (chemical,))
                    result = cursor.fetchone()

                    if result:
                        valve_no = result[0]
                    else:
                        print(f"Chemical '{chemical}' not found in the 'Chemical' table.")
                        return

                    # Insert data into 'BatchChemicalData'
                    cursor.execute('''
                        INSERT INTO BatchChemicalData (
                            BatchID, BatchName, SeqNo, TargetTank, ValveNo, Chemical, TargetWeight, DispensedWeight, UserName,
                            Status, DispenseWhen, Date, DispDate, DispTime, WaterAddition
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, '0', ?, ?, ?, ?, ?, ?, '0')
                    ''', (batch_id, batch_name, seq_no, tank_spinner, valve_no, chemical, target_weight,
                          user_name, status, dispense_when, date, disp_date, disp_time))

                connection.commit()
                print("Data inserted/updated into 'BatchChemicalData' successfully.")
                # self.fetch_and_store_data(connection, 'BatchChemicalData.json')

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def insert_into_BatchChemicalData_csv(self, connection, batch_name, seq_no, tank_spinner, chemical,
                                          target_weight, user_name, status, dispense_when):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT ID FROM BatchMetaData WHERE BatchName = ?', (batch_name,))
                batch_id_row = cursor.fetchone()
                batch_id = batch_id_row[0]
                if self.data_exists_batch(connection, batch_id, batch_name, seq_no, tank_spinner, chemical,
                                          target_weight, user_name, status, dispense_when):
                    return "Data Already Exist"
                date = datetime.now().strftime("%Y-%m-%d")
                disp_date = datetime.now().strftime("%Y-%m-%d")
                disp_time = datetime.now().strftime("%H:%M:%S")

                # Fetch ValveNo based on Chemical name from the 'Chemical' table
                cursor.execute('SELECT ValveNo FROM Chemical WHERE Name = ?', (chemical,))
                result = cursor.fetchone()

                if result:
                    valve_no = result[0]
                else:
                    print(f"Chemical '{chemical}' not found in the 'Chemical' table.")
                    return 'chemical not found'
                # Check if data with the same batch_id and seq_no already exists
                cursor.execute('''SELECT * FROM BatchChemicalData WHERE BatchID = ? AND SeqNo = ?''',
                               (batch_id, seq_no))
                existing_data = cursor.fetchone()

                if existing_data:
                    cursor.execute('''
                                    UPDATE BatchChemicalData
                                    SET SeqNo = SeqNo + 1
                                    WHERE BatchID = ? AND SeqNo >= ? AND typeof(SeqNo) = 'integer'
                                ''', (batch_id, seq_no))

                    cursor.execute('''
                        INSERT INTO BatchChemicalData (
                            BatchID, BatchName, SeqNo, TargetTank, ValveNo, Chemical, TargetWeight, DispensedWeight, UserName,
                            Status, DispenseWhen, Date, DispDate, DispTime, WaterAddition
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, '0', ?, ?, ?, ?, ?, ?, '0')
                    ''', (batch_id, batch_name, seq_no, tank_spinner, valve_no, chemical, target_weight,
                          user_name, status, dispense_when, date, disp_date, disp_time))

                    return "BatchChemicalData Updated Successfully"


                else:
                    # Ensure that date, disp_date, and disp_time have appropriate default values
                    date = datetime.now().strftime("%Y-%m-%d")
                    disp_date = datetime.now().strftime("%Y-%m-%d")
                    disp_time = datetime.now().strftime("%H:%M:%S")

                    # Fetch ValveNo based on Chemical name from the 'Chemical' table
                    cursor.execute('SELECT ValveNo FROM Chemical WHERE Name = ?', (chemical,))
                    result = cursor.fetchone()

                    if result:
                        valve_no = result[0]
                    else:
                        print(f"Chemical '{chemical}' not found in the 'Chemical' table.")
                        return 'Chemical Not Found'

                    # Insert data into 'BatchChemicalData'
                    cursor.execute('''
                        INSERT INTO BatchChemicalData (
                            BatchID, BatchName, SeqNo, TargetTank, ValveNo, Chemical, TargetWeight, DispensedWeight, UserName,
                            Status, DispenseWhen, Date, DispDate, DispTime, WaterAddition
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, '0', ?, ?, ?, ?, ?, ?, '0')
                    ''', (batch_id, batch_name, seq_no, tank_spinner, valve_no, chemical, target_weight,
                          user_name, status, dispense_when, date, disp_date, disp_time))

                connection.commit()
                return "BatchChemicalData inserted successfully."
                # self.fetch_and_store_data(connection, 'BatchChemicalData.json')

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_valveno_record_id(self, record_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = '''
                    SELECT ValveNo
                    FROM BatchChemicalData
                    WHERE ID = ?  
                    '''
                cursor.execute(query, (record_id,))
                results = cursor.fetchone()
                return results[0]

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_details_by_batch_chemical(self, batch_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Prepare the SQL query to fetch the specified columns based on BatchName and Chemical
                query = '''
                    SELECT ID, SeqNo, TargetTank, ValveNo, Chemical,
                           TargetWeight, DispensedWeight, Status,WaterAddition,DispenseWhen
                    FROM BatchChemicalData              
                    WHERE BatchID = ? 
                    ORDER BY SeqNo ASC
                '''
                cursor.execute(query, (batch_id,))

                results = cursor.fetchall()

                return results

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None

    def check_batch_exists(self, batch_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM BatchChemicalData WHERE ID = ?", (batch_id,))
                count = cursor.fetchone()[0]
                return count > 0
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return False

    def fetch_and_store_data(self, connection, Batch_chem_data, batch_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM BatchChemicalData WHERE BatchID = ?', (batch_id,))
                rows = cursor.fetchall()
                Batch_chem_data = 'BatchChemicalData.json'

                # Convert rows to a list of dictionaries
                data_list = []
                for row in rows:
                    data_dict = {
                        'ID': row[0],
                        'SeqNo': row[2],
                        'TargetTank': row[3],
                        'Chemical No': row[4],
                        'Chemical': row[5],
                        'TargetWeight': row[6],
                        'DispensedWeight': row[7],
                        'UserName': row[8],
                        'Status': row[9],
                        'Date': row[10],
                        'DispDate': row[11],
                        'DispTime': row[12],
                        'WaterAddition': row[13],
                        'DispenseWhen': row[14]
                    }
                    data_list.append(data_dict)

                # Store the data in a JSON file
                with open(Batch_chem_data, 'w') as json_file:
                    json.dump(data_list, json_file, indent=2)

                print(f"Data from 'BatchChemicalData' table successfully stored in '{Batch_chem_data}'.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def update_from_json(self, connection, json_filename):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Read data from the JSON file
                with open(json_filename, 'r') as json_file:
                    data_list = json.load(json_file)

                for data in data_list:
                    seq_no = data['SeqNo']
                    tank_spinner = data['TargetTank']
                    chemical = data['Chemical']
                    target_weight = data['TargetWeight']
                    user_name = data['UserName']
                    status = data['Status']
                    date = data['Date']

                    # Retrieve DispDate, DispTime, and DispenseWhen from the JSON data
                    disp_date = data.get('DispDate')
                    disp_time = data.get('DispTime')
                    dispense_when = data.get('DispenseWhen')

                    record_id = data['ID']

                    # Check the current status of the record in BatchChemicalData
                    cursor.execute('SELECT Status FROM BatchChemicalData WHERE ID = ?', (record_id,))
                    current_status = cursor.fetchone()

                    if current_status and current_status[0] == 'Complete':
                        print(f"Record ID {record_id} is already marked as 'Complete'. Skipping update.")
                        continue  # Skip updating this record

                    # Fetch ValveNo based on Chemical name from the 'Chemical' table
                    cursor.execute('SELECT ValveNo FROM Chemical WHERE Name = ?', (chemical,))
                    result = cursor.fetchone()

                    if result:
                        valve_no = result[0]
                    else:
                        print(f"Chemical '{chemical}' not found in the 'Chemical' table.")
                        continue

                    # Update data in 'BatchChemicalData' based on ID and BatchName
                    cursor.execute('''
                        UPDATE BatchChemicalData
                        SET ValveNo = ?, SeqNo = ?, TargetTank = ?, Chemical = ?, TargetWeight = ?, DispensedWeight = '0',
                            UserName = ?, Status = ?, Date = ?, DispDate = ?, DispTime = ?, DispenseWhen = ?
                        WHERE ID = ?
                    ''', (valve_no, seq_no, tank_spinner, chemical, target_weight, user_name, status,
                          date, disp_date, disp_time, dispense_when, record_id))

                    # Commit the changes
                    connection.commit()

                print("Data updated in 'BatchChemicalData' successfully.")
        except sqlite3.Error as e:
            print("SQLite error:", e)

    def fetch_BatchChemicalData_status(self, status_filter=None):
        database_file = "ChemDB.db"
        data = []

        try:
            with sqlite3.connect(database_file) as connection:
                cursor = connection.cursor()

                if status_filter:
                    cursor.execute('SELECT * FROM BatchChemicalData WHERE Status = ?', (status_filter,))
                else:
                    cursor.execute('SELECT * FROM BatchChemicalData')

                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")
        return data

    def data_exists_batch(self, conn, batch_id, batch_name, seq_no, tank_spinner, chemical, target_weight, user_name,
                          status, dispense_when):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = """
                    SELECT * FROM BatchChemicalData
                    WHERE BatchID=? AND BatchName=? AND SeqNo=? AND TargetTank=? AND Chemical=? AND TargetWeight=?
                    AND UserName=? AND Status=? AND DispenseWhen=?
                """
                cursor.execute(query, (
                batch_id, batch_name, seq_no, tank_spinner, chemical, target_weight, user_name, status, dispense_when))
                existing_data = cursor.fetchone()

                return existing_data is not None

        except sqlite3.Error as e:
            print(f"SQLite error in data_exists: {e}")
            return False

    def delete_Batchchemical(self, connection, batchid):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM BatchChemicalData WHERE ID=?", (batchid,))
                connection.commit()
                print(f"Deleted batch chemical with ID: {batchid}")

        except sqlite3.Error as e:
            connection.rollback()  # Rollback the transaction in case of an error
            print(f"Error deleting batch chemical with ID {batchid}: {e}")

    def fetch_BatchChemicalData_data_by_batch_name(self, batch_id):
        database_file = "ChemDB.db"
        data = []

        try:
            with sqlite3.connect(database_file) as connection:
                cursor = connection.cursor()

                query = '''
                            SELECT ID, SeqNo, TargetTank, ValveNo, Chemical,TargetWeight,DispensedWeight,
                                    UserName, Status,Date,DispDate,DispTime , WaterAddition,DispenseWhen
                            FROM BatchChemicalData
                            WHERE BatchID = ? 
                            ORDER BY  ID DESC
                        '''
                # Execute the query with the provided batch_name and chemical
                cursor.execute(query, (batch_id,))
                # Fetch all rows that match the query
                results = cursor.fetchall()
                return results

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

        return data


class BatchMetaData:
    def create_BatchMetaData_table(self, connection):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS BatchMetaData (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        BatchName TEXT NOT NULL,
                        FabricWt TEXT NOT NULL,
                        MLR TEXT NOT NULL,
                        MachinNo TEXT NOT NULL,
                        CreatedBy TEXT NOT NULL,
                        Date TEXT NOT NULL          
                    )
                ''')
                # for batch_name in range(1, 100001):
                #     cursor.execute('''
                #     INSERT OR IGNORE INTO BatchMetaData(BatchName, FabricWt, MLR, MachinNo, CreatedBy, Date)
                #     VALUES(?, '12', 'mlr', 'Ethel Machin', 'dharma', '')
                #     ''', (batch_name,))
                connection.commit()
                print("Table 'BatchMetaData' created or already exists.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def get_login_username(self):

        try:
            with open('login_info.json', 'r') as json_file:
                login_info = json.load(json_file)
                return login_info.get('username', '')
        except (FileNotFoundError, json.JSONDecodeError):
            return ''

    def insert_into_BatchMetaData(self, connection, batch_name, fabric_wt, mlr, machin_name):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                if self.data_exist_bachmeta(connection, batch_name, fabric_wt, mlr, machin_name):
                    print("Error: Data already exists.")
                    return

                # Get current date and time
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                created_by = self.get_login_username()

                # Insert data into BatchMetaData table
                cursor.execute('''
                    INSERT INTO BatchMetaData (BatchName, FabricWt, MLR, MachinNo, CreatedBy, Date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (batch_name, fabric_wt, mlr, machin_name, created_by, current_date))

                connection.commit()
                print("Data inserted successfully.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def insert_into_BatchMetaData_csv(self, connection, batch_name, fabric_wt, mlr, machin_name):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                if self.data_exist_bachmeta(connection, batch_name, fabric_wt, mlr, machin_name):
                    return "Error: BatchMetaData already exists."

                # Get current date and time
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                created_by = self.get_login_username()

                # Insert data into BatchMetaData table
                cursor.execute('''
                    INSERT INTO BatchMetaData (BatchName, FabricWt, MLR, MachinNo, CreatedBy, Date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (batch_name, fabric_wt, mlr, machin_name, created_by, current_date))

                connection.commit()
                return "BatchMetaData inserted successfully."
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_batch_name(self):
        names = []
        try:
            # Establish a connection to the database
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Execute the query to fetch the data
                cursor.execute('SELECT ID, BatchName FROM BatchMetaData ORDER BY ID DESC')

                # Loop through the fetched rows and construct the desired format
                names = [f"ID: {row[0]}    BatchName: {row[1]}" for row in cursor.fetchall()]

                # Return the list of formatted strings
                return names

        except sqlite3.Error as e:
            # Print error message in case of an exception
            print(f"SQLite error during data fetch: {e}")
            return []

    def fetch_batch_report(self):
        names = []
        try:
            # Establish a connection to the database
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Execute the query to fetch the data
                cursor.execute('SELECT ID, BatchName FROM BatchMetaData ORDER BY ID DESC')

                # Loop through the fetched rows and construct the desired format
                names = [f"ID: {row[0]}    Batch: {row[1]}" for row in cursor.fetchall()]

                # Return the list of formatted strings
                return names

        except sqlite3.Error as e:
            # Print error message in case of an exception
            print(f"SQLite error during data fetch: {e}")
            return []

    def fetch_selected_batch_details(self):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                            SELECT ID, BatchName, FabricWt, MLR, MachinNo, CreatedBy, Date
                            FROM BatchMetaData
                            ORDER BY ID DESC 
                            LIMIT 1
                        ''', )

                selected_batch_info = cursor.fetchone()
                return selected_batch_info
        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

    def fetch_selected_batch_id(self):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                            SELECT ID
                            FROM BatchMetaData
                            ORDER BY ID DESC 
                            LIMIT 1
                        ''', )

                selected_batch_info = cursor.fetchone()
                return selected_batch_info[0]
        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

    def fetch_selected_batch_info(self, batch_id):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT ID, BatchName, FabricWt, MLR, MachinNo, CreatedBy, Date
                    FROM BatchMetaData
                    WHERE ID = ?
                ''', (batch_id,))

                selected_batch_info = cursor.fetchone()
                return selected_batch_info
        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

    def fetch_selected_batch_main(self, batch_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT ID, BatchName, FabricWt, MLR, MachinNo, CreatedBy, Date
                    FROM BatchMetaData
                    WHERE ID = ?
                ''', (batch_id,))

                selected_batch_info = cursor.fetchone()
                return selected_batch_info
        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

    def delete_Batchmedata(self, connection, batch_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                cursor.execute("DELETE FROM BatchChemicalData WHERE BatchID=?", (batch_id,))

                # Delete from BatchMetaData using BatchName
                cursor.execute("DELETE FROM BatchMetaData WHERE ID=?", (batch_id,))

                connection.commit()
                print(f"Deleted batch data with BatchName: {batch_id}")

        except sqlite3.Error as e:
            connection.rollback()  # Rollback the transaction in case of an error
            print(f"Error deleting batch data with BatchName {batch_id}: {e}")

    def data_exist_bachmeta(self, conn, batch_name, fabric_wt, mlr, machin_name):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = """
                SELECT * FROM BatchMetaData 
                WHERE BatchName=? AND FabricWt=? AND MLR=? AND MachinNo=?
                """
                cursor.execute(query, (batch_name, fabric_wt, mlr, machin_name))
                existing_data = cursor.fetchone()
                return existing_data is not None

        except sqlite3.Error as e:
            print(f"SQLite error in data_exists: {e}")
            return False

    def fetch_batch_name_report(self):

        batch_names = []
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                                SELECT BatchName
                                FROM BatchMetaData 


                            ''', )

                batch_names = [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")
        return batch_names


class OutputLayout:
    def create_OutputLayout_table(self, connection):  # modify version2
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS OutputLayout (

                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        MachineName TEXT NOT NULL,
                        MachinPath TEXT NOT NULL,
                        DrainPath TEXT NOT NULL,
                        SlaveID TEXT NOT NULL,
                        Tank1Path TEXT,
                        Tank2Path TEXT,               
                        Tank3Path TEXT,
                        Tank4Path TEXT,
                        Tank5Path TEXT,
                        Tank1Stock INTEGER,
                        Tank2Stock INTEGER,
                        Tank3Stock INTEGER,
                        Tank4Stock INTEGER,
                        Tank5Stock INTEGER 
                    )
                ''')
                connection.commit()
                print("Table 'OutputLayout' created or already exists.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_tank_path_valid(self):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT Tank1Path,Tank2Path,Tank3Path,Tank4Path,Tank5Path FROM OutputLayout')
                data = cursor.fetchall()
                filtered_data = [value for row in data for value in row if value != '']
                print(filtered_data)
                return filtered_data
        except Exception as ex:
            print(f"fetched error: {ex}")

    def fetch_tank_for_wash(self, machine_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                query = f'''
                    SELECT MachineName,Tank1Path, Tank2Path, Tank3Path, Tank4Path, Tank5Path
                    FROM OutputLayout
                    WHERE ID = ?;
                '''
                cursor.execute(query, (machine_id,))
                result = cursor.fetchone()

                print(result)
                return result

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None  # Return None in case of a database error

    def fetch_tank_paths(self, connection, machine_name):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()


                # Assuming the table is already created using the provided create_OutputLayout_table function
                query = f'''
                    SELECT Tank1Path, Tank2Path, Tank3Path, Tank4Path, Tank5Path
                    FROM OutputLayout
                    WHERE MachineName = ?;
                '''
                cursor.execute(query, (machine_name,))
                result = cursor.fetchone()

                if result:
                    tank_names = [f'Tank{i}' for i, path in enumerate(result, start=1) if path and path.strip()]
                    return tank_names
                else:
                    print(f"No records found for MachineName: {machine_name}")
                    return None  # Return None if no records are found

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None  # Return None in case of a database error

    def fetch_and_store_output_layout_data(self, connection, output_layout_file):  # modify version2
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM OutputLayout')
                rows = cursor.fetchall()
                output_layout_file = 'OutputLayoutData.json'

                # Convert rows to a list of dictionaries
                data_list = []
                for row in rows:
                    data_dict = {
                        'ID': row[0],
                        'MachineName': row[1],
                        'MachinPath': row[2],
                        'DrainPath': row[3],
                        'SlaveID': row[4],
                        'Tank1Path': row[5],
                        'Tank2Path': row[6],
                        'Tank3Path': row[7],
                        'Tank4Path': row[8],
                        'Tank5Path': row[9],
                        'Tank1Stock': row[10],
                        'Tank2Stock': row[11],
                        'Tank3Stock': row[12],
                        'Tank4Stock': row[13],
                        'Tank5Stock': row[14]
                    }
                    data_list.append(data_dict)

                # Store the data in a JSON file
                with open(output_layout_file, 'w') as json_file:
                    json.dump(data_list, json_file, indent=2)

                print(f"Data from 'OutputLayout' table successfully stored in '{output_layout_file}'.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_machine_name_by_batch_name(self, connection, batch_name):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = '''
                    SELECT MachineName
                    FROM OutputLayout
                    WHERE MachineName = ?;
                '''
                cursor.execute(query, (batch_name,))
                result = cursor.fetchone()

                if result:
                    machine_name = result[0]
                    return machine_name
                else:
                    print(f"No records found for BatchName: {batch_name}")
                    return None

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None

    def update_from_output_layout(self, connection, json_filename):  # modify version2
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                # Read data from the JSON file
                with open(json_filename, 'r') as json_file:
                    data_list = json.load(json_file)

                for data in data_list:
                    machine_name = data.get('MachineName')
                    machine_path = data.get('MachinePath')
                    drain_path = data.get('DrainPath')
                    slave_id = data.get('SlaveID')
                    tank_1 = data.get('Tank1Path')
                    tank_2 = data.get('Tank2Path')
                    tank_3 = data.get('Tank3Path')
                    tank_4 = data.get('Tank4Path')
                    tank_5 = data.get('Tank5Path')
                    tank1_stock = data.get('Tank1Stock')
                    tank2_stock = data.get('Tank2Stock')
                    tank3_stock = data.get('Tank3Stock')
                    tank4_stock = data.get('Tank4Stock')
                    tank5_stock = data.get('Tank5Stock')

                    # Check if any field is updated

                    cursor.execute('''
                        UPDATE OutputLayout
                        SET MachineName = ?, MachinPath = ?, DrainPath = ?,SlaveID = ?, Tank1Path = ?, Tank2Path = ?, 
                            Tank3Path = ?, Tank4Path = ?, Tank5Path = ?,Tank1Stock = ?,Tank2Stock = ?, Tank3Stock=?,
                            Tank4Stock =?,Tank5Stock=?
                        WHERE ID = ?
                    ''', (machine_name, machine_path, drain_path, slave_id, tank_1, tank_2, tank_3, tank_4, tank_5,
                          tank1_stock, tank2_stock, tank3_stock, tank4_stock, tank5_stock,
                          data['ID']))

                connection.commit()
                print("Data updated in 'OutputLayout' successfully.")
                os.remove(json_filename)
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_OutputTank_data(self):
        database_file = "ChemDB.db"
        data = []

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Fetch data from the 'Chemical' table
                cursor.execute('SELECT * FROM OutputLayout')
                data = cursor.fetchall()

                print("Fetched data inside function:", data)  # Add this line to check if data is fetched


        except sqlite3.Error as e:

            print(f"SQLite error during data fetch: {e}")
        return data

    def insert_tank_data(self, Machin_Name, Machin_Path, Drain_Path, Slave_ID, Tank_1, Tank_2, Tank_3, Tank_4, Tank_5,
                         tank1_stock, tank2_stock, tank3_stock, tank4_stock, tank5_stock):  # modify version2

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO OutputLayout(MachineName, MachinPath, DrainPath,SlaveID, Tank1Path, Tank2Path, Tank3Path, Tank4Path, Tank5Path,Tank1Stock,Tank2Stock,Tank3Stock,Tank4Stock,Tank5Stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?, ?, ?)
                """, (
                Machin_Name, Machin_Path, Drain_Path, Slave_ID, Tank_1, Tank_2, Tank_3, Tank_4, Tank_5, tank1_stock,
                tank2_stock, tank3_stock, tank4_stock, tank5_stock))
                connection.commit()
                print("Tank data inserted successfully.")
                output_layout_file = 'OutputLayoutData.json'
                # self.fetch_and_store_output_layout_data(connection,output_layout_file)
        except sqlite3.Error as e:
            print(f"Error inserting tank data: {e}")

    def delete_tank(self, connection, tankid):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM OutputLayout WHERE ID = ?", (tankid,))
                connection.commit()
                print(f"Deleted tank with ID: {tankid}")
                return True
        except sqlite3.Error as e:
            print(f"Error deleting tank: {e}")
            return False

    def fetch_all_machine_slaveid(self):
        machine_names = []
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT SlaveID FROM OutputLayout')

                machine_names = [row[0] for row in cursor.fetchall()]
                print(machine_names)

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        return machine_names

    def fetch_slave_id_hmi(self):
        machine_names = []
        slave_ids = []
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT SlaveID FROM OutputLayout')

                machine_names = [row[0] for row in cursor.fetchall()]
                slave_ids = [int(machine_name) for machine_name in machine_names]
                # print(slave_ids)

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        # Convert the list of strings to a list of integers
        return slave_ids

    def fetch_all_machine_names(self):

        machine_names = []
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT ID,MachineName FROM OutputLayout')

                machine_names = [f"ID: {row[0]}   MachineName: {row[1]}" for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        return machine_names

    def get_machin_name(self):

        machine_names = []
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT MachineName FROM OutputLayout')

                machine_names = [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        return machine_names

    def fetch_tank_data_based_id(self, connection, tankid):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM OutputLayout WHERE ID = ?', (tankid,))
                data = cursor.fetchone()
                return data
        except Exception as e:
            print(f"Error fetching data: {e}")

    def validate_target_wt_based_tank(self,tank_no,machine_name):
        tank_map = {
            'Tank1': 'Tank1Stock',
            'Tank2': 'Tank2Stock',
            'Tank3': 'Tank3Stock',
            'Tank4': 'Tank4Stock',
            'Tank5': 'Tank5Stock'
        }
        tank_no_str = tank_map.get(str(tank_no))
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                            SELECT {} 
                            FROM OutputLayout 
                            WHERE MachineName = ? 
                        '''.format(tank_no_str), (machine_name,))
                fetched_tank = cursor.fetchone()
                if fetched_tank and fetched_tank[0] is not None:
                    return fetched_tank[0]
                else:
                    return 0
        except Exception as e:
            print("Error fetching tank path:", e)
            return 0


class TankWashDetails:
    def create_tank_details_table(self, connection):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS TankWashDetails (

                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        MachinID INTEGER NOT NULL,
                        MachineName TEXT NOT NULL,
                        Tank1 TEXT NOT NULL,
                        T1PreWash TEXT,
                        T1AfterWash1 TEXT,               
                        T1AfterWash2 TEXT,
                        Tank2 TEXT NOT NULL,
                        T2PreWash TEXT,
                        T2AfterWash1 TEXT,               
                        T2AfterWash2 TEXT,
                        Tank3 TEXT NOT NULL,
                        T3PreWash TEXT,
                        T3AfterWash1 TEXT,               
                        T3AfterWash2 TEXT,
                        Tank4 TEXT NOT NULL,
                        T4PreWash TEXT,
                        T4AfterWash1 TEXT,               
                        T4AfterWash2 TEXT,
                        Tank5 TEXT NOT NULL,
                        T5PreWash TEXT,
                        T5AfterWash1 TEXT,               
                        T5AfterWash2 TEXT

                    )
                ''')
                connection.commit()
                print("Table 'TankWashDetails' created or already exists.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def insert_tank_details_data(self,
                                 connection,
                                 machin_id, Machin_Name, Tank1, tank_1_prewash, tank_1_after1, tank_1_after2,
                                 Tank2, tank_2_prewash, tank_2_after1, tank_2_after2,
                                 Tank3, tank_3_prewash, tank_3_after1, tank_3_after2,
                                 Tank4, tank_4_prewash, tank_4_after1, tank_4_after2,
                                 Tank5, tank_5_prewash, tank_5_after1, tank_5_after2
                                 ):
        try:
            # Create a cursor object to execute the SQL statement
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Define the SQL insert statement
                sql_insert_query = '''
                    INSERT INTO TankWashDetails (
                        MachinID,MachineName,
                        Tank1, T1PreWash, T1AfterWash1, T1AfterWash2,
                        Tank2, T2PreWash, T2AfterWash1, T2AfterWash2,
                        Tank3, T3PreWash, T3AfterWash1, T3AfterWash2,
                        Tank4, T4PreWash, T4AfterWash1, T4AfterWash2,
                        Tank5, T5PreWash, T5AfterWash1, T5AfterWash2
                    )
                    VALUES (?, ?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''

                # Execute the insert statement with the provided parameters
                cursor.execute(sql_insert_query, (

                    machin_id, Machin_Name, Tank1, tank_1_prewash, tank_1_after1, tank_1_after2,
                    Tank2, tank_2_prewash, tank_2_after1, tank_2_after2,
                    Tank3, tank_3_prewash, tank_3_after1, tank_3_after2,
                    Tank4, tank_4_prewash, tank_4_after1, tank_4_after2,
                    Tank5, tank_5_prewash, tank_5_after1, tank_5_after2
                ))

                # Commit the changes to the database
                connection.commit()

                print("Data inserted successfully into TankWashDetails.")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def update_tank_details_data(self,
                                 connection,
                                 id,
                                 Machin_Name, Tank1, tank_1_prewash, tank_1_after1, tank_1_after2,
                                 Tank2, tank_2_prewash, tank_2_after1, tank_2_after2,
                                 Tank3, tank_3_prewash, tank_3_after1, tank_3_after2,
                                 Tank4, tank_4_prewash, tank_4_after1, tank_4_after2,
                                 Tank5, tank_5_prewash, tank_5_after1, tank_5_after2
                                 ):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Define the SQL update statement
                sql_update_query = '''
                    UPDATE TankWashDetails
                    SET
                        MachineName = ?,
                        Tank1 = ?,
                        T1PreWash = ?,
                        T1AfterWash1 = ?,
                        T1AfterWash2 = ?,
                        Tank2 = ?,
                        T2PreWash = ?,
                        T2AfterWash1 = ?,
                        T2AfterWash2 = ?,
                        Tank3 = ?,
                        T3PreWash = ?,
                        T3AfterWash1 = ?,
                        T3AfterWash2 = ?,
                        Tank4 = ?,
                        T4PreWash = ?,
                        T4AfterWash1 = ?,
                        T4AfterWash2 = ?,
                        Tank5 = ?,
                        T5PreWash = ?,
                        T5AfterWash1 = ?,
                        T5AfterWash2 = ?
                    WHERE ID = ?
                '''

                # Execute the update statement with the provided parameters and record ID
                cursor.execute(
                    sql_update_query,
                    (
                        Machin_Name, Tank1, tank_1_prewash, tank_1_after1, tank_1_after2,
                        Tank2, tank_2_prewash, tank_2_after1, tank_2_after2,
                        Tank3, tank_3_prewash, tank_3_after1, tank_3_after2,
                        Tank4, tank_4_prewash, tank_4_after1, tank_4_after2,
                        Tank5, tank_5_prewash, tank_5_after1, tank_5_after2,
                        id
                    )
                )

                # Commit the changes to the database
                connection.commit()

                print("Data updated successfully in TankWashDetails.")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def fetch_tank_details_data(self, machin_id):
        try:

            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                sql_select_query = '''
                    SELECT
                        ID, MachineName, Tank1, T1PreWash, T1AfterWash1, T1AfterWash2,
                        Tank2, T2PreWash, T2AfterWash1, T2AfterWash2,
                        Tank3, T3PreWash, T3AfterWash1, T3AfterWash2,
                        Tank4, T4PreWash, T4AfterWash1, T4AfterWash2,
                        Tank5, T5PreWash, T5AfterWash1, T5AfterWash2
                    FROM TankWashDetails
                    WHERE MachinID = ?
                '''

                # Execute the query with the specified machin_name
                cursor.execute(sql_select_query, (machin_id,))

                # Fetch the first row from the results
                data = cursor.fetchone()
                print(data)
                return data

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None

    def fetch_tank_details_data_byid(self, machin_id):
        try:

            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                sql_select_query = '''
                    SELECT
                        ID, MachineName, Tank1, T1PreWash, T1AfterWash1, T1AfterWash2,
                        Tank2, T2PreWash, T2AfterWash1, T2AfterWash2,
                        Tank3, T3PreWash, T3AfterWash1, T3AfterWash2,
                        Tank4, T4PreWash, T4AfterWash1, T4AfterWash2,
                        Tank5, T5PreWash, T5AfterWash1, T5AfterWash2
                    FROM TankWashDetails
                    WHERE ID = ?
                '''

                # Execute the query with the specified machin_name
                cursor.execute(sql_select_query, (machin_id,))

                # Fetch the first row from the results
                data = cursor.fetchone()
                print(data)
                return data

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None

    def fetch_machin_name(self, machin_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Fetch data for the specified MachineName
                sql_select_query = '''
                    SELECT MachinID
                    FROM TankWashDetails
                    WHERE MachinID = ?
                '''

                cursor.execute(sql_select_query, (machin_id,))

                data = cursor.fetchone()
                print("data")
                if data is None:
                    print(' none data', data)
                    return None

                return [data[0]]

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None


class User:
    def create_User_table(self, connection):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS User (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        UserName TEXT NOT NULL,
                        Password TEXT NOT NULL,
                        Privilage TEXT NOT NULL DEFAULT 'User'
                    )
                ''')
                connection.commit()
                print("Table 'User' created or already exists.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def check_user_exists(self, userid):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM User WHERE ID = ?", (userid,))
                count = cursor.fetchone()[0]
                return count > 0
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return False

    def fetch_user_names(self):
        names = []

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Fetch only the 'Name' column from the 'Chemical' table
                cursor.execute('SELECT Name FROM User')
                names = [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")

        return names

    def check_admin_users(self):
        with sqlite3.connect("ChemDB.db") as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM User WHERE Privilage = "Admin"')
            result = cursor.fetchone()
            return result is not None

    def authenticate_user(self, login_info):
        username = login_info.get("username", "")
        password = login_info.get("password", "")

        # Authenticate the user against the User table in the database
        with sqlite3.connect("ChemDB.db") as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT Privilage FROM User WHERE UserName = ? AND Password = ?", (username, password))
            result = cursor.fetchone()
            if result:
                logged_in_user = result[0]
                print(f"Authenticated as {result[0]}")
                return logged_in_user  # Return the value to the caller
            else:
                print("Authentication failed")
                return None

    def fetch_UserTable_data(self):
        data = []

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Fetch data from the 'Chemical' table
                cursor.execute('SELECT * FROM User')
                data = cursor.fetchall()

                print("Fetched data inside function:", data)  # Add this line to check if data is fetched


        except sqlite3.Error as e:

            print(f"SQLite error during data fetch: {e}")

        return data

    def insert_user_data(self, name, user_name, password, privilage):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                # Check if user with the same username and password already exists
                if self.data_exists(cursor, user_name, password):
                    print("Error: User with the same username and password already exists.")
                    return

                # Insert data into the User table, excluding the ID column
                cursor.execute("""
                    INSERT INTO User (Name, UserName, Password, Privilage)
                    VALUES (?, ?, ?, ?)
                """, (name, user_name, password, privilage))

                # Commit the changes
                connection.commit()

                print("User data inserted successfully.")

        except sqlite3.Error as e:
            print(f"Error inserting user data: {e}")

    def update_row_user(self, user_id, column_name, new_value):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM User WHERE ID = ?", (user_id,))
                count = len(cursor.fetchall())
                if count == 0:
                    raise ValueError(f"ID {user_id} does not exist in the database.")

                cursor.execute("SELECT * FROM User WHERE ID = ?", (user_id,))
                original_data = cursor.fetchall()
                update_query = f"UPDATE User SET {column_name}=? WHERE ID=?"  # Removed extra comma before WHERE
                cursor.execute(update_query, (new_value, user_id))
                connection.commit()
                print(f"Update successful for ID {user_id} in column {column_name}.")

                # Fetch the updated data
                cursor.execute("SELECT * FROM User WHERE ID=?", (user_id,))
                updated_row = cursor.fetchone()

                # Print only the new data
                for col_name, old_value, new_val in zip(cursor.description, original_data[0], updated_row):
                    col_name = col_name[0]
                    if old_value != new_val:
                        print(f"Changed in column {col_name}: {old_value} -> {new_val}")

                return updated_row  # Return the updated data here; updated Date is the current datetime

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            print("Update failed.")
        return None

    def fetch_user_data_for_id(self, connection, user_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM User WHERE ID = ?', (user_id,))
                data = cursor.fetchone()
                return data
        except Exception as e:
            print(f"Error fetching data: {e}")

    def delete_user(self, connection, userid):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM User WHERE ID = ?", (userid,))
                connection.commit()
                print(f"Deleted user with ID: {userid}")
        except sqlite3.Error as e:
            print(f"Error deleting user: {e}")

    def validate_login(self, entered_username, entered_password):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                cursor.execute('SELECT * FROM User WHERE UserName = ? AND Password = ?',
                               (entered_username, entered_password))
                user_data = cursor.fetchone()

                if user_data is not None:
                    return True
                else:
                    return False

        except sqlite3.Error as e:
            print(f"SQLite error during login validation: {e}")
            return False

    def data_exists(self, conn, user_name, password):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = "SELECT * FROM User WHERE UserName = ? AND Password = ?"
                cursor.execute(query, (user_name, password))
                existing_data = cursor.fetchone()
                return existing_data is not None

        except sqlite3.Error as e:
            print(f"SQLite error in data_exists: {e}")
            return False


class Report:

    def create_Report_table(self, connection):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Report (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT ,
                        RecordID INTEGER NOT NULL,
                        BatchID INTEGER NOT NULL,
                        BatchName TEXT NOT NULL,
                        SeqNo INTEGER NOT NULL,
                        TargetTank TEXT NOT NULL,
                        ValveNo INTEGER NOT NULL,
                        Chemical TEXT NOT NULL,
                        TargetWeight REAL NOT NULL DEFAULT 0 ,
                        DispensedWeight REAL NOT NULL,
                        UserName TEXT NOT NULL DEFAULT 0,
                        Status TEXT NOT NULL DEFAULT 0,
                        Date TEXT DEFAULT CURRENT_DATE,
                        DispDate TEXT DEFAULT CURRENT_DATE,
                        DispTime TEXT DEFAULT CURRENT_TIME,    
                        WaterAddition REAL NOT NULL,
                        DispenseWhen TEXT NOT NULL
                    )
                ''')
                connection.commit()
                print("Table 'Report' created or already exists.")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def deta_exist_report(self, RecordID, StationID, ValveNo, DispensedWt, WaterDispensedWt):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = """
                    SELECT * FROM Report
                    WHERE RecordID=? 
                """
                cursor.execute(query, (RecordID,))
                existing_data = cursor.fetchone()

                return existing_data is not None

        except sqlite3.Error as e:
            print(f"SQLite error in data_exists: {e}")
            return False

    def fetch_report_data(self, from_datetime, to_datetime):
        try:
            # Remove leading/trailing whitespace from datetime strings
            from_datetime_str = from_datetime.strip()
            to_datetime_str = to_datetime.strip()
            # Connect to the database
            with sqlite3.connect('ChemDB.db') as connection:
                cursor = connection.cursor()

                query = '''
                        SELECT ID, RecordID, BatchID, ValveNo, Chemical,UserName,DispensedWeight,WaterAddition,DispDate, DispTime
                        FROM Report
                        WHERE (DispDate || ' ' || DispTime) BETWEEN ? AND ?
                        ORDER BY ID DESC
                        '''

                # Execute the query with parameterized values
                cursor.execute(query, (from_datetime_str, to_datetime_str))
                results = cursor.fetchall()
                print(results)
                return results

        except ValueError as ve:
            print(f"Value error: {ve}")
            return []
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return []

    def fetch_chemical_data(self, from_time, to_time, chemical):
        try:
            # Remove leading/trailing whitespace from datetime strings
            from_datetime_str = from_time.strip()
            to_datetime_str = to_time.strip()
            chemical_str = chemical.strip()

            # Validate datetime format
            from_dt = datetime.strptime(from_datetime_str, '%Y-%m-%d %H:%M:%S')
            to_dt = datetime.strptime(to_datetime_str, '%Y-%m-%d %H:%M:%S')

            # Connect to the database
            with sqlite3.connect('ChemDB.db') as connection:
                cursor = connection.cursor()

                query = '''
                        SELECT ID, RecordID, BatchID, ValveNo, Chemical,UserName,DispensedWeight,WaterAddition,DispDate, DispTime
                        FROM Report
                        WHERE (DispDate || ' ' || DispTime) BETWEEN ? AND ?
                        AND Chemical = ?
                        ORDER BY ID DESC
                        '''

                # Execute the query with parameterized values
                cursor.execute(query, (from_datetime_str, to_datetime_str, chemical_str))
                results = cursor.fetchall()
                print(results)
                return results

        except ValueError as ve:
            print(f"Value error: {ve}")
            return []
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return []

    def fetch_batch_data_report(self, from_time, to_time, batch_name):
        try:
            # Remove leading/trailing whitespace from datetime strings
            from_datetime_str = from_time.strip()
            to_datetime_str = to_time.strip()
            batch_str = batch_name.strip()
            print("batch_id", batch_str)
            # Validate datetime format
            from_dt = datetime.strptime(from_datetime_str, '%Y-%m-%d %H:%M:%S')
            to_dt = datetime.strptime(to_datetime_str, '%Y-%m-%d %H:%M:%S')

            # Connect to the database
            with sqlite3.connect('ChemDB.db') as connection:
                cursor = connection.cursor()

                query = '''
                        SELECT ID, RecordID, BatchID, ValveNo,Chemical, BatchName,UserName,DispensedWeight,WaterAddition,DispDate, DispTime
                        FROM Report
                        WHERE (DispDate || ' ' || DispTime) BETWEEN ? AND ?
                        AND BatchID = ?
                        ORDER BY ID DESC
                        '''

                # Execute the query with parameterized values
                cursor.execute(query, (from_datetime_str, to_datetime_str, batch_str))
                results = cursor.fetchall()
                print(results)
                return results

        except ValueError as ve:
            print(f"Value error: {ve}")
            return []
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return []

    def fetch_report_data_batch(self, Batch_id):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = '''
                            SELECT ID, RecordID, BatchID, ValveNo,Chemical,UserName,DispensedWeight,WaterAddition, DispDate, DispTime
                            FROM Report
                            WHERE BatchID = ? 
                            ORDER BY ID DESC

                        '''

                cursor.execute(query, (Batch_id,))

                results = cursor.fetchall()
                return results

        except Exception as e:
            print(f"Fetch Error:{e}")


class SharedData:
    dispense_chem = []


class DispenseData:
    dispense_queue = []


class BatchRequest:
    hmi_request = []

class DatabaseInterfaceForHMI:

    def Error_Code_HMI(self, error_message, SlaveID):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{current_time}   - SlaveID: {SlaveID},  Error: {error_message}"

        # Log the message into a .log file
        with open("Error_Message.log", "a") as log_file:
            log_file.write(log_message + "\n")

    def fetch_batch_id_rec(self, rec_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT BatchID
                    FROM BatchChemicalData
                    WHERE ID = ?
                ''', (rec_id,))
                result = cursor.fetchone()

                if result is not None:
                    batch_id = result[0]
                    return int(batch_id)
                else:
                    return 0
        except sqlite3.Error as e:
            print("Error fetching batch id:", e)
            return 0



    def fetch_chemical_id(self, rec_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute(''' 
                                SELECT ID, ValveNo
                                FROM BatchChemicalData
                                WHERE ID = ? 
                                ''', (rec_id,))
                dispense_data = cursor.fetchone()  # Fetch one row
                print("dispense_data:", dispense_data)
                self.dispense_chemical_list(dispense_data)
                if dispense_data is not None:
                    return dispense_data
                else:
                    return 0
        except sqlite3.Error as e:
            print("Error fetching batch data:", e)

    def dispense_chemical_list(self, list_chemical):
        chemical = self.check_chemical_pending(list_chemical)
        if chemical is not None:
            if list_chemical not in SharedData.dispense_chem:
                if list_chemical not in DispenseData.dispense_queue:
                    SharedData.dispense_chem.append(list_chemical)
                    print(SharedData.dispense_chem)
                    return SharedData.dispense_chem

    def dispense_chemical_completed(self, list_data):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute(''' 
                                        SELECT DispensedWeight
                                        FROM Report
                                        WHERE RecordID = ?  And Status = 'Complete'
                                    ''', (list_data,))
                dispense_wt = cursor.fetchone()  # Fetch one row
                if dispense_wt is None:
                    # No matching records found
                    print("No matching records found for RecordID:", list_data)
                    return 0

                original_disp_wt = float(dispense_wt[0]) * 10
                print("Checked complete Data:", int(original_disp_wt))
                return int(original_disp_wt)

        except Exception as e:
            print("Error fetching batch data:", e)
            return 0

    def check_chemical_completed(self, list_data):
        record_id = list_data[0]
        chem_id = list_data[1]

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute(''' 
                                        SELECT RecordID, ValveNo,DispensedWeight
                                        FROM Report
                                        WHERE RecordID = ? AND ValveNo=? And Status = 'Complete'
                                    ''', (record_id, chem_id))
                checked_data = cursor.fetchone()  # Fetch one row
                print("Checked complete Data:", checked_data)
                return checked_data
        except Exception as e:
            print("Error fetching batch data:", e)

    def check_chemical_pending(self, list_chemical):
        record_id = list_chemical[0]
        chem_id = list_chemical[1]
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute(''' 
                                        SELECT ID, ValveNo
                                        FROM BatchChemicalData
                                        WHERE ID = ? AND ValveNo=? And Status = 'Pending'
                                    ''', (record_id, chem_id))
                checked_data = cursor.fetchone()  # Fetch one row
                print("Checked Data:", checked_data)
                return checked_data
        except Exception as e:
            print("Error fetching batch data:", e)

    def get_first_values(self, shared_data, dispense_data):
        # Extract first values from dispense_chem
        first_values_chem = [item[0] for item in shared_data.dispense_chem]

        # Extract first values from dispense_queue
        first_values_queue = [item[0] for item in dispense_data.dispense_queue]

        # Combine the lists
        combined_first_values = first_values_chem + first_values_queue

        return combined_first_values

    def BatchID_slaveId(self, batch_id, slave_id):
        with sqlite3.connect("ChemDB.db") as connection:
            cursor = connection.cursor()

            # Fetch machine name for the given slave_id
            cursor.execute('''
                SELECT MachineName
                FROM OutputLayout 
                WHERE SlaveID = ?
            ''', (slave_id,))
            slave_machine_name_row = cursor.fetchone()
            if slave_machine_name_row is None:
                print("No machine name found for the given slave_id.")
                return False

            slave_machine_name = slave_machine_name_row[0]
            print("slave_machine_name:", slave_machine_name)

            # Fetch machine name for the given batch ID
            cursor.execute('''
                SELECT MachinNo
                FROM BatchMetaData 
                WHERE ID = ?
            ''', (batch_id,))
            batch_machine_name_row = cursor.fetchone()
            if batch_machine_name_row is None:
                print("No machine name found for the given batch_id.")
                return False

            batch_machine_name = batch_machine_name_row[0]
            print("batch_machine_name:", batch_machine_name)

            # Compare the machine names
            return slave_machine_name == batch_machine_name

    def BatchID_Info_Request(self, batch_id, slave_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Fetch machine name for the given slave_id
                cursor.execute(''' 
                    SELECT MachineName
                    FROM OutputLayout 
                    WHERE SlaveID = ? 
                ''', (slave_id,))
                slave_machine_name_row = cursor.fetchone()
                if slave_machine_name_row is None:
                    print("No machine name found for given slave_id.")
                    return (None, [])
                slave_machine_name = slave_machine_name_row[0]
                print("slave_machine_name:", slave_machine_name)

                # Fetch machine name for the given batch ID
                cursor.execute(''' 
                    SELECT MachinNo
                    FROM BatchMetaData 
                    WHERE ID = ? 
                ''', (batch_id,))
                batch_machine_name_row = cursor.fetchone()
                if batch_machine_name_row is None:
                    print("No machine name found for given batch_id.")
                    return (None, [])
                batch_machine_name = batch_machine_name_row[0]
                print("batch_machine_name:", batch_machine_name)

                if slave_machine_name == batch_machine_name:
                    shared_data = SharedData()
                    dispense_data = DispenseData()
                    excluded_ids = self.get_first_values(shared_data, dispense_data)
                    placeholders = ','.join('?' for _ in excluded_ids)

                    if slave_machine_name == batch_machine_name:
                        query = f'''
                            SELECT ID, ValveNo, TargetWeight, DispensedWeight, TargetTank, SeqNo
                            FROM BatchChemicalData
                            WHERE BatchID = ? AND Status = 'Pending' AND ID NOT IN ({placeholders}) AND SeqNo NOT LIKE 'A%'
                            ORDER BY SeqNo ASC LIMIT 5
                        '''
                        # Combine batch_id with excluded_ids for the query parameters
                        params = (batch_id, *excluded_ids)
                        cursor.execute(query, params)
                        results = cursor.fetchall()
                        print("results", results)
                        for item in results:
                            if item[0] not in BatchRequest.hmi_request:
                                BatchRequest.hmi_request.append(item[0])
                        print('batch_rec',BatchRequest.hmi_request)
                    transformed_results = []

                    tank_mapping = {
                        'Tank1': 1,
                        'Tank2': 2,
                        'Tank3': 3,
                        'Tank4': 4,
                        'Tank5': 5
                    }

                    for row in results:
                        modified_row = list(row)
                        modified_row[2] = int(modified_row[2] * 10)  # Convert TargetWeight to int
                        modified_row[3] = int(modified_row[3] * 10)  # Convert DispensedWeight to int
                        modified_row[4] = tank_mapping.get(modified_row[4], modified_row[4])  # Map TargetTank
                        transformed_results.append(modified_row)

                    while len(transformed_results) < 5:
                        transformed_results.append([0, 0, 0, 0, 0, 0])
                    print("transformed_results:", (self.getBatchName(batch_id), transformed_results))
                    return (self.getBatchName(batch_id), transformed_results)
                else:
                    print("Machine names do not match.")
                    return (None, [])

        except sqlite3.Error as e:
            print(f"SQLite error during data fetch: {e}")
            return (None, [])

    # get 30 chemical name
    def Fetch_Chemical_Names(self):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Execute a query to fetch the first 30 names from the 'Chemical' table
                cursor.execute('''
                    SELECT Name
                    FROM Chemical
                    LIMIT 30
                ''')

                # Fetch all results from the query
                results = cursor.fetchall()

                # Convert the results to a list of strings (extraction from tuples)
                names_list = [result[0] for result in results]

                return names_list

        except Exception as e:
            print(f"Error: {e}")
            return []

    def fetch_tank_paths(self, batch_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                # Fetch MachineName for the given batch_id
                query_machine_name = '''
                    SELECT MachinNo
                    FROM BatchMetaData 
                    WHERE ID = ? 
                '''
                cursor.execute(query_machine_name, (batch_id,))
                batch_machine_name = cursor.fetchone()

                if batch_machine_name:
                    batch_machine_name = batch_machine_name[0]  # Extract the MachineName from the tuple

                    # Query tank paths based on MachineName
                    query_tank_paths = '''
                        SELECT Tank1Path, Tank2Path, Tank3Path, Tank4Path, Tank5Path
                        FROM OutputLayout
                        WHERE MachineName = ?;
                    '''
                    cursor.execute(query_tank_paths, (batch_machine_name,))
                    result = cursor.fetchone()

                    if result:
                        tank_paths = result  # Result is a tuple of Tank1Path, Tank2Path, ..., Tank5Path
                        tank_names = []
                        for i, path in enumerate(tank_paths):
                            if path and path.strip():
                                tank_names.append(i + 1)

                        return tank_names

                    else:
                        print("No result found for batch_id:", batch_id)
                        return None

                else:
                    print("No MachineName found for batch_id:", batch_id)
                    return None

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None

    def AdditionsRequest(self,Slave_id, batchID, AddNo, ChemID, TargetWt, TankNo):
        if not all([batchID, AddNo, ChemID, TargetWt, TankNo]):
            print("Invalid input parameters. All parameters are required.")
            return None

        date = datetime.now().strftime("%Y-%m-%d")
        batch_name = self.getBatchName(batchID)
        chemical_name = self.getChemicalName(ChemID)
        seq_no = 'A' + str(AddNo)
        dispensed_weight = 0.0
        user_name = 'HMI'
        status = 'Pending'
        dispense_when = 'Request'
        disp_date = None
        disp_time = None
        water_addition = 0.0
        original_target = TargetWt / 10
        machine_name = self.fetch_machine_name(batchID)
        tank_paths = self.fetch_tank_paths(batchID)
        if TankNo in tank_paths:
            Tank_no = self.identify_tank_no(TankNo)

            if self.data_exists_batch(batchID, AddNo):
                print("Error: Data already exists.")
                return None
            target_wt_validate = OutputLayout().validate_target_wt_based_tank(Tank_no, machine_name)
            try:
                if float(original_target) > int(target_wt_validate):
                    error_msg = f'Target weight is exceed than your Tank{TankNo} capacity{target_wt_validate} but you give {original_target}'
                    self.Error_Code_HMI(error_msg, Slave_id)
                    return None
            except Exception as ex:
                print(f'error in insert{ex}')

            try:
                with sqlite3.connect("ChemDB.db") as connection:
                    cursor = connection.cursor()

                    insert_query = '''
                        INSERT INTO BatchChemicalData (
                            BatchID, BatchName, SeqNo, TargetTank, ValveNo, Chemical, TargetWeight,
                            DispensedWeight, UserName, Status, DispenseWhen, Date, DispDate, DispTime, WaterAddition
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''

                    cursor.execute(insert_query, (
                        batchID, batch_name, seq_no, Tank_no, ChemID, chemical_name,
                        original_target, dispensed_weight, user_name, status, dispense_when,
                        date, disp_date, disp_time, water_addition
                    ))

                    cursor.execute('''
                        SELECT ID, SeqNo
                        FROM BatchChemicalData
                        WHERE SeqNo = ?
                        ORDER BY ID DESC
                        LIMIT 1
                    ''', (seq_no,))

                    last_row = cursor.fetchone()
                    print("Last row fetched:", last_row)

                    return last_row

            except sqlite3.Error as ex:
                print("SQLite error: Unable to add additions to database:", ex)
                return None
        else:
            print(f"Invalid TankNo: {TankNo}. Valid tank numbers are: {tank_paths}")
            return None

    def AdditionsRequest_2(self, Additions_RecordID):  # The New Function to add Record_ID and Valve No
        with sqlite3.connect("ChemDB.db") as connection2:
            cursor = connection2.cursor()

            cursor.execute('''
                SELECT ValveNo
                FROM BatchChemicalData
                WHERE ID = ?
            ''', (Additions_RecordID,))
            valve_no = cursor.fetchone()

            add_tuple = (Additions_RecordID, valve_no[0])

            if add_tuple not in SharedData.dispense_chem:
                SharedData.dispense_chem.insert(0, add_tuple)

            print("SharedData.dispense_chem", SharedData.dispense_chem)

    def fetch_seq_no_hmi_status(self, record_id):
        with sqlite3.connect("ChemDB.db") as connection2:
            cursor = connection2.cursor()

            cursor.execute('''
                SELECT SeqNo
                FROM BatchChemicalData
                WHERE ID = ?
            ''', (record_id,))

            seq_no = cursor.fetchone()
            return seq_no[0]
    def fetch_machine_name(self, batch_id):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                        SELECT MachinNo
                        FROM BatchMetaData
                        WHERE ID = ?
                    ''', (batch_id,))
                batch_name = cursor.fetchone()
                if batch_name is not None:
                    return str(batch_name[0])
                else:
                    return
        except Exception as ex:
            print("Error : in getting machine_name from batch id. ", ex)

    def getBatchName(self, batch_id):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                        SELECT BatchName
                        FROM BatchMetaData
                        WHERE ID = ?
                    ''', (batch_id,))
                batch_name = cursor.fetchone()
                if batch_name is not None:
                    return str(batch_name[0])
                else:
                    return 0
        except Exception as ex:
            print("Error : in getting batchname from batch id. ", ex)

    def getChemicalName(self, chemID):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                        SELECT Name
                        FROM Chemical
                        WHERE ValveNo = ?
                    ''', (chemID,))
                chemical_name = cursor.fetchone()
                return chemical_name[0]
        except Exception as ex:
            print("Error : in getting chemical_name from chem id. ", ex)

    def tank_no_value(self, batch_id, tank_no):
        tank_paths = self.fetch_tank_paths(batch_id)

        # Check if tank_no is in the list of valid tank paths
        if tank_no in tank_paths:
            print(f"Tank number {tank_no} is valid.")
            return tank_no  # Return the numeric tank number directly

        # Mapping of tank numbers to tank names
        tank_map = {
            '1': 'Tank1',
            '2': 'Tank2',
            '3': 'Tank3',
            '4': 'Tank4',
            '5': 'Tank5'
        }

        # Convert tank_no to string for comparison with tank_map keys
        tank_no_str = str(tank_no)

        # Check if tank_no_str is a valid key in tank_map
        if tank_no_str in tank_map:
            tank_name = tank_map[tank_no_str]
            print(f"Tank number {tank_no} is mapped to tank name: {tank_name}")
            return tank_name  # Return the corresponding tank name

        # If tank_no is not found in tank_paths and not a valid key in tank_map, return None
        print(f"Tank number {tank_no} is not valid for batch ID {batch_id}.")
        return None

    def identify_tank_no(self, tank_no):
        tank_map = {
            '1': 'Tank1',
            '2': 'Tank2',
            '3': 'Tank3',
            '4': 'Tank4',
            '5': 'Tank5'
        }
        tank_no_str = str(tank_no)
        return tank_map.get(tank_no_str, None)

    def data_exists_batch(self, batchID, AddNo):

        seq_no = 'A' + str(AddNo)
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                query = """
                    SELECT SeqNo FROM BatchChemicalData
                    WHERE BatchID=? AND SeqNo=? 
                """

                cursor.execute(query, (batchID, seq_no,))
                existing_data = cursor.fetchone()
                return existing_data is not None

        except sqlite3.Error as e:
            print(f"SQLite error in data_exists_batch: {e}")
            return None


class DatabaseInterfaceForWeigingSytsem:

    def UpdateErrorCode(self, error_message, StationID):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{current_time} - StationID: {StationID}, Error: {error_message}"

        # Log the message into a .log file
        with open("Error_Message.log", "a") as log_file:
            log_file.write(log_message + "\n")

    def identify_tank_wash(self, tank_no, machine_name):
        tank_map = {
            'Tank1': 'T1AfterWash1',
            'Tank2': 'T2AfterWash1',
            'Tank3': 'T3AfterWash1',
            'Tank4': 'T4AfterWash1',
            'Tank5': 'T5AfterWash1'
        }
        tank_no_str = tank_map.get(str(tank_no))
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT {}
                    FROM TankWashDetails
                    WHERE MachineName = ?
                '''.format(tank_no_str), (machine_name,))
                water_weight = cursor.fetchone()
                if water_weight and water_weight[0] is not None and water_weight[0] != '':
                    ori_water_weight = float(water_weight[0]) * 10
                    return int(ori_water_weight)

                else:
                    with open('form_data.json', 'r') as json_file:
                        connection_info = json.load(json_file)
                        after_wash = connection_info.get("default_water1", '')
                        result = float(after_wash) * 10
                        return int(result)

        except Exception as e:
            print("Error fetching water weight:", e)
            return 0

    def identify_tank_path(self, tank_no, machine_name):
        tank_map = {
            'Tank1': 'Tank1Path',
            'Tank2': 'Tank2Path',
            'Tank3': 'Tank3Path',
            'Tank4': 'Tank4Path',
            'Tank5': 'Tank5Path'
        }
        tank_no_str = tank_map.get(str(tank_no))
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT {} 
                    FROM OutputLayout 
                    WHERE MachineName = ?
                '''.format(tank_no_str), (machine_name,))
                fetched_tank = cursor.fetchone()
                tank_path = int(fetched_tank[0]) if fetched_tank else None
                print(tank_path)
                return tank_path
        except Exception as e:
            print("Error fetching tank path:", e)
        return None

    def fetch_batch_data(self, record_id):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT BatchID, TargetTank, TargetWeight
                    FROM BatchChemicalData
                    WHERE ID = ?
                ''', (record_id,))
                batch_data = cursor.fetchone()
                print(batch_data)
                return batch_data
        except Exception as e:
            print("Error fetching batch data:", e)
        return None

    def fetch_machine_name(self, batch_id):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT MachinNo
                    FROM BatchMetaData
                    WHERE ID = ?
                ''', (batch_id,))
                machine_name = cursor.fetchone()
                print(machine_name)
                return machine_name[0] if machine_name else None
        except Exception as e:
            print("Error fetching machine name:", e)
        return None

    def fetch_station_value(self, StationID, valve_no):
        # Define a dictionary to map StationID to actual station names in the database
        station_map = {
            1: 'Station1',
            2: 'Station2',
            3: 'Station3',
            4: 'Station4'
        }

        # Get the station name from station_map based on StationID
        station_name = station_map.get(int(StationID))
        print(station_name)
        print(valve_no)

        try:
            if station_name is not None:
                with sqlite3.connect("ChemDB.db") as connection:
                    cursor = connection.cursor()

                    # Use parameterized query to avoid SQL injection and format correctly
                    query = f'''
                        SELECT {station_name}
                        FROM Chemical
                        WHERE ValveNo = ?
                    '''
                    cursor.execute(query, (valve_no,))

                    # Fetch the station value
                    station_value = cursor.fetchone()

                    if station_value is not None:

                        return int(station_value[0])
                    else:
                        return None

        except Exception as e:
            print("Error fetching station value:", e)
            return

    def fetch_volve_by_recordid(self, RecordID):

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                cursor.execute('''
                            SELECT ValveNo
                            FROM BatchChemicalData
                            WHERE ID = ?
                        ''', (RecordID,))
                valve_no = cursor.fetchone()
                return valve_no[0]
        except Exception as e:
            print("Error fetching valveno:", e)
        return None

    def IsChemicalAvailableForDispense(self, StationID):
        print(SharedData.dispense_chem)

        if StationID in (1, 2, 3, 4):
            station_column = 'Station' + str(StationID)
            try:
                with sqlite3.connect("ChemDB.db") as connection:
                    cursor = connection.cursor()
                    cursor.execute(f'''
                        SELECT ValveNo
                        FROM Chemical
                        WHERE {station_column} != 0 AND NAME != ''
                    ''')
                    valve_numbers = cursor.fetchall()
                    print(valve_numbers)

                    for valve_number in valve_numbers:
                        for tup in SharedData.dispense_chem:
                            if valve_number[0] == tup[1]:
                                print(f"Valve number {valve_number[0]} is available for dispensing.")
                                batch_data = self.fetch_batch_data(
                                    tup[0])  # Fetch batch data based on first index of the tuple
                                if batch_data:
                                    machine_name = self.fetch_machine_name(
                                        batch_data[0])  # Fetch machine name based on BatchID
                                    disp_water_tank = self.identify_tank_wash(batch_data[1],
                                                                              machine_name)  # Identify tank data based on TargetTank
                                    tank_path = self.identify_tank_path(batch_data[1], machine_name)
                                    target_wt = int(batch_data[2] * 10)
                                    station_id = self.fetch_station_value(StationID, tup[1])
                                    transfer_data = (
                                    StationID, tup[0], station_id, target_wt, disp_water_tank, tank_path)
                                    print("transfer_data:", transfer_data)
                                    SharedData.dispense_chem.remove(tup)
                                    DispenseData.dispense_queue.append(tup)
                                    # DatabaseInterfaceForHMI().check_dispense_list_hmi(tup)
                                    return transfer_data

                    print("No valve numbers available for dispensing.")
                    return None  # No match found
            except Exception as e:
                print(f"Error checking chemical availability: {e}")
                return None
        return None

    def DispenseCompleted(self, RecordID, StationID, Valve_No, DispensedWt, WaterDispensedWt):
        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()

                date = datetime.now().strftime("%Y-%m-%d")
                disp_date = datetime.now().strftime("%Y-%m-%d")
                disp_time = datetime.now().strftime("%H:%M:%S")
                status = "Complete"
                dispense_when = "Request"
                DispensedWt = DispensedWt / 10
                print("final-dip-wieght", DispensedWt)
                WaterDispensedWt = WaterDispensedWt / 10
                print("final-water-weight", WaterDispensedWt)
                ValveNo = self.fetch_volve_by_recordid(RecordID)

                # Fetch ValveNo based on Chemical name from the 'Chemical' table
                cursor.execute('SELECT Name FROM Chemical WHERE ValveNo = ?', (ValveNo,))
                result = cursor.fetchone()

                if result:
                    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    chemical = result[0]
                    cursor.execute('SELECT Stock FROM Chemical WHERE Name = ?', (chemical,))
                    chem_stock = cursor.fetchone()

                    if chem_stock:

                        int_chem = int(chem_stock[0])
                        print("actual-chem", int_chem)
                        updated_stock = int_chem - DispensedWt
                        print("after stock reduce", updated_stock)
                        cursor.execute('''
                                        UPDATE Chemical
                                        SET Stock = ?,
                                        LastUpdated = ?
                                        WHERE Name = ?
                                    ''', (updated_stock, last_updated, chemical))

                        connection.commit()
                    else:
                        print(f"Stock for chemical '{chemical}' not found.")
                        return
                else:
                    print(f"Chemical '{ValveNo}' not found in the 'Chemical' table.")
                    return

                cursor.execute(
                    'SELECT BatchID, BatchName, SeqNo, TargetTank, TargetWeight, UserName FROM BatchChemicalData WHERE ID = ?',
                    (RecordID,))
                output_data = cursor.fetchone()

                if output_data:
                    batch_id, batch_name, seq_no, tank_spinner, target_weight, user_name = output_data
                else:
                    print(f"Batch '{RecordID}' not found in the 'BatchChemicalData' table.")
                    return

                # Update data in 'BatchChemicalData'
                cursor.execute('''
                    UPDATE BatchChemicalData 
                    SET BatchID=?, BatchName=?, SeqNo=?, TargetTank=?, ValveNo=?, Chemical=?, TargetWeight=?, DispensedWeight=?, UserName=?,
                    Status=?, DispenseWhen=?, Date=?, DispDate=?, DispTime=?, WaterAddition=?
                    WHERE ID=?
                ''', (batch_id, batch_name, seq_no, tank_spinner, ValveNo, chemical, target_weight, DispensedWt,
                      user_name, status, dispense_when, date, disp_date, disp_time, WaterDispensedWt, RecordID))

                connection.commit()
                print("Data updated into 'BatchChemicalData' successfully.")

                # Check if report data already exists
                if Report().deta_exist_report(RecordID, StationID, ValveNo, DispensedWt, WaterDispensedWt):
                    print(f"Data already exists for RecordID {RecordID}.")
                    self.check_chemical_pending()
                    return

                # Insert data into 'Report' table
                cursor.execute('''
                    INSERT INTO Report (
                        RecordID, BatchID, BatchName, SeqNo, TargetTank, ValveNo, Chemical, TargetWeight, DispensedWeight, UserName,
                        Status, DispenseWhen, Date, DispDate, DispTime, WaterAddition
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    RecordID, batch_id, batch_name, seq_no, tank_spinner, ValveNo, chemical, target_weight, DispensedWt,
                    user_name, status, dispense_when, date, disp_date, disp_time, WaterDispensedWt))

                connection.commit()
                print("Data inserted into 'Report' successfully.")
                self.check_chemical_pending()
                remove_list = (RecordID, ValveNo)
                DispenseData.dispense_queue.remove(remove_list)
                # DatabaseInterfaceForHMI().check_chemical_completed(remove_list)
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def check_chemical_pending(self):
        dispense_list = SharedData.dispense_chem
        print("old list:", dispense_list)

        try:
            with sqlite3.connect("ChemDB.db") as connection:
                cursor = connection.cursor()
                for item in dispense_list:
                    record_id, chem_id = item  # Unpack the tuple
                    cursor.execute(''' 
                        SELECT ID, ValveNo
                        FROM BatchChemicalData
                        WHERE ID = ? AND ValveNo = ? AND Status = 'Pending'
                    ''', (record_id, chem_id))
                    data = cursor.fetchone()  # Fetch one row
                    if not data:
                        # print("yes")
                        dispense_list.remove(item)  # Remove the tuple if no data found
                        print("new dispenselist:", dispense_list)
                        print("new global list:", SharedData.dispense_chem)
                return dispense_list
        except Exception as e:
            print("Error fetching batch data:", e)


def create_table():
    database_file = "ChemDB.db"
    conn = create_connection(database_file)
    Chemical().create_Chemical_table(conn)
    BatchChemicalData().create_BatchChemicalData_table(conn)
    BatchMetaData().create_BatchMetaData_table(conn)
    OutputLayout().create_OutputLayout_table(conn)
    User().create_User_table(conn)
    TankWashDetails().create_tank_details_table(conn)
    Report().create_Report_table(conn)
    # close_connection(conn)


if __name__ == "__main__":
    database_file = "ChemDB.db"
    conn = create_connection(database_file)
    if conn:
        Chemical().create_Chemical_table(conn)
        BatchChemicalData().create_BatchChemicalData_table(conn)
        BatchMetaData().create_BatchMetaData_table(conn)
        OutputLayout().create_OutputLayout_table(conn)
        User().create_User_table(conn)
        TankWashDetails().create_tank_details_table(conn)
        # close_connection(conn)
    # direct dosing
    myDbInterface = DatabaseInterfaceForHMI()
    # batchname, fetchedData = myDbInterface.BatchID_Info_Request(1)
    # print(batchname)
    # print(fetchedData)
    # print(myDbInterface.Fetch_Chemical_Names())
    # record_no = myDbInterface.AdditionsRequest(4, 1, 4, 27.9, 1)
    # print(record_no)
    #
    # # Example usage:
    # queue = AdditionsRequestQueue()
    # hmi_data = queue.add_request(1, 125, 5, 25.1, 1)

    # weiging sysytem

    mydata = DatabaseInterfaceForWeigingSytsem()
    # myDbInterface.dispense_chemical_list((95,2))
    # myDbInterface.dispense_chemical_completed(115)
    # myDbInterface.dispense_chemical_list((108, 3))
    # myDbInterface.dispense_chemical_list((105,2))
    # myDbInterface.dispense_chemical_list((77, 5))
    # myDbInterface.dispense_chemical_list((97, 4))
    # myDbInterface.dispense_chemical_list((106, 1))
    # # mydata.Error_Message_Stored("This station is Not currently Working",4)
    # #
    # mydata.IsChemicalAvailableForDispense(1)
    # mydata.UpdateErrorCode("The Data Is Already Exist",2)
    #
    # mydata.DispenseCompleted(104,2,1,111,564)
    # myDbInterface.BatchID_Info_Request(8,2)
    # OutputLayout().fetch_slave_id_hmi()
    # myDbInterface.fetch_tank_paths(12)
    # myDbInterface.tank_no_value(4,5)
    SharedData.dispense_chem.append((533, 2))
    SharedData.dispense_chem.append((530, 1))
    DispenseData.dispense_queue.append((357, 3))
    myDbInterface.BatchID_Info_Request(4, 2)

