import os
import time
import threading
#from sense_emu import SenseHat
from sense_hat import SenseHat
import requests, json 

sense = SenseHat()
sense.low_light = True
sense.set_rotation(270)
indoor_humidiy= 0
indoor_temperature = 0
outdoor_humidiy = 0
outdoor_temperature = 0
weather="N/A"

toggleFlag = 0
displayMode = 0

# get CPU temperature
def get_cpu_temp():
    res = os.popen("vcgencmd measure_temp").readline()
    t = float(res.replace("temp=","").replace("'C\n",""))
    return(t)
#    return(45)

# use moving average to smooth readings
def get_smooth(x):
    if not hasattr(get_smooth, "t"):
        get_smooth.t = [x,x,x]
    get_smooth.t[2] = get_smooth.t[1]
    get_smooth.t[1] = get_smooth.t[0]
    get_smooth.t[0] = x
    xs = (get_smooth.t[0]+get_smooth.t[1]+get_smooth.t[2])/3
    return(xs)

def readSensor():
    global indoor_humidiy, indoor_temperature
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    t_cpu = get_cpu_temp()

    # calculates the real temperature compesating CPU heating
    t = (t1+t2)/2
    t_corr = t - ((t_cpu-t)/1.8)
    t_corr = get_smooth(t_corr)
    indoor_temperature = t_corr*1.8 + 32
    indoor_humidiy = sense.get_humidity()
    #indoor_pressure = sense.get_pressure()

def readWeather():
    global weather, outdoor_humidiy, outdoor_temperature
    api_key = "a2062d3deac579aa39989a45a0ad5bf6"
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    city_name = "77584,us" 
    complete_url = base_url + "zip=" + city_name +"&appid=" + api_key
    response = requests.get(complete_url) 
    x = response.json() 
    if x["cod"] == 200: 
        y = x["main"] 
        outdoor_temperature = int((y["temp"] - 273.15 ) * 1.8 + 32 )
        #outdoor_pressure = y["pressure"] 
        outdoor_humidiy = y["humidity"] 
        z = x["weather"] 
        weather = z[0]["description"]

 

def display():
    global indoor_humidiy, indoor_temperature, weather, outdoor_humidiy, outdoor_temperature, sense, toggleFlag
    readSensor()
    readWeather()
    
    if toggleFlag == 1:
        sense.clear()
        return
    sense.show_message(time.strftime("%H:%M"), text_colour=[4, 8, 4])
    print(time.strftime("%H:%M"))

    if toggleFlag == 1:
        sense.clear()
        return
    time.sleep(1)
    
    if toggleFlag == 1:
        sense.clear()
        return
    sense.show_message("T%d/%d" % (outdoor_temperature, round(indoor_temperature)), text_colour=[4, 8, 8])
    print("T%d/%d" % (outdoor_temperature, round(indoor_temperature)))

    if toggleFlag == 1:
        sense.clear()
        return
    time.sleep(1)
        
    if toggleFlag == 1:
        sense.clear()
        return
    sense.show_message("H%d/%d" % (outdoor_humidiy, round(indoor_humidiy)), text_colour=[4, 8, 8])
    print("H%d/%d" % (outdoor_humidiy, round(indoor_humidiy)))

    if toggleFlag == 1:
        sense.clear()
        return
    time.sleep(1)
        
    if toggleFlag == 1:
        sense.clear()
        return
    sense.show_message(weather, text_colour=[4, 8, 8])
    print(weather)

    if toggleFlag == 1:
        sense.clear()
        return
    time.sleep(5)

class displayThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID=threadID
        self.name=name
    def run(self):
        global displayMode
        print ("Display Thread is running")
        while True:
            if displayMode == 0:  # Day Regular model 
                display()
            elif displayMode == 1: # Day sleep model 
                if int(time.strftime("%M")) == 0:
                    display()
            elif displayMode == 2: # Night Regular model (alway off)
                time.sleep(2)
            elif displayMode == 3:
                for _ in range(3): # Night wakeup model (display 3 times and then sleep)
                    display()
                displayMode = 2
            else:
                return

if (int(time.strftime("%H")) > 6):
    displayMode = 0
if (int(time.strftime("%H")) <= 6):
    displayMode = 3
show = displayThread(1, "DisplayThread")
show.start()
while True:
    acc = sense.get_accelerometer_raw()
    x = round(acc['x'], 0)
    y = round(acc['y'], 0)
    z = round(acc['z'], 0)
    print("x={0}, y={1}, z={2}".format(x, y, z))

  # Update the rotation of the display depending on which way up the Sense HAT is
    if x  == -1:
        sense.set_rotation(180)
    elif y == 1:
        sense.set_rotation(90)
    elif y == -1:
        sense.set_rotation(270)
    else:
        sense.set_rotation(0)

    x = abs(x)
    y = abs(y)
    z = abs(z)

    if (x>1 or y>1 or z>1):
        if  displayMode == 0:
            toggleFlag = 1
            displayMode = 1
            toggleFlag = 0
        elif displayMode == 1:
            toggleFlag = 1
            displayMode = 0
            toggleFlag = 0
        elif displayMode == 2:
            displayMode = 3
        time.sleep(3)
    time.sleep(.3)