import streamlit as st
import re
import json
import plotly.graph_objects as go
from supabase import create_client, Client

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# Custom CSS for Emerald Green & Spacious Buttons
st.markdown("""
    <style>
    div.stButton > button {
        white-space: nowrap !important;
        padding: 10px 18px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #10B981 !important;
        color: white !important;
        border: 1px solid #10B981 !important;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3) !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        background-color: #059669 !important;
        border-color: #059669 !important;
    }
    
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

# 2. Permanent Supabase Cloud Connection via Streamlit Secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# Smart function to process Google Drive links
def process_google_drive_link(url):
    if url and "drive.google.com" in url:
        match = re.search(r'/d/([^/]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/file/d/{file_id}/preview"
    return url

# Smart function to process Vimeo URLs
def process_vimeo_link(url):
    if url and "vimeo.com" in url:
        match = re.search(r'vimeo\.com/(\d+)', url)
        if match:
            video_id = match.group(1)
            return f"https://player.vimeo.com/video/{video_id}"
    return url

# Function to plot Radar Chart
def plot_player_radar(radar_dict):
    if not radar_dict:
        categories = ['Passing', 'Dribbling', 'Pace', 'Defending', 'Physical', 'Shooting']
        values = [50, 50, 50, 50, 50, 50]
    else:
        categories = list(radar_dict.keys())
        values = list(radar_dict.values())
        
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.4)',
        line=dict(color='#10B981', width=3),
        name='Performance Profile'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#CBD5E1"),
                gridcolor="#334155"
            ),
            angularaxis=dict(
                tickfont=dict(size=14, color="#F8FAFC"),
                gridcolor="#334155"
            ),
            bgcolor="#0F172A"
        ),
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        margin=dict(l=40, r=40, t=30, b=30),
        showlegend=False
    )
    return fig

# Safe Function to add/update player and clip
def add_video_smart(player_name, player_image, player_club, player_age, sofa_link, position, preferred_foot, scouting_report, radar_data, title, category, url):
    try:
        p_name = str(player_name).strip()
        
        try:
            p_age = int(player_age)
        except (ValueError, TypeError):
            p_age = 20
            
        player_data = {
            "player_name": p_name,
            "player_image": str(player_image).strip() if player_image else "",
            "player_club": str(player_club).strip() if player_club else "",
            "player_age": p_age,
            "sofa_link": str(sofa_link).strip() if sofa_link else "",
            "position": str(position).strip() if position else "N/A",
            "preferred_foot": str(preferred_foot).strip() if preferred_foot else "Both",
            "scouting_report": str(scouting_report).strip() if scouting_report else "",
            "radar_data": radar_data
        }
        
        existing = supabase.table("players").select("player_name").eq("player_name", p_name).execute()
        
        if existing.data and len(existing.data) > 0:
            supabase.table("players").update(player_data).eq("player_name", p_name).execute()
        else:
            supabase.table("players").insert(player_data).execute()
        
        if title and url:
            video_data = {
                "player_name": p_name,
                "title": str(title).strip(),
                "category": str(category).strip(),
                "video_url": str(url).strip()
            }
            supabase.table("videos").insert(video_data).execute()
            
        return True, f"Profile and Data updated successfully for {p_name}!"
        
    except Exception as e:
        return False, f"Supabase Error: {str(e)}"

# Function to get all players
def get_all_players_profiles():
    try:
        response = supabase.table("players").select("*").execute()
        rows = response.data if response.data else []
        return [{
            "name": r.get("player_name", "Unknown"), 
            "image": r.get("player_image", ""), 
            "club": r.get("player_club", ""), 
            "age": r.get("player_age", 20), 
            "sofa_link": r.get("sofa_link", ""),
            "position": r.get("position", "N/A"),
            "foot": r.get("preferred_foot", "N/A"),
            "scouting_report": r.get("scouting_report", ""),
            "radar_data": r.get("radar_data", {})
        } for r in rows]
    except Exception:
        return []

def get_videos_by_player_and_category(player_name, category):
    try:
        response = supabase.table("videos").select("*").eq("player_name", player_name).eq("category", category).execute()
        rows = response.data if response.data else []
        return [{"id": r["id"], "title": r["title"], "video_url": r["video_url"]} for r in rows]
    except Exception:
        return []

def get_all_videos_raw():
    try:
        response = supabase.table("videos").select("*").order("id", desc=True).execute()
        return response.data if response.data else []
    except Exception:
        return []

def delete_video_by_id(video_id):
    try:
        supabase.table("videos").delete().eq("id", video_id).execute()
    except Exception:
        pass

# --- UI Layout ---
st.title("Scouting & Video Analysis Center - TootScouting")
st.markdown("---")

tab1, tab2 = st.tabs(["Player Showcase & Analysis", "Analyst Control Panel"])

# ----------------- Tab 1: Client / User Interface -----------------
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
        
        selected_player_obj = next((p for p in players_list if p["name"] == st.session_state.selected_player_name), players_list[0])

        st.write(f"## Technical Performance Dashboard: **{selected_player_obj['name']}**")
        
        # Inner Tabs for Video Clips vs Scouting Report & Radar
        p_tab1, p_tab2, p_tab3 = st.tabs(["🎥 Video Analysis Clips", "📊 Performance Radar Chart", "📝 Scouting Report"])
        
        with p_tab1:
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
                ("Passes", "Passes"), ("Shots", "Shots"), ("Movement", "Movement"),
                ("Dribbles", "Dribbles"), ("Crosses", "Crosses"), ("Ground Duels", "Ground Duels"),
                ("Aerial Duels", "Aerial Duels"), ("Pressing", "Pressing"), ("Recoveries", "Recoveries"),
                ("Clearances", "Clearances"), ("Fouls Drawn", "Fouls Drawn"), ("Fouls Committed", "Fouls Committed"),
                ("Corners", "Corners"), ("Miscontrol", "Miscontrol")
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
                    elif raw_url.endswith((".mp4", ".webm", ".ogg", ".mov")):
                        st.video(raw_url)
                    else:
                        st.components.v1.iframe(raw_url, height=520, scrolling=False)
                    
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

        with p_tab2:
            st.subheader(f"Technical Attributes Profile - {selected_player_obj['name']}")
            radar_fig = plot_player_radar(selected_player_obj.get("radar_data"))
            st.plotly_chart(radar_fig, use_container_width=True)

        with p_tab3:
            st.subheader(f"Detailed Scouting Report & Executive Summary")
            report_text = selected_player_obj.get("scouting_report")
            if report_text:
                st.markdown(report_text)
            else:
                st.info("No detailed scouting report added for this player yet.")

    else:
        st.info("Welcome to TootScouting. Profiles will appear here once the analyst uploads the data.")

# ----------------- Tab 2: Analyst Control Panel -----------------
with tab2:
    st.subheader("Secure Analyst Login")
    password = st.text_input("Enter password to access the upload studio:", type="password")
    
    if password == "TootScouting2026":
        st.success("Access Granted!")
        st.markdown("---")
        
        st.write("### 1. Player Profile & Scouting Report Management Studio")
        
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

        st.markdown("#### 📊 Radar Metrics Rating (0 - 100)")
        r_cols1 = st.columns(3)
        r_cols2 = st.columns(3)
        
        val_pass = r_cols1[0].slider("Passing & Vision", 0, 100, 70)
        val_dribble = r_cols1[1].slider("Dribbling & Ball Control", 0, 100, 75)
        val_pace = r_cols1[2].slider("Pace & Acceleration", 0, 100, 80)
        
        val_def = r_cols2[0].slider("Defending & Workrate", 0, 100, 60)
        val_phys = r_cols2[1].slider("Physical & Duels", 0, 100, 65)
        val_shoot = r_cols2[2].slider("Shooting & Finishing", 0, 100, 70)
        
        radar_json_data = {
            "Passing": val_pass,
            "Dribbling": val_dribble,
            "Pace": val_pace,
            "Defending": val_def,
            "Physical": val_phys,
            "Shooting": val_shoot
        }

        st.markdown("#### 📝 Scouting Report Text")
        scout_report_input = st.text_area("Write full tactical assessment, strengths, weaknesses, and potential:", height=150)

        st.markdown("---")
        st.write("### 2. Video Clip Details (Optional when updating report only)")
        
        v_title = st.text_input("Clip Title / Event Action (e.g., Ball Recovery 1):")
        v_category = st.selectbox("Assign to Technical Category:", [
            "Passes", "Shots", "Movement", "Dribbles", "Crosses", "Ground Duels",
            "Aerial Duels", "Pressing", "Recoveries", "Clearances", "Fouls Drawn",
            "Fouls Committed", "Corners", "Miscontrol"
        ])
        v_url = st.text_input("Video URL (Google Drive, Vimeo, or Cloudinary):")
        
        if st.button("Save Profile, Radar & Report to Cloud", type="primary", use_container_width=True):
            if fast_name:
                success, msg = add_video_smart(
                    fast_name, fast_image, fast_club, fast_age, fast_sofa, 
                    fast_pos, fast_foot, scout_report_input, radar_json_data,
                    v_title, v_category, v_url
                )
                if success:
                    st.toast(msg)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("Action Required: Please enter Player Full Name.")
                    
        st.markdown("---")
        
        st.write("### 3. Manage & Delete Uploaded Video Clips")
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
