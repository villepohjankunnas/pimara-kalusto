import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime, date, timedelta

# --- 1. SUPABASE-ASETUKSET ---
URL = "https://zpyvpqnomoufadcnxqqb.supabase.co"
KEY = "sb_publishable_u9AzUI0N_A80-dVedNPzCg_IT7bkxH4"
supabase: Client = create_client(URL, KEY)
BUCKET_NAME = "pimara-kuvat"

# --- 2. TYYLIT (PIMARA INDUSTRIAL & Kirjautuminen) ---
st.set_page_config(page_title="PIMARA Kalustonhallinta Pro", layout="wide")

def apply_pro_style():
    st.markdown("""
        <style>
        :root { --p-yellow: #ffcc00; --p-dark: #1a1a1a; --p-text: #000000; }
        .stApp { background-color: #ffffff; }
        
        /* Sivupalkki keltaisilla painonapeilla */
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
            transition: 0.3s;
        }
        div.stSidebar [data-testid="stVerticalBlock"] button:hover { background-color: #e6b800 !important; transform: scale(1.02); }
        
        /* Mobiilikortit */
        .mobile-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 12px; background-color: #fcfcfc; border-left: 8px solid var(--p-yellow); }
        .alert-card-warning { padding: 15px; background-color: #fff3cd; border-left: 10px solid #ffc107; margin-bottom: 10px; color: #856404; font-weight: bold; }
        .alert-card-danger { padding: 15px; background-color: #f8d7da; border-left: 10px solid #dc3545; margin-bottom: 10px; color: #721c24; font-weight: bold; }
        
        h1, h2, h3 { color: var(--p-dark); font-weight: 800; text-transform: uppercase; border-left: 15px solid var(--p-yellow); padding-left: 15px; margin-top: 20px; }
        .brand-header { background-color: var(--p-dark); padding: 2rem; border-bottom: 6px solid var(--p-yellow); margin: -6rem -5rem 2rem -5rem; display: flex; align-items: center; }
        .logo-main { color: var(--p-yellow); font-size: 2.2rem; font-weight: 900; }
        
        /* Tekninen Taulukko */
        .tech-table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
        .tech-table td { border: 1px solid #ccc; padding: 12px; font-size: 0.95rem; }
        .tech-label { background-color: #f0f0f0; font-weight: bold; width: 30%; color: #333; }

        /* Kirjautumissivun keskitys */
        .login-box {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
            border: 2px solid var(--p-yellow);
            background-color: var(--p-dark);
            color: white;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

apply_pro_style()

# --- 3. SISÄÄNKIRJAUTUMISLOGIIKKA ---
def check_password():
    """Palauttaa True jos salasana on oikein."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Kirjautumisnäkymä
    st.markdown('<div style="text-align:center; padding:50px;"><h1 style="border:none;">PIMARA</h1><p>Järjestelmän kirjautuminen</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            password = st.text_input("Syötä salasana", type="password")
            submit = st.form_submit_button("KIRJAUDU SISÄÄN")
            if submit:
                if password == "Tappara": # Tähän voit vaihtaa haluamasi salasanan
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Väärä salasana.")
    return False

# Pysäytetään sovellus tähän, jos ei olla kirjauduttu
if not check_password():
    st.stop()

# --- 4. NAVIGAATION JA STATEN HALLINTA ---
if 'sivu' not in st.session_state: st.session_state.sivu = "TYÖPÖYTÄ"
if 'kortti_id' not in st.session_state: st.session_state.kortti_id = None

def vaihda_sivu(nimi):
    st.session_state.sivu = nimi
    st.session_state.kortti_id = None

# --- 5. APUFUNKTIOT ---
def get_konetyypit():
    res = supabase.table("konetyypit").select("nimi").execute()
    return [r['nimi'] for r in res.data] if res.data else []

def get_lisalaitetyypit():
    res = supabase.table("lisalaitetyypit").select("nimi").execute()
    return [r['nimi'] for r in res.data] if res.data else []

def get_yhtiot():
    res = supabase.table("yhtiot").select("id, nimi").execute()
    d = {0: "Valitse yhtiö"}
    for r in res.data: d[r['id']] = r['nimi']
    return d

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

def upload_image(file, folder_prefix):
    try:
        file_extension = file.name.split('.')[-1]
        file_name = f"{folder_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        file_path = f"uploads/{file_name}"
        supabase.storage.from_(BUCKET_NAME).upload(file_path, file.getvalue())
        return supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
    except: return None

# --- 6. VISUAALINEN KORTTI-KOMPONENTTI ---
def render_kone_kortti(k, y_dict, show_actions=False, task_id=None):
    st.markdown(f'<div class="kortti-header">KALUSTOKORTTI | {k.get("nimi","")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kortti-banner">{k.get("rekisteri", "EI REK")}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        if k.get("kuva_url"): st.image(k["kuva_url"], use_container_width=True)
        else: st.info("Ei kuvaa.")
        
    with col2:
        st.markdown(f"""
        <table class="tech-table">
            <tr><td class="tech-label">Omistaja</td><td>{y_dict.get(k.get('omistaja_id',0), 'Määrittelemetön')}</td></tr>
            <tr><td class="tech-label">Merkki / Malli</td><td>{k.get('merkki','')} {k.get('malli','')}</td></tr>
            <tr><td class="tech-label">Vuosimalli</td><td>{k.get('vuosimalli','')}</td></tr>
            <tr><td class="tech-label">Katsastus</td><td><b>{k.get('katsastus_pvm','')}</b></td></tr>
        </table>
        """, unsafe_allow_html=True)
        
        if show_actions:
            st.write("---")
            act1, act2 = st.columns(2)
            if act1.button(f"KATSASTETTU", key=f"dash_kats_{k['id']}_{task_id}"):
                uusi_kats = (date.today() + timedelta(days=365)).strftime("%d.%m.%Y")
                supabase.table("koneet").update({"katsastus_pvm": uusi_kats}).eq("id", k['id']).execute()
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "tyyppi": "Katsastus", "kuvaus": "Katsastus suoritettu"}).execute()
                st.rerun()
            if act2.button(f"HUOLLETTU", key=f"dash_huol_{k['id']}_{task_id}"):
                if task_id: supabase.table("aikataulu").update({"suoritettu": True}).eq("id", task_id).execute()
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "tyyppi": "Huolto", "kuvaus": "Huolto suoritettu"}).execute()
                st.rerun()

