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

# --- 2. TYYLIT (PIMARA INDUSTRIAL & MOBILE OPTIMIZED) ---
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
        div.stSidebar [data-testid="stVerticalBlock"] button:hover {
            background-color: #e6b800 !important;
            transform: scale(1.02);
        }
        
        /* Kortit ja Alertit */
        .mobile-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 12px; background-color: #fcfcfc; border-left: 8px solid var(--p-yellow); }
        .alert-card-warning { padding: 15px; background-color: #fff3cd; border-left: 10px solid #ffc107; margin-bottom: 10px; color: #856404; font-weight: bold; }
        .alert-card-danger { padding: 15px; background-color: #f8d7da; border-left: 10px solid #dc3545; margin-bottom: 10px; color: #721c24; font-weight: bold; }

        h1, h2, h3 { color: var(--p-dark); font-weight: 800; text-transform: uppercase; border-left: 15px solid var(--p-yellow); padding-left: 15px; margin-top: 20px; }
        .brand-header { background-color: var(--p-dark); padding: 2rem; border-bottom: 6px solid var(--p-yellow); margin: -6rem -5rem 2rem -5rem; display: flex; align-items: center; }
        .logo-main { color: var(--p-yellow); font-size: 2.2rem; font-weight: 900; }
        
        /* Kalustokortin taulukko */
        .tech-table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
        .tech-table td { border: 1px solid #ccc; padding: 12px; font-size: 0.95rem; }
        .tech-label { background-color: #f0f0f0; font-weight: bold; width: 30%; color: #333; }

        @media (max-width: 600px) {
            .tech-table tr { display: flex; flex-direction: column; border-bottom: 2px solid #ddd; }
            .tech-table td { width: 100% !important; border: none; padding: 5px 10px; }
        }
        </style>
    """, unsafe_allow_html=True)

apply_pro_style()

# --- 3. NAVIGAATION JA STATEN HALLINTA ---
if 'sivu' not in st.session_state: st.session_state.sivu = "TYÖPÖYTÄ"
if 'kortti_id' not in st.session_state: st.session_state.kortti_id = None
if 'edit_target' not in st.session_state: st.session_state.edit_target = None # (taulu, id)

def vaihda_sivu(nimi):
    st.session_state.sivu = nimi
    st.session_state.kortti_id = None
    st.session_state.edit_target = None

# --- 4. APUFUNKTIOT ---
def get_konetyypit():
    res = supabase.table("konetyypit").select("nimi").execute()
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

# --- 5. VISUAALINEN KALUSTOKORTTI-KOMPONENTTI ---
def render_kone_kortti(k, y_dict, show_actions=False, task_id=None):
    """Piirtää teknisen kortin koneesta. Jos show_actions=True, lisätään kuittausnapit."""
    st.markdown(f'<div class="kortti-header">AJONEUVOKORTTI | {k.get("nimi","")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kortti-banner">{k.get("rekisteri", "EI REK")}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        if k.get("kuva_url"): st.image(k["kuva_url"], use_container_width=True)
        else: st.info("Ei kuvaa.")
        
    with col2:
        st.markdown(f"""
        <table class="tech-table">
            <tr><td class="tech-label">Omistaja</td><td>{y_dict.get(k.get('omistaja_id',0), 'Määrittämätön')}</td></tr>
            <tr><td class="tech-label">Konetyyppi</td><td>{k.get('tyyppi','')}</td></tr>
            <tr><td class="tech-label">Merkki/Malli</td><td>{k.get('merkki','')} {k.get('malli','')}</td></tr>
            <tr><td class="tech-label">S/N</td><td>{k.get('sarjanumero','')}</td></tr>
            <tr><td class="tech-label">Katsastus</td><td><b>{k.get('katsastus_pvm','')}</b></td></tr>
        </table>
        """, unsafe_allow_html=True)
        
        if show_actions:
            st.write("---")
            act1, act2 = st.columns(2)
            if act1.button(f"KATSASTETTU", key=f"kats_{k['id']}_{task_id}"):
                uusi_pvm = (date.today() + timedelta(days=365)).strftime("%d.%m.%Y")
                supabase.table("koneet").update({"katsastus_pvm": uusi_pvm}).eq("id", k['id']).execute()
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "kuvaus": "Määräaikaiskatsastus suoritettu"}).execute()
                st.success("Katsastus päivitetty vuodella eteenpäin!")
                st.rerun()
            if act2.button(f"HUOLLETTU", key=f"huol_{k['id']}_{task_id}"):
                if task_id:
                    supabase.table("aikataulu").update({"suoritettu": True}).eq("id", task_id).execute()
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "kuvaus": "Määräaikaishuolto suoritettu (Dashboard)"}).execute()
                st.success("Huolto kirjattu historiaan!")
                st.rerun()

# --- 6. SIVUPALKKI ---
with st.sidebar:
    st.markdown('<div style="padding:20px; text-align:center; color:#ffcc00; font-size:2rem; font-weight:900; border-bottom:1px solid #333; margin-bottom:20px;">PIMARA</div>', unsafe_allow_html=True)
    if st.button("TYÖPÖYTÄ"): vaihda_sivu("TYÖPÖYTÄ")
    if st.button("KONEREKISTERI"): vaihda_sivu("KONEET")
    if st.button("HALLINTA"): vaihda_sivu("HALLINTA")
    if st.button("HUOLTOHISTORIA"): vaihda_sivu("HISTORIA")
    if st.button("VUOSIKELLO"): vaihda_sivu("VUOSIKELLO")

st.markdown('<div class="brand-header"><span class="logo-main">PIMARA</span><span style="color:white; margin-left:15px; font-weight:200;">KALUSTONHALLINTA</span></div>', unsafe_allow_html=True)

# --- 7. SIVU: TYÖPÖYTÄ (UUSI NÄKYMÄ) ---
if st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard - Työnalle tuleva kalusto")
    
    tanaan = date.today()
    raja_pvm = tanaan + timedelta(days=30)
    y_dict = get_yhtiot()
    
    # 1. METRIIKAT
    c1, c2, c3 = st.columns(3)
    k_res = supabase.table("koneet").select("id", count="exact").execute()
    u_res = supabase.table("urakat").select("id", count="exact").execute()
    c1.metric("Koneet", k_res.count if k_res.count else 0)
    c2.metric("Aktiiviset urakat", u_res.count if u_res.count else 0)
    
    # 2. HÄLYTYSLOGIIKKA JA KORTIT
    st.subheader("Huolto- ja katsastusjonossa")
    
    # Haetaan koneet joilla katsastus lähellä tai ohi
    koneet = supabase.table("koneet").select("*").execute().data
    pending_ids = set() # Estetään duplikaatit
    
    for k in koneet:
        needs_showing = False
        if k['katsastus_pvm']:
            try:
                kpvm = datetime.strptime(k['katsastus_pvm'], "%d.%m.%Y").date()
                if kpvm <= raja_pvm: needs_showing = True
            except: pass
            
        # Tarkista myös onko aikataulussa avoin tehtävä
        v_tasks = supabase.table("aikataulu").select("*").eq("kone_id", k['id']).eq("suoritettu", False).execute().data
        for t in v_tasks:
            try:
                vpvm = date.fromisoformat(t['erapaiva'])
                if vpvm <= raja_pvm: 
                    needs_showing = True
                    # Jos on tehtävä, renderöidään kortti tehtävä-id:n kanssa
                    with st.container():
                        render_kone_kortti(k, y_dict, show_actions=True, task_id=t['id'])
                        st.markdown(f"**Tehtävä:** {t['tyyppi']} - {t['kuvaus']} (Eräpäivä: {t['erapaiva']})")
                        pending_ids.add(k['id'])
            except: pass
            
        # Jos vain katsastus on lähellä mutta ei tehtävää
        if needs_showing and k['id'] not in pending_ids:
            with st.container():
                render_kone_kortti(k, y_dict, show_actions=True)
                pending_ids.add(k['id'])

    if not pending_ids:
        st.success("Ei välittömiä huolto- tai katsastustarpeita.")

# --- 8. SIVU: HALLINTA (KESKITETTY HALLINTA) ---
elif st.session_state.sivu == "HALLINTA":
    st.header("Järjestelmän hallinta")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["KONETYYPIT", "YHTIÖT", "URAKAT", "KONEIDEN MUOKKAUS", "LISÄLAITTEIDEN MUOKKAUS"])
    
    # TÄÄLLÄ ON KAIKKI MUOKKAUS JA POISTO LOGIIKKA
    with tab1:
        st.subheader("Konetyyppien hallinta")
        c1, c2 = st.columns([3,1])
        u_typ = c1.text_input("Uusi konetyyppi").strip()
        if c2.button("LISÄÄ TYYPPI"):
            if u_typ:
                supabase.table("konetyypit").insert({"nimi": u_typ}).execute()
                st.rerun()
        
        tyypit = get_konetyypit()
        for t in tyypit:
            col_t, col_b = st.columns([4,1])
            col_t.write(t)
            if col_b.button("POISTA", key=f"del_t_{t}"):
                supabase.table("konetyypit").delete().eq("nimi", t).execute()
                st.rerun()

    with tab2:
        st.subheader("Yhtiöiden hallinta")
        with st.form("y_form", clear_on_submit=True):
            yn = st.text_input("Yhtiön nimi")
            yt = st.text_input("Y-tunnus")
            if st.form_submit_button("LISÄÄ YHTIÖ"):
                supabase.table("yhtiot").insert({"nimi": yn, "y_tunnus": yt}).execute()
                st.rerun()
        y_data = supabase.table("yhtiot").select("*").execute().data
        for y in y_data:
            c1, c2 = st.columns([4,1])
            c1.write(f"**{y['nimi']}** ({y['y_tunnus']})")
            if c2.button("POISTA", key=f"dy_{y['id']}"):
                supabase.table("yhtiot").delete().eq("id", y['id']).execute()
                st.rerun()

    with tab3:
        st.subheader("Urakoiden hallinta")
        with st.form("u_form"):
            un = st.text_input("Urakan nimi")
            uo = st.text_input("Osoite / Sijainti")
            if st.form_submit_button("LISÄÄ URAKKA"):
                supabase.table("urakat").insert({"nimi": un, "yhteystiedot": uo}).execute()
                st.rerun()
        u_data = supabase.table("urakat").select("*").execute().data
        for u in u_data:
            c1, c2 = st.columns([4,1])
            c1.write(f"**{u['nimi']}** - {u['yhteystiedot']}")
            if c2.button("POISTA", key=f"du_{u['id']}"):
                supabase.table("urakat").delete().eq("id", u['id']).execute()
                st.rerun()

    with tab4:
        st.subheader("Koneiden muokkaus ja poisto")
        k_data = supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").execute().data
        for k in k_data:
            with st.expander(f"{k['nimi']} ({k['rekisteri']})"):
                # Tässä voisi olla täysi muokkauslomake, mutta tehdään poisto pika-apuna
                if st.button("POISTA KONE LOPULLISESTI", key=f"dk_{k['id']}"):
                    supabase.table("koneet").delete().eq("id", k['id']).execute()
                    st.rerun()

# --- 9. SIVU: KONEREKISTERI (SELAILU) ---
elif st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        k_id = st.session_state.kortti_id
        res = supabase.table("koneet").select("*").eq("id", k_id).execute()
        if res.data:
            render_kone_kortti(res.data[0], get_yhtiot())
        if st.button("SULJE KORTTI"):
            st.session_state.kortti_id = None
            st.rerun()
    else:
        st.header("Kalustoluettelo")
        tyypit = get_konetyypit()
        f_tyyppi = st.multiselect("Suodata tyypillä", tyypit)
        
        q = supabase.table("koneet").select("id, nimi, tyyppi, rekisteri")
        if f_tyyppi: q = q.in_("tyyppi", f_tyyppi)
        res = q.execute()
        
        for r in res.data:
            st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b> ({r["tyyppi"]})<br>Rek: {r["rekisteri"]}</div>', unsafe_allow_html=True)
            if st.button("AVAA KALUSTOKORTTI", key=f"open_{r['id']}"):
                st.session_state.kortti_id = r['id']
                st.rerun()

# --- 10. SIVU: HISTORIA JA VUOSIKELLO (ENNALLEEN) ---
elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    h_res = supabase.table("huollot").select("*").order("pvm", desc=True).execute()
    k_nimet = get_koneiden_nimet()
    for h in h_res.data:
        st.markdown(f'<div class="mobile-card"><b>{k_nimet.get(h["kone_id"])}</b> - {h["pvm"]}<br>{h["kuvaus"]}</div>', unsafe_allow_html=True)

elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello")
    k_opts = get_koneiden_nimet()
    with st.expander("LISÄÄ TAPAHTUMA"):
        with st.form("v_f"):
            vk = st.selectbox("Kone", list(k_opts.keys()), format_func=lambda x: k_opts[x])
            vp = st.date_input("Päivä")
            vt = st.text_input("Tehtävä")
            if st.form_submit_button("LISÄÄ"):
                supabase.table("aikataulu").insert({"kone_id": vk, "erapaiva": vp.isoformat(), "tyyppi": vt, "suoritettu": False}).execute()
                st.rerun()
    
    v_res = supabase.table("aikataulu").select("*").eq("suoritettu", False).order("erapaiva").execute()
    for r in v_res.data:
        st.markdown(f'<div class="mobile-card"><b>{k_opts.get(r["kone_id"])}</b>: {r["erapaiva"]}<br>{r["tyyppi"]}</div>', unsafe_allow_html=True)