import urequests as requests
import ujson
from machine import Pin, ADC, I2C, PWM
import ssd1306
from piotimer import Piotimer
from fifo import Fifo
import time
import network
from time import sleep_ms

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("abc", "xyz")
while not wlan.isconnected():
    pass


i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

encoder_a = Pin(10, Pin.IN, Pin.PULL_UP)
encoder_b = Pin(11, Pin.IN, Pin.PULL_UP)
rotsw = Pin(12, Pin.IN, Pin.PULL_UP)

sw0 = Pin(9, Pin.IN, Pin.PULL_UP)


def menu_handler():
    oled.fill(0)
    if menu == 1:
        oled.text("Heart rate <", 0, 10)
        oled.text("Off-line", 0, 25)
        oled.text("Real-time", 0, 40)
    
    if menu == 2:
        oled.text("Heart rate", 0, 10)
        oled.text("Off-line <", 0, 25)
        oled.text("Real-time", 0, 40)
    
    if menu == 3:
        oled.text("Heart rate", 0, 10)
        oled.text("Off-line", 0, 25)
        oled.text("Real-time <", 0, 40)
    
    oled.show()
    
menu = 1
display = 0

av = ADC(26)
sample_rate = 250
samples = Fifo(100)


beginning_value = None
previous_value = 0
increasing = True
FIRST_PEAK_THRESHOLD = 3
SECOND_PEAK_THRESHOLD = 2
first_peak = FIRST_PEAK_THRESHOLD
time_of_first_peak = 0
second_peak = SECOND_PEAK_THRESHOLD
time_of_second_peak = 0
last_sample_time = 0
time_of_previous_peak = 0
time_of_current_peak = 0
process_finished = False
interval = time_of_current_peak - time_of_previous_peak
bpm = 0
v = []
intervals = []


def encoder_a_handler(pin):
    global menu
    if display == 0:
        menu += 1
        if menu == 4:
            menu = 1
        print(menu)
        menu_handler()
    elif display == 1:
        print("1")
    elif display == 2:
        print("2")
    elif display == 3:
        print("3")

encoder_a.irq(handler = encoder_a_handler, trigger = Pin.IRQ_FALLING)
# 
# def encoder_b_handler(pin):
#     global menu
#     if display == 0:
#         menu += 1
#         if menu == 4:
#             menu = 1
#         print(menu)
#         menu_handler()
#     elif display == 1:
#         print("1")
#     elif display == 2:
#         print("2")
#     elif display == 3:
#         print("3")
# 
# encoder_b.irq(handler = encoder_b_handler, trigger = Pin.IRQ_FALLING)


def handler(timer):
    global beginning_value, previous_value, increasing, first_peak, time_of_first_peak, second_peak, time_of_second_peak
    global time_of_previous_peak, time_of_current_peak, process_finished, interval, bpm, v, samples
    temporary_value = av.read_u16()
    beginning_value = temporary_value
    samples.put(av.read_u16())
    
timer = Piotimer(freq=sample_rate, mode=Piotimer.PERIODIC, callback = handler)


 
def program1():
    global beginning_value, previous_value, increasing, first_peak, time_of_first_peak, second_peak, time_of_second_peak
    global time_of_previous_peak, time_of_current_peak, process_finished, interval, bpm, v, samples
    while True:
        if beginning_value is not None:
            temporary_value = int(beginning_value)

            if temporary_value < previous_value and increasing:
                second_peak = previous_value
                time_of_second_peak = last_sample_time
                increasing = False

                if first_peak < second_peak:
                    first_peak = second_peak

                if first_peak > second_peak:
                    time_of_current_peak = time_of_second_peak
                    process_finished = True

            elif temporary_value > previous_value:
                increasing = True
                last_sample_time = time.ticks_ms()

            previous_value = temporary_value

            if process_finished:
                interval = time_of_current_peak - time_of_previous_peak
                bpm = 60000/interval
                print(bpm)

                oled.fill(0)
                oled.text("Heart rate: ", 10, 20)
                oled.text(str(bpm), 10, 35)
                oled.show()
                
                time_of_previous_peak = time_of_current_peak
                first_peak = FIRST_PEAK_THRESHOLD
                second_peak = SECOND_PEAK_THRESHOLD
                process_finished = False
            if sw0.value() == 0:
                break
                rotsw_handler()
    
            beginning_value = None
            #v = []
        time.sleep_ms(100)


 
def program2():
    test_set_1 = [1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100]
