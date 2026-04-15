#!/usr/bin/env python
#
# BakeBit example for the basic functions of BakeBit 128x64 OLED (http://wiki.friendlyarm.com/wiki/index.php/BakeBit_-_OLED_128x64)
#
# The BakeBit connects the NanoPi NEO and BakeBit sensors.
# You can learn more about BakeBit here:  http://wiki.friendlyarm.com/BakeBit
#
# Have a question about this example?  Ask on the forums here:  http://www.friendlyarm.com/Forum/
#
'''
## License

The MIT License (MIT)

BakeBit: an open source platform for connecting BakeBit Sensors to the NanoPi NEO.
Copyright (C) 2016 FriendlyARM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from __future__ import print_function
import bakebit_128_64_oled as oled
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import sys
import subprocess
import threading
import signal
import os
import socket

global width
width=128
global height
height=64

global pageCount
pageCount=2
global pageIndex
pageIndex=0
global showPageIndicator
showPageIndicator=False

oled.init()  #initialze SEEED OLED display
oled.setNormalDisplay()      #Set display to normal mode (i.e non-inverse mode)
oled.setHorizontalMode()

global drawing
drawing = False

global image
image = Image.new('1', (width, height))
global draw
draw = ImageDraw.Draw(image)
global fontb24
fontb24 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 24);
global font14
font14 = ImageFont.truetype('DejaVuSansMono.ttf', 14);
global smartFont
smartFont = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10);
global fontb14
fontb14 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14);
global font11
font11 = ImageFont.truetype('DejaVuSansMono.ttf', 11);
global font20
font20 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 20);

global lock
lock = threading.Lock()

global scroll_x
scroll_x = 0
global scroll_dir
scroll_dir = -1
global cached_ips
cached_ips = ""
global last_ip_update
last_ip_update = 0
global ticker_text
ticker_text = ""
global ticker_img
ticker_img = None
global ticker_w
ticker_w = 1

def get_ticker_image(text, font):
    global ticker_text, ticker_img, ticker_w
    if ticker_text != text or ticker_img is None:
        ticker_text = text
        try:
            w, h = draw.textsize(text, font=font)
        except AttributeError:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        
        if w == 0:
            w = 1
        ticker_w = w
        
        # Create an image long enough to safely crop wrapping text
        # (width + screen_width) so we can crop from any x in [0, w) without out-of-bounds
        ticker_img = Image.new('1', (w + 128, 22))
        tdraw = ImageDraw.Draw(ticker_img)
        tdraw.text((0, 0), text, font=font, fill=255)
        tdraw.text((w, 0), text, font=font, fill=255)
        
    return ticker_img, ticker_w

def get_all_ips():
    global cached_ips
    global last_ip_update
    current_time = time.time()
    if current_time - last_ip_update > 2: # update every 2 seconds
        cmd = "ip -4 -o addr show up | awk '$2 != \"lo\" {print $2\": \"$4}'"
        try:
            output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            ips = []
            for line in output.split('\n'):
                line = line.strip() # Strip \r or trailing spaces
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        iface = parts[0].rstrip(':')
                        ip = parts[1].split('/')[0]
                        ips.append(iface + ": " + ip + ";")
            if not ips:
                cached_ips = "no ip address"
            else:
                cached_ips = " ".join(ips)
        except:
            cached_ips = "Error"
        last_ip_update = current_time
    return cached_ips

def draw_page():
    global drawing
    global image
    global draw
    global oled
    global font
    global font14
    global smartFont
    global width
    global height
    global pageCount
    global pageIndex
    global showPageIndicator
    global width
    global height
    global lock
    global scroll_x
    global scroll_dir

    lock.acquire()
    is_drawing = drawing
    page_index = pageIndex
    lock.release()

    if is_drawing:
        return

    lock.acquire()
    drawing = True
    lock.release()

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    # Draw current page indicator
    if showPageIndicator:
        dotWidth=4
        dotPadding=2
        dotX=width-dotWidth-1
        dotTop=(height-pageCount*dotWidth-(pageCount-1)*dotPadding)/2
        for i in range(pageCount):
            if i==page_index:
                draw.rectangle((dotX, dotTop, dotX+dotWidth, dotTop+dotWidth), outline=255, fill=255)
            else:
                draw.rectangle((dotX, dotTop, dotX+dotWidth, dotTop+dotWidth), outline=255, fill=0)
            dotTop=dotTop+dotWidth+dotPadding

    if page_index==0:
        
        # Get weekday (1-7) using the built-in time tuple (tm_wday: 0=Monday, 6=Sunday)
        now = time.localtime()
        weekday_num = now.tm_wday + 1
        
        date_text = time.strftime("%Y.%m.%d") + "({})".format(weekday_num)
        
        try:
            date_w, _ = draw.textsize(date_text, font=fontb24)
        except AttributeError:
            bbox = draw.textbbox((0, 0), date_text, font=fontb24)
            date_w = bbox[2] - bbox[0]
            
        if date_w > width - 4:
            scroll_x += scroll_dir * 4
            if scroll_x <= width - date_w - 2:
                scroll_x = width - date_w - 2
                scroll_dir = 1
            elif scroll_x >= 2:
                scroll_x = 2
                scroll_dir = -1
        else:
            scroll_x = 2
            
        draw.text((scroll_x, 2), date_text, font=fontb24, fill=255)
        
        text = time.strftime("%X")
        draw.text((2,40), text, font=fontb24, fill=255)
    elif page_index==1:
        # Uncomment next line to test fake long text
        # text = "1: line one 2: line two 3: line three "
        text = get_all_ips() + "   "
        
        t_img, t_w = get_ticker_image(text, font20)
        
        # Move text left by 4 pixels, wrap around at text_width seamlessly
        scroll_x = (abs(scroll_x) + 4) % t_w
        
        # Line 1: crop from scroll_x
        crop1 = t_img.crop((scroll_x, 0, scroll_x + width, 22))
        image.paste(crop1, (0, 1))
        
        # Line 2: crop from scroll_x + width
        scroll2 = (scroll_x + width) % t_w
        crop2 = t_img.crop((scroll2, 0, scroll2 + width, 22))
        image.paste(crop2, (0, 22))
        
        # Line 3: crop from scroll_x + width * 2
        scroll3 = (scroll_x + width * 2) % t_w
        crop3 = t_img.crop((scroll3, 0, scroll3 + width, 22))
        image.paste(crop3, (0, 43))
        
        scroll_x = -scroll_x # keep it negative for consistency if needed, but we use abs() above so it doesn't matter
    elif page_index==3: #shutdown -- no
        draw.text((2, 2),  'Shutdown?',  font=fontb14, fill=255)

        draw.rectangle((2,20,width-4,20+16), outline=0, fill=0)
        draw.text((4, 22),  'Yes',  font=font11, fill=255)

        draw.rectangle((2,38,width-4,38+16), outline=0, fill=255)
        draw.text((4, 40),  'No',  font=font11, fill=0)

    elif page_index==4: #shutdown -- yes
        draw.text((2, 2),  'Shutdown?',  font=fontb14, fill=255)

        draw.rectangle((2,20,width-4,20+16), outline=0, fill=255)
        draw.text((4, 22),  'Yes',  font=font11, fill=0)

        draw.rectangle((2,38,width-4,38+16), outline=0, fill=0)
        draw.text((4, 40),  'No',  font=font11, fill=255)

    elif page_index==5:
        draw.text((2, 2),  'Shutting down',  font=fontb14, fill=255)
        draw.text((2, 20),  'Please wait',  font=font11, fill=255)

    oled.drawImage(image)

    lock.acquire()
    drawing = False
    lock.release()


def is_showing_power_msgbox():
    global pageIndex
    lock.acquire()
    page_index = pageIndex
    lock.release()
    if page_index==3 or page_index==4:
        return True
    return False


def update_page_index(pi):
    global pageIndex
    global scroll_x
    global scroll_dir
    lock.acquire()
    pageIndex = pi
    scroll_x = 0
    scroll_dir = -1
    lock.release()

def receive_signal(signum, stack):
    global pageIndex

    lock.acquire()
    page_index = pageIndex
    lock.release()

    if page_index==5:
        return

    if signum == signal.SIGUSR1:
        print('K1 pressed')
        if is_showing_power_msgbox():
            if page_index==3:
                update_page_index(4)
            else:
                update_page_index(3)
        else:
            update_page_index(0)
        print('K1 released')

    if signum == signal.SIGUSR2:
        print('K2 pressed')
        if is_showing_power_msgbox():
            if page_index==4:
                update_page_index(5)
            else:
                update_page_index(0)
        else:
            update_page_index(1)
        print('K2 released')

    if signum == signal.SIGALRM:
        print('K3 pressed')
        if is_showing_power_msgbox():
            update_page_index(0)
        else:
            update_page_index(3)
        print('K3 released')


image0 = Image.open('friendllyelec.png').convert('1')
oled.drawImage(image0)
time.sleep(2)

signal.signal(signal.SIGUSR1, receive_signal)
signal.signal(signal.SIGUSR2, receive_signal)
signal.signal(signal.SIGALRM, receive_signal)

while True:
    try:
        draw_page()

        lock.acquire()
        page_index = pageIndex
        lock.release()

        if page_index==5:
            time.sleep(2)
            while True:
                lock.acquire()
                is_drawing = drawing
                lock.release()
                if not is_drawing:
                    lock.acquire()
                    drawing = True
                    lock.release()
                    oled.clearDisplay()
                    break
                else:
                    time.sleep(.1)
                    continue
            time.sleep(1)
            os.system('systemctl poweroff')
            break
        elif page_index in (0, 1):
            time.sleep(0.1)
        else:
            time.sleep(0.2)
    except KeyboardInterrupt:
        break
    except IOError:
        print ("Error")
