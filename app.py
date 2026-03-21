import streamlit as st
from datetime import date, datetime, timedelta
import config
import database as db
import ui_components as ui

config.apply_pro_style()

# --- KIRJAUTUMINEN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><h1>PIMARA</h1><p>KIRJAUDU SISÄÄN</p></div>', unsafe_allow_html=True)
    pw = st.text_input("Salasana", type="password")
    if st.button("KIRJAUDU"):
        if pw == "Pimara2024":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Väärä salasana.")
    st.stop()

# --- NAVIGAATIO ---
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
    st.write("---")
    if st.button("REFRESH DATA"): st.cache_data.clear(); st.rerun()
    if st.button("KIRJAUDU ULOS"): st.session_state.auth = False; st.rerun()

# --- SIVUT ---

if st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard - Huomioitava kalusto")
    raja_pvm = date.today() + timedelta(days=30)
    y_dict = db.get_yhtiot()
    # Haetaan koneet - tätä ei voi täysin välimuistaa jos halutaan reaaliaikaiset hälytykset
    koneet = config.supabase.table("koneet").select("*").execute().data
    naytetty_ids = set()

    for k in koneet:
        needs_action = False
        if k['katsastus_pvm']:
            try:
                if datetime.strptime(k['katsastus_pvm'], "%d.%m.%Y").date() <= raja_pvm: needs_action = True
            except: pass
        if needs_action:
            ui.render_kalustokortti(k, y_dict, show_actions=True)
            naytetty_ids.add(k['id'])
    
    if not naytetty_ids: st.success("Kaikki kalusto kunnossa.")

elif st.session_state.sivu == "HALLINTA":
    st.header("Järjestelmän hallinta")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["KONETYYPIT", "YHTIÖT", "URAKAT", "KONEET", "LISÄLAITTEET"])
    
    with tab4: # TÄYSI KONEHALLINTA
        st.subheader("Lisää uusi kone")
        with st.form("f_k_new", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            kn, kt = c1.text_input("Tunnus"), c1.selectbox("Tyyppi", db.get_konetyypit())
            ky = c1.selectbox("Omistajayhtiö", list(db.get_yhtiot().keys()), format_func=lambda x: db.get_yhtiot()[x])
            kme, kma, ksn = c1.text_input("Merkki"), c1.text_input("Malli"), c1.text_input("SN")
            kre, kvu, kte = c2.text_input("Rekisteri"), c2.text_input("Vuosi"), c2.text_input("Teho (kW)")
            kmo, kpa = c2.text_input("Moottori"), c2.text_input("Päästö")
            kpi, kko = c3.text_input("Pituus"), c3.text_input("Korkeus")
            kom, kka = c3.text_input("Omapaino"), c3.text_input("Kantavuus")
            kkat = st.text_input("Katsastus (pv.kk.vvvv)")
            kur = st.selectbox("Sijainti", list(db.get_urakat().keys()), format_func=lambda x: db.get_urakat()[x])
            kimg = st.file_uploader("Kuva")
            if st.form_submit_button("TALLENNA KONE"):
                url = db.upload_image(kimg, "kone") if kimg else None
                p = {"nimi":kn, "tyyppi":kt, "omistaja_id":ky, "merkki":kme, "malli":kma, "sarjanumero":ksn, "rekisteri":kre, "vuosimalli":kvu, "teho":kte, "moottori":kmo, "paastoluokka":kpa, "pituus":kpi, "korkeus":kko, "omamassa":kom, "kantavuus":kka, "katsastus_pvm":kkat, "urakka_id":kur, "kuva_url":url}
                config.supabase.table("koneet").insert(p).execute()
                st.cache_data.clear()
                st.rerun()

elif st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        res = config.supabase.table("koneet").select("*").eq("id", st.session_state.kortti_id).execute().data
        if res: ui.render_kalustokortti(res[0], db.get_yhtiot())
        if st.button("SULJE"): st.session_state.kortti_id = None; st.rerun()
    else:
        st.header("Kalustoluettelo")
        rows = config.supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").execute().data or []

        # Tyypit listasta (dynaaminen)
        tyypit_lista = sorted(
            {(r.get("tyyppi") or "").strip() for r in rows if (r.get("tyyppi") or "").strip()}
        )

        f1, f2 = st.columns([1, 1])
        with f1:
            valittu_tyyppi = st.selectbox(
                "Suodata tyypin mukaan",
                options=["Kaikki tyypit"] + tyypit_lista,
                index=0,
            )
        with f2:
            haku = st.text_input("Hae rekisterillä tai tunnuksella", placeholder="Kirjoita…")

        if valittu_tyyppi != "Kaikki tyypit":
            rows = [r for r in rows if (r.get("tyyppi") or "").strip() == valittu_tyyppi]

        if haku and haku.strip():
            q = haku.strip().lower()
            rows = [
                r
                for r in rows
                if q in (r.get("rekisteri") or "").lower()
                or q in (r.get("nimi") or "").lower()
            ]

        if not rows:
            st.info("Ei kalustoa valituilla suodattimilla.")

        for r in rows:
            rek = (r.get("rekisteri") or "").strip()
            nimi = (r.get("nimi") or "").strip()
            tyyppi = (r.get("tyyppi") or "").strip()
            # Pääotsikko: rekisterinumero; jos puuttuu, näytetään tunnus (nimi)
            otsikko = rek if rek else (nimi if nimi else "—")
            rivi2_osat = []
            if tyyppi:
                rivi2_osat.append(tyyppi)
            if rek and nimi:
                rivi2_osat.append(f"Tunnus {nimi}")
            rivi2 = " · ".join(rivi2_osat)
            rivi2_html = (
                f'<br><span style="opacity:0.9;font-size:0.95em">{rivi2}</span>'
                if rivi2
                else ""
            )
            st.markdown(
                f'<div class="mobile-card"><b>{otsikko}</b>{rivi2_html}</div>',
                unsafe_allow_html=True,
            )
            if st.button("AVAA KORTTI", key=f"v_{r['id']}"):
                st.session_state.kortti_id = r["id"]
                st.rerun()

elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    st.info("Ominaisuutta ei ole vielä toteutettu tässä versiokuvassa.")

elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello")
    st.info("Ominaisuutta ei ole vielä toteutettu tässä versiokuvassa.")

else:
    st.warning(f"Tuntematon näkymä: {st.session_state.sivu}")