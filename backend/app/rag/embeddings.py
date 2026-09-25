from openai import OpenAI

from app.core.config import settings


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


def create_embeddings(
    texts: list[str]
) -> list[list[float]]:

    if not texts:
        return []

    response = client.embeddings.create(
        model=(
            settings.OPENAI_EMBEDDING_MODEL
        ),
        input=texts,
    )

    return [
        item.embedding
        for item in response.data
    ]


def create_embedding(
    text: str
) -> list[float]:

    return create_embeddings(
        [text]
    )[0]