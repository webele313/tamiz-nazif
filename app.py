from flask import Flask, request, jsonify, session, redirect, render_template_string
import sqlite3
import re
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "tamiz-nazif-secret-change-this"

DB = "tamiz_nazif.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT NOT NULL,
            area TEXT NOT NULL,
            year TEXT DEFAULT '۱۴۰۵',
            month TEXT,
            day TEXT,
            time TEXT,
            address TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'جدید',
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # برای دیتابیس‌های نسخه قبلی
    columns = [
        ("tracking_code", "TEXT"),
        ("area", "TEXT"),
        ("year", "TEXT DEFAULT '۱۴۰۵'"),
        ("month", "TEXT"),
        ("day", "TEXT"),
        ("time", "TEXT")
    ]

    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(requests)").fetchall()
    }

    for name, definition in columns:
        if name not in existing:
            conn.execute(
                f"ALTER TABLE requests ADD COLUMN {name} {definition}"
            )

    admin = conn.execute(
        "SELECT * FROM admins WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        conn.execute(
            """
            INSERT INTO admins (username, password)
            VALUES (?, ?)
            """,
            (
                "admin",
                generate_password_hash("Tamiz12345")
            )
        )

    conn.commit()
    conn.close()


# =========================================================
# PERSIAN HELPERS
# =========================================================

months = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند"
]


def make_tracking_code():
    return "TN-" + secrets.token_hex(3).upper()


def only_digits(value):
    if not value:
        return False

    return bool(re.fullmatch(r"[0-9۰-۹]+", value))


# =========================================================
# MAIN WEBSITE
# =========================================================

