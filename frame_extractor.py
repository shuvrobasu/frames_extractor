#######################################################################################################################
# Extract frames from a video given start and end time in hh:mm:ss
# Frames are extracted 1 for each second so 30 seconds between start & end time would extract 30 frames max if user
# inputs value higher than permissible.
# images are saves as frame_xxxx.jpg where xxxx is the frame # starting from 0
# Developed by Shuvro Basu, 2023 (c)
# Released under MIT
########################################################################################################################

import cv2
import PySimpleGUI as sg
import os
import re
import datetime

# Global variables
video_path = ""
start_time_ms = 113000  # Default start time: 0:1:53 (in milliseconds)
end_time_ms = 143000  # Default end time: 0:2:23 (in milliseconds)
output_folder = ""
video_length_ms = 0
num_frames_to_extract = 10

def get_duration(filename):
    video = cv2.VideoCapture(filename)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    video.release()

    if fps == 0:
        raise ValueError("Invalid video file. Unable to get FPS information.")
    
    seconds = frame_count / fps
    return int(seconds * 1000)


def milliseconds_to_time(milliseconds):
    total_seconds = milliseconds // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def time_to_milliseconds(time_str):
    time_parts = re.split(r':', time_str)
    if len(time_parts) != 3:
        raise ValueError("Invalid time format. Please use hh:mm:ss format.")
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = int(time_parts[2])
    total_seconds = hours * 3600 + minutes * 60 + seconds
    milliseconds = total_seconds * 1000
    return milliseconds

def play_video(filename):
    cap = cv2.VideoCapture(filename)
    cv2.namedWindow("Video Player", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Video Player", 640, 480)

    while cap.isOpened():
        ret, frame = cap.read()

        if ret:
            cv2.imshow("Video Player", frame)
        else:
            break

        quit_button = cv2.waitKey(25) & 0xFF == ord('q')
        close_button = cv2.getWindowProperty('Video Player', cv2.WND_PROP_VISIBLE) < 1
        if quit_button or close_button:
            break

    cap.release()
    cv2.destroyAllWindows()

def extract_frames(filename):
    global num_frames_to_extract

    cap = cv2.VideoCapture(filename)
    cap.set(cv2.CAP_PROP_POS_MSEC, start_time_ms)

    total_frames = int((end_time_ms - start_time_ms) // 1000)
    num_frames_to_extract = min(num_frames_to_extract, total_frames)

    if num_frames_to_extract == 0:
        sg.popup("Start or end time exceeds video length!", title="Error")
        return

    frame_interval = max((end_time_ms - start_time_ms) // (num_frames_to_extract * 1000), 1)

    sg.OneLineProgressMeter('Progress', 0, num_frames_to_extract, 'extract_frames', orientation='h')

    frame_count = 0

    while cap.isOpened() and frame_count < num_frames_to_extract:
        ret, frame = cap.read()

        if ret:
            if cap.get(cv2.CAP_PROP_POS_MSEC) % frame_interval == 0:
                cv2.imwrite(f"{output_folder}/frame_{frame_count}.jpg", frame)
                frame_count += 1
                sg.OneLineProgressMeter('Progress', frame_count, num_frames_to_extract, 'extract_frames', orientation='h')
        else:
            break

        if cap.get(cv2.CAP_PROP_POS_MSEC) >= end_time_ms:
            break

    cap.release()
    cv2.destroyAllWindows()
    sg.OneLineProgressMeter('Progress', num_frames_to_extract, num_frames_to_extract, 'extract_frames', "Extraction Complete")
    sg.popup(f"Frames extracted successfully!\nTotal frames: {frame_count}", title="Extraction Complete")

def main():
    global video_path, output_folder, video_length_ms, num_frames_to_extract

    sg.theme("LightGrey1")

    layout = [
        [sg.Text("Frame Extractor", font=("Helvetica", 16))],
        [sg.Text("Select Video File:"), sg.InputText(key="-VIDEO-", default_text="../videoplayback.mp4"), sg.FileBrowse()],
        [sg.Text("Video Duration: "), sg.Text("", key="-VIDEODURATION-", size=(15, 1))],
        [sg.Text("Start Time (hh:mm:ss):"), sg.InputText(key="-STARTTIME-", default_text="0:1:53")],
        [sg.Text("End Time (hh:mm:ss):"), sg.InputText(key="-ENDTIME-", default_text="0:2:23")],
        [sg.Text("Output Folder:"), sg.InputText(key="-OUTPUTFOLDER-", default_text="."), sg.FolderBrowse()],
        [sg.Text("Number of Frames to Extract:"), sg.InputText(key="-NUMFRAMES-", default_text="10")],
        [sg.Button("Play Video"), sg.Button("Extract Frames"), sg.Button("Exit")]
    ]

    window = sg.Window("Frame Extractor", layout)

    while True:
        event, values = window.read()

        if event == "Exit" or event == sg.WINDOW_CLOSED:
            break

        if event == "-VIDEO-":
            video_path = values["-VIDEO-"]
            video_length_ms = get_duration(video_path)
            window["-VIDEODURATION-"].update(f"{datetime.timedelta(seconds=video_length_ms//1000)}")

        if event == "Play Video":
            video_path = values["-VIDEO-"]
            play_video(video_path)

        if event == "Extract Frames":
            video_path = values["-VIDEO-"]
            start_time_str = values["-STARTTIME-"]
            end_time_str = values["-ENDTIME-"]
            output_folder = values["-OUTPUTFOLDER-"]
            num_frames_to_extract = int(values["-NUMFRAMES-"])

            try:
                start_time_ms = time_to_milliseconds(start_time_str)
                end_time_ms = time_to_milliseconds(end_time_str)
                video_length_ms = get_duration(video_path)

                # if start_time_ms >= video_length_ms:
                #     start_time_ms = 0
                #     if end_time_ms > video_length_ms:
                #         end_time_ms = milliseconds_to_time(get_duration(video_path))
                #         print(start_time_str)
                #         print(end_time_ms)
                if start_time_ms >= video_length_ms or end_time_ms > video_length_ms:
                        sg.popup("Start or end time exceeds video length!", title="Error")
                        continue

                extract_frames(video_path)
            except ValueError as e:
                sg.popup(str(e), title="Error")

    window.close()

if __name__ == "__main__":
    main()
