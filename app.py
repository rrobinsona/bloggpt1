import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests

app = FastAPI()

# Получаем API ключи из переменных окружения
openai.api_key = os.environ.get("OPENAI_API_KEY")
newsapi_key = os.environ.get("NEWSAPI_KEY")

if not openai.api_key:
    raise ValueError("Переменная окружения OPENAI_API_KEY не установлена")
if not newsapi_key:
    raise ValueError("Переменная окружения NEWSAPI_KEY не установлена")


class Topic(BaseModel):
    topic: str


def get_recent_news(topic):
    """Получает последние новости по теме из NewsAPI."""
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={newsapi_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка при получении данных из NewsAPI")
    articles = response.json().get("articles", [])
    if not articles:
        return "Свежих новостей не найдено."
    recent_news = [article["title"] for article in articles[:1]]
    return "\n".join(recent_news)


def generate_post(topic):
    """Генерирует пост с использованием OpenAI и последних новостей."""
    recent_news = get_recent_news(topic)

    # Генерация заголовка
    prompt_title = f"Придумайте привлекательный заголовок для поста на тему: {topic}"
    try:
        response_title = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_title}],
            max_tokens=50,
            n=1,
            temperature=0.7,
        )
        title = response_title.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации заголовка: {str(e)}")

    # Генерация мета-описания
    prompt_meta = f"Напишите краткое, но информативное мета-описание для поста с заголовком: {title}"
    try:
        response_meta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_meta}],
            max_tokens=100,
            n=1,
            temperature=0.7,
        )
        meta_description = response_meta.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации мета-описания: {str(e)}")

    # Генерация контента поста
    prompt_post = (
        f"Напишите подробный и увлекательный пост для блога на тему: {topic}, учитывая следующие последние новости:\n"
        f"{recent_news}\n\n"
        "Используйте короткие абзацы, подзаголовки, примеры и ключевые слова для лучшего восприятия и SEO-оптимизации."
    )
    try:
        response_post = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_post}],
            max_tokens=1000,
            n=1,
            temperature=0.7,
        )
        post_content = response_post.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента поста: {str(e)}")

    return {
        "title": title,
        "meta_description": meta_description,
        "post_content": post_content
    }


@app.get("/")
async def root():
    """GET-запрос на корневой путь."""
    return {"message": "Сервер работает! Используйте POST-запросы для обработки данных."}


@app.post("/")
async def handle_post_request(topic: Topic):
    """
    Обрабатывает POST-запросы на корневом пути `/`.
    Позволяет использовать корневой путь для генерации постов.
    """
    generated_post = generate_post(topic.topic)
    return generated_post


@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    """
    Отдельный путь для генерации постов.
    Может использоваться, если нужно разделить обработку.
    """
    generated_post = generate_post(topic.topic)
    return generated_post


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
