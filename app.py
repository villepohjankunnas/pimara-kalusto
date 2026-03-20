import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime, date

# --- 1. SUPABASE-ASETUKSET ---
URL = "https://zpyvpqnomoufadcnxqqb.supabase.co"
KEY = "sb_publishable_u9AzUI0N_A80-dVedNPzCg_IT7bkxH4"
supabase: Client = create_client(URL, KEY)
BUCKET_NAME = "pimara-kuvat"

# --- 2. TYYLIT (PIMARA INDUSTRIAL & MOBILE) ---
st.set_page_config(page_title="PIMARA Kalustonhallinta", layout="wide")

def apply_pro_style():
    st.markdown("""
        <style>
        :root { --p-yellow: #ffcc00; --p-dark: #1a1a1a; --p-text: #000000; }
        .stApp { background-color: #ffffff; }
        
        /* Sivupalkki keltaisilla napeilla */
        [data-testid="stSidebar"] { background-color: var(--p-dark) !important; min-width: 280px !important; }
        div.stSidebar [data-testid="stVerticalBlock"] button {
            background-color: var(--p-yellow) !important;
            color: var(--p-text) !important;
            border: none !important;
            border-radius: 0px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            padding: 15px !important;
            margin-bottom: 8px !important;
            width: 100% !important;
        }

        /* Mobiilikortit listauksiin */
        .mobile-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 12px;
            background-color: #fcfcfc;
            border-left: 8px solid var(--p-yellow);
        }

        /* Otsikot responsiivisiksi */
        h1, h2, h3 { color: var(--p-dark); font-weight: 800; text-transform: uppercase; border-left: 10px solid var(--p-yellow); padding-left: 15px; }

        /* Tekninen Taulukko (Kalustokortti) */
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

# --- 4. APUFUNKTIOT ---
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

def upload_image(file, folder_prefix):
    """Lataa kuvan Supabase Storageen ja palauttaa julkisen URL:n"""
    file_extension = file.name.split('.')[-1]
    file_name = f"{folder_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
    file_path = f"uploads/{file_name}"
    
    # Upload to Supabase Storage
    content = file.getvalue()
    supabase.storage.from_(BUCKET_NAME).upload(file_path, content)
    
    # Hae julkinen URL
    return supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)

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

# --- 6. KALUSTOKORTTI-FUNKTIO ---
def render_kalustokortti(k_id):
    res = supabase.table("koneet").select("*").eq("id", k_id).execute()
    if not res.data: return
    k = res.data[0]
    
    st.markdown(f'<div style="background:#1a1a1a; color:#ffcc00; padding:15px; font-weight:900;">AJONEUVOKORTTI | PIMARA</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:#ffcc00; color:black; padding:15px; font-size:1.8rem; font-weight:900;">{k.get("rekisteri", "EI REKISTERIÄ")}</div>', unsafe_allow_html=True)
    
    col_img, col_data = st.columns([1, 1.2])
    with col_img:
        if k.get("kuva_url"):
            st.image(k["kuva_url"], use_container_width=True)
        else:
            st.info("Ei valokuvaa tallennettu.")

    with col_data:
        st.markdown(f"""
        <table class="tech-table">
            <tr><td class="tech-label">Merkki/Malli</td><td>{k.get('merkki', '')} {k.get('malli', '')}</td></tr>
            <tr><td class="tech-label">Sarjanumero</td><td>{k.get('sarjanumero', '')}</td></tr>
            <tr><td class="tech-label">Vuosimalli</td><td>{k.get('vuosimalli', '')}</td></tr>
            <tr><td class="tech-label">Teho (kW) / Moottori</td><td>{k.get('teho', '')} kW / {k.get('moottori', '')}</td></tr>
            <tr><td class="tech-label">Pituus / Korkeus</td><td>{k.get('pituus', '')} / {k.get('korkeus', '')} mm</td></tr>
            <tr><td class="tech-label">Omamassa / Kantavuus</td><td>{k.get('omamassa', '')} / {k.get('kantavuus', '')} kg</td></tr>
            <tr><td class="tech-label">Päästöluokka</td><td>{k.get('paastoluokka', '')}</td></tr>
            <tr><td class="tech-label">Seuraava Katsastus</td><td><b>{k.get('katsastus_pvm', '')}</b></td></tr>
        </table>
        """, unsafe_allow_html=True)

    st.subheader("Kytketyt lisälaitteet")
    l_res = supabase.table("lisalaitteet").select("nimi, tyyppi, merkki").eq("kone_id", k_id).execute()
    if l_res.data:
        st.table(pd.DataFrame(l_res.data))
    else:
        st.caption("Ei kytkettyjä lisälaitteita.")
    
    if st.button("SULJE KALUSTOKORTTI"):
        st.session_state.kortti_id = None
        st.rerun()

# --- 7. SIVUT ---

# --- KONEREKISTERI ---
if st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        render_kalustokortti(st.session_state.kortti_id)
    else:
        st.header("Konerekisteri")
        tyypit = get_konetyypit()
        urakat = get_urakat()
        
        with st.expander("LISÄÄ UUSI KONE (TEKNISET TIEDOT)"):
            with st.form("kone_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                kn = c1.text_input("Koneen tunnus (esim. JKX-577)")
                kt = c1.selectbox("Konetyyppi", tyypit)
                kme = c1.text_input("Merkki")
                kma = c1.text_input("Malli")
                ksn = c1.text_input("Sarjanumero")
                
                kre = c2.text_input("Rekisterinumero")
                kvu = c2.text_input("Vuosimalli")
                kvo = c2.text_input("Käyttövoima")
                kpa = c2.text_input("Päästöluokka")
                kte = c2.text_input("Teho (kW)")
                
                kpi = c3.text_input("Pituus (mm)")
                kko = c3.text_input("Korkeus (mm)")
                kom = c3.text_input("Omamassa (kg)")
                kka = c3.text_input("Kantavuus (kg)")
                kkat = c3.text_input("Katsastus pvm")
                
                kur = st.selectbox("Sijainti / Urakka", list(urakat.keys()), format_func=lambda x: urakat[x])
                k_image = st.file_uploader("Lataa koneen kuva", type=['jpg', 'png', 'jpeg'])
                
                if st.form_submit_button("TALLENNA KONE"):
                    url = upload_image(k_image, "kone") if k_image else None
                    data = {
                        "nimi": kn, "tyyppi": kt, "merkki": kme, "malli": kma, "sarjanumero": ksn,
                        "rekisteri": kre, "vuosimalli": kvu, "kayttovoima": kvo, "paastoluokka": kpa,
                        "teho": kte, "pituus": kpi, "korkeus": kko, "omamassa": kom, "kantavuus": kka,
                        "katsastus_pvm": kkat, "urakka_id": kur, "kuva_url": url, "tila": "Käytössä"
                    }
                    supabase.table("koneet").insert(data).execute()
                    st.rerun()

        # Kalustolistaus (Mobiiliystävälliset kortit)
        res = supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").execute()
        for r in res.data:
            st.markdown(f"""<div class="mobile-card">
                <b>{r['nimi']}</b> ({r['tyyppi']})<br>
                Rekisteri: {r['rekisteri']}
            </div>""", unsafe_allow_html=True)
            if st.button("AVAA KALUSTOKORTTI", key=f"k_{r['id']}"):
                st.session_state.kortti_id = r['id']
                st.rerun()

# --- URAKAT ---
elif st.session_state.sivu == "URAKAT":
    st.header("Urakkahallinta")
    with st.expander("LUO UUSI URAKKA / TYÖMAA"):
        with st.form("u_form"):
            un = st.text_input("Urakan nimi")
            uo = st.text_input("Sijainti / Osoite")
            up = st.text_input("Työmaapäällikkö")
            uk = st.text_input("Kalustovastaava")
            if st.form_submit_button("TALLENNA"):
                supabase.table("urakat").insert({"nimi": un, "yhteystiedot": uo, "tyopaallikko": up, "kalustovastaava": uk}).execute()
                st.rerun()
    res = supabase.table("urakat").select("*").execute()
    for r in res.data:
        st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b><br>PM: {r["tyopaallikko"]}<br>Sijainti: {r["yhteystiedot"]}</div>', unsafe_allow_html=True)

# --- LISÄLAITTEET ---
elif st.session_state.sivu == "LISÄLAITTEET":
    st.header("Lisälaiterekisteri")
    k_opts = get_koneiden_nimet()
    with st.expander("LISÄÄ UUSI LISÄLAITE"):
        with st.form("l_form"):
            ln = st.text_input("Laitteen nimi")
            lme = st.text_input("Merkki")
            lma = st.text_input("Malli")
            lsn = st.text_input("Valmistenumero")
            lty = st.selectbox("Tyyppi", ["Kauha", "Aura", "Hiekoitin", "Muu"])
            lko = st.selectbox("Kytke koneeseen", list(k_opts.keys()), format_func=lambda x: k_opts[x])
            l_image = st.file_uploader("Laitteen kuva", type=['jpg', 'png'])
            if st.form_submit_button("TALLENNA"):
                url = upload_image(l_image, "laite") if l_image else None
                supabase.table("lisalaitteet").insert({"nimi": ln, "merkki": lme, "malli": lma, "valmistenumero": lsn, "tyyppi": lty, "kone_id": lko, "kuva_url": url}).execute()
                st.rerun()
    res = supabase.table("lisalaitteet").select("*").execute()
    for r in res.data:
        st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b> ({r["merkki"]})<br>Kytketty: {k_opts.get(r["kone_id"])}</div>', unsafe_allow_html=True)
        if r.get("kuva_url"): st.image(r["kuva_url"], width=200)

# --- HISTORIA ---
elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    res = supabase.table("huollot").select("pvm, kuvaus, kone_id").order("pvm", desc=True).execute()
    k_nimet = get_koneiden_nimet()
    for r in res.data:
        st.markdown(f'<div class="mobile-card"><b>{k_nimet.get(r["kone_id"])}</b> - {r["pvm"]}<br>{r["kuvaus"]}</div>', unsafe_allow_html=True)

# --- VUOSIKELLO ---
elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello")
    k_opts = get_koneiden_nimet()
    with st.expander("LISÄÄ TAPAHTUMA"):
        with st.form("v_form"):
            vk = st.selectbox("Kone", list(k_opts.keys()), format_func=lambda x: k_opts[x])
            vp = st.date_input("Määräpäivä")
            vt = st.text_input("Tehtävä")
            if st.form_submit_button("LISÄÄ"):
                supabase.table("aikataulu").insert({"kone_id": vk, "erapaiva": vp.isoformat(), "tyyppi": vt, "suoritettu": False}).execute()
                st.rerun()
    res = supabase.table("aikataulu").select("*").eq("suoritettu", False).execute()
    for r in res.data:
        with st.container():
            st.markdown(f'<div class="mobile-card"><b>{k_opts.get(r["kone_id"])}</b>: {r["erapaiva"]}<br>{r["tyyppi"]}</div>', unsafe_allow_html=True)
            if st.button("KUITTAA TEHDYKSI", key=f"v_{r['id']}"):
                supabase.table("aikataulu").update({"suoritettu": True}).eq("id", r['id']).execute()
                supabase.table("huollot").insert({"kone_id": r['kone_id'], "pvm": date.today().isoformat(), "kuvaus": f"Kuitattu vuosikellosta: {r['tyyppi']}"}).execute()
                st.rerun()

# --- TYÖPÖYTÄ ---
elif st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard")
    k_res = supabase.table("koneet").select("id", count="exact").execute()
    l_res = supabase.table("lisalaitteet").select("id", count="exact").execute()
    u_res = supabase.table("urakat").select("id", count="exact").execute()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Koneet", k_res.count if k_res.count else 0)
    c2.metric("Laitteet", l_res.count if l_res.count else 0)
    c3.metric("Urakat", u_res.count if u_res.count else 0)