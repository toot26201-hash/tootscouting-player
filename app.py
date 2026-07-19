import streamlit as st
import sqlite3

# 1. إعدادات الصفحة لتكون بعرض الشاشة بالكامل (مريح جداً لمشاهدة التحليل)
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# 2. إنشاء وإعداد قاعدة البيانات لتخزين روابط Cloudinary والأقسام
def init_db():
    conn = sqlite3.connect("tootscouting_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            video_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# دالة لحفظ فيديو جديد برابط Cloudinary
def add_cloudinary_video(title, category, url):
    conn = sqlite3.connect("tootscouting_media.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (title, category, video_url) VALUES (?, ?, ?)", (title, category, url))
    conn.commit()
    conn.close()

# دالة لجلب الفيديوهات المضافة حسب الزر المختار
def get_videos_by_category(category):
    conn = sqlite3.connect("tootscouting_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, video_url FROM videos WHERE category = ?", (category,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "video_url": r[2]} for r in rows]

# --- واجهة مستخدم منصة توت سكاوتنج ---
st.title("⚽ مركز مشغل الميديا والحالات - TootScouting")
st.markdown("---")

# إنشاء التبويبات (تبويب للمشاهدة وتبويب للرفع والتحكم)
tab1, tab2 = st.tabs(["📺 مشغل الميديا والتحليل", "🔗 إضافة روابط Cloudinary الجديدة"])

# ----------------- التبويب الثاني: لوحة تحكم المحلل (إضافة الفيديوهات) -----------------
with tab2:
    st.subheader("⚙️ إضافة مقطع فيديو جديد من Cloudinary")
    st.caption("ارفع الفيديو على حسابك في Cloudinary، ثم انسخ رابط الـ Delivery URL (الذي ينتهي بـ .mp4) وضعه هنا:")
    
    with st.form("cloudinary_form", clear_on_submit=True):
        video_title = st.text_input("عنوان الفيديو (مثال: تحليل التحول الهجومي السريع):")
        
        video_category = st.selectbox("اختر قسم الزرار المناسب للفيديو:", [
            "تمريرات", "دريبل", "صراعات هوائية", "صراعات أرضية", "ضغط", "عرضيات", "كورنر"
        ])
        
        video_url = st.text_input("رابط الفيديو المباشر من Cloudinary:", placeholder="https://res.cloudinary.com/.../video.mp4")
        
        submit_btn = st.form_submit_button("حفظ الفيديو في المنصة ✨")
        
        if submit_btn:
            if video_title and video_url:
                # التأكد من صحة الرابط بشكل مبدئي
                if video_url.startswith("http") and (video_url.endswith(".mp4") or "video/upload" in video_url):
                    add_cloudinary_video(video_title, video_category, video_url)
                    st.success(f"✅ تم حفظ الفيديو بنجاح وربطه بزرار ({video_category})!")
                else:
                    st.error("❌ تأكد من أن الرابط صحيح وهو رابط مباشر للفيديو من Cloudinary.")
            else:
                st.error("❌ من فضلك أكمل البيانات؛ أدخل عنوان المقطع والرابط.")

# ----------------- التبويب الأول: مشغل الميديا المفلتر بالأزرار -----------------
with tab1:
    # إدارة الـ Session State للحفاظ على الزرار النشط والفيديو الحالي
    if "active_filter" not in st.session_state:
        st.session_state.active_filter = "تمريرات"
    
    if "selected_video_url" not in st.session_state:
        st.session_state.selected_video_url = None
        
    if "selected_video_title" not in st.session_state:
        st.session_state.selected_video_title = ""

    # دالة لتحديث الفلتر وتصفير المشغل عند الانتقال بين الأزرار
    def change_filter(category_name):
        st.session_state.active_filter = category_name
        st.session_state.selected_video_url = None
        st.session_state.selected_video_title = ""

    st.write("### تصفية الحالات حسب نوع اللعبة:")
    
    # توزيع الأزرار الـ 7 المطلوبة بالتساوي على الشاشة
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
        # تلوين الزرار المختار بلون مختلف (Primary) لمعرفة القسم الحالي
        if st.session_state.active_filter == tag:
            col.button(label, key=f"filter_{tag}", use_container_width=True, type="primary")
        else:
            col.button(label, key=f"filter_{tag}", use_container_width=True, on_click=change_filter, args=(tag,))
            
    st.markdown("---")
    
    # جلب قائمة الفيديوهات الخاصة بالقسم الحالي من قاعدة البيانات
    current_playlist = get_videos_by_category(st.session_state.active_filter)
    
    if current_playlist:
        # إذا لم يقم المستخدم باختيار كليب معين بعد، نقوم بتشغيل الكليب الأول في القائمة تلقائياً
        if st.session_state.selected_video_url is None:
            st.session_state.selected_video_url = current_playlist[0]["video_url"]
            st.session_state.selected_video_title = current_playlist[0]["title"]
            
        # تقسيم شاشة العرض (3 أجزاء للمشغل : جزء واحد للقائمة الجانبية للحالات) يحاكي السكتش تماماً
        player_col, list_col = st.columns([3, 1])
        
        with player_col:
            st.subheader(f"🎬 يعرض الآن: {st.session_state.selected_video_title}")
            # تشغيل الفيديو بشكل طبيعي كامل من البداية بدون أوتوبلاي حتى يضغط المستخدم Play
            st.video(st.session_state.selected_video_url)
            
        with list_col:
            st.subheader(f"📋 المقاطع المتاحة ({len(current_playlist)})")
            st.caption("اضغط على أي مقطع لتشغيله في المشغل:")
            
            for vid in current_playlist:
                # تمييز المقطع الشغال حالياً باللون الأخضر
                if vid["video_url"] == st.session_state.selected_video_url:
                    st.success(f"▶️ {vid['title']}")
                else:
                    if st.button(f"📹 {vid['title']}", key=f"vid_btn_{vid['id']}", use_container_width=True):
                        st.session_state.selected_video_url = vid["video_url"]
                        st.session_state.selected_video_title = vid["title"]
                        st.rerun()
    else:
        st.info(f"📂 لا توجد فيديوهات مضافة في قسم ({st.session_state.active_filter}) حالياً. توجه لتبويب الإضافة لربط فيديوهات Cloudinary الخاصة بك.")
