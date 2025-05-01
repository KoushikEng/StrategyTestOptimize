import sys
import time
from threading import Thread, Event

class ConsoleAnimator:
    def __init__(self):
        self.animation_thread = None
        self.stop_event = Event()
        self.current_message = ""
        self.last_line_length = 0
    
    def _animate(self):
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        
        while not self.stop_event.is_set():
            frame = frames[i % len(frames)]
            # Clear previous line and write new one
            sys.stdout.write(f'\r{" " * self.last_line_length}\r')
            sys.stdout.write(f'{frame} {self.current_message}')
            sys.stdout.flush()
            self.last_line_length = len(f'{frame} {self.current_message}')
            i += 1
            time.sleep(0.1)
        
        # Clear the animation line
        sys.stdout.write(f'\r{" " * self.last_line_length}\r')
        sys.stdout.flush()
    
    def start(self, message=""):
        """Start animation with optional initial message"""
        self.stop_event.clear()
        self.current_message = message
        self.animation_thread = Thread(target=self._animate)
        self.animation_thread.start()
    
    def write(self, message):
        """Update the animation message"""
        self.current_message = message
    
    def done(self, final_message=None, success=True):
        """Stop animation and display final message"""
        self.stop_event.set()
        if self.animation_thread:
            self.animation_thread.join()
        
        if final_message is not None:
            prefix = "✓ " if success else "✗ "
            print(f'\r{prefix}{final_message}')
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        self.done(success=success)
        return True
