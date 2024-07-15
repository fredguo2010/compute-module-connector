'''
Author: Fred Guo fred.guo@rockwellautomation.com
Date: 2024-05-31 21:19:38
LastEditors: Fred Guo fred.guo@rockwellautomation.com
LastEditTime: 2024-06-03 00:12:02
FilePath: \corning-havac-energy-saving-algorithm\src\test_algorithm.py
Description: 

Copyright (c) 2024 by Rockwell Automation, All Rights Reserved. 
'''
  
def calculate_cooling_water_return_temperature(wet_bulb_temperature):  

  # The Increment for the Cooling Warter Return Temp is set to beteween 3 to 4
  # If the Wet Bulb Temperature is too low or too high then the increment will be set to lower or upper limits
  # Else the Increment will be linearially between 20 and 30
  if wet_bulb_temperature <= 20:
      increment = 3
  elif wet_bulb_temperature >= 30:
      increment = 4
  else:
    slope = (4 - 3) / (30 - 20)  # k  
    intercept = 3  # b
    increment = slope * (wet_bulb_temperature - 20) + intercept 

  # Calc Cooling Water Return Temp
  cooling_water_return_temperature = wet_bulb_temperature + increment  
    
  return round(cooling_water_return_temperature, 1)  

# Testing...
wet_bulb_temperatures = [18, 22, 25, 30]  
for temp in wet_bulb_temperatures:  
    cooling_water_temp = calculate_cooling_water_return_temperature(temp)  
    print(f"Wet bulb temperature: {temp}, Cooling water return temperature: {cooling_water_temp}")