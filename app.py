import streamlit as st
from datetime import date, datetime, timedelta
import config
import database as db
import ui_components as ui

config.apply_pro_style()

# --- 1. KIRJAUDU SISÄÄN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><h1>PIMARA</h1><p>KIRJAUDU SISÄÄN</p></div>', unsafe_allow_html=True)
    pw = st.text_input("Salasana", type="password")
    if st.button("KIRJAUDU"):
        if pw == "Tappara":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Väärä salasana.")
    st.stop()

# --- 2. NAVIGAATIO ---
if 'sivu' not in st.session_state: st.session_state.sivu = "TYÖPÖYTÄ"
if 'kortti_id' not in st.session_state: st.session_state.kortti_id = None

def navigoi(nimi):
    st.session_state.sivu = nimi
    st.session_state.kortti_id = None

with st.sidebar:
    st.markdown('<div style="padding:20px; text-align:center; color:#ffcc00; font-size:2rem; font-weight:900;">PIMARA</div>', unsafe_allow_html=True)
    if st.button("TYÖPÖYTÄ"): navigoi("TYÖPÖYTÄ")
    if st.button("KONEREKISTERI"): navigoi("KONEET")
    if st.button("HALLINTA"): navigoi("HALLINTA")
    if st.button("HUOLTOHISTORIA"): navigoi("HISTORIA")
    if st.button("VUOSIKELLO"): navigoi("VUOSIKELLO")
    if st.button("KIRJAUDU ULOS"): st.session_state.auth = False; st.rerun()

st.markdown('<div class="brand-header"><span class="logo-main">PIMARA</span><span style="color:white; margin-left:15px; font-weight:200;">KALUSTONHALLINTA</span></div>', unsafe_allow_html=True)

# --- 3. SIVUJEN LOGIIKKA ---

# SIVU: TYÖPÖYTÄ
if st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard - Huoltojono")
    raja = date.today() + timedelta(days=30)
    y_dict = db.get_yhtiot()
    koneet = db.supabase.table("koneet").select("*").execute().data
    shown = set()
    for k in koneet:
        needs = False
        if k['katsastus_pvm']:
            try:
                if datetime.strptime(k['katsastus_pvm'], "%d.%m.%Y").date() <= raja: needs = True
            except: pass
        v_tasks = db.supabase.table("aikataulu").select("*").eq("kone_id", k['id']).eq("suoritettu", False).execute().data
        for t in v_tasks:
            if date.fromisoformat(t['erapaiva']) <= raja:
                ui.render_kalustokortti(k, y_dict, show_actions=True, task_id=t['id'])
                st.warning(f"TEHTÄVÄ: {t['tyyppi']} ({t['erapaiva']})")
                shown.add(k['id'])
        if needs and k['id'] not in shown:
            ui.render_kalustokortti(k, y_dict, show_actions=True)
            shown.add(k['id'])
    if not shown: st.success("Kaikki kalusto kunnossa.")

