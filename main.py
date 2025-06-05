from initializer import verify_requirements
try:
    verify_requirements()  # Ensures that proper libraries are installed
except FileNotFoundError as e:
    print(f"Could not find requirements: {e}")

import sys
from GUI.GUI import GUI
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)  # Create the application object
    window = GUI()         # Create an instance of our main window
    window.show()                 # Show the window
    sys.exit(app.exec_())         # Start the Qt event loop and exit cleanly

if __name__ == "__main__":
    main()