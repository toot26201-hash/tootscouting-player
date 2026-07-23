import streamlit as st
import re
from supabase import create_client, Client

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# Custom CSS for Emerald Green & Spacious Buttons
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

# 2. Permanent Supabase Cloud Database Connection
SUPABASE_URL = "https://tpldhmjbbhpzzlctrwcs.supabase.co"
SUPABASE_KEY = "sb_publishable_Chs3SrP6SCxQDWPrEG7k_g_AN8NgdTq"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

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

# Safe Function to add video & player profile into Supabase Cloud
def add_video_smart(player_name, player_image, player_club, player_age, sofa_link, position, preferred_foot, title, category, url):
    p_name = player_name.strip()
    
    player_data = {
        "player_name": p_name,
        "player_image": player_image.strip(),
        "player_club": player_club.strip(),
        "player_age": int(player_age),
        "sofa_link": sofa_link.strip(),
        "position": position.strip(),
        "preferred_foot": preferred_foot.strip()
    }
    
    # Check if player exists first
    existing = supabase.table("players").select("player_name").eq("player_name", p_name).execute()
    
    if existing.data:
        supabase.table("players").update(player_data).eq("player_name", p_name).execute()
    else:
        supabase.table("players").insert(player_data).execute()
    
    # Insert Video Clip Record
    video_data = {
        "player_name": p_name,
        "title": title.strip(),
        "category": category.strip(),
        "video_url": url.strip()
    }
    supabase.table("videos").insert(video_data).execute()

# Function to get all players profiles from Supabase Cloud
def get_all_players_profiles():
    try:
        response = supabase.table("players").select("*").execute()
        rows = response.data
        return [{
            "name": r["player_name"], 
            "image": r["player_image"], 
            "club": r["player_club"], 
            "age": r["player_age"], 
            "sofa_link": r["sofa_link"],
            "position": r.get("position", "N/A"),
            "foot": r.get("preferred_foot", "N/A")
        } for r in rows]
    except Exception:
        return []

# Function to get videos by player and category from Supabase
def get_videos_by_player_and_category(player_name, category):
    try:
        response = supabase.table("videos").select("*").eq("player_name", player_name).eq("category", category).execute()
        rows = response.data
        return [{"id": r["id"], "title": r["title"], "video_url": r["video_url"]} for r in rows]
    except Exception:
        return []

# Function to get ALL videos for management deletion
def get_all_videos_raw():
    try:
        response = supabase.table("videos").select("*").order("id", desc=True).execute()
        return response.data
    except Exception:
        return []

# Function to delete a video by ID from Supabase
def delete_video_by_id(video_id):
    supabase.table("videos").delete().eq("id", video_id).execute()

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
        
        if "selected_player_name" not in st.session_state or st.session_state.selected_player_name not in [p["name"] for p in players_list]:
            st.session_state.selected_player_name = players_list[0]["name"]
            
        for idx, player in enumerate(players_list):
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
                    st.markdown(f"<p style='text-align: center; margin-bottom: 6px;'><b>Club:</b> {player['club']} | <b>Age:</b> {player['age']} Y/O</p>", unsafe_allow_html=True)
                    
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
        selected_player_obj = next((p for p in players_list if p["name"] == st.session_state.selected_player_name), players_list[0])

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
            
            submit_video = st.form_submit_button("Upload Clip & Save Player Profile to Cloud")
            
            if submit_video:
                if fast_name and v_title and v_url:
                    add_video_smart(
                        fast_name, fast_image, fast_club, fast_age, fast_sofa, 
                        fast_pos, fast_foot,
                        v_title, v_category, v_url
                    )
                    st.toast(f"Clip & Profile permanently saved to Cloud for {fast_name}!")
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
            
            for vid in all_videos:
                vid_id = vid["id"]
                p_name = vid["player_name"]
                title = vid["title"]
                cat = vid["category"]
                
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
            st.info("Cloud Database is currently empty. No videos stored.")