# --- 7. SIVUPALKKI ---
with st.sidebar:
    st.markdown('<div style="padding:20px; text-align:center; color:#ffcc00; font-size:2rem; font-weight:900;">PIMARA</div>', unsafe_allow_html=True)
    if st.button("TYÖPÖYTÄ"): vaihda_sivu("TYÖPÖYTÄ")
    if st.button("KONEREKISTERI"): vaihda_sivu("KONEET")
    if st.button("HALLINTA"): vaihda_sivu("HALLINTA")
    if st.button("HUOLTOHISTORIA"): vaihda_sivu("HISTORIA")
    if st.button("VUOSIKELLO"): vaihda_sivu("VUOSIKELLO")
    
    st.write("---")
    if st.button("KIRJAUDU ULOS"):
        st.session_state.authenticated = False
        st.rerun()

st.markdown('<div class="brand-header"><span class="logo-main">PIMARA</span><span style="color:white; margin-left:15px; font-weight:200;">KALUSTONHALLINTA</span></div>', unsafe_allow_html=True)

# --- 8. SIVU: TYÖPÖYTÄ ---
if st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard - Huomioitava kalusto")
    raja_pvm = date.today() + timedelta(days=30)
    y_dict = get_yhtiot()
    koneet = supabase.table("koneet").select("*").execute().data
    naytetty_ids = set()

    for k in koneet:
        needs_actions = False
        if k['katsastus_pvm']:
            try:
                kpvm = datetime.strptime(k['katsastus_pvm'], "%d.%m.%Y").date()
                if kpvm <= raja_pvm:
                    with st.container():
                        render_kone_kortti(k, y_dict, show_actions=True)
                        naytetty_ids.add(k['id'])
            except: pass
        
        v_tasks = supabase.table("aikataulu").select("*").eq("kone_id", k['id']).eq("suoritettu", False).execute().data
        for t in v_tasks:
            if date.fromisoformat(t['erapaiva']) <= raja_pvm and k['id'] not in naytetty_ids:
                with st.container():
                    render_kone_kortti(k, y_dict, show_actions=True, task_id=t['id'])
                    st.warning(f"TEHTÄVÄ: {t['tyyppi']} - {t['kuvaus']}")
                    naytetty_ids.add(k['id'])
    
    if not naytetty_ids: st.success("Kaikki kalusto on ajan tasalla.")

