import sqlite3

CAMPAIGNS = [
    (
        "Sanitary Napkin Support",
        "Provide safe menstrual hygiene products and awareness support for girls and women who need consistent care.",
        100000,
        "sanitary",
    ),
    (
        "School Kits For Children",
        "Sponsor notebooks, bags, uniforms, and learning material for children who are ready to stay in school.",
        90000,
        "education",
    ),
    (
        "Scribe Support",
        "Arrange trained scribes and exam assistance for students who need writing support to continue their education.",
        75000,
        "scribe",
    ),
    (
        "Safe Shelter Fund",
        "Support rent, bedding, sanitation, and basic safety needs for vulnerable families rebuilding stability.",
        200000,
        "shelter",
    ),
    (
        "Psychology Service",
        "Offer counselling, emotional wellness sessions, and mental health guidance for children, families, and caregivers.",
        125000,
        "psychology",
    ),
]

conn = sqlite3.connect("donations.db")
cursor = conn.cursor()


cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        goal INTEGER,
        image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER,
        name TEXT,
        phone TEXT,
        amount INTEGER,
        district TEXT,
        state TEXT,
        payment_method TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)
cursor.execute("SELECT COUNT(*) FROM campaigns")
count = cursor.fetchone()[0]

if count == 0:
    cursor.executemany(
        """
        INSERT INTO campaigns (title, description, goal, image)
        VALUES (?, ?, ?, ?)
        """,
        CAMPAIGNS,
    )

conn.commit()
conn.close()

print("Donation database ready.")