HOME_HTML = r"""
<!DOCTYPE html>

<html lang="fa" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>تمیز نظیف منزل</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    scroll-behavior: smooth;
}

body {

    font-family:
        Tahoma,
        Arial,
        sans-serif;

    color: #fff;

    background:
        radial-gradient(
            circle at 15% 20%,
            rgba(0, 255, 255, .14),
            transparent 28%
        ),

        radial-gradient(
            circle at 85% 15%,
            rgba(255, 0, 170, .15),
            transparent 30%
        ),

        radial-gradient(
            circle at 50% 80%,
            rgba(80, 0, 255, .12),
            transparent 35%
        ),

        #050812;

    min-height: 100vh;
}


/* ==========================================
   HEADER
========================================== */

header {

    position: sticky;
    top: 0;
    z-index: 100;

    padding: 18px 7%;

    display: flex;
    justify-content: space-between;
    align-items: center;

    background:
        rgba(5, 8, 18, .72);

    backdrop-filter: blur(20px);

    border-bottom:
        1px solid rgba(255,255,255,.08);
}

.logo {

    font-size: 23px;
    font-weight: bold;

    background:
        linear-gradient(
            90deg,
            #5fffff,
            #ff65d8
        );

    -webkit-background-clip: text;
    color: transparent;
}

nav {
    display: flex;
    gap: 25px;
}

nav a {

    color: #ddd;

    text-decoration: none;

    font-size: 14px;

    transition: .2s;
}

nav a:hover {
    color: #63faff;
}


/* ==========================================
   HERO
========================================== */

.hero {

    min-height: 650px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 50px;

    padding: 80px 8%;
}

.hero-text {
    max-width: 600px;
}

.badge {

    display: inline-block;

    padding: 9px 17px;

    border-radius: 100px;

    border:
        1px solid rgba(80,255,255,.25);

    background:
        rgba(0,255,255,.06);

    color: #72ffff;

    margin-bottom: 22px;

    font-size: 13px;
}

h1 {

    font-size:
        clamp(38px, 6vw, 68px);

    line-height: 1.2;

    margin-bottom: 20px;
}

.gradient-text {

    background:
        linear-gradient(
            90deg,
            #58ffff,
            #ff65d8
        );

    -webkit-background-clip: text;

    color: transparent;
}

.hero-text p {

    color: #b9c0d1;

    line-height: 2;

    font-size: 17px;

    margin-bottom: 30px;
}

.buttons {

    display: flex;

    gap: 13px;

    flex-wrap: wrap;
}

.btn {

    display: inline-block;

    padding: 15px 25px;

    border-radius: 15px;

    border: 1px solid transparent;

    text-decoration: none;

    cursor: pointer;

    font-family: inherit;

    font-weight: bold;
}

.primary {

    color: #031013;

    background:
        linear-gradient(
            90deg,
            #52ffff,
            #d76bff
        );

    box-shadow:
        0 0 35px rgba(70,255,255,.18);
}

.secondary {

    color: white;

    border-color:
        rgba(255,255,255,.14);

    background:
        rgba(255,255,255,.05);
}


/* ==========================================
   HERO VISUAL
========================================== */

.visual {

    width: 440px;

    height: 430px;

    position: relative;

    display: flex;

    align-items: center;

    justify-content: center;
}

.orbit {

    position: absolute;

    width: 330px;
    height: 330px;

    border-radius: 50%;

    border:
        1px solid rgba(90,255,255,.22);

    box-shadow:
        0 0 60px rgba(60,255,255,.08);
}

.orbit2 {

    width: 230px;
    height: 230px;

    border-color:
        rgba(255,80,220,.22);

    transform: rotate(45deg);
}

.clean-card {

    position: relative;

    z-index: 2;

    width: 270px;

    padding: 35px 25px;

    text-align: center;

    border-radius: 30px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.13),
            rgba(255,255,255,.035)
        );

    border:
        1px solid rgba(255,255,255,.15);

    backdrop-filter: blur(20px);

    box-shadow:
        0 25px 80px rgba(0,0,0,.35);
}

.clean-icon {

    font-size: 75px;

    filter:
        drop-shadow(
            0 0 20px
            rgba(80,255,255,.5)
        );

    margin-bottom: 15px;
}

.clean-card h2 {
    margin-bottom: 10px;
}

.clean-card p {
    color: #b9c0d1;
    line-height: 1.9;
}


/* ==========================================
   SECTION
========================================== */

section {
    padding: 90px 8%;
}

.section-title {

    text-align: center;

    max-width: 700px;

    margin: auto auto 50px;
}

.section-title h2 {

    font-size: 38px;

    margin-bottom: 12px;
}

.section-title p {

    color: #aeb6ca;

    line-height: 1.9;
}


/* ==========================================
   SERVICES
========================================== */

.services {

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(220px,1fr));

    gap: 20px;
}

.service {

    padding: 28px 22px;

    border-radius: 24px;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid rgba(255,255,255,.09);

    transition: .3s;
}

.service:hover {

    transform:
        translateY(-7px);

    border-color:
        rgba(85,255,255,.35);

    box-shadow:
        0 15px 50px
        rgba(0,255,255,.07);
}

.service-icon {

    font-size: 40px;

    margin-bottom: 15px;
}

.service h3 {
    margin-bottom: 10px;
}

.service p {

    color: #aeb6ca;

    line-height: 1.9;

    font-size: 14px;
}


/* ==========================================
   MOVING
========================================== */

.moving-box {

    max-width: 1000px;

    margin: auto;

    padding: 50px 35px;

    border-radius: 35px;

    background:
        linear-gradient(
            135deg,
            rgba(80,255,255,.07),
            rgba(255,70,210,.07)
        );

    border:
        1px solid rgba(255,255,255,.1);
}

.moving-items {

    display: grid;

    grid-template-columns:
        repeat(3,1fr);

    gap: 15px;

    margin-top: 30px;
}

.moving-item {

    padding: 25px;

    border-radius: 20px;

    background:
        rgba(0,0,0,.18);

    border:
        1px solid rgba(255,255,255,.07);
}

.moving-item p {

    color: #aeb6ca;

    margin-top: 10px;

    line-height: 1.8;
}


/* ==========================================
   BOOKING
========================================== */

.booking-wrapper {

    max-width: 1000px;

    margin: auto;

    padding: 2px;

    border-radius: 34px;

    background:
        linear-gradient(
            120deg,
            #43ffff,
            #7c4dff,
            #ff4dd8,
            #43ffff
        );

    background-size: 300% 300%;

    animation: borderMove 8s ease infinite;
}

@keyframes borderMove {

    0% {
        background-position: 0% 50%;
    }

    50% {
        background-position: 100% 50%;
    }

    100% {
        background-position: 0% 50%;
    }
}

.booking {

    background:
        rgba(5,8,18,.94);

    border-radius: 32px;

    padding: 40px;
}

.form-grid {

    display: grid;

    grid-template-columns:
        repeat(2,1fr);

    gap: 20px;
}

.field {

    position: relative;
}

label {

    display: block;

    color: #dfe5f4;

    font-size: 13px;

    margin-bottom: 7px;
}

.required {
    color: #ff65d8;
}

input,
select,
textarea {

    width: 100%;

    padding: 16px;

    color: white;

    background:
        rgba(255,255,255,.055);

    border:
        1px solid rgba(255,255,255,.12);

    border-radius: 14px;

    outline: none;

    font-family: inherit;

    transition: .2s;
}

input:focus,
select:focus,
textarea:focus {

    border-color:
        rgba(75,255,255,.7);

    box-shadow:
        0 0 20px
        rgba(75,255,255,.08);
}

select option {
    background: #101522;
    color: white;
}

textarea {

    min-height: 120px;

    resize: vertical;
}

.full {
    grid-column: 1 / -1;
}

.submit {

    width: 100%;

    margin-top: 25px;

    font-size: 16px;

    padding: 17px;
}


/* ==========================================
   SUCCESS PANEL
========================================== */

#successPanel {

    display: none;

    margin-top: 25px;

    padding: 30px;

    border-radius: 25px;

    background:
        linear-gradient(
            135deg,
            rgba(0,255,190,.09),
            rgba(80,130,255,.09)
        );

    border:
        1px solid rgba(80,255,220,.3);

    text-align: center;

    animation: panelIn .5s ease;
}

@keyframes panelIn {

    from {
        opacity: 0;
        transform: translateY(15px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.success-icon {

    font-size: 55px;

    margin-bottom: 12px;
}

.success-panel-title {

    font-size: 23px;

    margin-bottom: 12px;

    color: #6fffff;
}

.success-text {

    color: #cbd3e5;

    line-height: 2;
}

.tracking {

    display: inline-block;

    margin-top: 18px;

    padding: 12px 18px;

    border-radius: 12px;

    background:
        rgba(255,255,255,.07);

    border:
        1px solid rgba(255,255,255,.1);

    color: #fff;
}

.tracking strong {
    color: #72ffff;
}

.notice {

    margin-top: 18px;

    padding: 15px;

    border-radius: 14px;

    background:
        rgba(255,210,70,.06);

    border:
        1px solid rgba(255,210,70,.15);

    color: #ffeaa0;

    font-size: 13px;
}


/* ==========================================
   FOOTER
========================================== */

footer {

    padding: 45px 8%;

    text-align: center;

    background: #03050b;

    border-top:
        1px solid rgba(255,255,255,.07);
}

footer p {

    color: #8f98ae;

    margin-top: 10px;
}


/* ==========================================
   MOBILE
========================================== */

@media(max-width: 800px) {

    nav {
        display: none;
    }

    .hero {

        flex-direction: column;

        text-align: center;

        padding-top: 55px;
    }

    .buttons {
        justify-content: center;
    }

    .visual {

        width: 100%;

        transform: scale(.85);
    }

    .form-grid {

        grid-template-columns: 1fr;
    }

    .full {
        grid-column: auto;
    }

    .moving-items {

        grid-template-columns: 1fr;
    }

    .booking {
        padding: 25px 18px;
    }

    section {
        padding: 65px 6%;
    }
}

</style>

</head>


<body>


<header>

<div class="logo">
    تمیز نظیف منزل ✨
</div>

<nav>

<a href="#services">خدمات</a>

<a href="#moving">اسباب‌کشی</a>

<a href="#booking">ثبت درخواست</a>

<a href="tel:09333367746">
    تماس
</a>

</nav>

</header>


<!-- HERO -->

<section class="hero">

<div class="hero-text">

<span class="badge">
    ✦ خدمات حرفه‌ای نظافت منزل
</span>

<h1>

خانه‌ای تمیز،
<br>

<span class="gradient-text">
    آرامشی بیشتر
</span>

</h1>

<p>

با چند کلیک درخواست خود را ثبت کنید.
ما اطلاعات درخواست شما را دریافت می‌کنیم
و برای هماهنگی با شما تماس خواهیم گرفت.

</p>

<div class="buttons">

<a href="#booking"
class="btn primary">

ثبت درخواست آنلاین

</a>

<a href="tel:09333367746"
class="btn secondary">

📞 تماس با ما

</a>

</div>

</div>


<div class="visual">

<div class="orbit"></div>

<div class="orbit orbit2"></div>

<div class="clean-card">

<div class="clean-icon">
    🧹
</div>

<h2>
    تمیزی با خیال راحت
</h2>

<p>
    خدمات نظافت منزل با ثبت درخواست آنلاین
</p>

</div>

</div>

</section>


<!-- SERVICES -->

<section id="services">

<div class="section-title">

<h2>
    خدمات ما
</h2>

<p>
    خدماتی برای تمیزی و آرامش بیشتر منزل شما
</p>

</div>


<div class="services">

<div class="service">

<div class="service-icon">
    🏠
</div>

<h3>
    نظافت منزل
</h3>

<p>
    نظافت بخش‌های مختلف منزل
    متناسب با نیاز شما.
</p>

</div>


<div class="service">

<div class="service-icon">
    🍳
</div>

<h3>
    نظافت آشپزخانه
</h3>

<p>
    نظافت سطوح، کابینت‌ها،
    سینک و قسمت‌های مختلف آشپزخانه.
</p>

</div>


<div class="service">

<div class="service-icon">
    🚿
</div>

<h3>
    حمام و سرویس
</h3>

<p>
    نظافت و شست‌وشوی سرویس
    و حمام منزل.
</p>

</div>


<div class="service">

<div class="service-icon">
    ✨
</div>

<h3>
    بعد از مهمانی
</h3>

<p>
    برگرداندن نظم و تمیزی منزل
    بعد از مهمانی.
</p>

</div>


<div class="service">

<div class="service-icon">
    🛠️
</div>

<h3>
    بعد از تعمیرات
</h3>

<p>
    پاک‌سازی گردوغبار و آلودگی
    بعد از تعمیرات.
</p>

</div>

</div>

</section>


<!-- MOVING -->

<section id="moving">

<div class="moving-box">

<div class="section-title">

<h2>
    📦 اسباب‌کشی
</h2>

<p>
    برای جابه‌جایی راحت‌تر،
    خدمات آماده‌سازی منزل را هم ارائه می‌دهیم.
</p>

</div>


<div class="moving-items">

<div class="moving-item">

<h3>
    📦 بسته‌بندی وسایل
</h3>

<p>
    آماده‌سازی و بسته‌بندی وسایل
    برای جابه‌جایی.
</p>

</div>


<div class="moving-item">

<h3>
    🧹 نظافت منزل جدید
</h3>

<p>
    تمیزکاری منزل قبل از ورود
    وسایل و اثاثیه.
</p>

</div>


<div class="moving-item">

<h3>
    ✨ آماده‌سازی منزل
</h3>

<p>
    آماده کردن فضای منزل
    برای شروعی تازه.
</p>

</div>

</div>

</div>

</section>


<!-- BOOKING -->

<section id="booking">

<div class="section-title">

<h2>
    🚀 ثبت درخواست
</h2>

<p>
    اطلاعات را کامل وارد کنید تا درخواست شما
    با موفقیت ثبت شود.
</p>

</div>


<div class="booking-wrapper">

<div class="booking">


<form id="bookingForm">


<div class="form-grid">


<!-- NAME -->

<div class="field">

<label>
نام و نام خانوادگی
<span class="required">*</span>
</label>

<input
type="text"
name="name"
required
placeholder="نام و نام خانوادگی">

</div>


<!-- PHONE -->

<div class="field">

<label>
شماره تماس
<span class="required">*</span>
</label>

<input
type="tel"
name="phone"
required
inputmode="numeric"
pattern="[0-9۰-۹]+"
maxlength="11"
placeholder="09xxxxxxxxx"
oninput="this.value=this.value.replace(/[^0-9۰-۹]/g,'').slice(0,11)">

</div>


<!-- SERVICE -->

<div class="field">

<label>
نوع خدمت
<span class="required">*</span>
</label>

<select
name="service"
required>

<option value="">
انتخاب خدمت
</option>

<option>
نظافت منزل
</option>

<option>
نظافت آشپزخانه
</option>

<option>
حمام و سرویس
</option>

<option>
نظافت بعد از مهمانی
</option>

<option>
نظافت بعد از تعمیرات
</option>

<option>
اسباب‌کشی - بسته‌بندی
</option>

<option>
اسباب‌کشی - نظافت منزل جدید
</option>

</select>

</div>


<!-- AREA -->

<div class="field">

<label>
متراژ منزل
<span class="required">*</span>
</label>

<input
type="number"
name="area"
required
min="1"
placeholder="مثلاً ۸۰">

</div>


<!-- YEAR -->

<div class="field">

<label>
سال
</label>

<select name="year">

<option selected>
۱۴۰۵
</option>

</select>

</div>


<!-- MONTH -->

<div class="field">

<label>
ماه
<span class="required">*</span>
</label>

<select
name="month"
required>

<option value="">
انتخاب ماه
</option>

<option>فروردین</option>
<option>اردیبهشت</option>
<option>خرداد</option>
<option>تیر</option>
<option>مرداد</option>
<option>شهریور</option>
<option>مهر</option>
<option>آبان</option>
<option>آذر</option>
<option>دی</option>
<option>بهمن</option>
<option>اسفند</option>

</select>

</div>


<!-- DAY -->

<div class="field">

<label>
روز
<span class="required">*</span>
</label>

<select
name="day"
required>

<option value="">
روز
</option>

{% for d in range(1, 32) %}

<option>{{ d }}</option>

{% endfor %}

</select>

</div>


<!-- TIME -->

<div class="field">

<label>
ساعت
<span class="required">*</span>
</label>

<select
name="time"
required>

<option value="">
انتخاب ساعت
</option>

<option>۰۷:۰۰</option>
<option>۰۸:۰۰</option>
<option>۰۹:۰۰</option>
<option>۱۰:۰۰</option>
<option>۱۱:۰۰</option>
<option>۱۲:۰۰</option>
<option>۱۳:۰۰</option>
<option>۱۴:۰۰</option>
<option>۱۵:۰۰</option>
<option>۱۶:۰۰</option>
<option>۱۷:۰۰</option>
<option>۱۸:۰۰</option>
<option>۱۹:۰۰</option>
<option>۲۰:۰۰</option>
<option>۲۱:۰۰</option>

</select>

</div>


<!-- ADDRESS -->

<div class="field full">

<label>
آدرس
<span class="required">*</span>
</label>

<input
type="text"
name="address"
required
placeholder="آدرس کامل محل انجام خدمت">

</div>


<!-- NOTES -->

<div class="field full">

<label>
توضیحات تکمیلی
</label>

<textarea
name="notes"
placeholder="توضیحات مورد نیاز خود را بنویسید..."></textarea>

</div>


</div>


<button
class="btn primary submit"
type="submit">

🚀 ثبت نهایی درخواست

</button>


</form>


<!-- SUCCESS PANEL -->

<div id="successPanel">

<div class="success-icon">
    ✅
</div>

<div class="success-panel-title">
    درخواست شما ثبت شد
</div>

<div class="success-text">

اطلاعات درخواست شما با موفقیت دریافت شد.

<br>

<strong>
همکاران ما کمتر از ۳۰ دقیقه با شما تماس خواهند گرفت.
</strong>

</div>


<div class="tracking">

کد پیگیری شما:

<strong id="trackingCode">
---</strong>

</div>


<div class="notice">

این کد را نگه دارید.
در نسخه بعدی می‌توانید با همین کد
وضعیت درخواست خود را پیگیری کنید.

</div>

</div>


</div>

</div>

</section>


<footer>

<h2>
    تمیز نظیف منزل
</h2>

<p>
    خدمات حرفه‌ای نظافت منزل
</p>

<p>
    📞 09333367746
</p>

</footer>


<script>

const form =
document.getElementById("bookingForm");

form.addEventListener(
"submit",
async function(event) {

    event.preventDefault();

    const button =
        form.querySelector("button");

    button.disabled = true;

    button.innerText =
        "⏳ در حال ثبت درخواست...";


    const data =
        Object.fromEntries(
            new FormData(form)
        );


    try {

        const response =
            await fetch(
                "/api/request",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(data)
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            alert(
                result.error ||
                "ثبت درخواست انجام نشد."
            );

            button.disabled = false;

            button.innerText =
                "🚀 ثبت نهایی درخواست";

            return;
        }


        document.getElementById(
            "trackingCode"
        ).innerText =
            result.tracking_code;


        document.getElementById(
            "successPanel"
        ).style.display = "block";


        form.style.display = "none";


        document.getElementById(
            "successPanel"
        ).scrollIntoView({
            behavior: "smooth",
            block: "center"
        });


    }

    catch(error) {

        alert(
            "ارتباط با سرور برقرار نشد."
        );

        button.disabled = false;

        button.innerText =
            "🚀 ثبت نهایی درخواست";
    }

});

</script>


</body>

</html>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template_string(
        HOME_HTML,
        months=months
    )


# =========================================================
# CREATE REQUEST
# =========================================================

@app.route("/api/request", methods=["POST"])
def create_request():

    data = request.get_json() or {}

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    service = str(data.get("service", "")).strip()
    area = str(data.get("area", "")).strip()

    year = str(data.get("year", "۱۴۰۵")).strip()
    month = str(data.get("month", "")).strip()
    day = str(data.get("day", "")).strip()
    time = str(data.get("time", "")).strip()

    address = str(data.get("address", "")).strip()
    notes = str(data.get("notes", "")).strip()


    if not name:
        return jsonify({
            "error": "نام و نام خانوادگی را وارد کنید."
        }), 400


    if not phone:
        return jsonify({
            "error": "شماره تماس را وارد کنید."
        }), 400


    if not only_digits(phone):
        return jsonify({
            "error": "شماره تماس باید فقط شامل عدد باشد."
        }), 400


    if len(phone) != 11:
        return jsonify({
            "error": "شماره تماس باید ۱۱ رقم باشد."
        }), 400


    if not service:
        return jsonify({
            "error": "نوع خدمت را انتخاب کنید."
        }), 400


    if not area:
        return jsonify({
            "error": "متراژ منزل را وارد کنید."
        }), 400


    if not month or not day or not time:
        return jsonify({
            "error": "تاریخ و ساعت را کامل انتخاب کنید."
        }), 400


    if not address:
        return jsonify({
            "error": "آدرس را وارد کنید."
        }), 400


    tracking_code = make_tracking_code()


    conn = get_db()

    conn.execute("""
        INSERT INTO requests
        (
            tracking_code,
            name,
            phone,
            service,
            area,
            year,
            month,
            day,
            time,
            address,
            notes,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        tracking_code,
        name,
        phone,
        service,
        area,
        year,
        month,
        day,
        time,
        address,
        notes,
        "جدید",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))


    conn.commit()
    conn.close()


    return jsonify({

        "success": True,

        "tracking_code":
            tracking_code

    })


