import struct
from USBvcpSerializer_V1 import USBvcpSerializer_V1
import time
from database import *


RESPONSE_TIMEOUT = 1.0
class HMI_SlaveInfo:
    def __init__(self, slaveid : bytes):
        self.SlaveID : bytes = slaveid
        self.CurrentBatchID = 0
        self.CurrentBatchName = 0
        self.ProcessStage = 0
        self.RequestToDispenseChemicalRecordID = 0
        self.ChemDisplayIndex = 0




        self.Additions_BatchID = 0
        self.Additions_No = 0
        self.Additions_ChemID = 0
        self.Additions_TargetWt = 0
        self.Additions_TankNo = 0
        self.Additions_RecordID = 0

class ResponseHmi:
    response_hmi=[]
class Unresponse_Hmi:
    unresponse_hmi=[]
class DirectDosing_HMI_Network_V1:
    def __init__(self, slaveIDList):
        self.MyPort = USBvcpSerializer_V1(self.Rx_Callback, self.Tx_Callback, self.Error_Callback)
        self.myDBCommunication = DatabaseInterfaceForHMI()

        self.ReportList = []
        self.ChemicalsRequestedFromHMI = []
        self.SlaveList = []
        if len(slaveIDList) > 0:
            for item in slaveIDList:
                self.SlaveList.append(HMI_SlaveInfo(item))
            self.CurrentSlaveIndex = 0
        self.batch_request={}
        # self.CurrentSlave = HMI_SlaveInfo(0)
        self.waitingForResponse = False
        self.lastResponseTime = time.time()
        self.MASTER_ID = 255
        self.SLAVE_STATE_ENQUIRE_STATE_OF_SLAVE : bytes = 0
        self.SLAVE_STATE_BatchID_Info_Request : bytes = 1
        self.SLAVE_STATE_Request_Chemical_Dispense : bytes = 2
        self.SLAVE_STATE_Fetch_Chemical_Names : bytes = 3
        self.SLAVE_STATE_Additions_Request : bytes = 4
        self.ERROR_STATE_CODE = 5
        # self.wait_for_slave_com_end = 0



    def Add_Report_Dispensing(self, recordID):
        # todo search in self.ChemicalsRequestedFromHMI
        slaveID = None
        chemindex =None
        record = None
        for record in self.ChemicalsRequestedFromHMI:
            if record[2] == recordID:
                slaveID = record[1]
                chemindex = record[3]
                break

        if slaveID is not None:
            self.ReportList.append(['Dispensing', slaveID, recordID,chemindex])
            print("Dispense List:",self.ReportList)
            self.Dispense_Complete_Error()
            print("After Dispense List:", self.ChemicalsRequestedFromHMI)
        else:
            print(f"Record ID {recordID} not found in the list.")

    def Add_Report_Completed(self, recordID):
        slaveID = None
        DispesedWt = None
        chemindex = None
        record = None
        for record in self.ChemicalsRequestedFromHMI:
            if record[2] == recordID:
                slaveID = record[1]
                DispesedWt=self.myDBCommunication.dispense_chemical_completed(recordID)
                chemindex = record[3]
                break
        if slaveID and DispesedWt is not None:
            self.ReportList.append(['Completed', slaveID, recordID,chemindex, DispesedWt])
            print("Completed List:",self.ReportList)
            self.Dispense_Complete_Error()
            print("After Dispense List:", self.ChemicalsRequestedFromHMI)

    def Add_Report_Error(self, recordID):
        slaveID = None
        chemindex = None
        error_code = None
        record_id = None
        record = None
        for record in self.ChemicalsRequestedFromHMI:
            if record[2] == recordID[0]:
                record_id = recordID[0]
                slaveID = record[1]
                chemindex = record[3]
                error_code = recordID[1]
                break
        self.ReportList.append(['Error', slaveID, record_id,chemindex, error_code])
        self.Dispense_Complete_Error()


    def Rx_Callback(self,msg,data):

        print(f"RX:{data}")
        self.Rx_Message_Store(data)
        if data[0] == self.MASTER_ID :
            if (data[2] == self.SLAVE_STATE_ENQUIRE_STATE_OF_SLAVE):
                if (data[3] == self.SLAVE_STATE_ENQUIRE_STATE_OF_SLAVE):
                    #Nothing needed from hmi
                    self.Switch_to_next_slave()
                    self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0
                elif data[3] == self.SLAVE_STATE_BatchID_Info_Request:
                    # HMI Requested Batch Info
                    batch_id = struct.unpack('>i', data[4:8])[0]
                    self.batch_request[self.SlaveList[self.CurrentSlaveIndex].SlaveID] = batch_id
                    self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID = batch_id
                    if self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID > 0:
                        self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 3  # Response for BatchID_Info_Request
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_message = f"{current_time} - HMI: {self.SlaveList[self.CurrentSlaveIndex].SlaveID} RX-Batch:{self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID}"

                        try:
                            with open("Batch_Request.log", "a") as log_file:
                                log_file.write(log_message + "\n")
                        except IOError as e:
                            print(f"Error writing to log file: {e}")


                elif  data[3] == self.SLAVE_STATE_Request_Chemical_Dispense:
                    # HMI Requested Chemical Dispense
                    rec_id=struct.unpack('>i', data[4:8])[0]
                    self.SlaveList[self.CurrentSlaveIndex].RequestToDispenseChemicalRecordID = struct.unpack('>i', data[4:8])[0]
                    self.SlaveList[self.CurrentSlaveIndex].ChemDisplayIndex = data[8]

                    if(self.SlaveList[self.CurrentSlaveIndex].RequestToDispenseChemicalRecordID > 0):
                        self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 4 # Response for - Request_Chemical_Dispense
                    else:
                        if rec_id in BatchRequest.hmi_request:
                            self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 4
                elif (data[3] == self.SLAVE_STATE_Fetch_Chemical_Names):
                    # HMI Requested Chamical Names
                    self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 5 # Response for - Fetch_Chemical_Names
                elif (data[3] == self.SLAVE_STATE_Additions_Request):
                    # HMI Requested Additions
                    newBatchID = struct.unpack('>i', data[4:8])[0]
                    additionsNo = data[8]
                    print('additionsNo',additionsNo)
                    chemID = data[9]
                    targetWt = struct.unpack('>i', data[10:14])[0]
                    tankNo = data[14]
                    current_slave_id = self.SlaveList[self.CurrentSlaveIndex].SlaveID

                    if current_slave_id in self.batch_request and self.batch_request[current_slave_id] == newBatchID:
                        self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID = newBatchID
                    else:
                        if self.myDBCommunication.BatchID_slaveId(newBatchID,current_slave_id):
                            self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID = newBatchID
                        else:
                            pass

                    if (self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID == newBatchID):

                        self.SlaveList[self.CurrentSlaveIndex].Additions_BatchID = newBatchID
                        self.SlaveList[self.CurrentSlaveIndex].Additions_No = additionsNo
                        self.SlaveList[self.CurrentSlaveIndex].Additions_ChemID = chemID
                        self.SlaveList[self.CurrentSlaveIndex].Additions_TargetWt = targetWt
                        self.SlaveList[self.CurrentSlaveIndex].Additions_TankNo = tankNo
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_message = f"{current_time} - received Data: {newBatchID, additionsNo, chemID, targetWt, tankNo}"
                        with open("Rx Addition.log", "a") as log_file:
                            log_file.write(log_message + "\n")
                        self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 6 # Response for - Additions Request

                    else:
                        self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0
                        return

            else:
               # ACK Commands from HMI or U
               pass



    def Rx_Message_Store(self,data):
        self.Identify_Response_slave(data[1])
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{current_time} - HMI: RX:{data}"

        # Log the message into a .log file
        with open("Tx_RX_Command.log", "a") as log_file:
            log_file.write(log_message + "\n")


    def Tx_Callback(self, msg):
        print(f"TX:{msg}")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{current_time} - HMI: TX:{msg}"

        # Log the message into a .log file
        with open("Tx_RX_Command.log", "a") as log_file:
            log_file.write(log_message + "\n")


    def Error_Callback(self, msg):
        error_message =  msg
        print(error_message)
        self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0
        self.myDBCommunication.Error_Code_HMI(msg,self.SlaveList[self.CurrentSlaveIndex].SlaveID)

        # if (len(self.SlaveList) > 0):
        #     if (self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 0):
        #
        #         if ((self.CurrentSlaveIndex + 1) < len(self.SlaveList)):
        #             self.CurrentSlaveIndex += 1
        #         else:
        #             self.CurrentSlaveIndex = 0
        #
        #         self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 1  # To Start Process

    def Dispense_Complete_Error(self):
        if len(self.ReportList) > 0:
            item = self.ReportList.pop()  # Peek at the first item from the list
            if item[0] == 'Dispensing':
                seq_no = self.myDBCommunication.fetch_seq_no_hmi_status(item[2])
                if isinstance(seq_no, str) and seq_no.startswith('A'):
                    int_seq_no = int(seq_no.lstrip('A'))
                    command = bytearray(4)
                    command[0] = item[1]  # Slave ID
                    command[1] = self.SLAVE_STATE_Additions_Request
                    command[2] = int_seq_no
                    command[3] = 4
                    command.extend(struct.pack('>i', item[2]))  # Record ID
                    self.MyPort.send_hex(command)
                    print("Dispense Tx:", command)
                    # self.ReportList.remove(item)  # Remove the item after processing
                    print("report_list", self.ReportList)

                else:
                    # ['Dispensing', 'Slave ID', 'Record ID', 'Chemindex']
                    command = bytearray(4)
                    command[0] = item[1]  # Slave ID
                    command[1] = self.SLAVE_STATE_Request_Chemical_Dispense
                    command[2] = item[3]  # Chemindex
                    command[3] = 4  # Dispensing
                    command.extend(struct.pack('>i', item[2]))  # Record ID
                    self.MyPort.send_hex(command)
                    print("Dispense Tx:", command)
                    # self.ReportList.remove(item)  # Remove the item after processing
                    print("report_list",self.ReportList)

            elif item[0] == 'Completed':
                seq_no = self.myDBCommunication.fetch_seq_no_hmi_status(item[2])
                print("seq_no: ", seq_no)
                if isinstance(seq_no, str) and seq_no.startswith('A'):
                    int_seq_no = int(seq_no.lstrip('A'))
                    command = bytearray(4)
                    command[0] = item[1]  # Slave ID
                    command[1] = self.SLAVE_STATE_Additions_Request
                    command[2] = int_seq_no
                    command[3] = 5
                    command.extend(struct.pack('>i', item[2]))  # Record ID
                    command.extend(struct.pack('>i', item[4]))  # dispwt
                    self.MyPort.send_hex(command)
                    print("Completed Tx:", command)
                    # self.ReportList.remove(item)  # Remove the item after processing
                    print("report_list", self.ReportList)
                else:
                    # ['Completed', 'Slave ID', 'Record ID', 'Chemindex', 'dispwt']
                    print("Completed Rec:", item[2])
                    command = bytearray(4)
                    command[0] = item[1]  # Slave ID
                    command[1] = self.SLAVE_STATE_Request_Chemical_Dispense
                    command[2] = item[3]  # Chemindex
                    command[3] = 5  # Completed
                    command.extend(struct.pack('>i', item[2]))  # Record ID
                    command.extend(struct.pack('>i', item[4]))  # dispwt
                    self.MyPort.send_hex(command)
                    print("Completed TX:", command)
                    # self.ReportList.remove(item)  # Remove the item after processing
                    print("After remove completed:", self.ReportList)

            elif item[0] == 'Error':
                # ['Error', 'Slave ID', 'Record ID', 'Chemindex', 'Error Code']
                command = bytearray(4)
                command[0] = item[1]  # Slave ID
                command[1] = self.SLAVE_STATE_Request_Chemical_Dispense
                command[2] = item[3]  # Chemindex
                command[3] = 6  # Error Code
                command.extend(struct.pack('>i', item[2]))  # Record ID
                command.extend(struct.pack('>i', item[4]))  # Error Code
                self.MyPort.send_hex(command)
                # self.ReportList.remove(item)  # Remove the item after processing
            else:
                print("after dispense error")

        else:
            print("Total error Dispense")
    def Switch_to_next_slave(self):
        if ((self.CurrentSlaveIndex + 1) < len(self.SlaveList)):
                self.CurrentSlaveIndex += 1
        else:
            self.CurrentSlaveIndex = 0
            self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 1



    def Identify_Response_slave(self,slave_id):
        if slave_id not in ResponseHmi().response_hmi:
            ResponseHmi().response_hmi.append(slave_id)
        elif slave_id in Unresponse_Hmi().unresponse_hmi:
            Unresponse_Hmi().unresponse_hmi.remove(slave_id)

    def Run(self):
        if (len(self.SlaveList) > 0):
            if self.waitingForResponse and (time.time() - self.lastResponseTime > 5):
                print(
                    f"No response from Slave {self.SlaveList[self.CurrentSlaveIndex].SlaveID} within 5 seconds. Switching to next slave.")
                if self.SlaveList[self.CurrentSlaveIndex].SlaveID not in Unresponse_Hmi().unresponse_hmi:
                    Unresponse_Hmi().unresponse_hmi.append(self.SlaveList[self.CurrentSlaveIndex].SlaveID)
                elif self.SlaveList[self.CurrentSlaveIndex].SlaveID in ResponseHmi().response_hmi:
                    ResponseHmi().response_hmi.remove(self.SlaveList[self.CurrentSlaveIndex].SlaveID)
                self.MyPort.waitingForResponse = False
                # Move to the next slave
                if (self.CurrentSlaveIndex + 1) < len(self.SlaveList):
                    self.CurrentSlaveIndex += 1
                else:
                    self.CurrentSlaveIndex = 0

                # Reset the timer and the waitingForResponse
                self.lastResponseTime = time.time()
                self.waitingForResponse = False  # Reset
                current_slave = self.SlaveList[self.CurrentSlaveIndex]
                current_slave.ProcessStage = 0

            if self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 0:
                # Update the process stage and reset timer
                self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 1
                self.lastResponseTime = time.time()
                self.waitingForResponse = True
                print(f"Starting process for Slave {self.SlaveList[self.CurrentSlaveIndex].SlaveID}")



            else:
                if (self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 1):
                    # Check for State
                    command = bytearray(2)
                    command[0] = self.SlaveList[self.CurrentSlaveIndex].SlaveID
                    command[1] = self.SLAVE_STATE_ENQUIRE_STATE_OF_SLAVE
                    self.MyPort.send_hex(command)
                    self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 2
                elif (self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 2):
                    # Wait for response from controller
                    time.sleep(0.01)
                elif (self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 3):
                    # Response for - BatchID_Info_Request
                    # Get Batch info for this batch id self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID
                    # batchname = 'batch1'
                    batchname,fetched_data = self.myDBCommunication.BatchID_Info_Request(
                        self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID,
                        self.SlaveList[self.CurrentSlaveIndex].SlaveID)
                    try:
                        if batchname and fetched_data  is not None:

                            spaces_needed = 16 - len(batchname)
                            padded_string = batchname + " " * spaces_needed
                            # Format needed RecordNo, Chemid, Target Wt, Dispensed Wt, TankNo
                            # Example - [125,2,340,0,2] - Record No - 125, ChemID-2, TargetWt = 34.0*10 = 340, Dispewt = 0, Tank2 = 2
                            # fetched_data=[[1000000, 1, 75000, 0, 2], [125000, 2, 440, 0, 1], [126, 3, 100, 0, 1], [127,4, 1000, 0, 2], [0,0,0,0,0]]

                            # fetched_data = self.myDBCommunication.fetch_batch_data_hmi(self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID)
                            command = bytearray(3)
                            command[0] = self.SlaveList[self.CurrentSlaveIndex].SlaveID
                            command[1] = self.SLAVE_STATE_BatchID_Info_Request
                            command[2] = 0
                            command.extend(padded_string.encode())
                            self.MyPort.send_hex(command)

                            i: bytes = 1
                            for item in fetched_data:
                                command = bytearray(3)
                                command[0] = self.SlaveList[self.CurrentSlaveIndex].SlaveID
                                command[1] = self.SLAVE_STATE_BatchID_Info_Request
                                command[2] = i
                                command.extend(struct.pack('>i', item[0]))  # Record ID
                                command.extend(item[1].to_bytes(1, 'big'))  # Chem ID
                                command.extend(struct.pack('>i', item[2]))  # Target Wt
                                command.extend(struct.pack('>i', item[3]))  # Dispensed Wt
                                command.extend(item[4].to_bytes(1, 'big'))  # Tank No
                                self.MyPort.send_hex(command)
                                i += 1
                            self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            log_message = f"{current_time} - HMI:{self.SlaveList[self.CurrentSlaveIndex].SlaveID} Tx-Data:{batchname, fetched_data}"
                            # Log the message into a .log file
                            with open("Request-Batch-Info.log", "a") as log_file:
                                log_file.write(log_message + "\n")
                        else:

                            if (self.CurrentSlaveIndex + 1) < len(self.SlaveList):
                                self.CurrentSlaveIndex += 1
                            else:
                                self.CurrentSlaveIndex = 0
                            self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 1

                    except Exception as e:
                        print("error:", e)


                elif (self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 4):
                    # Response for - Request_Chemical_Dispense
                    # func(recordid, chemindex) need event to trigger dispening, completed and error status in request Queue
                    # todo add to dispense queue
                    # todo_store_record(self.SlaveList[self.CurrentSlaveIndex].RequestToDispenseChemicalRecordID)
                    command = bytearray(4)
                    command[0] = self.SlaveList[self.CurrentSlaveIndex].SlaveID
                    command[1] = self.SLAVE_STATE_Request_Chemical_Dispense
                    command[2] = self.SlaveList[self.CurrentSlaveIndex].ChemDisplayIndex
                    command[3] = 3  # ACK IDENTIFIER
                    command.extend(struct.pack('>i', self.SlaveList[
                        self.CurrentSlaveIndex].RequestToDispenseChemicalRecordID))  # Record ID
                    self.MyPort.send_hex(command)
                    self.myDBCommunication.fetch_chemical_id(
                        self.SlaveList[self.CurrentSlaveIndex].RequestToDispenseChemicalRecordID)
                    self.ChemicalsRequestedFromHMI.append(['Akc', self.SlaveList[self.CurrentSlaveIndex].SlaveID,
                                                           self.SlaveList[
                                                               self.CurrentSlaveIndex].RequestToDispenseChemicalRecordID,
                                                           self.SlaveList[self.CurrentSlaveIndex].ChemDisplayIndex])
                    print("sending_command",command)
                    self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0
                elif (self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 5):
                    # Response for - Fetch_Chemical_Names
                    # chemNames = ['ammonia', 'calcium', 'sodium', 'sulferic', 'sulpher', 'sal', '', '', '', '', '', '', 'Chem1', '', '', 'Chemical2', '', '', '', '', 'Sulphuric', '', '', 'oxygen', '', '', 'nitrous', '', '', '']
                    # chemNames = ['ammonia', 'calcium', 'sodium', 'sulferic', 'sulpher', 'sal', '', 'carbon', '', 'methen', '', '', 'ethanal', '', 'oxide', '', '', 'bromine', '', 'chlorine', '', 'hydronium', '', 'pottasiam', '', 'sodiumboud', '', '', 'acetec', '']
                    chemNames = self.myDBCommunication.Fetch_Chemical_Names()
                    i: bytes = 1
                    for item in chemNames:
                        # todo check len greatet than 10
                        spaces_needed = 16 - len(item)
                        padded_string = item + " " * spaces_needed
                        command = bytearray(3)
                        command[0] = self.SlaveList[self.CurrentSlaveIndex].SlaveID
                        command[1] = self.SLAVE_STATE_Fetch_Chemical_Names
                        command[2] = i
                        command.extend(padded_string.encode())
                        self.MyPort.send_hex(command)
                        i += 1
                    self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0
                elif (self.SlaveList[self.CurrentSlaveIndex].ProcessStage == 6):
                    # Response for - Additions Request
                    # Func(Batchid, AdNo, ChemID, TargetWt, TankNo) will return record id
                    # Save it in self.SlaveList[self.CurrentSlaveIndex].RequestToDispenseChemicalRecordID
                    #         self.Additions_BatchID = 0

                    if self.myDBCommunication.data_exists_batch(
                            self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID,
                            self.SlaveList[self.CurrentSlaveIndex].Additions_No,):

                        error_message = "Error: The data already exists."
                        (self.Error_Callback(error_message))
                        return

                    result = self.myDBCommunication.AdditionsRequest(
                        self.SlaveList[self.CurrentSlaveIndex].SlaveID,
                        self.SlaveList[self.CurrentSlaveIndex].CurrentBatchID,
                        self.SlaveList[self.CurrentSlaveIndex].Additions_No,
                        self.SlaveList[self.CurrentSlaveIndex].Additions_ChemID,
                        self.SlaveList[self.CurrentSlaveIndex].Additions_TargetWt,
                        self.SlaveList[self.CurrentSlaveIndex].Additions_TankNo
                    )
                    # Unpack the result safely, ensuring that it's not None and has two elements
                    if result is not None and len(result) == 2:
                        self.SlaveList[self.CurrentSlaveIndex].Additions_RecordID, addno = result

                        if addno is not None:
                            if addno == ('A' + str(self.SlaveList[self.CurrentSlaveIndex].Additions_No)):
                                # self.SlaveList[self.CurrentSlaveIndex].Additions_RecordID = 125 # Will be unique database table ID
                                command = bytearray(4)
                                command[0] = self.SlaveList[self.CurrentSlaveIndex].SlaveID
                                command[1] = self.SLAVE_STATE_Additions_Request
                                command[2] = self.SlaveList[self.CurrentSlaveIndex].Additions_No
                                command[3] = 3  # ACK IDENTIFIER
                                command.extend(struct.pack('>i', self.SlaveList[
                                    self.CurrentSlaveIndex].Additions_RecordID))  # Additions Record ID
                                self.MyPort.send_hex(command)
                                self.myDBCommunication.AdditionsRequest_2(self.SlaveList[self.CurrentSlaveIndex].Additions_RecordID)
                                self.ChemicalsRequestedFromHMI.append(
                                    ['Akc', self.SlaveList[self.CurrentSlaveIndex].SlaveID,
                                     self.SlaveList[self.CurrentSlaveIndex].Additions_RecordID,
                                     0])
                            self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0
                    else:
                        self.SlaveList[self.CurrentSlaveIndex].ProcessStage = 0


    def Connect(self, portName, baudRate, rx_buffer_size=4096, tx_buffer_size=4096):
        return self.MyPort.Connect_Port(portName, baudRate, rx_buffer_size, tx_buffer_size)

    def Disconnect(self):
        return self.MyPort.Disconnect_Port()
    def is_connected(self):
        try:
            return self.MyPort.is_port_open()
        except Exception as e:
            print(f"Connection check failed: {e}")
            return False
    def __del__(self):
        self.Disconnect()


if __name__ == "__main__":

    SlaveIDList = [10]
    myDev = DirectDosing_HMI_Network_V1(SlaveIDList)
    myDBCommunication = DatabaseInterfaceForHMI()
    myDBCommunication.dispense_chemical_list((93,1))
    # myDBCommunication.check_dispense_list_hmi((104,1))
    # if myDBCommunication.check_dispense_list_hmi is True:
    #     print("True")
    # else:
    #     print("false")

    # Configurations


    if (myDev.Connect("COM4", 9600)):
        while True:
            myDev.Run()
            time.sleep(0.250) # Loop Time
    else:
        print("port not available")
