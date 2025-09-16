// Financial AI Dashboard Application - Enhanced with RSS Management
class FinancialDashboardApp {
    constructor() {
        this.currentPage = 'landing';
        this.currentSection = 'dashboard';
        this.currentSettingsTab = 'api-keys';
        this.isAuthenticated = false;
        this.sidebarOpen = false;
        this.mobileNavOpen = false;
        this.charts = {};
        this.userData = null;
        this.appData = null;
        this.currentPricingSlide = 0;
        this.currentMetricIndex = 0;
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.isScrolling = null;
        this.serviceWorkerRegistered = false;
        
        // RSS Management
        this.rssFeeds = [];
        this.rssAnalytics = {};
        this.currentRssFeedFilter = 'all';
        this.editingFeedId = null;
        
        this.init();
    }

    async init() {
        try {
            console.log('Initializing FinAI Dashboard...');
            
            // Make the app globally available FIRST
            window.app = this;
            
            this.loadTheme();
            this.loadAppData();
            this.loadRssData();
            this.setupGlobalHandlers();
            this.setupEventListeners();
            this.setupMobileFeatures();
            this.registerServiceWorker();
            
            // Check if user is already authenticated
            const savedUser = localStorage.getItem('finai_user');
            if (savedUser) {
                this.userData = JSON.parse(savedUser);
                this.isAuthenticated = true;
                await this.showMainApp();
            } else {
                // Render hero chart after a short delay
                setTimeout(() => this.renderHeroChart(), 100);
                this.setupPricingSlider();
            }
            
            console.log('FinAI Dashboard initialized successfully');
            console.log('Global app object:', window.app);
        } catch (error) {
            console.error('Initialization error:', error);
            this.showToast('Ошибка инициализации приложения', 'error');
        }
    }

    setupGlobalHandlers() {
        // Immediately bind all functions to window for global access
        console.log('Setting up global handlers...');
        
        // Authentication methods
        window.showLogin = () => this.showLogin();
        window.showRegister = (plan) => this.showRegister(plan);
        window.showRegisterFromLogin = () => this.showRegisterFromLogin();
        window.showLoginFromRegister = () => this.showLoginFromRegister();
        window.showForgotPassword = () => this.showForgotPassword();
        window.handleLogin = (event) => this.handleLogin(event);
        window.handleRegister = (event) => this.handleRegister(event);
        window.socialLogin = (provider) => this.socialLogin(provider);
        window.closeModal = (id) => this.closeModal(id);
        window.logout = () => this.logout();
        
        // Navigation methods
        window.navigateTo = (section) => this.navigateTo(section);
        window.toggleSidebar = () => this.toggleSidebar();
        window.closeSidebar = () => this.closeSidebar();
        window.toggleMobileNav = () => this.toggleMobileNav();
        window.scrollToDemo = () => this.scrollToDemo();
        
        // UI methods
        window.toggleNotifications = () => this.toggleNotifications();
        window.toggleUserMenu = () => this.toggleUserMenu();
        window.markAllRead = () => this.markAllRead();
        window.toggleTheme = () => this.toggleTheme();
        window.goToPricingSlide = (index) => this.goToPricingSlide(index);
        window.nextMetric = () => this.nextMetric();
        window.prevMetric = () => this.prevMetric();
        
        // Chat methods
        window.sendChatMessage = () => this.sendChatMessage();
        window.sendQuickMessage = (msg) => this.sendQuickMessage(msg);
        window.clearChat = () => this.clearChat();
        window.loadConsultation = (id) => this.loadConsultation(id);
        
        // Account methods
        window.syncAccounts = () => this.syncAccounts();
        window.showAccountDetails = (id) => this.showAccountDetails(id);
        window.addBankAccount = () => this.addBankAccount();
        
        // Report methods
        window.generateReport = () => this.generateReport();
        window.exportData = () => this.exportData();
        window.createReport = () => this.createReport();
        window.downloadReport = (type) => this.downloadReport(type);
        window.previewReport = (type) => this.previewReport(type);
        
        // Settings methods
        window.switchSettingsTab = (tab) => this.switchSettingsTab(tab);
        window.editApiKey = (service) => this.editApiKey(service);
        window.testApiKey = (service) => this.testApiKey(service);
        window.uploadAvatar = () => this.uploadAvatar();
        
        // RSS methods
        window.showAddRssFeed = () => this.showAddRssFeed();
        window.showEditFeed = (id) => this.showEditFeed(id);
        window.handleRssForm = (event) => this.handleRssForm(event);
        window.testFeed = (id) => this.testFeed(id);
        window.deleteFeed = (id) => this.deleteFeed(id);
        window.filterRssFeeds = (filter) => this.filterRssFeeds(filter);
        
        console.log('Global handlers setup complete. Available methods:', Object.keys(window).filter(key => typeof window[key] === 'function' && key.match(/^(show|handle|navigate|toggle|send|sync|generate|create|download|switch|edit|test|upload|clear|load|mark|scroll|close|add|delete|filter)/)));
    }

    loadRssData() {
        // Load RSS feeds data from JSON
        this.rssFeeds = [
            {
                "id": "1",
                "name": "Reuters Financial",
                "url": "https://feeds.reuters.com/reuters/businessNews",
                "description": "Мировые финансовые новости от Reuters",
                "category": "financial",
                "priority": 5,
                "is_active": true,
                "auto_analysis": true,
                "keywords": ["finance", "market", "economy", "oil", "dollar"],
                "fetch_frequency": "hourly",
                "error_count": 0,
                "articles_count": 156,
                "last_fetched": "2025-09-17T10:30:00Z"
            },
            {
                "id": "2",
                "name": "Bloomberg Economics",
                "url": "https://feeds.bloomberg.com/economics/news.rss",
                "description": "Экономические новости от Bloomberg",
                "category": "economics",
                "priority": 4,
                "is_active": true,
                "auto_analysis": true,
                "keywords": ["central bank", "inflation", "GDP", "policy"],
                "fetch_frequency": "hourly",
                "error_count": 0,
                "articles_count": 89,
                "last_fetched": "2025-09-17T10:15:00Z"
            },
            {
                "id": "3",
                "name": "Казахстанские финансы",
                "url": "https://kursiv.kz/feed/",
                "description": "Финансовые новости Казахстана",
                "category": "local",
                "priority": 5,
                "is_active": false,
                "auto_analysis": true,
                "keywords": ["тенге", "НБ РК", "экономика", "банки"],
                "fetch_frequency": "daily",
                "error_count": 2,
                "articles_count": 45,
                "last_fetched": "2025-09-16T09:00:00Z"
            }
        ];

        this.rssAnalytics = {
            "total_feeds": 3,
            "active_feeds": 2,
            "articles_analyzed": 245,
            "avg_relevance": 0.73,
            "avg_sentiment": 0.15,
            "top_topics": [
                {"topic": "oil prices", "count": 23, "relevance": 0.89},
                {"topic": "interest rates", "count": 19, "relevance": 0.85},
                {"topic": "inflation", "count": 17, "relevance": 0.78},
                {"topic": "tenge exchange", "count": 12, "relevance": 0.92},
                {"topic": "central bank policy", "count": 11, "relevance": 0.81}
            ],
            "recent_analyses": [
                {
                    "title": "Federal Reserve holds rates steady amid inflation concerns",
                    "relevance": 0.95,
                    "sentiment": -0.2,
                    "market_impact": "high",
                    "source": "Reuters Financial"
                },
                {
                    "title": "Oil prices surge on Middle East tensions",
                    "relevance": 0.88,
                    "sentiment": 0.1,
                    "market_impact": "medium",
                    "source": "Bloomberg Economics"
                }
            ]
        };
    }

    setupMobileFeatures() {
        // Setup touch gestures with Hammer.js if available
        if (typeof Hammer !== 'undefined') {
            this.setupTouchGestures();
        }
        
        // Setup pull-to-refresh
        this.setupPullToRefresh();
        
        // Setup swipe navigation for metrics
        this.setupMetricsSwipe();
        
        // Setup mobile viewport handling
        this.setupViewportHandling();
        
        // Setup keyboard handling for mobile
        this.setupMobileKeyboard();
        
        // Setup orientation change handling
        this.setupOrientationChange();
    }

