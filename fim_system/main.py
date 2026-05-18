import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import AppWindow

if __name__ == "__main__":
    app = AppWindow()
    app.mainloop()
