import streamlit as st
import re
from supabase import create_client, Client

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="TootScouting Media Center")

# Custom CSS for Neon Green Glow Effect on Hover (Cards & ALL Buttons)
st.markdown("""
    <style>
    /* UNIVERSAL BUTTON STYLING WITH NEON GREEN GLOW ON HOVER */
    div.stButton > button, div.stFormSubmitButton > button, a[data-testid="stHeaderNavigateButton"], a.stLinkButton {
        white-space: nowrap !important;
        padding: 10px 18px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.35s ease-in-out !important;
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        text-decoration: none !important;
    }
    
    /* Active / Primary Button Style */
    div.stButton > button[kind="primary"] {
        background-color: #10B981 !important;
        color: white !important;
        border: 1px solid #10B981 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4) !important;
    }
    
    /* ALL BUTTONS HOVER EFFECT (GREEN GLOW) */
    div.stButton > button:hover, div.stFormSubmitButton > button:hover, a.stLinkButton:hover {
        border-color: #10B981 !important;
        color: #10B981 !important;
        box-shadow: 0 0 18px rgba(16, 185, 129, 0.75), 0 0 5px rgba(16, 185, 129, 0.9) !important;
        transform: translateY(-2px) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        color: white !important;
        background-color: #059669 !important;
    }
    
    /* Player Bio Tags */
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

    /* GLOWING CARD STYLING FOR PLAYERS */
    .glowing-card {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 18px;
        transition: all 0.35s ease-in-out;
        margin-bottom: 15px;
    }

    .glowing-card:hover {
        border-color: #10B981 !important;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.7), 0 0 6px rgba(16, 185, 129, 0.9) !important;
        transform: translateY(-5px);
    }

    /* COMPACT, SMALL & PERFECTLY SIZED STAFF CARD */
    .staff-card-mini {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 15px;
        max-width: 260px;
        margin: 10px auto;
        text-align: center;
        transition: all 0.35s ease-in-out;
    }

    .staff-card-mini:hover {
        border-color: #10B981 !important;
        box-shadow: 0 0 18px rgba(16, 185, 129, 0.7) !important;
        transform: translateY(-4px);
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

# Smart function to process Google Drive direct Image URLs
def process_google_drive_image(url):
    if url and "drive.google.com" in url:
        match = re.search(r'/d/([^/]+)', url) or re.search(r'id=([^&]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://lh3.googleusercontent.com/d/{file_id}"
    return url

# Helpers for embeds
def process_google_drive_embed(url):
    if url and "drive.google.com" in url:
        match = re.search(r'/d/([^/]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/file/d/{file_id}/preview"
    return url

def process_vimeo_link(url):
    if url and "vimeo.com" in url:
        match = re.search(r'vimeo\.com/(\d+)', url)
        if match:
            video_id = match.group(1)
            return f"https://player.vimeo.com/video/{video_id}"
    return url

# Comprehensive Tactical Categories List
TACTICAL_CATEGORIES = [
    "Passes", 
    "Shots", 
    "Movement", 
    "Dribbles", 
    "1v1", 
    "Ball Carrying", 
    "Ball Retention", 
    "Crosses", 
    "Ground Duels", 
    "Aerial Duels", 
    "Tackles", 
    "Interceptions", 
    "Pressing", 
    "Recoveries", 
    "Clearances", 
    "Throw-ins", 
    "Fouls Drawn", 
    "Fouls Committed", 
    "Corners", 
    "Miscontrol"
]

# Database Operations
def add_video_smart(player_name, player_image, player_club, player_age, sofa_link, position, preferred_foot, radar_image, pdf_report_url, title, category, url):
    try:
        p_name = str(player_name).strip()
        try:
            p_age = int(player_age)
        except (ValueError, TypeError):
            p_age = 20
            
        cleaned_image = process_google_drive_image(player_image.strip()) if player_image else ""
        cleaned_radar = process_google_drive_image(radar_image.strip()) if radar_image else ""
        
        player_data = {
            "player_name": p_name,
            "player_image": cleaned_image,
            "player_club": str(player_club).strip() if player_club else "",
            "player_age": p_age,
            "sofa_link": str(sofa_link).strip() if sofa_link else "",
            "position": str(position).strip() if position else "N/A",
            "preferred_foot": str(preferred_foot).strip() if preferred_foot else "Both",
            "radar_image": cleaned_radar,
            "pdf_report_url": str(pdf_report_url).strip() if pdf_report_url else ""
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
            "radar_image": r.get("radar_image", ""),
            "pdf_report_url": r.get("pdf_report_url", "")
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

# Staff Database Operations
def add_staff_member(name, role, email, phone, image_url, bio):
    try:
        cleaned_staff_img = process_google_drive_image(image_url.strip()) if image_url else ""
        staff_data = {
            "name": str(name).strip(),
            "role": str(role).strip(),
            "email": str(email).strip() if email else "",
            "phone": str(phone).strip() if phone else "",
            "image_url": cleaned_staff_img,
            "bio": str(bio).strip() if bio else ""
        }
        supabase.table("staff").insert(staff_data).execute()
        return True, f"Staff member '{name}' added successfully!"
    except Exception as e:
        return False, f"Error adding staff: {str(e)}"

def get_all_staff():
    try:
        response = supabase.table("staff").select("*").order("id", desc=True).execute()
        return response.data if response.data else []
    except Exception:
        return []

def delete_staff_by_id(staff_id):
    try:
        supabase.table("staff").delete().eq("id", staff_id).execute()
    except Exception:
        pass

# --- UI Layout ---
st.title("Scouting & Video Analysis Center - TootScouting")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Player Showcase & Analysis", "👥 Our Staff & Team", "Analyst Control Panel"])

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
                player_img_url = player["image"] if player["image"] else "https://via.placeholder.com/150"
                
                st.markdown(
                    f"""
                    <div class="glowing-card">
                        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 12px; margin-top: 5px;">
                            <img src="{player_img_url}" style="width: 120px; height: 120px; aspect-ratio: 1/1; object-fit: cover; border-radius: 50%; border: 3px solid #10B981;">
                        </div>
                        <h3 style="text-align: center; margin-bottom: 2px; color: #F8FAFC;">{player['name']}</h3>
                        <p style="text-align: center; margin-bottom: 6px; color: #CBD5E1;"><b>Club:</b> {player['club']} | <b>Age:</b> {player['age']} Y/O</p>
                        <div style="text-align: center; margin-bottom: 12px;">
                            <span class="bio-tag">Pos: {player['position']}</span>
                            <span class="bio-tag">Foot: {player['foot']}</span>
                        </div>
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
        
        p_tab1, p_tab2, p_tab3 = st.tabs(["🎥 Video Analysis Clips", "📊 Performance Radar Chart", "📄 Scouting PDF Report"])
        
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

            cols = st.columns(6)
            for idx, cat_name in enumerate(TACTICAL_CATEGORIES):
                col_target = cols[idx % 6]
                if st.session_state.active_filter == cat_name:
                    col_target.button(cat_name, key=f"user_filter_{cat_name}", use_container_width=True, type="primary")
                else:
                    col_target.button(cat_name, key=f"user_filter_{cat_name}", use_container_width=True, on_click=change_filter, args=(cat_name,))
                    
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
                        drive_embed = process_google_drive_embed(raw_url)
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
            st.subheader(f"Radar Chart Profile - {selected_player_obj['name']}")
            radar_img = selected_player_obj.get("radar_image")
            if radar_img:
                st.image(radar_img, use_container_width=True, caption=f"Performance Radar for {selected_player_obj['name']}")
            else:
                st.info("No Radar Chart image uploaded for this player yet.")

        with p_tab3:
            st.subheader(f"Full Scouting PDF Report")
            pdf_url = selected_player_obj.get("pdf_report_url")
            if pdf_url:
                pdf_embed = process_google_drive_embed(pdf_url)
                st.components.v1.iframe(pdf_embed, height=750, scrolling=True)
                st.link_button("Download / Open Full PDF in New Tab", pdf_url, use_container_width=True)
            else:
                st.info("No PDF Scouting Report uploaded for this player yet.")

    else:
        st.info("Welcome to TootScouting. Profiles will appear here once the analyst uploads the data.")

# ----------------- Tab 2: Staff Showcase (Clean, Small & Fixed) -----------------
with tab2:
    st.subheader("TootScouting Professional Technical Staff & Analysts")
    st.markdown("---")
    
    staff_members = get_all_staff()
    if staff_members:
        # 4 Cards per row layout
        cols = st.columns(4)
        
        for idx, member in enumerate(staff_members):
            col_target = cols[idx % 4]
            with col_target:
                img = member.get("image_url") if member.get("image_url") else "https://via.placeholder.com/150"
                
                # HTML template for small card with white text
                email_html = f'<p style="margin: 3px 0; font-size: 11px; color: #CBD5E1;">📧 {member["email"]}</p>' if member.get('email') else ''
                phone_html = f'<p style="margin: 3px 0; font-size: 11px; color: #CBD5E1;">📞 {member["phone"]}</p>' if member.get('phone') else ''
                bio_html = f'<p style="font-style: italic; font-size: 12px; margin: 6px 0; color: #94A3B8;">{member["bio"]}</p>' if member.get('bio') else ''

                st.markdown(
                    f"""
                    <div class="staff-card-mini">
                        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                            <img src="{img}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2.5px solid #10B981;">
                        </div>
                        <h4 style="margin: 0; font-size: 15px; color: #F8FAFC; font-weight: 700;">{member['name']}</h4>
                        <p style="color: #10B981; font-weight: 600; font-size: 13px; margin: 4px 0 8px 0;">{member['role']}</p>
                        {bio_html}
                        {(email_html or phone_html) and '<hr style="border-color: #1E293B; margin: 8px 0;">'}
                        {email_html}
                        {phone_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No staff members added yet. Add staff details from the Analyst Control Panel.")

# ----------------- Tab 3: Analyst Control Panel -----------------
with tab3:
    st.subheader("Secure Analyst Login")
    password = st.text_input("Enter password to access the upload studio:", type="password")
    
    if password == "TootScouting2026":
        st.success("Access Granted!")
        st.markdown("---")
        
        # Section 1: Player Profile Management
        st.write("### 1. Player Profile, Radar & PDF Report Management Studio")
        
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
        st.write("### 2. Radar Image & PDF Scouting Report Links")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            radar_img_input = st.text_input("Radar Chart Image Link (URL or Drive Image):")
        with col_r2:
            pdf_report_input = st.text_input("PDF Scouting Report Link (Google Drive / Cloud Link):")

        st.markdown("---")
        st.write("### 3. Video Clip Details (Optional when updating report only)")
        
        v_title = st.text_input("Clip Title / Event Action (e.g., Ball Recovery 1):")
        v_category = st.selectbox("Assign to Technical Category:", TACTICAL_CATEGORIES)
        v_url = st.text_input("Video URL (Google Drive, Vimeo, or Cloudinary):")
        
        if st.button("Save Profile, Radar & PDF Report to Cloud", type="primary", use_container_width=True):
            if fast_name:
                success, msg = add_video_smart(
                    fast_name, fast_image, fast_club, fast_age, fast_sofa, 
                    fast_pos, fast_foot, radar_img_input, pdf_report_input,
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
        
        # Section 2: Manage Staff
        st.write("### 4. Manage Staff Team & Analysts")
        
        with st.form("add_staff_form", clear_on_submit=True):
            st.markdown("#### Add New Staff Member")
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                s_name = st.text_input("Staff Full Name:")
                s_role = st.text_input("Role / Job Title (e.g., Head Scouting Analyst):")
                s_img = st.text_input("Profile Image URL:")
            with s_col2:
                s_email = st.text_input("Email Address:")
                s_phone = st.text_input("Phone Number / WhatsApp:")
            
            s_bio = st.text_area("Brief Bio / Specialization Area:")
            
            submit_staff = st.form_submit_button("Add Staff Member to Team")
            
            if submit_staff:
                if s_name and s_role:
                    ok, msg = add_staff_member(s_name, s_role, s_email, s_phone, s_img, s_bio)
                    if ok:
                        st.toast(msg)
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Please fill Name and Role fields.")
        
        all_staff = get_all_staff()
        if all_staff:
            st.markdown("#### Existing Staff Members")
            for m in all_staff:
                st_cols = st.columns([1, 2, 2, 2, 1])
                st_cols[0].write(f"#{m['id']}")
                st_cols[1].write(f"**{m['name']}**")
                st_cols[2].write(m['role'])
                st_cols[3].write(m.get('email', 'N/A'))
                if st_cols[4].button("Delete", key=f"del_staff_{m['id']}", type="secondary"):
                    delete_staff_by_id(m['id'])
                    st.toast(f"Deleted {m['name']}")
                    st.rerun()

        st.markdown("---")
        
        # Section 3: Manage Videos
        st.write("### 5. Manage & Delete Uploaded Video Clips")
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
                
                if row_cols[4].button("Delete", key=f"del_vid_{vid_id}", type="secondary", use_container_width=True):
                    delete_video_by_id(vid_id)
                    st.toast(f"Clip #{vid_id} deleted successfully!")
                    st.rerun()
        else:
            st.info("Cloud Database is currently empty. No videos stored.")
