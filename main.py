# ⚡ FastAPI Backend с исправленными отчетами и мобильной поддержкой

from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, JSON, Integer, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
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
from email.mime.base import MIMEBase
from email import encoders
import csv
import io
import base64
from jinja2 import Template
import schedule
import threading
import time
import random
import os
from supabase import create_client

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "financial-ai-super-secret-key-for-development-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Database setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# FastAPI app
app = FastAPI(
    title="Financial AI Dashboard API",
    description="Backend API for Financial AI Dashboard - Corporate Liquidity Management System",
    version="1.0.0"
)

# CORS middleware with mobile browser support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files with mobile optimization
app.mount("/static", StaticFiles(directory="static"), name="static")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@financial-ai.com")

# =============================================================================
# Database Models
# =============================================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # user, admin, demo
    company = Column(String)
    phone = Column(String)
    avatar_url = Column(String)
    subscription_plan = Column(String, default="starter")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    timezone = Column(String, default="Asia/Almaty")
    language = Column(String, default="ru")
    mobile_app_enabled = Column(Boolean, default=True)  # New for mobile support
    push_notifications_enabled = Column(Boolean, default=True)  # New for mobile
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    tax_id = Column(String)
    base_currency = Column(String, default="KZT")
    industry = Column(String)
    country = Column(String, default="Kazakhstan")
    settings = Column(JSON, default={})
    mobile_settings = Column(JSON, default={})  # New for mobile-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    service = Column(String, nullable=False)
    key_name = Column(String, nullable=False)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    bank = Column(String, nullable=False)
    account_number = Column(String)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="KZT")
    account_type = Column(String, default="operational")
    is_active = Column(Boolean, default=True)
    mobile_priority = Column(Integer, default=0)  # New for mobile display priority
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CashFlow(Base):
    __tablename__ = "cash_flows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    account_id = Column(UUID(as_uuid=True))
    amount = Column(Float, nullable=False)
    currency = Column(String, default="KZT")
    description = Column(String)
    category = Column(String)
    planned_date = Column(DateTime, nullable=False)
    actual_date = Column(DateTime)
    probability = Column(Float, default=1.0)
    status = Column(String, default="planned")
    flow_type = Column(String, nullable=False)
    mobile_important = Column(Boolean, default=False)  # New for mobile highlighting
    created_at = Column(DateTime, default=datetime.utcnow)

class AIConsultation(Base):
    __tablename__ = "ai_consultations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_data = Column(JSON)
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)
    rating = Column(Integer)
    session_id = Column(String)
    device_type = Column(String, default="web")  # New: web, mobile, tablet
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    report_type = Column(String, nullable=False)
    parameters = Column(JSON, default={})
    schedule = Column(String)
    recipients = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    mobile_enabled = Column(Boolean, default=True)  # New for mobile notifications
    last_generated = Column(DateTime)
    next_scheduled = Column(DateTime)
    generation_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ReportHistory(Base):
    __tablename__ = "report_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String)
    file_size = Column(Integer)
    generation_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    mobile_optimized = Column(Boolean, default=False)  # New for mobile-optimized reports

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text)
    notification_type = Column(String, default="info")
    is_read = Column(Boolean, default=False)
    action_url = Column(String)
    mobile_push_sent = Column(Boolean, default=False)  # New for mobile push tracking
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_token = Column(String, nullable=False, unique=True)
    device_info = Column(JSON)
    user_agent = Column(String)
    ip_address = Column(String)
    is_mobile = Column(Boolean, default=False)  # New for mobile session tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# =============================================================================
# Pydantic Models
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    company: Optional[str] = None
    role: Optional[str] = "user"
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_info: Optional[Dict[str, Any]] = {}

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    company: Optional[str]
    subscription_plan: str
    avatar_url: Optional[str]
    is_verified: bool
    two_factor_enabled: bool
    mobile_app_enabled: bool
    timezone: str
    language: str
    created_at: datetime
    last_login: Optional[datetime]

class MobileOptimizedReportCreate(BaseModel):
    name: str
    description: Optional[str] = None
    report_type: str
    parameters: Optional[Dict[str, Any]] = {}
    schedule: Optional[str] = "manual"
    recipients: List[str] = []
    mobile_enabled: bool = True

class AIConsultationCreate(BaseModel):
    question: str
    context_data: Optional[Dict[str, Any]] = {}
    device_type: Optional[str] = "web"

# =============================================================================
# Utility Functions
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def detect_mobile_device(user_agent: str) -> bool:
    """Detect if request is from mobile device"""
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
    return any(keyword in user_agent.lower() for keyword in mobile_keywords)

