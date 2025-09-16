# Обновленная база данных с поддержкой пользовательских RSS каналов
-- PostgreSQL инициализация для Financial AI Dashboard Enhanced

-- Включение расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Пользователи системы
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    company VARCHAR(255),
    phone VARCHAR(50),
    subscription_plan VARCHAR(50) DEFAULT 'professional',
    is_active BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'Asia/Almaty',
    language VARCHAR(10) DEFAULT 'ru',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Банковские счета
CREATE TABLE IF NOT EXISTS bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    bank VARCHAR(255) NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'KZT',
    account_type VARCHAR(50) DEFAULT 'operational',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Курсы валют из НБ РК
CREATE TABLE IF NOT EXISTS exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_currency VARCHAR(10) NOT NULL,
    to_currency VARCHAR(10) NOT NULL,
    rate DECIMAL(10,4) NOT NULL,
    date TIMESTAMP NOT NULL,
    source VARCHAR(50) DEFAULT 'NBK',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Финансовые новости (обновленная)
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary TEXT,
    url VARCHAR(1000),
    published_at TIMESTAMP,
    source VARCHAR(100),
    category VARCHAR(50) DEFAULT 'financial',
    sentiment VARCHAR(20), -- positive, negative, neutral
    risk_level VARCHAR(20), -- low, medium, high
    relevance_score DECIMAL(3,2) DEFAULT 0.50, -- 0.00-1.00 AI оценка релевантности
    ai_tags JSONB, -- AI теги для категоризации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- НОВАЯ ТАБЛИЦА: Пользовательские RSS каналы
CREATE TABLE IF NOT EXISTS user_rss_feeds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- Название канала
    url VARCHAR(1000) NOT NULL, -- RSS URL
    description TEXT, -- Описание канала
    category VARCHAR(100) DEFAULT 'financial', -- Категория (financial, tech, oil, etc.)
    priority INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 5), -- Приоритет 1-5
    is_active BOOLEAN DEFAULT TRUE,
    auto_analysis BOOLEAN DEFAULT TRUE, -- Автоматический AI анализ
    keywords JSONB, -- Ключевые слова для фильтрации
    last_fetched TIMESTAMP,
    fetch_frequency VARCHAR(20) DEFAULT 'hourly', -- hourly, daily, weekly
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    articles_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- НОВАЯ ТАБЛИЦА: AI анализ RSS контента
CREATE TABLE IF NOT EXISTS rss_content_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rss_feed_id UUID REFERENCES user_rss_feeds(id) ON DELETE CASCADE,
    article_id UUID REFERENCES news_articles(id) ON DELETE SET NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- AI анализ контента
    financial_relevance DECIMAL(3,2) CHECK (financial_relevance >= 0 AND financial_relevance <= 1), -- 0-1 релевантность для финансов
    risk_indicators JSONB, -- Массив индикаторов рисков
    sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1), -- -1 to 1 (негативный - позитивный)
    key_topics JSONB, -- Основные темы статьи
    market_impact VARCHAR(20) DEFAULT 'low' CHECK (market_impact IN ('low', 'medium', 'high')), -- Влияние на рынок
    recommendations TEXT, -- AI рекомендации
    
    -- Метаданные анализа
    processing_time_ms INTEGER,
    ai_confidence DECIMAL(3,2) CHECK (ai_confidence >= 0 AND ai_confidence <= 1), -- Уверенность AI в анализе
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI консультации (обновленная)
CREATE TABLE IF NOT EXISTS ai_consultations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    context_data JSONB,
    rss_sources_used JSONB, -- НОВОЕ: RSS источники использованные в ответе
    session_id VARCHAR(255),
    source VARCHAR(50) DEFAULT 'web', -- web, n8n, telegram
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Отчеты (обновленная)
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    content TEXT,
    file_path VARCHAR(500),
    rss_feeds_included JSONB, -- НОВОЕ: RSS каналы включенные в отчет
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи webhook'ов для интеграции с n8n
CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL, -- n8n, telegram, etc
    event_type VARCHAR(100),
    payload JSONB,
    response JSONB,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Денежные потоки (для прогнозирования)
