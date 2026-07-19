import streamlit as st
import sqlite3

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# 2. إنشاء وإعداد قاعدة البيانات المطورة لدعم بيانات بطاقة اللاعب
def init_db():
    conn = sqlite3.connect("tootscouting_luxury_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            player_image TEXT,
            player_club TEXT,
            player_age INTEGER,
            title TEXT,
            category TEXT,
            video_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# دالة لحفظ فيديو جديد مع بيانات اللاعب
def add_cloudinary_video(player_name, player_image, player_club, player_age, title, category, url):
    conn = sqlite3.connect("tootscouting_luxury_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (player_name, player_image, player_club, player_age, title, category, video_url) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (player_name.strip(), player_image.strip(), player_club.strip(), int(player_age), title, category, url))
    conn.commit()
    conn.close()

# دالة لجلب بيانات اللاعبين الفريدة لإنشاء البطاقات
def get_all_players_cards():
    conn = sqlite3.connect("tootscouting_luxury_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name, player_image, player_club, player_age FROM videos")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[0], "image": r[1], "club": r[2], "age": r[3]} for r in rows]

# دالة لجلب الفيديوهات بناءً على اللاعب والقسم
def get_videos_by_player_and_category(player_name, category):
    conn = sqlite3.connect("tootscouting_luxury_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, video_url FROM videos WHERE player_name = ? AND category = ?", (player_name, category))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "video_url": r[2]} for r in rows]

# --- واجهة مستخدم منصة توت سكاوتنج ---
st.title("⚽ مركز كشافة ومشغل ميديا اللاعبين - TootScouting")
st.markdown("---")

# إنشاء التبويبات
tab1, tab2 = st.tabs(["📺 معرض اللاعبين والتحليل", "🔒 لوحة تحكم المحلل الخاصة"])

