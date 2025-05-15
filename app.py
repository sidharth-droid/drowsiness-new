from flask import Flask, render_template, Response, jsonify, request
import cv2
import dlib
import numpy as np
from scipy.spatial import distance
from imutils import face_utils
import imutils
import threading
import base64
status_lock = threading.Lock()
drowsy_status = "awake"


app = Flask(__name__)
cap = cv2.VideoCapture(0)

# Load dlib models
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("models/my_model.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["mouth"]

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(mouth):
    A = distance.euclidean(mouth[2], mouth[10])
    B = distance.euclidean(mouth[4], mouth[8])
    C = distance.euclidean(mouth[0], mouth[6])
    return (A + B) / (2.0 * C)

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    EAR_THRESHOLD = 0.25
    MAR_THRESHOLD = 0.6
    CONSEC_FRAMES = 20
    ear_counter = 0
    mar_counter = 0
    
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = imutils.resize(frame, width=640)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)

        global drowsy_status
        status = "awake"

        for rect in rects:
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            mouth = shape[mStart:mEnd]

            ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0
            mar = mouth_aspect_ratio(mouth)

            if ear < EAR_THRESHOLD:
                ear_counter += 1
            else:
                ear_counter = 0

            if mar > MAR_THRESHOLD:
                mar_counter += 1
            else:
                mar_counter = 0

            if ear_counter >= CONSEC_FRAMES or mar_counter >= CONSEC_FRAMES:
                status = "drowsy"
        with status_lock:
            drowsy_status = status


            cv2.putText(frame, f"Status: {status}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 0, 255) if status == "drowsy" else (0, 255, 0), 2)

        cv2.putText(frame, f"@ALERT:{status}", (5, 470), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 1)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @app.route('/video')
# def video():
#     return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detect', methods=['POST'])
def detect():
    if 'frame' not in request.files:
        return jsonify({'error': 'No frame uploaded'}), 400

    file = request.files['frame']
    npimg = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({'error': 'Invalid image'}), 400

    # Run detection logic on the frame (similar to your gen_frames() body)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)

    status = "awake"
    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        mouth = shape[mStart:mEnd]

        ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0
        mar = mouth_aspect_ratio(mouth)

        if ear < 0.25 or mar > 0.6:
            status = "drowsy"
            break

    with status_lock:
        global drowsy_status
        drowsy_status = status

    return jsonify({"status": status})


@app.route("/status")
def status():
    with status_lock:
        return jsonify({"status": drowsy_status})

@app.route("/stop", methods=["POST"])
def stop_camera():
    global cap
    cap.release()
    return jsonify({"message": "Camera stopped"})


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)

