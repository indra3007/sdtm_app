
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from threading import Thread
from my_app_8 import app  # Import your Dash app from app.py
from PyQt5.QtCore import QUrl
# Define the PyQt main window
class DashWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dash App in PyQt")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create a QWebEngineView widget
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

        # Start the Dash server in a separate thread
        self.start_dash_server()

        # Convert the string URL to QUrl and load it in the QWebEngineView
        self.browser.setUrl(QUrl("http://127.0.0.1:8050"))

    def start_dash_server(self):
        # Start the Dash app server in a separate thread
        dash_thread = Thread(target=self.run_dash, daemon=True)
        dash_thread.start()

    def run_dash(self):
        # Run the Dash app
        app.run_server(debug=False, use_reloader=False)

# Main entry point for PyQt application
if __name__ == "__main__":
    qt_app = QApplication(sys.argv)  # This is the PyQt application instance
    main_window = DashWindow()
    main_window.show()
    sys.exit(qt_app.exec_())  # Start the PyQt event loop