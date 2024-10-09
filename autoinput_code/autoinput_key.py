import sys
import pyautogui
import time
import json

with open(sys.argv[1], 'r') as f:
    data = json.load(f)
    
for content in data:
    if content["type"].lower() == "key":
        pyautogui.click(100,100)
        for key in content["input"]:
            for i in range(5):
                pyautogui.hotkey(*key)
                time.sleep(0.1)
            time.sleep(0.5)
