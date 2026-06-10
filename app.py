from flask import Flask, abort, redirect, render_template, request, session
import sqlite3
import db_setup

app = Flask(__name__)

app.secret_key = "SRF_NGO_2026"
ADMIN_PASSWORD = "SRF_Admin!@#2026"

UPI_ID = "7540096440@okbizaxis"
NGO_NAME = "Siddharth Rasi Foundation"

CAMPAIGN_SEEDS = [
    (
        1,
        "Sanitary Napkin Support",
        "Provide safe menstrual hygiene products and awareness support for girls and women who need consistent care.",
        100000,
        "sanitary",
    ),
    (
        2,
        "School Kits For Children",
        "Sponsor notebooks, bags, uniforms, and learning material for children who are ready to stay in school.",
        90000,
        "education",
    ),
    (
        3,
        "Scribe Support",
        "Arrange trained scribes and exam assistance for students who need writing support to continue their education.",
        75000,
        "scribe",
    ),
    (
        4,
        "Safe Shelter Fund",
        "Support rent, bedding, sanitation, and basic safety needs for vulnerable families rebuilding stability.",
        200000,
        "shelter",
    ),
    (
        5,
        "Psychology Service",
        "Offer counselling, emotional wellness sessions, and mental health guidance for children, families, and caregivers.",
        125000,
        "psychology",
    ),
]


def get_connection():
    return sqlite3.connect("donations.db")


def ensure_campaigns():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM campaigns")
    count = cursor.fetchone()[0]

    if count < len(CAMPAIGN_SEEDS):
        for campaign in CAMPAIGN_SEEDS:
            cursor.execute(
                """
                INSERT OR REPLACE INTO campaigns (id, title, description, goal, image)
                VALUES (?, ?, ?, ?, ?)
                """,
                campaign,
            )

        conn.commit()

    conn.close()


def get_campaigns_with_progress():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, description, goal, image FROM campaigns ORDER BY id")
    campaigns = cursor.fetchall()

    campaign_cards = []
    for campaign in campaigns:
        cursor.execute(
            """
            SELECT SUM(amount) FROM donations
            WHERE campaign_id=? AND payment_method='UPI-Verified'
            """,
            (campaign[0],),
        )
        total = cursor.fetchone()[0] or 0
        goal = campaign[3] or 0
        progress = min((total / goal) * 100, 100) if goal else 0

        campaign_cards.append(
            {
                "id": campaign[0],
                "title": campaign[1],
                "description": campaign[2],
                "goal": goal,
                "image": campaign[4] or "medical",
                "total": total,
                "progress": round(progress, 1),
                "remaining": max(goal - total, 0),
            }
        )

    conn.close()
    return campaign_cards


@app.route("/")
def home():
    ensure_campaigns()
    campaigns = get_campaigns_with_progress()
    total_raised = sum(campaign["total"] for campaign in campaigns)
    total_goal = sum(campaign["goal"] for campaign in campaigns)
    verified_campaigns = sum(1 for campaign in campaigns if campaign["total"] > 0)

    return render_template(
        "campaign.html",
        campaigns=campaigns,
        total_raised=total_raised,
        total_goal=total_goal,
        verified_campaigns=verified_campaigns,
        upi_id=UPI_ID,
        ngo_name=NGO_NAME,
    )


@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    data = request.get_json() or {}

    try:
        campaign_id = int(data.get("campaign_id"))
        amount = int(data.get("amount"))
    except (TypeError, ValueError):
        abort(400)

    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not name or not phone or amount < 1:
        abort(400)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM campaigns WHERE id=?", (campaign_id,))
    if not cursor.fetchone():
        conn.close()
        abort(404)

    cursor.execute(
        """
        INSERT INTO donations
        (campaign_id, name, phone, amount, district, state, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (campaign_id, name, phone, amount, "Chennai", "TN", "Pending"),
    )

    conn.commit()
    conn.close()

    return "OK"

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

        return "Invalid Password"

    return """
    <h2>Admin Login</h2>
    <form method="post">
        <input type="password" name="password" placeholder="Enter Password">
        <button type="submit">Login</button>
    </form>
    """

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin-login")

    ensure_campaigns()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT donations.id, donations.campaign_id, campaigns.title, donations.name,
               donations.phone, donations.amount, donations.payment_method,
               donations.created_at
        FROM donations
        LEFT JOIN campaigns ON campaigns.id = donations.campaign_id
        ORDER BY donations.id DESC
        """
    )
    donations = cursor.fetchall()

    conn.close()

    return render_template("admin.html", donations=donations)


@app.route("/approve/<int:id>", methods=["POST"])
def approve(id):
    if not session.get("admin"):
        return redirect("/admin-login")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE donations
        SET payment_method='UPI-Verified'
        WHERE id=?
        """,
        (id,),
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/reject/<int:id>", methods=["POST"])
def reject(id):
    if not session.get("admin"):
        return redirect("/admin-login")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM donations WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin-login")

import db_setup
if __name__ == "__main__":
    ensure_campaigns()
    app.run(host="0.0.0.0", port=5000, debug=True)
