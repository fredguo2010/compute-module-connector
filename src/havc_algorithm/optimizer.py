'''
Author: Fred Guo fred.guo@rockwellautomation.com
Date: 2024-05-31 21:19:38
LastEditors: Fred Guo fred.guo@rockwellautomation.com
LastEditTime: 2024-06-02 19:53:59
FilePath: \corning-havac-energy-saving-algorithm\src\hvac_algorithm\optimizer.py
Description: main class access to algorithms for hvac

Copyright (c) 2024 by Rockwell Automation, All Rights Reserved. 
'''

class Optimizer:  
  def __init__(self, wet_bulb_temperature):  
      self.wet_bulb_temperature = wet_bulb_temperature 

  def validateInput(self):
    return self.wet_bulb_temperature >= 5 and self.wet_bulb_temperature <= 35

  def calculate_cooling_water_return_temperature(self):  
    # The Increment for the Cooling Warter Return Temp is set to beteween 3 to 4
    # If the Wet Bulb Temperature is too low or too high then the increment will be set to lower or upper limits
    # Else the Increment will be linearially between 20 and 30
    if self.wet_bulb_temperature <= 20:
        increment = 3
    elif self.wet_bulb_temperature >= 30:
        increment = 4
    else:
      slope = (4 - 3) / (30 - 20)  # k  
      intercept = 3  # b
      increment = slope * (self.wet_bulb_temperature - 20) + intercept 

    # Calc Cooling Water Return Temp
    cooling_water_return_temperature = self.wet_bulb_temperature + increment  
      
    return round(cooling_water_return_temperature, 1)  
  
  def validateOutput(self, outputVal):
    return outputVal >= 15 and outputVal <= 30