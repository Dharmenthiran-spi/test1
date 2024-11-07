import serial  # pip install pyserial
import threading  # just import
import time  # just import
from collections import deque  # just import
import struct  # Python struct module can be used in handling binary data stored
import crcmod  # crc checking module

# Updated
# 16/5/24 - CRC Option Enabled
# CRCRequired and With feedback Initialize as True

# LAST UPDATE 20/05/24 ( CHANGE CRC AND FEEDBACK IS SELECTED FORMAT  )


''' AR - E YOU USING THIS LIBRARY YOU ARE COMFORM USING CALLBACK FUNCTION IN YOUR PROGRAMME
EXAMPLE:callbackRx=(YOUR PROGRAMME  CODE RX FUNCTION), callbackTx=(YOUR PROGRAMME CODE TX FUNCTION),
callbackError=(YOUR PROGRAMME CODE ERROR FUNCTION)'''


class USBvcpSerializer_V1():
    def __init__(self, callbackRx=None, callbackTx=None, callbackError=None):
        self.TxQueue = deque()  # should hold bytes
        self.serial = serial.Serial()  # serial open comment
        self.txcommand = ""
        self.waitingForResponse = False
        self.tx_thread_sleep_time = 0.1  # Tx Thread Sleep Time. This is incremented to match rx_reponse_wait_time for repeat command
        self.rx_thread_sleep_time = 0.00001    #0.00001
        self.rx_data = ""
        self.rx_reponse_wait_time = 2.3 #0.1  # Wait time till resend command is executed
        self.rx_data_sleep_time = 0.1
        self.on_received = callbackRx
        self.on_msg_sent = callbackTx
        self.on_error = callbackError
        self.tx_counter = 0
        self.rx_counter = 0
        self.crc_count = 0
        self.crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)  # CRC CHECK CONDITION

        self.isCRCRequired = True  # CRC Initialize as True
        self.feedback = True  # Feedback Initialize as True

    def without_feedback(self, msg):
        """Enable or disable waiting for response (with or without feedback)."""
        self.feedback = msg

    def crc_checking(self, msg):
        """Enable or disable CRC checking."""
        self.isCRCRequired = msg

    def send_hex(self, msg):  # example send hex values  (send_hex('[41, 42]'))
        if self.serial.is_open:
            try:

                    if self.isCRCRequired:  ## self.isCRCRequired == True

                        crc_val = self.crc16(msg)
                        HighByte = (crc_val >> 8) & 0xff

                        lowByte = crc_val & 0xff
                        msg.append(lowByte)
                        msg.append(HighByte)
                        self.TxQueue.append(msg)
                    else:
                        self.TxQueue.append(msg)  ## self.isCRCRequired == False
            except ValueError:
                self.on_error("ERROR: please only input hex value")

    def send_ascii(self, msg):  # example send ascii values  (send_ascii('ab'))
        if self.serial.is_open:
            try:
                if msg.strip() == "":
                    self.on_error("ERROR:Please input first your message ")
                    return

                send_data = bytearray(bytes(msg.encode("utf-8")))
                if self.isCRCRequired:  ## self.isCRCRequired == True

                    crc_val = self.crc16(send_data)
                    HighByte = (crc_val >> 8) & 0xff
                    lowByte = crc_val & 0xff
                    send_data.append(lowByte)
                    send_data.append(HighByte)
                    self.TxQueue.append(send_data)
                else:
                    self.TxQueue.append(send_data)  ## self.isCRCRequired == False
            except Exception as ex:
                print(ex)

    def Connect_Port(self, portName, baudRate, rx_buffer_size=4096, tx_buffer_size=4096):  # (Connect_Port('COM4',9600))
        """ Connected serial port """
        isValidationOk = True
        if portName is None and baudRate is not None:
            self.on_error("ERROR: Please Select Your Port")
            isValidationOk = False
        elif baudRate is None and portName is not None:
            self.on_error("ERROR: Please Select Your Baudrate")
            isValidationOk = False

        try:
            if isValidationOk:
                if self.serial is None or not self.serial.is_open:
                    """ serial open statement """
                    self.serial = serial.Serial(
                        port=portName,
                        baudrate=baudRate,
                        bytesize=serial.EIGHTBITS,
                        timeout=2,
                        stopbits=serial.STOPBITS_ONE,
                        parity=serial.PARITY_NONE,
                        rtscts=False
                    )
                    self.serial.set_buffer_size(rx_size=rx_buffer_size, tx_size=tx_buffer_size)

                    self.isAlive = True

                    """ TX AND RX thread start """
                    self.tx_thread = threading.Thread(target=self.tx_thread_callback, name='tx_thread')
                    self.rx_thread = threading.Thread(target=self.rx_thread_callback, name='rx_thread')
                    self.tx_thread.start()
                    self.rx_thread.start()

                    self.on_msg_sent("Connected")
                    return isValidationOk

        except Exception as ex:
            self.on_error("ERROR-Connect Exception please select port and baudrate")
            return False

    def is_port_open(self):
        return self.serial.is_open if hasattr(self.serial, 'is_open') else False
    def Disconnect_Port(self):
        self.isAlive = False

        if self.serial and self.serial.is_open:
            """ serial close statement """
            self.serial.close()
        if hasattr(self, 'tx_thread') and hasattr(self, 'rx_thread'):
            """ TX AND RX thread close """
            self.tx_thread.join()
            self.rx_thread.join()
            # print("Disconnected")
        self.on_msg_sent("Disconnected")

    def tx_thread_callback(self):

        """ The serial write(TX) statement uses two concepts:

            1.You need feedback (self.feedback == True), and you are always waiting for a response.
            2.You don't need feedback (self.feedback == False), and you are never waiting for a response."""
        try:
            while (self.isAlive):

                if self.crc_count <= 5:
                    if self.feedback:  ##  self.feedback == True

                        if not self.waitingForResponse:  ## waiting for response  Initialize as False
                            if len(self.TxQueue) > 0:
                                self.txcommand = self.TxQueue.popleft()

                                cmd = f"{' '.join(format(x, '02x') for x in self.txcommand)}"

                                self.on_msg_sent(cmd)

                                self.serial.write(self.txcommand)
                                self.waitingForResponse = True  ##  waiting for response  change  as True
                                self.response_wait_timeout = 0
                        else:
                            if self.response_wait_timeout >= self.rx_reponse_wait_time:
                                self.on_msg_sent(f"{self.txcommand}")
                                self.serial.write(self.txcommand)
                                self.response_wait_timeout = 0
                            else:
                                self.response_wait_timeout += self.tx_thread_sleep_time
                        time.sleep(self.tx_thread_sleep_time)

                    else:  ##  self.feedback == False
                        if len(self.TxQueue) > 0:
                            self.txcommand = self.TxQueue.popleft()

                            cmd = f"{' '.join(format(x, '02x') for x in self.txcommand)}"

                            self.on_msg_sent(cmd)

                            self.serial.write(self.txcommand)
                else:
                    time.sleep(1)
                    self.serial.reset_output_buffer()
                    self.serial.reset_input_buffer()
                    if self.serial.in_waiting > 0:
                        data = self.serial.read(self.serial.in_waiting)
                        print(data)

                    print("Buffer flushed. Resetting After Max CRC Error Count Reached")
                    self.crc_count = 0

        except Exception as e:
            print("while unplug in process:",e)

        finally:
            try:
                self.Disconnect_Port()
            except RuntimeError as e:
                print(f"RuntimeError during port disconnection: {e}")
            except Exception as e:
                print(f"Unexpected error during port disconnection: {e}")

    def validate_crc(self, data):

        """ CRC (Cyclic Redundancy Check) is a method used to detect errors in data transmission over serial communication.
        When data is sent through a serial port at a specified baud rate, CRC generates a check sum value based on the data.
        The receiver also calculates the CRC checksum and compares it with the transmitted one to ensure data integrity and detect any errors
        that may have occurred during transmission. """

        """ you need crc checking declare  CRC Initialize as self.isCRCRequired  = True otherwise 
            declare  CRC Initialize as self.isCRCRequired  = False """
        cmd = f"{' '.join(format(x, '02x') for x in bytearray(data))}"
        print("crc_Rx_Data:",cmd)
        if len(data) >= 2:
            received_crc = int.from_bytes(data[-2:], byteorder='little')
            print(f"Received CRC: {received_crc:04X}")
            calculated_crc = self.crc16(data[:-2])
            print(f"Calculated CRC: {calculated_crc:04X}")

            return received_crc == calculated_crc
        return False

    def rx_thread_callback(self):

        """ The serial read(RX) statement uses two concepts:

            1.You need feedback (self.feedback == True), and you are always waiting for a response.
            2.You don't need feedback (self.feedback == False), and you are never waiting for a response."""
        try:
            while self.isAlive:
                if self.feedback:  ##  self.feedback == True
                    if self.serial.is_open:
                        if self.serial.in_waiting > 0:
                            #time.sleep(0.05)
                            time.sleep(0.01)
                            bytesToRead = self.serial.in_waiting
                            if bytesToRead > 0:
                                time.sleep(0.05)
                                bytesToRead = self.serial.in_waiting
                                self.rx_data = self.serial.read(bytesToRead)  ## READ COMMENT

                                if self.isCRCRequired:  ##  self.isCRCRequired == True

                                    if self.validate_crc(self.rx_data):
                                        cmd = f"{' '.join(format(x, '02x') for x in bytearray(self.rx_data[:-2]))}"
                                        self.on_received(cmd,self.rx_data)
                                        self.rx_counter += 1
                                        self.waitingForResponse = False
                                        # self.crc_count = 0
                                    # else:
                                    #     self.crc_count += 1
                                    #     if self.crc_count <= 5:
                                    #         # Retry sending the last command
                                    #         self.tx_thread_callback()
                                    #     else:
                                    #         # Flush and reset
                                    #         self.serial.reset_output_buffer()
                                    #         self.serial.reset_input_buffer()
                                    #         print("Buffer flushed. Resetting After Max CRC Error Count Reached")
                                    #         self.crc_count = 0
                                    else:
                                        cmd = f"{' '.join(format(x, '02x') for x in bytearray(self.rx_data))}"
                                        self.on_error(f"CRC Mismatch.{cmd}")
                                        self.crc_count+=1

                                        print("crc_count:",self.crc_count)
                                        # time.sleep(0.5)


                                else:  ##  self.isCRCRequired == False

                                    cmd = f"{' '.join(format(x, '02x') for x in bytearray(self.rx_data))}"
                                    self.on_received(cmd,self.rx_data)

                                    self.rx_counter += 1
                                    self.waitingForResponse = False




                        else:
                            time.sleep(self.rx_thread_sleep_time)
        except Exception as e:
            print(f"Unexpected error in RX thread: {e}")

    def __del__(self):
        self.Disconnect_Port()


