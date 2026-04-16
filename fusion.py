def fuse_emotions(face_emotion, behavior_emotion):
    # simple priority logic
    if behavior_emotion in ["Frustrated", "Confused"]:
        return behavior_emotion
    
    if face_emotion in ["Frustrated", "Bored"]:
        return face_emotion

    return "Engaged"
