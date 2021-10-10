from time import sleep
from evdev import InputDevice, categorize, ecodes
from pitop.pma import EncoderMotor, ForwardDirection, BrakingType, ServoMotor, ServoMotorState, LED, Buzzer, UltrasonicSensor
import threading 

# first we set up the motors, this gives us functions to control the robot
# note that the motor objects have ForwardDirection set oposite to eachother.
motor_left = EncoderMotor("M0", ForwardDirection.CLOCKWISE)
motor_left.braking_type = BrakingType.COAST
motor_right = EncoderMotor("M3", ForwardDirection.COUNTER_CLOCKWISE)
motor_right.braking_type = BrakingType.COAST

pan_servo = ServoMotor("S0")
pan_servo._ServoMotor__controller.set_acceleration_mode(1)


tilt_servo = ServoMotor("S3")
tilt_servo._ServoMotor__controller.set_acceleration_mode(1)
pan_servo.target_angle = 0
tilt_servo.target_angle = 0
TARGET_SPEED = 25
#pan_servo.target_speed = -TARGET_SPEED
#tilt_servo.target_speed = -TARGET_SPEED
flLed = LED("D5")
rlLed = LED("D7")
frLed = LED("D2")
rrLed = LED("D0")

fUltra = UltrasonicSensor("D3")
buzzer = Buzzer("D4")

gamepad = InputDevice('/dev/input/event0')

MAX_SPEED = 114
MOVE_CENTER_TOLERANCE = 8192
STICK_MAX = 32768
PT_CENTER_TOLERANCE = int(STICK_MAX/1.8)


ABS_AXIS = {
    ecodes.ABS_X: 'ABS_X', # 0 - 65,536   the middle is 32768
    ecodes.ABS_Y: 'ABS_Y', # 0 - 65,536
    ecodes.ABS_Z: 'ABS_Z',  # 0 - 255
    ecodes.ABS_RX: 'ABS_RX', # 0 - 65,536   the middle is 32768
    ecodes.ABS_RY: 'ABS_RY', # 0 - 65,536
    ecodes.ABS_RZ: 'ABS_RZ', # 0 - 255
    ecodes.ABS_HAT0X: 'ABS_HAT0X', # 0 - 1
    ecodes.ABS_HAT0Y: 'ABS_HAT0Y' # 0 - 1
}
LAST_ABS_VALUE = {
    'ABS_X': 0,
    'ABS_Y': 0,
    'ABS_Z': 0,
    'ABS_RX': 0,
    'ABS_RY': 0,
    'ABS_RZ': 0,
    'ABS_HAT0X': 0,
    'ABS_HAT0Y': 0
}
orpm_speed = 0
lrpm_speed = 0
rrpm_speed = 0

flLed.off()
frLed.off()
rlLed.off()
rrLed.off()
buzzer.off()

flSwitch = 0
frSwitch = 0
rlSwitch = 0
rrSwitch = 0
emergency = 0
pevalue = 0
tevalue = 0

lstop_threads = False
rstop_threads = False

def drive(tleft_rpm: float, tright_rpm: float):
    motor_left.set_target_rpm(tleft_rpm)
    motor_right.set_target_rpm(tright_rpm)

def ledSwitch(switch):
    global flSwitch, frSwitch, rlSwitch, rrSwitch
    if switch == "FL":
        if flSwitch == 0:
            flSwitch = 1
            flLed.on()
        else: 
            flSwitch = 0
            flLed.off()
    if switch == "FR":
        if frSwitch == 0:
            frSwitch = 1
            frLed.on()
        else: 
            frSwitch = 0
            frLed.off()
    if switch == "RL":
        if rlSwitch == 0:
            rlSwitch = 1
            rlLed.on()
        else: 
            rlSwitch = 0
            rlLed.off()
    if switch == "RR":
        if rrSwitch == 0:
            rrSwitch = 1
            rrLed.on()
        else: 
            rrSwitch = 0
            rrLed.off()

def turn(driection):
    if driection == "LEFT":
        while True:
            flLed.on()
            rlLed.on()
            sleep(0.5)
            flLed.off()
            rlLed.off()
            sleep(0.5)
            global lstop_threads 
            if lstop_threads: 
                break
    if driection == "RIGHT":
        while True:
            frLed.on()
            rrLed.on()
            sleep(0.5)
            frLed.off()
            rrLed.off()
            sleep(0.5)
            global rstop_threads 
            if rstop_threads: 
                break

def pan():
    while True:
        global pevalue
        pan_current_state = pan_servo.state
        pan_current_angle = pan_current_state.angle
        pan_target_angle = pan_current_angle - pevalue*2
        if abs(pan_target_angle)<=45:
            pan_servo.target_angle = pan_target_angle
        else:
            break
        sleep(0.005)
        if pevalue == 0:
            break
def tilt():
    while True:
        global tevalue
        tilt_current_state = tilt_servo.state
        tilt_current_angle = tilt_current_state.angle
        tilt_target_angle = tilt_current_angle + tevalue*2
        if abs(tilt_target_angle)<=45:    
            tilt_servo.target_angle = tilt_target_angle
        else:
            break
        sleep(0.005)
        if tevalue == 0:
            break

def beep():
    while True:
        global bvalue
        buzzer.on()
        sleep(0.001)
        if bvalue == 0:
            buzzer.off()
            break

def startUltrasonicSensor():
    while True:
        freq = fUltra.distance/5
        if freq < 0.05:
            freq = 0.05
        if freq < 0.1:
            #print(fUltra.distance)
            buzzer.on()
            sleep(freq)
            buzzer.off()
        sleep(freq)