# =========================================================
# ADMIN LOGIN
# =========================================================

LOGIN_HTML = """
<!DOCTYPE html>

<html lang="fa" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>ورود مدیریت</title>

<style>

body {

    margin: 0;

    font-family: Tahoma;

    min-height: 100vh;

    display: flex;

    align-items: center;

    justify-content: center;

    background:
        radial-gradient(
            circle at top,
            #253c55,
            #050812 60%
        );

    color: white;
}

.box {

    width: 360px;

    max-width: 90%;

    padding: 35px;

    border-radius: 25px;

    background:
        rgba(255,255,255,.07);

    border:
        1px solid rgba(255,255,255,.12);

    backdrop-filter: blur(20px);
}

h2 {
    text-align: center;
}

input {

    width: 100%;

    box-sizing: border-box;

    padding: 15px;

    margin-top: 10px;

    border-radius: 12px;

    border:
        1px solid rgba(255,255,255,.15);

    background:
        rgba(255,255,255,.06);

    color: white;
}

button {

    width: 100%;

    margin-top: 18px;

    padding: 15px;

    border: 0;

    border-radius: 12px;

    background:
        linear-gradient(
            90deg,
            #52ffff,
            #d76bff
        );

    cursor: pointer;

    font-weight: bold;
}

.error {

    color: #ff8f9b;

    text-align: center;

    margin-top: 15px;
}

</style>

</head>

<body>

<div class="box">

<h2>
🔐 مدیریت تمیز نظیف
</h2>

<form method="POST">

<input
name="username"
placeholder="نام کاربری"
required>

<input
type="password"
name="password"
placeholder="رمز عبور"
required>

<button>
ورود به پنل
</button>

</form>


{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}

</div>

</body>

</html>
"""


