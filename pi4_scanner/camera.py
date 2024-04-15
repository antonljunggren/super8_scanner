from picamera2 import Picamera2
from picamera2.controls import Controls
import libcamera


class Camera:
    
    def __init__(self):
        print("start camera")
        self.__mid_res = (2028, 1520)
        self.__high_res = (4056, 3040)
        tuning_file = Picamera2.load_tuning_file("imx477_scientific.json")
        self.__camera: Picamera2 = Picamera2(tuning=tuning_file)
        self.__main = {"size": self.__mid_res, "format": "RGB888"}
        self.__raw = {"size": self.__high_res, "format": "SRGGB12"}
        
        self.__base_exposure = 3000
        self.__color_gains = (2.92, 1.5)
        self.__color_gains = (0.0, 0.0)
        
        self.__camera_config = self.__camera.create_still_configuration(lores={}, main=self.__main, raw=self.__raw, buffer_count=1)
        self.__camera_config["transform"] = libcamera.Transform(vflip=1)
        self.__camera.configure(self.__camera_config)
        controls = Controls(self.__camera)
        #controls.ExposureTime = self.__base_exposure
        controls.AnalogueGain = 1.0
        controls.AwbMode = libcamera.controls.AwbModeEnum.Auto
        controls.AwbEnable = True

        #controls.ColourGains = self.__color_gains
        controls.AeEnable = True
        #controls.ExposureValue = -0.5
        controls.Sharpness = 1.0
        controls.FrameDurationLimits = (31, 100000)
        self.__camera.set_controls(controls)
        self.__camera.start()
        
    def close(self):
        self.__camera.stop()
        self.__camera.close()
        print("closing camera")
        
    def get_awb_modes(self):

        modes = []

        modes.append(("Auto", 0))
        modes.append(("Tungsten", 1))
        modes.append(("Fluorescent", 2))
        modes.append(("Indoor", 3))
        modes.append(("Daylight", 4))
        modes.append(("Cloudy", 5))

        return modes
    
    def set_awb_mode(self, mode):
        if int(mode) == 0:
            self.__camera.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Auto})
        elif int(mode) == 1:
            self.__camera.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Tungsten})
        elif int(mode) == 2:
            self.__camera.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Fluorescent})
        elif int(mode) == 3:
            self.__camera.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Indoor})
        elif int(mode) == 4:
            self.__camera.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Daylight})
        elif int(mode) == 5:
            self.__camera.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Cloudy})
        else:
            self.__camera.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Auto})

    def get_frame(self):
        request = self.__camera.capture_request()
        image = request.make_array("main")
        request.release()
        return image
    
    def get_raw_frame(self):
        request = self.__camera.capture_request()
        metadata = request.get_metadata()
        image = request.make_array("raw")
        request.release()
        return image, metadata
    
    def save_dng(self, image, metadata, filename):
        self.__camera.helpers.save_dng(image, metadata, self.__camera_config["raw"], filename)
    
    def save_raw(self, filename):
        
        request = self.__camera.capture_request()
        metadata = request.get_metadata()
        image = request.make_array("raw")
        request.release()
        
        self.__camera.helpers.save_dng(image, metadata, self.__camera_config["raw"], filename)
        
    def get_color_gains(self):
        return self.__color_gains
    
    def set_color_gains(self, new_gains):
        self.__color_gains = new_gains
        self.__camera.set_controls({"ColourGains": self.__color_gains})
        print("new gains:", self.__color_gains)
        
    def set_exposure(self, exposure):
        self.__base_exposure = exposure

        self.__camera.controls.ExposureTime = exposure
        print("Set expo:", exposure)
        while True:
            expo = self.__camera.capture_metadata()["ExposureTime"]
            if abs(expo - exposure) < 50:
                break