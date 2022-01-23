import smbus
import time
from datetime import datetime

# Config Register (R/W)
_REG_CONFIG                 = 0x00
# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE           = 0x01

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE             = 0x02

# POWER REGISTER (R)
_REG_POWER                  = 0x03

# CURRENT REGISTER (R)
_REG_CURRENT                = 0x04

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION            = 0x05

class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V               = 0x00      # set bus voltage range to 16V
    RANGE_32V               = 0x01      # set bus voltage range to 32V (default)

class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV              = 0x00      # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV              = 0x01      # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV             = 0x02      # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV             = 0x03      # shunt prog. gain set to /8, 320 mV range

class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S          = 0x00      #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S         = 0x01      # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S         = 0x02      # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S         = 0x03      # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S         = 0x09      # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S         = 0x0A      # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S         = 0x0B      # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S        = 0x0C      # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S        = 0x0D      # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S        = 0x0E      # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S       = 0x0F      # 12bit, 128 samples, 68.10ms

class Mode:
    """Constants for ``mode``"""
    POWERDOW                = 0x00      # power down
    SVOLT_TRIGGERED         = 0x01      # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02      # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03      # shunt and bus voltage triggered
    ADCOFF                  = 0x04      # ADC off
    SVOLT_CONTINUOUS        = 0x05      # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06      # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07      # shunt and bus voltage continuous


