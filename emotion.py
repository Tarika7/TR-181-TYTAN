import mediapipe as mp
import cv2

mp_face = mp.solutions.face_mesh

face_mesh = mp_face.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
)

def get_emotion(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return "No Face"

    landmarks = results.multi_face_landmarks[0].landmark

    # Key landmarks
    left_mouth = landmarks[61]
    right_mouth = landmarks[291]
    upper_lip = landmarks[13]
    lower_lip = landmarks[14]
    brow = landmarks[70]
    eye = landmarks[159]

    # Basic geometry
    mouth_open = abs(upper_lip.y - lower_lip.y)
    mouth_width = abs(left_mouth.x - right_mouth.x)
    eye_open = eye.y
    brow_height = brow.y

    # Simple rules
    if mouth_open < 0.01 and brow_height < 0.3:
        return "Frustrated"
    elif eye_open < 0.2:
        return "Bored"
    elif mouth_width > 0.1:
        return "Engaged"
    else:
        return "Confused"