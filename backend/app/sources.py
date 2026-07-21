"""RSS feeds for EV charging news — LOCAL-LANGUAGE sources per market.

Each region gets feeds from local news outlets in local languages.
The LLM pipeline detects non-English articles and translates them.

Source confidence tags:
  - stable: reliable feed, online for >3 months
  - experimental: new feed, may be intermittent
"""

SOURCES = {
    "korea": {
        "name": "South Korea",
        "language": "ko",
        "feeds": [
            # Korean-language sources
            {"url": "https://www.yna.co.kr/rss/industry.xml", "name": "연합뉴스 산업", "language": "ko", "confidence": "stable"},
            # 한국경제 RSS returns 403 — blocked
            {"url": "https://www.hani.co.kr/rss/", "name": "한겨레", "language": "ko", "confidence": "stable"},
            {"url": "https://rss.etnews.com/Section901.xml", "name": "전자신문", "language": "ko", "confidence": "stable"},
        ],
        "google_news_query": "전기차 충전 인프라 EV",
        "geo_keywords": [
            "korea", "korean", "seoul", "busan",
            "전기차", "충전", "한국", "서울",
            "ev charg", "electric vehicle",
        ],
        "source_confidence": "stable",
    },
    "uae": {
        "name": "UAE / Middle East",
        "language": "ar",
        "feeds": [
            # Arabic sources
            {"url": "https://www.aljazeera.net/rss", "name": "الجزيرة نت", "language": "ar", "confidence": "stable"},
            {"url": "https://www.albawaba.com/rss/ar-all", "name": "البوابة", "language": "ar", "confidence": "experimental"},
            # English sources
            {"url": "https://www.aljazeera.com/xml/rss/all.xml", "name": "Al Jazeera", "language": "en", "confidence": "stable"},
            {"url": "https://www.arabnews.com/rss.xml", "name": "Arab News", "language": "en", "confidence": "stable"},
            {"url": "https://gulfnews.com/rss/business", "name": "Gulf News", "language": "en", "confidence": "stable"},
            {"url": "https://www.khaleejtimes.com/rss", "name": "Khaleej Times", "language": "en", "confidence": "stable"},
        ],
        "google_news_query": "شحن السيارات الكهربائية الإمارات",
        "geo_keywords": [
            "uae", "dubai", "abu dhabi", "saudi", "riyadh", "qatar", "doha",
            "gcc", "middle east", "شحن", "سيارة كهربائية",
            "ev charg",
        ],
        "source_confidence": "stable",
    },
    "southeast_asia": {
        "name": "Southeast Asia",
        "language": "en",
        "feeds": [
            {"url": "https://www.channelnewsasia.com/rss", "name": "CNA", "language": "en", "confidence": "stable"},
            {"url": "https://www.straitstimes.com/rss/asia.xml", "name": "Straits Times", "language": "en", "confidence": "stable"},
            {"url": "https://www.bangkokpost.com/rss/data/general.xml", "name": "Bangkok Post", "language": "en", "confidence": "stable"},
            {"url": "https://www.thestar.com.my/rss/News", "name": "The Star MY", "language": "en", "confidence": "stable"},
            # VnExpress RSS DNS failure
            # {"url": "https://rss.vnexpress.net/rss/tin-moi.xml", "name": "VnExpress", "language": "vi", "confidence": "stable"},
        ],
        "google_news_query": "EV charging electric vehicle ASEAN Singapore Thailand Indonesia Vietnam",
        "geo_keywords": [
            "singapore", "thailand", "indonesia", "vietnam", "malaysia",
            "asean", "sea ev", "mobil listrik", "xe điện", "ชาร์จ EV",
            "ev charg",
        ],
        "source_confidence": "stable",
    },
    "japan": {
        "name": "Japan",
        "language": "ja",
        "feeds": [
            # Japanese-language sources
            {"url": "https://response.jp/rss20/index.rdf", "name": "レスポンス", "language": "ja", "confidence": "stable"},
            {"url": "https://bestcarweb.jp/feed", "name": "ベストカー", "language": "ja", "confidence": "experimental"},
            {"url": "https://motor-fan.jp/feed/", "name": "モーターファン", "language": "ja", "confidence": "experimental"},
            # English sources
            {"url": "https://www.japantimes.co.jp/feed/", "name": "Japan Times", "language": "en", "confidence": "stable"},
            {"url": "https://asia.nikkei.com/rss", "name": "Nikkei Asia", "language": "en", "confidence": "stable"},
        ],
        "google_news_query": "EV充電 電気自動車 充電インフラ Japan",
        "geo_keywords": [
            "japan", "japanese", "tokyo", "osaka",
            "充電", "電気自動車", "EV充電",
            "ev charg",
        ],
        "source_confidence": "stable",
    },
    "australia": {
        "name": "Australia",
        "language": "en",
        "feeds": [
            {"url": "https://www.abc.net.au/news/feed/51120/rss.xml", "name": "ABC News AU", "language": "en", "confidence": "stable"},
            {"url": "https://www.drive.com.au/feed/", "name": "Drive.com.au", "language": "en", "confidence": "stable"},
            {"url": "https://www.whichcar.com.au/feed/", "name": "WhichCar", "language": "en", "confidence": "experimental"},
        ],
        "google_news_query": "EV charging Australia electric vehicle infrastructure",
        "geo_keywords": [
            "australia", "sydney", "melbourne", "brisbane",
            "chargefox", "evie networks", "tesla australia",
            "ev charg",
        ],
        "source_confidence": "stable",
    },
    "taiwan": {
        "name": "Taiwan",
        "language": "zh",
        "feeds": [
            # Chinese-language sources
            # 聯合新聞網 302/XML parse error, 中央社 404 — both broken
            # {"url": "https://udn.com/rss/news/life/transport", "name": "聯合新聞網", "language": "zh", "confidence": "stable"},
            # {"url": "https://www.cna.com.tw/rss/news.xml", "name": "中央社", "language": "zh", "confidence": "stable"},
            # English source
            {"url": "https://www.taipeitimes.com/xml/rss.xml", "name": "Taipei Times", "language": "en", "confidence": "stable"},
        ],
        "google_news_query": "電動車充電 台灣 EV充電站",
        "geo_keywords": [
            "taiwan", "taipei",
            "電動車", "充電", "台灣",
            "gogoro", "ev charg",
        ],
        "source_confidence": "stable",
    },
    "africa": {
        "name": "Africa / South Africa",
        "language": "en",
        "feeds": [
            {"url": "https://www.news24.com/rss/fin24", "name": "News24 Fin24", "language": "en", "confidence": "stable"},
            {"url": "https://www.businesslive.co.za/rss/?publication=bd", "name": "Business Day SA", "language": "en", "confidence": "stable"},
        ],
        "google_news_query": "EV charging Africa South Africa electric vehicle",
        "geo_keywords": [
            "south africa", "cape town", "johannesburg",
            "africa", "kenya", "nigeria", "egypt",
            "ev charg", "electric vehicle",
        ],
        "source_confidence": "experimental",
    },
    "brazil": {
        "name": "Brazil",
        "language": "pt",
        "feeds": [
            # Portuguese-language sources
            {"url": "https://g1.globo.com/rss/g1/carros", "name": "G1 Carros", "language": "pt", "confidence": "stable"},
            {"url": "https://rss.uol.com.br/feed/carros.xml", "name": "UOL Carros", "language": "pt", "confidence": "stable"},
            {"url": "https://quatrorodas.abril.com.br/feed/", "name": "Quatro Rodas", "language": "pt", "confidence": "stable"},
            {"url": "https://www.canaltech.com.br/rss/", "name": "Canaltech", "language": "pt", "confidence": "stable"},
        ],
        "google_news_query": "carregamento veículo elétrico Brasil EV",
        "geo_keywords": [
            "brazil", "brasil", "sao paulo",
            "carregamento", "veículo elétrico", "carro elétrico",
            "ev charg",
        ],
        "source_confidence": "stable",
    },
    "mexico": {
        "name": "Mexico / Central America",
        "language": "es",
        "feeds": [
            # Spanish-language sources
            {"url": "https://expansion.mx/rss", "name": "Expansión", "language": "es", "confidence": "stable"},
            {"url": "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml", "name": "El Financiero", "language": "es", "confidence": "stable"},
            {"url": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml", "name": "La Tercera", "language": "es", "confidence": "stable"},
        ],
        "google_news_query": "carga vehículos eléctricos México EV estaciones de carga",
        "geo_keywords": [
            "mexico", "mexican", "méxico", "mexico city",
            "carga", "vehículo eléctrico", "estación de carga",
            "ev charg", "latin america",
        ],
        "source_confidence": "experimental",
    },
}

# Category definitions (priority order — highest first)
# Used for primary category assignment when an article matches multiple
CATEGORY_PRIORITY = [
    "government_policy",   # Regulations, subsidies, incentives, government actions
    "ma_partnership",      # M&A, partnerships, funding rounds, joint ventures
    "charger_install",     # Charger installation, expansion, infrastructure builds
    "charging_standards",  # NACS, CCS, charging tech standards, interoperability
    "grid_pricing",        # Power grid, electricity pricing, energy policy
    "ev_sales_stats",      # EV sales data, charger counts, market statistics
]

CATEGORY_NAMES = {
    "government_policy": "📋 Policy",
    "ma_partnership": "🤝 M&A / Partnerships",
    "charger_install": "⚡ Charger Install",
    "charging_standards": "🔌 Standards",
    "grid_pricing": "⚡ Grid / Pricing",
    "ev_sales_stats": "📊 EV Sales / Stats",
}

CATEGORY_KEYWORDS = {
    "government_policy": [
        "subsidy", "incentive", "regulation", "mandate", "policy", "government",
        "ministry", "department of", "public consultation", "tax credit",
        "grant", "funding program", "legislation", "decree", "law",
        "보조금", "정책", "규제", "법안", "지원금",
        "補助金", "政策", "規制", "補助",
        "subsídio", "incentivo", "regulamentação", "política",
        "subvención", "incentivo", "regulación", "política",
    ],
    "ma_partnership": [
        "acquisition", "merger", "partnership", "joint venture", "investment",
        "funding round", "series a", "series b", "ipo", "stake",
        "투자", "인수", "합작", "파트너십", "자금 조달",
        "買収", "合併", "提携", "出資", "投資",
        "aquisição", "fusão", "parceria", "investimento",
        "adquisición", "fusión", "asociación", "inversión",
    ],
    "charger_install": [
        "charging station", "charging point", "charger installation",
        "charging infrastructure", "charging hub", "charger deployment",
        "fast charging", "ultra-fast", "supercharger",
        "충전소", "충전기", "급속 충전", "충전 인프라",
        "充電スタンド", "充電インフラ", "充電器",
        "estação de carga", "carregador", "infraestrutura de carga",
        "estación de carga", "punto de recarga", "infraestructura de carga",
    ],
    "charging_standards": [
        "nacs", "ccs", "chademo", "charging standard", "interoperability",
        "plug standard", "megawatt charging", "mcs",
        "충전 표준", "NACS", "CCS",
        "充電規格", "NACS", "CCS",
        "padrão de carregamento",
        "estándar de carga",
    ],
    "grid_pricing": [
        "electricity price", "tariff", "grid capacity", "demand charge",
        "time-of-use", "v2g", "vehicle-to-grid", "smart charging",
        "renewable energy", "solar charging", "grid integration",
        "전기 요금", "전력망", "충전 요금",
        "電気料金", "電力網", "充電料金",
        "tarifa", "preço da eletricidade", "rede elétrica",
        "tarifa", "precio de electricidad", "red eléctrica",
    ],
    "ev_sales_stats": [
        "ev sales", "ev adoption", "ev market share", "ev registration",
        "ev penetration", "ev fleet", "electric vehicle sales",
        "전기차 판매", "EV 판매량", "전기차 보급",
        "EV販売", "電気自動車販売", "EV普及",
        "venda de veículos elétricos", "adoção de EV",
        "venta de vehículos eléctricos", "adopción de EV",
    ],
}
