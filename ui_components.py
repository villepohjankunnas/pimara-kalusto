import streamlit as st
import pandas as pd
from datetime import date, timedelta
from config import supabase

def render_kalustokortti(k, y_dict, show_actions=False, task_id=None):
    st.markdown(f'<div class="kortti-header">AJONEUVOKORTTI | {k.get("nimi","")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kortti-banner">{k.get("rekisteri", "EI REK")}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        if k.get("kuva_url"): st.image(k["kuva_url"], use_container_width=True)
        else: st.info("Ei valokuvaa tallennettu.")
        
    with col2:
        st.markdown(f"""
        <table class="tech-table">
            <tr><td class="tech-label">Omistaja</td><td>{y_dict.get(k.get('omistaja_id',0), 'Pimara')}</td></tr>
            <tr><td class="tech-label">Merkki / Malli</td><td>{k.get('merkki','')} {k.get('malli','')}</td></tr>
            <tr><td class="tech-label">Sarjanumero</td><td>{k.get('sarjanumero','')}</td></tr>
            <tr><td class="tech-label">Vuosimalli</td><td>{k.get('vuosimalli','')}</td></tr>
            <tr><td class="tech-label">Teho / Moottori</td><td>{k.get('teho','')} kW / {k.get('moottori','')}</td></tr>
            <tr><td class="tech-label">Pituus / Korkeus</td><td>{k.get('pituus','')} / {k.get('korkeus','')} mm</td></tr>
            <tr><td class="tech-label">Massat (Oma/Kant)</td><td>{k.get('omamassa','')} / {k.get('kantavuus','')} kg</td></tr>
            <tr><td class="tech-label">Katsastus</td><td><b>{k.get('katsastus_pvm','')}</b></td></tr>
        </table>
        """, unsafe_allow_html=True)
        
        if show_actions:
            st.write("---")
            act1, act2 = st.columns(2)
            if act1.button(f"KATSASTETTU", key=f"d_k_{k['id']}_{task_id}"):
                uusi = (date.today() + timedelta(days=365)).strftime("%d.%m.%Y")
                supabase.table("koneet").update({"katsastus_pvm": uusi}).eq("id", k['id']).execute()
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "tyyppi": "Katsastus", "kuvaus": "Määräaikaiskatsastus suoritettu"}).execute()
                st.rerun()
            if act2.button(f"HUOLLETTU", key=f"d_h_{k['id']}_{task_id}"):
                if task_id: supabase.table("aikataulu").update({"suoritettu": True}).eq("id", task_id).execute()
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "tyyppi": "Huolto", "kuvaus": "Huolto kuitattu"}).execute()
                st.rerun()