#     test_set_2 = [828, 836, 852, 760, 800, 796, 856, 824, 808, 776, 724, 816, 800, 812, 812, 812, 756, 820, 812, 800]

    def calculate_hrv(ppi_values):
        mean_ppi = sum(ppi_values) / len(ppi_values)
        mean_hr = 60 * 1000 / mean_ppi
        
        sdnn = 0
        for ppi in ppi_values:
            sdnn += (ppi - mean_ppi) ** 2
        sdnn = (sdnn / (len(ppi_values) - 1)) ** 0.5
        
        rmssd = 0
        for i in range(len(ppi_values) - 1):
            rmssd += (ppi_values[i+1] - ppi_values[i]) ** 2
        rmssd = (rmssd / (len(ppi_values) - 1)) ** 0.5
        
        return mean_ppi, mean_hr, sdnn, rmssd

    mean_ppi_1, mean_hr_1, sdnn_1, rmssd_1 = calculate_hrv(test_set_1)

    oled.fill(0)
    oled.text("Test Set 1", 0, 0)
    oled.text("Mean PPI: {:.0f} ms".format(mean_ppi_1), 0, 10)
    oled.text("Mean HR: {:.0f} bpm".format(mean_hr_1), 0, 20)
    oled.text("SDNN: {:.0f} ms".format(sdnn_1), 0, 30)
    oled.text("RMSSD: {:.0f} ms".format(rmssd_1), 0, 40)
    oled.show()
    


def program3():
    oled.text("Program is", 10, 10)
    oled.text("running...", 10, 20)
    oled.show()
    global beginning_value, previous_value, increasing, first_peak, time_of_first_peak, second_peak, time_of_second_peak
    global time_of_previous_peak, time_of_current_peak, process_finished, interval, bpm, v, samples , intervals
    handler(timer)

    APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
    CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
    CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"

    LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login" 
    TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token" 
    REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"
    response = requests.post(
        url = TOKEN_URL,
        data = 'grant_type=client_credentials&client_id={}'.format(CLIENT_ID), 
        headers = {'Content-Type':'application/x-www-form-urlencoded'},
        auth = (CLIENT_ID, CLIENT_SECRET))

    response = response.json() #Parse JSON response into a python dictionary
    access_token = response["access_token"] #Parse access token out of the response dictionary

    while True:
        if beginning_value is not None:
            temporary_value = int(beginning_value)

            if temporary_value < previous_value and increasing:
                second_peak = previous_value
                time_of_second_peak = last_sample_time
                increasing = False

                if first_peak < second_peak:
                    first_peak = second_peak

                if first_peak > second_peak:
                    time_of_current_peak = time_of_second_peak
                    process_finished = True

            elif temporary_value > previous_value:
                increasing = True
                last_sample_time = time.ticks_ms()

            previous_value = temporary_value

            if process_finished:
                interval = time_of_current_peak - time_of_previous_peak
                print(interval)
                

                oled.show()
                time_of_previous_peak = time_of_current_peak
                first_peak = FIRST_PEAK_THRESHOLD
                second_peak = SECOND_PEAK_THRESHOLD
                process_finished = False
                intervals.append(interval)
                for a in intervals:
                        oled.text(f"Interval:", 20, 10)
                        oled.fill(0)
                        oled.text(f"Interval:", 20, 10)
                        oled.text(f"{a}", 20, 25)
                if len(intervals) == 25:
                    intervals = (intervals[5:])
                    
                    data_set = {
                         "type": "RRI",
                         "data": intervals,
                         "analysis": {
                             "type": "readiness"
                          }
                    }

                    response = requests.post(
                        url = "https://analysis.kubioscloud.com/v2/analytics/analyze",
                        headers = { "Authorization": "Bearer {}".format(access_token), #use access token to access your KubiosCloud analysis session
                                    "X-Api-Key": APIKEY},
                        json = data_set) #dataset will be automatically converted to JSON by the urequests library
                    response = response.json()

                    print(response)

                    sns_index = response["analysis"]["sns_index"]
                    print(sns_index)
                    pns_index = response["analysis"]["pns_index"]
                    print(pns_index)
                    stress_index = response["analysis"]["stress_index"]
                    print(stress_index)
                     
                    oled.fill(0)
                    oled.text(f"SNS index: {sns_index}.", 0, 0)
                    oled.text(f"PNS index: {pns_index}.", 0, 15)
                    oled.text(f"Stress index:", 0, 30)
                    oled.text(f"{stress_index}", 0, 40)

                    oled.show()
                    break
                
            
            beginning_value = None

        time.sleep_ms(100)

    print("a")



def change_display():
    global beginning_value, previous_value, increasing, first_peak, time_of_first_peak, second_peak, time_of_second_peak
    global time_of_previous_peak, time_of_current_peak, process_finished, interval, bpm, v, samples 
    oled.fill(0)
    if menu == 1:
        program1()
                
    if menu == 2:
        program2()

    if menu == 3:
        
        program3()
        
        
def rotsw_handler(menu):
    global beginning_value, previous_value, increasing, first_peak, time_of_first_peak, second_peak, time_of_second_peak
    global time_of_previous_peak, time_of_current_peak, process_finished, interval, bpm, v, samples 
    global display
    sleep_ms(20)
    if rotsw.value() == 0:
        if display == 0:
            change_display()   
            display = menu
        else:
            menu_handler()
            display = 0
    
rotsw.irq(handler = rotsw_handler, trigger = Pin.IRQ_FALLING)
menu_handler()