def encrypt_api_key(key: str) -> str:
    import base64
    return base64.b64encode(key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    import base64
    return base64.b64decode(encrypted_key.encode()).decode()

def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "••••••••"
    return key[:4] + "•" * (len(key) - 8) + key[-4:]

# =============================================================================
# Report Generation Functions (Enhanced for Mobile)
# =============================================================================

def generate_liquidity_report(user_id: str, db: Session, mobile_optimized: bool = False) -> Dict[str, Any]:
    """Generate liquidity analysis report with mobile optimization"""
    user = db.query(User).filter(User.id == user_id).first()
    accounts = db.query(BankAccount).filter(BankAccount.user_id == user_id, BankAccount.is_active == True).all()
    
    # Sort by mobile priority for mobile clients
    if mobile_optimized:
        accounts = sorted(accounts, key=lambda x: x.mobile_priority or 0, reverse=True)
    
    # Calculate total balance
    total_balance_kzt = 0
    account_data = []
    
    for account in accounts:
        # Convert to KZT (mock exchange rates)
        if account.currency == "USD":
            balance_kzt = account.balance * 480
        elif account.currency == "EUR":
            balance_kzt = account.balance * 520
        else:
            balance_kzt = account.balance
            
        total_balance_kzt += balance_kzt
        account_data.append({
            "name": account.name,
            "bank": account.bank,
            "balance": account.balance,
            "currency": account.currency,
            "balance_kzt": balance_kzt,
            "account_type": account.account_type,
            "mobile_priority": getattr(account, 'mobile_priority', 0)
        })
    
    # Get cash flows with mobile importance
    cash_flows = db.query(CashFlow).filter(
        CashFlow.user_id == user_id,
        CashFlow.planned_date >= datetime.utcnow() - timedelta(days=7),
        CashFlow.planned_date <= datetime.utcnow() + timedelta(days=30)
    ).all()
    
    if mobile_optimized:
        # Prioritize important cash flows for mobile
        cash_flows = sorted(cash_flows, key=lambda x: (x.mobile_important or False, abs(x.amount)), reverse=True)
    
    inflows = sum([cf.amount for cf in cash_flows if cf.flow_type == "inflow"])
    outflows = sum([abs(cf.amount) for cf in cash_flows if cf.flow_type == "outflow"])
    net_cash_flow = inflows - outflows
    
    # Determine liquidity status
    if total_balance_kzt < 30000000:  # 30M KZT
        liquidity_status = "CRITICAL"
        risk_level = "HIGH"
    elif total_balance_kzt < 100000000:  # 100M KZT
        liquidity_status = "LOW"
        risk_level = "MEDIUM"
    elif total_balance_kzt > 300000000:  # 300M KZT
        liquidity_status = "EXCESS"
        risk_level = "LOW"
    else:
        liquidity_status = "ADEQUATE"
        risk_level = "LOW"
    
    recommendations = []
    if liquidity_status == "CRITICAL":
        recommendations.append("🚨 Срочно пересмотрите планы платежей и привлеките дополнительное финансирование")
        recommendations.append("⏱️ Рассмотрите возможность отсрочки крупных выплат")
    elif liquidity_status == "LOW":
        recommendations.append("📈 Усильте контроль за дебиторской задолженностью")
        recommendations.append("💰 Оптимизируйте кредиторскую задолженность")
    elif liquidity_status == "EXCESS":
        recommendations.append("🏦 Рассмотрите размещение избыточных средств в депозиты")
        recommendations.append("📊 Оцените возможности инвестирования свободных средств")
    
    return {
        "report_type": "liquidity_daily",
        "mobile_optimized": mobile_optimized,
        "generated_at": datetime.utcnow().isoformat(),
        "company_name": user.company,
        "user_name": user.name,
        "period": {
            "from": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "to": (datetime.utcnow() + timedelta(days=30)).date().isoformat()
        },
        "summary": {
            "total_balance_kzt": total_balance_kzt,
            "accounts_count": len(accounts),
            "liquidity_status": liquidity_status,
            "risk_level": risk_level,
            "net_cash_flow_30d": net_cash_flow
        },
        "accounts": account_data[:3] if mobile_optimized else account_data,  # Limit for mobile
        "cash_flows": {
            "inflows": inflows,
            "outflows": outflows,
            "net": net_cash_flow
        },
        "recommendations": recommendations[:2] if mobile_optimized else recommendations
    }

def generate_risk_report(user_id: str, db: Session, mobile_optimized: bool = False) -> Dict[str, Any]:
    """Generate risk analysis report with mobile optimization"""
    user = db.query(User).filter(User.id == user_id).first()
    accounts = db.query(BankAccount).filter(BankAccount.user_id == user_id, BankAccount.is_active == True).all()
    
    # Risk analysis
    risks = []
    
    # Currency concentration risk
    currencies = {}
    total_balance = 0
    for account in accounts:
        balance_kzt = account.balance
        if account.currency == "USD":
            balance_kzt = account.balance * 480
        elif account.currency == "EUR":
            balance_kzt = account.balance * 520
        
        currencies[account.currency] = currencies.get(account.currency, 0) + balance_kzt
        total_balance += balance_kzt
    
    for currency, amount in currencies.items():
        percentage = (amount / total_balance) * 100 if total_balance > 0 else 0
        if percentage > 70:
            risks.append({
                "type": "currency_concentration",
                "level": "HIGH",
                "description": f"📱 Концентрация в валюте {currency}: {percentage:.1f}%" if mobile_optimized else f"Концентрация в валюте {currency}: {percentage:.1f}%",
                "recommendation": "Диверсифицируйте валютную структуру портфеля",
                "mobile_priority": True
            })
    
    # Bank concentration risk
    banks = {}
    for account in accounts:
        balance_kzt = account.balance
        if account.currency == "USD":
            balance_kzt = account.balance * 480
        elif account.currency == "EUR":
            balance_kzt = account.balance * 520
        
        banks[account.bank] = banks.get(account.bank, 0) + balance_kzt
    
    for bank, amount in banks.items():
        percentage = (amount / total_balance) * 100 if total_balance > 0 else 0
        if percentage > 60:
            risks.append({
                "type": "bank_concentration",
                "level": "MEDIUM",
                "description": f"🏦 Концентрация в банке {bank}: {percentage:.1f}%" if mobile_optimized else f"Концентрация в банке {bank}: {percentage:.1f}%",
                "recommendation": "Рассмотрите распределение средств между несколькими банками",
                "mobile_priority": False
            })
    
    # Liquidity risk
    if total_balance < 50000000:  # 50M KZT
        risks.append({
            "type": "liquidity",
            "level": "HIGH",
            "description": "💧 Низкий уровень ликвидности для операционных нужд" if mobile_optimized else "Низкий уровень ликвидности для операционных нужд",
            "recommendation": "Увеличьте резервы ликвидности или привлеките дополнительное финансирование",
            "mobile_priority": True
        })
    
    if mobile_optimized:
        # Sort and limit risks for mobile
        risks = sorted(risks, key=lambda x: (x.get('mobile_priority', False), x['level'] == 'HIGH'), reverse=True)[:3]
    
    # Overall risk assessment
    high_risks = len([r for r in risks if r["level"] == "HIGH"])
    medium_risks = len([r for r in risks if r["level"] == "MEDIUM"])
    
    if high_risks > 0:
        overall_risk = "HIGH"
    elif medium_risks > 1:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"
    
    return {
        "report_type": "risk_weekly",
        "mobile_optimized": mobile_optimized,
        "generated_at": datetime.utcnow().isoformat(),
        "company_name": user.company,
        "user_name": user.name,
        "period": {
            "from": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "to": datetime.utcnow().date().isoformat()
        },
        "summary": {
            "overall_risk": overall_risk,
            "total_risks": len(risks),
            "high_risks": high_risks,
            "medium_risks": medium_risks,
            "total_balance_kzt": total_balance
        },
        "risk_breakdown": {
            "currency_distribution": currencies,
            "bank_distribution": banks
        },
        "identified_risks": risks
    }

def generate_cashflow_report(user_id: str, db: Session, mobile_optimized: bool = False) -> Dict[str, Any]:
    """Generate cash flow report with mobile optimization"""
    user = db.query(User).filter(User.id == user_id).first()
    
    # Get cash flows for the last month and next month
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow() + timedelta(days=30)
    
    cash_flows = db.query(CashFlow).filter(
        CashFlow.user_id == user_id,
        CashFlow.planned_date >= start_date,
        CashFlow.planned_date <= end_date
    ).all()
    
    if mobile_optimized:
        # Prioritize important flows for mobile
        cash_flows = sorted(cash_flows, key=lambda x: (x.mobile_important or False, abs(x.amount)), reverse=True)
    
    # Group by week
    weekly_data = {}
    total_inflows = 0
    total_outflows = 0
    
    for cf in cash_flows:
        week = cf.planned_date.strftime("%Y-W%U")
        if week not in weekly_data:
            weekly_data[week] = {"inflows": 0, "outflows": 0, "net": 0}
        
        if cf.flow_type == "inflow":
            weekly_data[week]["inflows"] += cf.amount
            total_inflows += cf.amount
        else:
            weekly_data[week]["outflows"] += abs(cf.amount)
            total_outflows += abs(cf.amount)
        
        weekly_data[week]["net"] = weekly_data[week]["inflows"] - weekly_data[week]["outflows"]
    
    # Calculate forecast
    net_cash_flow = total_inflows - total_outflows
    
    # Limit cash flows for mobile
    mobile_cash_flows = cash_flows[:5] if mobile_optimized else cash_flows
    
    return {
        "report_type": "cashflow_monthly",
        "mobile_optimized": mobile_optimized,
        "generated_at": datetime.utcnow().isoformat(),
        "company_name": user.company,
        "user_name": user.name,
        "period": {
            "from": start_date.date().isoformat(),
            "to": end_date.date().isoformat()
        },
        "summary": {
            "total_inflows": total_inflows,
            "total_outflows": total_outflows,
            "net_cash_flow": net_cash_flow,
            "weeks_analyzed": len(weekly_data)
        },
        "weekly_breakdown": weekly_data,
        "cash_flows": [
            {
                "date": cf.planned_date.isoformat(),
                "amount": cf.amount,
                "type": cf.flow_type,
                "description": cf.description,
                "category": cf.category,
                "probability": cf.probability,
                "mobile_important": getattr(cf, 'mobile_important', False)
            }
            for cf in mobile_cash_flows
        ]
    }

def create_mobile_optimized_report_html(report_data: Dict[str, Any]) -> str:
    """Generate mobile-optimized HTML report"""
    
    mobile_html_template = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
        <title>{{ report_title }}</title>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
                margin: 0; 
                padding: 10px; 
                background: #f8fafc; 
                font-size: 16px;
                line-height: 1.5;
            }
            .container { 
                max-width: 100%; 
                margin: 0 auto; 
                background: white; 
                padding: 15px; 
                border-radius: 12px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            }
            .header { 
                text-align: center; 
                border-bottom: 2px solid #3B82F6; 
                padding-bottom: 15px; 
                margin-bottom: 20px; 
            }
            .logo { 
                font-size: 18px; 
                font-weight: bold; 
                color: #3B82F6; 
                margin-bottom: 5px; 
            }
            h1 { 
                color: #1F2937; 
                margin: 0; 
                font-size: 20px;
            }
            h2 { 
                color: #374151; 
                border-left: 4px solid #3B82F6; 
                padding-left: 10px; 
                font-size: 18px;
                margin-top: 25px;
            }
            .summary { 
                display: grid; 
                grid-template-columns: 1fr; 
                gap: 10px; 
                margin: 15px 0; 
            }
            @media (min-width: 480px) {
                .summary { grid-template-columns: repeat(2, 1fr); }
            }
            .summary-card { 
                background: #F8FAFC; 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 4px solid #10B981; 
                min-height: 80px;
            }
            .summary-card.warning { border-left-color: #F59E0B; }
            .summary-card.danger { border-left-color: #EF4444; }
            .summary-card h3 { 
                margin: 0 0 5px 0; 
                font-size: 12px; 
                color: #6B7280; 
                text-transform: uppercase; 
                font-weight: 600;
            }
            .summary-card .value { 
                font-size: 20px; 
                font-weight: bold; 
                color: #1F2937; 
            }
            .mobile-table {
                width: 100%;
                margin: 15px 0;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .mobile-table-row {
                padding: 15px;
                border-bottom: 1px solid #E5E7EB;
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            .mobile-table-row:last-child {
                border-bottom: none;
            }
            .mobile-table-header {
                font-weight: 600;
                color: #1F2937;
                font-size: 16px;
            }
            .mobile-table-data {
                color: #6B7280;
                font-size: 14px;
            }
            .status-adequate { color: #059669; font-weight: bold; }
            .status-low { color: #D97706; font-weight: bold; }
            .status-critical { color: #DC2626; font-weight: bold; }
            .status-excess { color: #7C3AED; font-weight: bold; }
            .recommendations { 
                background: #FEF3C7; 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 4px solid #F59E0B; 
                margin-top: 20px;
            }
            .recommendations h3 { 
                margin-top: 0; 
                color: #92400E; 
                font-size: 16px;
            }
            .recommendations ul { 
                margin: 10px 0; 
                padding-left: 20px;
            }
            .recommendations li { 
                margin: 8px 0; 
                line-height: 1.6;
            }
            .footer { 
                text-align: center; 
                margin-top: 25px; 
                padding-top: 15px; 
                border-top: 1px solid #E5E7EB; 
                color: #6B7280; 
                font-size: 12px; 
            }
            .date { 
                color: #6B7280; 
                font-size: 14px; 
            }
            .emoji {
                margin-right: 5px;
            }
            @media (max-width: 480px) {
                body { padding: 5px; font-size: 15px; }
                .container { padding: 10px; }
                h1 { font-size: 18px; }
                h2 { font-size: 16px; }
                .summary-card .value { font-size: 18px; }
                .mobile-table-row { padding: 12px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">💰 Financial AI Dashboard</div>
                <h1>{{ report_title }}</h1>
                <div class="date">{{ company_name }} • {{ generated_date }}</div>
            </div>
            
            {{ content }}
            
            <div class="footer">
                <p>📱 Мобильная версия отчета</p>
                <p>© 2025 Financial AI Dashboard</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    if report_data["report_type"] == "liquidity_daily":
        content = f"""
        <div class="summary">
            <div class="summary-card">
                <h3><span class="emoji">💰</span>Общий баланс</h3>
                <div class="value">{report_data['summary']['total_balance_kzt']:,.0f} ₸</div>
            </div>
            <div class="summary-card">
                <h3><span class="emoji">🏦</span>Счета</h3>
                <div class="value">{report_data['summary']['accounts_count']}</div>
            </div>
            <div class="summary-card {'warning' if report_data['summary']['liquidity_status'] in ['LOW', 'CRITICAL'] else ''}">
                <h3><span class="emoji">📊</span>Ликвидность</h3>
                <div class="value status-{report_data['summary']['liquidity_status'].lower()}">{report_data['summary']['liquidity_status']}</div>
            </div>
            <div class="summary-card">
                <h3><span class="emoji">💸</span>Чистый поток</h3>
                <div class="value">{report_data['summary']['net_cash_flow_30d']:,.0f} ₸</div>
            </div>
        </div>
        
        <h2>🏦 Банковские счета</h2>
        <div class="mobile-table">
            {chr(10).join([f'''
            <div class="mobile-table-row">
                <div class="mobile-table-header">{acc["name"]}</div>
                <div class="mobile-table-data">{acc["bank"]} • {acc["balance"]:,.0f} {acc["currency"]}</div>
                <div class="mobile-table-data">В тенге: {acc["balance_kzt"]:,.0f} ₸</div>
            </div>''' for acc in report_data["accounts"]])}
        </div>
        
        <h2>💸 Денежные потоки</h2>
        <div class="summary">
            <div class="summary-card">
                <h3><span class="emoji">📈</span>Поступления</h3>
                <div class="value">{report_data['cash_flows']['inflows']:,.0f} ₸</div>
            </div>
            <div class="summary-card">
                <h3><span class="emoji">📉</span>Платежи</h3>
                <div class="value">{report_data['cash_flows']['outflows']:,.0f} ₸</div>
            </div>
        </div>
        """
        
        if report_data.get("recommendations"):
            content += f"""
            <div class="recommendations">
                <h3>🎯 Рекомендации</h3>
                <ul>
                    {chr(10).join([f'<li>{rec}</li>' for rec in report_data["recommendations"]])}
                </ul>
            </div>
            """
        
        report_title = "📊 Отчет по ликвидности"
        
    elif report_data["report_type"] == "risk_weekly":
        content = f"""
        <div class="summary">
            <div class="summary-card {'danger' if report_data['summary']['overall_risk'] == 'HIGH' else 'warning' if report_data['summary']['overall_risk'] == 'MEDIUM' else ''}">
                <h3><span class="emoji">⚠️</span>Общий риск</h3>
                <div class="value">{report_data['summary']['overall_risk']}</div>
            </div>
            <div class="summary-card">
                <h3><span class="emoji">📋</span>Всего рисков</h3>
                <div class="value">{report_data['summary']['total_risks']}</div>
            </div>
            <div class="summary-card danger">
                <h3><span class="emoji">🚨</span>Высоких</h3>
                <div class="value">{report_data['summary']['high_risks']}</div>
            </div>
            <div class="summary-card warning">
                <h3><span class="emoji">⚡</span>Средних</h3>
                <div class="value">{report_data['summary']['medium_risks']}</div>
            </div>
        </div>
        
        <h2>⚠️ Выявленные риски</h2>
        <div class="mobile-table">
            {chr(10).join([f'''
            <div class="mobile-table-row">
                <div class="mobile-table-header">{risk["description"]}</div>
                <div class="mobile-table-data">Уровень: <span class="status-{risk["level"].lower()}">{risk["level"]}</span></div>
                <div class="mobile-table-data">{risk["recommendation"]}</div>
            </div>''' for risk in report_data["identified_risks"]])}
        </div>
        """
        
        report_title = "⚠️ Анализ рисков"
        
    else:  # cashflow_monthly
        content = f"""
        <div class="summary">
            <div class="summary-card">
                <h3><span class="emoji">📈</span>Поступления</h3>
                <div class="value">{report_data['summary']['total_inflows']:,.0f} ₸</div>
            </div>
            <div class="summary-card">
                <h3><span class="emoji">📉</span>Платежи</h3>
                <div class="value">{report_data['summary']['total_outflows']:,.0f} ₸</div>
            </div>
            <div class="summary-card">
                <h3><span class="emoji">💰</span>Чистый поток</h3>
                <div class="value">{report_data['summary']['net_cash_flow']:,.0f} ₸</div>
            </div>
            <div class="summary-card">
                <h3><span class="emoji">📅</span>Недель</h3>
                <div class="value">{report_data['summary']['weeks_analyzed']}</div>
            </div>
        </div>
        
        <h2>📊 Еженедельная разбивка</h2>
        <div class="mobile-table">
            {chr(10).join([f'''
            <div class="mobile-table-row">
                <div class="mobile-table-header">Неделя {week}</div>
                <div class="mobile-table-data">Поступления: {data["inflows"]:,.0f} ₸</div>
                <div class="mobile-table-data">Платежи: {data["outflows"]:,.0f} ₸</div>
                <div class="mobile-table-data">Чистый поток: {data["net"]:,.0f} ₸</div>
            </div>''' for week, data in report_data["weekly_breakdown"].items()])}
        </div>
        """
        
        report_title = "💸 Отчет по денежным потокам"
    
    template = Template(mobile_html_template)
    
    return template.render(
        report_title=report_title,
        company_name=report_data["company_name"],
        generated_date=datetime.fromisoformat(report_data["generated_at"]).strftime("%d.%m.%Y %H:%M"),
        content=content
    )

async def generate_and_send_report(report_id: str, db: Session, mobile_optimized: bool = False):
    """Generate and send report with mobile optimization"""
    try:
        start_time = datetime.utcnow()
        
        # Get report configuration
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report or not report.is_active:
            logger.warning(f"Report {report_id} not found or inactive")
            return
        
        # Generate report data with mobile optimization
        if report.report_type == "liquidity_daily":
            report_data = generate_liquidity_report(str(report.user_id), db, mobile_optimized)
        elif report.report_type == "risk_weekly":
            report_data = generate_risk_report(str(report.user_id), db, mobile_optimized)
        elif report.report_type == "cashflow_monthly":
            report_data = generate_cashflow_report(str(report.user_id), db, mobile_optimized)
        else:
            logger.error(f"Unknown report type: {report.report_type}")
            return
        
        # Generate HTML with mobile optimization
        if mobile_optimized:
            html_content = create_mobile_optimized_report_html(report_data)
        else:
            html_content = create_report_html(report_data)
        
        # Save report to file
        reports_dir = Path("static/reports")
        reports_dir.mkdir(exist_ok=True)
        
        suffix = "_mobile" if mobile_optimized else ""
        file_name = f"{report.report_type}_{report.user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{suffix}.html"
        file_path = reports_dir / file_name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        file_size = os.path.getsize(file_path)
        generation_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Save to history
        history = ReportHistory(
            report_id=report.id,
            user_id=report.user_id,
            file_path=str(file_path),
            file_size=file_size,
            generation_time_ms=generation_time,
            success=True,
            mobile_optimized=mobile_optimized
        )
        db.add(history)
        
        # Update report
        report.last_generated = datetime.utcnow()
        report.generation_count += 1
        
        # Calculate next scheduled time
        if report.schedule and report.schedule != "manual":
            if report.schedule == "daily_8am":
                next_run = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
                if next_run <= datetime.utcnow():
                    next_run += timedelta(days=1)
                report.next_scheduled = next_run
            elif report.schedule == "weekly_monday":
                next_run = datetime.utcnow() + timedelta(days=7)
                report.next_scheduled = next_run
            elif report.schedule == "monthly_1st":
                next_run = datetime.utcnow().replace(day=1) + timedelta(days=32)
                next_run = next_run.replace(day=1)
                report.next_scheduled = next_run
        
        db.commit()
        
        # Send email
        if report.recipients:
            subject = f"📱 Финансовый отчет: {report.name}" if mobile_optimized else f"Финансовый отчет: {report.name}"
            send_email_with_attachment(
                to_emails=report.recipients,
                subject=subject,
                html_content=html_content,
                attachment_path=str(file_path)
            )
        
        logger.info(f"Report {report_id} generated successfully in {generation_time}ms (mobile: {mobile_optimized})")
        
    except Exception as e:
        logger.error(f"Failed to generate report {report_id}: {str(e)}")
        
        # Save error to history
        error_history = ReportHistory(
            report_id=report_id,
            user_id=report.user_id if report else None,
            success=False,
            error_message=str(e),
            mobile_optimized=mobile_optimized
        )
        db.add(error_history)
        db.commit()

def send_email_with_attachment(to_emails: List[str], subject: str, html_content: str, attachment_path: str = None):
    """Send email with HTML content and optional attachment"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email send")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = subject
        
        # Add HTML content
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}',
                )
                msg.attach(part)
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_emails}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

# =============================================================================
# Demo User Creation with Mobile Data
# =============================================================================

async def create_demo_user(db: Session):
    """Create demo user with test data and mobile optimizations"""
    
    # Check if demo user already exists
    demo_user = db.query(User).filter(User.email == "demo@financial-ai.com").first()
    if demo_user:
        return demo_user
    
    # Create demo user with mobile settings
    demo_user = User(
        email="demo@financial-ai.com",
        name="Demo CFO",
        hashed_password=get_password_hash("demo123"),
        role="demo",
        company="ТОО КазахТрейд ДЕМО",
        phone="+7 777 123 4567",
        subscription_plan="professional",
        is_active=True,
        is_verified=True,
        mobile_app_enabled=True,
        push_notifications_enabled=True
    )
    db.add(demo_user)
    db.flush()  # To get the ID
    
    # Create demo company with mobile settings
    demo_company = Company(
        user_id=demo_user.id,
        name="ТОО КазахТрейд ДЕМО",
        tax_id="123456789012",
        base_currency="KZT",
        industry="Торговля",
        country="Kazakhstan",
        mobile_settings={
            "dashboard_layout": "compact",
            "chart_type": "simplified",
            "notifications_enabled": True
        }
    )
    db.add(demo_company)
    
    # Create demo API keys
    demo_openai_key = APIKey(
        user_id=demo_user.id,
        service="openai",
        key_name="Demo OpenAI Key",
        encrypted_key=encrypt_api_key("sk-demo-key-not-real"),
        is_active=True,
        usage_count=45,
        last_used=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(demo_openai_key)
    
    demo_telegram_key = APIKey(
        user_id=demo_user.id,
        service="telegram",
        key_name="Demo Telegram Bot",
        encrypted_key=encrypt_api_key("1234567890:demo-token-not-real"),
        is_active=True,
        usage_count=12,
        last_used=datetime.utcnow() - timedelta(hours=1)
    )
    db.add(demo_telegram_key)
    
    # Create demo bank accounts with mobile priorities
    accounts_data = [
        {"name": "Основной операционный счет", "bank": "Halyk Bank", "balance": 125300000, "currency": "KZT", "type": "operational", "mobile_priority": 1},
        {"name": "Валютный счет USD", "bank": "Kaspi Bank", "balance": 248500, "currency": "USD", "type": "currency", "mobile_priority": 2},
        {"name": "Резервный фонд", "bank": "Forte Bank", "balance": 45200000, "currency": "KZT", "type": "reserve", "mobile_priority": 3},
        {"name": "Евро счет", "bank": "Halyk Bank", "balance": 85600, "currency": "EUR", "type": "currency", "mobile_priority": 4},
        {"name": "Операционный счет 2", "bank": "Kaspi Bank", "balance": 67800000, "currency": "KZT", "type": "operational", "mobile_priority": 5}
    ]
    
    for acc_data in accounts_data:
        account = BankAccount(
            user_id=demo_user.id,
            name=acc_data["name"],
            bank=acc_data["bank"],
            balance=acc_data["balance"],
            currency=acc_data["currency"],
            account_type=acc_data["type"],
            is_active=True,
            mobile_priority=acc_data["mobile_priority"]
        )
        db.add(account)
        db.flush()
        
        # Add some cash flows for this account with mobile importance
        base_date = datetime.utcnow()
        for i in range(5):
            # Inflow
            is_important = i < 2  # First 2 are important for mobile
            inflow = CashFlow(
                user_id=demo_user.id,
                account_id=account.id,
                amount=random.randint(5000000, 25000000),
                currency=acc_data["currency"],
                description=f"Поступление от клиентов #{i+1}",
                category="sales",
                planned_date=base_date + timedelta(days=random.randint(1, 30)),
                probability=0.8 + random.random() * 0.2,
                status="planned",
                flow_type="inflow",
                mobile_important=is_important
            )
            db.add(inflow)
            
            # Outflow
            outflow = CashFlow(
                user_id=demo_user.id,
                account_id=account.id,
                amount=-random.randint(3000000, 18000000),
                currency=acc_data["currency"],
                description=f"Платеж поставщикам #{i+1}",
                category="purchases",
                planned_date=base_date + timedelta(days=random.randint(2, 25)),
                probability=0.9,
                status="planned",
                flow_type="outflow",
                mobile_important=is_important
            )
            db.add(outflow)
    
    # Create demo AI consultations with device tracking
    consultations_data = [
        {
            "question": "Какая текущая ликвидность компании?",
            "response": "На текущий момент ваша компания имеет адекватный уровень ликвидности. Общий баланс составляет 245.75 млн тенге, что покрывает операционные потребности на ближайшие 45 дней. Рекомендуется поддерживать текущий уровень и мониторить крупные платежи.",
            "tokens_used": 156,
            "processing_time_ms": 2300,
            "rating": 5,
            "device_type": "mobile"
        },
        {
            "question": "Стоит ли размещать избыточную ликвидность?",
            "response": "Учитывая прогноз превышения оптимального уровня ликвидности с 20 сентября, рекомендуется рассмотреть размещение 15-20 млн тенге в краткосрочные депозиты сроком на 1-3 месяца. Это позволит получить дополнительный доход при сохранении доступности средств.",
            "tokens_used": 143,
            "processing_time_ms": 3100,
            "rating": 4,
            "device_type": "web"
        },
        {
            "question": "Какие риски кассовых разрывов?",
            "response": "Анализ денежных потоков показывает низкий риск кассовых разрывов в ближайшие 30 дней. Критическая точка может наступить в районе 15 октября, когда планируются крупные платежи поставщикам. Рекомендуется подготовить резерв в 25-30 млн тенге.",
            "tokens_used": 178,
            "processing_time_ms": 2800,
            "rating": 5,
            "device_type": "tablet"
        }
    ]
    
    for i, cons_data in enumerate(consultations_data):
        consultation = AIConsultation(
            user_id=demo_user.id,
            question=cons_data["question"],
            response=cons_data["response"],
            tokens_used=cons_data["tokens_used"],
            processing_time_ms=cons_data["processing_time_ms"],
            rating=cons_data["rating"],
            session_id=f"demo_session_{i+1}",
            device_type=cons_data["device_type"],
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
        )
        db.add(consultation)
    
    # Create demo reports with mobile settings
    reports_data = [
        {
            "name": "Ежедневный отчет по ликвидности",
            "description": "Автоматический анализ состояния ликвидности компании с прогнозом на 30 дней",
            "report_type": "liquidity_daily",
            "schedule": "daily_8am",
            "recipients": ["demo@financial-ai.com", "finance@kazakhtrade.kz"],
            "mobile_enabled": True
        },
        {
            "name": "Еженедельный анализ рисков",
            "description": "Детальный анализ финансовых рисков и рекомендации по их минимизации",
            "report_type": "risk_weekly",
            "schedule": "weekly_monday",
            "recipients": ["demo@financial-ai.com"],
            "mobile_enabled": True
        },
        {
            "name": "Месячный отчет по денежным потокам",
            "description": "Подробный анализ денежных потоков с трендами и прогнозами",
            "report_type": "cashflow_monthly",
            "schedule": "monthly_1st",
            "recipients": ["demo@financial-ai.com", "ceo@kazakhtrade.kz"],
            "mobile_enabled": False  # Only desktop version for detailed report
        }
    ]
    
    for rep_data in reports_data:
        report = Report(
            user_id=demo_user.id,
            name=rep_data["name"],
            description=rep_data["description"],
            report_type=rep_data["report_type"],
            schedule=rep_data["schedule"],
            recipients=rep_data["recipients"],
            is_active=True,
            mobile_enabled=rep_data["mobile_enabled"],
            last_generated=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
            generation_count=random.randint(5, 25)
        )
        db.add(report)
    
    # Create demo notifications with mobile push tracking
    notifications_data = [
        {
            "title": "📱 Прогноз обновлен",
            "message": "Получены новые данные по валютным курсам. Прогноз ликвидности пересчитан.",
            "type": "info",
            "is_read": False,
            "mobile_push_sent": True
        },
        {
            "title": "📧 Отчет сгенерирован",
            "message": "Ежедневный отчет по ликвидности успешно создан и отправлен.",
            "type": "success",
            "is_read": True,
            "mobile_push_sent": True
        },
        {
            "title": "⚠️ Требует внимания",
            "message": "Баланс на USD счете приближается к минимальному лимиту.",
            "type": "warning",
            "is_read": False,
            "mobile_push_sent": False
        }
    ]
    
    for notif_data in notifications_data:
        notification = Notification(
            user_id=demo_user.id,
            title=notif_data["title"],
            message=notif_data["message"],
            notification_type=notif_data["type"],
            is_read=notif_data["is_read"],
            mobile_push_sent=notif_data["mobile_push_sent"],
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        db.add(notification)
    
    db.commit()
    logger.info("Demo user and test data with mobile optimizations created successfully")
    return demo_user

# =============================================================================
# API Routes (Enhanced for Mobile)
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application with mobile detection"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "mobile_support": True,
        "version": "2.0.0"
    }

@app.post("/api/init-demo")
async def initialize_demo_data(db: Session = Depends(get_db)):
    """Initialize demo user and test data with mobile optimizations"""
    try:
        demo_user = await create_demo_user(db)
        return {
            "message": "Demo data with mobile optimizations initialized", 
            "demo_email": "demo@financial-ai.com", 
            "demo_password": "demo123",
            "mobile_supported": True
        }
    except Exception as e:
        logger.error(f"Failed to initialize demo data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize demo data")

# Authentication routes with mobile device detection
@app.post("/api/auth/register")
async def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user with mobile device detection"""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_agent = request.headers.get("user-agent", "")
    is_mobile = detect_mobile_device(user_agent)
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=user.role,
        company=user.company,
        phone=user.phone,
        mobile_app_enabled=is_mobile  # Auto-enable for mobile users
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create user session
    session_token = str(uuid.uuid4())
    session = UserSession(
        user_id=db_user.id,
        session_token=session_token,
        user_agent=user_agent,
        ip_address=request.client.host,
        is_mobile=is_mobile,
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.add(session)
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_mobile": is_mobile,
        "user": UserResponse(
            id=str(db_user.id),
            email=db_user.email,
            name=db_user.name,
            role=db_user.role,
            company=db_user.company,
            subscription_plan=db_user.subscription_plan,
            avatar_url=db_user.avatar_url,
            is_verified=db_user.is_verified,
            two_factor_enabled=db_user.two_factor_enabled,
            mobile_app_enabled=db_user.mobile_app_enabled,
            timezone=db_user.timezone,
            language=db_user.language,
            created_at=db_user.created_at,
            last_login=db_user.last_login
        )
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Login user with mobile device detection"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_agent = request.headers.get("user-agent", "")
    is_mobile = detect_mobile_device(user_agent)
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create user session
    session_token = str(uuid.uuid4())
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        device_info=user_data.device_info,
        user_agent=user_agent,
        ip_address=request.client.host,
        is_mobile=is_mobile,
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.add(session)
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_mobile": is_mobile,
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            company=user.company,
            subscription_plan=user.subscription_plan,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            two_factor_enabled=user.two_factor_enabled,
            mobile_app_enabled=user.mobile_app_enabled,
            timezone=user.timezone,
            language=user.language,
            created_at=user.created_at,
            last_login=user.last_login
        )
    }

# Mobile-optimized dashboard endpoint
@app.get("/api/dashboard")
async def get_dashboard_data(
    request: Request,
    mobile: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard data with mobile optimization"""
    user_agent = request.headers.get("user-agent", "")
    is_mobile_request = mobile or detect_mobile_device(user_agent)
    
    # Get accounts with mobile priority ordering
    accounts_query = db.query(BankAccount).filter(
        BankAccount.user_id == current_user.id,
        BankAccount.is_active == True
    )
    
    if is_mobile_request:
        accounts = accounts_query.order_by(BankAccount.mobile_priority.desc().nulls_last()).limit(3).all()
    else:
        accounts = accounts_query.all()
    
    # Calculate total balance in KZT
    total_balance = 0
    for account in accounts:
        if account.currency == "KZT":
            total_balance += account.balance
        elif account.currency == "USD":
            total_balance += account.balance * 480  # Mock exchange rate
        elif account.currency == "EUR":
            total_balance += account.balance * 520  # Mock exchange rate
    
    # Get recent cash flows with mobile importance
    cash_flows_query = db.query(CashFlow).filter(
        CashFlow.user_id == current_user.id,
        CashFlow.planned_date >= datetime.utcnow() - timedelta(days=7)
    )
    
    if is_mobile_request:
        recent_cash_flows = cash_flows_query.filter(
            CashFlow.mobile_important == True
        ).order_by(CashFlow.planned_date.desc()).limit(5).all()
    else:
        recent_cash_flows = cash_flows_query.order_by(CashFlow.planned_date.desc()).limit(10).all()
    
    # Calculate cash flow for this month
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cash_flow_this_month = db.query(func.sum(CashFlow.amount)).filter(
        CashFlow.user_id == current_user.id,
        CashFlow.planned_date >= current_month,
        CashFlow.flow_type == "inflow"
    ).scalar() or 0
    
    # Mock liquidity status calculation
    liquidity_status = "ADEQUATE"
    if total_balance < 50000000:  # 50M KZT
        liquidity_status = "LOW"
    elif total_balance > 200000000:  # 200M KZT
        liquidity_status = "EXCESS"
        
    risk_level = "LOW"
    if total_balance < 30000000:  # 30M KZT
        risk_level = "HIGH"
    elif total_balance < 100000000:  # 100M KZT
        risk_level = "MEDIUM"
    
    # Get notifications (prioritize unread for mobile)
    notifications_query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    
    if is_mobile_request:
        notifications = notifications_query.filter(
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).limit(3).all()
    else:
        notifications = notifications_query.order_by(Notification.created_at.desc()).limit(5).all()
    
    return {
        "totalBalance": total_balance,
        "currency": "KZT",
        "cashFlowThisMonth": cash_flow_this_month,
        "liquidityStatus": liquidity_status,
        "riskLevel": risk_level,
        "accountsCount": len(accounts),
        "lastUpdated": datetime.utcnow().isoformat(),
        "isMobile": is_mobile_request,
        "accounts": [
            {
                "id": str(acc.id),
                "name": acc.name,
                "bank": acc.bank,
                "balance": acc.balance,
                "currency": acc.currency,
                "account_type": acc.account_type,
                "mobile_priority": getattr(acc, 'mobile_priority', 0),
                "lastTransaction": acc.updated_at.isoformat()
            }
            for acc in accounts
        ],
        "recentCashFlows": [
            {
                "id": str(cf.id),
                "amount": cf.amount,
                "description": cf.description,
                "type": cf.flow_type,
                "date": cf.planned_date.isoformat(),
                "mobile_important": getattr(cf, 'mobile_important', False)
            }
            for cf in recent_cash_flows
        ],
        "notifications": [
            {
                "id": str(n.id),
                "title": n.title,
                "message": n.message,
                "type": n.notification_type,
                "isRead": n.is_read,
                "createdAt": n.created_at.isoformat()
            }
            for n in notifications
        ]
    }

# Mobile-optimized AI consultation endpoint
@app.post("/api/ai/consult")
async def create_ai_consultation(
    consultation: AIConsultationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create AI consultation with mobile device detection"""
    user_agent = request.headers.get("user-agent", "")
    is_mobile = detect_mobile_device(user_agent)
    device_type = consultation.device_type or ("mobile" if is_mobile else "web")
    
    # Mock AI response (in real implementation, call OpenAI API)
    mock_responses = [
        "На основе анализа ваших банковских счетов, текущий уровень ликвидности составляет 245.7 млн тенге. Это адекватный уровень для покрытия операционных потребностей на ближайшие 45 дней.",
        "Анализ денежных потоков показывает положительный тренд. Рекомендуется рассмотреть размещение избыточных средств в краткосрочные инвестиции.",
        "Выявлен риск концентрации средств в одном банке. Рекомендуется диверсификация для снижения банковских рисков."
    ]
    
    response_text = random.choice(mock_responses)
    
    # Shorten response for mobile
    if is_mobile and len(response_text) > 200:
        response_text = response_text[:197] + "..."
    
    consultation_record = AIConsultation(
        user_id=current_user.id,
        question=consultation.question,
        response=response_text,
        context_data=consultation.context_data,
        tokens_used=random.randint(50, 200),
        processing_time_ms=random.randint(1000, 3000),
        session_id=str(uuid.uuid4()),
        device_type=device_type
    )
    
    db.add(consultation_record)
    db.commit()
    db.refresh(consultation_record)
    
    return {
        "id": str(consultation_record.id),
        "question": consultation_record.question,
        "response": consultation_record.response,
        "tokens_used": consultation_record.tokens_used,
        "processing_time_ms": consultation_record.processing_time_ms,
        "device_type": consultation_record.device_type,
        "created_at": consultation_record.created_at.isoformat()
    }

# Mobile-optimized reports endpoints
@app.post("/api/reports")
async def create_report(
    report: MobileOptimizedReportCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new report with mobile optimization"""
    user_agent = request.headers.get("user-agent", "")
    is_mobile = detect_mobile_device(user_agent)
    
    db_report = Report(
        user_id=current_user.id,
        name=report.name,
        description=report.description,
        report_type=report.report_type,
        parameters=report.parameters,
        schedule=report.schedule,
        recipients=report.recipients,
        is_active=True,
        mobile_enabled=report.mobile_enabled or is_mobile
    )
    
    # Set next scheduled time if not manual
    if report.schedule and report.schedule != "manual":
        if report.schedule == "daily_8am":
            next_run = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
            if next_run <= datetime.utcnow():
                next_run += timedelta(days=1)
            db_report.next_scheduled = next_run
        elif report.schedule == "weekly_monday":
            days_ahead = 0 - datetime.utcnow().weekday()  # Monday is 0
            if days_ahead <= 0:
                days_ahead += 7
            next_run = datetime.utcnow() + timedelta(days=days_ahead)
            db_report.next_scheduled = next_run.replace(hour=9, minute=0, second=0, microsecond=0)
        elif report.schedule == "monthly_1st":
            next_run = datetime.utcnow().replace(day=1, hour=9, minute=0, second=0, microsecond=0)
            next_run = next_run + timedelta(days=32)
            next_run = next_run.replace(day=1)
            db_report.next_scheduled = next_run
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return {
        "id": str(db_report.id),
        "name": db_report.name,
        "description": db_report.description,
        "report_type": db_report.report_type,
        "schedule": db_report.schedule,
        "recipients": db_report.recipients,
        "is_active": db_report.is_active,
        "mobile_enabled": db_report.mobile_enabled,
        "last_generated": db_report.last_generated,
        "next_scheduled": db_report.next_scheduled,
        "generation_count": db_report.generation_count,
        "created_at": db_report.created_at
    }

@app.post("/api/reports/{report_id}/generate")
async def generate_report(
    report_id: str,
    mobile: bool = False,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate report manually with mobile optimization"""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    user_agent = request.headers.get("user-agent", "")
    is_mobile_request = mobile or detect_mobile_device(user_agent)
    mobile_optimized = is_mobile_request and report.mobile_enabled
    
    # Run report generation in background
    background_tasks.add_task(generate_and_send_report, report_id, db, mobile_optimized)
    
    return {
        "message": "Report generation started", 
        "report_id": report_id,
        "mobile_optimized": mobile_optimized
    }

# Scheduled report generation (run in background)
def check_and_run_scheduled_reports():
    """Check for scheduled reports and run them"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        scheduled_reports = db.query(Report).filter(
            Report.is_active == True,
            Report.next_scheduled <= now,
            Report.schedule != "manual"
        ).all()
        
        for report in scheduled_reports:
            logger.info(f"Running scheduled report: {report.name} (ID: {report.id})")
            
            # Generate both regular and mobile versions if mobile is enabled
            asyncio.run(generate_and_send_report(str(report.id), db, False))
            
            if report.mobile_enabled:
                asyncio.run(generate_and_send_report(str(report.id), db, True))
            
    except Exception as e:
        logger.error(f"Error in scheduled report check: {str(e)}")
    finally:
        db.close()

# Schedule the report checker to run every hour
schedule.every().hour.do(check_and_run_scheduled_reports)

def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Start scheduler thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    import uvicorn
    
    # Create reports directory
    Path("static/reports").mkdir(exist_ok=True, parents=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
