# a code that calculates the basic HRV analysis parameters and shows the values on the OLED

from machine import Pin, I2C
import ssd1306

# OLED display
pin_i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = ssd1306.SSD1306_I2C(128, 64, pin_i2c)

# PPI values
ppi_1 = [1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100, 1000, 1100]
ppi_2 = [828, 836, 852, 760, 800, 796, 856, 824, 808, 776, 724, 816, 800, 812, 812, 812, 756, 820, 812, 800]

# HRV parameters function
def hrv_parameters(ppi_set):
    mean_ppi = sum(ppi_set) / len(ppi_set)
    mean_hr = 60 * 1000 / mean_ppi

    # SDNN
    sdnn = 0
    for ppi in ppi_set:
        sdnn += (ppi - mean_ppi) ** 2
    sdnn = (sdnn / (len(ppi_set) - 1)) ** 0.5

    # RMSSD
    rmssd = 0
    for i in range(len(ppi_set) - 1):
        rmssd += (ppi_set[i+1] - ppi_set[i]) ** 2
    rmssd = (rmssd / (len(ppi_set) - 1)) ** 0.5

    return mean_ppi, mean_hr, sdnn, rmssd

# HRV parameters for set 1
mean_ppi_1, mean_hr_1, sdnn_1, rmssd_1 = hrv_parameters(ppi_1)

# Display HRV parameters on OLED
oled.fill(0)
oled.text("Test Set 1", 0, 0)
oled.text("PPI: {:.0f} ms".format(mean_ppi_1), 0, 10)
oled.text("HR: {:.0f} bpm".format(mean_hr_1), 0, 20)
oled.text("SDNN: {:.0f} ms".format(sdnn_1), 0, 30)
oled.text("RMSSD: {:.0f} ms".format(rmssd_1), 0, 40)
oled.show()

# HRV parameters for set 2
mean_ppi_2, mean_hr_2, sdnn_2, rmssd_2 = hrv_parameters(ppi_2)

# Display HRV parameters on OLED
oled.fill(0)
oled.text("Test Set 2", 0, 0)
oled.text("PPI: {:.0f} ms".format(mean_ppi_2), 0, 10)
oled.text("HR: {:.0f} bpm".format(mean_hr_2), 0, 20)
oled.text("SDNN: {:.0f} ms".format(sdnn_2), 0, 30)
oled.text("RMSSD: {:.0f} ms".format(rmssd_2), 0, 40)