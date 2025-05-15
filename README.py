import streamlit as st
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin

# 1. Firebase Admin SDK sozlamasi
cred = credentials.Certificate("serviceAccountKey.json")  # sizning kalit faylingiz yo'li
if not firebase_admin._apps:
    initialize_app(cred)
db = firestore.client()

# 2. Admin login ma'lumotlari
ADMIN_EMAIL = "shaxriyorcholiyev951@gmail.com"
ADMIN_PASSWORD = "admin123"

# 3. Psixologik savollar ro'yxati (30 ta)
questions = [
    "Siz qanday his qilasiz?",
    "Maktabdagi baholaringiz qanday?",
    "Do'stlaringiz bilan munosabatingiz qanday?",
    "Oila bilan munosabatlaringiz qanday?",
    "Bo'sh vaqtingizni qanday o'tkazasiz?",
    "O'zligingizni qanday baholaysiz?",
    "Kelajak rejalaringiz qanday?",
    "Stress bilan qanday kurashasiz?",
    "O'zingizga ishonchingiz qanchalik?",
    "Maktabga qanday tayyorlanasiz?",
    "Yangi do'stlar orttirish qobiliyatingiz bormi?",
    "Boshqalar oldida o'zingizni qanday his qilasiz?",
    "Sizni nima hayajonlantiradi?",
    "Qanday qobiliyatlaringiz bor deb o'ylaysiz?",
    "Maktabdan tashqari qiziqishlaringiz qanday?",
    "Kelajakda nimani o'zgartirmoqchisiz?",
    "Eng muhim qadriyatlaringiz nimalar?",
    "His-tuyg'ularingizni qanday ifodalasiz?",
    "Qiyin vaziyatlarda qanday harakat qilasiz?",
    "Sizga qanday maslahatlar beriladi?",
    "O'zligingizni qanchalik tushunasiz?",
    "Sizni nima ruhlantiradi?",
    "Qaysi mashg'ulotlar yoqadi?",
    "Stressni qanday kamaytirasiz?",
    "Qaysi odatlar mavjud?",
    "Qanday qaror qabul qilasiz?",
    "Oila va do'stlaringiz bilan munosabatlaringiz qanday?",
    "Nima siz uchun baxt manbai?",
    "O'zgarishlarga munosabatingiz qanday?",
    "Kelajak uchun eng katta orzuingiz nima?"
]

answer_options = ["A", "B", "C"]


# 4. Login funksiyasi
def login():
    st.title("Admin Login")
    email = st.text_input("Email")
    password = st.text_input("Parol", type="password")
    if st.button("Kirish"):
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            st.session_state["logged_in"] = True
        else:
            st.error("Noto‘g‘ri email yoki parol!")


# 5. Admin panel
def admin_panel():
    st.title("Admin Panel")
    st.write("Foydalanuvchilar ro‘yxati:")
    users_ref = db.collection("users")
    users = users_ref.stream()
    for user in users:
        st.write(user.to_dict())

    st.write("---")
    st.write("Test natijalari:")
    results_ref = db.collection("results")
    results = results_ref.stream()
    for res in results:
        st.write(res.to_dict())

    if st.button("Chiqish"):
        st.session_state["logged_in"] = False


# 6. Foydalanuvchi uchun test formasi
def user_test():
    st.title("Psixologik Test")

    with st.form("user_info"):
        ism = st.text_input("Ism")
        familiya = st.text_input("Familiya")
        yosh = st.number_input("Yosh", min_value=6, max_value=18)
        jins = st.selectbox("Jins", ["Erkak", "Ayol"])
        viloyat = st.selectbox("Viloyat", [
            "Toshkent", "Samarqand", "Buxoro", "Farg'ona", "Namangan",
            "Andijon", "Qashqadaryo", "Navoiy", "Xorazm", "Surxondaryo",
            "Jizzax", "Sirdaryo"
        ])
        submitted = st.form_submit_button("Testni boshlash")

    if submitted:
        if not ism or not familiya or not yosh or not jins or not viloyat:
            st.error("Iltimos barcha maydonlarni to‘ldiring!")
            return
        st.session_state["user_info"] = {
            "ism": ism,
            "familiya": familiya,
            "yosh": yosh,
            "jins": jins,
            "viloyat": viloyat
        }
        st.session_state["current_question"] = 0
        st.session_state["answers"] = [None] * len(questions)
        st.experimental_rerun()

    if "user_info" in st.session_state:
        show_questions()


# 7. Savollarni ko‘rsatish va javob qabul qilish
def show_questions():
    q_idx = st.session_state["current_question"]
    st.write(f"**Savol {q_idx+1}:** {questions[q_idx]}")

    answer = st.radio("Javobni tanlang:", answer_options, index=st.session_state["answers"][q_idx] or 0, key=f"ans{q_idx}")

    st.session_state["answers"][q_idx] = answer

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Oldingi") and q_idx > 0:
            st.session_state["current_question"] -= 1
            st.experimental_rerun()
    with col2:
        if st.button("Keyingi") and q_idx < len(questions) - 1:
            st.session_state["current_question"] += 1
            st.experimental_rerun()
    with col3:
        if st.button("Yakunlash") and None not in st.session_state["answers"]:
            save_results()
            st.success("Test natijalaringiz saqlandi!")
            st.session_state.pop("user_info")
            st.session_state.pop("answers")
            st.session_state.pop("current_question")
            st.experimental_rerun()
        elif st.button("Yakunlash"):
            st.warning("Iltimos, barcha savollarga javob bering.")


# 8. Natijalarni Firestore ga saqlash
def save_results():
    data = {
        **st.session_state["user_info"],
        "answers": st.session_state["answers"]
    }
    db.collection("users").add({
        "ism": data["ism"],
        "familiya": data["familiya"],
        "yosh": data["yosh"],
        "jins": data["jins"],
        "viloyat": data["viloyat"],
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    db.collection("results").add({
        "answers": data["answers"],
        "timestamp": firestore.SERVER_TIMESTAMP
    })


# 9. Dastur ishga tushishi
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Tizim ishga tushishi
if st.session_state["logged_in"]:
    admin_panel()
else:
    # Agar admin email/parol to‘g‘ri bo‘lsa, admin panel ko‘rinadi
    # Aks holda, foydalanuvchi test oynasi
    page = st.sidebar.selectbox("Bo‘limni tanlang", ["Foydalanuvchi Testi", "Admin Kirish"])
    if page == "Admin Kirish":
        login()
    else:
        user_test()
