import os
from datetime import datetime

import streamlit as st
import requests


def _get_setting(key: str, default=None):
    """
    Hakee asetuksen ensisijaisesti Streamlit-secretsista ja varmistaa fallbackilla ympäristömuuttujista.
    """
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # st.secrets ei ole aina saatavilla (esim. paikallinen ajo ilman secretsia)
        pass
    return os.getenv(key, default)


SUPABASE_URL = _get_setting("SUPABASE_URL")
SUPABASE_ANON_KEY = _get_setting("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = _get_setting("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = _get_setting("BUCKET_NAME", "kalustokuvat")


class _SupabaseNotConfigured:
    def __getattr__(self, name):
        raise RuntimeError(
            "Supabasen client ei ole konfiguroitu. "
            "Aseta vähintään `SUPABASE_URL` ja `SUPABASE_ANON_KEY` (Streamlit secrets tai environment)."
        )

class _SupabaseResponse:
    def __init__(self, data):
        self.data = data


def _auth_headers(anon_key: str, bearer_key: str):
    # Supabasen REST (PostgREST / storage) käyttää apikey- ja Authorization-headeria.
    # - apikey: public/anon key
    # - Authorization: Bearer <JWT> / service role key (riippuen operaatiosta)
    return {
        "apikey": anon_key,
        "Authorization": f"Bearer {bearer_key}",
        "Accept": "application/json",
    }


def _guess_mime_from_key(key: str) -> str:
    k = key.lower()
    if k.endswith(".png"):
        return "image/png"
    if k.endswith(".jpg") or k.endswith(".jpeg"):
        return "image/jpeg"
    if k.endswith(".gif"):
        return "image/gif"
    if k.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


class _StorageBucket:
    def __init__(self, client, bucket: str):
        self._client = client
        self._bucket = bucket

    def upload(self, path: str, content_bytes: bytes):
        self._client._require_config()
        url = f"{self._client.supabase_url}/storage/v1/object/{self._bucket}/{path}"

        # Standard upload on multipart/form-data. Kentän nimi voi vaihdella; käytämme oletuksena `file`.
        mime = _guess_mime_from_key(path)
        headers = _auth_headers(self._client.anon_key, self._client.bearer_key_for_write())
        files = {"file": (os.path.basename(path), content_bytes, mime)}
        r = requests.post(url, headers=headers, files=files, timeout=60)
        if not (200 <= r.status_code < 300):
            raise RuntimeError(f"Storage upload epäonnistui: HTTP {r.status_code}: {r.text}")
        try:
            return r.json()
        except Exception:
            return None

    def get_public_url(self, path: str) -> str:
        # Oletus: bucket on public. Jos bucket on private, tämä ei anna toimivaa suoraa URL:ia.
        self._client._require_config()
        return f"{self._client.supabase_url}/storage/v1/object/public/{self._bucket}/{path}"


class _StorageClient:
    def __init__(self, client):
        self._client = client

    def from_(self, bucket: str) -> _StorageBucket:
        return _StorageBucket(self._client, bucket)


class _TableQuery:
    def __init__(self, client, table: str):
        self._client = client
        self._table = table

        self._operation = None  # "select" | "insert" | "update" | "delete"
        self._select_columns = None
        self._payload = None
        self._filters = []  # list[(field, value)]

    def select(self, columns: str):
        self._operation = "select"
        self._select_columns = columns
        return self

    def insert(self, payload: dict):
        self._operation = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict):
        self._operation = "update"
        self._payload = payload
        return self

    def delete(self):
        self._operation = "delete"
        return self

    def eq(self, field: str, value):
        self._filters.append((field, value))
        return self

    def _build_filters(self):
        params = {}
        for field, value in self._filters:
            params[field] = f"eq.{value}"
        return params

    def execute(self):
        self._client._require_config()
        base_url = f"{self._client.supabase_url}/rest/v1/{self._table}"

        headers = {
            **_auth_headers(self._client.anon_key, self._client.bearer_key_for_select()),
            "Content-Type": "application/json",
        }

        # Prefer return=representation on kätevä jos server palauttaa dataa; select palauttaa joka tapauksessa.
        headers["Prefer"] = "return=representation"

        params = self._build_filters()

        if self._operation == "select":
            # Supabase-py käyttää `select`-parametria. PostgREST ei pidä välilyönneistä pilkkujen jälkeen.
            cols = self._select_columns or "*"
            cols = ",".join([c.strip() for c in cols.split(",")]) if cols != "*" else "*"
            params["select"] = cols
            r = requests.get(base_url, headers=headers, params=params, timeout=60)
        elif self._operation == "insert":
            headers["Authorization"] = f"Bearer {self._client.bearer_key_for_write()}"
            r = requests.post(base_url, headers=headers, params=params, json=[self._payload], timeout=60)
        elif self._operation == "update":
            headers["Authorization"] = f"Bearer {self._client.bearer_key_for_write()}"
            r = requests.patch(base_url, headers=headers, params=params, json=self._payload, timeout=60)
        elif self._operation == "delete":
            headers["Authorization"] = f"Bearer {self._client.bearer_key_for_write()}"
            r = requests.delete(base_url, headers=headers, params=params, timeout=60)
        else:
            raise RuntimeError("Tuntematon tauluoperaatio.")

        if not (200 <= r.status_code < 300):
            raise RuntimeError(f"Supabase REST epäonnistui: HTTP {r.status_code}: {r.text}")

        if r.status_code == 204 or not r.content:
            return _SupabaseResponse(None)
        try:
            return _SupabaseResponse(r.json())
        except Exception:
            return _SupabaseResponse(None)


