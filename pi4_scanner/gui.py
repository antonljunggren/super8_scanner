import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2 as cv
from i2c_mcu import I2C_Mcu
from time import sleep
from enum import Enum

from scanner import Scanner



class GUI_State(Enum):
    PREVIEW = 0,
    SCAN = 1,
    FOCUS = 2,
    ERROR = 3,
    REWIND = 4

class GUI():

    def __init__(self):

        self.scanner = Scanner()
        self.gui_state = GUI_State.PREVIEW

        self.root = tk.Tk()
        self.root.geometry("900x700")
        self.root.title("Super8 Scanner")

        self.frame = tk.Frame(self.root)
        self.frame.columnconfigure(0, weight=10)
        self.frame.columnconfigure(1, weight=1)

        self.canvas = tk.Canvas(self.frame, width=450, height=600)
        self.canvas.grid(row=0, column=0, rowspan=10, sticky=tk.W+tk.E)

        self.frames_scanned_label = tk.Label(self.frame, text=f"Scanned frames: {self.scanner.get_frames_scanned_cnt()}", font=('Arial', 18))
        self.frames_scanned_label.grid(row=0, column=1, sticky=tk.W+tk.E)

        self.next_frame_button = tk.Button(self.frame, text="Next frame", font=('Arial', 18), command=self.advance_frame)
        self.next_frame_button.grid(row=1, column=1, sticky=tk.W+tk.E)

        self.focus_button = tk.Button(self.frame, text="Focus", font=('Arial', 18), command=self.focus)
        self.focus_button.grid(row=2, column=1, sticky=tk.W+tk.E)

        self.scan_button = tk.Button(self.frame, text="Start scanning", font=('Arial', 18), command=self.start_stop_scanning)
        self.scan_button.grid(row=3, column=1, sticky=tk.W+tk.E)

        self.sprocket_offset_frame = tk.Frame(self.frame)

        self.sprocket_offset_label = tk.Label(self.sprocket_offset_frame, text=f"Sprocket offset: {self.scanner.get_sprocket_offset()}", font=('Arial', 18))
        self.sprocket_offset_label.pack(anchor=tk.W)

        self.add_sprocket_offset_button = tk.Button(self.sprocket_offset_frame, text="Add Offset", font=('Arial', 18), command= lambda: self.change_sprocket_offset(1))
        self.add_sprocket_offset_button.pack(anchor=tk.W)

        self.remove_sprocket_offset_button = tk.Button(self.sprocket_offset_frame, text="Remove Offset", font=('Arial', 18), command= lambda: self.change_sprocket_offset(-1))
        self.remove_sprocket_offset_button.pack(anchor=tk.W)

        self.sprocket_offset_frame.grid(row=4, column=1, sticky=tk.W+tk.E)

        self.awb_frame = tk.Frame(self.frame)

        self.select_awb_label = tk.Label(self.awb_frame, text="Select auto white balance", font=('Arial', 18))
        self.select_awb_label.pack(anchor=tk.W)

        self.awb_mode_var = tk.IntVar(value=self.scanner.get_awb_modes()[0][1])

        for (awb_name, awb_mode_int) in self.scanner.get_awb_modes():
            radio_button = tk.Radiobutton(self.awb_frame, text=awb_name, value=awb_mode_int, variable=self.awb_mode_var, command=self.on_awb_mode_change)
            radio_button.pack(anchor=tk.W)

        self.awb_frame.grid(row=5, column=1, sticky=tk.W+tk.E)

        self.rewind_button = tk.Button(self.frame, text="Start/Stop rewinding", font=('Arial', 18), command=self.start_stop_rewind)
        self.rewind_button.grid(row=6, column=1, sticky=tk.W+tk.E)

        self.frame.pack(padx=20, pady=20, fill='x')

        self.update_preview()

        self.root.mainloop()

    def __del__(self):
        self.scanner.close()

    def advance_frame(self):
        if self.gui_state is GUI_State.SCAN:
            return
        
        self.gui_state = GUI_State.PREVIEW
        self.scanner.advance_frame()

    def start_stop_rewind(self):
        if self.gui_state is GUI_State.SCAN:
            return
        

        if self.gui_state is GUI_State.REWIND:
            self.scanner.start_stop_rewind(False)
            self.gui_state = GUI_State.PREVIEW
        else:
            self.gui_state = GUI_State.REWIND
            self.scanner.start_stop_rewind(True)

    def on_awb_mode_change(self):
        if self.gui_state is GUI_State.SCAN:
            return
        
        self.scanner.set_awb_mode(self.awb_mode_var.get())

    def change_sprocket_offset(self, offset):
        if self.gui_state is GUI_State.SCAN:
            return
        
        new_offset = self.scanner.get_sprocket_offset() + offset

        self.scanner.set_sprocket_offset(new_offset)

        self.sprocket_offset_label.config(text=f"Sprocket offset: {self.scanner.get_sprocket_offset()}")

    def draw_focus_values(self, image):

        focus_val = int(self.calculate_focus(image))
        text = f'Focus: {focus_val}'
        position = (10, 550)
        font = cv.FONT_HERSHEY_SIMPLEX
        font_scale = 2
        font_color = (255, 255, 255)
        thickness = 2
        text_background_color = (0, 0, 0, 125)

        # Get the width and height of the text box
        (text_width, text_height), _ = cv.getTextSize(text, font, font_scale, thickness)

        # Create a semi-translucent black rectangle
        overlay = image.copy()
        output = image.copy()
        cv.rectangle(overlay, (position[0], position[1] + 5), (position[0] + text_width, position[1] - text_height - 5), text_background_color, -1)

        # Alpha blending to create the semi-translucency effect
        alpha = 0.5
        cv.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)

        cv.putText(output, text, position, font, font_scale, font_color, thickness, cv.LINE_AA)
        

        return output

    def prepare_preview(self, image):
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

        if self.gui_state is GUI_State.FOCUS:
            height = len(image)
            width = len(image[0])
            height_crop = 600
            width_crop = 450
            y1=int((height/2) - height_crop/2)
            y2=int((height/2) + height_crop/2)
            x1=int((width/2) - width_crop/2)
            x2=int((width/2) + width_crop/2)
            image = image[y1:y2, x1:x2]
            image = self.draw_focus_values(image)
        else:
            image = cv.resize(image, (450, 600))
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)

        self.canvas.create_image(0, 0, anchor=tk.NW, image=image)
        self.canvas.image = image  # Keep a reference so it's not garbage collected

    def update_preview(self):
        preview = self.scanner.get_preview()
        self.prepare_preview(preview)

        if self.gui_state is GUI_State.PREVIEW or self.gui_state is GUI_State.FOCUS or self.gui_state is GUI_State.REWIND:
            self.root.after(100, self.update_preview) 

    def calculate_focus(self, image):
        # Convert the image to grayscale
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        # Calculate the Laplacian
        laplacian = cv.Laplacian(gray, cv.CV_64F)

        # Calculate the variance of the Laplacian
        focus_measure = laplacian.var()

        return focus_measure

    def focus(self):
        if self.gui_state is GUI_State.SCAN:
            return
        
        if self.gui_state is GUI_State.FOCUS:
            self.gui_state = GUI_State.PREVIEW
            self.focus_button.config(text="Focus")
        else:
            self.gui_state = GUI_State.FOCUS
            self.focus_button.config(text="Stop Focus")


    def scan(self):
        if self.gui_state is GUI_State.SCAN:
            status, preview = self.scanner.scan()
            self.prepare_preview(preview)
            if status is not I2C_Mcu.McuStatus.OK:
                self.gui_state = GUI_State.ERROR
                self.scan_button.config(text="Start scanning")
            
            self.frames_scanned_label.config(text=f"Scanned frames: {self.scanner.get_frames_scanned_cnt()}")
            self.root.after(100, self.scan) 

    def start_stop_scanning(self):

        if self.gui_state is GUI_State.SCAN:
            self.gui_state = GUI_State.PREVIEW
            self.scan_button.config(text="Start scanning")
            self.update_preview()
        else:
            self.gui_state = GUI_State.SCAN
            self.scan_button.config(text="STOP")
            self.focus_button.config(text="Focus")
            self.scan()

GUI()
