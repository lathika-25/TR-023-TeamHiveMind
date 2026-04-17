# File: setup_database.py
import sqlite3
import random
import datetime

# All 38 Districts of Tamil Nadu and approximate coordinates
DISTRICTS = {
    "Ariyalur": (11.1393, 79.0805),
    "Chengalpattu": (12.6841, 79.9780),
    "Chennai": (13.0827, 80.2707),
    "Coimbatore": (11.0168, 76.9558),
    "Cuddalore": (11.7480, 79.7714),
    "Dharmapuri": (12.1211, 78.1582),
    "Dindigul": (10.3673, 77.9803),
    "Erode": (11.3410, 77.7172),
    "Kallakurichi": (11.7383, 78.9639),
    "Kanchipuram": (12.8185, 79.6947),
    "Kanyakumari": (8.0883, 77.5385),
    "Karur": (10.9601, 78.0766),
    "Krishnagiri": (12.5186, 78.2137),
    "Madurai": (9.9252, 78.1198),
    "Nagapattinam": (10.7672, 79.8449),
    "Namakkal": (11.2189, 78.1674),
    "Nilgiris": (11.4916, 76.7337),
    "Perambalur": (11.2342, 78.8821),
    "Pudukkottai": (10.3797, 78.8205),
    "Ramanathapuram": (9.3639, 78.8306),
    "Ranipet": (12.9275, 79.3333),
    "Salem": (11.6643, 78.1460),
    "Sivaganga": (9.8433, 78.4809),
    "Tenkasi": (8.9592, 77.3056),
    "Thanjavur": (10.7828, 79.1318),
    "Theni": (10.0104, 77.4768),
    "Thoothukudi": (8.7642, 78.1348),
    "Tiruchirappalli": (10.7905, 78.7047),
    "Tirunelveli": (8.7139, 77.7567),
    "Tirupathur": (12.4984, 78.5630),
    "Tiruppur": (11.1085, 77.3411),
    "Tiruvallur": (13.1436, 79.9144),
    "Tiruvannamalai": (12.2274, 79.0664),
    "Tiruvarur": (10.7715, 79.6366),
    "Vellore": (12.9165, 79.1325),
    "Viluppuram": (11.9401, 79.4861),
    "Virudhunagar": (9.5680, 77.9624)
}

TOILETS_DATA = []

# Generate exactly 94 toilets across the 38 districts
districts_list = list(DISTRICTS.keys())
# To get exactly 94: (18 * 3) + (20 * 2) = 54 + 40 = 94
districts_with_3 = set(random.sample(districts_list, k=18))

for city, coords in DISTRICTS.items():
    num_toilets = 3 if city in districts_with_3 else 2
    for j in range(1, num_toilets + 1):
        uid = f"T_{city.upper().replace(' ', '')}_{j:02d}"
        if j == 1:
            name = f"{city} Central Bus Stand Toilet"
        elif j == 2:
            name = f"{city} Main Market Public Toilet"
        else:
            name = f"{city} Railway Station Utility"
        
        TOILETS_DATA.append((uid, name, city, f"Ward {random.randint(1, 40)}"))

STAFF_NAMES = [
    "G. Kishore Kumar", "M. Saravanan", "A. Karthik", "S. Muthu", "V. Rajesh",
    "R. Lakshmi", "K. Meena", "P. Anbu", "N. Venkatesh", "T. Balaji",
    "S. Prabhu", "M. Priya", "V. Kavitha", "R. Suresh", "K. Dinesh",
    "G. Ramesh", "P. Anand", "N. Vijay", "T. Arun", "A. Senthil"
]
ROLES = ["Sanitary Supervisor", "Maintenance Worker", "Area Inspector"]

REVIEW_TEMPLATES = [
    ("Clean and well maintained", 5, ""),
    ("Very good condition", 5, ""),
    ("Acceptable hygiene, decent lighting", 4, ""),
    ("Water is available, quite clean", 4, ""),
    ("Looks okay but smells a bit", 3, "foul smell"),
    ("Water supply is low", 3, "no water, tap dry"),
    ("A bit messy and unlit", 3, "dark, dim, messy"),
    ("Very dirty, no water available", 1, "dirty, no water"),
    ("This toilet is very dirty, no water, and smells terrible! Pitch black.", 1, "dirty, filthy, no water, stench, pitch black"),
    ("No steps for wheelchair, very stained", 2, "wheelchair, not accessible, stained"),
    ("Garbage everywhere, unbearable stench", 1, "garbage, waste, smell, stink")
]