    setupTouchGestures() {
        // Pricing slider gestures
        const pricingSlider = document.getElementById('pricingSlider');
        if (pricingSlider && typeof Hammer !== 'undefined') {
            const hammer = new Hammer(pricingSlider);
            hammer.get('swipe').set({ direction: Hammer.DIRECTION_HORIZONTAL });
            
            hammer.on('swipeleft', () => {
                this.nextPricingSlide();
            });
            
            hammer.on('swiperight', () => {
                this.prevPricingSlide();
            });
        }

        // Chat messages swipe gestures
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages && typeof Hammer !== 'undefined') {
            const hammer = new Hammer(chatMessages);
            hammer.get('swipe').set({ direction: Hammer.DIRECTION_HORIZONTAL });
            
            hammer.on('swiperight', () => {
                if (this.currentSection === 'ai-consultant') {
                    this.clearChat();
                }
            });
        }
    }

    setupPullToRefresh() {
        let pullToRefreshElement = null;
        let startY = 0;
        let currentY = 0;
        let pulling = false;

        const createPullToRefreshElement = () => {
            if (!pullToRefreshElement) {
                pullToRefreshElement = document.createElement('div');
                pullToRefreshElement.className = 'pull-to-refresh';
                pullToRefreshElement.innerHTML = '↓';
                document.body.appendChild(pullToRefreshElement);
            }
        };

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                createPullToRefreshElement();
            }
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (window.scrollY === 0 && startY) {
                currentY = e.touches[0].clientY;
                const diff = currentY - startY;
                
                if (diff > 0 && diff < 100) {
                    pulling = true;
                    if (pullToRefreshElement) {
                        pullToRefreshElement.style.opacity = Math.min(diff / 60, 1);
                        pullToRefreshElement.style.transform = `translateY(${Math.min(diff - 40, 20)}px) translateX(-50%)`;
                    }
                } else if (diff >= 100) {
                    if (pullToRefreshElement) {
                        pullToRefreshElement.classList.add('active');
                        pullToRefreshElement.innerHTML = '↻';
                    }
                }
            }
        }, { passive: true });

        document.addEventListener('touchend', () => {
            if (pulling && currentY - startY >= 100) {
                this.refreshData();
            }
            
            if (pullToRefreshElement) {
                pullToRefreshElement.style.opacity = '0';
                pullToRefreshElement.style.transform = 'translateY(-40px) translateX(-50%)';
                pullToRefreshElement.classList.remove('active');
                pullToRefreshElement.innerHTML = '↓';
            }
            
            pulling = false;
            startY = 0;
            currentY = 0;
        });
    }

    setupMetricsSwipe() {
        const metricsCarousel = document.getElementById('metricsCarousel');
        if (!metricsCarousel) return;

        let startX = 0;
        let currentX = 0;
        let isDragging = false;

        metricsCarousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
        }, { passive: true });

        metricsCarousel.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            currentX = e.touches[0].clientX;
        }, { passive: true });

        metricsCarousel.addEventListener('touchend', () => {
            if (!isDragging) return;
            
            const diff = startX - currentX;
            const threshold = 50;

            if (Math.abs(diff) > threshold) {
                if (diff > 0) {
                    this.nextMetric();
                } else {
                    this.prevMetric();
                }
            }

            isDragging = false;
        });
    }

    setupViewportHandling() {
        // Handle viewport changes on mobile
        const viewport = document.querySelector('meta[name="viewport"]');
        
        // Adjust viewport on input focus to prevent zoom
        document.addEventListener('focusin', (e) => {
            if (e.target.matches('input, textarea, select')) {
                if (viewport) {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
                }
            }
        });

        document.addEventListener('focusout', (e) => {
            if (e.target.matches('input, textarea, select')) {
                if (viewport) {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, user-scalable=no');
                }
            }
        });
    }

    setupMobileKeyboard() {
        // Handle virtual keyboard on mobile
        let initialViewportHeight = window.innerHeight;

        window.addEventListener('resize', () => {
            const currentHeight = window.innerHeight;
            const diff = initialViewportHeight - currentHeight;

            // If height difference is significant, keyboard is likely open
            if (diff > 150) {
                document.body.classList.add('keyboard-open');
                
                // Scroll active input into view
                const activeElement = document.activeElement;
                if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
                    setTimeout(() => {
                        activeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 300);
                }
            } else {
                document.body.classList.remove('keyboard-open');
            }
        });
    }

    setupOrientationChange() {
        window.addEventListener('orientationchange', () => {
            // Refresh charts on orientation change
            setTimeout(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && chart.resize) {
                        chart.resize();
                    }
                });
            }, 500);
        });
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const swCode = `
                const CACHE_NAME = 'finai-v1';
                const urlsToCache = [
                    '/',
                    '/style.css',
                    '/app.js',
                    'https://cdn.jsdelivr.net/npm/chart.js',
                    'https://cdn.jsdelivr.net/npm/hammerjs@2.0.8'
                ];

                self.addEventListener('install', event => {
                    event.waitUntil(
                        caches.open(CACHE_NAME)
                            .then(cache => cache.addAll(urlsToCache))
                    );
                });

                self.addEventListener('fetch', event => {
                    event.respondWith(
                        caches.match(event.request)
                            .then(response => {
                                if (response) {
                                    return response;
                                }
                                return fetch(event.request);
                            })
                    );
                });
                `;
                
                const swBlob = new Blob([swCode], { type: 'application/javascript' });
                const swUrl = URL.createObjectURL(swBlob);
                
                const registration = await navigator.serviceWorker.register(swUrl);
                console.log('Service Worker registered:', registration);
                this.serviceWorkerRegistered = true;
                
                // Handle updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showToast('Доступно обновление приложения', 'info');
                        }
                    });
                });
            } catch (error) {
                console.log('Service Worker registration failed:', error);
            }
        }
    }

    loadAppData() {
        // Load enhanced data with mobile optimizations
        this.appData = {
            "users": [
                {
                    "id": "user_1",
                    "name": "Алексей Петров",
                    "email": "alex@company.kz", 
                    "role": "CFO",
                    "company": "ТОО КазахТрейд",
                    "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150",
                    "subscription": "Professional",
                    "lastLogin": "2025-09-17T09:30:00Z",
                    "settings": {
                        "theme": "light",
                        "language": "ru",
                        "timezone": "Asia/Almaty",
                        "notifications": {
                            "email": true,
                            "telegram": true,
                            "criticalAlerts": true,
                            "rssUpdates": true
                        }
                    }
                }
            ],
            "dashboardMetrics": {
                "totalBalance": 245750000,
                "currency": "KZT",
                "cashFlowThisMonth": 15430000,
                "liquidityStatus": "ADEQUATE",
                "riskLevel": "LOW",
                "accountsCount": 8,
                "lastUpdated": "2025-09-17T09:35:00Z"
            },
            "accounts": [
                {
                    "id": "acc_1",
                    "name": "Основной операционный счет",
                    "bank": "Halyk Bank",
                    "balance": 125300000,
                    "currency": "KZT",
                    "type": "operational",
                    "lastTransaction": "2025-09-17T08:20:00Z"
                },
                {
                    "id": "acc_2", 
                    "name": "Валютный счет USD",
                    "bank": "Kaspi Bank",
                    "balance": 248500,
                    "currency": "USD",
                    "type": "currency",
                    "lastTransaction": "2025-09-16T15:15:00Z"
                },
                {
                    "id": "acc_3",
                    "name": "Резервный фонд",
                    "bank": "Forte Bank",
                    "balance": 45200000,
                    "currency": "KZT", 
                    "type": "reserve",
                    "lastTransaction": "2025-09-16T12:30:00Z"
                }
            ],
            "liquidityForecast": [
                {"date": "2025-09-17", "balance": 245750000, "status": "ADEQUATE"},
                {"date": "2025-09-18", "balance": 248200000, "status": "ADEQUATE"},
                {"date": "2025-09-19", "balance": 243100000, "status": "ADEQUATE"}, 
                {"date": "2025-09-20", "balance": 239800000, "status": "ADEQUATE"},
                {"date": "2025-09-21", "balance": 255600000, "status": "EXCESS"},
                {"date": "2025-09-22", "balance": 258900000, "status": "EXCESS"},
                {"date": "2025-09-23", "balance": 261200000, "status": "EXCESS"}
            ],
            "cashFlowData": [
                {"date": "2025-09-17", "inflow": 12500000, "outflow": 8300000},
                {"date": "2025-09-18", "inflow": 15200000, "outflow": 12600000},
                {"date": "2025-09-19", "inflow": 9800000, "outflow": 14200000},
                {"date": "2025-09-20", "inflow": 18300000, "outflow": 11900000},
                {"date": "2025-09-21", "inflow": 22100000, "outflow": 6400000},
                {"date": "2025-09-22", "inflow": 11700000, "outflow": 8400000},
                {"date": "2025-09-23", "inflow": 16900000, "outflow": 14600000}
            ],
            "aiConsultations": [
                {
                    "id": "consultation_1",
                    "question": "Какая текущая ликвидность компании?",
                    "response": "На текущий момент ваша компания имеет адекватный уровень ликвидности. Общий баланс составляет 245.75 млн тенге, что покрывает операционные потребности на ближайшие 45 дней...",
                    "timestamp": "2025-09-17T08:45:00Z",
                    "rating": 5,
                    "processingTime": "2.3s"
                },
                {
                    "id": "consultation_2", 
                    "question": "Что говорят RSS новости о рынке?",
                    "response": "Анализ последних RSS новостей показывает смешанные настроения на рынке. Основные темы: повышение процентных ставок ФРС (негативно), рост цен на нефть (позитивно для экономики Казахстана). Рекомендую осторожность в валютных операциях...",
                    "timestamp": "2025-09-17T08:20:00Z", 
                    "rating": 4,
                    "processingTime": "3.1s"
                }
            ],
            "notifications": [
                {
                    "id": "notif_1",
                    "type": "info",
                    "title": "RSS обновление",
                    "message": "Получено 12 новых финансовых новостей для анализа", 
                    "timestamp": "2025-09-17T09:35:00Z",
                    "read": false
                },
                {
                    "id": "notif_2",
                    "type": "success", 
                    "title": "Отчет сгенерирован",
                    "message": "Ежедневный отчет по ликвидности и RSS анализ отправлены",
                    "timestamp": "2025-09-17T08:00:00Z",
                    "read": false
                }
            ]
        };
    }

    setupEventListeners() {
        // Global event listeners with better error handling
        document.addEventListener('click', (e) => {
            // Close dropdowns when clicking outside
            if (!e.target.closest('.notifications-dropdown')) {
                this.hideElement('notificationsPanel');
            }
            if (!e.target.closest('.user-menu')) {
                this.hideElement('userDropdown');
            }
            
            // Close mobile nav when clicking outside
            if (!e.target.closest('.navbar') && this.mobileNavOpen) {
                this.closeMobileNav();
            }
            
            // Handle modal backdrop clicks
            if (e.target.classList.contains('modal')) {
                this.closeAllModals();
            }
        });

        // Enhanced keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
                this.closeSidebar();
                this.closeMobileNav();
            }
            if (e.ctrlKey && e.key === '/') {
                e.preventDefault();
                const chatInput = document.getElementById('chatInput');
                if (chatInput && this.currentSection === 'ai-consultant') {
                    chatInput.focus();
                }
            }
            // Mobile navigation shortcuts
            if (e.ctrlKey && e.key === 'm') {
                e.preventDefault();
                this.toggleSidebar();
            }
        });

        // Handle responsive sidebar on resize
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 1024) {
                this.sidebarOpen = false;
                this.mobileNavOpen = false;
                this.updateSidebarState();
                this.closeMobileNav();
            }
        });

        // Enhanced chat input handling
        document.addEventListener('keypress', (e) => {
            if (e.target.id === 'chatInput' && e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('auth-form') || e.target.classList.contains('rss-form')) {
                e.preventDefault();
            }
        });
    }

    // Mobile Navigation
    toggleMobileNav() {
        console.log('Toggle mobile nav called');
        this.mobileNavOpen = !this.mobileNavOpen;
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
        
        if (mobileNavMenu) {
            if (this.mobileNavOpen) {
                mobileNavMenu.classList.add('open');
            } else {
                mobileNavMenu.classList.remove('open');
            }
        }
        
        if (mobileNavToggle) {
            if (this.mobileNavOpen) {
                mobileNavToggle.classList.add('active');
            } else {
                mobileNavToggle.classList.remove('active');
            }
        }
    }

    closeMobileNav() {
        this.mobileNavOpen = false;
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
        
        if (mobileNavMenu) {
            mobileNavMenu.classList.remove('open');
        }
        
        if (mobileNavToggle) {
            mobileNavToggle.classList.remove('active');
        }
    }

    // Enhanced Pricing Slider
    setupPricingSlider() {
        this.updatePricingDots();
    }

    goToPricingSlide(index) {
        const slider = document.getElementById('pricingSlider');
        if (!slider) return;

        const cards = slider.querySelectorAll('.pricing-card');
        if (index >= 0 && index < cards.length) {
            this.currentPricingSlide = index;
            
            // Smooth scroll to the card
            const targetCard = cards[index];
            const scrollLeft = targetCard.offsetLeft - (slider.offsetWidth - targetCard.offsetWidth) / 2;
            
            slider.scrollTo({
                left: scrollLeft,
                behavior: 'smooth'
            });
            
            this.updatePricingDots();
        }
    }

    nextPricingSlide() {
        const slider = document.getElementById('pricingSlider');
        if (!slider) return;
        
        const cards = slider.querySelectorAll('.pricing-card');
        if (this.currentPricingSlide < cards.length - 1) {
            this.goToPricingSlide(this.currentPricingSlide + 1);
        }
    }

    prevPricingSlide() {
        const slider = document.getElementById('pricingSlider');
        if (!slider) return;
        
        if (this.currentPricingSlide > 0) {
            this.goToPricingSlide(this.currentPricingSlide - 1);
        }
    }

    updatePricingDots() {
        const dots = document.querySelectorAll('.pricing-dots .dot');
        dots.forEach((dot, index) => {
            if (index === this.currentPricingSlide) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    // Enhanced Metrics Navigation
    nextMetric() {
        const carousel = document.getElementById('metricsCarousel');
        if (!carousel) return;
        
        const cards = carousel.querySelectorAll('.metric-card');
        if (this.currentMetricIndex < cards.length - 1) {
            this.currentMetricIndex++;
            this.scrollToMetric(this.currentMetricIndex);
        }
    }

    prevMetric() {
        if (this.currentMetricIndex > 0) {
            this.currentMetricIndex--;
            this.scrollToMetric(this.currentMetricIndex);
        }
    }

    scrollToMetric(index) {
        const carousel = document.getElementById('metricsCarousel');
        if (!carousel) return;
        
        const cards = carousel.querySelectorAll('.metric-card');
        if (index >= 0 && index < cards.length) {
            const targetCard = cards[index];
            const scrollLeft = targetCard.offsetLeft - (carousel.offsetWidth - targetCard.offsetWidth) / 2;
            
            carousel.scrollTo({
                left: scrollLeft,
                behavior: 'smooth'
            });
        }
    }

    // Theme Management
    loadTheme() {
        const savedTheme = localStorage.getItem('finai_theme') || 'light';
        this.setTheme(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-color-scheme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        this.showToast(`Тема изменена на ${newTheme === 'light' ? 'светлую' : 'темную'}`, 'info');
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-color-scheme', theme);
        localStorage.setItem('finai_theme', theme);
        
        // Update chart colors if they exist
        setTimeout(() => {
            Object.values(this.charts).forEach(chart => {
                if (chart && chart.update) {
                    chart.update();
                }
            });
        }, 100);
    }

    // Enhanced Navigation with better logging
    showLogin() {
        console.log('showLogin called');
        this.closeMobileNav();
        this.showElement('loginModal');
        // Focus first input for better mobile UX
        setTimeout(() => {
            const firstInput = document.querySelector('#loginModal input[type="email"]');
            if (firstInput) firstInput.focus();
        }, 300);
    }

    showRegister(plan = null) {
        console.log('showRegister called with plan:', plan);
        this.closeMobileNav();
        if (plan) {
            console.log('Selected plan:', plan);
        }
        this.showElement('registerModal');
        // Focus first input for better mobile UX
        setTimeout(() => {
            const firstInput = document.querySelector('#registerModal input[type="text"]');
            if (firstInput) firstInput.focus();
        }, 300);
    }

    showRegisterFromLogin() {
        this.hideElement('loginModal');
        this.showElement('registerModal');
        setTimeout(() => {
            const firstInput = document.querySelector('#registerModal input[type="text"]');
            if (firstInput) firstInput.focus();
        }, 300);
    }

    showLoginFromRegister() {
        this.hideElement('registerModal');
        this.showElement('loginModal');
        setTimeout(() => {
            const firstInput = document.querySelector('#loginModal input[type="email"]');
            if (firstInput) firstInput.focus();
        }, 300);
    }

    showForgotPassword() {
        this.hideElement('loginModal');
        this.showToast('Функция восстановления пароля будет доступна в ближайшее время', 'info');
    }

    // Enhanced Authentication
    handleLogin(event) {
        console.log('handleLogin called');
        event.preventDefault();
        this.showLoading(true);
        
        // Add haptic feedback on mobile
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Simulate API call
        setTimeout(() => {
            this.userData = this.appData.users[0];
            this.isAuthenticated = true;
            localStorage.setItem('finai_user', JSON.stringify(this.userData));
            
            this.hideElement('loginModal');
            this.showLoading(false);
            this.showMainApp();
            this.showToast('Добро пожаловать в FinAI Dashboard!', 'success');
        }, 1500);
        
        return false;
    }

    handleRegister(event) {
        console.log('handleRegister called');
        event.preventDefault();
        this.showLoading(true);
        
        // Add haptic feedback on mobile
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Simulate API call
        setTimeout(() => {
            const form = event.target;
            const inputs = form.querySelectorAll('input[type="text"], input[type="email"]');
            
            this.userData = {
                id: 'user_' + Date.now(),
                name: inputs[0]?.value || 'Новый пользователь',
                company: inputs[1]?.value || 'Новая компания',
                email: form.querySelector('input[type="email"]')?.value || 'user@example.com',
                role: 'CFO',
                subscription: 'Professional',
                avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150'
            };
            
            this.isAuthenticated = true;
            localStorage.setItem('finai_user', JSON.stringify(this.userData));
            
            this.hideElement('registerModal');
            this.showLoading(false);
            this.showMainApp();
            this.showToast('Регистрация успешно завершена!', 'success');
        }, 1500);
        
        return false;
    }

    socialLogin(provider) {
        this.showToast(`Вход через ${provider} будет доступен в ближайшее время`, 'info');
    }

    logout() {
        localStorage.removeItem('finai_user');
        this.isAuthenticated = false;
        this.userData = null;
        this.hideElement('userDropdown');
        this.closeSidebar();
        this.showLandingPage();
        this.showToast('Вы вышли из системы', 'info');
    }

    // Page Management
    showLandingPage() {
        console.log('Showing landing page');
        this.currentPage = 'landing';
        this.hideElement('mainApp');
        this.showElement('landingPage');
        
        // Render hero chart
        setTimeout(() => {
            this.renderHeroChart();
            this.setupPricingSlider();
        }, 100);
    }

    async showMainApp() {
        console.log('Showing main app');
        this.currentPage = 'main';
        this.hideElement('landingPage');
        this.showElement('mainApp');
        
        // Close mobile navigation
        this.closeMobileNav();
        
        // Initialize dashboard with delay to ensure DOM is ready
        setTimeout(() => {
            this.populateDashboard();
            this.renderDashboardCharts();
            this.populateNotifications();
            this.populateConsultationHistory();
            this.populateRssFeeds();
            this.updateRssStats();
            this.populateRssInsights();
            this.populateTopTopics();
        }, 200);
    }

    // Enhanced Main App Navigation
    navigateTo(section) {
        console.log('Navigating to:', section);
        // Update navigation state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('nav-item--active');
        });
        
        const activeNavItem = document.querySelector(`[data-section="${section}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('nav-item--active');
        }

        // Update content sections
        document.querySelectorAll('.content-section').forEach(contentSection => {
            contentSection.classList.remove('active');
        });
        
        const activeSection = document.getElementById(section);
        if (activeSection) {
            activeSection.classList.add('active');
        }

        // Update page title
        const titles = {
            'dashboard': 'Dashboard',
            'ai-consultant': 'AI Консультант',
            'reports': 'Отчеты',
            'bank-accounts': 'Банковские счета',
            'rss-settings': 'RSS Настройки',
            'settings': 'Настройки',
            'profile': 'Профиль'
        };
        
        const titleElement = document.getElementById('pageTitle');
        if (titleElement) {
            titleElement.textContent = titles[section] || section;
        }

        this.currentSection = section;
        
        // Close sidebar on mobile after navigation
        if (window.innerWidth < 1024) {
            this.closeSidebar();
        }

        // Section-specific initialization
        if (section === 'reports' && !this.charts.reportPreview) {
            setTimeout(() => this.renderReportPreviewChart(), 200);
        }
        if (section === 'rss-settings') {
            setTimeout(() => {
                this.renderRssAnalyticsChart();
                this.renderRssSentimentChart();
            }, 200);
        }
        if (section === 'bank-accounts') {
            setTimeout(() => this.populateDetailedAccounts(), 200);
        }
        
        // Clear any typing indicators when leaving AI consultant
        if (this.currentSection !== 'ai-consultant') {
            this.hideTypingIndicator();
        }

        // Add haptic feedback on mobile
        if (navigator.vibrate) {
            navigator.vibrate(20);
        }
    }

    toggleSidebar() {
        this.sidebarOpen = !this.sidebarOpen;
        this.updateSidebarState();
    }

    closeSidebar() {
        this.sidebarOpen = false;
        this.updateSidebarState();
    }

    updateSidebarState() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (sidebar) {
            if (this.sidebarOpen) {
                sidebar.classList.add('open');
                if (overlay) overlay.classList.add('active');
            } else {
                sidebar.classList.remove('open');
                if (overlay) overlay.classList.remove('active');
            }
        }
    }

    // Enhanced Demo functionality
    scrollToDemo() {
        console.log('Scroll to demo called');
        const featuresSection = document.getElementById('features');
        if (featuresSection) {
            featuresSection.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
            
            // Show a demo notification
            setTimeout(() => {
                this.showToast('Это демонстрация функций FinAI Dashboard. Зарегистрируйтесь для получения полного доступа!', 'info');
            }, 1000);
        } else {
            // If features section not found, show demo by logging in automatically
            this.showToast('Загружаем демо-версию...', 'info');
            setTimeout(() => {
                this.userData = this.appData.users[0];
                this.isAuthenticated = true;
                this.showMainApp();
                this.showToast('Добро пожаловать в демо-версию FinAI Dashboard!', 'success');
            }, 1500);
        }
    }

    /* =============== RSS MANAGEMENT FUNCTIONS =============== */

    showAddRssFeed() {
        console.log('showAddRssFeed called');
        this.editingFeedId = null;
        document.getElementById('rssModalTitle').textContent = 'Добавить RSS канал';
        document.getElementById('rssForm').reset();
        document.getElementById('priorityValue').textContent = '3';
        this.showElement('rssModal');
        
        // Focus first input for better UX
        setTimeout(() => {
            const firstInput = document.querySelector('#rssModal input[name="name"]');
            if (firstInput) firstInput.focus();
        }, 300);
    }

    showEditFeed(feedId) {
        console.log('showEditFeed called with id:', feedId);
        const feed = this.rssFeeds.find(f => f.id === feedId);
        if (!feed) {
            this.showToast('Канал не найден', 'error');
            return;
        }

        this.editingFeedId = feedId;
        document.getElementById('rssModalTitle').textContent = 'Редактировать RSS канал';
        
        const form = document.getElementById('rssForm');
        form.name.value = feed.name;
        form.url.value = feed.url;
        form.description.value = feed.description || '';
        form.category.value = feed.category;
        form.priority.value = feed.priority;
        document.getElementById('priorityValue').textContent = feed.priority;
        form.frequency.value = feed.fetch_frequency;
        form.autoAnalysis.checked = feed.auto_analysis;
        form.keywords.value = feed.keywords.join(', ');
        
        this.showElement('rssModal');
    }

    handleRssForm(event) {
        console.log('handleRssForm called');
        event.preventDefault();
        
        const form = event.target;
        const formData = {
            name: form.name.value.trim(),
            url: form.url.value.trim(),
            description: form.description.value.trim(),
            category: form.category.value,
            priority: parseInt(form.priority.value),
            frequency: form.frequency.value,
            autoAnalysis: form.autoAnalysis.checked,
            keywords: form.keywords.value.split(',').map(k => k.trim()).filter(Boolean)
        };

        // Validation
        if (!formData.name) {
            this.showToast('Введите название канала', 'error');
            return;
        }

        if (!formData.url) {
            this.showToast('Введите URL канала', 'error');
            return;
        }

        // URL validation
        try {
            new URL(formData.url);
        } catch {
            this.showToast('Некорректный URL', 'error');
            return;
        }

        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }

        if (this.editingFeedId) {
            // Update existing feed
            const feedIndex = this.rssFeeds.findIndex(f => f.id === this.editingFeedId);
            if (feedIndex !== -1) {
                this.rssFeeds[feedIndex] = {
                    ...this.rssFeeds[feedIndex],
                    name: formData.name,
                    url: formData.url,
                    description: formData.description,
                    category: formData.category,
                    priority: formData.priority,
                    fetch_frequency: formData.frequency,
                    auto_analysis: formData.autoAnalysis,
                    keywords: formData.keywords,
                    last_fetched: new Date().toISOString()
                };
                this.showToast('Канал обновлен', 'success');
            }
        } else {
            // Add new feed
            const newFeed = {
                id: Date.now().toString(),
                name: formData.name,
                url: formData.url,
                description: formData.description,
                category: formData.category,
                priority: formData.priority,
                is_active: true,
                auto_analysis: formData.autoAnalysis,
                keywords: formData.keywords,
                fetch_frequency: formData.frequency,
                error_count: 0,
                articles_count: 0,
                last_fetched: new Date().toISOString()
            };
            
            this.rssFeeds.push(newFeed);
            this.showToast('Канал добавлен', 'success');
        }

        this.hideElement('rssModal');
        this.populateRssFeeds();
        this.updateRssStats();
        
        return false;
    }

    testFeed(feedId) {
        console.log('testFeed called with id:', feedId);
        const feed = this.rssFeeds.find(f => f.id === feedId);
        if (!feed) return;

        this.showToast('Тестируем RSS канал...', 'info');
        
        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }

        // Simulate API test
        setTimeout(() => {
            const success = Math.random() > 0.2; // 80% success rate
            if (success) {
                this.showToast('Канал успешно протестирован', 'success');
                feed.error_count = 0;
                feed.last_fetched = new Date().toISOString();
            } else {
                this.showToast('Ошибка при загрузке RSS', 'error');
                feed.error_count += 1;
            }
            this.populateRssFeeds();
        }, 1500);
    }

    deleteFeed(feedId) {
        console.log('deleteFeed called with id:', feedId);
        const feed = this.rssFeeds.find(f => f.id === feedId);
        if (!feed) return;

        if (!confirm(`Удалить канал "${feed.name}"?`)) return;

        this.rssFeeds = this.rssFeeds.filter(f => f.id !== feedId);
        this.showToast('Канал удален', 'success');
        this.populateRssFeeds();
        this.updateRssStats();
        
        // Update analytics
        this.rssAnalytics.total_feeds = this.rssFeeds.length;
        this.rssAnalytics.active_feeds = this.rssFeeds.filter(f => f.is_active && f.error_count === 0).length;
        
        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(100);
        }
    }

    filterRssFeeds(filter) {
        console.log('filterRssFeeds called with filter:', filter);
        this.currentRssFeedFilter = filter;
        this.populateRssFeeds();
    }

    populateRssFeeds() {
        const container = document.getElementById('rssFeedsList');
        if (!container) return;

        let filteredFeeds = [...this.rssFeeds];

        // Apply filter
        switch (this.currentRssFeedFilter) {
            case 'active':
                filteredFeeds = filteredFeeds.filter(f => f.is_active && f.error_count === 0);
                break;
            case 'inactive':
                filteredFeeds = filteredFeeds.filter(f => !f.is_active);
                break;
            case 'error':
                filteredFeeds = filteredFeeds.filter(f => f.error_count > 0);
                break;
            default:
                // 'all' - no filtering needed
                break;
        }

        if (filteredFeeds.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px 20px; color: var(--color-text-secondary);">
                    <p>Каналы не найдены</p>
                    <button class="btn btn--primary" onclick="showAddRssFeed()">Добавить первый канал</button>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredFeeds.map(feed => {
            const categoryNames = {
                'financial': 'Финансы',
                'economics': 'Экономика',
                'technology': 'Технологии',
                'oil': 'Нефть',
                'commodities': 'Сырье',
                'geopolitics': 'Геополитика',
                'local': 'Локальные'
            };

            const frequencyNames = {
                'hourly': 'Каждый час',
                'daily': 'Ежедневно',
                'weekly': 'Еженедельно'
            };

            const statusClass = feed.error_count > 0 ? 'status-dot--error' : 
                               (feed.is_active ? 'status-dot--active' : 'status-dot--inactive');
            const statusText = feed.error_count > 0 ? `Ошибок: ${feed.error_count}` : 
                              (feed.is_active ? 'Активен' : 'Неактивен');

            return `
                <div class="rss-feed-card">
                    <div class="rss-feed-header">
                        <div class="rss-feed-info">
                            <div class="rss-feed-name">${feed.name}</div>
                            <div class="rss-feed-url">${feed.url}</div>
                            ${feed.description ? `<div style="font-size: 12px; color: var(--color-text-secondary); margin: 4px 0;">${feed.description}</div>` : ''}
                            <div class="rss-feed-meta">
                                <span class="rss-badge rss-badge--category">${categoryNames[feed.category] || feed.category}</span>
                                <span class="rss-badge rss-badge--priority">Приоритет: ${feed.priority}</span>
                                <span class="rss-badge rss-badge--frequency">${frequencyNames[feed.fetch_frequency] || feed.fetch_frequency}</span>
                                ${feed.auto_analysis ? '<span class="rss-badge rss-badge--category">AI анализ</span>' : ''}
                            </div>
                        </div>
                        <div class="rss-feed-status">
                            <span class="status-dot ${statusClass}"></span>
                            <span style="font-size: 11px;">${statusText}</span>
                        </div>
                    </div>
                    <div class="rss-feed-stats">
                        <span>Статей: ${feed.articles_count}</span>
                        <span>Обновлено: ${this.formatDateTime(feed.last_fetched)}</span>
                    </div>
                    ${feed.keywords.length > 0 ? `<div style="margin: 8px 0; font-size: 11px; color: var(--color-text-secondary);">Ключевые слова: ${feed.keywords.join(', ')}</div>` : ''}
                    <div class="rss-feed-actions">
                        <button class="btn btn--xs btn--outline touch-target" onclick="showEditFeed('${feed.id}')">Редактировать</button>
                        <button class="btn btn--xs btn--outline touch-target" onclick="testFeed('${feed.id}')">Тестировать</button>
                        <button class="btn btn--xs btn--outline touch-target" onclick="deleteFeed('${feed.id}')" style="color: var(--color-error);">Удалить</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateRssStats() {
        // Update RSS statistics in the UI
        const totalFeedsEl = document.getElementById('totalFeeds');
        const activeFeedsEl = document.getElementById('activeFeeds');
        const articlesAnalyzedEl = document.getElementById('articlesAnalyzed');
        const avgRelevanceEl = document.getElementById('avgRelevance');

        if (totalFeedsEl) totalFeedsEl.textContent = this.rssFeeds.length;
        if (activeFeedsEl) activeFeedsEl.textContent = this.rssFeeds.filter(f => f.is_active && f.error_count === 0).length;
        if (articlesAnalyzedEl) articlesAnalyzedEl.textContent = this.rssAnalytics.articles_analyzed;
        if (avgRelevanceEl) avgRelevanceEl.textContent = Math.round(this.rssAnalytics.avg_relevance * 100) + '%';
    }

    populateRssInsights() {
        const container = document.getElementById('rssInsights');
        if (!container) return;

        container.innerHTML = this.rssAnalytics.recent_analyses.map(analysis => `
            <div class="insight-card">
                <div class="insight-title">${analysis.title}</div>
                <div class="insight-content">
                    Влияние на рынок: ${analysis.market_impact === 'high' ? 'Высокое' : 
                                       analysis.market_impact === 'medium' ? 'Среднее' : 'Низкое'}
                </div>
                <div class="insight-meta">
                    <span class="relevance-score">Релевантность: ${Math.round(analysis.relevance * 100)}%</span>
                    <span>Настроение: ${analysis.sentiment > 0 ? '+' : ''}${analysis.sentiment}</span>
                    <span>Источник: ${analysis.source}</span>
                </div>
            </div>
        `).join('');
    }

    populateTopTopics() {
        const container = document.getElementById('topTopics');
        if (!container) return;

        container.innerHTML = this.rssAnalytics.top_topics.map(topic => `
            <div class="topic-item">
                <span class="topic-name">${topic.topic}</span>
                <div class="topic-stats">
                    <span class="topic-count">${topic.count}</span>
                    <span class="topic-relevance">${Math.round(topic.relevance * 100)}%</span>
                </div>
            </div>
        `).join('');
    }

    renderRssAnalyticsChart() {
        const canvas = document.getElementById('rssAnalyticsChart');
        if (!canvas || this.charts.rssAnalytics) return;

        const ctx = canvas.getContext('2d');
        const topics = this.rssAnalytics.top_topics.slice(0, 5);

        this.charts.rssAnalytics = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: topics.map(t => t.topic),
                datasets: [{
                    label: 'Количество статей',
                    data: topics.map(t => t.count),
                    backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F'],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    renderRssSentimentChart() {
        const canvas = document.getElementById('rssSentimentChart');
        if (!canvas || this.charts.rssSentiment) return;

        const ctx = canvas.getContext('2d');
        
        // Generate sample sentiment data for the past week
        const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
        const sentimentData = [0.1, 0.2, 0.05, 0.15, 0.08, 0.12, 0.15];

        this.charts.rssSentiment = new Chart(ctx, {
            type: 'line',
            data: {
                labels: days,
                datasets: [{
                    label: 'Среднее настроение',
                    data: sentimentData,
                    borderColor: '#1FB8CD',
                    backgroundColor: 'rgba(31, 184, 205, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#1FB8CD',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        min: -0.5,
                        max: 0.5,
                        ticks: {
                            callback: function(value) {
                                return value > 0 ? '+' + value : value.toString();
                            }
                        }
                    }
                }
            }
        });
    }

    /* =============== REMAINING ORIGINAL FUNCTIONS =============== */

    // Enhanced Notifications
    toggleNotifications() {
        const panel = document.getElementById('notificationsPanel');
        if (panel) {
            panel.classList.toggle('hidden');
            
            // Add haptic feedback
            if (navigator.vibrate && !panel.classList.contains('hidden')) {
                navigator.vibrate(30);
            }
        }
    }

    populateNotifications() {
        const container = document.getElementById('headerNotificationsList');
        if (!container) return;

        const notifications = this.appData.notifications;
        
        container.innerHTML = notifications.map(notification => `
            <div class="notification-item ${notification.read ? 'read' : ''}" style="padding: 12px; border-bottom: 1px solid var(--color-border); cursor: pointer;" onclick="app.markNotificationRead('${notification.id}')">
                <div class="notification-content">
                    <h4 style="margin: 0 0 4px 0; font-size: 14px;">${notification.title}</h4>
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: var(--color-text-secondary);">${notification.message}</p>
                    <small style="font-size: 10px; color: var(--color-text-secondary);">${this.formatDateTime(notification.timestamp)}</small>
                </div>
            </div>
        `).join('');

        // Update badge
        const unreadCount = notifications.filter(n => !n.read).length;
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? 'block' : 'none';
        }
    }

    markNotificationRead(notificationId) {
        const notification = this.appData.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.read = true;
            this.populateNotifications();
        }
    }

    markAllRead() {
        this.appData.notifications.forEach(n => n.read = true);
        this.populateNotifications();
        this.hideElement('notificationsPanel');
        this.showToast('Все уведомления отмечены как прочитанные', 'success');
    }

    toggleUserMenu() {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.classList.toggle('hidden');
            
            // Add haptic feedback
            if (navigator.vibrate && !dropdown.classList.contains('hidden')) {
                navigator.vibrate(30);
            }
        }
    }

    // Enhanced Dashboard
    populateDashboard() {
        this.populateAccountsList();
    }

    populateAccountsList() {
        const container = document.getElementById('accountsList');
        if (!container) return;

        container.innerHTML = this.appData.accounts.map(account => `
            <div class="account-card" onclick="showAccountDetails('${account.id}')">
                <div class="account-card-header">
                    <div class="account-name">${account.name}</div>
                    <div class="account-balance">${this.formatCurrency(account.balance, account.currency)}</div>
                </div>
                <div class="account-details">
                    <span>${account.bank}</span>
                    <span>${this.translateAccountType(account.type)}</span>
                </div>
                <div class="account-details">
                    <span>Обновлено: ${this.formatDateTime(account.lastTransaction)}</span>
                </div>
            </div>
        `).join('');
    }

    populateDetailedAccounts() {
        const container = document.getElementById('detailedAccountsList');
        if (!container) return;

        container.innerHTML = this.appData.accounts.map(account => `
            <div class="account-card mobile-card" style="margin-bottom: 16px;">
                <div class="account-card-header">
                    <div class="account-name" style="font-size: 16px; font-weight: 600;">${account.name}</div>
                    <div class="account-balance" style="font-size: 18px; font-weight: bold; color: var(--color-primary);">${this.formatCurrency(account.balance, account.currency)}</div>
                </div>
                <div class="account-details" style="margin-top: 8px;">
                    <span><strong>Банк:</strong> ${account.bank}</span>
                    <span><strong>Тип:</strong> ${this.translateAccountType(account.type)}</span>
                </div>
                <div class="account-details" style="margin-top: 4px;">
                    <span><strong>Последняя операция:</strong> ${this.formatDateTime(account.lastTransaction)}</span>
                </div>
                <div style="margin-top: 12px;">
                    <button class="btn btn--sm btn--outline touch-target" onclick="showAccountDetails('${account.id}')">Подробнее</button>
                </div>
            </div>
        `).join('');
    }

    addBankAccount() {
        this.showToast('Функция добавления банковского счета будет доступна в ближайшее время', 'info');
    }

    // Enhanced Charts with mobile optimization
    renderHeroChart() {
        const canvas = document.getElementById('heroChart');
        if (!canvas || canvas.chart) return;

        const ctx = canvas.getContext('2d');
        
        // Generate sample data for hero chart
        const data = this.appData.liquidityForecast.slice(0, 5).map((item, index) => ({
            x: index,
            y: item.balance / 1000000 // Convert to millions
        }));

        canvas.chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    data: data,
                    borderColor: '#1FB8CD',
                    backgroundColor: 'rgba(31, 184, 205, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { display: false },
                    y: { display: false }
                },
                elements: {
                    point: { radius: 0 }
                },
                interaction: {
                    intersect: false
                }
            }
        });
    }

    renderDashboardCharts() {
        setTimeout(() => {
            this.renderLiquidityForecastChart();
        }, 300);
    }

    renderLiquidityForecastChart() {
        const canvas = document.getElementById('liquidityForecastChart');
        if (!canvas || this.charts.liquidityForecast) return;

        const ctx = canvas.getContext('2d');
        
        const dates = this.appData.liquidityForecast.map(item => 
            new Date(item.date).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })
        );
        const balances = this.appData.liquidityForecast.map(item => item.balance / 1000000);

        this.charts.liquidityForecast = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Баланс (млн ₸)',
                    data: balances,
                    borderColor: '#1FB8CD',
                    backgroundColor: 'rgba(31, 184, 205, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#1FB8CD',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return value + ' млн ₸';
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    renderReportPreviewChart() {
        const canvas = document.getElementById('reportPreviewChart');
        if (!canvas || this.charts.reportPreview) return;

        const ctx = canvas.getContext('2d');

        this.charts.reportPreview = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Операционные', 'Резервные', 'Валютные'],
                datasets: [{
                    data: [125.3, 45.2, 75.2],
                    backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8
                    }
                }
            }
        });
    }

    // AI Consultant Functions
    sendChatMessage() {
        console.log('Send chat message called');
        const input = document.getElementById('chatInput');
        if (!input || !input.value.trim()) return;

        const message = input.value.trim();
        input.value = '';

        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }

        this.addChatMessage(message, 'user');
        
        // Show typing indicator
        setTimeout(() => {
            this.showTypingIndicator();
            
            // Simulate AI response delay
            setTimeout(() => {
                this.hideTypingIndicator();
                const response = this.generateAIResponse(message);
                this.addChatMessage(response, 'ai');
                
                // Add haptic feedback for response
                if (navigator.vibrate) {
                    navigator.vibrate([50, 100, 50]);
                }
            }, 2000);
        }, 500);
    }

    sendQuickMessage(message) {
        console.log('Send quick message called:', message);
        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }

        this.addChatMessage(message, 'user');
        
        setTimeout(() => {
            this.showTypingIndicator();
            
            setTimeout(() => {
                this.hideTypingIndicator();
                const response = this.generateAIResponse(message);
                this.addChatMessage(response, 'ai');
                
                // Add haptic feedback for response
                if (navigator.vibrate) {
                    navigator.vibrate([50, 100, 50]);
                }
            }, 2000);
        }, 500);
    }

    addChatMessage(text, sender) {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        const messageEl = document.createElement('div');
        messageEl.className = `chat-message chat-message--${sender}`;
        
        const avatar = sender === 'ai' ? '🤖' : '👤';
        const time = new Date().toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageEl.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${text}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        container.appendChild(messageEl);
        
        // Smooth scroll to bottom with mobile optimization
        requestAnimationFrame(() => {
            container.scrollTop = container.scrollHeight;
        });
    }

    showTypingIndicator() {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        // Remove existing indicator first
        this.hideTypingIndicator();

        const indicator = document.createElement('div');
        indicator.id = 'typingIndicator';
        indicator.className = 'chat-message chat-message--ai';
        indicator.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="message-text">
                    <div class="typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(indicator);
        
        // Smooth scroll to bottom
        requestAnimationFrame(() => {
            container.scrollTop = container.scrollHeight;
        });

        // Add typing animation styles if not exists
        if (!document.getElementById('typingStyles')) {
            const style = document.createElement('style');
            style.id = 'typingStyles';
            style.textContent = `
                .typing-dots {
                    display: flex;
                    gap: 4px;
                    align-items: center;
                }
                .typing-dots span {
                    width: 6px;
                    height: 6px;
                    background: currentColor;
                    border-radius: 50%;
                    animation: typing 1.4s infinite ease-in-out;
                }
                .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
                .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
                @keyframes typing {
                    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    generateAIResponse(question) {
        const lowerQuestion = question.toLowerCase();
        
        // RSS-specific responses
        if (lowerQuestion.includes('rss') || lowerQuestion.includes('новост')) {
            return `Анализ последних RSS новостей показывает следующие тенденции:

📈 **Ключевые темы:**
• Цены на нефть (+15% за неделю) - позитивно для экономики Казахстана
• Политика ФРС - ожидается стабилизация ставок
• Курс тенге - умеренное укрепление к доллару

🎯 **Рекомендации на основе RSS анализа:**
• Рассмотреть увеличение валютной позиции в USD
• Мониторить новости по нефтегазовому сектору
• Подготовиться к возможной волатильности

Всего проанализировано ${this.rssAnalytics.articles_analyzed} статей с релевантностью ${Math.round(this.rssAnalytics.avg_relevance * 100)}%.`;
        }
        
        // Original responses for liquidity, risks, etc.
        const responses = {
            'ликвидность': `Текущий уровень ликвидности вашей компании составляет 245.75 млн тенге, что соответствует статусу "Адекватная". 

Это хороший показатель, который обеспечивает покрытие операционных расходов на 42 дня вперед. 

Рекомендации:
• Поддерживать текущий уровень
• Рассмотреть размещение избыточных средств в краткосрочные инструменты
• Мониторить крупные платежи на этой неделе`,
            
            'размещение': `На основе прогноза превышения оптимального уровня ликвидности с 21 сентября рекомендую:

1. Разместить 15-20 млн тенге в краткосрочные депозиты (до 30 дней)
2. Рассмотреть возможность досрочного погашения дорогих кредитов
3. Инвестировать в высоколиквидные инструменты

Ожидаемая доходность: 12-15% годовых при сохранении ликвидности.`,
            
            'риск': `Анализ рисков на текущую неделю:

🟢 Уровень риска: НИЗКИЙ (2.1/10)

Основные факторы:
• Стабильные денежные потоки
• Диверсификация по банкам
• Адекватные резервы

Потенциальные риски:
• Валютные колебания (USD позиция)
• Задержка платежа 19 сентября (2.1 млн)

Рекомендация: Продолжить текущую стратегию управления рисками.`
        };

        for (const [key, response] of Object.entries(responses)) {
            if (lowerQuestion.includes(key)) {
                return response;
            }
        }

        return `Благодарю за вопрос! 

На основе текущих данных вашей компании и RSS анализа:
• Общий баланс: 245.75 млн ₸
• Статус ликвидности: Адекватная
• RSS каналов активных: ${this.rssFeeds.filter(f => f.is_active).length}
• Риск-уровень: Низкий

Рекомендую регулярно мониторить ключевые показатели и следить за RSS новостями для принятия оперативных решений. 

Для более детального анализа можете задать конкретный вопрос по ликвидности, рискам, RSS новостям или прогнозам.`;
    }

    clearChat() {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        container.innerHTML = `
            <div class="chat-message chat-message--ai">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="message-text">Чат очищен. Здравствуйте! Я ваш финансовый AI-ассистент с поддержкой RSS анализа. Чем могу помочь?</div>
                    <div class="message-time">Сейчас</div>
                </div>
            </div>
        `;
        
        this.showToast('Чат очищен', 'info');
    }

    loadConsultation(consultationId) {
        const consultation = this.appData.aiConsultations.find(c => c.id === consultationId);
        if (!consultation) return;

        this.clearChat();
        this.addChatMessage(consultation.question, 'user');
        
        setTimeout(() => {
            this.addChatMessage(consultation.response, 'ai');
        }, 500);
        
        // Navigate to AI consultant if not already there
        if (this.currentSection !== 'ai-consultant') {
            this.navigateTo('ai-consultant');
        }
    }

    populateConsultationHistory() {
        const container = document.getElementById('consultationHistory');
        if (!container) return;

        const consultations = this.appData.aiConsultations.slice(0, 5);
        
        container.innerHTML = consultations.map(consultation => `
            <div class="consultation-item touch-target" onclick="loadConsultation('${consultation.id}')" style="cursor: pointer; padding: 12px; border: 1px solid var(--color-border); border-radius: 8px; margin-bottom: 8px; transition: background-color 0.2s;">
                <div class="consultation-question" style="font-size: 14px; margin-bottom: 4px; font-weight: 500;">${consultation.question.substring(0, 50)}...</div>
                <div class="consultation-time" style="font-size: 12px; color: var(--color-text-secondary);">${this.formatDateTime(consultation.timestamp)}</div>
            </div>
        `).join('');
    }

    // Add remaining utility and action methods
    switchSettingsTab(tabName) {
        console.log('Switch settings tab:', tabName);
        // Update nav
        document.querySelectorAll('.settings-tab-btn').forEach(item => {
            item.classList.remove('active');
        });
        const activeNav = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeNav) {
            activeNav.classList.add('active');
        }

        // Update content
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        const activeTab = document.getElementById(`${tabName}-tab`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        this.currentSettingsTab = tabName;

        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(30);
        }
    }

    editApiKey(service) {
        this.showToast(`Функция редактирования API ключей будет доступна в полной версии`, 'info');
    }

    testApiKey(service) {
        this.showLoading(true);
        
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        setTimeout(() => {
            this.showLoading(false);
            const success = Math.random() > 0.3;
            
            if (success) {
                this.showToast(`Подключение к ${service} успешно`, 'success');
                if (navigator.vibrate) {
                    navigator.vibrate([50, 100, 50]);
                }
            } else {
                this.showToast(`Ошибка подключения к ${service}`, 'error');
                if (navigator.vibrate) {
                    navigator.vibrate([100, 100, 100]);
                }
            }
        }, 1500);
    }

    refreshData() {
        this.showLoading(true);
        
        setTimeout(() => {
            this.appData.accounts.forEach(account => {
                const variation = (Math.random() - 0.5) * 0.02;
                account.balance = Math.round(account.balance * (1 + variation));
                account.lastTransaction = new Date().toISOString();
            });
            
            this.populateAccountsList();
            this.populateDetailedAccounts();
            this.populateNotifications();
            
            Object.values(this.charts).forEach(chart => {
                if (chart && chart.update) {
                    chart.update();
                }
            });
            
            this.showLoading(false);
            this.showToast('Данные обновлены', 'success');
            
            if (navigator.vibrate) {
                navigator.vibrate([50, 100, 50]);
            }
        }, 2000);
    }

    syncAccounts() {
        this.showLoading(true);
        
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        setTimeout(() => {
            this.appData.accounts.forEach(account => {
                const variation = (Math.random() - 0.5) * 0.02;
                account.balance = Math.round(account.balance * (1 + variation));
                account.lastTransaction = new Date().toISOString();
            });
            
            this.populateAccountsList();
            this.populateDetailedAccounts();
            this.showLoading(false);
            this.showToast('Счета синхронизированы', 'success');
            
            if (navigator.vibrate) {
                navigator.vibrate([50, 100, 50]);
            }
        }, 2000);
    }

    generateReport() {
        this.showLoading(true);
        
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        setTimeout(() => {
            this.showLoading(false);
            this.navigateTo('reports');
            this.showToast('Отчет готов к просмотру', 'success');
            
            if (navigator.vibrate) {
                navigator.vibrate([50, 100, 50]);
            }
        }, 1500);
    }

    exportData() {
        const data = {
            timestamp: new Date().toISOString(),
            accounts: this.appData.accounts,
            metrics: this.appData.dashboardMetrics,
            forecast: this.appData.liquidityForecast,
            rssFeeds: this.rssFeeds,
            rssAnalytics: this.rssAnalytics
        };
        
        if (navigator.share) {
            const blob = new Blob([JSON.stringify(data, null, 2)], { 
                type: 'application/json' 
            });
            const file = new File([blob], `finai_export_${new Date().toISOString().split('T')[0]}.json`, {
                type: 'application/json'
            });
            
            navigator.share({
                files: [file],
                title: 'FinAI Data Export',
                text: 'Экспорт данных из FinAI Dashboard'
            }).then(() => {
                this.showToast('Данные экспортированы', 'success');
            }).catch(() => {
                this.fallbackExportData(data);
            });
        } else {
            this.fallbackExportData(data);
        }
    }

    fallbackExportData(data) {
        try {
            const blob = new Blob([JSON.stringify(data, null, 2)], { 
                type: 'application/json' 
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `finai_export_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showToast('Данные экспортированы', 'success');
        } catch (error) {
            this.showToast('Ошибка экспорта данных', 'error');
        }
    }

    createReport() {
        this.showToast('Создание отчета...', 'info');
        
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        setTimeout(() => {
            this.showToast('Отчет создан и добавлен в список', 'success');
            
            if (navigator.vibrate) {
                navigator.vibrate([50, 100, 50]);
            }
        }, 2000);
    }

    downloadReport(reportType) {
        this.showToast('Загрузка отчета...', 'info');
        
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        setTimeout(() => {
            this.showToast('Отчет загружен', 'success');
            
            if (navigator.vibrate) {
                navigator.vibrate([50, 100, 50]);
            }
        }, 1500);
    }

    previewReport(reportType) {
        this.showToast('Предпросмотр отчета готов', 'info');
    }

    showAccountDetails(accountId) {
        const account = this.appData.accounts.find(a => a.id === accountId);
        if (!account) return;

        this.showToast(`${account.name}: ${this.formatCurrency(account.balance, account.currency)}`, 'info');
        
        if (navigator.vibrate) {
            navigator.vibrate(30);
        }
    }

    uploadAvatar() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.capture = 'environment';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                this.showToast('Функция загрузки аватара будет доступна в ближайшее время', 'info');
            }
        };
        input.click();
    }

    // Enhanced Utility Methods
    showElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('hidden');
        }
    }

    hideElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('hidden');
        }
    }

    closeModal(modalId) {
        if (modalId) {
            this.hideElement(modalId);
        }
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    showLoading(show) {
        if (show) {
            this.showElement('loadingOverlay');
        } else {
            this.hideElement('loadingOverlay');
        }
    }

    showToast(message, type = 'info') {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container mobile-toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        toast.innerHTML = `
            <div class="toast-content" style="display: flex; align-items: center; justify-content: space-between;">
                <span style="flex: 1; padding-right: 12px;">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; cursor: pointer; font-size: 18px; color: var(--color-text-secondary); padding: 4px; min-width: 32px; min-height: 32px; display: flex; align-items: center; justify-content: center;" aria-label="Закрыть">&times;</button>
            </div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-100%)';
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);

        if (type === 'error' && navigator.vibrate) {
            navigator.vibrate([100, 100, 100]);
        } else if (type === 'success' && navigator.vibrate) {
            navigator.vibrate([50, 100, 50]);
        }
    }

    formatCurrency(amount, currency = 'KZT') {
        const formatter = new Intl.NumberFormat('ru-RU');
        const symbols = {
            'KZT': '₸',
            'USD': '$',
            'EUR': '€'
        };
        
        return `${formatter.format(amount)} ${symbols[currency] || currency}`;
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInHours = (now - date) / (1000 * 60 * 60);
        
        if (diffInHours < 1) {
            const diffInMinutes = Math.floor((now - date) / (1000 * 60));
            return `${diffInMinutes} мин назад`;
        } else if (diffInHours < 24) {
            return `${Math.floor(diffInHours)} ч назад`;
        } else {
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    translateAccountType(type) {
        const translations = {
            'operational': 'Операционный',
            'currency': 'Валютный',
            'reserve': 'Резервный'
        };
        return translations[type] || type;
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - initializing FinAI Dashboard');
    // Create the app instance
    window.finAiApp = new FinancialDashboardApp();
});

// Also try to initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    // Do nothing, DOMContentLoaded will fire
} else {
    // DOM is already loaded
    console.log('DOM already loaded - initializing FinAI Dashboard immediately');
    window.finAiApp = new FinancialDashboardApp();
}