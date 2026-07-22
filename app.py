import streamlit as st
import sqlite3
import re

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# Custom CSS for Green & Spacious Buttons
st.markdown("""
    <style>
    /* Styling Streamlit Buttons */
    div.stButton > button {
        white-space: nowrap !important;
        padding: 10px 18px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    /* Primary (Active) Button Styling - Emerald Green */
    div.stButton > button[kind="primary"] {
        background-color: #10B981 !important;
        color: white !important;
        border: 1px solid #10B981 !important;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3) !important;
    }
    
    /* Hover state for Primary Button */
    div.stButton > button[kind="primary"]:hover {
        background-color: #059669 !important;
        border-color: #059669 !important;
    }
    
    /* Custom Styling for Player Bio Tags */
    .bio-tag {
        background-color: #1E293B;
        color: #F8FAFC;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
        border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

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
            sofa_link TEXT,
            position TEXT,
            preferred_foot TEXT,
            country TEXT
        )
    ''')
    
    # Auto-migration columns if updating existing DB
    columns_to_add = [
        ("sofa_link", "TEXT"),
        ("position", "TEXT"),
        ("preferred_foot", "TEXT"),
        ("country", "TEXT")
    ]
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE players ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
        
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
def add_video_smart(player_name, player_image, player_club, player_age, sofa_link, position, preferred_foot, country, title, category, url):
    conn = sqlite3.connect("tootscouting_relational_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO players (player_name, player_image, player_club, player_age, sofa_link, position, preferred_foot, country)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            player_image=excluded.player_image,
            player_club=excluded.player_club,
            player_age=excluded.player_age,
            sofa_link=excluded.sofa_link,
            position=excluded.position,
            preferred_foot=excluded.preferred_foot,
            country=excluded.country
    ''', (
        player_name.strip(), 
        player_image.strip(), 
        player_club.strip(), 
        int(player_age), 
        sofa_link.strip(),
        position.strip(),
        preferred_foot.strip(),
        country.strip() if country else "International"
    ))
    
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
    cursor.execute("SELECT player_name, player_image, player_club, player_age, sofa_link, position, preferred_foot, country FROM players")
    rows = cursor.fetchall()
    conn.close()
    return [{
        "name": r[0], 
        "image": r[1], 
        "club": r[2], 
        "age": r[3], 
        "sofa_link": r[4],
        "position": r[5] if r[5] else "N/A",
        "foot": r[6] if r[6] else "N/A",
        "country": r[7] if r[7] else "International"
    } for r in rows]

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
        # Country Flags Navigation Filter
        all_countries = sorted(list(set([p["country"] for p in players_list if p["country"]])))
        
        if "selected_country" not in st.session_state:
            st.session_state.selected_country = "All"
            
        st.subheader("Select League / Country Location:")
        country_cols = st.columns(len(all_countries) + 1)
        
        # 'All Countries' Button
        if st.session_state.selected_country == "All":
            country_cols[0].button("All Locations", key="cntry_all", use_container_width=True, type="primary")
        else:
            if country_cols[0].button("All Locations", key="cntry_all", use_container_width=True):
                st.session_state.selected_country = "All"
                st.rerun()
                
        # Individual Country Flag Buttons
        for c_idx, country_name in enumerate(all_countries):
            col_target = country_cols[c_idx + 1]
            if st.session_state.selected_country == country_name:
                col_target.button(f"{country_name}", key=f"cntry_{country_name}", use_container_width=True, type="primary")
            else:
                if col_target.button(f"{country_name}", key=f"cntry_{country_name}", use_container_width=True):
                    st.session_state.selected_country = country_name
                    st.rerun()

        st.markdown("---")

        # Filter players by selected country
        if st.session_state.selected_country == "All":
            filtered_players = players_list
        else:
            filtered_players = [p for p in players_list if p["country"] == st.session_state.selected_country]

        st.subheader(f"Available Player Profiles ({st.session_state.selected_country}):")
        
        if filtered_players:
            num_columns = min(len(filtered_players), 4)
            card_cols = st.columns(num_columns) if num_columns > 0 else []
            
            if "selected_player_name" not in st.session_state or st.session_state.selected_player_name not in [p["name"] for p in filtered_players]:
                st.session_state.selected_player_name = filtered_players[0]["name"]
                
            for idx, player in enumerate(filtered_players):
                col_idx = idx % 4
                with card_cols[col_idx]:
                    with st.container(border=True):
                        player_img_url = player["image"] if player["image"] else "https://via.placeholder.com/150"
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 12px; margin-top: 5px;">
                                <img src="{player_img_url}" style="width: 120px; height: 120px; aspect-ratio: 1/1; object-fit: cover; border-radius: 50%; border: 3px solid #10B981;">
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        st.markdown(f"<h3 style='text-align: center; margin-bottom: 2px;'>{player['name']}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; margin-bottom: 4px;'><b>Club:</b> {player['club']} | <b>Age:</b> {player['age']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; margin-bottom: 6px; color: #10B981; font-weight: bold;'>Location: {player['country']}</p>", unsafe_allow_html=True)
                        
                        st.markdown(
                            f"""
                            <div style="text-align: center; margin-bottom: 12px;">
                                <span class="bio-tag">Pos: {player['position']}</span>
                                <span class="bio-tag">Foot: {player['foot']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        if player["sofa_link"]:
                            st.link_button("SofaScore Profile", player["sofa_link"], use_container_width=True)

                        if st.button("View Analysis", key=f"select_{player['name']}", use_container_width=True):
                            st.session_state.selected_player_name = player["name"]
                            st.session_state.active_filter = "Passes"
                            st.session_state.selected_video_url = None
                            st.session_state.selected_video_title = ""
                            st.rerun()

            st.markdown("---")
            
            # Retrieve selected player object
            selected_player_obj = next((p for p in filtered_players if p["name"] == st.session_state.selected_player_name), filtered_players[0])

            st.write(f"## Technical Performance Dashboard: **{selected_player_obj['name']}**")
            
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

            categories_buttons = [
                ("Passes", "Passes"), 
                ("Shots", "Shots"),
                ("Movement", "Movement"),
                ("Dribbles", "Dribbles"), 
                ("Crosses", "Crosses"),
                ("Ground Duels", "Ground Duels"), 
                ("Aerial Duels", "Aerial Duels"), 
                ("Pressing", "Pressing"), 
                ("Recoveries", "Recoveries"),
                ("Clearances", "Clearances"),
                ("Fouls Drawn", "Fouls Drawn"),
                ("Fouls Committed", "Fouls Committed"),
                ("Corners", "Corners"),
                ("Miscontrol", "Miscontrol")
            ]
            
            cols = st.columns(7)
            for idx, (label, tag) in enumerate(categories_buttons):
                col_target = cols[idx % 7]
                if st.session_state.active_filter == tag:
                    col_target.button(label, key=f"user_filter_{tag}", use_container_width=True, type="primary")
                else:
                    col_target.button(label, key=f"user_filter_{tag}", use_container_width=True, on_click=change_filter, args=(tag,))
                    
            st.markdown("---")
            
            current_playlist = get_videos_by_player_and_category(selected_player_obj["name"], st.session_state.active_filter)
            
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
            st.info(f"No player profiles available in {st.session_state.selected_country} currently.")
    else:
        st.info("Welcome to TootScouting. Profiles will appear here once the analyst uploads the data.")

# ----------------- Tab 2: Analyst Control Panel -----------------
with tab2:
    st.subheader("Secure Analyst Login")
    password = st.text_input("Enter password to access the upload studio:", type="password")
    
    if password == "TootScouting2026":
        st.success("Access Granted!")
        st.markdown("---")
        
        st.write("### 1. Upload Video Clips & Player Tactical Profile Studio")
        
        col_a, col_b = st.columns(2)
        with col_a:
            fast_name = st.text_input("Player Full Name (e.g., Iyad Al-Asiri):", key="fast_p_name")
            fast_image = st.text_input("Player Profile Image URL:", key="fast_p_img")
            fast_club = st.text_input("Current Club Name:", key="fast_p_club")
            fast_age = st.number_input("Player Age:", min_value=12, max_value=45, value=20, key="fast_p_age")
        
        with col_b:
            fast_country = st.text_input("Country / Flag (e.g., 🇸🇦 Saudi Arabia, 🇫🇮 Finland, 🇪🇬 Egypt):", key="fast_p_country")
            fast_pos = st.text_input("Primary Position (e.g., RW / AM):", key="fast_p_pos")
            fast_foot = st.selectbox("Preferred Foot:", ["Right", "Left", "Both"], key="fast_p_foot")
            fast_sofa = st.text_input("SofaScore Profile Link (Optional):", key="fast_p_sofa")

        st.markdown("---")
        
        with st.form("fast_video_form", clear_on_submit=True):
            v_title = st.text_input("Clip Title / Event Action (e.g., Ball Recovery 1):")
            
            v_category = st.selectbox("Assign to Technical Category:", [
                "Passes", 
                "Shots", 
                "Movement",
                "Dribbles", 
                "Crosses", 
                "Ground Duels", 
                "Aerial Duels", 
                "Pressing", 
                "Recoveries",
                "Clearances",
                "Fouls Drawn",
                "Fouls Committed",
                "Corners",
                "Miscontrol"
            ])
            
            v_url = st.text_input("Video URL (Google Drive, Vimeo, or Cloudinary):")
            
            submit_video = st.form_submit_button("Upload Clip & Save Player Profile")
            
            if submit_video:
                if fast_name and v_title and v_url:
                    add_video_smart(
                        fast_name, fast_image, fast_club, fast_age, fast_sofa, 
                        fast_pos, fast_foot, fast_country,
                        v_title, v_category, v_url
                    )
                    st.toast(f"Clip & Profile updated successfully for {fast_name}!")
                    st.rerun()
                else:
                    st.error("Action Required: Fill all required video form details.")
                    
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
