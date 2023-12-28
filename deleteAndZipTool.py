import tkinter as tk
from tkinter import messagebox
import boto3
from datetime import datetime, timedelta
import pytz
import zipfile
import os
import config

# AWS credentials 
aws_access_key_id = config.AWS_ACCESS_KEY_ID
aws_secret_access_key = config.AWS_SECRET_ACCESS_KEY

utc = pytz.UTC
local_tz = pytz.timezone('Etc/GMT+5')  # Adjust time to account for UTC 

def delete_files(bucket, start, end, access_key, secret_key):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    s3 = session.client('s3')

    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket)

    try:
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    last_modified_utc = obj['LastModified'].replace(tzinfo=pytz.UTC)
                    if start <= last_modified_utc <= end:
                        s3.delete_object(Bucket=bucket, Key=obj['Key'])
                        print(f"Deleted {obj['Key']}")
        messagebox.showinfo("Success", "Files deleted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def download_and_zip_files(bucket, start, end, access_key, secret_key):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    s3 = session.client('s3')

    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket)

    download_dir = f"downloads_{start.strftime('%Y%m%d')}"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    try:
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Convert last_modified to UTC
                    last_modified_utc = obj['LastModified'].replace(tzinfo=pytz.UTC)
                    
                    # Debugging (can remove)
                    print(f"Considering file: {obj['Key']}, Last Modified (UTC): {last_modified_utc}")
                    
                    if start <= last_modified_utc <= end:
                        print(f"Downloading file: {obj['Key']}")
                        file_path = os.path.join(download_dir, obj['Key'])
                        s3.download_file(bucket, obj['Key'], file_path)

        zip_name = f"{download_dir}.zip"
        with zipfile.ZipFile(zip_name, 'w') as zipf:
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), file)
        print(f"Created zip archive: {zip_name}")

    except Exception as e:
        print(f"An error occurred: {e}")

def on_delete_click():
    utc = pytz.UTC
    local_tz = pytz.timezone('Etc/GMT+5')  
    
    # Convert the user input for dates into datetime objects in your local timezone
    start_date_local = local_tz.localize(datetime.strptime(start_date_entry.get() + " 00:00:00", '%Y-%m-%d %H:%M:%S'))
    end_date_local = local_tz.localize(datetime.strptime(end_date_entry.get() + " 23:59:59", '%Y-%m-%d %H:%M:%S'))
    
    # Convert local times to UTC for comparison with S3 timestamps
    start_date = start_date_local.astimezone(utc)
    end_date = end_date_local.astimezone(utc)
    
    bucket = bucket_entry.get()
    
    delete_files(bucket, start_date, end_date, aws_access_key_id, aws_secret_access_key)

def on_download_and_zip_click():
    start_date_local = local_tz.localize(datetime.strptime(start_date_entry.get() + " 00:00:00", '%Y-%m-%d %H:%M:%S'))
    end_date_local = local_tz.localize(datetime.strptime(end_date_entry.get() + " 23:59:59", '%Y-%m-%d %H:%M:%S'))
    start_date = start_date_local.astimezone(utc)
    end_date = end_date_local.astimezone(utc)
    bucket = bucket_entry.get()  
    download_and_zip_files(bucket, start_date, end_date, aws_access_key_id, aws_secret_access_key)

# GUI
root = tk.Tk()
root.title("AWS S3 File Manager")

tk.Label(root, text="Bucket Name").pack()
bucket_entry = tk.Entry(root)
bucket_entry.pack()

tk.Label(root, text="Start Date (YYYY-MM-DD)").pack()
start_date_entry = tk.Entry(root)
start_date_entry.pack()

tk.Label(root, text="End Date (YYYY-MM-DD)").pack()
end_date_entry = tk.Entry(root)
end_date_entry.pack()

delete_button = tk.Button(root, text="Delete Files", command=on_delete_click)
delete_button.pack()

download_zip_button = tk.Button(root, text="Download and Zip Files", command=on_download_and_zip_click)
download_zip_button.pack()

root.mainloop()
