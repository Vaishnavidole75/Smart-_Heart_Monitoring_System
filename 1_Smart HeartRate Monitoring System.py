# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21  14:38:30 2023

@author: Vaishnavi
"""

#        Smart Heart Rate Monitoring System

#REQUIIRED DATA:-
#1] - Hardware SetUP ( Heart Monitoring System)
#2] - ECG Data (.csv/.xcl  file)
#3] - Smart Application to Monitor(GUI Window)


'Package need to import for to develop Our System'
import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.animation as animation
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import scipy.signal
import serial
from serial import SerialException
import peakutils
import xlwt
import threading
import time
import pandas as pd
from matplotlib import pyplot as plt
from scipy.signal import find_peaks


# Global variables for the heart rate monitor
recording = False
serialDataRecorded = []
serialOpen = False
serialData = [0] * 70
OptionList = ["--Select a COM port--"] + [str(i) for i in range(19)]
global ser, ax, recordText, labelRecord, connectText, labelConnect

# Login window class
class LoginWindow:
    def __init__(self, master):
        self.master = master        
        self.master.title("Login")
        self.master.geometry("400x600")

        # Username Field
        self.username_label = tk.Label(master, text="Username:")
        self.username_label.pack(pady=5)
        self.username_entry = tk.Entry(master)
        self.username_entry.pack(pady=5)

        # Password Field
        self.password_label = tk.Label(master, text="Password:")
        self.password_label.pack(pady=5)
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.pack(pady=5)

        # Login Button
        self.login_button = tk.Button(master, text="Login", command=self.login, bg="green", fg="white")
        self.login_button.pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # System authentication 
        if username == "admin" and password == "Password@123":
            self.master.destroy()  # Close login window
            open_heart_rate_monitor()  # Open heart rate monitor GUI
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

# Function to open the heart rate monitor GUI
def open_heart_rate_monitor():
    window = tk.Tk()
    window.title("Heart Rate Monitor v0.1")
    window.rowconfigure(0, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)

    fig = Figure(figsize=(6, 5), dpi=50)
    global ax
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim([0, 10])
    ax.set_ylim([0, 150])
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()

    lbl_live = tk.Label(window, text="Live Data:", font=('Helvetica', 12), fg='red')
    fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)

    global connectText, labelConnect
    connectText = tk.StringVar(window)
    connectText.set("Not connected")
    labelConnect = tk.Label(fr_buttons, textvariable=connectText, font=('Helvetica', 12), fg='red')
    labelConnect.grid(row=0, column=0, sticky="ew", padx=10)

    var = tk.StringVar(window)
    var.set(OptionList[0])
    opt_com = tk.OptionMenu(fr_buttons, var, *OptionList)
    opt_com.config(width=20)
    opt_com.grid(row=1, column=0, sticky="ew", padx=10)

    btn_st_serial = tk.Button(fr_buttons, text="Open Serial", command=lambda: startSerial(var))
    btn_st_serial.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

    btn_stop_serial = tk.Button(fr_buttons, text="Close Serial", command=kill_Serial)
    btn_stop_serial.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

    global recordText, labelRecord
    recordText = tk.StringVar(window)
    recordText.set("Not Recording")
    labelRecord = tk.Label(fr_buttons, textvariable=recordText, font=('Helvetica', 12), fg='black')
    labelRecord.grid(row=4, column=0, sticky="ew", padx=10)

    btn_st_rec = tk.Button(fr_buttons, text="Start Recording", command=startRecording)
    btn_st_rec.grid(row=5, column=0, sticky="ew", padx=10, pady=5)

    btn_stop_rec = tk.Button(fr_buttons, text="Stop Recording", command=stopRecording)
    btn_stop_rec.grid(row=6, column=0, sticky="ew", padx=10, pady=5)

    # Add Get Analysis button
    btn_get_analysis = tk.Button(fr_buttons, text="Get Analysis", command=open_ml_app)
    btn_get_analysis.grid(row=7, column=0, sticky="ew", padx=10, pady=5)

    fr_buttons.grid(row=0, column=0, sticky="ns")
    lbl_live.grid(row=1, column=1, sticky="nsew")
    canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew")

    def ask_quit():
        if messagebox.askokcancel("Quit", "This will end the serial connection :)"):
            kill_Serial()
            window.destroy()

    window.protocol("WM_DELETE_WINDOW", ask_quit)
    ani = animation.FuncAnimation(fig, animate, interval=50)
    window.mainloop()

def read_from_port(ser):
    global serialOpen, serialData, serialDataRecorded
    while serialOpen:
        reading = float(ser.readline().strip())
        serialData.append(reading)
        if recording:
            serialDataRecorded.append(reading)

def startSerial(var):
    global ser, serialOpen, connectText, labelConnect
    try:
        s = var.get()
        ser = serial.Serial('COM' + s , 9600, timeout=20)
        ser.close()
        ser.open()
        serialOpen = True
        thread = threading.Thread(target=read_from_port, args=(ser,))
        thread.start()
        connectText.set("Connected to COM" + s)
        labelConnect.config(fg="green")
        return serialOpen
    except SerialException:
        connectText.set("Error: wrong port?")
        labelConnect.config(fg="red")

def kill_Serial():
    global ser, serialOpen, connectText, labelConnect
    try:
        serialOpen = False
        time.sleep(1)
        ser.close()
        connectText.set("Not connected")
        labelConnect.config(fg="red")
    except:
        connectText.set("Failed to end serial")

def animate(i):
    global serialData, ax
    if len(serialData) > 70:
        serialData = serialData[-70:]
    data = serialData[-70:]
    x = np.linspace(0, 69, dtype='int', num=70)
    ax.clear()
    ax.plot(x, data)

def startRecording():
    global recording, recordText, labelRecord
    if serialOpen:
        recording = True
        recordText.set("Recording . . . ")
        labelRecord.config(fg="red")
    else:
        messagebox.showinfo("Error", "Please start the serial monitor")

def stopRecording():
    global recording, serialDataRecorded, recordText, labelRecord
    if recording:
        recording = False
        recordText.set("Not Recording")
        labelRecord.config(fg="black")
        processRecording(serialDataRecorded)
        serialDataRecorded = []
    else:
        messagebox.showinfo("Error", "You weren't recording!")

def processRecording(data):
    z = scipy.signal.savgol_filter(data, 11, 3)
    data2 = np.asarray(z, dtype=np.float32)
    a = len(data)
    base = peakutils.baseline(data2, 2)
    y = data2 - base
    directory = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel Sheet", "*.csv"),("All Files", "*.*")])
    if not directory:
        return
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet 1")
    for i in range(a):
        sheet1.write(i, 0, i)
        sheet1.write(i, 1, y[i])
    book.save(directory)

# Function to open ML Application window
def open_ml_app():
    root = tk.Tk()
    app = MLApp(root)
    root.mainloop()

class MLApp:
    def __init__(self, master):
        self.master = master
        self.master.title("ML Application")
        self.master.geometry("1920x1000")

        # Buttons for loading file and analyzing heart rate
        self.btn_load = tk.Button(master, text="Load File", command=self.load_file, bg="blue", fg="white")
        self.btn_load.pack(pady=10)

        self.btn_analyze = tk.Button(master, text="Analyze Heart Rate", command=self.analyze_heart_rate, bg="green", fg="white")
        self.btn_analyze.pack(pady=5)

        # Labels for displaying results
        self.peak_value_label = tk.Label(master, text="")
        self.peak_value_label.pack(pady=5)

        self.result_label = tk.Label(master, text="")
        self.result_label.pack(pady=5)

        # Matplotlib figure and canvas for heart rate analysis
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        self.data = pd.read_csv(self.file_path, nrows=200)  # Read only the first 200 rows

    def preprocess_data(self):
        # No need to preprocess or drop columns if only 'time' and 'heartbeat_rate' are present
        pass

    def analyze_heart_rate(self):
        if hasattr(self, 'file_path'):
            try:
                # Find peaks with a minimum height threshold
                peaks, _ = find_peaks(self.data['target'], height=80)

                # Plot graph
                self.ax.clear()
                self.ax.plot(self.data.index, self.data['target'], label='Heart Beat Rate')  # Add label for legend
                self.ax.set_xlabel('Time')
                self.ax.set_ylabel('Heart Beat Rate')
                self.ax.set_title('Here is your Heart Rate Analysis!!!!')

                # Annotate peaks
                for peak in peaks:
                    self.ax.annotate(f'Peak: {self.data["target"][peak]}', xy=(peak, self.data['target'][peak]),
                                     xytext=(peak, self.data['target'][peak] + 5),
                                     arrowprops=dict(facecolor='red', shrink=0.05))

                # Add legend
                self.ax.legend()

                self.canvas.draw()

                # Calculate average heart rate
                avg_heart_rate = self.data['target'].mean()
                self.peak_value_label.config(text=f"Average Heart Rate: {avg_heart_rate:.2f}")

                # Determine if heart rate is normal or abnormal
                if 60 <= avg_heart_rate <= 100:
                    self.result_label.config(text="Heart is Normal")
                else:
                    self.result_label.config(text="Heart is Abnormal")
            except Exception as e:
                self.result_label.config(text="Error occurred: " + str(e))
        else:
            self.result_label.config(text="Please load a file first")

def main():
    root = tk.Tk()
    login_window = LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
