import streamlit as st
import sqlite3

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# 2. إنشاء وإعداد قاعدة البيانات المطورة لدعم اسم اللاعب
def init_db():
    conn = sqlite3.connect("tootscouting_players_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            title TEXT,
            category TEXT,
            video_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# دالة لحفظ فيديو جديد مع ربطه باللاعب والقسم
def add_cloudinary_video(player_name, title, category, url):
    conn = sqlite3.connect("tootscouting_players_media.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (player_name, title, category, video_url) VALUES (?, ?, ?, ?)", 
                   (player_name.strip(), title, category, url))
    conn.commit()
    conn.close()

# دالة لجلب قائمة اللاعبين المتاحين في قاعدة البيانات بدون تكرار
def get_all_players():
    conn = sqlite3.connect("tootscouting_players_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name FROM videos")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

# دالة لجلب الفيديوهات بناءً على اللاعب النشط والقسم النشط
def get_videos_by_player_and_category(player_name, category):
    conn = sqlite3.connect("tootscouting_players_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, video_url FROM videos WHERE player_name = ? AND category = ?", (player_name, category))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "video_url": r[2]} for r in rows]

# --- واجهة مستخدم منصة توت سكاوتنج ---
st.title("⚽ مركز مشغل ميديا اللاعبين - TootScouting")
st.markdown("---")

tab1, tab2 = st.tabs(["📺 مشغل الميديا والتحليل", "🔗 لوحة تحكم المحلل (إضافة لاعبين وفيديوهات)"])

# ----------------- التبويب الثاني: لوحة تحكم المحلل (إضافة الفيديوهات واللاعبين) -----------------
with tab2:
    st.subheader("⚙️ رفع وإضافة فيديو جديد للاعب")
    
    with st.form("cloudinary_form", clear_on_submit=True):
        # خانة اسم اللاعب (لو الاسم جديد هيتضاف في القائمة تلقائي، ولو موجود هيتجمع تحته)
        player_name = st.text_input("اسم اللاعب (مثال: إياد العسيري):")
        
        video_title = st.text_input("عنوان الفيديو الحركي (مثال: تمريرة لعمق المهاجم):")
        
        video_category = st.selectbox("اختر قسم الزرار المناسب للفيديو:", [
            "تمريرات", "دريبل", "صراعات هوائية", "صراعات أرضية", "ضغط", "عرضيات", "كورنر"
        ])
        
        video_url = st.text_input("رابط الفيديو (سواء Embed أو رابط مباشر ينتهي بـ .mp4):")
        
        submit_btn = st.form_submit_button("حفظ المقطع في ملف اللاعب ✨")
        
        if submit_btn:
            if player_name and video_title and video_url:
                add_cloudinary_video(player_name, video_title, video_category, video_url)
                st.success(f"✅ تم حفظ الفيديو بنجاح وربطه باللاعب ({player_name}) في قسم ({video_category})!")
            else:
                st.error("❌ من فضلك أكمل جميع الخانات (اسم اللاعب، عنوان الفيديو، والرابط).")

# ----------------- التبويب الأول: مشغل الميديا المفلتر باللاعبين والأزرار -----------------
with tab1:
    # جلب قائمة اللاعبين المتاحين أونلاين
    available_players = get_all_players()
    
    if available_players:
        # 1. قائمة منسدلة لاختيار اللاعب أولاً في أعلى الصفحة
        selected_player = st.selectbox("🎯 اختر اللاعب المراد عرض تحليله:", available_players)
        
        # إدارة الـ Session State للحفاظ على الزرار النشط والفيديو الحالي
        if "active_filter" not in st.session_state:
            st.session_state.active_filter = "تمريرات"
        
        if "selected_video_url" not in st.session_state:
            st.session_state.selected_video_url = None
            
        if "selected_video_title" not in st.session_state:
            st.session_state.selected_video_title = ""

        # دالة لتحديث الفلتر وتصفير المشغل عند الانتقال بين الأزرار الـ 7
        def change_filter(category_name):
            st.session_state.active_filter = category_name
            st.session_state.selected_video_url = None
            st.session_state.selected_video_title = ""

        st.write(f"### حالات اللاعب ({selected_player}) المفلترة حسب نوع اللعبة:")
        
        # الأزرار الـ 7 المطلوبة موزعة بالتساوي
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
                col.button(label, key=f"filter_{tag}", use_container_width=True, type="primary")
            else:
                col.button(label, key=f"filter_{tag}", use_container_width=True, on_click=change_filter, args=(tag,))
                
        st.markdown("---")
        
        # جلب الفيديوهات الخاصة باللاعب المحدد + القسم المحدد
        current_playlist = get_videos_by_player_and_category(selected_player, st.session_state.active_filter)
        
        if current_playlist:
            if st.session_state.selected_video_url is None:
                st.session_state.selected_video_url = current_playlist[0]["video_url"]
                st.session_state.selected_video_title = current_playlist[0]["title"]
                
            # تقسيم شاشة العرض (3 أجزاء للمشغل : جزء واحد للقائمة الجانبية للكليبات)
            player_col, list_col = st.columns([3, 1])
            
            with player_col:
                st.subheader(f"🎬 {st.session_state.selected_video_title}")
                
                url = st.session_state.selected_video_url
                # ذكاء اصطناعي برمجياً: تشغيل الرابط سواء كان Embed iFrame أو رابط مباشر .mp4 تلقائياً
                if "player.cloudinary.com" in url or "iframe" in url:
                    st.components.v1.iframe(url, height=520, scrolling=False)
                else:
                    st.video(url)
                
            with list_col:
                st.subheader(f"📋 مقاطع الفيديو ({len(current_playlist)})")
                
                for vid in current_playlist:
                    if vid["video_url"] == st.session_state.selected_video_url:
                        st.success(f"▶️ {vid['title']}")
                    else:
                        if st.button(f"📹 {vid['title']}", key=f"vid_btn_{vid['id']}", use_container_width=True):
                            st.session_state.selected_video_url = vid["video_url"]
                            st.session_state.selected_video_title = vid["title"]
                            st.rerun()
        else:
            st.info(f"📂 لا توجد فيديوهات مضافة للاعب **{selected_player}** في قسم ({st.session_state.active_filter}) حالياً.")
    else:
        st.info("📂 المنصة فارغة حالياً. توجه لتبويب الإضافة لرفع أول لاعب وحالاته من Cloudinary.")
