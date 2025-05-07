import enum

class SessionState(enum.Enum):
    WAITING_FOR_DOG_QUESTION = "waiting_for_dog_question"
    WAITING_FOR_DOG_RAG = "waiting_for_dog_rag"
    WAITING_FOR_DOG_TRANSITION = "waiting_for_dog_transition"
    WAITING_FOR_COACH_INTRO = "waiting_for_coach_intro"
    WAITING_FOR_COACH_GOAL = "waiting_for_coach_goal"
    WAITING_FOR_COACH_QUESTION = "waiting_for_coach_question"
    WAITING_FOR_COACH_RAG = "waiting_for_coach_rag"
    WAITING_FOR_COACH_TRAINING_QUESTION = "waiting_for_coach_training_question"
    WAITING_FOR_COACH_TRAINING = "waiting_for_coach_training"
    ENDED = "ended"

    def next(state: "SessionState") -> "SessionState":
        order = [
            SessionState.WAITING_FOR_DOG_QUESTION,
            SessionState.WAITING_FOR_DOG_RAG,
            SessionState.WAITING_FOR_DOG_TRANSITION,
            SessionState.WAITING_FOR_COACH_INTRO,
            SessionState.WAITING_FOR_COACH_GOAL,
            SessionState.WAITING_FOR_COACH_QUESTION,
            SessionState.WAITING_FOR_COACH_RAG,
            SessionState.WAITING_FOR_COACH_TRAINING_QUESTION,
            SessionState.WAITING_FOR_COACH_TRAINING,
        ]
        try:
            idx = order.index(state)
            return order[idx + 1]
        except (ValueError, IndexError):
            return SessionState.WAITING_FOR_DOG_QUESTION