import streamlit as st
import sqlite3

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# 2. Database Initialization with Two Separated Tables (To Prevent Duplication)
def init_db():
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    # Table 1: Stores unique player profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_name TEXT PRIMARY KEY,
            player_image TEXT,
            player_club TEXT,
            player_age INTEGER
        )
    ''')
    # Table 2: Stores video clips linked to the player
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            title TEXT,
            category TEXT,
            video_url TEXT,
            FOREIGN KEY (player_name) REFERENCES players (player_name)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Smart Function to add video and handle player creation/update automatically
def add_video_smart(player_name, player_image, player_club, player_age, title, category, url):
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    
    # Check if the player already exists or update their profile data
    cursor.execute('''
        INSERT INTO players (player_name, player_image, player_club, player_age)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            player_image=excluded.player_image,
            player_club=excluded.player_club,
            player_age=excluded.player_age
    ''', (player_name.strip(), player_image.strip(), player_club.strip(), int(player_age)))
    
    # Insert the video clip
    cursor.execute('''
        INSERT INTO videos (player_name, title, category, video_url) 
        VALUES (?, ?, ?, ?)
    ''', (player_name.strip(), title, category, url))
    
    conn.commit()
    conn.close()

# Function to get unique player profiles for the cards layout
def get_all_players_profiles():
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT player_name, player_image, player_club, player_age FROM players")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[0], "image": r[1], "club": r[2], "age": r[3]} for r in rows]

# Function to get videos by player and category
def get_videos_by_player_and_category(player_name, category):
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, video_url FROM videos WHERE player_name = ? AND category = ?", (player_name, category))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "video_url": r[2]} for r in rows]

# --- TootScouting UI Layout ---
st.title("⚽ Scouting & Video Analysis Center - TootScouting")
st.markdown("---")

tab1, tab2 = st.tabs(["📺 Player Showcase & Analysis", "🔒 Analyst Control Panel"])

# ----------------- Tab 1: User / Client Interface -----------------
with tab1:
    players_list = get_all_players_profiles()
    
    if players_list:
        st.subheader("🎯 Available Player Profiles:")
        num_columns = min(len(players_list), 4)
        card_cols = st.columns(num_columns) if num_columns > 0 else []
        
        if "selected_player_name" not in st.session_state:
            st.session_state.selected_player_name = players_list[0]["name"]
            
        for idx, player in enumerate(players_list):
            col_idx = idx % 4
            with card_cols[col_idx]:
                with st.container(border=True):
                    # Perfect Circular Image Fix
                    player_img_url = player["image"] if player["image"] else "https://via.placeholder.com/150"
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px; margin-top: 10px;">
                            <img src="{player_img_url}" style="width: 130px; height: 130px; aspect-ratio: 1/1; object-fit: cover; border-radius: 50%; border: 3px solid #0D9AFF;">
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
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

        cols = st.columns(7)
        categories_buttons = [
            ("🔄 Passes", "Passes"), ("⚡ Dribbles", "Dribbles"), 
            ("🪂 Aerial Duels", "Aerial Duels"), ("🏃‍♂️ Ground Duels", "Ground Duels"), 
            ("🛑 Pressing", "Pressing"), ("📐 Crosses", "Crosses"), ("🚩 Corners", "Corners")
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
        st.info("📂 Welcome to TootScouting. Profiles will appear here once the analyst uploads the data.")

# ----------------- Tab 2: Analyst Control Panel -----------------
with tab2:
    st.subheader("🔑 Secure Analyst Login")
    password = st.text_input("Enter password to access the upload studio:", type="password")
    
    if password == "TootScouting2026":
        st.success("🔓 Access Granted!")
        st.markdown("---")
        
        st.write("### 📇 1. Lock Player Profile Details:")
        fast_name = st.text_input("Player Full Name (e.g., Iyad Al-Asiri):", key="fast_p_name")
        fast_image = st.text_input("Player Profile Image URL (Cloudinary Link):", key="fast_p_img")
        fast_club = st.text_input("Current Club Name:", key="fast_p_club")
        fast_age = st.number_input("Player Age:", min_value=12, max_value=45, value=20, key="fast_p_age")
        
        st.markdown("---")
        st.write("### 🎬 2. Upload Video Clips (Player info above remains locked):")
        
        with st.form("fast_video_form", clear_on_submit=True):
            v_title = st.text_input("Clip Title / Event Action (e.g., Deep Pass 1):")
            v_category = st.selectbox("Assign to Technical Category:", ["Passes", "Dribbles", "Aerial Duels", "Ground Duels", "Pressing", "Crosses", "Corners"])
            v_url = st.text_input("Cloudinary Video URL:")
            
            submit_video = st.form_submit_button("🚀 Upload Clip & Keep Player Profile Locked")
            
            if submit_video:
                if fast_name and v_title and v_url:
                    # Smart insert fixes the duplicate card issue completely
                    add_video_smart(fast_name, fast_image, fast_club, fast_age, v_title, v_category, v_url)
                    st.toast(f"✅ Clip successfully added for {fast_name}!", icon="🔥")
                else:
                    st.error("❌ Action Required: Ensure Player Name is filled above, and both Clip Title and URL are filled below.")
