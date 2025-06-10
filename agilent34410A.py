import sys
import pyvisa
import csv
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QFileDialog, QComboBox
)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from datetime import datetime


class DMMReader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agilent 34410A Voltage Logger")
        self.setGeometry(100, 100, 600, 400)

        # VISA and instrument
        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        self.data = []

        # UI Elements
        self.device_selector = QComboBox()
        self.refresh_devices()

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_device)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_logging)
        self.start_button.setEnabled(False)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_logging)
        self.stop_button.setEnabled(False)

        self.save_button = QPushButton("Save CSV")
        self.save_button.clicked.connect(self.save_csv)
        self.save_button.setEnabled(False)

        self.status_label = QLabel("Status: Disconnected")

        self.plot = pg.PlotWidget(title="Voltage (V)")
        self.plot.setYRange(0, 10)
        self.curve = self.plot.plot(pen='g')
        self.x = []
        self.y = []

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.device_selector)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.plot)

        self.setLayout(layout)

        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_measurement)

    def refresh_devices(self):
        self.device_selector.clear()
        try:
            resources = self.rm.list_resources()
            for res in resources:
                if "USB" in res:
                    self.device_selector.addItem(res)
        except Exception as e:
            self.status_label.setText(f"Error listing devices: {e}")

    def connect_device(self):
        res = self.device_selector.currentText()
        try:
            self.instrument = self.rm.open_resource(res)
            self.instrument.write("*RST")
            self.instrument.write("CONF:VOLT:DC 10")
            idn = self.instrument.query("*IDN?")
            self.status_label.setText(f"Connected: {idn.strip()}")
            self.start_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Connection error: {e}")

    def start_logging(self):
        self.timer.start(1000)  # every second
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.data.clear()
        self.x.clear()
        self.y.clear()
        self.curve.setData([], [])

    def stop_logging(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)

    def read_measurement(self):
        try:
            voltage = float(self.instrument.query("READ?").strip())
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.x.append(len(self.x))
            self.y.append(voltage)
            self.data.append((timestamp, voltage))
            self.curve.setData(self.x, self.y)
            self.status_label.setText(f"Voltage: {voltage:.5f} V")
        except Exception as e:
            self.status_label.setText(f"Read error: {e}")
            self.stop_logging()

    def save_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Voltage (V)"])
                    writer.writerows(self.data)
                self.status_label.setText("CSV saved.")
            except Exception as e:
                self.status_label.setText(f"Save error: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DMMReader()
    window.show()
    sys.exit(app.exec_())
