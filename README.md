# Super 8 Scanner
A Raspberry Pi 4 scanner to scan Super 8 reels into a collection of raw DNG frames to stitch and edit.
The scanner is a "sprocketless" driven scanner, meaning that it does not pull or claw on the film sprockets when moving the film. All of the movement is from pulling the feed and take-up reels.

The scanner is constructed out of a Raspberry Pi 4, the HQ 4k camera for said Pi, a generic microscope lens, a Raspberry Pi Pico to control stepper motors, light, sensors and many 3D printed parts.

![The scanner](/scanner_img.jpg) "The scanner"

Note that this scanner is not "user-friendly" in the sense that it is completely plug and play. There may be problems with fitting the parts as each 3D printer is different, and the detection of the sprockets can vary greatly depending on the film emulsion.
So be prepared to debug some and read a little bit of code.

As the saying goes, "It works on my computer..."

<br>

## Some context (storytime)
I got hold of many Super 8 film reels that my grandfather and his father had filmed, documenting various events from my family's past, like birthdays, vacations and other special occasions. Some of these films were even Super 8 sound films.

I remember long ago when my grandfather and I tried to record the films being projected on a screen. That did not work out as you can imagine and other than the occasional rare viewing, the films were stored away.

That was until I got a hold of my own old home movies on magnetic tape, and got the idea to digitize them. That was a straightforward project. I found a DVR, connected the old camera my parents had and recorded the output to my PC through a SCART to HDMI converter. I did the same with some older home movies on VHS through the DVR/VHS player.

Seeing as that was quite a straightforward process, I wanted to tackle the Super 8 films. And I started searching around, one of the first results I found was by "Stuart Pittaway": <br>
https://github.com/stuartpittaway/Super8FilmScanner<br>
https://www.youtube.com/watch?v=rd1Xu6e6nrw
<br>
I started by building his design straight away and got it working exceptionally well. This should have been the end of the story, but I wanted more and to try and design everything myself. I thought that I could just use Stuart's design as a backup.

I started by modifying Stuart's design, making it accept larger reels and adding tension sensors. Then I started to branch out on my own. I wanted a faster frame advance and to not pinch the film. So I decided to design a scanner that has rollers, a tension arm and a sprocket sensor as I did not want to use the camera to detect the sprockets *(with the sensor config at 4K it took a lot of time).*<br>
And after many iterations over the course of 1 year, the design is somewhat finished.

## Hardware
Everything in the CAD file is to be 3D printed, apart from that:<br>
- 2x 8mm bearings with an outer diameter of 22mm
- 4x 5mm (4.9mm) bearings with outer diameter of 16mm
- 1x 500ohm potentiometer (regular single turn 3 pin)
- random assortment of M2, M3 and M4 bolts 12mm & 19/25mm with nuts & washers
    - (my specific parts, but they can differ depending on printing etc.)
    - 15x M4x25mm screw
    - 2x M4x12mm screw for LED heatsink mount (if using an LED board and not a lamp)
    - 8x M3x12 screws for mounting stepper motors
    - 25x M3x19mm screws
    - 6x M3 nuts
    - 18x M3 washers
    - 11x M2x12mm screws
    - 7x M2 nuts
    - 7x M2 washers
