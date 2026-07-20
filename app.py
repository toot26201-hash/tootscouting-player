import streamlit as st
import sqlite3

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# 2. Database Initialization
def init_db():
    conn = sqlite3.connect("tootscouting_english_media.db")
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

# Function to add a video
def add_cloudinary_video(player_name, player_image, player_club, player_age, title, category, url):
    conn = sqlite3.connect("tootscouting_english_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (player_name, player_image, player_club, player_age, title, category, video_url) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (player_name.strip(), player_image.strip(), player_club.strip(), int(player_age), title, category, url))
    conn.commit()
    conn.close()

# Function to get all unique player cards
def get_all_players_cards():
    conn = sqlite3.connect("tootscouting_english_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name, player_image, player_club, player_age FROM videos")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[0], "image": r[1], "club": r[2], "age": r[3]} for r in rows]

# Function to get videos by player and category
def get_videos_by_player_and_category(player_name, category):
    conn = sqlite3.connect("tootscouting_english_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, video_url FROM videos WHERE player_name = ? AND category = ?", (player_name, category))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "video_url": r[2]} for r in rows]

# --- TootScouting UI Layout ---
st.title("⚽ Scouting & Video Analysis Center - TootScouting")
st.markdown("---")

# Navigation Tabs
tab1, tab2 = st.tabs(["📺 Player Showcase & Analysis", "🔒 Analyst Control Panel"])

