import struct
from USBvcpSerializer_V1 import USBvcpSerializer_V1
import time
from database import *

class WeigingStation_Info:
    def __init__(self, stationID : bytes):
        self.StationID = stationID
        self.CurrentState = 0

        self.ProcessResponseState = 0
        self.ErrorCode = 0
        self.DispensedWt = 0
        self.ValveNo = 0
        self.RecordID = 0
        self.WaterDispensedWt = 0

class ChemicalCompleted:
    chem_complete = []

class ChemicalDispense:
    chem_dispense = []

class ErrorCode:
    dispense_error = []

class Responsemachine:
    response_machine=[]

class DirectDosing_WeigingSystem_V1:
    def __init__(self, slaveID, noOfAvailableStations):
        self.MyPort = USBvcpSerializer_V1(self.Rx_Callback, self.Tx_Callback, self.Error_Callback)
        self.myDBCommunication = DatabaseInterfaceForWeigingSytsem()

        self.CurrentSlaveID = slaveID

        self.AvailableStationList = []
        stationID = 1
        self.ProcessStage = 0
        self.timoutCounter = 0
        for i in range(noOfAvailableStations):
            # print(stationID)
            itme = WeigingStation_Info(stationID)
            self.AvailableStationList.append(itme)
            # print(type(self.AvailableStationList))
            # print(self.AvailableStationList)
            # print(self.AvailableStationList[i].StationID)
            stationID += 1

        # States and Constants
        self.MASTER_ID = 255
        self.SLAVE_STATE_ENQUIRE_STATE_OF_SLAVE : bytes = 0
        self.SLAVE_STATE_Free : bytes = 1
        self.SLAVE_STATE_Busy : bytes = 2
        self.SLAVE_STATE_Completed : bytes = 3
        self.SLAVE_STATE_ErrorCode : bytes = 4
        self.SLAVE_STATE_Disabled : bytes = 5

    def Rx_Callback(self, msg, data):
        print(f"RX:{data}")
        self.Rx_Message_Machine(data)
        if(data[0] == self.MASTER_ID and data[1] == self.CurrentSlaveID):
            if data[1] not in Responsemachine.response_machine:
                Responsemachine.response_machine.append(data[1])
            if (data[2] == self.SLAVE_STATE_ENQUIRE_STATE_OF_SLAVE):
                for i in range(len(self.AvailableStationList)):
                    self.AvailableStationList[i].CurrentState = data[3+i]
                self.ProcessStage = 2 # Process Slave State Response
            elif(data[2] == self.SLAVE_STATE_Free):
                stationID = data[3]
                self.AvailableStationList[stationID - 1].ProcessResponseState = 0
            elif (data[2] == self.SLAVE_STATE_Completed):
                if (data[3] > 0):
                    stationID = data[3]
                    self.AvailableStationList[stationID - 1].ProcessResponseState = self.SLAVE_STATE_Completed
                    self.AvailableStationList[stationID - 1].RecordID = struct.unpack('>i', data[4:8])[0]
                    self.AvailableStationList[stationID - 1].ValveNo = data[8]
                    self.AvailableStationList[stationID - 1].DispensedWt = struct.unpack('>i', data[9:13])[0]
                    self.AvailableStationList[stationID - 1].WaterDispensedWt = struct.unpack('>i', data[13:17])[0]
            elif (data[2] == self.SLAVE_STATE_ErrorCode):
                stationID = data[3]
                self.AvailableStationList[stationID - 1].ErrorCode = data[4]
                self.AvailableStationList[stationID - 1].ProcessResponseState = self.SLAVE_STATE_ErrorCode


    def Rx_Message_Machine(self,data):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{current_time} - Machine: RX:{data}"

        # Log the message into a .log file
        with open("Tx_RX_Command.log", "a") as log_file:
            log_file.write(log_message + "\n")
    def Tx_Callback(self, msg):
        print(f"TX:{msg}")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{current_time} - Machine: TX:{msg}"

        # Log the message into a .log file
        with open("Tx_RX_Command.log", "a") as log_file:
            log_file.write(log_message + "\n")

    def Error_Callback(self, msg):
        print(f"Error:{msg}")
        # self.myDBCommunication.UpdateErrorCode(msg, self.AvailableStationList.StationID)

    def Run(self):
        try:
            if(len(self.AvailableStationList) > 0):
                if (self.ProcessStage == 0):
                    # Enquire for Slave Station States
                    command = bytearray(2)
                    command[0] = self.CurrentSlaveID
                    command[1] = self.SLAVE_STATE_ENQUIRE_STATE_OF_SLAVE
                    self.MyPort.send_hex(command)
                    self.ProcessStage = 1
                    self.timoutCounter = 0
                elif (self.ProcessStage == 1):
                    # Wait for Response
                    time.sleep(0.01)
                    self.timoutCounter += 1
                    if(self.timoutCounter > 200):
                        self.ProcessStage = 0
                elif(self.ProcessStage == 2):
                    # Process Station States
                    for i in range(len(self.AvailableStationList)):
                        if(self.AvailableStationList[i].CurrentState == 0 or self.AvailableStationList[i].CurrentState == self.SLAVE_STATE_Busy or self.AvailableStationList[i].CurrentState == self.SLAVE_STATE_Disabled):
                            self.AvailableStationList[i].ProcessResponseState = 0
                        elif(self.AvailableStationList[i].CurrentState == self.SLAVE_STATE_Free):
                            # Check if Queue has available chemicals for this stations
                            id = self.AvailableStationList[i].StationID
                            print("StationID:",id)
                            avalableChem = self.myDBCommunication.IsChemicalAvailableForDispense(id)
                            if avalableChem != None:
                                print("available:",avalableChem)
                                # avalableChem = [Record ID, Station ID, Valve No, Target Wt, Water Wt, MachineID]
                                # avalableChem = [Station ID, Record ID, Valve No, Target Wt, Water Wt, MachineID]
                                if(avalableChem != None ):
                                    if(len(avalableChem) >= 6):
                                        command = bytearray(2)
                                        command[0] = self.CurrentSlaveID
                                        command[1] = self.SLAVE_STATE_Free
                                        command.extend(avalableChem[0].to_bytes(1, 'big')) # Station ID
                                        command.extend(struct.pack('>i', avalableChem[1])) # Record ID
                                        command.extend(avalableChem[2].to_bytes(1, 'big')) # Valve No
                                        command.extend(struct.pack('>i', avalableChem[3])) # Target Wt
                                        command.extend(struct.pack('>i', avalableChem[4])) # Water Wt
                                        command.extend(avalableChem[5].to_bytes(1, 'big')) # Machine ID
                                        self.MyPort.send_hex(command)
                                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        log_data = (
                                            f"Station : {avalableChem[0]} , Recid : {avalableChem[1]} , Volveno : {avalableChem[2]} , TargetWt : {avalableChem[3]} , DispWt : {avalableChem[4]} , Tank : {avalableChem[5]}")
                                        log_message = f"{current_time} - Station:{avalableChem[0]} Transfer Data: {log_data}"
                                        with open("Tx_Data_Machine.log", "a") as log_file:
                                            log_file.write(log_message + "\n")
                                        if avalableChem[1] not in ChemicalCompleted.chem_complete:
                                            ChemicalDispense.chem_dispense.append(avalableChem[1])
                                            print("ChemicalDispense:", ChemicalDispense.chem_dispense)
                                        self.AvailableStationList[i].ProcessResponseState = 1
                                else:
                                    self.AvailableStationList[i].ProcessResponseState = 0
                            else:
                                self.AvailableStationList[i].ProcessResponseState = 0
                        elif(self.AvailableStationList[i].CurrentState ==  self.SLAVE_STATE_Completed):
                            command = bytearray(2)
                            command[0] = self.CurrentSlaveID
                            command[1] = self.SLAVE_STATE_Completed
                            command.extend(self.AvailableStationList[i].StationID.to_bytes(1, 'big')) # Station ID
                            self.MyPort.send_hex(command)
                            self.AvailableStationList[i].ProcessResponseState = 1
                        elif(self.AvailableStationList[i].CurrentState == self.SLAVE_STATE_ErrorCode):
                            command = bytearray(2)
                            command[0] = self.CurrentSlaveID
                            command[1] = self.SLAVE_STATE_ErrorCode
                            command.extend(self.AvailableStationList[i].StationID.to_bytes(1, 'big')) # Station ID
                            self.MyPort.send_hex(command)
                            self.AvailableStationList[i].ProcessResponseState = 1
                    self.ProcessStage =  3
                elif(self.ProcessStage == 3):
                    # Processing for all response
                    for i in range(len(self.AvailableStationList)):
                        if(self.AvailableStationList[i].ProcessResponseState == self.SLAVE_STATE_Completed):
                            # Update Database For Completion Report
                            self.myDBCommunication.DispenseCompleted(self.AvailableStationList[i].RecordID,
                                              self.AvailableStationList[i].StationID,
                                              self.AvailableStationList[i].ValveNo,
                                              self.AvailableStationList[i].DispensedWt,
                                              self.AvailableStationList[i].WaterDispensedWt)
                            # if self.AvailableStationList[i].RecordID not in ChemicalDispense.chem_dispense:
                            ChemicalCompleted.chem_complete.append(self.AvailableStationList[i].RecordID)
                            print("ChemicalCompleted:",ChemicalCompleted.chem_complete)
                            self.AvailableStationList[i].ProcessResponseState = 0 # Process Response Completed
                        elif(self.AvailableStationList[i].ProcessResponseState == self.SLAVE_STATE_ErrorCode):
                            # Update Error Code in GUI and Logs
                            self.myDBCommunication.UpdateErrorCode(self.AvailableStationList[i].StationID,
                                            self.AvailableStationList[i].ErrorCode)
                            ErrorCode.dispense_error.append((self.AvailableStationList[i].RecordID,self.AvailableStationList[i].ErrorCode))
                            self.AvailableStationList[i].ProcessResponseState = 0 # Process Response Completed

                    WaitingForResponse = False
                    for i in range(len(self.AvailableStationList)):
                        if (self.AvailableStationList[i].ProcessResponseState > 0):
                            WaitingForResponse = True
                    if(WaitingForResponse == False):
                        self.ProcessStage = 0 # Check for States again all response received
                    time.sleep(0.01)
                else:
                    self.ProcessStage = 0 # Check for States again all response received
        except Exception as e:
            print("Error in Weiging:",e)
            self.AvailableStationList[i].ProcessResponseState = 0

                    
    def Connect(self, portName, baudRate, rx_buffer_size=4096, tx_buffer_size=4096):
        return self.MyPort.Connect_Port(portName, baudRate,rx_buffer_size,tx_buffer_size)
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
    slaveID = 20
    noOfStations = 2
    myDev = DirectDosing_WeigingSystem_V1(slaveID, noOfStations)
    # Configurations


    if (myDev.Connect("COM4", 9600)):
        while True:
            myDev.Run()
            time.sleep(0.250) # Loop Time
    else:
        print("port not available")