if __name__ == '__main__':

    errorCount = 0
    rxCount = 0
    txCount = 0


    def rx_callback(data):
        print(f"RX : {data}")
        global rxCount
        rxCount += 1


    def tx_callback(msg):
        print(f"TX: {msg}")
        global txCount
        txCount += 1


    def er_callback(msg):
        global errorCount
        errorCount += 1
        print(f"ER: {msg}")


    myPort = USBvcpSerializer_V1(rx_callback, tx_callback, er_callback)
    myPort.Connect_Port("COM4", 115200)  # 921600

    num = 0

    # Slow Speed Test - ASCII

    print('Slow Speed Test - ASCII - Start')
    for i in range(10):
        myPort.send_ascii('This is Sakthi\r\n')
        time.sleep(1)
    print('Slow Speed Test - ASCII - Ends')

    # # Slow Speed Test - HEX

    print('Slow Speed Test - Hex - Start')
    for i in range(10):
        byteValues = bytearray([0, 1, 2, 10, 12, 14, 15, 16, 20, 25, 127, 255, i])
        myPort.send_hex(byteValues)
        time.sleep(1)
    print('Slow Speed Test - Hex - Ends')

    # Full Speed Test - ASCII

    max_count = 10
    current_count = 0
    queue_max_test_value = 20000  # These many Commands will be added to Queue at 0.1sec interval
    temp_count_val = queue_max_test_value

    print("Starting to add data to Queue - ASCII")
    for i in range(max_count):
        current_count += 1
        myPort.send_ascii(f'count value is {current_count}')

        if current_count >= temp_count_val:
            time.sleep(0.05)
            temp_count_val += queue_max_test_value
            print(f"Added {current_count}. Tx: {txCount} RX: {rxCount} Error: {errorCount}")
    print("All ASCII data added. Waiting for transmit to complete")
    while len(myPort.TxQueue) > 0:
        time.sleep(0.001)
    time.sleep(0.01)

    # Full Speed Test - Hex

    current_count = 0
    temp_count_val = queue_max_test_value
    print("Starting to add data to Queue - HEX")
    for i in range(max_count):
        current_count += 1
        # <I little Endian, >I big endian for 32 bit number
        # <h little Endian, >h big endian for 16 bit number
        current_count_byte_array = struct.pack('<I', current_count)  # <I little Endian, >I big endian
        print(current_count_byte_array)
        print(type(current_count_byte_array))
        byteValues = bytearray([0, 1, 2, 10, 12, 14, 15, 16, 20, 25, 127, 255])
        byteValues.extend(current_count_byte_array)
        myPort.send_hex(byteValues)

        if current_count >= temp_count_val:
            time.sleep(0.1)
            temp_count_val += queue_max_test_value
            print(f"Added {current_count}. Tx: {txCount} RX: {rxCount} Error: {errorCount}")
    print("All HEX data added. Waiting for transmit to complete")
    while len(myPort.TxQueue) > 0:
        time.sleep(0.001)
    time.sleep(0.01)

    print("Completed")

    myPort.Disconnect_Port()
    print(f"Total Tx: {txCount} RX: {rxCount} Error: {errorCount}")

    time.sleep(0.00001)

# # image test  1400000  hex datas and 64 bytes :
#     import random
#     num_items = 1400000  # Adjust this to 10 for testing

#     # Loop to generate and enqueue random hex values
#     for i in range(num_items):
#         # Generate a random 64-byte value
#         byte_values = bytearray([random.getrandbits(8) for _ in range(10)])
#         myPort.send_hex(byte_values)

#     print("All HEX data added. Waiting for transmit to complete")
#     while len(myPort.TxQueue) > 0:
#         time.sleep(0.001)
#     time.sleep(0.01)


#     print("Completed")


#     myPort.Disconnect_Port()
#     print(f"Total Tx: {txCount} RX: {rxCount} Error: {errorCount}")

#     time.sleep(0.00001)