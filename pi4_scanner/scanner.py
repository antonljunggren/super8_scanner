import glob
import os
import cv2 as cv
from camera import Camera
from i2c_mcu import I2C_Mcu

from threading import Thread
import queue

class Scanner:
    
    def __init__(self):
        self.__camera = Camera()
        self.__i2c_mcu = I2C_Mcu()
        self.__save_location = "/home/pi/Desktop/scanner_share/frames/"

        self.__sprokcet_offset = 30
        
        self.__writeQueue = queue.Queue(maxsize=10)
        self.__writeThreads = []
        
        for _ in range(3):
            writeThread = Thread(target=self.__image_write, args=(self.__writeQueue,))
            writeThread.setDaemon(False)
            writeThread.start()
            self.__writeThreads.append(writeThread)
        
        self.__current_frame_number = len(self.__get_saved_frames())
        
        print("scanned frames:",  self.__current_frame_number)
        
        self.__i2c_mcu.request_led_level(500)
    
    def close(self):
        print("shutdown scanner")
        for x in range(len(self.__writeThreads)):
            self.__writeQueue.put((None, None, None))
        
        self.__writeQueue.join()
        
        for x in range(len(self.__writeThreads)):
            self.__writeThreads[x].join()
        
        self.__i2c_mcu.request_led_level(0)
        self.__i2c_mcu.close()
        self.__camera.close()
        print("scanner closed")
    
    def __image_write(self, queue):
        while True:
            image, metadata, filename = queue.get(block=True, timeout=None)
            if image is None:
                queue.task_done()
                break
            
            print("save file:", filename)
            self.__camera.save_dng(image, metadata, filename)

            queue.task_done()
    
    def __extract_frame_index(self, file_name):
        number = int(file_name.split('_')[-1].split('.')[0])
        return number
    
    def __get_saved_frames(self):
        return sorted(glob.glob(os.path.join(self.__save_location, "frame_*.*")), key=self.__extract_frame_index, reverse=False)
     
    def get_frames_scanned_cnt(self):
        return self.__current_frame_number
    
    def get_awb_modes(self):
        return self.__camera.get_awb_modes()
    
    def set_awb_mode(self, mode):
        self.__camera.set_awb_mode(mode)

    def get_frame(self):
        image = self.__camera.get_frame()
        image = cv.rotate(image, cv.ROTATE_90_CLOCKWISE)
        return image
    
    def get_preview(self):
        image = self.__camera.get_frame()
        image = cv.rotate(image, cv.ROTATE_90_CLOCKWISE)
        image = cv.resize(image, (600, 800))
        return image
    
    def start_stop_rewind(self, start = False):
        self.__i2c_mcu.request_rewind(start)

    def scan(self):
        print("scan frame")
        filename = f'frame_{self.__current_frame_number}.dng'
        filename = os.path.join(self.__save_location, filename)
        image, metadata = self.__camera.get_raw_frame()
        self.__writeQueue.put((image, metadata, filename))
        
        preview = self.get_preview()
        self.__current_frame_number += 1
        status = self.advance_frame()
        
        return status, preview
    
    def advance_frame(self, frames = 1):
        status = self.__i2c_mcu.request_next_frame(frames)
                    
        if status is not I2C_Mcu.McuStatus.OK:
            print("error i2c:", status)
        
        return status
    
    def get_color_gains(self):
        return self.__camera.get_color_gains()
    
    def set_color_gains(self, new_gains):
        self.__camera.set_color_gains(new_gains)
    
    def set_exposure(self, exposure):
        self.__camera.set_exposure(exposure)

    def get_sprocket_offset(self):
        return self.__sprokcet_offset
    
    def set_sprocket_offset(self, new_offset):

        if new_offset > 0 and new_offset < 256:
            self.__sprokcet_offset = new_offset
            self.__i2c_mcu.set_sprocket_offset(self.__sprokcet_offset)
