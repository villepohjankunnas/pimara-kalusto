import streamlit as st
from datetime import date, datetime, timedelta
from config import apply_pro_style, supabase
import database as db
import ui_components as ui

apply_pro_style()

# --- 1. KIRJAUTUMINEN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><h1>PIMARA</h1><p>KIRJAUDU SISÄÄN</p></div>', unsafe_allow_html=True)
    pw = st.text_input("Salasana", type="password")
    if st.button("KIRJAUDU"):
        if pw == "Tappara":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Väärin.")
    st.stop()

# --- 2. NAVIGAATIO ---
if 'sivu' not in st.session_state: st.session_state.sivu = "TYÖPÖYTÄ"
if 'kortti_id' not in st.session_state: st.session_state.kortti_id = None

with st.sidebar:
    st.markdown('<div style="text-align:center; color:#ffcc00; font-size:2rem; font-weight:900; padding:20px;">PIMARA</div>', unsafe_allow_html=True)
    if st.button("TYÖPÖYTÄ"): st.session_state.sivu = "TYÖPÖYTÄ"; st.session_state.kortti_id = None
    if st.button("KONEREKISTERI"): st.session_state.sivu = "KONEET"; st.session_state.kortti_id = None
    if st.button("HALLINTA"): st.session_state.sivu = "HALLINTA"
    if st.button("HUOLTOHISTORIA"): st.session_state.sivu = "HISTORIA"
    if st.button("VUOSIKELLO"): st.session_state.sivu = "VUOSIKELLO"
    if st.button("KIRJAUDU ULOS"): st.session_state.auth = False; st.rerun()

st.markdown('<div class="brand-header"><span class="logo-main">PIMARA</span><span style="color:white; margin-left:15px; font-weight:200;">KALUSTONHALLINTA</span></div>', unsafe_allow_html=True)

# --- 3. SIVUT ---

if st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard - Huoltojono")
    raja = date.today() + timedelta(days=30)
    y_dict = db.get_yhtiot()
    koneet = supabase.table("koneet").select("*").execute().data
    shown = set()
    for k in koneet:
        needs = False
        if k['katsastus_pvm']:
            try:
                if datetime.strptime(k['katsastus_pvm'], "%d.%m.%Y").date() <= raja: needs = True
            except: pass
        v_tasks = supabase.table("aikataulu").select("*").eq("kone_id", k['id']).eq("suoritettu", False).execute().data
        for t in v_tasks:
            if date.fromisoformat(t['erapaiva']) <= raja:
                ui.render_kone_kortti(k, y_dict, show_actions=True, task_id=t['id'])
                st.warning(f"TEHTÄVÄ: {t['tyyppi']} ({t['erapaiva']})")
                shown.add(k['id'])
        if needs and k['id'] not in shown:
            ui.render_kone_kortti(k, y_dict, show_actions=True)
            shown.add(k['id'])
    if not shown: st.success("Ei kiireellisiä toimenpiteitä.")

elif st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        res = supabase.table("koneet").select("*").eq("id", st.session_state.kortti_id).execute().data
        if res: ui.render_kone_kortti(res[0], db.get_yhtiot())
        if st.button("SULJE"): st.session_state.kortti_id = None; st.rerun()
    else:
        st.header("Kalustoluettelo")
        for r in supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").execute().data:
            st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b> ({r["tyyppi"]})<br>Rek: {r["rekisteri"]}</div>', unsafe_allow_html=True)
            if st.button("AVAA KORTTI", key=f"v_{r['id']}"): st.session_state.kortti_id = r['id']; st.rerun()

elif st.session_state.sivu == "HALLINTA":
    st.header("Hallintapaneeli")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["TYYPIT", "YHTIÖT", "URAKAT", "KONEET", "LISÄLAITTEET"])
    
    with tab4: # KONEIDEN TÄYSI LOMAKE
        st.subheader("Lisää uusi kone")
        with st.form("k_f_full", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            kn = c1.text_input("Tunnus")
            kt = c1.selectbox("Tyyppi", db.get_konetyypit())
            ky = c1.selectbox("Yhtiö", list(db.get_yhtiot().keys()), format_func=lambda x: db.get_yhtiot()[x])
            kme, kma, ksn = c1.text_input("Merkki"), c1.text_input("Malli"), c1.text_input("SN")
            kre, kvu, kvo = c2.text_input("Rekisteri"), c2.text_input("Vuosimalli"), c2.text_input("Käyttövoima")
            kpa, kmo, kte = c2.text_input("Päästöluokka"), c2.text_input("Moottori"), c2.text_input("Teho (kW)")
            kpi, kko, kom = c3.text_input("Pituus (mm)"), c3.text_input("Korkeus (mm)"), c3.text_input("Omamassa (kg)")
            kka, kkat = c3.text_input("Kantavuus (kg)"), c3.text_input("Katsastus (pv.kk.vvvv)")
            kur = st.selectbox("Sijainti", list(db.get_urakat().keys()), format_func=lambda x: db.get_urakat()[x])
            kimg = st.file_uploader("Kuva")
            if st.form_submit_button("TALLENNA KONE"):
                url = db.upload_image(kimg, "kone") if kimg else None
                payload = {"nimi":kn, "tyyppi":kt, "omistaja_id":ky, "merkki":kme, "malli":kma, "sarjanumero":ksn, "rekisteri":kre, "vuosimalli":kvu, "kayttovoima":kvo, "paastoluokka":kpa, "moottori":kmo, "teho":kte, "pituus":kpi, "korkeus":kko, "omamassa":kom, "kantavuus":kka, "katsastus_pvm":kkat, "urakka_id":kur, "kuva_url":url}
                supabase.table("koneet").insert(payload).execute(); st.rerun()
        for k in supabase.table("koneet").select("id, nimi").execute().data:
            if st.button(f"POISTA: {k['nimi']}", key=f"dk_{k['id']}"):
                db.poita_kohde("koneet", k['id']); st.rerun()

    # (Tämän jälkeen muut HALLINTA-välilehdet täytetään samalla kaavalla tähän...)

elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    kn = db.get_koneiden_nimet()
    for h in supabase.table("huollot").select("*").order("pvm", desc=True).execute().data:
        st.markdown(f'<div class="mobile-card"><b>{kn.get(h["kone_id"])}</b> - {h["pvm"]}<br>{h["kuvaus"]}</div>', unsafe_allow_html=True)

elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello")
    with st.form("v_f"):
        vk = st.selectbox("Kone", list(db.get_koneiden_nimet().keys()), format_func=lambda x: db.get_koneiden_nimet()[x])
        vp, vt = st.date_input("Määräpäivä"), st.text_input("Tehtävä")
        if st.form_submit_button("LISÄÄ"):
            supabase.table("aikataulu").insert({"kone_id":vk, "erapaiva":vp.isoformat(), "tyyppi":vt, "suoritettu":False}).execute(); st.rerun()