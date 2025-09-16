#!/bin/bash

# =============================================================================
# 🚀 ФИНАНСОВЫЙ AI DASHBOARD - СКРИПТ АВТОМАТИЧЕСКОЙ УСТАНОВКИ
# =============================================================================
# Скрипт для развертывания Financial AI Dashboard с интеграциями НБ РК и n8n

set -e  # Остановка при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} ${CYAN}$1${NC} ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Проверка операционной системы
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos" 
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    
    print_info "Обнаружена ОС: $OS"
}

# Проверка Docker
check_docker() {
    print_header "ПРОВЕРКА DOCKER"
    
    if command -v docker &> /dev/null && command -v docker compose &> /dev/null; then
        print_success "Docker установлен"
        docker --version
        docker compose version
        return 0
    else
        print_error "Docker не найден!"
        echo
        echo "Пожалуйста, установите Docker:"
        echo "• Ubuntu/Debian: sudo apt update && sudo apt install docker.io docker-compose-plugin"
        echo "• CentOS/RHEL: sudo yum install docker docker-compose"  
        echo "• macOS: https://docs.docker.com/desktop/mac/install/"
        echo "• Windows: https://docs.docker.com/desktop/windows/install/"
        echo
        exit 1
    fi
}

# Проверка доступности портов
check_ports() {
    print_header "ПРОВЕРКА ПОРТОВ"
    
    PORTS=(8000 5432 6379 5678 3000 8080)
    OCCUPIED_PORTS=()
    
    for port in "${PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
            OCCUPIED_PORTS+=($port)
            print_warning "Порт $port уже занят"
        else
            print_success "Порт $port свободен"
        fi
    done
    
    if [ ${#OCCUPIED_PORTS[@]} -ne 0 ]; then
        echo
        print_warning "Следующие порты заняты: ${OCCUPIED_PORTS[*]}"
        print_info "Остановите сервисы на этих портах или измените конфигурацию"
        echo
        read -p "Продолжить установку? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Создание директорий проекта
create_project_structure() {
    print_header "СОЗДАНИЕ СТРУКТУРЫ ПРОЕКТА"
    
    # Создание основных директорий
    mkdir -p {logs,static/{reports,uploads},data/cache,ssl,n8n/workflows,backups}
    
    # Создание .gitignore
    cat > .gitignore << 'EOF'
# Переменные окружения
.env
.env.local
.env.production

# Логи
logs/
*.log

# Загрузки пользователей
static/uploads/*
!static/uploads/.gitkeep

# Кеш
data/cache/
*.cache

# SSL сертификаты
ssl/*.pem
ssl/*.key

# Базы данных
*.db
*.sqlite3

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
venv/
env/

# Docker
docker-compose.override.yml

# Backups
backups/
*.sql
*.dump

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF

    touch static/uploads/.gitkeep
    
    print_success "Структура проекта создана"
}

# Настройка переменных окружения
setup_environment() {
    print_header "НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ"
    
    if [ ! -f .env ]; then
        print_info "Создание файла .env из .env.example"
        cp .env.example .env
        
        # Генерация случайных паролей
        SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || date | md5sum | cut -d' ' -f1)
        POSTGRES_PASSWORD=$(openssl rand -base64 16 2>/dev/null || date +%s | sha256sum | cut -d' ' -f1 | head -c 16)
        N8N_PASSWORD=$(openssl rand -base64 12 2>/dev/null || date +%s | sha1sum | cut -d' ' -f1 | head -c 12)
        
        # Обновление .env файла
        sed -i "s/finai-super-secret-jwt-key-change-this-in-production-please/$SECRET_KEY/g" .env
        sed -i "s/finai_very_strong_password_2024/$POSTGRES_PASSWORD/g" .env  
        sed -i "s/n8n_secure_password_2024/$N8N_PASSWORD/g" .env
        
        print_success "Файл .env создан с безопасными паролями"
    else
        print_warning "Файл .env уже существует"
    fi
    
    # Проверка важных переменных
    source .env
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
        echo
        print_warning "⚠️  ВНИМАНИЕ: OpenAI API ключ не настроен!"
        print_info "Получите API ключ на https://platform.openai.com/api-keys"
        print_info "И обновите OPENAI_API_KEY в файле .env"
        echo
        echo -e "${YELLOW}Без OpenAI API ключа AI функции будут работать в демо режиме${NC}"
        echo
    fi
}

# Запуск сервисов
start_services() {
    print_header "ЗАПУСК СЕРВИСОВ"
    
    print_info "Загрузка Docker образов..."
    docker compose pull
    
    print_info "Сборка приложения..."
    docker compose build
    
    print_info "Запуск основных сервисов..."
    docker compose up -d
    
    print_success "Сервисы запущены"
}

# Ожидание готовности сервисов
wait_for_services() {
    print_header "ОЖИДАНИЕ ГОТОВНОСТИ СЕРВИСОВ"
    
    print_info "Ожидание PostgreSQL..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker compose exec -T postgres pg_isready -U finai_user >/dev/null 2>&1; then
            print_success "PostgreSQL готов"
            break
        fi
        sleep 2
        ((timeout -= 2))
        echo -n "."
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Таймаут ожидания PostgreSQL"
        exit 1
    fi
    
    print_info "Ожидание Financial AI Dashboard..."
    timeout=90
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Financial AI Dashboard готов"
            break
        fi
        sleep 3
        ((timeout -= 3))
        echo -n "."
    done
    
    if [ $timeout -le 0 ]; then
        print_warning "Таймаут ожидания Financial AI Dashboard (но продолжаем...)"
    fi
}

# Инициализация демо данных
initialize_demo_data() {
    print_header "ИНИЦИАЛИЗАЦИЯ ДЕМО ДАННЫХ"
    
    print_info "Создание демо пользователя и тестовых данных..."
    
    if curl -f -X POST "http://localhost:8000/api/init-demo" >/dev/null 2>&1; then
        print_success "Демо данные инициализированы"
    else
        print_warning "Не удалось инициализировать демо данные автоматически"
        print_info "Попробуйте позже: curl -X POST 'http://localhost:8000/api/init-demo'"
    fi
}

# Проверка состояния системы
check_system_status() {
    print_header "ПРОВЕРКА СОСТОЯНИЯ СИСТЕМЫ"
    
    echo "Статус контейнеров:"
    docker compose ps
    
    echo
    echo "Проверка сервисов:"
    
    # Financial AI Dashboard
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Financial AI Dashboard: http://localhost:8000 ✅"
    else
        print_error "Financial AI Dashboard: http://localhost:8000 ❌"
    fi
    
    # n8n
    if curl -f http://localhost:5678 >/dev/null 2>&1; then
        print_success "n8n Automation: http://localhost:5678 ✅"
    else
        print_warning "n8n Automation: http://localhost:5678 ⚠️"
    fi
    
    # PostgreSQL
    if docker compose exec -T postgres pg_isready -U finai_user >/dev/null 2>&1; then
        print_success "PostgreSQL Database ✅"
    else
        print_error "PostgreSQL Database ❌"
    fi
    
    # Redis
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis Cache ✅"
    else
        print_warning "Redis Cache ⚠️"
    fi
}

# Вывод итоговой информации
show_final_info() {
    print_header "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
    
    echo -e "${GREEN}Financial AI Dashboard успешно развернут!${NC}"
    echo
    echo -e "${CYAN}📊 Доступ к сервисам:${NC}"
    echo "   🏦 Financial AI Dashboard: ${BLUE}http://localhost:8000${NC}"
    echo "   🤖 n8n Automation: ${BLUE}http://localhost:5678${NC}"
    echo "   📈 Grafana (опционально): ${BLUE}http://localhost:3000${NC}"
    echo "   🗄️  pgAdmin (опционально): ${BLUE}http://localhost:8080${NC}"
    echo
    echo -e "${CYAN}👤 Демо аккаунт:${NC}"
    echo "   📧 Email: ${GREEN}demo@finai.kz${NC}"
    echo "   🔑 Пароль: ${GREEN}demo123${NC}"
    echo
    echo -e "${CYAN}🔧 Управление системой:${NC}"
    echo "   📊 Статус: ${YELLOW}docker compose ps${NC}"
    echo "   📋 Логи: ${YELLOW}docker compose logs -f finai-app${NC}"
    echo "   ⏹️  Остановка: ${YELLOW}docker compose down${NC}"
    echo "   🔄 Перезапуск: ${YELLOW}docker compose restart${NC}"
    echo
    echo -e "${CYAN}🤖 n8n интеграция:${NC}"
    echo "   Webhook URL: ${GREEN}http://localhost:8000/webhook/n8n/chat${NC}"
    echo "   Статус: ${GREEN}http://localhost:8000/webhook/n8n/status${NC}"
    echo
    echo -e "${CYAN}📊 Функции системы:${NC}"
    echo "   ✅ Автоматическое обновление курсов НБ РК"
    echo "   ✅ Мониторинг финансовых новостей" 
    echo "   ✅ AI анализ и рекомендации"
    echo "   ✅ Ежедневные отчеты"
    echo "   ✅ n8n webhook интеграция"
    echo "   ✅ Мобильная адаптация"
    echo
    
    # Проверка OpenAI API ключа
    source .env
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
        echo -e "${YELLOW}⚠️  ВАЖНО: Настройте OpenAI API ключ в файле .env для полной функциональности AI!${NC}"
        echo
    fi
    
    echo -e "${PURPLE}🚀 Система готова к использованию!${NC}"
}

# Основная функция
main() {
    clear
    echo -e "${PURPLE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🏦 FINANCIAL AI DASHBOARD - АВТОМАТИЧЕСКАЯ УСТАНОВКА      ║
║                                                              ║
║  Система управления корпоративной ликвидностью с AI          ║
║  • Интеграция с Национальным банком РК                      ║
║  • Мониторинг финансовых новостей                           ║
║  • AI анализ и прогнозирование                              ║
║  • n8n автоматизация и webhook                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    detect_os
    check_docker
    check_ports
    create_project_structure
    setup_environment
    start_services
    wait_for_services
    initialize_demo_data
    check_system_status
    show_final_info
}

# Обработка аргументов командной строки
case "${1:-install}" in
    "install"|"")
        main
        ;;
    "start")
        print_header "ЗАПУСК СИСТЕМЫ"
        docker compose up -d
        print_success "Система запущена"
        ;;
    "stop")
        print_header "ОСТАНОВКА СИСТЕМЫ"
        docker compose down
        print_success "Система остановлена"
        ;;
    "restart")
        print_header "ПЕРЕЗАПУСК СИСТЕМЫ"
        docker compose restart
        print_success "Система перезапущена"
        ;;
    "status")
        check_system_status
        ;;
    "logs")
        print_header "ПРОСМОТР ЛОГОВ"
        docker compose logs -f finai-app
        ;;
    "update")
        print_header "ОБНОВЛЕНИЕ СИСТЕМЫ"
        docker compose pull
        docker compose up -d --build
        print_success "Система обновлена"
        ;;
    "clean")
        print_header "ОЧИСТКА СИСТЕМЫ"
        read -p "⚠️  Удалить ВСЕ данные? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v
            docker system prune -f
            print_success "Система очищена"
        else
            print_info "Операция отменена"
        fi
        ;;
    "help")
        echo "Financial AI Dashboard - Управление системой"
        echo
        echo "Использование: $0 [команда]"
        echo
        echo "Команды:"
        echo "  install    Установка системы (по умолчанию)"
        echo "  start      Запуск системы"
        echo "  stop       Остановка системы"  
        echo "  restart    Перезапуск системы"
        echo "  status     Проверка статуса"
        echo "  logs       Просмотр логов"
        echo "  update     Обновление системы"
        echo "  clean      Полная очистка"
        echo "  help       Эта справка"
        ;;
    *)
        print_error "Неизвестная команда: $1"
        print_info "Используйте: $0 help"
        exit 1
        ;;
esac