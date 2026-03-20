from config import supabase, BUCKET_NAME
from datetime import datetime

def get_konetyypit():
    res = supabase.table("konetyypit").select("nimi").execute()
    return [r['nimi'] for r in res.data] if res.data else []

def get_lisalaitetyypit():
    res = supabase.table("lisalaitetyypit").select("nimi").execute()
    return [r['nimi'] for r in res.data] if res.data else []

def get_yhtiot():
    res = supabase.table("yhtiot").select("id, nimi").execute()
    d = {0: "Valitse yhtiö / Pimara"}
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

def poista_rivi(taulu, rivi_id):
    supabase.table(taulu).delete().eq("id", rivi_id).execute()

def poista_konetyyppi(nimi):
    supabase.table("konetyypit").delete().eq("nimi", nimi).execute()

def poista_lisalaitetyyppi(nimi):
    supabase.table("lisalaitetyypit").delete().eq("nimi", nimi).execute()