# ----------------- Tab 1: User / Client Interface (English) -----------------
with tab1:
    players_list = get_all_players_cards()
    
    if players_list:
        st.subheader("🎯 Available Player Profiles:")
        num_columns = min(len(players_list), 4)
        card_cols = st.columns(num_columns) if num_columns > 0 else []
        
        if "selected_player_name" not in st.session_state:
            st.session_state.selected_player_name = players_list[0]["name"] if players_list else ""
            
        for idx, player in enumerate(players_list):
            col_idx = idx % 4
            with card_cols[col_idx]:
                with st.container(border=True):
                    # Fixed & Compact Circular Profile Image Design
                    player_img_url = player["image"] if player["image"] else "https://via.placeholder.com/150"
                    st.markdown(
                        f"""
                        <div style="text-align: center; margin-bottom: 15px; margin-top: 10px;">
                            <img src="{player_img_url}" style="width: 130px; height: 130px; object-fit: cover; border-radius: 50%; border: 3px solid #0D9AFF;">
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    # Player Information Text (Centered)
                    st.markdown(f"<h3 style='text-align: center; margin-bottom: 5px;'>{player['name']}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; margin-bottom: 2px;'>🏃‍♂️ <b>Club:</b> {player['club']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; margin-bottom: 15px;'>🎂 <b>Age:</b> {player['age']} Y/O</p>", unsafe_allow_html=True)
                    
                    if st.button(f"🔎 View Analysis", key=f"select_{player['name']}", use_container_width=True):
                        st.session_state.selected_player_name = player["name"]
                        st.session_state.active_filter = "Passes"
                        st.session_state.selected_video_url = None
                        st.session_state.selected_video_title = ""
                        st.rerun()

        st.markdown("---")
        st.write(f"## 📊 Technical Performance Dashboard: **{st.session_state.selected_player_name}**")
        
        if "active_filter" not in st.session_state:
            st.session_state.active_filter = "Passes"
        if "selected_video_url" not in st.session_state:
            st.session_state.selected_video_url = None
        if "selected_video_title" not in st.session_state:
            st.session_state.selected_video_title = ""

        def change_filter(category_name):
            st.session_state.active_filter = category_name
            st.session_state.selected_video_url = None
            st.session_state.selected_video_title = ""

        # The 7 Requested Buttons in English
        cols = st.columns(7)
        categories_buttons = [
            ("🔄 Passes", "Passes"), 
            ("⚡ Dribbles", "Dribbles"), 
            ("🪂 Aerial Duels", "Aerial Duels"), 
            ("🏃‍♂️ Ground Duels", "Ground Duels"), 
            ("🛑 Pressing", "Pressing"), 
            ("📐 Crosses", "Crosses"), 
            ("🚩 Corners", "Corners")
        ]
        
        for col, (label, tag) in zip(cols, categories_buttons):
            if st.session_state.active_filter == tag:
                col.button(label, key=f"user_filter_{tag}", use_container_width=True, type="primary")
            else:
                col.button(label, key=f"user_filter_{tag}", use_container_width=True, on_click=change_filter, args=(tag,))
                
        st.markdown("---")
        
        # Fetching filtered videos
        current_playlist = get_videos_by_player_and_category(st.session_state.selected_player_name, st.session_state.active_filter)
        
        if current_playlist:
            if st.session_state.selected_video_url is None:
                st.session_state.selected_video_url = current_playlist[0]["video_url"]
                st.session_state.selected_video_title = current_playlist[0]["title"]
                
            player_col, list_col = st.columns([3, 1])
            
            with player_col:
                st.subheader(f"🎬 Current Clip: {st.session_state.selected_video_title}")
                url = st.session_state.selected_video_url
                if "player.cloudinary.com" in url or "iframe" in url:
                    st.components.v1.iframe(url, height=520, scrolling=False)
                else:
                    st.video(url)
                
            with list_col:
                st.subheader(f"📋 Video Clips")
                for vid in current_playlist:
                    if vid["video_url"] == st.session_state.selected_video_url:
                        st.success(f"▶️ {vid['title']}")
                    else:
                        if st.button(f"📹 {vid['title']}", key=f"user_vid_btn_{vid['id']}", use_container_width=True):
                            st.session_state.selected_video_url = vid["video_url"]
                            st.session_state.selected_video_title = vid["title"]
                            st.rerun()
        else:
            st.info(f"📂 No video clips available under ({st.session_state.active_filter}) for this player yet.")
    else:
        st.info("📂 Welcome to TootScouting. Clips will appear here once the analyst uploads the technical data.")

# ----------------- Tab 2: Analyst Control Panel (Password Protected) -----------------
with tab2:
    st.subheader("🔑 Secure Analyst Login")
    password = st.text_input("Enter password to access the upload studio:", type="password")
    
    # Password set to "TootScouting2026"
    if password == "TootScouting2026":
        st.success("🔓 Access Granted! You can now upload clips rapidly.")
        st.markdown("---")
        
        # Part 1: Persistent Player Metadata Lock
        st.write("### 📇 1. Lock Player Profile Details (Stays saved during bulk upload):")
        fast_name = st.text_input("Player Full Name (e.g., Iyad Al-Asiri):", key="fast_p_name")
        fast_image = st.text_input("Player Profile Image URL (Cloudinary Link):", key="fast_p_img")
        fast_club = st.text_input("Current Club Name:", key="fast_p_club")
        fast_age = st.number_input("Player Age:", min_value=12, max_value=45, value=20, key="fast_p_age")
        
        st.markdown("---")
        
        # Part 2: Dynamic Video Form (Clears automatically for the next clip)
        st.write("### 🎬 2. Upload Video Clips (Player info above remains locked):")
        
        with st.form("fast_video_form", clear_on_submit=True):
            v_title = st.text_input("Clip Title / Event Action (e.g., Line-Breaking Pass 1):")
            v_category = st.selectbox("Assign to Technical Category (Button):", ["Passes", "Dribbles", "Aerial Duels", "Ground Duels", "Pressing", "Crosses", "Corners"])
            v_url = st.text_input("Cloudinary Video URL (Embed or Direct Link):")
            
            submit_video = st.form_submit_button("🚀 Upload Clip & Clear Input for Next")
            
            if submit_video:
                if fast_name and v_title and v_url:
                    add_cloudinary_video(fast_name, fast_image, fast_club, fast_age, v_title, v_category, v_url)
                    st.toast(f"✅ Clip successfully added for {fast_name}!", icon="🔥")
                else:
                    st.error("❌ Action Required: Ensure Player Name is filled above, and both Clip Title and URL are filled below.")
