import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime, date

# --- 1. SUPABASE-YHTEYS ---
# Käytetään aiemmin annettua URL-osoitetta ja avainta
SUPABASE_URL = "https://zpyvpqnomoufadcnxqqb.supabase.co"
SUPABASE_KEY = "sb_publishable_u9AzUI0N_A80-dVedNPzCg_IT7bkxH4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. MOBIILIOPTIMOITU TYYLI (PIMARA BRAND) ---
st.set_page_config(page_title="PIMARA Kalustohallinta", layout="wide")

def apply_pro_style():
    st.markdown("""
        <style>
        :root { --p-yellow: #ffcc00; --p-dark: #1a1a1a; --p-text: #000000; }
        .stApp { background-color: #ffffff; }
        
        /* Sivupalkki keltaisilla napeilla */
        [data-testid="stSidebar"] { background-color: var(--p-dark) !important; }
        div.stSidebar [data-testid="stVerticalBlock"] button {
            background-color: var(--p-yellow) !important;
            color: var(--p-text) !important;
            border: none !important;
            border-radius: 0px !important;
            font-weight: 800 !important;
            text-transform: uppercase;
            padding: 15px !important;
            margin-bottom: 8px !important;
            width: 100% !important;
            transition: 0.3s;
        }
        div.stSidebar [data-testid="stVerticalBlock"] button:hover {
            background-color: #e6b800 !important;
            transform: scale(1.02);
        }

        /* Mobiilikortit */
        .mobile-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 12px;
            background-color: #fcfcfc;
            border-left: 8px solid var(--p-yellow);
        }

        /* Otsikot */
        h1, h2, h3 { color: var(--p-dark); font-weight: 800; text-transform: uppercase; border-left: 10px solid var(--p-yellow); padding-left: 15px; }

        /* Responsiivinen Kalustokortin taulukko */
        .tech-table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
        .tech-table td { border: 1px solid #ccc; padding: 10px; font-size: 0.9rem; }
        .tech-label { background-color: #f0f0f0; font-weight: bold; width: 35%; }

        @media (max-width: 600px) {
            .tech-table tr { display: flex; flex-direction: column; border-bottom: 2px solid #ddd; }
            .tech-table td { width: 100% !important; border: none; padding: 5px 10px; }
            .tech-label { background-color: #eee; padding-top: 10px; }
            .logo-main { font-size: 1.5rem !important; }
            .brand-header { padding: 1rem !important; margin: -6rem -2rem 1rem -2rem !important; }
        }

        .brand-header { background-color: var(--p-dark); padding: 2rem; border-bottom: 6px solid var(--p-yellow); margin: -6rem -5rem 2rem -5rem; display: flex; align-items: center; }
        .logo-main { color: var(--p-yellow); font-size: 2rem; font-weight: 900; }
        .sidebar-brand { padding: 30px 0; text-align: center; color: var(--p-yellow); font-size: 1.8rem; font-weight: 900; }
        </style>
    """, unsafe_allow_html=True)

apply_pro_style()

# --- 3. NAVIGAATION JA STATEN HALLINTA ---
if 'sivu' not in st.session_state: st.session_state.sivu = "TYÖPÖYTÄ"
if 'kortti_id' not in st.session_state: st.session_state.kortti_id = None

def vaihda_sivu(nimi):
    st.session_state.sivu = nimi
    st.session_state.kortti_id = None

# --- 4. APUFUNKTIOT (SUPABASE-RAKENTEELLE) ---
def get_konetyypit():
    res = supabase.table("konetyypit").select("nimi").execute()
    return [r['nimi'] for r in res.data] if res.data else []

def get_urakat():
    res = supabase.table("urakat").select("id, nimi").execute()
    d = {0: "Varasto / Ei määritelty"}
    for r in res.data: d[r['id']] = r['nimi']
    return d

def get_koneiden_nimet():
    res = supabase.table("koneet").select("id, nimi").execute()
    d = {0: "Ei kytketty"}
    for r in res.data: d[r['id']] = r['nimi']
    return d