# --- 9. SIVU: HALLINTA ---
elif st.session_state.sivu == "HALLINTA":
    st.header("Järjestelmän asetukset")
    t1, t2, t3, t4, t5 = st.tabs(["KONETYYPIT", "YHTIÖT", "URAKAT", "KONEET", "LISÄLAITTEET"])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Konetyypit")
            with st.form("f_t_kone"):
                nt = st.text_input("Uusi konetyyppi")
                if st.form_submit_button("LISÄÄ"):
                    supabase.table("konetyypit").insert({"nimi": nt}).execute()
                    st.rerun()
            for t in get_konetyypit():
                col_a, col_b = st.columns([4,1])
                col_a.write(t)
                if col_b.button("X", key=f"dt_k_{t}"):
                    supabase.table("konetyypit").delete().eq("nimi", t).execute()
                    st.rerun()
        with c2:
            st.subheader("Lisälaitetyypit")
            with st.form("f_t_laite"):
                ntl = st.text_input("Uusi lisälaitetyyppi")
                if st.form_submit_button("LISÄÄ"):
                    supabase.table("lisalaitetyypit").insert({"nimi": ntl}).execute()
                    st.rerun()
            for tl in get_lisalaitetyypit():
                col_a, col_b = st.columns([4,1])
                col_a.write(tl)
                if col_b.button("X", key=f"dt_l_{tl}"):
                    supabase.table("lisalaitetyypit").delete().eq("nimi", tl).execute()
                    st.rerun()

    with t2:
        st.subheader("Konserniyhtiöt")
        with st.form("f_y"):
            yn, yt, yo = st.text_input("Nimi"), st.text_input("Y-tunnus"), st.text_input("Osoite")
            if st.form_submit_button("TALLENNA YHTIÖ"):
                supabase.table("yhtiot").insert({"nimi": yn, "y_tunnus": yt, "osoite": yo}).execute()
                st.rerun()
        for y in supabase.table("yhtiot").select("*").execute().data:
            st.write(f"**{y['nimi']}**")
            if st.button("POISTA", key=f"dy_{y['id']}"):
                supabase.table("yhtiot").delete().eq("id", y['id']).execute()
                st.rerun()

    with t3:
        st.subheader("Urakkahallinta")
        with st.form("f_u"):
            un, uo, up = st.text_input("Nimi"), st.text_input("Osoite"), st.text_input("PM Nimi")
            uph, uem = st.text_input("Puhelin"), st.text_input("Sähköposti")
            if st.form_submit_button("LISÄÄ URAKKA"):
                supabase.table("urakat").insert({"nimi":un, "yhteystiedot":uo, "tyopaallikko":up, "puhelin":uph, "sahkoposti":uem}).execute()
                st.rerun()
        for u in supabase.table("urakat").select("*").execute().data:
            st.write(f"**{u['nimi']}**")
            if st.button("POISTA", key=f"du_{u['id']}"):
                supabase.table("urakat").delete().eq("id", u['id']).execute()
                st.rerun()

    with t4:
        st.subheader("Koneiden lisäys")
        with st.form("f_k_new"):
            ca, cb, cc = st.columns(3)
            kn = ca.text_input("Tunnus")
            kt = ca.selectbox("Konetyyppi", get_konetyypit())
            ky = ca.selectbox("Omistajayhtiö", list(get_yhtiot().keys()), format_func=lambda x: get_yhtiot()[x])
            ksn, kma, kre = cb.text_input("SN"), cb.text_input("Merkki/Malli"), cb.text_input("Rekisteri")
            kkat = cc.text_input("Katsastus (pv.kk.vvvv)")
            kur = st.selectbox("Sijainti", list(get_urakat().keys()), format_func=lambda x: get_urakat()[x])
            kimg = st.file_uploader("Kuva")
            if st.form_submit_button("TALLENNA KONE"):
                url = upload_image(kimg, "kone") if kimg else None
                supabase.table("koneet").insert({"nimi": kn, "tyyppi": kt, "omistaja_id": ky, "sarjanumero": ksn, "malli": kma, "rekisteri": kre, "katsastus_pvm": kkat, "urakka_id": kur, "kuva_url": url}).execute()
                st.rerun()

    with t5:
        st.subheader("Lisälaitteiden lisäys")
        with st.form("f_l"):
            lt = st.selectbox("Tyyppi", get_lisalaitetyypit())
            lm, lsn = st.text_input("Merkki/Malli"), st.text_input("SN")
            lk = st.selectbox("Koneeseen", list(get_koneiden_nimet().keys()), format_func=lambda x: get_koneiden_nimet()[x])
            if st.form_submit_button("LISÄÄ LAITE"):
                supabase.table("lisalaitteet").insert({"nimi": lt, "merkki": lm, "valmistenumero": lsn, "kone_id": lk}).execute()
                st.rerun()

# --- 10. SIVU: KONEREKISTERI (KATSELU) ---
elif st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        res = supabase.table("koneet").select("*").eq("id", st.session_state.kortti_id).execute().data
        if res: render_kone_kortti(res[0], get_yhtiot())
        if st.button("SULJE"):
            st.session_state.kortti_id = None
            st.rerun()
    else:
        st.header("Kalustoluettelo")
        for r in supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").execute().data:
            st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b> ({r["tyyppi"]})<br>Rek: {r["rekisteri"]}</div>', unsafe_allow_html=True)
            if st.button("AVAA KORTTI", key=f"view_{r['id']}"):
                st.session_state.kortti_id = r['id']
                st.rerun()

# --- 11. MUUT ---
elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    h_data = supabase.table("huollot").select("*").order("pvm", desc=True).execute().data
    kn = get_koneiden_nimet()
    for h in h_data:
        st.markdown(f'<div class="mobile-card"><b>{kn.get(h["kone_id"])}</b> - {h["pvm"]}<br>{h["kuvaus"]}</div>', unsafe_allow_html=True)

elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello")
    with st.form("v_f"):
        vk = st.selectbox("Kone", list(get_koneiden_nimet().keys()), format_func=lambda x: get_koneiden_nimet()[x])
        vp, vt = st.date_input("Päivä"), st.text_input("Tehtävä")
        if st.form_submit_button("LISÄÄ"):
            supabase.table("aikataulu").insert({"kone_id": vk, "erapaiva": vp.isoformat(), "tyyppi": vt, "suoritettu": False}).execute()
            st.rerun()