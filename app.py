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
        }
        </style>
    """, unsafe_allow_html=True)

apply_pro_style()

# --- 3. NAVIGAATION JA STATEN HALLINTA ---
if 'sivu' not in st.session_state: st.session_state.sivu = "TYÖPÖYTÄ"
if 'kortti_id' not in st.session_state: st.session_state.kortti_id = None
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

def vaihda_sivu(nimi):
    st.session_state.sivu = nimi
    st.session_state.kortti_id = None
    st.session_state.edit_id = None

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

# --- 6. KALUSTOKORTTI-FUNKTIO ---
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

# --- 7. SIVU: TYÖPÖYTÄ (HÄLYTYKSET 30 PV) ---
if st.session_state.sivu == "TYÖPÖYTÄ":
    st.header("Dashboard - Tilannekatsaus")
    
    tanaan = date.today()
    raja_pvm = tanaan + timedelta(days=30)
    alertit = []
    
    # Katsastushälytykset
    k_res = supabase.table("koneet").select("id, nimi, katsastus_pvm").execute()
    for k in k_res.data:
        if k['katsastus_pvm']:
            try:
                kpvm = datetime.strptime(k['katsastus_pvm'], "%d.%m.%Y").date()
                if kpvm <= tanaan: alertit.append({"t": "danger", "m": f"KATSASTUS VANHUNUT: {k['nimi']} ({k['katsastus_pvm']})"})
                elif kpvm <= raja_pvm: alertit.append({"t": "warning", "m": f"Katsastus lähestyy: {k['nimi']} ({k['katsastus_pvm']})"})
            except: pass

    # Huoltohälytykset vuosikellosta
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
        st.success("Ei erääntyvää kalustoa tai huoltoja seuraavan 30 päivän aikana.")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    k_tot = supabase.table("koneet").select("id", count="exact").execute().count
    u_tot = supabase.table("urakat").select("id", count="exact").execute().count
    c1.metric("Koneet", k_tot if k_tot else 0)
    c2.metric("Urakat", u_tot if u_tot else 0)
    c3.metric("Lisälaitteet", len(supabase.table("lisalaitteet").select("id").execute().data))

# --- 8. SIVU: KONEREKISTERI (CRUD) ---
elif st.session_state.sivu == "KONEET":
    if st.session_state.kortti_id:
        render_kalustokortti(st.session_state.kortti_id)
    elif st.session_state.edit_id:
        st.header("Muokkaa koneen tietoja")
        c_data = supabase.table("koneet").select("*").eq("id", st.session_state.edit_id).execute().data[0]
        with st.form("edit_kone_form"):
            col1, col2 = st.columns(2)
            enimi = col1.text_input("Tunnus", value=c_data['nimi'])
            merkki = col1.text_input("Merkki", value=c_data.get('merkki',''))
            malli = col1.text_input("Malli", value=c_data.get('malli',''))
            rekkari = col2.text_input("Rekisteri", value=c_data.get('rekisteri',''))
            kats = col2.text_input("Katsastus (pv.kk.vvvv)", value=c_data.get('katsastus_pvm',''))
            if st.form_submit_button("TALLENNA MUUTOKSET"):
                supabase.table("koneet").update({"nimi": enimi, "merkki": merkki, "malli": malli, "rekisteri": rekkari, "katsastus_pvm": kats}).eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
        if st.button("PERUUTA"):
            st.session_state.edit_id = None
            st.rerun()
    else:
        st.header("Konerekisteri")
        with st.expander("LISÄÄ UUSI KONE"):
            with st.form("kone_f", clear_on_submit=True):
                ca, cb, cc = st.columns(3)
                kn = ca.text_input("Tunnus (esim. JKX-577)")
                kt = ca.selectbox("Tyyppi", get_konetyypit())
                ky = ca.selectbox("Omistaja", list(get_yhtiot().keys()), format_func=lambda x: get_yhtiot()[x])
                kme = cb.text_input("Merkki")
                kma = cb.text_input("Malli")
                ksn = cb.text_input("Sarjanumero")
                kre = cc.text_input("Rekisteri")
                kkat = cc.text_input("Katsastus (pv.kk.vvvv)")
                kimg = st.file_uploader("Kuva", type=['jpg','png','jpeg'])
                if st.form_submit_button("TALLENNA"):
                    url = upload_image(kimg, "kone") if kimg else None
                    supabase.table("koneet").insert({"nimi":kn, "tyyppi":kt, "omistaja_id":ky, "merkki":kme, "malli":kma, "sarjanumero":ksn, "rekisteri":kre, "katsastus_pvm":kkat, "kuva_url":url}).execute()
                    st.rerun()

        res = supabase.table("koneet").select("id, nimi, tyyppi, rekisteri").order("nimi").execute()
        for r in res.data:
            with st.container():
                st.markdown(f'<div class="mobile-card"><b>{r["nimi"]}</b> ({r["tyyppi"]})<br>Rek: {r["rekisteri"]}</div>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("KORTTI", key=f"v_{r['id']}"):
                    st.session_state.kortti_id = r['id']
                    st.rerun()
                if c2.button("MUOKKAA", key=f"e_{r['id']}"):
                    st.session_state.edit_id = r['id']
                    st.rerun()
                with c3:
                    with st.popover("POISTA"):
                        if st.button("VAHVISTA POISTO", key=f"del_k_{r['id']}"):
                            supabase.table("koneet").delete().eq("id", r['id']).execute()
                            st.rerun()

# --- 9. SIVU: YHTIÖIDEN HALLINTA (CRUD) ---
elif st.session_state.sivu == "YHTIOT":
    st.header("Konsernin Yhtiöt")
    if st.session_state.edit_id:
        curr = supabase.table("yhtiot").select("*").eq("id", st.session_state.edit_id).execute().data[0]
        with st.form("edit_y"):
            en = st.text_input("Nimi", value=curr['nimi'])
            et = st.text_input("Y-tunnus", value=curr['y_tunnus'])
            if st.form_submit_button("TALLENNA"):
                supabase.table("yhtiot").update({"nimi": en, "y_tunnus": et}).eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
    else:
        with st.expander("LISÄÄ UUSI YHTIÖ"):
            with st.form("y_form"):
                yn = st.text_input("Nimi")
                yt = st.text_input("Y-tunnus")
                if st.form_submit_button("TALLENNA"):
                    supabase.table("yhtiot").insert({"nimi": yn, "y_tunnus": yt}).execute()
                    st.rerun()
        
    y_res = supabase.table("yhtiot").select("*").execute()
    for y in y_res.data:
        st.markdown(f'<div class="mobile-card"><b>{y["nimi"]}</b><br>Y: {y["y_tunnus"]}</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button("MUOKKAA", key=f"ey_{y['id']}"):
            st.session_state.edit_id = y['id']
            st.rerun()
        with col2:
            with st.popover("POISTA"):
                if st.button("VAHVISTA POISTO", key=f"dy_{y['id']}"):
                    supabase.table("yhtiot").delete().eq("id", y['id']).execute()
                    st.rerun()

# --- 10. SIVU: LISÄLAITTEET (CRUD) ---
elif st.session_state.sivu == "LISÄLAITTEET":
    st.header("Lisälaiterekisteri")
    if st.session_state.edit_id:
        curr = supabase.table("lisalaitteet").select("*").eq("id", st.session_state.edit_id).execute().data[0]
        with st.form("el_form"):
            en = st.text_input("Nimi", value=curr['nimi'])
            if st.form_submit_button("TALLENNA"):
                supabase.table("lisalaitteet").update({"nimi": en}).eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
    else:
        with st.expander("LISÄÄ UUSI LISÄLAITE"):
            with st.form("l_form"):
                ln = st.text_input("Nimi")
                lko = st.selectbox("Kone", list(get_koneiden_nimet().keys()), format_func=lambda x: get_koneiden_nimet()[x])
                if st.form_submit_button("TALLENNA"):
                    supabase.table("lisalaitteet").insert({"nimi": ln, "kone_id": lko}).execute()
                    st.rerun()
    
    l_res = supabase.table("lisalaitteet").select("*").execute()
    k_nimet = get_koneiden_nimet()
    for l in l_res.data:
        st.markdown(f'<div class="mobile-card"><b>{l["nimi"]}</b><br>Kytketty: {k_nimet.get(l["kone_id"])}</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button("MUOKKAA", key=f"el_{l['id']}"):
            st.session_state.edit_id = l['id']
            st.rerun()
        with col2:
            with st.popover("POISTA"):
                if st.button("VAHVISTA POISTO", key=f"dl_{l['id']}"):
                    supabase.table("lisalaitteet").delete().eq("id", l['id']).execute()
                    st.rerun()

# --- 11. SIVU: URAKAT (CRUD) ---
elif st.session_state.sivu == "URAKAT":
    st.header("Urakat")
    if st.session_state.edit_id:
        curr = supabase.table("urakat").select("*").eq("id", st.session_state.edit_id).execute().data[0]
        with st.form("eu_form"):
            un = st.text_input("Nimi", value=curr['nimi'])
            if st.form_submit_button("TALLENNA"):
                supabase.table("urakat").update({"nimi": un}).eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
    else:
        with st.expander("LISÄÄ UUSI URAKKA"):
            with st.form("u_form"):
                un = st.text_input("Nimi")
                if st.form_submit_button("TALLENNA"):
                    supabase.table("urakat").insert({"nimi": un}).execute()
                    st.rerun()
                    
    u_res = supabase.table("urakat").select("*").execute()
    for u in u_res.data:
        st.markdown(f'<div class="mobile-card"><b>{u["nimi"]}</b></div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button("MUOKKAA", key=f"eu_{u['id']}"):
            st.session_state.edit_id = u['id']
            st.rerun()
        with col2:
            with st.popover("POISTA"):
                if st.button("VAHVISTA POISTO", key=f"du_{u['id']}"):
                    supabase.table("urakat").delete().eq("id", u['id']).execute()
                    st.rerun()

# --- 12. HUOLTOHISTORIA JA VUOSIKELLO (Samalla logiikalla kuin aiemmin) ---
elif st.session_state.sivu == "HISTORIA":
    st.header("Huoltohistoria")
    h_res = supabase.table("huollot").select("*").order("pvm", desc=True).execute()
    kn = get_koneiden_nimet()
    for h in h_res.data:
        st.markdown(f'<div class="mobile-card"><b>{kn.get(h["kone_id"])}</b> - {h["pvm"]}<br>{h["kuvaus"]}</div>', unsafe_allow_html=True)

elif st.session_state.sivu == "VUOSIKELLO":
    st.header("Vuosikello")
    k_opts = get_koneiden_nimet()
    with st.expander("UUSI TAPAHTUMA"):
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
        if st.button("KUITTAA VALMIIKSI", key=f"v_{r['id']}"):
            supabase.table("aikataulu").update({"suoritettu": True}).eq("id", r['id']).execute()
            supabase.table("huollot").insert({"kone_id": r['kone_id'], "pvm": date.today().isoformat(), "kuvaus": f"Kuitattu: {r['tyyppi']}"}).execute()
            st.rerun()