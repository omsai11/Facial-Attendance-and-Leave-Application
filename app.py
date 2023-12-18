import streamlit as st
import pandas as pd
import time 
from flask import Flask, render_template, request, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql
import cv2
import pickle
import numpy as np
import os
from sklearn.neighbors import KNeighborsClassifier
import cv2
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime
from win32com.client import Dispatch

from twilio.rest import Client

# Your Twilio account SID and auth token from the Twilio Console
account_sid = 'ACe0b7a55e22b79a4a619765f22ca4ab50'
auth_token = 'b774972231658cf8a67b5a6cf2139b7d'

# Create a Twilio client
client = Client(account_sid, auth_token)

# Replace with your Twilio phone number and the recipient's phone number
twilio_phone_number = 'whatsapp:+14155238886'
recipient_phone_number = 'whatsapp:+919067951440'  # Replace with the recipient's phone number

# The message you want to send
message_body1 = 'Your leave application is approved Successfully !'
message_body2 = 'Your leave application is not approved !'

def speak(str1):
    speak=Dispatch(("SAPI.SpVoice"))
    speak.Speak(str1)
video=cv2.VideoCapture(0)
facedetect=cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')

app = Flask(__name__)

db = pymysql.connect(
    host='localhost',
    user='poshan',
    password='Poshan@1234',
    database='cse'
)

@app.route('/', methods=['GET', 'POST'])
def hello_world(): 
    return render_template('index.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/leave', methods=['GET', 'POST'])
def leave():
    return render_template('mail.html')



@app.route('/approve',methods=['GET', 'POST'])
def display_leave_applications():
    cursor = db.cursor()
    cursor.execute("SELECT name, reason, contact FROM leave_applications")
    data = cursor.fetchall()
    return render_template('application.html', applications=data)


@app.route('/submit', methods=['POST'])
def submit_leave():
    name = request.form['name']
    reason = request.form['reason']
    contact = request.form['mbl']
    status = "no"
    
    cursor = db.cursor()
    query = "INSERT INTO leave_applications (name, reason, contact, status) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (name, reason, contact, status))

    # Commit the changes to the database
    db.commit()

    if cursor.rowcount > 0:
        print('Leave application submitted successfully!')
        return render_template('submit.html')
    else:
        return render_template('notsubmit.html')
    
@app.route('/accept/<string:name>', methods=['GET'])
def accept_leave_application(name):
    cursor = db.cursor()
    query = "DELETE FROM leave_applications WHERE name = %s"
    cursor.execute(query, (name,))
    db.commit()
    try:
    # Send the message
        message = client.messages.create(
            body=message_body1,
            from_=twilio_phone_number,
            to=recipient_phone_number
        )
        print(f"Message SID: {message.sid}")
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")
    return redirect(url_for('display_leave_applications'))

@app.route('/delete/<string:name>', methods=['GET'])
def delete_leave_application(name):
    cursor = db.cursor()
    query = "DELETE FROM leave_applications WHERE name = %s"
    cursor.execute(query, (name,))
    db.commit()
    try:
    # Send the message
        message = client.messages.create(
            body=message_body2,
            from_=twilio_phone_number,
            to=recipient_phone_number
        )
        print(f"Message SID: {message.sid}")
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")
    return redirect(url_for('display_leave_applications'))

    
@app.route('/admin', methods=['POST'])
def login_submitadmin():
    email = request.form['email']
    password = request.form['password']

    cursor = db.cursor()
    query = "SELECT * FROM faculty WHERE email = %s AND password = %s"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()
    print(user)

    if user:
        return redirect(url_for('display_leave_applications'))
    else:
        # Authentication failed, redirect back to login with error message
        return redirect(url_for('/', error='Invalid credentials'))