@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]


        conn = get_db()

        admin =conn.execute(
                """
                SELECT *
                FROM admins
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

        conn.close()


        if admin and check_password_hash(
            admin["password"],
            password
        ):

            session["admin"] = True

            return redirect("/admin")


        return render_template_string(
            LOGIN_HTML,
            error=
            "نام کاربری یا رمز عبور اشتباه است."
        )


    return render_template_string(
        LOGIN_HTML
    )


# =========================================================
# ADMIN PANEL
# =========================================================

ADMIN_HTML = """
<!DOCTYPE html>

<html lang="fa" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>پنل مدیریت</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family: Tahoma;

    background: #070a12;

    color: white;
}

header {

    padding: 22px 6%;

    display: flex;

    justify-content:
        space-between;

    align-items: center;

    background:
        rgba(255,255,255,.04);

    border-bottom:
        1px solid rgba(255,255,255,.08);
}

header a {

    color: #72ffff;

    text-decoration: none;
}

.container {

    width: 94%;

    max-width: 1500px;

    margin: 30px auto;
}

.stats {

    display: grid;

    grid-template-columns:
        repeat(3,1fr);

    gap: 18px;

    margin-bottom: 25px;
}

.stat {

    padding: 25px;

    border-radius: 20px;

    background:
        rgba(255,255,255,.05);

    border:
        1px solid rgba(255,255,255,.08);
}

