CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Entertainment",
    "Health & Medical", "Housing", "Utilities", "Travel", "Education", "Other",
]

# order matters: "uber eats" has to match before "uber"
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("Food & Dining", [
        "uber eats", "doordash", "skip the dishes", "skipthedishes", "tim hortons", "starbucks",
        "mcdonald", "subway", "a&w", "wendy", "burger", "pizza", "sushi", "restaurant", "cafe",
        "coffee", "bakery", "grill", "loblaws", "no frills", "sobeys", "metro", "food basics",
        "fortinos", "freshco", "farm boy", "grocery", "chipotle", "osmow", "popeyes",
    ]),
    ("Transportation", [
        "presto", "go transit", "ttc", "hsr", "uber", "lyft", "esso", "petro-canada", "petro canada",
        "shell", "pioneer", "ultramar", "gas station", "parking", "impark", "407 etr",
    ]),
    ("Entertainment", [
        "netflix", "spotify", "disney", "crave", "apple music", "youtube", "cineplex", "steam",
        "playstation", "xbox", "nintendo", "ticketmaster", "twitch", "prime video",
    ]),
    ("Health & Medical", [
        "shoppers drug", "rexall", "pharmacy", "pharma", "dental", "dentist", "clinic",
        "physio", "optometr", "goodlife", "fit4less", "gym",
    ]),
    ("Utilities", [
        "rogers", "bell canada", "telus", "fido", "koodo", "freedom mobile", "virgin plus",
        "hydro", "enbridge", "alectra", "internet", "water bill",
    ]),
    ("Housing", ["rent", "landlord", "mortgage", "property management", "condo fee"]),
    ("Travel", [
        "air canada", "westjet", "porter", "flair", "airbnb", "hotel", "marriott", "hilton",
        "expedia", "booking.com", "via rail",
    ]),
    ("Education", [
        "mcmaster", "tuition", "textbook", "campus store", "bookstore", "coursera", "udemy",
        "chegg", "pearson", "leetcode",
    ]),
    ("Shopping", [
        "amazon", "amzn", "walmart", "costco", "best buy", "winners", "indigo", "canadian tire",
        "dollarama", "ikea", "h&m", "zara", "uniqlo", "apple store", "sport chek", "aritzia",
    ]),
]


def categorize_by_keywords(text: str) -> str | None:
    lowered = text.lower()
    for category, keywords in KEYWORD_RULES:
        if any(k in lowered for k in keywords):
            return category
    return None
