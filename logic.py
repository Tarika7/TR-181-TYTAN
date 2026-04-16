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