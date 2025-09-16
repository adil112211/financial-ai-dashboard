# 🏦 Financial AI Dashboard - Главный модуль с пользовательскими RSS каналами

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, JSON, Integer, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, HttpUrl
import jwt
import uuid
import os
import httpx
import asyncio
import json
import logging
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import threading
import time
import random
from jinja2 import Template
import xml.etree.ElementTree as ET
import feedparser
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
SECRET_KEY = os.getenv("SECRET_KEY", "financial-ai-super-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finai_user:finai_password@localhost/finai_db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Настройки API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NBK_API_URL = "https://www.nationalbank.kz/rss/get_rates.cfm"  # НБ РК API
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Инициализация OpenAI
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None
    logger.warning("OpenAI API key not configured")

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# FastAPI приложение
app = FastAPI(
    title="Financial AI Dashboard - Enhanced with Custom RSS",
    description="AI-powered Corporate Liquidity Management with Custom RSS Feeds",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS для мобильной поддержки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статичные файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Создание директорий
Path("logs").mkdir(exist_ok=True)
Path("static/reports").mkdir(exist_ok=True, parents=True)
Path("static/uploads").mkdir(exist_ok=True, parents=True)

# =============================================================================
# Модели базы данных
# =============================================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    company = Column(String)
    phone = Column(String)
    subscription_plan = Column(String, default="professional")
    is_active = Column(Boolean, default=True)
    timezone = Column(String, default="Asia/Almaty")
    language = Column(String, default="ru")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    bank = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="KZT")
    account_type = Column(String, default="operational")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency = Column(String, nullable=False)
    to_currency = Column(String, nullable=False)
    rate = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    source = Column(String, default="NBK")
    created_at = Column(DateTime, default=datetime.utcnow)

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String)
    published_at = Column(DateTime)
    source = Column(String)
    category = Column(String, default="financial")
    sentiment = Column(String)  # positive, negative, neutral
    risk_level = Column(String)  # low, medium, high
    relevance_score = Column(Float, default=0.5)  # AI оценка релевантности
    ai_tags = Column(JSON)  # AI теги для категоризации
    created_at = Column(DateTime, default=datetime.utcnow)

# НОВАЯ МОДЕЛЬ: Пользовательские RSS каналы
class UserRSSFeed(Base):
    __tablename__ = "user_rss_feeds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)  # Название канала
    url = Column(String, nullable=False)   # RSS URL
    description = Column(Text)             # Описание канала
    category = Column(String, default="financial")  # Категория
    priority = Column(Integer, default=1)  # Приоритет (1-5)
    is_active = Column(Boolean, default=True)
    auto_analysis = Column(Boolean, default=True)  # Автоматический AI анализ
    keywords = Column(JSON)  # Ключевые слова для фильтрации
    last_fetched = Column(DateTime)
    fetch_frequency = Column(String, default="hourly")  # hourly, daily, weekly
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    articles_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# НОВАЯ МОДЕЛЬ: Анализ RSS контента
class RSSContentAnalysis(Base):
    __tablename__ = "rss_content_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    rss_feed_id = Column(UUID(as_uuid=True), nullable=False)
    article_id = Column(UUID(as_uuid=True))  # Связь с news_articles
    analysis_date = Column(DateTime, default=datetime.utcnow)
    
    # AI анализ контента
    financial_relevance = Column(Float)  # 0-1 релевантность для финансов
    risk_indicators = Column(JSON)       # Индикаторы рисков
    sentiment_score = Column(Float)      # -1 to 1 (негативный - позитивный)
    key_topics = Column(JSON)           # Основные темы
    market_impact = Column(String)      # low, medium, high
    recommendations = Column(Text)      # AI рекомендации
    
    # Метаданные анализа
    processing_time_ms = Column(Integer)
    ai_confidence = Column(Float)       # Уверенность AI в анализе
    created_at = Column(DateTime, default=datetime.utcnow)

class AIConsultation(Base):
    __tablename__ = "ai_consultations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_data = Column(JSON)
    rss_sources_used = Column(JSON)  # НОВОЕ: RSS источники использованные в ответе
    session_id = Column(String)
    source = Column(String, default="web")  # web, n8n, telegram
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)
    content = Column(Text)
    file_path = Column(String)
    rss_feeds_included = Column(JSON)  # НОВОЕ: RSS каналы включенные в отчет
    generated_at = Column(DateTime, default=datetime.utcnow)
    