# SIVU: HALLINTA (TÄYSI CRUD JA LOMAKKEET)
elif st.session_state.sivu == "HALLINTA":
    st.header("Järjestelmän asetukset")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["TYYPIT", "YHTIÖT", "URAKAT", "KONEET", "LISÄLAITTEET"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Konetyypit")
            with st.form("f_t_k"):
                nt = st.text_input("Uusi konetyyppi")
                if st.form_submit_button("LISÄÄ"):
                    db.supabase.table("konetyypit").insert({"nimi":nt}).execute(); st.rerun()
            for t in db.get_konetyypit():
                col_a, col_b = st.columns([4,1])
                col_a.write(t)
                if col_b.button("X", key=f"dk_{t}"): db.poista_konetyyppi(t); st.rerun()
        with c2:
            st.subheader("Lisälaitetyypit")
            with st.form("f_t_l"):
                ntl = st.text_input("Uusi lisälaitetyyppi")
                if st.form_submit_button("LISÄÄ"):
                    db.supabase.table("lisalaitetyypit").insert({"nimi":ntl}).execute(); st.rerun()
            for tl in db.get_lisalaitetyypit():
                col_a, col_b = st.columns([4,1])
                col_a.write(tl)
                if col_b.button("X", key=f"dl_{tl}"): db.poista_lisalaitetyyppi(tl); st.rerun()

    with tab2:
        st.subheader("Konserniyhtiöt")
        with st.form("f_y"):
            yn, yt, yo = st.text_input("Nimi"), st.text_input("Y-tunnus"), st.text_input("Osoite")
            if st.form_submit_button("TALLENNA"):
                db.supabase.table("yhtiot").insert({"nimi":yn, "y_tunnus":yt, "osoite":yo}).execute(); st.rerun()
        for y in db.supabase.table("yhtiot").select("*").execute().data:
            c1, c2 = st.columns([4,1])
            c1.write(y['nimi'])
            if c2.button("POISTA", key=f"dy_{y['id']}"): db.poista_rivi("yhtiot", y['id']); st.rerun()

    with tab3:
        st.subheader("Urakat")
        with st.form("f_u"):
            un = st.text_input("Urakan nimi")
            uo = st.text_input("Osoite / Sijainti")
            up = st.text_input("Työmaapäällikkö")
            uph = st.text_input("PM Puhelin")
            uem = st.text_input("PM Sähköposti")
            if st.form_submit_button("LISÄÄ URAKKA"):
                db.supabase.table("urakat").insert({"nimi":un, "yhteystiedot":uo, "tyopaallikko":up, "puhelin":uph, "sahkoposti":uem}).execute(); st.rerun()
        for u in db.supabase.table("urakat").select("*").execute().data:
            c1, c2 = st.columns([4,1])
            c1.write(f"{u['nimi']} ({u.get('tyopaallikko','')})")
            if c2.button("POISTA", key=f"du_{u['id']}"): db.poista_rivi("urakat", u['id']); st.rerun()

    with tab4:
        st.subheader("Koneiden hallinta")
        with st.expander("LISÄÄ UUSI KONE"):
            with st.form("f_k"):
                c1, c2, c3 = st.columns(3)
                kn = c1.text_input("Tunnus")
                kt = c1.selectbox("Tyyppi", db.get_konetyypit())
                ky = c1.selectbox("Yhtiö", list(db.get_yhtiot().keys()), format_func=lambda x: db.get_yhtiot()[x])
                kme, kma, ksn = c2.text_input("Merkki"), c2.text_input("Malli"), c2.text_input("SN")
                kre, kvu, kte = c2.text_input("Rekisteri"), c2.text_input("Vuosi"), c2.text_input("Teho")
                kmo, kpa = c3.text_input("Moottori"), c3.text_input("Päästö")
                kpi, kko = c3.text_input("Pituus"), c3.text_input("Korkeus")
                kom, kka = c3.text_input("Omapaino"), c3.text_input("Kantavuus")
                kkat = st.text_input("Katsastus (pv.kk.vvvv)")
                kur = st.selectbox("Urakka", list(db.get_urakat().keys()), format_func=lambda x: db.get_urakat()[x])
                kimg = st.file_uploader("Kuva")
                if st.form_submit_button("TALLENNA KONE"):
                    url = db.upload_image(kimg, "kone") if kimg else None
                    p = {"nimi":kn, "tyyppi":kt, "omistaja_id":ky, "merkki":kme, "malli":kma, "sarjanumero":ksn, "rekisteri":kre, "vuosimalli":kvu, "teho":kte, "moottori":kmo, "paastoluokka":kpa, "pituus":kpi, "korkeus":kko, "omamassa":kom, "kantavuus":kka, "katsastus_pvm":kkat, "urakka_id":kur, "kuva_url":url}
                    db.supabase.table("koneet").insert(p).execute(); st.rerun()
        for k in db.supabase.table("koneet").select("id, nimi").execute().data:
            c1, c2 = st.columns([4,1])
            c1.write(k['nimi'])
            if c2.button("POISTA", key=f"dk_{k['id']}"): db.poista_rivi("koneet", k['id']); st.rerun()

    with tab5:
        st.subheader("Lisälaitteiden hallinta")
        with st.form("f_l"):
            lt = st.selectbox("Tyyppi", db.get_lisalaitetyypit())
            lm, lma, lsn = st.text_input("Merkki"), st.text_input("Malli"), st.text_input("Valmistenumero")
            lk = st.selectbox("Kytke koneeseen", list(db.get_koneiden_nimet().keys()), format_func=lambda x: db.get_koneiden_nimet()[x])
            if st.form_submit_button("LISÄÄ LAITE"):
                db.supabase.table("lisalaitteet").insert({"nimi":lt, "merkki":lm, "malli":lma, "valmistenumero":lsn, "kone_id":lk}).execute(); st.rerun()
        for l in db.supabase.table("lisalaitteet").select("id, nimi, merkki").execute().data:
            c1, c2 = st.columns([4,1])
            c1.write(f"{l['nimi']} ({l['merkki']})")
            if c2.button("POISTA", key=f"dl_{l['id']}"): db.poista_rivi("lisalaitteet", l['id']); st.rerun()

# SIVU: KONEET
elif st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        res = db.supabase.table("koneet").select("*").eq("id", st.session_state.kortti_id).execute().data
        if res: ui.render_kalustokortti(res[0], db.get_yhtiot())
        if st.button("SULJE"): st.session_state.kortti_id = None; st.rerun()
    else:
        st.header("Kalustoluettelo")
        for r in db.supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").execute().data:
            st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b> ({r["tyyppi"]})<br>Rek: {r["rekisteri"]}</div>', unsafe_allow_html=True)
            if st.button("AVAA KORTTI", key=f"v_{r['id']}"): st.session_state.kortti_id = r['id']; st.rerun()

# SIVU: HISTORIA
elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    kn = db.get_koneiden_nimet()
    for h in db.supabase.table("huollot").select("*").order("pvm", desc=True).execute().data:
        st.markdown(f'<div class="mobile-card"><b>{kn.get(h["kone_id"])}</b> - {h["pvm"]}<br>{h["kuvaus"]}</div>', unsafe_allow_html=True)

# SIVU: VUOSIKELLO
elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello")
    with st.form("v_f"):
        vk = st.selectbox("Kone", list(db.get_koneiden_nimet().keys()), format_func=lambda x: db.get_koneiden_nimet()[x])
        vp, vt = st.date_input("Määräpäivä"), st.text_input("Tehtävä")
        if st.form_submit_button("LISÄÄ"):
            db.supabase.table("aikataulu").insert({"kone_id":vk, "erapaiva":vp.isoformat(), "tyyppi":vt, "suoritettu":False}).execute(); st.rerun()
    for r in db.supabase.table("aikataulu").select("*").eq("suoritettu", False).order("erapaiva").execute().data:
        st.markdown(f'<div class="mobile-card"><b>{db.get_koneiden_nimet().get(r["kone_id"])}</b>: {r["erapaiva"]}<br>{r["tyyppi"]}</div>', unsafe_allow_html=True)