@app.route('/login', methods=['POST'])
def login_submit():
    email = request.form['email']
    password = request.form['password']

    cursor = db.cursor()
    query = "SELECT * FROM faculty WHERE email = %s AND password = %s"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()
    print(user)

    if user:
        cursor1 = db.cursor()
        faces_data=[]
        index=3
        add_value = user[index]  # Assuming 'add' is a column in your 'faculty' table
        if add_value == 'no':
            id_to_update = 101  # Replace with the specific ID you want to update
            new_value = "yes"  # Replace 'new_value' with the value you want to set

            update_query = "UPDATE faculty SET face = %s WHERE id = %s"
            cursor1.execute(update_query, (new_value, id_to_update))


            db.commit()
            cursor1.close()
            db.close()
            i=0
            name = email
            while True:
                ret,frame=video.read()
                gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces=facedetect.detectMultiScale(gray, 1.3 ,5)
                for (x,y,w,h) in faces:
                    crop_img=frame[y:y+h, x:x+w, :]
                    resized_img=cv2.resize(crop_img, (50,50))
                    if len(faces_data)<=100 and i%10==0:
                        faces_data.append(resized_img)
                    i=i+1
                    cv2.putText(frame, str(len(faces_data)), (50,50), cv2.FONT_HERSHEY_COMPLEX, 1, (50,50,255), 1)
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (50,50,255), 1)
                cv2.imshow("Frame",frame)
                k=cv2.waitKey(1)
                if k==ord('q') or len(faces_data)==100:
                    break
            video.release()
            cv2.destroyAllWindows()

            faces_data=np.asarray(faces_data)
            faces_data=faces_data.reshape(100, -1)


            if 'names.pkl' not in os.listdir('data/'):
                names=[name]*100
                with open('data/names.pkl', 'wb') as f:
                    pickle.dump(names, f)
            else:
                with open('data/names.pkl', 'rb') as f:
                    names=pickle.load(f)
                names=names+[name]*100
                with open('data/names.pkl', 'wb') as f:
                    pickle.dump(names, f)

            if 'faces_data.pkl' not in os.listdir('data/'):
                with open('data/faces_data.pkl', 'wb') as f:
                    pickle.dump(faces_data, f)
            else:
                with open('data/faces_data.pkl', 'rb') as f:
                    faces=pickle.load(f)
                faces=np.append(faces, faces_data, axis=0)
                with open('data/faces_data.pkl', 'wb') as f:
                    pickle.dump(faces, f)
            

            return redirect(url_for('home'))
        else:
            # Redirect to home if 'add' is 'yes'
            return redirect(url_for('home'))
    else:
        # Authentication failed, redirect back to login with error message
        return redirect(url_for('login', error='Invalid credentials'))
    
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    video=cv2.VideoCapture(0)
    facedetect=cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
    with open('data/names.pkl', 'rb') as w:
        LABELS=pickle.load(w)
    with open('data/faces_data.pkl', 'rb') as f:
        FACES=pickle.load(f)

    print('Shape of Faces matrix --> ', FACES.shape)

    knn=KNeighborsClassifier(n_neighbors=5)
    knn.fit(FACES, LABELS)

    imgBackground=cv2.imread("background.png")

    COL_NAMES = ['NAME', 'TIME']

    while True:
        ret,frame=video.read()
        gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces=facedetect.detectMultiScale(gray, 1.3 ,5)
        ts=time.time()
        date=datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
        timestamp=datetime.fromtimestamp(ts).strftime("%H:%M-%S")
        for (x,y,w,h) in faces:
            crop_img=frame[y:y+h, x:x+w, :]
            resized_img=cv2.resize(crop_img, (50,50)).flatten().reshape(1,-1)
            output=knn.predict(resized_img)
            ts=time.time()
            date=datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
            timestamp=datetime.fromtimestamp(ts).strftime("%H:%M-%S")
            exist=os.path.isfile("Attendance/Attendance_" + date + ".csv")
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,0,255), 1)
            cv2.rectangle(frame,(x,y),(x+w,y+h),(50,50,255),2)
            cv2.rectangle(frame,(x,y-40),(x+w,y),(50,50,255),-1)
            cv2.putText(frame, str(output[0]), (x,y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255), 1)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (50,50,255), 1)
            attendance=[str(output[0]), str(timestamp)]
        imgBackground[162:162 + 480, 55:55 + 640] = frame
        cv2.imshow("Frame",imgBackground)
        k=cv2.waitKey(1)
        if k==ord('o'):
            speak("Attendance Taken..")
            time.sleep(5)
            if exist:
                with open("Attendance/Attendance_" + date + ".csv", "+a") as csvfile:
                    writer=csv.writer(csvfile)
                    writer.writerow(attendance)
                    cursor2 = db.cursor()
                    query = "INSERT INTO attendance (id, date, time) VALUES (%s, %s, %s)"
                    cursor2.execute(query, (str(output[0]),date, str(timestamp) ))
                    user = cursor2.fetchone()
                    db.commit()
                    cursor2.close()
                    db.close()

                    print("Attendance inserted successfully!", user)
                    video.release()
                    cv2.destroyAllWindows() 
                    return render_template('camsuccessful.html')
                    csvfile.close()
            else:
                with open("Attendance/Attendance_" + date + ".csv", "+a") as csvfile:
                    writer=csv.writer(csvfile)
                    writer.writerow(COL_NAMES)
                    writer.writerow(attendance)
                    video.release()
                    cv2.destroyAllWindows()
                    return render_template('camfailes.html')
                    csvfile.close()
        if k==ord('q'):
            break
    video.release()
    cv2.destroyAllWindows()

    return render_template('.html')


if __name__ == "__main__":
    app.run(debug=True, port=8000)