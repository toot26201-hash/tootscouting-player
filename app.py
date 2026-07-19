import streamlit as st
import sqlite3

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# 2. إنشاء وإعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect("tootscouting_fast_media.db")
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

# دالة لحفظ فيديو جديد
def add_cloudinary_video(player_name, player_image, player_club, player_age, title, category, url):
    conn = sqlite3.connect("tootscouting_fast_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (player_name, player_image, player_club, player_age, title, category, video_url) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (player_name.strip(), player_image.strip(), player_club.strip(), int(player_age), title, category, url))
    conn.commit()
    conn.close()

# دالة لجلب كروت اللاعبين
def get_all_players_cards():
    conn = sqlite3.connect("tootscouting_fast_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name, player_image, player_club, player_age FROM videos")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[0], "image": r[1], "club": r[2], "age": r[3]} for r in rows]

# دالة لجلب الفيديوهات بناءً على اللاعب والقسم
def get_videos_by_player_and_category(player_name, category):
    conn = sqlite3.connect("tootscouting_fast_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, video_url FROM videos WHERE player_name = ? AND category = ?", (player_name, category))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "video_url": r[2]} for r in rows]

# --- واجهة مستخدم منصة توت سكاوتنج ---
st.title("⚽ مركز كشافة ومشغل ميديا اللاعبين - TootScouting")
st.markdown("---")

tab1, tab2 = st.tabs(["📺 معرض اللاعبين والتحليل", "🔒 لوحة تحكم المحلل (الرفع السريع المكثف)"])

# ----------------- التبويب الأول: واجهة العرض والمشاهدة للمستخدم -----------------
with tab1:
    players_list = get_all_players_cards()
    
    if players_list:
        st.subheader("🎯 بطاقات كشافة اللاعبين المتاحين:")
        num_columns = min(len(players_list), 4)
        card_cols = st.columns(num_columns) if num_columns > 0 else []
        
        if "selected_player_name" not in st.session_state:
            st.session_state.selected_player_name = players_list[0]["name"]
            
        for idx, player in enumerate(players_list):
            col_idx = idx % 4
            with card_cols[col_idx]:
                with st.container(border=True):
                    if player["image"]:
                        st.image(player["image"], use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/150", use_container_width=True)
                    st.subheader(player["name"])
                    st.write(f"🏃‍♂️ **النادي:** {player['club']}")
                    st.write(f"🎂 **السن:** {player['age']} عام")
                    
                    if st.button(f"🔎 عرض تحليل {player['name']}", key=f"select_{player['name']}", use_container_width=True):
                        st.session_state.selected_player_name = player["name"]
                        st.session_state.active_filter = "تمريرات"
                        st.session_state.selected_video_url = None
                        st.session_state.selected_video_title = ""
                        st.rerun()

        st.markdown("---")
        st.write(f"## 📊 نافذة التحليل الفني للاعب: **{st.session_state.selected_player_name}**")
        
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

        cols = st.columns(7)
        categories_buttons = [
            ("🔄 التمريرات", "تمريرات"), ("⚡ الدريبل", "دريبل"), 
            ("🪂 صراعات هوائية", "صراعات هوائية"), ("🏃‍♂️ صراعات أرضية", "صراعات أرضية"), 
            ("🛑 الضغط", "ضغط"), ("📐 العرضيات", "عرضيات"), ("🚩 الكورنر", "كورنر")
        ]
        
        for col, (label, tag) in zip(cols, categories_buttons):
            if st.session_state.active_filter == tag:
                col.button(label, key=f"user_filter_{tag}", use_container_width=True, type="primary")
            else:
                col.button(label, key=f"user_filter_{tag}", use_container_width=True, on_click=change_filter, args=(tag,))
                
        st.markdown("---")
        
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
            st.info(f"📂 لا توجد فيديوهات مضافة في قسم ({st.session_state.active_filter}) حالياً.")
    else:
        st.info("📂 سيتم عرض اللاعبين هنا بمجرد رفع البيانات.")

# ----------------- التبويب الثاني: لوحة تحكم المحلل (الرفع السريع بدون تكرار) -----------------
with tab2:
    st.subheader("🔑 تسجيل الدخول للوحة التحكم")
    password = st.text_input("أدخل كلمة المرور الخاصة بالمحلل:", type="password")
    
    if password == "TootScouting2026":
        st.success("🔓 تم تأكيد الهوية! يمكنك الآن استخدام الرفع المكثف السريع.")
        st.markdown("---")
        
        # الجزء الأول: بيانات اللاعب الثابتة (تكتبها مرة واحدة فقط طول الجلسة)
        st.write("### 📇 1. تثبيت بيانات كارت اللاعب:")
        fast_name = st.text_input("اسم اللاعب بالكامل:", key="fast_p_name")
        fast_image = st.text_input("رابط صورة اللاعب من Cloudinary:", key="fast_p_img")
        fast_club = st.text_input("نادي اللاعب الحالي:", key="fast_p_club")
        fast_age = st.number_input("عمر اللاعب:", min_value=12, max_value=45, value=20, key="fast_p_age")
        
        st.markdown("---")
        
        # الجزء الثاني: نموذج إضافة الحالات المتكرر (البيانات هنا فقط يتم تصفيرها بعد كل ضغطة)
        st.write("### 🎬 2. ارفع الفيديوهات وراء بعضها هنا (بيانات اللاعب فوق ستظل ثابتة):")
        
        # استخدام st.form لضمان عملية تصفير سريعة وخاصة بخانات الفيديو فقط
        with st.form("fast_video_form", clear_on_submit=True):
            v_title = st.text_input("عنوان لقطة الفيديو (مثال: تمريرة لكسر الخطوط 1):")
            v_category = st.selectbox("اختر قسم الزرار المناسب:", ["تمريرات", "دريبل", "صراعات هوائية", "صراعات أرضية", "ضغط", "عرضيات", "كورنر"])
            v_url = st.text_input("رابط الفيديو من Cloudinary:")
            
            submit_video = st.form_submit_button("🚀 رفع الفيديو الحالي والانتقال للتالي فوراً")
            
            if submit_video:
                if fast_name and v_title and v_url:
                    # حفظ في قاعدة البيانات مع سحب بيانات اللاعب الثابتة من الأعلى
                    add_cloudinary_video(fast_name, fast_image, fast_club, fast_age, v_title, v_category, v_url)
                    st.toast(f"✅ تم حفظ مقطع ({v_title}) بنجاح للاعب {fast_name}!", icon="🔥")
                else:
                    st.error("❌ تأكد من كتابة اسم اللاعب فوق، بالإضافة لعنوان ورابط الفيديو في هذا النموذج.")