CREATE TABLE IF NOT EXISTS cash_flows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID REFERENCES bank_accounts(id) ON DELETE CASCADE,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'KZT',
    description TEXT,
    category VARCHAR(100),
    planned_date TIMESTAMP NOT NULL,
    actual_date TIMESTAMP,
    probability DECIMAL(3,2) DEFAULT 1.00,
    status VARCHAR(50) DEFAULT 'planned', -- planned, actual, cancelled
    flow_type VARCHAR(20) NOT NULL CHECK (flow_type IN ('inflow', 'outflow')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Уведомления для пользователей
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) DEFAULT 'info', -- info, warning, error, success
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API ключи пользователей
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    service VARCHAR(100) NOT NULL, -- openai, telegram, etc
    key_name VARCHAR(255) NOT NULL,
    encrypted_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации запросов

-- Пользователи
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_plan);

-- Банковские счета
CREATE INDEX IF NOT EXISTS idx_bank_accounts_user_id ON bank_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_active ON bank_accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_currency ON bank_accounts(currency);

-- Курсы валют
CREATE INDEX IF NOT EXISTS idx_exchange_rates_date ON exchange_rates(date DESC);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_currency ON exchange_rates(from_currency, to_currency);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_source ON exchange_rates(source);

-- Новости
CREATE INDEX IF NOT EXISTS idx_news_articles_date ON news_articles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source);
CREATE INDEX IF NOT EXISTS idx_news_articles_category ON news_articles(category);
CREATE INDEX IF NOT EXISTS idx_news_articles_sentiment ON news_articles(sentiment);
CREATE INDEX IF NOT EXISTS idx_news_articles_relevance ON news_articles(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_title_trgm ON news_articles USING gin(title gin_trgm_ops);

-- RSS каналы пользователей
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_user_id ON user_rss_feeds(user_id);
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_active ON user_rss_feeds(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_category ON user_rss_feeds(category);
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_priority ON user_rss_feeds(priority DESC);
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_frequency ON user_rss_feeds(fetch_frequency);
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_last_fetched ON user_rss_feeds(last_fetched);

-- RSS анализ контента
CREATE INDEX IF NOT EXISTS idx_rss_content_analysis_user_id ON rss_content_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_rss_content_analysis_feed_id ON rss_content_analysis(rss_feed_id);
CREATE INDEX IF NOT EXISTS idx_rss_content_analysis_date ON rss_content_analysis(analysis_date DESC);
CREATE INDEX IF NOT EXISTS idx_rss_content_analysis_relevance ON rss_content_analysis(financial_relevance DESC);
CREATE INDEX IF NOT EXISTS idx_rss_content_analysis_sentiment ON rss_content_analysis(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_rss_content_analysis_impact ON rss_content_analysis(market_impact);

-- AI консультации
CREATE INDEX IF NOT EXISTS idx_ai_consultations_user_id ON ai_consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_consultations_date ON ai_consultations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_consultations_source ON ai_consultations(source);
CREATE INDEX IF NOT EXISTS idx_ai_consultations_session ON ai_consultations(session_id);

-- Отчеты
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(generated_at DESC);

-- Webhook логи
CREATE INDEX IF NOT EXISTS idx_webhook_logs_source ON webhook_logs(source);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_date ON webhook_logs(processed_at DESC);

-- Денежные потоки
CREATE INDEX IF NOT EXISTS idx_cash_flows_user_id ON cash_flows(user_id);
CREATE INDEX IF NOT EXISTS idx_cash_flows_account_id ON cash_flows(account_id);
CREATE INDEX IF NOT EXISTS idx_cash_flows_date ON cash_flows(planned_date);
CREATE INDEX IF NOT EXISTS idx_cash_flows_type ON cash_flows(flow_type);

-- Уведомления
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;

-- API ключи
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_service ON api_keys(service);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- Функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления
CREATE TRIGGER update_bank_accounts_updated_at 
    BEFORE UPDATE ON bank_accounts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_rss_feeds_updated_at 
    BEFORE UPDATE ON user_rss_feeds 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Представления для удобных запросов

-- Последние курсы валют
CREATE OR REPLACE VIEW latest_exchange_rates AS
SELECT DISTINCT ON (from_currency, to_currency)
    from_currency,
    to_currency,
    rate,
    date,
    source
FROM exchange_rates
ORDER BY from_currency, to_currency, date DESC;

-- Сводка по пользователю с RSS
CREATE OR REPLACE VIEW user_dashboard_summary AS
SELECT 
    u.id,
    u.name,
    u.company,
    u.subscription_plan,
    COUNT(DISTINCT ba.id) as accounts_count,
    COALESCE(SUM(ba.balance), 0) as total_balance_kzt,
    COUNT(DISTINCT CASE WHEN n.is_read = FALSE THEN n.id END) as unread_notifications,
    COUNT(DISTINCT CASE WHEN rss.is_active = TRUE THEN rss.id END) as active_rss_feeds,
    MAX(ac.created_at) as last_consultation,
    MAX(rss.last_fetched) as last_rss_update
FROM users u
LEFT JOIN bank_accounts ba ON u.id = ba.user_id AND ba.is_active = TRUE AND ba.currency = 'KZT'
LEFT JOIN notifications n ON u.id = n.user_id
LEFT JOIN ai_consultations ac ON u.id = ac.user_id
LEFT JOIN user_rss_feeds rss ON u.id = rss.user_id
GROUP BY u.id, u.name, u.company, u.subscription_plan;

-- Статистика RSS каналов пользователя
CREATE OR REPLACE VIEW user_rss_stats AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    COUNT(rss.id) as total_rss_feeds,
    COUNT(CASE WHEN rss.is_active = TRUE THEN 1 END) as active_feeds,
    COUNT(CASE WHEN rss.error_count > 0 THEN 1 END) as feeds_with_errors,
    AVG(rss.priority) as avg_priority,
    SUM(rss.articles_count) as total_articles_processed,
    COUNT(DISTINCT rss.category) as categories_count
FROM users u
LEFT JOIN user_rss_feeds rss ON u.id = rss.user_id
GROUP BY u.id, u.name;

-- Топ RSS источники по релевантности
CREATE OR REPLACE VIEW top_rss_sources AS
SELECT 
    rss.name,
    rss.category,
    rss.url,
    COUNT(analysis.id) as analysis_count,
    AVG(analysis.financial_relevance) as avg_relevance,
    AVG(analysis.sentiment_score) as avg_sentiment,
    COUNT(CASE WHEN analysis.market_impact = 'high' THEN 1 END) as high_impact_count
FROM user_rss_feeds rss
LEFT JOIN rss_content_analysis analysis ON rss.id = analysis.rss_feed_id
WHERE rss.is_active = TRUE 
    AND analysis.analysis_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY rss.id, rss.name, rss.category, rss.url
HAVING COUNT(analysis.id) > 0
ORDER BY avg_relevance DESC, analysis_count DESC
LIMIT 20;

-- Последние финансовые новости с RSS анализом
CREATE OR REPLACE VIEW recent_financial_news_with_rss AS
SELECT 
    n.title,
    n.content,
    n.url,
    n.source,
    n.sentiment,
    n.created_at,
    analysis.financial_relevance,
    analysis.market_impact,
    analysis.key_topics,
    rss.name as rss_feed_name,
    rss.category as rss_category
FROM news_articles n
LEFT JOIN rss_content_analysis analysis ON n.id = analysis.article_id
LEFT JOIN user_rss_feeds rss ON analysis.rss_feed_id = rss.id
WHERE n.created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY n.created_at DESC, analysis.financial_relevance DESC NULLS LAST
LIMIT 50;

-- Функция для получения RSS анализа пользователя
CREATE OR REPLACE FUNCTION get_user_rss_insights(user_uuid UUID, days_back INTEGER DEFAULT 7)
RETURNS TABLE (
    topic TEXT,
    mention_count BIGINT,
    avg_relevance NUMERIC,
    avg_sentiment NUMERIC,
    risk_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH topic_analysis AS (
        SELECT 
            jsonb_array_elements_text(analysis.key_topics) as topic,
            analysis.financial_relevance,
            analysis.sentiment_score,
            analysis.market_impact
        FROM rss_content_analysis analysis
        WHERE analysis.user_id = user_uuid
            AND analysis.analysis_date >= CURRENT_DATE - INTERVAL '1 day' * days_back
    )
    SELECT 
        ta.topic,
        COUNT(*) as mention_count,
        ROUND(AVG(ta.financial_relevance), 3) as avg_relevance,
        ROUND(AVG(ta.sentiment_score), 3) as avg_sentiment,
        CASE 
            WHEN AVG(ta.financial_relevance) > 0.7 THEN 'high'
            WHEN AVG(ta.financial_relevance) > 0.4 THEN 'medium'
            ELSE 'low'
        END as risk_level
    FROM topic_analysis ta
    GROUP BY ta.topic
    HAVING COUNT(*) >= 2
    ORDER BY mention_count DESC, avg_relevance DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки старых данных (обновленная)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Удаление старых курсов валют (старше 1 года)
    DELETE FROM exchange_rates 
    WHERE date < CURRENT_DATE - INTERVAL '1 year';
    
    -- Удаление старых новостей (старше 6 месяцев)
    DELETE FROM news_articles 
    WHERE created_at < CURRENT_DATE - INTERVAL '6 months';
    
    -- Удаление старых RSS анализов (старше 3 месяцев)
    DELETE FROM rss_content_analysis 
    WHERE analysis_date < CURRENT_DATE - INTERVAL '3 months';
    
    -- Удаление старых логов webhook'ов (старше 3 месяцев)
    DELETE FROM webhook_logs 
    WHERE processed_at < CURRENT_DATE - INTERVAL '3 months';
    
    -- Удаление прочитанных уведомлений (старше 1 месяца)
    DELETE FROM notifications 
    WHERE is_read = TRUE AND created_at < CURRENT_DATE - INTERVAL '1 month';
    
    -- Сброс счетчиков ошибок для RSS каналов (если ошибки старше недели)
    UPDATE user_rss_feeds 
    SET error_count = 0, last_error = NULL
    WHERE error_count > 0 
        AND (last_fetched IS NULL OR last_fetched < CURRENT_DATE - INTERVAL '7 days');
    
    RAISE NOTICE 'Old data cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Функция для получения рекомендаций по RSS каналам
CREATE OR REPLACE FUNCTION get_rss_recommendations(user_uuid UUID)
RETURNS TABLE (
    recommendation_type TEXT,
    message TEXT,
    priority INTEGER
) AS $$
BEGIN
    RETURN QUERY
    
    -- Рекомендация добавить RSS каналы
    SELECT 
        'add_feeds'::TEXT,
        'Добавьте больше RSS каналов для более полного анализа рынка'::TEXT,
        1::INTEGER
    WHERE (SELECT COUNT(*) FROM user_rss_feeds WHERE user_id = user_uuid AND is_active = TRUE) < 3
    
    UNION ALL
    
    -- Рекомендация по проблемным каналам
    SELECT 
        'fix_errors'::TEXT,
        'У вас есть RSS каналы с ошибками. Проверьте их настройки'::TEXT,
        2::INTEGER
    WHERE EXISTS (
        SELECT 1 FROM user_rss_feeds 
        WHERE user_id = user_uuid AND error_count > 3
    )
    
    UNION ALL
    
    -- Рекомендация по неактивным каналам
    SELECT 
        'update_inactive'::TEXT,
        'Некоторые RSS каналы давно не обновлялись. Проверьте их статус'::TEXT,
        3::INTEGER
    WHERE EXISTS (
        SELECT 1 FROM user_rss_feeds 
        WHERE user_id = user_uuid 
            AND is_active = TRUE 
            AND (last_fetched IS NULL OR last_fetched < CURRENT_DATE - INTERVAL '2 days')
    )
    
    ORDER BY priority;
END;
$$ LANGUAGE plpgsql;

-- Создание пользователя для приложения (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'finai_user') THEN
        CREATE USER finai_user WITH PASSWORD 'finai_strong_password';
    END IF;
END
$$;

-- Предоставление прав пользователю приложения
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finai_user;
GRANT USAGE ON SCHEMA public TO finai_user;

-- Инициализация демо данных с RSS каналами
INSERT INTO users (email, name, hashed_password, company, subscription_plan) 
VALUES 
    ('demo@finai.kz', 'Demo CFO', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdVGxl9G1KQ1QK8K.', 'ТОО КазахТрейд ДЕМО', 'professional'),
    ('admin@finai.kz', 'System Admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdVGxl9G1KQ1QK8K.', 'Financial AI Systems', 'enterprise')
ON CONFLICT (email) DO NOTHING;

-- Инициализация курсов валют (базовые значения)
INSERT INTO exchange_rates (from_currency, to_currency, rate, date, source) 
VALUES 
    ('USD', 'KZT', 480.50, CURRENT_TIMESTAMP, 'NBK'),
    ('EUR', 'KZT', 520.30, CURRENT_TIMESTAMP, 'NBK'),
    ('RUB', 'KZT', 5.20, CURRENT_TIMESTAMP, 'NBK')
ON CONFLICT DO NOTHING;

-- Демо RSS каналы для demo пользователя
DO $$
DECLARE
    demo_user_id UUID;
BEGIN
    SELECT id INTO demo_user_id FROM users WHERE email = 'demo@finai.kz';
    
    IF demo_user_id IS NOT NULL THEN
        INSERT INTO user_rss_feeds (user_id, name, url, description, category, priority, keywords, fetch_frequency)
        VALUES 
            (demo_user_id, 'Reuters Financial', 'https://feeds.reuters.com/reuters/businessNews', 'Мировые финансовые новости', 'international', 5, '["finance", "market", "economy"]', 'hourly'),
            (demo_user_id, 'Bloomberg Economics', 'https://feeds.bloomberg.com/economics/news.rss', 'Экономические новости', 'economics', 4, '["central bank", "inflation", "GDP"]', 'hourly'),
            (demo_user_id, 'Казахстанские финансы', 'https://kursiv.kz/feed/', 'Финансы Казахстана', 'local', 5, '["тенге", "НБ РК", "экономика"]', 'daily')
        ON CONFLICT DO NOTHING;
    END IF;
END
$$;

-- Создание расписания для очистки данных (если поддерживается pg_cron)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * 0', 'SELECT cleanup_old_data();');

-- Комментарии к таблицам для документации
COMMENT ON TABLE users IS 'Пользователи системы Financial AI Dashboard';
COMMENT ON TABLE bank_accounts IS 'Банковские счета пользователей';
COMMENT ON TABLE exchange_rates IS 'Курсы валют из НБ РК и других источников';
COMMENT ON TABLE news_articles IS 'Финансовые новости для анализа рисков';
COMMENT ON TABLE user_rss_feeds IS 'Пользовательские RSS каналы для персонализированного анализа';
COMMENT ON TABLE rss_content_analysis IS 'AI анализ контента из пользовательских RSS каналов';
COMMENT ON TABLE ai_consultations IS 'История AI консультаций с учетом RSS данных';
COMMENT ON TABLE reports IS 'Генерируемые отчеты с включением RSS анализа';
COMMENT ON TABLE webhook_logs IS 'Логи webhook интеграций (n8n, Telegram, etc.)';

-- Комментарии к ключевым полям
COMMENT ON COLUMN user_rss_feeds.priority IS 'Приоритет RSS канала (1-5), влияет на частоту обновления и количество анализируемых статей';
COMMENT ON COLUMN user_rss_feeds.auto_analysis IS 'Включить автоматический AI анализ статей из этого канала';
COMMENT ON COLUMN user_rss_feeds.keywords IS 'JSON массив ключевых слов для фильтрации релевантных статей';
COMMENT ON COLUMN user_rss_feeds.fetch_frequency IS 'Частота обновления: hourly, daily, weekly';

COMMENT ON COLUMN rss_content_analysis.financial_relevance IS 'AI оценка релевантности статьи для финансовых решений (0.0-1.0)';
COMMENT ON COLUMN rss_content_analysis.sentiment_score IS 'AI анализ настроения статьи (-1.0 негативное, +1.0 позитивное)';
COMMENT ON COLUMN rss_content_analysis.market_impact IS 'AI оценка влияния новости на рынок: low, medium, high';
COMMENT ON COLUMN rss_content_analysis.ai_confidence IS 'Уверенность AI в своем анализе (0.0-1.0)';

-- Настройки PostgreSQL для оптимизации
/*
Рекомендуемые настройки postgresql.conf для оптимальной работы с RSS:

shared_preload_libraries = 'pg_stat_statements'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Для полнотекстового поиска
default_text_search_config = 'russian'
*/