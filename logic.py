def get_next_question(emotion):
    if emotion == "Frustrated":
        return "Simplifying explanation", "Easy: What is 2 + 2?"
    elif emotion == "Bored":
        return "Increasing difficulty", "Hard: Solve 12x + 5 = 29"
    elif emotion == "Confused":
        return "Giving hint", "Hint: Try breaking the problem step by step"
    elif emotion == "No Face":
        return "Waiting for user", "Please look at the screen"
    else:
        return "Normal flow", "Medium: What is 5 + 7?"
        # store current answer
current_answer = "12"  # default

def get_next_question(emotion):
    global current_answer

    if emotion == "Frustrated":
        current_answer = "4"
        return "Simplifying explanation", "Easy: What is 2 + 2?"
    
    elif emotion == "Bored":
        current_answer = "2"
        return "Increasing difficulty", "Hard: Solve 12x + 5 = 29 (x=?)"
    
    elif emotion == "Confused":
        current_answer = "12"
        return "Giving hint", "Hint: What is 5 + 7?"
    
    elif emotion == "No Face":
        return "Waiting for user", "Please look at the screen"
    
    else:
        current_answer = "12"
        return "Normal flow", "Medium: What is 5 + 7?"

def get_current_answer():
    return current_answer
