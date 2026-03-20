import streamlit as st
from supabase import create_client, Client

# Supabase-yhteyden tiedot
SUPABASE_URL = "https://zpyvpqnomoufadcnxqqb.supabase.co"
SUPABASE_KEY = "sb_publishable_u9AzUI0N_A80-dVedNPzCg_IT7bkxH4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "pimara-kuvat"

def apply_pro_style():
    st.markdown("""
        <style>
        :root { --p-yellow: #ffcc00; --p-dark: #1a1a1a; --p-text: #000000; }
        .stApp { background-color: #ffffff; }
        [data-testid="stSidebar"] { background-color: var(--p-dark) !important; min-width: 280px !important; }
        div.stSidebar [data-testid="stVerticalBlock"] button {
            background-color: var(--p-yellow) !important;
            color: var(--p-text) !important;
            border: none !important;
            border-radius: 0px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            padding: 15px !important;
            margin-bottom: 10px !important;
            width: 100% !important;
        }
        .mobile-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 12px; background-color: #fcfcfc; border-left: 8px solid var(--p-yellow); }
        .alert-card-warning { padding: 15px; background-color: #fff3cd; border-left: 10px solid #ffc107; margin-bottom: 10px; color: #856404; font-weight: bold; }
        .alert-card-danger { padding: 15px; background-color: #f8d7da; border-left: 10px solid #dc3545; margin-bottom: 10px; color: #721c24; font-weight: bold; }
        h1, h2, h3 { color: var(--p-dark); font-weight: 800; text-transform: uppercase; border-left: 15px solid var(--p-yellow); padding-left: 15px; }
        .brand-header { background-color: var(--p-dark); padding: 2rem; border-bottom: 6px solid var(--p-yellow); margin: -6rem -5rem 2rem -5rem; display: flex; align-items: center; }
        .logo-main { color: var(--p-yellow); font-size: 2.2rem; font-weight: 900; }
        .tech-table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
        .tech-table td { border: 1px solid #ccc; padding: 12px; font-size: 0.95rem; }
        .tech-label { background-color: #f0f0f0; font-weight: bold; width: 35%; color: #333; }
        </style>
    """, unsafe_allow_html=True)