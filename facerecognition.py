import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
import pandas as pd
import pyttsx3


KNOWN_FACES_DIR = r"D:\cours\pfa\hardware\code\rfid\faces"
ATTENDANCE_FILE = "attendance.csv"


engine = pyttsx3.init()
engine.setProperty('rate', 150)


known_face_encodings = []
known_face_names = []


def load_known_faces():
    if not os.path.exists(KNOWN_FACES_DIR):
        print(f"Error: Directory '{KNOWN_FACES_DIR}' does not exist. Please create it and add employee images.")
        return

    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            name = os.path.splitext(filename)[0]
            image_path = os.path.join(KNOWN_FACES_DIR, filename)
            try:
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(name)
                else:
                    print(f"Warning: No face found in {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")


def mark_attendance(name):
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    time_string = now.strftime('%H:%M:%S')

    if not os.path.isfile(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['Name', 'Date', 'Time'])
        df.to_csv(ATTENDANCE_FILE, index=False)

    try:
        df = pd.read_csv(ATTENDANCE_FILE)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=['Name', 'Date', 'Time'])

    if not ((df['Name'] == name) & (df['Date'] == date_string)).any():
        new_entry = pd.DataFrame([[name, date_string, time_string]],
                                 columns=['Name', 'Date', 'Time'])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
        print(f"Attendance marked for {name} at {time_string}")


def speak_message(message):
    try:
        engine.say(message)
        engine.runAndWait()
    except RuntimeError as e:
        print(f"Audio error: {e}")


def run_face_recognition():

    load_known_faces()
    if not known_face_encodings:
        print("No known faces loaded. Exiting.")
        return


    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("Error: Could not open webcam.")
        return

    last_recognized_name = None
    last_speech_time = datetime.now()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Error: Failed to capture frame from webcam.")
            break


        if frame is not None:

            frame = cv2.convertScaleAbs(frame)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Proper BGR to RGB conversion

            try:
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=1)
            except Exception as e:
                print(f"Error in face recognition: {e}")
                continue

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    mark_attendance(name)


                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


                current_time = datetime.now()
                if (last_recognized_name != name or
                        (current_time - last_speech_time).total_seconds() > 5):
                    if name != "Unknown":
                        speak_message(f"Welcome {name}")
                    else:
                        speak_message("Access Denied")
                    last_recognized_name = name
                    last_speech_time = current_time

            cv2.imshow('Employee Attendance System', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("Starting Attendance System with Audio Feedback...")
    print("Press 'q' to quit")
    run_face_recognition()