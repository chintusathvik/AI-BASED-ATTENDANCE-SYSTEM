import pandas as pd
import datetime
import os

def generate_daily_report(attendance_df):
    ts = datetime.datetime.now()
    date = ts.strftime('%Y-%m-%d')
    file_name = f"Attendance/Attendance_{date}.xlsx"
    attendance_df.to_excel(file_name, index=False)
    return file_name