- 2x NEMA 17 stepper motors
- 2x DRV8825 stepper drivers
- 1x photoresistor Cds 4-7kohm
- 1x 3V LED diode (for photoresistor to detect sprockets)
- 1x 3.3V regulator for LED and Pico if USB is not used
- 1x Raspberry Pi 3/4
- 1x Raspberry Pi HQ camera
- 1x longer cable to camera ~300mm
- 1x C-mount microscope lens
- 1x power source for steppers
- 2x capacitors ~500uF
- 1x 5V power source
- 1x rubber band ~3-5cm diameter (change if the feed stepper can't keep the tension, to a larger band)
- 1x breadboard push button / tactile switch
- 1x light source (I use a 3W LED 6000k on a PCB)
- 1x light diffuser
- many wires, some breadboard, some soldered (potentiometer, LED)
- 1x 330ohm resistor for the sprocket detection LED
- 1x 4.7K resistor for the photoresistor to ground
- 1x MDF board approx 300mm x 400mm (if you have larger reels than 100m/300ft maybe increase the dimensions)

<b>It is important to note that the stepper drivers are set to maximum micro stepping.</b>

### Light source
The light source can either be an LED diode on a PCB or an MR16 Osram lamp. Both variations exist in the CAD, the MR16 is just hidden. <br>
The code hints at light intensity controls, but I just ended up having it on max and letting the camera do auto exposure. So I leave those electronics out, but you can read more about it at: https://forums.kinograph.cc/t/lighting-research-results/1720/69
If you really want to control the light intensity.

### Circuit diagram
Note that I still have everything connected on a breadboard using jumper wires. I have only soldered the potentiometer wires to the potentiometer.<br>
I was lazy and did not connect some grounds in the diagram, but all grounds are connected in common.

For 5V power, I used a USB wire cut from another device, the Pico is powered by USB from PC, the steppers are powered by a 12V DC supply.

![The circuit diagram](/circuit_diagram.jpg) "The basic circuit diagram"

<br>

## Software
The two packages used in the Pico code are: <br>
https://github.com/khoih-prog/MBED_RP2040_PWM<br>
https://github.com/br3ttb/Arduino-PID-Library<br>
The Arduino IDE was used to program and debug the Pico.<br>
Some of the libraries for the Python code on the Pi are:
- Picamera2
- Libcamera
- OpenCV
- Tkinter
- Numpy
- SMBus

But most of these should already be installed on the Pi image, if not you will notice when running the code what is missing.<br>
I also mounted a network drive to the desktop folder "scanner_share" but that can be decided by the user how to deal with it. But saving to the SD card is not recommended as a long Super 8 film at 4K DNG is over 100GB and a regular 2-3min film is ~60GB

## GUI & How to Use the Scanner

### Setup for each film
When setting up each reel, the steppers have to be turned off, either by disabling the drivers (not implemented in the project) or removing the power for the drivers, in my case a 12V DC power supply.

The supply reel rotates clockwise like in a projector and the take-up reel also rotates clockwise.

Then we can thread the film around the tension arm counterclockwise, around the closest roller clockwise, down to the roller next to the gate counterclockwise, over the filmgate (make sure that the film is in the middle of the gate). Then around the second roller next to the gate counterclockwise, then up towards the roller next to the camera and sprocket detector clockwise. Then pull the film through the sprocket detector and counterclockwise around the last roller into the take-up reel that rotates clockwise.

![The film path](/film_path.jpg) "The film path illustrated"

Then turn on the steppers by either connecting the power or enabling the drivers. Then start the program and set the tension by advancing frames until the tension finds an optimal point (where the tension arm barely moves anymore). Then click on focus and try to get the highest number possible (make sure that there is a scene present and not completely white or black film). Then stop the focusing. Then select an auto white balance that suits your film. (it takes some time for it to affect the frame, so wait 10-20 seconds after each change, you will see it slowly changing).

Then just start scanning (the scanner will stop if the tension drops, but you should still be present in case something happens).
<br>

### Diagnostics
If the frame registration is skipping some frames, then change the sprocket offset and see if it improves.

The Pico also prints out data in the serial log to use for diagnostics.

<br>

### The GUI

![The GUI](/gui_example.png) "The GUI screen"

The GUI is very simple, we have the amount of scanned frames on top, a button for advancing to the next frame (used for setup and testing). Underneath, we have a focus button that zooms in on the frame and displays a focus number, higher is better. The user changes the focus by either moving the camera on the sled or focusing the lens. The focus button also changes name to Stop Focus when the mode is on.

The start scanning button says what it does, it starts the procedure for scanning (take a picture, save and advance frame). Like the focus button, it changes the button name depending on state.

The remove and add offset is for changing the sprocket detector "sensitivity" by adjusting an offset of the threshold. This can be tweaked if frames are skipped or misaligned.

Select auto balance is what it says, as described in the setup section this takes some time to apply, you can see it change slowly when a new AWB is selected.

The start and stop rewind button is for rewinding the film, this can also be done with the physical button.

### Scanning Done & Rewinding
When the tension releases and the reel is done scanning, I recommend moving the scanned frames to a new folder then rearranging the film like the image below. Only pull the film around the bottom right roller, then to the roller next to the tension arm, around the tension arm and back to the feed reel.

Then rewind some manually with the button first (you can also engage the button to loosen up some film from the take-up reel without disconnecting power to the steppers)

![Rewind path](/rewind_path.jpg) "The rewind path"

Then stitch the frames together and stabilize the movie using other tools. I myself use DaVinci Resolve and VirtualDub with the Neat Video plugin for scratch removal.