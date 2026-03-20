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
        [data-testid="stSidebar"] { background-color: var(--p-dark) !important; min-width: 300px !important; }
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
        
        /* Mobiilikortit */
        .mobile-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 12px;
            background-color: #fcfcfc;
            border-left: 8px solid var(--p-yellow);
        }

        /* Hälytyskortit Dashboardilla */
        .alert-card-warning { padding: 15px; background-color: #fff3cd; border-left: 10px solid #ffc107; margin-bottom: 10px; color: #856404; font-weight: bold; }
        .alert-card-danger { padding: 15px; background-color: #f8d7da; border-left: 10px solid #dc3545; margin-bottom: 10px; color: #721c24; font-weight: bold; }

        /* Otsikot */
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
            .logo-main { font-size: 1.5rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)

apply_pro_style()

# --- 3. NAVIGAATION JA STATEN HALLINTA ---
if 'sivu' not in st.session_state: st.session_state.sivu = "TYÖPÖYTÄ"
if 'kortti_id' not in st.session_state: st.session_state.kortti_id = None

def vaihda_sivu(nimi):
    st.session_state.sivu = nimi
    st.session_state.kortti_id = None

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
    except Exception as e:
        st.error(f"Virhe kuvan latauksessa: {e}")
        return None

# --- 5. SIVUPALKKI ---
with st.sidebar:
    st.markdown('<div style="padding:20px; text-align:center; color:#ffcc00; font-size:2rem; font-weight:900; border-bottom:1px solid #333; margin-bottom:20px;">PIMARA</div>', unsafe_allow_html=True)
    if st.button("TYÖPÖYTÄ"): vaihda_sivu("TYÖPÖYTÄ")
    if st.button("KONEREKISTERI"): vaihda_sivu("KONEET")
    if st.button("YHTIÖIDEN HALLINTA"): vaihda_sivu("YHTIOT")
    if st.button("URAKAT JA TYÖMAAT"): vaihda_sivu("URAKAT")
    if st.button("LISÄLAITEREKISTERI"): vaihda_sivu("LISÄLAITTEET")
    if st.button("HUOLTOHISTORIA"): vaihda_sivu("HISTORIA")
    if st.button("VUOSIKELLO"): vaihda_sivu("VUOSIKELLO")

st.markdown('<div class="brand-header"><span class="logo-main">PIMARA</span><span style="color:white; margin-left:15px; font-weight:200;">KALUSTONHALLINTA</span></div>', unsafe_allow_html=True)

# --- 6. KALUSTOKORTTI-FUNKTIO (TÄYSI TEKNINEN NÄKYMÄ) ---
def render_kalustokortti(k_id):
    res = supabase.table("koneet").select("*").eq("id", k_id).execute()
    if not res.data: return
    k = res.data[0]
    y_dict = get_yhtiot()
    
    st.markdown(f'<div class="kortti-header">AJONEUVOKORTTI <br><span style="color:white; font-size:1rem; font-weight:300;">Pimara Kuljetus Oy</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kortti-banner">{k.get("rekisteri", "EI REKISTERIÄ")}</div>', unsafe_allow_html=True)
    
    c_img, c_data = st.columns([1, 1.2])
    with c_img:
        if k.get("kuva_url"): st.image(k["kuva_url"], use_container_width=True)
        else: st.info("Ei valokuvaa tallennettu.")

    with c_data:
        st.markdown(f"""
        <table class="tech-table">
            <tr><td class="tech-label">Omistaja (Yhtiö)</td><td><b>{y_dict.get(k.get('omistaja_id', 0), 'Määrittelemetön')}</b></td></tr>
            <tr><td class="tech-label">Merkki / Malli</td><td>{k.get('merkki', '')} {k.get('malli', '')}</td></tr>
            <tr><td class="tech-label">Sarjanumero</td><td>{k.get('sarjanumero', '')}</td></tr>
            <tr><td class="tech-label">Vuosimalli</td><td>{k.get('vuosimalli', '')}</td></tr>
            <tr><td class="tech-label">Käyttövoima / Päästö</td><td>{k.get('kayttovoima', '')} / {k.get('paastoluokka', '')}</td></tr>
            <tr><td class="tech-label">Moottori / Teho</td><td>{k.get('moottori', '')} / {k.get('teho', '')} kW</td></tr>
            <tr><td class="tech-label">Mitat (P / K)</td><td>{k.get('pituus', '')} / {k.get('korkeus', '')} mm</td></tr>
            <tr><td class="tech-label">Massat (Oma / Kant.)</td><td>{k.get('omamassa', '')} / {k.get('kantavuus', '')} kg</td></tr>
            <tr><td class="tech-label">Seuraava Katsastus</td><td><b>{k.get('katsastus_pvm', '')}</b></td></tr>
        </table>
        """, unsafe_allow_html=True)

    st.subheader("Kytketyt lisälaitteet")
    l_res = supabase.table("lisalaitteet").select("nimi, tyyppi, merkki, valmistenumero").eq("kone_id", k_id).execute()
    if l_res.data: st.table(pd.DataFrame(l_res.data))
    else: st.caption("Ei kytkettyjä lisälaitteita.")
    
    if st.button("SULJE KALUSTOKORTTI"):
        st.session_state.kortti_id = None
        st.rerun()

# --- 7. SIVU: TYÖPÖYTÄ (LOGIIKKAVARMISTETTU DASHBOARD) ---
if st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard - Tilannekatsaus")
    
    tanaan = date.today()
    raja_pvm = tanaan + timedelta(days=30)
    alertit = []
    
    # Tarkista Katsastukset
    kone_res = supabase.table("koneet").select("id, nimi, katsastus_pvm").execute()
    for k in kone_res.data:
        if k['katsastus_pvm']:
            try:
                kpvm = datetime.strptime(k['katsastus_pvm'], "%d.%m.%Y").date()
                if kpvm <= tanaan: alertit.append({"t": "danger", "m": f"KATSASTUS VANHUNUT: {k['nimi']} ({k['katsastus_pvm']})"})
                elif kpvm <= raja_pvm: alertit.append({"t": "warning", "m": f"Katsastus lähestyy: {k['nimi']} ({k['katsastus_pvm']})"})
            except: pass

    # Tarkista Vuosikellon Huollot
    v_res = supabase.table("aikataulu").select("erapaiva, tyyppi, kone_id").eq("suoritettu", False).execute()
    k_nimet = get_koneiden_nimet()
    for v in v_res.data:
        try:
            vpvm = date.fromisoformat(v['erapaiva'])
            kn = k_nimet.get(v['kone_id'], "Tuntematon")
            if vpvm <= tanaan: alertit.append({"t": "danger", "m": f"HUOLTO MYÖHÄSSÄ: {kn} - {v['tyyppi']} ({vpvm})"})
            elif vpvm <= raja_pvm: alertit.append({"t": "warning", "m": f"TULEVA HUOLTO: {kn} - {v['tyyppi']} ({vpvm})"})
        except: pass

    if alertit:
        for a in alertit:
            st.markdown(f'<div class="alert-card-{a["t"]}">{a["m"]}</div>', unsafe_allow_html=True)
    else:
        st.success("Kaikki katsastukset ja huollot ovat ajan tasalla.")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    k_tot = supabase.table("koneet").select("id", count="exact").execute().count
    l_tot = supabase.table("lisalaitteet").select("id", count="exact").execute().count
    u_tot = supabase.table("urakat").select("id", count="exact").execute().count
    c1.metric("Koneet", k_tot if k_tot else 0)
    c2.metric("Laitteet", l_tot if l_tot else 0)
    c3.metric("Urakat", u_tot if u_tot else 0)

# --- 8. SIVU: KONEREKISTERI (TÄYSI LOMAKE) ---
elif st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        render_kalustokortti(st.session_state.kortti_id)
    else:
        st.header("Konerekisteri")
        tyypit = get_konetyypit()
        yhtiot = get_yhtiot()
        urakat = get_urakat()
        
        with st.expander("⚙️ HALLITSE KONETYYPPEJÄ"):
            c1, c2 = st.columns([3,1])
            u_typ = c1.text_input("Uusi tyyppi").strip()
            if c2.button("LISÄÄ"):
                if u_typ:
                    supabase.table("konetyypit").insert({"nimi": u_typ}).execute()
                    st.rerun()

        with st.expander("LISÄÄ UUSI KONE (KAIKKI TEKNISET TIEDOT)"):
            with st.form("kone_form_full", clear_on_submit=True):
                ca, cb, cc = st.columns(3)
                # Sarake 1
                kn = ca.text_input("Tunnus / Nimi")
                kt = ca.selectbox("Konetyyppi", tyypit)
                ky = ca.selectbox("Omistajayhtiö", list(yhtiot.keys()), format_func=lambda x: yhtiot[x])
                kmerkki = ca.text_input("Merkki")
                kmalli = ca.text_input("Malli")
                ksn = ca.text_input("Sarjanumero")
                # Sarake 2
                kre = cb.text_input("Rekisterinumero")
                kvu = cb.text_input("Vuosimalli")
                kvo = cb.text_input("Käyttövoima")
                kpa = cb.text_input("Päästöluokka")
                kmo = cb.text_input("Moottorin tiedot")
                kte = cb.text_input("Teho (kW)")
                # Sarake 3
                klu = cc.text_input("Ajoneuvoluokka")
                kak = cc.text_input("Akselit")
                kpi = cc.text_input("Pituus (mm)")
                kko = cc.text_input("Korkeus (mm)")
                kom = cc.text_input("Omamassa (kg)")
                kka = cc.text_input("Kantavuus (kg)")
                
                kkat = st.text_input("Katsastuspäivä (pv.kk.vvvv)")
                kur = st.selectbox("Sijainti", list(urakat.keys()), format_func=lambda x: urakat[x])
                k_img = st.file_uploader("Koneen kuva", type=['jpg','png','jpeg'])
                
                if st.form_submit_button("TALLENNA KONE"):
                    url = upload_image(k_img, "kone") if k_img else None
                    payload = {
                        "nimi": kn, "tyyppi": kt, "omistaja_id": ky, "merkki": kmerkki, "malli": kmalli,
                        "sarjanumero": ksn, "rekisteri": kre, "vuosimalli": kvu, "kayttovoima": kvo,
                        "paastoluokka": kpa, "moottori": kmo, "teho": kte, "luokka": klu, "akselit": kak,
                        "pituus": kpi, "korkeus": kko, "omamassa": kom, "kantavuus": kka, 
                        "katsastus_pvm": kkat, "urakka_id": kur, "kuva_url": url, "tila": "Käytössä"
                    }
                    supabase.table("koneet").insert(payload).execute()
                    st.rerun()

        # Kalustolistaus (Mobiilioptimoidut kortit)
        y_names = get_yhtiot()
        res = supabase.table("koneet").select("id, nimi, tyyppi, rekisteri, omistaja_id").execute()
        for r in res.data:
            st.markdown(f"""<div class="mobile-card">
                <b>{r['nimi']}</b> ({r['tyyppi']})<br>
                Yhtiö: {y_names.get(r['omistaja_id'])}<br>
                Rek: {r['rekisteri']}
            </div>""", unsafe_allow_html=True)
            if st.button("AVAA KALUSTOKORTTI", key=f"sel_{r['id']}"):
                st.session_state.kortti_id = r['id']
                st.rerun()

# --- 9. SIVU: YHTIÖIDEN HALLINTA ---
elif st.session_state.sivu == "YHTIOT":
    st.header("Konsernin Yhtiöt")
    with st.expander("LISÄÄ UUSI TYTÄRYHTIÖ"):
        with st.form("y_form"):
            yn = st.text_input("Yhtiön nimi")
            yt = st.text_input("Y-tunnus")
            yo = st.text_input("Osoite")
            if st.form_submit_button("TALLENNA"):
                supabase.table("yhtiot").insert({"nimi": yn, "y_tunnus": yt, "osoite": yo}).execute()
                st.rerun()
    y_res = supabase.table("yhtiot").select("*").execute()
    for y in y_res.data:
        st.markdown(f'<div class="mobile-card"><b>{y["nimi"]}</b><br>Y-tunnus: {y["y_tunnus"]}</div>', unsafe_allow_html=True)

# --- 10. SIVU: LISÄLAITTEET (TÄYSI REKISTERI) ---
elif st.session_state.sivu == "LISÄLAITTEET":
    st.header("Lisälaiterekisteri")
    k_opts = get_koneiden_nimet()
    with st.expander("LISÄÄ UUSI LISÄLAITE"):
        with st.form("l_form"):
            c1, c2 = st.columns(2)
            ln = c1.text_input("Laitteen nimi")
            lm = c1.text_input("Merkki")
            lma = c1.text_input("Malli")
            lsn = c2.text_input("Valmistenumero")
            lty = c2.selectbox("Tyyppi", ["Kauha", "Aura", "Hiekoitin", "Muu"])
            lk = st.selectbox("Kytke koneeseen", list(k_opts.keys()), format_func=lambda x: k_opts[x])
            l_img = st.file_uploader("Kuva", type=['jpg','png'])
            lkom = st.text_area("Kommentit")
            if st.form_submit_button("TALLENNA LAITE"):
                url = upload_image(l_img, "laite") if l_img else None
                payload = {"nimi": ln, "merkki": lm, "malli": lma, "valmistenumero": lsn, "tyyppi": lty, "kone_id": lk, "kuva_url": url, "kommentti": lkom}
                supabase.table("lisalaitteet").insert(payload).execute()
                st.rerun()
    l_res = supabase.table("lisalaitteet").select("*").execute()
    for l in l_res.data:
        st.markdown(f'<div class="mobile-card"><b>{l["nimi"]}</b><br>Kone: {k_opts.get(l["kone_id"])}<br>SN: {l["valmistenumero"]}</div>', unsafe_allow_html=True)
        if l.get("kuva_url"): st.image(l["kuva_url"], width=200)

# --- 11. SIVU: HISTORIA (TÄYSI LOKI) ---
elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    h_res = supabase.table("huollot").select("*").order("pvm", desc=True).execute()
    kn = get_koneiden_nimet()
    for h in h_res.data:
        st.markdown(f'<div class="mobile-card"><b>{kn.get(h["kone_id"])}</b> - {h["pvm"]}<br><b>{h.get("tyyppi", "")}:</b> {h["kuvaus"]}</div>', unsafe_allow_html=True)

# --- 12. SIVU: VUOSIKELLO (KUITTAUSLOGIIKKA) ---
elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello ja suunnittelu")
    k_opts = get_koneiden_nimet()
    with st.expander("LISÄÄ SUUNNITELTU TAPAHTUMA"):
        with st.form("v_form"):
            vk = st.selectbox("Kone", list(k_opts.keys()), format_func=lambda x: k_opts[x])
            vp = st.date_input("Määräpäivä")
            vt = st.selectbox("Tyyppi", ["Vuosihuolto", "Katsastus", "Tarkastus", "Määräaikaishuolto"])
            vd = st.text_input("Kuvaus")
            if st.form_submit_button("LISÄÄ"):
                supabase.table("aikataulu").insert({"kone_id": vk, "erapaiva": vp.isoformat(), "tyyppi": vt, "kuvaus": vd, "suoritettu": False}).execute()
                st.rerun()
    
    v_res = supabase.table("aikataulu").select("*").eq("suoritettu", False).order("erapaiva").execute()
    for r in v_res.data:
        with st.container():
            st.markdown(f'<div class="mobile-card"><b>{k_opts.get(r["kone_id"])}</b>: {r["erapaiva"]}<br>{r["tyyppi"]} - {r["kuvaus"]}</div>', unsafe_allow_html=True)
            if st.button("KUITTAA TEHDYKSI", key=f"v_{r['id']}"):
                supabase.table("aikataulu").update({"suoritettu": True}).eq("id", r['id']).execute()
                supabase.table("huollot").insert({"kone_id": r['kone_id'], "pvm": date.today().isoformat(), "tyyppi": r['tyyppi'], "kuvaus": f"TEHTY VUOSIKELLOSTA: {r['kuvaus']}"}).execute()
                st.success("Siirretty huoltohistoriaan.")
                st.rerun()

# --- 13. SIVU: URAKAT ---
elif st.session_state.sivu == "URAKAT":
    st.header("Urakat ja Työmaat")
    with st.expander("LISÄÄ UUSI URAKKA"):
        with st.form("u_f"):
            un = st.text_input("Nimi")
            uo = st.text_input("Osoite")
            up = st.text_input("PM")
            uk = st.text_input("KV")
            if st.form_submit_button("TALLENNA"):
                supabase.table("urakat").insert({"nimi": un, "yhteystiedot": uo, "tyopaallikko": up, "kalustovastaava": uk}).execute()
                st.rerun()
    u_res = supabase.table("urakat").select("*").execute()
    for r in u_res.data:
        st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b><br>PM: {r["tyopaallikko"]} | Sijainti: {r["yhteystiedot"]}</div>', unsafe_allow_html=True)