# --- 5. SIVUPALKKI ---
with st.sidebar:
    st.markdown('<div class="sidebar-brand">PIMARA</div>', unsafe_allow_html=True)
    if st.button("TYÖPÖYTÄ"): vaihda_sivu("TYÖPÖYTÄ")
    if st.button("KONEREKISTERI"): vaihda_sivu("KONEET")
    if st.button("URAKAT JA TYÖMAAT"): vaihda_sivu("URAKAT")
    if st.button("LISÄLAITTEET"): vaihda_sivu("LISÄLAITTEET")
    if st.button("HUOLTOHISTORIA"): vaihda_sivu("HISTORIA")
    if st.button("VUOSIKELLO"): vaihda_sivu("VUOSIKELLO")

st.markdown('<div class="brand-header"><span class="logo-main">PIMARA</span><span style="color:white; margin-left:15px; font-weight:200;">KALUSTONHALLINTA</span></div>', unsafe_allow_html=True)

# --- 6. KALUSTOKORTTI (SUPABASE-YHTEENSOPIVA) ---
def render_kortti(k_id):
    res = supabase.table("koneet").select("*").eq("id", k_id).execute()
    if not res.data: return
    k = res.data[0]
    
    st.markdown(f'<div style="background:#1a1a1a; color:#ffcc00; padding:15px; font-weight:900;">AJONEUVOKORTTI | PIMARA</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:#ffcc00; color:black; padding:15px; font-size:1.8rem; font-weight:900;">{k["rekisteri"] if k["rekisteri"] else "EI REKISTERIÄ"}</div>', unsafe_allow_html=True)
    
    # Kuvat Supabase Storage linkistä (olettaen että linkki on tietokannassa)
    if k.get('kuva_url'):
        st.image(k['kuva_url'], use_container_width=True)

    st.markdown(f"""
    <table class="tech-table">
        <tr><td class="tech-label">Merkki/Malli</td><td>{k.get('merkki', '')} {k.get('malli', '')}</td></tr>
        <tr><td class="tech-label">S/N</td><td>{k.get('sarjanumero', '')}</td></tr>
        <tr><td class="tech-label">Vuosimalli</td><td>{k.get('vuosimalli', '')}</td></tr>
        <tr><td class="tech-label">Teho / Kone</td><td>{k.get('teho', '')} kW / {k.get('moottori', '')}</td></tr>
        <tr><td class="tech-label">Katsastus</td><td>{k.get('katsastus_pvm', '')}</td></tr>
    </table>
    """, unsafe_allow_html=True)

    st.subheader("Kytketyt lisälaitteet")
    l_res = supabase.table("lisalaitteet").select("nimi, tyyppi").eq("kone_id", k_id).execute()
    if l_res.data:
        st.dataframe(pd.DataFrame(l_res.data), use_container_width=True)
    
    if st.button("SULJE KORTTI"):
        st.session_state.kortti_id = None
        st.rerun()

# --- 7. SIVUJEN LOGIIKKA ---

# SIVU: KONEREKISTERI
if st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        render_kortti(st.session_state.kortti_id)
    else:
        st.header("Konerekisteri")
        tyypit = get_konetyypit()
        urakat = get_urakat()
        
        with st.expander("LISÄÄ UUSI KONE"):
            with st.form("k_f", clear_on_submit=True):
                kn = st.text_input("Tunnus (esim. JKX-577)")
                kt = st.selectbox("Tyyppi", tyypit)
                kme = st.text_input("Merkki")
                kma = st.text_input("Malli")
                kre = st.text_input("Rekisterinumero")
                kkat = st.text_input("Katsastus pvm")
                kur = st.selectbox("Sijainti", list(urakat.keys()), format_func=lambda x: urakat[x])
                
                if st.form_submit_button("TALLENNA KONE"):
                    data = {
                        "nimi": kn, "tyyppi": kt, "merkki": kme, "malli": kma, 
                        "rekisteri": kre, "katsastus_pvm": kkat, "urakka_id": kur, "tila": "Käytössä"
                    }
                    supabase.table("koneet").insert(data).execute()
                    st.rerun()

        # Kalustolistaus korteilla (Mobiiliystävällinen)
        res = supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").execute()
        for r in res.data:
            st.markdown(f"""<div class="mobile-card">
                <b>{r['nimi']}</b> ({r['tyyppi']})<br>
                Rekisteri: {r['rekisteri']}
            </div>""", unsafe_allow_html=True)
            if st.button("AVAA KALUSTOKORTTI", key=f"btn_{r['id']}"):
                st.session_state.kortti_id = r['id']
                st.rerun()