# ----------------- التبويب الأول: واجهة المستخدم أو العميل (بطاقات الكشافة ومشغل الميديا) -----------------
with tab1:
    players_list = get_all_players_cards()
    
    if players_list:
        st.subheader("🎯 بطاقات كشافة اللاعبين المتاحين:")
        
        # عرض بطاقات اللاعبين في صفوف (كل صف يحتوي على 4 لاعبين كحد أقصى)
        # لحساب عدد الأعمدة ديناميكياً
        num_columns = min(len(players_list), 4)
        card_cols = st.columns(num_columns) if num_columns > 0 else []
        
        # إنشاء Session State لحفظ اللاعب الذي ضغط المستخدم على زر عرضه
        if "selected_player_name" not in st.session_state:
            st.session_state.selected_player_name = players_list[0]["name"]
            
        for idx, player in enumerate(players_list):
            col_idx = idx % 4
            with card_cols[col_idx]:
                # تصميم صندوق أو حاوية صغيرة لكل لاعب
                with st.container(border=True):
                    # عرض صورة اللاعب (إذا لم تتوفر يعرض صورة افتراضية)
                    if player["image"]:
                        st.image(player["image"], use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/150", caption="لا توجد صورة", use_container_width=True)
                    
                    st.subheader(player["name"])
                    st.write(f"🏃‍♂️ **النادي:** {player['club']}")
                    st.write(f"🎂 **السن:** {player['age']} عام")
                    
                    # زر لاختيار هذا اللاعب وفتح مشغله بالأسفل
                    if st.button(f"🔎 عرض تحليل {player['name']}", key=f"select_{player['name']}", use_container_width=True):
                        st.session_state.selected_player_name = player["name"]
                        st.session_state.active_filter = "تمريرات"  # تصفير الأزرار للبدء بالتمريرات
                        st.session_state.selected_video_url = None
                        st.session_state.selected_video_title = ""
                        st.rerun()

        st.markdown("---")
        st.write(f"## 📊 نافذة التحليل الفني للاعب: **{st.session_state.selected_player_name}**")
        
        # إدارة الـ Session State للأزرار والمشغل
        if "active_filter" not in st.session_state:
            st.session_state.active_filter = "تمريرات"
        if "selected_video_url" not in st.session_state:
            st.session_state.selected_video_url = None
        if "selected_video_title" not in st.session_state:
            st.session_state.selected_video_title = ""

        def change_filter(category_name):
            st.session_state.active_filter = category_name
            st.session_state.selected_video_url = None
            st.session_state.selected_video_title = ""

        # الأزرار السبعة الشهيرة
        cols = st.columns(7)
        categories_buttons = [
            ("🔄 التمريرات", "تمريرات"),
            ("⚡ الدريبل", "دريبل"),
            ("🪂 صراعات هوائية", "صراعات هوائية"),
            ("🏃‍♂️ صراعات أرضية", "صراعات أرضية"),
            ("🛑 الضغط", "ضغط"),
            ("📐 العرضيات", "عرضيات"),
            ("🚩 الكورنر", "كورنر")
        ]
        
        for col, (label, tag) in zip(cols, categories_buttons):
            if st.session_state.active_filter == tag:
                col.button(label, key=f"user_filter_{tag}", use_container_width=True, type="primary")
            else:
                col.button(label, key=f"user_filter_{tag}", use_container_width=True, on_click=change_filter, args=(tag,))
                
        st.markdown("---")
        
        # جلب فيديوهات اللاعب المختار + القسم المختار
        current_playlist = get_videos_by_player_and_category(st.session_state.selected_player_name, st.session_state.active_filter)
        
        if current_playlist:
            if st.session_state.selected_video_url is None:
                st.session_state.selected_video_url = current_playlist[0]["video_url"]
                st.session_state.selected_video_title = current_playlist[0]["title"]
                
            player_col, list_col = st.columns([3, 1])
            
            with player_col:
                st.subheader(f"🎬 {st.session_state.selected_video_title}")
                url = st.session_state.selected_video_url
                if "player.cloudinary.com" in url or "iframe" in url:
                    st.components.v1.iframe(url, height=520, scrolling=False)
                else:
                    st.video(url)
                
            with list_col:
                st.subheader(f"📋 قائمة المقاطع")
                for vid in current_playlist:
                    if vid["video_url"] == st.session_state.selected_video_url:
                        st.success(f"▶️ {vid['title']}")
                    else:
                        if st.button(f"📹 {vid['title']}", key=f"user_vid_btn_{vid['id']}", use_container_width=True):
                            st.session_state.selected_video_url = vid["video_url"]
                            st.session_state.selected_video_title = vid["title"]
                            st.rerun()
        else:
            st.info(f"📂 لا توجد فيديوهات مضافة للاعب في قسم ({st.session_state.active_filter}) حالياً.")
    else:
        st.info("📂 مرحباً بك في منصة توت سكاوتنج. سيتم عرض بطاقات اللاعبين وفيديوهاتهم هنا بمجرد إضافة المحلل للحالات.")

# ----------------- التبويب الثاني: لوحة تحكم المحلل (محمية بكلمة سر) -----------------
with tab2:
    st.subheader("🔑 تسجيل الدخول للوحة التحكم")
    password = st.text_input("أدخل كلمة المرور الخاصة بالمحلل لرؤية نموذج الرفع والبيانات:", type="password")
    
    if password == "TootScouting2026":
        st.success("🔓 تم تأكيد الهوية بنجاح! يمكنك إضافة وتحديث بيانات كروت اللاعبين وفيديوهاتهم.")
        st.markdown("---")
        
        with st.form("admin_luxury_form", clear_on_submit=True):
            st.write("### 📇 بيانات كارت كشافة اللاعب (تُكتب مع أول فيديو ويرتبط بها أي فيديو لاحق):")
            player_name = st.text_input("اسم اللاعب بالكامل (مثال: إياد العسيري):")
            player_image = st.text_input("رابط صورة اللاعب (يمكنك رفع الصورة على Cloudinary ووضع الرابط المباشر هنا):")
            player_club = st.text_input("النادي الحالي للاعب:")
            player_age = st.number_input("عمر اللاعب الحقيقي:", min_value=12, max_value=45, value=20)
            
            st.markdown("---")
            st.write("### 🎬 تفاصيل مقطع الفيديو الحالي:")
            video_title = st.text_input("عنوان الفيديو الحركي (مثال: افتكاك رائع في ثلث الملعب الدفاعي):")
            
            video_category = st.selectbox("اختر قسم الزرار المناسب للفيديو:", [
                "تمريرات", "دريبل", "صراعات هوائية", "صراعات أرضية", "ضغط", "عرضيات", "كورنر"
            ])
            
            video_url = st.text_input("رابط الفيديو من Cloudinary (Embed أو رابط مباشر):")
            
            submit_btn = st.form_submit_button("حفظ المقطع وإنشاء/تحديث كارت اللاعب ✨")
            
            if submit_btn:
                if player_name and video_title and video_url and player_club:
                    add_cloudinary_video(player_name, player_image, player_club, player_age, video_title, video_category, video_url)
                    st.success(f"✅ تم حفظ الفيديو بنجاح وربطه ببطاقة اللاعب ({player_name})!")
                    st.rerun()
                else:
                    st.error("❌ من فضلك تأكد من ملء الحقول الأساسية (الاسم، النادي، عنوان الفيديو، والرابط).")
    elif password != "":
        st.error("❌ كلمة المرور غير صحيحة!")
