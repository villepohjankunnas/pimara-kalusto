import streamlit as st
import pandas as pd
from datetime import date, timedelta
from config import supabase

def render_kone_kortti(k, y_dict, show_actions=False, task_id=None):
    st.markdown(f'<div class="kortti-header">KALUSTOKORTTI | {k.get("nimi","")}</div>', unsafe_allow_html=True)
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
            <tr><td class="tech-label">S/N</td><td>{k.get('sarjanumero','')}</td></tr>
            <tr><td class="tech-label">Moottori / Teho</td><td>{k.get('moottori','')} / {k.get('teho','')} kW</td></tr>
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
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "tyyppi": "Katsastus", "kuvaus": "Hyväksytty"}).execute()
                st.rerun()
            if act2.button(f"HUOLLETTU", key=f"d_h_{k['id']}_{task_id}"):
                if task_id: supabase.table("aikataulu").update({"suoritettu": True}).eq("id", task_id).execute()
                supabase.table("huollot").insert({"kone_id": k['id'], "pvm": date.today().isoformat(), "tyyppi": "Huolto", "kuvaus": "Määräaikaishuolto suoritettu"}).execute()
                st.rerun()