# SIVU: TYÖPÖYTÄ
elif st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard")
    k_res = supabase.table("koneet").select("id", count="exact").execute()
    l_res = supabase.table("lisalaitteet").select("id", count="exact").execute()
    
    c1, c2 = st.columns(2)
    c1.metric("Koneet yhteensä", k_res.count if k_res.count else 0)
    c2.metric("Laitteet yhteensä", l_res.count if l_res.count else 0)
    
    st.subheader("Muistutukset")
    m_res = supabase.table("aikataulu").select("erapaiva, tyyppi").eq("suoritettu", False).limit(5).execute()
    if m_res.data:
        st.table(pd.DataFrame(m_res.data))

# SIVU: URAKAT
elif st.session_state.sivu == "URAKAT":
    st.header("Urakat ja Työmaat")
    with st.expander("LISÄÄ UUSI URAKKA"):
        with st.form("u_f"):
            un = st.text_input("Urakan nimi")
            uo = st.text_input("Sijainti")
            if st.form_submit_button("TALLENNA"):
                supabase.table("urakat").insert({"nimi": un, "yhteystiedot": uo}).execute()
                st.rerun()
    
    u_res = supabase.table("urakat").select("*").execute()
    for r in u_res.data:
        st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b><br>{r["yhteystiedot"]}</div>', unsafe_allow_html=True)

# SIVU: LISÄLAITTEET
elif st.session_state.sivu == "LISÄLAITTEET":
    st.header("Lisälaiterekisteri")
    k_opts = get_koneiden_nimet()
    with st.expander("LISÄÄ LAITE"):
        with st.form("l_f"):
            ln = st.text_input("Laitteen nimi")
            lko = st.selectbox("Kytke koneeseen", list(k_opts.keys()), format_func=lambda x: k_opts[x])
            if st.form_submit_button("TALLENNA"):
                supabase.table("lisalaitteet").insert({"nimi": ln, "kone_id": lko}).execute()
                st.rerun()
    
    l_res = supabase.table("lisalaitteet").select("nimi, kone_id").execute()
    for r in l_res.data:
        st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b><br>Kytketty: {k_opts.get(r["kone_id"])}</div>', unsafe_allow_html=True)

# SIVU: HISTORIA
elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    h_res = supabase.table("huollot").select("pvm, kuvaus, kone_id").order("pvm", desc=True).execute()
    k_nimet = get_koneiden_nimet()
    for r in h_res.data:
        st.markdown(f'<div class="mobile-card"><b>{k_nimet.get(r["kone_id"])}</b> - {r["pvm"]}<br>{r["kuvaus"]}</div>', unsafe_allow_html=True)

# SIVU: VUOSIKELLO
elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello ja suunnittelu")
    k_opts = get_koneiden_nimet()
    with st.expander("UUSI TAPAHTUMA"):
        with st.form("v_f"):
            vk = st.selectbox("Kone", list(k_opts.keys()), format_func=lambda x: k_opts[x])
            vp = st.date_input("Päivä")
            vt = st.text_input("Mitä tehdään?")
            if st.form_submit_button("LISÄÄ"):
                supabase.table("aikataulu").insert({"kone_id": vk, "erapaiva": vp.isoformat(), "tyyppi": vt, "suoritettu": False}).execute()
                st.rerun()
    
    v_res = supabase.table("aikataulu").select("id, erapaiva, tyyppi, kone_id").eq("suoritettu", False).execute()
    for r in v_res.data:
        with st.container():
            st.markdown(f'<div class="mobile-card"><b>{k_opts.get(r["kone_id"])}</b>: {r["erapaiva"]}<br>{r["tyyppi"]}</div>', unsafe_allow_html=True)
            if st.button("KUITTAA TEHDYKSI", key=f"v_{r['id']}"):
                # Merkitse tehdyksi ja siirrä historiaan
                supabase.table("aikataulu").update({"suoritettu": True}).eq("id", r['id']).execute()
                supabase.table("huollot").insert({"kone_id": r['kone_id'], "pvm": date.today().isoformat(), "kuvaus": f"Kuitattu: {r['tyyppi']}"}).execute()
                st.rerun()