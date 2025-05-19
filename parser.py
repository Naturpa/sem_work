import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from config import NEWS_API_KEY
import re


class NewsParser:
    """Класс для парсинга новостей с РБК и работы с NewsAPI"""

    @staticmethod
    def parse_rbc_news() -> List[Dict]:
        """
        Парсит главные новости с rbc.ru
        Возвращает список из 5 последних новостей
        """
        url = "https://www.rbc.ru/"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Парсим главные новости (первые 5)
            for item in soup.select('.js-news-feed-list a.news-feed__item')[:5]:
                # Получаем заголовок и URL
                title = item.text.strip()
                url = item['href']

                # Парсим полный текст новости
                try:
                    article_response = requests.get(url, headers=headers, timeout=5)
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')

                    # Извлекаем текст статьи
                    article_text = ''
                    for p in article_soup.select('.article__text__overview, .article__text p'):
                        text = p.get_text(strip=True)
                        if text:
                            article_text += text + '\n\n'

                    # Очищаем текст от лишних пробелов
                    article_text = re.sub(r'\s+', ' ', article_text).strip()

                    # Извлекаем дату публикации
                    time_elem = article_soup.select_one('.article__header__date')
                    time = time_elem['content'] if time_elem and time_elem.has_attr('content') else ''

                    news_items.append({
                        'source': 'РБК',
                        'title': title,
                        'url': url,
                        'text': article_text[:500] + '...' if len(article_text) > 500 else article_text,
                        'time': time
                    })
                except Exception as e:
                    print(f"Ошибка при парсинге статьи {url}: {e}")
                    continue

            return news_items
        except Exception as e:
            print(f"Ошибка при парсинге РБК: {e}")
            return []

    # Остальные методы остаются без изменений
    @staticmethod
    def get_news_categories() -> List[str]:
        """Возвращает список доступных категорий новостей"""
        return ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']

    @staticmethod
    def get_news_by_category(category: str) -> List[Dict]:
        """Получает новости по категории через NewsAPI"""
        url = f"https://newsapi.org/v2/top-headlines?category={category}&apiKey={NEWS_API_KEY}&pageSize=3"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            return [{
                'source': article['source']['name'],
                'title': article['title'],
                'summary': article['description'] or '',
                'url': article['url']
            } for article in data.get('articles', [])]
        except Exception as e:
            print(f"NewsAPI error for {category}: {e}")
            return []

    @staticmethod
    def get_news_by_keyword(keyword: str) -> List[Dict]:
        """Поиск новостей по ключевому слову через NewsAPI"""
        url = f"https://newsapi.org/v2/everything?q={keyword}&apiKey={NEWS_API_KEY}&pageSize=3"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            return [{
                'source': article['source']['name'],
                'title': article['title'],
                'summary': article['description'] or '',
                'url': article['url']
            } for article in data.get('articles', [])]
        except Exception as e:
            print(f"NewsAPI search error for '{keyword}': {e}")
            return []