class INA219:
    def __init__(self, i2c_bus=1, addr=0x40):
        self.bus = smbus.SMBus(i2c_bus);
        self.addr = addr

        # Set chip to known config values to start
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2A()

    def read(self,address):
        data = self.bus.read_i2c_block_data(self.addr, address, 2)
        return ((data[0] * 256 ) + data[1])

    def write(self,address,data):
        temp = [0,0]
        temp[1] = data & 0xFF
        temp[0] =(data & 0xFF00) >> 8
        self.bus.write_i2c_block_data(self.addr,address,temp)

    def set_calibration_32V_2A(self):
        """Configures to INA219 to be able to measure up to 32V and 2A of current. Counter
           overflow occurs at 3.2A.
           ..note :: These calculations assume a 0.1 shunt ohm resistor is present
        """
        # By default we use a pretty huge range for the input voltage,
        # which probably isn't the most appropriate choice for system
        # that don't use a lot of power.  But all of the calculations
        # are shown below if you want to change the settings.  You will
        # also need to change any relevant register settings, such as
        # setting the VBUS_MAX to 16V instead of 32V, etc.

        # VBUS_MAX = 32V             (Assumes 32V, can also be set to 16V)
        # VSHUNT_MAX = 0.32          (Assumes Gain 8, 320mV, can also be 0.16, 0.08, 0.04)
        # RSHUNT = 0.1               (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 3.2A

        # 2. Determine max expected current
        # MaxExpected_I = 2.0A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.000061              (61uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0,000488              (488uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.0001 (100uA per bit)
        self._current_lsb = .1  # Current LSB = 100uA per bit

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 4096 (0x1000)

        self._cal_value = 4096

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.002 (2mW per bit)
        self._power_lsb = .002  # Power LSB = 2mW per bit

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # Max_Current = Current_LSB * 32767
        # Max_Current = 3.2767A before overflow
        #
        # If Max_Current > Max_Possible_I then
        #    Max_Current_Before_Overflow = MaxPossible_I
        # Else
        #    Max_Current_Before_Overflow = Max_Current
        # End If
        #
        # Max_ShuntVoltage = Max_Current_Before_Overflow * RSHUNT
        # Max_ShuntVoltage = 0.32V
        #
        # If Max_ShuntVoltage >= VSHUNT_MAX
        #    Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Else
        #    Max_ShuntVoltage_Before_Overflow = Max_ShuntVoltage
        # End If

        # 8. Compute the Maximum Power
        # MaximumPower = Max_Current_Before_Overflow * VBUS_MAX
        # MaximumPower = 3.2 * 32V
        # MaximumPower = 102.4W

        # Set Calibration register to 'Cal' calculated above
        self.write(_REG_CALIBRATION,self._cal_value)

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = self.bus_voltage_range << 13 | \
                      self.gain << 11 | \
                      self.bus_adc_resolution << 7 | \
                      self.shunt_adc_resolution << 3 | \
                      self.mode
        self.write(_REG_CONFIG,self.config)
        
    def getShuntVoltage_mV(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01
        
    def getBusVoltage_V(self):  
        self.write(_REG_CALIBRATION,self._cal_value)
        self.read(_REG_BUSVOLTAGE)
        return (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004
        
    def getCurrent_mA(self):
        value = self.read(_REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb
        
    def getPower_W(self):
        value = self.read(_REG_POWER)
        if value > 32767:
            value -= 65535
        return value * self._power_lsb    
        
      
if __name__=='__main__':

    ina1 = INA219(addr=0x40)
    ina2 = INA219(addr=0x41)
    ina3 = INA219(addr=0x42)
    ina4 = INA219(addr=0x43)
    
    print("ina219_v2 test")
    
    import time
    import sqlite3
    con = sqlite3.connect('STC_Voltage.db')
    
    
    last_write = 0
    interval = 29                                         # time in seconds
    samples = 0                                           # number of voltage sambles fomr ina219
    repetitions = 0                                       # number of times that infoirmation is saved on db
    low_v_rpi_times = 0                                   # number of times PBPi is below 4.82 V
    low_v_bat1_times = 0                                  # number of times BAT1 is below 13.5 V
    rpi_voltage_min = 5.1
    t_last_low_v_rpi ='N/A'
    t_last_low_v_bat1 = 'N/A'
    t_last_rpi_voltage_min = 'N/A'
    cputempmax = 40
    t_last_cputempmax = 'N/A'
    now = datetime.now()                                  # current date and time
    running_from = now.strftime("%d/%m/%Y, %H:%M:%S")
    
    import io 
    
    while True:
        bus_voltage1 = ina1.getBusVoltage_V()             # voltage on V- (load side)
        shunt_voltage1 = ina1.getShuntVoltage_mV() / 1000 # voltage between V+ and V- across the shunt
        current1 = ina1.getCurrent_mA()                   # current in mA
        power1 = ina1.getPower_W()                        # power in watts

        bus_voltage2 = ina2.getBusVoltage_V()             # voltage on V- (load side)
        shunt_voltage2 = ina2.getShuntVoltage_mV() / 1000 # voltage between V+ and V- across the shunt
        current2 = ina2.getCurrent_mA()                   # current in mA
        power2 = ina2.getPower_W()                        # power in watts

        bus_voltage3 = ina3.getBusVoltage_V()             # voltage on V- (load side)
        shunt_voltage3 = ina3.getShuntVoltage_mV() / 1000 # voltage between V+ and V- across the shunt
        current3 = ina3.getCurrent_mA()                   # current in mA
        power3 = ina3.getPower_W()                        # power in watts

        bus_voltage4 = ina4.getBusVoltage_V()             # voltage on V- (load side)
        shunt_voltage4 = ina4.getShuntVoltage_mV() / 1000 # voltage between V+ and V- across the shunt
        current4 = ina4.getCurrent_mA()                   # current in mA
        power4 = ina4.getPower_W()                        # power in watts
        
        now = datetime.now()                              # current date and time
        date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        ara = time.time()
        samples = samples + 1
        f = open("/sys/class/thermal/thermal_zone0/temp", "r")
        t = f.readline ()
        cputemp = int(t)
       
        print("ina219_v2 test")
        #print ("CPU temp: %.3f" %(cputemp/1000.0))
        print("CPU temp: {:6.3f}C    ".format((cputemp/1000.0)))

        # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
        print("PSU Voltage SOL_1: {:6.3f}V    Shunt Voltage:{:9.6f}V    Load Voltage:{:6.3f}V    Power:{:9.6f}W    Current:{:9.6f}A".format((bus_voltage1 + shunt_voltage1 - 0.03),(shunt_voltage1),(bus_voltage1),(power1),(current1/1000)))
        print("PSU Voltage BAT_1: {:6.3f}V    Shunt Voltage:{:9.6f}V    Load Voltage:{:6.3f}V    Power:{:9.6f}W    Current:{:9.6f}A".format((bus_voltage2 + shunt_voltage2 - 0.18),(shunt_voltage2),(bus_voltage2),(power2),(current2/1000)))
        print("PSU Voltage BAT_2: {:6.3f}V    Shunt Voltage:{:9.6f}V    Load Voltage:{:6.3f}V    Power:{:9.6f}W    Current:{:9.6f}A".format((bus_voltage3 + shunt_voltage3 - 0.00),(shunt_voltage3),(bus_voltage3),(power3),(current3/1000)))
        print("PSU Voltage RB_Pi: {:6.3f}V    Shunt Voltage:{:9.6f}V    Load Voltage:{:6.3f}V    Power:{:9.6f}W    Current:{:9.6f}A".format((bus_voltage4 + shunt_voltage4 - 0.05),(shunt_voltage4),(bus_voltage4),(power4),(current3/1000)))
       
        print("Date and time: %s" %(date_time))
        print('\033[1m' + 'EB3CJR STC 2022' + '\033[0m')
        print("Running from: %s" %(running_from))
        
        #Detecta i compta el nombre de vegades que el voltatge de la RBPI baixa de 4,82 V
        rpi_voltage = (bus_voltage4 + shunt_voltage4 - 0.05) 
        print("Rpi_V: %s" %(rpi_voltage))
        if rpi_voltage < 4.82:
            low_v_rpi_times = low_v_rpi_times + 1
            t_last_low_v_rpi = now.strftime("%d/%m/%Y, %H:%M:%S")
            
        #Detecta  i mostra el voltatge minim de la RBPI
        rpi_voltage = (bus_voltage4 + shunt_voltage4 - 0.05) 
        if rpi_voltage < rpi_voltage_min:
            rpi_voltage_min = rpi_voltage
            t_last_rpi_voltage_min = now.strftime("%d/%m/%Y, %H:%M:%S")   
            
        #Detecta i compta el nombre de vegades que el voltatge de la BAT1 baixa de 12,4 V 
        bat1_voltage = (bus_voltage2 + shunt_voltage2 - 0.18) 
        print("BAT1_V: %s" %(bat1_voltage))
        if bat1_voltage < 12.40:
            low_v_bat1_times = low_v_bat1_times + 1
            t_last_low_v_bat1 = now.strftime("%d/%m/%Y, %H:%M:%S")
            
        #Detecta i registra la Tmax de la CPU i l'hora
        if cputemp > cputempmax:
            cputempmax = cputemp
            t_last_cputempmax = now.strftime("%d/%m/%Y, %H:%M:%S")
        
        #print("The bold text is",'\033[1m' + 'Python' + '\033[0m')
        
        if last_write == 0 or ara - last_write > interval:
            cur = con.cursor()
            cur.execute('insert into STC_BAT_dades values (1, ' + str(bus_voltage1) + ',' + str(shunt_voltage1) + ',' + str(current1) + ',' + str(power1) + ',' + str(time.time()) + ')')
            con.commit()
            cur = con.cursor()
            cur.execute('insert into STC_BAT_dades values (2, ' + str(bus_voltage2) + ',' + str(shunt_voltage2) + ',' + str(current2) + ',' + str(power2) + ',' + str(time.time()) + ')')
            con.commit()
            cur = con.cursor()
            cur.execute('insert into STC_BAT_dades values (3, ' + str(bus_voltage3) + ',' + str(shunt_voltage3) + ',' + str(current3) + ',' + str(power3) + ',' + str(time.time()) + ')')
            con.commit()
            cur = con.cursor()
            cur.execute('insert into STC_BAT_dades values (4, ' + str(bus_voltage4) + ',' + str(shunt_voltage4) + ',' + str(current4) + ',' + str(power4) + ',' + str(time.time()) + ')')
            con.commit()
            last_write = ara
            repetitions = repetitions + 1
            
        print("")
        print("ara: %s :: last_write: %s " %(ara, last_write))
        print("#samples: %d, #Repetitions: %d" %(samples, repetitions))
        print("#V< 4,8v: %s, Ultima vegada: %s" %(low_v_rpi_times, t_last_low_v_rpi))
        print("#V<12,4v: %s, Ultima vegada: %s" %(low_v_bat1_times, t_last_low_v_bat1))
        print("CPU Tmax: %s, Ultima vegada: %s" %(cputempmax/1000.0, t_last_cputempmax))
        print("RPI Vmin:  %s, Ultima vegada: %s" %(rpi_voltage_min, t_last_rpi_voltage_min))
        print("")
                
        time.sleep(2)
