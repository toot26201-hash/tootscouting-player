import streamlit as st
import sqlite3
import re

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# 2. Database Initialization
def init_db():
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    
    # Table 1: Players Profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_name TEXT PRIMARY KEY,
            player_image TEXT,
            player_club TEXT,
            player_age INTEGER,
            sofa_link TEXT
        )
    ''')
    
    # Migration to add sofa_link if database already exists
    try:
        cursor.execute("ALTER TABLE players ADD COLUMN sofa_link TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    # Table 2: Videos
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

# Smart function to process Google Drive links for direct iframe preview
def process_google_drive_link(url):
    if "drive.google.com" in url:
        match = re.search(r'/d/([^/]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/file/d/{file_id}/preview"
    return url

# Smart function to process Vimeo URLs into player embed links
def process_vimeo_link(url):
    if "vimeo.com" in url:
        match = re.search(r'vimeo\.com/(\d+)', url)
        if match:
            video_id = match.group(1)
            return f"https://player.vimeo.com/video/{video_id}"
    return url

# Function to add video smartly
def add_video_smart(player_name, player_image, player_club, player_age, sofa_link, title, category, url):
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO players (player_name, player_image, player_club, player_age, sofa_link)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            player_image=excluded.player_image,
            player_club=excluded.player_club,
            player_age=excluded.player_age,
            sofa_link=excluded.sofa_link
    ''', (player_name.strip(), player_image.strip(), player_club.strip(), int(player_age), sofa_link.strip()))
    
    cursor.execute('''
        INSERT INTO videos (player_name, title, category, video_url) 
        VALUES (?, ?, ?, ?)
    ''', (player_name.strip(), title, category, url))
    conn.commit()
    conn.close()

# Function to get all players profiles
def get_all_players_profiles():
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT player_name, player_image, player_club, player_age, sofa_link FROM players")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[0], "image": r[1], "club": r[2], "age": r[3], "sofa_link": r[4]} for r in rows]

# Function to get videos by player and category
def get_videos_by_player_and_category(player_name, category):
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, video_url FROM videos WHERE player_name = ? AND category = ?", (player_name, category))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "video_url": r[2]} for r in rows]

# Function to get ALL videos for management deletion
def get_all_videos_raw():
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, player_name, title, category FROM videos ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to delete a video by ID
def delete_video_by_id(video_id):
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    conn.commit()
    
    cursor.execute('''
        DELETE FROM players WHERE player_name NOT IN (SELECT DISTINCT player_name FROM videos)
    ''')
    conn.commit()
    conn.close()

# --- TootScouting UI Layout ---
st.title("Scouting & Video Analysis Center - TootScouting")
st.markdown("---")

tab1, tab2 = st.tabs(["Player Showcase & Analysis", "Analyst Control Panel"])

