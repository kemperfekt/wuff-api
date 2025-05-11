from src.models.flow_models import AgentMessage

def safe_message(sender: str, text: str) -> AgentMessage:
    return AgentMessage(role=sender, content=text)
