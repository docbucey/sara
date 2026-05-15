import datetime


import threading
import time
import os
import winsound  # For .wav playback on Windows
from typing import Callable, Optional

class MamaClock:
    def __init__(self):
        self.timers = []  # List of (target_time, callback, repeat, label, sound)
        self.alarms = []  # List of (target_time, callback, label, sound)
        self.reminders = []  # List of (target_time, message, label, sound)
        self.running = False
        self.stock_sounds = {
            'beep': None,  # Use winsound.Beep
            'chime': os.path.join(os.path.dirname(__file__), 'sounds', 'chime.wav'),
            'alert': os.path.join(os.path.dirname(__file__), 'sounds', 'alert.wav'),
        }

    @staticmethod
    def get_time_info():
        now = datetime.datetime.now()
        gregorian = now.strftime("%Y-%m-%d")
        julian = now.strftime("%j")
        hundredth = now.strftime("%H:%M:%S.%f")[:11]
        return {
            "gregorian": gregorian,
            "julian": julian,
            "hundredth_time": hundredth
        }

    def add_timer(self, seconds: float, callback: Callable, repeat: Optional[float]=None, label: str="", sound: str="beep"):
        target = time.time() + seconds
        self.timers.append((target, callback, repeat, label, sound))

    def add_alarm(self, target_time: datetime.datetime, callback: Callable, label: str="", sound: str="chime"):
        self.alarms.append((target_time, callback, label, sound))

    def add_reminder(self, target_time: datetime.datetime, message: str, label: str="", sound: str="alert"):
        self.reminders.append((target_time, message, label, sound))

    def play_sound(self, sound: str):
        if sound == 'beep':
            winsound.Beep(1000, 300)
        elif sound in self.stock_sounds and os.path.exists(self.stock_sounds[sound]):
            winsound.PlaySound(self.stock_sounds[sound], winsound.SND_FILENAME)
        elif os.path.exists(sound):
            winsound.PlaySound(sound, winsound.SND_FILENAME)
        else:
            winsound.Beep(800, 200)

    def run(self):
        self.running = True
        while self.running:
            now = time.time()
            dt_now = datetime.datetime.now()
            # Timers
            for t in list(self.timers):
                target, callback, repeat, label, sound = t
                if now >= target:
                    callback()
                    self.play_sound(sound)
                    self.timers.remove(t)
                    if repeat:
                        self.add_timer(repeat, callback, repeat, label, sound)
            # Alarms
            for a in list(self.alarms):
                target_time, callback, label, sound = a
                if dt_now >= target_time:
                    callback()
                    self.play_sound(sound)
                    self.alarms.remove(a)
            # Reminders
            for r in list(self.reminders):
                target_time, message, label, sound = r
                if dt_now >= target_time:
                    print(f"Reminder: {message}")
                    self.play_sound(sound)
                    self.reminders.remove(r)
            time.sleep(0.05)

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

# Example usage
if __name__ == "__main__":
    clock = MamaClock()
    def say_hello():
        print("Timer: Hello!")
    clock.add_timer(2, say_hello, repeat=5, label="hello_timer", sound="beep")
    clock.add_alarm(datetime.datetime.now() + datetime.timedelta(seconds=4), lambda: print("Alarm!"), label="alarm1", sound="chime")
    clock.add_reminder(datetime.datetime.now() + datetime.timedelta(seconds=6), "Take a break!", label="reminder1", sound="alert")
    clock.start()
    while True:
        time.sleep(1)
