import sys
import pyvisa
import csv
import platform
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QFileDialog, QComboBox
)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from datetime import datetime
import usbtmc
instr =  usbtmc.Instrument(2391, 1543)
import subprocess
print(subprocess.run(["python3", "openusbtmc.py"], capture_output=True, text=True))
if platform.system() == "Windows":
    import winsound


class AgilentMultimeterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agilent 34410A Multimeter GUI")
        self.setGeometry(100, 100, 600, 400)

        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        self.data = []

        # UI Elements
        self.device_selector = QComboBox()
        self.refresh_devices()

        self.mode_selector = QComboBox()
        self.mode_selector.addItems([
            "DC Voltage",
            "AC Voltage",
            "DC Current",
            "AC Current",
            "Resistance",
            "Continuity",
            "Frequency",
            "Period",
            "Diode Test"
        ])

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

        self.plot = pg.PlotWidget(title="Measurement Plot")
        self.curve = self.plot.plot(pen='g')
        self.x = []
        self.y = []

        layout = QVBoxLayout()
        layout.addWidget(self.device_selector)
        layout.addWidget(self.mode_selector)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.plot)

        self.setLayout(layout)

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
            self.set_measurement_mode()
            idn = self.instrument.query("*IDN?")
            self.status_label.setText(f"Connected: {idn.strip()}")
            self.start_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Connection error: {e}")

    def set_measurement_mode(self):
        mode = self.mode_selector.currentText()
        cmd = {
            "DC Voltage": "CONF:VOLT:DC 10",
            "AC Voltage": "CONF:VOLT:AC 10",
            "DC Current": "CONF:CURR:DC",
            "AC Current": "CONF:CURR:AC",
            "Resistance": "CONF:RES",
            "Continuity": "CONF:CONT",
            "Frequency": "CONF:FREQ",
            "Period": "CONF:PER",
            "Diode Test": "CONF:DIODe"
        }.get(mode, "CONF:VOLT:DC 10")

        self.instrument.write(cmd)

    def start_logging(self):
        self.set_measurement_mode()
        self.timer.start(1000)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.data.clear()
        self.x.clear()
        self.y.clear()
        self.curve.setData([], [])
        self.plot.enableAutoRange(axis=pg.ViewBox.YAxis)

    def stop_logging(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)

    def read_measurement(self):
        try:
            val = self.instrument.query("READ?").strip()
            voltage = float(val)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.data.append((timestamp, voltage))
            self.x.append(len(self.x))
            self.y.append(voltage)
            self.curve.setData(self.x, self.y)

            mode = self.mode_selector.currentText()

            if "Continuity" in mode:
                if voltage < 1:
                    self.status_label.setText(f"Continuity: PASS ({voltage:.2f} Ω)")
                    if platform.system() == "Windows":
                        winsound.Beep(1000, 200)
                else:
                    self.status_label.setText(f"Continuity: FAIL ({voltage:.2f} Ω)")

            elif "Diode" in mode:
                if 0.4 < voltage < 0.9:
                    self.status_label.setText(f"Diode Test: PASS ({voltage:.2f} V)")
                else:
                    self.status_label.setText(f"Diode Test: FAIL ({voltage:.2f} V)")

            else:
                self.status_label.setText(f"{mode}: {voltage:.5f}")

        except Exception as e:
            self.status_label.setText(f"Read error: {e}")
            self.stop_logging()

    def save_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Value"])
                    writer.writerows(self.data)
                self.status_label.setText("CSV saved.")
            except Exception as e:
                self.status_label.setText(f"Save error: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = AgilentMultimeterGUI()
    gui.show()
    sys.exit(app.exec_())
