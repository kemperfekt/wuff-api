import os
import weaviate
from weaviate.classes.init import Auth

weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_APIKEY")

def get_weaviate_client():
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
        headers={
            "X-Openai-Api-Key": openai_api_key
        }
    )
