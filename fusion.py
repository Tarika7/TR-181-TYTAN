def fuse_emotions(face_emotion, behavior_emotion):
    # behavior has higher priority
    if behavior_emotion in ["Frustrated", "Confused"]:
        return behavior_emotion

    if face_emotion in ["Frustrated", "Bored"]:
        return face_emotion

    return "Engaged"


def tutor_score(face_emotion, final_emotion):
    # simple alignment score
    if face_emotion == final_emotion:
        return 1.0
    elif face_emotion in ["Confused", "Frustrated"] and final_emotion == "Engaged":
        return 0.3
    else:
        return 0.7
