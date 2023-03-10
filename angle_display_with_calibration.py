from machine import Pin, ADC            #importing Pin and ADC class
import time
potentiometer = ADC(28)           #creating potentiometer object
from machine import Pin,SoftSPI
from machine import Timer
machine.freq()          # get the current frequency of the CPU
machine.freq(200000000) # set the CPU frequency to 240 MHz
p20 = Pin(19, Pin.OUT)    # create output pin on GPIO0
p21 = Pin(8, Pin.OUT)    # create output pin on GPIO0
p22 = Pin(9, Pin.OUT)    # create output pin on GPIO0
# construct a SoftSPI bus on the given pins
# polarity is the idle state of SCK
# phase=0 means sample on the first edge of SCK, phase=1 means the second

p20.value(1)
spi = SoftSPI(baudrate=100_000, polarity=1, phase=0, sck=Pin(20), mosi=Pin(18), miso=Pin(12))
spi.init(baudrate=100000) # set the baudrate
displayed_num = 0
counter = 0
blank_counter = 0
blank = 0
average = 0


def handleInterrupt(timer):#timer interrupt handler
    
    global counter#variable to hold info on which digit is being displayed
    global blank_counter#variable for looping through on states of the display(on-off)
    global blank#variable for indicating if we need to blank the display if we are in overrange
    if displayed_num <= 0:
         writenum(displayed_num,counter,blank,1)#turning off the display if the value is equal or lower than zero
    else:
        writenum(displayed_num,counter,blank,0)#turning on the display with the appropiate number displayed
    counter = counter + 1
    if counter > 1:
        counter = 0
    if(displayed_num >32)and(blank_counter == 0)and(blank == 0):#blanking logic
        blank = 1
        blank_counter = 10
    
    if blank_counter >0:
        blank_counter = blank_counter-1
        if blank_counter == 0:
            blank_counter = -10
            blank = 0
    if blank_counter <0:
        blank_counter = blank_counter+1
        
        
tim = Timer(period=5000, mode=Timer.ONE_SHOT, callback=lambda t:print(1))#start of timer
tim.init(period=10, mode=Timer.PERIODIC, callback=handleInterrupt)#timer interrupt for display multiplexing
def writenum(number,digit,blank,ledon):
    if digit == 1:
        time.sleep_us(1)
        digit0 = number%10
        p21.value(0)
        p22.value(1)
        time.sleep_us(1)
    if (digit == 0):
        digit0 = number//10
        if digit0 != 0:
            time.sleep_us(1)
            p22.value(0)
            p21.value(1)
            time.sleep_us(1)
        else:
            time.sleep_us(1)
            p21.value(1)
            p22.value(1)
            time.sleep_us(1)
    
    spibuf = bytearray(1)
    if(digit0 == 0):
        spibuf[0] = 0b00111111
    if(digit0 == 1):
        spibuf[0] = 0b00000110
    if(digit0 == 2):
        spibuf[0] = 0b01011011
    if(digit0 == 3):
        spibuf[0] = 0b01001111
    if(digit0 == 4):
        spibuf[0] = 0b01100110
    if(digit0 == 5):
        spibuf[0] = 0b01101101
    if(digit0 == 6):
        spibuf[0] = 0b01111101
    if(digit0 == 7):
        spibuf[0] = 0b00000111
    if(digit0 == 8):
        spibuf[0] = 0b01111111
    if(digit0 == 9):
        spibuf[0] = 0b01101111
    if(blank == 1):
        spibuf[0] = 0b00000000
    if(ledon == 1):
        spibuf[0] = 0b10000000#indicating via a led that the reading is lower than zero
    spi.write(spibuf)     
    time.sleep_us(5)
    p20.value(0)
    time.sleep_us(5)
    p20.value(1)
    
while True:
    average = 0
    for a in range(20):#average around 20 readings
        sum = 0
        result = 0
        for i in range(1024):#oversample for additional 6 bits
            sum = sum + (potentiometer.read_u16()>>4)
        result = sum>>6    
        average = average + result
        
    average = average/20#scale back a little
    potentiometer_value = (average - 54500) * (40 - 0) / (43025 - 54500) + 0
    print("raw value:         %.2f"%(average))
    print("calc value before correction:  %d"%(int(potentiometer_value)))
    pot_value = 0
    if (potentiometer_value >=0) and(potentiometer_value <11):
        pot_value = (average - 54500) * (10 - 0) / (51080 - 54500) + 0
    if (potentiometer_value >=10) and(potentiometer_value <21):
        pot_value = (average - 51080) * (20 - 12) / (47650 - 51080) + 10
    if (potentiometer_value >=20) and(potentiometer_value <31):
        pot_value = (average - 47650) * (30 - 20) / (44900 - 47650) + 20
    if (potentiometer_value >=30) and(potentiometer_value <41):
        pot_value = (average - 44900) * (40 - 30) / (43025 - 44900) + 30  
        
    #the line above ic copied from the arduino source, it is the map() function
    #(x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    #you can tune the displayed values by adjusting the in_min and in_max according to the values
    #of what you read on the console as you move the potentiometer to its min and max endpoints (3k-4k)
    print("raw value:         %.2f"%(average))
    print("calculated value:  %d"%(int(pot_value)))
    if int(pot_value) >40:
        pot_value = 40
    displayed_num = int(pot_value)