class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False)  # n8n, telegram, etc
    event_type = Column(String)
    payload = Column(JSON)
    response = Column(JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# =============================================================================
# Pydantic модели
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AIQuestionRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = {}
    source: Optional[str] = "web"
    include_rss: Optional[bool] = True  # НОВОЕ: включать RSS в анализ

class N8NWebhookPayload(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    webhook_url: Optional[str] = None

# НОВЫЕ МОДЕЛИ для RSS
class RSSFeedCreate(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = ""
    category: Optional[str] = "financial"
    priority: Optional[int] = 1
    auto_analysis: Optional[bool] = True
    keywords: Optional[List[str]] = []
    fetch_frequency: Optional[str] = "hourly"

class RSSFeedUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    auto_analysis: Optional[bool] = None
    keywords: Optional[List[str]] = None
    fetch_frequency: Optional[str] = None
    is_active: Optional[bool] = None

class RSSFeedResponse(BaseModel):
    id: str
    name: str
    url: str
    description: str
    category: str
    priority: int
    is_active: bool
    auto_analysis: bool
    keywords: List[str]
    last_fetched: Optional[datetime]
    fetch_frequency: str
    error_count: int
    articles_count: int
    created_at: datetime

# =============================================================================
# Утилиты
# =============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def validate_rss_url(url: str) -> bool:
    """Валидация RSS URL"""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Проверяем доступность RSS
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False

# =============================================================================
# Сервисы интеграции (обновленные)
# =============================================================================

class NBKExchangeRateService:
    """Сервис для получения курсов валют из НБ РК"""
    
    @staticmethod
    async def fetch_exchange_rates():
        """Получение курсов валют из НБ РК"""
        try:
            logger.info("Fetching exchange rates from NBK...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(NBK_API_URL)
                response.raise_for_status()
                
            # Парсинг XML ответа от НБ РК
            root = ET.fromstring(response.content)
            rates = []
            
            # НБ РК предоставляет данные в формате XML
            for item in root.findall('.//item'):
                try:
                    title = item.find('title').text if item.find('title') is not None else ""
                    description = item.find('description').text if item.find('description') is not None else ""
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    
                    # Извлечение курса из описания
                    if "USD" in title:
                        rate_text = description.split()[-1]
                        rate = float(rate_text.replace(',', '.'))
                        rates.append({
                            'from_currency': 'USD',
                            'to_currency': 'KZT',
                            'rate': rate,
                            'date': datetime.now(timezone.utc),
                            'source': 'NBK'
                        })
                    elif "EUR" in title:
                        rate_text = description.split()[-1]
                        rate = float(rate_text.replace(',', '.'))
                        rates.append({
                            'from_currency': 'EUR',
                            'to_currency': 'KZT',
                            'rate': rate,
                            'date': datetime.now(timezone.utc),
                            'source': 'NBK'
                        })
                    elif "RUB" in title:
                        rate_text = description.split()[-1]
                        rate = float(rate_text.replace(',', '.'))
                        rates.append({
                            'from_currency': 'RUB',
                            'to_currency': 'KZT',
                            'rate': rate,
                            'date': datetime.now(timezone.utc),
                            'source': 'NBK'
                        })
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Error parsing rate item: {e}")
                    continue
            
            # Если не получилось парсить XML, используем fallback API или статичные данные
            if not rates:
                logger.warning("Failed to parse NBK XML, using fallback rates")
                rates = [
                    {'from_currency': 'USD', 'to_currency': 'KZT', 'rate': 480.5, 'date': datetime.now(timezone.utc), 'source': 'NBK_FALLBACK'},
                    {'from_currency': 'EUR', 'to_currency': 'KZT', 'rate': 520.3, 'date': datetime.now(timezone.utc), 'source': 'NBK_FALLBACK'},
                    {'from_currency': 'RUB', 'to_currency': 'KZT', 'rate': 5.2, 'date': datetime.now(timezone.utc), 'source': 'NBK_FALLBACK'},
                ]
            
            logger.info(f"Fetched {len(rates)} exchange rates from NBK")
            return rates
            
        except Exception as e:
            logger.error(f"Error fetching NBK exchange rates: {e}")
            # Возвращаем последние известные курсы или статичные
            return [
                {'from_currency': 'USD', 'to_currency': 'KZT', 'rate': 480.5, 'date': datetime.now(timezone.utc), 'source': 'FALLBACK'},
                {'from_currency': 'EUR', 'to_currency': 'KZT', 'rate': 520.3, 'date': datetime.now(timezone.utc), 'source': 'FALLBACK'},
                {'from_currency': 'RUB', 'to_currency': 'KZT', 'rate': 5.2, 'date': datetime.now(timezone.utc), 'source': 'FALLBACK'},
            ]

class EnhancedNewsService:
    """Обновленный сервис для получения и анализа новостей с пользовательскими RSS"""
    
    @staticmethod
    async def fetch_default_news():
        """Получение новостей из базовых источников"""
        try:
            logger.info("Fetching default financial news...")
            
            default_sources = [
                {
                    'url': 'https://feedpress.me/tengrinews-economy',
                    'source': 'Tengrinews',
                    'category': 'economy'
                },
                {
                    'url': 'https://forbes.kz/rss/',
                    'source': 'Forbes Kazakhstan',
                    'category': 'financial'
                },
                {
                    'url': 'https://kursiv.kz/feed/',
                    'source': 'Kursiv',
                    'category': 'business'
                }
            ]
            
            all_articles = []
            
            # Получение новостей из RSS лент
            for source in default_sources:
                try:
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        response = await client.get(source['url'])
                        response.raise_for_status()
                    
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries[:5]:  # Берем последние 5 новостей из каждого источника
                        article = {
                            'title': entry.get('title', ''),
                            'content': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'published_at': datetime.now(timezone.utc),
                            'source': source['source'],
                            'category': source['category']
                        }
                        all_articles.append(article)
                        
                except Exception as e:
                    logger.warning(f"Error fetching from {source['source']}: {e}")
                    continue
            
            logger.info(f"Fetched {len(all_articles)} default news articles")
            return all_articles
            
        except Exception as e:
            logger.error(f"Error fetching default news: {e}")
            return []

    @staticmethod
    async def fetch_user_rss_feeds(user_id: str, db: Session):
        """Получение новостей из пользовательских RSS каналов"""
        try:
            logger.info(f"Fetching user RSS feeds for user {user_id}")
            
            # Получаем активные RSS каналы пользователя
            user_feeds = db.query(UserRSSFeed).filter(
                UserRSSFeed.user_id == user_id,
                UserRSSFeed.is_active == True
            ).all()
            
            if not user_feeds:
                logger.info(f"No active RSS feeds for user {user_id}")
                return []
            
            all_articles = []
            
            for feed in user_feeds:
                try:
                    logger.info(f"Processing RSS feed: {feed.name} - {feed.url}")
                    
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        response = await client.get(str(feed.url))
                        response.raise_for_status()
                    
                    parsed_feed = feedparser.parse(response.content)
                    
                    # Определяем количество статей в зависимости от приоритета
                    max_articles = min(feed.priority * 3, 15)  # 3-15 статей
                    
                    for entry in parsed_feed.entries[:max_articles]:
                        article = {
                            'title': entry.get('title', ''),
                            'content': entry.get('summary', '') or entry.get('description', ''),
                            'url': entry.get('link', ''),
                            'published_at': datetime.now(timezone.utc),
                            'source': feed.name,
                            'category': feed.category,
                            'rss_feed_id': str(feed.id),
                            'user_id': user_id
                        }
                        
                        # Фильтрация по ключевым словам
                        if feed.keywords:
                            title_lower = article['title'].lower()
                            content_lower = article['content'].lower()
                            
                            if any(keyword.lower() in title_lower or keyword.lower() in content_lower 
                                   for keyword in feed.keywords):
                                article['relevance_score'] = 0.8  # Высокая релевантность
                                all_articles.append(article)
                            elif feed.priority >= 4:  # Высокий приоритет - берем все статьи
                                article['relevance_score'] = 0.6
                                all_articles.append(article)
                        else:
                            article['relevance_score'] = 0.7
                            all_articles.append(article)
                    
                    # Обновляем статистику канала
                    feed.last_fetched = datetime.utcnow()
                    feed.error_count = 0
                    feed.articles_count += len(parsed_feed.entries[:max_articles])
                    feed.last_error = None
                    
                except Exception as e:
                    logger.error(f"Error fetching RSS feed {feed.name}: {e}")
                    feed.error_count += 1
                    feed.last_error = str(e)
                    continue
            
            db.commit()
            logger.info(f"Fetched {len(all_articles)} articles from user RSS feeds")
            return all_articles
            
        except Exception as e:
            logger.error(f"Error fetching user RSS feeds: {e}")
            return []

class EnhancedAIAnalysisService:
    """Обновленный AI сервис с поддержкой пользовательских RSS"""
    
    @staticmethod
    async def analyze_rss_content(article_data: Dict, rss_feed_id: str, user_id: str, db: Session):
        """AI анализ контента из RSS канала"""
        try:
            if not client:
                logger.warning("OpenAI client not available for RSS analysis")
                return None
            
            title = article_data.get('title', '')
            content = article_data.get('content', '')
            
            prompt = f"""
Проанализируй следующую новостную статью с точки зрения финансовых рисков и возможностей:

ЗАГОЛОВОК: {title}

СОДЕРЖАНИЕ: {content}

Предоставь анализ в формате JSON:
{{
    "financial_relevance": 0.0-1.0,  // релевантность для финансовых решений
    "risk_indicators": ["indicator1", "indicator2"],  // индикаторы рисков
    "sentiment_score": -1.0 to 1.0,  // негативный (-1) до позитивный (+1)
    "key_topics": ["topic1", "topic2"],  // основные темы
    "market_impact": "low|medium|high",  // влияние на рынок
    "recommendations": "краткие рекомендации",
    "ai_confidence": 0.0-1.0  // уверенность в анализе
}}

Отвечай только JSON, без дополнительного текста.
"""
            
            start_time = datetime.utcnow()
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты эксперт по финансовому анализу. Анализируешь новости на предмет финансовых рисков и возможностей. Отвечаешь только в формате JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            try:
                analysis_result = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI analysis JSON, using defaults")
                analysis_result = {
                    "financial_relevance": 0.5,
                    "risk_indicators": [],
                    "sentiment_score": 0.0,
                    "key_topics": [],
                    "market_impact": "low",
                    "recommendations": "Требуется дополнительный анализ",
                    "ai_confidence": 0.3
                }
            
            # Сохраняем анализ в базу данных
            analysis = RSSContentAnalysis(
                user_id=user_id,
                rss_feed_id=rss_feed_id,
                financial_relevance=analysis_result.get('financial_relevance', 0.5),
                risk_indicators=analysis_result.get('risk_indicators', []),
                sentiment_score=analysis_result.get('sentiment_score', 0.0),
                key_topics=analysis_result.get('key_topics', []),
                market_impact=analysis_result.get('market_impact', 'low'),
                recommendations=analysis_result.get('recommendations', ''),
                processing_time_ms=processing_time,
                ai_confidence=analysis_result.get('ai_confidence', 0.5)
            )
            
            db.add(analysis)
            db.commit()
            
            logger.info(f"AI analysis completed for RSS article: {title[:50]}...")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in RSS content analysis: {e}")
            return None

    @staticmethod
    async def analyze_financial_data_with_rss(exchange_rates: List[Dict], news_articles: List[Dict], 
                                            user_context: Optional[Dict] = None, user_id: Optional[str] = None, db: Optional[Session] = None):
        """Анализ финансовых данных с учетом пользовательских RSS"""
        try:
            if not client:
                logger.warning("OpenAI client not available, using mock analysis")
                return {
                    'summary': 'Текущая экономическая ситуация характеризуется умеренной стабильностью валютного курса.',
                    'risk_assessment': 'MEDIUM',
                    'recommendations': [
                        'Мониторить изменения курса доллара США',
                        'Диверсифицировать валютные позиции',
                        'Следить за решениями НБ РК по базовой ставке'
                    ],
                    'forecast': 'На ближайшие 30 дней прогнозируется сохранение текущих тенденций',
                    'rss_insights': []
                }
            
            # Подготовка контекста для AI
            rates_text = "\n".join([f"{r['from_currency']}/{r['to_currency']}: {r['rate']}" for r in exchange_rates[:5]])
            news_text = "\n".join([f"- {n['title']}: {n['content'][:200]}..." for n in news_articles[:10]])
            
            # Получение анализа пользовательских RSS (если доступно)
            rss_insights = []
            if user_id and db:
                try:
                    recent_rss_analysis = db.query(RSSContentAnalysis).filter(
                        RSSContentAnalysis.user_id == user_id,
                        RSSContentAnalysis.analysis_date >= datetime.utcnow() - timedelta(days=1)
                    ).order_by(RSSContentAnalysis.financial_relevance.desc()).limit(5).all()
                    
                    for analysis in recent_rss_analysis:
                        rss_insights.append({
                            'topics': analysis.key_topics,
                            'risk_indicators': analysis.risk_indicators,
                            'market_impact': analysis.market_impact,
                            'recommendations': analysis.recommendations,
                            'sentiment': analysis.sentiment_score,
                            'confidence': analysis.ai_confidence
                        })
                except Exception as e:
                    logger.warning(f"Failed to get RSS insights: {e}")
            
            rss_context = ""
            if rss_insights:
                rss_context = f"\n\nДОПОЛНИТЕЛЬНЫЕ ИНСАЙТЫ ИЗ ПОЛЬЗОВАТЕЛЬСКИХ RSS:\n"
                for i, insight in enumerate(rss_insights[:3], 1):
                    rss_context += f"{i}. Темы: {', '.join(insight['topics'][:3])}\n"
                    rss_context += f"   Риски: {', '.join(insight['risk_indicators'][:2])}\n"
                    rss_context += f"   Влияние: {insight['market_impact']}\n"
            
            prompt = f"""
Проанализируй текущую финансовую ситуацию в Казахстане на основе следующих данных:

КУРСЫ ВАЛЮТ (НБ РК):
{rates_text}

ФИНАНСОВЫЕ НОВОСТИ:
{news_text}

{rss_context}

КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:
{json.dumps(user_context) if user_context else 'Общий анализ'}

Предоставь анализ в формате JSON:
{{
    "summary": "краткое резюме текущей ситуации (до 200 символов)",
    "risk_assessment": "LOW|MEDIUM|HIGH",
    "recommendations": ["рекомендация1", "рекомендация2", "рекомендация3"],
    "forecast": "прогноз на ближайшие 30 дней",
    "rss_insights": ["инсайт1", "инсайт2"],
    "market_factors": ["фактор1", "фактор2"]
}}

Отвечай на русском языке, учитывая специфику казахстанского рынка.
"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты профессиональный финансовый аналитик, специализирующийся на казахстанском рынке. Анализируешь данные из различных источников, включая пользовательские RSS каналы."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Попытка парсинга JSON ответа
            try:
                analysis = json.loads(ai_response)
            except json.JSONDecodeError:
                # Если AI не вернул JSON, создаем структуру из текста
                analysis = {
                    'summary': ai_response[:200],
                    'risk_assessment': 'MEDIUM',
                    'recommendations': ai_response.split('\n')[-3:],
                    'forecast': 'Требуется дополнительный анализ',
                    'rss_insights': [f"Анализировано {len(rss_insights)} RSS источников"] if rss_insights else [],
                    'market_factors': []
                }
            
            logger.info("Enhanced AI analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in enhanced AI analysis: {e}")
            return {
                'summary': 'Ошибка при получении AI анализа. Используются базовые рекомендации.',
                'risk_assessment': 'MEDIUM',
                'recommendations': [
                    'Продолжить мониторинг валютных курсов',
                    'Диверсифицировать риски',
                    'Консультироваться с финансовыми консультантами'
                ],
                'forecast': 'Анализ временно недоступен',
                'rss_insights': [],
                'market_factors': []
            }

    @staticmethod
    async def answer_question_with_rss(question: str, context: Optional[Dict] = None, user_id: Optional[str] = None, db: Optional[Session] = None):
        """Ответ на вопрос пользователя с учетом RSS данных"""
        try:
            if not client:
                return f"Извините, AI консультант временно недоступен. Ваш вопрос: '{question}' был сохранен для обработки."
            
            # Получение актуальных данных для контекста
            if not db:
                db = SessionLocal()
            
            try:
                # Последние курсы валют
                latest_rates = db.query(ExchangeRate).filter(
                    ExchangeRate.date >= datetime.now() - timedelta(days=1)
                ).all()
                
                # Последние новости
                latest_news = db.query(NewsArticle).filter(
                    NewsArticle.created_at >= datetime.now() - timedelta(days=1)
                ).limit(5).all()
                
                # RSS анализ пользователя
                rss_context = ""
                if user_id:
                    recent_rss = db.query(RSSContentAnalysis).filter(
                        RSSContentAnalysis.user_id == user_id,
                        RSSContentAnalysis.analysis_date >= datetime.now() - timedelta(days=2)
                    ).order_by(RSSContentAnalysis.financial_relevance.desc()).limit(3).all()
                    
                    if recent_rss:
                        rss_context = "\n\nДанные из ваших RSS каналов:\n"
                        for rss in recent_rss:
                            rss_context += f"- Темы: {', '.join(rss.key_topics[:3])}\n"
                            rss_context += f"  Рекомендации: {rss.recommendations[:100]}...\n"
                
                rates_context = "\n".join([f"{r.from_currency}/{r.to_currency}: {r.rate}" for r in latest_rates])
                news_context = "\n".join([f"- {n.title}" for n in latest_news])
                
            finally:
                if 'db' in locals():
                    db.close()
            
            prompt = f"""
Контекст:
АКТУАЛЬНЫЕ КУРСЫ ВАЛЮТ:
{rates_context}

ПОСЛЕДНИЕ НОВОСТИ:
{news_context}

{rss_context}

ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ:
{json.dumps(context) if context else 'Отсутствует'}

Вопрос пользователя: {question}

Ответь как профессиональный финансовый консультант, специализирующийся на казахстанском рынке.
Используй актуальные данные из контекста, включая данные из RSS каналов пользователя.
Ответ должен быть информативным, но кратким (до 300 слов).
"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты профессиональный финансовый консультант Financial AI Dashboard. Отвечаешь на русском языке, даёшь практические советы на основе актуальных данных, включая пользовательские RSS источники."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error answering question with RSS: {e}")
            return f"Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, повторите попытку позже. Ваш вопрос был: '{question}'"

# =============================================================================
# Обновленные задачи по расписанию
# =============================================================================

async def update_user_rss_feeds():
    """Обновление пользовательских RSS каналов"""
    logger.info("Starting user RSS feeds update...")
    
    try:
        db = SessionLocal()
        try:
            # Получаем RSS каналы, которые нужно обновить
            now = datetime.utcnow()
            feeds_to_update = db.query(UserRSSFeed).filter(
                UserRSSFeed.is_active == True
            ).all()
            
            for feed in feeds_to_update:
                try:
                    # Проверяем, нужно ли обновлять этот канал
                    if feed.last_fetched:
                        time_diff = now - feed.last_fetched
                        
                        if feed.fetch_frequency == "hourly" and time_diff < timedelta(hours=1):
                            continue
                        elif feed.fetch_frequency == "daily" and time_diff < timedelta(days=1):
                            continue
                        elif feed.fetch_frequency == "weekly" and time_diff < timedelta(weeks=1):
                            continue
                    
                    logger.info(f"Updating RSS feed: {feed.name}")
                    
                    # Получаем статьи из RSS
                    articles = await EnhancedNewsService.fetch_user_rss_feeds(str(feed.user_id), db)
                    
                    # Анализируем каждую статью с помощью AI
                    for article in articles:
                        if article.get('rss_feed_id') == str(feed.id):
                            # Сохраняем статью в базу
                            news_article = NewsArticle(
                                title=article['title'],
                                content=article['content'],
                                url=article['url'],
                                published_at=article['published_at'],
                                source=article['source'],
                                category=article['category'],
                                relevance_score=article.get('relevance_score', 0.5)
                            )
                            db.add(news_article)
                            db.flush()
                            
                            # AI анализ статьи
                            if feed.auto_analysis:
                                await EnhancedAIAnalysisService.analyze_rss_content(
                                    article, str(feed.id), str(feed.user_id), db
                                )
                    
                except Exception as e:
                    logger.error(f"Error updating RSS feed {feed.name}: {e}")
                    feed.error_count += 1
                    feed.last_error = str(e)
                    continue
            
            db.commit()
            logger.info("User RSS feeds update completed")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in user RSS feeds update: {e}")

# Обновленные задачи планировщика
async def update_exchange_rates():
    """Обновление курсов валют"""
    logger.info("Starting scheduled exchange rates update...")
    
    try:
        rates = await NBKExchangeRateService.fetch_exchange_rates()
        
        db = SessionLocal()
        try:
            for rate_data in rates:
                # Проверяем, есть ли уже такой курс на сегодня
                existing = db.query(ExchangeRate).filter(
                    ExchangeRate.from_currency == rate_data['from_currency'],
                    ExchangeRate.to_currency == rate_data['to_currency'],
                    ExchangeRate.date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ).first()
                
                if not existing:
                    rate = ExchangeRate(**rate_data)
                    db.add(rate)
            
            db.commit()
            logger.info(f"Successfully updated {len(rates)} exchange rates")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error updating exchange rates: {e}")

async def update_news():
    """Обновление базовых новостей"""
    logger.info("Starting scheduled news update...")
    
    try:
        articles = await EnhancedNewsService.fetch_default_news()
        
        db = SessionLocal()
        try:
            for article_data in articles:
                # Проверяем, есть ли уже такая новость
                existing = db.query(NewsArticle).filter(
                    NewsArticle.title == article_data['title']
                ).first()
                
                if not existing:
                    # Анализ настроения через AI (упрощенно)
                    if any(word in article_data['title'].lower() for word in ['рост', 'увеличение', 'стабильность']):
                        sentiment = 'positive'
                    elif any(word in article_data['title'].lower() for word in ['падение', 'снижение', 'кризис']):
                        sentiment = 'negative'
                    else:
                        sentiment = 'neutral'
                    
                    article_data['sentiment'] = sentiment
                    article_data['risk_level'] = 'medium'  # По умолчанию
                    
                    news = NewsArticle(**article_data)
                    db.add(news)
            
            db.commit()
            logger.info(f"Successfully updated {len(articles)} news articles")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error updating news: {e}")

async def generate_daily_report():
    """Генерация ежедневного отчета с RSS данными"""
    logger.info("Starting daily report generation...")
    
    try:
        db = SessionLocal()
        try:
            # Получение актуальных данных
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            rates = db.query(ExchangeRate).filter(
                ExchangeRate.date >= today
            ).all()
            
            news = db.query(NewsArticle).filter(
                NewsArticle.created_at >= today
            ).all()
            
            # AI анализ с учетом всех RSS данных
            analysis = await EnhancedAIAnalysisService.analyze_financial_data_with_rss(
                [{'from_currency': r.from_currency, 'to_currency': r.to_currency, 'rate': r.rate} for r in rates],
                [{'title': n.title, 'content': n.content or ''} for n in news],
                db=db
            )
            
            # Получение инсайтов из RSS анализа
            rss_insights = db.query(RSSContentAnalysis).filter(
                RSSContentAnalysis.analysis_date >= today
            ).order_by(RSSContentAnalysis.financial_relevance.desc()).limit(10).all()
            
            # Создание отчета
            rss_section = ""
            if rss_insights:
                rss_section = f"""
## 📡 Анализ пользовательских RSS каналов
{chr(10).join([f"- **{', '.join(insight.key_topics[:2])}**: {insight.recommendations[:100]}..." for insight in rss_insights[:5]])}

**Общее настроение RSS источников:** {sum([insight.sentiment_score for insight in rss_insights]) / len(rss_insights):.2f}
"""
            
            report_content = f"""
# Ежедневный финансовый отчет
**Дата:** {datetime.now().strftime('%d.%m.%Y')}

## 📊 Курсы валют (НБ РК)
{chr(10).join([f"- {r.from_currency}/{r.to_currency}: {r.rate:.2f}" for r in rates])}

## 📈 Анализ ситуации
{analysis['summary']}

**Уровень риска:** {analysis['risk_assessment']}

## 💡 Рекомендации
{chr(10).join([f"- {rec}" for rec in analysis['recommendations']])}

{rss_section}

## 🔮 Прогноз
{analysis['forecast']}

## 📰 Последние новости
{chr(10).join([f"- {n.title}" for n in news[:5]])}

---
*Отчет сгенерирован автоматически системой Financial AI Dashboard с анализом пользовательских RSS каналов*
"""

            # Сохранение отчета
            rss_feeds_data = [str(insight.rss_feed_id) for insight in rss_insights]
            
            report = Report(
                name=f"Ежедневный отчет {datetime.now().strftime('%d.%m.%Y')}",
                report_type="daily_summary",
                content=report_content,
                rss_feeds_included=rss_feeds_data
            )
            db.add(report)
            db.commit()
            
            logger.info("Enhanced daily report generated successfully")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")

# Планировщик задач
def schedule_tasks():
    """Планирование автоматических задач"""
    schedule.every().day.at("08:00").do(lambda: asyncio.run(update_exchange_rates()))
    schedule.every().hour.do(lambda: asyncio.run(update_news()))
    schedule.every().hour.do(lambda: asyncio.run(update_user_rss_feeds()))  # НОВОЕ
    schedule.every().day.at("09:00").do(lambda: asyncio.run(generate_daily_report()))
    
    logger.info("Enhanced scheduled tasks configured")

def run_scheduler():
    """Запуск планировщика в отдельном потоке"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# Запуск планировщика
schedule_tasks()
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# =============================================================================
# API Routes (обновленные и новые)
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Главная страница"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "nbk_api": "available",
            "ai_service": "available" if client else "unavailable",
            "news_service": "available",
            "rss_feeds": "available"
        },
        "version": "2.1.0"
    }

# =============================================================================
# RSS Feed Management API (НОВЫЕ ENDPOINTS)
# =============================================================================

@app.get("/api/rss/feeds", response_model=List[RSSFeedResponse])
async def get_user_rss_feeds(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получение списка RSS каналов пользователя"""
    try:
        feeds = db.query(UserRSSFeed).filter(UserRSSFeed.user_id == current_user.id).all()
        
        return [
            RSSFeedResponse(
                id=str(feed.id),
                name=feed.name,
                url=feed.url,
                description=feed.description or "",
                category=feed.category,
                priority=feed.priority,
                is_active=feed.is_active,
                auto_analysis=feed.auto_analysis,
                keywords=feed.keywords or [],
                last_fetched=feed.last_fetched,
                fetch_frequency=feed.fetch_frequency,
                error_count=feed.error_count,
                articles_count=feed.articles_count,
                created_at=feed.created_at
            )
            for feed in feeds
        ]
        
    except Exception as e:
        logger.error(f"Error getting RSS feeds: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения RSS каналов")

@app.post("/api/rss/feeds", response_model=RSSFeedResponse)
async def create_rss_feed(
    feed_data: RSSFeedCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового RSS канала"""
    try:
        # Валидация RSS URL
        if not validate_rss_url(str(feed_data.url)):
            raise HTTPException(status_code=400, detail="Недоступный или некорректный RSS URL")
        
        # Проверка лимитов подписки
        existing_feeds_count = db.query(UserRSSFeed).filter(UserRSSFeed.user_id == current_user.id).count()
        
        max_feeds = 5 if current_user.subscription_plan == "starter" else 20 if current_user.subscription_plan == "professional" else 100
        
        if existing_feeds_count >= max_feeds:
            raise HTTPException(
                status_code=400, 
                detail=f"Достигнут лимит RSS каналов для плана {current_user.subscription_plan}: {max_feeds}"
            )
        
        # Создание RSS канала
        rss_feed = UserRSSFeed(
            user_id=current_user.id,
            name=feed_data.name,
            url=str(feed_data.url),
            description=feed_data.description,
            category=feed_data.category,
            priority=feed_data.priority,
            auto_analysis=feed_data.auto_analysis,
            keywords=feed_data.keywords,
            fetch_frequency=feed_data.fetch_frequency
        )
        
        db.add(rss_feed)
        db.commit()
        db.refresh(rss_feed)
        
        # Немедленное тестовое обновление
        try:
            await EnhancedNewsService.fetch_user_rss_feeds(str(current_user.id), db)
        except Exception as e:
            logger.warning(f"Initial RSS fetch failed: {e}")
        
        return RSSFeedResponse(
            id=str(rss_feed.id),
            name=rss_feed.name,
            url=rss_feed.url,
            description=rss_feed.description or "",
            category=rss_feed.category,
            priority=rss_feed.priority,
            is_active=rss_feed.is_active,
            auto_analysis=rss_feed.auto_analysis,
            keywords=rss_feed.keywords or [],
            last_fetched=rss_feed.last_fetched,
            fetch_frequency=rss_feed.fetch_frequency,
            error_count=rss_feed.error_count,
            articles_count=rss_feed.articles_count,
            created_at=rss_feed.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания RSS канала")

@app.put("/api/rss/feeds/{feed_id}", response_model=RSSFeedResponse)
async def update_rss_feed(
    feed_id: str,
    feed_data: RSSFeedUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление RSS канала"""
    try:
        feed = db.query(UserRSSFeed).filter(
            UserRSSFeed.id == feed_id,
            UserRSSFeed.user_id == current_user.id
        ).first()
        
        if not feed:
            raise HTTPException(status_code=404, detail="RSS канал не найден")
        
        # Обновляем поля
        update_data = feed_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feed, field, value)
        
        feed.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(feed)
        
        return RSSFeedResponse(
            id=str(feed.id),
            name=feed.name,
            url=feed.url,
            description=feed.description or "",
            category=feed.category,
            priority=feed.priority,
            is_active=feed.is_active,
            auto_analysis=feed.auto_analysis,
            keywords=feed.keywords or [],
            last_fetched=feed.last_fetched,
            fetch_frequency=feed.fetch_frequency,
            error_count=feed.error_count,
            articles_count=feed.articles_count,
            created_at=feed.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления RSS канала")

@app.delete("/api/rss/feeds/{feed_id}")
async def delete_rss_feed(
    feed_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление RSS канала"""
    try:
        feed = db.query(UserRSSFeed).filter(
            UserRSSFeed.id == feed_id,
            UserRSSFeed.user_id == current_user.id
        ).first()
        
        if not feed:
            raise HTTPException(status_code=404, detail="RSS канал не найден")
        
        # Удаляем связанные анализы
        db.query(RSSContentAnalysis).filter(
            RSSContentAnalysis.rss_feed_id == feed_id
        ).delete()
        
        # Удаляем сам канал
        db.delete(feed)
        db.commit()
        
        return {"message": "RSS канал успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления RSS канала")

@app.post("/api/rss/feeds/{feed_id}/test")
async def test_rss_feed(
    feed_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Тестирование RSS канала"""
    try:
        feed = db.query(UserRSSFeed).filter(
            UserRSSFeed.id == feed_id,
            UserRSSFeed.user_id == current_user.id
        ).first()
        
        if not feed:
            raise HTTPException(status_code=404, detail="RSS канал не найден")
        
        # Тестовое получение данных
        articles = await EnhancedNewsService.fetch_user_rss_feeds(str(current_user.id), db)
        
        # Фильтруем статьи для этого канала
        feed_articles = [a for a in articles if a.get('rss_feed_id') == feed_id]
        
        return {
            "status": "success",
            "articles_found": len(feed_articles),
            "sample_articles": [
                {
                    "title": article["title"],
                    "url": article["url"],
                    "relevance_score": article.get("relevance_score", 0)
                }
                for article in feed_articles[:3]
            ],
            "last_test": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка тестирования RSS канала")

@app.get("/api/rss/analysis")
async def get_rss_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 7
):
    """Получение анализа RSS контента"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        analyses = db.query(RSSContentAnalysis).filter(
            RSSContentAnalysis.user_id == current_user.id,
            RSSContentAnalysis.analysis_date >= start_date
        ).order_by(RSSContentAnalysis.financial_relevance.desc()).limit(50).all()
        
        # Агрегированная статистика
        total_analyses = len(analyses)
        avg_relevance = sum([a.financial_relevance for a in analyses]) / max(total_analyses, 1)
        avg_sentiment = sum([a.sentiment_score for a in analyses]) / max(total_analyses, 1)
        
        # Топ темы
        all_topics = []
        for analysis in analyses:
            all_topics.extend(analysis.key_topics or [])
        
        from collections import Counter
        top_topics = Counter(all_topics).most_common(10)
        
        # Распределение по влиянию на рынок
        impact_distribution = Counter([a.market_impact for a in analyses])
        
        return {
            "summary": {
                "total_analyses": total_analyses,
                "average_relevance": round(avg_relevance, 2),
                "average_sentiment": round(avg_sentiment, 2),
                "period_days": days
            },
            "top_topics": [{"topic": topic, "count": count} for topic, count in top_topics],
            "market_impact_distribution": dict(impact_distribution),
            "recent_analyses": [
                {
                    "id": str(analysis.id),
                    "analysis_date": analysis.analysis_date.isoformat(),
                    "financial_relevance": analysis.financial_relevance,
                    "sentiment_score": analysis.sentiment_score,
                    "key_topics": analysis.key_topics[:3],
                    "market_impact": analysis.market_impact,
                    "recommendations": analysis.recommendations[:100] + "..." if len(analysis.recommendations) > 100 else analysis.recommendations,
                    "ai_confidence": analysis.ai_confidence
                }
                for analysis in analyses[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting RSS analysis: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения анализа RSS")

# =============================================================================
# Обновленные основные API Routes
# =============================================================================

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Авторизация пользователя"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "company": user.company,
            "subscription_plan": user.subscription_plan
        }
    }

@app.post("/api/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация пользователя"""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        company=user_data.company
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "company": user.company,
            "subscription_plan": user.subscription_plan
        }
    }

@app.get("/api/dashboard")
async def get_dashboard_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получение данных для дашборда с RSS инсайтами"""
    try:
        # Получение актуальных курсов валют
        latest_rates = db.query(ExchangeRate).filter(
            ExchangeRate.date >= datetime.now() - timedelta(days=1)
        ).all()
        
        # Получение последних новостей
        latest_news = db.query(NewsArticle).filter(
            NewsArticle.created_at >= datetime.now() - timedelta(days=1)
        ).limit(5).all()
        
        # Получение банковских счетов пользователя
        accounts = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()
        
        # Получение RSS статистики пользователя
        rss_feeds_count = db.query(UserRSSFeed).filter(
            UserRSSFeed.user_id == current_user.id,
            UserRSSFeed.is_active == True
        ).count()
        
        recent_rss_analyses = db.query(RSSContentAnalysis).filter(
            RSSContentAnalysis.user_id == current_user.id,
            RSSContentAnalysis.analysis_date >= datetime.now() - timedelta(days=1)
        ).order_by(RSSContentAnalysis.financial_relevance.desc()).limit(3).all()
        
        # Расчет общего баланса в тенге
        total_balance_kzt = 0
        for account in accounts:
            if account.currency == "KZT":
                total_balance_kzt += account.balance
            else:
                # Конвертация через актуальные курсы
                rate = next((r.rate for r in latest_rates if r.from_currency == account.currency and r.to_currency == "KZT"), 1)
                total_balance_kzt += account.balance * rate
        
        # Определение статуса ликвидности
        if total_balance_kzt < 30000000:
            liquidity_status = "CRITICAL"
        elif total_balance_kzt < 100000000:
            liquidity_status = "LOW"
        elif total_balance_kzt > 300000000:
            liquidity_status = "EXCESS"
        else:
            liquidity_status = "ADEQUATE"
        
        return {
            "user": {
                "name": current_user.name,
                "company": current_user.company,
                "subscription_plan": current_user.subscription_plan
            },
            "summary": {
                "total_balance_kzt": total_balance_kzt,
                "liquidity_status": liquidity_status,
                "accounts_count": len(accounts),
                "rss_feeds_count": rss_feeds_count,
                "last_updated": datetime.now().isoformat()
            },
            "exchange_rates": [
                {
                    "from_currency": rate.from_currency,
                    "to_currency": rate.to_currency,
                    "rate": rate.rate,
                    "date": rate.date.isoformat(),
                    "source": rate.source
                }
                for rate in latest_rates
            ],
            "news": [
                {
                    "id": str(news.id),
                    "title": news.title,
                    "content": news.content[:200] + "..." if news.content and len(news.content) > 200 else news.content,
                    "url": news.url,
                    "source": news.source,
                    "sentiment": news.sentiment,
                    "published_at": news.published_at.isoformat() if news.published_at else None
                }
                for news in latest_news
            ],
            "rss_insights": [
                {
                    "key_topics": analysis.key_topics[:3],
                    "market_impact": analysis.market_impact,
                    "sentiment_score": analysis.sentiment_score,
                    "financial_relevance": analysis.financial_relevance,
                    "recommendations": analysis.recommendations[:100] + "..." if len(analysis.recommendations) > 100 else analysis.recommendations
                }
                for analysis in recent_rss_analyses
            ],
            "accounts": [
                {
                    "id": str(account.id),
                    "name": account.name,
                    "bank": account.bank,
                    "balance": account.balance,
                    "currency": account.currency,
                    "account_type": account.account_type
                }
                for account in accounts
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных дашборда")

@app.post("/api/ai/consult")
async def ai_consultation(
    request: AIQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI консультация с учетом RSS данных"""
    try:
        # Подготовка контекста пользователя
        user_context = {
            "user_id": str(current_user.id),
            "company": current_user.company,
            "subscription_plan": current_user.subscription_plan
        }
        user_context.update(request.context)
        
        # Получение ответа от AI с учетом RSS
        if request.include_rss:
            response = await EnhancedAIAnalysisService.answer_question_with_rss(
                request.question, user_context, str(current_user.id), db
            )
            
            # Получаем RSS источники, которые были использованы
            rss_sources = db.query(UserRSSFeed).filter(
                UserRSSFeed.user_id == current_user.id,
                UserRSSFeed.is_active == True
            ).limit(5).all()
            
            rss_sources_info = [{"name": feed.name, "category": feed.category} for feed in rss_sources]
        else:
            response = await EnhancedAIAnalysisService.answer_question_with_rss(
                request.question, user_context
            )
            rss_sources_info = []
        
        # Сохранение консультации
        consultation = AIConsultation(
            user_id=current_user.id,
            question=request.question,
            response=response,
            context_data=user_context,
            rss_sources_used=rss_sources_info,
            session_id=str(uuid.uuid4()),
            source=request.source
        )
        db.add(consultation)
        db.commit()
        
        return {
            "id": str(consultation.id),
            "question": request.question,
            "response": response,
            "rss_sources_used": rss_sources_info,
            "include_rss": request.include_rss,
            "created_at": consultation.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in AI consultation: {e}")
        raise HTTPException(status_code=500, detail="Ошибка AI консультации")

@app.get("/api/reports/latest")
async def get_latest_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получение последнего отчета с RSS данными"""
    try:
        latest_report = db.query(Report).filter(
            Report.report_type == "daily_summary"
        ).order_by(Report.generated_at.desc()).first()
        
        if not latest_report:
            # Генерируем отчет прямо сейчас
            await generate_daily_report()
            latest_report = db.query(Report).filter(
                Report.report_type == "daily_summary"
            ).order_by(Report.generated_at.desc()).first()
        
        return {
            "id": str(latest_report.id),
            "name": latest_report.name,
            "content": latest_report.content,
            "rss_feeds_included": latest_report.rss_feeds_included or [],
            "generated_at": latest_report.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting latest report: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения отчета")

# =============================================================================
# n8n Webhook Integration (обновленная)
# =============================================================================

@app.post("/webhook/n8n/chat")
async def n8n_chat_webhook(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Webhook для интеграции с n8n чат-ботом с RSS поддержкой"""
    try:
        logger.info(f"Received n8n webhook: {payload}")
        
        # Извлечение сообщения из payload
        message = payload.get("message", "")
        user_id = payload.get("user_id")
        session_id = payload.get("session_id", str(uuid.uuid4()))
        webhook_url = payload.get("webhook_url")  # URL для отправки ответа обратно в n8n
        include_rss = payload.get("include_rss", True)  # НОВОЕ: включать RSS в анализ
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Логирование webhook
        webhook_log = WebhookLog(
            source="n8n",
            event_type="chat_message",
            payload=payload
        )
        db.add(webhook_log)
        db.commit()
        
        # Получение ответа от AI с учетом RSS
        if include_rss and user_id:
            response = await EnhancedAIAnalysisService.answer_question_with_rss(
                message, {"source": "n8n", "session_id": session_id}, user_id, db
            )
            
            # Получаем информацию об использованных RSS источниках
            user_feeds = db.query(UserRSSFeed).filter(
                UserRSSFeed.user_id == user_id,
                UserRSSFeed.is_active == True
            ).limit(3).all()
            
            rss_info = [f"{feed.name} ({feed.category})" for feed in user_feeds]
        else:
            response = await EnhancedAIAnalysisService.answer_question_with_rss(
                message, {"source": "n8n", "session_id": session_id}
            )
            rss_info = []
        
        # Сохранение консультации
        consultation = AIConsultation(
            user_id=user_id if user_id else None,
            question=message,
            response=response,
            context_data={"source": "n8n", "session_id": session_id, "include_rss": include_rss},
            rss_sources_used=rss_info,
            session_id=session_id,
            source="n8n"
        )
        db.add(consultation)
        db.commit()
        
        # Подготовка ответа
        response_data = {
            "response": response,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "source": "financial_ai_dashboard",
            "rss_sources_used": rss_info,
            "include_rss": include_rss
        }
        
        # Если указан webhook_url, отправляем ответ обратно в n8n
        if webhook_url:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(webhook_url, json=response_data)
                logger.info(f"Response sent back to n8n webhook: {webhook_url}")
            except Exception as e:
                logger.error(f"Error sending response to n8n webhook: {e}")
        
        # Обновляем лог с ответом
        webhook_log.response = response_data
        db.commit()
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing n8n webhook: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки webhook")

@app.get("/webhook/n8n/status")
async def n8n_webhook_status():
    """Статус webhook для n8n с RSS поддержкой"""
    return {
        "status": "active",
        "webhook_url": "/webhook/n8n/chat",
        "supported_methods": ["POST"],
        "required_fields": ["message"],
        "optional_fields": ["user_id", "session_id", "webhook_url", "include_rss"],
        "features": ["rss_analysis", "user_context", "ai_consultation"],
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# Инициализация данных (обновленная)
# =============================================================================

@app.post("/api/init-demo")
async def initialize_demo_data(db: Session = Depends(get_db)):
    """Инициализация демонстрационных данных с RSS каналами"""
    try:
        # Проверяем, есть ли уже демо пользователь
        demo_user = db.query(User).filter(User.email == "demo@finai.kz").first()
        if demo_user:
            return {"message": "Demo data already exists", "demo_email": "demo@finai.kz", "demo_password": "demo123"}
        
        # Создание демо пользователя
        demo_user = User(
            email="demo@finai.kz",
            name="Demo CFO",
            hashed_password=get_password_hash("demo123"),
            company="ТОО КазахТрейд ДЕМО",
            phone="+7 777 123 4567",
            subscription_plan="professional"
        )
        db.add(demo_user)
        db.flush()
        
        # Создание демо банковских счетов
        demo_accounts = [
            BankAccount(
                user_id=demo_user.id,
                name="Основной операционный счет",
                bank="Halyk Bank",
                balance=125300000,
                currency="KZT",
                account_type="operational"
            ),
            BankAccount(
                user_id=demo_user.id,
                name="Валютный счет USD",
                bank="Kaspi Bank",
                balance=248500,
                currency="USD",
                account_type="currency"
            ),
            BankAccount(
                user_id=demo_user.id,
                name="Резервный фонд",
                bank="Forte Bank",
                balance=45200000,
                currency="KZT",
                account_type="reserve"
            )
        ]
        
        for account in demo_accounts:
            db.add(account)
        
        # НОВОЕ: Создание демо RSS каналов
        demo_rss_feeds = [
            UserRSSFeed(
                user_id=demo_user.id,
                name="Reuters Financial News",
                url="https://feeds.reuters.com/reuters/businessNews",
                description="Мировые финансовые новости от Reuters",
                category="international",
                priority=5,
                auto_analysis=True,
                keywords=["finance", "market", "economy", "oil", "dollar"],
                fetch_frequency="hourly"
            ),
            UserRSSFeed(
                user_id=demo_user.id,
                name="Bloomberg Economics",
                url="https://feeds.bloomberg.com/economics/news.rss",
                description="Экономические новости от Bloomberg",
                category="economics",
                priority=4,
                auto_analysis=True,
                keywords=["central bank", "inflation", "GDP", "policy"],
                fetch_frequency="hourly"
            ),
            UserRSSFeed(
                user_id=demo_user.id,
                name="Казахстанские финансы",
                url="https://kursiv.kz/feed/",
                description="Финансовые новости Казахстана",
                category="local",
                priority=5,
                auto_analysis=True,
                keywords=["тенге", "НБ РК", "экономика", "банки"],
                fetch_frequency="daily"
            )
        ]
        
        for rss_feed in demo_rss_feeds:
            db.add(rss_feed)
        
        db.commit()
        
        # Запуск первичного обновления данных
        await update_exchange_rates()
        await update_news()
        await update_user_rss_feeds()  # НОВОЕ
        await generate_daily_report()
        
        logger.info("Demo data with RSS feeds initialized successfully")
        
        return {
            "message": "Demo data with RSS feeds initialized successfully",
            "demo_email": "demo@finai.kz",
            "demo_password": "demo123",
            "features": ["NBK exchange rates", "Financial news monitoring", "AI analysis", "n8n integration", "Custom RSS feeds"],
            "demo_rss_feeds": len(demo_rss_feeds)
        }
        
    except Exception as e:
        logger.error(f"Error initializing demo data: {e}")
        raise HTTPException(status_code=500, detail="Ошибка инициализации демо данных")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Enhanced Financial AI Dashboard with RSS support...")
    uvicorn.run(app, host="0.0.0.0", port=8000)