# ----------------- Tab 1: User / Client Interface -----------------
with tab1:
    players_list = get_all_players_profiles()
    
    if players_list:
        st.subheader("Available Player Profiles:")
        num_columns = min(len(players_list), 4)
        card_cols = st.columns(num_columns) if num_columns > 0 else []
        
        if "selected_player_name" not in st.session_state:
            st.session_state.selected_player_name = players_list[0]["name"]
            
        for idx, player in enumerate(players_list):
            col_idx = idx % 4
            with card_cols[col_idx]:
                with st.container(border=True):
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
                    st.markdown(f"<p style='text-align: center; margin-bottom: 2px;'><b>Club:</b> {player['club']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; margin-bottom: 10px;'><b>Age:</b> {player['age']} Y/O</p>", unsafe_allow_html=True)
                    
                    if player["sofa_link"]:
                        st.link_button("SofaScore Profile", player["sofa_link"], use_container_width=True)
                    
                    if st.button(f"View Analysis", key=f"select_{player['name']}", use_container_width=True):
                        st.session_state.selected_player_name = player["name"]
                        st.session_state.active_filter = "Passes"
                        st.session_state.selected_video_url = None
                        st.session_state.selected_video_title = ""
                        st.rerun()

        st.markdown("---")
        
        current_names = [p["name"] for p in players_list]
        if st.session_state.selected_player_name not in current_names:
            st.session_state.selected_player_name = players_list[0]["name"]

        st.write(f"## Technical Performance Dashboard: **{st.session_state.selected_player_name}**")
        
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

        # Updated to 10 Category Buttons (Added Movement)
        cols = st.columns(10)
        categories_buttons = [
            ("Passes", "Passes"), 
            ("Shots", "Shots"),
            ("Movement", "Movement"),
            ("Dribbles", "Dribbles"), 
            ("Crosses", "Crosses"),
            ("Ground Duels", "Ground Duels"), 
            ("Aerial Duels", "Aerial Duels"), 
            ("Pressing", "Pressing"), 
            ("Corners", "Corners"),
            ("Miscontrol", "Miscontrol")
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
                st.subheader(f"Current Clip: {st.session_state.selected_video_title}")
                raw_url = st.session_state.selected_video_url
                
                if "drive.google.com" in raw_url:
                    drive_embed = process_google_drive_link(raw_url)
                    st.components.v1.iframe(drive_embed, height=520, scrolling=False)
                elif "vimeo.com" in raw_url:
                    vimeo_embed = process_vimeo_link(raw_url)
                    st.components.v1.iframe(vimeo_embed, height=520, scrolling=False)
                elif "player.cloudinary.com" in raw_url or "iframe" in raw_url:
                    st.components.v1.iframe(raw_url, height=520, scrolling=False)
                else:
                    st.video(raw_url)
                
            with list_col:
                st.subheader("Video Clips")
                for vid in current_playlist:
                    if vid["video_url"] == st.session_state.selected_video_url:
                        st.success(f"PLAYING: {vid['title']}")
                    else:
                        if st.button(f"{vid['title']}", key=f"user_vid_btn_{vid['id']}", use_container_width=True):
                            st.session_state.selected_video_url = vid["video_url"]
                            st.session_state.selected_video_title = vid["title"]
                            st.rerun()
        else:
            st.info(f"No video clips available under ({st.session_state.active_filter}) for this player yet.")
    else:
        st.info("Welcome to TootScouting. Profiles will appear here once the analyst uploads the data.")

# ----------------- Tab 2: Analyst Control Panel -----------------
with tab2:
    st.subheader("Secure Analyst Login")
    password = st.text_input("Enter password to access the upload studio:", type="password")
    
    if password == "TootScouting2026":
        st.success("Access Granted!")
        st.markdown("---")
        
        st.write("### 1. Upload Video Clips Studio")
        fast_name = st.text_input("Player Full Name (e.g., Iyad Al-Asiri):", key="fast_p_name")
        fast_image = st.text_input("Player Profile Image URL:", key="fast_p_img")
        fast_club = st.text_input("Current Club Name:", key="fast_p_club")
        fast_age = st.number_input("Player Age:", min_value=12, max_value=45, value=20, key="fast_p_age")
        fast_sofa = st.text_input("SofaScore Profile Link (Optional):", key="fast_p_sofa")
        
        with st.form("fast_video_form", clear_on_submit=True):
            v_title = st.text_input("Clip Title / Event Action (e.g., Off-ball Run 1):")
            
            # Updated Dropdown Menu with "Movement"
            v_category = st.selectbox("Assign to Technical Category:", [
                "Passes", 
                "Shots", 
                "Movement",
                "Dribbles", 
                "Crosses", 
                "Ground Duels", 
                "Aerial Duels", 
                "Pressing", 
                "Corners",
                "Miscontrol"
            ])
            
            v_url = st.text_input("Video URL (Google Drive, Vimeo, or Cloudinary):")
            
            submit_video = st.form_submit_button("Upload Clip & Keep Player Profile Locked")
            
            if submit_video:
                if fast_name and v_title and v_url:
                    add_video_smart(fast_name, fast_image, fast_club, fast_age, fast_sofa, v_title, v_category, v_url)
                    st.toast(f"Clip successfully added for {fast_name}!")
                    st.rerun()
                else:
                    st.error("Action Required: Fill all video form details.")
                    
        st.markdown("---")
        
        st.write("### 2. Manage & Delete Uploaded Video Clips")
        all_videos = get_all_videos_raw()
        
        if all_videos:
            head_cols = st.columns([1, 2, 3, 2, 2])
            head_cols[0].markdown("**ID**")
            head_cols[1].markdown("**Player Name**")
            head_cols[2].markdown("**Clip Title**")
            head_cols[3].markdown("**Category**")
            head_cols[4].markdown("**Action**")
            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
            
            for vid_id, p_name, title, cat in all_videos:
                row_cols = st.columns([1, 2, 3, 2, 2])
                row_cols[0].write(f"#{vid_id}")
                row_cols[1].write(p_name)
                row_cols[2].write(title)
                row_cols[3].write(cat)
                
                if row_cols[4].button("Delete", key=f"del_{vid_id}", type="secondary", use_container_width=True):
                    delete_video_by_id(vid_id)
                    st.toast(f"Clip #{vid_id} deleted successfully!")
                    st.rerun()
        else:
            st.info("Database is currently empty. No videos to manage.")
