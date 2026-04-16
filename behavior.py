import time

# store session data (simple for hackathon)
last_question_time = time.time()

def evaluate_answer(user_answer, correct_answer):
    global last_question_time

    current_time = time.time()
    time_taken = current_time - last_question_time
    last_question_time = current_time

    # simple correctness
    is_correct = str(user_answer).strip() == str(correct_answer).strip()

    # behavior logic
    if not is_correct and time_taken > 5:
        return "Confused"
    elif not is_correct and time_taken < 3:
        return "Frustrated"
    elif is_correct and time_taken < 3:
        return "Bored"
    else:
        return "Engaged"