tl = threading.Thread(target = turn, args=("LEFT",))
tr = threading.Thread(target = turn, args=("RIGHT",))
panT = threading.Thread(target = pan)
tiltT = threading.Thread(target = tilt)
beepT = threading.Thread(target = beep)
uSensorT = threading.Thread(target = startUltrasonicSensor)
uSensorT.start() 
for event in gamepad.read_loop():
    if event.type == ecodes.EV_ABS:
        if event.code == ecodes.ABS_HAT0X:
            if event.value != 0:
                if not panT.isAlive():
                    pevalue = event.value
                    panT = threading.Thread(target = pan)
                    panT.start() 
            else:
                pevalue = 0
                if panT.isAlive():
                    panT.join() 
        if event.code == ecodes.ABS_HAT0Y:
            if event.value != 0:
                if not tiltT.isAlive():
                    tevalue = event.value
                    tiltT = threading.Thread(target = tilt)
                    tiltT.start() 
            else:
                tevalue = 0
                if tiltT.isAlive():
                    tiltT.join() 
        if event.code == ecodes.ABS_X or event.code == ecodes.ABS_Y:
            if abs(event.value) < MOVE_CENTER_TOLERANCE and event.code == ecodes.ABS_X:
                LAST_ABS_VALUE[ ABS_AXIS[ event.code ] ] = 0
            else:
                LAST_ABS_VALUE[ ABS_AXIS[ event.code ] ] = event.value
            orpm_speed = (LAST_ABS_VALUE['ABS_Y']/STICK_MAX)*MAX_SPEED
            lrpm_speed = orpm_speed
            rrpm_speed = orpm_speed
            diff = 1 - (abs(LAST_ABS_VALUE['ABS_X'])/STICK_MAX)
            if LAST_ABS_VALUE['ABS_X'] > 0:
                lrpm_speed = rrpm_speed * diff
            elif LAST_ABS_VALUE['ABS_X'] < 0:
                rrpm_speed = lrpm_speed * diff
            drive(lrpm_speed, rrpm_speed)
        """
        if event.code == ecodes.ABS_RX or event.code == ecodes.ABS_RY:
            LAST_ABS_VALUE[ ABS_AXIS[ event.code ] ] = event.value
            orpm_speed = (LAST_ABS_VALUE['ABS_RY']/STICK_MAX)*MAX_SPEED
            lrpm_speed = orpm_speed
            rrpm_speed = orpm_speed
            diff = 1 - (abs(LAST_ABS_VALUE['ABS_RX'])/STICK_MAX)
            if LAST_ABS_VALUE['ABS_RX'] > 0:
                lrpm_speed = rrpm_speed * diff
            elif LAST_ABS_VALUE['ABS_RX'] < 0:
                rrpm_speed = lrpm_speed * diff
            drive(lrpm_speed, rrpm_speed)
        """
        if event.code == ecodes.ABS_RX:
            if abs(event.value) > PT_CENTER_TOLERANCE:
                if event.value <  0:
                    pevalue = -1
                if event.value >  0:
                    pevalue = 1
                if not panT.isAlive():
                    panT = threading.Thread(target = pan)
                    panT.start() 
            else:
                if panT.isAlive():
                    pevalue = 0
                    panT.join() 
        if event.code == ecodes.ABS_RY:
            if abs(event.value) > PT_CENTER_TOLERANCE:
                if event.value <  0:
                    tevalue = -1
                if event.value >  0:
                    tevalue = 1
                if not tiltT.isAlive():
                    tiltT = threading.Thread(target = tilt)
                    tiltT.start() 
            else:
                if tiltT.isAlive():
                    tevalue = 0
                    tiltT.join() 


    if event.type == ecodes.EV_KEY:
        if event.code == ecodes.BTN_TL:
            if event.value == 1:
                if not tl.isAlive():
                    tl = threading.Thread(target = turn, args=("LEFT",))
                    tl.start() 
            else:
                lstop_threads = True
                if tl.isAlive():
                    tl.join() 
                lstop_threads = False
                if flSwitch == 0:
                    flLed.off()
                else:
                    flLed.on()
                if rlSwitch == 0:
                    rlLed.off()
                else:
                    rlLed.on()
        if event.code == ecodes.BTN_TR:
            if event.value == 1:
                if not tr.isAlive():
                    tr = threading.Thread(target = turn, args=("RIGHT",))
                    tr.start() 
            else:
                rstop_threads = True
                if tr.isAlive():
                    tr.join() 
                rstop_threads = False
                if frSwitch == 0:
                    frLed.off()
                else:
                    frLed.on()
                if rrSwitch == 0:
                    rrLed.off()
                else:
                    rrLed.on()
        if event.code == ecodes.BTN_WEST:
            if event.value == 1:
                ledSwitch("FL")
                ledSwitch("FR")
        if event.code == ecodes.BTN_SOUTH:
            if event.value == 1:
                ledSwitch("RL")
                ledSwitch("RR")
        if event.code == ecodes.BTN_NORTH:
            if event.value == 1:
                if emergency == 0:
                    emergency =1
                    if not tl.isAlive():
                        tl = threading.Thread(target = turn, args=("LEFT",))
                        tl.start()
                    if not tr.isAlive():
                        tr = threading.Thread(target = turn, args=("RIGHT",))
                        tr.start() 
                else:
                    emergency = 0
                    lstop_threads = True
                    rstop_threads = True
                    if tl.isAlive():
                        tl.join()
                    if tr.isAlive():
                        tr.join() 
                    lstop_threads = False
                    rstop_threads = False
        if event.code == ecodes.BTN_EAST:
            if event.value == 1:
                bvalue = event.value
                if not beepT.isAlive():
                    beepT = threading.Thread(target = beep)
                    beepT.start() 
            else:
                bvalue = 0
                if beepT.isAlive():
                    beepT.join() 