.stat strong {

    display: block;

    font-size: 32px;

    color: #6fffff;

    margin-top: 8px;
}

.table-box {

    background:
        rgba(255,255,255,.04);

    padding: 20px;

    border-radius: 20px;

    overflow: auto;
}

table {

    width: 100%;

    min-width: 1300px;

    border-collapse: collapse;
}

th,
td {

    padding: 13px;

    border-bottom:
        1px solid rgba(255,255,255,.08);

    text-align: right;
}

th {

    color: #6fffff;

    background:
        rgba(80,255,255,.05);
}

select {

    padding: 8px;

    background: #121827;

    color: white;

    border:
        1px solid #333;

    border-radius: 8px;
}

button {

    border: 0;

    border-radius: 8px;

    padding: 8px 12px;

    cursor: pointer;
}

.update {

    background: #52ffff;

    color: #041013;
}

.delete {

    background: #44202a;

    color: #ff9aaa;
}

@media(max-width:700px) {

    .stats {
        grid-template-columns: 1fr;
    }

    header {
        flex-direction: column;
        gap: 12px;
    }
}

</style>

</head>

<body>


<header>

<h2>
پنل مدیریت تمیز نظیف
</h2>

<a href="/admin/logout">
خروج
</a>

</header>


<div class="container">


<div class="stats">

