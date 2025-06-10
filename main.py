"""
Date:
File Description: Main file
Name: Notorious LB
"""

import initializer #Automatically runs initializer 

import sys
from GUI.GUI import GUI
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)  # Create the application object
    window = GUI()         # Create an instance of main window
    window.show()                 # Show the window
    sys.exit(app.exec_())         # Start the Qt event loop and exit cleanly

if __name__ == "__main__":
    main()