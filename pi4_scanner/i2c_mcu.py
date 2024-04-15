from smbus import SMBus
import time
from enum import Enum

class I2C_Mcu:
    
    class McuStatus(Enum):
        OK = 0
        ERR = 1
        TENSION = 2
    
    def __init__(self):
        print("starting i2c")
        self.__pico_addr = 0x3F
        self.__bus = SMBus(0)
        time.sleep(0.01)
        
    def close(self):
        print("closes i2c")
        del self
        
    def request_next_frame(self, num_of_frames: int = 1) -> McuStatus:
        
        if num_of_frames > 255:
            num_of_frames = 255
        
        if num_of_frames < 0:
            num_of_frames = 0
        
        frames_in_bytes = num_of_frames.to_bytes(1, 'big') 
        self.__bus.write_i2c_block_data(self.__pico_addr, 0x02, list(frames_in_bytes))
        
        time.sleep(0.2)
        while True:
            try:
                status = self.__bus.read_byte(self.__pico_addr)
                break
            
            except IOError as e:
                time.sleep(0.2)
            
            except Exception as e:
                raise e
        
        if status > 64:
                status = 0
        
        #print("status:", status)
        
        time.sleep(0.1)
        
        return I2C_Mcu.McuStatus(status)
    
    def request_rewind(self, run = False):
        run_value = 0
        if run is True:
            run_value = 1
        
        self.__bus.write_i2c_block_data(self.__pico_addr, 0x06, [run_value & 0xFF])

    def request_led_level(self, led_level = 512) -> McuStatus:
        
        if led_level >= 512:
            led_level = 511
        elif led_level < 0:
            led_level = 0
        
        byte1 = (int(led_level) >> 1) & 0xFF
        byte2 = (int(led_level) & 1) << 7
        
        #print(byte1, byte2)
        
        light_values = [byte1, byte2]
        
        self.__bus.write_i2c_block_data(self.__pico_addr, 0x05, light_values)
        time.sleep(0.25)
        return I2C_Mcu.McuStatus.OK
    
    def set_sprocket_offset(self, offset):
        
        if offset > 255:
            offset = 255
        
        if offset < 0:
            offset = 0
        
        offset_byte = offset.to_bytes(1, 'big')
        
        self.__bus.write_i2c_block_data(self.__pico_addr, 0x03, list(offset_byte))
        
        time.sleep(0.2)
        status = self.__bus.read_byte(self.__pico_addr)
        
        time.sleep(0.1)
        
        return I2C_Mcu.McuStatus(status)