def init_db():
    print("Initializing Database...")
    conn = sqlite3.connect('sanitation.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS toilets')
    cursor.execute('DROP TABLE IF EXISTS reviews')
    cursor.execute('DROP TABLE IF EXISTS staff')
    cursor.execute('DROP TABLE IF EXISTS alerts')

    cursor.execute('''
    CREATE TABLE toilets (
        id TEXT PRIMARY KEY,
        name TEXT,
        lat REAL,
        lng REAL,
        city TEXT,
        ward TEXT,
        average_score REAL DEFAULT 3.0
    )
    ''')

    cursor.execute('''
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        toilet_id TEXT,
        user_rating INTEGER,
        review_text TEXT,
        detected_issues TEXT,
        hygiene_score REAL,
        timestamp TEXT,
        latitude REAL,
        longitude REAL,
        city TEXT,
        FOREIGN KEY(toilet_id) REFERENCES toilets(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE staff (
        id TEXT PRIMARY KEY,
        name TEXT,
        phone TEXT,
        assigned_toilet_ids TEXT,
        city TEXT,
        role TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        toilet_id TEXT,
        staff_id TEXT,
        staff_phone TEXT,
        message TEXT,
        severity INTEGER,
        status TEXT,
        timestamp TEXT
    )
    ''')
    
    print("Tables created.")
    return conn, cursor

def populate_data(conn, cursor):
    print(f"Generating exactly {len(TOILETS_DATA)} toilets across exactly 38 districts...")
    toilet_ids = []
    
    for t in TOILETS_DATA:
        t_id, t_name, t_city, t_ward = t
        base_lat, base_lng = DISTRICTS[t_city]
        lat = base_lat + random.uniform(-0.02, 0.02)
        lng = base_lng + random.uniform(-0.02, 0.02)
        cursor.execute('''
            INSERT INTO toilets (id, name, lat, lng, city, ward, average_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (t_id, t_name, lat, lng, t_city, t_ward, 0.0))
        toilet_ids.append(t_id)

    print("Generating 20 staff members...")
    for i, name in enumerate(STAFF_NAMES):
        s_id = f"S{i+1:03d}"
        phone = f"+9198{random.randint(10000000, 99999999)}"
        city = random.choice(list(DISTRICTS.keys()))
        assigned = random.sample(toilet_ids, k=min(random.randint(2, 6), len(toilet_ids)))
        assigned_str = ",".join(assigned)
        role = random.choice(ROLES)
        cursor.execute('''
            INSERT INTO staff (id, name, phone, assigned_toilet_ids, city, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (s_id, name, phone, assigned_str, city, role))

    print("Generating 500 synthetic reviews...")
    def calculate_deduction(extracted_keywords_str):
        if not extracted_keywords_str: return 0.0
        issues_qty = len(extracted_keywords_str.split(',')) 
        return min(issues_qty * 0.5, 3.0)

    now = datetime.datetime.now()
    toilet_scores = {t_id: [] for t_id in toilet_ids}
    
    for i in range(500):
        t_id = random.choice(toilet_ids)
        days_ago = random.randint(0, 90)
        hours_ago = random.randint(0, 23)
        rev_time = now - datetime.timedelta(days=days_ago, hours=hours_ago)
        
        t_index = toilet_ids.index(t_id)
        if t_index % 3 == 0:
            template = random.choice(REVIEW_TEMPLATES[0:4])
        elif t_index % 3 == 1:
            template = random.choice(REVIEW_TEMPLATES[4:7])
        else:
            template = random.choice(REVIEW_TEMPLATES[7:])
            
        r_text, r_rating, r_issues = template
        deduction = calculate_deduction(r_issues)
        final_score = max(1.0, min(5.0, r_rating - deduction))
        
        cursor.execute('SELECT lat, lng, city FROM toilets WHERE id = ?', (t_id,))
        t_lat, t_lng, t_city = cursor.fetchone()
        u_lat = t_lat + random.uniform(-0.001, 0.001)
        u_lng = t_lng + random.uniform(-0.001, 0.001)
        
        cursor.execute('''
            INSERT INTO reviews (toilet_id, user_rating, review_text, detected_issues, hygiene_score, timestamp, latitude, longitude, city)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (t_id, r_rating, r_text, r_issues, final_score, rev_time.strftime("%Y-%m-%d %H:%M:%S"), u_lat, u_lng, t_city))
        toilet_scores[t_id].append(final_score)

    print("Calculating and updating average toilet scores...")
    for t_id, scores in toilet_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            cursor.execute('UPDATE toilets SET average_score = ? WHERE id = ?', (round(avg, 2), t_id))
    
    conn.commit()
    print("Database properly generated and successfully saved to sanitation.db.")

if __name__ == "__main__":
    conn, cursor = init_db()
    populate_data(conn, cursor)
    conn.close()