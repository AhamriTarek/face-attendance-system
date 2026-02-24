import os
import cv2
import numpy as np
import face_recognition
from threading import Lock
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

KNOWN_DIR = "known_faces"
TOLERANCE = 0.50
FRAME_RESIZE = 0.25  # speed

os.makedirs(KNOWN_DIR, exist_ok=True)

known_encodings = []
known_names = []

# Seen students (at least once)
seen_names = set()
seen_lock = Lock()


def reload_known_faces():
    global known_encodings, known_names
    known_encodings = []
    known_names = []

    for file in os.listdir(KNOWN_DIR):
        if not file.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        path = os.path.join(KNOWN_DIR, file)
        name = os.path.splitext(file)[0]

        img = face_recognition.load_image_file(path)
        enc = face_recognition.face_encodings(img)

        # keep only valid faces
        if enc:
            known_encodings.append(enc[0])
            known_names.append(name)


reload_known_faces()


@app.route("/")
def index():
    # show known people on UI
    return render_template("index.html", people=sorted(set(known_names)))


@app.route("/add_person", methods=["POST"])
def add_person():
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Name is required"}), 400

    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("_", "-")).strip()
    if not safe_name:
        return jsonify({"ok": False, "error": "Invalid name"}), 400

    if "image" not in request.files:
        return jsonify({"ok": False, "error": "Image is required"}), 400

    f = request.files["image"]
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg"]:
        ext = ".jpg"

    out_path = os.path.join(KNOWN_DIR, safe_name + ext)
    f.save(out_path)

    # validate face exists
    img = face_recognition.load_image_file(out_path)
    encs = face_recognition.face_encodings(img)
    if not encs:
        os.remove(out_path)
        return jsonify({"ok": False, "error": "No face detected in this image"}), 400

    reload_known_faces()
    return jsonify({"ok": True, "message": f"Added {safe_name}", "people": sorted(set(known_names))})


def gen_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        return

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # speed up
        small = cv2.resize(frame, (0, 0), fx=FRAME_RESIZE, fy=FRAME_RESIZE)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"

            if known_encodings:
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                best = int(np.argmin(distances))
                if distances[best] <= TOLERANCE:
                    name = known_names[best]

            # mark as seen if known
            if name != "Unknown":
                with seen_lock:
                    seen_names.add(name)

            # scale back to original frame size
            top = int(top / FRAME_RESIZE)
            right = int(right / FRAME_RESIZE)
            bottom = int(bottom / FRAME_RESIZE)
            left = int(left / FRAME_RESIZE)

            # draw rectangle + label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 30), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

    cap.release()


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/seen")
def seen():
    with seen_lock:
        return jsonify({"seen": sorted(list(seen_names))})


@app.route("/reset_seen", methods=["POST"])
def reset_seen():
    with seen_lock:
        seen_names.clear()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