<div class="stat">

درخواست‌های کل

<strong>
{{ total }}
</strong>

</div>


<div class="stat">

درخواست‌های جدید

<strong>
{{ new_count }}
</strong>

</div>


<div class="stat">

درخواست‌های امروز

<strong>
{{ today_count }}
</strong>

</div>

</div>


<div class="table-box">

<h2>
📋 درخواست‌های مشتریان
</h2>


<table>

<tr>

<th>کد پیگیری</th>

<th>نام</th>

<th>تلفن</th>

<th>خدمت</th>

<th>متراژ</th>

<th>تاریخ</th>

<th>ساعت</th>

<th>آدرس</th>

<th>توضیحات</th>

<th>وضعیت</th>

<th>عملیات</th>

</tr>


{% for r in requests %}

<tr>

<td>
{{ r.tracking_code }}
</td>

<td>
{{ r.name }}
</td>

<td>
{{ r.phone }}
</td>

<td>
{{ r.service }}
</td>

<td>
{{ r.area }} متر
</td>

<td>
{{ r.year }} /
{{ r.month }} /
{{ r.day }}
</td>

<td>
{{ r.time }}
</td>

<td>
{{ r.address }}
</td>

<td>
{{ r.notes }}
</td>

<td>

<form
method="POST"
action="/admin/status/{{ r.id }}"
>

