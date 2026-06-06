"""RSS feeds for EV charging news — REGION-SPECIFIC sources only.

Each region uses LOCAL news sources that cover that market.
No global feeds — every article must be geographically relevant.
"""

SOURCES = {
    "korea": {
        "name": "South Korea",
        "feeds": [
            # Korean English-language business/tech news
            {"url": "https://www.koreaherald.com/rss/020200000000.xml", "name": "Korea Herald", "language": "en"},
            {"url": "https://www.koreatimes.co.kr/rss/biz.xml", "name": "Korea Times", "language": "en"},
            {"url": "https://koreajoongangdaily.joins.com/section/rss/200", "name": "JoongAng Daily", "language": "en"},
            {"url": "https://www.yna.co.kr/RSS/news.xml", "name": "Yonhap News", "language": "en"},
        ],
        "geo_keywords": [
            "korea", "korean", "seoul", "busan", "incheon", "daejeon",
            "sk innovation", "samsung sdi", "lg energy", "kepco",
            "hyundai", "genesis", "kia ev", "ev charg", "충전",
            "한국", "서울", "전기차",
        ],
    },
    "uae": {
        "name": "UAE / Middle East",
        "feeds": [
            {"url": "https://gulfnews.com/rss/business", "name": "Gulf News", "language": "en"},
            {"url": "https://www.khaleejtimes.com/rss", "name": "Khaleej Times", "language": "en"},
            {"url": "https://www.arabianbusiness.com/rss", "name": "Arabian Business", "language": "en"},
            {"url": "https://wam.ae/en/rss", "name": "WAM", "language": "en"},
        ],
        "geo_keywords": [
            "uae", "dubai", "abu dhabi", "sharjah", "ajman",
            "saudi", "riyadh", "jeddah", "qatar", "doha",
            "bahrain", "oman", "kuwait", "middle east", "gcc",
            "dewa", "adnoc", "emas", "ewa",
        ],
    },
    "southeast_asia": {
        "name": "Southeast Asia",
        "feeds": [
            {"url": "https://www.channelnewsasia.com/rss", "name": "CNA", "language": "en"},
            {"url": "https://www.straitstimes.com/rss/asia.xml", "name": "Straits Times", "language": "en"},
            {"url": "https://www.bangkokpost.com/rss/data/general.xml", "name": "Bangkok Post", "language": "en"},
            {"url": "https://www.thestar.com.my/rss/News", "name": "The Star MY", "language": "en"},
        ],
        "geo_keywords": [
            "singapore", "thailand", "bangkok", "indonesia", "jakarta",
            "vietnam", "hanoi", "ho chi minh", "malaysia", "kuala lumpur",
            "philippines", "manila", "asean", "sea ev",
            "ac mobility", "sp mobility", "grabcargo", "byd sea",
        ],
    },
    "japan": {
        "name": "Japan",
        "feeds": [
            {"url": "https://www.japantimes.co.jp/feed/", "name": "Japan Times", "language": "en"},
            {"url": "https://asia.nikkei.com/rss", "name": "Nikkei Asia", "language": "en"},
            {"url": "https://english.kyodonews.net/rss/all.xml", "name": "Kyodo News", "language": "en"},
        ],
        "geo_keywords": [
            "japan", "japanese", "tokyo", "osaka", "nagoya", "yokohama",
            "toyota", "nissan", "honda", "mazda", "subaru",
            "chademo", "japan ev", "charge networking",
        ],
    },
    "australia": {
        "name": "Australia",
        "feeds": [
            {"url": "https://www.abc.net.au/news/feed/51120/rss.xml", "name": "ABC News AU", "language": "en"},
            {"url": "https://www.drive.com.au/feed/", "name": "Drive.com.au", "language": "en"},
            {"url": "https://www.which-50.com/feed/", "name": "Which-50", "language": "en"},
        ],
        "geo_keywords": [
            "australia", "australian", "sydney", "melbourne", "brisbane",
            "perth", "adelaide", "act ev", "nsw ev", "vic ev",
            "tesla australia", "chargefox", "evie networks",
        ],
    },
    "taiwan": {
        "name": "Taiwan",
        "feeds": [
            {"url": "https://www.taipeitimes.com/xml/rss.xml", "name": "Taipei Times", "language": "en"},
        ],
        "geo_keywords": [
            "taiwan", "taipei", "kaohsiung", "taichung",
            "foxconn", "pegatron", "taiwan ev", "gogoro",
        ],
    },
    "africa": {
        "name": "Africa / South Africa",
        "feeds": [
            {"url": "https://www.news24.com/rss/fin24", "name": "News24 Fin24", "language": "en"},
            {"url": "https://www.businesslive.co.za/rss/?publication=bd", "name": "Business Day SA", "language": "en"},
        ],
        "geo_keywords": [
            "south africa", "cape town", "johannesburg", "durban",
            "africa", "kenya", "nigeria", "ghana", "egypt",
            "african ev", "load shedding ev",
        ],
    },
    "brazil": {
        "name": "Brazil",
        "feeds": [
            {"url": "https://www.reuters.com/arc/outboundfeeds/v3/all/rss.xml", "name": "Reuters LatAm", "language": "en"},
            {"url": "https://www.bnamericas.com/en/rss", "name": "BN Americas", "language": "en"},
        ],
        "geo_keywords": [
            "brazil", "brazilian", "sao paulo", "rio de janeiro",
            "byd brazil", "volkswagen brazil", "fiat brazil",
            "carregamento", "veículo elétrico",
        ],
    },
    "mexico": {
        "name": "Mexico / Central America",
        "feeds": [
            {"url": "https://www.reuters.com/arc/outboundfeeds/v3/all/rss.xml", "name": "Reuters LatAm", "language": "en"},
            {"url": "https://www.bnamericas.com/en/rss", "name": "BN Americas", "language": "en"},
        ],
        "geo_keywords": [
            "mexico", "mexican", "mexico city", "monterrey",
            "tesla gigafactory mexico", "bmw mexico", "audi mexico",
            "latin america ev", "centroamerica",
        ],
    },
}

# Categories for classification
CATEGORIES = ["service", "trend", "policy", "other"]
