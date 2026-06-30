"""RSS feeds for EV charging news — LOCAL-LANGUAGE sources per market.

Each region gets feeds from LOCAL news outlets in LOCAL languages.
The LLM pipeline detects non-English articles and translates them.
"""

SOURCES = {
    "korea": {
        "name": "South Korea",
        "language": "ko",
        "feeds": [
            # Korean-language sources
            {"url": "https://www.yna.co.kr/rss/industry.xml", "name": "연합뉴스 산업", "language": "ko"},
            {"url": "https://www.hankyung.com/feed/all-news", "name": "한국경제", "language": "ko"},
            {"url": "https://www.hani.co.kr/rss/", "name": "한겨레", "language": "ko"},
            {"url": "https://rss.etnews.com/Section901.xml", "name": "전자신문", "language": "ko"},
        ],
        "google_news_query": "전기차 충전 인프라 EV",
        "geo_keywords": [
            "korea", "korean", "seoul", "busan",
            "전기차", "충전", "한국", "서울",
            "ev charg", "electric vehicle",
        ],
    },
    "uae": {
        "name": "UAE / Middle East",
        "language": "ar",
        "feeds": [
            # Arabic sources
            {"url": "https://www.aljazeera.net/rss", "name": "الجزيرة نت", "language": "ar"},
            {"url": "https://www.albawaba.com/rss/ar-all", "name": "البوابة", "language": "ar"},
            # English sources
            {"url": "https://www.aljazeera.com/xml/rss/all.xml", "name": "Al Jazeera", "language": "en"},
            {"url": "https://www.arabnews.com/rss.xml", "name": "Arab News", "language": "en"},
            {"url": "https://gulfnews.com/rss/business", "name": "Gulf News", "language": "en"},
            {"url": "https://www.khaleejtimes.com/rss", "name": "Khaleej Times", "language": "en"},
        ],
        "google_news_query": "EV charging UAE Middle East شحن السيارات الكهربائية",
        "geo_keywords": [
            "uae", "dubai", "abu dhabi", "saudi", "riyadh", "qatar", "doha",
            "gcc", "middle east", "شحن", "سيارة كهربائية",
            "ev charg",
        ],
    },
    "southeast_asia": {
        "name": "Southeast Asia",
        "language": "en",
        "feeds": [
            {"url": "https://www.channelnewsasia.com/rss", "name": "CNA", "language": "en"},
            {"url": "https://www.straitstimes.com/rss/asia.xml", "name": "Straits Times", "language": "en"},
            {"url": "https://www.bangkokpost.com/rss/data/general.xml", "name": "Bangkok Post", "language": "en"},
            {"url": "https://www.thestar.com.my/rss/News", "name": "The Star MY", "language": "en"},
            {"url": "https://rss.vnexpress.net/rss/tin-moi.xml", "name": "VnExpress", "language": "vi"},
        ],
        "google_news_query": "pengisian daya EV mobil listrik ASEAN xe điện sạc",
        "geo_keywords": [
            "singapore", "thailand", "indonesia", "vietnam", "malaysia",
            "asean", "sea ev", "mobil listrik", "xe điện", "ชาร์จ EV",
            "ev charg",
        ],
    },
    "japan": {
        "name": "Japan",
        "language": "ja",
        "feeds": [
            # Japanese-language sources
            {"url": "https://response.jp/rss20/index.rdf", "name": "レスポンス", "language": "ja"},
            {"url": "https://bestcarweb.jp/feed", "name": "ベストカー", "language": "ja"},
            {"url": "https://motor-fan.jp/feed/", "name": "モーターファン", "language": "ja"},
            # English sources
            {"url": "https://www.japantimes.co.jp/feed/", "name": "Japan Times", "language": "en"},
            {"url": "https://asia.nikkei.com/rss", "name": "Nikkei Asia", "language": "en"},
        ],
        "google_news_query": "EV充電 電気自動車 充電インフラ Japan",
        "geo_keywords": [
            "japan", "japanese", "tokyo", "osaka",
            "充電", "電気自動車", "EV充電",
            "ev charg",
        ],
    },
    "australia": {
        "name": "Australia",
        "language": "en",
        "feeds": [
            {"url": "https://www.abc.net.au/news/feed/51120/rss.xml", "name": "ABC News AU", "language": "en"},
            {"url": "https://www.drive.com.au/feed/", "name": "Drive.com.au", "language": "en"},
            {"url": "https://www.whichcar.com.au/feed/", "name": "WhichCar", "language": "en"},
        ],
        "google_news_query": "EV charging Australia electric vehicle infrastructure",
        "geo_keywords": [
            "australia", "sydney", "melbourne", "brisbane",
            "chargefox", "evie networks", "tesla australia",
            "ev charg",
        ],
    },
    "taiwan": {
        "name": "Taiwan",
        "language": "zh",
        "feeds": [
            # Chinese-language sources
            {"url": "https://udn.com/rss/news/life/transport", "name": "聯合新聞網", "language": "zh"},
            {"url": "https://www.cna.com.tw/rss/news.xml", "name": "中央社", "language": "zh"},
            # English source
            {"url": "https://www.taipeitimes.com/xml/rss.xml", "name": "Taipei Times", "language": "en"},
        ],
        "google_news_query": "電動車充電 台灣 EV充電站",
        "geo_keywords": [
            "taiwan", "taipei",
            "電動車", "充電", "台灣",
            "gogoro", "ev charg",
        ],
    },
    "africa": {
        "name": "Africa / South Africa",
        "language": "en",
        "feeds": [
            {"url": "https://www.news24.com/rss/fin24", "name": "News24 Fin24", "language": "en"},
            {"url": "https://www.businesslive.co.za/rss/?publication=bd", "name": "Business Day SA", "language": "en"},
        ],
        "google_news_query": "EV charging Africa South Africa electric vehicle",
        "geo_keywords": [
            "south africa", "cape town", "johannesburg",
            "africa", "kenya", "nigeria", "egypt",
            "ev charg", "electric vehicle",
        ],
    },
    "brazil": {
        "name": "Brazil",
        "language": "pt",
        "feeds": [
            # Portuguese-language sources
            {"url": "https://g1.globo.com/rss/g1/carros", "name": "G1 Carros", "language": "pt"},
            {"url": "https://rss.uol.com.br/feed/carros.xml", "name": "UOL Carros", "language": "pt"},
            {"url": "https://quatrorodas.abril.com.br/feed/", "name": "Quatro Rodas", "language": "pt"},
            {"url": "https://www.canaltech.com.br/rss/", "name": "Canaltech", "language": "pt"},
        ],
        "google_news_query": "carregamento veículo elétrico Brasil EV",
        "geo_keywords": [
            "brazil", "brasil", "sao paulo",
            "carregamento", "veículo elétrico", "carro elétrico",
            "ev charg",
        ],
    },
    "mexico": {
        "name": "Mexico / Central America",
        "language": "es",
        "feeds": [
            # Spanish-language sources
            {"url": "https://expansion.mx/rss", "name": "Expansión", "language": "es"},
            {"url": "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml", "name": "El Financiero", "language": "es"},
            {"url": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml", "name": "La Tercera", "language": "es"},
        ],
        "google_news_query": "carga vehículos eléctricos México EV estaciones de carga",
        "geo_keywords": [
            "mexico", "mexican", "méxico", "mexico city",
            "carga", "vehículo eléctrico", "estación de carga",
            "ev charg", "latin america",
        ],
    },
}

CATEGORIES = ["service", "trend", "policy", "other"]
