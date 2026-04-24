from db import get_connection
from flask import Flask, render_template, request,session, redirect, url_for
import os
import random

app = Flask(__name__)
app.secret_key = "vestilefit_secret"


# HOME ----------------
@app.route("/")
def home():
    detected_body = request.args.get("detected_body")
    detected_size = request.args.get("detected_size")
    return render_template("index.html", detected_body=detected_body, detected_size=detected_size)

# FIT ANALYZER PAGE----------------
@app.route("/fit-analyzer")
def fit_analyzer_page():
    return render_template("fit_analyzer.html")

# FIT ANALYZER ----------------
@app.route("/analyze-fit", methods=["POST"])
def analyze_fit():
    bust = float(request.form["bust"])
    waist = float(request.form["waist"])
    hip = float(request.form["hip"])

   
    if abs(bust - hip) <= 5 and (bust - waist) >= 20:
        body_type = "Hourglass"
    elif hip - bust > 5:
        body_type = "Pear"
    elif bust - hip > 5:
        body_type = "Triangle"
    elif abs(bust - waist) <= 10 and abs(waist - hip) <= 10:
        body_type = "Rectangle"
    else:
        body_type = "Apple"


    if 80 <= bust <= 84 and 60 <= waist <= 64 and 86 <= hip <= 90:
        size = "XS"
    elif 85 <= bust <= 89 and 65 <= waist <= 69 and 91 <= hip <= 95:
        size = "S"
    elif 90 <= bust <= 95 and 70 <= waist <= 75 and 96 <= hip <= 101:
        size = "M"
    elif 96 <= bust <= 101 and 76 <= waist <= 81 and 102 <= hip <= 107:
        size = "L"
    elif 102 <= bust <= 107 and 82 <= waist <= 87 and 108 <= hip <= 113:
        size = "XL"
    else:
        avg = (bust + waist + hip) / 3
        if avg < 80:
            size = "XS"
        elif avg < 88:
            size = "S"
        elif avg < 96:
            size = "M"
        elif avg < 104:
            size = "L"
        elif avg < 112:
            size = "XL"
        else:
            size = "XXL"


    session["body_type"] = body_type
    session["detected_size"] = size

    return redirect(url_for("home"))

# DRESS RECOMMENDATION PAGE ----------------
@app.route("/dress-recommendation")
def dress_recommendation_page():
    return render_template("dress_recommendation.html",body_type=session.get("body_type"))


warm = ["Red", "Orange", "Brown","Tan","Peach","Maroon","Coral","Burgundy","Wine Red","Mustard","Gold","Dusty Pink","Rose Pink"]
cool = ["Blue", "Green", "Purple","Sky blue","Navy blue","Light Blue","Emerald Green","Olive Green","Dark blue","royal Blue","Teal","Olive","Mint Green","Light Blue"]
pastel = ["Pink", "Lavender", "Sky Blue","Peach","Mint Green","Light Blue","Sky Blue","pink","Rose Pink","Lavender","Ivory","Dusty Pink","Pastel Blue"]
neutral = ["Black", "White", "Gray", "Beige","ivory","Cream","Brown"]



# RECOMMEND ----------------

@app.route("/recommend", methods=["POST"])
def recommend():

    gender = request.form["gender"]
    age = int(request.form["age"])

    if age <= 0 or age > 100:
        return "invalid age entered"
    form_body = request.form.get("body_type")
    session_body = session.get("body_type")
    body_type = form_body if form_body else session_body
    size = session.get("detected_size")
    weather = request.form["weather"]
    occasion = request.form["occasion"]
    color = request.form.get("color")
    wanted_categories = request.form.getlist("wanted_category[]")

    all_season_material=["Denim","Georgette"]
    if weather == "Summer":
        materials = ["Cotton", "Net","Linen","Chiffon","Denim","Cotton Blend","Linen Blend","Rayon"]+all_season_material
    elif weather == "Winter":
        materials = ["Wool", "Denim","Sequin","Leather","Velvet","Wool Blend","Fleece"]+all_season_material
    else:
        materials = ["Cotton","Net","Sequin", "Denim", "Linen","Leather","Chiffon","Crepe","Satin","Silk"]+all_season_material

    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    mat_placeholders = ",".join(["%s"] * len(materials))


    if occasion == "Office":
        query = f"""
        SELECT * FROM dresses
        WHERE min_age <= %s AND max_age >= %s
        AND body_type=%s
        AND occasion=%s
        AND (material IN ({mat_placeholders})
                OR category='Suit')
        """
    else:
        query = f"""
        SELECT * FROM dresses
        WHERE min_age <= %s AND max_age >= %s
        AND (body_type=%s OR body_type='all')
        AND occasion=%s
        AND material IN ({mat_placeholders}) 
        """

    params = [age, age, body_type, occasion,*materials]


    # CATEGORY LOGIC
    cats=[]
    if wanted_categories:
        cats = list(dict.fromkeys(wanted_categories))
    else:
        cats = ["Top", "Bottom", "Dress"]

    if cats:
        cat_placeholders = ",".join(["%s"] * len(cats))
        query += f" AND category IN ({cat_placeholders})"
        params.extend(cats)

    if gender == "Unisex":
        query += " AND gender IN ('Female','Male','Unisex')"
    else:
        query += " AND gender=%s"
        params.append(gender)
    
    
    query += " ORDER BY RAND()"


    cursor.execute(query, params)
    results = cursor.fetchall()


    cursor.close()
    conn.close()


    return render_template(
        "result.html",
        dresses=results,
        size=session.get("detected_size"),
        show_size=bool(session.get("detected_size"))
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)