class _SupabaseRestClient:
    def __init__(self, supabase_url: str, anon_key: str, service_role_key: str | None = None):
        self.supabase_url = supabase_url
        self.anon_key = anon_key
        self.service_role_key = service_role_key
        self.storage = _StorageClient(self)

    def _require_config(self):
        if not self.supabase_url or not self.anon_key:
            raise RuntimeError(
                "Supabasen client ei ole konfiguroitu. "
                "Aseta vähintään `SUPABASE_URL` ja `SUPABASE_ANON_KEY` (Streamlit secrets tai environment)."
            )

    def table(self, table: str) -> _TableQuery:
        return _TableQuery(self, table)

    def bearer_key_for_select(self) -> str:
        # Valinnat/selailut tehdään lähtökohtaisesti anon-avaimella.
        return self.anon_key

    def bearer_key_for_write(self) -> str:
        # Jos service role -avain on asetettu, käytetään sitä kirjoituksiin.
        # Muuten käytetään anon-avainta (jolloin RLS voi estää kirjoittamisen).
        return self.service_role_key or self.anon_key


if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = _SupabaseRestClient(SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY)
else:
    supabase = _SupabaseNotConfigured()


def apply_pro_style():
    """Lisää sovelluksen perus-UI tyylit ja sivuasetukset."""
    # Suorittaa ennen muuta UI:ta, jotta asetukset pysyvät yhteensopivina Streamlitin kanssa.
    st.set_page_config(page_title="PIMARA", layout="wide")

    st.markdown(
        """
        <style>
        body { background: #121212; color: #eaeaea; }
        .mobile-card{
            background:#1a1a1a; color:#ffcc00;
            padding:14px; margin:10px 0;
            border-radius:12px;
            border: 1px solid rgba(255,204,0,0.25);
        }
        .tech-table{
            width:100%; border-collapse: collapse;
        }
        .tech-label{
            color:#ffcc00; font-weight:700;
            width:35%; padding:6px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Välimuistetaan listat 10 minuutiksi (600 sekuntia)
@st.cache_data(ttl=600)
def get_konetyypit():
    res = supabase.table("konetyypit").select("nimi").execute()
    return [r['nimi'] for r in res.data] if res.data else []

@st.cache_data(ttl=600)
def get_lisalaitetyypit():
    res = supabase.table("lisalaitetyypit").select("nimi").execute()
    return [r['nimi'] for r in res.data] if res.data else []

@st.cache_data(ttl=600)
def get_yhtiot():
    res = supabase.table("yhtiot").select("id, nimi").execute()
    d = {0: "Pimara"}
    for r in res.data: d[r['id']] = r['nimi']
    return d

@st.cache_data(ttl=600)
def get_urakat():
    res = supabase.table("urakat").select("id, nimi").execute()
    d = {0: "Varasto / Ei määritelty"}
    for r in res.data: d[r['id']] = r['nimi']
    return d

# Koneiden nimet välimuistetaan lyhyemmäksi aikaa (1 min), koska ne muuttuvat usein
@st.cache_data(ttl=60)
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
        # Tyhjennetään välimuisti, jotta uusi kuva näkyy
        st.cache_data.clear()
        return supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
    except: return None

def poista_rivi(taulu, rivi_id):
    supabase.table(taulu).delete().eq("id", rivi_id).execute()
    st.cache_data.clear() # Tyhjennetään välimuisti poiston jälkeen

def poista_konetyyppi(nimi):
    supabase.table("konetyypit").delete().eq("nimi", nimi).execute()
    st.cache_data.clear()