<select name="status">

<option
{% if r.status == 'جدید' %}
selected
{% endif %}
>
جدید
</option>

<option
{% if r.status == 'تماس گرفته شد' %}
selected
{% endif %}
>
تماس گرفته شد
</option>

<option
{% if r.status == 'رزرو شد' %}
selected
{% endif %}
>
رزرو شد
</option>

<option
{% if r.status == 'انجام شد' %}
selected
{% endif %}
>
انجام شد
</option>

<option
{% if r.status == 'لغو شد' %}
selected
{% endif %}
>
لغو شد
</option>

</select>

<button class="update">
ذخیره
</button>

</form>

</td>


<td>

<form
method="POST"
action="/admin/delete/{{ r.id }}"
onsubmit="return confirm('این درخواست حذف شود؟')"
>

<button class="delete">
حذف
</button>

</form>

</td>

</tr>

{% endfor %}

</table>

</div>

</div>

</body>

</html>
"""


@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/admin/login")


    conn = get_db()


    requests =conn.execute(
            """
            SELECT *
            FROM requests
            ORDER BY id DESC
            """
        ).fetchall()


    total = conn.execute(
            "SELECT COUNT(*) FROM requests"
        ).fetchone()[0]


    new_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE status = 'جدید'
            """
        ).fetchone()[0]


    today = datetime.now().strftime(
            "%Y-%m-%d"
        )


    today_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM requests
            WHERE substr(created_at,1,10) = ?
            """,
            (today,)
        ).fetchone()[0]


    conn.close()


    return render_template_string(
        ADMIN_HTML,

        requests=requests,

        total=total,

        new_count=new_count,

        today_count=today_count
    )


# =========================================================
# STATUS
# =========================================================

@app.route(
    "/admin/status/<int:request_id>",
    methods=["POST"]
)
def change_status(request_id):

    if not session.get("admin"):
        return redirect("/admin/login")


    status = request.form["status"]


    conn = get_db()


    conn.execute(
        """
        UPDATE requests
        SET status = ?
        WHERE id = ?
        """,
        (status, request_id)
    )


    conn.commit()
    conn.close()


    return redirect("/admin")


# =========================================================
# DELETE
# =========================================================

@app.route(
    "/admin/delete/<int:request_id>",
    methods=["POST"]
)
def delete_request(request_id):

    if not session.get("admin"):
        return redirect("/admin/login")


    conn = get_db()


    conn.execute(
        """
        DELETE FROM requests
        WHERE id = ?
        """,
        (request_id,)
    )


    conn.commit()
    conn.close()


    return redirect("/admin")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/admin/logout")
def logout():

    session.clear()

    return redirect("/admin/login")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    init_db()

    print()
    print("======================================")
    print("       TAMIZ NAZIF MANZEL")
    print("======================================")
    print("[OK] DATABASE READY")
    print("[OK] BACKEND READY")
    print("[OK] ADMIN PANEL READY")
    print()
    print("Website:")
    print("http://127.0.0.1:20200")
    print()
    print("Admin:")
    print("http://127.0.0.1:20200/admin/login")
    print()
    print("Username: admin")
    print("Password: Tamiz12345")
    print("======================================")

    app.run(
        host="0.0.0.0",
        port=20200,
        debug=True
    )