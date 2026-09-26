import streamlit as st

# ═══════════════════════════════════════════════════════════════════════════
# 🚨🚨🚨 EN KRİTİK KURAL — ASLA İHLAL EDİLMEZ 🚨🚨🚨
# HERHANGİ BİR "Kaydet"/"Sil"/toplu güncelleme işlemi, FİLTRELENMİŞ/DARALTILMIŞ
# bir görünümdeki verilerle o filtrenin DIŞINDA KALAN kayıtların ÜZERİNE
# YAZAMAZ. Bir müşterinin/kaydın TAM listesi HER ZAMAN önce taze (fresh) olarak
# yüklenip, sadece GERÇEKTEN değiştirilen/silinen satırlar o listenin İÇİNDE
# güncellenmeli — asla "görünenlerle tüm listeyi değiştir" mantığı kurulmaz.
# Bu kural 2026'da bir Kargolar sayfası hatası yüzünden 94 kargo kaydının
# kalıcı olarak kaybolmasına neden oldu. BİR DAHA ASLA OLMAYACAK.
# Yeni bir toplu kaydet/sil özelliği yazmadan önce bu yorumu tekrar oku.
#
# 🚨 GENİŞLETME (kullanıcı talimatı): Bu kural SADECE Kargolar'a özel değil,
# SİSTEMİN TAMAMINA (Kargo, Tedarikçi, Müşteri/Cari, ve bundan sonra eklenecek
# HER modül) geçerlidir. YENİ KOD YAZARKEN veya MEVCUT bir özelliği
# GÜNCELLERKEN DAHİ — yani "sadece yeni özellik eklüyorum, eski koda
# dokunmuyorum" denilen durumlarda BİLE — bu kurala aykırı bir kaydetme/silme
# deseni (delete-then-insert, "görünenle tüm listeyi değiştir" vb.) asla
# yazılmaz. Kayıt gerçekten silinecekse bile fiziksel olarak yok edilmez;
# Müşteri (cari_kartlar → "silindi" bayrağı) ve Tedarikçi'de zaten yapıldığı
# gibi "silindi" bayrağıyla işaretlenip listede kalır ve "🗑️ Silinenler"den
# geri alınabilir. Kalıcı/fiziksel silme sadece kullanıcının AÇIK ve TEKİL
# onayıyla (ör. "Silinenler" ekranındaki ayrı "Kalıcı Sil" butonu) yapılabilir.
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 🚨 KALICI KURAL 2 (kullanıcı talimatı, 2026-09): Sistemde HİÇBİR YERDE
# kullanıcıya teknik boşluk göstergesi ("None", "NaN", "nan", "null", "NAT")
# YAZI OLARAK gösterilmeyecek. Kök neden genelde `sozluk.get("alan", "")`
# kalıbının, anahtar SÖZLÜKTE VARSA ama değeri gerçekten None ise varsayılanı
# DEVREYE SOKMAMASIDIR — dict.get'in ikinci parametresi SADECE anahtar hiç
# yokken kullanılır; değer None olsa bile anahtar varsa None döner. `str(None)`
# de "None" metnini üretir ve bu bazen kalıcı olarak veriye yazılabilir (normal
# pd.fillna("") bunu YAKALAYAMAZ, çünkü ortada geçerli bir string vardır,
# NaN/None değil). Yeni kod yazarken: (1) `sozluk.get("alan") or ""` kullan
# (None VE eksik anahtarın ikisini de yakalar), asla sadece
# `sozluk.get("alan", "")` yazma; (2) kullanıcıya gösterilecek HER
# DataFrame'de son adım olarak bu teknik metinleri temizle (bkz.
# `_hic_none_gosterme` yardımcı fonksiyonu, tabloyu render etmeden hemen önce
# çağrılır).
# ═══════════════════════════════════════════════════════════════════════════

# ── İL SÜTUNLARI — GLOBAL sabit (birden fazla sayfadan erişilir: Cari Liste
# tablosunda kolon olarak, Kullanıcılar sayfasındaki Kolon Ayarları'nda genişlik
# ayarı olarak). Tek bir sayfanın içinde tanımlanırsa diğer sayfa NameError alır.
_IL_SUTUN_LISTESI = ["İstanbul","Bursa","İzmir","Manisa","Tekirdağ","Kocaeli","Ankara","Konya",
                     "Denizli","Adana","Gaziantep","Kayseri","Antalya","Aydın","Balıkesir",
                     "Diyarbakır","Erzurum","Eskişehir","Hatay","Kahramanmaraş","Malatya",
                     "Mardin","Mersin","Muğla","Ordu","Sakarya","Samsun","Trabzon","Van",
                     "Şanlıurfa","Diğer"]

# İl sütunu başlıklarının kısaltmaları — GLOBAL (hem Cari Liste tablosundaki
# başlıklarda hem "Rut" otomatik hesaplamasında kullanılır).
_IL_KISA_ETIKET = {"İstanbul":"İst","Bursa":"Brs","İzmir":"İzm","Manisa":"Man","Tekirdağ":"Tek",
                    "Kocaeli":"Koc","Ankara":"Ank","Konya":"Kon","Denizli":"Den","Adana":"Ada",
                    "Gaziantep":"Gaz","Kayseri":"Kay","Antalya":"Ant","Aydın":"Ayd","Balıkesir":"Bal",
                    "Diyarbakır":"Diy","Erzurum":"Erz","Eskişehir":"Esk","Hatay":"Hat","Kahramanmaraş":"Kah",
                    "Malatya":"Mal","Mardin":"Mar","Mersin":"Mrs","Muğla":"Muğ","Ordu":"Ord",
                    "Sakarya":"Sak","Samsun":"Sam","Trabzon":"Tra","Van":"Van","Şanlıurfa":"Şan","Diğer":"Diğ"}


_CL_OZEL_FILTRE_SECENEKLERI = {
    "": "-- Kullanılmıyor --",
    "firma": "Firma",
    "rakip_firma": "Özel (Rakip Firma)",
    "yetkili": "Yetkili",
    "gsm": "GSM",
    "sabit": "Sabit Tel",
    "email": "Email",
    "adres": "Adres",
    "il": "İl",
    "ilce": "İlçe",
    "durum": "Durum",
    "temsilci": "Temsilci",
    "islem_asamasi": "İlk Temas",
    "vergi_no": "Vergi No",
    "vergi_dairesi": "Vergi Dairesi",
    "musteri_subesi": "Müşteri Şubesi",
    "vade": "Vade",
    "odeme": "Ödeme",
    "teklif_fiyat": "Teklif Fiyat",
    "islem_tarihi_manuel": "İşlem Tarihi",
    "takip_tarihi_manuel": "Takip Tarihi",
    "randevu_tarihi_manuel": "Randevu Tarihi",
    "aciklama": "Açıklama",
    "asama1": "1. Aşama",
    "asama2": "2. Aşama",
    "asama3": "3. Aşama",
    "sonuc": "Sonuç",
    "ara_islem": "Ara İşlem",
    "il_ciro_ozet": "İl Ciroları",
    "sektor": "Sektör",
    "rut": "Rut",
}


def _cl_ozel_filtre_alani_yukle():
    """KULLANICI İSTEĞİ (2026-09): Cari Liste'de HANGİ alanın ek bir filtre
    olarak gösterileceği, Kullanıcılar > Kolon Ayarları'ndan seçilebilir
    (örn. 'Yetkili'). Bu ayar kullanici_tercih'te saklanır — dönen değer,
    seçili alanın İÇ ADI (örn. "yetkili") ya da hiç ayarlanmadıysa "" dır."""
    try:
        sb = get_sb_client()
        if not sb:
            return ""
        r = sb.table("kullanici_tercih").select("deger").eq(
            "kullanici", "__liste_ui__").eq("anahtar", "_cl_ozel_filtre_alani").execute()
        if r.data:
            _v = r.data[0]["deger"]
            return _v if _v in _CL_OZEL_FILTRE_SECENEKLERI else ""
        return ""
    except Exception:
        return ""


def _cl_ozel_filtre_alani_kaydet(_alan):
    """GÜVENLİ (bkz. _tedarikci_kaydet ile aynı desen) — SİLME YOK, satır
    varsa UPDATE, yoksa INSERT."""
    try:
        sb = get_sb_client()
        if not sb:
            return False
        _guncelle = sb.table("kullanici_tercih").update({"deger": _alan}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", "_cl_ozel_filtre_alani").execute()
        if not _guncelle.data:
            sb.table("kullanici_tercih").insert({
                "kullanici": "__liste_ui__", "anahtar": "_cl_ozel_filtre_alani", "deger": _alan
            }).execute()
        return True
    except Exception:
        return False



_CARI_EK_ALAN_ANAHTAR = "_cari_ek_bilgiler"
_CARI_EK_ALAN_LISTESI = ["vergi_no", "vergi_dairesi", "musteri_subesi", "vade", "odeme", "teklif_fiyat", "islem_tarihi_manuel", "takip_tarihi_manuel", "randevu_tarihi_manuel", "il_ciro_ozet"]
_CARI_EK_ALAN_ETIKET = {
    "vergi_no": "Vergi No", "vergi_dairesi": "Vergi Dairesi",
    "musteri_subesi": "Müşteri Şubesi", "vade": "Vade", "odeme": "Ödeme",
    "teklif_fiyat": "Teklif Fiyat", "islem_tarihi_manuel": "İşlem Tarihi", "takip_tarihi_manuel": "Takip Tarihi",
    "randevu_tarihi_manuel": "Randevu Tarihi",
    "il_ciro_ozet": "İl Ciroları",
}


def _cari_ek_bilgi_yukle():
    """KULLANICI İSTEĞİ (2026-09): Vergi No / Vergi Dairesi / Müşteri Şubesi /
    Vade / Ödeme alanları cari_kartlar'da GERÇEK birer sütun DEĞİL (proje
    kuralı: yeni SQL migration yok) — Rut ile AYNI desen: mevcut
    kullanici_tercih tablosunda TEK bir JSON blob olarak, {cari_id_str:
    {alan: değer}} şeklinde saklanır."""
    try:
        sb = get_sb_client()
        if not sb:
            return {}
        r = sb.table("kullanici_tercih").select("deger").eq(
            "kullanici", "__liste_ui__").eq("anahtar", _CARI_EK_ALAN_ANAHTAR).execute()
        if r.data:
            return json.loads(r.data[0]["deger"])
        return {}
    except Exception:
        return {}


def _cari_ek_bilgi_kaydet(_sozluk):
    """GÜVENLİ (bkz. _cari_rut_kaydet ile aynı desen) — SİLME YOK, satır
    varsa UPDATE, yoksa INSERT."""
    try:
        sb = get_sb_client()
        if not sb:
            return False
        _deger = json.dumps(_sozluk, ensure_ascii=False)
        _guncelle = sb.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", _CARI_EK_ALAN_ANAHTAR).execute()
        if not _guncelle.data:
            sb.table("kullanici_tercih").insert({
                "kullanici": "__liste_ui__", "anahtar": _CARI_EK_ALAN_ANAHTAR, "deger": _deger
            }).execute()
        return True
    except Exception:
        return False


# ── MÜŞTERİ KODU (MW1, MW2, ...) — KULLANICI İSTEĞİ (2026-09): gerçek
# veritabanı "id"sine (kargo/not/randevu/il gönderim gibi ONLARCA yerde
# kullanılan asıl anahtar) ASLA dokunulmaz — o sabit kalır. Bunun yerine
# SADECE GÖRÜNTÜLEME/REFERANS amaçlı, kayıt tarihine göre sıralı, boşluksuz
# "MW1, MW2, ..." şeklinde AYRI bir kod tutulur (kullanici_tercih'te,
# {cari_id_str: "MW<n>"} olarak). Bir müşteri silinirse, o numara "boşta"
# sayılır ve BİR SONRAKİ yeni müşteriye otomatik verilir (numara tekrar
# kullanılır) — ama bu SADECE bu kozmetik kod içindir, gerçek id etkilenmez.
_MUSTERI_KODU_ANAHTAR = "_musteri_kodu_haritasi"


def _musteri_kodu_yukle():
    try:
        sb = get_sb_client()
        if not sb:
            return {}
        r = sb.table("kullanici_tercih").select("deger").eq(
            "kullanici", "__liste_ui__").eq("anahtar", _MUSTERI_KODU_ANAHTAR).execute()
        if r.data:
            return json.loads(r.data[0]["deger"])
        return {}
    except Exception:
        return {}


def _musteri_kodu_kaydet(_sozluk):
    """GÜVENLİ — SİLME YOK, satır varsa UPDATE, yoksa INSERT."""
    try:
        sb = get_sb_client()
        if not sb:
            return False
        _deger = json.dumps(_sozluk, ensure_ascii=False)
        _guncelle = sb.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", _MUSTERI_KODU_ANAHTAR).execute()
        if not _guncelle.data:
            sb.table("kullanici_tercih").insert({
                "kullanici": "__liste_ui__", "anahtar": _MUSTERI_KODU_ANAHTAR, "deger": _deger
            }).execute()
        return True
    except Exception:
        return False


def _musteri_kodu_yeniden_baslat(_df_tum):
    """KULLANICI İSTEĞİ (2026-09): TÜM (silinmemiş) müşterileri KAYIT
    TARİHİNE göre sıralayıp MW1'den başlayarak boşluksuz yeniden numaralar.
    _df_tum: en az "id" ve "tarih" sütunlu, silinmiş kayıtları İÇERMEYEN
    DataFrame (get_cari_listesi() zaten silindi=1 olanları eledi)."""
    if _df_tum.empty or "id" not in _df_tum.columns:
        return {}
    _siralama_sutunu = "tarih" if "tarih" in _df_tum.columns else "id"
    _sirali = _df_tum.sort_values(by=_siralama_sutunu, na_position="last")
    _yeni_harita = {}
    for _sira_no, (_idx, _satir) in enumerate(_sirali.iterrows(), start=1):
        try:
            _cid = str(int(_satir["id"]))
        except Exception:
            continue
        _yeni_harita[_cid] = f"MW{_sira_no}"
    return _yeni_harita


def _musteri_kodu_sonraki_bul(_harita, _tum_gecerli_idler):
    """Yeni bir müşteri eklendiğinde çağrılır. Silinen (artık "harita"da id'si
    olmayan ama sayısı hâlâ kullanılan) numaraları BULUP boşta olanı
    (en küçük boşluğu) döndürür — yoksa bir sonraki (max+1) numarayı verir."""
    _kullanilan_no = set()
    for _cid_str, _kod in _harita.items():
        if _cid_str in _tum_gecerli_idler and str(_kod or "").startswith("MW"):
            try:
                _kullanilan_no.add(int(str(_kod)[2:]))
            except Exception:
                pass
    if not _kullanilan_no:
        return "MW1"
    _n = 1
    while _n in _kullanilan_no:
        _n += 1
    return f"MW{_n}"


# ── CARİ ARŞİV — KULLANICI İSTEĞİ (2026-09): bazı müşteriler SİLİNMEYECEK
# (veri kaybı yok, "silindi=1" kullanılmaz) ama Cari Ana Liste'de
# VARSAYILAN olarak GÖRÜNMEYECEK — üstteki GENEL/SONUÇ raporlarında ise
# "Kaybedildi" olarak SAYILMAYA devam edecek. Bunun için: (1) müşterinin
# "sonuc" alanı "Kaybedildi" yapılır (gerçek cari_kartlar sütunu, rapor
# sayaçları zaten buna göre sayıyor), (2) AYRICA id'si bu arşiv haritasına
# eklenir — Cari Liste, "Arşivi Göster" açık olmadıkça bu id'leri listeden
# gizler (ama get_cari_listesi() ve dolayısıyla raporlar bunları GÖRMEYE
# devam eder, sadece EKRANDAKİ liste onları göstermez).
_CARI_ARSIV_ANAHTAR = "_cari_arsiv_idler"


def _cari_arsiv_yukle():
    try:
        sb = get_sb_client()
        if not sb:
            return set()
        r = sb.table("kullanici_tercih").select("deger").eq(
            "kullanici", "__liste_ui__").eq("anahtar", _CARI_ARSIV_ANAHTAR).execute()
        if r.data:
            return set(json.loads(r.data[0]["deger"]))
        return set()
    except Exception:
        return set()


def _cari_arsiv_kaydet(_id_seti):
    """GÜVENLİ — SİLME YOK, satır varsa UPDATE, yoksa INSERT."""
    try:
        sb = get_sb_client()
        if not sb:
            return False
        _deger = json.dumps(sorted(_id_seti))
        _guncelle = sb.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", _CARI_ARSIV_ANAHTAR).execute()
        if not _guncelle.data:
            sb.table("kullanici_tercih").insert({
                "kullanici": "__liste_ui__", "anahtar": _CARI_ARSIV_ANAHTAR, "deger": _deger
            }).execute()
        return True
    except Exception:
        return False


@st.dialog("📦 Arşiv — Gizlenen Müşteriler", width="large")
def _cari_arsiv_goruntule_dialog():
    """Ana Cari Liste'de gizlenen (ama SİLİNMEYEN) müşterileri gösterir.
    Buradan 'Geri Al' ile müşteri Cari Liste'ye anında geri döner.
    KALICI BAYRAK deseni (bkz. not_dialog) — pencere içinde bir işlem
    (Geri Al) yapılıp sayfa yenilense bile, "❌ Kapat"a basılana kadar
    açık kalır."""
    _ars_idler = _cari_arsiv_yukle()
    if not _ars_idler:
        st.info("📦 Arşivde hiç müşteri yok.")
    else:
        try:
            _df_tum_ars = get_cari_listesi()
            _df_ars = _df_tum_ars[_df_tum_ars["id"].astype(str).isin(_ars_idler)]
            st.caption(f"Arşivde **{len(_df_ars)}** müşteri var. Cari Liste'ye geri döndürmek için ilgili satırın yanındaki butona bas.")
            for _idx, _row in _df_ars.iterrows():
                _c1, _c2 = st.columns([5, 1.6])
                with _c1:
                    st.write(f"**{_row.get('firma','')}** — {_row.get('il','')}/{_row.get('ilce','')} — 📞 {_row.get('gsm','') or _row.get('sabit','')}")
                with _c2:
                    if st.button("↩️ Geri Al", key=f"ars_geri_al_{_row['id']}", use_container_width=True):
                        _ars_yeni = _cari_arsiv_yukle()
                        _ars_yeni.discard(str(int(_row["id"])))
                        _cari_arsiv_kaydet(_ars_yeni)
                        get_cari_listesi.clear()
                        st.toast(f"↩️ '{_row.get('firma','')}' arşivden çıkarıldı, Cari Liste'de tekrar görünecek", icon="↩️")
                        st.rerun()
        except Exception as _arsg:
            st.error(f"Arşiv yüklenemedi: {_arsg}")
    st.divider()
    if st.button("❌ Kapat", key="ars_kapat_btn", use_container_width=True):
        st.session_state["_cl_arsiv_penceresi_acik"] = False
        st.rerun()


def _fy_il_ciro_parse(_metin):
    """Ortak ayrıştırma: 'Fiyat İncele' metninden {il: toplam} sözlüğü çıkarır.
    Hem _fy_il_ciro_ozet_cikar hem _fy_il_ciro_genel_toplam bunu kullanır —
    böylece İl Ciroları metni ile Hedeflenen Ciro HER ZAMAN aynı veriden,
    birbirinden asla farklı olmayacak şekilde hesaplanır.
    🚨 DÜZELTME (2026-09): eskiden "İL TOPLAM CİRO" alt toplamına (bir
    satırda İKİNCİ 'TL' değeri, sadece grubun İLK satırında bulunur) itimat
    ediliyordu — ama aynı il metin içinde birden fazla AYRI blokta geçerse
    (ör. sonradan tekrar ayrıştırma/ekleme yapıldıysa) bu, İKİLETME riski
    taşıyordu (kullanıcı bunu fark etti). ARTIK bu alt toplama HİÇ
    güvenilmiyor — HER SATIRIN KENDİ TOPLAM'ı (satırdaki İLK 'TL' değeri)
    tek tek alınıp aynı ile ait TÜM satırlar toplanıyor. Bu yöntem, Excel'de
    her satırı elle toplamakla BİREBİR aynı, hataya yer bırakmayan sonucu
    verir — hangi düzende/kaç kez tekrar etmiş olursa olsun."""
    import re as _fyre3
    _sonuc = {}
    _fy_haric_kelimeler = {"ARA", "GENEL", "VARIŞ", "---", "V.İLİ"}
    for _satir in str(_metin or "").split("\n"):
        _tllar = _fyre3.findall(r'([\d.]+)\s*TL', _satir)
        if len(_tllar) < 1:
            continue
        _parcalar = _satir.strip().split()
        if not _parcalar:
            continue
        _sehir = _parcalar[0]
        # NOT: hariç tutma kontrolü SADECE karşılaştırma için basit .upper()
        # kullanır (bu kelimelerde Türkçe İ/ı karışıklığı yok) — SAKLANAN
        # şehir adı ORİJİNAL haliyle (İ/ı dahil) bırakılır, yoksa aşağıdaki
        # _oncelik_sira ("İSTANBUL" vb.) ile eşleşme bozulurdu.
        if _sehir.upper() in _fy_haric_kelimeler:
            continue
        try:
            _tutar = float(_tllar[0])  # satırın KENDİ toplamı — HER ZAMAN ilk TL
        except Exception:
            continue
        _sonuc[_sehir] = _sonuc.get(_sehir, 0.0) + _tutar
    return _sonuc


def _fy_il_ciro_genel_toplam(_metin):
    """KULLANICI İSTEĞİ (2026-09): Hedeflenen Ciro, İl Ciroları'ndaki GENEL
    TOPLAM ile HER ZAMAN birebir aynı olmalı — bu yüzden İKİSİ DE aynı
    _fy_il_ciro_parse'tan hesaplanır. Koli/Palet her kaydedildiğinde bu
    fonksiyon çağrılıp Hedeflenen Ciro (beklenen_ciro) GÜNCELLENİR.
    🚨 GÜVENLİK (2026-09): metin HİÇ eşleşmezse (format tanınmıyorsa, ör.
    kullanıcı sade bir not yazdıysa) None döner — 0 DEĞİL — çağıran taraf
    bunu "güncelleme, elleme" olarak yorumlar. Aksi halde, biri Koli/Palet'e
    rastgele bir şey yazınca mevcut Hedeflenen Ciro yanlışlıkla SIFIRLANIRDI."""
    try:
        _sonuc = _fy_il_ciro_parse(_metin)
        if not _sonuc:
            return None
        return round(sum(_sonuc.values()), 2)
    except Exception:
        return None


def _fy_il_ciro_ozet_cikar(_metin):
    """KULLANICI İSTEĞİ (2026-09, GÜNCELLENDİ): 'Fiyat İncele' metninden
    (Koli/Palet alanı, _fy_format_tablo'nun ürettiği format), her ilin İL
    TOPLAM CİROSUNU (bir satırda İKİNCİ 'TL' değeri) çıkarır. Çıktı yapısı:
    1) Başlık satırı ("VARIŞ İLİ  CİRO") + ayraç.
    2) ÖNCELİKLİ iller (varsa, SABİT sırayla): İstanbul, İzmir, Bursa,
       Manisa, Tekirdağ, Kocaeli + bunların ARA TOPLAMI.
    3) Diğer TÜM iller (cirosu en yüksekten en düşüğe sıralı) + onların da
       ARA TOPLAMI.
    4) İkisinin toplamı olan GENEL TOPLAM.
    HİZALAMA: her satır, EN UZUN il/etiket ismine göre sabit genişlikte
    sola yaslanır (ljust) — tutar hep aynı sütunda başlar, alt alta gelir.
    Format eşleşmezse (elle çok değiştirilmiş metin gibi) boş döner — hata
    fırlatmaz."""
    try:
        _sonuc = _fy_il_ciro_parse(_metin)
        return _fy_il_ciro_ozet_formatla(_sonuc)
    except Exception:
        return ""


def _fy_il_ciro_ozet_formatla(_sonuc):
    """Ortak formatlama: {il: tutar} sözlüğünden hizalı 'İl Ciroları' metni
    üretir (öncelikli iller + Ara Toplam, diğer iller + Ara Toplam, GENEL
    TOPLAM). Hem _fy_il_ciro_ozet_cikar (metinden) hem
    _fy_il_ciro_ozet_girislerden (yapılandırılmış veriden) bunu kullanır."""
    if not _sonuc:
        return ""
    _oncelik_sira = ["İSTANBUL", "İZMİR", "BURSA", "MANİSA", "TEKİRDAĞ", "KOCAELİ"]
    _oncelikli = [(_ad, _sonuc[_ad]) for _ad in _oncelik_sira if _ad in _sonuc]
    _oncelik_toplam = sum(t for _, t in _oncelikli)
    _diger = sorted([(k, v) for k, v in _sonuc.items() if k not in _oncelik_sira], key=lambda x: -x[1])
    _diger_toplam = sum(t for _, t in _diger)
    _genel_toplam = _oncelik_toplam + _diger_toplam
    _tum_etiketler = [a for a, _ in _oncelikli] + (["Ara Toplam"] if _oncelikli else []) + \
                      [a for a, _ in _diger] + (["Ara Toplam"] if _diger else []) + \
                      ["GENEL TOPLAM", "VARIŞ İLİ"]
    _genislik = max(len(a) for a in _tum_etiketler)

    def _icy_fmt(_il, _tutar):
        return f"{_il.ljust(_genislik)}  {_tutar:,.0f}".replace(",", ".")

    _satirlar = [f"{'VARIŞ İLİ'.ljust(_genislik)}  CİRO", "-" * (_genislik + 10)]
    for _ad, _t in _oncelikli:
        _satirlar.append(_icy_fmt(_ad, _t))
    if _oncelikli:
        _satirlar.append(_icy_fmt("Ara Toplam", _oncelik_toplam))
        _satirlar.append("---")
    for _ad, _t in _diger:
        _satirlar.append(_icy_fmt(_ad, _t))
    if _diger:
        _satirlar.append(_icy_fmt("Ara Toplam", _diger_toplam))
        _satirlar.append("")
    _satirlar.append(_icy_fmt("GENEL TOPLAM", _genel_toplam))
    return "\n".join(_satirlar)


def _fy_il_ciro_ozet_girislerden(_girisler):
    """🚨 KRİTİK DÜZELTME (2026-09): "Hedeflenen Ciro" ile "İl Ciroları" bazı
    satırlarda (3 sayı içeren, ör. 'İSTANBUL 15 300 4.200') FARKLI sayılardan
    hesaplanıyordu — Hedef SON sayıyı (_g[5], hedef_katkisi) alırken, "Fiyat
    İncele" tablosundaki TOPLAM sütunu (ve dolayısıyla ondan metin-ayrıştırma
    ile hesaplanan İl Ciroları) İKİNCİ sayıyı (_g[4], toplam) gösteriyordu.
    Bu fonksiyon, İl Ciroları'nı DOĞRUDAN yapılandırılmış _girisler'den,
    Hedef'in kullandığı AYNI alanla (_g[5]) hesaplar — böylece ikisi HER
    ZAMAN birebir aynı olur, metin ayrıştırma riski de tamamen ortadan
    kalkar. _girisler: (sehir, tur, desi, ikinci_sayi, toplam, hedef_katkisi)
    tuple'larının listesi (bkz. 'Ayrıştır ve Hazırla' akışı)."""
    try:
        _sonuc = {}
        for _g in _girisler:
            _sehir = str(_g[0] or "").strip()
            if not _sehir:
                continue
            _sonuc[_sehir] = _sonuc.get(_sehir, 0.0) + float(_g[5])
        return _fy_il_ciro_ozet_formatla(_sonuc)
    except Exception:
        return ""


def _fy_teklif_onerisi_hesapla(_girisler):
    """🆕 YENİ ÖZELLİK (2026-09, KULLANICI İSTEĞİ) — eski hiçbir formata
    (Fiyat İncele, İl Ciroları, Hedeflenen Ciro) DOKUNMAZ, tamamen EK bir
    hesaplama. Aynı müşterinin KENDİ geçmiş fiyat girişlerinden (_girisler:
    (sehir, tur, desi, ikinci_sayi, toplam, hedef_katkisi) tuple listesi),
    her il için "TOPLAM ÷ DESİ" (desi başına TL) oranını hesaplar — basit
    bir ORTALAMA değil, o ilde EN SIK TEKRAR EDEN (moda) oranı bulur, çünkü
    kullanıcı "ortalama yakın değil, en çok tekrar eden" istedi. Desi=0 olan
    (KOLİ gibi sabit fiyatlı) satırlar için oran hesaplanamayacağından, o
    satırların KENDİSİNDE en sık tekrar eden SABİT tutar bulunur. Sonuç,
    "İL: ~X,XX TL/desi (N/M kayıttan)" biçiminde, İL BAŞINA TEK SATIR halinde
    (az satırda) döndürülür — "Teklif Fiyat" alanına yazılmak üzere."""
    from collections import defaultdict, Counter
    try:
        _il_oranlari = defaultdict(list)
        _il_sabitler = defaultdict(list)
        for _g in _girisler:
            _sehir = str(_g[0] or "").strip()
            if not _sehir:
                continue
            try:
                _desi = float(_g[2])
                _toplam = float(_g[4])
            except Exception:
                continue
            if _desi > 0:
                _il_oranlari[_sehir].append(round(_toplam / _desi, 2))
            else:
                _il_sabitler[_sehir].append(_toplam)

        # KULLANICI İSTEĞİ (2026-09): şehir isimleri farklı uzunlukta olduğu
        # için ":" ve rakamlar hizasız, "çorba gibi" görünüyordu. Artık EN
        # UZUN şehir ismine göre sabit genişlikte hizalanıyor (İl Ciroları
        # ve Detaylı Barem Bazlı Teklif ile AYNI okunabilirlik standardı).
        _tum_iller_sirali = sorted(set(list(_il_oranlari.keys()) + list(_il_sabitler.keys())))
        if not _tum_iller_sirali:
            return ""
        _il_genislik = max(len(_il) for _il in _tum_iller_sirali)

        _sonuc_satirlari = []
        for _il in _tum_iller_sirali:
            _il_hizali = _il.ljust(_il_genislik)
            if _il_oranlari.get(_il):
                _sayac = Counter(_il_oranlari[_il])
                _en_sik_oran, _adet = _sayac.most_common(1)[0]
                _sonuc_satirlari.append(f"{_il_hizali} : ~{_en_sik_oran:.2f} TL/desi ({_adet}/{len(_il_oranlari[_il])} kayıttan)")
            elif _il_sabitler.get(_il):
                _sayac2 = Counter(_il_sabitler[_il])
                _en_sik_sabit, _adet2 = _sayac2.most_common(1)[0]
                _sonuc_satirlari.append(f"{_il_hizali} : ~{_en_sik_sabit:,.0f} TL sabit ({_adet2}/{len(_il_sabitler[_il])} kayıttan)".replace(",", "."))
        return "\n".join(_sonuc_satirlari)
    except Exception:
        return ""


def _fy_desi_baremli_teklif_hesapla(_girisler):
    """🆕 YENİ ÖZELLİK (2026-09, KULLANICI İSTEĞİ, GÜNCELLENDİ) — her il için
    KOLİ'de 100 desi'ye kadar sabit BAREMLER (30, 50, 75, 100), PALET'te
    101-1000 desi arası sabit BAREMLER (330, 500, 750, 1000) belirlenir.
    Her geçmiş kayıt EN YAKIN barem'e atanır (İL BAZLI). Bir barem'e SADECE
    1 kayıt düşerse fiyatı/desisi AYNEN yazılır; BİRDEN FAZLA düşerse
    İKİSİNİN DE (hem fiyat hem desi) ORTALAMASI yazılır — barem numarası
    değil, kayıtların GERÇEK desi ortalaması gösterilir.
    🚨 DÜZELTME: desi=0 kayıtlar artık İKİYE ayrılıyor —
      - fiyatı 1000 TL'YE KADARSA: gerçekten sabit fiyatlı kabul edilir,
        kendi TÜRÜ altında (desi belirtilmeden) ayrı gösterilir.
      - fiyatı 1000 TL'DEN FAZLAYSA: desisi unutulmuş BÜYÜK bir gönderim
        kabul edilip PALET'in EN DÜŞÜK baremine (330) dahil edilir — ama
        kendi desisi bilinmediği için o baremin desi ORTALAMASINA katılmaz
        (sadece fiyat ortalamasına katkı sağlar, gerçek desisi olan diğer
        kayıtlarla karışmaz)."""
    from collections import defaultdict
    _KOLI_BAREMLER = [30, 50, 75, 100]
    _PALET_BAREMLER = [330, 500, 750, 1000]

    def _tr_para(_v):
        # Türkçe para biçimi: binlik ayraç nokta, ondalık ayraç virgül (ör. 1.962,50)
        return f"{_v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    try:
        # (tür, barem) -> [(desi_ya_da_None, fiyat), ...]
        _il_barem_gruplari = defaultdict(lambda: defaultdict(list))
        _il_sabit_gruplari = defaultdict(lambda: defaultdict(list))
        for _g in _girisler:
            _il = str(_g[0] or "").strip()
            if not _il:
                continue
            _tur = str(_g[1] or "KOLİ").strip().upper() or "KOLİ"
            try:
                _desi = float(_g[2])
                _toplam = float(_g[4])
            except Exception:
                continue
            if _desi <= 0 and _toplam > 1000:
                # Desisi kaydedilmemiş ama fiyatı yüksek — büyük (palet)
                # gönderim kabul edilip PALET'in en düşük baremine dahil
                # edilir; desi ortalamasına KATILMAZ (None).
                _il_barem_gruplari[_il][("PALET", 330)].append((None, _toplam))
            elif _desi <= 0:
                _il_sabit_gruplari[_il][_tur].append(_toplam)
            elif _desi <= 100:
                _en_yakin = min(_KOLI_BAREMLER, key=lambda b: abs(b - _desi))
                _il_barem_gruplari[_il][("KOLİ", _en_yakin)].append((_desi, _toplam))
            else:
                _en_yakin = min(_PALET_BAREMLER, key=lambda b: abs(b - _desi))
                _il_barem_gruplari[_il][("PALET", _en_yakin)].append((_desi, _toplam))

        _sonuc = {}
        for _il in sorted(set(list(_il_barem_gruplari.keys()) + list(_il_sabit_gruplari.keys()))):
            _satir_ciftleri = []
            if _il in _il_sabit_gruplari:
                for _tur in sorted(_il_sabit_gruplari[_il].keys()):
                    _fiyatlar = _il_sabit_gruplari[_il][_tur]
                    _deger = _fiyatlar[0] if len(_fiyatlar) == 1 else sum(_fiyatlar) / len(_fiyatlar)
                    _satir_ciftleri.append((f"{_tur} 0 DESİ", f"{_tr_para(_deger)} TL"))
            for _tur_ad, _barem_sirasi in [("KOLİ", _KOLI_BAREMLER), ("PALET", _PALET_BAREMLER)]:
                for _barem in _barem_sirasi:
                    _key = (_tur_ad, _barem)
                    if _il in _il_barem_gruplari and _key in _il_barem_gruplari[_il]:
                        _cift = _il_barem_gruplari[_il][_key]
                        _fiyatlar = [f for _, f in _cift]
                        _desiler = [d for d, _ in _cift if d is not None]
                        _fiyat_ort = _fiyatlar[0] if len(_fiyatlar) == 1 else sum(_fiyatlar) / len(_fiyatlar)
                        # KULLANICI İSTEĞİ: barem NUMARASI değil, GERÇEK desi
                        # ortalaması gösterilir (fiyat ortalaması gibi).
                        _desi_ort = (_desiler[0] if len(_desiler) == 1 else sum(_desiler) / len(_desiler)) if _desiler else _barem
                        _satir_ciftleri.append((f"{_tur_ad} {_desi_ort:.0f} DESİ", f"{_tr_para(_fiyat_ort)} TL"))
            if _satir_ciftleri:
                _genislik = max(len(e) for e, _ in _satir_ciftleri)
                _sonuc[_il] = "\n".join(f"{_e.ljust(_genislik)}   {_f}" for _e, _f in _satir_ciftleri)
        return _sonuc
    except Exception:
        return {}


def _fy_hepsini_yerlestir_ana_tablo(cari_id, ham_metin, firma_adi=""):
    """🆕 YENİ ÖZELLİK (2026-09, KULLANICI İSTEĞİ): Cari Liste'nin ANA
    tablosundaki "Fiyatlandırma" hücresine yazılan veriden, "Seç" penceresindeki
    "🎯 Hepsini Yerleştir" ile AYNI 6 işlemi (Ayrıştır + İl İşaretleme +
    Hedeflenen Ciro + İl Ciroları + Teklif Fiyat + Koli/Palet kaydet) yapar —
    SEÇSİZ, tek tabloda hızlı toplu giriş için. 🚨 KRİTİK: bu fonksiyon "Seç"
    penceresindeki (not_dialog içindeki) mevcut koda HİÇ DOKUNMAZ, dokunmadan
    AYNI mantığı BAĞIMSIZ olarak burada tekrarlar — "Seç" akışı bu fonksiyon
    var olmasaydı da, silinse de birebir aynı çalışmaya devam eder.
    KULLANICI İSTEĞİ: yeni veri ESKİNİN ÜZERİNE YAZAR (birleştirmez) —
    "Hepsini Yerleştir" ile birebir aynı davranış.
    Dönüş: (basarili: bool, mesaj: str)"""
    import re as _fyat_re

    def _fyat_norm(_s):
        return (str(_s or "").strip().upper().replace("İ", "I").replace("Ş", "S")
                .replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C"))

    def _fyat_sayi_parse(_metin):
        _sfy = str(_metin).strip()
        if "," in _sfy and "." in _sfy:
            _sfy = _sfy.replace(".", "").replace(",", ".")
        elif "," in _sfy:
            _sfy = _sfy.replace(",", ".")
        elif "." in _sfy:
            _nokta_sonrasi = _sfy.split(".")[-1]
            if len(_nokta_sonrasi) == 3 and _nokta_sonrasi.isdigit():
                _sfy = _sfy.replace(".", "")
        try:
            return float(_sfy)
        except Exception:
            return 0.0

    try:
        if not str(ham_metin or "").strip():
            return False, "Fiyatlandırma hücresi boş."

        _fyat_tum_iller = _IL_SUTUN_LISTESI[:-1] + _IL_DIGER_LISTESI
        _fyat_il_norm_map = {_fyat_norm(a): a.upper() for a in _fyat_tum_iller}
        _fyat_il_kanonik_map = {_fyat_norm(a): a for a in _fyat_tum_iller}
        _fyat_iller_bulunan_set = set()
        _fyat_girisler = []
        _fyat_son_sehir = None
        for _satir_ham in str(ham_metin).strip().split("\n"):
            _s = _satir_ham.strip()
            if not _s:
                continue
            _s_norm = _fyat_norm(_s)
            if "SEHIRICI" in _s_norm:
                _s_norm = _s_norm.replace("SEHIRICI", "ISTANBUL")
            _sehir_bulundu = None
            for _il_norm_fy, _il_ad_fy in _fyat_il_norm_map.items():
                if _il_norm_fy in _s_norm:
                    _sehir_bulundu = _il_ad_fy
                    break
            if _sehir_bulundu:
                _fy_kanonik_bulunan = _fyat_il_kanonik_map.get(_fyat_norm(_sehir_bulundu))
                if _fy_kanonik_bulunan:
                    _fyat_iller_bulunan_set.add(_fy_kanonik_bulunan)
            if _sehir_bulundu:
                if "\t" in _s:
                    _sehir_ham_fy = _s.split("\t")[0].strip()
                else:
                    _m_sehir_ham_fy = _fyat_re.match(r"^(\D+)", _s)
                    _sehir_ham_fy = _m_sehir_ham_fy.group(1).strip() if _m_sehir_ham_fy else ""
                _sehir_ham_fy_norm = _fyat_norm(_sehir_ham_fy)
                if _sehir_bulundu == "İSTANBUL" and (
                        "ANADOLU" in _sehir_ham_fy_norm or "AVRUPA" in _sehir_ham_fy_norm or "VARUPA" in _sehir_ham_fy_norm):
                    _fyat_son_sehir = "İSTANBUL"
                else:
                    _fyat_son_sehir = _tr_buyuk(_sehir_ham_fy) if _sehir_ham_fy else _sehir_bulundu
            _sehir = _fyat_son_sehir
            if not _sehir:
                continue
            _tum_sayi_m = _fyat_re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?", _s)
            if len(_tum_sayi_m) < 2:
                continue
            try:
                _desi = int(round(_fyat_sayi_parse(_tum_sayi_m[0])))
                _ikinci_sayi = _fyat_sayi_parse(_tum_sayi_m[1])
            except Exception:
                continue
            _toplam = round(_ikinci_sayi, 2)
            _hedef_katkisi = _fyat_sayi_parse(_tum_sayi_m[-1])
            _tip = "KOLİ" if _desi <= 100 else "PALET"
            _fyat_girisler.append((_sehir, _tip, _desi, _ikinci_sayi, _toplam, _hedef_katkisi))

        if not _fyat_girisler:
            return False, "Yazılan metinde tanınan bir il ismi + desi + birim fiyat bulunamadı."

        _fyat_sira_liste = [_fyat_norm(a) for a in _IL_SUTUN_LISTESI[:-1]] + [_fyat_norm(a) for a in _IL_DIGER_LISTESI]
        def _fyat_sira_no(_giris):
            _sehir_metni_norm = _fyat_norm(_giris[0])
            for _i_fy, _il_fy_norm in enumerate(_fyat_sira_liste):
                if _il_fy_norm in _sehir_metni_norm:
                    return _i_fy
            return 999
        _fyat_girisler.sort(key=lambda g: (_fyat_sira_no(g), g[2]))

        # ── Fiyat İncele tablosu (_fy_format_tablo ile BİREBİR aynı format) ──
        def _fyat_format_tablo(_girisler):
            if not _girisler:
                return ""
            _sehir_w = max(len("V.İLİ"), max(len(g[0]) for g in _girisler))
            _tur_metinleri = [f"- {g[1]}" for g in _girisler]
            _tur_w = max(len("TÜR"), max(len(t) for t in _tur_metinleri))
            _desi_sayi_w = max(len(str(g[2])) for g in _girisler)
            _desi_metinleri = [f"{str(g[2]).rjust(_desi_sayi_w)} DESİ -KG" for g in _girisler]
            _desi_w = max(len("DESİ-KG"), max(len(t) for t in _desi_metinleri))
            _toplam_metinleri = [f"{g[4]:.2f}" for g in _girisler]
            _toplam_sayi_w = max(len(t) for t in _toplam_metinleri)
            _toplam_metinleri = [f"{t.rjust(_toplam_sayi_w)} TL" for t in _toplam_metinleri]
            _toplam_w = max(len("TOPLAM"), max(len(t) for t in _toplam_metinleri))
            _il_toplam_ciro_map = {}
            for _g in _girisler:
                _il_anahtar_norm = _fyat_norm(_g[0])
                _il_toplam_ciro_map[_il_anahtar_norm] = _il_toplam_ciro_map.get(_il_anahtar_norm, 0.0) + _g[4]
            _il_ciro_metinleri = []
            _gosterilen_iller = set()
            for _g in _girisler:
                _il_anahtar_norm = _fyat_norm(_g[0])
                if _il_anahtar_norm not in _gosterilen_iller:
                    _il_ciro_metinleri.append(f"{_il_toplam_ciro_map[_il_anahtar_norm]:.2f} TL")
                    _gosterilen_iller.add(_il_anahtar_norm)
                else:
                    _il_ciro_metinleri.append("")
            _il_ciro_w = max([len("İL TOPLAM CİRO")] + [len(t) for t in _il_ciro_metinleri])
            _baslik = (f"{'V.İLİ'.ljust(_sehir_w)}   {'TÜR'.ljust(_tur_w)}   {'DESİ-KG'.ljust(_desi_w)}   "
                       f"{'TOPLAM'.ljust(_toplam_w)}   {'İL TOPLAM CİRO'.ljust(_il_ciro_w)}")
            _ayrac = "-" * len(_baslik)
            _satirlar = ["FİYAT İNCELE", _ayrac, "", _baslik, _ayrac]
            _onceki_sehir = None
            for _i, _g in enumerate(_girisler):
                if _onceki_sehir is not None and _fyat_norm(_g[0]) != _fyat_norm(_onceki_sehir):
                    _satirlar.append(_ayrac)
                _satirlar.append(f"{_g[0].ljust(_sehir_w)}   {_tur_metinleri[_i].ljust(_tur_w)}   {_desi_metinleri[_i].ljust(_desi_w)}   "
                                  f"{_toplam_metinleri[_i].ljust(_toplam_w)}   {_il_ciro_metinleri[_i].ljust(_il_ciro_w)}")
                _onceki_sehir = _g[0]
            return "\n".join(_satirlar)

        _fyat_tablo_metni = _fyat_format_tablo(_fyat_girisler)

        # ── Hedeflenen Ciro ──
        _fyat_hedef_toplam = round(sum(_g[5] for _g in _fyat_girisler), 2)
        db_update("cari_kartlar", {"beklenen_ciro": _fyat_hedef_toplam}, "id", int(cari_id))
        try: db_read.clear()
        except Exception: pass
        try: get_cari_listesi.clear()
        except Exception: pass

        # ── İl Ciroları (Hedef ile AYNI kaynaktan, _g[5]) ──
        try:
            _fyat_icy_ozet = _fy_il_ciro_ozet_girislerden(_fyat_girisler)
            _fyat_icy_harita = _cari_ek_bilgi_yukle()
            _fyat_icy_harita.setdefault(str(int(cari_id)), {})["il_ciro_ozet"] = _fyat_icy_ozet
            _cari_ek_bilgi_kaydet(_fyat_icy_harita)
        except Exception:
            pass

        # ── İlleri İşaretle (Varış İlleri matrisine) ──
        _fyat_il_isaretlenen = []
        try:
            _fyat_tum_matris = dict(_il_gonderim_matrisi_yukle())
            _fyat_id_str = str(int(cari_id))
            _fyat_tum_matris.setdefault(_fyat_id_str, {})
            for _fyat_il_bulunan in _fyat_iller_bulunan_set:
                if _fyat_il_bulunan in _IL_SUTUN_LISTESI and _fyat_il_bulunan != "Diğer":
                    if not str(_fyat_tum_matris[_fyat_id_str].get(_fyat_il_bulunan, "")).strip():
                        _fyat_tum_matris[_fyat_id_str][_fyat_il_bulunan] = _fyat_il_bulunan.upper()
                    _fyat_il_isaretlenen.append(_fyat_il_bulunan)
                elif _fyat_il_bulunan in _IL_DIGER_LISTESI:
                    _mevcut_diger_fy = str(_fyat_tum_matris[_fyat_id_str].get("Diğer", "") or "").strip()
                    _diger_satirlari_fy = [s.strip() for s in _mevcut_diger_fy.split("\n") if s.strip()]
                    if _fyat_il_bulunan.upper() not in _diger_satirlari_fy:
                        _diger_satirlari_fy.append(_fyat_il_bulunan.upper())
                    _fyat_tum_matris[_fyat_id_str]["Diğer"] = "\n".join(_diger_satirlari_fy)
                    _fyat_il_isaretlenen.append(_fyat_il_bulunan)
            _il_gonderim_matrisi_kaydet(_fyat_tum_matris)
            _il_gonderim_matrisi_yukle.clear()
        except Exception:
            pass

        # ── Teklif Fiyat (basit TL/desi özeti + detaylı barem kırılımı) ──
        try:
            _fyat_teklif_onerisi = _fy_teklif_onerisi_hesapla(_fyat_girisler)
            _fyat_barem_detay = _fy_desi_baremli_teklif_hesapla(_fyat_girisler)
            _fyat_teklif_parcalari = []
            if _fyat_teklif_onerisi:
                _fyat_teklif_parcalari.append(_fyat_teklif_onerisi)
            if _fyat_barem_detay:
                _fyat_teklif_parcalari.append("--- Detaylı Barem Bazlı Teklif ---")
                for _fyat_il_ad in sorted(_fyat_barem_detay.keys()):
                    _fyat_teklif_parcalari.append(f"\n{_fyat_il_ad}:")
                    _fyat_teklif_parcalari.append(_fyat_barem_detay[_fyat_il_ad])
            _fyat_teklif_tam = "\n".join(_fyat_teklif_parcalari)
            if _fyat_teklif_tam.strip():
                _fyat_tf_harita = _cari_ek_bilgi_yukle()
                _fyat_tf_harita.setdefault(str(int(cari_id)), {})["teklif_fiyat"] = _fyat_teklif_tam
                _cari_ek_bilgi_kaydet(_fyat_tf_harita)
        except Exception:
            pass

        # ── Koli/Palet KAYDET — KULLANICI İSTEĞİ: eskinin ÜZERİNE YAZAR
        # (birleştirmez), "Hepsini Yerleştir" ile birebir aynı davranış.
        _sb_fyat = get_sb_client()
        if _sb_fyat:
            import json as _fyatj
            _r_fyat = _sb_fyat.table("kullanici_tercih").select("deger").eq(
                "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
            _kp_map_fyat = _fyatj.loads(_r_fyat.data[0]["deger"]) if _r_fyat.data else {}
            _kp_map_fyat[str(int(cari_id))] = _fyat_tablo_metni
            _kpo_deger_fyat = _fyatj.dumps(_kp_map_fyat, ensure_ascii=False)
            _kpo_guncelle_fyat = _sb_fyat.table("kullanici_tercih").update({"deger": _kpo_deger_fyat}).eq(
                "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
            if not _kpo_guncelle_fyat.data:
                _sb_fyat.table("kullanici_tercih").insert({
                    "kullanici": "__liste_ui__", "anahtar": "_koli_palet_manuel", "deger": _kpo_deger_fyat
                }).execute()
            st.session_state["_koli_palet_manuel"] = _kp_map_fyat
        get_cari_listesi.clear()

        _mesaj = f"✅ {firma_adi or cari_id}: Hedef Ciro {_kg_tr_format(_fyat_hedef_toplam)} ₺"
        if _fyat_il_isaretlenen:
            _mesaj += f", işaretlenen iller: {', '.join(_fyat_il_isaretlenen)}"
        return True, _mesaj
    except Exception as _fyat_hata:
        return False, f"Hata: {_fyat_hata}"


def _alt_ilerleme_cubugu_html(_yuzde, _mesaj):
    """KULLANICI İSTEĞİ (2026-09): kaydetme gibi işlemler sürerken, ekranın
    ALT kısmında sabit, küçük ve şık bir ilerleme çubuğu — % arttıkça
    BEYAZ'dan SARI'ya, SARI'dan YEŞİL'e geçiş yapar."""
    _y = max(0, min(100, _yuzde))
    if _y <= 50:
        _o = _y / 50.0
        _r = round(255 + (250 - 255) * _o); _g = round(255 + (204 - 255) * _o); _b = round(255 + (21 - 255) * _o)
    else:
        _o = (_y - 50) / 50.0
        _r = round(250 + (34 - 250) * _o); _g = round(204 + (197 - 204) * _o); _b = round(21 + (94 - 21) * _o)
    _renk = f"rgb({_r},{_g},{_b})"
    return f"""
<div style='position:fixed;bottom:0;left:0;right:0;z-index:99999;background:#ffffff;
            padding:8px 18px;box-shadow:0 -3px 10px rgba(0,0,0,0.10);
            border-top:1px solid #e5e7eb;font-family:inherit;'>
  <div style='display:flex;align-items:center;gap:12px;font-size:12px;color:#374151;'>
    <span style='white-space:nowrap;'>⏳ {_mesaj}</span>
    <div style='flex:1;height:9px;background:#f1f5f9;border-radius:5px;overflow:hidden;'>
      <div style='width:{_y}%;height:100%;background:{_renk};transition:width 0.25s ease;border-radius:5px;'></div>
    </div>
    <span style='white-space:nowrap;font-weight:600;'>%{int(_y)}</span>
  </div>
</div>
"""



def _cari_rut_hesapla_otomatik(_cari_id, _il_matrisi):
    """KULLANICI İSTEĞİ (2026-09): "Rut" artık elle yazılmıyor — o müşterinin
    hangi İL sütun(lar)ına gönderim bilgisi girildiğine bakılarak OTOMATİK
    hesaplanır. Sadece DOLU olan iller (sütun sırasına göre) kısaltılıp
    " - " ile birleştirilir (örn. "İST - BRS - ANK"). _il_matrisi,
    _il_gonderim_matrisi_yukle()'den gelen {cari_id_str: {il_adi: değer}}
    sözlüğüdür.
    "Diğer" sütunu (30 ana ilin dışındaki iller için serbest metin) ÖZEL:
    tek bir sabit "DİĞ" kısaltması KULLANILMAZ — içine yazılan HER il adı
    kendi başına (virgül/eğik çizgi/satır sonu/çoklu boşlukla ayrılmış
    parçalar halinde) ayrı ayrı kısaltılıp Rut'a eklenir (ör. içine
    "Kırklareli, Çorum" yazılmışsa "KIR - ÇOR" olarak eklenir)."""
    try:
        if _cari_id is None or (isinstance(_cari_id, float) and pd.isna(_cari_id)):
            return ""
        _kayit_il = _il_matrisi.get(str(int(_cari_id)), {}) or {}
    except Exception:
        return ""
    _kisaltmalar = []
    for _il_kol in _IL_SUTUN_LISTESI:
        _deger = str(_kayit_il.get(_il_kol, "") or "").strip()
        if not _deger:
            continue
        if _il_kol == "Diğer":
            _parcalar = [p.strip() for p in re.split(r"[,/\n]+|\s{2,}", _deger) if p.strip()]
            if not _parcalar:
                _parcalar = [_deger]
            for _p in _parcalar:
                _kisaltmalar.append(_tr_buyuk(_p)[:3])
        else:
            _kisaltmalar.append(_IL_KISA_ETIKET.get(_il_kol, _il_kol[:3]).upper())
    return " - ".join(_kisaltmalar)


def _fy_tablo_olustur_global(_girisler):
    """Kargo Girişi dialog'undaki fiyat tablosu formatlayıcısıyla (_fy_format_tablo)
    AYNI mantık — GLOBAL bir kopyası, eski (BİRİM FİYAT'lı, "FİYAT İNCELE"
    başlıksız) 'Koli/Palet' metinlerini toplu olarak yeni formata çevirebilmek
    için burada tutuluyor. _girisler: [(sehir, tur, desi, toplam), ...]."""
    if not _girisler:
        return ""
    _sehir_w = max(len("V.İLİ"), max(len(g[0]) for g in _girisler))
    _tur_metinleri = [f"- {g[1]}" for g in _girisler]
    _tur_w = max(len("TÜR"), max(len(t) for t in _tur_metinleri))
    _desi_sayi_w = max(len(str(g[2])) for g in _girisler)
    _desi_metinleri = [f"{str(g[2]).rjust(_desi_sayi_w)} DESİ -KG" for g in _girisler]
    _desi_w = max(len("DESİ-KG"), max(len(t) for t in _desi_metinleri))
    _toplam_metinleri = [f"{g[3]:.2f}" for g in _girisler]
    _toplam_sayi_w = max(len(t) for t in _toplam_metinleri)
    _toplam_metinleri = [f"{t.rjust(_toplam_sayi_w)} TL" for t in _toplam_metinleri]
    _toplam_w = max(len("TOPLAM"), max(len(t) for t in _toplam_metinleri))
    _baslik = (f"{'V.İLİ'.ljust(_sehir_w)}   {'TÜR'.ljust(_tur_w)}   {'DESİ-KG'.ljust(_desi_w)}   "
               f"{'TOPLAM'.ljust(_toplam_w)}")
    _ayrac = "-" * len(_baslik)
    _satirlar = ["FİYAT İNCELE", _ayrac, "", _baslik, _ayrac]
    _onceki_sehir = None
    for _i, _g in enumerate(_girisler):
        if _onceki_sehir is not None and _g[0] != _onceki_sehir:
            _satirlar.append(_ayrac)
        _satirlar.append(f"{_g[0].ljust(_sehir_w)}   {_tur_metinleri[_i].ljust(_tur_w)}   {_desi_metinleri[_i].ljust(_desi_w)}   "
                          f"{_toplam_metinleri[_i].ljust(_toplam_w)}")
        _onceki_sehir = _g[0]
    return "\n".join(_satirlar)


import re as _fy_re_erken

@st.cache_data(ttl=300, show_spinner=False)
def _tum_musteri_kargo_yekun_toplami():
    """KULLANICI İSTEĞİ (2026-09): Cari Liste'deki 'Gerçekleşen Ciro' artık
    HER MÜŞTERİ İÇİN, o müşterinin TÜM (silinmemiş) kargo kayıtlarındaki
    Yekün (B.Tutar × Adet) toplamından CANLI hesaplanır — {cari_id: toplam}.
    Eskiden bu alan, her kargo ekle/düzenle/sil işleminde elle artırılıp
    azaltılan bir SAYAÇ idi (_cari_gerceklesen_ciro_ekle); zamanla küçük
    hatalar/atlanan durumlar birikip gerçek toplamdan (bazen abartılı
    şekilde) sapabiliyordu. Bu fonksiyon hiçbir sayaca güvenmez, HER
    SEFERİNDE kargo kayıtlarının kendisinden taze toplar — asla yanlış
    bir sayı biriktiremez."""
    try:
        sb = get_sb_client()
        if not sb:
            return {}
        _tum_satirlar = []
        _offset = 0
        while True:
            _r = sb.table("kullanici_tercih").select("anahtar,deger").eq(
                "kullanici", "__liste_ui__").like("anahtar", "_kargo_kayitlari_%").range(
                _offset, _offset + 999).execute()
            _batch = _r.data or []
            _tum_satirlar.extend(_batch)
            if len(_batch) < 1000:
                break
            _offset += 1000
        _toplamlar = {}
        for _row in _tum_satirlar:
            try:
                _cid = int(str(_row["anahtar"]).replace("_kargo_kayitlari_", ""))
            except Exception:
                continue
            try:
                _liste = json.loads(_row["deger"])
            except Exception:
                _liste = []
            _toplam = _toplamlar.get(_cid, 0.0)
            _gorulmus_kayitlar = set()
            for _kayit in _liste:
                if _kayit.get("silindi"):
                    continue
                # BİREBİR MÜKERRER (Kargolar sayfasındaki "🔁 Mükerrer" ile
                # AYNI tanım: tüm alanları birebir aynı) kayıtlar SADECE BİR
                # KEZ sayılır — aksi halde yanlışlıkla iki kez girilmiş/
                # yüklenmiş bir kayıt, toplamı gereksiz yere şişirir.
                try:
                    _mukerrer_anahtar = tuple(sorted(
                        (k, str(v)) for k, v in _kayit.items() if k != "silindi"))
                except Exception:
                    _mukerrer_anahtar = None
                if _mukerrer_anahtar is not None:
                    if _mukerrer_anahtar in _gorulmus_kayitlar:
                        continue
                    _gorulmus_kayitlar.add(_mukerrer_anahtar)
                try:
                    _toplam += float(_kayit.get("yekun", 0) or 0)
                except Exception:
                    pass
            _toplamlar[_cid] = _toplam
        return _toplamlar
    except Exception:
        return {}

# "Diğer" başlığının altına, alt alta yazılacak iller (başlığı olmayan 50 il).
# "Varış İlleri" hızlı-girişinde bu illerden biri yazılırsa "Diğer" sütununa,
# üstteki 30 il de kendi sütununa gider.
_IL_DIGER_LISTESI = ["Adıyaman","Afyonkarahisar","Ağrı","Aksaray","Amasya","Ardahan","Artvin",
                     "Bartın","Batman","Bayburt","Bilecik","Bingöl","Bitlis","Bolu","Burdur",
                     "Çanakkale","Çankırı","Çorum","Düzce","Edirne","Elazığ","Erzincan",
                     "Giresun","Gümüşhane","Hakkari","Iğdır","Isparta","Karabük","Karaman",
                     "Kars","Kastamonu","Kırıkkale","Kırklareli","Kırşehir","Kilis","Kütahya",
                     "Muş","Nevşehir","Niğde","Osmaniye","Rize","Siirt","Sinop","Sivas",
                     "Şırnak","Tokat","Tunceli","Uşak","Yalova","Yozgat","Zonguldak"]

# İl seçilince ilçe açılır listesinin dolması için kullanılıyor.
# Kaynak: NVI/resmi il-ilçe listesi (81 il, 973 ilçe).
_IL_ILCE_HARITASI = {
    "Adana": ["Aladağ", "Ceyhan", "Feke", "Karaisalı", "Karataş", "Kozan", "Pozantı", "Saimbeyli", "Sarıçam", "Seyhan", "Tufanbeyli", "Yumurtalık", "Yüreğir", "Çukurova", "İmamoğlu"],
    "Adıyaman": ["Merkez", "Besni", "Gerger", "Gölbaşı", "Kahta", "Samsat", "Sincik", "Tut", "Çelikhan"],
    "Afyonkarahisar": ["Merkez", "Bayat", "Başmakçı", "Bolvadin", "Dazkırı", "Dinar", "Emirdağ", "Evciler", "Hocalar", "Kızılören", "Sandıklı", "Sinanpaşa", "Sultandağı", "Çay", "Çobanlar", "İhsaniye", "İscehisar", "Şuhut"],
    "Aksaray": ["Merkez", "Ağaçören", "Eskil", "Gülağaç", "Güzelyurt", "Ortaköy", "Sarıyahşi", "Sultanhanı"],
    "Amasya": ["Merkez", "Göynücek", "Gümüşhacıköy", "Hamamözü", "Merzifon", "Suluova", "Taşova"],
    "Ankara": ["Akyurt", "Altındağ", "Ayaş", "Bala", "Beypazarı", "Elmadağ", "Etimesgut", "Evren", "Gölbaşı", "Güdül", "Haymana", "Kahramankazan", "Kalecik", "Keçiören", "Kızılcahamam", "Mamak", "Nallıhan", "Polatlı", "Pursaklar", "Sincan", "Yenimahalle", "Çamlıdere", "Çankaya", "Çubuk", "Şereflikoçhisar"],
    "Antalya": ["Akseki", "Aksu", "Alanya", "Demre", "Döşemealtı", "Elmalı", "Finike", "Gazipaşa", "Gündoğmuş", "Kaş", "Kemer", "Kepez", "Konyaaltı", "Korkuteli", "Kumluca", "Manavgat", "Muratpaşa", "Serik", "İbradı"],
    "Ardahan": ["Merkez", "Damal", "Göle", "Hanak", "Posof", "Çıldır"],
    "Artvin": ["Merkez", "Ardanuç", "Arhavi", "Borçka", "Hopa", "Kemalpaşa", "Murgul", "Yusufeli", "Şavşat"],
    "Aydın": ["Bozdoğan", "Buharkent", "Didim", "Efeler", "Germencik", "Karacasu", "Karpuzlu", "Koçarlı", "Kuyucak", "Kuşadası", "Köşk", "Nazilli", "Sultanhisar", "Söke", "Yenipazar", "Çine", "İncirliova"],
    "Ağrı": ["Merkez", "Diyadin", "Doğubayazıt", "Eleşkirt", "Hamur", "Patnos", "Taşlıçay", "Tutak"],
    "Balıkesir": ["Altıeylül", "Ayvalık", "Balya", "Bandırma", "Bigadiç", "Burhaniye", "Dursunbey", "Edremit", "Erdek", "Gömeç", "Gönen", "Havran", "Karesi", "Kepsut", "Manyas", "Marmara", "Savaştepe", "Susurluk", "Sındırgı", "İvrindi"],
    "Bartın": ["Merkez", "Amasra", "Kurucaşile", "Ulus"],
    "Batman": ["Merkez", "Beşiri", "Gercüş", "Hasankeyf", "Kozluk", "Sason"],
    "Bayburt": ["Merkez", "Aydıntepe", "Demirözü"],
    "Bilecik": ["Merkez", "Bozüyük", "Gölpazarı", "Osmaneli", "Pazaryeri", "Söğüt", "Yenipazar", "İnhisar"],
    "Bingöl": ["Merkez", "Adaklı", "Genç", "Karlıova", "Kiğı", "Solhan", "Yayladere", "Yedisu"],
    "Bitlis": ["Merkez", "Adilcevaz", "Ahlat", "Güroymak", "Hizan", "Mutki", "Tatvan"],
    "Bolu": ["Merkez", "Dörtdivan", "Gerede", "Göynük", "Kıbrıscık", "Mengen", "Mudurnu", "Seben", "Yeniçağa"],
    "Burdur": ["Merkez", "Altınyayla", "Ağlasun", "Bucak", "Gölhisar", "Karamanlı", "Kemer", "Tefenni", "Yeşilova", "Çavdır", "Çeltikçi"],
    "Bursa": ["Büyükorhan", "Gemlik", "Gürsu", "Harmancık", "Karacabey", "Keles", "Kestel", "Mudanya", "Mustafakemalpaşa", "Nilüfer", "Orhaneli", "Orhangazi", "Osmangazi", "Yenişehir", "Yıldırım", "İnegöl", "İznik"],
    "Denizli": ["Acıpayam", "Babadağ", "Baklan", "Bekilli", "Beyağaç", "Bozkurt", "Buldan", "Güney", "Honaz", "Kale", "Merkezefendi", "Pamukkale", "Sarayköy", "Serinhisar", "Tavas", "Çal", "Çameli", "Çardak", "Çivril"],
    "Diyarbakır": ["Bağlar", "Bismil", "Dicle", "Ergani", "Eğil", "Hani", "Hazro", "Kayapınar", "Kocaköy", "Kulp", "Lice", "Silvan", "Sur", "Yenişehir", "Çermik", "Çüngüş", "Çınar"],
    "Düzce": ["Merkez", "Akçakoca", "Cumayeri", "Gölyaka", "Gümüşova", "Kaynaşlı", "Yığılca", "Çilimli"],
    "Edirne": ["Merkez", "Enez", "Havsa", "Keşan", "Lalapaşa", "Meriç", "Süloğlu", "Uzunköprü", "İpsala"],
    "Elazığ": ["Merkez", "Alacakaya", "Arıcak", "Ağın", "Baskil", "Karakoçan", "Keban", "Kovancılar", "Maden", "Palu", "Sivrice"],
    "Erzincan": ["Merkez", "Kemah", "Kemaliye", "Otlukbeli", "Refahiye", "Tercan", "Çayırlı", "Üzümlü", "İliç"],
    "Erzurum": ["Aziziye", "Aşkale", "Horasan", "Hınıs", "Karayazı", "Karaçoban", "Köprüköy", "Narman", "Oltu", "Olur", "Palandöken", "Pasinler", "Pazaryolu", "Tekman", "Tortum", "Uzundere", "Yakutiye", "Çat", "İspir", "Şenkaya"],
    "Eskişehir": ["Alpu", "Beylikova", "Günyüzü", "Han", "Mahmudiye", "Mihalgazi", "Mihalıççık", "Odunpazarı", "Sarıcakaya", "Seyitgazi", "Sivrihisar", "Tepebaşı", "Çifteler", "İnönü"],
    "Gaziantep": ["Araban", "Karkamış", "Nizip", "Nurdağı", "Oğuzeli", "Yavuzeli", "İslahiye", "Şahinbey", "Şehitkamil"],
    "Giresun": ["Merkez", "Alucra", "Bulancak", "Dereli", "Doğankent", "Espiye", "Eynesil", "Görele", "Güce", "Keşap", "Piraziz", "Tirebolu", "Yağlıdere", "Çamoluk", "Çanakçı", "Şebinkarahisar"],
    "Gümüşhane": ["Merkez", "Kelkit", "Köse", "Kürtün", "Torul", "Şiran"],
    "Hakkari": ["Merkez", "Derecik", "Yüksekova", "Çukurca", "Şemdinli"],
    "Hatay": ["Altınözü", "Antakya", "Arsuz", "Belen", "Defne", "Dörtyol", "Erzin", "Hassa", "Kumlu", "Kırıkhan", "Payas", "Reyhanlı", "Samandağ", "Yayladağı", "İskenderun"],
    "Isparta": ["Merkez", "Aksu", "Atabey", "Eğirdir", "Gelendost", "Gönen", "Keçiborlu", "Senirkent", "Sütçüler", "Uluborlu", "Yalvaç", "Yenişarbademli", "Şarkikaraağaç"],
    "Iğdır": ["Merkez", "Aralık", "Karakoyunlu", "Tuzluca"],
    "Kahramanmaraş": ["Afşin", "Andırın", "Dulkadiroğlu", "Ekinözü", "Elbistan", "Göksun", "Nurhak", "Onikişubat", "Pazarcık", "Türkoğlu", "Çağlayancerit"],
    "Karabük": ["Merkez", "Eflani", "Eskipazar", "Ovacık", "Safranbolu", "Yenice"],
    "Karaman": ["Merkez", "Ayrancı", "Başyayla", "Ermenek", "Kazımkarabekir", "Sarıveliler"],
    "Kars": ["Merkez", "Akyaka", "Arpaçay", "Digor", "Kağızman", "Sarıkamış", "Selim", "Susuz"],
    "Kastamonu": ["Merkez", "Abana", "Araç", "Azdavay", "Ağlı", "Bozkurt", "Cide", "Daday", "Devrekani", "Doğanyurt", "Hanönü", "Küre", "Pınarbaşı", "Seydiler", "Taşköprü", "Tosya", "Çatalzeytin", "İhsangazi", "İnebolu", "Şenpazar"],
    "Kayseri": ["Akkışla", "Bünyan", "Develi", "Felahiye", "Hacılar", "Kocasinan", "Melikgazi", "Pınarbaşı", "Sarıoğlan", "Sarız", "Talas", "Tomarza", "Yahyalı", "Yeşilhisar", "Özvatan", "İncesu"],
    "Kilis": ["Merkez", "Elbeyli", "Musabeyli", "Polateli"],
    "Kocaeli": ["Başiskele", "Darıca", "Derince", "Dilovası", "Gebze", "Gölcük", "Kandıra", "Karamürsel", "Kartepe", "Körfez", "Çayırova", "İzmit"],
    "Konya": ["Ahırlı", "Akören", "Akşehir", "Altınekin", "Beyşehir", "Bozkır", "Cihanbeyli", "Derbent", "Derebucak", "Doğanhisar", "Emirgazi", "Ereğli", "Güneysınır", "Hadim", "Halkapınar", "Hüyük", "Ilgın", "Kadınhanı", "Karapınar", "Karatay", "Kulu", "Meram", "Sarayönü", "Selçuklu", "Seydişehir", "Taşkent", "Tuzlukçu", "Yalıhüyük", "Yunak", "Çeltik", "Çumra"],
    "Kütahya": ["Merkez", "Altıntaş", "Aslanapa", "Domaniç", "Dumlupınar", "Emet", "Gediz", "Hisarcık", "Pazarlar", "Simav", "Tavşanlı", "Çavdarhisar", "Şaphane"],
    "Kırklareli": ["Merkez", "Babaeski", "Demirköy", "Kofçaz", "Lüleburgaz", "Pehlivanköy", "Pınarhisar", "Vize"],
    "Kırıkkale": ["Merkez", "Bahşili", "Balışeyh", "Delice", "Karakeçili", "Keskin", "Sulakyurt", "Yahşihan", "Çelebi"],
    "Kırşehir": ["Merkez", "Akpınar", "Akçakent", "Boztepe", "Kaman", "Mucur", "Çiçekdağı"],
    "Malatya": ["Akçadağ", "Arapgir", "Arguvan", "Battalgazi", "Darende", "Doğanyol", "Doğanşehir", "Hekimhan", "Kale", "Kuluncak", "Pütürge", "Yazıhan", "Yeşilyurt"],
    "Manisa": ["Ahmetli", "Akhisar", "Alaşehir", "Demirci", "Gölmarmara", "Gördes", "Kula", "Köprübaşı", "Kırkağaç", "Salihli", "Saruhanlı", "Sarıgöl", "Selendi", "Soma", "Turgutlu", "Yunusemre", "Şehzadeler"],
    "Mardin": ["Artuklu", "Dargeçit", "Derik", "Kızıltepe", "Mazıdağı", "Midyat", "Nusaybin", "Savur", "Yeşilli", "Ömerli"],
    "Mersin": ["Akdeniz", "Anamur", "Aydıncık", "Bozyazı", "Erdemli", "Gülnar", "Mezitli", "Mut", "Silifke", "Tarsus", "Toroslar", "Yenişehir", "Çamlıyayla"],
    "Muğla": ["Bodrum", "Dalaman", "Datça", "Fethiye", "Kavaklıdere", "Köyceğiz", "Marmaris", "Menteşe", "Milas", "Ortaca", "Seydikemer", "Ula", "Yatağan"],
    "Muş": ["Merkez", "Bulanık", "Hasköy", "Korkut", "Malazgirt", "Varto"],
    "Nevşehir": ["Merkez", "Acıgöl", "Avanos", "Derinkuyu", "Gülşehir", "Hacıbektaş", "Kozaklı", "Ürgüp"],
    "Niğde": ["Merkez", "Altunhisar", "Bor", "Ulukışla", "Çamardı", "Çiftlik"],
    "Ordu": ["Akkuş", "Altınordu", "Aybastı", "Fatsa", "Gölköy", "Gülyalı", "Gürgentepe", "Kabadüz", "Kabataş", "Korgan", "Kumru", "Mesudiye", "Perşembe", "Ulubey", "Çamaş", "Çatalpınar", "Çaybaşı", "Ünye", "İkizce"],
    "Osmaniye": ["Merkez", "Bahçe", "Düziçi", "Hasanbeyli", "Kadirli", "Sumbas", "Toprakkale"],
    "Rize": ["Merkez", "Ardeşen", "Derepazarı", "Fındıklı", "Güneysu", "Hemşin", "Kalkandere", "Pazar", "Çamlıhemşin", "Çayeli", "İkizdere", "İyidere"],
    "Sakarya": ["Adapazarı", "Akyazı", "Arifiye", "Erenler", "Ferizli", "Geyve", "Hendek", "Karapürçek", "Karasu", "Kaynarca", "Kocaali", "Pamukova", "Sapanca", "Serdivan", "Söğütlü", "Taraklı"],
    "Samsun": ["19 mayıs", "Alaçam", "Asarcık", "Atakum", "Ayvacık", "Bafra", "Canik", "Havza", "Kavak", "Ladik", "Salıpazarı", "Tekkeköy", "Terme", "Vezirköprü", "Yakakent", "Çarşamba", "İlkadım"],
    "Siirt": ["Merkez", "Baykan", "Eruh", "Kurtalan", "Pervari", "Tillo", "Şirvan"],
    "Sinop": ["Merkez", "Ayancık", "Boyabat", "Dikmen", "Durağan", "Erfelek", "Gerze", "Saraydüzü", "Türkeli"],
    "Sivas": ["Merkez", "Akıncılar", "Altınyayla", "Divriği", "Doğanşar", "Gemerek", "Gölova", "Gürün", "Hafik", "Kangal", "Koyulhisar", "Suşehri", "Ulaş", "Yıldızeli", "Zara", "İmranlı", "Şarkışla"],
    "Tekirdağ": ["Ergene", "Hayrabolu", "Kapaklı", "Malkara", "Marmaraereğlisi", "Muratlı", "Saray", "Süleymanpaşa", "Çerkezköy", "Çorlu", "Şarköy"],
    "Tokat": ["Merkez", "Almus", "Artova", "Başçiftlik", "Erbaa", "Niksar", "Pazar", "Reşadiye", "Sulusaray", "Turhal", "Yeşilyurt", "Zile"],
    "Trabzon": ["Akçaabat", "Araklı", "Arsin", "Beşikdüzü", "Dernekpazarı", "Düzköy", "Hayrat", "Köprübaşı", "Maçka", "Of", "Ortahisar", "Sürmene", "Tonya", "Vakfıkebir", "Yomra", "Çarşıbaşı", "Çaykara", "Şalpazarı"],
    "Tunceli": ["Merkez", "Hozat", "Mazgirt", "Nazımiye", "Ovacık", "Pertek", "Pülümür", "Çemişgezek"],
    "Uşak": ["Merkez", "Banaz", "Eşme", "Karahallı", "Sivaslı", "Ulubey"],
    "Van": ["Bahçesaray", "Başkale", "Edremit", "Erciş", "Gevaş", "Gürpınar", "Muradiye", "Saray", "Tuşba", "Çaldıran", "Çatak", "Özalp", "İpekyolu"],
    "Yalova": ["Merkez", "Altınova", "Armutlu", "Termal", "Çiftlikköy", "Çınarcık"],
    "Yozgat": ["Merkez", "Akdağmadeni", "Aydıncık", "Boğazlıyan", "Kadışehri", "Saraykent", "Sarıkaya", "Sorgun", "Yenifakılı", "Yerköy", "Çandır", "Çayıralan", "Çekerek", "Şefaatli"],
    "Zonguldak": ["Merkez", "Alaplı", "Devrek", "Ereğli", "Gökçebey", "Kilimli", "Kozlu", "Çaycuma"],
    "Çanakkale": ["Merkez", "Ayvacık", "Bayramiç", "Biga", "Bozcaada", "Eceabat", "Ezine", "Gelibolu", "Gökçeada", "Lapseki", "Yenice", "Çan"],
    "Çankırı": ["Merkez", "Atkaracalar", "Bayramören", "Eldivan", "Ilgaz", "Korgun", "Kurşunlu", "Kızılırmak", "Orta", "Yapraklı", "Çerkeş", "Şabanözü"],
    "Çorum": ["Merkez", "Alaca", "Bayat", "Boğazkale", "Dodurga", "Kargı", "Laçin", "Mecitözü", "Ortaköy", "Osmancık", "Oğuzlar", "Sungurlu", "Uğurludağ", "İskilip"],
    "İstanbul": ["Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bahçelievler", "Bakırköy", "Bayrampaşa", "Bağcılar", "Başakşehir", "Beykoz", "Beylikdüzü", "Beyoğlu", "Beşiktaş", "Büyükçekmece", "Esenler", "Esenyurt", "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kartal", "Kağıthane", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer", "Silivri", "Sultanbeyli", "Sultangazi", "Tuzla", "Zeytinburnu", "Çatalca", "Çekmeköy", "Ümraniye", "Üsküdar", "Şile", "Şişli"],
    "İzmir": ["Aliağa", "Balçova", "Bayraklı", "Bayındır", "Bergama", "Beydağ", "Bornova", "Buca", "Dikili", "Foça", "Gaziemir", "Güzelbahçe", "Karabağlar", "Karaburun", "Karşıyaka", "Kemalpaşa", "Kiraz", "Konak", "Kınık", "Menderes", "Menemen", "Narlıdere", "Seferihisar", "Selçuk", "Tire", "Torbalı", "Urla", "Çeşme", "Çiğli", "Ödemiş"],
    "Şanlıurfa": ["Akçakale", "Birecik", "Bozova", "Ceylanpınar", "Eyyübiye", "Halfeti", "Haliliye", "Harran", "Hilvan", "Karaköprü", "Siverek", "Suruç", "Viranşehir"],
    "Şırnak": ["Merkez", "Beytüşşebap", "Cizre", "Güçlükonak", "Silopi", "Uludere", "İdil"],
}


def _tr_buyuk(_s):
    """Türkçe karakterleri doğru büyüten upper() — Python'un varsayılan .upper()
    fonksiyonu 'i' harfini 'İ' değil 'I' yapar, bu yanlış Türkçe büyük harfe
    yol açar. Kargo Girişi gibi serbest metin alanlarını büyük harfe çevirmek
    için her yerde bu fonksiyon kullanılır."""
    return str(_s or "").replace("i", "İ").replace("ı", "I").upper()


def _hizli_firma_ayristir(_metin):
    """KULLANICI İSTEĞİ (2026-09): İnternetten kopyalanan karmaşık/düzensiz
    firma bilgisini (Google/Yandex Haritalar, rehber siteleri vb. tarzı)
    otomatik olarak Firma Adı / GSM / Sabit Tel(ler) / Email(ler) / Adres /
    İl / İlçe alanlarına ayrıştırır. SONUÇ SADECE BİR ÖNİZLEMEDİR — hiçbir
    şey otomatik/sessizce kaydedilmez, kullanıcı önce gözden geçirip
    düzeltebilir, sonra kendisi kaydeder."""
    import re as _hf_re
    _ham = str(_metin or "")
    _satirlar_ham = [s.strip() for s in _ham.split("\n") if s.strip()]
    _firma_adi = _satirlar_ham[0] if _satirlar_ham else ""

    # ÖNEMLİ: firma adı satırı YAPISAL OLARAK baştan çıkarılır — bir string
    # karşılaştırmasına (== _firma_adi) güvenmek, ufak boşluk/noktalama
    # farklarında satırın adrese sızmasına yol açıyordu.
    _kalan_satirlar_ham = _ham.split("\n")
    if _kalan_satirlar_ham and _kalan_satirlar_ham[0].strip() == _firma_adi:
        _calisma = "\n".join(_kalan_satirlar_ham[1:])
    else:
        _calisma = _ham

    # E-postalar — KÜÇÜK HARF olarak, olduğu gibi bırakılır (kullanıcı isteği)
    _emailler = _hf_re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', _calisma)
    _emailler = list(dict.fromkeys(_emailler))  # sırayı koru, tekilleştir
    for _e in _emailler:
        _calisma = _calisma.replace(_e, " ")

    # Telefon adayları — geniş bir kalıpla yakala, rakam sayısına göre süz.
    # 10 haneye (başındaki 0 ve/veya 90 ülke kodu atıldıktan sonra) tamamlanan
    # her aday geçerli sayılır; "5" ile başlıyorsa GSM, değilse Sabit Tel.
    # ÖNEMLİ: bazı firmalar numarayı "+90 0216 ..." gibi HEM ülke kodu HEM
    # başındaki sıfırla birlikte yazıyor (13 hane) — bu yüzden tek seferlik
    # değil, 10 haneye inene kadar TEKRARLI olarak ülke kodu/sıfır atılır.
    _tel_gsm, _tel_sabit = [], []
    # ÖNEMLİ: \s DEĞİL sadece boşluk kullanılır — \s satır sonunu (\n) da
    # kapsadığından, farklı satırlardaki iki ayrı telefon numarasını
    # birbirine karıştırıp ikisini de geçersiz kılabiliyordu.
    # ÖNEMLİ: tire (-) ARTIK dahil değil — "0216 766 67 04 - 0216 611 00 06"
    # gibi İKİ AYRI numara boşluklu tire ile yan yana yazılınca, tire
    # izin verilen karakterler arasında olduğu için regex ikisini TEK (ve
    # rakam sayısı tutmadığı için GEÇERSİZ) bir adaya kaynaştırıp İKİSİNİ
    # DE kaybediyordu. Tire kaldırılınca her numara kendi başına yakalanır.
    _tel_adaylari = _hf_re.findall(r'[\+]?\d[\d \.\(\)]{7,17}\d', _calisma)
    for _aday in _tel_adaylari:
        _rakamlar = _hf_re.sub(r'\D', '', _aday)
        while len(_rakamlar) > 10:
            if _rakamlar.startswith("90") and len(_rakamlar) >= 12:
                _rakamlar = _rakamlar[2:]
            elif _rakamlar.startswith("0"):
                _rakamlar = _rakamlar[1:]
            else:
                break
        if len(_rakamlar) != 10:
            continue
        # Format: "216 591 08 08" (baştaki 0 OLMADAN) — kullanıcı isteği,
        # örnek verdiği format buydu.
        _bicimli = f"{_rakamlar[0:3]} {_rakamlar[3:6]} {_rakamlar[6:8]} {_rakamlar[8:10]}"
        if _rakamlar[0] == "5":
            if _bicimli not in _tel_gsm:
                _tel_gsm.append(_bicimli)
        else:
            if _bicimli not in _tel_sabit:
                _tel_sabit.append(_bicimli)
        _calisma = _calisma.replace(_aday, " ")

    # "Türkiye"/"Turkey" ibaresi kaldırılır
    _calisma = _hf_re.sub(r'\bt[üu]rk[iİ]ye\b', ' ', _calisma, flags=_hf_re.IGNORECASE)
    _calisma = _hf_re.sub(r'\bturkey\b', ' ', _calisma, flags=_hf_re.IGNORECASE)

    # Posta kodu (tek başına 5 haneli sayı) kaldırılır
    _calisma = _hf_re.sub(r'\b\d{5}\b', ' ', _calisma)

    # İl / İlçe tespiti — bilinen 81 il/ilçe listesine göre (_IL_ILCE_HARITASI)
    def _hf_norm(_x):
        return str(_x or "").upper().replace("İ","I").replace("Ş","S").replace("Ğ","G").replace("Ü","U").replace("Ö","O").replace("Ç","C")
    _bulunan_il, _bulunan_ilce = "", ""
    _calisma_norm = _hf_norm(_calisma)
    for _il_adi in _IL_ILCE_HARITASI.keys():
        if _hf_re.search(r'\b' + _hf_re.escape(_hf_norm(_il_adi)) + r'\b', _calisma_norm):
            _bulunan_il = _il_adi
            for _ilce_adi in _IL_ILCE_HARITASI[_il_adi]:
                if _hf_re.search(r'\b' + _hf_re.escape(_hf_norm(_ilce_adi)) + r'\b', _calisma_norm):
                    _bulunan_ilce = _ilce_adi
                    break
            break

    # ── ADRES — KULLANICI İSTEĞİ: SADECE gerçek adres bileşenleri (mahalle,
    # cadde, sokak, sanayi sitesi adları, bina adları, sokak no, ilçe, il,
    # semt) gelecek. Ürün/hizmet açıklaması, telefon, email gibi HERHANGİ
    # bir başka bilgi ADRES'e KESİNLİKLE karışmayacak. Bunun için DENYLIST
    # (gürültü kelimeleri) yetmiyor — bunun yerine WHITELIST kullanılıyor:
    # bir parça, adres göstergesi bir anahtar kelime (mah/cad/sok/no:/sanayi/
    # sitesi/osb vb.) YA DA bilinen bir İl/İlçe adı İÇERMİYORSA doğrudan
    # ATILIR — "adres gibi görünmeyen" hiçbir şey adrese girmez.
    _ADRES_ANAHTAR_KELIME_HF = ["mah", "mh.", "cad", "cd.", "sok", "sk.", "no:", "no.",
                                 "kat", "daire", "blok", "site", "sit", "osb", "apt",
                                 "bulvar", "meydan", "köy", "mevkii", "mevki", "merkez",
                                 "sanayi", "plaza", "han", "çarşı", "semt", "bina"]
    _il_ilce_kelime_seti_hf = set()
    for _il_a_hf, _ilce_l_hf in _IL_ILCE_HARITASI.items():
        _il_ilce_kelime_seti_hf.add(_hf_norm(_il_a_hf))
        for _ilce_a_hf in _ilce_l_hf:
            _il_ilce_kelime_seti_hf.add(_hf_norm(_ilce_a_hf))

    def _hf_adres_benzeri_mi(_parca):
        _pk = _parca.lower()
        if any(_ak in _pk for _ak in _ADRES_ANAHTAR_KELIME_HF):
            return True
        _p_norm = _hf_norm(_parca)
        for _kelime in _hf_re.split(r'[^A-ZİĞÜŞÖÇ0-9]+', _p_norm):
            if _kelime and _kelime in _il_ilce_kelime_seti_hf:
                return True
        return False

    _GURULTU_KELIME_HF = ["yorum yaz", "yorum", "üretici", "web sitesi", "yol tarifi",
                           "kaydet", "paylaş", "telefon et", "telefon", "fax", "faks",
                           "e-posta", "eposta", "e posta", "varış süresi",
                           "saatler", "değerlendirme", "işletmeyi öner", "yorumlar",
                           "routes", "directions", "share", "website", "call"]

    def _hf_gurultu_temizle(_metin):
        _parcalar_ic = []
        for _parca in _hf_re.split(r'[\n,]', _metin):
            _p_temiz = _hf_re.sub(r'\s+', ' ', _parca).strip(" ,.-")
            if not _p_temiz or _p_temiz == _firma_adi.strip():
                continue
            _p_kucuk = _p_temiz.lower()
            if any(_gk in _p_kucuk for _gk in _GURULTU_KELIME_HF):
                continue
            if _hf_re.fullmatch(r'[\d.,]+', _p_temiz):  # tek başına rakam/puan/süre
                continue
            if _hf_re.fullmatch(r'\d+\s*dk\.?', _p_kucuk):
                continue
            if not _hf_adres_benzeri_mi(_p_temiz):  # adres göstergesi YOKSA at
                continue
            _parcalar_ic.append(_p_temiz)
        return " ".join(_parcalar_ic)

    _adres = ""
    _etiket_m = _hf_re.search(
        r'adres\s*:?\s*(.+?)(?=\n|varış süresi|saatler?\b|web sitesi|yorum|değerlendirme|$)',
        _calisma, _hf_re.IGNORECASE | _hf_re.DOTALL)
    if _etiket_m:
        _aday_adres = _etiket_m.group(1).strip(" ,.-")
        if _aday_adres:
            _adres = _aday_adres
    if not _adres:
        _adres = _calisma
    _adres = _hf_gurultu_temizle(_adres)
    # SON GÜVENLİK KATMANI: adreste hâlâ bir telefon/email kalıntısı varsa
    # (nadiren, farklı bir formatta yazıldığı için ilk taramada kaçmışsa) son
    # bir kez daha temizlenir.
    for _kalinti_tel in _hf_re.findall(r'[\+]?\d[\d \-\.\(\)]{7,17}\d', _adres):
        _adres = _adres.replace(_kalinti_tel, " ")
    for _kalinti_email in _hf_re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', _adres):
        _adres = _adres.replace(_kalinti_email, " ")
    # KULLANICI İSTEĞİ: Adreste HİÇ virgül olmayacak.
    _adres = _adres.replace(",", " ")
    _adres = _hf_re.sub(r'[ \t]+', ' ', _adres).strip(" ,")

    # ── SON GÜVENLİK KATMANI: kaynak metinde adres ile ürün/hizmet açıklaması
    # arasında virgül/satır sonu gibi bir ayraç YOKSA (tek bitişik metin),
    # yukarıdaki parça-bazlı filtre ikisini ayıramaz. Bu yüzden: adresin son
    # geçerli "İlçe/İl" ya da "İl" eşleşmesinden SONRA kalan kısım, adres
    # göstergesi TAŞIMIYORSA (ör. ürün açıklaması, telefon kalıntısı) oradan
    # itibaren KESİLİR.
    _il_ilce_desenleri_hf = []
    for _il_a2, _ilce_l2 in _IL_ILCE_HARITASI.items():
        _il_n2 = _hf_norm(_il_a2)
        for _ilce_a2 in _ilce_l2:
            _il_ilce_desenleri_hf.append(r'\b' + _hf_re.escape(_hf_norm(_ilce_a2)) + r'\s*/?\s*' + _hf_re.escape(_il_n2) + r'\b')
        _il_ilce_desenleri_hf.append(r'\b' + _hf_re.escape(_il_n2) + r'\b')
    _adres_norm_kontrol = _hf_norm(_adres)
    _son_gecerli_konum = None
    for _desen_k in _il_ilce_desenleri_hf:
        for _m_k in _hf_re.finditer(_desen_k, _adres_norm_kontrol):
            if _son_gecerli_konum is None or _m_k.end() > _son_gecerli_konum:
                _son_gecerli_konum = _m_k.end()
    if _son_gecerli_konum is not None and _son_gecerli_konum < len(_adres):
        _kalan_metin_hf = _adres[_son_gecerli_konum:].strip()
        if _kalan_metin_hf and not _hf_adres_benzeri_mi(_kalan_metin_hf):
            _adres = _adres[:_son_gecerli_konum].strip()

    # ── BİRDEN FAZLA ADRES — KULLANICI İSTEĞİ: yapıştırılan metinde art arda
    # birkaç şube/adres varsa (her biri kendi "İlçe/İl" ile bitiyorsa), her
    # "İlçe/İl" kalıbından hemen SONRA satır atlanıp bir sonraki adres YENİ
    # SATIRDA başlar — aynı il/ilçe tekrar etse bile sorun değil, ayraç
    # olarak yine kullanılır.
    _adres_norm_hf = _hf_norm(_adres)
    _ekleme_noktalari_hf = set()
    for _il_adi3, _ilceler3 in _IL_ILCE_HARITASI.items():
        _il_norm3 = _hf_norm(_il_adi3)
        for _ilce_adi3 in _ilceler3:
            _ilce_norm3 = _hf_norm(_ilce_adi3)
            _desen3 = r'\b' + _hf_re.escape(_ilce_norm3) + r'\s*/\s*' + _hf_re.escape(_il_norm3) + r'\b'
            for _m3 in _hf_re.finditer(_desen3, _adres_norm_hf):
                _ekleme_noktalari_hf.add(_m3.end())
    if _ekleme_noktalari_hf:
        _sirali_noktalar = sorted(_ekleme_noktalari_hf)
        _parcalar_yeni_hf = []
        _onceki_konum_hf = 0
        for _nokta_hf in _sirali_noktalar:
            _parcalar_yeni_hf.append(_adres[_onceki_konum_hf:_nokta_hf].strip())
            _onceki_konum_hf = _nokta_hf
        _son_parca_hf = _adres[_onceki_konum_hf:].strip(" ,.-:")
        # Son parça, gerçekten adres göstergesi TAŞIMIYORSA (ör. sondan kalan
        # "Merkez Ofis :" gibi bir etiket kırıntısı), eklenmez.
        if _son_parca_hf and _hf_adres_benzeri_mi(_son_parca_hf):
            _parcalar_yeni_hf.append(_son_parca_hf)
        _adres = "\n".join(p for p in _parcalar_yeni_hf if p)

    return {
        "firma_adi": _tr_buyuk(_firma_adi.strip()),
        "gsm": "\n".join(_tel_gsm),
        "sabit": "\n".join(_tel_sabit),
        "email": "\n".join(_emailler),
        "adres": _tr_buyuk(_adres),
        "il": _bulunan_il,
        "ilce": _bulunan_ilce,
    }


def _hizli_firma_mukerrer_kontrol(_firma_adi, _gsm, _sabit, _email, _adres=""):
    """KULLANICI İSTEĞİ (2026-09): Hızlı Firma Ekle ile kaydetmeden ÖNCE,
    mevcut Cari Ana Liste'de AYNI İSİM, AYNI TELEFON (GSM veya Sabit) ya da
    AYNI EMAİL'e sahip bir kayıt olup olmadığını kontrol eder — göz ardı
    edilmesin diye. Eşleşen kayıtları listeler; hiçbir şeyi otomatik
    ENGELLEMEZ/SİLMEZ, sadece UYARIR — kayıt yine de eklenebilir."""
    import re as _mk_re
    try:
        _df_mk = get_cari_listesi()
    except Exception:
        return []
    if _df_mk.empty or "firma" not in _df_mk.columns:
        return []

    def _mk_isim_norm(_x):
        return _mk_re.sub(r'[^A-ZİĞÜŞÖÇ0-9]', '', _tr_buyuk(str(_x or "")).strip())

    def _mk_tel_norm_liste(_x):
        _parcalar = [p for p in _mk_re.split(r'[\n,;/]+', str(_x or "")) if p.strip()]
        _sonuc = []
        for _p in _parcalar:
            _r = _mk_re.sub(r'\D', '', _p)
            if len(_r) >= 7:
                _sonuc.append(_r[-10:])
        return _sonuc

    def _mk_email_seti(_x):
        return {e.strip().lower() for e in str(_x or "").split("\n") if e.strip()}

    _yeni_isim = _mk_isim_norm(_firma_adi)
    _yeni_tel_seti = set(_mk_tel_norm_liste(_gsm) + _mk_tel_norm_liste(_sabit))
    _yeni_email_seti = _mk_email_seti(_email)

    _eslesenler = []
    for _, _r in _df_mk.iterrows():
        _sebepler = []
        if _yeni_isim and _mk_isim_norm(_r.get("firma", "")) == _yeni_isim:
            _sebepler.append("Aynı isim")
        _r_tel_seti = set(_mk_tel_norm_liste(_r.get("gsm", "")) + _mk_tel_norm_liste(_r.get("sabit", "")))
        if _yeni_tel_seti and (_yeni_tel_seti & _r_tel_seti):
            _sebepler.append("Aynı telefon")
        _r_email_seti = _mk_email_seti(_r.get("email", ""))
        if _yeni_email_seti and (_yeni_email_seti & _r_email_seti):
            _sebepler.append("Aynı email")
        if _sebepler:
            _eslesenler.append({
                "id": _r.get("id"), "firma": _r.get("firma", ""), "gsm": _r.get("gsm", ""),
                "sabit": _r.get("sabit", ""), "email": _r.get("email", ""),
                "il": _r.get("il", ""), "sebep": ", ".join(_sebepler)
            })
    return _eslesenler

import sqlite3
import pandas as pd
import shutil
import os
import io
import re
import json
import time
import concurrent.futures
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════════════════
# 📌 PROJE_KURALLARI — MWCRMPRO geliştirme kuralları (Claude için otomatik bağlam)
# main.py yeni bir Claude sohbetine yüklendiğinde bu blok otomatik okunur.
# Aynı metin CRM içinde: Kullanıcı Yönetimi → 📌 Kurallar sekmesinde de görünür.
# ═══════════════════════════════════════════════════════════════════════════
KURALLAR_PIN = "1907"  # Kurallar sekmesi için erişim PIN'i — değiştirmek istersen söyle yeter

PROJE_KURALLARI = """
### 1) Git Komutları
Her kod teslimatının sonunda:
```
git add main.py
git commit -m "..."   (değişikliği özetleyen mesaj)
git push
```

### 2) Kesin Çalışma Kuralları
- Yeni SQL migration yok, sadece mevcut tabloları kullan.
- requirements.txt'e yeni pip paketi ekleme, sadece stdlib (urllib vb.).
- Kullanıcıya asla manuel/elle kod değişikliği yaptırma; her değişikliği tam çalışır main.py dosyası olarak ver.
- Stabilite önceliklidir, çalışan özellikleri bozma. (Not arşivleme özelliğinde geçmişte veri kaybı yaşandı — bu alanda ekstra dikkatli ol.)
- `cari_aciklamalar` tablosuna insert: sadece `cari_id`, `aciklama`, `olusturan` kolonları var; `tip` / `tarih` kolonu YOK.

### 3) Veri Güvenliği — KRİTİK
Asla veri silinmeyecek/kaybolmayacak. Silme gerektiren hiçbir işlem (toplu silme dahil) önce açık kullanıcı onayı olmadan YAPILMAZ.

### 3b) Kargo / Tedarikçi / Sistem Geneli Veri Kaybı Yasağı — KRİTİK (2026-09)
Kullanıcı bunu bizzat yaşayıp bildirdi: Kargo listesinde, Tedarikçi listesinde
ve genel olarak SİSTEMİN HERHANGİ BİR YERİNDE **asla ve asla** veri/bilgi kaybı
olmayacak — bu kural **yeni kod yazılırken veya mevcut bir özellik
güncellenirken dahi** geçerlidir, "sadece ekliyorum eskiyi bozmuyorum" denilen
durumlar dahil.
- Kayıt "silinecekse" bile fiziksel olarak yok edilmez; Müşteri'de (cari_kartlar
  → `silindi` bayrağı) ve Tedarikçi'de zaten yapıldığı gibi **soft-delete**
  (`silindi` bayrağı + `silinme_tarihi`) ile işaretlenip listede kalır,
  "🗑️ Silinenler" ekranından geri alınabilir. Kargo kayıtları da aynı deseni
  kullanır — bu davranış korunacak, asla hard-delete'e çevrilmeyecek.
- Supabase'e yazılan her "tam liste" (kargo, tedarikçi, il gönderim matrisi,
  manuel alıcı hafızası vb. `kullanici_tercih` tablosundaki JSON blob'lar) için:
  DELETE hiç kullanılmaz. Satır zaten varsa doğrudan UPDATE edilir (atomik,
  tek adım), satır hiç yoksa INSERT edilir. (Not: daha önce "önce ekle, id ile
  doğrula, sonra eskiyi sil" denendi — ama id doğrulaması beklenen gibi
  çalışmayınca yeni kayıtlar eski satırın arkasında saklı kalıp görünmez oldu.
  UPDATE-yoksa-INSERT deseni hiçbir sütuna bağımlı olmadığı için bu riski
  taşımıyor — kesin tercih edilecek yöntem budur.)
- Okuma başarısız olduğunda (bağlantı sorunu) asla `[]` (boş) dönülüp "kayıt
  yokmuş" gibi davranılmaz — `_OKUMA_BASARISIZ` sinyali kullanılır ve çağıran
  taraf işlemi iptal eder.
- Yeni bir modül/özellik için kaydetme fonksiyonu yazılacaksa, kargo
  (`_kg_kayitlari_kaydet`) ve tedarikçi (`_tedarikci_kaydet`) için kullanılan
  UPDATE-yoksa-INSERT deseni birebir kopyalanır; DELETE içeren bir "kaydet"
  fonksiyonu yazılmaz.

### 3c) Hiçbir Yerde "None" Yazısı Gösterilmeyecek — KALICI (2026-09)
Kullanıcıya hiçbir tabloda/alanda teknik boşluk göstergesi ("None", "NaN",
"nan", "null") YAZI olarak gösterilmez. `sozluk.get("alan", "")` yerine
`sozluk.get("alan") or ""` kullanılır (anahtar var ama değeri None ise ilki
bunu YAKALAMAZ). Kullanıcıya gösterilecek her DataFrame, render edilmeden
hemen önce `_hic_none_gosterme(df)` içinden geçirilir.

### 3d) `st.form()` KESİN OLARAK KALDIRILDI — Bir Daha Önerilmeyecek — KALICI (2026-09, MUTLAK NİHAİ KARAR)
Cari Liste tablosuna "veri girerken yanıp sönmesin" diye `st.form()` eklendi,
sonra kaldırıldı, sonra tekrar eklendi — İKİ KEZ. İkinci denemede form,
"Seç" kutusuyla açılan Notlar/Randevu penceresinin (bkz. `not_dialog`)
BEKLENMEDİK şekilde kapanmasına, kullanıcının "İl işaretleme / Fiyat
Tablosu / Hedeflenen Ciro" gibi işlemlerinin form'un "sadece Kaydet'te
gönderir" davranışı yüzünden HİÇ KAYDEDİLMEMİŞ olabileceği şüphesine yol
açtı. Kullanıcı bunun üzerine formu KESİN OLARAK kaldırmamızı istedi.
MUTLAK NİHAİ KARAR: Cari Liste tablosu ARTIK VE HER ZAMAN form'suz, düz
`st.data_editor()` olarak kalacak. "Kaydet" HER ZAMAN üstteki sticky buton
satırındadır (Satır Ekle/Kolon Sıfırla/Excel İndir/Tümünü Seç/Seçimi
Temizle ile aynı satırda). "Seç" kutusu işaretlenince Notlar/Randevu
penceresi ANINDA açılır (bkz. `if secili_sayi == 1: not_dialog(...)`).
`st.form()` BU TABLO İÇİN BİR DAHA ASLA ÖNERİLMEYECEK/DENENMEYECEK — "veri
girerken yanıp sönme" konusu KAPANMIŞTIR, bir daha gündeme getirilmeyecek.
Yerine tercih edilen çözüm: ağır arka plan hesaplamalarını (Rut,
Gerçekleşen Ciro) önbelleğe alarak yeniden çizim MALİYETİNİ düşürmek —
bkz. `_cl_il_rut_onbellek_*` ve `_tum_musteri_kargo_yekun_toplami` (ttl=300).

### 3e) RİSKLİ/DENEYSEL MİMARİ DEĞİŞİKLİK ASLA ÖNERİLMEZ — KALICI (2026-09, KESİN)
Kullanıcı bunu AÇIKÇA istedi: "yanıp sönme" gibi performans/UX konuları için
`st.form()`, `st.fragment()` gibi Streamlit'in DAVRANIŞ MODELİNİ değiştiren,
DENEYSEL/RİSKLİ mimari çözümler BİR DAHA ASLA önerilmeyecek — kullanıcının
üzerinde çok emek harcadığı canlı bir iş uygulaması bu, "acaba çalışır mı"
diye denemeye açık değil. Kullanıcı net bir şekilde "risk göze almıyorum,
emeklerim var" dedi. Bu tür konularda İZİN VERİLEN TEK yol: MEVCUT davranışı
(hangi widget'ın ne zaman rerun tetiklediği) hiç DEĞİŞTİRMEDEN, sadece
ARKA PLANDAKİ AĞIR HESAPLAMALARI (önbellekleme, TTL artırma, gereksiz
sorguları azaltma gibi SAF PERFORMANS optimizasyonları — DAVRANIŞ/AKIŞ
değişikliği içermeyen) iyileştirmektir. Herhangi bir değişikliğin kullanıcı
davranışını (bir butonun ne zaman göründüğü, bir etkileşimin ne zaman
işlendiği, verinin ne zaman kaydedildiği) DEĞİŞTİRİP DEĞİŞTİRMEDİĞİNDEN emin
olunmalı — değiştiriyorsa, önce KESİN bir onay alınmadan uygulanmaz.
ÖNEMLİ DERS (2026-09): Cari Liste'nin Rut/İl sütunları için session_state
tabanlı bir önbellekleme eklenmişti ("saf performans" niyetiyle) — ama bu,
işaretlenen illerin/Rut'un tabloda GÖRÜNMEMESİNE yol açan gerçek bir veri
GÖRÜNTÜLEME hatasına neden oldu ve KALDIRILDI. Rut/İl sütunları artık HER
RENDER'DA doğrudan, önbelleksiz hesaplanıyor (bkz. `_il_gonderim_matrisi_yukle`
sonrası, `_cari_rut_hesapla_otomatik` çağrısı) — DAHA YAVAŞ ama HER ZAMAN
DOĞRU. Bu iki sütun için ("rut" ve `_IL_SUTUN_LISTESI`) BİR DAHA
session_state/önbellek tabanlı bir "hızlandırma" DENENMEYECEK — "saf
performans" göründüğü halde veri doğruluğunu bozma riski kanıtlanmış
durumda. Başka bir alanda önbellekleme önerilecekse bile, önce KAPSAMLI
şekilde test edilip (kaydet → hemen görüntüle → doğrula) kanıtlanmadan
uygulanmaz.

### 4) MacroDroid Entegrasyonu
- Supabase proje: `asinwzxwmkkrcbtjrkoq.supabase.co` — tablolar: `islem_kaydi`, `cari_kartlar`, `kisiler`
- Amaç: Gelen/Giden Arama & SMS'te arayan/gönderen adını rehberden bulup CRM'e (`musteri_adi`) otomatik yazdırmak.
- Kullanıcı MacroDroid'i Türkçe arayüzde kullanıyor, teknik bilgisi sınırlı — adımlar tek tek, ekran görüntüsüyle doğrulanarak anlatılmalı.
- "Kişileri Al" + sözlük yöntemi ÇOK YAVAŞ (8000 kişide ~4 dk) — bunun yerine anılık sistem değişkenleri kullanılmalı: `*Çağrı ismi`, `*Gelen SMS kişisi`, `*Giden SMS kişisi`

### 5) Supabase Erişim Bilgileri
- `SUPABASE_URL` = `https://asinwzxwmkkrcbtjrkoq.supabase.co`
- `SUPABASE_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFzaW53enh3bWtrcmNidGpya29xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA3MzM4MzQsImV4cCI6MjA5NjMwOTgzNH0.7WNPNWG-uXO7COSOhzVyAbR-MTaP6RdSlOTI0IfyNAU`

### 6) Muhasebe (Paraşüt) Entegrasyonu — KALDIRILDI (2026-09)
Bu entegrasyon (Faturalar, Teklifler, Müşteriler, Gider Listesi, Tedarikçiler,
Çalışanlar, Kasa/Banka, Çekler, 8 rapor sayfası — ~1100 satır) menüde/gezinmede
HİÇBİR YERDEN erişilemediği (kullanılmayan "ölü kod" olduğu) için kullanıcı
isteğiyle koddan TAMAMEN kaldırıldı. Bir daha eklenmesi istenirse bu notu
referans almayın — API bilgileri artık koddan silindi, yeniden entegre etmek
isterse kullanıcının CLIENT_ID/CLIENT_SECRET/COMPANY_ID bilgilerini yeniden
vermesi gerekir.
"""

# ── SUPABASE BAĞLANTISI ───────────────────────────────────────────────────────
def sb_or_sqlite():
    """Supabase varsa True, yoksa SQLite kullan"""
    try:
        url = st.secrets.get("SUPABASE_URL","")
        key = st.secrets.get("SUPABASE_KEY","")
        return bool(url and key)
    except:
        return False

@st.cache_resource
def get_sb_client():
    """Supabase client — tek seferlik oluştur, cache'le"""
    try:
        from supabase import create_client, ClientOptions
        url = st.secrets.get("SUPABASE_URL","")
        key = st.secrets.get("SUPABASE_KEY","")
        if url and key:
            try:
                # Max rows limitini kaldır
                opts = ClientOptions(postgrest_client_timeout=60)
                client = create_client(url, key, options=opts)
                client.postgrest.auth(key)
                return client
            except:
                return create_client(url, key)
    except:
        pass
    return None


# ── İL GÖNDERİM MATRİSİ — GLOBAL (Cari Liste tablosu VE Notlar&Randevu
# dialog'undaki "Varış/Fiyat" sekmesi AYNI fonksiyonu/önbelleği paylaşır.
# Ayrı ayrı tanımlanırsa, dialogdan kaydedince Cari Liste'nin önbelleği
# temizlenmiyor, yazılan iller tabloda hemen görünmüyordu.
@st.cache_data(ttl=30, show_spinner=False)
def _il_gonderim_matrisi_yukle():
    try:
        _sb_ilm = get_sb_client()
        if _sb_ilm:
            _r_ilm = _sb_ilm.table("kullanici_tercih").select("deger").eq(
                "kullanici", "__liste_ui__").eq("anahtar", "_il_gonderim_matrisi").execute()
            if _r_ilm.data:
                import json as _ilmj
                return _ilmj.loads(_r_ilm.data[0]["deger"])
    except Exception:
        pass
    return {}

def _il_gonderim_matrisi_kaydet(_matris):
    """GÜVENLİ (2026-09, 2. düzeltme) — bkz. _tedarikci_kaydet. SİLME YOK,
    satır varsa UPDATE, yoksa INSERT."""
    try:
        _sb_ilm2 = get_sb_client()
        if not _sb_ilm2:
            return False
        import json as _ilmj2
        _deger = _ilmj2.dumps(_matris, ensure_ascii=False)
        _guncelle_sonuc = _sb_ilm2.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", "_il_gonderim_matrisi").execute()
        if not _guncelle_sonuc.data:
            _sb_ilm2.table("kullanici_tercih").insert(
                {"kullanici": "__liste_ui__", "anahtar": "_il_gonderim_matrisi", "deger": _deger}
            ).execute()
        # 🚨 DÜZELTME (2026-09): Cari Liste'nin Rut/İl sütunları performans için
        # session_state'te önbelleğe alınıyor (bkz. _cl_il_rut_onbellek_*).
        # İl matrisi HER değiştiğinde bu önbellek de KESİN olarak temizlenir —
        # aksi halde işaretleme kaydedilse bile tabloda eski (güncellenmemiş)
        # Rut değeri görünmeye devam edebiliyordu.
        try:
            for _k_temiz in [k for k in list(st.session_state.keys()) if k.startswith("_cl_il_rut_onbellek_")]:
                st.session_state.pop(_k_temiz, None)
        except Exception:
            pass
        return True
    except Exception:
        return False


# ── MANUEL ALICI FİRMA HAFIZASI — Kargo Girişi'nde elle yazılan Alıcı Firma
# isimleri kalıcı olarak {firma: il} şeklinde saklanır. Bir daha o firma adı
# yazılınca ili otomatik gelir; yeni bir firma-il çifti girildikçe otomatik
# kaydedilir. cari_kartlar'a yeni kolon açılmaz (migration yok kuralı).
@st.cache_data(ttl=30, show_spinner=False)
def _kg_manuel_alici_yukle():
    try:
        _sb_ma = get_sb_client()
        if _sb_ma:
            _r_ma = _sb_ma.table("kullanici_tercih").select("deger").eq(
                "kullanici", "__liste_ui__").eq("anahtar", "_kargo_manuel_alici_firmalar").execute()
            if _r_ma.data:
                import json as _maj
                return _maj.loads(_r_ma.data[0]["deger"])
    except Exception:
        pass
    return {}

def _kg_manuel_alici_kaydet(_sozluk):
    """GÜVENLİ (2026-09, 2. düzeltme) — bkz. _tedarikci_kaydet. SİLME YOK,
    satır varsa UPDATE, yoksa INSERT."""
    try:
        _sb_ma2 = get_sb_client()
        if not _sb_ma2:
            return False
        import json as _maj2
        _deger = _maj2.dumps(_sozluk, ensure_ascii=False)
        _guncelle_sonuc = _sb_ma2.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", "_kargo_manuel_alici_firmalar").execute()
        if not _guncelle_sonuc.data:
            _sb_ma2.table("kullanici_tercih").insert(
                {"kullanici": "__liste_ui__", "anahtar": "_kargo_manuel_alici_firmalar", "deger": _deger}
            ).execute()
        return True
    except Exception:
        return False


# ── KARGO KAYITLARI (müşteriye özel) — GLOBAL. Hem Notlar&Randevu dialog'undaki
# Kargo Girişi sekmesi hem Kargolar sayfası AYNI fonksiyonu/önbelleği kullanır —
# ayrı ayrı tanımlanırsa biri diğerini GÖREMEZ, "silme/kaydetme çalışmıyor" gibi
# sessiz hatalara yol açar (bir kere böyle bir hata yaşandı, tekrar olmasın).
@st.cache_data(ttl=30, show_spinner=False)
def _kg_kayitlari_yukle(_anahtar):
    try:
        _sb_kg = get_sb_client()
        if _sb_kg:
            _r_kg = _sb_kg.table("kullanici_tercih").select("deger").eq(
                "kullanici", "__liste_ui__").eq("anahtar", _anahtar).execute()
            if _r_kg.data:
                import json as _kgj
                return _kgj.loads(_r_kg.data[0]["deger"])
    except Exception:
        pass
    return []


# ── KRİTİK GÜVENLİK SİNYALİ ─────────────────────────────────────────────────
# "Tam listeyi yükle → değiştir → tamamını üzerine yaz" işlemlerinde, okuma
# BAŞARISIZ olduğunda (ağ sorunu, geçici bağlantı kopması vb.) ASLA [] (boş)
# döndürülmez — çünkü bu, "veri gerçekten yok" ile "şu an okunamadı" ayrımını
# kaybettirip, üzerine yazma sırasında GERÇEK VERİYİ SİLİYORDU (109 kargo
# kaydının 102'ye, yeni eklenen 3 tedarikçinin 0'a inmesinin kök nedeni buydu).
# Bu sinyal döndüğünde çağıran taraf İŞLEMİ İPTAL ETMELİ, boşmuş gibi devam
# ETMEMELİ.
_OKUMA_BASARISIZ = object()


def _kg_kayitlari_yukle_taze(_anahtar):
    """_kg_kayitlari_yukle ile AYNI okuma, ama ÖNBELLEKSİZ — doğrudan
    Supabase'den okur. GÜVENLİK: 'tam listeyi yükle → bir kısmını değiştir →
    TAMAMINI üzerine yaz' işlemlerinde (Kaydet/Sil/Geri Al/Kalıcı Sil) artık
    HEP bu kullanılıyor. Okuma BAŞARISIZ olursa (bağlantı yok / hata) _OKUMA_BASARISIZ
    döner — [] DÖNMEZ, çünkü çağıran taraf bunu 'kayıt yok' sanıp üzerine
    yazarsa VERİ KAYBI olur. Kayıt gerçekten yoksa (sorgu başarılı, satır yok)
    boş liste [] döner — bu GERÇEK boşluktur, güvenlidir."""
    try:
        _sb_kgt = get_sb_client()
        if not _sb_kgt:
            return _OKUMA_BASARISIZ
        _r_kgt = _sb_kgt.table("kullanici_tercih").select("deger").eq(
            "kullanici", "__liste_ui__").eq("anahtar", _anahtar).execute()
        if _r_kgt.data:
            import json as _kgjt
            return _kgjt.loads(_r_kgt.data[0]["deger"])
        return []
    except Exception:
        return _OKUMA_BASARISIZ

def _kg_kayitlari_kaydet(_anahtar, _liste):
    """GÜVENLİ (2026-09, 2. düzeltme — 1. düzeltmedeki hata giderildi): bkz.
    _tedarikci_kaydet'teki aynı gerekçe. SİLME YOK — satır zaten varsa
    doğrudan UPDATE edilir, yoksa INSERT edilir. id sütununa bağımlı
    değildir, bu yüzden 'yeni kayıt görünmüyor' riski taşımaz."""
    try:
        _sb_kg2 = get_sb_client()
        if not _sb_kg2:
            return False
        import json as _kgj2
        _deger = _kgj2.dumps(_liste, ensure_ascii=False)
        _guncelle_sonuc = _sb_kg2.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", _anahtar).execute()
        if not _guncelle_sonuc.data:
            _sb_kg2.table("kullanici_tercih").insert(
                {"kullanici": "__liste_ui__", "anahtar": _anahtar, "deger": _deger}
            ).execute()
        # Kargo değişti — Cari Liste'deki "Gerçekleşen Ciro" önbelleğini
        # (performans için 5 dk'lık) hemen geçersiz kıl, bir sonraki
        # açılışta güncel görünsün (2 dk beklemek zorunda kalmasın).
        try: _tum_musteri_kargo_yekun_toplami.clear()
        except Exception: pass
        return True
    except Exception:
        return False


def _kg_efektif_tutar(_kayit):
    """Bir kargo kaydının 'gerçek' tutarı — Toplam Fatura doluysa o, yoksa Tutar.
    Ciro hesaplarında (özet satırı, ödeme ekstresi, cari kart senkronu) hep
    aynı mantık kullanılsın diye tek yerden."""
    try:
        _tf = float(_kayit.get("toplam_fatura", 0) or 0)
    except Exception:
        _tf = 0.0
    if _tf:
        return _tf
    try:
        return float(_kayit.get("tutar", 0) or 0)
    except Exception:
        return 0.0


def _kg_yuvarla(_deger, _basamak=2):
    """Excel'den veya elle girişten gelen uzun ondalıklı sayıları (ör.
    90.72164948) TÜM parasal alanlarda 2 ondalık haneye indirir — muhasebe
    kolay olsun diye. Hem düz sayıyı hem Türkçe biçimli metni ('1.234,56')
    doğru okur. Sayıya çevrilemeyen değerler 0 döner."""
    if _deger is None:
        return 0.0
    _s = str(_deger).strip()
    if not _s:
        return 0.0
    if "," in _s and "." in _s:
        _s = _s.replace(".", "").replace(",", ".")
    elif "," in _s:
        _s = _s.replace(",", ".")
    try:
        return round(float(_s), _basamak)
    except Exception:
        return 0.0


def _kg_hesap_zinciri(_kayit):
    """B.Tutar (birim fiyat) × Adet = Yekün; oradan Sigorta %6 → Ara Toplam
    → Kdv %20 → Son Toplam (toplam_fatura) ZİNCİRLEME otomatik hesaplanır.
    Hiçbiri artık elle yazılmıyor — kayıt/güncelleme anında türetilip
    üzerine yazılır. Ayrıca B.Tutar/Desi/Kilo'nun kendisi de (Excel'den
    gelen uzun ondalıklı sayılar dahil) burada 2 haneye YUVARLANIR.
    _kayit sözlüğünü YERİNDE günceller ve aynı sözlüğü döndürür."""
    _tutar = _kg_yuvarla(_kayit.get("tutar", 0))
    _adet = _kg_yuvarla(_kayit.get("adet", 0))
    _kayit["tutar"] = _tutar
    _kayit["desi"] = _kg_yuvarla(_kayit.get("desi", 0))
    _kayit["kilo"] = _kg_yuvarla(_kayit.get("kilo", 0))
    _yekun = round(_tutar * _adet, 2)
    _sigorta = round(_yekun * 0.06, 2)
    _ara_toplam = round(_yekun + _sigorta, 2)
    _kdv = round(_ara_toplam * 0.20, 2)
    _kayit["yekun"] = _yekun
    _kayit["sigorta"] = _sigorta
    _kayit["ara_toplam"] = _ara_toplam
    _kayit["kdv"] = _kdv
    _kayit["toplam_fatura"] = round(_ara_toplam + _kdv, 2)
    return _kayit


def _kg_kar_zarar_hesapla(_kayit):
    """Kar/Zarar = Müşteri Tutar - Dış Nakliye Tutar (ESKİ formül tersti,
    düzeltildi). Sonuç pozitifse 'kar' alanına, negatifse 'zarar' alanına
    yazılır, diğeri 0 kalır (tabloda 0 yerine '-' gösterilir). Müşteri
    Tutar/Dış Nakliye Tutar'ın kendisi de burada 2 haneye YUVARLANIR. Artık
    elle yazılmıyor — kayıt/güncelleme anında otomatik hesaplanıp üzerine
    yazılır. _kayit sözlüğünü YERİNDE günceller ve aynı sözlüğü döndürür."""
    _mt = _kg_yuvarla(_kayit.get("musteri_tutar", 0))
    _dn = _kg_yuvarla(_kayit.get("dis_nakliye_tutar", 0))
    _kayit["musteri_tutar"] = _mt
    _kayit["dis_nakliye_tutar"] = _dn
    _net = round(_mt - _dn, 2)
    _kayit["kar"] = _net if _net > 0 else 0.0
    _kayit["zarar"] = _net if _net < 0 else 0.0
    return _kayit


def _kg_tr_format(_deger):
    """Sayıyı TÜRKÇE biçimde string'e çevirir: 1234.5 -> '1.234,50'
    (nokta binlik ayracı, virgül ondalık ayracı) — Streamlit'in number_input'u
    bunu doğal olarak yapamadığı için parasal alanlarda bunu kullanıyoruz."""
    try:
        _fv = float(_deger or 0)
    except Exception:
        _fv = 0.0
    _s = f"{_fv:,.2f}"  # ör: '1,234.50' (ABD biçimi)
    return _s.replace(",", "X").replace(".", ",").replace("X", ".")  # -> '1.234,50'


def _kg_tr_parse(_metin):
    """Türkçe (1.234,56 / 1234,56) ya da ABD (1234.56) biçiminde yazılmış bir
    sayıyı float'a çevirir — kullanıcı hangi ayracı kullanırsa kullansın
    doğru okunsun diye. Anlaşılamazsa 0 döner."""
    if _metin is None:
        return 0.0
    _s = str(_metin).strip()
    if not _s:
        return 0.0
    if "," in _s and "." in _s:
        _s = _s.replace(".", "").replace(",", ".")
    elif "," in _s:
        _s = _s.replace(",", ".")
    try:
        return float(_s)
    except Exception:
        return 0.0


def _kg_sifir_tire(_deger):
    """Kar/Zarar gibi 'ya biri ya diğeri dolu' sütunları TABLODA gösterirken
    0 yerine '-' yazsın diye — sadece görünüm; kayıt sırasında zaten
    _kg_kar_zarar_hesapla ile doğru sayısal değer yeniden yazılır. Türkçe
    (virgül ondalık, nokta binlik) biçimde gösterir."""
    try:
        _fv = float(_deger)
    except Exception:
        return "-"
    if _fv == 0:
        return "-"
    return _kg_tr_format(_fv)


def _kg_referans_no_temizle(_deger):
    """Takip No / Fatura No gibi PARASAL OLMAYAN referans numaraları içindir.
    Excel'den okunurken sayı olarak algılanıp '1910372.0' gibi gereksiz '.0'
    kuyruğuyla kaydedilmiş/gösterilmiş değerleri '1910372' olarak temizler
    (kullanıcı isteği: bu alan parasal değil, tam sayı gibi görünmeli).
    Gerçekten ondalıklı bir değer varsa (ör. '1910372.5') ya da sayısal
    değilse (harf/tire vb. içeriyorsa) OLDUĞU GİBİ bırakılır — sadece tam
    sayıya denk gelen '.0' kuyruğu kaldırılır, başka hiçbir şey değişmez."""
    _s = str(_deger if _deger is not None else "").strip()
    if _s.endswith(".0"):
        _govde = _s[:-2]
        if _govde and _govde.lstrip("-").isdigit():
            return _govde
    return _s


def _gecerli_metin(_v):
    """Bir değerin GERÇEKTEN dolu, kullanılabilir bir metin olup olmadığını
    kontrol eder — boş string VEYA 'None'/'NaN'/'null' gibi teknik boşluk
    göstergelerinden biriyse False döner. Tedarikçi/Dış Nakliye Firma gibi
    seçim listelerinde bozuk eski kayıtların ('None' metni olarak kaydedilmiş
    firma adı gibi) seçeneklere karışmaması için kullanılır."""
    _s = str(_v if _v is not None else "").strip()
    return bool(_s) and _s not in ("None", "none", "NONE", "NaN", "nan", "NAN", "null", "NULL", "<NA>")


_NONE_METIN_LISTESI = [None, "None", "none", "NONE", "NaN", "nan", "NAN", "NAT", "nat", "null", "NULL", "<NA>"]
_NONE_KELIME_KUCUK = {"none", "nan", "null", "nat", "<na>"}


def _hic_none_hucre_temizle(_v):
    """Tek bir hücreyi kontrol eder: None/NaN ise VEYA (baştaki/sondaki
    boşluklar temizlendikten ve küçük harfe çevrildikten sonra) 'none',
    'nan', 'null' gibi bir teknik boşluk göstergesine eşitse boş metin
    döner. Böylece '  None', 'None ', 'NONE', 'nan' gibi varyasyonların
    hepsi yakalanır — sadece BİREBİR eşleşen (Series.replace ile
    yakalanamayan boşluklu/karışık büyük-küçük harf durumları dahil)."""
    if _v is None:
        return ""
    try:
        if isinstance(_v, float) and pd.isna(_v):
            return ""
    except Exception:
        pass
    if isinstance(_v, str) and _v.strip().lower() in _NONE_KELIME_KUCUK:
        return ""
    return _v


def _hic_none_gosterme(_df):
    """KALICI KURAL (kullanıcı talimatı, 2026-09): sistemde hiçbir yerde
    kullanıcıya 'None'/'NaN'/'null' gibi teknik boşluk göstergeleri YAZI
    olarak gösterilmez. Bazı eski kayıtlarda `sozluk.get("alan", "")`
    kalıbının None değerleri yakalayamaması yüzünden bu metinler KALICI
    olarak veriye yazılmış olabilir — normal pd.fillna("") bunu YAKALAMAZ
    (ortada geçerli bir string vardır, gerçek NaN/None değil). Kullanıcıya
    gösterilecek HER DataFrame, render edilmeden hemen önce bu fonksiyondan
    geçirilir. Series.map (applymap DEĞİL — yeni pandas sürümlerinde
    kaldırıldı) ile HÜCRE HÜCRE kontrol eder; böylece baştaki/sondaki
    boşluklu ('None ') veya farklı büyük-küçük harfli ('NONE') varyasyonlar
    da (basit birebir .replace()'in kaçırabileceği durumlar) yakalanır."""
    try:
        return _df.apply(lambda _kol: _kol.map(_hic_none_hucre_temizle))
    except Exception:
        try:
            return _df.replace(to_replace=_NONE_METIN_LISTESI, value="")
        except Exception:
            return _df


_CARI_RUT_ANAHTAR = "_cari_rut_atamalari"


def _cari_rut_kaydet(_sozluk):
    """GÜVENLİ (bkz. _tedarikci_kaydet ile aynı desen) — SİLME YOK, satır
    varsa UPDATE, yoksa INSERT."""
    try:
        sb = get_sb_client()
        if not sb:
            return False
        _deger = json.dumps(_sozluk, ensure_ascii=False)
        _guncelle = sb.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", _CARI_RUT_ANAHTAR).execute()
        if not _guncelle.data:
            sb.table("kullanici_tercih").insert({
                "kullanici": "__liste_ui__", "anahtar": _CARI_RUT_ANAHTAR, "deger": _deger
            }).execute()
        return True
    except Exception:
        return False


def _cari_gerceklesen_ciro_ekle(_cari_id, _miktar):
    """Kargo kaydı eklenince/düzenlenince/silinince, ana Cari Liste'deki
    müşterinin 'gerçekleşen ciro' alanını otomatik günceller — _miktar
    pozitifse artırır, negatifse azaltır (0'ın altına düşürmez). Böylece
    kargo girdikçe müşterinin gerçekleşen cirosu (ve buna bağlı segment —
    Özel Müşteri/Portföy) elle dokunmadan kendiliğinden güncel kalır."""
    try:
        _miktar = float(_miktar or 0)
    except Exception:
        return
    if not _miktar:
        return
    try:
        _sb_gc = get_sb_client()
        if not _sb_gc:
            return
        _r_gc = _sb_gc.table("cari_kartlar").select("gerceklesen_ciro").eq("id", int(_cari_id)).execute()
        if not _r_gc.data:
            return
        _mevcut = float(_r_gc.data[0].get("gerceklesen_ciro") or 0)
        _yeni = max(0.0, round(_mevcut + _miktar, 2))
        _sb_gc.table("cari_kartlar").update({"gerceklesen_ciro": _yeni}).eq("id", int(_cari_id)).execute()
        try:
            get_cari_listesi.clear()
        except Exception:
            pass
    except Exception:
        pass


@st.cache_resource
def get_sb_service():
    """Supabase service_role client — log ve admin işlemler için"""
    try:
        from supabase import create_client
        url = st.secrets.get("SUPABASE_URL","")
        # Önce service key dene, yoksa normal key
        key = st.secrets.get("SUPABASE_SERVICE_KEY","") or st.secrets.get("SUPABASE_KEY","")
        if url and key:
            return create_client(url, key)
    except:
        pass
    return None

def hesapla_segment(manuel_segment, gerceklesen_ciro):
    """Manuel segment varsa onu normalize et, yoksa ciroya göre otomatik hesapla"""
    # Normalize — eski kayıtlardaki farklı ikonları düzelt
    _norm = {"⭐ A+":"👑 A+","A+":"👑 A+","⭐ A-":"⭐ A","A":"⭐ A","A-":"⭐ A","B":"🔵 B","C":"⚪ C"}
    if manuel_segment:
        _m = str(manuel_segment).strip()
        if _m and _m not in ["","--","nan","None"]:
            # Önce tam eşleşme dene
            if _m in ["👑 A+","⭐ A","🔵 B","⚪ C"]: return _m
            # Sonra normalize
            for _k,_v in _norm.items():
                if _k in _m: return _v
            return _m
    ger = float(gerceklesen_ciro or 0)
    if ger >= 500000: return "👑 A+"
    if ger >= 200000: return "⭐ A"
    if ger >= 50000:  return "🔵 B"
    if ger > 0:       return "⚪ C"
    return ""

def segment_renk(seg):
    """Segment → arka plan ve yazı rengi"""
    s = str(seg or "")
    if "A+" in s: return "#fef3c7","#92400e","#f59e0b"  # bg, text, border
    if "A"  in s: return "#f1f5f9","#475569","#94a3b8"
    if "B"  in s: return "#eff6ff","#1e40af","#3b82f6"
    if "C"  in s: return "#f8fafc","#64748b","#cbd5e1"
    return "#ffffff","#374151","#e2e8f0"

def get_supabase():
    return get_sb_client()

def _tel_gruplu(s):
    """Ham rakamlardan '541 357 80 20' gibi gruplu, baştaki 0/90'sız görünüm
    oluşturur. 10 haneli bir GSM/sabit numarasına indirgenemiyorsa (eksik/
    hatalı veri), veri kaybı olmasın diye olduğu gibi bırakır.
    Float ".0" artığını (2163679000.0 gibi) da kendi içinde temizler —
    çağıran taraf ayrıca temizlemek zorunda değil."""
    if not s:
        return s
    _s = str(s).strip()
    if _s.endswith(".0"):
        _s = _s[:-2]
    _digits = "".join(ch for ch in _s if ch.isdigit())
    if _digits.startswith("90") and len(_digits) == 12:
        _digits = _digits[2:]
    elif _digits.startswith("0") and len(_digits) == 11:
        _digits = _digits[1:]
    if len(_digits) == 10:
        return f"{_digits[0:3]} {_digits[3:6]} {_digits[6:8]} {_digits[8:10]}"
    return s

def _telefon_temizle(seri):
    """5413578020.0 gibi float telefonları '541 357 80 20' gruplu gösterime çevirir"""
    def _tek(v):
        if v is None:
            return ""
        s = str(v).strip()
        if s.lower() in ["nan", "none", ""]:
            return ""
        # Float .0 temizle
        if s.endswith(".0"):
            s = s[:-2]
        # Bilimsel notasyon temizle (1e+10 gibi)
        try:
            if "e" in s.lower() or "E" in s:
                s = str(int(float(s)))
        except:
            pass
        return _tel_gruplu(s)
    return seri.apply(_tek)

def _atama_filtresi_uygula(df):
    """Admin hepsini görür, diğerleri sadece kendine atananları"""
    try:
        _rol = str(st.session_state.get("rol","")).strip().lower()
        _kul = str(st.session_state.get("kullanici","")).strip()
        # Admin veya kullanıcı yoksa hepsini göster
        if "admin" in _rol or _kul == "admin" or not _kul:
            return df
        if df.empty or "atanan_kullanici" not in df.columns:
            return df
        # Kullanıcıya atananlar VEYA atanmamışlar
        return df[
            (df["atanan_kullanici"].astype(str) == _kul) |
            (df["atanan_kullanici"].isna()) |
            (df["atanan_kullanici"].astype(str).isin(["None","nan",""]))
        ]
    except:
        return df

# ── BÖLGE EŞLEŞTİRME (il + ilçe → bölge adı) ────────────────────────────────
_BL_ISTANBUL_ANADOLU = {"adalar","atasehir","beykoz","cekmekoy","kadikoy","kartal",
    "maltepe","pendik","sancaktepe","sultanbeyli","sile","tuzla","umraniye","uskudar"}
_BL_ISTANBUL_AVRUPA = {"arnavutkoy","avcilar","bagcilar","bahcelievler","bakirkoy",
    "basaksehir","bayrampasa","besiktas","beylikduzu","beyoglu","buyukcekmece",
    "catalca","esenler","esenyurt","eyupsultan","fatih","gaziosmanpasa","gungoren",
    "kagithane","kucukcekmece","sariyer","silivri","sisli","zeytinburnu","sultangazi"}
# Yaygın mahalle/semt isimleri → resmi ilçe (kişiler genelde resmi ilçe yerine
# bilindik semt adını yazar, bunları da tanıyalım ki Havuz'da takılı kalmasınlar)
_BL_ISTANBUL_MAHALLE_ILCE = {
    "yenibosna":"bahcelievler","bahcesehir":"basaksehir","atakoy":"bakirkoy",
    "florya":"bakirkoy","yesilkoy":"bakirkoy","halkali":"kucukcekmece",
    "levent":"besiktas","etiler":"besiktas","ortakoy":"besiktas","bebek":"besiktas",
    "nisantasi":"sisli","mecidiyekoy":"sisli","maslak":"sariyer",
    "taksim":"beyoglu","karakoy":"beyoglu","cihangir":"beyoglu","galata":"beyoglu",
    "balat":"fatih","sultanahmet":"fatih","aksaray":"fatih","topkapi":"fatih",
    "merter":"gungoren","bostanci":"kadikoy","suadiye":"kadikoy",
    "fenerbahce":"kadikoy","kozyatagi":"kadikoy","acibadem":"uskudar",
    "camlica":"uskudar","kisikli":"uskudar","kavacik":"beykoz",
}
_BL_IL_ADI = {
    "tekirdag":"Tekirdağ","kocaeli":"Kocaeli","bursa":"Bursa","manisa":"Manisa",
    "ankara":"Ankara","konya":"Konya","eskisehir":"Eskişehir","denizli":"Denizli","aydin":"Aydın",
}
# 81 ilin TAMAMININ doğru yazımı — Türkçe .title() İ/I sorunu yüzünden yanlış
# yazılmasın (ör. "İZMİR".title() bozuk çıkar) diye .title() yerine bu kaynaktan okunur.
_BL_TUM_ILLER_DOGRU_YAZIM = ["Adana","Adıyaman","Afyonkarahisar","Ağrı","Amasya","Ankara",
    "Antalya","Artvin","Aydın","Balıkesir","Bilecik","Bingöl","Bitlis","Bolu","Burdur",
    "Bursa","Çanakkale","Çankırı","Çorum","Denizli","Diyarbakır","Edirne","Elazığ",
    "Erzincan","Erzurum","Eskişehir","Gaziantep","Giresun","Gümüşhane","Hakkari","Hatay",
    "Isparta","Mersin","İstanbul","İzmir","Kars","Kastamonu","Kayseri","Kırklareli",
    "Kırşehir","Kocaeli","Konya","Kütahya","Malatya","Manisa","Kahramanmaraş","Mardin",
    "Muğla","Muş","Nevşehir","Niğde","Ordu","Rize","Sakarya","Samsun","Siirt","Sinop",
    "Sivas","Tekirdağ","Tokat","Trabzon","Tunceli","Şanlıurfa","Uşak","Van","Yozgat",
    "Zonguldak","Aksaray","Bayburt","Karaman","Kırıkkale","Batman","Şırnak","Bartın",
    "Ardahan","Iğdır","Yalova","Karabük","Kilis","Osmaniye","Düzce"]

def _bl_sadelestir(s):
    s = str(s or "").strip().lower()
    for _k,_v in {"ı":"i","i̇":"i","ş":"s","ğ":"g","ü":"u","ö":"o","ç":"c"}.items():
        s = s.replace(_k,_v)
    return s

_BL_TUM_ILLER_ADI = {_bl_sadelestir(_ad): _ad for _ad in _BL_TUM_ILLER_DOGRU_YAZIM}

def il_ilce_bolge_bul(il, ilce):
    """il+ilçe bilgisinden bölge adı üretir. İl doluysa MUTLAKA bir bölge olur —
    tanımlı 11 bölgeden biriyse o isimle, değilse ilin kendi adıyla. Sadece il
    tamamen BOŞSA — veya İstanbul'un ilçesi Anadolu/Avrupa listesinde yoksa (manuel
    toplu atama için) — Havuz'a düşer."""
    _il = _bl_sadelestir(il)
    _ilce = _bl_sadelestir(ilce)
    if not _il:
        return None  # il tamamen boşsa Havuz
    if "istanbul" in _il:
        # Önce birebir eşleşme dene (hızlı ve kesin)
        _ilce_eslesen = _BL_ISTANBUL_MAHALLE_ILCE.get(_ilce, _ilce)
        if _ilce_eslesen in _BL_ISTANBUL_ANADOLU:
            return "İstanbul Anadolu"
        if _ilce_eslesen in _BL_ISTANBUL_AVRUPA:
            return "İstanbul Avrupa"
        # Birebir eşleşmediyse — hücrede ilçe adı GEÇİYOR mu diye bak
        # ("Sultanbeyli Mah.", "Sultanbeyli/İstanbul" gibi ekstra kelimeli hücreler için)
        if _ilce:
            for _resmi_ilce in _BL_ISTANBUL_ANADOLU:
                if _resmi_ilce in _ilce:
                    return "İstanbul Anadolu"
            for _resmi_ilce in _BL_ISTANBUL_AVRUPA:
                if _resmi_ilce in _ilce:
                    return "İstanbul Avrupa"
            for _mahalle, _resmi_ilce in _BL_ISTANBUL_MAHALLE_ILCE.items():
                if _mahalle in _ilce:
                    return "İstanbul Anadolu" if _resmi_ilce in _BL_ISTANBUL_ANADOLU else "İstanbul Avrupa"
        return None  # ilçe hiçbir şekilde eşleşmiyor — Havuz'da kalır, manuel toplu atama için
    if _il in _BL_IL_ADI:
        return _BL_IL_ADI[_il]
    # Tanımlı 11 bölgeden biri değil ama il doluysa — ilin kendi adı bölge olur.
    # 81 il listesindeyse doğru yazımıyla (ikon eşleşsin diye), değilse .title() ile.
    if _il in _BL_TUM_ILLER_ADI:
        return _BL_TUM_ILLER_ADI[_il]
    return str(il).strip().title()

@st.cache_data(ttl=60)
def get_cari_listesi():
    """60 sn cache'li cari listesi — HTTP Range ile limitsiz çek.
    GÜVENLİ (2026-09 düzeltmesi): eskiden bir ara sayfa (batch) ağ hatasına
    takılırsa liste SESSİZCE YARIM kalıp (ör. 3700 yerine 1800 kayıt)
    DOĞRUYMUŞ gibi 60 saniye önbelleğe alınıyordu — kullanıcı 'müşteriler
    kayboldu' diye endişeleniyordu, oysa hiçbir veri silinmemişti, sadece
    YARIM YÜKLENİYORDU. Şimdi: her sayfa en fazla 3 kez denenir; TÜM
    denemeler başarısız olursa o ana kadar toplanan (güvenilir olmayan)
    sonuç TAMAMEN ATILIR ve ikinci yönteme (supabase-py ile, AYNI ŞEKİLDE
    tam sayfalanmış) geçilir — asla yarım bir liste 'tam liste'ymiş gibi
    döndürülmez."""
    import requests as _rq
    import time as _cl_time
    _url = st.secrets.get("SUPABASE_URL","")
    _key = st.secrets.get("SUPABASE_SERVICE_KEY","") or st.secrets.get("SUPABASE_KEY","")
    _tum = []
    _pagination_guvenilir = False
    if _url and _key:
        try:
            _offset = 0
            while True:
                _hdrs = {
                    "apikey": _key,
                    "Authorization": f"Bearer {_key}",
                    "Range-Unit": "items",
                    "Range": f"{_offset}-{_offset+999}"
                }
                _batch = None
                for _deneme_cl in range(3):
                    try:
                        _r = _rq.get(
                            f"{_url}/rest/v1/cari_kartlar?select=*&order=id.asc",
                            headers=_hdrs, timeout=30
                        )
                        if _r.status_code in [200, 206]:
                            _batch = _r.json()
                            break
                    except Exception:
                        pass
                    _cl_time.sleep(0.5)
                if _batch is None:
                    # 3 denemede de başarısız — bu sonucu GÜVENİLİR SAYMA,
                    # ikinci yönteme düş (yarım listeyi asla döndürme).
                    _tum = []
                    _pagination_guvenilir = False
                    break
                if not _batch:
                    _pagination_guvenilir = True
                    break
                _tum.extend(_batch)
                if len(_batch) < 1000:
                    _pagination_guvenilir = True
                    break
                _offset += 1000
        except Exception:
            _tum = []
            _pagination_guvenilir = False
    if not _pagination_guvenilir:
        try:
            sb = get_sb_client()
            if sb:
                _tum2 = []
                _offset2 = 0
                while True:
                    _r2 = sb.table("cari_kartlar").select("*").order("id", desc=False).range(
                        _offset2, _offset2 + 999).execute()
                    _batch2 = _r2.data or []
                    _tum2.extend(_batch2)
                    if len(_batch2) < 1000:
                        break
                    _offset2 += 1000
                if _tum2:
                    _tum = _tum2
        except Exception:
            pass
    _df_g = pd.DataFrame(_tum) if _tum else pd.DataFrame()
    if not _df_g.empty:
        if "silindi" in _df_g.columns:
            _df_g = _df_g[~(_df_g["silindi"].astype(str).str.strip().isin(["1","True","true","1.0"]))]
        for _tk in ["gsm","sabit"]:
            if _tk in _df_g.columns:
                _df_g[_tk] = _telefon_temizle(_df_g[_tk])
    return _df_g
    try:
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM cari_kartlar WHERE silindi=0 OR silindi='0' OR silindi IS NULL ORDER BY firma", conn)
        conn.close()
        for _tk in ["gsm","sabit"]:
            if _tk in df.columns:
                df[_tk] = _telefon_temizle(df[_tk])
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=120)
def get_kullanici_listesi():
    """2 dk cache'li kullanıcı listesi"""
    return db_read("kullanicilar", extra_sql="")

def db_read(table, filters=None, order_col="id", desc=True, limit=None, extra_sql=None):
    """Supabase veya SQLite'dan DataFrame döner"""
    sb = get_sb_client()
    if sb:
        try:
            q = sb.table(table).select("*")
            if filters:
                for k, v in filters.items():
                    if v == "NOT_NULL":
                        q = q.not_.is_(k, "null")
                    elif v == "neq_1":
                        q = q.neq(k, 1)
                    else:
                        q = q.eq(k, v)
            if order_col:
                q = q.order(order_col, desc=desc)
            if limit:
                q = q.limit(limit)
            res = q.execute()
            if res and res.data is not None:
                return pd.DataFrame(res.data) if res.data else pd.DataFrame()
            return pd.DataFrame()
        except Exception as _e_read:
            pass
    try:
        sql = f"SELECT * FROM {table}"
        if extra_sql:
            sql += f" {extra_sql}"
        conn = get_conn()
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()


def db_insert(table, data):
    """Insert — Supabase önce, SQLite fallback — firma_id otomatik eklenir"""
    sb = get_sb_client()
    _sb_hata = None
    if sb:
        try:
            res = sb.table(table).insert(data).execute()
            if res.data:
                return True
        except Exception as e:
            _sb_hata = str(e)
    # SQLite fallback
    try:
        conn = get_conn()
        cols = ", ".join(data.keys())
        vals = ", ".join(["?" for _ in data])
        conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({vals})", list(data.values()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.session_state["_last_db_error"] = f"Supabase: {_sb_hata} | SQLite: {e}"
        st.error(f"DB insert hatası ({table}): {e}")
    return False

def db_update(table, data, where_col, where_val):
    """Update — Supabase veya SQLite"""
    # 🚨 GÜVENLİK KİLİDİ (2026-09): "hesaplama" (Cari Liste'deki sadece
    # tetikleyici amaçlı, kalıcı bir veritabanı sütunu OLMAYAN alan) HANGİ
    # YOLDAN gelirse gelsin "cari_kartlar" tablosuna ASLA ulaşmasın diye son
    # bir güvenlik filtresi — hangi çağıran kod bunu unutursa unutsun, burada
    # kesin olarak süzülür.
    if table == "cari_kartlar" and isinstance(data, dict) and "hesaplama" in data:
        data = {k: v for k, v in data.items() if k != "hesaplama"}
        if not data:
            return True
    sb = get_sb_client()
    if sb:
        try:
            sb.table(table).update(data).eq(where_col, where_val).execute()
            return True
        except Exception as _e_up:
            # Supabase hata — SQLite'a dön
            pass
    try:
        conn = get_conn()
        sets = ", ".join([f"{k}=?" for k in data.keys()])
        conn.execute(f"UPDATE {table} SET {sets} WHERE {where_col}=?",
                    list(data.values()) + [where_val])
        conn.commit()
        conn.close()
        return True
    except Exception as _e_sq:
        pass
    return False

ILLER_ILCELER = {
    "Adana": ["Aladağ","Ceyhan","Çukurova","Feke","İmamoğlu","Karaisalı","Karataş","Kozan","Pozantı","Saimbeyli","Sarıçam","Seyhan","Tufanbeyli","Yumurtalık","Yüreğir"],
    "Adıyaman": ["Besni","Çelikhan","Gerger","Gölbaşı","Kahta","Merkez","Samsat","Sincik","Tut"],
    "Afyonkarahisar": ["Başmakçı","Bayat","Bolvadin","Çay","Çobanlar","Dazkırı","Dinar","Emirdağ","Evciler","Hocalar","İhsaniye","İscehisar","Kızılören","Merkez","Sandıklı","Sinanpaşa","Sultandağı","Şuhut"],
    "Ağrı": ["Diyadin","Doğubayazıt","Eleşkirt","Hamur","Merkez","Patnos","Taşlıçay","Tutak"],
    "Amasya": ["Göynücek","Gümüşhacıköy","Hamamözü","Merkez","Merzifon","Suluova","Taşova"],
    "Ankara": ["Akyurt","Altındağ","Ayaş","Bala","Beypazarı","Çamlıdere","Çankaya","Çubuk","Elmadağ","Etimesgut","Evren","Gölbaşı","Güdül","Haymana","Kalecik","Kahramankazan","Keçiören","Kızılcahamam","Mamak","Nallıhan","Polatlı","Pursaklar","Sincan","Şereflikoçhisar","Yenimahalle"],
    "Antalya": ["Akseki","Aksu","Alanya","Demre","Döşemealtı","Elmalı","Finike","Gazipaşa","Gündoğmuş","İbradı","Kaş","Kemer","Kepez","Konyaaltı","Korkuteli","Kumluca","Manavgat","Muratpaşa","Serik"],
    "Artvin": ["Ardanuç","Arhavi","Borçka","Hopa","Merkez","Murgul","Şavşat","Yusufeli"],
    "Aydın": ["Bozdoğan","Buharkent","Çine","Didim","Efeler","Germencik","İncirliova","Karacasu","Karpuzlu","Koçarlı","Köşk","Kuşadası","Kuyucak","Merkez","Nazilli","Söke","Sultanhisar","Yenipazar"],
    "Balıkesir": ["Altıeylül","Ayvalık","Balya","Bandırma","Bigadiç","Burhaniye","Dursunbey","Edremit","Erdek","Gömeç","Gönen","Havran","İvrindi","Karesi","Kepsut","Manyas","Marmara","Savaştepe","Sındırgı","Susurluk"],
    "Bilecik": ["Bozüyük","Gölpazarı","İnhisar","Merkez","Osmaneli","Pazaryeri","Söğüt","Yenipazar"],
    "Bingöl": ["Adaklı","Genç","Karlıova","Kiğı","Merkez","Solhan","Yayladere","Yedisu"],
    "Bitlis": ["Adilcevaz","Ahlat","Güroymak","Hizan","Merkez","Mutki","Tatvan"],
    "Bolu": ["Dörtdivan","Gerede","Göynük","Kıbrıscık","Mengen","Merkez","Mudurnu","Seben","Yeniçağa"],
    "Burdur": ["Ağlasun","Altınyayla","Bucak","Çavdır","Çeltikçi","Gölhisar","Karamanlı","Kemer","Merkez","Tefenni","Yeşilova"],
    "Bursa": ["Büyükorhan","Gemlik","Gürsu","Harmancık","İnegöl","İznik","Karacabey","Keles","Kestel","Mudanya","Mustafakemalpaşa","Nilüfer","Orhaneli","Orhangazi","Osmangazi","Yıldırım","Yenişehir"],
    "Çanakkale": ["Ayvacık","Bayramiç","Biga","Bozcaada","Çan","Eceabat","Ezine","Gelibolu","Gökçeada","Lapseki","Merkez","Yenice"],
    "Çankırı": ["Atkaracalar","Bayramören","Çerkeş","Eldivan","Ilgaz","Kızılırmak","Korgun","Kurşunlu","Merkez","Orta","Şabanözü","Yapraklı"],
    "Çorum": ["Alaca","Bayat","Boğazkale","Dodurga","İskilip","Kargı","Laçin","Mecitözü","Merkez","Oğuzlar","Ortaköy","Osmancık","Sungurlu","Uğurludağ"],
    "Denizli": ["Acıpayam","Babadağ","Baklan","Bekilli","Beyağaç","Bozkurt","Buldan","Çal","Çameli","Çardak","Çivril","Güney","Honaz","Kale","Merkezefendi","Pamukkale","Sarayköy","Serinhisar","Tavas"],
    "Diyarbakır": ["Bağlar","Bismil","Çermik","Çınar","Çüngüş","Dicle","Eğil","Ergani","Hani","Hazro","Kayapınar","Kocaköy","Kulp","Lice","Silvan","Sur","Yenişehir"],
    "Düzce": ["Akçakoca","Cumayeri","Çilimli","Gölyaka","Gümüşova","Kaynaşlı","Merkez","Yığılca"],
    "Edirne": ["Enez","Havsa","İpsala","Keşan","Lalapaşa","Merkez","Meriç","Süloğlu","Uzunköprü"],
    "Elazığ": ["Ağın","Alacakaya","Arıcak","Baskil","Karakoçan","Keban","Kovancılar","Maden","Merkez","Palu","Sivrice"],
    "Erzincan": ["Çayırlı","İliç","Kemah","Kemaliye","Merkez","Otlukbeli","Refahiye","Tercan","Üzümlü"],
    "Erzurum": ["Aşkale","Aziziye","Çat","Hinis","Horasan","İspir","Karakoçan","Karayazı","Köprüköy","Merkez","Narman","Oltu","Olur","Palandöken","Pasinler","Pazaryolu","Şenkaya","Tekman","Tortum","Uzundere","Yakutiye"],
    "Eskişehir": ["Alpu","Beylikova","Çifteler","Günyüzü","Han","İnönü","Mahmudiye","Mihalgazi","Mihalıççık","Merkez","Odunpazarı","Sarıcakaya","Seyitgazi","Sivrihisar","Tepebaşı"],
    "Gaziantep": ["Araban","İslahiye","Karkamış","Nizip","Nurdağı","Oğuzeli","Şahinbey","Şehitkamil","Yavuzeli"],
    "Giresun": ["Alucra","Bulancak","Çamoluk","Çanakçı","Dereli","Doğankent","Espiye","Eynesil","Görele","Güce","Keşap","Merkez","Piraziz","Şebinkarahisar","Tirebolu","Yağlıdere"],
    "Gümüşhane": ["Kelkit","Köse","Kürtün","Merkez","Şiran","Torul"],
    "Hakkari": ["Çukurca","Derecik","Merkez","Şemdinli","Yüksekova"],
    "Hatay": ["Altınözü","Antakya","Arsuz","Belen","Defne","Dörtyol","Erzin","Hassa","İskenderun","Kırıkhan","Kumlu","Payas","Reyhanlı","Samandağ","Yayladağı"],
    "Iğdır": ["Aralık","Karakoyunlu","Merkez","Tuzluca"],
    "Isparta": ["Aksu","Atabey","Eğirdir","Gelendost","Gönen","Keçiborlu","Merkez","Senirkent","Sütçüler","Şarkikaraağaç","Uluborlu","Yalvaç","Yenişarbademli"],
    "İstanbul": ["Adalar","Arnavutköy","Ataşehir","Avcılar","Bağcılar","Bahçelievler","Bakırköy","Başakşehir","Bayrampaşa","Beşiktaş","Beykoz","Beylikdüzü","Beyoğlu","Büyükçekmece","Çatalca","Çekmeköy","Esenler","Esenyurt","Eyüpsultan","Fatih","Gaziosmanpaşa","Güngören","Kadıköy","Kağıthane","Kartal","Küçükçekmece","Maltepe","Pendik","Sancaktepe","Sarıyer","Silivri","Sultanbeyli","Sultangazi","Şile","Şişli","Tuzla","Ümraniye","Üsküdar","Zeytinburnu"],
    "İzmir": ["Aliağa","Balçova","Bayındır","Bayraklı","Bergama","Beydağ","Bornova","Buca","Çeşme","Çiğli","Dikili","Foça","Gaziemir","Güzelbahçe","Karabağlar","Karaburun","Karşıyaka","Kemalpaşa","Kınık","Kiraz","Konak","Menderes","Menemen","Narlıdere","Ödemiş","Seferihisar","Selçuk","Tire","Torbalı","Urla"],
    "Kahramanmaraş": ["Afşin","Andırın","Çağlayancerit","Dulkadiroğlu","Ekinözü","Elbistan","Göksun","Merkez","Nurhak","Onikişubat","Pazarcık","Türkoğlu"],
    "Karabük": ["Eflani","Eskipazar","Merkez","Ovacık","Safranbolu","Yenice"],
    "Karaman": ["Ayrancı","Başyayla","Ermenek","Kazımkarabekir","Merkez","Sarıveliler"],
    "Kars": ["Akyaka","Arpaçay","Digor","Kağızman","Merkez","Sarıkamış","Selim","Susuz"],
    "Kastamonu": ["Abana","Ağlı","Araç","Azdavay","Bozkurt","Cide","Çatalzeytin","Daday","Devrekani","Doğanyurt","Hanönü","İhsangazi","İnebolu","Küre","Merkez","Pınarbaşı","Seydiler","Şenpazar","Taşköprü","Tosya"],
    "Kayseri": ["Akkışla","Bünyan","Develi","Felahiye","Hacılar","İncesu","Kocasinan","Melikgazi","Özvatan","Pınarbaşı","Sarıoğlan","Sarız","Talas","Tomarza","Yahyalı","Yeşilhisar"],
    "Kırıkkale": ["Bahşili","Balışeyh","Çelebi","Delice","Karakeçili","Keskin","Merkez","Sulakyurt","Yahşihan"],
    "Kırklareli": ["Babaeski","Demirköy","Kofçaz","Lüleburgaz","Merkez","Pehlivanköy","Pınarhisar","Vize"],
    "Kırşehir": ["Akçakent","Akpınar","Boztepe","Çiçekdağı","Kaman","Merkez","Mucur"],
    "Kilis": ["Elbeyli","Merkez","Musabeyli","Polateli"],
    "Kocaeli": ["Başiskele","Çayırova","Darıca","Derince","Dilovası","Gebze","Gölcük","İzmit","Kandıra","Karamürsel","Kartepe","Körfez"],
    "Konya": ["Ahırlı","Akören","Akşehir","Altınekin","Beyşehir","Bozkır","Cihanbeyli","Çeltik","Çumra","Derbent","Derebucak","Doğanhisar","Emirgazi","Ereğli","Güneysınır","Hadim","Halkapınar","Hüyük","Ilgın","Kadınhanı","Karapınar","Karatay","Kulu","Meram","Sarayönü","Selçuklu","Seydişehir","Taşkent","Tuzlukçu","Yalıhüyük","Yunak"],
    "Kütahya": ["Altıntaş","Aslanapa","Çavdarhisar","Domaniç","Dumlupınar","Emet","Gediz","Hisarcık","Merkez","Pazarlar","Simav","Şaphane","Tavşanlı"],
    "Malatya": ["Akçadağ","Arapgir","Arguvan","Battalgazi","Darende","Doğanyol","Doğanşehir","Hekimhan","Kale","Kuluncak","Merkez","Pütürge","Yazıhan","Yeşilyurt"],
    "Manisa": ["Ahmetli","Akhisar","Alaşehir","Demirci","Gölmarmara","Gördes","Kırkağaç","Köprübaşı","Kula","Merkez","Salihli","Sarıgöl","Saruhanlı","Selendi","Soma","Şehzadeler","Turgutlu","Yunusemre"],
    "Mardin": ["Artuklu","Dargeçit","Derik","Kızıltepe","Mazıdağı","Merkez","Midyat","Nusaybin","Ömerli","Savur","Yeşilli"],
    "Mersin": ["Akdeniz","Anamur","Aydıncık","Bozyazı","Çamlıyayla","Erdemli","Gülnar","Mezitli","Mut","Silifke","Tarsus","Toroslar","Yenişehir"],
    "Muğla": ["Bodrum","Dalaman","Datça","Fethiye","Kavaklıdere","Köyceğiz","Marmaris","Menteşe","Milas","Ortaca","Seydikemer","Ula","Yatağan"],
    "Muş": ["Bulanık","Hasköy","Korkut","Malazgirt","Merkez","Varto"],
    "Nevşehir": ["Acıgöl","Avanos","Derinkuyu","Gülşehir","Hacıbektaş","Kozaklı","Merkez","Ürgüp"],
    "Niğde": ["Altunhisar","Bor","Çamardı","Çiftlik","Merkez","Ulukışla"],
    "Ordu": ["Akkuş","Altınordu","Aybastı","Çamaş","Çatalpınar","Çaybaşı","Fatsa","Gölköy","Gülyalı","Gürgentepe","İkizce","Kabadüz","Kabataş","Korgan","Kumru","Mesudiye","Perşembe","Ulubey","Ünye"],
    "Osmaniye": ["Bahçe","Düziçi","Hasanbeyli","Kadirli","Merkez","Sumbas","Toprakkale"],
    "Rize": ["Ardeşen","Çamlıhemşin","Çayeli","Derepazarı","Fındıklı","Güneysu","Hemşin","İkizdere","İyidere","Kalkandere","Merkez","Pazar"],
    "Sakarya": ["Adapazarı","Akyazı","Arifiye","Erenler","Ferizli","Geyve","Hendek","Karapürçek","Karasu","Kaynarca","Kocaali","Mithatpaşa","Pamukova","Sapanca","Serdivan","Söğütlü","Taraklı"],
    "Samsun": ["Alaçam","Asarcık","Atakum","Ayvacık","Bafra","Canik","Çarşamba","İlkadım","Kavak","Ladik","Merkez","Ondokuzmayıs","Salıpazarı","Tekkeköy","Terme","Vezirköprü","Yakakent"],
    "Siirt": ["Baykan","Eruh","Kurtalan","Merkez","Pervari","Şirvan","Tillo"],
    "Sinop": ["Ayancık","Boyabat","Dikmen","Durağan","Erfelek","Gerze","Merkez","Saraydüzü","Türkeli"],
    "Sivas": ["Akıncılar","Altınyayla","Divriği","Doğanşar","Gemerek","Gölova","Gürun","Hafik","İmranlı","Kangal","Koyulhisar","Merkez","Suşehri","Şarkışla","Ulaş","Yıldızeli","Zara"],
    "Şanlıurfa": ["Akçakale","Birecik","Bozova","Ceylanpınar","Eyyübiye","Halfeti","Haliliye","Harran","Hilvan","Karaköprü","Merkez","Siverek","Suruç","Viranşehir"],
    "Şırnak": ["Beytüşşebap","Cizre","Güçlükonak","İdil","Merkez","Silopi","Uludere"],
    "Tekirdağ": ["Çerkezköy","Çorlu","Ergene","Hayrabolu","Malkara","Marmara Ereğlisi","Muratlı","Saray","Süleymanpaşa","Şarköy"],
    "Tokat": ["Almus","Artova","Başçiftlik","Erbaa","Merkez","Niksar","Pazar","Reşadiye","Sulusaray","Turhal","Yeşilyurt","Zile"],
    "Trabzon": ["Akçaabat","Araklı","Arsin","Beşikdüzü","Çarşıbaşı","Çaykara","Dernekpazarı","Düzköy","Hayrat","Köprübaşı","Maçka","Merkez","Of","Ortahisar","Sürmene","Şalpazarı","Tonya","Vakfıkebir","Yomra"],
    "Tunceli": ["Çemişgezek","Hozat","Mazgirt","Merkez","Nazımiye","Ovacık","Pertek","Pülümür"],
    "Uşak": ["Banaz","Eşme","Karahallı","Merkez","Sivaslı","Ulubey"],
    "Van": ["Bahçesaray","Başkale","Çaldıran","Çatak","Edremit","Erciş","Gevaş","Gürpınar","İpekyolu","Merkez","Muradiye","Özalp","Saray","Tuşba"],
    "Yalova": ["Altınova","Armutlu","Çınarcık","Çiftlikköy","Merkez","Termal"],
    "Yozgat": ["Akdağmadeni","Aydıncık","Boğazlıyan","Çandır","Çayıralan","Çekerek","Kadışehri","Merkez","Saraykent","Sarıkaya","Şefaatli","Sorgun","Yenifakılı","Yerköy"],
    "Zonguldak": ["Alaplı","Çaycuma","Devrek","Gökçebey","Kilimli","Kozlu","Merkez"],
}

# ── VERİTABANI ───────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect("mw_crm.db", check_same_thread=False)

def otomatik_yedek():
    """Her gun otomatik yedek alir (sadece SQLite modunda)"""
    if sb_or_sqlite():
        return  # Supabase modunda yedek gerekmez
    try:
        if not os.path.exists("mw_crm.db"):
            return
        bugun = datetime.now().strftime("%Y-%m-%d")
        yedek_klasor = "backups"
        os.makedirs(yedek_klasor, exist_ok=True)
        db_yedek = os.path.join(yedek_klasor, f"mw_crm_{bugun}.db")
        if not os.path.exists(db_yedek):
            shutil.copy2("mw_crm.db", db_yedek)
    except:
        pass

otomatik_yedek()


# ── KULLANICI LOG FONKSİYONU ──────────────────────────────────────────────────
def kullanici_log_kaydet(islem, sayfa="", detay=""):
    """Her işlemi logla — service_role key ile Supabase'e yaz"""
    try:
        if not st.session_state.get("giris", False): return
        _sb_log = get_sb_service()
        if not _sb_log: return
        _sb_log.table("kullanici_log").insert({
            "kullanici": str(st.session_state.get("kullanici", "?")),
            "rol":       str(st.session_state.get("rol", "?")),
            "sayfa":     str(sayfa or st.session_state.get("aktif_tab", "")),
            "islem":     str(islem),
            "detay":     str(detay)[:500],
        }).execute()
    except:
        pass

def sayfa_log(sayfa):
    """Sayfa değişince logla — önceki sayfa farklıysa yaz"""
    try:
        _onceki = st.session_state.get("_son_sayfa", "")
        if _onceki != sayfa:
            st.session_state["_son_sayfa"] = sayfa
            kullanici_log_kaydet("SAYFA_GİRİŞİ", sayfa, f"→ {sayfa}")
    except:
        pass
    # Sekme başlığını güncelle
    _menu_adlari = {
        "yeni": "Yeni Kart", "liste": "Cari Liste",
        "excel": "Excel", "kullanici": "Kullanıcılar",
        "dis_nakliye": "Dış Nakliye", "dis_nakliye_toplu": "Dış Nakliyeler Listesi",
    }
    _ad = _menu_adlari.get(sayfa, sayfa)



def _tanimlar_yukle(tip):
    """sistem_tanimlar tablosundan aşama/durum listesi çek"""
    _sb = get_sb_client()
    _liste = []
    try:
        if _sb:
            _r = _sb.table("sistem_tanimlar").select("deger").eq("tip", tip).order("sira").execute()
            if _r.data:
                # Duplicate temizle — sırayı koru
                _goruldu = set()
                for d in _r.data:
                    _v = str(d["deger"] or "").strip()
                    if _v and _v not in _goruldu:
                        _liste.append(_v)
                        _goruldu.add(_v)
    except: pass

    # cari_kartlar'daki değerleri de ekle — eksik olanları sistem_tanimlar'a yaz
    try:
        if _sb:
            _kolon = "islem_asamasi" if tip == "asama" else "durum"
            _cr = _sb.table("cari_kartlar").select(_kolon).execute()
            if _cr.data:
                _mevcut_max = len(_liste)
                for _row in _cr.data:
                    _val = str(_row.get(_kolon,"") or "").strip()
                    if _val and _val != "nan" and _val not in _liste:
                        _liste.append(_val)
                        # sistem_tanimlar'a da ekle
                        try:
                            _mevcut_max += 1
                            _sb.table("sistem_tanimlar").insert({
                                "tip": tip,
                                "deger": _val,
                                "sira": _mevcut_max
                            }).execute()
                        except: pass
    except: pass

    if _liste:
        if tip == "durum":
            _gizli_durumlar = {"aktif", "pasif", "hedef"}
            _liste = [x for x in _liste if x.strip().lower() not in _gizli_durumlar]
        return _liste

    # Fallback
    if tip == "asama":
        return ["Arama","Tekrar Ara","Randevu","Teklif","Fiyat Hazırla","Deneme","Sözleşme","Kazanıldı","Kaybedildi","Devam Ediyor"]
    return []

def giris_ekrani():
    # ── KÜÇÜK & YUKARIDA GÖRÜNÜM İÇİN CSS ──────────────────────────────────────
    st.markdown("""
<style>
header[data-testid="stHeader"]{display:none !important;}
section[data-testid="stMain"]{align-items:flex-start !important;}
div[data-testid="stAppViewContainer"]{align-items:flex-start !important;}
.block-container{padding-top:0.3rem !important;padding-bottom:0.5rem !important;}
div[data-testid="stVerticalBlock"]{gap:0.3rem !important;}
div[data-testid="stElementContainer"]:has(style){display:contents !important;}
div[data-testid="stElementContainer"]:has(script){display:contents !important;}
div[data-testid="stForm"]{border:none;padding:0;}
div[data-testid="stForm"] .stTextInput input{font-size:11px;padding:0.25rem 0.5rem;height:1.8rem;}
div[data-testid="stForm"] label{font-size:10px;}
div[data-testid="stForm"] button{font-size:11px;padding:0.25rem 0.5rem;height:1.8rem;min-height:1.8rem;}
div[data-testid="stRadio"] label{font-size:10px;}
div[data-testid="stRadio"] div[role="radiogroup"]{gap:0.4rem;}
</style>
""", unsafe_allow_html=True)

    # ── LOGO ──────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;padding:0.1rem 0 0.3rem;">
  <div style="width:28px;height:28px;background:#1d4ed8;border-radius:8px;
       display:inline-flex;align-items:center;justify-content:center;margin-bottom:5px;">
    <svg width="16" height="16" viewBox="0 0 36 36" fill="none">
      <rect x="4" y="4" width="12" height="12" rx="2" fill="white" opacity=".9"/>
      <rect x="20" y="4" width="12" height="12" rx="2" fill="white" opacity=".7"/>
      <rect x="4" y="20" width="12" height="12" rx="2" fill="white" opacity=".7"/>
      <rect x="20" y="20" width="12" height="12" rx="2" fill="white" opacity=".5"/>
    </svg>
  </div>
  <div style="font-size:13px;font-weight:600;color:#0f172a;letter-spacing:-.5px;">MWCRMPRO</div>
  <div style="font-size:9px;color:#64748b;margin-top:2px;margin-bottom:8px;">Cari Yönetim Sistemi</div>
</div>
""", unsafe_allow_html=True)

    _gc1, _gc2, _gc3 = st.columns([5,2,5])
    with _gc2:
        # ── CİHAZ SEÇİMİ — radio buton ile, rerun YOK ────────────────────────
        st.markdown("""
<div style="background:white;border:0.5px solid #e2e8f0;border-radius:8px;
     padding:8px 8px 6px;margin-bottom:6px;">
  <div style="font-size:9px;color:#64748b;text-align:center;margin-bottom:6px;font-weight:500;">
    Hangi cihazdan bağlanıyorsunuz?
  </div>
</div>
""", unsafe_allow_html=True)
        _cihaz = st.radio(
            "Cihaz",
            options=["🖥️  Masaüstü / Laptop", "📱  Telefon / Tablet"],
            horizontal=True,
            label_visibility="collapsed",
            key="giris_cihaz_radio"
        )
        _mobil_secildi = "Telefon" in _cihaz

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── GİRİŞ FORMU ────────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("""
<div style="font-size:11px;font-weight:600;color:#0f172a;margin-bottom:10px;">Giriş Yap</div>
""", unsafe_allow_html=True)

            with st.form("giris_form", clear_on_submit=False):
                kullanici = st.text_input("Kullanıcı Adı", placeholder="kullanici_adi")
                sifre     = st.text_input("Şifre", type="password", placeholder="••••••••")
                _giris_btn = st.form_submit_button("Giriş Yap →", use_container_width=True, type="primary")

        if _giris_btn:
            row = None
            # 1. Supabase
            try:
                from supabase import create_client
                url = st.secrets.get("SUPABASE_URL","")
                key = st.secrets.get("SUPABASE_KEY","")
                if url and key:
                    sb = create_client(url, key)
                    res = sb.table("kullanicilar").select("*").eq("kullanici_adi", kullanici).eq("sifre", sifre).execute()
                    if res.data:
                        row = res.data[0]
            except: pass
            # 2. SQLite fallback
            if row is None:
                try:
                    conn = get_conn()
                    r = conn.execute("SELECT * FROM kullanicilar WHERE kullanici_adi=? AND sifre=?", (kullanici, sifre)).fetchone()
                    conn.close()
                    if r:
                        row = {"kullanici_adi": r[1], "sifre": r[2], "rol": r[3]}
                except: pass
            # 3. Hardcoded admin
            if row is None and kullanici == "admin" and sifre == "admin123":
                row = {"kullanici_adi": "admin", "sifre": "admin123", "rol": "admin"}

            if row:
                rol_val = str(row.get("rol") or "") if isinstance(row, dict) else ""
                if not rol_val or rol_val == "None":
                    rol_val = "admin" if kullanici == "admin" else "kullanici"
                try:
                    import json as _yjson
                    _yetki_val = str(row.get("yetkiler","tam") or "tam")
                    _yetki = "tam" if _yetki_val == "tam" else _yjson.loads(_yetki_val)
                except:
                    _yetki = "tam"
                _firma_id_giris = 1

                # Tüm state'i tek seferde set et — kopma olmasın
                st.session_state.update({
                    "giris":            True,
                    "kullanici":        kullanici,
                    "kullanici_ad":     kullanici,
                    "rol":              rol_val,
                    "aktif_tab":        "liste",
                    "_yetki_listesi":   _yetki,
                    "_mobil_mod":       _mobil_secildi,
                    "_ekran_kontrol":   True,
                    "giris_cihaz":      "mobil" if _mobil_secildi else "masaustu",
                })
                # localStorage'a kaydet — sayfa yenilenince otomatik giriş
                _ls_veri = json.dumps({"kullanici": kullanici, "sifre": sifre, "mobil": _mobil_secildi})
                st.markdown(f"""<script>
try{{localStorage.setItem('mwcrm_oturum', {repr(_ls_veri)});}}catch(e){{}}
</script>""", unsafe_allow_html=True)
                # Giriş logla
                try:
                    _sb_logi = get_sb_client()
                    if _sb_logi:
                        _sb_logi.table("kullanici_log").insert({
                            "kullanici": kullanici, "rol": rol_val,
                            "sayfa": "giris", "islem": "GİRİŞ_YAPILDI",
                            "detay": f"{kullanici} sisteme giriş yaptı",
                        }).execute()
                except: pass
                st.rerun()
            else:
                st.error("❌ Kullanıcı adı veya şifre hatalı!")

def cikis():
    try:
        _sb_logc = get_sb_client()
        if _sb_logc and st.session_state.get("kullanici"):
            _sb_logc.table("kullanici_log").insert({
                "kullanici": st.session_state.get("kullanici","?"),
                "rol":       st.session_state.get("rol","?"),
                "sayfa":     "cikis",
                "islem":     "ÇIKIŞ_YAPILDI",
                "detay":     f"{st.session_state.get('kullanici','?')} sistemden çıkış yaptı",
            }).execute()
    except: pass
    st.session_state.clear()
    st.markdown("""<script>
try{localStorage.removeItem('mwcrm_oturum');}catch(e){}
</script>""", unsafe_allow_html=True)
    st.rerun()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
_sayfa_adlari_cfg = {
    "yeni":"Yeni Kart","liste":"Cari Liste",
    "excel":"Excel","kullanici":"Kullanıcılar",
    "dis_nakliye":"Dış Nakliye","dis_nakliye_toplu":"Dış Nakliyeler Listesi",
}
_aktif_cfg = st.session_state.get("aktif_tab","liste")
_baslik_cfg = "MWCRMPRO | " + _sayfa_adlari_cfg.get(_aktif_cfg,"MWCRMPRO")
st.set_page_config(page_title=_baslik_cfg, layout="wide", initial_sidebar_state="expanded")

# ── UYGULAMAYI HER ZAMAN AÇIK TEMADA SABİTLE ─────────────────────────────────
# Bazı bilgisayarlarda Windows/tarayıcı karanlık mod (dark mode) kullanıyor,
# Streamlit da otomatik koyu temaya geçiyor — ama uygulamanın tasarımı hep
# açık tema (beyaz zemin, koyu yazı) varsayımıyla yapıldı. Koyu modda bazı
# yazılar koyu zemin üstünde koyu kalıp okunmaz oluyordu. Bu blok, Streamlit'in
# kendi renk değişkenlerini zorla açık temaya sabitler — hangi bilgisayarda,
# hangi sistem/tarayıcı ayarıyla açılırsa açılsın görünüm hep aynı kalır.
st.markdown("""
<style>
:root, html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    color-scheme: light !important;
    --background-color: #ffffff !important;
    --secondary-background-color: #f8fafc !important;
    --text-color: #0f172a !important;
    --primary-color: #ef4444 !important;
}
[data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container,
section[data-testid="stMain"], section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
section[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
}

/* ── KOMPAKT MOD — tüm sistem genelinde gerçek küçültme ──────────────────
   NOT: Tablo (data_editor) canvas ile çizildiği için normal font-size CSS'i
   onu küçültemiyor. "zoom" özelliği tarayıcının PİKSEL bazında her şeyi
   (canvas dahil) küçültmesini sağlar — gerçek/kalıcı çözüm budur. */
[data-testid="stAppViewContainer"] { zoom: 0.95 !important; }
section[data-testid="stSidebar"] { zoom: 0.95 !important; }
html { font-size: 14px !important; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 1.5rem !important; }
section[data-testid="stSidebar"] .block-container { padding-top: 1rem !important; }
/* Streamlit 1.40+ konteyner sınıfını değiştirdi — eski .block-container artık
   gerçek genişlik konteynerine denk gelmiyor, sayfa "wide" modda bile dar
   kalıyordu. Yeni gerçek konteyner buradaki data-testid — tüm sayfalarda
   tam genişlik için bunu da hedefliyoruz. */
[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
[data-testid="stAppViewContainer"] { max-width: 100% !important; }
[data-testid="stAppViewContainer"] > .main { max-width: 100% !important; }
/* ── VERİ TABLOSU (data_editor/dataframe) TAM GENİŞLİK ────────────────────
   Glide tabanlı tablo bileşeni kendi dış kutusunun genişliğine göre kolon
   alanını hesaplıyor. use_container_width=True tek başına her zaman tam
   genişliğe ulaşmadığı için dış kapsayıcıyı burada CSS ile zorluyoruz —
   böylece rapor barındaki (GENEL/AŞAMA/...) tam genişlikli HTML tabloyla
   Cari Liste tablosunun sağ kenarı denk gelir, sağda boşluk kalmaz. */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"],
[data-testid="stDataFrame"] > div, [data-testid="stDataFrameResizable"] > div {
    width: 100% !important;
    max-width: 100% !important;
}
/* Dış kapsayıcı, içindeki tablo canvas'ından daha dar kalınca KENDİ yatay
   kaydırma çubuğunu da gösteriyordu — tablonun asıl (alttaki) scrollbar'ıyla
   birlikte İKİ tane üst üste görünüyordu. Dış kapsayıcının kendi scrollbar'ını
   kapatıyoruz, asıl/doğru scrollbar (tablonun kendi iç scrollbar'ı) kalıyor. */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
    overflow-x: hidden !important;
}
/* ── TABLO ARAÇ ÇUBUĞU (göz/indir/ara/tam ekran) ÜST ÜSTE BİNMESİN ────────
   Streamlit, fare tablonun üzerine gelince sağ üst köşede yüzen bir araç
   çubuğu gösteriyor; bu çubuk tablonun kendi kutusunun biraz dışına taşıp
   hemen üstündeki elemanın üzerine biniyordu. NOT: Önceki çözümde tüm
   tablolara margin-top eklemiştik ama bu, Cari Liste'deki sticky üst bar ve
   buton satırlarının konumunu kaydırıp YENİ bir üst üste binmeye yol açtı —
   o yüzden tablonun kendi kutusuna DOKUNMUYORUZ, sadece araç çubuğunun
   kendi float konumunu nazikçe aşağı itiyoruz.
*/
div[data-testid="stElementToolbar"] {
    z-index: 999 !important;
    transform: translateY(8px);
}
h1 { font-size: 1.6rem !important; }
h2 { font-size: 1.35rem !important; }
h3 { font-size: 1.15rem !important; }
h4, h5, h6 { font-size: 1rem !important; }
.stButton button, .stDownloadButton button { padding: 0.35rem 0.75rem !important; font-size: 0.85rem !important; }
section[data-testid="stSidebar"] .stButton button { padding: 0.4rem 0.6rem !important; font-size: 0.85rem !important; }
[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
.stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input { font-size: 0.85rem !important; }
[data-testid="stExpander"] summary { font-size: 0.9rem !important; padding: 0.5rem 0.75rem !important; }
p, .stMarkdown, label { font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

# Sekme başlığını aktif menüye göre güncelle
_sayfa_adlari = {
    "yeni":"Yeni Kart","liste":"Cari Liste",
    "excel":"Excel","kullanici":"Kullanıcılar",
    "dis_nakliye":"Dış Nakliye","dis_nakliye_toplu":"Dış Nakliyeler Listesi",
}
_aktif_sayfa = st.session_state.get("aktif_tab","liste")
_sayfa_adi = _sayfa_adlari.get(_aktif_sayfa, _aktif_sayfa)
st.markdown(f"<script>document.title='MWCRMPRO | {_sayfa_adi}'</script>", unsafe_allow_html=True)
st.markdown("""<style>
section[data-testid="stSidebar"]{transform:none!important;display:flex!important;}
button[data-testid="collapsedControl"]{display:none!important;}
[data-testid="stSidebarCollapseButton"]{display:none!important;}
button[kind="header"]{display:none!important;}
.st-emotion-cache-zq5wmm{display:none!important;}
.st-emotion-cache-1lna32f{display:none!important;}
.mw-not-wrap{display:inline-block;position:relative;cursor:pointer;}
.mw-not-ikon{display:inline-flex;align-items:center;gap:3px;font-size:12px;color:#2563eb;background:#eff6ff;padding:2px 8px;border-radius:20px;border:0.5px solid #bfdbfe;white-space:nowrap;user-select:none;}
.mw-not-ikon:hover{background:#dbeafe;}
.mw-not-tooltip{display:none;position:absolute;left:0;top:calc(100%% + 4px);z-index:9999;background:white;border:0.5px solid #e2e8f0;border-radius:8px;padding:10px 14px;min-width:260px;max-width:340px;font-size:12px;color:#374151;}
.mw-not-wrap:hover .mw-not-tooltip{display:block;}
.mw-not-satir{padding:6px 0;border-bottom:0.5px solid #f1f5f9;line-height:1.5;}
.mw-not-satir:last-child{border-bottom:none;padding-bottom:0;}
.mw-not-meta{font-size:11px;color:#94a3b8;margin-bottom:2px;}
.mw-not-metin{color:#1e293b;}
.mw-not-daha{font-size:11px;color:#94a3b8;margin-top:6px;font-style:italic;}
</style>""", unsafe_allow_html=True)

st.markdown("""<script>
(function(){setInterval(function(){try{var _=window.parent.document.title;}catch(e){}},270000);})();
</script>""", unsafe_allow_html=True)

# ── TAKVİM TÜRKÇELEŞTİRME — tüm date_input bileşenleri için ──────────────────
st.markdown("""<script>
(function(){
  var AY_TR = {
    "January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan",
    "May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos",
    "September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"
  };
  // Gün kısaltmaları sıralı dizi olarak — "Sa" hem Tuesday hem Saturday kısaltması olduğundan
  // object key çakışmasını önlemek için pozisyon bazlı eşleştirme kullanılır.
  // Streamlit/BaseWeb takvimi pazartesi başlangıçlı: Mo,Tu,We,Th,Fr,Sa,Su
  var GUN_KISA_SIRA = ["Mo","Tu","We","Th","Fr","Sa","Su"];
  var GUN_KISA_TR   = ["Pt","Sa","Ça","Pe","Cu","Ct","Pa"];
  var GUN_TAM_TR = {
    "Monday":"Pazartesi","Tuesday":"Salı","Wednesday":"Çarşamba",
    "Thursday":"Perşembe","Friday":"Cuma","Saturday":"Cumartesi","Sunday":"Pazar"
  };
  function turkceleştir(root){
    if(!root) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
    var node;
    while(node = walker.nextNode()){
      var t = node.nodeValue;
      if(!t || !t.trim()) continue;
      var trimmed = t.trim();
      var degisti = false;

      // Ay isimleri — metin içinde geçebilir (örn. "30 June 2026")
      for(var ay in AY_TR){
        if(t.indexOf(ay) !== -1){ t = t.split(ay).join(AY_TR[ay]); degisti = true; }
      }

      // Tam gün isimleri (Monday, Tuesday...)
      for(var gunTam in GUN_TAM_TR){
        if(t.indexOf(gunTam) !== -1){ t = t.split(gunTam).join(GUN_TAM_TR[gunTam]); degisti = true; }
      }

      // Kısa gün başlıkları — SADECE node içeriği TAM OLARAK kısaltmaya eşitse değiştir
      // (içerik karışmasını önlemek için, örn. "Sa" hücre içinde tek başınaysa)
      if(!degisti){
        var idx = GUN_KISA_SIRA.indexOf(trimmed);
        if(idx !== -1 && trimmed === t.trim()){
          t = t.replace(trimmed, GUN_KISA_TR[idx]);
          degisti = true;
        }
      }

      if(degisti) node.nodeValue = t;
    }
  }
  function tumDokumani(){
    try { turkceleştir(document.body); } catch(e){}
    try { if(window.parent && window.parent.document) turkceleştir(window.parent.document.body); } catch(e){}
  }
  // İlk çalıştırma
  tumDokumani();
  // Takvim her açıldığında tekrar çalıştır (MutationObserver)
  try {
    var hedefDoc = (window.parent && window.parent.document) ? window.parent.document : document;
    var observer = new MutationObserver(function(mutations){
      tumDokumani();
    });
    observer.observe(hedefDoc.body, { childList: true, subtree: true });
  } catch(e){}
  // Periyodik yedek kontrol
  setInterval(tumDokumani, 800);
})();
</script>""", unsafe_allow_html=True)


# ── EKRAN AYARLARI UYGULA ────────────────────────────────────────────────────
_e_ust     = st.session_state.get("_ust_px", 32)
_e_alt     = st.session_state.get("_alt_px", 32)
_e_yan     = st.session_state.get("_yan_px", 16)

# Arka plan artık kullanıcı tarafından değiştirilemez — her cihazda/ekranda
# HER ZAMAN beyaz, tek renk. Takım teması / arka plan rengi seçimi özelliği
# kalıcı olarak kaldırıldı.
_bg_css = "body, .main { background-color: #ffffff !important; }"

st.markdown(f"""
<style>
/* Tüm olası selector'lar */
.main .block-container,
div[data-testid="stAppViewContainer"] > section > div,
div[data-testid="stAppViewContainer"] > .main > div,
section.main > div.block-container,
.block-container {{
    padding-top: {_e_ust}px !important;
    padding-bottom: {_e_alt}px !important;
    padding-left: {_e_yan}px !important;
    padding-right: {_e_yan}px !important;
}}
{_bg_css}
</style>
<script>
(function applyPadding() {{
    function apply() {{
        var bc = document.querySelector('.block-container') ||
                 document.querySelector('[data-testid="stAppViewBlockContainer"]') ||
                 document.querySelector('section.main > div');
        if (bc) {{
            bc.style.setProperty('padding-top', '{_e_ust}px', 'important');
            bc.style.setProperty('padding-bottom', '{_e_alt}px', 'important');
            bc.style.setProperty('padding-left', '{_e_yan}px', 'important');
            bc.style.setProperty('padding-right', '{_e_yan}px', 'important');
        }}
    }}
    apply();
    setTimeout(apply, 500);
    setTimeout(apply, 1500);
    var obs = new MutationObserver(apply);
    obs.observe(document.body, {{childList:true, subtree:true}});
}})();
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ── GENEL BUTON & DROPDOWN ── */
.stButton>button { border-radius: 8px !important; }
[data-baseweb="popover"] [data-baseweb="menu"] { max-height: 600px !important; overflow-y: auto !important; }
[data-baseweb="select"] [data-baseweb="menu"] { max-height: 600px !important; }

/* ── MOBİL NAV — her zaman tanımlanır, sadece .mw-mobil-aktif class'ı varsa görünür ── */
#mw-mobile-nav {
  display: none;
  position: fixed !important;
  bottom: 0 !important; left: 0 !important; right: 0 !important;
  z-index: 9999 !important;
  background: white !important;
  border-top: 0.5px solid #e2e8f0 !important;
  justify-content: space-around !important;
  align-items: center !important;
  padding: 6px 0 10px !important;
  box-shadow: 0 -2px 12px rgba(0,0,0,.07) !important;
}
body.mw-mobil-aktif #mw-mobile-nav { display: flex !important; }
#mw-mobile-nav a {
  display: flex !important; flex-direction: column !important;
  align-items: center !important; gap: 2px !important;
  text-decoration: none !important; color: #64748b !important;
  font-size: 10px !important; font-weight: 500 !important;
  padding: 4px 6px !important; border-radius: 8px !important;
  min-width: 52px !important; min-height: 44px !important;
  justify-content: center !important;
}
#mw-mobile-nav a.aktif { color: #2563eb !important; background: #eff6ff !important; }
#mw-mobile-nav a span.nav-ikon { font-size: 20px !important; line-height: 1 !important; }

/* ── MOBİL MOD — sadece body.mw-mobil-aktif varken ── */
body.mw-mobil-aktif .block-container {
  padding: 4px 6px 80px 6px !important;
  max-width: 100vw !important;
}
body.mw-mobil-aktif section[data-testid="stSidebar"] {
  display: none !important;
}
body.mw-mobil-aktif h1 { font-size: 1.2rem !important; margin-bottom: 6px !important; }
body.mw-mobil-aktif h2 { font-size: 1.05rem !important; margin-bottom: 5px !important; }
body.mw-mobil-aktif h3 { font-size: 0.95rem !important; margin-bottom: 4px !important; }
body.mw-mobil-aktif div[data-testid="column"] {
  width: 100% !important; min-width: 100% !important;
  flex: 0 0 100% !important;
  padding-left: 0 !important; padding-right: 0 !important;
}
body.mw-mobil-aktif div[data-testid="stHorizontalBlock"] {
  flex-wrap: wrap !important; gap: 6px !important;
}
body.mw-mobil-aktif .stButton>button {
  width: 100% !important; min-height: 44px !important;
  font-size: 14px !important; border-radius: 10px !important;
  padding: 10px 14px !important;
}
body.mw-mobil-aktif .stButton>button p {
  font-size: 14px !important; white-space: normal !important; text-align: left !important;
}
body.mw-mobil-aktif .stTextInput>div>div>input,
body.mw-mobil-aktif .stTextArea>div>div>textarea,
body.mw-mobil-aktif .stSelectbox>div>div,
body.mw-mobil-aktif .stNumberInput>div>div>input,
body.mw-mobil-aktif .stDateInput>div>div>input {
  font-size: 16px !important; min-height: 44px !important; border-radius: 8px !important;
}
body.mw-mobil-aktif div[data-baseweb="select"] > div {
  min-height: 44px !important; font-size: 14px !important;
}
body.mw-mobil-aktif .stDataFrame, body.mw-mobil-aktif [data-testid="stDataFrame"],
body.mw-mobil-aktif [data-testid="stDataEditor"] {
  overflow-x: auto !important; font-size: 11px !important; width: 100% !important;
}
body.mw-mobil-aktif div[data-testid="metric-container"] {
  background: white !important; border: 0.5px solid #e2e8f0 !important;
  border-radius: 10px !important; padding: 10px 12px !important; min-width: 0 !important;
}
body.mw-mobil-aktif div[data-testid="metric-container"] label { font-size: 11px !important; }
body.mw-mobil-aktif div[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 18px !important; }
body.mw-mobil-aktif button[data-baseweb="tab"] {
  font-size: 12px !important; padding: 8px 10px !important; min-height: 40px !important;
}
body.mw-mobil-aktif div[data-baseweb="tab-list"] {
  overflow-x: auto !important; flex-wrap: nowrap !important; scrollbar-width: none !important;
}
body.mw-mobil-aktif div[data-baseweb="tab-list"]::-webkit-scrollbar { display: none !important; }
body.mw-mobil-aktif details > summary {
  font-size: 14px !important; padding: 12px !important; min-height: 44px !important;
}
body.mw-mobil-aktif .stCheckbox label, body.mw-mobil-aktif .stRadio label { font-size: 14px !important; }
body.mw-mobil-aktif .stSlider [role="slider"] { width: 24px !important; height: 24px !important; }
body.mw-mobil-aktif [data-testid="stDownloadButton"] button {
  min-height: 44px !important; font-size: 14px !important; width: 100% !important;
}
body.mw-mobil-aktif [data-testid="stAlert"] {
  font-size: 13px !important; padding: 10px 12px !important; border-radius: 8px !important;
}
body.mw-mobil-aktif footer { display: none !important; }
body.mw-mobil-aktif [data-testid="stHeader"] { display: none !important; }
body.mw-mobil-aktif [data-testid="stModal"] > div {
  width: 95vw !important; max-width: 95vw !important;
  margin: 10px auto !important; border-radius: 14px !important;
}
body.mw-mobil-aktif div[data-testid="stHorizontalBlock"]:has(.an-kart-btn) > div:first-child {
  flex: 0 0 85% !important; min-width: 85% !important;
}
body.mw-mobil-aktif div[data-testid="stHorizontalBlock"]:has(.an-kart-btn) > div:last-child {
  flex: 0 0 13% !important; min-width: 13% !important;
}
</style>
""", unsafe_allow_html=True)

# ── MOBİL ALT NAVİGASYON ─────────────────────────────────────────────────────
st.markdown("""<div id="mw-mobile-nav">
  <a class="mw-nav-btn" id="mwnav-liste" href="?_nav=liste"><span class="nav-ikon">📋</span>Liste</a>
  <a class="mw-nav-btn" id="mwnav-analiz" href="?_nav=rapor"><span class="nav-ikon">📊</span>Rapor</a>
  <a class="mw-nav-btn" id="mwnav-randevu" href="?_nav=randevu"><span class="nav-ikon">📅</span>Randevu</a>
  <a class="mw-nav-btn" id="mwnav-harita" href="?_nav=harita"><span class="nav-ikon">🗺️</span>Harita</a>
</div>
<a href="?_masaustune_gec=1" style="
  position:fixed; top:8px; right:8px; z-index:100000;
  background:#0f172a; color:white; text-decoration:none;
  font-size:11px; font-weight:600; padding:7px 12px;
  border-radius:20px; box-shadow:0 2px 8px rgba(0,0,0,.25);
  display:none;" id="mw-masaustu-btn">🖥️ Masaüstüne geç</a>
<script>
(function(){
  var _b = window.parent ? window.parent.document.body : document.body;
  var _btn = document.getElementById('mw-masaustu-btn');
  if(_btn && _b.classList.contains('mw-mobil-aktif')){ _btn.style.display = 'block'; }
})();
</script>""", unsafe_allow_html=True)

# Mobilde menüye hiç girmeden tek dokunuşla masaüstü moduna geçiş
try:
    if st.query_params.get("_masaustune_gec", "") == "1":
        st.session_state["_mobil_mod"] = False
        st.markdown("""<script>
try{
  var _eski = localStorage.getItem('mwcrm_oturum');
  if(_eski){ var _o = JSON.parse(_eski); _o.mobil = false; localStorage.setItem('mwcrm_oturum', JSON.stringify(_o)); }
}catch(e){}
</script>""", unsafe_allow_html=True)
        st.query_params.clear()
        st.rerun()
except Exception:
    pass

# Gizli tab geçiş butonları — mobil nav bunları tetikler
# Mobil nav — query param ile tab geçişi (sadece mobil nav için)
try:
    _mob_nav_qp = st.query_params.get("_nav", "")
    _mob_nav_tablar = ["liste","yeni"]
    if _mob_nav_qp and _mob_nav_qp in _mob_nav_tablar:
        st.session_state["aktif_tab"] = _mob_nav_qp
        st.query_params.clear()
        st.rerun()
except Exception:
    pass

st.markdown("""

<style>
.mw-nav-btn {
  display:flex !important; flex-direction:column !important;
  align-items:center !important; gap:2px !important;
  background:none !important; border:none !important;
  color:#64748b !important; font-size:10px !important;
  font-weight:500 !important; padding:4px 6px !important;
  border-radius:8px !important; min-width:52px !important;
  min-height:44px !important; cursor:pointer !important;
  justify-content:center !important;
}
.mw-nav-btn.aktif { color:#2563eb !important; background:#eff6ff !important; }
.mw-nav-btn .nav-ikon { font-size:20px !important; line-height:1 !important; }
/* Gizli streamlit nav butonları */
button[data-testid="baseButton-secondary"][kind="secondary"]:is(
  [data-key="mw_nav_st_liste"],
  [data-key="mw_nav_st_analiz"],
  [data-key="mw_nav_st_randevu"],
  [data-key="mw_nav_st_teklif"],
  [data-key="mw_nav_st_harita"]
) { display: none !important; }
div:has(> button[data-testid="baseButton-secondary"]:is(
  [data-key="mw_nav_st_liste"],
  [data-key="mw_nav_st_analiz"],
  [data-key="mw_nav_st_randevu"],
  [data-key="mw_nav_st_teklif"],
  [data-key="mw_nav_st_harita"]
)) { height: 0 !important; overflow: hidden !important; margin: 0 !important; padding: 0 !important; }
</style>
<script>
function mwTab(tab) {
  // Streamlit'in sidebar butonlarını bul ve tıkla — session state güvenli
  var btns = window.parent.document.querySelectorAll('section[data-testid="stSidebar"] button');
  var tabMap = {
    'liste':'Cari Liste','analiz':'Müşteri Analizi','randevu':'Randevular',
    'ozel_teklif':'Özel Teklif','sozlesme':'Sözleşmeler','harita':'Müşteri Haritası',
    'rapor':'Raporlar','yeni':'Yeni Kart'
  };
  var hedef = tabMap[tab] || tab;
  for(var i=0;i<btns.length;i++){
    if(btns[i].innerText && btns[i].innerText.indexOf(hedef.substring(0,6)) >= 0){
      btns[i].click();
      // Aktif class güncelle
      document.querySelectorAll('.mw-nav-btn').forEach(function(b){ b.classList.remove('aktif'); });
      event.currentTarget.classList.add('aktif');
      return;
    }
  }
}
</script>
""", unsafe_allow_html=True)


# ── MENÜ FONKSİYONLARI (sidebar'dan önce tanımlanmalı) ───────────────────────

def fmt_para(n):
    """Türk muhasebe formatı: 1.000.000,00 ₺"""
    try:
        n = float(n or 0)
        if n == int(n):
            s = f"{int(n):,}".replace(",",".")
        else:
            tam = int(n)
            kurus = round((n - tam) * 100)
            s = f"{tam:,}".replace(",",".") + f",{kurus:02d}"
        return s + " ₺"
    except:
        return "0 ₺"


def fmt_tel(n):
    """5544929309.0 → 554 492 93 09"""
    try:
        if not n or str(n).strip() in ["", "None", "nan", "-"]: return ""
        s = str(n).strip()
        # Float .0 temizle
        if s.endswith(".0"): s = s[:-2]
        # Bilimsel notasyon: 5.52e+09 gibi
        try:
            if "e" in s.lower(): s = str(int(float(s)))
        except: pass
        # Sadece rakam, +, boşluk, tire bırak
        import re as _re2
        s = _re2.sub(r"[^0-9\+\s\-]", "", s).strip()
        return _tel_gruplu(s)
    except: return ""

def _duzenleme_form_key_temizle(fid):
    """Belirli bir müşteri ID'sine ait düzenleme formu widget key'lerini
    session_state'ten siler. Düzenle her tıklandığında çağrılmalı —
    yoksa eskiden o key'e yapışmış (boş veya yanlış) değer, yeni
    value= parametresini görmezden gelip ekranda kalmaya devam eder."""
    _alanlar = ["yeni_il_dis","yeni_ilce_dis","yeni_durum_dis","yeni_temsilci_dis",
                "yeni_seg_dis","yeni_asama_dis","yeni_firma","yeni_yetkili",
                "yeni_gsm","yeni_sabit","yeni_email","yeni_adres","yeni_notlar",
                "bek_ciro_str","ger_ciro_str"]
    for _a in _alanlar:
        st.session_state.pop(f"{_a}_{fid}", None)

def parse_para(s):
    """1.000.000,50 → 1000000.50"""
    try:
        s = str(s).strip().replace(" ","").replace("₺","").replace("TL","")
        if not s: return 0.0
        if "," in s and "." in s:
            s = s.replace(".","").replace(",",".")
        elif "," in s:
            s = s.replace(",",".")
        else:
            s = s.replace(".","")
        return float(s)
    except:
        return 0.0

def fmt_tarih(v):
    """Herhangi bir tarih string'ini 22.06.2026 formatına çevirir"""
    if not v: return ""
    s = str(v).strip()
    if not s or s in ["nan","None",""]: return ""
    try:
        if len(s) >= 10 and s[4] == "-":
            return f"{s[8:10]}.{s[5:7]}.{s[:4]}"
        if len(s) >= 10 and s[2] == "." and s[5] == ".":
            return s[:10]
    except:
        pass
    return s[:10]

def _guncelleme_tarih_parse(s):
    """Farklı formatlardaki (ISO 'T', boşluklu, Türkçe nokta) tarih string'lerini
    gerçek datetime nesnesine çevirir. String karşılaştırması ('2026-08-12 ...' ile
    '2026-08-12T...' gibi farklı ayraçlar) yanlış sonuç verdiği için Güncelleme
    Tarihi hesabında SADECE bu fonksiyonla parse edilmiş datetime'lar karşılaştırılır."""
    if not s:
        return None
    s = str(s).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return None
    import re as _gtre
    _s_temiz = _gtre.sub(r"(\+\d{2}:\d{2}|Z)$", "", s.replace("Z", "+00:00").replace("+00:00", ""))
    for _cand in (_s_temiz, s):
        try:
            return datetime.fromisoformat(_cand)
        except Exception:
            continue
    for _fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, _fmt)
        except Exception:
            continue
    return None

def fmt_tarih_saat(v):
    """Herhangi bir tarih-saat string'ini '22.06.2026 14:23' formatına çevirir (sadece tarih+saat, başka bilgi yok)"""
    if not v: return ""
    s = str(v).strip()
    if not s or s in ["nan","None",""]: return ""
    try:
        _tarih_kismi = fmt_tarih(s)
        _saat_kismi = ""
        _ayrac = "T" if "T" in s else (" " if " " in s else None)
        if _ayrac:
            _saat_ham = s.split(_ayrac, 1)[1].strip()
            if len(_saat_ham) >= 5:
                _saat_kismi = _saat_ham[:5]
        if _tarih_kismi and _saat_kismi:
            return f"{_tarih_kismi} {_saat_kismi}"
        return _tarih_kismi or s[:16]
    except:
        return s[:16]

@st.cache_data(ttl=30, show_spinner=False)
def _notlar_yukle(cari_id):
    try:
        _sb = get_sb_client()
        if _sb:
            _r = _sb.table("cari_aciklamalar").select("*").eq("cari_id", int(cari_id)).execute()
            return _r.data or []
    except: pass
    return []

# ═══════════════════════════════════════════════════════════════════════════
# 🚚 DIŞ NAKLİYE — ortak kolon yapısı / yükleme / kaydetme
# Yeni SQL tablosu AÇILMIYOR — mevcut "kullanici_tercih" tablosunda tek bir
# JSON kayıt olarak saklanıyor (kullanici="__liste_ui__",
# anahtar="dis_nakliye_islemleri"). Her kayıt bir "cari_id" taşır (0 = belirli
# bir müşteriyle ilişkilendirilmemiş, toplu listeden eklenmiş demektir).
# Taşıyıcı (tedarikçi) master listesi de aynı şekilde ayrı bir anahtarda
# ("dis_nakliye_tasiyicilar") JSON olarak saklanır.
# ═══════════════════════════════════════════════════════════════════════════
_DIS_NAKLIYE_KOLONLAR = [
    "tarih", "gonderen_firma", "gonderici_tel", "gonderen_adres", "gonderen_il", "gonderen_ilce",
    "alici_firma", "alici_tel", "alici_adres", "alici_il", "alici_ilce",
    "vergi_dairesi", "vergi_no", "odeme_turu",
    "adet1", "fiyat1", "yekun1", "kdvli1", "odendi1",
    "tasiyici", "yetkili", "yetkili_tel",
    "adet2", "fiyat2", "yekun2", "kdvli2", "odendi2",
    "kar",
]
_DIS_NAKLIYE_BASLIKLAR = {
    "tarih": "TARİH",
    "gonderen_firma": "GÖNDEREN FİRMA", "gonderici_tel": "GÖNDERİCİ TEL", "gonderen_adres": "GÖNDEREN ADRESİ",
    "gonderen_il": "GÖNDEREN İL", "gonderen_ilce": "GÖNDEREN İLÇE",
    "alici_firma": "ALICI FİRMA", "alici_tel": "ALICI TEL", "alici_adres": "ALICI ADRES",
    "alici_il": "ALICI İL", "alici_ilce": "ALICI İLÇE",
    "vergi_dairesi": "VERGİ DAİRESİ", "vergi_no": "VERGİ NO", "odeme_turu": "ÖDEME TÜRÜ",
    "adet1": "ADET", "fiyat1": "BİRİM FİYAT", "yekun1": "YEKÜN", "kdvli1": "KDV'Lİ", "odendi1": "ÖDENDİ",
    "tasiyici": "TAŞIYICI", "yetkili": "YETKİLİ", "yetkili_tel": "YETKİLİ TEL",
    "adet2": "ADET", "fiyat2": "ADET FİYATI", "yekun2": "YEKÜN", "kdvli2": "KDV'Lİ", "odendi2": "ÖDENDİ",
    "kar": "KAR",
}
_DIS_NAKLIYE_GENISLIK = {
    "tarih": 85, "gonderen_firma": 120, "gonderici_tel": 95, "gonderen_adres": 120, "gonderen_il": 75, "gonderen_ilce": 75,
    "alici_firma": 120, "alici_tel": 95, "alici_adres": 120, "alici_il": 75, "alici_ilce": 75,
    "vergi_dairesi": 95, "vergi_no": 90, "odeme_turu": 90,
    "adet1": 55, "fiyat1": 85, "yekun1": 85, "kdvli1": 85, "odendi1": 65,
    "tasiyici": 110, "yetkili": 100, "yetkili_tel": 95,
    "adet2": 55, "fiyat2": 95, "yekun2": 85, "kdvli2": 85, "odendi2": 65,
    "kar": 90,
}
_DIS_NAKLIYE_SAYI_KOLON = {"adet1", "fiyat1", "adet2", "fiyat2"}
_DIS_NAKLIYE_HESAP_KOLON = {"yekun1", "kdvli1", "yekun2", "kdvli2", "kar"}
_DIS_NAKLIYE_CHECK_KOLON = {"odendi1", "odendi2"}

def _dis_nakliye_col_config():
    cfg = {}
    for k in _DIS_NAKLIYE_KOLONLAR:
        w = _DIS_NAKLIYE_GENISLIK.get(k, 90)
        baslik = _DIS_NAKLIYE_BASLIKLAR[k]
        if k in _DIS_NAKLIYE_CHECK_KOLON:
            cfg[k] = st.column_config.CheckboxColumn(baslik, width=w)
        elif k in _DIS_NAKLIYE_SAYI_KOLON:
            cfg[k] = st.column_config.NumberColumn(baslik, width=w, min_value=0, step=1)
        elif k in _DIS_NAKLIYE_HESAP_KOLON:
            cfg[k] = st.column_config.NumberColumn(
                baslik, width=w, format="%.2f ₺", disabled=True,
                help="Otomatik hesaplanır — Adet × Fiyat = Yekün, Yekün × %20 KDV = KDV'li, "
                     "Kar = Müşteri KDV'li − Taşıyıcı KDV'li. Kaydet'e basınca güncellenir.")
        else:
            cfg[k] = st.column_config.TextColumn(baslik, width=w)
    return cfg

def _dis_nakliye_hesapla(df):
    """Yekün / KDV'li / Kar kolonlarını Adet × Fiyat mantığıyla yeniden hesaplar (%20 KDV)."""
    for c in ["adet1", "fiyat1", "adet2", "fiyat2"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["yekun1"] = df["adet1"] * df["fiyat1"]
    df["kdvli1"] = df["yekun1"] * 1.20
    df["yekun2"] = df["adet2"] * df["fiyat2"]
    df["kdvli2"] = df["yekun2"] * 1.20
    df["kar"] = df["kdvli1"] - df["kdvli2"]
    # Metin kolonlarında None/nan yerine boş göster
    for _tk in _DIS_NAKLIYE_KOLONLAR:
        if _tk not in _DIS_NAKLIYE_SAYI_KOLON and _tk not in _DIS_NAKLIYE_HESAP_KOLON and _tk not in _DIS_NAKLIYE_CHECK_KOLON:
            df[_tk] = df[_tk].astype(str).replace(["None", "nan", "NaN", "none"], "")
    return df

def _dis_nakliye_yukle():
    if "_dn2_kayitlar" not in st.session_state:
        st.session_state["_dn2_kayitlar"] = []
        try:
            _sb = get_sb_client()
            if _sb:
                _r = _sb.table("kullanici_tercih").select("deger").eq(
                    "kullanici", "__liste_ui__").eq("anahtar", "dis_nakliye_islemleri").execute()
                if _r.data:
                    st.session_state["_dn2_kayitlar"] = json.loads(_r.data[0]["deger"])
        except Exception:
            pass
    return st.session_state["_dn2_kayitlar"]

def _dis_nakliye_kaydet(kayitlar):
    try:
        _sb = get_sb_client()
        if _sb:
            _sb.table("kullanici_tercih").upsert({
                "kullanici": "__liste_ui__", "anahtar": "dis_nakliye_islemleri",
                "deger": json.dumps(kayitlar, ensure_ascii=False)
            }, on_conflict="kullanici,anahtar").execute()
        st.session_state["_dn2_kayitlar"] = kayitlar
        return True
    except Exception:
        return False

def _dis_nakliye_tasiyici_yukle():
    if "_dn2_tasiyicilar" not in st.session_state:
        st.session_state["_dn2_tasiyicilar"] = []
        try:
            _sb = get_sb_client()
            if _sb:
                _r = _sb.table("kullanici_tercih").select("deger").eq(
                    "kullanici", "__liste_ui__").eq("anahtar", "dis_nakliye_tasiyicilar").execute()
                if _r.data:
                    st.session_state["_dn2_tasiyicilar"] = json.loads(_r.data[0]["deger"])
        except Exception:
            pass
    return st.session_state["_dn2_tasiyicilar"]

def _dis_nakliye_tasiyici_kaydet(liste):
    try:
        _sb = get_sb_client()
        if _sb:
            _sb.table("kullanici_tercih").upsert({
                "kullanici": "__liste_ui__", "anahtar": "dis_nakliye_tasiyicilar",
                "deger": json.dumps(liste, ensure_ascii=False)
            }, on_conflict="kullanici,anahtar").execute()
        st.session_state["_dn2_tasiyicilar"] = liste
        return True
    except Exception:
        return False


# ── TEDARİKÇİ (nakliyeci/taşıyıcı) KAYIT SİSTEMİ ─────────────────────────────
# NOT: Kargo kaydından öğrenilen ders gereği (bkz. dosya başındaki kritik uyarı)
# bu fonksiyonlar ÖNBELLEKSİZ — her zaman doğrudan Supabase'den okur/yazar.
_TEDARIKCI_ANAHTAR = "tedarikciler_listesi_v2"
_TEDARIKCI_MIGRASYON_ANAHTARI = "tedarikciler_migrasyon_yapildi_v2"


def _tedarikci_yukle_ham_guvenli():
    """Supabase'den DOĞRUDAN okur. BAŞARISIZ olursa (bağlantı/hata) _OKUMA_BASARISIZ
    döner — ASLA sessizce boş liste dönüp 'kayıt yokmuş gibi' davranmaz. Bu
    ayrımın kaybolması, yeni eklenen tedarikçilerin geçici bir okuma hatası
    yüzünden eski (migrasyon) listesiyle EZİLİP kaybolmasına yol açmıştı."""
    try:
        _sb_td = get_sb_client()
        if not _sb_td:
            return _OKUMA_BASARISIZ
        _r_td = _sb_td.table("kullanici_tercih").select("deger").eq(
            "kullanici", "__liste_ui__").eq("anahtar", _TEDARIKCI_ANAHTAR).execute()
        if _r_td.data:
            return json.loads(_r_td.data[0]["deger"])
        return []  # gerçekten yok (sorgu başarılı, satır yok) — güvenli boşluk
    except Exception:
        return _OKUMA_BASARISIZ


def _tedarikci_kaydet(liste):
    """GÜVENLİ (2026-09, 2. düzeltme — 1. düzeltmedeki hata giderildi):
    Önceki sürüm 'önce ekle, dönen id ile doğrula, sonra eskiyi sil'
    yapıyordu — ama id doğrulaması beklendiği gibi çalışmayınca (kullanılan
    Supabase şemasında farklı davranış), eski satır hiç silinmiyor, yeni
    eklenen tedarikçi ise okuma sırasında görünmüyordu ('kayıt yapmıyor' gibi
    görünen hata buydu). ŞİMDİ: hiçbir sütuna (id vb.) bağımlı olmayan çok
    daha basit ve sağlam bir yöntem kullanılıyor — SİLME YOK. Satır zaten
    varsa doğrudan UPDATE edilir (atomik, tek adım, hiçbir an veri eksik
    durumda olmaz); satır hiç yoksa (ilk kayıt) INSERT edilir."""
    try:
        _sb_td2 = get_sb_client()
        if not _sb_td2:
            return False
        _deger = json.dumps(liste, ensure_ascii=False)
        _guncelle_sonuc = _sb_td2.table("kullanici_tercih").update({"deger": _deger}).eq(
            "kullanici", "__liste_ui__").eq("anahtar", _TEDARIKCI_ANAHTAR).execute()
        if not _guncelle_sonuc.data:
            # Eşleşen satır yoktu (ilk kayıt) — şimdi ekle.
            _sb_td2.table("kullanici_tercih").insert({
                "kullanici": "__liste_ui__", "anahtar": _TEDARIKCI_ANAHTAR, "deger": _deger
            }).execute()
        return True
    except Exception:
        return False


def _tedarikci_migrasyon_yapildi_mi():
    """Eski taşıyıcı listesinden migrasyonun daha önce KESİNLİKLE yapıldığını
    gösteren AYRI bir işaret. Bu sayede geçici bir okuma hatası 'hiç migrasyon
    yapılmamış' sanılıp tekrar migrasyon (ve üzerine yazma) tetiklemez —
    yaşanan veri kaybının kök nedeni tam olarak buydu."""
    try:
        _sb_tdm = get_sb_client()
        if _sb_tdm:
            _r_tdm = _sb_tdm.table("kullanici_tercih").select("deger").eq(
                "kullanici", "__liste_ui__").eq("anahtar", _TEDARIKCI_MIGRASYON_ANAHTARI).execute()
            return bool(_r_tdm.data)
    except Exception:
        pass
    return False


def _tedarikci_migrasyon_isaretle():
    try:
        _sb_tdm2 = get_sb_client()
        if _sb_tdm2:
            _sb_tdm2.table("kullanici_tercih").upsert({
                "kullanici": "__liste_ui__", "anahtar": _TEDARIKCI_MIGRASYON_ANAHTARI, "deger": "1"
            }, on_conflict="kullanici,anahtar").execute()
    except Exception:
        pass


def _tedarikci_yukle_goster():
    """SADECE GÖRÜNTÜLEME için (Kargolar'daki Dış Nakliye Firma açılır listesi,
    başka sayfalardan hızlı bakış vb.) — okuma başarısız olursa (bağlantı
    sorunu) HİÇBİR ŞEY YAZMADAN boş liste döner, sessizce devam eder. Migrasyon
    SADECE Tedarikçi sayfasının kendisinde, açıkça ve güvenlik kontrolleriyle
    yapılır — burada ASLA bir yazma tetiklenmez."""
    _sonuc = _tedarikci_yukle_ham_guvenli()
    if _sonuc is _OKUMA_BASARISIZ:
        return []
    return _sonuc

def _dis_nakliye_musteri_bilgisi(cari_id):
    """Seçilen müşterinin cari kartından Gönderen bloğu için otomatik bilgileri çeker."""
    try:
        _sb = get_sb_client()
        if _sb:
            _r = _sb.table("cari_kartlar").select("firma,gsm,sabit,adres,il,ilce").eq("id", int(cari_id)).execute()
            if _r.data:
                return _r.data[0]
    except Exception:
        pass
    return {}

def _dis_nakliye_tasiyici_secici(key_prefix):
    """Kayıtlı taşıyıcılar arasından seçim yapılabilen küçük bir bileşen —
    seçilirse (taşıyıcı, yetkili, yetkili_tel) döner, yoksa (None, None, None)."""
    _liste = _dis_nakliye_tasiyici_yukle()
    if not _liste:
        return None, None, None
    _secenekler = ["— Kayıtlı taşıyıcı seç (opsiyonel) —"] + [
        f"{t.get('tasiyici','')} — {t.get('yetkili','')}" for t in _liste
    ]
    _sec = st.selectbox("Kayıtlı Taşıyıcıdan Doldur", _secenekler, key=f"{key_prefix}_tasiyici_sec", label_visibility="collapsed")
    if _sec != _secenekler[0]:
        _idx = _secenekler.index(_sec) - 1
        _t = _liste[_idx]
        return _t.get("tasiyici",""), _t.get("yetkili",""), _t.get("yetkili_tel","")
    return None, None, None

def not_dialog(cari_id, firma_adi=""):
    """Ekran ortasında açılan not + randevu + silme + düzenleme penceresi"""
    # ── AÇIK KALSIN — pencere içinde bir işlem yapılıp (Ayrıştır, Kaydet vb.)
    # st.rerun() tetiklenince, tabloyu yeniden oluşturan koşul bazen aynı
    # şekilde tekrar sağlanmayabiliyor ve pencere kapanıyordu. Bu yüzden
    # hangi firma için açık olduğu ayrıca session_state'te "kalıcı" tutuluyor —
    # sayfanın en başında bu kayıt varsa pencere garanti yeniden açılıyor.
    st.session_state["_not_dialog_kalici_id"] = cari_id
    st.session_state["_not_dialog_kalici_firma"] = firma_adi
    # ── PENCEREYİ GENİŞLET — Streamlit'in "large" seçeneği en fazla 1280px
    # veriyor, Dış Nakliye tablosundaki çok sayıda kolon için yetersiz
    # kalıyordu. CSS ile ekranın büyük kısmını kaplayacak şekilde zorluyoruz.
    st.markdown("""<style>
[data-testid="stDialog"] div[role="dialog"] {
    width: 96vw !important;
    max-width: 1900px !important;
}
</style>""", unsafe_allow_html=True)
    if st.button("❌ Bu Pencereyi Kapat", key=f"dlg_kapat_{cari_id}"):
        # KULLANICI İSTEĞİ (2026-09): "Kapat"a basınca bu müşteri için pencere
        # bir daha KENDİLİĞİNDEN açılmasın (Seç kutusu hâlâ işaretli kalmış
        # olsa bile) — sadece kullanıcı BİLEREK tekrar Seç'e basarsa açılsın.
        st.session_state["_not_dialog_son_kapatilan_id"] = cari_id
        st.session_state.pop("_not_dialog_kalici_id", None)
        st.session_state.pop("_not_dialog_kalici_firma", None)
        st.rerun()
    _tab_not, _tab_hizli, _tab_rdv, _tab_yetkili, _tab_dn, _tab_kargo, _tab_varis, _tab_duz, _tab_sil = st.tabs(["📝 Notlar", "⚡ Hızlı Firma Ekle", "📅 Randevu Ekle", "👥 Yetkililer", "🚚 Dış Nakliye", "📦 Kargo Girişi", "📦 Varış/Fiyat", "✏️ Cari Kartı Düzenle", "🗑️ Cari Sil"])
    with _tab_not:
        not_paneli(cari_id, firma_adi, key_prefix="dlg")
    with _tab_hizli:
        st.caption("İnternetten kopyaladığın karmaşık/düzensiz firma bilgisini aşağıya yapıştır — Firma Adı, GSM, Sabit Tel, Email, Adres, İl ve İlçe otomatik ayrıştırılır. Bu, YENİ bir müşteri olarak Cari Ana Liste'ye eklenir (şu an açık olan '{}' ile ilgisi yoktur).".format(firma_adi or ""))
        _hf_ham_metin = st.text_area("Yapıştır", height=150, key=f"hf_ham_{cari_id}", placeholder="Firma adı\nAdres satırı...\n0212 555 44 33\n0555 444 33 22\ninfo@firma.com\n34000 İstanbul/Türkiye", label_visibility="collapsed")
        if st.button("🔍 Ayrıştır", key=f"hf_ayristir_btn_{cari_id}"):
            if _hf_ham_metin.strip():
                # KULLANICI İSTEĞİ: yeni ayrıştırmadan önce, önceki ayrıştırmadan
                # kalan alan kutularının (widget) session_state değerleri de
                # temizlenir — aksi halde Streamlit widget'ları "value=" parametresini
                # yok sayıp ESKİ değerleri göstermeye devam ediyordu (form
                # yenilenmiyormuş gibi görünüyordu).
                for _hf_alan_k in ("firma", "gsm", "sabit", "email", "adres", "il", "ilce"):
                    st.session_state.pop(f"hf_{_hf_alan_k}_{cari_id}", None)
                st.session_state[f"hf_sonuc_{cari_id}"] = _hizli_firma_ayristir(_hf_ham_metin)
            else:
                st.warning("Önce bir metin yapıştır.")
        _hf_sonuc = st.session_state.get(f"hf_sonuc_{cari_id}")
        if _hf_sonuc:
            st.markdown("**Ayrıştırılan bilgiler — kaydetmeden önce gözden geçir/düzelt:**")
            _hfc1, _hfc2 = st.columns(2)
            _hf_firma = _hfc1.text_input("Firma Adı", value=_hf_sonuc["firma_adi"], key=f"hf_firma_{cari_id}")
            _hf_gsm = _hfc2.text_area("GSM (birden fazlaysa alt alta)", value=_hf_sonuc["gsm"], key=f"hf_gsm_{cari_id}", height=70)
            _hfc3, _hfc4 = st.columns(2)
            _hf_sabit = _hfc3.text_area("Sabit Tel (birden fazlaysa alt alta)", value=_hf_sonuc["sabit"], key=f"hf_sabit_{cari_id}", height=70)
            _hf_email = _hfc4.text_area("Email (birden fazlaysa alt alta)", value=_hf_sonuc["email"], key=f"hf_email_{cari_id}", height=70)
            _hf_adres = st.text_area("Adres(ler) (birden fazlaysa alt alta)", value=_hf_sonuc["adres"], height=90, key=f"hf_adres_{cari_id}")
            _hfc5, _hfc6 = st.columns(2)
            _hf_il_opts = ["-- İl seçilir --"] + sorted(_IL_ILCE_HARITASI.keys())
            _hf_il_idx = _hf_il_opts.index(_hf_sonuc["il"]) if _hf_sonuc["il"] in _hf_il_opts else 0
            _hf_il = _hfc5.selectbox("İl", _hf_il_opts, index=_hf_il_idx, key=f"hf_il_{cari_id}",
                                      format_func=lambda x: _tr_buyuk(x) if x != "-- İl seçilir --" else x)
            _hf_ilce_opts = _IL_ILCE_HARITASI.get(_hf_il, []) if _hf_il != "-- İl seçilir --" else []
            _hf_ilce_liste = ["-- Önce il seç --"] + _hf_ilce_opts if _hf_ilce_opts else ["-- Önce il seç --"]
            _hf_ilce_idx = _hf_ilce_liste.index(_hf_sonuc["ilce"]) if _hf_sonuc["ilce"] in _hf_ilce_liste else 0
            _hf_ilce = _hfc6.selectbox("İlçe", _hf_ilce_liste, index=_hf_ilce_idx, key=f"hf_ilce_{cari_id}",
                                        format_func=lambda x: _tr_buyuk(x) if x != "-- Önce il seç --" else x)

            # ── MÜKERRER KONTROLÜ — kaydetmeden ÖNCE, aynı isim/telefon/email'e
            # sahip mevcut kayıt var mı diye kontrol edilir. Sadece UYARIR,
            # engellemez — kullanıcı yine de eklemeyi seçebilir.
            _hf_mukerrer = _hizli_firma_mukerrer_kontrol(_hf_firma, _hf_gsm, _hf_sabit, _hf_email)
            if _hf_mukerrer:
                st.warning(f"⚠️ Bende şu kayıt(lar) zaten var — dikkatli ol, mükerrer olabilir:")
                for _hfm in _hf_mukerrer:
                    st.markdown(f"- **{_hfm['firma']}** ({_hfm['sebep']}) — GSM: {_hfm['gsm'] or '-'} · Sabit: {_hfm['sabit'] or '-'} · Email: {_hfm['email'] or '-'} · İl: {_hfm['il'] or '-'}")

            if st.button("💾 Cari Ana Listeye Ekle", type="primary", key=f"hf_kaydet_btn_{cari_id}", use_container_width=True):
                if not _hf_firma.strip():
                    st.error("⚠️ Firma Adı boş olamaz.")
                else:
                    _hf_ok = db_insert("cari_kartlar", {
                        "tarih": datetime.now().isoformat(),
                        "firma": _tr_buyuk(_hf_firma), "yetkili": "",
                        "gsm": _hf_gsm.strip(), "sabit": _hf_sabit.strip(),
                        "email": _hf_email.strip(),
                        "adres": _tr_buyuk(_hf_adres),
                        "ilce": _tr_buyuk(_hf_ilce) if _hf_ilce != "-- Önce il seç --" else "",
                        "il": _tr_buyuk(_hf_il) if _hf_il != "-- İl seçilir --" else "",
                        "durum": "Portföy", "silindi": 0,
                        "olusturan": st.session_state.get("kullanici", ""),
                        "beklenen_ciro": 0, "gerceklesen_ciro": 0,
                        "atanan_kullanici": st.session_state.get("kullanici", "")
                    })
                    try: db_read.clear()
                    except: pass
                    try: get_cari_listesi.clear()
                    except: pass
                    if _hf_ok:
                        st.session_state.pop(f"hf_sonuc_{cari_id}", None)
                        st.session_state.pop(f"hf_ham_{cari_id}", None)
                        for _hf_alan_k2 in ("firma", "gsm", "sabit", "email", "adres", "il", "ilce"):
                            st.session_state.pop(f"hf_{_hf_alan_k2}_{cari_id}", None)
                        st.toast(f"✅ '{_hf_firma}' Cari Ana Liste'ye eklendi", icon="⚡")
                        st.rerun()
                    else:
                        st.error("⚠️ Kaydedilemedi — lütfen tekrar dene.")

            # ── KULLANICI İSTEĞİ (2026-09): eski/eksik bilgili bir müşteriye
            # TIKLAYIP açtıysan, YENİ müşteri oluşturmak yerine aynı
            # ayrıştırma sonucunu BU müşterinin (şu an açık olan) eksik
            # alanlarına doldurabilirsin. Zaten DOLU olan alanlara ASLA
            # dokunulmaz — sadece BOŞ olanlar bu ayrıştırılan verilerle
            # doldurulur (mevcut veri kaybı riski yok). Çoklu değerli alanlar
            # (GSM/Sabit/Email) için yeni satırlar mevcutlara EKLENİR
            # (tekrarlanmayan satırlar).
            st.divider()
            if st.button(f"🔄 '{firma_adi}' Müşterisinin Eksik Bilgilerini Bu Verilerle Doldur",
                         key=f"hf_mevcut_doldur_btn_{cari_id}", use_container_width=True):
                try:
                    _hf_mevcut_df = get_cari_listesi()
                    _hf_mevcut_satir = _hf_mevcut_df[_hf_mevcut_df["id"] == int(cari_id)]
                    if _hf_mevcut_satir.empty:
                        st.error("⚠️ Bu müşteri bulunamadı — sayfayı yenileyip tekrar dene.")
                    else:
                        _hf_m = _hf_mevcut_satir.iloc[0]

                        def _hf_coklu_birlestir(_eski, _yeni):
                            # KULLANICI İSTEĞİ (2026-09): YENİ veriler ÜSTTE,
                            # ESKİ veriler ALTTA görünsün — böylece en güncel
                            # bilgi ilk bakışta görülür.
                            _eski_satirlar = [s.strip() for s in str(_eski or "").split("\n") if s.strip()]
                            _yeni_satirlar = [s.strip() for s in str(_yeni or "").split("\n") if s.strip()]
                            _birlesik = list(_yeni_satirlar)
                            for _es in _eski_satirlar:
                                if _es not in _birlesik:
                                    _birlesik.append(_es)
                            return "\n".join(_birlesik)

                        _hf_guncelle_alan = {}
                        _hf_guncelle_alan["gsm"] = _hf_coklu_birlestir(_hf_m.get("gsm", ""), _hf_gsm)
                        _hf_guncelle_alan["sabit"] = _hf_coklu_birlestir(_hf_m.get("sabit", ""), _hf_sabit)
                        _hf_guncelle_alan["email"] = _hf_coklu_birlestir(_hf_m.get("email", ""), _hf_email)
                        # KULLANICI İSTEĞİ (2026-09 düzeltmesi): "sadece alan
                        # BOŞSA doldur" kuralı çok katıydı — mevcut kayıtta
                        # o alanda anlamsız bir kalıntı (boşluk, tire vb.)
                        # varsa "zaten dolu" sayılıp hiç güncellenmiyordu, bu
                        # yüzden "adres/il geçmedi" şikayetine yol açtı. Artık
                        # ayrıştırılan veri VARSA doğrudan uygulanır (bu
                        # buton zaten "eksik bilgileri BU verilerle doldur"
                        # demek için tıklanıyor — kullanıcı bunu istiyor).
                        if _hf_adres.strip():
                            _hf_guncelle_alan["adres"] = _tr_buyuk(_hf_adres)
                        if _hf_il != "-- İl seçilir --":
                            _hf_guncelle_alan["il"] = _tr_buyuk(_hf_il)
                        if _hf_ilce != "-- Önce il seç --":
                            _hf_guncelle_alan["ilce"] = _tr_buyuk(_hf_ilce)
                        db_update("cari_kartlar", _hf_guncelle_alan, "id", int(cari_id))
                        try: db_read.clear()
                        except: pass
                        try: get_cari_listesi.clear()
                        except: pass
                        st.session_state.pop(f"hf_sonuc_{cari_id}", None)
                        st.session_state.pop(f"hf_ham_{cari_id}", None)
                        for _hf_alan_k3 in ("firma", "gsm", "sabit", "email", "adres", "il", "ilce"):
                            st.session_state.pop(f"hf_{_hf_alan_k3}_{cari_id}", None)
                        st.toast(f"✅ '{firma_adi}' güncellendi — eksik alanlar dolduruldu", icon="🔄")
                        st.rerun()
                except Exception as _hf_doldur_hata:
                    st.error(f"Hata: {_hf_doldur_hata}")
    with _tab_rdv:
        if firma_adi:
            st.markdown(f"**{firma_adi}** için randevu ekle")

        # ── Bu müşterinin ÖNCEKİ randevuları — hiçbiri silinmez, hepsi burada listelenir ──
        try:
            _rdv_sb_l = get_sb_client()
            _rdv_gecmis = pd.DataFrame(_rdv_sb_l.table("randevular").select("*").eq("musteri_id", int(cari_id)).order("randevu_tarihi", desc=True).execute().data) if _rdv_sb_l else pd.DataFrame()
        except Exception:
            _rdv_gecmis = pd.DataFrame()

        if not _rdv_gecmis.empty:
            st.caption(f"📌 {len(_rdv_gecmis)} randevu kayıtlı — yeni ekleme bunları silmez:")
            for _, _rg in _rdv_gecmis.iterrows():
                _rgc1, _rgc2, _rgc3, _rgc4 = st.columns([1.2, 1.2, 3, 0.6])
                _rgc1.caption(f"📅 {fmt_tarih(_rg.get('randevu_tarihi',''))} {_rg.get('randevu_saati','')}")
                _rgc2.caption(f"🏷️ {_rg.get('gorev','') or '—'}")
                _rgc3.caption(f"📝 {(_rg.get('aciklama','') or '—')[:60]}")
                if _rgc4.button("🗑", key=f"dlg_rdv_gecmis_sil_{cari_id}_{int(_rg['id'])}"):
                    try:
                        _rdv_sb_l.table("randevular").delete().eq("id", int(_rg["id"])).execute()
                        st.rerun()
                    except Exception as _rge:
                        st.error(f"Hata: {_rge}")
            st.divider()
        else:
            st.caption("Henüz randevu kaydı yok.")

        st.markdown("**➕ Yeni Randevu Ekle**")
        _dr1, _dr2 = st.columns(2)
        _rdv_t = _dr1.date_input("Tarih", key=f"dlg_rdv_t_{cari_id}")
        _rdv_s = _dr2.selectbox("Saat", [f"{h:02d}:{m:02d}" for h in range(8,21) for m in [0,30]], key=f"dlg_rdv_s_{cari_id}")
        _rdv_g = st.selectbox("Görev", ["Ziyaret","Toplantı","Online Görüşme","Telefon","Diğer"], key=f"dlg_rdv_g_{cari_id}")
        _rdv_n = st.text_area("Not", key=f"dlg_rdv_n_{cari_id}", placeholder="Randevu notu...", height=80)
        if st.button("📅 Randevu Kaydet", key=f"dlg_rdv_k_{cari_id}", type="primary", use_container_width=True):
            try:
                _sb_r = get_sb_client()
                if _sb_r:
                    _sb_r.table("randevular").insert({
                        "musteri_id":    cari_id,
                        "musteri_adi":   firma_adi,
                        "randevu_tarihi": str(_rdv_t),
                        "randevu_saati":  _rdv_s,
                        "gorev":          _rdv_g,
                        "aciklama":       _rdv_n,
                        "olusturan":      st.session_state.get("kullanici",""),
                    }).execute()
                    st.success(f"✅ Randevu eklendi!")
                    st.cache_data.clear()
                    st.rerun()
            except Exception as _re:
                st.error(f"Hata: {_re}")
    with _tab_yetkili:
        st.caption(f"**{firma_adi}** için birden fazla yetkili kişi ekleyebilirsiniz (ad, görev, email, GSM, sabit tel).")
        import json as _ykj
        _YK_ETIKET = "##YETKILI##"

        # ── Kart üzerindeki mevcut (eski) tek Yetkili alanını da listenin başında göster ──
        _yk_kart_liste = []
        try:
            _yk_sb0 = get_sb_client()
            _yk_kart_r = _yk_sb0.table("cari_kartlar").select("yetkili,gsm,sabit,email").eq("id", int(cari_id)).execute() if _yk_sb0 else None
            if _yk_kart_r and _yk_kart_r.data:
                _yk_kart = _yk_kart_r.data[0]
                if str(_yk_kart.get("yetkili","") or "").strip():
                    _yk_kart_liste.append({
                        "id": None, "ad": _yk_kart.get("yetkili",""), "gorev": "(Kart üzerindeki birincil yetkili)",
                        "email": _yk_kart.get("email","") or "", "gsm": _yk_kart.get("gsm","") or "",
                        "sabit_tel": _yk_kart.get("sabit","") or "", "kart_kaynakli": True,
                    })
        except Exception:
            pass

        try:
            _yk_sb = get_sb_client()
            _yk_ham = pd.DataFrame(_yk_sb.table("cari_aciklamalar").select("*").eq("cari_id", int(cari_id)).order("id").execute().data) if _yk_sb else pd.DataFrame()
        except Exception as _yke:
            _yk_ham = pd.DataFrame()
            st.caption(f"⚠️ Yetkililer yüklenemedi: {_yke}")

        _yk_liste = list(_yk_kart_liste)
        if not _yk_ham.empty and "aciklama" in _yk_ham.columns:
            for _, _hr in _yk_ham.iterrows():
                _metin = str(_hr.get("aciklama","") or "")
                if _metin.startswith(_YK_ETIKET):
                    try:
                        _kayit = _ykj.loads(_metin[len(_YK_ETIKET):])
                        _kayit["id"] = _hr.get("id")
                        _yk_liste.append(_kayit)
                    except Exception:
                        pass

        if _yk_liste:
            for _yk_r in _yk_liste:
                with st.container(border=True):
                    _yk_duzenleniyor = st.session_state.get("dlg_yk_duzenle_id") == _yk_r.get("id") and _yk_r.get("id") is not None

                    if _yk_duzenleniyor:
                        _dc1, _dc2, _dc3, _dc4, _dc5 = st.columns([2,1.4,2,1.4,1.4])
                        _d_ad    = _dc1.text_input("Ad Soyad", value=_yk_r.get("ad",""), key=f"dlg_yk_dad_{_yk_r['id']}")
                        _d_gorev = _dc2.text_input("Görev", value=_yk_r.get("gorev",""), key=f"dlg_yk_dgorev_{_yk_r['id']}")
                        _d_email = _dc3.text_input("Email", value=_yk_r.get("email",""), key=f"dlg_yk_demail_{_yk_r['id']}")
                        _d_gsm   = _dc4.text_input("GSM", value=_yk_r.get("gsm",""), key=f"dlg_yk_dgsm_{_yk_r['id']}")
                        _d_sabit = _dc5.text_input("Sabit Tel", value=_yk_r.get("sabit_tel",""), key=f"dlg_yk_dsabit_{_yk_r['id']}")
                        _de1, _de2 = st.columns(2)
                        if _de1.button("💾 Kaydet", key=f"dlg_yk_dkaydet_{_yk_r['id']}", type="primary", use_container_width=True):
                            try:
                                _yeni_json = _ykj.dumps({
                                    "ad": _d_ad.strip(), "gorev": _d_gorev.strip(), "email": _d_email.strip(),
                                    "gsm": _d_gsm.strip(), "sabit_tel": _d_sabit.strip(),
                                }, ensure_ascii=False)
                                _yk_sb.table("cari_aciklamalar").update({"aciklama": _YK_ETIKET + _yeni_json}).eq("id", int(_yk_r["id"])).execute()
                                st.session_state.pop("dlg_yk_duzenle_id", None)
                                st.success("✅ Güncellendi!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as _yue:
                                st.error(f"Hata: {_yue}")
                        if _de2.button("✖️ Vazgeç", key=f"dlg_yk_diptal_{_yk_r['id']}", use_container_width=True):
                            st.session_state.pop("dlg_yk_duzenle_id", None)
                            st.rerun()
                    else:
                        _yc1, _yc2, _yc3, _yc4, _yc5 = st.columns([2,1.4,2,1.4,1.4])
                        _yc1.markdown(f"**{_yk_r.get('ad','') or '—'}**")
                        _yc2.caption(f"🧩 {_yk_r.get('gorev','') or '—'}")
                        _yc3.caption(f"✉️ {_yk_r.get('email','') or '—'}")
                        _yc4.caption(f"📱 {_yk_r.get('gsm','') or '—'}")
                        _yc5.caption(f"☎️ {_yk_r.get('sabit_tel','') or '—'}")
                        if _yk_r.get("kart_kaynakli"):
                            st.caption("ℹ️ Bu kişi cari karttaki 'Yetkili' alanından otomatik geliyor — değiştirmek için 'Cari Kartı Düzenle' sekmesini kullanın.")
                        else:
                            _yb1, _yb2 = st.columns(2)
                            if _yb1.button("✏️ Düzenle", key=f"dlg_yk_duz_{cari_id}_{int(_yk_r['id'])}", use_container_width=True):
                                st.session_state["dlg_yk_duzenle_id"] = _yk_r["id"]
                                st.rerun()
                            if _yb2.button("🗑️ Sil", key=f"dlg_yk_sil_{cari_id}_{int(_yk_r['id'])}", use_container_width=True):
                                try:
                                    _yk_sb.table("cari_aciklamalar").delete().eq("id", int(_yk_r["id"])).execute()
                                    st.success("Silindi.")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as _yde:
                                    st.error(f"Hata: {_yde}")
        else:
            st.caption("Henüz yetkili eklenmemiş.")

        st.markdown("**➕ Yeni Yetkili Ekle**")
        _yn1, _yn2, _yn3, _yn4, _yn5 = st.columns([2,1.4,2,1.4,1.4])
        _yk_ad     = _yn1.text_input("", placeholder="Ad Soyad", key=f"dlg_yk_ad_{cari_id}", label_visibility="collapsed")
        _yk_gorev  = _yn2.text_input("", placeholder="Görev", key=f"dlg_yk_gorev_{cari_id}", label_visibility="collapsed")
        _yk_email  = _yn3.text_input("", placeholder="Email", key=f"dlg_yk_email_{cari_id}", label_visibility="collapsed")
        _yk_gsm    = _yn4.text_input("", placeholder="GSM", key=f"dlg_yk_gsm_{cari_id}", label_visibility="collapsed")
        _yk_sabit  = _yn5.text_input("", placeholder="Sabit Tel", key=f"dlg_yk_sabit_{cari_id}", label_visibility="collapsed")
        if st.button("👥 Yetkili Ekle", key=f"dlg_yk_ekle_{cari_id}", type="primary", use_container_width=True):
            if not _yk_ad.strip():
                st.warning("Ad Soyad gerekli.")
            else:
                try:
                    _yk_sb2 = get_sb_client()
                    _yk_json = _ykj.dumps({
                        "ad": _yk_ad.strip(), "gorev": _yk_gorev.strip(), "email": _yk_email.strip(),
                        "gsm": _yk_gsm.strip(), "sabit_tel": _yk_sabit.strip(),
                    }, ensure_ascii=False)
                    _yk_sb2.table("cari_aciklamalar").insert({
                        "cari_id": int(cari_id),
                        "aciklama": _YK_ETIKET + _yk_json,
                        "olusturan": st.session_state.get("kullanici",""),
                    }).execute()
                    st.success("✅ Yetkili eklendi!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as _yee:
                    st.error(f"Hata: {_yee}")
    with _tab_dn:
        st.caption(f"**{firma_adi}** için dış nakliye kaydı — Gönderen bilgileri bu müşteriden otomatik gelir.")
        _dn_tum = _dis_nakliye_yukle()
        _dn_bu_musteri = [r for r in _dn_tum if int(r.get("cari_id", 0) or 0) == int(cari_id)]

        with st.expander("➕ Yeni Dış Nakliye Kaydı Ekle", expanded=not _dn_bu_musteri):
            _dnt_ad, _dnt_yet, _dnt_tel = _dis_nakliye_tasiyici_secici(f"dlg_dn_{cari_id}")
            _dnf1, _dnf2 = st.columns(2)
            _dn_tasiyici_v = _dnf1.text_input("Taşıyıcı", value=_dnt_ad or "", key=f"dlg_dn_tasiyici_{cari_id}")
            _dn_yetkili_v = _dnf2.text_input("Yetkili", value=_dnt_yet or "", key=f"dlg_dn_yetkili_{cari_id}")
            _dn_yetkili_tel_v = st.text_input("Yetkili Tel", value=_dnt_tel or "", key=f"dlg_dn_yetkilitel_{cari_id}")
            _dn_tasiyici_kaydet_check = st.checkbox("Bu taşıyıcıyı ileride tekrar seçebilmek için kaydet",
                                                     key=f"dlg_dn_tas_kaydet_{cari_id}")
            if st.button("➕ Kaydı Oluştur", key=f"dlg_dn_ekle_btn_{cari_id}", type="primary", use_container_width=True):
                _musteri_bilgi = _dis_nakliye_musteri_bilgisi(cari_id)
                _yeni_id = int(max([int(r.get("id", 0) or 0) for r in _dn_tum], default=0)) + 1
                _yeni_kayit = {
                    "id": _yeni_id, "cari_id": int(cari_id), "tarih": str(datetime.now().date()),
                    "gonderen_firma": _musteri_bilgi.get("firma", firma_adi) or firma_adi,
                    "gonderici_tel": _musteri_bilgi.get("gsm") or _musteri_bilgi.get("sabit") or "",
                    "gonderen_adres": _musteri_bilgi.get("adres", "") or "",
                    "gonderen_il": _musteri_bilgi.get("il", "") or "",
                    "gonderen_ilce": _musteri_bilgi.get("ilce", "") or "",
                    "alici_firma": "", "alici_tel": "", "alici_adres": "", "alici_il": "", "alici_ilce": "",
                    "vergi_dairesi": "", "vergi_no": "", "odeme_turu": "",
                    "adet1": 0, "fiyat1": 0, "yekun1": 0, "kdvli1": 0, "odendi1": False,
                    "tasiyici": _dn_tasiyici_v, "yetkili": _dn_yetkili_v, "yetkili_tel": _dn_yetkili_tel_v,
                    "adet2": 0, "fiyat2": 0, "yekun2": 0, "kdvli2": 0, "odendi2": False,
                    "kar": 0,
                }
                _dn_tum.append(_yeni_kayit)
                if _dis_nakliye_kaydet(_dn_tum):
                    if _dn_tasiyici_kaydet_check and _dn_tasiyici_v.strip():
                        _tas_liste = _dis_nakliye_tasiyici_yukle()
                        if not any(t.get("tasiyici","").strip().lower() == _dn_tasiyici_v.strip().lower() for t in _tas_liste):
                            _tas_liste.append({"tasiyici": _dn_tasiyici_v, "yetkili": _dn_yetkili_v, "yetkili_tel": _dn_yetkili_tel_v})
                            _dis_nakliye_tasiyici_kaydet(_tas_liste)
                    st.success("✅ Dış nakliye kaydı eklendi — aşağıdaki tabloda diğer bilgileri (alıcı, adet, fiyat vb.) doldurup Kaydet'e basabilirsin.")
                    st.rerun()
                else:
                    st.error("❌ Kaydedilemedi, bağlantıyı kontrol et.")

        if _dn_bu_musteri:
            _dn_df = pd.DataFrame(_dn_bu_musteri)
            for _c in _DIS_NAKLIYE_KOLONLAR:
                if _c not in _dn_df.columns:
                    _dn_df[_c] = 0 if _c in _DIS_NAKLIYE_SAYI_KOLON or _c in _DIS_NAKLIYE_HESAP_KOLON else (False if _c in _DIS_NAKLIYE_CHECK_KOLON else "")
            _dn_df = _dis_nakliye_hesapla(_dn_df)
            _dn_df = _dn_df[["id", "cari_id"] + _DIS_NAKLIYE_KOLONLAR]
            _dn_df = _dn_df.reset_index(drop=True)
            _dn_df.insert(0, "Seç", False)
            _dn_df.index = _dn_df.index + 1
            _dn_df.index.name = "S.No"

            _dn_edited = st.data_editor(
                _dn_df, use_container_width=True, num_rows="fixed",
                column_config={
                    **_dis_nakliye_col_config(), "id": None, "cari_id": None,
                    "Seç": st.column_config.CheckboxColumn("Seç", default=False),
                },
                key=f"dlg_dn_editor_{cari_id}",
                height=min(400, 45 + (len(_dn_df) * 35) + 5),
            )

            _dn_secili = _dn_edited[_dn_edited["Seç"] == True]
            _dn_secili_sayi = len(_dn_secili)
            _dn_secili_idler = _dn_secili["id"].tolist() if not _dn_secili.empty else []

            _dnk1, _dnk2 = st.columns([1, 1])
            with _dnk1:
                if st.button("💾 Değişiklikleri Kaydet", key=f"dlg_dn_kaydet_{cari_id}", type="primary", use_container_width=True):
                    _dn_final = _dn_edited.drop(columns=["Seç"]).reset_index(drop=True).copy()
                    _dn_final = _dis_nakliye_hesapla(_dn_final)
                    for _c in ["id", "cari_id"]:
                        if _c not in _dn_final.columns:
                            _dn_final[_c] = 0
                    _dn_final["id"] = _dn_final["id"].apply(lambda x: int(x) if str(x).strip() not in ("", "nan", "None") and float(x) > 0 else 0)
                    _dn_final["cari_id"] = int(cari_id)
                    _yeni_id_sayac = int(max([int(r.get("id", 0) or 0) for r in _dn_tum], default=0)) + 1
                    _bu_musteri_yeni = []
                    for _, _row in _dn_final.iterrows():
                        _rd = _row.to_dict()
                        if not _rd.get("id"):
                            _rd["id"] = _yeni_id_sayac
                            _yeni_id_sayac += 1
                        _bu_musteri_yeni.append(_rd)
                    _diger_musteriler = [r for r in _dn_tum if int(r.get("cari_id", 0) or 0) != int(cari_id)]
                    _tam_liste = _diger_musteriler + _bu_musteri_yeni
                    if _dis_nakliye_kaydet(_tam_liste):
                        st.toast("✅ Dış nakliye kayıtları güncellendi!", icon="✅")
                        st.rerun()
                    else:
                        st.error("❌ Kaydedilemedi, bağlantıyı kontrol et.")
            with _dnk2:
                if _dn_secili_sayi > 0:
                    if not st.session_state.get(f"_dn_sil_onay_bekliyor_{cari_id}"):
                        if st.button(f"🗑️ Seçili {_dn_secili_sayi} Kaydı Sil", key=f"dlg_dn_sil_{cari_id}", use_container_width=True):
                            st.session_state[f"_dn_sil_onay_bekliyor_{cari_id}"] = True
                            st.rerun()
                else:
                    st.caption("Silmek için satırları soldaki Seç kutusuyla işaretle.")

            if _dn_secili_sayi > 0 and st.session_state.get(f"_dn_sil_onay_bekliyor_{cari_id}"):
                st.warning(f"⚠️ Seçili {_dn_secili_sayi} kayıt kalıcı olarak silinecek, geri alınamaz! Silmek istediğine emin misin?")
                _dnsa1, _dnsa2 = st.columns(2)
                with _dnsa1:
                    if st.button(f"✅ Evet, {_dn_secili_sayi} kaydı sil", type="primary", key=f"dlg_dn_sil_onay_{cari_id}", use_container_width=True):
                        _dn_silinecek_idler = set(int(x) for x in _dn_secili_idler)
                        _dn_kalan = [r for r in _dn_tum if int(r.get("id", 0) or 0) not in _dn_silinecek_idler]
                        if _dis_nakliye_kaydet(_dn_kalan):
                            st.session_state.pop(f"_dn_sil_onay_bekliyor_{cari_id}", None)
                            st.success(f"✅ {_dn_secili_sayi} kayıt silindi!")
                            st.rerun()
                        else:
                            st.error("❌ Silinemedi, bağlantıyı kontrol et.")
                with _dnsa2:
                    if st.button("❌ Vazgeç", key=f"dlg_dn_sil_vazgec_{cari_id}", use_container_width=True):
                        st.session_state.pop(f"_dn_sil_onay_bekliyor_{cari_id}", None)
                        st.rerun()
        else:
            st.caption("Bu müşteri için henüz dış nakliye kaydı yok.")
    with _tab_kargo:
        # ── KARGO GİRİŞİ — cari_kartlar'a yeni kolon açmadan (migration yok
        # kuralı), her müşterinin kargo çıkış kayıtları kullanici_tercih
        # tablosunda MÜŞTERİYE ÖZEL bir anahtarda (JSON liste) tutulur:
        # anahtar = "_kargo_kayitlari_<cari_id>"
        # NOT: _kg_kayitlari_yukle/_kg_kayitlari_kaydet artık GLOBAL (dosyanın
        # başında) — hem bu dialog hem Kargolar sayfası AYNI fonksiyonu kullanır.
        _kg_sb = get_sb_client()
        _kg_anahtar = f"_kargo_kayitlari_{int(cari_id)}"

        st.caption(f"**{firma_adi}** için kargo çıkış kaydı ekle:")
        # Kayıtlı müşteri listesi — Gönderen/Alıcı/Fatura Ödeyen alanlarında
        # elle yazmak yerine sistemdeki müşterilerden seçilebilsin diye.
        try:
            _kg_musteri_liste = sorted(get_cari_listesi()["firma"].dropna().astype(str).unique().tolist())
        except Exception:
            _kg_musteri_liste = []
        _kg_musteri_opts = ["-- Seç veya elle yaz --"] + _kg_musteri_liste
        _kg_il_opts = ["-- İl seçilir --"] + [_tr_buyuk(a) for a in (_IL_SUTUN_LISTESI[:-1] + _IL_DIGER_LISTESI)]
        try:
            _kg_tasiyici_opts = ["-- Seç veya elle yaz --"] + sorted(set(
                _t.get("firma_adi", "") for _t in _tedarikci_yukle_goster() if not _t.get("silindi") and _gecerli_metin(_t.get("firma_adi", ""))))
        except Exception:
            _kg_tasiyici_opts = ["-- Seç veya elle yaz --"]
        # Bu iller "yakın/yerel" sayılır — Alıcı İl bunlardan biriyse Dış Nakliye
        # alanları hiç gösterilmez (dış bölgeye çıkmıyor demektir).
        _KG_YEREL_ILLER = [_tr_buyuk(a) for a in ["İzmir", "Bursa", "Kocaeli", "Tekirdağ", "İstanbul", "Manisa"]]

        # NOT: st.form KULLANILMIYOR — "Alıcı İl" seçimine göre Dış Nakliye
        # bölümünün anlık (canlı) gösterilip gizlenmesi gerekiyor; form içindeki
        # widget'lar sadece gönderilince işlenir, canlı tepki veremez.
        # ── Manuel olarak hatırlanan Alıcı Firma isimleri de "Alıcı Firma"
        # açılır listesine eklenir — bir daha elle yazmaya gerek kalmasın,
        # doğrudan listeden seçilebilsin.
        _kg_manuel_alici_hafiza = _kg_manuel_alici_yukle()
        _kg_musteri_opts_buyuk = set(_tr_buyuk(x) for x in _kg_musteri_liste)
        _kg_hafizadan_ek = sorted([f for f in _kg_manuel_alici_hafiza.keys() if f not in _kg_musteri_opts_buyuk])
        _kg_alici_opts = ["-- Seç veya elle yaz --"] + sorted(set(_kg_musteri_liste) | set(_kg_hafizadan_ek))

        _kgc1, _kgc2, _kgc3 = st.columns(3)
        _kg_tarih = _kgc1.date_input("Tarih *", key=f"kg_tarih_{cari_id}")
        _kg_takip = _kgc2.text_input("Takip No", key=f"kg_takip_{cari_id}")
        _kg_fatura_no = _kgc3.text_input("Fatura No", key=f"kg_fatura_no_{cari_id}")

        _kg_gonderen_idx = (_kg_musteri_opts.index(firma_adi) if firma_adi in _kg_musteri_opts else 0)
        _kg_gonderen_sec = _kgc1.selectbox("Gönderen Firma", _kg_musteri_opts, index=_kg_gonderen_idx, key=f"kg_gonderen_sec_{cari_id}")
        _kg_gonderen_elle = _kgc1.text_area("(Listede yoksa elle yaz)", key=f"kg_gonderen_elle_{cari_id}", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz", height=68)
        _kg_alici_sec = _kgc2.selectbox("Alıcı Firma", _kg_alici_opts, key=f"kg_alici_sec_{cari_id}")
        _kg_alici_elle = _kgc2.text_area("(Listede yoksa elle yaz)", key=f"kg_alici_elle_{cari_id}", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz", height=68)
        # ── Fatura Ödeyen — "Ödeme Türü (Fatura)" seçimine göre OTOMATİK belirlenir:
        # PÖ veya CH ise Gönderen Firma, ÜA ise Alıcı Firma otomatik seçilir.
        # (O widget kodda daha aşağıda tanımlı olsa da, session_state'teki
        # ÖNCEKİ seçimi buradan okuyabiliyoruz — Streamlit rerun'da widget
        # değerleri kod çalışmadan ÖNCE zaten session_state'te hazır olur.)
        _kg_gonderen_hesaplanan = _kg_gonderen_elle.strip() or (_kg_gonderen_sec if _kg_gonderen_sec != "-- Seç veya elle yaz --" else "")
        _kg_alici_hesaplanan = _kg_alici_elle.strip() or (_kg_alici_sec if _kg_alici_sec != "-- Seç veya elle yaz --" else "")
        _kg_odeme_sekli_onceki = st.session_state.get(f"kg_fatura_odeme_sekli_{cari_id}", "")
        _kg_fatura_varsayilan_idx = 0
        if _kg_odeme_sekli_onceki in ("PÖ", "CH") and _kg_gonderen_hesaplanan in _kg_musteri_opts:
            _kg_fatura_varsayilan_idx = _kg_musteri_opts.index(_kg_gonderen_hesaplanan)
        elif _kg_odeme_sekli_onceki == "ÜA" and _kg_alici_hesaplanan in _kg_musteri_opts:
            _kg_fatura_varsayilan_idx = _kg_musteri_opts.index(_kg_alici_hesaplanan)
        _kg_fatura_sec = _kgc3.selectbox("Fatura Ödeyen *", _kg_musteri_opts, index=_kg_fatura_varsayilan_idx, key=f"kg_fatura_sec_{cari_id}")
        _kg_fatura_elle = _kgc3.text_area("(Listede yoksa elle yaz)", key=f"kg_fatura_elle_{cari_id}", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz", height=68)

        _kg_gonderen_il = _kgc1.selectbox("Gönderen İl", _kg_il_opts, key=f"kg_gonderen_il_{cari_id}")
        # ── Alıcı İl — daha önce bu Alıcı Firma için kaydedilmiş bir il varsa
        # otomatik önerilir (elle her seferinde yazmaya gerek kalmasın diye).
        _kg_alici_firma_hesaplanan = _kg_alici_elle.strip() or (_kg_alici_sec if _kg_alici_sec != "-- Seç veya elle yaz --" else "")
        _kg_alici_il_varsayilan_idx = 0
        if _kg_alici_firma_hesaplanan:
            _kg_hafizadaki_il = _kg_manuel_alici_hafiza.get(_tr_buyuk(_kg_alici_firma_hesaplanan))
            if _kg_hafizadaki_il and _kg_hafizadaki_il in _kg_il_opts:
                _kg_alici_il_varsayilan_idx = _kg_il_opts.index(_kg_hafizadaki_il)
        _kg_alici_il = _kgc2.selectbox("Alıcı İl", _kg_il_opts, index=_kg_alici_il_varsayilan_idx, key=f"kg_alici_il_{cari_id}")
        if _kg_alici_firma_hesaplanan and _kg_alici_il != "-- İl seçilir --" and _kg_manuel_alici_hafiza.get(_tr_buyuk(_kg_alici_firma_hesaplanan)):
            st.caption(f"💡 '{_kg_alici_firma_hesaplanan}' için daha önce kaydedilen il otomatik önerildi.")
        _kg_fatura_odeme_sekli = _kgc3.selectbox("Ödeme Türü (Fatura)", ["", "Faturasız", "PÖ", "ÜA", "CH"], key=f"kg_fatura_odeme_sekli_{cari_id}",
                                                  help="PÖ/CH seçilirse Fatura Ödeyen otomatik Gönderen olur, ÜA seçilirse otomatik Alıcı olur.")

        _kg_tur = _kgc1.text_input("Tür", key=f"kg_tur_{cari_id}", placeholder="Koli / Palet / ...")
        _kg_desi = _kg_tr_parse(_kgc2.text_input("Desi", value="0", key=f"kg_desi_{cari_id}", help="Virgülle ondalık yazabilirsin (ör. 12,5)"))
        _kg_kilo = _kg_tr_parse(_kgc3.text_input("Kilo", value="0", key=f"kg_kilo_{cari_id}", help="Virgülle ondalık yazabilirsin (ör. 12,5)"))

        # ── OTOMATİK HESAPLAMA ZİNCİRİ — Yekün (B.Tutar × Adet) → Sigorta %6 →
        # Ara Toplam → Kdv %20 → Son Toplam, hepsi B.Tutar ve Adet'ten
        # türetilir. ELLE YAZILMAZ; burada sadece CANLI ÖNİZLEME gösterilir,
        # kayıt anında da aynı mantıkla hesaplanır. Tüm parasal kutular
        # Türkçe biçimde (virgül ondalık, nokta binlik) yazılır/gösterilir.
        _kg_adet = _kgc1.number_input("Adet", min_value=0, step=1, key=f"kg_adet_{cari_id}")
        _kg_tutar = _kg_tr_parse(_kgc2.text_input("B.Tutar", value="0", key=f"kg_tutar_{cari_id}",
                                  help="Virgülle ondalık yaz (ör. 90,72). Yekün, Sigorta, Ara Toplam, Kdv ve Son Toplam bunun üzerinden otomatik hesaplanır."))
        _kg_onizleme = _kg_hesap_zinciri({"tutar": _kg_tutar, "adet": _kg_adet})
        _kgc3.text_input("Yekün (₺)", value=_kg_tr_format(_kg_onizleme['yekun']), key=f"kg_onizleme_yekun_{cari_id}_{_kg_tutar}_{_kg_adet}",
                          help="B.Tutar × Adet")
        _kgc1.text_input("Sigorta %6 (₺)", value=_kg_tr_format(_kg_onizleme['sigorta']), key=f"kg_onizleme_sigorta_{cari_id}_{_kg_tutar}_{_kg_adet}")
        _kgc2.text_input("Ara Toplam (₺)", value=_kg_tr_format(_kg_onizleme['ara_toplam']), key=f"kg_onizleme_ara_{cari_id}_{_kg_tutar}_{_kg_adet}")
        _kgc3.text_input("Kdv %20 (₺)", value=_kg_tr_format(_kg_onizleme['kdv']), key=f"kg_onizleme_kdv_{cari_id}_{_kg_tutar}_{_kg_adet}")
        _kgc1.text_input("Son Toplam (₺)", value=_kg_tr_format(_kg_onizleme['toplam_fatura']), key=f"kg_onizleme_son_{cari_id}_{_kg_tutar}_{_kg_adet}")

        _kg_yetkili = _kgc2.text_input("Yetkili", key=f"kg_yetkili_{cari_id}", placeholder="İlgili kişiyi elle yaz")
        _kg_tahsilat = _kgc3.selectbox("Tahsilat", ["", "Evet", "Hayır", "Kısmi"], key=f"kg_tahsilat_{cari_id}")
        _kg_not = _kgc1.text_input("Not", key=f"kg_not_{cari_id}", placeholder="Serbest not (opsiyonel)")
        _kg_odeme_tur = ""  # Bu şemada "Ödeme Türü" (Nakit/Havale/Çek) yok — kaldırıldı

        # ── Dış Nakliye bölümü — SADECE Alıcı İl "yerel" iller dışında bir il
        # (dış bölge) ise gösterilir. Yerel il seçiliyse bu alanlar hiç görünmez.
        _kg_dis_bolge_mi = (_kg_alici_il != "-- İl seçilir --" and _kg_alici_il not in _KG_YEREL_ILLER)
        _kg_dn_firma, _kg_dn_fatura, _kg_dn_detay, _kg_dn_tutar, _kg_musteri_tutar, _kg_dn_odeme = "", "", "", 0.0, 0.0, ""
        if _kg_dis_bolge_mi:
            st.markdown(f"**🚚 Dış Nakliye** — *{_kg_alici_il} dış bölge sayıldığı için gerekli*")
            with st.container(border=True):
                _kgd1, _kgd2, _kgd3 = st.columns(3)
                _kg_dn_firma_sec = _kgd1.selectbox("Dış Nakliye Firma", _kg_tasiyici_opts, key=f"kg_dn_firma_sec_{cari_id}")
                _kg_dn_firma_elle = _kgd1.text_input("(Listede yoksa elle yaz)", key=f"kg_dn_firma_elle_{cari_id}", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz")
                _kg_dn_fatura = _kgd2.text_input("Dış Nakliye Fatura", key=f"kg_dn_fatura_{cari_id}")
                _kg_dn_detay = _kgd3.text_input("Dış Nakliye Detay", key=f"kg_dn_detay_{cari_id}", placeholder="Örn: 2 Palet")
                _kg_dn_tutar = _kg_tr_parse(_kgd1.text_input("Dış Nakliye Tutar", value="0", key=f"kg_dn_tutar_{cari_id}", help="Virgülle ondalık yazabilirsin (ör. 3.500,50)"))
                _kg_musteri_tutar = _kg_tr_parse(_kgd2.text_input("Müşteri Tutar", value="0", key=f"kg_musteri_tutar_{cari_id}", help="Virgülle ondalık yazabilirsin (ör. 3.500,50)"))
                _kg_dn_odeme = _kgd3.selectbox("İşlendi mi?", ["", "Evet", "Hayır", "Kısmi"], key=f"kg_dn_odeme_{cari_id}")
                st.caption("🧮 Kar/Zarar, kaydedince otomatik hesaplanır: Müşteri Tutar − Dış Nakliye Tutar (pozitifse Kar, negatifse Zarar)")
                _kg_dn_firma = _kg_dn_firma_elle.strip() or (_kg_dn_firma_sec if _kg_dn_firma_sec != "-- Seç veya elle yaz --" else "")
        else:
            st.caption("💡 Alıcı İl olarak yerel bir il (İstanbul, Bursa, İzmir, Kocaeli, Tekirdağ, Manisa) seçilmedi/seçilirse Dış Nakliye alanları burada görünmez.")

        st.divider()
        if st.button("💾 Kargo Girişini Kaydet", type="primary", key=f"kg_kaydet_btn_{cari_id}", use_container_width=True):
            # Elle yazılan varsa o, yoksa seçilen (seçim "-- Seç veya elle yaz --" ise boş) kullanılır
            _kg_gonderen = _kg_gonderen_elle.strip() or (_kg_gonderen_sec if _kg_gonderen_sec != "-- Seç veya elle yaz --" else "")
            _kg_alici = _kg_alici_elle.strip() or (_kg_alici_sec if _kg_alici_sec != "-- Seç veya elle yaz --" else "")
            _kg_fatura_odeyen = _kg_fatura_elle.strip() or (_kg_fatura_sec if _kg_fatura_sec != "-- Seç veya elle yaz --" else "")
            # ── ZORUNLU ALAN KONTROLÜ ──
            _kg_eksikler = []
            if not _kg_tarih:
                _kg_eksikler.append("Tarih")
            if not _kg_fatura_odeyen:
                _kg_eksikler.append("Fatura Ödeyen")
            if _kg_eksikler:
                st.error(f"⚠️ Zorunlu alan(lar) eksik: {', '.join(_kg_eksikler)}")
            else:
                _kg_gonderen_il_deger = _kg_gonderen_il if _kg_gonderen_il != "-- İl seçilir --" else ""
                _kg_alici_il_deger = _kg_alici_il if _kg_alici_il != "-- İl seçilir --" else ""
                _kg_liste = list(_kg_kayitlari_yukle(_kg_anahtar))
                # Yazdığın her şey (il isimleri dahil) kaydedilirken otomatik
                # BÜYÜK HARFE çevrilir — Türkçe karaktere duyarlı şekilde.
                _kg_yeni_kayit = {
                    "tarih": str(_kg_tarih), "takip_no": _tr_buyuk(_kg_takip), "fatura_no": _tr_buyuk(_kg_fatura_no), "gonderen_firma": _tr_buyuk(_kg_gonderen),
                    "alici_firma": _tr_buyuk(_kg_alici), "fatura_firma": _tr_buyuk(_kg_fatura_odeyen),
                    "gonderen_il": _tr_buyuk(_kg_gonderen_il_deger), "alici_il": _tr_buyuk(_kg_alici_il_deger),
                    "fatura_odeme_sekli": _kg_fatura_odeme_sekli, "yetkili": _tr_buyuk(_kg_yetkili), "not": _kg_not,
                    "adet": _kg_adet, "tur": _tr_buyuk(_kg_tur), "tutar": _kg_tutar,
                    "desi": _kg_desi, "kilo": _kg_kilo,
                    "odeme_tur": _kg_odeme_tur, "tahsilat_durumu": _kg_tahsilat,
                    "dis_nakliye_firma": _tr_buyuk(_kg_dn_firma), "dis_nakliye_fatura": _tr_buyuk(_kg_dn_fatura),
                    "dis_nakliye_detay": _tr_buyuk(_kg_dn_detay), "dis_nakliye_tutar": _kg_dn_tutar,
                    "musteri_tutar": _kg_musteri_tutar, "dis_nakliye_odeme_durumu": _kg_dn_odeme,
                }
                # Sigorta/Ara Toplam/Kdv/Son Toplam VE Kar/Zarar burada da
                # (canlı önizlemedekiyle birebir aynı mantıkla) OTOMATİK
                # hesaplanıp kayda yazılır — elle girilen bir değer yok.
                _kg_hesap_zinciri(_kg_yeni_kayit)
                _kg_kar_zarar_hesapla(_kg_yeni_kayit)
                _kg_liste.append(_kg_yeni_kayit)
                _kg_kayitlari_kaydet(_kg_anahtar, _kg_liste)
                _kg_kayitlari_yukle.clear()
                _cari_gerceklesen_ciro_ekle(cari_id, _kg_efektif_tutar(_kg_liste[-1]))
                # Alıcı Firma + Alıcı İl çiftini kalıcı hafızaya yaz — bir dahaki
                # sefere bu firma yazılınca ili otomatik gelsin.
                if _kg_alici and _kg_alici_il_deger:
                    _kg_hafiza_guncel = dict(_kg_manuel_alici_hafiza)
                    _kg_hafiza_guncel[_tr_buyuk(_kg_alici)] = _tr_buyuk(_kg_alici_il_deger)
                    _kg_manuel_alici_kaydet(_kg_hafiza_guncel)
                    _kg_manuel_alici_yukle.clear()
                st.toast("✅ Kargo girişi kaydedildi", icon="🚚")
                st.rerun()

        _kg_mevcut_ham = _kg_kayitlari_yukle(_kg_anahtar)
        # GÜVENLİK: silinen kayıtlar listeden TAMAMEN çıkarılmıyor, sadece
        # "silindi" işaretliyse normal görünümden gizleniyor — "🗑️ Silinenler"
        # bölümünden (Kargolar sayfasında) geri alınabilir.
        _kg_silinmis_kayitlar = [_k for _k in _kg_mevcut_ham if _k.get("silindi")]
        _kg_mevcut = [_k for _k in _kg_mevcut_ham if not _k.get("silindi")]
        if _kg_mevcut:
            st.divider()
            st.caption(f"📋 Bu müşteri için {len(_kg_mevcut)} kargo kaydı — düzenleyebilir, seçip silebilirsin:")
            import pandas as _kg_pd
            _kg_df = _kg_pd.DataFrame(_kg_mevcut)
            _kg_df = _kg_df.fillna("")  # eski kayıtlarda olmayan alanlar "None" değil boş görünsün
            _kg_df.insert(0, "Seç", False)
            _KG_SIRA = ["tarih", "takip_no", "fatura_no", "gonderen_firma", "alici_firma", "fatura_firma", "yetkili",
                        "gonderen_il", "alici_il", "tur", "desi", "kilo", "adet", "fatura_odeme_sekli", "tutar", "yekun", "sigorta",
                        "ara_toplam", "kdv", "toplam_fatura", "odeme_tur", "tahsilat_durumu", "not", "dis_nakliye_firma",
                        "dis_nakliye_fatura", "dis_nakliye_detay", "dis_nakliye_tutar", "musteri_tutar", "kar", "zarar",
                        "dis_nakliye_odeme_durumu"]
            _kg_df = _kg_df[["Seç"] + [c for c in _KG_SIRA if c in _kg_df.columns]
                            + [c for c in _kg_df.columns if c not in (["Seç", "silindi", "silinme_tarihi"] + _KG_SIRA)]]
            _kg_kolon_isim = {"tarih": "Tarih", "takip_no": "Takip No", "fatura_no": "Fatura No",
                               "gonderen_firma": "Gönderen", "alici_firma": "Alıcı", "fatura_firma": "Fatura Ödeyen", "yetkili": "Yetkili",
                               "gonderen_il": "Gönderen İl", "alici_il": "Alıcı İl", "tur": "Tür", "desi": "Desi", "kilo": "Kilo", "adet": "Adet",
                               "fatura_odeme_sekli": "Fatura Ödeme Şekli", "tutar": "B.Tutar", "yekun": "Yekün", "sigorta": "Sigorta %6", "ara_toplam": "Ara Toplam",
                               "kdv": "Kdv %20", "toplam_fatura": "Son Toplam", "odeme_tur": "Ödeme Türü", "tahsilat_durumu": "Tahsilat", "not": "Not",
                               "dis_nakliye_firma": "Dış Nakliye Firma", "dis_nakliye_fatura": "Dış Nakliye Fatura", "dis_nakliye_detay": "Dış Nakliye Detay",
                               "dis_nakliye_tutar": "Dış Nakliye Tutar", "musteri_tutar": "Müşteri Tutar", "kar": "Kar", "zarar": "Zarar",
                               "dis_nakliye_odeme_durumu": "Dış Nak. Ödeme"}
            _kg_df = _kg_df.rename(columns=_kg_kolon_isim)
            # Takip No / Fatura No PARASAL DEĞİL — geçmişte Excel'den sayı
            # olarak okunup '1910372.0' gibi gereksiz '.0' kuyruğuyla
            # kaydedilmiş kayıtlar burada temizlenip düz '1910372' gösterilir
            # (kullanıcı isteği). Kaydedince bu temiz hâliyle kalıcı olur.
            for _kg_ref_kol in ("Takip No", "Fatura No"):
                if _kg_ref_kol in _kg_df.columns:
                    _kg_df[_kg_ref_kol] = _kg_df[_kg_ref_kol].map(_kg_referans_no_temizle)
            # Kar/Zarar'da ikisinden sadece biri dolu olur — 0 yerine "-"
            # göstersin diye biçimlendiriliyor (kayıt sırasında gerçek sayısal
            # değer zaten otomatik yeniden hesaplanıp yazılıyor).
            for _kg_kz_kol in ("Kar", "Zarar"):
                if _kg_kz_kol in _kg_df.columns:
                    _kg_df[_kg_kz_kol] = _kg_df[_kg_kz_kol].map(_kg_sifir_tire)
            # Bunlar salt okunur/otomatik hesaplanan sütunlar olduğu için
            # Türkçe biçime (virgül ondalık) çevirmek güvenli — Kaydet/Hesapla
            # bunları B.Tutar'dan (sayısal) yeniden türetiyor, buradaki metin
            # halini hiç okumuyor.
            for _kg_hesap_kol in ("B.Tutar", "Desi", "Kilo", "Yekün", "Sigorta %6", "Ara Toplam", "Kdv %20", "Son Toplam",
                                   "Müşteri Tutar", "Dış Nakliye Tutar"):
                if _kg_hesap_kol in _kg_df.columns:
                    _kg_df[_kg_hesap_kol] = _kg_df[_kg_hesap_kol].map(_kg_tr_format)
            # Kolon Ayarları'nda ayarlanan (5-50 arası) genişlikleri burada da uygula —
            # yoksa tablo çok geniş açılıp okunması zorlaşıyordu.
            if "_kargo_kol_genislik" not in st.session_state:
                try:
                    _sb_kg_gen0 = get_sb_client()
                    if _sb_kg_gen0:
                        _r_kg_gen0 = _sb_kg_gen0.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_kargo_kol_genislik").execute()
                        if _r_kg_gen0.data:
                            import json as _kggenj0
                            st.session_state["_kargo_kol_genislik"] = _kggenj0.loads(_r_kg_gen0.data[0]["deger"])
                except Exception:
                    pass
            _kg_kol_genislik = st.session_state.get("_kargo_kol_genislik", {})
            _KG_OTOMATIK_HESAPLI_KOLONLAR = {
                "Kar": "Otomatik hesaplanır: Müşteri Tutar − Dış Nakliye Tutar (pozitifse burada görünür)",
                "Zarar": "Otomatik hesaplanır: Müşteri Tutar − Dış Nakliye Tutar (negatifse burada görünür)",
                "Yekün": "Otomatik hesaplanır: B.Tutar × Adet",
                "Sigorta %6": "Otomatik hesaplanır: Yekün × %6",
                "Ara Toplam": "Otomatik hesaplanır: Yekün + Sigorta %6",
                "Kdv %20": "Otomatik hesaplanır: Ara Toplam × %20",
                "Son Toplam": "Otomatik hesaplanır: Ara Toplam + Kdv %20",
            }
            _kg_col_config = {"Seç": st.column_config.CheckboxColumn("Seç", default=False, width=40)}
            # Dış Nakliye Firma SADECE Tedarikçi listesinden gelir — eski
            # kargo kayıtlarındaki (bazen bozuk/uzun/"None" gibi) elle
            # yazılmış değerler seçeneklere KARIŞTIRILMAZ (kullanıcı isteği).
            _kg_dnf_opts = sorted(set(
                _t.get("firma_adi", "") for _t in _tedarikci_yukle_goster() if not _t.get("silindi") and _gecerli_metin(_t.get("firma_adi", ""))
            ))
            for _kg_kol_ad in _kg_df.columns:
                if _kg_kol_ad == "Seç":
                    continue
                _kg_gen = _kg_kol_genislik.get(_kg_kol_ad, 15)
                if _kg_kol_ad in _KG_OTOMATIK_HESAPLI_KOLONLAR:
                    # Bu sütunlar artık ELLE YAZILMIYOR — otomatik hesaplanıp
                    # kayıt anında üzerine yazılıyor.
                    _kg_col_config[_kg_kol_ad] = st.column_config.Column(
                        _kg_kol_ad, width=int(_kg_gen) * 8, disabled=True,
                        help=_KG_OTOMATIK_HESAPLI_KOLONLAR[_kg_kol_ad])
                elif _kg_kol_ad == "Dış Nakliye Firma":
                    _kg_col_config[_kg_kol_ad] = st.column_config.SelectboxColumn(
                        _kg_kol_ad, width=int(_kg_gen) * 8, options=[""] + _kg_dnf_opts,
                        help="Tedarikçi sayfasından eklediğin firmalar burada listelenir.")
                else:
                    _kg_col_config[_kg_kol_ad] = st.column_config.Column(_kg_kol_ad, width=int(_kg_gen) * 8)
            _kg_ver_anahtari = f"_kg_editor_versiyon_{cari_id}"
            if _kg_ver_anahtari not in st.session_state:
                st.session_state[_kg_ver_anahtari] = 0
            _kg_tumu_secili_anahtari = f"_kg_tumu_secili_mod_{cari_id}"
            # NOT: Bayrak artık KALICI (pop değil) — Streamlit'in data_editor'ü
            # seçimi taban veriye göre değil FARK olarak sakladığı için, tek
            # seferlik bayrak ikinci render'da (Sil'e basılınca) sıfırlanıp
            # seçimi kaybettiriyordu. Şimdi Temizle'ye ya da başarılı bir
            # Kaydet/Sil işlemine kadar her render'da yeniden uygulanıyor.
            if st.session_state.get(_kg_tumu_secili_anahtari, False):
                _kg_df["Seç"] = True
            _kg_df = _hic_none_gosterme(_kg_df)
            _kg_editor_key = f"kg_editor_{cari_id}_{st.session_state[_kg_ver_anahtari]}"
            _kg_duzenlenen = st.data_editor(_kg_df, use_container_width=True, hide_index=True,
                                             key=_kg_editor_key,
                                             column_config=_kg_col_config)
            _kgb0a, _kgb0b, _kgb1, _kgb2 = st.columns(4)
            with _kgb0a:
                if st.button("☑️ Tümünü Seç", key=f"kg_tumunu_sec_{cari_id}", use_container_width=True):
                    st.session_state[_kg_tumu_secili_anahtari] = True
                    st.session_state[_kg_ver_anahtari] += 1
                    st.rerun()
            with _kgb0b:
                if st.button("⬜ Seçimi Temizle", key=f"kg_secimi_temizle_{cari_id}", use_container_width=True):
                    st.session_state[_kg_tumu_secili_anahtari] = False
                    st.session_state[_kg_ver_anahtari] += 1
                    st.rerun()
            with _kgb1:
                if st.button("💾 Değişiklikleri Kaydet", key=f"kg_duzenle_kaydet_{cari_id}", use_container_width=True):
                    _kg_ters_isim = {v: k for k, v in _kg_kolon_isim.items()}
                    _kg_eski_toplam = sum(_kg_efektif_tutar(_k) for _k in _kg_mevcut)
                    _kg_yeni_liste = []
                    # GÜVENLİK: Kaydet artık "Seç" işaretine bakmadan SADECE
                    # değerleri günceller — işaretli olsa bile SATIR SİLİNMEZ.
                    # Silme SADECE aşağıdaki ayrı "Sil" butonuyla yapılır. (Bu
                    # ayrım olmayınca, "Düzenle" için işaretlenip sonra
                    # unutulan bir kutu, alakasız bir Kaydet tıklamasında
                    # kaydı sessizce siliyordu — tehlikeliydi, düzeltildi.)
                    for _, _r in _kg_duzenlenen.iterrows():
                        _kg_kayit = {}
                        for _kol, _val in _r.items():
                            if _kol == "Seç":
                                continue
                            _kg_kayit[_kg_ters_isim.get(_kol, _kol)] = _val
                        _kg_hesap_zinciri(_kg_kayit)
                        _kg_kar_zarar_hesapla(_kg_kayit)
                        _kg_yeni_liste.append(_kg_kayit)
                    # GÜVENLİK: silinmiş kayıtları da RENDER anındaki (bayat
                    # olabilecek) kopyadan değil, tam bu an TAZE çekiyoruz —
                    # yoksa arada başka bir yerden eklenmiş bir kayıt burada
                    # sessizce kaybolabilirdi.
                    _kg_taze_sonuc = _kg_kayitlari_yukle_taze(_kg_anahtar)
                    if _kg_taze_sonuc is _OKUMA_BASARISIZ:
                        st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için hiçbir şey kaydedilmedi. Lütfen tekrar dene.")
                    else:
                        _kg_silinmis_taze = [_k for _k in _kg_taze_sonuc if _k.get("silindi")]
                        _kg_kayitlari_kaydet(_kg_anahtar, _kg_yeni_liste + _kg_silinmis_taze)
                        _kg_kayitlari_yukle.clear()
                        _kg_yeni_toplam = sum(_kg_efektif_tutar(_k) for _k in _kg_yeni_liste)
                        _cari_gerceklesen_ciro_ekle(cari_id, _kg_yeni_toplam - _kg_eski_toplam)
                        st.session_state[_kg_tumu_secili_anahtari] = False
                        st.session_state[_kg_ver_anahtari] += 1
                        st.toast("✅ Kargo kayıtları güncellendi", icon="🚚")
                        st.rerun()
            with _kgb2:
                _kg_secili_sayi = int(_kg_duzenlenen["Seç"].sum()) if "Seç" in _kg_duzenlenen.columns else 0
                if st.button(f"🗑️ Seçili {_kg_secili_sayi} Kaydı Sil", key=f"kg_sil_btn_{cari_id}", use_container_width=True, disabled=_kg_secili_sayi == 0):
                    _kg_ters_isim2 = {v: k for k, v in _kg_kolon_isim.items()}
                    _kg_eski_toplam2 = sum(_kg_efektif_tutar(_k) for _k in _kg_mevcut)
                    # GÜVENLİK: YUMUŞAK SİLME — kayıt tamamen kaybolmuyor,
                    # "silindi" işaretlenip listede kalıyor, "🗑️ Silinenler"den
                    # geri alınabiliyor.
                    _kg_kalanlar = []
                    for _, _r in _kg_duzenlenen.iterrows():
                        _kg_kayit2 = {}
                        for _kol, _val in _r.items():
                            if _kol == "Seç":
                                continue
                            _kg_kayit2[_kg_ters_isim2.get(_kol, _kol)] = _val
                        if bool(_r.get("Seç")):
                            _kg_kayit2["silindi"] = True
                            _kg_kayit2["silinme_tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        _kg_kalanlar.append(_kg_kayit2)
                    _kg_taze_sonuc2 = _kg_kayitlari_yukle_taze(_kg_anahtar)
                    if _kg_taze_sonuc2 is _OKUMA_BASARISIZ:
                        st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için hiçbir şey silinmedi. Lütfen tekrar dene.")
                    else:
                        _kg_silinmis_taze2 = [_k for _k in _kg_taze_sonuc2 if _k.get("silindi")]
                        _kg_kayitlari_kaydet(_kg_anahtar, _kg_kalanlar + _kg_silinmis_taze2)
                        _kg_kayitlari_yukle.clear()
                        _kg_yeni_toplam2 = sum(_kg_efektif_tutar(_k) for _k in _kg_kalanlar if not _k.get("silindi"))
                        _cari_gerceklesen_ciro_ekle(cari_id, _kg_yeni_toplam2 - _kg_eski_toplam2)
                        st.session_state[_kg_tumu_secili_anahtari] = False
                        st.session_state[_kg_ver_anahtari] += 1
                        st.toast(f"🗑️ {_kg_secili_sayi} kayıt silindi — 'Kargolar' sayfasındaki '🗑️ Silinenler'den geri alabilirsin", icon="🗑️")
                        st.rerun()
        else:
            st.caption("Bu müşteri için henüz kargo kaydı yok.")
    with _tab_varis:
        st.caption("Karışık/serbest yazabilirsin — aynı Cari Liste'deki il sütunlarıyla birebir aynı şekilde çalışır.")

        def _vd_norm(_s):
            return (str(_s or "").strip().upper().replace("İ", "I").replace("Ş", "S")
                    .replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C"))

        # Global paylaşılan fonksiyon — Cari Liste tablosuyla AYNI önbelleği kullanır.
        _vd_tum_matris = _il_gonderim_matrisi_yukle()
        _vd_matris_firma = _vd_tum_matris.get(str(int(cari_id)), {})
        _vd_dolu = {k: v for k, v in _vd_matris_firma.items() if str(v).strip()}
        if _vd_dolu:
            _vd_dolu_metin = ", ".join(f"{k} ({str(v).replace(chr(10), '/')})" for k, v in _vd_dolu.items())
            st.caption(f"📍 Şu an işaretli iller: {_vd_dolu_metin}")
        else:
            st.caption("📍 Şu an hiç il işaretlenmemiş.")

        _vd_illeri = st.text_input("Varış İlleri", key=f"dlg_varis_illeri_{cari_id}",
                                    placeholder="Örn: istanbul ankara izmir (karışık yazabilirsin)")
        if st.button("💾 İlleri İşaretle", key=f"dlg_varis_illeri_kaydet_{cari_id}", use_container_width=True):
            if _vd_illeri.strip():
                try:
                    import re as _vd_re
                    _vd_tum_matris2 = dict(_il_gonderim_matrisi_yukle())
                    _vd_id_str = str(int(cari_id))
                    _vd_tum_matris2.setdefault(_vd_id_str, {})
                    # Kelime bazlı TAM eşleşme — böylece yazım hatası olan kelimeler
                    # de ayrıca gösterilip fark edilebiliyor (önceki "içeriyor mu"
                    # mantığı yazım hatalarını sessizce yutuyordu).
                    _vd_tokenler = [t for t in _vd_re.split(r"[,;\n]+|\s+", _vd_illeri.strip()) if t]
                    _vd_il_norm_map = {_vd_norm(a): a for a in _IL_SUTUN_LISTESI if a != "Diğer"}
                    _vd_diger_norm_map = {_vd_norm(a): a for a in _IL_DIGER_LISTESI}
                    _vd_eslesen = []
                    _vd_eslesmeyen = []
                    for _tok in _vd_tokenler:
                        _tok_n = _vd_norm(_tok)
                        _bulunan_il = _vd_il_norm_map.get(_tok_n)
                        _bulunan_diger = _vd_diger_norm_map.get(_tok_n)
                        if _bulunan_il:
                            if not str(_vd_tum_matris2[_vd_id_str].get(_bulunan_il, "")).strip():
                                _vd_tum_matris2[_vd_id_str][_bulunan_il] = _bulunan_il.upper()
                            if _bulunan_il not in _vd_eslesen:
                                _vd_eslesen.append(_bulunan_il)
                        elif _bulunan_diger:
                            # Başlığı olmayan il — "Diğer" sütununa ALT ALTA (üst üste
                            # eklenerek, birden fazla girilebilecek şekilde) yazılır.
                            _mevcut_diger = str(_vd_tum_matris2[_vd_id_str].get("Diğer", "") or "").strip()
                            _diger_satirlari = [s.strip() for s in _mevcut_diger.split("\n") if s.strip()]
                            if _bulunan_diger.upper() not in _diger_satirlari:
                                _diger_satirlari.append(_bulunan_diger.upper())
                            _vd_tum_matris2[_vd_id_str]["Diğer"] = "\n".join(_diger_satirlari)
                            if _bulunan_diger not in _vd_eslesen:
                                _vd_eslesen.append(_bulunan_diger)
                        else:
                            _vd_eslesmeyen.append(_tok)
                    _il_gonderim_matrisi_kaydet(_vd_tum_matris2)
                    _il_gonderim_matrisi_yukle.clear()  # Cari Liste tablosu da HEMEN güncel görsün
                    if _vd_eslesen:
                        st.toast(f"✅ İşaretlendi: {', '.join(_vd_eslesen)}", icon="📍")
                    if _vd_eslesmeyen:
                        st.warning(f"⚠️ Tanınmayan kelime(ler) — yazım hatası olabilir: **{', '.join(_vd_eslesmeyen)}**")
                    if not _vd_eslesen and not _vd_eslesmeyen:
                        st.warning("Yazdığın metinde tanınan bir il ismi bulunamadı.")
                    st.rerun()
                except Exception as _vd_hata:
                    st.error(f"Hata: {_vd_hata}")
            else:
                st.warning("Önce bir şey yazın.")

        st.divider()
        _vd_sb = get_sb_client()
        st.caption("Excel'den kopyaladığın gibi SATIR SATIR yapıştır — her satırda **Şehir, Desi Kg, Birim Fiyat** olsun "
                   "(örn. **'AMASYA 227 3.574'**). **TOPLAM = Desi × Birim Fiyat** olarak otomatik hesaplanır, sana bırakmaz. "
                   "100 desi'ye kadar otomatik **KOLİ**, üzeri otomatik **PALET** sayılır.")
        # Sayaçlı (suffix'li) key — "Yenile" butonu, Streamlit'in "widget zaten
        # oluşturulduktan sonra aynı key'e atama yapılamaz" kısıtı yüzünden
        # kutunun KENDİ key'ine doğrudan yazamıyor; bunun yerine sayaç artırılıp
        # bir sonraki çizimde TAMAMEN YENİ (boş) bir kutu oluşturuluyor.
        _fy_kutu_sfx = st.session_state.get(f"_fy_kutu_sfx_{cari_id}", 0)
        _vd_fiyat = st.text_area("Fiyatlandırma", key=f"dlg_fiyat_{cari_id}_{_fy_kutu_sfx}", height=140,
                                  placeholder="AMASYA 227 3.574\nAMASYA 300 3.531\nAMASYA 356 3.487")

        def _fy_norm(_s):
            return (str(_s or "").strip().upper().replace("İ", "I").replace("Ş", "S")
                    .replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C"))

        _fy_sira_liste = [_fy_norm(a) for a in _IL_SUTUN_LISTESI[:-1]] + [_fy_norm(a) for a in _IL_DIGER_LISTESI]

        def _fy_sira_no(_giris):
            # ARTIK TAM EŞLEŞME değil — şehir metni "İSTANBUL ANADOLU" gibi
            # ek kelimeler içerebileceğinden, bilinen il adı bu metnin
            # İÇİNDE mi diye bakılır (sıralama için); GÖSTERİM metni
            # (_giris[0]) hiç değiştirilmez. ÖNEMLİ: karşılaştırma HER İKİ
            # tarafta da _fy_norm ile yapılır — Python'un standart .upper()
            # fonksiyonu Türkçe "i" harfini yanlış büyütüyor (İZMİR yerine
            # İZMIR gibi), bu da "İZMİR"in tanınmayıp gruplanamadan
            # dağılmasına yol açıyordu. _fy_norm bu farkı ortadan kaldırır.
            _sehir_metni_fy_norm = _fy_norm(_giris[0])
            for _i_fy, _il_fy_norm in enumerate(_fy_sira_liste):
                if _il_fy_norm in _sehir_metni_fy_norm:
                    return _i_fy
            return 999

        # ── Hizalı TABLO formatı — en uzun değere göre tüm sütunlar aynı hizada,
        # şehir grupları arasında ayraç çizgisi.
        # Girişler: (sehir, tip, desi, birim_fiyat, toplam)
        def _fy_format_tablo(_girisler):
            if not _girisler:
                return ""
            _sehir_w = max(len("V.İLİ"), max(len(g[0]) for g in _girisler))
            _tur_metinleri = [f"- {g[1]}" for g in _girisler]
            _tur_w = max(len("TÜR"), max(len(t) for t in _tur_metinleri))
            _desi_sayi_w = max(len(str(g[2])) for g in _girisler)
            _desi_metinleri = [f"{str(g[2]).rjust(_desi_sayi_w)} DESİ -KG" for g in _girisler]
            _desi_w = max(len("DESİ-KG"), max(len(t) for t in _desi_metinleri))
            _toplam_metinleri = [f"{g[4]:.2f}" for g in _girisler]
            _toplam_sayi_w = max(len(t) for t in _toplam_metinleri)
            _toplam_metinleri = [f"{t.rjust(_toplam_sayi_w)} TL" for t in _toplam_metinleri]
            _toplam_w = max(len("TOPLAM"), max(len(t) for t in _toplam_metinleri))

            # ── KULLANICI İSTEĞİ (2026-09): "İL TOPLAM CİRO" — YENİ bir sütun.
            # Eski format (V.İLİ/TÜR/DESİ-KG/TOPLAM) HİÇ DEĞİŞTİRİLMEDİ, sadece
            # sona bu sütun EKLENDİ. Her il grubunun SADECE İLK satırında, o
            # ile ait TÜM satırların TOPLAM'larının toplamı gösterilir; aynı
            # ilin diğer satırlarında bu sütun BOŞ kalır (tekrar etmesin diye).
            _il_toplam_ciro_map = {}
            for _g in _girisler:
                _il_anahtar_norm = _fy_norm(_g[0])
                _il_toplam_ciro_map[_il_anahtar_norm] = _il_toplam_ciro_map.get(_il_anahtar_norm, 0.0) + _g[4]
            _il_ciro_metinleri = []
            _gosterilen_iller = set()
            for _g in _girisler:
                _il_anahtar_norm = _fy_norm(_g[0])
                if _il_anahtar_norm not in _gosterilen_iller:
                    _il_ciro_metinleri.append(f"{_il_toplam_ciro_map[_il_anahtar_norm]:.2f} TL")
                    _gosterilen_iller.add(_il_anahtar_norm)
                else:
                    _il_ciro_metinleri.append("")
            _il_ciro_w = max([len("İL TOPLAM CİRO")] + [len(t) for t in _il_ciro_metinleri])

            _baslik = (f"{'V.İLİ'.ljust(_sehir_w)}   {'TÜR'.ljust(_tur_w)}   {'DESİ-KG'.ljust(_desi_w)}   "
                       f"{'TOPLAM'.ljust(_toplam_w)}   {'İL TOPLAM CİRO'.ljust(_il_ciro_w)}")
            _ayrac = "-" * len(_baslik)
            _satirlar = ["FİYAT İNCELE", _ayrac, "", _baslik, _ayrac]
            _onceki_sehir = None
            for _i, _g in enumerate(_girisler):
                if _onceki_sehir is not None and _fy_norm(_g[0]) != _fy_norm(_onceki_sehir):
                    _satirlar.append(_ayrac)
                _satirlar.append(f"{_g[0].ljust(_sehir_w)}   {_tur_metinleri[_i].ljust(_tur_w)}   {_desi_metinleri[_i].ljust(_desi_w)}   "
                                  f"{_toplam_metinleri[_i].ljust(_toplam_w)}   {_il_ciro_metinleri[_i].ljust(_il_ciro_w)}")
                _onceki_sehir = _g[0]
            return "\n".join(_satirlar)

        _fyb1, _fyb2, _fyb3, _fyb4 = st.columns([1.7, 0.8, 2.3, 1.6])
        _fy_ayristir_tiklandi = _fyb1.button("🔍 Ayrıştır ve Hazırla", key=f"dlg_fiyat_ayristir_{cari_id}", use_container_width=True)
        if _fyb2.button("🔄 Yenile", key=f"dlg_fiyat_yenile_{cari_id}", use_container_width=True,
                        help="Kutuyu ve önizlemeyi temizler, sıfırdan başlarsın."):
            st.session_state.pop(f"_fy_hazir_{cari_id}", None)
            st.session_state[f"_fy_kutu_sfx_{cari_id}"] = _fy_kutu_sfx + 1
            st.rerun()
        # KULLANICI İSTEĞİ (2026-09): "İlleri İşaretle" ve "Ayrıştır ve
        # Hazırla" AYNI ANDA çalışsın — aynı yapıştırdığın fiyat metnindeki
        # şehirler hem fiyat tablosuna hem "Varış İlleri" işaretlemesine
        # birden uygulanır, tek tek ayrı ayrı yapmana gerek kalmaz.
        _fy_ikisi_tiklandi = _fyb3.button("🚀 İkisini Birden Çalıştır (İllerle İşaretle + Ayrıştır)",
                                           key=f"dlg_fiyat_ikisi_{cari_id}", use_container_width=True)
        # 🆕 YENİ BUTON (2026-09, KULLANICI İSTEĞİ): "İkisini Birden Çalıştır"
        # ESKİ haline (kaydetmeden, elle inceleme fırsatı bırakarak) geri
        # döndürüldü. Bunun yerine, TAMAMEN AYRI bu YENİ buton — İl İşaretleme
        # + Ayrıştırma + TÜM hesaplamalar (Hedeflenen Ciro, İl Ciroları,
        # Teklif Fiyat) + Koli/Palet tablosunun OTOMATİK KAYDEDİLMESİ dahil
        # HER ŞEYİ tek tıkla yapıp doğrudan Cari Ana Liste'ye işler.
        _fy_hepsi_tiklandi = _fyb4.button("🎯 Hepsini Yerleştir",
                                           key=f"dlg_fiyat_hepsi_{cari_id}", use_container_width=True, type="primary",
                                           help="İlleri işaretler + fiyat tablosunu ayrıştırır + Hedeflenen Ciro/İl Ciroları/Teklif Fiyat'ı hesaplar + HEPSİNİ OTOMATİK KAYDEDER — Cari Liste'ye anında, kayıtlı olarak geçer.")
        if _fy_ayristir_tiklandi or _fy_ikisi_tiklandi or _fy_hepsi_tiklandi:
            if not _vd_fiyat.strip():
                st.warning("Önce bir şey yazın.")
            else:
                import re as _fy_re
                _fy_tum_iller = _IL_SUTUN_LISTESI[:-1] + _IL_DIGER_LISTESI
                _fy_il_norm_map = {_fy_norm(a): a.upper() for a in _fy_tum_iller}
                # KANONİK (doğru harfli, _IL_SUTUN_LISTESI/_IL_DIGER_LISTESI'ndeki
                # ile BİREBİR aynı) eşleme — "İkisini Birden Çalıştır" bunu
                # kullanır. _fy_il_norm_map'in değeri (.upper()) Python'un
                # Türkçe "i" hatası yüzünden "İZMIR" gibi YANLIŞ büyütülmüş
                # olabiliyordu, bu da il listesiyle asla eşleşmeyip
                # "İllerle İşaretle" kısmının hiç çalışmamasına yol açıyordu.
                _fy_il_kanonik_map = {_fy_norm(a): a for a in _fy_tum_iller}
                _fy_iller_bulunan_set = set()  # "İkisini Birden" için: tespit edilen KANONİK il/diğer adları

                def _fy_sayi_parse(_metin):
                    """Türkçe sayı yazımını DOĞRU okur — hiçbir matematik
                    işlemi YAPMAZ, sadece metni doğru sayıya çevirir. '1.478'
                    gibi bir değer, virgül YOKSA ve nokttan sonra TAM 3 rakam
                    varsa BİNLİK AYRACI sayılır (-> 1478) — kullanıcı isteği:
                    '1.600' gibi bir tutar yanlışlıkla '1,60' gibi küçük bir
                    ondalık sayıya dönüştürülmesin. Hem nokta hem virgül
                    varsa (1.234,56) klasik Türkçe biçim: nokta binlik,
                    virgül ondalık. Sadece virgül varsa (162,5) virgül
                    ondalık ayraçtır."""
                    _sfy = str(_metin).strip()
                    if "," in _sfy and "." in _sfy:
                        _sfy = _sfy.replace(".", "").replace(",", ".")
                    elif "," in _sfy:
                        _sfy = _sfy.replace(",", ".")
                    elif "." in _sfy:
                        _nokta_sonrasi = _sfy.split(".")[-1]
                        if len(_nokta_sonrasi) == 3 and _nokta_sonrasi.isdigit():
                            _sfy = _sfy.replace(".", "")
                    try:
                        return float(_sfy)
                    except Exception:
                        return 0.0

                # ── SATIR SATIR ayrıştırma — her satırda: Şehir, Desi (tam sayı),
                # Birim Fiyat (ondalıklı sayı, örn. 3.574 ya da 3,574). Ondalık
                # nokta/virgül içeren sayı HER ZAMAN birim fiyat sayılır, tam sayı
                # ise desi sayılır — Excel'den satır satır kopyala-yapıştır içindir.
                _fy_yeni_girisler = []
                _fy_son_sehir = None  # şehir tekrarlanmadan alt alta yazılmışsa hatırla
                for _satir_ham in _vd_fiyat.strip().split("\n"):
                    _s = _satir_ham.strip()
                    if not _s:
                        continue
                    _s_norm = _fy_norm(_s)
                    if "SEHIRICI" in _s_norm:
                        _s_norm = _s_norm.replace("SEHIRICI", "ISTANBUL")
                    # Şehir bul — TESPİT için bilinen il listesi kullanılır,
                    # ama GÖSTERİM için satırın kendi ham metni (kullanıcının
                    # birebir yazdığı gibi — "ANADOLU"/"VARUPA" gibi ek
                    # kelimeler dahil) korunur. Bilinen ana il ismine asla
                    # İNDİRGENMEZ — kullanıcı ne yazdıysa o gösterilir.
                    _sehir_bulundu = None
                    for _il_norm_fy, _il_ad_fy in _fy_il_norm_map.items():
                        if _il_norm_fy in _s_norm:
                            _sehir_bulundu = _il_ad_fy
                            break
                    if _sehir_bulundu:
                        _fy_kanonik_bulunan = _fy_il_kanonik_map.get(_fy_norm(_sehir_bulundu))
                        if _fy_kanonik_bulunan:
                            _fy_iller_bulunan_set.add(_fy_kanonik_bulunan)
                    if _sehir_bulundu:
                        if "\t" in _s:
                            _sehir_ham_fy = _s.split("\t")[0].strip()
                        else:
                            _m_sehir_ham_fy = _fy_re.match(r"^(\D+)", _s)
                            _sehir_ham_fy = _m_sehir_ham_fy.group(1).strip() if _m_sehir_ham_fy else ""
                        _sehir_ham_fy_norm = _fy_norm(_sehir_ham_fy)
                        # KULLANICI İSTEĞİ: "ANADOLU"/"AVRUPA" (Avrupa yakası)
                        # gibi İstanbul'un yaka bilgisi görülürse, sadece
                        # düz "İSTANBUL" yazılır — yaka bilgisi metne
                        # eklenmez. Diğer tüm iller için ham metin (yazıldığı
                        # gibi) korunmaya devam eder.
                        if _sehir_bulundu == "İSTANBUL" and (
                                "ANADOLU" in _sehir_ham_fy_norm or "AVRUPA" in _sehir_ham_fy_norm or "VARUPA" in _sehir_ham_fy_norm):
                            _fy_son_sehir = "İSTANBUL"
                        else:
                            _fy_son_sehir = _tr_buyuk(_sehir_ham_fy) if _sehir_ham_fy else _sehir_bulundu
                    _sehir = _fy_son_sehir
                    if not _sehir:
                        continue  # bu satırda ve öncesinde hiç şehir yoksa atla (muhtemelen başlık satırı)
                    # Sayıları bul — ARTIK ondalık olup olmamasına bakılmaz:
                    # satırdaki İLK sayı her zaman DESİ, İKİNCİ sayı her zaman
                    # BİRİM FİYAT sayılır (ikisi de tam sayı olabilir, ör.
                    # "ANKARA 37 200", ya da fiyat ondalıklı olabilir, ör.
                    # "AMASYA 227 3.574" — ikisi de aynı sırayla çalışır).
                    # DÜZELTME (2026-09): eski desen "17.500,00" gibi HEM
                    # binlik nokta HEM ondalık virgül içeren sayıları "17.500"
                    # ve "00" diye İKİYE BÖLÜYORDU — bu da "son sayı" olarak
                    # yanlışlıkla sadece "00" (yani 0) alınmasına yol açıyordu.
                    # Yeni desen: önce "binlik gruplu" tam sayıyı (12.345.678,90
                    # gibi çoklu grupları da dahil) TEK PARÇA yakalar, o hiç
                    # yoksa düz rakam dizisini (virgüllü ondalıkla) yakalar.
                    _tum_sayi_m = _fy_re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?", _s)
                    if len(_tum_sayi_m) < 2:
                        continue  # hem desi hem birim fiyat yoksa (örn. sadece şehir adı yazılan satır) atla
                    try:
                        _desi = int(round(_fy_sayi_parse(_tum_sayi_m[0])))
                        _ikinci_sayi = _fy_sayi_parse(_tum_sayi_m[1])
                    except Exception:
                        continue
                    # KULLANICI İSTEĞİ (2026-09): ÇARPMA YAPILMAZ — TOPLAM,
                    # satırdaki İKİNCİ sayının KENDİSİDİR (yazdığın veri
                    # dışında, hesaplanmış/uydurma bir tutar üretilmez).
                    _toplam = round(_ikinci_sayi, 2)
                    # KULLANICI İSTEĞİ (2026-09, KESİN KURAL — doğrulandı):
                    # Hedeflenen Ciro'ya bu satırdan giden katkı, HER ZAMAN
                    # satırdaki SON (en sondaki) sayıdır — 2 sayı varsa 2.si,
                    # 3 sayı varsa 3.sü. ARADAKİ sayı (varsa) ASLA ayrıca
                    # eklenmez — eklenirse toplam yanlış (fazla) çıkıyordu.
                    # Örn. "İSTANBUL 15 300 4.200" → Hedef'e SADECE 4.200 gider,
                    # 300 değil, 300+4.200 hiç değil.
                    _hedef_katkisi = _fy_sayi_parse(_tum_sayi_m[-1])
                    _tip = "KOLİ" if _desi <= 100 else "PALET"
                    _fy_yeni_girisler.append((_sehir, _tip, _desi, _ikinci_sayi, _toplam, _hedef_katkisi))

                if not _fy_yeni_girisler:
                    st.warning("Yazdığın metinde tanınan bir il ismi + desi + birim fiyat bulunamadı.")
                else:
                    # ÖNEMLİ: eski/önceki kayıtlarla BİRLEŞTİRME yapılmıyor — sadece
                    # o an kutuya yazılan veri kullanılır (kullanıcı isteği: sistem
                    # eskileri "hatırlamasın", her seferinde sadece verileni kullansın).
                    _fy_yeni_girisler.sort(key=lambda g: (_fy_sira_no(g), g[2]))
                    # Kaydetmeden önce DÜZ/HİZALI TABLO olarak göster — kullanıcı
                    # üzerinde elle oynayabilsin, hazır metin dayatılmasın.
                    st.session_state[f"_fy_hazir_{cari_id}"] = _fy_format_tablo(_fy_yeni_girisler)

                    # ── HEDEFLENEN CİRO — KULLANICI İSTEĞİ (2026-09): yapıştırılan
                    # İl/Desi/Tutar satırlarındaki TUTAR'ların (DESİ'YE
                    # DOKUNULMADAN, sadece 3. sütun — g[3]) TOPLAMI, bu
                    # müşterinin Cari Liste'deki "Hedeflenen Ciro" (Hedef ₺)
                    # alanına yazılır — böylece o an girilen tüm illerin
                    # toplam potansiyel cirosu tek bakışta görülür.
                    try:
                        _fy_hedef_toplam = round(sum(_g[5] for _g in _fy_yeni_girisler), 2)
                        db_update("cari_kartlar", {"beklenen_ciro": _fy_hedef_toplam}, "id", int(cari_id))
                        try: db_read.clear()
                        except: pass
                        try: get_cari_listesi.clear()
                        except: pass
                        # 🚨 KRİTİK DÜZELTME (2026-09): "İl Ciroları" artık BURADA,
                        # Hedeflenen Ciro ile AYNI ANDA ve AYNI kaynaktan
                        # (_fy_yeni_girisler'in _g[5] alanı) hesaplanıp kaydedilir
                        # — metin ayrıştırmaya (ve 3-sayılı satırlarda TOPLAM ile
                        # hedef_katkisi'nin farklı çıkmasına) bağlı KALMAZ, ikisi
                        # bir daha asla birbirinden farklı olamaz.
                        try:
                            _fy_icy_ozet = _fy_il_ciro_ozet_girislerden(_fy_yeni_girisler)
                            _fy_icy_harita = _cari_ek_bilgi_yukle()
                            _fy_icy_harita.setdefault(str(int(cari_id)), {})["il_ciro_ozet"] = _fy_icy_ozet
                            _cari_ek_bilgi_kaydet(_fy_icy_harita)
                        except Exception:
                            pass
                        st.toast(f"🎯 Hedeflenen Ciro: {_kg_tr_format(_fy_hedef_toplam)} ₺ olarak Cari Liste'ye yazıldı", icon="🎯")
                    except Exception as _fy_hedef_hata:
                        st.error(f"Hedeflenen Ciro yazılırken hata: {_fy_hedef_hata}")

                    # ── "🚀 İkisini Birden Çalıştır" — KULLANICI İSTEĞİ (2026-09):
                    # aynı fiyat metninde tespit edilen şehirler, "İlleri
                    # İşaretle" ile AYNI mantıkla Varış İlleri'ne de işlenir —
                    # ayrıca o kutuya tekrar yazmaya gerek kalmaz.
                    if (_fy_ikisi_tiklandi or _fy_hepsi_tiklandi) and _fy_iller_bulunan_set:
                        try:
                            _fy_tum_matris2 = dict(_il_gonderim_matrisi_yukle())
                            _fy_id_str = str(int(cari_id))
                            _fy_tum_matris2.setdefault(_fy_id_str, {})
                            _fy_il_isaretlenen = []
                            for _fy_il_bulunan in _fy_iller_bulunan_set:
                                if _fy_il_bulunan in _IL_SUTUN_LISTESI and _fy_il_bulunan != "Diğer":
                                    if not str(_fy_tum_matris2[_fy_id_str].get(_fy_il_bulunan, "")).strip():
                                        _fy_tum_matris2[_fy_id_str][_fy_il_bulunan] = _fy_il_bulunan.upper()
                                    _fy_il_isaretlenen.append(_fy_il_bulunan)
                                elif _fy_il_bulunan in _IL_DIGER_LISTESI:
                                    _mevcut_diger_fy = str(_fy_tum_matris2[_fy_id_str].get("Diğer", "") or "").strip()
                                    _diger_satirlari_fy = [s.strip() for s in _mevcut_diger_fy.split("\n") if s.strip()]
                                    if _fy_il_bulunan.upper() not in _diger_satirlari_fy:
                                        _diger_satirlari_fy.append(_fy_il_bulunan.upper())
                                    _fy_tum_matris2[_fy_id_str]["Diğer"] = "\n".join(_diger_satirlari_fy)
                                    _fy_il_isaretlenen.append(_fy_il_bulunan)
                            _il_gonderim_matrisi_kaydet(_fy_tum_matris2)
                            _il_gonderim_matrisi_yukle.clear()
                            if _fy_il_isaretlenen:
                                st.toast(f"✅ Fiyat tablosu hazırlandı + İşaretlendi: {', '.join(_fy_il_isaretlenen)}", icon="🚀")
                        except Exception as _fy_ikisi_hata:
                            st.error(f"İl işaretleme hatası: {_fy_ikisi_hata}")

                        # ── 🆕 YENİ ÖZELLİK (2026-09, KULLANICI İSTEĞİ) — eski
                        # hiçbir şeye dokunmadan EK olarak: bu müşterinin KENDİ
                        # geçmiş fiyat verisinden (yukarıdaki _fy_yeni_girisler),
                        # her il için "TOPLAM ÷ DESİ" oranının EN SIK tekrar eden
                        # (moda) değerini bulup, "İL: ~X TL/desi (N/M kayıttan)"
                        # şeklinde AZ SATIRDA bir özet üretir ve bunu "Teklif
                        # Fiyat" alanına otomatik yazar — o ile ait geçmiş
                        # tekliflerden çıkarılan, güncel bir referans teklif.
                        # 🆕 2. EK (2026-09, KULLANICI İSTEĞİ): bunun ALTINA,
                        # KOLİ (30/50/75/100 desi) ve PALET (330/500/750/1000
                        # desi) baremlerine göre İL BAZLI detaylı kırılım da
                        # eklenir — barem'e tek kayıt düşerse aynen, birden
                        # fazla düşerse ortalaması yazılır.
                        try:
                            _fy_teklif_onerisi = _fy_teklif_onerisi_hesapla(_fy_yeni_girisler)
                            _fy_barem_detay = _fy_desi_baremli_teklif_hesapla(_fy_yeni_girisler)
                            _fy_teklif_parcalari = []
                            if _fy_teklif_onerisi:
                                _fy_teklif_parcalari.append(_fy_teklif_onerisi)
                            if _fy_barem_detay:
                                _fy_teklif_parcalari.append("--- Detaylı Barem Bazlı Teklif ---")
                                for _fy_il_ad in sorted(_fy_barem_detay.keys()):
                                    _fy_teklif_parcalari.append(f"\n{_fy_il_ad}:")
                                    _fy_teklif_parcalari.append(_fy_barem_detay[_fy_il_ad])
                            _fy_teklif_tam = "\n".join(_fy_teklif_parcalari)
                            if _fy_teklif_tam.strip():
                                _fy_tf_harita = _cari_ek_bilgi_yukle()
                                _fy_tf_harita.setdefault(str(int(cari_id)), {})["teklif_fiyat"] = _fy_teklif_tam
                                _cari_ek_bilgi_kaydet(_fy_tf_harita)
                        except Exception:
                            pass

                        # ── 🆕 YENİ BUTON (2026-09, KULLANICI İSTEĞİ): "İkisini
                        # Birden Çalıştır" ESKİ haline (kaydetmeden, elle inceleme
                        # fırsatı bırakarak) geri döndürüldü — bu otomatik kaydetme
                        # SADECE "🎯 Hepsini Yerleştir" butonuna özeldir. Yukarıdaki
                        # hiçbir hesaplamaya (Hedeflenen Ciro, İl Ciroları, Teklif
                        # Fiyat, İl İşaretleme) DOKUNULMADI — onlar zaten doğru,
                        # SADECE "Hepsini Yerleştir" tıklanınca EK olarak
                        # "Koli/Palet" tablosu da otomatik kaydedilir.
                        if _fy_hepsi_tiklandi:
                            try:
                                _fy_oto_metin = st.session_state.get(f"_fy_hazir_{cari_id}", "").strip()
                                if _fy_oto_metin:
                                    _r_kpo_oto = _vd_sb.table("kullanici_tercih").select("deger").eq(
                                        "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
                                    import json as _kpoj_oto
                                    _kp_map_oto = _kpoj_oto.loads(_r_kpo_oto.data[0]["deger"]) if _r_kpo_oto.data else {}
                                    _kp_id_str_oto = str(int(cari_id))
                                    _kp_map_oto[_kp_id_str_oto] = _fy_oto_metin
                                    _kpo_deger_oto = _kpoj_oto.dumps(_kp_map_oto, ensure_ascii=False)
                                    _kpo_guncelle_oto = _vd_sb.table("kullanici_tercih").update({"deger": _kpo_deger_oto}).eq(
                                        "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
                                    if not _kpo_guncelle_oto.data:
                                        _vd_sb.table("kullanici_tercih").insert({
                                            "kullanici": "__liste_ui__", "anahtar": "_koli_palet_manuel",
                                            "deger": _kpo_deger_oto
                                        }).execute()
                                    st.session_state["_koli_palet_manuel"] = _kp_map_oto
                                    st.session_state.pop(f"_fy_hazir_{cari_id}", None)
                                    get_cari_listesi.clear()
                                    st.toast("🎯 Her şey tamamlandı: İller işaretlendi, fiyat tablosu kaydedildi, Cari Liste güncellendi!", icon="✅")
                            except Exception as _fy_oto_hata:
                                st.error(f"Otomatik kaydetme hatası: {_fy_oto_hata}")
                    st.rerun()

        _fy_hazir = st.session_state.get(f"_fy_hazir_{cari_id}")
        # KULLANICI İSTEĞİ (2026-09): sadece YENİ bir "Ayrıştır" sonrası değil,
        # bu sekme her açıldığında, o müşteri için ZATEN KAYITLI bir fiyat
        # tablosu varsa da AYNI (hizalı/monospace) kutuda gösterilsin —
        # görüntülemek için tekrar ayrıştırmaya gerek kalmasın.
        if _fy_hazir is None:
            try:
                _fy_kayitli_harita = st.session_state.get("_koli_palet_manuel", {})
                if not _fy_kayitli_harita:
                    _r_fy_mevcut = _vd_sb.table("kullanici_tercih").select("deger").eq(
                        "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
                    if _r_fy_mevcut.data:
                        import json as _fy_mevcut_j
                        _fy_kayitli_harita = _fy_mevcut_j.loads(_r_fy_mevcut.data[0]["deger"])
                        st.session_state["_koli_palet_manuel"] = _fy_kayitli_harita
                _fy_kayitli_deger = str(_fy_kayitli_harita.get(str(int(cari_id)), "") or "").strip()
                if _fy_kayitli_deger:
                    _fy_hazir = _fy_kayitli_deger
            except Exception:
                pass
        if _fy_hazir is not None:
            st.markdown("**Hazırlanan tablo — istersen elle düzenle, sonra kaydet:**")
            # 🚨 GÜÇLENDİRİLDİ (2026-09): kullanıcı hem bu kutuda hem Cari
            # Liste'nin ana tablosundaki "Koli/Palet" hücresinde bilgilerin
            # dağınık/iç içe göründüğünü bildirdi. Bu kutu için CSS seçicisi
            # daha SAĞLAM hale getirildi (aria-label + genel yedek seçici
            # birlikte). ÖNEMLİ: Cari Liste'nin ANA tablosundaki hücre,
            # Streamlit'in "canvas" tabanlı (HTML/CSS ile stillendirilemeyen)
            # bir bileşenle çiziliyor — o hücrenin yazı tipini CSS ile
            # değiştirmek TEKNİK OLARAK MÜMKÜN DEĞİL. Bu YÜZDEN, kaydedilen
            # tablo HER ZAMAN burada (bu sekmede) da hizalı/monospace olarak
            # görüntülenebilsin diye yukarıdaki "her zaman göster" eklendi.
            st.markdown("""<style>
textarea[aria-label="Koli/Palet önizleme"] {
    font-family: 'Courier New', Courier, monospace !important;
    white-space: pre !important;
    font-size: 13px !important;
}
</style>""", unsafe_allow_html=True)
            _fy_son_metin = st.text_area("Koli/Palet önizleme", value=_fy_hazir, height=200,
                                          key=f"_fy_son_metin_{cari_id}", label_visibility="collapsed")
            if st.button("💾 Kaydet", key=f"dlg_fiyat_kaydet_{cari_id}", type="primary", use_container_width=True):
                try:
                    _r_kpo2 = _vd_sb.table("kullanici_tercih").select("deger").eq(
                        "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
                    import json as _kpoj2
                    _kp_map2 = _kpoj2.loads(_r_kpo2.data[0]["deger"]) if _r_kpo2.data else {}
                    _kp_id_str2 = str(int(cari_id))
                    _kp_map2[_kp_id_str2] = _fy_son_metin.strip()
                    _kpo_deger2 = _kpoj2.dumps(_kp_map2, ensure_ascii=False)
                    _kpo_guncelle2 = _vd_sb.table("kullanici_tercih").update({"deger": _kpo_deger2}).eq(
                        "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
                    if not _kpo_guncelle2.data:
                        _vd_sb.table("kullanici_tercih").insert({"kullanici": "__liste_ui__", "anahtar": "_koli_palet_manuel",
                                                                  "deger": _kpo_deger2}).execute()
                    st.session_state["_koli_palet_manuel"] = _kp_map2
                    # 🚨 KRİTİK DÜZELTME (2026-09): "Ayrıştır ve Hazırla" zaten
                    # "İl Ciroları" ve "Hedeflenen Ciro"yu DOĞRU (yapılandırılmış
                    # veriden, hedef_katkisi ile) hesaplayıp kaydetmişti. Metin
                    # burada HİÇ DEĞİŞTİRİLMEDİYSE (kullanıcı elle düzenlemediyse),
                    # metin-ayrıştırma ile TEKRAR hesaplayıp o DOĞRU değerin
                    # ÜZERİNE YANLIŞ bir şey YAZMAYIZ — sadece kullanıcı GERÇEKTEN
                    # elle değiştirdiyse (metin farklıysa) metinden yeniden
                    # hesaplarız (en iyi çaba, o durumda text-parsing tek seçenek).
                    _icy_metin_degisti = _fy_son_metin.strip() != str(_fy_hazir or "").strip()
                    if _icy_metin_degisti:
                        # KULLANICI İSTEĞİ (2026-09): "İl Ciroları" — bu metinden
                        # otomatik çıkarılıp ayrıca kaydedilir (Cari Liste'de
                        # "Ara İşlem"in sağındaki sütunda gösterilecek).
                        try:
                            _icy_ozet = _fy_il_ciro_ozet_cikar(_fy_son_metin.strip())
                            _icy_harita = _cari_ek_bilgi_yukle()
                            _icy_harita.setdefault(_kp_id_str2, {})["il_ciro_ozet"] = _icy_ozet
                            _cari_ek_bilgi_kaydet(_icy_harita)
                        except Exception:
                            pass
                        try:
                            _icy_hedef = _fy_il_ciro_genel_toplam(_fy_son_metin.strip())
                            if _icy_hedef is not None:
                                db_update("cari_kartlar", {"beklenen_ciro": _icy_hedef}, "id", int(cari_id))
                                get_cari_listesi.clear()
                        except Exception:
                            pass
                    st.session_state.pop(f"_fy_hazir_{cari_id}", None)
                    st.toast("✅ Koli/Palet ve Hedeflenen Ciro güncellendi", icon="📦")
                    st.rerun()
                except Exception as _vd_hata2:
                    st.error(f"Hata: {_vd_hata2}")
    with _tab_duz:
        st.caption(f"**{firma_adi}** — kayıtlı tüm bilgilerle eksiksiz düzenleme ekranı açılır.")
        if st.button("✏️ Cari Kartı Düzenle", key=f"dlg_cari_duzenle_{cari_id}", type="primary", use_container_width=True):
            try:
                _df_duz = get_cari_listesi()
                _satir_duz = _df_duz[_df_duz["id"] == int(cari_id)]
                if _satir_duz.empty:
                    st.error("⚠️ Kayıt bulunamadı.")
                else:
                    kart_row = _satir_duz.iloc[0]
                    d2 = {str(k):(None if str(v) in ["nan","None","NaT"] else v) for k,v in kart_row.items()}
                    for _k in ["firma","yetkili","gsm","sabit","email","adres","il","ilce","durum","temsilci","islem_asamasi","aciklama"]:
                        if _k in d2: d2[_k] = "" if d2[_k] is None else str(d2[_k])
                    if not d2.get("gsm"):
                        d2["gsm"] = str(kart_row.get("telefon") or kart_row.get("tel") or "")
                    if not d2.get("sabit"):
                        d2["sabit"] = str(kart_row.get("sabit_hat") or "")
                    _duzenleme_form_key_temizle(str(cari_id))
                    st.session_state["duzenle_musteri"] = d2
                    st.session_state["aktif_tab"] = "yeni"
                    st.rerun()
            except Exception as _de:
                st.error(f"Hata: {_de}")
    with _tab_sil:
        st.caption(f"**{firma_adi}** kaydını komple sil — tıklayınca anında silinir, onay istenmez.")
        if st.button("🗑️ Cari Komple Sil", key=f"dlg_cari_sil_{cari_id}", type="primary", use_container_width=True):
            try:
                _sb_cs = get_sb_client()
                if _sb_cs:
                    _sb_cs.table("cari_kartlar").update({"silindi": 1}).eq("id", int(cari_id)).execute()
                else:
                    db_update("cari_kartlar", {"silindi": 1}, "id", int(cari_id))
                get_cari_listesi.clear()
                st.cache_data.clear()
                st.session_state.pop("cari_editor", None)
                st.toast(f"🗑️ '{firma_adi}' silindi", icon="🗑️")
                st.rerun()
            except Exception as _cse:
                st.error(f"Silme hatası: {_cse}")

        st.divider()
        # ── 📦 ARŞİVE AL — KULLANICI İSTEĞİ (2026-09): SİLMEZ, veri kalır.
        # Sadece (1) Sonuç'u "Kaybedildi" yapar (üstteki raporlar bunu SAYMAYA
        # devam eder), (2) Cari Ana Liste'de VARSAYILAN olarak GİZLER
        # ("📦 Arşivi Göster" açılmadıkça görünmez).
        st.caption(f"**{firma_adi}**'yi Cari Ana Liste'de gizle ama SİLME — veri kalır, üstteki raporlarda 'Kaybedildi' olarak sayılmaya devam eder.")
        if st.button("📦 Arşive Al (Silme, Sadece Gizle)", key=f"dlg_cari_arsiv_{cari_id}", use_container_width=True):
            try:
                db_update("cari_kartlar", {"sonuc": "Kaybedildi"}, "id", int(cari_id))
                _ars_guncel = _cari_arsiv_yukle()
                _ars_guncel.add(str(int(cari_id)))
                _cari_arsiv_kaydet(_ars_guncel)
                get_cari_listesi.clear()
                st.session_state.pop("cari_editor", None)
                st.toast(f"📦 '{firma_adi}' arşive alındı — Cari Liste'de artık görünmeyecek ama veri kaybolmadı", icon="📦")
                st.rerun()
            except Exception as _arse:
                st.error(f"Arşive alma hatası: {_arse}")

# 🚨 KULLANICI İSTEĞİ (2026-09): "Seç" ile açılan bu pencere, sayfada BAŞKA
# BİR YERE tıklanınca (Streamlit'in dialog'ların VARSAYILAN "dışına
# tıklayınca kapan" davranışı yüzünden) kendiliğinden kapanıyordu — kullanıcı
# bunun yerine SADECE "❌ Bu Pencereyi Kapat" ile kapanmasını istiyor. Bunun
# için Streamlit'in "dismissible=False" özelliği kullanılıyor. GÜVENLİK:
# bu özellik ESKİ Streamlit sürümlerinde YOK — önce desteklenip
# desteklenmediği kontrol ediliyor, desteklenmiyorsa uygulama ÇÖKMEDEN eski
# (varsayılan, dışına tıklayınca kapanan) davranışa sessizce geri dönülür.
try:
    import inspect as _nd_inspect
    if "dismissible" in _nd_inspect.signature(st.dialog).parameters:
        not_dialog = st.dialog("📋 Notlar & Randevu", width="large", dismissible=False)(not_dialog)
    else:
        not_dialog = st.dialog("📋 Notlar & Randevu", width="large")(not_dialog)
except Exception:
    not_dialog = st.dialog("📋 Notlar & Randevu", width="large")(not_dialog)

@st.dialog("✏️ Kargo Kaydını Düzenle", width="large")
def kargo_kaydi_duzenle_dialog(cari_id, satir_no):
    """Kargolar — Tüm Müşteriler sayfasından TEK bir kayıt seçip bu formda
    düzenlemek için. Kargo Girişi formuyla birebir aynı alanlar/hesaplamalar,
    ama YENİ satır eklemek yerine var olan kaydın (satir_no) üzerine yazar."""
    _kgd_anahtar = f"_kargo_kayitlari_{int(cari_id)}"
    _kgd_liste = list(_kg_kayitlari_yukle(_kgd_anahtar))
    if satir_no >= len(_kgd_liste):
        st.error("Bu kayıt artık bulunamadı (başka bir yerden silinmiş olabilir).")
        if st.button("Kapat", key=f"kgduz_bulunamadi_kapat_{cari_id}_{satir_no}"):
            st.rerun()
        return
    _kgd_kayit = _kgd_liste[satir_no]

    try:
        _kgd_cl = get_cari_listesi()
        _kgd_satir_cl = _kgd_cl[_kgd_cl["id"] == int(cari_id)]
        _kgd_firma_adi = _kgd_satir_cl["firma"].iloc[0] if not _kgd_satir_cl.empty else ""
    except Exception:
        _kgd_firma_adi = ""

    st.caption(f"**{_kgd_firma_adi}** — kayıtlı kargo kaydını düzenliyorsun. Kaydedince YENİ satır eklenmez, bu kaydın üzerine yazılır.")
    if st.button("❌ Vazgeç (kaydetmeden kapat)", key=f"kgduz_vazgec_{cari_id}_{satir_no}"):
        st.rerun()

    # ── MÜŞTERİ SEÇİCİ — bu kayıt yanlışlıkla başka bir müşterinin altına
    # girmiş olabilir; buradan başka bir müşteriye TAŞINABİLİR. Kaydedince
    # eski müşteriden silinip yeni müşteriye eklenir, gerçekleşen ciro da
    # her ikisinde buna göre güncellenir.
    try:
        _kgd_tum_cari = get_cari_listesi()
        _kgd_musteri_id_harita = dict(zip(_kgd_tum_cari["firma"].astype(str), _kgd_tum_cari["id"]))
        _kgd_musteri_secim_opts = sorted(_kgd_musteri_id_harita.keys())
    except Exception:
        _kgd_musteri_id_harita = {}
        _kgd_musteri_secim_opts = []
    _kgd_musteri_varsayilan_idx = _kgd_musteri_secim_opts.index(_kgd_firma_adi) if _kgd_firma_adi in _kgd_musteri_secim_opts else 0
    _kgd_musteri_secili_firma = st.selectbox("Müşteri", _kgd_musteri_secim_opts, index=_kgd_musteri_varsayilan_idx, key=f"kgduz_{cari_id}_{satir_no}_musteri_sec",
                                              help="Bu kayıt yanlış müşterideyse, buradan doğru müşteriyi seçip kaydedebilirsin — kayıt o müşteriye taşınır.")
    _kgd_hedef_cari_id = int(_kgd_musteri_id_harita.get(_kgd_musteri_secili_firma, cari_id))
    if _kgd_hedef_cari_id != int(cari_id):
        st.info(f"💡 Kaydedince bu kayıt **{_kgd_firma_adi}** → **{_kgd_musteri_secili_firma}** müşterisine taşınacak.")

    try:
        _kgd_musteri_liste = sorted(get_cari_listesi()["firma"].dropna().astype(str).unique().tolist())
    except Exception:
        _kgd_musteri_liste = []
    _kgd_musteri_opts = ["-- Seç veya elle yaz --"] + _kgd_musteri_liste
    _kgd_il_opts = ["-- İl seçilir --"] + [_tr_buyuk(a) for a in (_IL_SUTUN_LISTESI[:-1] + _IL_DIGER_LISTESI)]
    try:
        _kgd_tasiyici_opts = ["-- Seç veya elle yaz --"] + sorted(set(
            _t.get("firma_adi", "") for _t in _tedarikci_yukle_goster() if not _t.get("silindi") and _gecerli_metin(_t.get("firma_adi", ""))))
    except Exception:
        _kgd_tasiyici_opts = ["-- Seç veya elle yaz --"]
    _KGD_YEREL_ILLER = [_tr_buyuk(a) for a in ["İzmir", "Bursa", "Kocaeli", "Tekirdağ", "İstanbul", "Manisa"]]
    _kgd_manuel_alici_hafiza = _kg_manuel_alici_yukle()
    _kgd_musteri_opts_buyuk = set(_tr_buyuk(x) for x in _kgd_musteri_liste)
    _kgd_hafizadan_ek = sorted([f for f in _kgd_manuel_alici_hafiza.keys() if f not in _kgd_musteri_opts_buyuk])
    _kgd_alici_opts = ["-- Seç veya elle yaz --"] + sorted(set(_kgd_musteri_liste) | set(_kgd_hafizadan_ek))

    def _kgd_idx(_opts, _deger):
        _dbuyuk = _tr_buyuk(str(_deger or "").strip())
        for _i, _o in enumerate(_opts):
            if _tr_buyuk(str(_o).strip()) == _dbuyuk:
                return _i
        return 0

    def _kgd_float(_deger):
        try:
            return float(_deger or 0)
        except Exception:
            return 0.0

    def _kgd_elle_varsayilan(_opts, _deger):
        """Kayıttaki değer açılır listede YOKSA (silinmiş müşteri, tek seferlik
        alıcı, eski taşıyıcı adı vb.) boş görünüp veri kaybolmasın diye, o
        değeri 'Listede yoksa elle yaz' kutusuna otomatik koyar."""
        _dtemiz = str(_deger or "").strip()
        if not _dtemiz:
            return ""
        return _dtemiz if _kgd_idx(_opts, _dtemiz) == 0 else ""

    try:
        _kgd_tarih_val = datetime.strptime(str(_kgd_kayit.get("tarih", "")).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        _kgd_tarih_val = datetime.now().date()

    _kp = f"kgduz_{cari_id}_{satir_no}"

    _kgc1, _kgc2, _kgc3 = st.columns(3)
    _kg_tarih = _kgc1.date_input("Tarih *", value=_kgd_tarih_val, key=f"{_kp}_tarih")
    _kg_takip = _kgc2.text_input("Takip No", value=_kg_referans_no_temizle(_kgd_kayit.get("takip_no", "")), key=f"{_kp}_takip")
    _kg_fatura_no = _kgc3.text_input("Fatura No", value=_kg_referans_no_temizle(_kgd_kayit.get("fatura_no", "")), key=f"{_kp}_fatura_no")

    _kg_gonderen_sec = _kgc1.selectbox("Gönderen Firma", _kgd_musteri_opts, index=_kgd_idx(_kgd_musteri_opts, _kgd_kayit.get("gonderen_firma", "")), key=f"{_kp}_gonderen_sec")
    _kg_gonderen_elle = _kgc1.text_area("(Listede yoksa elle yaz)", value=_kgd_elle_varsayilan(_kgd_musteri_opts, _kgd_kayit.get("gonderen_firma", "")), key=f"{_kp}_gonderen_elle", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz", height=68)
    _kg_alici_sec = _kgc2.selectbox("Alıcı Firma", _kgd_alici_opts, index=_kgd_idx(_kgd_alici_opts, _kgd_kayit.get("alici_firma", "")), key=f"{_kp}_alici_sec")
    _kg_alici_elle = _kgc2.text_area("(Listede yoksa elle yaz)", value=_kgd_elle_varsayilan(_kgd_alici_opts, _kgd_kayit.get("alici_firma", "")), key=f"{_kp}_alici_elle", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz", height=68)
    _kg_fatura_sec = _kgc3.selectbox("Fatura Ödeyen *", _kgd_musteri_opts, index=_kgd_idx(_kgd_musteri_opts, _kgd_kayit.get("fatura_firma", "")), key=f"{_kp}_fatura_sec")
    _kg_fatura_elle = _kgc3.text_area("(Listede yoksa elle yaz)", value=_kgd_elle_varsayilan(_kgd_musteri_opts, _kgd_kayit.get("fatura_firma", "")), key=f"{_kp}_fatura_elle", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz", height=68)

    _kg_gonderen_il = _kgc1.selectbox("Gönderen İl", _kgd_il_opts, index=_kgd_idx(_kgd_il_opts, _kgd_kayit.get("gonderen_il", "")), key=f"{_kp}_gonderen_il")
    _kg_alici_il = _kgc2.selectbox("Alıcı İl", _kgd_il_opts, index=_kgd_idx(_kgd_il_opts, _kgd_kayit.get("alici_il", "")), key=f"{_kp}_alici_il")
    _kgd_fos_opts = ["", "Faturasız", "PÖ", "ÜA", "CH"]
    _kgd_fos_mevcut = str(_kgd_kayit.get("fatura_odeme_sekli", "") or "")
    if _kgd_fos_mevcut and _kgd_fos_mevcut not in _kgd_fos_opts:
        _kgd_fos_opts = _kgd_fos_opts + [_kgd_fos_mevcut]
    _kg_fatura_odeme_sekli = _kgc3.selectbox("Ödeme Türü (Fatura)", _kgd_fos_opts,
                                              index=(_kgd_fos_opts.index(_kgd_fos_mevcut) if _kgd_fos_mevcut in _kgd_fos_opts else 0),
                                              key=f"{_kp}_fatura_odeme_sekli")

    _kg_tur = _kgc1.text_input("Tür", value=str(_kgd_kayit.get("tur", "")), key=f"{_kp}_tur", placeholder="Koli / Palet / ...")
    _kg_desi = _kg_tr_parse(_kgc2.text_input("Desi", value=_kg_tr_format(_kgd_kayit.get("desi")), key=f"{_kp}_desi", help="Virgülle ondalık yazabilirsin (ör. 12,5)"))
    _kg_kilo = _kg_tr_parse(_kgc3.text_input("Kilo", value=_kg_tr_format(_kgd_kayit.get("kilo")), key=f"{_kp}_kilo", help="Virgülle ondalık yazabilirsin (ör. 12,5)"))

    _kg_adet = _kgc1.number_input("Adet", min_value=0, step=1, value=int(_kgd_float(_kgd_kayit.get("adet"))), key=f"{_kp}_adet")
    _kg_tutar = _kg_tr_parse(_kgc2.text_input("B.Tutar", value=_kg_tr_format(_kgd_kayit.get("tutar")), key=f"{_kp}_tutar",
                              help="Virgülle ondalık yaz (ör. 90,72). Yekün ve oradan Sigorta, Ara Toplam, Kdv, Son Toplam otomatik hesaplanır."))
    _kg_onizleme = _kg_hesap_zinciri({"tutar": _kg_tutar, "adet": _kg_adet})
    _kgc3.text_input("Yekün (₺)", value=_kg_tr_format(_kg_onizleme['yekun']), key=f"{_kp}_oniz_yekun_{_kg_tutar}_{_kg_adet}", help="B.Tutar × Adet")
    _kgc1.text_input("Sigorta %6 (₺)", value=_kg_tr_format(_kg_onizleme['sigorta']), key=f"{_kp}_oniz_sigorta_{_kg_tutar}_{_kg_adet}")
    _kgc2.text_input("Ara Toplam (₺)", value=_kg_tr_format(_kg_onizleme['ara_toplam']), key=f"{_kp}_oniz_ara_{_kg_tutar}_{_kg_adet}")
    _kgc3.text_input("Kdv %20 (₺)", value=_kg_tr_format(_kg_onizleme['kdv']), key=f"{_kp}_oniz_kdv_{_kg_tutar}_{_kg_adet}")
    _kgc1.text_input("Son Toplam (₺)", value=_kg_tr_format(_kg_onizleme['toplam_fatura']), key=f"{_kp}_oniz_son_{_kg_tutar}_{_kg_adet}")

    _kg_yetkili = _kgc2.text_input("Yetkili", value=str(_kgd_kayit.get("yetkili", "")), key=f"{_kp}_yetkili", placeholder="İlgili kişiyi elle yaz")
    _kgd_tahsilat_opts = ["", "Evet", "Hayır", "Kısmi"]
    _kgd_tahsilat_mevcut = str(_kgd_kayit.get("tahsilat_durumu", "") or "")
    if _kgd_tahsilat_mevcut and _kgd_tahsilat_mevcut not in _kgd_tahsilat_opts:
        # Eski bir kayıttan kalma (ör. "Bekliyor") olabilir — kaybolmasın diye
        # listeye geçici olarak ekleniyor, kaydedince yine seçtiğin ne olursa o kalır.
        _kgd_tahsilat_opts = _kgd_tahsilat_opts + [_kgd_tahsilat_mevcut]
    _kg_tahsilat = _kgc3.selectbox("Tahsilat", _kgd_tahsilat_opts,
                                    index=(_kgd_tahsilat_opts.index(_kgd_tahsilat_mevcut) if _kgd_tahsilat_mevcut in _kgd_tahsilat_opts else 0),
                                    key=f"{_kp}_tahsilat")
    _kg_not = _kgc1.text_input("Not", value=str(_kgd_kayit.get("not", "")), key=f"{_kp}_not", placeholder="Serbest not (opsiyonel)")
    _kg_odeme_tur = _kgd_kayit.get("odeme_tur", "")

    _kg_dis_bolge_mi = (_kg_alici_il != "-- İl seçilir --" and _kg_alici_il not in _KGD_YEREL_ILLER)
    _kg_dn_firma, _kg_dn_fatura, _kg_dn_detay, _kg_dn_tutar, _kg_musteri_tutar, _kg_dn_odeme = "", "", "", 0.0, 0.0, ""
    if _kg_dis_bolge_mi:
        st.markdown(f"**🚚 Dış Nakliye** — *{_kg_alici_il} dış bölge sayıldığı için gerekli*")
        with st.container(border=True):
            _kgd1, _kgd2, _kgd3 = st.columns(3)
            _kg_dn_firma_sec = _kgd1.selectbox("Dış Nakliye Firma", _kgd_tasiyici_opts, index=_kgd_idx(_kgd_tasiyici_opts, _kgd_kayit.get("dis_nakliye_firma", "")), key=f"{_kp}_dn_firma_sec")
            _kg_dn_firma_elle = _kgd1.text_input("(Listede yoksa elle yaz)", value=_kgd_elle_varsayilan(_kgd_tasiyici_opts, _kgd_kayit.get("dis_nakliye_firma", "")), key=f"{_kp}_dn_firma_elle", label_visibility="collapsed", placeholder="Listede yoksa buraya elle yaz")
            _kg_dn_fatura = _kgd2.text_input("Dış Nakliye Fatura", value=str(_kgd_kayit.get("dis_nakliye_fatura", "")), key=f"{_kp}_dn_fatura")
            _kg_dn_detay = _kgd3.text_input("Dış Nakliye Detay", value=str(_kgd_kayit.get("dis_nakliye_detay", "")), key=f"{_kp}_dn_detay", placeholder="Örn: 2 Palet")
            _kg_dn_tutar = _kg_tr_parse(_kgd1.text_input("Dış Nakliye Tutar", value=_kg_tr_format(_kgd_kayit.get("dis_nakliye_tutar")), key=f"{_kp}_dn_tutar", help="Virgülle ondalık yazabilirsin (ör. 3.500,50)"))
            _kg_musteri_tutar = _kg_tr_parse(_kgd2.text_input("Müşteri Tutar", value=_kg_tr_format(_kgd_kayit.get("musteri_tutar")), key=f"{_kp}_musteri_tutar", help="Virgülle ondalık yazabilirsin (ör. 3.500,50)"))
            _kgd_dn_odeme_opts = ["", "Evet", "Hayır", "Kısmi"]
            _kgd_dn_odeme_mevcut = str(_kgd_kayit.get("dis_nakliye_odeme_durumu", "") or "")
            if _kgd_dn_odeme_mevcut and _kgd_dn_odeme_mevcut not in _kgd_dn_odeme_opts:
                _kgd_dn_odeme_opts = _kgd_dn_odeme_opts + [_kgd_dn_odeme_mevcut]
            _kg_dn_odeme = _kgd3.selectbox("İşlendi mi?", _kgd_dn_odeme_opts,
                                            index=(_kgd_dn_odeme_opts.index(_kgd_dn_odeme_mevcut) if _kgd_dn_odeme_mevcut in _kgd_dn_odeme_opts else 0),
                                            key=f"{_kp}_dn_odeme")
            st.caption("🧮 Kar/Zarar, kaydedince otomatik hesaplanır: Müşteri Tutar − Dış Nakliye Tutar (pozitifse Kar, negatifse Zarar)")
            _kg_dn_firma = _kg_dn_firma_elle.strip() or (_kg_dn_firma_sec if _kg_dn_firma_sec != "-- Seç veya elle yaz --" else "")
    else:
        st.caption("💡 Alıcı İl olarak yerel bir il (İstanbul, Bursa, İzmir, Kocaeli, Tekirdağ, Manisa) seçilmedi/seçilirse Dış Nakliye alanları burada görünmez.")

    st.divider()
    if st.button("💾 Değişiklikleri Kaydet", type="primary", key=f"{_kp}_kaydet_btn", use_container_width=True):
        _kg_gonderen = _kg_gonderen_elle.strip() or (_kg_gonderen_sec if _kg_gonderen_sec != "-- Seç veya elle yaz --" else "")
        _kg_alici = _kg_alici_elle.strip() or (_kg_alici_sec if _kg_alici_sec != "-- Seç veya elle yaz --" else "")
        _kg_fatura_odeyen = _kg_fatura_elle.strip() or (_kg_fatura_sec if _kg_fatura_sec != "-- Seç veya elle yaz --" else "")
        _kgd_eksikler = []
        if not _kg_tarih:
            _kgd_eksikler.append("Tarih")
        if not _kg_fatura_odeyen:
            _kgd_eksikler.append("Fatura Ödeyen")
        if _kgd_eksikler:
            st.error(f"⚠️ Zorunlu alan(lar) eksik: {', '.join(_kgd_eksikler)}")
        else:
            _kg_gonderen_il_deger = _kg_gonderen_il if _kg_gonderen_il != "-- İl seçilir --" else ""
            _kg_alici_il_deger = _kg_alici_il if _kg_alici_il != "-- İl seçilir --" else ""
            _kgd_guncel_kayit = {
                "tarih": str(_kg_tarih), "takip_no": _tr_buyuk(_kg_takip), "fatura_no": _tr_buyuk(_kg_fatura_no), "gonderen_firma": _tr_buyuk(_kg_gonderen),
                "alici_firma": _tr_buyuk(_kg_alici), "fatura_firma": _tr_buyuk(_kg_fatura_odeyen),
                "gonderen_il": _tr_buyuk(_kg_gonderen_il_deger), "alici_il": _tr_buyuk(_kg_alici_il_deger),
                "fatura_odeme_sekli": _kg_fatura_odeme_sekli, "yetkili": _tr_buyuk(_kg_yetkili), "not": _kg_not,
                "adet": _kg_adet, "tur": _tr_buyuk(_kg_tur), "tutar": _kg_tutar,
                "desi": _kg_desi, "kilo": _kg_kilo,
                "odeme_tur": _kg_odeme_tur, "tahsilat_durumu": _kg_tahsilat,
                "dis_nakliye_firma": _tr_buyuk(_kg_dn_firma), "dis_nakliye_fatura": _tr_buyuk(_kg_dn_fatura),
                "dis_nakliye_detay": _tr_buyuk(_kg_dn_detay), "dis_nakliye_tutar": _kg_dn_tutar,
                "musteri_tutar": _kg_musteri_tutar, "dis_nakliye_odeme_durumu": _kg_dn_odeme,
            }
            _kg_hesap_zinciri(_kgd_guncel_kayit)
            _kg_kar_zarar_hesapla(_kgd_guncel_kayit)
            _kgd_yeni_tutar = _kg_efektif_tutar(_kgd_guncel_kayit)

            if _kgd_hedef_cari_id == int(cari_id):
                # ── AYNI MÜŞTERİ — yerinde güncelle (satir_no'nun üzerine yaz).
                _kgd_taze_sonuc = _kg_kayitlari_yukle_taze(_kgd_anahtar)
                if _kgd_taze_sonuc is _OKUMA_BASARISIZ:
                    st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için hiçbir şey kaydedilmedi. Lütfen tekrar dene.")
                else:
                    _kgd_liste_fresh = list(_kgd_taze_sonuc)
                    if satir_no >= len(_kgd_liste_fresh):
                        st.error("Bu kayıt kaydedilirken bulunamadı, başka bir yerden silinmiş olabilir.")
                    else:
                        _kgd_eski_tutar = _kg_efektif_tutar(_kgd_liste_fresh[satir_no])
                        _kgd_liste_fresh[satir_no] = _kgd_guncel_kayit
                        _kg_kayitlari_kaydet(_kgd_anahtar, _kgd_liste_fresh)
                    _kg_kayitlari_yukle.clear()
                    # NOT: _kargolar_tumunu_yukle Kargolar sayfasının kendi İÇİNDE
                    # tanımlı yerel bir fonksiyon, buradan (ayrı bir dialog
                    # fonksiyonundan) doğrudan erişilemiyor — o yüzden Kargolar
                    # sayfasının önbelleğini de kapsayacak şekilde genel önbellek
                    # temizleniyor (not_dialog'daki "Cari Sil" ile aynı yöntem).
                    st.cache_data.clear()
                    _cari_gerceklesen_ciro_ekle(cari_id, _kgd_yeni_tutar - _kgd_eski_tutar)
                    if _kg_alici and _kg_alici_il_deger:
                        _kgd_hafiza_guncel = dict(_kgd_manuel_alici_hafiza)
                        _kgd_hafiza_guncel[_tr_buyuk(_kg_alici)] = _tr_buyuk(_kg_alici_il_deger)
                        _kg_manuel_alici_kaydet(_kgd_hafiza_guncel)
                        _kg_manuel_alici_yukle.clear()
                    st.toast("✅ Kargo kaydı güncellendi", icon="🚚")
                    st.rerun()
            else:
                # ── FARKLI MÜŞTERİ SEÇİLDİ — kayıt TAŞINIYOR: eski müşteriden
                # silinip yeni müşteriye (güncel haliyle) ekleniyor. Gerçekleşen
                # ciro her iki müşteride de buna göre düzeltiliyor.
                _kgd_eski_sonuc = _kg_kayitlari_yukle_taze(_kgd_anahtar)
                if _kgd_eski_sonuc is _OKUMA_BASARISIZ:
                    st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için taşıma yapılmadı. Lütfen tekrar dene.")
                else:
                    _kgd_eski_liste = list(_kgd_eski_sonuc)
                    if satir_no >= len(_kgd_eski_liste):
                        st.error("Bu kayıt taşınırken bulunamadı, başka bir yerden silinmiş olabilir.")
                    else:
                        _kgd_hedef_anahtar = f"_kargo_kayitlari_{_kgd_hedef_cari_id}"
                        _kgd_hedef_sonuc = _kg_kayitlari_yukle_taze(_kgd_hedef_anahtar)
                        if _kgd_hedef_sonuc is _OKUMA_BASARISIZ:
                            st.error("⚠️ Hedef müşterinin verisine şu an ulaşılamadı — güvenlik için taşıma yapılmadı. Lütfen tekrar dene.")
                        else:
                            _kgd_eski_tutar = _kg_efektif_tutar(_kgd_eski_liste[satir_no])
                            _kgd_eski_liste_temiz = [_k for _i2, _k in enumerate(_kgd_eski_liste) if _i2 != satir_no]
                            _kg_kayitlari_kaydet(_kgd_anahtar, _kgd_eski_liste_temiz)
                            _kgd_hedef_liste = list(_kgd_hedef_sonuc)
                            _kgd_hedef_liste.append(_kgd_guncel_kayit)
                            _kg_kayitlari_kaydet(_kgd_hedef_anahtar, _kgd_hedef_liste)
                            _kg_kayitlari_yukle.clear()
                            st.cache_data.clear()
                            _cari_gerceklesen_ciro_ekle(cari_id, -_kgd_eski_tutar)
                            _cari_gerceklesen_ciro_ekle(_kgd_hedef_cari_id, _kgd_yeni_tutar)
                            if _kg_alici and _kg_alici_il_deger:
                                _kgd_hafiza_guncel = dict(_kgd_manuel_alici_hafiza)
                                _kgd_hafiza_guncel[_tr_buyuk(_kg_alici)] = _tr_buyuk(_kg_alici_il_deger)
                                _kg_manuel_alici_kaydet(_kgd_hafiza_guncel)
                                _kg_manuel_alici_yukle.clear()
                            st.toast(f"✅ Kayıt '{_kgd_musteri_secili_firma}' müşterisine taşındı ve güncellendi", icon="🚚")
                            st.rerun()


def not_paneli(cari_id, firma_adi="", key_prefix="np"):
    """Her yerde kullanılan ortak not paneli — Model 5: ultra minimal"""
    _sb = get_sb_client()
    _notlar = _notlar_yukle(cari_id)
    _notlar = [n for n in _notlar if not str(n.get("aciklama","") or "").startswith("##YETKILI##")]

    try:
        _notlar = sorted(_notlar, key=lambda x: str(x.get("created_at","") or x.get("tarih","") or x.get("id",0)), reverse=True)
    except: pass

    st.caption(f"{len(_notlar)} not")

    # Model 5 — ultra minimal: tarih | metin | kim | 🗑
    _css5 = """<style>
.np5-satir{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:0.5px solid #e2e8f0;}
.np5-satir:last-child{border-bottom:none;}
.np5-tarih{font-size:11px;color:#64748b;min-width:68px;white-space:nowrap;}
.np5-txt{font-size:13px;color:#0f172a;flex:1;line-height:1.5;}
.np5-kim{font-size:11px;color:#94a3b8;white-space:nowrap;}
</style>"""
    st.markdown(_css5, unsafe_allow_html=True)

    for _nn in _notlar:
        _nid = _nn.get("id","")
        _txt = str(_nn.get("aciklama","") or _nn.get("metin","") or _nn.get("not","") or _nn.get("icerik","") or "")
        _kim = str(_nn.get("olusturan","") or _nn.get("kullanici","") or "")
        _tar = fmt_tarih(str(_nn.get("created_at","") or _nn.get("tarih","") or ""))
        if not _txt: continue

        _col1, _col2, _col3, _col4 = st.columns([0.9, 5, 1, 0.5])
        _col1.markdown(f"<div class='np5-tarih'>{_tar[:8]}</div>", unsafe_allow_html=True)
        _col2.markdown(f"<div class='np5-txt'>{_txt.replace('<','&lt;')}</div>", unsafe_allow_html=True)
        _col3.markdown(f"<div class='np5-kim'>{_kim}</div>", unsafe_allow_html=True)
        if _col4.button("🗑", key=f"{key_prefix}_sil_{_nid}_{cari_id}"):
            try:
                if _sb: _sb.table("cari_aciklamalar").delete().eq("id", int(_nid)).execute()
                try: _notlar_yukle.clear()
                except: pass
                st.rerun()
            except Exception as _se:
                st.error(f"Sil hatası: {_se}")

    # Yeni not — tek satır
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    _nc1, _nc2 = st.columns([5, 1])
    _yeni = _nc1.text_input("", key=f"{key_prefix}_yeni_{cari_id}", placeholder="Not yaz...", label_visibility="collapsed")
    if _nc2.button("Kaydet", key=f"{key_prefix}_kaydet_{cari_id}", type="primary", use_container_width=True):
        if _yeni and _yeni.strip():
            try:
                _yazar = st.session_state.get("kullanici","")
                _veri = {"cari_id": int(cari_id), "aciklama": _yeni.strip(), "olusturan": _yazar}
                if _sb: _sb.table("cari_aciklamalar").insert(_veri).execute()
                try: _notlar_yukle.clear()
                except: pass
                st.success("✅ Eklendi!")
                st.rerun()
            except Exception as _ne:
                st.error(f"Hata: {_ne}")
        else:
            st.warning("Not boş!")



_TAB_LISTESI_DEFAULT = ["yeni", "hizli_firma", "liste", "excel", "kullanici", "mukerrer", "kargolar", "tedarikci"]
_TAB_ETIKETLER = {
    "yeni": "➕ Yeni Kart Ekle",
    "hizli_firma": "⚡ Hızlı Firma Ekle",
    "liste": "📋 Cari Liste / Düzenle",
    "excel": "📥 Excel Aktar",
    "dis_nakliye": "🚚 Dış Nakliye",
    "dis_nakliye_toplu": "🚚 Dış Nakliyeler Listesi",
    
    "kullanici": "👥 Kullanıcı Yönetimi",
    "mesajlar": "💬 Mesajlar",
    "kargolar": "🚚 Kargolar",
    "mukerrer": "🔍 Mükerrer Bul",
    "tedarikci": "🚛 Tedarikçi",
    
}

def get_menu_tercihi(kullanici):
    def _temizle(liste):
        goruldu = []
        for t in liste:
            if t not in goruldu:
                goruldu.append(t)
        return goruldu

    try:
        sb_m = get_sb_client()
        if sb_m:
            res = sb_m.table("kullanici_tercih").select("deger").eq("kullanici", kullanici).eq("anahtar","menu_sirasi").execute()
            if res.data:
                kayitli = json.loads(res.data[0]["deger"])
                tam_liste = _TAB_LISTESI_DEFAULT.copy()
                if st.session_state.get("rol") == "admin":
                    tam_liste += ["kullanici"]
                tam_liste = _temizle(tam_liste)
                # Eksik olanları tam_liste'deki sıraya göre doğru pozisyona ekle
                for i, t in enumerate(tam_liste):
                    if t not in kayitli:
                        # Önceki elemanın pozisyonundan sonraya ekle
                        onceki = next((x for x in reversed(tam_liste[:i]) if x in kayitli), None)
                        if onceki:
                            pos = kayitli.index(onceki) + 1
                        else:
                            pos = 0
                        kayitli.insert(pos, t)
                kayitli = [t for t in kayitli if t in tam_liste]
                return _temizle(kayitli)
        else:
            conn = get_conn()
            conn.execute("CREATE TABLE IF NOT EXISTS kullanici_tercih (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, anahtar TEXT, deger TEXT, UNIQUE(kullanici, anahtar))")
            conn.commit()
            row = conn.execute("SELECT deger FROM kullanici_tercih WHERE kullanici=? AND anahtar='menu_sirasi'", (kullanici,)).fetchone()
            conn.close()
            if row:
                kayitli = json.loads(row[0])
                tam_liste = _TAB_LISTESI_DEFAULT.copy()
                if st.session_state.get("rol") == "admin":
                    tam_liste += ["kullanici"]
                tam_liste = _temizle(tam_liste)
                for i, t in enumerate(tam_liste):
                    if t not in kayitli:
                        onceki = next((x for x in reversed(tam_liste[:i]) if x in kayitli), None)
                        if onceki:
                            pos = kayitli.index(onceki) + 1
                        else:
                            pos = 0
                        kayitli.insert(pos, t)
                kayitli = [t for t in kayitli if t in tam_liste]
                return _temizle(kayitli)
    except: pass
    tam_liste = _TAB_LISTESI_DEFAULT.copy()
    if st.session_state.get("rol") == "admin":
        tam_liste += ["kullanici"]
    return _temizle(tam_liste)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

# ── VERSİYON KONTROL SİSTEMİ ─────────────────────────────────────────────────
GUNCEL_SURUM = "v6.7"  # Bu kodun versiyonu — her güncellemede artır

# Giriş kontrolü
if not st.session_state.get("giris", False):
    # ── ÖNCE localStorage'dan otomatik giriş dene ────────────────────────────
    _auto_giris_qp = st.query_params.get("_ag", "")
    if _auto_giris_qp:
        try:
            _ag_veri = json.loads(_auto_giris_qp)
            _ag_kul  = _ag_veri.get("kullanici","")
            _ag_sif  = _ag_veri.get("sifre","")
            _ag_mob  = _ag_veri.get("mobil", False)
            if _ag_kul and _ag_sif:
                _ag_row = None
                try:
                    from supabase import create_client as _agsc
                    _ag_sb = _agsc(st.secrets.get("SUPABASE_URL",""), st.secrets.get("SUPABASE_KEY",""))
                    _ag_res = _ag_sb.table("kullanicilar").select("*").eq("kullanici_adi", _ag_kul).eq("sifre", _ag_sif).execute()
                    if _ag_res.data: _ag_row = _ag_res.data[0]
                except: pass
                if _ag_row:
                    _ag_rol = str(_ag_row.get("rol","") or "kullanici")
                    try:
                        import json as _agj
                        _ag_yetki_val = str(_ag_row.get("yetkiler","tam") or "tam")
                        _ag_yetki = "tam" if _ag_yetki_val == "tam" else _agj.loads(_ag_yetki_val)
                    except: _ag_yetki = "tam"
                    st.session_state.update({
                        "giris": True, "kullanici": _ag_kul, "kullanici_ad": _ag_kul,
                        "rol": _ag_rol, "aktif_tab": "liste",
                        "_yetki_listesi": _ag_yetki,
                        "_mobil_mod": _ag_mob, "_ekran_kontrol": True,
                        "giris_cihaz": "mobil" if _ag_mob else "masaustu",
                    })
                    st.query_params.clear()
                    st.rerun()
        except: pass
        st.query_params.clear()

    # localStorage'dan oku ve query param ile gönder
    if not st.session_state.get("giris", False) and not st.session_state.get("_ls_denendi", False):
        st.session_state["_ls_denendi"] = True
        st.markdown("""<script>
(function(){
  try{
    var v = localStorage.getItem('mwcrm_oturum');
    if(v){
      var url = new URL(window.parent.location.href);
      url.searchParams.set('_ag', v);
      window.parent.location.replace(url.toString());
    }
  }catch(e){}
})();
</script>""", unsafe_allow_html=True)

    giris_ekrani()
    st.stop()




# ── SİSTEM AÇIK KALSIN — timeout yok ──────────────────────────────────────────
# Streamlit oturumu kullanıcı kapatana kadar aktif kalır; ekstra keep-alive gerekmez.
# st.session_state["giris"] = True zaten set, yeniden giriş istenmez.

# ── CARİ LİSTE KOLON DURUM BAŞLAT ────────────────────────────────────────────
if "_cl_kolon_genislik" not in st.session_state:
    st.session_state["_cl_kolon_genislik"] = {}
if "_cl_kolon_sira" not in st.session_state:
    st.session_state["_cl_kolon_sira"] = []

# Versiyon kontrolü — sadece admin olmayanlara
if st.session_state.get("rol") != "admin":
    try:
        _sb_s = get_sb_client()
        if _sb_s:
            _res = _sb_s.table("sistem_ayarlari").select("deger").eq("anahtar","stable_surum").execute()
            if _res.data:
                _stable = _res.data[0]["deger"]
                if _stable != GUNCEL_SURUM:
                    st.markdown("""
                    <div style='text-align:center;padding:60px 20px'>
                    <div style='font-size:3rem'>⏳</div>
                    <h2 style='color:#ff9800'>Güncelleme Hazırlanıyor</h2>
                    <p style='color:#888;font-size:1rem'>Sistem yeni sürüme hazırlanıyor.<br>
                    Yönetici onayı bekleniyor, kısa süre içinde devam edebilirsiniz.</p>
                    <p style='color:#666;font-size:0.85rem'>Verileriniz güvende — hiçbir şey kaybolmadı.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.stop()
    except:
        pass  # Bağlantı hatası olursa engelleme yapma


with st.sidebar:
    st.markdown("""
<style>
section[data-testid="stSidebar"] { 
    padding-top: 0.5rem !important; 
    transform: translateX(0px) !important;
    overflow-y: auto !important;
    height: 100vh !important;
    min-width: 260px !important;
    width: 260px !important;
    visibility: visible !important;
    display: block !important;
    margin-left: 0px !important;
    position: relative !important;
}
/* KRİTİK: Streamlit "kapalı" durumdayken sidebar'a kendi iç stilinden
   (aria-expanded="false") sıfır genişlik/gizli görünürlük veriyor — yukarıdaki
   genel kural bunu her zaman yenemiyordu ("sol menü hiç yok" sorununun kök
   nedeni buydu). Bu yüzden kapalı durumu AÇIKÇA hedefleyip aynı zorlamayı
   burada da tekrarlıyoruz. */
section[data-testid="stSidebar"][aria-expanded="false"] {
    transform: translateX(0px) !important;
    min-width: 260px !important;
    width: 260px !important;
    margin-left: 0px !important;
    visibility: visible !important;
    display: block !important;
}
section[data-testid="stSidebar"] > div:first-child {
    overflow-y: auto !important;
    height: 100% !important;
}
section[data-testid="stSidebar"] > div > div {
    overflow-y: auto !important;
}
/* Gereksiz boşlukları kaldır */
div[data-testid="stVerticalBlock"] > div:empty { display: none !important; }
div[data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
hr { margin: 0.3rem 0 !important; }
div[data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }
/* Scroll barlar: sidebar/menü gibi dar alanlarda gizli kalsın (eski görünüm),
   ama ana içerik alanı ve tablolarda mausla sürüklenebilsin diye görünür yapıldı.
   Not: st.data_editor/st.dataframe içeride kaydırma kutusunu birkaç seviye iç
   içe div ile sarabiliyor, bu yüzden "*" ile TÜM alt elemanlar hedeflendi. */
* { scrollbar-width: none !important; -ms-overflow-style: none !important; }
*::-webkit-scrollbar { display: none !important; width: 0 !important; height: 0 !important; }
section[data-testid="stMain"],
section[data-testid="stMain"] *,
div[data-testid="stDataEditor"],
div[data-testid="stDataEditor"] *,
div[data-testid="stDataFrame"],
div[data-testid="stDataFrame"] *,
div[data-testid="stElementContainer"]:has(div[data-testid="stDataEditor"]),
div[data-testid="stElementContainer"]:has(div[data-testid="stDataEditor"]) *,
div[data-baseweb="popover"],
div[data-baseweb="popover"] *,
div[data-baseweb="menu"],
div[data-baseweb="menu"] *,
ul[data-baseweb="menu"],
ul[data-baseweb="menu"] *,
[role="listbox"],
[role="listbox"] * {
    scrollbar-width: thin !important;
    -ms-overflow-style: auto !important;
}
section[data-testid="stMain"]::-webkit-scrollbar,
section[data-testid="stMain"] *::-webkit-scrollbar,
div[data-testid="stDataEditor"]::-webkit-scrollbar,
div[data-testid="stDataEditor"] *::-webkit-scrollbar,
div[data-testid="stDataFrame"]::-webkit-scrollbar,
div[data-testid="stDataFrame"] *::-webkit-scrollbar,
div[data-baseweb="popover"]::-webkit-scrollbar,
div[data-baseweb="popover"] *::-webkit-scrollbar,
div[data-baseweb="menu"]::-webkit-scrollbar,
div[data-baseweb="menu"] *::-webkit-scrollbar,
ul[data-baseweb="menu"]::-webkit-scrollbar,
ul[data-baseweb="menu"] *::-webkit-scrollbar,
[role="listbox"]::-webkit-scrollbar,
[role="listbox"] *::-webkit-scrollbar {
    display: block !important; width: 10px !important; height: 10px !important;
}
section[data-testid="stMain"]::-webkit-scrollbar-thumb,
section[data-testid="stMain"] *::-webkit-scrollbar-thumb,
div[data-testid="stDataEditor"]::-webkit-scrollbar-thumb,
div[data-testid="stDataEditor"] *::-webkit-scrollbar-thumb,
div[data-testid="stDataFrame"]::-webkit-scrollbar-thumb,
div[data-testid="stDataFrame"] *::-webkit-scrollbar-thumb,
div[data-baseweb="popover"]::-webkit-scrollbar-thumb,
div[data-baseweb="popover"] *::-webkit-scrollbar-thumb,
div[data-baseweb="menu"]::-webkit-scrollbar-thumb,
div[data-baseweb="menu"] *::-webkit-scrollbar-thumb,
ul[data-baseweb="menu"]::-webkit-scrollbar-thumb,
ul[data-baseweb="menu"] *::-webkit-scrollbar-thumb,
[role="listbox"]::-webkit-scrollbar-thumb,
[role="listbox"] *::-webkit-scrollbar-thumb {
    background: #94a3b8 !important; border-radius: 6px !important;
}
section[data-testid="stMain"]::-webkit-scrollbar-track,
div[data-testid="stDataEditor"]::-webkit-scrollbar-track,
div[data-testid="stDataFrame"]::-webkit-scrollbar-track,
div[data-baseweb="popover"]::-webkit-scrollbar-track,
div[data-baseweb="menu"]::-webkit-scrollbar-track,
ul[data-baseweb="menu"]::-webkit-scrollbar-track,
[role="listbox"]::-webkit-scrollbar-track {
    background: #f1f5f9 !important;
}
/* NOT: collapsedControl (sidebar'ı yeniden açan ok butonu) ARTIK
   gizlenmiyor — eskiden gizliydi, ama sidebar bir şekilde (dar ekran,
   yanlışlıkla tıklama vb.) kapanınca onu geri açacak hiçbir yol
   kalmıyordu ("sol menü kayboldu" sorununun kök nedeni buydu). */
section[data-testid="stSidebar"] .stButton>button {
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 10px 14px !important;
    font-size: 13px !important;
    border-radius: 6px !important;
    margin: 0 !important;
    border: 1.5px solid #cbd5e1 !important;
    background: #ffffff !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton>button p {
    text-align: left !important;
    color: inherit !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
    background: #f1f5f9 !important;
    border-color: #94a3b8 !important;
}
section[data-testid="stSidebar"] .stButton>button[kind="primary"] {
    background: #dbeafe !important;
    border-color: #3b82f6 !important;
    box-shadow: 0 1px 3px rgba(59,130,246,0.2) !important;
}
section[data-testid="stSidebar"] .stButton>button[kind="primary"] p {
    color: #1d4ed8 !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stButton { margin: 0 !important; padding: 0 !important; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div { gap: 4px !important; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 4px !important; }
section[data-testid="stSidebar"] hr { margin: 8px 0 !important; }
section[data-testid="stSidebar"] div[data-testid="stExpander"] { margin: 0 !important; }
section[data-testid="stSidebar"] div[data-testid="stExpander"] > div { padding: 0 !important; }
#MainMenu { visibility: hidden !important; }
.main .block-container {
    padding-top: 0.3rem !important;
    padding-bottom: 0.3rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}
div[data-testid="stVerticalBlock"] > div { gap: 0.3rem !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
button[data-testid="manage-app-button"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="stBottom"] { display: none !important; }
.styles_viewerBadge__CvC9N { display: none !important; }
#stDecoration { display: none !important; }
</style>
""", unsafe_allow_html=True)

    st.markdown(
        "<div style='display:flex;align-items:center;gap:11px;font-size:17px;font-weight:700;color:#1a4f9e;"
        "padding:16px 10px 16px;letter-spacing:0.4px;border-bottom:2px solid #2568c7;margin-bottom:10px;'>"
        "<svg width='30' height='30' viewBox='0 0 100 100' style='flex:none'>"
        "<rect width='100' height='100' rx='22' fill='#1D4ED8'/>"
        "<rect x='20' y='20' width='26' height='26' rx='6' fill='#97AEED'/>"
        "<rect x='54' y='20' width='26' height='26' rx='6' fill='#97AEED'/>"
        "<rect x='20' y='54' width='26' height='26' rx='6' fill='#97AEED'/>"
        "<rect x='54' y='54' width='26' height='26' rx='6' fill='#97AEED'/>"
        "</svg>"
        "MWCRMPRO</div>",
        unsafe_allow_html=True
    )

    # ── ⬅️ GERİ / 🔄 YENİLE / ➡️ İLERİ — KULLANICI İSTEĞİ (2026-09): üçü yan
    # yana, tek satırda. "Yenile" şifreden/oturumdan ÇIKMADAN, hangi sayfada
    # olursan ol her zaman ulaşabileceğin bir buton — sadece veri
    # önbelleklerini temizleyip sayfayı yeniden çizer, session_state'teki
    # "kullanici"/"rol" (giriş bilgisi) HİÇ DOKUNULMAZ, oturum açık kalır.
    # "Geri"/"İleri" ise tarayıcıdaki gibi, önceki/sonraki sayfaya döner.
    _sg_liste_btn = st.session_state.get("_sayfa_gecmisi", [st.session_state.get("aktif_tab", "liste")])
    _sg_idx_btn = st.session_state.get("_sayfa_gecmisi_idx", 0)
    _sg_geri_var = _sg_idx_btn > 0
    _sg_ileri_var = _sg_idx_btn < len(_sg_liste_btn) - 1
    _gnav1, _gnav2, _gnav3 = st.columns(3)
    if _gnav1.button("⬅️", key="sayfa_geri_btn", use_container_width=True, disabled=not _sg_geri_var, help="Geri"):
        st.session_state["_sayfa_gecmisi_idx"] = _sg_idx_btn - 1
        st.session_state["_sg_geri_ileri_tiklandi"] = True
        st.session_state["aktif_tab"] = _sg_liste_btn[_sg_idx_btn - 1]
        st.rerun()
    if _gnav2.button("🔄", key="_sb_yenile_btn", use_container_width=True,
                 help="Şifreden çıkmadan, sadece veriyi tazeler."):
        # KULLANICI İSTEĞİ (2026-09): daha önce sadece 4 önbellek temizleniyordu,
        # dosyaya eklenen YENİ önbellekli fonksiyonlar (Kargolar, Bildirimler,
        # Kullanıcı Listesi, Notlar vb.) bu listeye dahil edilmemişti — bu
        # yüzden "Yenile" bazı güncel verileri getirmiyordu. Artık dosyadaki
        # TÜM @st.cache_data fonksiyonları tek tek temizleniyor.
        for _yenile_fn in [get_cari_listesi, _tum_musteri_kargo_yekun_toplami,
                            _il_gonderim_matrisi_yukle, _kg_manuel_alici_yukle,
                            _kg_kayitlari_yukle, get_kullanici_listesi, _notlar_yukle]:
            try: _yenile_fn.clear()
            except Exception: pass
        try: db_read.clear()
        except Exception: pass
        # Filtre/sıralama gibi arayüz önbelleklerini de sıfırla — böylece
        # sayfa, en güncel ayarları (ör. Kolon Ayarları'nda az önce
        # kaydedilen bir tercih) DOĞRUDAN veritabanından yeniden okur.
        st.session_state.pop("_cl_ozel_filtre_alani_cache", None)
        st.toast("🔄 Veriler tazelendi", icon="🔄")
        st.rerun()
    if _gnav3.button("➡️", key="sayfa_ileri_btn", use_container_width=True, disabled=not _sg_ileri_var, help="İleri"):
        st.session_state["_sayfa_gecmisi_idx"] = _sg_idx_btn + 1
        st.session_state["_sg_geri_ileri_tiklandi"] = True
        st.session_state["aktif_tab"] = _sg_liste_btn[_sg_idx_btn + 1]
        st.rerun()

    # ── MENÜ LİSTESİ ──────────────────────────────────────────────────────────
    _sb_liste = get_menu_tercihi(st.session_state.get("kullanici",""))
    if st.session_state.get("rol") == "admin":
        for _t in ["kullanici"]:
            if _t not in _sb_liste:
                _sb_liste.append(_t)
    if st.session_state.get("rol") != "admin":
        try:
            import json as _yj
            _yk = f"yetki_{st.session_state['kullanici']}"
            if _yk not in st.session_state:
                _dfk = db_read("kullanicilar", extra_sql="")
                if not _dfk.empty and "yetkiler" in _dfk.columns:
                    _kr = _dfk[_dfk["kullanici_adi"] == st.session_state["kullanici"]]
                    if not _kr.empty:
                        st.session_state[_yk] = str(_kr.iloc[0].get("yetkiler","tam") or "tam")
            _yv = st.session_state.get(_yk, "tam")
            if _yv != "tam":
                _izin_listesi = _yj.loads(_yv)
                # "Hızlı Firma Ekle" yeni eklendi — eski kaydedilmiş yetki
                # listelerinde henüz yok. "Yeni Kart Ekle" izni olan herkese
                # bunu da otomatik ver (elle her kullanıcının yetkisini
                # güncellemeye gerek kalmasın).
                if "yeni" in _izin_listesi and "hizli_firma" not in _izin_listesi:
                    _izin_listesi.append("hizli_firma")
                _sb_liste = [t for t in _sb_liste if t in _izin_listesi]
        except: pass

    _sb_liste_temiz = []
    for _t in _sb_liste:
        if _t not in _sb_liste_temiz:
            _sb_liste_temiz.append(_t)
    _sb_liste = _sb_liste_temiz

    # ── ADMIN OLMAYAN KULLANICILARDAN GİZLENECEK SAYFALAR ─────────────────────
    _SADECE_ADMIN = {"kullanici", "excel"}
    if st.session_state.get("rol") != "admin":
        _sb_liste = [t for t in _sb_liste if t not in _SADECE_ADMIN]

    _TAB_RENKLER = {
        "yeni":        "#16a34a",
        "liste":       "#0369a1",
        "excel":       "#047857",
        "kullanici":   "#be123c",
        "mesajlar":    "#0891b2",
    }

    # Gizli menü öğelerini yükle
    if "_gizli_menu_list" not in st.session_state:
        try:
            _sb_gml = get_sb_client()
            if _sb_gml:
                import json as _gmlj
                _r_gml = _sb_gml.table("kullanici_tercih").select("deger").eq("kullanici", st.session_state["kullanici"]).eq("anahtar","_gizli_menu").execute()
                st.session_state["_gizli_menu_list"] = _gmlj.loads(_r_gml.data[0]["deger"]) if _r_gml.data else []
        except: st.session_state["_gizli_menu_list"] = []

    _gizli_menu_render = st.session_state.get("_gizli_menu_list", [])
    _sb_liste = [t for t in _sb_liste if t not in _gizli_menu_render]

    # Yetki bazlı menü gizleme — admin olmayan kullanıcılardan bazı menüler gizlenir
    _menu_rol = st.session_state.get("rol", "")
    # Sadece admin görebilecek menüler
    _sadece_admin_menuler = []
    if _menu_rol != "admin":
        _sb_liste = [t for t in _sb_liste if t not in _sadece_admin_menuler]

    # ── MENÜ GÖRÜNÜMÜ: Gruplu (akordeon) ────────────────────────────────────────
    st.markdown("""<style>
    section[data-testid='stSidebar'] { background-color:#ffffff; }
    section[data-testid='stSidebar'] hr { border-color:#eceae2; }
    section[data-testid='stSidebar'] .stButton>button[kind='secondary'] {
        background:transparent; border:none; border-radius:8px;
        justify-content:flex-start !important; text-align:left !important;
        transition:background-color .15s ease, color .15s ease;
    }
    section[data-testid='stSidebar'] .stButton>button[kind='secondary'] div[data-testid='stMarkdownContainer'] { width:100%; text-align:left !important; }
    section[data-testid='stSidebar'] .stButton>button[kind='secondary'] p {
        color:#2c2c2a !important; font-weight:500 !important; text-align:left !important;
        width:100%; transition:color .15s ease;
    }
    section[data-testid='stSidebar'] .stButton>button[kind='secondary']:hover { background:#f6f8fb; }
    section[data-testid='stSidebar'] .stButton>button[kind='secondary']:hover p { color:#1a4f9e !important; }
    section[data-testid='stSidebar'] .stButton>button[kind='primary'] {
        background:#eef4fc; border:none; border-left:3px solid #2568c7; border-radius:8px;
        justify-content:flex-start !important; text-align:left !important;
        transition:background-color .15s ease;
    }
    section[data-testid='stSidebar'] .stButton>button[kind='primary'] div[data-testid='stMarkdownContainer'] { width:100%; text-align:left !important; }
    section[data-testid='stSidebar'] .stButton>button[kind='primary'] p {
        color:#1a4f9e !important; font-weight:600 !important; text-align:left !important; width:100%;
    }
    section[data-testid='stSidebar'] label p, section[data-testid='stSidebar'] .stMarkdown p { color:#3d3d3a; }
    section[data-testid='stSidebar'] summary p, section[data-testid='stSidebar'] summary span { color:#3d3d3a !important; }
    </style>""", unsafe_allow_html=True)

    _MENU_GRUPLARI = [
        ("🧾 Cari işlemleri",    ["yeni", "hizli_firma", "liste", "kargolar", "excel", "mukerrer"]),
        ("🚛 Tedarikçi",         ["tedarikci"]),
        ("⚙️ Yönetim",          ["kullanici"]),
    ]

    if "_acik_grup" not in st.session_state:
        _varsayilan_acik = None
        for _g_ad, _g_keys in _MENU_GRUPLARI:
            if st.session_state["aktif_tab"] in _g_keys:
                _varsayilan_acik = _g_ad
                break
        st.session_state["_acik_grup"] = _varsayilan_acik or (_MENU_GRUPLARI[0][0] if _MENU_GRUPLARI else None)

    _gruplanan = set()
    for _g_ad, _g_keys in _MENU_GRUPLARI:
        _g_items = [t for t in _sb_liste if t in _g_keys]
        if not _g_items:
            continue
        _gruplanan.update(_g_items)

        if len(_g_items) == 1:
            # Tek sayfalı grup — kendisi tek olduğu gibi, direkt tıklanabilir tek buton
            _tek_key = _g_items[0]
            _etiket = _TAB_ETIKETLER.get(_tek_key, _tek_key)
            _aktif_mi = st.session_state["aktif_tab"] == _tek_key
            if st.button(_etiket, use_container_width=True,
                         type="primary" if _aktif_mi else "secondary",
                         key=f"sb_tek_{_tek_key}"):
                st.session_state["aktif_tab"] = _tek_key
                st.rerun()

            continue

        _acik_mi = st.session_state["_acik_grup"] == _g_ad
        _ok = "▾" if _acik_mi else "▸"
        if st.button(f"{_g_ad}   {_ok}", use_container_width=True,
                     type="primary" if _acik_mi else "secondary",
                     key=f"grphdr_{_g_ad}"):
            st.session_state["_acik_grup"] = None if _acik_mi else _g_ad
            st.rerun()
        if _acik_mi:
            for _tab_key in _g_items:
                _etiket = _TAB_ETIKETLER.get(_tab_key, _tab_key)
                _aktif_mi = st.session_state["aktif_tab"] == _tab_key
                _c1, _c2 = st.columns([1, 6])
                with _c2:
                    if st.button(_etiket, use_container_width=True,
                                 type="primary" if _aktif_mi else "secondary",
                                 key=f"sb_{_g_ad}_{_tab_key}"):
                        st.session_state["aktif_tab"] = _tab_key
                        st.rerun()

    _kalanlar = [t for t in _sb_liste if t not in _gruplanan]
    if _kalanlar:
        _acik_mi = st.session_state["_acik_grup"] == "DİĞER"
        _ok = "▾" if _acik_mi else "▸"
        if st.button(f"Diğer   {_ok}", use_container_width=True,
                     type="primary" if _acik_mi else "secondary",
                     key="grphdr_DIGER"):
            st.session_state["_acik_grup"] = None if _acik_mi else "DİĞER"
            st.rerun()
        if _acik_mi:
            for _tab_key in _kalanlar:
                _etiket = _TAB_ETIKETLER.get(_tab_key, _tab_key)
                _aktif_mi = st.session_state["aktif_tab"] == _tab_key
                _c1, _c2 = st.columns([1, 6])
                with _c2:
                    if st.button(_etiket, use_container_width=True,
                                 type="primary" if _aktif_mi else "secondary",
                                 key=f"sb_diger_{_tab_key}"):
                        st.session_state["aktif_tab"] = _tab_key
                        st.rerun()

    # ── ALT BÖLÜM ─────────────────────────────────────────────────────────────
    st.divider()

    st.divider()

    st.divider()

    # ── KULLANICI + ÇIKIŞ ─────────────────────────────────────────────────────
    _kc1, _kc2 = st.columns([3, 1])
    _kul_ad = st.session_state.get('kullanici','')
    _kul_bas_harf = (_kul_ad[:2].upper() if _kul_ad else "AD")
    _kc1.markdown(
        f"<div style='padding:4px 4px;display:flex;align-items:center;gap:9px;'>"
        f"<div style='width:26px;height:26px;border-radius:50%;background:#eef4fc;color:#1a4f9e;"
        f"display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;flex:none;'>{_kul_bas_harf}</div>"
        f"<div style='line-height:1.4;'>"
        f"<div style='font-size:12.5px;font-weight:500;color:#2c2c2a;'>{_kul_ad}</div>"
        f"<div style='font-size:11px;color:#8a8880;'>{st.session_state.get('rol','')}</div>"
        f"</div></div>",
        unsafe_allow_html=True
    )
    if _kc2.button("🚪", key="sidebar_cikis", use_container_width=True, help="Çıkış"):
        cikis()


# ── ANA UYGULAMA ──────────────────────────────────────────────────────────────
st.divider()

# Tab her zaman session_state'ten
if "aktif_tab" not in st.session_state:
    st.session_state["aktif_tab"] = "liste"
aktif = st.session_state["aktif_tab"]

# ── SAYFA GEZİNME GEÇMİŞİ (⬅️ Geri / ➡️ İleri) — KULLANICI İSTEĞİ (2026-09):
# tarayıcıdaki gibi, sol menüden farklı sayfalara geçerken, şifreden HİÇ
# çıkmadan önceki/sonraki sayfaya dönebilme. "aktif_tab" her DEĞİŞTİĞİNDE
# (Geri/İleri butonlarından DEĞİL, menüden tıklanarak) bu geçmiş listesine
# eklenir; "ileri" kısmı (geri gidilmişse) yeni bir sayfaya tıklanınca kesilir
# — tarayıcı geçmişiyle birebir aynı mantık.
if "_sayfa_gecmisi" not in st.session_state:
    st.session_state["_sayfa_gecmisi"] = [aktif]
    st.session_state["_sayfa_gecmisi_idx"] = 0
else:
    _sg_liste_kontrol = st.session_state["_sayfa_gecmisi"]
    _sg_idx_kontrol = st.session_state["_sayfa_gecmisi_idx"]
    if not st.session_state.pop("_sg_geri_ileri_tiklandi", False):
        if not _sg_liste_kontrol or _sg_liste_kontrol[_sg_idx_kontrol] != aktif:
            _sg_liste_kontrol = _sg_liste_kontrol[:_sg_idx_kontrol + 1] + [aktif]
            st.session_state["_sayfa_gecmisi"] = _sg_liste_kontrol
            st.session_state["_sayfa_gecmisi_idx"] = len(_sg_liste_kontrol) - 1


# ── MOBİL MOD — body class + nav aktif ikon ──────────────────────────────────
_mobil_mod_aktif = st.session_state.get("_mobil_mod", False)
_aktif_tab_js = aktif
st.markdown(f"""
<script>
(function(){{
  var _body = window.parent ? window.parent.document.body : document.body;
  if({'true' if _mobil_mod_aktif else 'false'}){{
    _body.classList.add('mw-mobil-aktif');
  }} else {{
    _body.classList.remove('mw-mobil-aktif');
  }}
  // Nav butonlarında aktif class güncelle
  var _cur = '{_aktif_tab_js}';
  var _tabMap = {{'liste':'liste','analiz':'analiz','randevu':'randevu','harita':'harita'}};
  var _curNav = _tabMap[_cur] || _cur;
  document.querySelectorAll('.mw-nav-btn').forEach(function(b){{
    var _fn = b.getAttribute('onclick') || '';
    var _m = _fn.match(/mwTab\('([^']+)'\)/);
    if(_m && _m[1] === _curNav) b.classList.add('aktif');
    else b.classList.remove('aktif');
  }});
}})();
</script>
""", unsafe_allow_html=True)

# ── OTOMATİK SAYFA TAKİBİ ───────────────────────────────────────────────────
sayfa_log(aktif)


# ── YENİ KART EKLE / DÜZENLE ─────────────────────────────────────────────────
if aktif == "yeni":
    sayfa_log("yeni")

    # Müşteri ara ve düzenle
    st.markdown("### 🔍 Mevcut Müşteri Ara & Düzenle")
    col_ara1, col_ara2 = st.columns([3, 1])
    with col_ara1:
        musteri_ara = st.text_input("ID veya Firma Adı ile ara...", key="musteri_ara", placeholder="Örn: 5  veya  'ABC Ltd'")
    with col_ara2:
        st.markdown("<br>", unsafe_allow_html=True)
        ara_btn = st.button("🔎 Ara", use_container_width=True)

    bulunan = None
    if musteri_ara and ara_btn:
        df_ara_s = db_read("cari_kartlar", extra_sql="WHERE (silindi=0 OR silindi='0' OR silindi IS NULL) ORDER BY firma")
        if not df_ara_s.empty:
            if musteri_ara.strip().isdigit():
                row_s = df_ara_s[df_ara_s["id"]==int(musteri_ara.strip())]
            else:
                row_s = df_ara_s[df_ara_s["firma"].str.contains(musteri_ara.strip(), case=False, na=False)]
            if not row_s.empty:
                r_d = row_s.iloc[0]
                bulunan = {str(k): ("" if str(v) in ["nan","None","NaT"] else str(v)) for k,v in r_d.items()}
                if not bulunan.get("gsm"):
                    bulunan["gsm"] = str(r_d.get("telefon") or r_d.get("tel") or "")
                if not bulunan.get("sabit"):
                    bulunan["sabit"] = str(r_d.get("sabit_hat") or "")
                _duzenleme_form_key_temizle(str(bulunan.get("id","")))
                st.session_state["duzenle_musteri"] = bulunan
                st.success(f"✅ **{bulunan.get('firma')}** (ID: {bulunan.get('id')})")
            else:
                st.error("Müşteri bulunamadı.")
                st.session_state.pop("duzenle_musteri", None)

    duzenle = st.session_state.get("duzenle_musteri")
    # Formdaki widget key'lerini düzenlenen müşterinin ID'sine bağlıyoruz.
    # Böylece farklı bir müşteriye geçildiğinde (veya yeni boş karta geçildiğinde)
    # Streamlit eski session_state değerini değil, müşterinin GERÇEK verisini gösterir.
    _form_id = str(duzenle.get("id")) if duzenle else "new"
    # Her düzenlemede form key'lerini temizle — eski değer yapışmasın
    _form_keys = [
        f"yeni_firma_{_form_id}", f"yeni_yetkili_{_form_id}",
        f"yeni_gsm_{_form_id}", f"yeni_sabit_{_form_id}", f"yeni_email_{_form_id}",
        f"yeni_adres_{_form_id}", f"yeni_notlar_{_form_id}",
        f"yeni_il_dis_{_form_id}", f"yeni_ilce_dis_{_form_id}",
        f"yeni_durum_dis_{_form_id}", f"yeni_temsilci_dis_{_form_id}",
        f"yeni_seg_dis_{_form_id}", f"yeni_asama_dis_{_form_id}",
    ]
    # Sadece müşteri değişince temizle
    _onceki_form_id = st.session_state.get("_onceki_form_id","")
    if _onceki_form_id != _form_id:
        for _fk in _form_keys:
            if _fk in st.session_state:
                del st.session_state[_fk]
        st.session_state["_onceki_form_id"] = _form_id

    st.divider()
    if duzenle:
        st.markdown(f"### ✏️ Düzenleniyor: **{duzenle.get('firma')}** (ID: {duzenle.get('id')})")
    else:
        st.markdown("### ➕ Yeni Cari Kart")

    il_listesi = sorted(ILLER_ILCELER.keys())
    _il_normalize_harita = {_bl_sadelestir(_ad): _ad for _ad in il_listesi}
    _kayitli_il_ham = duzenle.get("il","") if duzenle else ""
    # Büyük/küçük harf, yazım farkı toleranslı eşleştirme — kayıtlı değer varsa ASLA sessizce sıfırlanmaz
    mevcut_il = _il_normalize_harita.get(_bl_sadelestir(_kayitli_il_ham), il_listesi[0])
    if _kayitli_il_ham and _bl_sadelestir(_kayitli_il_ham) not in _il_normalize_harita:
        st.warning(f"⚠️ Kayıtlı il '{_kayitli_il_ham}' tanımlı 81 il listesinde bulunamadı — "
                   f"geçici olarak '{il_listesi[0]}' gösteriliyor. Doğru ili siz seçin, kaydedince güncellenir.")
    # Eski session key'lerini temizle — her durumda temizle ki eski değer yapışmasın
    for _dk in ["yeni_il_sec","yeni_ilce_sec","yeni_il_form","yeni_ilce_form",
                f"yeni_il_dis_{_form_id}", f"yeni_ilce_dis_{_form_id}"]:
        if _dk in st.session_state:
            del st.session_state[_dk]
    _asama_base = _tanimlar_yukle("asama")
    try:
        _df_as2 = db_read("cari_kartlar", extra_sql="WHERE silindi=0 OR silindi IS NULL")
        if not _df_as2.empty and "islem_asamasi" in _df_as2.columns:
            for _a in _df_as2["islem_asamasi"].dropna().unique():
                if str(_a).strip() and str(_a) not in ["nan",""] and _a not in _asama_base:
                    _asama_base.append(str(_a))
    except: pass

    # ── İL / İLÇE form dışında — dinamik güncelleme için ───────────────────
    r2c1,r2c2,r2c3,r2c4,r2c5,r2c6 = st.columns(6)
    il_idx  = il_listesi.index(mevcut_il) if mevcut_il in il_listesi else 0
    il      = r2c1.selectbox("İl", il_listesi, index=il_idx, key=f"yeni_il_dis_{_form_id}")
    ilce_list_tum = ILLER_ILCELER.get(il, [""])
    _ilce_normalize_harita = {_bl_sadelestir(_ad): _ad for _ad in ilce_list_tum}
    _kayitli_ilce_ham = duzenle.get("ilce","") if duzenle else ""
    mevcut_ilce = _ilce_normalize_harita.get(_bl_sadelestir(_kayitli_ilce_ham), ilce_list_tum[0] if ilce_list_tum else "")
    # Streamlit'in yerleşik dropdown araması Türkçe karakterlerde (ş,ğ,ç,ı,ö,ü)
    # güvenilir eşleşmiyor ("baş" yazınca "Başakşehir" bulunamıyor). Bu yüzden
    # kendi Türkçe-toleranslı arama kutumuzu kullanıyoruz (_bl_sadelestir ile).
    _ilce_arama = r2c2.text_input("İlçe", key=f"yeni_ilce_arama_{_form_id}", placeholder="🔍 İlçe ara...")
    if _ilce_arama.strip():
        _arama_norm = _bl_sadelestir(_ilce_arama)
        ilce_list = [i for i in ilce_list_tum if _arama_norm in _bl_sadelestir(i)]
        if mevcut_ilce and mevcut_ilce not in ilce_list:
            ilce_list = [mevcut_ilce] + ilce_list
        if not ilce_list:
            ilce_list = ilce_list_tum  # arama sonuçsuzsa tam listeye düş, kullanıcı kilitlenmesin
    else:
        ilce_list = ilce_list_tum
    ilce_idx = ilce_list.index(mevcut_ilce) if mevcut_ilce in ilce_list else 0
    ilce    = r2c2.selectbox(" ", ilce_list, index=ilce_idx, key=f"yeni_ilce_dis_{_form_id}", label_visibility="collapsed")
    durum_opts = _tanimlar_yukle("durum") or ["Özel Müşteri","Portföy"]
    durum_idx  = durum_opts.index(duzenle.get("durum","")) if duzenle and duzenle.get("durum","") in durum_opts else 0
    durum   = r2c3.selectbox("Durum", durum_opts, index=durum_idx, key=f"yeni_durum_dis_{_form_id}")
    temsilci_dis = r2c4.text_input("Temsilci", value=duzenle.get("temsilci","") if duzenle else "", key=f"yeni_temsilci_dis_{_form_id}", placeholder="Temsilci adı")
    seg_opts = ["--","👑 A+","⭐ A","🔵 B","⚪ C"]
    seg_idx  = seg_opts.index(duzenle.get("segment","--")) if duzenle and duzenle.get("segment","--") in seg_opts else 0
    segment  = r2c5.selectbox("Segment", seg_opts, index=seg_idx, key=f"yeni_seg_dis_{_form_id}")
    _asama_default = duzenle.get("islem_asamasi") if duzenle else st.session_state.pop("varsayilan_asama", None)
    asama_idx = _asama_base.index(_asama_default) if _asama_default and _asama_default in _asama_base else 0
    asama    = r2c6.selectbox("İşlem Aşaması", _asama_base, index=asama_idx, key=f"yeni_asama_dis_{_form_id}")

    with st.form("yeni_kart_form"):
        # ── SATIR 1: Rakip Firma, Firma, Yetkili, GSM, Sabit Tel, E-Mail ─────
        r1c0,r1c1,r1c2,r1c3,r1c4,r1c5 = st.columns(6)
        rakip_firma = r1c0.text_input("Rakip Firma", value=duzenle.get("rakip_firma","") if duzenle else "", placeholder="Rakip firma adı", key=f"yeni_rakip_{_form_id}")
        firma   = r1c1.text_input("Firma Adı *", value=duzenle.get("firma","") if duzenle else "", placeholder="Firma adı", key=f"yeni_firma_{_form_id}")
        yetkili = r1c2.text_input("Yetkili",     value=duzenle.get("yetkili","") if duzenle else "", placeholder="Ad Soyad", key=f"yeni_yetkili_{_form_id}")
        gsm     = r1c3.text_input("GSM",         value=fmt_tel(duzenle.get("gsm","")) if duzenle else "", placeholder="05xx xxx xx xx", key=f"yeni_gsm_{_form_id}")
        sabit   = r1c4.text_input("Sabit Tel",   value=fmt_tel(duzenle.get("sabit","")) if duzenle else "", placeholder="0212 xxx xx xx", key=f"yeni_sabit_{_form_id}")
        email   = r1c5.text_input("E-Mail",      value=duzenle.get("email","") if duzenle else "", placeholder="mail@firma.com", key=f"yeni_email_{_form_id}")
        temsilci = temsilci_dis  # form dışından al

        # ── SATIR 3: Adres, Açıklama ─────────────────────────────────────────
        r3c1, r3c2 = st.columns(2)
        adres    = r3c1.text_area("Adres", value=duzenle.get("adres","") if duzenle else "", height=70, key=f"yeni_adres_{_form_id}")
        notlar_v = r3c2.text_area("📝 Açıklama", value=str(duzenle.get("aciklama","") or "") if duzenle else "", height=70, key=f"yeni_notlar_{_form_id}")

        # ── SATIR 4: Ciro ────────────────────────────────────────────────────
        cc1,cc2,cc3,cc4 = st.columns(4)
        bek_val = duzenle.get("beklenen_ciro",0) if duzenle else 0
        ger_val = duzenle.get("gerceklesen_ciro",0) if duzenle else 0
        bek_str = cc1.text_input("Beklenen Ciro (₺)", value=fmt_para(bek_val).replace(" ₺",""), placeholder="0", key=f"bek_ciro_str_{_form_id}")
        ger_str = cc2.text_input("Gerçekleşen Ciro (₺)", value=fmt_para(ger_val).replace(" ₺",""), placeholder="0", key=f"ger_ciro_str_{_form_id}")
        beklenen_ciro    = parse_para(bek_str)
        gerceklesen_ciro = parse_para(ger_str)
        fark  = gerceklesen_ciro - beklenen_ciro
        yuzde = (gerceklesen_ciro/beklenen_ciro*100) if beklenen_ciro>0 else 0
        cc3.metric("Fark (₺)", fmt_para(fark))
        cc4.metric("Gerçekleşme %", f"%{yuzde:.1f}".replace(".",","))

        btn_label = "💾 Güncelle" if duzenle else "💾 Cari Kartı Kaydet"
        if st.form_submit_button(btn_label, type="primary", use_container_width=True):
            # Form dışındaki değerleri session_state'den al
            _il_kayit    = st.session_state.get(f"yeni_il_dis_{_form_id}", il)
            _ilce_kayit  = st.session_state.get(f"yeni_ilce_dis_{_form_id}", ilce)
            _durum_kayit = st.session_state.get(f"yeni_durum_dis_{_form_id}", durum)
            _seg_kayit   = st.session_state.get(f"yeni_seg_dis_{_form_id}", "--")
            _asama_kayit = st.session_state.get(f"yeni_asama_dis_{_form_id}", asama)
            _tem_kayit   = st.session_state.get(f"yeni_temsilci_dis_{_form_id}", temsilci)

            # ── CİRO'YA GÖRE DURUM OTOMATİK BELİRLE ──────────────────────────
            # 100.000₺ altı → Portföy | 100.000₺ ve üzeri → Özel Müşteri
            if beklenen_ciro > 0:
                _durum_kayit = "Özel Müşteri" if beklenen_ciro >= 100000 else "Portföy"
            if not firma:
                st.warning("Firma adı boş bırakılamaz!")
            else:
                # Ekranda "541 357 80 20" gruplu görünse de veritabanına her zaman
                # sade rakamlarla yazılır (WhatsApp vb. entegrasyonlar boşluksuz
                # rakam bekliyor).
                gsm = "".join(ch for ch in str(gsm or "") if ch.isdigit())
                sabit = "".join(ch for ch in str(sabit or "") if ch.isdigit())
            if not firma:
                pass
            elif duzenle:
                ok = db_update("cari_kartlar", {
                    "firma": firma, "rakip_firma": rakip_firma, "yetkili": yetkili, "gsm": gsm,
                    "sabit": sabit, "email": email, "adres": adres,
                    "ilce": _ilce_kayit, "il": _il_kayit, "durum": _durum_kayit,
                    "temsilci": _tem_kayit, "islem_asamasi": _asama_kayit,
                    "segment": _seg_kayit, "aciklama": notlar_v,
                    "beklenen_ciro": beklenen_ciro, "gerceklesen_ciro": gerceklesen_ciro
                }, "id", duzenle.get("id"))
                try: db_read.clear()
                except: pass
                st.session_state.pop("duzenle_musteri", None)
                st.session_state["aktif_tab"] = "liste"
                st.session_state["kayit_mesaj"] = f"✅ '{firma}' güncellendi!"
                st.rerun()
            else:
                ok = db_insert("cari_kartlar", {
                    "tarih": datetime.now().isoformat(),
                    "firma": firma, "rakip_firma": rakip_firma, "yetkili": yetkili, "gsm": gsm,
                    "sabit": sabit, "email": email, "adres": adres,
                    "ilce": _ilce_kayit, "il": _il_kayit, "durum": _durum_kayit,
                    "temsilci": _tem_kayit, "islem_asamasi": _asama_kayit,
                    "segment": _seg_kayit, "aciklama": notlar_v,
                    "silindi": 0, "olusturan": st.session_state["kullanici"],
                    "beklenen_ciro": beklenen_ciro, "gerceklesen_ciro": gerceklesen_ciro,
                    "atanan_kullanici": st.session_state.get("kullanici","")
                })
                try: db_read.clear()
                except: pass
                st.session_state["aktif_tab"] = "liste"
                st.session_state["kayit_mesaj"] = f"✅ '{firma}' kaydedildi!"
                st.rerun()

    if duzenle:
        if st.button("❌ Düzenlemeyi İptal Et", use_container_width=True):
            st.session_state.pop("duzenle_musteri", None)
            st.rerun()

# ── CARİ LİSTE ───────────────────────────────────────────────────────────────
elif aktif == "hizli_firma":
    st.subheader("⚡ Hızlı Firma Ekle")
    st.caption("İnternetten (Google/Yandex Haritalar, rehber siteleri vb.) kopyaladığın karmaşık/düzensiz firma bilgisini aşağıya yapıştır — Firma Adı, GSM, Sabit Tel, Email, Adres, İl ve İlçe otomatik ayrıştırılır. Kaydetmeden önce gözden geçirip düzeltebilirsin.")
    _hfs_ham_metin = st.text_area("Yapıştır", height=180, key="hfs_ham", placeholder="Firma adı\nAdres: Mahalle, Cadde No:12, İlçe/İl\n0212 555 44 33\n0555 444 33 22\ninfo@firma.com", label_visibility="collapsed")
    if st.button("🔍 Ayrıştır", key="hfs_ayristir_btn"):
        if _hfs_ham_metin.strip():
            # KULLANICI İSTEĞİ: yeni ayrıştırmadan önce, önceki ayrıştırmadan
            # kalan alan kutularının session_state değerleri de temizlenir —
            # aksi halde Streamlit "value=" parametresini yok sayıp ESKİ
            # değerleri göstermeye devam ediyordu.
            for _hfs_alan_k in ("firma", "gsm", "sabit", "email", "adres", "il", "ilce"):
                st.session_state.pop(f"hfs_{_hfs_alan_k}", None)
            st.session_state["hfs_sonuc"] = _hizli_firma_ayristir(_hfs_ham_metin)
        else:
            st.warning("Önce bir metin yapıştır.")
    _hfs_sonuc = st.session_state.get("hfs_sonuc")
    if _hfs_sonuc:
        st.markdown("**Ayrıştırılan bilgiler — kaydetmeden önce gözden geçir/düzelt:**")
        _hfsc1, _hfsc2 = st.columns(2)
        _hfs_firma = _hfsc1.text_input("Firma Adı", value=_hfs_sonuc["firma_adi"], key="hfs_firma")
        _hfs_gsm = _hfsc2.text_area("GSM (birden fazlaysa alt alta)", value=_hfs_sonuc["gsm"], key="hfs_gsm", height=70)
        _hfsc3, _hfsc4 = st.columns(2)
        _hfs_sabit = _hfsc3.text_area("Sabit Tel (birden fazlaysa alt alta)", value=_hfs_sonuc["sabit"], key="hfs_sabit", height=70)
        _hfs_email = _hfsc4.text_area("Email (birden fazlaysa alt alta)", value=_hfs_sonuc["email"], key="hfs_email", height=70)
        _hfs_adres = st.text_area("Adres(ler) (birden fazlaysa alt alta)", value=_hfs_sonuc["adres"], height=90, key="hfs_adres")
        _hfsc5, _hfsc6 = st.columns(2)
        _hfs_il_opts = ["-- İl seçilir --"] + sorted(_IL_ILCE_HARITASI.keys())
        _hfs_il_idx = _hfs_il_opts.index(_hfs_sonuc["il"]) if _hfs_sonuc["il"] in _hfs_il_opts else 0
        _hfs_il = _hfsc5.selectbox("İl", _hfs_il_opts, index=_hfs_il_idx, key="hfs_il",
                                    format_func=lambda x: _tr_buyuk(x) if x != "-- İl seçilir --" else x)
        _hfs_ilce_opts = _IL_ILCE_HARITASI.get(_hfs_il, []) if _hfs_il != "-- İl seçilir --" else []
        _hfs_ilce_liste = ["-- Önce il seç --"] + _hfs_ilce_opts if _hfs_ilce_opts else ["-- Önce il seç --"]
        _hfs_ilce_idx = _hfs_ilce_liste.index(_hfs_sonuc["ilce"]) if _hfs_sonuc["ilce"] in _hfs_ilce_liste else 0
        _hfs_ilce = _hfsc6.selectbox("İlçe", _hfs_ilce_liste, index=_hfs_ilce_idx, key="hfs_ilce",
                                      format_func=lambda x: _tr_buyuk(x) if x != "-- Önce il seç --" else x)

        # ── MÜKERRER KONTROLÜ — kaydetmeden ÖNCE, aynı isim/telefon/email'e
        # sahip mevcut kayıt var mı diye kontrol edilir. Sadece UYARIR,
        # engellemez — kullanıcı yine de eklemeyi seçebilir.
        _hfs_mukerrer = _hizli_firma_mukerrer_kontrol(_hfs_firma, _hfs_gsm, _hfs_sabit, _hfs_email)
        if _hfs_mukerrer:
            st.warning(f"⚠️ Bende şu kayıt(lar) zaten var — dikkatli ol, mükerrer olabilir:")
            for _hfsm in _hfs_mukerrer:
                st.markdown(f"- **{_hfsm['firma']}** ({_hfsm['sebep']}) — GSM: {_hfsm['gsm'] or '-'} · Sabit: {_hfsm['sabit'] or '-'} · Email: {_hfsm['email'] or '-'} · İl: {_hfsm['il'] or '-'}")

        if st.button("💾 Cari Ana Listeye Ekle", type="primary", key="hfs_kaydet_btn", use_container_width=True):
            if not _hfs_firma.strip():
                st.error("⚠️ Firma Adı boş olamaz.")
            else:
                _hfs_ok = db_insert("cari_kartlar", {
                    "tarih": datetime.now().isoformat(),
                    "firma": _tr_buyuk(_hfs_firma), "yetkili": "",
                    "gsm": _hfs_gsm.strip(), "sabit": _hfs_sabit.strip(),
                    "email": _hfs_email.strip(),
                    "adres": _tr_buyuk(_hfs_adres),
                    "ilce": _tr_buyuk(_hfs_ilce) if _hfs_ilce != "-- Önce il seç --" else "",
                    "il": _tr_buyuk(_hfs_il) if _hfs_il != "-- İl seçilir --" else "",
                    "durum": "Portföy", "silindi": 0,
                    "olusturan": st.session_state.get("kullanici", ""),
                    "beklenen_ciro": 0, "gerceklesen_ciro": 0,
                    "atanan_kullanici": st.session_state.get("kullanici", "")
                })
                try: db_read.clear()
                except: pass
                try: get_cari_listesi.clear()
                except: pass
                if _hfs_ok:
                    st.session_state.pop("hfs_sonuc", None)
                    st.session_state.pop("hfs_ham", None)
                    for _hfs_alan_k2 in ("firma", "gsm", "sabit", "email", "adres", "il", "ilce"):
                        st.session_state.pop(f"hfs_{_hfs_alan_k2}", None)
                    st.success(f"✅ '{_hfs_firma}' Cari Ana Liste'ye eklendi!")
                    st.rerun()
                else:
                    st.error("⚠️ Kaydedilemedi — lütfen tekrar dene.")

        # ── KULLANICI İSTEĞİ (2026-09): eski/eksik bilgili bir müşteri
        # SEÇİP, YENİ müşteri oluşturmak yerine aynı ayrıştırma sonucunu o
        # müşterinin eksik alanlarına doldurabilirsin. Zaten DOLU olan
        # alanlara ASLA dokunulmaz — sadece BOŞ olanlar doldurulur (veri
        # kaybı riski yok). Çoklu değerli alanlar (GSM/Sabit/Email) için
        # yeni satırlar mevcutlara EKLENİR (tekrarlanmayan satırlar).
        st.divider()
        with st.expander("🔄 Bunun yerine, eksik bilgili MEVCUT bir müşteriyi doldur"):
            _hfs_mevcut_df2 = get_cari_listesi()
            if _hfs_mevcut_df2.empty or "firma" not in _hfs_mevcut_df2.columns:
                st.caption("Henüz müşteri kaydı yok.")
            else:
                _hfs_mevcut_secenekler = [f"[{int(i)}] {f}" for i, f in zip(_hfs_mevcut_df2["id"], _hfs_mevcut_df2["firma"]) if str(f) not in ["", "nan", "None"]]
                _hfs_mevcut_sec = st.selectbox("Doldurulacak müşteri", ["-- Müşteri seçilir --"] + _hfs_mevcut_secenekler, key="hfs_mevcut_musteri_sec")
                if _hfs_mevcut_sec != "-- Müşteri seçilir --" and st.button(
                        "🔄 Seçili Müşterinin Eksik Bilgilerini Bu Verilerle Doldur",
                        key="hfs_mevcut_doldur_btn", use_container_width=True):
                    try:
                        _hfs_mevcut_id = int(_hfs_mevcut_sec.split("]")[0].replace("[", "").strip())
                        _hfs_mevcut_satir = _hfs_mevcut_df2[_hfs_mevcut_df2["id"] == _hfs_mevcut_id]
                        if _hfs_mevcut_satir.empty:
                            st.error("⚠️ Bu müşteri bulunamadı — sayfayı yenileyip tekrar dene.")
                        else:
                            _hfs_m = _hfs_mevcut_satir.iloc[0]

                            def _hfs_coklu_birlestir(_eski, _yeni):
                                # KULLANICI İSTEĞİ (2026-09): YENİ veriler
                                # ÜSTTE, ESKİ veriler ALTTA görünsün.
                                _eski_satirlar = [s.strip() for s in str(_eski or "").split("\n") if s.strip()]
                                _yeni_satirlar = [s.strip() for s in str(_yeni or "").split("\n") if s.strip()]
                                _birlesik = list(_yeni_satirlar)
                                for _es in _eski_satirlar:
                                    if _es not in _birlesik:
                                        _birlesik.append(_es)
                                return "\n".join(_birlesik)

                            _hfs_guncelle_alan = {}
                            _hfs_guncelle_alan["gsm"] = _hfs_coklu_birlestir(_hfs_m.get("gsm", ""), _hfs_gsm)
                            _hfs_guncelle_alan["sabit"] = _hfs_coklu_birlestir(_hfs_m.get("sabit", ""), _hfs_sabit)
                            _hfs_guncelle_alan["email"] = _hfs_coklu_birlestir(_hfs_m.get("email", ""), _hfs_email)
                            # KULLANICI İSTEĞİ (2026-09 düzeltmesi): ayrıştırılan
                            # veri VARSA doğrudan uygulanır — "sadece boşsa
                            # doldur" kuralı, mevcut kayıttaki anlamsız
                            # kalıntılar (boşluk, tire vb.) yüzünden "zaten
                            # dolu" sayılıp adres/il hiç güncellenmiyordu.
                            if _hfs_adres.strip():
                                _hfs_guncelle_alan["adres"] = _tr_buyuk(_hfs_adres)
                            if _hfs_il != "-- İl seçilir --":
                                _hfs_guncelle_alan["il"] = _tr_buyuk(_hfs_il)
                            if _hfs_ilce != "-- Önce il seç --":
                                _hfs_guncelle_alan["ilce"] = _tr_buyuk(_hfs_ilce)
                            db_update("cari_kartlar", _hfs_guncelle_alan, "id", _hfs_mevcut_id)
                            try: db_read.clear()
                            except: pass
                            try: get_cari_listesi.clear()
                            except: pass
                            st.session_state.pop("hfs_sonuc", None)
                            st.session_state.pop("hfs_ham", None)
                            for _hfs_alan_k3 in ("firma", "gsm", "sabit", "email", "adres", "il", "ilce"):
                                st.session_state.pop(f"hfs_{_hfs_alan_k3}", None)
                            st.success(f"✅ '{_hfs_m.get('firma','')}' güncellendi — eksik alanlar dolduruldu")
                            st.rerun()
                    except Exception as _hfs_doldur_hata:
                        st.error(f"Hata: {_hfs_doldur_hata}")

elif aktif == "mukerrer":
    sayfa_log("mukerrer")
    st.markdown("## 🔍 Mükerrer (Aynı İsimli) Müşterileri Bul ve Birleştir")

    _mk_df = get_cari_listesi()
    if not _mk_df.empty and "silindi" in _mk_df.columns:
        _mk_df = _mk_df[~(_mk_df["silindi"].astype(str).str.strip().isin(["1","True","true","1.0"]))]
    _mk_df = _atama_filtresi_uygula(_mk_df)

    if _mk_df.empty or "firma" not in _mk_df.columns:
        st.caption("Veri yok.")
    else:
        _mk_firma_gruplari = _mk_df.groupby(_mk_df["firma"].astype(str).str.strip().str.upper())["id"].apply(list)
        _mk_mukerrerler = {k: v for k, v in _mk_firma_gruplari.items() if len(v) > 1 and k not in ["", "NAN", "NONE"]}
        if not _mk_mukerrerler:
            st.success("✅ Mükerrer müşteri bulunamadı.")
        else:
            _mk_tum_idler = [int(i) for _v in _mk_mukerrerler.values() for i in _v]
            st.warning(f"{len(_mk_mukerrerler)} mükerrer firma adı bulundu — toplam {len(_mk_tum_idler)} kayıt.")
            st.caption("Hücrelere tıklayıp elle düzenleyin, \"💾 Kaydet\" ile kaydedin. "
                       "Silmek istediklerinizi \"Seç\" kutusuyla işaretleyip \"🗑️ Seçilenleri Sil\"e basın.")

            _mk_kolonlar = [c for c in ["id","rakip_firma","firma","yetkili","gsm","sabit","email","il","ilce",
                                         "durum","islem_asamasi","beklenen_ciro","gerceklesen_ciro"]
                             if c in _mk_df.columns]
            _mk_tablo = _mk_df[_mk_df["id"].astype(int).isin(_mk_tum_idler)][_mk_kolonlar].copy()
            _mk_tablo = _mk_tablo.sort_values("firma").reset_index(drop=True)

            # ── Not / Analiz / Randevu bilgisi — diğer tablolardan hesaplanır (salt okunur) ──
            _mk_sb_ek = get_sb_client()
            _mk_not_sayac, _mk_rand_sayac, _mk_analiz_set = {}, {}, set()
            if _mk_sb_ek:
                try:
                    _mk_not_ham = _mk_sb_ek.table("cari_aciklamalar").select("cari_id,aciklama").in_(
                        "cari_id", _mk_tum_idler).execute().data or []
                    for _r in _mk_not_ham:
                        if str(_r.get("aciklama","") or "").startswith("##YETKILI##"):
                            continue
                        _cid = int(_r.get("cari_id", 0) or 0)
                        _mk_not_sayac[_cid] = _mk_not_sayac.get(_cid, 0) + 1
                except Exception: pass
                try:
                    _mk_rand_ham = _mk_sb_ek.table("randevular").select("musteri_id").in_(
                        "musteri_id", _mk_tum_idler).execute().data or []
                    for _r in _mk_rand_ham:
                        _cid = int(_r.get("musteri_id", 0) or 0)
                        _mk_rand_sayac[_cid] = _mk_rand_sayac.get(_cid, 0) + 1
                except Exception: pass
                try:
                    _mk_firmalar_upper = set(_mk_tablo["firma"].astype(str).str.strip().str.upper())
                    _mk_analiz_ham = _mk_sb_ek.table("musteri_analiz").select("firma").execute().data or []
                    _mk_analiz_set = {str(a.get("firma","")).strip().upper() for a in _mk_analiz_ham
                                       if str(a.get("firma","")).strip().upper() in _mk_firmalar_upper}
                except Exception: pass

            _mk_tablo["Notlar"] = _mk_tablo["id"].apply(lambda x: _mk_not_sayac.get(int(x), 0))
            _mk_tablo["Randevu"] = _mk_tablo["id"].apply(lambda x: _mk_rand_sayac.get(int(x), 0))
            _mk_tablo["Analiz"] = _mk_tablo["firma"].apply(
                lambda x: "✅" if str(x).strip().upper() in _mk_analiz_set else "")

            _mk_tablo.insert(0, "Seç", False)

            # Kolon genişlik ayarlarını (Kolon Ayarları panelinde kaydedilen) burada da uygula
            _mk_KG = st.session_state.get("_kol_genislik", {})
            _mk_VARSAYILAN = {
                "firma":90,"rakip_firma":90,"yetkili":90,"gsm":100,"sabit":90,"email":90,
                "il":70,"ilce":60,"durum":80,"islem_asamasi":80,
                "beklenen_ciro":70,"gerceklesen_ciro":70,
                "id":40,"Seç":40,"Notlar":50,"Randevu":170,"Analiz":70,
            }
            def _mk_w(k):
                return int(_mk_KG.get(k, _mk_VARSAYILAN.get(k, 100)))

            _mk_col_config = {
                "Seç": st.column_config.CheckboxColumn("Seç", default=False, width=_mk_w("Seç")),
                "id": st.column_config.NumberColumn("ID", disabled=True, width=_mk_w("id")),
                "rakip_firma": st.column_config.TextColumn("Rakip Firma", width=_mk_w("rakip_firma")),
                "firma": st.column_config.TextColumn("Firma", width=_mk_w("firma")),
                "yetkili": st.column_config.TextColumn("Yetkili", width=_mk_w("yetkili")),
                "gsm": st.column_config.TextColumn("GSM", width=_mk_w("gsm")),
                "sabit": st.column_config.TextColumn("Sabit", width=_mk_w("sabit")),
                "email": st.column_config.TextColumn("Email", width=_mk_w("email")),
                "il": st.column_config.TextColumn("İl", width=_mk_w("il")),
                "ilce": st.column_config.TextColumn("İlçe", width=_mk_w("ilce")),
                "durum": st.column_config.TextColumn("Durum", width=_mk_w("durum")),
                "islem_asamasi": st.column_config.TextColumn("Aşama", width=_mk_w("islem_asamasi")),
                "beklenen_ciro": st.column_config.NumberColumn("Hedef ₺", format="%,.0f ₺", width=_mk_w("beklenen_ciro")),
                "gerceklesen_ciro": st.column_config.NumberColumn("Gerçek ₺", format="%,.0f ₺", width=_mk_w("gerceklesen_ciro")),
                "Notlar": st.column_config.NumberColumn("📨 Notlar", disabled=True, width=_mk_w("Notlar")),
                "Randevu": st.column_config.NumberColumn("📅 Randevu", disabled=True, width=_mk_w("Randevu")),
                "Analiz": st.column_config.TextColumn("✅ Analiz", disabled=True, width=_mk_w("Analiz")),
            }

            _mk_edited = st.data_editor(
                _mk_tablo, use_container_width=True, hide_index=True,
                column_config=_mk_col_config, key="mk_editor",
                height=min(600, 80 + 35 * len(_mk_tablo)))

            _mkc1, _mkc2 = st.columns([2,1])
            with _mkc1:
                if st.button("💾 Kaydet", type="primary", use_container_width=True, key="mk_kaydet_btn"):
                    _mk_sb = get_sb_client()
                    _mk_kaydedilen = 0
                    for _, _mkr in _mk_edited.iterrows():
                        _mk_id = int(_mkr["id"])
                        _mk_orig = _mk_tablo[_mk_tablo["id"] == _mk_id].iloc[0]
                        _mk_guncel = {}
                        for _mkk in _mk_kolonlar:
                            if _mkk == "id": continue
                            _yeni_v = _mkr.get(_mkk, "")
                            _eski_v = _mk_orig.get(_mkk, "")
                            if _mkk in ("gsm", "sabit"):
                                # Ekranda gruplu görünüyor ama veritabanına sade rakam yazılır.
                                _yeni_v = "".join(ch for ch in str(_yeni_v or "") if ch.isdigit())
                            if str(_yeni_v) != str(_eski_v):
                                _mk_guncel[_mkk] = _yeni_v
                        if _mk_guncel:
                            try:
                                if _mk_sb:
                                    _mk_sb.table("cari_kartlar").update(_mk_guncel).eq("id", _mk_id).execute()
                                else:
                                    db_update("cari_kartlar", _mk_guncel, "id", _mk_id)
                                _mk_kaydedilen += 1
                            except Exception:
                                pass
                    if _mk_kaydedilen:
                        try: get_cari_listesi.clear()
                        except: pass
                        st.session_state.pop("mk_editor", None)
                        st.toast(f"✅ {_mk_kaydedilen} kayıt güncellendi", icon="✅")
                        st.rerun()
                    else:
                        st.info("Değişiklik yok.")
            with _mkc2:
                _mk_secili = _mk_edited[_mk_edited["Seç"] == True]
                if st.button(f"🗑️ Seçilenleri Sil ({len(_mk_secili)})", use_container_width=True,
                             key="mk_sil_btn", disabled=(len(_mk_secili) == 0)):
                    _mk_sb2 = get_sb_client()
                    _mk_silinen = 0
                    for _mid in _mk_secili["id"].tolist():
                        try:
                            if _mk_sb2:
                                _mk_sb2.table("cari_kartlar").update({"silindi": 1}).eq("id", int(_mid)).execute()
                            else:
                                db_update("cari_kartlar", {"silindi": 1}, "id", int(_mid))
                            _mk_silinen += 1
                        except Exception:
                            pass
                    if _mk_silinen:
                        try: get_cari_listesi.clear()
                        except: pass
                        st.session_state.pop("mk_editor", None)
                        st.toast(f"🗑️ {_mk_silinen} kayıt silindi", icon="🗑️")
                        st.rerun()

elif aktif == "liste":
    sayfa_log("liste")
    st.markdown("""<style>
.block-container { padding-left: 0.6rem !important; padding-right: 0.6rem !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { max-width: 100% !important; }
[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-left: 0.6rem !important; padding-right: 0.6rem !important; }
</style>""", unsafe_allow_html=True)

    # ── KAYDETME SONRASI ONAY BANNER'I — toast kaçırılırsa diye burada da göster ──
    _son_kaydet_msg = st.session_state.pop("_son_kaydet_ozeti", None)
    if _son_kaydet_msg:
        st.success(_son_kaydet_msg, icon="✅")

    # NOT (ÖNEMLİ KURAL): Geçici teşhis/debug panelleri asla önbelleksiz (cache'siz)
    # tam tablo taraması yapıp HER sayfa yenilemesinde (rerun) otomatik ("expanded=True")
    # çalışacak şekilde eklenmez — bu, sayfayı fark edilir şekilde yavaşlatır ve
    # yanıp sönme/kayma hissi verir. Bir önceki "BARSAN/CRN ham sorgu" paneli bu
    # yüzden kaldırıldı. Gerekirse: sadece bir BUTONA basılınca çalışan, sonucu
    # session_state'te tutan, tek seferlik bir kontrol olarak eklenmeli.

    # ── MOBİL KART GÖRÜNÜMÜ ──────────────────────────────────────────────────
    if st.session_state.get("_mobil_mod", False):
        st.markdown("""
<style>
/* Mobil liste sayfası — masaüstü elementleri gizle */
.mw-mob-only { display: block !important; }
.mw-desk-only { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 4px 6px 80px 6px !important; }
/* Kart stilleri */
.mw-firma-card {
  background: white;
  border: 0.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: box-shadow .15s;
}
.mw-firma-card:active { background: #f8fafc; }
.mw-kart-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; }
.mw-kart-adi { font-size: 14px; font-weight: 600; color: #0f172a; }
.mw-kart-badge { font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 500; white-space: nowrap; }
.mw-kart-meta { font-size: 12px; color: #64748b; margin-bottom: 6px; }
.mw-kart-foot { display: flex; justify-content: space-between; align-items: center; border-top: 0.5px solid #f1f5f9; padding-top: 6px; }
.mw-kart-ciro { font-size: 13px; font-weight: 600; color: #0f172a; }
.mw-kart-acts { display: flex; gap: 6px; }
.mw-act-btn { width: 34px; height: 34px; border-radius: 8px; border: 0.5px solid #e2e8f0; background: #f8fafc; display: flex; align-items: center; justify-content: center; font-size: 16px; text-decoration: none; }
.mw-analiz-tag { font-size: 11px; color: #16a34a; background: #dcfce7; padding: 2px 7px; border-radius: 20px; }
/* Alt nav */
#mw-mobile-nav { display: flex !important; }
</style>
""", unsafe_allow_html=True)

        # Veri yükle
        _sb_m = get_sb_client()
        try:
            if _sb_m:
                _res_m = _sb_m.table("cari_kartlar").select("*").neq("silindi",1).order("tarih",desc=True).execute()
                _df_m = pd.DataFrame(_res_m.data) if _res_m.data else pd.DataFrame()
            else:
                raise Exception()
        except:
            _df_m = db_read("cari_kartlar", extra_sql="WHERE silindi=0 OR silindi IS NULL ORDER BY tarih DESC")

        if not _df_m.empty:
            for _tk in ["gsm","sabit"]:
                if _tk in _df_m.columns:
                    _df_m[_tk] = _telefon_temizle(_df_m[_tk])
            # "Gerçekleşen Ciro" — masaüstüyle aynı: kargo kayıtlarından
            # CANLI toplanır, eski sayaç değeri kullanılmaz.
            if "id" in _df_m.columns:
                _kargo_yekun_toplamlari_mob = _tum_musteri_kargo_yekun_toplami()
                _df_m["gerceklesen_ciro"] = _df_m["id"].apply(
                    lambda _rid: _kargo_yekun_toplamlari_mob.get(int(_rid), 0.0) if pd.notna(_rid) else 0.0)

        # Analiz yapılmış firmalar
        _analiz_set = set()
        try:
            if _sb_m:
                _an_r = _sb_m.table("musteri_analiz").select("firma").execute().data or []
                def _nm(s): return str(s or "").strip().upper().replace("İ","I").replace("Ş","S").replace("Ğ","G").replace("Ü","U").replace("Ö","O").replace("Ç","C")
                _analiz_set = set(_nm(x.get("firma","")) for x in _an_r if x.get("firma"))
        except: pass

        # "Rut" — KULLANICI İSTEĞİ (2026-09): elle atanmıyor, o müşterinin
        # hangi İL sütun(lar)ına gönderim bilgisi girildiyse OTOMATİK
        # hesaplanır (masaüstü Cari Liste tablosundaki İL sütunlarıyla aynı
        # kaynak — bkz. _cari_rut_hesapla_otomatik, dosya başında GLOBAL).
        _il_gonderim_matrisi_mob = _il_gonderim_matrisi_yukle()
        if not _df_m.empty:
            _df_m["rut"] = _df_m["id"].apply(lambda _rid: _cari_rut_hesapla_otomatik(_rid, _il_gonderim_matrisi_mob))

        # "Rut" filtresi — masaüstüyle aynı: metin kutusu değil, mevcut Rut
        # kodlarından oluşan SEÇİLEBİLİR liste.
        _mob_rut_kod_seti = set()
        if not _df_m.empty and "rut" in _df_m.columns:
            for _rv in _df_m["rut"].dropna():
                for _parca in str(_rv).split(" - "):
                    _parca = _parca.strip()
                    if _parca:
                        _mob_rut_kod_seti.add(_parca)
        _mob_rut_opts = sorted(_mob_rut_kod_seti)
        _mc1, _mc2, _mc3 = st.columns([2.2, 1.3, 1])
        _mob_ara = _mc1.text_input("🔍 Ara", placeholder="Firma, yetkili, il...", key="mob_ara", label_visibility="collapsed")
        _mob_rut = _mc2.multiselect("🛣️ Rut", _mob_rut_opts, key="mob_rut_filtre", placeholder="🛣️ Rut...", label_visibility="collapsed")
        _mob_durum = _mc3.selectbox("Durum", ["Tümü","Portföy","Özel Müşteri","Randevu","Tekrar Ara","Fiyat Hazırla","Teklif","Pasif"], key="mob_dur", label_visibility="collapsed")

        # Filtrele
        _df_mob = _df_m.copy() if not _df_m.empty else pd.DataFrame()
        if not _df_mob.empty:
            if _mob_ara:
                _mask = (
                    _df_mob.get("firma", pd.Series()).astype(str).str.contains(_mob_ara, case=False, na=False) |
                    _df_mob.get("yetkili", pd.Series()).astype(str).str.contains(_mob_ara, case=False, na=False) |
                    _df_mob.get("il", pd.Series()).astype(str).str.contains(_mob_ara, case=False, na=False)
                )
                _df_mob = _df_mob[_mask]
            if _mob_rut:
                _mob_rut_set = set(_mob_rut)
                _df_mob = _df_mob[_df_mob.get("rut", pd.Series()).astype(str).apply(
                    lambda _rv: bool({p.strip() for p in _rv.split(" - ") if p.strip()} & _mob_rut_set))]
            if _mob_durum != "Tümü":
                if "durum" in _df_mob.columns:
                    _df_mob = _df_mob[_df_mob["durum"].astype(str).str.contains(_mob_durum, case=False, na=False)]

        st.caption(f"{len(_df_mob)} müşteri")
        # NOT: "🛣️ Bir Müşteriye Rut Ata / Değiştir" bölümü kaldırıldı — Rut
        # artık elle atanmıyor, İL sütunlarından otomatik hesaplanıyor.
        # Bir müşterinin Rut'unu değiştirmek için masaüstü Cari Liste
        # tablosundaki ilgili İL sütununu doldur/boşalt.

        # Durum renk & badge
        _DURUM_RENK = {
            "Portföy":         ("#dcfce7","#166534"),
            "Özel Müşteri":    ("#eff6ff","#1d4ed8"),
            "Randevu":         ("#dbeafe","#1e40af"),
            "Tekrar Ara":      ("#fef9c3","#854d0e"),
            "Fiyat Hazırla":   ("#ede9fe","#5b21b6"),
            "Teklif":          ("#fef3c7","#92400e"),
            "Pasif":           ("#f1f5f9","#475569"),
            "Kazanıldı":       ("#dcfce7","#14532d"),
        }

        # Kartları render et
        if not _df_mob.empty:
            for _, _row in _df_mob.iterrows():
                _firma   = str(_row.get("firma","") or "?")
                _yetkili = str(_row.get("yetkili","") or "")
                _gsm     = str(_row.get("gsm","") or "")
                _il      = str(_row.get("il","") or "")
                _ilce    = str(_row.get("ilce","") or "")
                _durum   = str(_row.get("durum","") or "")
                _asama   = str(_row.get("islem_asamasi","") or "")
                _bek     = float(_row.get("beklenen_ciro",0) or 0)
                _ger     = float(_row.get("gerceklesen_ciro",0) or 0)
                _seg     = str(_row.get("segment","") or "")
                _rut     = str(_row.get("rut","") or "")
                _cari_id = _row.get("id","")

                # Segment dot
                _dot = "🟢" if "A" in _seg else ("🔵" if "B" in _seg else ("⚪" if "C" in _seg else ""))
                # Analiz var mı
                def _nrm(s): return str(s or "").strip().upper().replace("İ","I").replace("Ş","S").replace("Ğ","G").replace("Ü","U").replace("Ö","O").replace("Ç","C")
                _analiz_var = _nrm(_firma) in _analiz_set
                # Badge renk
                _bg, _tc = _DURUM_RENK.get(_durum, ("#f1f5f9","#475569"))
                # Telefon link
                _gsm_clean = _gsm.replace(" ","").replace("-","").replace("(","").replace(")","")
                if _gsm_clean and not _gsm_clean.startswith("90"): _gsm_clean = "90" + _gsm_clean.lstrip("0")

                # Kart HTML — değişkenler önceden hesapla
                _meta_html = ""
                if _il:
                    _meta_html += f"📍 {_il}" + (f"/{_ilce}" if _ilce else "")
                if _yetkili and _yetkili not in ["nan","None",""]:
                    _meta_html += f"  👤 {_yetkili}"
                if _asama and _asama not in ["nan","None",""]:
                    _meta_html += f"  🏭 {_asama}"
                if _rut and _rut not in ["nan","None",""]:
                    _meta_html += f"  🛣️ {_rut}"
                _analiz_html = "<span class='mw-analiz-tag'>✅</span>" if _analiz_var else ""
                _tel_html = f"<a class='mw-act-btn' href='tel:{_gsm_clean}'>📞</a>" if _gsm_clean else ""
                _wa_html  = f"<span class='mw-act-btn' style='opacity:0.35;cursor:not-allowed' title='Geçici devre dışı'>💬</span>" if _gsm_clean else ""
                _ciro_str = f"{int(_bek):,}₺ / {int(_ger):,}₺"

                st.markdown(f"""<div class="mw-firma-card">
  <div class="mw-kart-top">
    <div class="mw-kart-adi">{_dot} {_firma}</div>
    <span class="mw-kart-badge" style="background:{_bg};color:{_tc};">{_durum}</span>
  </div>
  <div class="mw-kart-meta">{_meta_html}</div>
  <div class="mw-kart-foot">
    <div>
      <div style="font-size:10px;color:#94a3b8;">Hedef / Gerçek</div>
      <div class="mw-kart-ciro">{_ciro_str}</div>
    </div>
    <div class="mw-kart-acts">{_analiz_html}{_tel_html}{_wa_html}</div>
  </div>
</div>""", unsafe_allow_html=True)

                # Nota git butonu
                if st.button(f"📋 Not / Detay — {_firma[:25]}", key=f"mob_det_{_cari_id}", use_container_width=True):
                    st.session_state["mob_secili_id"] = _cari_id
                    st.session_state["mob_secili_firma"] = _firma
                    st.rerun()
        else:
            st.info("Müşteri bulunamadı.")
        st.stop()
    # ── MASAÜSTÜ — normal liste devam eder ──────────────────────────────────
    # Kolon genişliklerini localStorage'a kaydet ve geri yükle
    st.markdown("""<script>
(function(){
  const STORE_KEY = 'mwcrm_col_widths';
  function saveWidths(){
    try {
      const headers = document.querySelectorAll('[data-testid="stDataEditor"] th');
      if(!headers.length) return;
      const widths = {};
      headers.forEach(th => {
        const label = th.innerText.trim();
        if(label) widths[label] = th.offsetWidth;
      });
      localStorage.setItem(STORE_KEY, JSON.stringify(widths));
    } catch(e){}
  }
  function restoreWidths(){
    try {
      const saved = localStorage.getItem(STORE_KEY);
      if(!saved) return;
      const widths = JSON.parse(saved);
      const headers = document.querySelectorAll('[data-testid="stDataEditor"] th');
      headers.forEach(th => {
        const label = th.innerText.trim();
        if(widths[label]){
          th.style.width = widths[label]+'px';
          th.style.minWidth = widths[label]+'px';
          th.style.maxWidth = widths[label]+'px';
        }
      });
    } catch(e){}
  }
  // Resize observer — genişlik değişince kaydet
  const obs = new MutationObserver(() => {
    restoreWidths();
    setTimeout(saveWidths, 500);
  });
  function init(){
    const editor = document.querySelector('[data-testid="stDataEditor"]');
    if(editor){
      restoreWidths();
      obs.observe(editor, {childList:true, subtree:true, attributes:true});
      editor.addEventListener('mouseup', () => setTimeout(saveWidths, 300));
    } else {
      setTimeout(init, 500);
    }
  }
  setTimeout(init, 1000);
})();
</script>""", unsafe_allow_html=True)
    if st.session_state.get("kayit_mesaj"):
        st.success(st.session_state["kayit_mesaj"])
        st.session_state["kayit_mesaj"] = ""

    # ── VERİ YÜKLE ──────────────────────────────────────────────────────────────
    sb_liste = get_sb_client()
    # NOT: Burada eskiden HER render'da (yani her tek hücre düzenlemesinde bile)
    # get_cari_listesi.clear() ile önbellek zorla temizlenip TÜM müşteri
    # tablosu (3700+ kayıt) yeniden Supabase'den çekiliyordu. Bu, düzenleme
    # yaparken her hücre değişiminde gözle görülür bir "sorgu çalışıyor" gecikmesi
    # ve ekran titremesine sebep oluyordu. Artık önbellek SADECE gerçek bir
    # kayıt/silme/arşivleme işleminden SONRA (ilgili yerlerde zaten çağrılıyor)
    # temizleniyor; salt düzenleme sırasında 60 saniyelik önbellek kullanılıyor.
    df = get_cari_listesi()

    # "Rut" — filtre kutusunun kullanacağı erken hesap. KULLANICI İSTEĞİ
    # (2026-09): elle atanmıyor, hangi İL sütun(lar)ına gönderim bilgisi
    # girildiyse (bkz. _il_gonderim_matrisi_yukle) OTOMATİK hesaplanır.
    _il_gonderim_matrisi_erken = _il_gonderim_matrisi_yukle()
    if not df.empty and "id" in df.columns:
        df["rut"] = df["id"].apply(lambda _rid: _cari_rut_hesapla_otomatik(_rid, _il_gonderim_matrisi_erken))

    # "Gerçekleşen Ciro" — KULLANICI İSTEĞİ (2026-09): artık kargo
    # kayıtlarının kendisinden CANLI toplanır (bkz. _tum_musteri_kargo_yekun_toplami),
    # eski "sayaç" değeri değil — böylece asla gerçek kargo toplamından
    # sapmış/abartılı bir sayı gösterilmez.
    if not df.empty and "id" in df.columns:
        _kargo_yekun_toplamlari_erken = _tum_musteri_kargo_yekun_toplami()
        df["gerceklesen_ciro"] = df["id"].apply(
            lambda _rid: _kargo_yekun_toplamlari_erken.get(int(_rid), 0.0) if pd.notna(_rid) else 0.0)

    # ── Vergi No / Vergi Dairesi / Müşteri Şubesi / Vade / Ödeme — KULLANICI
    # İSTEĞİ (2026-09): cari_kartlar'da GERÇEK sütun DEĞİL (yeni SQL migration
    # yok), Rut ile AYNI desen — kullanici_tercih'te {cari_id: {alan: değer}}.
    _cari_ek_bilgi_erken = _cari_ek_bilgi_yukle()
    if not df.empty and "id" in df.columns:
        # 🚀 SAF PERFORMANS (2026-09, davranış değişmedi, sadece daha hızlı):
        # .apply()+lambda yerine ön-hesaplanmış {id: değer} sözlüğü ile .map()
        # kullanılıyor — 4800 satır × 5 alan için aynı sonucu çok daha hızlı verir.
        _id_str_erken = df["id"].apply(lambda _r: str(int(_r)) if pd.notna(_r) else "")
        for _cek_alan in _CARI_EK_ALAN_LISTESI:
            _cek_map = {k: v.get(_cek_alan, "") for k, v in _cari_ek_bilgi_erken.items()}
            df[_cek_alan] = _id_str_erken.map(_cek_map).fillna("")

    # 🆕 YENİ ÖZELLİK (2026-09, KULLANICI İSTEĞİ): "Hesaplama" — kalıcı bir
    # değeri YOKTUR (Koli/Palet, Teklif Fiyat gibi kayıtlı bir alan değil),
    # SADECE hızlı toplu giriş için HER ZAMAN BOŞ başlayan bir yazı kutusu.
    # Kaydedilince içeriği "_fy_hepsini_yerlestir_ana_tablo"yu tetikler ve
    # sonucu Koli/Palet'e yazılır — kendisi BOŞ kalmaya devam eder.
    if not df.empty:
        df["hesaplama"] = ""

    # ── MÜŞTERİ KODU (MW1, MW2, ...) — KULLANICI İSTEĞİ (2026-09): eski
    # karışık ID'ler yerine kayıt tarihine göre sıralı, boşluksuz "MW1,
    # MW2..." kodu görüntülenir. Gerçek "id" (kargo/not/randevu/il gönderim
    # gibi onlarca yerde kullanılan asıl anahtar) HİÇ DEĞİŞMEZ — sadece bu
    # YENİ kod GÖRÜNTÜLEME/REFERANS için eklenir. Henüz kodu olmayan (yeni
    # eklenmiş) müşterilere otomatik, silinen müşterilerin boşta kalan
    # numarası öncelikli olacak şekilde kod atanır.
    _musteri_kodu_erken = _musteri_kodu_yukle()
    if not df.empty and "id" in df.columns:
        _mk_gecerli_idler = set(str(int(_r)) for _r in df["id"] if pd.notna(_r))
        _mk_degisti = False
        for _mk_id in _mk_gecerli_idler:
            if _mk_id not in _musteri_kodu_erken:
                _musteri_kodu_erken[_mk_id] = _musteri_kodu_sonraki_bul(_musteri_kodu_erken, _mk_gecerli_idler)
                _mk_degisti = True
        if _mk_degisti:
            _musteri_kodu_kaydet(_musteri_kodu_erken)
        df["musteri_kodu"] = df["id"].apply(
            lambda _rid: _musteri_kodu_erken.get(str(int(_rid)), "") if pd.notna(_rid) else "")

    # ── Güncelleme Tarihi ön-hesabı — ÇOKLU TARİH filtre kutusu için burada
    # (filtrelemeden önce) hesaplanmalı. ÖNEMLİ: bir müşterinin sadece "EN SON"
    # tarihine bakılmıyor — o müşteriye ait HER işlemin (her not, her teklif,
    # her mesaj/arama, her kart düzenlemesi, ilk kayıt) kendi tarihi ayrı ayrı
    # toplanıyor. Böylece "8 Temmuz" seçilince, en son işlemi daha sonraki bir
    # tarihte olsa bile 8 Temmuz'da GERÇEKTEN işlem görmüş her müşteri gelir —
    # sadece "en son işlemi tam o gün olan" tek bir müşteri değil. SAATSİZ.
    if "_cari_son_guncelleme" not in st.session_state:
        st.session_state["_cari_son_guncelleme"] = {}
        try:
            _sb_sg_erken = get_sb_client()
            if _sb_sg_erken:
                import json as _sgj_erken
                _r_sg_erken = _sb_sg_erken.table("kullanici_tercih").select("deger").eq(
                    "kullanici","__liste_ui__").eq("anahtar","_cari_son_guncelleme").execute()
                if _r_sg_erken.data:
                    st.session_state["_cari_son_guncelleme"] = _sgj_erken.loads(_r_sg_erken.data[0]["deger"])
        except:
            pass
    _cari_son_guncelleme_erken = st.session_state.get("_cari_son_guncelleme", {})

    @st.cache_data(ttl=60, show_spinner=False)
    def _tum_aktivite_tarihleri_yukle_erken():
        """id_str -> o müşteriye ait TÜM işlem günlerinin kümesi (set of date)."""
        import collections as _colae
        _kume = _colae.defaultdict(set)
        _sb_ae = get_sb_client()
        if not _sb_ae:
            return dict(_kume)

        def _ekle_ae(_mid_ham, _tarih_ham):
            if not _mid_ham or not _tarih_ham:
                return
            _dt = _guncelleme_tarih_parse(_tarih_ham)
            if _dt is None:
                return
            _kume[str(_mid_ham)].add(_dt.date())

        # 1) Notlar/açıklamalar
        try:
            _rae1 = _sb_ae.table("cari_aciklamalar").select("cari_id,created_at").execute()
            for _rw in (_rae1.data or []):
                _ekle_ae(_rw.get("cari_id"), _rw.get("created_at"))
        except Exception:
            pass
        # 2) Teklifler
        try:
            _rae2 = _sb_ae.table("teklifler").select("musteri_id,created_at").execute()
            for _rw in (_rae2.data or []):
                _ekle_ae(_rw.get("musteri_id"), _rw.get("created_at"))
        except Exception:
            pass
        # 3) Mesaj/arama/whatsapp kayıtları
        try:
            _rae3 = _sb_ae.table("islem_kaydi").select("musteri_id,tarih").execute()
            for _rw in (_rae3.data or []):
                _ekle_ae(_rw.get("musteri_id"), _rw.get("tarih"))
        except Exception:
            pass
        return {k: v for k, v in _kume.items()}

    _tum_aktivite_erken = {}
    try:
        _tum_aktivite_erken = _tum_aktivite_tarihleri_yukle_erken()
    except Exception:
        _tum_aktivite_erken = {}

    # id_str -> {date, date, ...} — aktivite günleri + cari kartı düzenleme
    # günleri + ilk kayıt günü, HEPSİ BİRDEN (tek bir "en son" değil)
    _id_tum_gunler = {}
    if not df.empty and "id" in df.columns:
        for _gidx, _grow in df.iterrows():
            try:
                _grid = str(int(_grow["id"]))
            except Exception:
                continue
            _gunler = set(_tum_aktivite_erken.get(_grid, set()))
            _sg_ham = _cari_son_guncelleme_erken.get(_grid)
            if _sg_ham:
                _sg_dt = _guncelleme_tarih_parse(_sg_ham)
                if _sg_dt:
                    _gunler.add(_sg_dt.date())
            _gr_ilk = _grow.get("tarih") or _grow.get("created_at")
            if _gr_ilk:
                _ilk_dt = _guncelleme_tarih_parse(str(_gr_ilk))
                if _ilk_dt:
                    _gunler.add(_ilk_dt.date())
            if _gunler:
                _id_tum_gunler[_grid] = _gunler

    # Filtre kutusu seçenekleri — sistemde görülen TÜM tarihler, en yeni en üstte
    _guncelleme_tarih_opts_set = set()
    for _gset in _id_tum_gunler.values():
        _guncelleme_tarih_opts_set.update(_gset)
    _guncelleme_tarih_opts = sorted(_guncelleme_tarih_opts_set, reverse=True)
    _guncelleme_tarih_opts_str = [d.strftime("%d.%m.%Y") for d in _guncelleme_tarih_opts]
    # id_str -> {"08.07.2026","12.08.2026",...} — string haline çevrilmiş tam küme
    _id_tum_gunler_str = {k: {d.strftime("%d.%m.%Y") for d in v} for k, v in _id_tum_gunler.items()}

    # NOT: "tarih" (İşlem Tarih) sütunu tablonun içinde DÜZENLENEBİLİR bir alan.
    # Eskiden her rerun'da canlı "tarih" değerine göre yeniden sıralanıyordu —
    # yani bir müşterinin İşlem Tarihini değiştirip kaydetmek o müşterinin
    # satırını kaydırıyordu. Streamlit'te "Seç" işareti satır POZİSYONUNA göre
    # tutulduğu için, sıra kayınca işaret başka bir müşteride kalmış gibi
    # görünüyordu. Çözüm: sıralamayı sadece müşteri KÜMESİ değiştiğinde
    # (yeni/silinen kayıt) yeniden hesapla, aynı kümede kalan bir düzenleme +
    # kayıt sırasında sırayı SABİT tut.
    if not df.empty and "tarih" in df.columns and "id" in df.columns:
        _cl_id_kume = tuple(sorted(int(x) for x in df["id"].tolist()))
        if st.session_state.get("_cl_sira_id_kume") != _cl_id_kume or not st.session_state.get("_cl_sabit_sira"):
            _cl_sirali_idler = df.sort_values("tarih", ascending=False)["id"].tolist()
            st.session_state["_cl_sabit_sira"] = _cl_sirali_idler
            st.session_state["_cl_sira_id_kume"] = _cl_id_kume
        else:
            _cl_sirali_idler = st.session_state["_cl_sabit_sira"]
        _cl_sira_map = {v: i for i, v in enumerate(_cl_sirali_idler)}
        df["_cl_sira_key"] = df["id"].map(_cl_sira_map).fillna(len(_cl_sirali_idler))
        df = df.sort_values("_cl_sira_key").drop(columns=["_cl_sira_key"]).reset_index(drop=True)

    if not df.empty:
        for _tk in ["gsm","sabit"]:
            if _tk in df.columns:
                df[_tk] = _telefon_temizle(df[_tk])

    # ── ATAMA FİLTRESİ — admin hepsini görür, kullanıcı sadece kendine atananları ──
    df = _atama_filtresi_uygula(df)

    for _kol in ["aciklama","adres","notlar"]:
        if _kol not in df.columns: df[_kol] = ""
    df["aciklama"] = df["aciklama"].fillna("").astype(str)
    df["aciklama"] = df["aciklama"].replace("nan","")

    # Supabase'de notlar kolonu yoksa ekle
    if sb_liste:
        try:
            _test = sb_liste.table("cari_kartlar").select("aciklama").limit(1).execute()
        except:
            pass  # Kolon yoksa update sırasında hata alırız, onu da yakalayacağız

    # ── ASAMA & DURUM LİSTELERİ — sistem_tanimlar tablosundan ──────────────────
    tum_asama_opts = _tanimlar_yukle("asama")
    tum_durum_opts = _tanimlar_yukle("durum")
    # SONUÇ rozetlerinden biri (Devam Ediyor) tanımlar tablosunda eksik olsa bile
    # filtre kutusunda seçilebilir olsun diye garanti ediyoruz
    if "Devam Ediyor" not in tum_asama_opts:
        tum_asama_opts.append("Devam Ediyor")
    # NOT: df'de olan ama tanımlardan silinmiş durum/aşamalar eklenmez
    # Sadece tanımlar tablosundakiler gösterilir

    # ── ÜST METRİKLER — TÜM DURUM VE AŞAMALAR ──────────────────────────────
    # Durum emoji haritası
    _DURUM_EMOJI = {
        "Toplam":       "📊",
        "Portföy":      "💼",
        "Hedef":        "🎯",
        "Aktif":        "✅",
        "Deneme":       "🧪",
        "Takip":        "👁️",
        "Tekrar Ara":   "📞",
        "Pasif":        "⚫",
    }
    # Aşama emoji haritası
    _ASAMA_EMOJI = {
                "Teklif":           "📄",
        "Deneme":           "🧪",
        "Sözleşme":         "📝",
        "Kazanıldı":        "🏆",
        "Kaybedildi":       "❌",
                "Gereksizler":      "🗑️",
    }

    # Durum butonu sırası — hafızada tut
    # ── DURUM & AŞAMA BUTONLARI ───────────────────────────────────────────────
    def _rapor_satir(veri_listesi, sira_key, gizli_key, fil_key, emoji_map, satir_label, d_adlar=None):
        """Genel buton satırı: sıralama + gizle/göster"""
        _veri_dict = {ad: sayi for ad, sayi in veri_listesi}
        _adlar = [ad for ad, _ in veri_listesi]

        def _tercih_yukle(anahtar, varsayilan):
            """DB'den tercih yükle"""
            try:
                _sb = get_sb_client()
                if _sb:
                    _r = _sb.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar",anahtar).execute()
                    if _r.data:
                        import json as _tj
                        return _tj.loads(_r.data[0]["deger"])
            except: pass
            return varsayilan

        def _tercih_kaydet(anahtar, deger):
            """DB'ye tercih kaydet"""
            try:
                _sb = get_sb_client()
                if _sb:
                    import json as _tj
                    _sb.table("kullanici_tercih").upsert({
                        "kullanici":"__liste_ui__","anahtar":anahtar,
                        "deger":_tj.dumps(deger, ensure_ascii=False)
                    }, on_conflict="kullanici,anahtar").execute()
            except: pass

        # Sıra — session_state'te yoksa DB'den yükle
        if sira_key not in st.session_state:
            st.session_state[sira_key] = _tercih_yukle(sira_key, _adlar.copy())
        _sira = st.session_state[sira_key]
        for _a in _adlar:
            if _a not in _sira: _sira.append(_a)
        _sira = [x for x in _sira if x in _adlar]
        st.session_state[sira_key] = _sira

        # Gizli — session_state'te yoksa DB'den yükle
        if gizli_key not in st.session_state:
            st.session_state[gizli_key] = _tercih_yukle(gizli_key, [])
        _gizli_list = st.session_state.get(gizli_key, [])
        if not isinstance(_gizli_list, list): _gizli_list = list(_gizli_list)
        _gizli = set(_gizli_list)

        # Düzenleme modu
        _mode = st.session_state.get(f"_{sira_key}_mode", False)

        if _mode:
            # Düzenleme modu — başında ✓ sonra her buton
            st.caption("← → taşı · 🙈 gizle · ✓ bitir")
            _tum = _sira.copy()
            _edit_cols = st.columns([0.4] + [1]*len(_tum))
            # İlk kolona ✓ butonu
            if _edit_cols[0].button("✓", key=f"{sira_key}_bitti", use_container_width=True):
                st.session_state[f"_{sira_key}_mode"] = False; st.rerun()
            for i, _ad in enumerate(_tum):
                _sayi = _veri_dict.get(_ad, 0)
                _em = emoji_map.get(_ad, "🔹")
                _gizli_mi = _ad in _gizli
                with _edit_cols[i+1]:
                    _r1, _r2, _r3 = st.columns(3)
                    if _r1.button("←", key=f"{sira_key}_sol_{i}", use_container_width=True):
                        if i > 0:
                            _sira[i], _sira[i-1] = _sira[i-1], _sira[i]
                            st.session_state[sira_key] = _sira
                            _tercih_kaydet(sira_key, _sira); st.rerun()
                    if _r2.button("→", key=f"{sira_key}_sag_{i}", use_container_width=True):
                        if i < len(_tum)-1:
                            _sira[i], _sira[i+1] = _sira[i+1], _sira[i]
                            st.session_state[sira_key] = _sira
                            _tercih_kaydet(sira_key, _sira); st.rerun()
                    if _r3.button("🙈" if not _gizli_mi else "👁", key=f"{sira_key}_giz_{i}", use_container_width=True):
                        if _gizli_mi: _gizli.discard(_ad)
                        else: _gizli.add(_ad)
                        st.session_state[gizli_key] = list(_gizli)
                        _tercih_kaydet(gizli_key, list(_gizli)); st.rerun()
                    st.button(f"{_em} {_ad}\n{_sayi}", key=f"{sira_key}_prev_{i}",
                              use_container_width=True, disabled=True)
                    if _gizli_mi:
                        st.markdown("<div style='text-align:center;font-size:10px;color:#94a3b8'>gizli</div>", unsafe_allow_html=True)
        else:
            # Normal mod — sadece görünen butonlar + başında ⚙️
            _gorunen = [(_ad, _veri_dict.get(_ad, 0)) for _ad in _sira if _ad not in _gizli]
            if _gorunen:
                _btn_cols = st.columns([0.4] + [1]*len(_gorunen))
                if _btn_cols[0].button("⚙️", key=f"{sira_key}_toggle2", use_container_width=True):
                    st.session_state[f"_{sira_key}_mode"] = True; st.rerun()
                for i, (_ad, _sayi) in enumerate(_gorunen):
                    _em = emoji_map.get(_ad, "🔹")
                    if _btn_cols[i+1].button(f"{_em} {_ad}\n{_sayi}", key=f"{sira_key}_btn_{i}", use_container_width=True):
                        if fil_key == "durum":
                            st.session_state["_cl_fil_durum_multi"] = [] if _ad == "Toplam" else [_ad]
                        elif fil_key == "asama":
                            st.session_state["_cl_fil_asama_multi"] = [_ad]
                        else:  # tek — durum+asama birleşik
                            if _ad == "Toplam":
                                st.session_state["_toplam_aktif"] = True
                                for _fk in ["_cl_fil_durum_multi","_cl_fil_asama_multi",
                                            "_cl_fil_il_multi","_cl_fil_ilce_multi",
                                            "_cl_fil_temsilci_multi","_cl_sec_kart"]:
                                    if _fk in st.session_state: del st.session_state[_fk]
                                st.session_state["_filtre_reset_sayac"] = st.session_state.get("_filtre_reset_sayac", 0) + 1
                            elif d_adlar and _ad in d_adlar:
                                st.session_state["_toplam_aktif"] = False
                                st.session_state["_cl_fil_durum_multi"] = [_ad]
                                st.session_state["_cl_fil_asama_multi"] = []
                            else:
                                st.session_state["_toplam_aktif"] = False
                                st.session_state["_cl_fil_asama_multi"] = [_ad]
                                st.session_state["_cl_fil_durum_multi"] = []
                        st.rerun()

    # Toplam basınca tüm filtreleri sıfırla
    if st.session_state.get("_tek_sec_tek") == "Toplam" or st.session_state.get("_tek_fil") == "Toplam":
        for _fk in ["_cl_fil_asama_multi","_cl_fil_durum_multi","_cl_sec_kart",
                    "_cl_fil_il_multi","_cl_fil_ilce_multi","_tek_sec_tek"]:
            if _fk in st.session_state: del st.session_state[_fk]
        st.session_state["_tek_fil"] = None
        st.rerun()

    # ── TEK SATIR: Durum + Aşama birleşik ───────────────────────────────────
    _d_veri = [("Toplam", len(df))]
    for _dn in tum_durum_opts:
        if str(_dn).upper() in ["NONE","NAN",""]: continue
        _dc = len(df[df["durum"]==_dn]) if "durum" in df.columns else 0
        _d_veri.append((_dn, _dc))
    _a_veri = [(a, len(df[df["islem_asamasi"]==a]) if "islem_asamasi" in df.columns else 0) for a in tum_asama_opts if str(a).upper() not in ["NONE","NAN",""]] if tum_asama_opts else []
    _tum_veri = _d_veri + _a_veri
    _d_adlar = {x[0] for x in _d_veri}

    # ── AŞAMA GRUPLARI — gerçek aşama adlarına göre ──────────────────────────
    # ── AŞAMA GRUPLARI — Supabase'deki GERÇEK değerler ──────────────────────
    # islem_asamasi kolonundaki tam değerler:
    # Arama, Tekrar Ara, E-Mail, Randevu, Teklif, Fiyat Hazırla, Deneme, Sözleşme, TAKİP
    # Kazanıldı, Kaybedildi, Devam Ediyor

    # AŞAMA grubu — iletişim aşamaları
    _grp1_asama = [a for a in tum_asama_opts if a in ["Arama","Tekrar Ara","E-Mail","Mail","Mesaj","Whatsapp Mesaj"]]

    # 1. AŞAMA — Randevu
    _grp2_asama = [a for a in tum_asama_opts if a in ["Randevu"]]

    # 2. AŞAMA — Teklif
    # NOT: tanımlarda aynı isim (büyük/küçük harf farklı vb.) birden fazla kez
    # kayıtlıysa çift sayıma yol açabiliyordu — normalize edilmiş isme göre
    # TEKİLLEŞTİRİLİYOR, "Teklif" sadece BİR kutu olarak sayılır.
    _grp3_asama_ham = [a for a in tum_asama_opts if a in ["Teklif"]]
    _grp3_asama = list(dict.fromkeys(_grp3_asama_ham))  # sırayı koruyarak tekilleştir

    # 3. AŞAMA — Deneme, TAKİP, Sözleşme, Fiyat Hazırla (aynı tekilleştirme)
    _grp4_asama_ham = [a for a in tum_asama_opts if a in ["Deneme","TAKİP","Sözleşme","Fiyat Hazırla"]]
    _grp4_asama = list(dict.fromkeys(_grp4_asama_ham))

    # SONUÇ
    _grp5_asama = [a for a in tum_asama_opts if a in ["Kazanıldı","Kaybedildi","Devam Ediyor"]]
    if "Devam Ediyor" not in _grp5_asama: _grp5_asama.append("Devam Ediyor")

    _tum_grp = set(_grp1_asama+_grp2_asama+_grp3_asama+_grp4_asama+_grp5_asama)
    # İlk Temas = Aşamasız sayılır — gruplara dahil edilmez
    # Diğer grubu YOK
    _tum_grp = set(_grp1_asama+_grp2_asama+_grp3_asama+_grp4_asama+_grp5_asama)


    def _asama_sayi(ad):
        if "islem_asamasi" not in df.columns: return 0
        return len(df[df["islem_asamasi"]==ad])

    def _durum_sayi(ad):
        if ad == "Toplam": return len(df)
        if "durum" not in df.columns: return 0
        return len(df[df["durum"]==ad])

    def _asamasiz_sayi():
        if "islem_asamasi" not in df.columns: return 0
        _tum_asama = [a for grp in [_grp1_asama,_grp2_asama,_grp3_asama,_grp4_asama,_grp5_asama] for a in grp]
        return len(df[~df["islem_asamasi"].isin(_tum_asama) | df["islem_asamasi"].isna()])

    _grp1_toplam = sum(_asama_sayi(a) for a in _grp1_asama)
    _grp2_toplam = sum(_asama_sayi(a) for a in _grp2_asama)
    _grp3_toplam = sum(_asama_sayi(a) for a in _grp3_asama)
    _grp4_toplam = sum(_asama_sayi(a) for a in _grp4_asama)
    _grp5_toplam = sum(_asama_sayi(a) for a in _grp5_asama)

    # ── HTML RAPOR SATIRI ─────────────────────────────────────────────────────
    import json as _rjson
    _aktif_fil_durum = st.session_state.get("_cl_fil_durum_multi", [])
    _aktif_fil_asama = st.session_state.get("_cl_fil_asama_multi", [])
    _toplam_aktif_flag = st.session_state.get("_toplam_aktif", False)
    _grp_gizli = set(st.session_state.get("_rbar_grp_gizli", []))
    _grp_sira_def = ["genel","iletisim","asama1","asama2","asama3","sonuc"]
    _grp_sira = list(st.session_state.get("_rbar_grp_sira", _grp_sira_def.copy()))
    for _gs in _grp_sira_def:
        if _gs not in _grp_sira: _grp_sira.append(_gs)
    _ayar_modu = st.session_state.get("_rbar_ayar_modu", False)

    def _asama_ikon(a):
        _m = {"arama":"📞","tekrar ara":"📲","mesaj":"💬","mail":"📧","e-mail":"📧",
              "whatsapp":"💬","takip":"📌","randevu":"📅","ilk temas":"👋",
              "teklif":"📄","fiyat hazırla":"💰","fiyat":"💰","deneme":"🧪",
              "sözleşme":"📝","devam ediyor":"⏳","kazanıldı":"🏆","kazanildi":"🏆",
              "kaybedildi":"❌","negatif":"👎"}
        for k,v in _m.items():
            if k in a.lower(): return v
        return "🔹"

    def _durum_ikon(d):
        return {"Portföy":"📦","Özel Müşteri":"⭐","Aşamasız":"📋","Toplam":"📊"}.get(d,"🔹")

    def _asama_norm(s):
        """Büyük/küçük harf ve Türkçe karakter farkını yok sayarak karşılaştırma için normalize eder"""
        return (str(s or "").strip().upper()
                .replace("İ","I").replace("Ş","S").replace("Ğ","G")
                .replace("Ü","U").replace("Ö","O").replace("Ç","C"))

    def _asama_sayi(ad):
        """islem_asamasi kolonundan say — AŞAMA grubu (Arama vs.)"""
        if "islem_asamasi" not in df.columns: return 0
        _ad_n = _asama_norm(ad)
        return len(df[df["islem_asamasi"].apply(_asama_norm) == _ad_n])

    def _kolon_sayi(kolon, ad):
        """Belirtilen kolonda değeri say (büyük/küçük harf farkı yok sayılır)"""
        if kolon not in df.columns: return 0
        _ad_n = _asama_norm(ad)
        return len(df[df[kolon].apply(_asama_norm) == _ad_n])

    def _durum_sayi(ad):
        if ad == "Toplam": return len(df)
        if "durum" not in df.columns: return 0
        return len(df[df["durum"]==ad])

    def _asamasiz_sayi():
        if df.empty: return 0
        _mask = pd.Series([True]*len(df), index=df.index)
        for _k in ["islem_asamasi","asama1","asama2","asama3"]:
            if _k in df.columns:
                _mask = _mask & (df[_k].isna() | df[_k].astype(str).str.strip().isin(["","None","nan"]))
        return int(_mask.sum())

    # grp1 = islem_asamasi (Arama, Tekrar Ara, E-Mail)
    _grp1_toplam = sum(_asama_sayi(a) for a in _grp1_asama)
    # grp2 = asama1 (Randevu)
    _grp2_toplam = sum(_kolon_sayi("asama1", a) for a in _grp2_asama)
    # grp3 = asama2 (Teklif)
    _grp3_toplam = sum(_kolon_sayi("asama2", a) for a in _grp3_asama)
    # grp4 = asama3 (Takip, Fiyat Hazırla, Deneme, Sözleşme)
    _grp4_toplam = sum(_kolon_sayi("asama3", a) for a in _grp4_asama)
    # grp5 = sonuc (Kazanıldı, Kaybedildi, Devam Ediyor)
    _grp5_toplam = sum(_kolon_sayi("sonuc", a) for a in _grp5_asama)

    # Genel grup
    _genel_items = [
        ("📊","Toplam", len(df), "toplam", _toplam_aktif_flag),
        ("📦","Portföy", _durum_sayi("Portföy"), "durum_Portföy", "Portföy" in _aktif_fil_durum),
        ("⭐","Özel Müşteri", _durum_sayi("Özel Müşteri"), "durum_Özel Müşteri", "Özel Müşteri" in _aktif_fil_durum),
        ("📋","Aşamasız", _asamasiz_sayi(), "asamasiz", st.session_state.get("_asamasiz_aktif",False)),
    ]
    for _dn in tum_durum_opts:
        if str(_dn).upper() in ["NONE","NAN",""] or _dn in ["Portföy","Özel Müşteri"]: continue
        _dn_sayi = _durum_sayi(_dn)
        if _dn_sayi <= 0: continue  # 0 kayıtlı durum tipleri üst raporda gösterilmez
        _genel_items.append((_durum_ikon(_dn), _dn, _dn_sayi, f"durum_{_dn}", _dn in _aktif_fil_durum))

    # ── Gerçek Mesaj sayısı — islem_kaydi tablosundan (WhatsApp/Email gönderim
    # kayıtları) + Cari Liste'de MANUEL yazılan override değerleri. Cari
    # Liste'de görünen "💬 N" değerleriyle BİREBİR aynı toplamı versin diye
    # override'lar da dahil ediliyor (sadece gerçek kayıt sayısı değil).
    @st.cache_data(ttl=60, show_spinner=False)
    def _rbar_mesaj_toplam_yukle():
        _toplam = 0
        try:
            _sb_rbm = get_sb_client()
            if not _sb_rbm:
                return 0
            # 1) Her müşterinin GERÇEK mesaj sayısı (islem_kaydi'den)
            _r_rbm = _sb_rbm.table("islem_kaydi").select("musteri_id,islem_turu").in_(
                "islem_turu", ["WhatsApp Teklif", "Email Teklif"]).execute()
            import collections as _rbmcol
            _gercek_sayac = _rbmcol.Counter([str(r.get("musteri_id","")) for r in (_r_rbm.data or [])])
            # 2) Manuel override'lar (Cari Liste'de elle yazılmış değerler)
            _override_map = {}
            try:
                _r_rbov = _sb_rbm.table("kullanici_tercih").select("deger").eq(
                    "kullanici","__liste_ui__").eq("anahtar","_mesaj_manuel_override").execute()
                if _r_rbov.data:
                    import json as _rbovj
                    _override_map = _rbovj.loads(_r_rbov.data[0]["deger"])
            except Exception:
                pass
            # 3) Sistemdeki TÜM müşteri id'leri üzerinden — override varsa onu,
            # yoksa gerçek sayıyı topla (Cari Liste'de gösterilenle aynı mantık)
            _tum_idler = set(_gercek_sayac.keys()) | set(_override_map.keys())
            for _mid in _tum_idler:
                if _mid in _override_map:
                    try: _toplam += int("".join(ch for ch in str(_override_map[_mid]) if ch.isdigit()) or 0)
                    except Exception: pass
                else:
                    _toplam += _gercek_sayac.get(_mid, 0)
        except Exception:
            return 0
        return _toplam
    _mesaj_gercek_toplam = _rbar_mesaj_toplam_yukle()

    @st.cache_data(ttl=60, show_spinner=False)
    def _rbar_mesaj_id_seti_yukle():
        """'💬 Mesaj' kutusuna tıklanınca filtrelemek için — mesaj toplamıyla
        AYNI mantık (gerçek islem_kaydi + manuel override), ama toplam yerine
        hangi müşteri id'lerinin dahil olduğunu (id seti) döndürür."""
        try:
            _sb_rbm2 = get_sb_client()
            if not _sb_rbm2:
                return set()
            _r_rbm2 = _sb_rbm2.table("islem_kaydi").select("musteri_id,islem_turu").in_(
                "islem_turu", ["WhatsApp Teklif", "Email Teklif"]).execute()
            _gercek_idler = {str(r.get("musteri_id","")) for r in (_r_rbm2.data or []) if r.get("musteri_id")}
            _override_idler = set()
            try:
                _r_rbov2 = _sb_rbm2.table("kullanici_tercih").select("deger").eq(
                    "kullanici","__liste_ui__").eq("anahtar","_mesaj_manuel_override").execute()
                if _r_rbov2.data:
                    import json as _rbovj2
                    _override_map2 = _rbovj2.loads(_r_rbov2.data[0]["deger"])
                    _override_idler = set(_override_map2.keys())
            except Exception:
                pass
            return _gercek_idler | _override_idler
        except Exception:
            return set()


    # ── "2. AŞAMA — Teklif" sayısı — Cari Liste'deki "🧾 Teklif" kolonunda
    # görünen TÜM sayıların TOPLAMI (tekil firma sayısı DEĞİL). Bir firmanın
    # 4 teklifi varsa 4 olarak, 2 teklifi varsa 2 olarak sayılır, hepsi
    # toplanır. Kaynak: gerçek teklifler tablosu + manuel override (hangisi
    # varsa o kullanılır — Cari Liste'de gösterilenle birebir aynı mantık).
    # ÖNEMLİ: sadece AKTİF (silinmemiş, Cari Liste'de görünen) müşterilerle
    # sınırlanır — aksi halde silinmiş/eski müşterilere ait yetim teklif
    # kayıtları da toplama karışıp sayıyı şişiriyordu (232 gibi yanlış sayı).
    _aktif_id_seti = set(str(int(x)) for x in df["id"].dropna().tolist()) if not df.empty and "id" in df.columns else set()

    @st.cache_data(ttl=60, show_spinner=False)
    def _rbar_teklif_toplam_yukle(_aktif_idler):
        # ID'leri normalize eden yardımcı — bazı kayıtlarda musteri_id "123" yerine
        # "123.0" gibi ondalıklı/farklı biçimde saklanmış olabilir; bu farklar
        # eşleşmeyi kaçırıp gerçek teklifleri toplamdan düşürüyordu (rapor düşük
        # çıkıyordu). Her ID'yi aynı sade tam sayı metnine çeviriyoruz.
        def _id_norm_f(_v):
            _s = str(_v).strip()
            try:
                return str(int(float(_s)))
            except Exception:
                return _s
        _toplam = 0
        try:
            _sb_rbf = get_sb_client()
            if not _sb_rbf:
                return 0
            _r_rbf = _sb_rbf.table("teklifler").select("musteri_id").execute()
            import collections as _rbfcol
            _gercek_sayac_f = _rbfcol.Counter([_id_norm_f(r.get("musteri_id","")) for r in (_r_rbf.data or [])])
            _override_map_f_ham = {}
            try:
                _r_rbfov = _sb_rbf.table("kullanici_tercih").select("deger").eq(
                    "kullanici","__liste_ui__").eq("anahtar","_teklif_manuel_override").execute()
                if _r_rbfov.data:
                    import json as _rbfovj
                    _override_map_f_ham = _rbfovj.loads(_r_rbfov.data[0]["deger"])
            except Exception:
                pass
            _override_map_f = {_id_norm_f(k): v for k, v in _override_map_f_ham.items()}
            _aktif_idler_norm = set(_id_norm_f(x) for x in _aktif_idler)
            _tum_idler_f = (set(_gercek_sayac_f.keys()) | set(_override_map_f.keys())) & _aktif_idler_norm
            for _mid in _tum_idler_f:
                if _mid in _override_map_f:
                    try: _toplam += int("".join(ch for ch in str(_override_map_f[_mid]) if ch.isdigit()) or 0)
                    except Exception: pass
                else:
                    _toplam += _gercek_sayac_f.get(_mid, 0)
        except Exception:
            return 0
        return _toplam
    _teklif_firma_sayisi = _rbar_teklif_toplam_yukle(frozenset(_aktif_id_seti))

    # "Tekrar Ara" ve aşama-bazlı "Mesaj" kutuları kullanıcı isteğiyle KALDIRILDI —
    # NOT: bu sadece görünümden kaldırma; _grp1_asama'nın kendisine dokunulmadı,
    # çünkü o değişken "Aşamasız" hesabında da kullanılıyor (o kayıtlar hâlâ
    # aşamalı sayılmaya devam etsin, "aşamasız"a düşmesinler diye).
    _grp1_asama_goster = [a for a in _grp1_asama if a not in ["Tekrar Ara", "Mesaj"]]
    _mesaj_gercek_aktif_flag = st.session_state.get("_mesaj_gercek_aktif", False)

    _grp_data = {
        "genel":    ("📊","GENEL",    None, _genel_items),
        "genel":    ("📊","GENEL",    None, _genel_items),
        "iletisim": ("🤝","İlk Temas",    None, [((_asama_ikon(a),a,_asama_sayi(a),f"asama_{a}",a in _aktif_fil_asama)) for a in _grp1_asama_goster] + [("💬","Mesaj",_mesaj_gercek_toplam,"mesaj_gercek",_mesaj_gercek_aktif_flag)]),
        "asama1":   ("📅","1. AŞAMA", None, [((_asama_ikon(a),a,_kolon_sayi("asama1",a),f"asama1_{a}",False)) for a in _grp2_asama]),
        "asama2":   ("📄","2. AŞAMA", None, [((_asama_ikon(a),a,_kolon_sayi("asama2",a),f"asama2_{a}",False)) for a in _grp3_asama]),
        "asama3":   ("🧪","3. AŞAMA", None, [((_asama_ikon(a),a,_kolon_sayi("asama3",a),f"asama3_{a}",False)) for a in _grp4_asama]),
        "sonuc":    ("🏆","SONUÇ",    None, [((_asama_ikon(a),a,_kolon_sayi("sonuc",a),f"sonuc_{a}",False)) for a in _grp5_asama]),
    }
    # HTML oluştur - 2 satırlı tablo
    # ── Rapor barı SABİT %100 genişlikte kalır, kendi başına kaymaz/kaydırılmaz.
    # Cari Liste tablosu, kendi ayrı kolon-genişliği formülüyle (aşağıda _w())
    # buna uymaya çalışır; rapor barı bunun için değişken hale getirilmez.
    _html = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">'
    _html += '<div style="overflow-x:hidden;margin-bottom:4px;"><table style="border-collapse:separate;border-spacing:0;font-family:inherit;font-size:12px;width:100%;">'

    # 1. SATIR — grup başlıkları
    _html += '<thead><tr>'
    _ilk = True
    for _gid in _grp_sira:
        if _gid not in _grp_data or _gid in _grp_gizli: continue
        _ikon,_lbl,_top,_items = _grp_data[_gid]
        if not _items: continue
        _span = len(_items)
        _top_txt = f" {_top}" if _top is not None else ""
        # Grup arası boşluk
        _border_l = "border-left:2px solid #cbd5e1;" if not _ilk else ""
        _ilk = False
        if _ayar_modu:
            _idx = _grp_sira.index(_gid)
            _n = len([g for g in _grp_sira if g in _grp_data and _grp_data[g][3] and g not in _grp_gizli])
            _sol = "opacity:.3;" if _idx==0 else "cursor:pointer;"
            _sag = "opacity:.3;" if _idx>=_n-1 else "cursor:pointer;"
            _h  = f'<th colspan="{_span}" style="border:0.5px solid #e2e8f0;{_border_l}padding:0;background:#fef9c3;text-align:center;">'
            _h += f'<div style="display:flex;align-items:center;justify-content:space-between;padding:2px 4px;">'
            _h += f'<span onclick="gs(\'{_gid}\',\'l\')" style="font-size:10px;{_sol}">◀</span>'
            _h += f'<b style="font-size:10px;color:#374151;">{_ikon} {_lbl}{_top_txt}</b>'
            _h += f'<span onclick="gs(\'{_gid}\',\'r\')" style="font-size:10px;{_sag}">▶</span>'
            _h += f'<span onclick="gg(\'{_gid}\')" style="font-size:11px;cursor:pointer;">🙈</span>'
            _h += '</div></th>'
        else:
            _h = f'<th colspan="{_span}" style="border:0.5px solid #e2e8f0;{_border_l}padding:4px 10px;background:#f8fafc;text-align:center;font-size:12px;font-weight:700;color:#374151;white-space:nowrap;">{_ikon} {_lbl}{_top_txt}</th>'
        _html += _h

    # Gizli gruplar için ayar modunda göster
    if _ayar_modu:
        for _gid in _grp_sira:
            if _gid in _grp_gizli and _gid in _grp_data:
                _ikon,_lbl,_top,_items = _grp_data[_gid]
                _html += "<th onclick=\"gg('" + _gid + "')\" style=\"border:0.5px solid #e2e8f0;padding:3px 5px;background:#fee2e2;cursor:pointer;font-size:9px;white-space:nowrap;\">👁 " + _lbl + "</th>"

    _cl_view2 = st.session_state.get("_cl_view","liste")
    _gear_bg = "#fef9c3" if _ayar_modu else "#f8fafc"
    _html += '</tr></thead>'

    # 2. SATIR — sayılar
    _html += '<tbody><tr>'
    _ilk2 = True
    for _gid in _grp_sira:
        if _gid not in _grp_data or _gid in _grp_gizli: continue
        _ikon,_lbl,_top,_items = _grp_data[_gid]
        if not _items: continue
        _grp_ilk = True
        for _ic, _ad, _sayi, _key, _aktif in _items:
            _bg = "background:#dbeafe;" if _aktif else "background:#fff;"
            _tc = "color:#1d4ed8;font-weight:700;" if _aktif else "color:#0f172a;"
            _border_l2 = ("border-left:2px solid #cbd5e1;" if not _ilk2 and _grp_ilk else "")
            _td_onclick = f"sf('{_key}')"
            _html += f'<td onclick="{_td_onclick}" style="border:0.5px solid #f1f5f9;{_border_l2}padding:4px 7px;text-align:center;cursor:pointer;white-space:nowrap;{_bg}vertical-align:middle;min-width:50px;">'
            _html += f'<div style="font-size:18px;line-height:1;margin-bottom:4px;">{_ic}</div>'
            _html += f'<div style="font-size:14px;font-weight:600;{_tc};line-height:1;">{_sayi}</div>'
            _html += f'<div style="font-size:14px;font-weight:500;color:#374151;line-height:1;">{_ad}</div>'
            _html += '</td>'
            _grp_ilk = False
            _ilk2 = False

    _cl_view2 = st.session_state.get("_cl_view","liste")
    _html += '</tr></tbody></table></div>'
    import json as _rjson2
    _html += f"""<script>
var _s={_rjson2.dumps(_grp_sira)};
function sf(k){{
  if(k==='_ayar_toggle'){{
    var u=new URL(window.parent.location.href);
    u.searchParams.set("_rfil","_ayar_toggle");
    window.parent.location.replace(u.toString());
    return;
  }}
  var u=new URL(window.parent.location.href);u.searchParams.set("_rfil",k);window.parent.location.replace(u.toString());
}}
function gg(id){{var u=new URL(window.parent.location.href);var g=JSON.parse(u.searchParams.get("_grp_gizli")||"[]");if(g.includes(id))g=g.filter(x=>x!==id);else g.push(id);u.searchParams.set("_grp_gizli",JSON.stringify(g));window.parent.location.replace(u.toString());}}
function gs(id,dir){{var u=new URL(window.parent.location.href);var s=JSON.parse(u.searchParams.get("_grp_sira")||JSON.stringify(_s));var i=s.indexOf(id);if(dir==="l"&&i>0){{var t=s[i-1];s[i-1]=s[i];s[i]=t;}}else if(dir==="r"&&i<s.length-1){{var t=s[i+1];s[i+1]=s[i];s[i]=t;}}u.searchParams.set("_grp_sira",JSON.stringify(s));window.parent.location.replace(u.toString());}}
</script>"""
    st.markdown(_html, unsafe_allow_html=True)


    # Grup ayar param
    _qp_grp_gizli = st.query_params.get("_grp_gizli","")
    _qp_grp_sira  = st.query_params.get("_grp_sira","")
    if _qp_grp_gizli or _qp_grp_sira:
        if _qp_grp_gizli:
            try: st.session_state["_rbar_grp_gizli"] = _rjson.loads(_qp_grp_gizli)
            except: pass
        if _qp_grp_sira:
            try: st.session_state["_rbar_grp_sira"] = _rjson.loads(_qp_grp_sira)
            except: pass
        st.query_params.clear(); st.rerun()

    # Query param'dan filtre oku
    _qp_rfil = st.query_params.get("_rfil", "")
    if _qp_rfil:
        st.query_params.clear()
        _fk_sfx_now = st.session_state.get("_filtre_reset_sayac", 0)

        def _rapor_kutuya_ekle(_hedef_key, _deger):
            """Üst rapor rozetine tıklanınca değeri ilgili filtre kutusuna (Aşama.../Durum...) ekler.
            Kutuda zaten varsa tekrar eklemez — hem tek tek hem toplu tıklama birikerek çalışır."""
            _cur = list(st.session_state.get(_hedef_key, []))
            if _deger not in _cur:
                _cur.append(_deger)
            st.session_state[_hedef_key] = _cur
            st.session_state[f"{_hedef_key}_{_fk_sfx_now}"] = _cur

        def _tekli_asama_temizle():
            """Eski tekli-kolon (1/2/3. Aşama) yedek filtrelerini temizler — genel kutuyla çakışmasın diye"""
            for _fk in ["_cl_fil_asama1", "_cl_fil_asama2", "_cl_fil_asama3", "_cl_fil_sonuc"]:
                st.session_state.pop(_fk, None)

        if _qp_rfil == "toplam":
            st.session_state["_toplam_aktif"] = True
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            st.session_state["_filtre_reset_sayac"] = st.session_state.get("_filtre_reset_sayac",0)+1
            _tekli_asama_temizle()
            for _fk in ["_cl_fil_durum_multi","_cl_fil_asama_multi","_cl_fil_il_multi","_cl_fil_ilce_multi","_cl_fil_temsilci_multi"]:
                st.session_state.pop(_fk, None)
        elif _qp_rfil == "asamasiz":
            st.session_state["_asamasiz_aktif"] = True
            st.session_state["_toplam_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            _tekli_asama_temizle()
            st.session_state.pop("_cl_fil_durum_multi", None)
            st.session_state["_cl_fil_asama_multi"] = []
        elif _qp_rfil == "mesaj_gercek":
            # "💬 Mesaj" kutusuna tıklanınca — gerçekten mesaj/whatsapp/email
            # kaydı olan (veya manuel override edilmiş) müşterileri filtrele.
            st.session_state["_toplam_aktif"] = False
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = True
            _tekli_asama_temizle()
            st.session_state.pop("_cl_fil_durum_multi", None)
            st.session_state["_cl_fil_asama_multi"] = []
        elif _qp_rfil.startswith("durum_"):
            _d = _qp_rfil[6:]
            st.session_state["_toplam_aktif"] = False
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            _rapor_kutuya_ekle("_cl_fil_durum_multi", _d)
        elif _qp_rfil.startswith("asama_"):
            _a = _qp_rfil[6:]
            st.session_state["_toplam_aktif"] = False
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            _rapor_kutuya_ekle("_cl_fil_asama_multi", _a)
        elif _qp_rfil.startswith("asama1_"):
            _a = _qp_rfil[7:]
            st.session_state["_toplam_aktif"] = False
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            _tekli_asama_temizle()
            st.session_state["_cl_fil_asama1"] = _a
            _rapor_kutuya_ekle("_cl_fil_asama_multi", _a)
        elif _qp_rfil.startswith("asama2_"):
            _a = _qp_rfil[7:]
            st.session_state["_toplam_aktif"] = False
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            _tekli_asama_temizle()
            st.session_state["_cl_fil_asama2"] = _a
            _rapor_kutuya_ekle("_cl_fil_asama_multi", _a)
        elif _qp_rfil.startswith("asama3_"):
            _a = _qp_rfil[7:]
            st.session_state["_toplam_aktif"] = False
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            _tekli_asama_temizle()
            st.session_state["_cl_fil_asama3"] = _a
            _rapor_kutuya_ekle("_cl_fil_asama_multi", _a)
        elif _qp_rfil.startswith("sonuc_"):
            _a = _qp_rfil[6:]
            st.session_state["_toplam_aktif"] = False
            st.session_state["_asamasiz_aktif"] = False
            st.session_state["_mesaj_gercek_aktif"] = False
            _tekli_asama_temizle()
            st.session_state["_cl_fil_sonuc"] = _a
            _rapor_kutuya_ekle("_cl_fil_asama_multi", _a)
        st.rerun()

    # Kanban view
    _cl_view = st.session_state.get("_cl_view", "liste")

    if _cl_view == "kanban":
        # ── KART TIKLAMASI — query param ile müşteri seç ─────────────────────
        try:
            if "kb_not_id" in st.query_params:
                _kb_qid2 = int(st.query_params["kb_not_id"])
                st.query_params.clear()
                _kb_row2 = df[df["id"] == _kb_qid2]
                if not _kb_row2.empty:
                    _kb_firma2 = str(_kb_row2.iloc[0]["firma"])
                    st.session_state["kb_alt_sec"] = f"[{_kb_qid2}] {_kb_firma2}"
                st.rerun()
        except: pass
        # ── KANBAN GÖRÜNÜMÜ ───────────────────────────────────────────────────
        import streamlit.components.v1 as _kb_comp
        import json as _kbj

        # Veriyi hazırla — silindi olmayanlar
        _kb_df = df.copy() if not df.empty else pd.DataFrame()
        if not _kb_df.empty and "silindi" in _kb_df.columns:
            _kb_df = _kb_df[_kb_df["silindi"].astype(str).isin(["0","False","","nan","None"]) | _kb_df["silindi"].isna()]

        _kanban_asama_listesi = tum_asama_opts if tum_asama_opts else (sorted(_kb_df["islem_asamasi"].dropna().unique().tolist()) if "islem_asamasi" in _kb_df.columns else [])
        _kanban_renk = ["#f59e0b","#2563eb","#16a34a","#7c3aed","#0891b2","#dc2626","#f97316","#0d9488","#6366f1","#84cc16","#ec4899","#14b8a6"]

        # Not sayılarını al
        try:
            _sb_kbn = get_sb_client()
            _kb_not_data = _sb_kbn.table("cari_aciklamalar").select("cari_id,aciklama").execute().data or [] if _sb_kbn else []
            _kb_not_data = [r for r in _kb_not_data if not str(r.get("aciklama","") or "").startswith("##YETKILI##")]
            import collections as _kbc2
            _kb_not_sayac = _kbc2.Counter([str(r["cari_id"]) for r in _kb_not_data])
        except: _kb_not_sayac = {}

        _kanban_kolonlar = []
        for _ki, _ka in enumerate(_kanban_asama_listesi):
            _kdf = _kb_df[_kb_df["islem_asamasi"] == _ka] if "islem_asamasi" in _kb_df.columns else pd.DataFrame()
            _kartlar = []
            for _, _kr in _kdf.iterrows():
                try: _hedef = float(_kr.get("beklenen_ciro",0) or 0)
                except: _hedef = 0
                _kid = int(_kr.get("id",0) or 0)
                _kartlar.append({
                    "id": _kid,
                    "firma": str(_kr.get("firma","") or "")[:30],
                    "yetkili": str(_kr.get("yetkili","") or "")[:20],
                    "gsm": _tel_gruplu(str(_kr.get("gsm","") or "")),
                    "il": str(_kr.get("il","") or ""),
                    "ilce": str(_kr.get("ilce","") or ""),
                    "durum": str(_kr.get("durum","") or ""),
                    "hedef": f"{_hedef:,.0f}".replace(",",".") if _hedef > 0 else "",
                    "not_sayi": int(_kb_not_sayac.get(str(_kid), 0)),
                })
            _kanban_kolonlar.append({
                "asama": _ka,
                "renk": _kanban_renk[_ki % len(_kanban_renk)],
                "sayi": len(_kartlar),
                "kartlar": _kartlar[:50]
            })

        _kanban_filtreli = _kanban_kolonlar
        _kanban_json = _kbj.dumps(_kanban_filtreli, ensure_ascii=False)

        _kanban_html = ("""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,sans-serif;}
html,body{height:100%;overflow:hidden;}
body{background:#f1f5f9;padding:6px;}
.board{display:flex;gap:6px;height:calc(100vh - 16px);overflow-x:auto;overflow-y:hidden;}
.board::-webkit-scrollbar{height:5px;}
.board::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px;}
.col{flex:1 1 0;min-width:160px;background:#f8fafc;border-radius:10px;border:0.5px solid #e2e8f0;display:flex;flex-direction:column;height:100%;overflow:hidden;}
.col-hdr{padding:9px 11px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;}
.col-name{font-size:11px;font-weight:700;color:white;word-break:break-word;}
.col-badge{background:rgba(255,255,255,.3);color:white;border-radius:20px;padding:1px 7px;font-size:10px;font-weight:700;flex-shrink:0;margin-left:4px;}
.col-body{padding:6px;display:flex;flex-direction:column;gap:4px;overflow-y:auto;flex:1;min-height:0;}
.col-body::-webkit-scrollbar{width:2px;}
.col-body::-webkit-scrollbar-thumb{background:#e2e8f0;}
.kart{background:white;border-radius:7px;padding:9px;border:0.5px solid #e2e8f0;}
.kart:hover{border-color:#93c5fd;box-shadow:0 1px 6px rgba(0,0,0,.08);}
.firma{font-size:11px;font-weight:700;color:#0f172a;margin-bottom:2px;line-height:1.3;}
.ytkl{font-size:10px;color:#64748b;margin-bottom:1px;}
.gsm{font-size:10px;color:#2563eb;margin-bottom:2px;font-weight:500;}
.yer{font-size:9px;color:#94a3b8;margin-bottom:3px;}
.dchip{display:inline-block;padding:1px 6px;border-radius:20px;font-size:9px;background:#f1f5f9;color:#374151;margin-bottom:3px;}
.footer{display:flex;justify-content:space-between;align-items:center;padding-top:5px;border-top:0.5px solid #f1f5f9;}
.hedef{font-size:10px;font-weight:700;color:#16a34a;}
.nbtn{background:#eff6ff;color:#2563eb;border:none;border-radius:4px;padding:2px 7px;font-size:9px;cursor:pointer;font-weight:600;}
.nbtn:hover{background:#dbeafe;}
.bos{padding:12px;text-align:center;font-size:11px;color:#cbd5e1;}
</style></head><body>
<div class="board" id="board"></div>
<script>
var data=""" + _kanban_json + """;
var board=document.getElementById('board');
if(!data||!data.length){board.innerHTML='<div class="bos">Veri yok</div>';}
data.forEach(function(kol){
  var col=document.createElement('div');col.className='col';
  var h='<div class="col-hdr" style="background:'+kol.renk+'"><span class="col-name">'+kol.asama+'</span><span class="col-badge">'+kol.sayi+'</span></div>';
  var b='<div class="col-body">';
  if(!kol.kartlar.length) b+='<div class="bos">Boş</div>';
  kol.kartlar.forEach(function(k){
    var yer=[k.il,k.ilce].filter(Boolean).join('/');
    b+='<div class="kart" onclick="kartSec('+k.id+')">';
    b+='<div class="firma">'+k.firma+'</div>';
    if(k.yetkili) b+='<div class="ytkl">👤 '+k.yetkili+'</div>';
    if(k.gsm) b+='<div class="gsm">📞 '+k.gsm+'</div>';
    if(yer) b+='<div class="yer">📍 '+yer+'</div>';
    if(k.durum) b+='<span class="dchip">'+k.durum+'</span><br>';
    b+='<div class="footer">';
    b+=k.hedef?'<span class="hedef">'+k.hedef+' ₺</span>':'<span></span>';
    var notLbl=k.not_sayi>0?'📋 '+k.not_sayi+' not':'📋 Not';
    b+='<span class="nbtn">'+notLbl+'</span>';
    b+='</div></div>';
  });
  b+='</div>';
  col.innerHTML=h+b;
  board.appendChild(col);
});
function kartSec(id){
  var base=window.parent.location.href.split('?')[0];
  window.parent.location.href=base+'?kb_not_id='+id;
}
</script></body></html>""")

        import streamlit.components.v1 as _kbc
        _kbc.html(_kanban_html, height=640, scrolling=False)


        # Not butonu — query param ile dialog açıldı (yukarda)
        _ = None

        # ── KANBAN ALT PANEL — tek satır ─────────────────────────────────────
        st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
        _kb_opts = ["— Müşteri seçin —"] + [f"[{int(r['id'])}] {r.get('firma','')}" for _, r in _kb_df.sort_values("firma").iterrows()]
        _kb_sec_def = st.session_state.get("kb_alt_sec", "— Müşteri seçin —")
        if _kb_sec_def not in _kb_opts: _kb_sec_def = "— Müşteri seçin —"

        _kp1, _kp2, _kp3, _kp4 = st.columns([3, 2, 1, 1])
        _kb_sec = _kp1.selectbox("m", _kb_opts, index=_kb_opts.index(_kb_sec_def), key="kb_alt_sec", label_visibility="collapsed")

        if _kb_sec != "— Müşteri seçin —":
            _kb_sel_id = int(_kb_sec.split("]")[0].replace("[","").strip())
            _kb_sel_row = _kb_df[_kb_df["id"] == _kb_sel_id]
            _kb_sel_firma = str(_kb_sel_row.iloc[0]["firma"]) if not _kb_sel_row.empty else ""
            _kb_sel_asama = str(_kb_sel_row.iloc[0].get("islem_asamasi","") or "") if not _kb_sel_row.empty else ""

            _asama_idx = tum_asama_opts.index(_kb_sel_asama) if _kb_sel_asama in tum_asama_opts else 0
            _kb_yeni_asama = _kp2.selectbox("a", tum_asama_opts, index=_asama_idx, key="kb_asama_sec", label_visibility="collapsed")

            if _kp3.button("✅ Kaydet", key="kb_asama_kaydet", use_container_width=True, type="primary"):
                try:
                    _sb_kba = get_sb_client()
                    if _sb_kba:
                        _sb_kba.table("cari_kartlar").update({"islem_asamasi": _kb_yeni_asama}).eq("id", _kb_sel_id).execute()
                    try: db_read.clear()
                    except: pass
                    st.toast(f"✅ {_kb_sel_firma} → {_kb_yeni_asama}", icon="✅")
                    st.rerun()
                except Exception as _kbae:
                    st.error(f"Hata: {_kbae}")

            if _kp4.button("📋 Not", key="kb_not_ac", use_container_width=True):
                not_dialog(_kb_sel_id, _kb_sel_firma)

        st.caption(f"📋 Kanban — {len(_kb_df)} müşteri · {len(_kanban_filtreli)} sütun")
        st.stop()

    # ── GELİŞMİŞ FİLTRE PANEL ────────────────────────────────────────────────
    _cok_secili_idler = set()

    # ── ÇOKLU FİRMA SEÇİMİ — kullanıcı isteği: tek satır filtrelerin ÜSTÜNDE,
    # kendi tam genişlikte satırında, AÇILIR/KAPANIR PANELE (Filtreler & Arama)
    # GİRMEDEN her zaman görünür ve açık kalır.
    _cok_sec_opts = [f"[{int(i)}] {f}" for i, f in zip(df["id"], df["firma"]) if str(f) not in ["","nan","None"]] if not df.empty and "firma" in df.columns else []
    # Taslak "Yükle" butonundan gelen bekleyen değeri — widget OLUŞTURULMADAN ÖNCE uygulanmalı
    # (Streamlit, widget instantiate edildikten SONRA aynı key'e session_state ataması yapılmasına izin vermiyor)
    if "_cok_tsk_bekleyen" in st.session_state:
        _bekleyen_idler = set(st.session_state.pop("_cok_tsk_bekleyen"))
        st.session_state["_cl_cok_secim"] = [o for o in _cok_sec_opts if int(o.split("]")[0].replace("[","").strip()) in _bekleyen_idler]
    _cok_secili_ham = st.multiselect("🔍 Çoklu Firma Seçimi", _cok_sec_opts, key="_cl_cok_secim", placeholder="Birden fazla firma seçmek için tıkla...")
    for _cs in _cok_secili_ham:
        try: _cok_secili_idler.add(int(_cs.split("]")[0].replace("[","").strip()))
        except: pass

    # ── 📦 ARŞİVİ GÖSTER — artık üstteki sticky buton satırında (Kaydet/Satır
    # Ekle/Sil ile aynı satır), burada tekrar tanımlanmaz.

    with st.expander("🔍 Filtreler & Arama", expanded=False):
        # ── TEK SATIR FİLTRE ───────────────────────────────────────────────────
        if st.session_state.get("kart_sec_reset"):
            st.session_state.pop("kart_sec_reset", None)
            st.session_state.pop("kart_sec", None)

        kart_opts_inline = ["-- Müşteri Seçin --", "🔵 Tüm Firmalar"]
        if not df.empty and "firma" in df.columns and "id" in df.columns:
            kart_opts_inline += [f"[{int(i)}] {f}" for i, f in zip(df["id"], df["firma"]) if str(f) not in ["","nan","None"]]
        if st.session_state.get("kart_sec_reset"):
            st.session_state.pop("kart_sec_reset", None)
            st.session_state.pop("kart_sec", None)

        # ── TEK SATIR — hepsi aynı hizada, eşit genişlikte: Yeni firma kontrol,
        # Özel, Aşama, Durum, İl, İlçe, Güncelleme Tarihi (Çoklu firma artık
        # bu panelin ÜSTÜNDE, kendi ayrı satırında — her zaman açık) ────────
        _fc = st.columns(14)

        # ── YENİ FİRMA KONTROLÜ — "Satır Ekle" ile elle firma adı yazmadan önce,
        # aynı/benzer isimde zaten kayıtlı müşteri var mı diye anlık arama.
        # ÖNEMLİ: Kelime kelime ayrı ayrı arama YAPILMAZ — yazılan ifade (boşluk/nokta
        # farkları yok sayılarak) ART ARDA/BÜTÜN olarak firma adında geçiyor mu diye
        # bakılır. Örn. "KAPKA HEDİ" yazınca sadece "KAPKA HEDİYELİK..." gibi bu ifadeyi
        # ard arda içeren firmalar gelir; sadece "HEDİ" geçen alakasız firmalar gelmez.
        _yf_ara = _fc[0].text_input("yf", placeholder="🔍 Yeni firma kontrol...", key="_cl_yeni_firma_ara", label_visibility="collapsed")
        # "Rut" filtresi — kullanıcı isteğiyle "Ara/Yeni firma kontrol"ün SAĞINDA.
        # Yazılan metin, o müşteriye atanmış Rut adında GEÇİYORSA eşleşir.
        # "Rut" filtresi — KULLANICI İSTEĞİ: diğer filtreler (Özel filtrele,
        # Aşama, Durum...) gibi SEÇİLEBİLİR bir liste olsun, serbest metin
        # kutusu değil. Seçenekler, o an var olan TÜM Rut değerlerinin
        # parçalarına (her il/kod) ayrıştırılıp tekilleştirilmesiyle oluşur.
        _rut_kod_seti = set()
        if "rut" in df.columns:
            for _rv in df["rut"].dropna():
                for _parca in str(_rv).split(" - "):
                    _parca = _parca.strip()
                    if _parca:
                        _rut_kod_seti.add(_parca)
        _rut_opts = sorted(_rut_kod_seti)
        _rut_sec = _fc[1].multiselect("rut", _rut_opts, key="_cl_fil_rut_multi", placeholder="🛣️ Rut...", label_visibility="collapsed")
        _ozel_opts = sorted(df["rakip_firma"].dropna().astype(str).unique().tolist()) if "rakip_firma" in df.columns else []
        _ozel_opts = [x for x in _ozel_opts if x not in ["", "nan", "None"]]
        _ozel_sec = _fc[2].multiselect("oz", _ozel_opts, key="_cl_fil_ozel_multi", placeholder="🔍 Özel filtrele...", label_visibility="collapsed")

        # "Müşteri Seçin" kutusu kullanıcı isteğiyle kaldırıldı — sabit nötr
        # değerde tutuluyor (aşağıdaki tekli-müşteri seçim mantığı bu değere
        # bağlı olduğu için değişkeni koruyoruz, sadece görünür kutuyu kaldırdık).
        secili_kart_inline = "-- Müşteri Seçin --"
        # Genel serbest metin arama kutusu kullanıcı isteğiyle kaldırıldı — ara_txt
        # boş sabit tutuluyor (aşağıdaki filtreleme mantığı buna bağlı olduğu için
        # değişkeni koruyoruz, sadece görünür arama kutusunu kaldırdık).
        ara_txt = ""

        _fk_sfx = st.session_state.get("_filtre_reset_sayac", 0)
        _asama_def = [] if st.session_state.get("_filtre_sifirla_flag") else [x for x in st.session_state.get("_cl_fil_asama_multi",[]) if x in tum_asama_opts]
        _asama_sec = _fc[3].multiselect("a", tum_asama_opts, default=_asama_def, key=f"_cl_fil_asama_multi_{_fk_sfx}", placeholder="Aşama...", label_visibility="collapsed")
        st.session_state["_cl_fil_asama_multi"] = _asama_sec
        # Kutudan çıkarılmış/değiştirilmiş bir değer için eski tekli-kolon yedeği (asama1/2/3/sonuc) takılı kalmasın
        for _fk_stale in ["_cl_fil_asama1", "_cl_fil_asama2", "_cl_fil_asama3", "_cl_fil_sonuc"]:
            _fv_stale = st.session_state.get(_fk_stale)
            if _fv_stale and _fv_stale not in _asama_sec:
                st.session_state.pop(_fk_stale, None)

        _fk_sfx = st.session_state.get("_filtre_reset_sayac", 0)
        _durum_opts_tumu = [x for x in tum_durum_opts if str(x).upper() not in ["NONE","NAN",""]]
        _durum_def = [] if st.session_state.get("_filtre_sifirla_flag") else [x for x in st.session_state.get("_cl_fil_durum_multi",[]) if x in _durum_opts_tumu]
        _durum_sec_raw = _fc[4].multiselect("d", _durum_opts_tumu, default=_durum_def, key=f"_cl_fil_durum_multi_{_fk_sfx}", placeholder="Durum...", label_visibility="collapsed")
        st.session_state["_cl_fil_durum_multi"] = _durum_sec_raw
        _durum_sec = _durum_sec_raw

        filtre_seg = "Tümü"

        _il_opts = sorted(df["il"].dropna().astype(str).unique().tolist()) if "il" in df.columns else []
        _il_def  = [x for x in st.session_state.get("_cl_fil_il_multi",[]) if x in _il_opts]
        _il_sec  = _fc[5].multiselect("i", _il_opts, default=_il_def, key="_cl_fil_il_multi", placeholder="İl...", label_visibility="collapsed")

        _ilce_opts = sorted((df[df["il"].astype(str).isin(_il_sec)] if _il_sec else df)["ilce"].dropna().astype(str).unique().tolist()) if "ilce" in df.columns else []
        _ilce_opts = [x for x in _ilce_opts if x not in ["nan","None",""]]
        _ilce_sec  = _fc[6].multiselect("ilce", _ilce_opts, default=[x for x in st.session_state.get("_cl_fil_ilce_multi",[]) if x in _ilce_opts], key="_cl_fil_ilce_multi", placeholder="İlçe...", label_visibility="collapsed")

        _tem_sec = []
        siralama_kol = "Tarih↓"

        # ── Güncelleme Tarihi filtresi — ÇOKLU seçim, saatsiz (sadece gün).
        # Seçenekler alt alta açılır, birden fazla tarih seçilebilir.
        # Filtre satırının en sonunda. ──────────────────────────────────────
        _guncelleme_tarih_sec = _fc[7].multiselect(
            "gt", _guncelleme_tarih_opts_str, key="_cl_fil_guncelleme_tarih_multi",
            placeholder="🔍 Güncelleme Tarihi...", label_visibility="collapsed"
        )

        # ── SONUÇ FİLTRESİ — KULLANICI İSTEĞİ (2026-09): "Devam Ediyor",
        # "Kazanıldı", "Kaybedildi" gibi Sonuç değerine göre doğrudan,
        # ayarlara girmeden filtreleme — Durum/Aşama ile aynı satırda.
        _sonuc_filtre_sec = _fc[9].multiselect(
            "sn", ["Kazanıldı", "Kaybedildi", "Devam Ediyor"], key="_cl_fil_sonuc_multi",
            placeholder="🏆 Sonuç...", label_visibility="collapsed"
        )

        # ── 🔀 KALICI SIRALAMA — KULLANICI İSTEĞİ (2026-09): tarayıcının kendi
        # "sütun başlığına tıkla sırala" özelliği Python'un hiç haberi olmadığı
        # için Kaydet gibi bir işlemde (sayfa yenilenince) kayboluyordu. Bunun
        # yerine GERÇEK, KALICI bir sıralama — seçim session_state'te tutulur,
        # sen değiştirene kadar (Kaydet dahil) HİÇBİR ŞEY onu sıfırlamaz.
        # Kullanıcı isteğiyle diğer filtrelerle AYNI tek satırda gösterilir.
        _CL_SIRALA_SECENEKLERI = {
            "": "-- Sıralama Yok (varsayılan) --",
            "musteri_kodu": "Müşteri Kodu", "id": "ID", "firma": "Firma Adı", "rakip_firma": "Özel (Rakip Firma)",
            "yetkili": "Yetkili", "gsm": "GSM", "sabit": "Sabit Tel", "email": "Email", "adres": "Adres",
            "il": "İl", "ilce": "İlçe", "durum": "Durum", "temsilci": "Temsilci",
            "vergi_no": "Vergi No", "vergi_dairesi": "Vergi Dairesi", "musteri_subesi": "Müşteri Şubesi",
            "vade": "Vade", "odeme": "Ödeme", "teklif_fiyat": "Teklif Fiyat",
            "beklenen_ciro": "Hedeflenen Ciro", "gerceklesen_ciro": "Gerçekleşen Ciro",
            "islem_asamasi": "İlk Temas", "asama1": "1. Aşama", "asama2": "2. Aşama", "asama3": "3. Aşama",
            "aciklama": "Açıklama", "ara_islem": "Ara İşlem", "il_ciro_ozet": "İl Ciroları", "sektor": "Sektör", "rut": "Rut", "sonuc": "Sonuç",
        }
        for _cl_sirala_il_kv in _IL_SUTUN_LISTESI:
            if _cl_sirala_il_kv not in _CL_SIRALA_SECENEKLERI:
                _CL_SIRALA_SECENEKLERI[_cl_sirala_il_kv] = _cl_sirala_il_kv
        _cl_sirala_alan = _fc[10].selectbox("🔀 Sırala", list(_CL_SIRALA_SECENEKLERI.keys()),
                                             format_func=lambda k: _CL_SIRALA_SECENEKLERI[k],
                                             key="_cl_sirala_alan_sec", label_visibility="collapsed")
        _cl_sirala_yon = _fc[11].selectbox("Yön", ["Artan (A→Z, küçük→büyük)", "Azalan (Z→A, büyük→küçük)"],
                                            key="_cl_sirala_yon_sec", label_visibility="collapsed",
                                            disabled=not _cl_sirala_alan)

        # ── 📅 TARİH SIRALAMA — KULLANICI İSTEĞİ (2026-09): tarih başlıkları
        # (Kayıt, Güncelleme, İşlem, Takip, Randevu Tarihi) için, genel
        # "🔀 Sırala"dan TAMAMEN AYRI, bağımsız çalışan ikinci bir sıralama.
        # İkisi AYNI ANDA aktif olabilir gibi görünse de, TEK bir tabloya
        # aynı anda İKİ farklı sıralama uygulanamayacağı için: bu kutuda bir
        # seçim varsa O ÖNCELİKLİDİR (tabloyu tarihe göre sıralar); boşsa
        # genel "🔀 Sırala"nın seçimi geçerli olur.
        _CL_TARIH_SIRALA_SECENEKLERI = {
            "": "-- Tarih Sıralama Yok --",
            "tarih": "Kayıt Tarihi", "guncelleme_tarihi": "Güncelleme Tarihi",
            "islem_tarihi_manuel": "İşlem Tarihi", "takip_tarihi_manuel": "Takip Tarihi",
            "randevu_tarihi_manuel": "Randevu Tarihi",
        }
        _cl_tarih_sirala_alan = _fc[12].selectbox("📅 Tarih Sırala", list(_CL_TARIH_SIRALA_SECENEKLERI.keys()),
                                                   format_func=lambda k: _CL_TARIH_SIRALA_SECENEKLERI[k],
                                                   key="_cl_tarih_sirala_alan_sec", label_visibility="collapsed")
        _cl_tarih_sirala_yon = _fc[13].selectbox("Tarih Yön", ["Eskiden Yeniye", "Yeniden Eskiye"],
                                                  key="_cl_tarih_sirala_yon_sec", label_visibility="collapsed",
                                                  disabled=not _cl_tarih_sirala_alan)

        # ── ÖZEL (AYARLANABİLİR) FİLTRE — KULLANICI İSTEĞİ (2026-09):
        # Kullanıcılar > Kolon Ayarları > "🔍 Filtre Düzenle"de seçilen alana
        # göre (örn. Yetkili) ek bir filtre kutusu. Alan seçilmemişse (--
        # Kullanılmıyor --) bu kutu hiç gösterilmez.
        _cl_ozel_filtre_alani = st.session_state.get("_cl_ozel_filtre_alani_cache")
        if _cl_ozel_filtre_alani is None:
            _cl_ozel_filtre_alani = _cl_ozel_filtre_alani_yukle()
            st.session_state["_cl_ozel_filtre_alani_cache"] = _cl_ozel_filtre_alani
        _cl_ozel_filtre_sec = []
        if _cl_ozel_filtre_alani and _cl_ozel_filtre_alani in df.columns:
            # DOĞAL (SAYISAL) SIRALAMA — KULLANICI İSTEĞİ (2026-09): "MW1,
            # MW2...MW4800" gibi sonu rakamla biten değerler, düz metin
            # sıralamasında "MW12, MW120, MW1200, MW2..." gibi karışık
            # çıkıyordu (harf harf karşılaştırma). Sondaki sayı varsa SAYI
            # olarak, yoksa normal metin olarak sıralanır.
            import re as _cl_re_nat
            def _cl_dogal_sirala_anahtar(_v):
                _m = _cl_re_nat.match(r'^(.*?)(\d+)$', str(_v))
                if _m:
                    return (0, _m.group(1), int(_m.group(2)))
                return (1, str(_v), 0)
            _cl_ozel_filtre_opts = sorted(
                [x for x in df[_cl_ozel_filtre_alani].dropna().astype(str).unique().tolist() if x.strip() and x not in ["nan", "None"]],
                key=_cl_dogal_sirala_anahtar
            )
            _cl_ozel_filtre_etiket = _CL_OZEL_FILTRE_SECENEKLERI.get(_cl_ozel_filtre_alani, _cl_ozel_filtre_alani)
            _cl_ozel_filtre_sec = _fc[8].multiselect(
                "ozf", _cl_ozel_filtre_opts, key=f"_cl_fil_ozel_ayarlanabilir_{_cl_ozel_filtre_alani}",
                placeholder=f"🔍 {_cl_ozel_filtre_etiket}...", label_visibility="collapsed"
            )

        # Manuel filtre kutularından biri (Aşama, Durum, Arama, İl, İlçe, Tarih) kullanıldıysa
        # 'Toplam' modu otomatik kapanır — aksi halde seçim görünür ama uygulanmaz
        if ara_txt or _asama_sec or _durum_sec or _il_sec or _ilce_sec or _guncelleme_tarih_sec or _ozel_sec or _rut_sec or _cl_ozel_filtre_sec or _sonuc_filtre_sec:
            st.session_state["_toplam_aktif"] = False
        # NOT: "Çoklu Firma Seçimi" artık bu panelin ÜSTÜNDE, kendi ayrı
        # satırında render ediliyor (_cok_secili_ham/_cok_secili_idler orada
        # zaten hesaplandı) — burada TEKRAR oluşturulmuyor (aynı widget key'i
        # iki kez kullanmak Streamlit'te hataya yol açar).

        # ── YENİ FİRMA KONTROLÜ SONUCU — arama kutusu artık tek satırlık filtre
        # barının içinde (yer kaplamasın diye); eşleşme bulununca sonuç/düzenleme
        # tablosu burada, filtre satırının hemen altında gösteriliyor.
        if _yf_ara and _yf_ara.strip() and "firma" in df.columns:
            def _yf_norm(_s):
                return (str(_s).upper().replace("İ", "I").replace("Ş", "S")
                        .replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C"))
            _yf_q_bosluksuz = _yf_norm(_yf_ara.strip()).replace(" ", "").replace(".", "")
            _yf_kaynak = df.copy()
            _yf_kaynak["_yf_norm_bs"] = (_yf_kaynak["firma"].apply(_yf_norm)
                                          .str.replace(" ", "", regex=False).str.replace(".", "", regex=False))
            _yf_eslesen = _yf_kaynak[_yf_kaynak["_yf_norm_bs"].apply(
                lambda _tam: bool(_yf_q_bosluksuz) and _yf_q_bosluksuz in _tam
            )]
            if not _yf_eslesen.empty:
                st.caption(f"⚠️ {len(_yf_eslesen)} eşleşen kayıt bulundu — kontrol edin.")
                _yf_kol = [c for c in ["id", "firma", "yetkili", "rakip_firma", "gsm", "sabit", "email", "adres", "ilce", "il", "aciklama"] if c in _yf_eslesen.columns]
                _yf_gosterilecek = _yf_eslesen[_yf_kol].head(15).copy()
                _yf_gosterilecek.insert(0, "Seç", False)
                _yf_duzenlenen = st.data_editor(
                    _yf_gosterilecek, use_container_width=True, hide_index=True,
                    disabled=["id"], key="_yf_duzenle_editor", num_rows="dynamic",
                    column_config={
                        "Seç": st.column_config.CheckboxColumn("Seç", default=False, width="small"),
                        "id": st.column_config.NumberColumn("ID", width="small"),
                        "firma": st.column_config.TextColumn("firma", width="small"),
                        "yetkili": st.column_config.TextColumn("yet", width="small"),
                        "rakip_firma": st.column_config.TextColumn("Öze", width="small"),
                        "gsm": st.column_config.TextColumn("gsm", width="small"),
                        "sabit": st.column_config.TextColumn("sabit", width="small"),
                        "email": st.column_config.TextColumn("em", width="small"),
                        "adres": st.column_config.TextColumn("adres", width="small"),
                        "ilce": st.column_config.TextColumn("ilce", width="small"),
                        "il": st.column_config.TextColumn("il", width="small"),
                        "aciklama": st.column_config.TextColumn("Açıklama", width="small"),
                    }
                )
                # ── NOT PANELİ — ana Cari Liste tablosuyla AYNI davranış: tek
                # satır "Seç" işaretlenince o müşterinin not paneli açılır. ──
                _yf_secili_satirlar = _yf_duzenlenen[_yf_duzenlenen["Seç"] == True]
                if len(_yf_secili_satirlar) == 1 and pd.notna(_yf_secili_satirlar.iloc[0].get("id")):
                    _yf_sel_id = int(_yf_secili_satirlar.iloc[0]["id"])
                    _yf_sel_firma = str(_yf_secili_satirlar.iloc[0].get("firma", ""))
                    not_dialog(_yf_sel_id, _yf_sel_firma)
                if st.button("💾 Değişiklikleri Kaydet", key="_yf_duzenle_kaydet_btn"):
                    _yf_guncellenen = 0
                    _yf_eklenen = 0
                    _yf_kayit_hatasi = []
                    _sb_yf = get_sb_client()
                    _yf_eski_idler = set(_yf_gosterilecek["id"].dropna().astype(int).tolist())
                    for _yi in range(len(_yf_duzenlenen)):
                        _satir_yeni = _yf_duzenlenen.iloc[_yi]
                        _yf_id_ham = _satir_yeni.get("id")
                        _yf_mevcut_mi = pd.notna(_yf_id_ham) and int(_yf_id_ham) in _yf_eski_idler
                        if _yf_mevcut_mi:
                            _satir_eski = _yf_gosterilecek[_yf_gosterilecek["id"] == int(_yf_id_ham)].iloc[0]
                            _yf_fark = {}
                            for _yc in _yf_kol:
                                if _yc == "id": continue
                                _yv, _ev = _satir_yeni[_yc], _satir_eski[_yc]
                                _yv_str = "" if pd.isna(_yv) else str(_yv)
                                _ev_str = "" if pd.isna(_ev) else str(_ev)
                                if _yv_str != _ev_str:
                                    _yf_fark[_yc] = _yv_str
                            if _yf_fark and _sb_yf:
                                try:
                                    _sb_yf.table("cari_kartlar").update(_yf_fark).eq("id", int(_yf_id_ham)).execute()
                                    _yf_guncellenen += 1
                                except Exception as _yf_hata:
                                    _yf_kayit_hatasi.append(f"ID {int(_yf_id_ham)}: {_yf_hata}")
                        else:
                            _yf_yeni_kayit = {}
                            for _yc in _yf_kol:
                                if _yc == "id": continue
                                _yv = _satir_yeni[_yc]
                                if pd.notna(_yv) and str(_yv).strip():
                                    _yf_yeni_kayit[_yc] = str(_yv).strip()
                            if _yf_yeni_kayit.get("firma") and _sb_yf:
                                try:
                                    _sb_yf.table("cari_kartlar").insert(_yf_yeni_kayit).execute()
                                    _yf_eklenen += 1
                                except Exception as _yf_hata:
                                    _yf_kayit_hatasi.append(f"Yeni satır ({_yf_yeni_kayit.get('firma')}): {_yf_hata}")
                            elif not _yf_yeni_kayit.get("firma") and any(_yf_yeni_kayit.values()):
                                _yf_kayit_hatasi.append("Yeni satır: 'firma' adı boş olamaz, kaydedilmedi.")
                    if _yf_guncellenen or _yf_eklenen:
                        _mesaj_parca = []
                        if _yf_guncellenen: _mesaj_parca.append(f"{_yf_guncellenen} kayıt güncellendi")
                        if _yf_eklenen: _mesaj_parca.append(f"{_yf_eklenen} yeni firma eklendi")
                        st.toast(f"💾 {' · '.join(_mesaj_parca)}", icon="✅")
                        st.cache_data.clear()
                        st.rerun()
                    if _yf_kayit_hatasi:
                        st.error("Bazı satırlar kaydedilemedi:\n" + "\n".join(_yf_kayit_hatasi))
                    if not _yf_guncellenen and not _yf_eklenen and not _yf_kayit_hatasi:
                        st.info("Herhangi bir değişiklik bulunamadı.")
            else:
                st.caption(f"✅ '{_yf_ara}' ile eşleşen kayıtlı müşteri yok — yeni firma olarak güvenle eklenebilir.")

        # ── Çoklu Firma Taslakları — seçili firmaları isimle kaydet, sonra tek tıkla geri yükle ──
        if "_cok_firma_taslaklar" not in st.session_state:
            st.session_state["_cok_firma_taslaklar"] = {}
            try:
                _sb_tsk0 = get_sb_client()
                if _sb_tsk0:
                    import json as _tskj0
                    _r_tsk0 = _sb_tsk0.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_cok_firma_taslaklar").execute()
                    if _r_tsk0.data:
                        st.session_state["_cok_firma_taslaklar"] = _tskj0.loads(_r_tsk0.data[0]["deger"])
            except:
                pass

        def _cok_firma_taslak_kaydet_db():
            try:
                _sb_tsk1 = get_sb_client()
                if _sb_tsk1:
                    import json as _tskj1
                    _deger_tsk1 = _tskj1.dumps(st.session_state["_cok_firma_taslaklar"], ensure_ascii=False)
                    # GÜVENLİ (2026-09): "kullanici_tercih" tablosunda (kullanici, anahtar)
                    # için unique constraint olmadığı için upsert(on_conflict=...)
                    # güvenilir değil — ama bunun çözümü "önce sil sonra ekle" DEĞİL,
                    # çünkü o sırada silme başarılı olup ekleme başarısız kalırsa veri
                    # TAMAMEN kaybolur. Bunun yerine: satır varsa UPDATE (unique
                    # constraint'e ihtiyaç duymaz, sadece eşleşeni günceller), yoksa
                    # INSERT edilir.
                    _tsk_guncelle1 = _sb_tsk1.table("kullanici_tercih").update({"deger": _deger_tsk1}).eq(
                        "kullanici", "__liste_ui__").eq("anahtar", "_cok_firma_taslaklar").execute()
                    if not _tsk_guncelle1.data:
                        _sb_tsk1.table("kullanici_tercih").insert({
                            "kullanici": "__liste_ui__", "anahtar": "_cok_firma_taslaklar",
                            "deger": _deger_tsk1
                        }).execute()
            except Exception as _tsk_db_hata:
                st.error(f"⚠️ Taslak veritabanına kaydedilemedi: {_tsk_db_hata}")

        if st.session_state.get("_filtre_sifirla_flag"):
            del st.session_state["_filtre_sifirla_flag"]

        # Eski sistemle uyumluluk
        _df_il  = df["il"]  if "il"  in df.columns else pd.Series([""] * len(df))
        _df_asa = df["islem_asamasi"] if "islem_asamasi" in df.columns else pd.Series([""] * len(df))
        kart_opts = ["-- Müşteri Seçin --"] + [
            f"[{int(i)}] {f} | {il} | {a}"
            for i, f, il, a in zip(df["id"], df["firma"], _df_il, _df_asa)
            if str(f) not in ["","nan","None"]
        ] if not df.empty and "firma" in df.columns else ["-- Müşteri Seçin --"]
        if secili_kart_inline == "🔵 Tüm Firmalar":
            secili_kart = "-- Müşteri Seçin --"
            # Query param ile tam sıfırlama — widget değerleri de temizlenir
            _u = st.query_params.to_dict()
            _u["_rfil"] = "toplam"
            st.query_params.update(_u)
            st.rerun()
        elif secili_kart_inline != "-- Müşteri Seçin --":
            _id_str = secili_kart_inline.split("]")[0].replace("[","").strip()
            _esles = [o for o in kart_opts if f"[{_id_str}]" in o]
            secili_kart = _esles[0] if _esles else "-- Müşteri Seçin --"
        else:
            secili_kart = "-- Müşteri Seçin --"

    # Varsayılan: hiçbir filtre seçilmemişse tüm liste gelsin
    # NOT: "Filtre Düzenle" ile eklenen özel filtrenin widget anahtarı DİNAMİK
    # (seçilen alana göre değişir) — bu yüzden burada AYRICA kontrol edilir.
    _cl_ozel_filtre_alani_erken = st.session_state.get("_cl_ozel_filtre_alani_cache")
    if _cl_ozel_filtre_alani_erken is None:
        _cl_ozel_filtre_alani_erken = _cl_ozel_filtre_alani_yukle()
        st.session_state["_cl_ozel_filtre_alani_cache"] = _cl_ozel_filtre_alani_erken
    _cl_ozel_filtre_widget_anahtari_erken = f"_cl_fil_ozel_ayarlanabilir_{_cl_ozel_filtre_alani_erken}" if _cl_ozel_filtre_alani_erken else None
    if not st.session_state.get("_toplam_aktif") and \
       not st.session_state.get("_cl_fil_durum_multi") and \
       not st.session_state.get("_cl_fil_asama_multi") and \
       not st.session_state.get("_asamasiz_aktif") and \
       not st.session_state.get("_mesaj_gercek_aktif") and \
       not st.session_state.get("_cl_fil_asama1") and \
       not st.session_state.get("_cl_fil_asama2") and \
       not st.session_state.get("_cl_fil_asama3") and \
       not st.session_state.get("_cl_fil_sonuc") and \
       not st.session_state.get("_cl_fil_il_multi") and \
       not st.session_state.get("_cl_fil_ilce_multi") and \
       not st.session_state.get("_cl_fil_ozel_multi") and \
       not st.session_state.get("_cl_fil_guncelleme_tarih_multi") and \
       not (_cl_ozel_filtre_widget_anahtari_erken and st.session_state.get(_cl_ozel_filtre_widget_anahtari_erken)) and \
       not st.session_state.get("_cl_fil_sonuc_multi") and \
       not st.session_state.get("_cl_fil_rut_multi"):
        st.session_state["_toplam_aktif"] = True

    # Filtre uygula
    df_f = df.copy()
    # ── 📦 ARŞİV — KULLANICI İSTEĞİ (2026-09, DÜZELTİLDİ): Ana Cari Liste HER
    # ZAMAN arşivsiz (normal) haliyle gösterilir — işaretli/işaretsiz gibi bir
    # durum YOK. Arşivdekileri görmek için AYRI bir buton/pencere kullanılır
    # (bkz. "📦 Arşiv" butonu, sticky bar'da — kendi dialog'unu açar). Üstteki
    # GENEL/SONUÇ rapor sayaçları bu filtrelemeden ETKİLENMEZ.
    _cl_arsiv_idler_gizli = _cari_arsiv_yukle()
    if _cl_arsiv_idler_gizli and "id" in df_f.columns:
        df_f = df_f[~df_f["id"].astype(str).isin(_cl_arsiv_idler_gizli)]
    # Toplam aktifse tüm filtreleri zorla sıfırla
    if st.session_state.get("_toplam_aktif", False):
        ara_txt = ""; _asama_sec = []; _durum_sec = []; _il_sec = []; _ilce_sec = []; _tem_sec = []; filtre_seg = "Tümü"; _guncelleme_tarih_sec = []; _ozel_sec = []; _rut_sec = []
        for _fk in ["_cl_fil_asama1","_cl_fil_asama2","_cl_fil_asama3","_cl_fil_sonuc"]:
            st.session_state.pop(_fk, None)
    # Aşamasız filtresi
    if st.session_state.get("_asamasiz_aktif", False):
        _tum_asama_set = set(_grp1_asama + _grp2_asama + _grp3_asama + _grp4_asama + _grp5_asama)
        if "islem_asamasi" in df_f.columns:
            df_f = df_f[df_f["islem_asamasi"].isna() | ~df_f["islem_asamasi"].isin(_tum_asama_set)]
    # "💬 Mesaj" kutusuna tıklanınca — gerçek mesaj/whatsapp/email kaydı olan
    # (veya manuel override edilmiş) müşterilerle filtrele.
    elif st.session_state.get("_mesaj_gercek_aktif", False):
        if "id" in df_f.columns:
            _mg_idler = _rbar_mesaj_id_seti_yukle()
            df_f = df_f[df_f["id"].astype(str).isin(_mg_idler)]
    # Toplam butonuna basıldıysa hiçbir filtre uygulanmaz
    elif not st.session_state.get("_toplam_aktif", False):
        if ara_txt:
            df_f = df_f[df_f.apply(lambda r: ara_txt.lower() in str(r).lower(), axis=1)]
        if _asama_sec:
            # Aşama değerleri (Randevu, Teklif, TAKİP, Sözleşme...) ile Sonuç değerlerini (Kazanıldı, Kaybedildi, Devam Ediyor)
            # ayrı gruplar olarak ele alıyoruz: kendi grubu içinde VEYA (OR), gruplar arasında VE (AND).
            # Örn: "TAKİP" + "Devam Ediyor" seçilince -> 3. aşaması TAKİP OLAN VE sonucu Devam Ediyor OLAN kayıtlar gelir.
            _sonuc_kategori_n = {_asama_norm(x) for x in ["Kazanıldı", "Kaybedildi", "Devam Ediyor"]}
            _asama_sec_n = [_asama_norm(x) for x in _asama_sec]
            _stage_vals_n = [x for x in _asama_sec_n if x not in _sonuc_kategori_n]
            _sonuc_vals_n = [x for x in _asama_sec_n if x in _sonuc_kategori_n]

            _stage_mask = None
            if _stage_vals_n:
                _stage_mask = df_f["islem_asamasi"].apply(_asama_norm).isin(_stage_vals_n) if "islem_asamasi" in df_f.columns else pd.Series([False] * len(df_f), index=df_f.index)
                for _acol in ["asama1", "asama2", "asama3"]:
                    if _acol in df_f.columns:
                        _stage_mask = _stage_mask | df_f[_acol].apply(_asama_norm).isin(_stage_vals_n)

            _sonuc_mask = None
            if _sonuc_vals_n:
                _sonuc_mask = df_f["sonuc"].apply(_asama_norm).isin(_sonuc_vals_n) if "sonuc" in df_f.columns else pd.Series([False] * len(df_f), index=df_f.index)

            if _stage_mask is not None and _sonuc_mask is not None:
                _asama_mask = _stage_mask & _sonuc_mask
            elif _stage_mask is not None:
                _asama_mask = _stage_mask
            else:
                _asama_mask = _sonuc_mask
            df_f = df_f[_asama_mask]
        # asama1/2/3/sonuc filtresi — hangi kolonda olduğuna bakılmaksızın, büyük/küçük harf farkı yok sayılarak eşleşeni yakalar
        _tekli_asama_hedef = (st.session_state.get("_cl_fil_asama1") or
                               st.session_state.get("_cl_fil_asama2") or
                               st.session_state.get("_cl_fil_asama3"))
        if _tekli_asama_hedef:
            _tekli_hedef_n = _asama_norm(_tekli_asama_hedef)
            _tek_mask = pd.Series([False] * len(df_f), index=df_f.index)
            for _acol in ["islem_asamasi", "asama1", "asama2", "asama3"]:
                if _acol in df_f.columns:
                    _tek_mask = _tek_mask | (df_f[_acol].apply(_asama_norm) == _tekli_hedef_n)
            df_f = df_f[_tek_mask]
        if st.session_state.get("_cl_fil_sonuc") and "sonuc" in df_f.columns:
            df_f = df_f[df_f["sonuc"].apply(_asama_norm) == _asama_norm(st.session_state["_cl_fil_sonuc"])]
        if _durum_sec:
            df_f = df_f[df_f["durum"].isin(_durum_sec)]
        if filtre_seg != "Tümü":
            df_f["_seg_tmp"] = df_f.apply(lambda r: hesapla_segment(r.get("segment",""), r.get("gerceklesen_ciro",0)), axis=1)
            if filtre_seg == "Segmentsiz": df_f = df_f[df_f["_seg_tmp"]==""]
            else: df_f = df_f[df_f["_seg_tmp"]==filtre_seg]
        if _il_sec:
            df_f = df_f[df_f["il"].astype(str).isin(_il_sec)]
        if _ilce_sec:
            df_f = df_f[df_f["ilce"].astype(str).isin(_ilce_sec)]
        if _rut_sec:
            _rut_secili_set = set(_rut_sec)
            df_f = df_f[df_f.get("rut", pd.Series(dtype=str)).astype(str).apply(
                lambda _rv: bool({p.strip() for p in _rv.split(" - ") if p.strip()} & _rut_secili_set))]
        if _ozel_sec and "rakip_firma" in df_f.columns:
            df_f = df_f[df_f["rakip_firma"].astype(str).isin(_ozel_sec)]
        if _tem_sec:
            df_f = df_f[df_f["temsilci"].astype(str).isin(_tem_sec)]
        if _guncelleme_tarih_sec:
            # Güncelleme Tarihi — ÇOKLU seçim, saatsiz. Bir müşteri, seçilen
            # tarihlerden HERHANGİ BİRİNDE gerçekten işlem görmüşse gelir
            # (sadece "en son işlemi" o tarihte olan değil — _id_tum_gunler_str
            # o müşterinin TÜM işlem günlerini tutar, kesişim kontrolü yapılır).
            _sec_tarih_set = set(_guncelleme_tarih_sec)
            df_f = df_f[df_f["id"].apply(lambda x: bool(_id_tum_gunler_str.get(str(int(x)), set()) & _sec_tarih_set))]

    # ── ÖZEL (AYARLANABİLİR) FİLTRE — Kullanıcılar > Kolon Ayarları'nda
    # seçilen alana (örn. Müşteri Şubesi) göre uygulanır.
    # 🚨 KRİTİK DÜZELTME (2026-09): bu filtre eskiden yukarıdaki "elif not
    # _toplam_aktif" bloğunun İÇİNDEYDİ — yani "Toplam" modu aktifken (hatta
    # yanlışlıkla aktif kaldığında) bu filtre HİÇ ÇALIŞMIYORDU, kullanıcı bir
    # şube seçse bile TÜM liste görünmeye devam ediyordu. Artık KOŞULSUZ,
    # Toplam modundan BAĞIMSIZ olarak HER ZAMAN uygulanır — kullanıcı bu
    # filtreyi seçtiğinde her zaman geçerli olmalı.
    if _cl_ozel_filtre_sec and _cl_ozel_filtre_alani and _cl_ozel_filtre_alani in df_f.columns:
        df_f = df_f[df_f[_cl_ozel_filtre_alani].astype(str).isin(_cl_ozel_filtre_sec)]

    # ── SONUÇ FİLTRESİ — aynı gerekçeyle (yukarıdaki gibi) Toplam modundan
    # BAĞIMSIZ, her zaman uygulanır.
    if _sonuc_filtre_sec and "sonuc" in df_f.columns:
        df_f = df_f[df_f["sonuc"].astype(str).isin(_sonuc_filtre_sec)]

    # Bölgeler ekranından gelen gizli bölge filtresi (ilçe pill'leri taşmasın diye görünmez uygulanır)
    if st.session_state.get("_bl_ilce_filtre") and "ilce" in df_f.columns:
        _bl_hedef_ilceler = set(st.session_state["_bl_ilce_filtre"])
        df_f = df_f[df_f["ilce"].astype(str).isin(_bl_hedef_ilceler)]

    # Mükerrer bölümünden gelen filtre — tüm mükerrer kayıtları tabloda gösterir
    if st.session_state.get("_mr_liste_filtre") and "id" in df_f.columns:
        _mr_hedef_idler = set(st.session_state["_mr_liste_filtre"])
        df_f = df[df["id"].isin(_mr_hedef_idler)].reset_index(drop=True) if "id" in df.columns else df_f
        _mrf1, _mrf2 = st.columns([5,1])
        with _mrf1:
            st.info(f"🔍 Mükerrer kayıtlar gösteriliyor — {len(df_f)} kayıt. Düzenleyip Kaydet'e basabilir, "
                    "Seç kutusunu işaretleyip silebilirsiniz.")
        with _mrf2:
            if st.button("✕ Kaldır", key="_mr_liste_filtre_kaldir", use_container_width=True):
                st.session_state.pop("_mr_liste_filtre", None)
                st.rerun()

    # Havuz (Bölgesiz) filtresi — hiçbir tanımlı bölgeye uymayan (il boş veya tanımsız) kayıtlar
    if st.session_state.get("_bl_havuz_filtre") and not df_f.empty:
        _hv_ilce_kol = "ilce" if "ilce" in df_f.columns else None
        df_f = df_f[df_f.apply(
            lambda r: il_ilce_bolge_bul(r.get("il",""), r.get(_hv_ilce_kol,"") if _hv_ilce_kol else "") is None,
            axis=1)]
        if not df_f.empty and "id" in df_f.columns:
            _hv_kolonlar = [c for c in ["id","firma","il","ilce"] if c in df_f.columns]
            _hv_edit_df = df_f[_hv_kolonlar].copy().reset_index(drop=True)

            _hv_col_config = {
                "id":     st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "firma":  st.column_config.TextColumn("Firma", disabled=True, width="medium"),
                "il":     st.column_config.TextColumn("İl (yazın)", width="small"),
                "ilce":   st.column_config.TextColumn("İlçe (yazın)", width="small"),
            }
            with st.expander(f"✏️ Bu {len(df_f)} kaydı düzelt (kaydırmadan)", expanded=True):
                # Form içinde — siz "Kaydet"e basana kadar sayfa hiç yeniden hesaplanmaz,
                # yazarken ekran oynayıp durmaz.
                with st.form(key="hv_form", clear_on_submit=False):
                    _hv_edited = st.data_editor(
                        _hv_edit_df, use_container_width=True, hide_index=True,
                        column_config=_hv_col_config, key="hv_editor", height=300,
                        column_order=["firma","il","ilce","id"])
                    _hv_submit = st.form_submit_button("💾 Kaydet ve Bölgelere Dağıt",
                                                        type="primary", use_container_width=True)

                if _hv_submit:
                    _hv_basarili = 0
                    _hv_hala_havuzda = 0
                    _sb_hv = get_sb_client()
                    with st.spinner("Kaydediliyor ve bölgelere dağıtılıyor..."):
                        for _, _hv_row in _hv_edited.iterrows():
                            _hv_orig_satir = df_f[df_f["id"] == _hv_row["id"]]
                            if _hv_orig_satir.empty:
                                continue
                            _hv_orig = _hv_orig_satir.iloc[0]
                            _hv_yeni_il = str(_hv_row.get("il","")).strip()
                            _hv_yeni_ilce = str(_hv_row.get("ilce","")).strip()
                            if _hv_yeni_il != str(_hv_orig.get("il","") or "").strip() or _hv_yeni_ilce != str(_hv_orig.get("ilce","") or "").strip():
                                try:
                                    if _sb_hv:
                                        _sb_hv.table("cari_kartlar").update({"il": _hv_yeni_il, "ilce": _hv_yeni_ilce}).eq("id", int(_hv_row["id"])).execute()
                                    else:
                                        db_update("cari_kartlar", {"il": _hv_yeni_il, "ilce": _hv_yeni_ilce}, "id", int(_hv_row["id"]))
                                    _hv_basarili += 1
                                    if il_ilce_bolge_bul(_hv_yeni_il, _hv_yeni_ilce) is None:
                                        _hv_hala_havuzda += 1
                                except Exception:
                                    pass
                    if _hv_basarili:
                        try: get_cari_listesi.clear()
                        except: pass
                        try: db_read.clear()
                        except: pass
                        st.session_state.pop("hv_editor", None)
                        _hv_ozet = f"✅ {_hv_basarili} kayıt güncellendi."
                        if _hv_hala_havuzda:
                            _hv_ozet += f" ({_hv_hala_havuzda} tanesi yazdığınız il/ilçeyle hâlâ eşleşmedi, Havuz'da kaldı — kontrol edin.)"
                        st.toast(_hv_ozet, icon="✅")
                        st.rerun()
                    else:
                        st.info("Hiçbir değişiklik yapılmadı.")

    # ── HİÇ FİLTRE SEÇİLİ DEĞİLKEN — sadece işlem görmemiş (Özel Müşteri/Portföy) göster ──
    # Bir müşteriye durum atanınca (Randevu, Teklif, Tekrar Ara vb.) artık burada görünmesin,
    # Segment hesapla ve sırala
    if df_f.empty or "firma" not in df_f.columns:
        df_f = pd.DataFrame()
    else:
        df_f["_seg_goster"] = df_f.apply(lambda r: hesapla_segment(r.get("segment",""), r.get("gerceklesen_ciro",0)), axis=1)
        _seg_sira = {"👑 A+":0,"⭐ A":1,"🔵 B":2,"⚪ C":3,"":4}
        df_f["_seg_sira"] = df_f["_seg_goster"].map(lambda s: _seg_sira.get(s,4))
        df_f = df_f.sort_values(["_seg_sira","firma"], ascending=[True,True]).reset_index(drop=True)
        if siralama_kol == "Firma A-Z":      df_f = df_f.sort_values("firma", ascending=True)
        elif siralama_kol == "Firma Z-A":    df_f = df_f.sort_values("firma", ascending=False)
        elif siralama_kol == "İl A-Z" and "il" in df_f.columns:       df_f = df_f.sort_values("il", ascending=True)
        elif siralama_kol == "Temsilci A-Z" and "temsilci" in df_f.columns: df_f = df_f.sort_values("temsilci", ascending=True)
        elif siralama_kol == "Hedef ₺↓" and "beklenen_ciro" in df_f.columns:
            df_f = df_f.copy(); df_f["_s"] = pd.to_numeric(df_f["beklenen_ciro"], errors="coerce").fillna(0)
            df_f = df_f.sort_values("_s", ascending=False).drop(columns=["_s"])
        elif siralama_kol == "Hedef ₺↑" and "beklenen_ciro" in df_f.columns:
            df_f = df_f.copy(); df_f["_s"] = pd.to_numeric(df_f["beklenen_ciro"], errors="coerce").fillna(0)
            df_f = df_f.sort_values("_s", ascending=True).drop(columns=["_s"])
        elif siralama_kol == "Gerçek ₺↓" and "gerceklesen_ciro" in df_f.columns:
            df_f = df_f.copy(); df_f["_s"] = pd.to_numeric(df_f["gerceklesen_ciro"], errors="coerce").fillna(0)
            df_f = df_f.sort_values("_s", ascending=False).drop(columns=["_s"])
        elif siralama_kol == "Gerçek ₺↑" and "gerceklesen_ciro" in df_f.columns:
            df_f = df_f.copy(); df_f["_s"] = pd.to_numeric(df_f["gerceklesen_ciro"], errors="coerce").fillna(0)
            df_f = df_f.sort_values("_s", ascending=True).drop(columns=["_s"])
        df_f = df_f.reset_index(drop=True)

    # Çoklu firma seçimi yapıldıysa — diğer filtreler ne olursa olsun sadece seçilenler gösterilir
    if _cok_secili_idler and "id" in df_f.columns:
        df_f = df.copy()  # tüm listeden (mevcut il/durum filtrelerinden bağımsız) seçilenleri bul
        # 🚨 DÜZELTME (2026-09): bu satır df_f'i df'ten TAZE kuruyordu, bu da
        # yukarıdaki 📦 arşiv gizleme filtresini YOK SAYIYORDU — Çoklu Firma
        # Seçimi aktifken arşivlenmiş müşteriler yine görünüyordu. Aynı
        # filtre burada da uygulanır.
        if _cl_arsiv_idler_gizli:
            df_f = df_f[~df_f["id"].astype(str).isin(_cl_arsiv_idler_gizli)]
        df_f = df_f[df_f["id"].isin(_cok_secili_idler)].reset_index(drop=True)
        st.info(f"🔍 {len(df_f)} firma karşılaştırma için seçili — temizlemek için yukarıdaki kutudan kaldırın.")
        # ── ŞEFFAFLIK: Seçilen ID sayısı ile bulunan satır sayısı farklıysa
        # (örn. arşivlenmiş/silinmiş bir firma seçiliyse) bunu SESSİZCE
        # gizlemiyoruz — hangi ID'lerin bulunamadığını açıkça gösteriyoruz.
        # Burada uygulanan HİÇBİR sayısal sınır/limit yok; "isin()" filtresi
        # seçilen TÜM ID'leri arıyor.
        _bulunmayan_idler = _cok_secili_idler - set(df_f["id"].astype(int).tolist())
        if _bulunmayan_idler:
            st.warning(f"⚠️ Seçtiğin {len(_bulunmayan_idler)} firma listede bulunamadı (ID: {sorted(_bulunmayan_idler)}) — "
                       "muhtemelen arşivlenmiş/silinmiş ya da başka bir kullanıcı tarafından kaldırılmış. "
                       "Bu bir gösterim sınırı değil, o kayıtlar artık mevcut değil.")

    _aktif_fil_sayisi = sum([bool(ara_txt),bool(_asama_sec),bool(_durum_sec),filtre_seg!="Tümü",bool(_il_sec),bool(_ilce_sec),bool(_tem_sec),bool(_guncelleme_tarih_sec),bool(_ozel_sec),bool(_rut_sec)])
    if secili_kart != "-- Müşteri Seçin --" and "[" in secili_kart:
        try:
            kart_id = int(secili_kart.split("]")[0].replace("[","").strip())
            # Önce filtrelenmiş listede ara, yoksa tüm listede ara
            _km = df_f[df_f["id"]==kart_id]
            if _km.empty:
                _km = get_cari_listesi()
                _km = _km[_km["id"]==kart_id]
            if _km.empty:
                st.warning("⚠️ Seçili müşteri bulunamadı. Filtreyi temizleyip tekrar deneyin.")
                st.stop()
            kart_row = _km.iloc[0]
            bek = float(kart_row.get("beklenen_ciro",0) or 0)
            ger = float(kart_row.get("gerceklesen_ciro",0) or 0)
            _seg_val = str(kart_row.get("segment","") or "")
            def _temiz(v):
                s = str(v or "").strip()
                return s if s and s not in ["nan","None","-",""] else "-"
            _gsm     = _tel_gruplu(_temiz(kart_row.get("gsm","") or kart_row.get("telefon","") or kart_row.get("tel","")))
            _sabit   = _tel_gruplu(_temiz(kart_row.get("sabit","") or kart_row.get("sabit_hat","")))
            _email   = _temiz(kart_row.get("email","") or kart_row.get("eposta",""))
            _yetkili = _temiz(kart_row.get("yetkili","") or kart_row.get("yetkili_adi",""))
            _il = str(kart_row.get("il","") or "-")
            _ilce = str(kart_row.get("ilce","") or "-")
            _durum = str(kart_row.get("durum","") or "-")
            _asama = str(kart_row.get("islem_asamasi","") or "-")
            _temsilci = str(kart_row.get("temsilci","") or "-")
            _yuzde = round((ger/bek)*100) if bek > 0 else 0
            _fark = ger - bek
            _fark_renk = "#16a34a" if _fark >= 0 else "#dc2626"

            # ── BAŞLIK ───────────────────────────────────────────────────────
            _seg_auto = hesapla_segment(kart_row.get("segment",""), kart_row.get("gerceklesen_ciro",0))
            _sbg, _stxt, _sbrd = segment_renk(_seg_auto)
            _baslik_renk = {"👑 A+":"#92400e","⭐ A":"#374151","🔵 B":"#1e3a8a","⚪ C":"#334155"}.get(_seg_auto,"#1e293b")
            st.markdown(f"""
<div style='background:{_baslik_renk};color:white;padding:12px 20px;border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:space-between'>
  <div style='display:flex;align-items:center;gap:12px'>
    <span style='font-size:28px'>🏢</span>
    <div>
      <div style='font-size:11px;color:rgba(255,255,255,0.6)'>Müşteri Detay Paneli</div>
      <div style='font-size:20px;font-weight:800;letter-spacing:0.5px'>{kart_row.get('firma','').upper()}</div>
    </div>
  </div>
  {f"<div style='background:rgba(255,255,255,0.2);padding:4px 14px;border-radius:20px;font-size:14px;font-weight:700'>{_seg_auto}</div>" if _seg_auto else ""}
</div>""", unsafe_allow_html=True)

            # ── 3 PANEL ──────────────────────────────────────────────────────
            _p1, _p2, _p3 = st.columns(3)

            with _p1:
                st.markdown(f"""
<div style='border:1px solid #e2e8f0;border-radius:0 0 0 10px;padding:16px;height:100%'>
  <div style='font-weight:700;font-size:13px;margin-bottom:10px;color:#374151'>📋 İletişim & Konum</div>
  <div style='font-size:13px;line-height:2;color:#374151'>
    <div>👤 {_yetkili}</div>
    <div>📱 {_gsm}</div>
    <div>☎️ {_sabit}</div>
    <div>✉️ {"<a href='mailto:"+_email+"' style='color:#3b82f6'>"+_email+"</a>" if "@" in _email else _email}</div>
  </div>
</div>""", unsafe_allow_html=True)

            with _p2:
                st.markdown(f"""
<div style='border:1px solid #e2e8f0;border-top:none;padding:16px;height:100%'>
  <div style='font-weight:700;font-size:13px;margin-bottom:10px;color:#374151'>📍 Konum & Durum</div>
  <div style='font-size:13px;line-height:2;color:#374151'>
    <div>🏙️ {_il} / {_ilce}</div>
    <div>📊 {_durum}</div>
    <div>🔄 {_asama}</div>
    <div>👔 {_temsilci}</div>
    {f"<div><span style='background:#eff6ff;color:#1d4ed8;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600'>{_seg_val}</span></div>" if _seg_val and _seg_val not in ["--",""] else ""}
  </div>
</div>""", unsafe_allow_html=True)

            with _p3:
                st.markdown(f"""
<div style='border:1px solid #e2e8f0;border-radius:0 0 10px 0;border-top:none;padding:16px;height:100%'>
  <div style='font-weight:700;font-size:13px;margin-bottom:10px;color:#374151'>💰 Özet Finans</div>
  <div style='display:flex;align-items:center;gap:16px'>
    <div style='text-align:center'>
      <svg width='80' height='80' viewBox='0 0 80 80'>
        <circle cx='40' cy='40' r='32' fill='none' stroke='#e2e8f0' stroke-width='8'/>
        <circle cx='40' cy='40' r='32' fill='none' stroke='{"#22c55e" if _yuzde>=100 else "#3b82f6"}' stroke-width='8'
          stroke-dasharray='{min(_yuzde,100)*2.01} 201' stroke-dashoffset='50' stroke-linecap='round'/>
      </svg>
      <div style='font-size:12px;color:#64748b;margin-top:-8px'>%{_yuzde}</div>
    </div>
    <div>
      <div style='font-size:11px;color:#94a3b8'>Beklenen:</div>
      <div style='font-size:18px;font-weight:800;color:#1e40af'>{fmt_para(bek)}</div>
      <div style='font-size:11px;color:#94a3b8;margin-top:6px'>Gerçekleşen:</div>
      <div style='font-size:16px;font-weight:700;color:#374151'>{fmt_para(ger)}</div>
      <div style='margin-top:4px;background:{"#f0fdf4" if _fark>=0 else "#fef2f2"};color:{_fark_renk};padding:2px 8px;border-radius:6px;font-size:12px;font-weight:600;display:inline-block'>
        {"▲" if _fark>=0 else "▼"} {fmt_para(abs(_fark))}
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

            # ── AKSİYONLAR ───────────────────────────────────────────────────
            st.markdown("<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;margin-top:12px'>", unsafe_allow_html=True)
            _ax1,_ax2,_ax3,_ax4,_ax5 = st.columns([1,1,1.2,1,1])
            if _ax1.button("✏️ Düzenle", key=f"kd_{kart_id}", use_container_width=True):
                d2 = {str(k):(None if str(v) in ["nan","None","NaT"] else v) for k,v in kart_row.items()}
                for _k in ["firma","yetkili","gsm","sabit","email","adres","il","ilce","durum","temsilci","islem_asamasi","aciklama"]:
                    if _k in d2: d2[_k] = "" if d2[_k] is None else str(d2[_k])
                # GSM/Sabit bazı eski kayıtlarda farklı sütunlarda olabiliyor (telefon/tel/sabit_hat) —
                # detay kartındaki gösterimle aynı fallback'i burada da uyguluyoruz, yoksa form boş açılır.
                if not d2.get("gsm"):
                    d2["gsm"] = str(kart_row.get("telefon") or kart_row.get("tel") or "")
                if not d2.get("sabit"):
                    d2["sabit"] = str(kart_row.get("sabit_hat") or "")
                _duzenleme_form_key_temizle(str(kart_id))
                st.session_state["duzenle_musteri"] = d2
                st.session_state["aktif_tab"] = "yeni"; st.rerun()
            _gsm_raw = str(kart_row.get("gsm","") or "").replace(" ","").replace("-","")
            if _gsm_raw.startswith("0"): _gsm_raw = "90" + _gsm_raw[1:]
            if _gsm_raw and _ax3.button("💬 WhatsApp", key=f"kwa_{kart_id}", use_container_width=True):
                st.markdown(f"<span style='opacity:0.4;cursor:not-allowed' title='Geçici devre dışı'>WhatsApp aç (devre dışı)</span>", unsafe_allow_html=True)
            if _ax4.button("💾 Kaydet", key=f"kkaydet_{kart_id}", use_container_width=True, type="primary"):
                try:
                    _g = {"firma":str(kart_row.get("firma","")), "yetkili":str(kart_row.get("yetkili","")), "gsm":str(kart_row.get("gsm","")), "sabit":str(kart_row.get("sabit","")), "email":str(kart_row.get("email","")), "il":str(kart_row.get("il","")), "ilce":str(kart_row.get("ilce","")), "durum":str(kart_row.get("durum","")), "temsilci":str(kart_row.get("temsilci","")), "islem_asamasi":str(kart_row.get("islem_asamasi",""))}
                    if sb_liste: sb_liste.table("cari_kartlar").update(_g).eq("id",kart_id).execute()
                    else: db_update("cari_kartlar",_g,"id",kart_id)
                    try: db_read.clear()
                    except: pass
                    st.success("✅ Kaydedildi!")
                except Exception as _ke: st.error(f"Hata: {_ke}")
            if _ax5.button("🗑️ Arşive", key=f"ka_{kart_id}", use_container_width=True):
                if sb_liste: sb_liste.table("cari_kartlar").update({"silindi":1}).eq("id",kart_id).execute()
                else: db_update("cari_kartlar",{"silindi":1},"id",kart_id)
                try: db_read.clear()
                except: pass
                st.success("Arşive gönderildi!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            # ── AÇIKLAMA SİSTEMİ ──────────────────────────────────────────────
            st.markdown("---")
            st.markdown(f"#### 📝 Açıklamalar")

            # Notlar — ortak panel
            st.markdown("---")
            not_paneli(kart_id, str(kart_row.get("firma","")), key_prefix=f"ck_{kart_id}")

        except Exception as e:
            st.error(f"Kart hatası: {e}")

    st.divider()

    # ── DURUM LİSTESİ — Supabase'den yükle (col_config için) ─────────────────
    def _durum_listesi_yukle():
        try:
            _sb_d = get_sb_client()
            if _sb_d:
                _res = _sb_d.table("kullanici_tercih").select("deger") \
                    .eq("kullanici","__sistem__").eq("anahtar","ekstra_durumlar").execute()
                if _res.data:
                    import json as _jdl
                    return _jdl.loads(_res.data[0]["deger"])
        except: pass
        return []
    _ekstra_d = _durum_listesi_yukle()
    _durum_temel = _tanimlar_yukle("durum") or ["Özel Müşteri","Portföy"]
    _tum_durumlar = _durum_temel + [d for d in _ekstra_d if d not in _durum_temel]

    # ── KOLON AYARLARI ──────────────────────────────────────────────────────────
    # ── KOLON GENİŞLİKLERİ — DB'den oku ─────────────────────────────────────
    _KOL_VARSAYILAN = {
        "tarih":90,"guncelleme_tarihi":100,
        "hesaplama":120,"firma":90,"rakip_firma":90,"yetkili":90,"gsm":100,"sabit":90,"email":90,
        "adres":110,"il":70,"ilce":60,"durum":80,"temsilci":80,
        "vergi_no":90,"vergi_dairesi":100,"musteri_subesi":100,"vade":70,"odeme":80,"teklif_fiyat":90,"islem_tarihi_manuel":90,"takip_tarihi_manuel":90,"randevu_tarihi_manuel":100,
        "islem_asamasi":80,"aciklama":110,"📅 Son Randevu":170,"📨 Notlar":50,"id":40,"musteri_kodu":80,
        "beklenen_ciro":70,"gerceklesen_ciro":70,"✅ Analiz":70,"Varış İli":90,"Koli/Palet":110,
        "🧾 Teklif":70,"💬 Mesaj":70,
        "asama1":90,"asama2":90,"asama3":90,"sonuc":90,"ara_islem":90,"il_ciro_ozet":110,"sektor":100,"rut":90
    }
    for _il_vars in _IL_SUTUN_LISTESI:
        _KOL_VARSAYILAN[_il_vars] = 10
    # Gizli kolonları DB'den yükle
    if "_kol_genislik_init" not in st.session_state:
        try:
            _sb_kg = get_sb_client()
            if _sb_kg:
                import json as _kgj
                _r_kg = _sb_kg.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_kol_genislik").execute()
                if _r_kg.data:
                    _kg_loaded = _kgj.loads(_r_kg.data[0]["deger"])
                    # Varsayılanlarla birleştir — eksik kolonlar olabilir
                    _kg_merged = _KOL_VARSAYILAN.copy()
                    _kg_merged.update(_kg_loaded)
                    st.session_state["_kol_genislik"] = _kg_merged
                else:
                    st.session_state["_kol_genislik"] = _KOL_VARSAYILAN.copy()
                _r_gizli_cl = _sb_kg.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_kol_gizli").execute()
                if _r_gizli_cl.data:
                    st.session_state["_kol_gizli"] = _kgj.loads(_r_gizli_cl.data[0]["deger"])
                else:
                    st.session_state["_kol_gizli"] = []
        except:
            st.session_state["_kol_genislik"] = _KOL_VARSAYILAN.copy()
            st.session_state["_kol_gizli"] = []
        st.session_state["_kol_genislik_init"] = True

    _KG = st.session_state.get("_kol_genislik", _KOL_VARSAYILAN.copy())
    _GIZLI_KOLONLAR = set(st.session_state.get("_kol_gizli", []))

    # Firma'ya kadarki (ve GSM/S.Tel'e kadar) kolonlar küçük/okunur kalsın diye
    # ayrı bir grup — bunlar büyütülürse Firma ilk görünümden çıkıyordu.
    # Bu grubun SONRASINDAKİ kolonlar daha fazla büyütülüyor ki toplam genişlik
    # üst rapor barına ulaşsın (aradaki fark bu "geç" kolonlara dağıtılıyor).
    _KOL_ERKEN = {"tarih","guncelleme_tarihi","id","rakip_firma","firma","yetkili","gsm","sabit"}

    def _w(k):
        # Gerçek piksel genişliği kullan — small/medium/large'a yuvarlarsak
        # 10 ile 79 arası tüm değerler görsel olarak aynı görünüyordu.
        _carpan = 4.5 if k in _KOL_ERKEN else 8.5
        return int(int(_KG.get(k, _KOL_VARSAYILAN.get(k, 100))) * _carpan)

    # Asama1/2/3 sabit seçenek listeleri — mevcut veride bu listede olmayan bir
    # değer varsa açılır kutu bozulmasın diye otomatik listeye eklenir.
    def _asama_secenek_guvenli(_kol, _sabit_liste):
        _liste = list(_sabit_liste)
        if _kol in df.columns:
            for _v in df[_kol].dropna().astype(str).unique():
                _v = _v.strip()
                if _v and _v not in _liste and _v.lower() not in ["nan","none"]:
                    _liste.append(_v)
        return _liste

    # ── İL SÜTUNLARI — global sabit (dosyanın en başında tanımlı), burada tekrar tanımlanmaz ──

    col_config = {
        "islem_tarihi_manuel": st.column_config.TextColumn("İşlem Tarihi", width=_w("islem_tarihi_manuel"), help="Elle yazılan işlem tarihi (bu, otomatik 'İşlem Tarih' kayıt tarihinden farklıdır)."),
        "takip_tarihi_manuel": st.column_config.TextColumn("Takip Tarihi", width=_w("takip_tarihi_manuel"), help="Elle yazılan takip/hatırlatma tarihi."),
        "randevu_tarihi_manuel": st.column_config.TextColumn("Randevu Tarihi", width=_w("randevu_tarihi_manuel"), help="Elle yazılan randevu tarihi (bu, otomatik '📅 Son Randevu' alanından farklıdır)."),
        "Seç":           st.column_config.CheckboxColumn("Seç", default=False, width=_w("Seç")),
        "tarih":         st.column_config.TextColumn("İşlem Tarih", disabled=True, width=_w("tarih")),
        "guncelleme_tarihi": st.column_config.TextColumn("Güncelleme Tarihi", disabled=True, width=_w("guncelleme_tarihi"), help="Bu müşteriye en son ne zaman not, teklif veya mesaj/işlem eklendiğini gösterir."),
        "musteri_kodu":  st.column_config.TextColumn("Müşteri Kodu", disabled=True, width=_w("musteri_kodu"), help="Kayıt tarihine göre sıralı, boşluksuz referans kodu. Silinen müşterinin kodu yeni bir müşteriye yeniden verilir."),
        "id":            st.column_config.NumberColumn("ID", disabled=True, width=_w("id")),
        "olusturan": None, "silindi": None,
        "beklenen_ciro":    st.column_config.NumberColumn("Hedef ₺",  format="%,.0f ₺", width=_w("beklenen_ciro")),
        "gerceklesen_ciro": st.column_config.NumberColumn("Gerçek ₺", format="%,.0f ₺", width=_w("gerceklesen_ciro"), disabled=True,
                                help="OTOMATİK hesaplanır — bu müşterinin TÜM kargo kayıtlarındaki Yekün toplamı. Elle düzenlenmez; değiştirmek için Kargolar sayfasından ilgili kargo kaydını düzenleyin."),
        "rakip_firma":   st.column_config.TextColumn("Özel", width=_w("rakip_firma")),
        "hesaplama":     st.column_config.TextColumn("Hesaplama", width=_w("hesaplama"),
                                                       help="Şehir, Desi, Birim Fiyat satır satır yapıştır (örn. 'AMASYA 227 3.574') — Kaydet'e basınca İl İşaretleme + Ayrıştırma + Hedeflenen Ciro + İl Ciroları + Teklif Fiyat + Koli/Palet OTOMATİK hesaplanıp kaydedilir (eskinin üzerine yazar)."),
        "firma":         st.column_config.TextColumn("Firma",     width=_w("firma")),
        "yetkili":       st.column_config.TextColumn("Yetkili",   width=_w("yetkili")),
        "gsm":           st.column_config.TextColumn("GSM",       width=_w("gsm")),
        "sabit":         st.column_config.TextColumn("S. Tel",    width=_w("sabit")),
        "email":         st.column_config.TextColumn("Email",     width=_w("email")),
        "adres":         st.column_config.TextColumn("Adres",     width=_w("adres")),
        "il":            st.column_config.TextColumn("İl",        width=_w("il")),
        "ilce":          st.column_config.TextColumn("İlçe",      width=_w("ilce")),
        "vergi_no":        st.column_config.TextColumn("Vergi No", width=_w("vergi_no")),
        "vergi_dairesi":   st.column_config.TextColumn("Vergi Dairesi", width=_w("vergi_dairesi")),
        "musteri_subesi":  st.column_config.TextColumn("Müşteri Şubesi", width=_w("musteri_subesi")),
        "vade":            st.column_config.TextColumn("Vade", width=_w("vade")),
        "odeme":           st.column_config.TextColumn("Ödeme", width=_w("odeme")),
        "teklif_fiyat":    st.column_config.TextColumn("Teklif Fiyat", width=_w("teklif_fiyat")),
        "durum":         st.column_config.SelectboxColumn("Durum", options=["Tümü"] + [x for x in tum_durum_opts if str(x).upper() not in ["NONE","NAN",""]], width=_w("durum")),
        "temsilci":      st.column_config.TextColumn("Temsilci",  width=_w("temsilci")),
        "islem_asamasi": st.column_config.SelectboxColumn("İlk Temas", options=["Tümü", "Arama", "Tekrar Ara", "Mesaj", "E-Mail"], width=_w("islem_asamasi")),
        "aciklama":      st.column_config.TextColumn("Açıklama",  width=_w("aciklama")),
        "📅 Son Randevu": st.column_config.TextColumn("📅 Son Randevu", disabled=False, width=_w("📅 Son Randevu"), help="Manuel tarih yazıp kaydedebilirsin (örn. 15.08.2026 veya 15.08.2026 14:00) — gerçek bir randevu kaydı oluşturulur."),
        "📨 Notlar":     st.column_config.TextColumn("📨 Notlar", disabled=True, width=_w("📨 Notlar")),
        "✅ Analiz":     st.column_config.TextColumn("✅ Analiz", disabled=False, width=_w("✅ Analiz"), help="Herhangi bir şey yazıp kaydedin (örn. bir nokta) — ✅ ikonu manuel olarak gösterilir. Boş bırakırsan otomatik eşleşme geri döner."),
        "🧾 Teklif":     st.column_config.TextColumn("🧾 Teklif", disabled=False, width=_w("🧾 Teklif"), help="Sadece rakam girin (örn. 5). İkon otomatik eklenir. Boş bırakırsan otomatik hesaplanan sayı geri döner."),
        "💬 Mesaj":      st.column_config.TextColumn("💬 Mesaj", disabled=False, width=_w("💬 Mesaj"), help="Sadece rakam girin (örn. 3). İkon otomatik eklenir. Boş bırakırsan otomatik hesaplanan sayı geri döner."),
        "Varış İli":     st.column_config.TextColumn("Varış İli", disabled=False, width=_w("Varış İli"), help="Müşterinin kargo varış ili — manuel serbest metin. Buraya veya Koli/Palet'e bir şey yazılırsa Analiz otomatik ✅ olur."),
        "Koli/Palet":    st.column_config.TextColumn("Koli/Palet", disabled=False, width=_w("Koli/Palet"), help="Koli, palet vb. bilgiler — manuel, sınırsız serbest metin."),
        "asama1":        st.column_config.SelectboxColumn("1. Aşama", options=_asama_secenek_guvenli("asama1", ["", "Randevu"]), width=_w("asama1")),
        "asama2":        st.column_config.SelectboxColumn("2. Aşama", options=_asama_secenek_guvenli("asama2", ["", "Teklif"]), width=_w("asama2")),
        "asama3":        st.column_config.SelectboxColumn("3. Aşama", options=_asama_secenek_guvenli("asama3", ["Tümü", "Deneme", "TAKİP", "Fiyat Hazırla", "Sözleşme"]), width=_w("asama3")),
        "ara_islem":     st.column_config.TextColumn("Ara İşlem", width=_w("ara_islem")),
        "il_ciro_ozet":  st.column_config.TextColumn("İl Ciroları", disabled=True, width=_w("il_ciro_ozet"),
                                                       help="Koli/Palet fiyat tablosundan otomatik hesaplanır — en yüksek cirolu il en üstte."),
        "sektor":        st.column_config.TextColumn("Sektör", width=_w("sektor")),
        "rut":           st.column_config.TextColumn("🛣️ Rut", width=_w("rut"), disabled=True,
                             help="OTOMATİK hesaplanır — hangi İL sütun(lar)ına gönderim bilgisi girildiyse, o illerin kısaltması buraya otomatik yazılır. Elle düzenlenmez; değiştirmek için ilgili İL sütununu doldurun/boşaltın."),
        "sonuc":         st.column_config.SelectboxColumn("Sonuç", options=_asama_secenek_guvenli("sonuc", ["Tümü", "Kazanıldı", "Kaybedildi", "Devam Ediyor"]), width=_w("sonuc")),
    }
    # _IL_KISA_ETIKET artık GLOBAL (dosya başında tanımlı) — burada tekrar
    # tanımlanmaz; hem Rut otomatik hesaplaması hem bu başlıklar aynı sabiti kullanır.
    for _il_kol_cfg in _IL_SUTUN_LISTESI:
        col_config[_il_kol_cfg] = st.column_config.TextColumn(
            _IL_KISA_ETIKET.get(_il_kol_cfg, _il_kol_cfg[:3]), width=_w(_il_kol_cfg),
            help=f"{_il_kol_cfg} — Bu firmanın bu ile ne gönderdiğini serbestçe yazın (sayı veya metin).")
    # Sütun sırası — sizin verdiğiniz şablonla birebir: Seç, İşlem Tarih, Id, Firma, Yetkili,
    # Gsm, S.Tel, E-Mail, Adres, İlçe, İl, Hedef(+Gerçek), Durum, Analiz, Aşama, 1-2-3.Aşama,
    # Açıklama, Notlar, Son Randevu, Teklif, Mesaj, Sonuç. Temsilci silinmedi, en sona eklendi.
    # ── SATIR SIRASINI DONDUR — segment/ciro gibi kayıt sırasında değişebilen
    # alanlara göre yapılan sıralama (yukarıda), her kayıttan sonra o müşterinin
    # segmenti/cirosu değiştiği için satırın yerini kaydırıyordu. Bu da "Seç"
    # işaretinin ve genel çalışma sırasının bir kayıttan diğerine kaymasına
    # sebep oluyordu. Çözüm: GÖRÜNEN (filtrelenmiş) müşteri KÜMESİ değişmediği
    # sürece (yeni/silinen/filtre dışı kalan müşteri yoksa) sırayı burada
    # sabitliyoruz — bir alanı düzenleyip kaydetmek artık satırların yerini
    # değiştirmiyor.
    if not df_f.empty and "id" in df_f.columns:
        _cl2_id_kume = tuple(sorted(int(x) for x in df_f["id"].tolist()))  # SIRASIZ küme — sadece hangi müşteriler görünüyor, onu karşılaştırır
        _cl2_anahtar = (str(siralama_kol), _cl2_id_kume)
        if st.session_state.get("_cl2_son_anahtar") != _cl2_anahtar or not st.session_state.get("_cl2_sabit_sira"):
            st.session_state["_cl2_sabit_sira"] = df_f["id"].tolist()
            st.session_state["_cl2_son_anahtar"] = _cl2_anahtar
        else:
            _cl2_sirali = st.session_state["_cl2_sabit_sira"]
            _cl2_map = {v: i for i, v in enumerate(_cl2_sirali)}
            df_f = df_f.copy()
            df_f["_cl2_key"] = df_f["id"].map(_cl2_map).fillna(len(_cl2_sirali))
            df_f = df_f.sort_values("_cl2_key").drop(columns=["_cl2_key"]).reset_index(drop=True)

    col_order = ["islem_tarihi_manuel","takip_tarihi_manuel","randevu_tarihi_manuel","Seç","tarih","guncelleme_tarihi","musteri_kodu","id","rakip_firma","hesaplama","firma","yetkili","gsm","sabit","email","adres","ilce","il",
                 "vergi_no","vergi_dairesi","musteri_subesi","vade","odeme",
                 "beklenen_ciro","gerceklesen_ciro","durum","✅ Analiz","Varış İli","Koli/Palet","teklif_fiyat","islem_asamasi",
                 "asama1","asama2","asama3","aciklama","📨 Notlar","📅 Son Randevu",
                 "🧾 Teklif","💬 Mesaj","ara_islem","il_ciro_ozet","sektor","rut","sonuc","temsilci"] + _IL_SUTUN_LISTESI
    # Gizli kolonları çıkar
    _kol_gizli_map = {"hesaplama":"hesaplama","firma":"firma","rakip_firma":"rakip_firma","yetkili":"yetkili","gsm":"gsm","sabit":"sabit","email":"email",
                      "adres":"adres","il":"il","ilce":"ilce","durum":"durum","temsilci":"temsilci",
                      "vergi_no":"vergi_no","vergi_dairesi":"vergi_dairesi","musteri_subesi":"musteri_subesi","vade":"vade","odeme":"odeme","musteri_kodu":"musteri_kodu","teklif_fiyat":"teklif_fiyat","islem_tarihi_manuel":"islem_tarihi_manuel","takip_tarihi_manuel":"takip_tarihi_manuel","randevu_tarihi_manuel":"randevu_tarihi_manuel",
                      "islem_asamasi":"islem_asamasi","aciklama":"aciklama","tarih":"tarih","guncelleme_tarihi":"guncelleme_tarihi",
                      "📅 Son Randevu":"📅 Son Randevu","📨 Notlar":"📨 Notlar","id":"id",
                      "beklenen_ciro":"beklenen_ciro","gerceklesen_ciro":"gerceklesen_ciro","✅ Analiz":"✅ Analiz",
                      "🧾 Teklif":"🧾 Teklif","💬 Mesaj":"💬 Mesaj","Varış İli":"Varış İli","Koli/Palet":"Koli/Palet",
                      "asama1":"asama1","asama2":"asama2","asama3":"asama3","sonuc":"sonuc","ara_islem":"ara_islem","il_ciro_ozet":"il_ciro_ozet","sektor":"sektor","rut":"rut"}
    col_order = [c for c in col_order if not any(c == _kol_gizli_map.get(g,g) for g in _GIZLI_KOLONLAR)]

    # ── 🔀 KALICI SIRALAMA UYGULAMASI — widget'lar artık YUKARIDA (filtre
    # satırında) oluşturuluyor, burada SADECE seçime göre df_f sıralanıyor.
    # ÖNCELİK: "📅 Tarih Sırala"da bir seçim varsa O uygulanır (tarih olarak
    # anlaşılmaya çalışılır — DD.MM.YYYY gibi yazılmış olsa bile doğru
    # sıralanır, tarih olarak okunamayan metinler en sona atılır); yoksa
    # genel "🔀 Sırala" uygulanır. İkisi AYNI ANDA TEK tabloya uygulanamaz.
    if _cl_tarih_sirala_alan and _cl_tarih_sirala_alan in df_f.columns:
        _cl_tarih_azalan = _cl_tarih_sirala_yon == "Yeniden Eskiye"
        try:
            _cl_tarih_ayristirilmis = pd.to_datetime(df_f[_cl_tarih_sirala_alan], dayfirst=True, errors="coerce")
            df_f = df_f.assign(_cl_tarih_sira_gecici=_cl_tarih_ayristirilmis).sort_values(
                by="_cl_tarih_sira_gecici", ascending=not _cl_tarih_azalan, na_position="last"
            ).drop(columns=["_cl_tarih_sira_gecici"])
        except Exception:
            pass
    elif _cl_sirala_alan and _cl_sirala_alan in df_f.columns:
        _cl_sirala_azalan = _cl_sirala_yon.startswith("Azalan")
        try:
            if _cl_sirala_alan in ("beklenen_ciro", "gerceklesen_ciro", "id"):
                df_f = df_f.sort_values(by=_cl_sirala_alan, ascending=not _cl_sirala_azalan, na_position="last")
            else:
                df_f = df_f.sort_values(
                    by=_cl_sirala_alan, key=lambda _s: _s.astype(str).str.lower(),
                    ascending=not _cl_sirala_azalan, na_position="last"
                )
        except Exception:
            pass

    # ── SAYFALAMA KALDIRILDI — kullanıcı isteği üzerine, liste artık her zaman
    # tam (Tümü) gösteriliyor, sayfa butonları tamamen kaldırıldı. ────────────
    _cl_toplam_kayit = len(df_f)
    df_f_sayfali = df_f

    df_edit = df_f_sayfali.copy()
    # "None" / "nan" string değerlerini temizle — boş göster
    for _col in df_edit.columns:
        if df_edit[_col].dtype == object:
            df_edit[_col] = df_edit[_col].replace({"None": "", "nan": "", "NaN": "", "none": ""})
    # aciklama kolonu kesinlikle olsun
    if "aciklama" not in df_edit.columns:
        df_edit["aciklama"] = ""
    df_edit["aciklama"] = df_edit["aciklama"].fillna("").astype(str).replace("nan","")
    # rakip_firma kolonu kesinlikle olsun
    if "rakip_firma" not in df_edit.columns:
        df_edit["rakip_firma"] = ""
    df_edit["rakip_firma"] = df_edit["rakip_firma"].fillna("").astype(str).replace("nan","")
    # ara_islem kolonu kesinlikle olsun
    if "ara_islem" not in df_edit.columns:
        df_edit["ara_islem"] = ""
    df_edit["ara_islem"] = df_edit["ara_islem"].fillna("").astype(str).replace("nan","")
    # ── İL SÜTUNLARI — global fonksiyonlar (dosya başında tanımlı) kullanılıyor,
    # burada tekrar tanımlanmaz — hem burası hem Notlar&Randevu dialog'u AYNI
    # önbelleği paylaşır, biri kaydedince diğeri de hemen güncel görür.
    # 🚨 GERİ ALINDI (2026-09): performans için eklenen önbellekleme (session_state
    # tabanlı) KALDIRILDI — kullanıcı, işaretlediği illerin/Rut'un tabloda
    # görünmediğini bildirdi ("günlerdir emeğim"). KULLANICI İSTEĞİ AÇIKÇA:
    # asla veri kaybı/yanlış görünme riski olmasın, hız ikinci öncelik. Artık
    # HER RENDER'DA doğrudan, önbelleksiz hesaplanıyor — daha yavaş olabilir
    # ama HER ZAMAN DOĞRU ve GÜNCEL sonucu garanti eder.
    _il_gonderim_matrisi = _il_gonderim_matrisi_yukle()
    if "id" in df_edit.columns:
        for _il_kol in _IL_SUTUN_LISTESI:
            df_edit[_il_kol] = df_edit["id"].apply(
                lambda _rid: (_il_gonderim_matrisi.get(str(int(_rid)), {}).get(_il_kol, "") or "") if pd.notna(_rid) else "")
        # "Rut" — KULLANICI İSTEĞİ (2026-09): artık elle yazılmıyor, hangi İL
        # sütun(lar)ına gönderim bilgisi girildiyse OTOMATİK hesaplanır (bkz.
        # _cari_rut_hesapla_otomatik, dosya başında tanımlı GLOBAL fonksiyon).
        df_edit["rut"] = df_edit["id"].apply(lambda _rid: _cari_rut_hesapla_otomatik(_rid, _il_gonderim_matrisi))
    elif "rut" not in df_edit.columns:
        df_edit["rut"] = ""

    # Son randevu bilgisini ekle (tarih + saat + bölge) — normalize edilmiş eşleştirme
    try:
        _df_rand_join = db_read("randevular", extra_sql="ORDER BY randevu_tarihi DESC, randevu_saati DESC")
        if not _df_rand_join.empty and "musteri_adi" in _df_rand_join.columns:
            def _norm_rand(s):
                return (str(s or "").strip()
                        .upper()
                        .replace("İ","I").replace("Ş","S").replace("Ğ","G")
                        .replace("Ü","U").replace("Ö","O").replace("Ç","C")
                        .replace("  "," "))
            _son_rand = {}
            for _, _rj in _df_rand_join.iterrows():
                _mn_norm = _norm_rand(_rj.get("musteri_adi",""))
                if _mn_norm and _mn_norm not in _son_rand:
                    _dt = fmt_tarih(str(_rj.get("randevu_tarihi","") or ""))
                    _st = str(_rj.get("randevu_saati","") or "")[:5]
                    _bl = str(_rj.get("bolge","") or "")
                    _sc = str(_rj.get("sonuc","") or "")
                    _son_rand[_mn_norm] = f"📅 {_dt} {_st}"
            df_edit["📅 Son Randevu"] = df_edit["firma"].apply(lambda x: _son_rand.get(_norm_rand(x),""))
    except:
        df_edit["📅 Son Randevu"] = ""
    # Aşama 1-4 ve Sonuç kolonları — yoksa boş ekle
    for _ak in ["asama1","asama2","asama3","sonuc"]:
        if _ak not in df_edit.columns:
            df_edit[_ak] = ""

    # Ciro kolonlarını sayısal tut — başlığa tıklayınca doğru sıralar
    if "beklenen_ciro" in df_edit.columns:
        df_edit["beklenen_ciro"] = pd.to_numeric(df_edit["beklenen_ciro"], errors="coerce").fillna(0)
    if "gerceklesen_ciro" in df_edit.columns:
        df_edit["gerceklesen_ciro"] = pd.to_numeric(df_edit["gerceklesen_ciro"], errors="coerce").fillna(0)
    # ── Manuel Analiz / Çıkış İli / Koli-Palet override'ları — DB'den yükle ──
    # (Analiz hesabından ÖNCE yüklenmeli — aşağıda kullanılıyor)
    for _ov_key in ["_analiz_manuel_override", "_cikis_ili_manuel", "_koli_palet_manuel"]:
        if _ov_key not in st.session_state:
            st.session_state[_ov_key] = {}
    if not st.session_state.get("_ekstra_override_yuklendi"):
        st.session_state["_ekstra_override_yuklendi"] = True
        try:
            _sb_ex0 = get_sb_client()
            if _sb_ex0:
                import json as _exj0
                _r_ex0 = _sb_ex0.table("kullanici_tercih").select("anahtar,deger").eq("kullanici","__liste_ui__").in_(
                    "anahtar", ["_analiz_manuel_override", "_cikis_ili_manuel", "_koli_palet_manuel"]).execute()
                for _row_ex in (_r_ex0.data or []):
                    st.session_state[_row_ex["anahtar"]] = _exj0.loads(_row_ex["deger"])
        except:
            pass
    _analiz_override = st.session_state.get("_analiz_manuel_override", {})
    _cikis_ili_map   = st.session_state.get("_cikis_ili_manuel", {})
    _koli_palet_map  = st.session_state.get("_koli_palet_manuel", {})

    try:
        # Analiz yapılmış firmaları işaretle
        try:
            _sb_an = get_sb_client()
            if _sb_an:
                _an_raw = _sb_an.table("musteri_analiz").select("firma").execute().data or []
                def _norm_firma(s):
                    return (str(s or "").strip()
                            .upper()
                            .replace("İ","I").replace("Ş","S").replace("Ğ","G")
                            .replace("Ü","U").replace("Ö","O").replace("Ç","C")
                            .replace("  "," "))
                _analiz_firma_list = [
                    _norm_firma(_ar.get("firma",""))
                    for _ar in _an_raw
                    if _ar.get("firma")
                ]
                _analiz_firma_set = set(_analiz_firma_list)
                def _analiz_esles(firma_adi):
                    _n = _norm_firma(firma_adi)
                    if not _n:
                        return ""
                    # 1) Tam eşleşme
                    if _n in _analiz_firma_set:
                        return "✅"
                    # 2) Kısmi eşleşme — biri diğerinin içinde mi
                    for _af in _analiz_firma_list:
                        if not _af:
                            continue
                        if _n in _af or _af in _n:
                            return "✅"
                        # 3) İlk 8 karakter eşleşmesi
                        if len(_n) >= 8 and len(_af) >= 8 and _n[:8] == _af[:8]:
                            return "✅"
                    return ""
                df_edit["✅ Analiz"] = df_edit["firma"].apply(_analiz_esles)
            else:
                df_edit["✅ Analiz"] = ""
        except Exception as _ane:
            df_edit["✅ Analiz"] = ""
    except:
        df_edit["✅ Analiz"] = ""

    # Manuel Analiz override — otomatik eşleşme olmasa bile hücreye bir şey
    # yazılırsa (örn. "." veya "ok") ✅ ikonu manuel olarak gösterilir. Ayrıca
    # Varış İli veya Koli/Palet'e bir şey yazılırsa (Analiz'e hiç dokunulmasa
    # bile) "analiz yapılmış" kabul edilip ✅ otomatik gösterilir.
    if "id" in df_edit.columns:
        df_edit["Varış İli"] = [(_cikis_ili_map.get(str(int(rid)), "") or "") for rid in df_edit["id"]]
        df_edit["Koli/Palet"] = [(_koli_palet_map.get(str(int(rid)), "") or "") for rid in df_edit["id"]]
        df_edit["✅ Analiz"] = [
            ("✅" if (str(int(rid)) in _analiz_override or str(otomatik or "").strip()
                      or str(varis or "").strip() or str(koli or "").strip()) else "")
            for rid, otomatik, varis, koli in zip(df_edit["id"], df_edit["✅ Analiz"], df_edit["Varış İli"], df_edit["Koli/Palet"])
        ]
    else:
        df_edit["Varış İli"] = ""
        df_edit["Koli/Palet"] = ""

    _not_detay = {}
    _not_sayac = {}
    if sb_liste:
        try:
            @st.cache_data(ttl=60, show_spinner=False)
            def _tum_notlari_yukle():
                _sb2 = get_sb_client()
                if _sb2:
                    _r2 = _sb2.table("cari_aciklamalar").select("*").execute()
                    return _r2.data or []
                return []
            _res_notlar_data = _tum_notlari_yukle()
            # NOT: Yetkililer sekmesi de aynı cari_aciklamalar tablosuna "##YETKILI##"
            # etiketiyle kayıt atıyor — bunlar gerçek not değil, rozet sayısına dahil
            # edilmemeli (Notlar penceresindeki sayıyla tutarlı olsun diye).
            _res_notlar_data = [r for r in _res_notlar_data
                                 if not str(r.get("aciklama","") or "").startswith("##YETKILI##")]
            if _res_notlar_data:
                import collections
                _not_sayac = collections.Counter([str(r["cari_id"]) for r in _res_notlar_data])
                for _nr in _res_notlar_data:
                    _ncid = str(_nr.get("cari_id",""))
                    if _ncid not in _not_detay:
                        _not_detay[_ncid] = []
                    _not_detay[_ncid].append({
                        "id": _nr.get("id",""),
                        "tarih": fmt_tarih(_nr.get("created_at","") or _nr.get("tarih","")),
                        "kim": str(_nr.get("olusturan","") or ""),
                        "metin": str(_nr.get("aciklama","") or ""),
                    })
                if "id" in df_edit.columns:
                    df_edit["📨 Notlar"] = df_edit["id"].apply(lambda x: f"📨 {_not_sayac.get(str(int(x)),0)}" if _not_sayac.get(str(int(x)),0) > 0 else "")
                else:
                    df_edit["📨 Notlar"] = ""
                # NOT: burada eskiden "_not_sayi"ye göre azalan sıralama yapılıyordu.
                # Bu sıralama not sayısı DEĞİŞTİKÇE (yani tam olarak bir not kaydedince)
                # satır sırasını kaydırıyordu — ve "Seç" işareti Streamlit'te satır
                # POZİSYONUNA göre tutulduğu için, sıra kayınca işaret başka bir
                # müşteriye "geçmiş" gibi görünüyordu. Sıralama kaldırıldı ki satır
                # sırası bir işlemden diğerine SABİT kalsın, Seç işareti doğru
                # müşteride kalsın.
            else:
                df_edit["📨 Notlar"] = ""
        except Exception as _not_err:
            df_edit["📨 Notlar"] = ""
            st.warning(f"Not yükleme hatası: {_not_err}")
    else:
        df_edit["📨 Notlar"] = ""

    # ── Manuel Teklif/Mesaj override'ları — DB'den yükle (bir kere) ──
    if "_teklif_manuel_override" not in st.session_state or "_mesaj_manuel_override" not in st.session_state:
        st.session_state["_teklif_manuel_override"] = {}
        st.session_state["_mesaj_manuel_override"] = {}
        try:
            _sb_ov0 = get_sb_client()
            if _sb_ov0:
                import json as _ovj0
                _r_ov0 = _sb_ov0.table("kullanici_tercih").select("anahtar,deger").eq("kullanici","__liste_ui__").in_(
                    "anahtar", ["_teklif_manuel_override", "_mesaj_manuel_override"]).execute()
                for _row_ov in (_r_ov0.data or []):
                    st.session_state[_row_ov["anahtar"]] = _ovj0.loads(_row_ov["deger"])
        except:
            pass
    _teklif_override = st.session_state.get("_teklif_manuel_override", {})
    _mesaj_override  = st.session_state.get("_mesaj_manuel_override", {})

    # ── Cari kartında GERÇEKTEN yapılan her kaydetme (aşama/durum/alan
    # değişikliği vb.) burada iz bırakır — "Güncelleme Tarihi" bunun üzerinden
    # hesaplanır. cari_kartlar'da updated_at kolonu/tetikleyicisi olmadığı için
    # (yeni kolon açmadan) kullanici_tercih'te ayrı bir JSON haritada tutulur:
    # {cari_id_str: "YYYY-MM-DD HH:MM:SS"}.
    if "_cari_son_guncelleme" not in st.session_state:
        st.session_state["_cari_son_guncelleme"] = {}
        try:
            _sb_sg0 = get_sb_client()
            if _sb_sg0:
                import json as _sgj0
                _r_sg0 = _sb_sg0.table("kullanici_tercih").select("deger").eq(
                    "kullanici","__liste_ui__").eq("anahtar","_cari_son_guncelleme").execute()
                if _r_sg0.data:
                    st.session_state["_cari_son_guncelleme"] = _sgj0.loads(_r_sg0.data[0]["deger"])
        except:
            pass
    _cari_son_guncelleme = st.session_state.get("_cari_son_guncelleme", {})

    # ── Teklif sayısı (yeni sütun, Notlar ile aynı mantık) ──

    _tek_sayac_cl = {}
    if sb_liste:
        try:
            @st.cache_data(ttl=60, show_spinner=False)
            def _tum_teklif_sayac_yukle():
                _sb3 = get_sb_client()
                if _sb3:
                    _r3 = _sb3.table("teklifler").select("musteri_id").execute()
                    return _r3.data or []
                return []
            def _id_norm_cl(_v):
                _s = str(_v).strip()
                try:
                    return str(int(float(_s)))
                except Exception:
                    return _s
            _res_tek_data_cl = _tum_teklif_sayac_yukle()
            if _res_tek_data_cl:
                import collections as _coltek_cl
                _tek_sayac_cl = _coltek_cl.Counter([_id_norm_cl(r.get("musteri_id","")) for r in _res_tek_data_cl])
        except Exception:
            _tek_sayac_cl = {}
    if "id" in df_edit.columns:
        # Manuel override varsa onu göster, yoksa otomatik hesaplanan sayıyı göster
        df_edit["🧾 Teklif"] = df_edit["id"].apply(
            lambda x: (f"🧾 {_teklif_override.get(str(int(x)))}" if str(int(x)) in _teklif_override
            else (f"🧾 {_tek_sayac_cl.get(str(int(x)),0)}" if _tek_sayac_cl.get(str(int(x)),0) > 0 else "")))
    else:
        df_edit["🧾 Teklif"] = ""

    # ── Mesaj (yeni sütun) — gerçek WhatsApp/Email gönderim kayıtları (islem_kaydi
    # tablosu, musteri_id ile bağlı) — WhatsApp Teklif ve Email Teklif türleri sayılır ──
    _mesaj_sayac_cl = {}
    if sb_liste:
        try:
            @st.cache_data(ttl=60, show_spinner=False)
            def _tum_mesaj_sayac_yukle():
                _sb4 = get_sb_client()
                if _sb4:
                    _r4 = _sb4.table("islem_kaydi").select("musteri_id,islem_turu").in_(
                        "islem_turu", ["WhatsApp Teklif", "Email Teklif"]).execute()
                    return _r4.data or []
                return []
            _res_mesaj_data_cl = _tum_mesaj_sayac_yukle()
            if _res_mesaj_data_cl:
                import collections as _colmsg_cl
                _mesaj_sayac_cl = _colmsg_cl.Counter([str(r.get("musteri_id","")) for r in _res_mesaj_data_cl])
        except Exception:
            _mesaj_sayac_cl = {}
    if "id" in df_edit.columns:
        # Manuel override varsa onu göster, yoksa otomatik hesaplanan sayıyı göster
        df_edit["💬 Mesaj"] = df_edit["id"].apply(
            lambda x: (f"💬 {_mesaj_override.get(str(int(x)))}" if str(int(x)) in _mesaj_override
            else (f"💬 {_mesaj_sayac_cl.get(str(int(x)),0)}" if _mesaj_sayac_cl.get(str(int(x)),0) > 0 else "")))
    else:
        df_edit["💬 Mesaj"] = ""

    # ── İşlem Tarih — sadece tarih+saat gösterir, ham/karışık format değil ──
    if "tarih" in df_edit.columns:
        df_edit["tarih_ham_ilk_kayit"] = df_edit["tarih"]  # güncelleme hesabı için ham hali sakla
        df_edit["tarih"] = df_edit["tarih"].apply(fmt_tarih_saat)

    # ── Güncelleme Tarihi — bu müşteriye ait EN SON aktiviteyi gösterir:
    # yeni not/açıklama, yeni teklif, ya da mesaj/arama kaydı eklenmişse en
    # güncel tarih burada görünür. Hiçbiri yoksa ilk kayıt (İşlem Tarih) tarihi
    # gösterilir. cari_kartlar'da yeni kolon açmadan, mevcut ilişkili
    # tablolardan (cari_aciklamalar, teklifler, islem_kaydi) hesaplanır.
    @st.cache_data(ttl=60, show_spinner=False)
    def _son_aktivite_tarihleri_yukle():
        _sonuc = {}
        _sb5 = get_sb_client()
        if not _sb5:
            return _sonuc

        def _guncelle(_mid_ham, _tarih_ham):
            if not _mid_ham or not _tarih_ham:
                return
            _mid = str(_mid_ham)
            _yeni_dt = _guncelleme_tarih_parse(_tarih_ham)
            if _yeni_dt is None:
                return
            _mevcut_dt = _guncelleme_tarih_parse(_sonuc.get(_mid)) if _mid in _sonuc else None
            if _mevcut_dt is None or _yeni_dt > _mevcut_dt:
                _sonuc[_mid] = str(_tarih_ham)

        # 1) Notlar/açıklamalar — created_at Supabase'in otomatik alanı
        try:
            _r5 = _sb5.table("cari_aciklamalar").select("cari_id,created_at").execute()
            for _row in (_r5.data or []):
                _guncelle(_row.get("cari_id"), _row.get("created_at"))
        except Exception:
            pass

        # 2) Teklifler — created_at varsa kullan (tarih kolonu production'da güvenilir değil)
        try:
            _r6 = _sb5.table("teklifler").select("musteri_id,created_at").execute()
            for _row in (_r6.data or []):
                _guncelle(_row.get("musteri_id"), _row.get("created_at"))
        except Exception:
            pass

        # 3) Mesaj/arama/whatsapp kayıtları — islem_kaydi.tarih güvenilir
        try:
            _r7 = _sb5.table("islem_kaydi").select("musteri_id,tarih").execute()
            for _row in (_r7.data or []):
                _guncelle(_row.get("musteri_id"), _row.get("tarih"))
        except Exception:
            pass

        return _sonuc

    _son_aktivite = {}
    if sb_liste:
        try:
            _son_aktivite = _son_aktivite_tarihleri_yukle()
        except Exception:
            _son_aktivite = {}

    if "id" in df_edit.columns:
        def _guncelleme_tarihi_hesapla(_rid, _ilk_kayit_ham):
            _sid = str(int(_rid))
            _aday1 = _son_aktivite.get(_sid, "")          # not/teklif/mesaj kaydı
            _aday2 = _cari_son_guncelleme.get(_sid, "")   # gerçek alan/aşama/durum düzenlemesi
            _ilk = str(_ilk_kayit_ham or "")
            _adaylar = [t for t in [_aday1, _aday2, _ilk] if t]
            if not _adaylar:
                return ""
            # ÖNEMLİ: düz string karşılaştırması (max()) farklı tarih formatlarını
            # (ISO 'T' ayraçlı vs boşluklu) yanlış sıralıyordu — gerçek datetime'a
            # çevirip öyle karşılaştırıyoruz.
            _en_son = max(_adaylar, key=lambda t: _guncelleme_tarih_parse(t) or datetime.min)
            return fmt_tarih_saat(_en_son)
        df_edit["guncelleme_tarihi"] = [
            _guncelleme_tarihi_hesapla(rid, ilk) for rid, ilk in zip(df_edit["id"], df_edit.get("tarih_ham_ilk_kayit", df_edit["id"]*0))
        ]
    else:
        df_edit["guncelleme_tarihi"] = ""
    if "tarih_ham_ilk_kayit" in df_edit.columns:
        df_edit.drop(columns=["tarih_ham_ilk_kayit"], inplace=True)

    df_edit.insert(0, "Seç", False)

    import json as _json_ls

    # ── TÜMÜ GÖSTER — tablo sol, not paneli sağ ──────────────────────────────
    _kayitli_sira = st.session_state.get("_cl_kolon_sira", [])
    if _kayitli_sira and "🎨 Renk" in _kayitli_sira:
        # Renk artık ana tabloda bir sütun değil — eski kayıtlı sıralamada
        # kalmış olabilir, temizle (yoksa olmayan bir sütuna referans hatası verir).
        _kayitli_sira = [c for c in _kayitli_sira if c != "🎨 Renk"]
        st.session_state["_cl_kolon_sira"] = _kayitli_sira
        try:
            _sb_ko = get_sb_client()
            if _sb_ko:
                _sb_ko.table("kullanici_tercih").upsert({
                    "kullanici": "__liste_ui__", "anahtar": "_cl_kolon_sira",
                    "deger": json.dumps(_kayitli_sira)
                }, on_conflict="kullanici,anahtar").execute()
        except Exception:
            pass
    _aktif_col_order = _kayitli_sira if _kayitli_sira else col_order

    # ── KAYITLI SIRAYI GEÇERLİ/GÖRÜNÜR KOLONLARLA TEMİZLE ────────────────────
    # _kayitli_sira (kullanıcının sürükleyip kaydettiği kolon sırası) eski
    # olabilir: sonradan gizlenmiş bir kolonu hâlâ içerebilir, ya da sonradan
    # eklenmiş yeni bir kolonu (örn. Varış İli) hiç içermeyebilir. Bu durumda
    # "son kolon" araması aşağıda GERÇEKTE görünmeyen bir kolonu bulup onun
    # genişliğini kaldırıyordu — asıl görünen son kolon sabit genişlikte
    # kalıp sağda boşluk bırakıyordu. Burada kayıtlı sırayı güncel "col_order"
    # (görünür kolonlar) ile kesiştirip, yeni/eksik kolonları sona ekliyoruz.
    if _kayitli_sira:
        _kayitli_temiz = [c for c in _kayitli_sira if c in col_order]
        _eksik_yeni = [c for c in col_order if c not in _kayitli_temiz]
        _aktif_col_order = _kayitli_temiz + _eksik_yeni

    # "Rut" ve "Sektör" kullanıcı isteğiyle HER ZAMAN "Ara İşlem"in hemen
    # sağında olmalı — kayıtlı (sürükle-bırak ile özelleştirilmiş) eski sütun
    # sırası bunları tanımadığı için sona atabiliyordu; burada konumları
    # zorla düzeltilir (sıra: Ara İşlem, Sektör, Rut).
    if "sektor" in _aktif_col_order and "ara_islem" in _aktif_col_order:
        _aktif_col_order = [c for c in _aktif_col_order if c != "sektor"]
        _ai_pos2 = _aktif_col_order.index("ara_islem")
        _aktif_col_order.insert(_ai_pos2 + 1, "sektor")
    if "rut" in _aktif_col_order and "ara_islem" in _aktif_col_order:
        _aktif_col_order = [c for c in _aktif_col_order if c != "rut"]
        _ai_pos = _aktif_col_order.index("ara_islem")
        _aktif_col_order.insert(_ai_pos + 1, "rut")
    # "Hesaplama" da AYNI SEBEPLE (eski kayıtlı sütun sırası bu YENİ sütunu
    # tanımadığından, "eksik_yeni" mantığı onu EN SONA atıyordu — kullanıcı
    # bunu bulamıyordu) HER ZAMAN "Firma"nın hemen SOLUNA zorla yerleştirilir.
    if "hesaplama" in _aktif_col_order and "firma" in _aktif_col_order:
        _aktif_col_order = [c for c in _aktif_col_order if c != "hesaplama"]
        _fh_pos = _aktif_col_order.index("firma")
        _aktif_col_order.insert(_fh_pos, "hesaplama")

    # ── SAĞ TARAFTAKİ BOŞLUĞU KAPAT ─────────────────────────────────────────
    # Tüm kolonlara sabit piksel genişliği verildiğinde, toplam genişlik ekran
    # genişliğinden az kalırsa tablonun sağında boş bir alan kalıyordu (ekran
    # boyutuna göre değişiyordu). Çözüm: en sondaki GÖRÜNÜR kolonun piksel
    # genişliğini sabitlemiyoruz — Streamlit o kolonu kalan boş alanı
    # dolduracak şekilde otomatik büyütüyor, böylece hangi ekran/monitör
    # olursa olsun sağda boşluk kalmıyor.
    for _son_kol in reversed(_aktif_col_order):
        if _son_kol != "Seç" and _son_kol in col_config and isinstance(col_config[_son_kol], dict):
            col_config[_son_kol] = dict(col_config[_son_kol])
            col_config[_son_kol].pop("width", None)
            break

    # NOT: Eskiden burada notlu satırları sarı yapan bir CSS triki vardı
    # (ilk N satır notluydu, çünkü tablo not sayısına göre sıralanıyordu).
    # Sıralama kaldırıldığı için bu trik artık rastgele satırları sarı
    # yapardı — bu yüzden kaldırıldı. Notlu müşteriler "📨 Notlar" sütunundaki
    # sayıdan hâlâ görülebiliyor.

    # Sağda not paneli açık mı?
    _not_panel_id = st.session_state.get("_cl_not_panel_id")

    # ── KAYDET BUTONU — TABLONUN ÜSTÜNDE, STICKY ───────────────────────────────
    st.markdown("""<style>
.cl-sticky-bar{
    position: sticky; top: 0; z-index: 999;
    background: white; padding: 8px 0 6px;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 6px;
}
</style>""", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="cl-sticky-bar">', unsafe_allow_html=True)
        _sb1, _sb2, _sb3, _sb4, _sb5, _sb6, _sb7, _sb8 = st.columns([1.2, 0.9, 0.9, 1.1, 1.0, 1.1, 1.0, 1.3])
        with _sb1:
            if st.button("💾 Değişiklikleri Kaydet", type="primary", key="liste_kaydet_ust", use_container_width=True):
                st.session_state["_kaydet_flag"] = True
        with _sb2:
            if st.button("➕ Satır Ekle", key="cl_hizli_ekle_btn_ust", use_container_width=True):
                st.session_state["_cl_taslak_sayisi"] = st.session_state.get("_cl_taslak_sayisi", 0) + 1
                st.rerun()
        with _sb3:
            if st.button("🔄 Kolon Sıfırla", key="cl_kolon_sifirla_ust", use_container_width=True):
                st.session_state.pop("_cl_kolon_sira", None)
                st.rerun()
        with _sb4:
            # Gerçek .xlsx (openpyxl) — virgülle ayrılmış CSV DEĞİL, Excel'de doğrudan
            # sorunsuz açılan binary Excel formatı. Ekrandaki (filtrelenmiş) liste iner.
            import io as _cl_xio
            _cl_xl_buf = _cl_xio.BytesIO()
            df_f.to_excel(_cl_xl_buf, index=False, engine="openpyxl")
            _cl_xl_buf.seek(0)
            st.download_button("📥 Excel İndir", data=_cl_xl_buf,
                                file_name=f"cari_liste_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="cl_excel_indir_ust", use_container_width=True)
        # KULLANICI İSTEĞİ (2026-09): "☑️ Tümünü Seç" / "⬜ Seçimi Temizle"
        # artık AYRI bir satırda değil, aynı üst buton satırında.
        with _sb5:
            if st.button("☑️ Tümünü Seç", key="cl_tumunu_sec_btn", use_container_width=True):
                st.session_state["_cl_tumu_secili_mod"] = True
                st.session_state["_cl_tumu_haric_idler"] = set()
                st.session_state["_cl_editor_versiyon"] += 1
                st.rerun()
        with _sb6:
            if st.button("⬜ Seçimi Temizle", key="cl_secimi_temizle_btn", use_container_width=True):
                st.session_state["_cl_tumu_secili_mod"] = False
                st.session_state["_cl_tumu_haric_idler"] = set()
                st.session_state["_cl_editor_versiyon"] += 1
                st.rerun()
        with _sb7:
            # KULLANICI İSTEĞİ (2026-09): "🗑️ Seçili Kaydı Sil" de AYNI üst
            # satıra taşındı. Tablo henüz çizilmediği için kaç kaydın işaretli
            # olduğu burada BİLİNMİYOR — bu yüzden buton her zaman görünür,
            # tıklanınca sadece bir NİYET bayrağı ayarlar; gerçek silme,
            # tablo çizilip seçili sayısı netleşince (aşağıda) yapılır.
            if st.button("🗑️ Seçili Kaydı Sil", key="cl_sil_niyet_btn", use_container_width=True):
                st.session_state["_cl_sil_niyeti"] = True
        with _sb8:
            # KULLANICI İSTEĞİ (2026-09, DÜZELTİLDİ): işaretli/işaretsiz bir
            # kutu DEĞİL — tıklanınca AYRI bir pencerede arşivi açan buton.
            # Ana liste bundan HİÇ etkilenmez, her zaman normal (arşivsiz)
            # haliyle kalır. KALICI BAYRAK (bkz. not_dialog benzeri düzeltme):
            # pencere içinde "Geri Al" gibi bir işlem yapılıp sayfa yenilense
            # bile, "❌ Kapat"a basılana kadar açık kalır.
            if st.button("📦 Arşiv", key="cl_arsiv_ac_btn", use_container_width=True):
                st.session_state["_cl_arsiv_penceresi_acik"] = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        if st.session_state.get("_cl_arsiv_penceresi_acik", False):
            _cari_arsiv_goruntule_dialog()


    _tbl_col = st.container()
    _not_col = None

    # ── TASLAK SATIR(LAR) — "➕ Satır Ekle" ile açılan, henüz DB'ye YAZILMAMIŞ
    # boş satır(lar). id=0 ile işaretlenir. Firma alanı doldurulup "Kaydet"
    # edilirse gerçek bir müşteri kaydı oluşturulur (kaydetmezsen hiçbir şey
    # yazılmaz).
    # ÖNEMLİ (kritik veri kaybı hatası düzeltmesi): Eskiden bu blok bir BOOLEAN
    # bayrağa (_cl_taslak_aktif) bakıyordu ve bayrak True olduğu SÜRECE HER
    # rerun'da (yani kullanıcı bir hücreye yazıp Tab/Enter'a bastığında bile)
    # YENİDEN bir boş satır ekliyordu. Bu da her hücre düzenlemesinde tabloya
    # yeni bir boş satır girip önceki satırları kaydırıyordu — kullanıcının o
    # ana kadar yazdığı bilgiler artık YANLIŞ satıra karışıyor, bazı hücreler
    # kaybolmuş gibi görünüyordu. Şimdi kaç taslak satır isteneceği SABİT bir
    # sayaçta (_cl_taslak_sayisi) tutuluyor — bu sayaç SADECE "Satır Ekle"
    # butonuna basınca 1 artıyor, başka hiçbir rerun'da değişmiyor. Böylece
    # satır sayısı ve sırası, kullanıcı yazarken stabil kalıyor.
    _cl_taslak_sayisi = int(st.session_state.get("_cl_taslak_sayisi", 0) or 0)
    if _cl_taslak_sayisi > 0:
        _tas_bos_liste = []
        for _ in range(_cl_taslak_sayisi):
            _tas_bos = {c: "" for c in df_edit.columns}
            _tas_bos["id"] = 0
            if "Seç" in df_edit.columns:
                _tas_bos["Seç"] = False
            if "beklenen_ciro" in df_edit.columns:
                _tas_bos["beklenen_ciro"] = 0
            if "gerceklesen_ciro" in df_edit.columns:
                _tas_bos["gerceklesen_ciro"] = 0
            _tas_bos_liste.append(_tas_bos)
        df_edit = pd.concat([pd.DataFrame(_tas_bos_liste), df_edit], ignore_index=True)

    # Tablo yüksekliğini görünen satır sayısına göre hesapla — sabit 800px'lik
    # yükseklik, sayfa başına 12 satır varken altında boş satırlar bırakıyordu.
    # "Tümü" modunda (binlerce satır) yükseklik 800px'de sabit kalıp iç kaydırma kullanır.
    _cl_editor_yukseklik = min(800, 38 + (len(df_edit) * 35) + 3)

    # ── Sol Index Kolonu — "Sıra No" başlıklı, temiz sıralı (1,2,3...) numara.
    # Streamlit'te index kolonu zaten otomatik olarak sol tarafta SABİT kalır
    # (kaydırmada kaymaz). Eskiden burada firma id'sinin ham/karışık index'i
    # görünüyordu (17, 1692, 0, 5...) — artık temiz 1'den başlayan sıra no var.
    # 🚨 DÜZELTME (2026-09): kullanıcı hâlâ karışık (1688, 3589, 862...) sıra
    # numaraları gördüğünü bildirdi — "reset_index(drop=True)" bazı özel
    # durumlarda (ör. Çoklu Firma karşılaştırma modu) beklendiği gibi
    # davranmıyor olabilir. Artık index'i SIFIRLAMAYA güvenmek yerine,
    # DOĞRUDAN 1'den len(df_edit)'e kadar bir sıra ATANIYOR — bu, önceki
    # index'in ne olduğundan TAMAMEN bağımsız, HER ZAMAN garanti 1,2,3...
    df_edit = df_edit.reset_index(drop=True)
    df_edit.index = range(1, len(df_edit) + 1)
    df_edit.index.name = "S.No"

    # ── "☑️ Tümünü Seç" / "⬜ Seçimi Temizle" — KULLANICI İSTEĞİ (2026-09):
    # tek tek işaretlemek yerine tüm (o an filtrede görünen) müşterileri bir
    # tıkla seçebilmek için.
    # 🚨 KRİTİK GÜVENLİK DÜZELTMESİ #2 (2026-09): "tek seferlik" yöntem YANLIŞTI
    # — Streamlit her render'da "Seç" tabanını (df_edit'ten) TAZE alıp
    # kullanıcının o anki tek tıklamasıyla birleştiriyor; taban bir dahaki
    # render'da (tek seferlik olduğu için) varsayılan (boş/işaretsiz) haline
    # dönünce, SADECE senin dokunduğun satır değil, DOKUNMADIĞIN TÜM satırlar
    # da işaretsiz görünüyordu ("hepsini kaldırıyor" sorunu buydu).
    # ŞİMDİ DOĞRU YÖNTEM: hangi id'lerin HARİÇ TUTULDUĞU (senin elle
    # kaldırdıkların) kalıcı bir kümede (session_state) tutuluyor. HER
    # render'da taban, bu kümeye göre yeniden kuruluyor (hariç tutulanlar
    # işaretsiz, diğerleri işaretli) — ve render SONRASI, o anki gerçek
    # işaretli/işaretsiz durum bu kümeye TAM olarak senkronize ediliyor
    # (yeniden işaretlersen kümeden çıkar, kaldırırsan kümeye girer).
    st.session_state.setdefault("_cl_editor_versiyon", 0)
    st.session_state.setdefault("_cl_tumu_haric_idler", set())
    if st.session_state.get("_cl_tumu_secili_mod", False) and "id" in df_edit.columns:
        _cl_haric = st.session_state["_cl_tumu_haric_idler"]
        _cl_id_sayisal = pd.to_numeric(df_edit["id"], errors="coerce").fillna(-1).astype(int)
        df_edit["Seç"] = ~_cl_id_sayisal.isin(_cl_haric)
    _cl_editor_key = f"cari_editor_{st.session_state['_cl_editor_versiyon']}"

    # ── KALICI KURAL 3c UYGULAMASI (2026-09 düzeltmesi): "Hiçbir Yerde None
    # Yazısı Gösterilmeyecek" kuralı yazılmıştı ama Cari Liste'nin ANA
    # tablosuna hiç UYGULANMAMIŞTI — kullanıcı hücrelerde "None" gördüğünü
    # bildirdi. Şimdi uygulanıyor — AMA GÜVENLİK İÇİN SADECE METİN
    # sütunlarına (sayısal sütunlara DEĞİL): test ettim, sayısal bir
    # sütunda (örn. Gerçek ₺) gerçek bir boş (NaN) değer varsa, bu temizlik
    # onu metne çevirip sütunun sayısal tipini bozabiliyordu (NumberColumn
    # hata verebilirdi) — bu riski almamak için sayısal/onay-kutusu
    # sütunları hariç tutuluyor, davranış/hız hiç değişmiyor.
    _cl_sayisal_disi_kolonlar = [c for c in df_edit.columns if c not in ("id", "beklenen_ciro", "gerceklesen_ciro", "Seç")]
    if _cl_sayisal_disi_kolonlar:
        df_edit[_cl_sayisal_disi_kolonlar] = _hic_none_gosterme(df_edit[_cl_sayisal_disi_kolonlar])

    with _tbl_col:
        edited_df = st.data_editor(
            df_edit,
            use_container_width=True,
            num_rows="fixed",
            column_config=col_config,
            column_order=_aktif_col_order,
            height=_cl_editor_yukseklik,
            key=_cl_editor_key
        )
        # Render SONRASI: gerçek işaretli/işaretsiz durumu "hariç tutulanlar"
        # kümesine TAM senkronize et — bir dahaki render'da doğru taban
        # buradan yeniden kurulacak.
        if st.session_state.get("_cl_tumu_secili_mod", False) and "id" in edited_df.columns:
            _cl_id_sayisal2 = pd.to_numeric(edited_df["id"], errors="coerce").fillna(-1).astype(int)
            st.session_state["_cl_tumu_haric_idler"] = set(
                _cl_id_sayisal2[edited_df["Seç"] == False].tolist()
            )

    # (not paneli artık tablonun altında expander olarak açılıyor)


    # Kolon sırası değiştiyse kaydet — hem session_state hem DB
    try:
        _editor_meta = st.session_state.get(_cl_editor_key, {})
        _col_order_now = _editor_meta.get("column_order", [])
        if _col_order_now and _col_order_now != st.session_state.get("_cl_kolon_sira"):
            st.session_state["_cl_kolon_sira"] = _col_order_now
            try:
                _sb_ko = get_sb_client()
                if _sb_ko:
                    import json as _koj
                    _sb_ko.table("kullanici_tercih").upsert({
                        "kullanici":"__liste_ui__","anahtar":"_cl_kolon_sira",
                        "deger":_koj.dumps(_col_order_now, ensure_ascii=False)
                    }, on_conflict="kullanici,anahtar").execute()
            except: pass
    except: pass

    # İlk yüklemede kolon sırasını DB'den al
    if "_cl_kolon_sira_init" not in st.session_state:
        try:
            _sb_ki = get_sb_client()
            if _sb_ki:
                import json as _kij
                _r_ko = _sb_ki.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_cl_kolon_sira").execute()
                if _r_ko.data:
                    st.session_state["_cl_kolon_sira"] = _kij.loads(_r_ko.data[0]["deger"])
        except: pass
        st.session_state["_cl_kolon_sira_init"] = True

    # Her render'da tüm tabloyu session_state'e kaydet
    try:
        _kv = edited_df.copy()
        if "aciklama" not in _kv.columns:
            _kv["aciklama"] = ""
        _kv["aciklama"] = _kv["aciklama"].fillna("").astype(str).replace("nan","")
        _kayit_kolonlar = ["id","firma","yetkili","gsm","sabit","email","il","ilce","durum","temsilci","islem_asamasi","aciklama","asama1","asama2","asama3","sonuc"]
        _mevcut = [c for c in _kayit_kolonlar if c in _kv.columns]
        st.session_state["_ls_tablo"] = _kv[_mevcut].to_json(orient="records", force_ascii=False)
    except:
        pass

    # NOT: Burada eskiden "anında not arşivleme" vardı — Açıklama hücresine her
    # yazıldığında (Kaydet'e basılmadan) otomatik olarak sorgu atıp sayfayı
    # yeniliyordu. Bu, kullanıcı henüz TÜM değişikliklerini bitirmeden ekranın
    # yanıp sönmesine ve işlemin yarıda kalmasına sebep oluyordu. Kaldırıldı —
    # artık hiçbir şey otomatik çalışmıyor, arşivleme sadece "Değişiklikleri
    # Kaydet" butonuna basılınca yapılıyor.

    secili_df = edited_df[edited_df["Seç"] == True]
    secili_sayi = len(secili_df)
    secili_idler = secili_df["id"].tolist() if not secili_df.empty else []

    # ── "Seç" işaretli firmaları taslak olarak kaydetme paneli kullanıcı
    # isteğiyle kaldırıldı (arşivleme/silme butonlarıyla birlikte, aşağıda) ──

    # ── NOT DİALOG — KULLANICI İSTEĞİ (2026-09, GÜNCELLENDİ): "Seç" kutusunu
    # işaretleyince pencere açılır ve — işlemler bitmeden sayfa yenilense,
    # "Seç" kutusu her ne sebeple sıfırlansa bile — SADECE kullanıcı "❌ Bu
    # Pencereyi Kapat"a basınca kapanır. Kapatıldıktan sonra, "Seç" kutusu
    # HÂLÂ işaretli kalmış olsa bile pencere KENDİLİĞİNDEN tekrar açılmaz —
    # kullanıcı BİLEREK yeniden Seç'e basmadıkça (kutuyu kaldırıp tekrar
    # işaretlemedikçe) bir daha görünmez. Bu, hem "yenilesem bile açık
    # kalsın" hem "kapatınca kendi kendine açılmasın" isteklerini birlikte
    # karşılar.
    if secili_sayi == 1:
        _sel_id = int(secili_idler[0])
        if st.session_state.get("_not_dialog_son_kapatilan_id") != _sel_id:
            _sel_rows = df_edit[df_edit["id"] == _sel_id]
            _sel_firma = str(_sel_rows.iloc[0].get("firma","")) if not _sel_rows.empty else ""
            not_dialog(_sel_id, _sel_firma)
    elif st.session_state.get("_not_dialog_kalici_id"):
        not_dialog(st.session_state["_not_dialog_kalici_id"], st.session_state.get("_not_dialog_kalici_firma", ""))
    else:
        # Hiçbir şey seçili değil VE pencere kalıcı olarak da açık değilse —
        # "kapatılan" hafızasını da temizle, böylece BİR SONRAKİ kez aynı
        # müşteriyi seçtiğinde pencere yine normal şekilde açılabilsin.
        st.session_state.pop("_not_dialog_son_kapatilan_id", None)


    # ── BUTONLAR ──────────────────────────────────────────────────────────────
    # NOT: "Değişiklikleri Kaydet" ve "Kolon Sıfırla" butonları artık SADECE
    # üst toolbar'da (sticky bar) gösteriliyor — burada tekrar render edilmiyor,
    # ama kaydetme mantığı (_kaydet_flag üzerinden) aynen çalışmaya devam ediyor.
    btn_k, btn_a, btn_s, btn_kolon = st.columns(4)
    _do_kaydet = st.session_state.pop("_kaydet_flag", False)
    with btn_k:
        if _do_kaydet:
            _editor_state = st.session_state.get(_cl_editor_key, {})
            _edited_rows  = dict(_editor_state.get("edited_rows", {}))
            # ── GÜVENLİK AĞI: session_state'teki edited_rows bazen son hücreyi
            # kaçırabiliyor (widget'ın kendi zamanlama davranışı). Bu yüzden HER
            # zaman df_edit ile edited_df'i satır satır karşılaştırıp gerçek
            # farkı da hesaplıyoruz ve edited_rows ile BİRLEŞTİRİYORUZ — sadece
            # edited_rows boşsa değil, her durumda. edited_df zaten ekranda o an
            # görünen/kaydedilmiş son hâl olduğu için bu karşılaştırma en güvenilir
            # kaynak.
            # 🚨 KRİTİK DÜZELTME (2026-09): eskiden TÜM karşılaştırma TEK bir
            # try/except içindeydi — TEK bir satırda/sütunda (ör. yeni eklenen
            # bir sütunda) küçük bir uyumsuzluk olursa, o noktadan SONRAKİ TÜM
            # satırların güvenlik ağı sessizce devre dışı kalıyordu. Bu da
            # "birden fazla satırı birden düzenleyince sadece biri kaydediliyor"
            # sorununun kök nedeniydi. Şimdi HER HÜCRE ayrı ayrı korunuyor —
            # bir hücrede sorun olsa bile diğer TÜM satır/sütunlar etkilenmez.
            if "edited_df" in dir():
                try:
                    _orig = df_edit.reset_index(drop=True)
                    _ed   = edited_df.reset_index(drop=True)
                    _ortak_kolonlar = [c for c in _ed.columns if c in _orig.columns]
                    for _ei in range(min(len(_orig), len(_ed))):
                        _rd = dict(_edited_rows.get(str(_ei), {}))
                        for _ec in _ortak_kolonlar:
                            try:
                                if str(_orig.at[_ei,_ec]) != str(_ed.at[_ei,_ec]):
                                    _rd[_ec] = _ed.at[_ei,_ec]
                            except Exception:
                                continue  # SADECE bu hücre atlanır, diğer satır/sütunlar etkilenmez
                        if _rd: _edited_rows[str(_ei)] = _rd
                except Exception:
                    pass
            _tablo_json   = st.session_state.get("_ls_tablo")
            kayit_sayi = 0
            hata_list  = []
            if not _edited_rows:
                st.info("Değişiklik yok.")
            else:
              with st.spinner(f"💾 {len(_edited_rows)} satır kaydediliyor..."):
                try:
                    _rows = _json_ls.loads(_tablo_json) if _tablo_json else []
                except:
                    _rows = []

                # ── TASLAK SATIRLAR (id=0) işleme — "Satır Ekle" ile açılan boş
                # satır(lar) burada gerçek kayda dönüşür. Firma alanı hâlâ boşsa
                # o taslak için hiçbir şey yapılmaz, ekranda kalmaya devam eder.
                # ÖNEMLİ (hata düzeltmesi): Eskiden kod sadece İLK id=0 satırını
                # işleyip duruyordu (break ile) — birden fazla yeni satır eklenip
                # doldurulduğunda ikinciden itibaren TÜMÜ sessizce kayboluyordu.
                # Şimdi TÜM id=0 satırları tek tek işleniyor, hiçbiri atlanmıyor.
                _taslak_idxler = []
                for _ti, _trow in enumerate(_rows):
                    try:
                        if int(float(str(_trow.get("id", -1)))) == 0:
                            _taslak_idxler.append(_ti)
                    except Exception:
                        continue
                _taslak_basarili_sayisi = 0
                for _taslak_idx in _taslak_idxler:
                    _taslak_idx_str = str(_taslak_idx)
                    _taslak_firma = ""
                    _ed_tas = None
                    if "edited_df" in dir():
                        try:
                            _ed_tas = edited_df.reset_index(drop=True)
                            if _taslak_idx < len(_ed_tas) and "firma" in _ed_tas.columns:
                                _taslak_firma = str(_ed_tas.at[_taslak_idx, "firma"] or "").strip()
                        except Exception:
                            _ed_tas = None
                    if not _taslak_firma:
                        # Firma boş — DB'ye hiçbir şey yazma, taslağı olduğu gibi bırak
                        _edited_rows.pop(_taslak_idx_str, None)
                    else:
                        def _tas_al(_kol, _varsayilan="", _idx=_taslak_idx, _df=_ed_tas):
                            try:
                                if _df is not None and _kol in _df.columns:
                                    _v = _df.at[_idx, _kol]
                                    return str(_v) if _v not in [None, "nan", "None"] else _varsayilan
                            except Exception:
                                pass
                            return _varsayilan
                        _yeni_kayit = {
                            "tarih": datetime.now().isoformat(),
                            "firma": _taslak_firma,
                            "rakip_firma": _tas_al("rakip_firma"),
                            "yetkili": _tas_al("yetkili"),
                            "gsm": _tas_al("gsm").strip(),
                            "sabit": _tas_al("sabit").strip(),
                            "email": _tas_al("email"),
                            "adres": _tas_al("adres"),
                            "ilce": _tas_al("ilce"),
                            "il": _tas_al("il", "İstanbul"),
                            "durum": _tas_al("durum", "Portföy"),
                            "temsilci": _tas_al("temsilci", st.session_state.get("kullanici","")),
                            "islem_asamasi": _tas_al("islem_asamasi"),
                            "segment": "--",
                            "aciklama": _tas_al("aciklama"),
                            "silindi": 0, "olusturan": st.session_state.get("kullanici",""),
                            "beklenen_ciro": 0, "gerceklesen_ciro": 0,
                            "atanan_kullanici": st.session_state.get("kullanici","")
                        }
                        _taslak_basarili = False
                        _taslak_hata = ""
                        try:
                            _sb_tas = get_sb_client()
                            if _sb_tas:
                                _res_tas = _sb_tas.table("cari_kartlar").insert(_yeni_kayit).execute()
                                _taslak_basarili = bool(_res_tas.data)
                            else:
                                _taslak_hata = "Supabase bağlantısı yok."
                        except Exception as _tas_e:
                            _taslak_hata = str(_tas_e)
                        if _taslak_basarili:
                            kayit_sayi += 1
                            _taslak_basarili_sayisi += 1
                            try: get_cari_listesi.clear()
                            except: pass
                        else:
                            hata_list.append(f"Yeni satır ({_taslak_firma}): {_taslak_hata}")
                        _edited_rows.pop(_taslak_idx_str, None)
                if _taslak_basarili_sayisi:
                    # Sadece BAŞARIYLA kaydedilen taslak sayısı kadar azalt —
                    # firma alanı boş bırakılan taslak(lar) ekranda kalmaya devam etsin.
                    st.session_state["_cl_taslak_sayisi"] = max(0, _cl_taslak_sayisi - _taslak_basarili_sayisi)

                # ── Teklif/Mesaj manuel override'ları — cari_kartlar'da bu isimde
                # kolon yok, bu yüzden ayrı kullanici_tercih JSON'unda saklanır.
                # Hücre boş bırakılırsa override silinir, otomatik sayı geri döner.
                _teklif_ov_guncel = dict(st.session_state.get("_teklif_manuel_override", {}))
                _mesaj_ov_guncel  = dict(st.session_state.get("_mesaj_manuel_override", {}))
                _ov_degisti = False
                for _idx_str_ov, _deg_ov in _edited_rows.items():
                    _idxn_ov = int(_idx_str_ov)
                    if _idxn_ov >= len(_rows):
                        continue
                    _rid_ov = int(float(str(_rows[_idxn_ov].get("id", 0))))
                    if not _rid_ov:
                        continue
                    if "🧾 Teklif" in _deg_ov:
                        _v_ov_ham = str(_deg_ov["🧾 Teklif"] or "")
                        _v_ov = "".join(ch for ch in _v_ov_ham if ch.isdigit())  # sadece rakam — ikon zaten otomatik eklenir
                        if _v_ov:
                            _teklif_ov_guncel[str(_rid_ov)] = _v_ov
                        else:
                            _teklif_ov_guncel.pop(str(_rid_ov), None)
                        _ov_degisti = True
                    if "💬 Mesaj" in _deg_ov:
                        _v_ov_ham = str(_deg_ov["💬 Mesaj"] or "")
                        _v_ov = "".join(ch for ch in _v_ov_ham if ch.isdigit())  # sadece rakam — ikon zaten otomatik eklenir
                        if _v_ov:
                            _mesaj_ov_guncel[str(_rid_ov)] = _v_ov
                        else:
                            _mesaj_ov_guncel.pop(str(_rid_ov), None)
                        _ov_degisti = True
                if _ov_degisti:
                    st.session_state["_teklif_manuel_override"] = _teklif_ov_guncel
                    st.session_state["_mesaj_manuel_override"] = _mesaj_ov_guncel
                    try:
                        _sb_ov1 = get_sb_client()
                        if _sb_ov1:
                            import json as _ovj1
                            _sb_ov1.table("kullanici_tercih").upsert([
                                {"kullanici": "__liste_ui__", "anahtar": "_teklif_manuel_override",
                                 "deger": _ovj1.dumps(_teklif_ov_guncel, ensure_ascii=False)},
                                {"kullanici": "__liste_ui__", "anahtar": "_mesaj_manuel_override",
                                 "deger": _ovj1.dumps(_mesaj_ov_guncel, ensure_ascii=False)},
                            ], on_conflict="kullanici,anahtar").execute()
                    except:
                        pass
                    # Üst AŞAMA raporundaki Mesaj toplam kutusu ve 2.AŞAMA'daki
                    # Teklif firma sayısı 60 sn önbellekli — kaydettikten hemen
                    # sonra güncel görünsün diye önbellek burada da temizlenir.
                    try: _rbar_mesaj_toplam_yukle.clear()
                    except: pass
                    try: _rbar_teklif_toplam_yukle.clear()
                    except: pass

                # ── Analiz / Çıkış İli / Koli-Palet manuel override'ları ────────────────
                _analiz_ov_guncel = dict(st.session_state.get("_analiz_manuel_override", {}))
                _cikis_ov_guncel  = dict(st.session_state.get("_cikis_ili_manuel", {}))
                _koli_ov_guncel   = dict(st.session_state.get("_koli_palet_manuel", {}))
                _icy_etkilenen_idler = set()  # KULLANICI İSTEĞİ (2026-09): "İl Ciroları" — Koli/Palet değişen satırlar
                _ex_degisti = False
                for _idx_str_ex, _deg_ex in _edited_rows.items():
                    _idxn_ex = int(_idx_str_ex)
                    if _idxn_ex >= len(_rows):
                        continue
                    _rid_ex = int(float(str(_rows[_idxn_ex].get("id", 0))))
                    if not _rid_ex:
                        continue
                    if "✅ Analiz" in _deg_ex:
                        _v_ex = str(_deg_ex["✅ Analiz"] or "").strip()
                        if _v_ex:
                            _analiz_ov_guncel[str(_rid_ex)] = "1"
                        else:
                            _analiz_ov_guncel.pop(str(_rid_ex), None)
                        _ex_degisti = True
                    if "Varış İli" in _deg_ex:
                        _v_ex = str(_deg_ex["Varış İli"] or "").strip()
                        if _v_ex:
                            _cikis_ov_guncel[str(_rid_ex)] = _v_ex
                        else:
                            _cikis_ov_guncel.pop(str(_rid_ex), None)
                        _ex_degisti = True
                    if "Koli/Palet" in _deg_ex:
                        _v_ex = str(_deg_ex["Koli/Palet"] or "").strip()
                        if _v_ex:
                            _koli_ov_guncel[str(_rid_ex)] = _v_ex
                        else:
                            _koli_ov_guncel.pop(str(_rid_ex), None)
                        _ex_degisti = True
                        _icy_etkilenen_idler.add(_rid_ex)
                    # ── 🆕 YENİ ÖZELLİK (2026-09, KULLANICI İSTEĞİ): "Hesaplama"
                    # hücresine (Firma'nın solunda) Şehir/Desi/Fiyat yapıştırılıp
                    # kaydedilince, "Seç" penceresindeki "🎯 Hepsini Yerleştir"
                    # ile AYNI 6 işlemi (Ayrıştır + İl İşaretleme + Hedeflenen
                    # Ciro + İl Ciroları + Teklif Fiyat + Koli/Palet kaydet)
                    # SEÇSİZ, doğrudan bu satır üzerinde çalıştırır. Yeni veri
                    # ESKİNİN ÜZERİNE YAZAR (birleştirmez). "Seç" penceresindeki
                    # koda HİÇ dokunulmadı, o aynen çalışmaya devam ediyor.
                    # 🚨 DÜZELTME: eskiden "Fiyatlandırma" diye VAR OLMAYAN
                    # (col_config'de hiç tanımlanmamış, kullanıcının hiç
                    # göremediği) bir sütuna bağlıydı — o yüzden hiç
                    # çalışmıyordu. Artık gerçekten var olan "Hesaplama"
                    # sütununa (Firma'nın solunda, Kolon Ayarları'nda da
                    # görünür) bağlı.
                    if "hesaplama" in _deg_ex:
                        _v_fiyat = str(_deg_ex["hesaplama"] or "").strip()
                        if _v_fiyat:
                            _fyat_firma_adi = str(_rows[_idxn_ex].get("firma", "")) if _idxn_ex < len(_rows) else ""
                            _fyat_basarili, _fyat_mesaj = _fy_hepsini_yerlestir_ana_tablo(_rid_ex, _v_fiyat, _fyat_firma_adi)
                            if _fyat_basarili:
                                st.toast(f"🎯 {_fyat_mesaj}", icon="✅")
                            else:
                                st.toast(f"⚠️ {_fyat_firma_adi or _rid_ex}: {_fyat_mesaj}", icon="⚠️")
                            # KRİTİK: yukarıdaki fonksiyon "_koli_palet_manuel"yi
                            # DOĞRUDAN kaydetti — buradaki ESKİ (fonksiyon
                            # çalışmadan ÖNCE alınmış) kopyayı GÜNCEL haliyle
                            # senkronize ediyoruz, yoksa aşağıdaki toplu kayıt
                            # bu satırın YENİ verisinin ÜZERİNE ESKİ veriyi
                            # yazıp SİLERDİ.
                            _koli_ov_guncel = dict(st.session_state.get("_koli_palet_manuel", _koli_ov_guncel))
                            _ex_degisti = True
                if _ex_degisti:
                    st.session_state["_analiz_manuel_override"] = _analiz_ov_guncel
                    st.session_state["_cikis_ili_manuel"] = _cikis_ov_guncel
                    st.session_state["_koli_palet_manuel"] = _koli_ov_guncel
                    try:
                        _sb_ex1 = get_sb_client()
                        if _sb_ex1:
                            import json as _exj1
                            _sb_ex1.table("kullanici_tercih").upsert([
                                {"kullanici": "__liste_ui__", "anahtar": "_analiz_manuel_override",
                                 "deger": _exj1.dumps(_analiz_ov_guncel, ensure_ascii=False)},
                                {"kullanici": "__liste_ui__", "anahtar": "_cikis_ili_manuel",
                                 "deger": _exj1.dumps(_cikis_ov_guncel, ensure_ascii=False)},
                                {"kullanici": "__liste_ui__", "anahtar": "_koli_palet_manuel",
                                 "deger": _exj1.dumps(_koli_ov_guncel, ensure_ascii=False)},
                            ], on_conflict="kullanici,anahtar").execute()
                    except:
                        pass
                    # KULLANICI İSTEĞİ (2026-09): "İl Ciroları" — Koli/Palet
                    # değişen HER satır için otomatik yeniden hesaplanır.
                    # 🚨 KRİTİK DÜZELTME: "Hedeflenen Ciro" de AYNI ANDA, AYNI
                    # veriden (İl Ciroları GENEL TOPLAM ile) güncellenir —
                    # ikisi bir daha asla birbirinden farklı olamaz.
                    if _icy_etkilenen_idler:
                        try:
                            _icy_harita2 = _cari_ek_bilgi_yukle()
                            for _icy_rid in _icy_etkilenen_idler:
                                _icy_metin = _koli_ov_guncel.get(str(_icy_rid), "")
                                _icy_harita2.setdefault(str(_icy_rid), {})["il_ciro_ozet"] = _fy_il_ciro_ozet_cikar(_icy_metin)
                                _icy_hedef2 = _fy_il_ciro_genel_toplam(_icy_metin)
                                if _icy_hedef2 is not None:
                                    try:
                                        db_update("cari_kartlar", {"beklenen_ciro": _icy_hedef2}, "id", int(_icy_rid))
                                    except Exception:
                                        pass
                            _cari_ek_bilgi_kaydet(_icy_harita2)
                            get_cari_listesi.clear()
                        except Exception:
                            pass

                # ── Vergi No / Vergi Dairesi / Müşteri Şubesi / Vade / Ödeme —
                # KULLANICI İSTEĞİ (2026-09): cari_kartlar'da GERÇEK sütun
                # DEĞİL, Rut ile AYNI desen — kullanici_tercih'te
                # {cari_id: {alan: değer}} olarak saklanır. GÜVENLİ (SİLME
                # YOK, UPDATE-yoksa-INSERT) fonksiyon kullanılır.
                _cek_guncel = _cari_ek_bilgi_yukle()
                _cek_degisti = False
                for _idx_str_cek, _deg_cek in _edited_rows.items():
                    _idxn_cek = int(_idx_str_cek)
                    if _idxn_cek >= len(_rows):
                        continue
                    _rid_cek = int(float(str(_rows[_idxn_cek].get("id", 0))))
                    if not _rid_cek:
                        continue
                    for _cek_alan in _CARI_EK_ALAN_LISTESI:
                        if _cek_alan in _deg_cek:
                            _v_cek = str(_deg_cek[_cek_alan] or "").strip()
                            _cek_guncel.setdefault(str(_rid_cek), {})
                            if _v_cek:
                                _cek_guncel[str(_rid_cek)][_cek_alan] = _v_cek
                            else:
                                _cek_guncel[str(_rid_cek)].pop(_cek_alan, None)
                            _cek_degisti = True
                if _cek_degisti:
                    _cari_ek_bilgi_kaydet(_cek_guncel)

                # NOT: "🛣️ Rut" artık elle düzenlenmiyor — İL sütunlarından
                # otomatik hesaplanıyor (bkz. _cari_rut_hesapla_otomatik).
                # Sütun disabled=True olduğu için _edited_rows'a hiç girmez;
                # bu yüzden burada ayrı bir kaydetme bloğuna gerek kalmadı.

                # ── "📅 Son Randevu" hücresine manuel tarih yazılırsa GERÇEK bir
                # randevu kaydı (randevular tablosu) oluşturulur — override değil,
                # gerçek veri. Format: "15.08.2026" veya "15.08.2026 14:00".
                import re as _rndre
                for _idx_str_rn, _deg_rn in _edited_rows.items():
                    if "📅 Son Randevu" not in _deg_rn:
                        continue
                    _rn_ham = str(_deg_rn["📅 Son Randevu"] or "").strip()
                    if not _rn_ham:
                        continue  # boşaltma = randevu silme değil, sadece görmezden gel
                    _idxn_rn = int(_idx_str_rn)
                    if _idxn_rn >= len(_rows):
                        continue
                    _rid_rn = int(float(str(_rows[_idxn_rn].get("id", 0))))
                    _firma_rn = str(_rows[_idxn_rn].get("firma", "") or "")
                    if not _rid_rn:
                        continue
                    # Emoji/etiket kalıntılarını temizle (örn. "📅 15.08.2026 14:00")
                    _rn_temiz = _rndre.sub(r"[^\d.:/ ]", "", _rn_ham).strip()
                    _rn_saat_m = _rndre.search(r"(\d{1,2}):(\d{2})", _rn_temiz)
                    _rn_saat = f"{_rn_saat_m.group(1).zfill(2)}:{_rn_saat_m.group(2)}" if _rn_saat_m else "10:00"
                    _rn_tarih_str = _rndre.sub(r"\d{1,2}:\d{2}", "", _rn_temiz).strip()
                    _rn_dt = _guncelleme_tarih_parse(_rn_tarih_str) or _guncelleme_tarih_parse(_rn_temiz)
                    if not _rn_dt:
                        # Doğrudan DD.MM.YYYY formatını dene (parse edemediyse)
                        _rn_m = _rndre.match(r"(\d{1,2})[.\/](\d{1,2})[.\/](\d{2,4})", _rn_tarih_str)
                        if _rn_m:
                            try:
                                _gg, _aa, _yy = int(_rn_m.group(1)), int(_rn_m.group(2)), int(_rn_m.group(3))
                                if _yy < 100: _yy += 2000
                                _rn_dt = datetime(_yy, _aa, _gg)
                            except Exception:
                                _rn_dt = None
                    if not _rn_dt:
                        continue  # anlaşılamayan tarih — sessizce atla, veri bozma
                    _rn_basarili = False
                    _rn_hata = ""
                    try:
                        _sb_rn = get_sb_client()
                        if _sb_rn:
                            _res_rn = _sb_rn.table("randevular").insert({
                                "randevu_tarihi": _rn_dt.strftime("%Y-%m-%d"),
                                "randevu_saati": _rn_saat,
                                "musteri_id": _rid_rn, "musteri_adi": _firma_rn,
                                "bolge": "", "gorev": "", "takip": "",
                                "adet": 1, "aciklama": "Cari Liste'den hızlı eklendi",
                                "sonuc": "", "temsilci": st.session_state.get("kullanici",""),
                                "olusturan": st.session_state.get("kullanici","")
                            }).execute()
                            _rn_basarili = bool(_res_rn.data)
                        else:
                            _rn_hata = "Supabase bağlantısı yok."
                    except Exception as _rn_e:
                        _rn_hata = str(_rn_e)
                    if _rn_basarili:
                        try: db_read.clear()
                        except: pass
                        # Randevu tarihi eklenince, müşterinin "1. Aşama"sı henüz
                        # boşsa otomatik "Randevu" yapılır — Kanban'daki "1. AŞAMA"
                        # sayacına yansısın diye (aksi halde sayaç hiç değişmiyordu).
                        _mevcut_asama1 = str(_rows[_idxn_rn].get("asama1","") or "").strip()
                        if not _mevcut_asama1:
                            try:
                                if _sb_rn:
                                    _sb_rn.table("cari_kartlar").update({"asama1":"Randevu"}).eq("id", _rid_rn).execute()
                                    try: get_cari_listesi.clear()
                                    except: pass
                            except Exception:
                                pass
                    else:
                        st.error(f"❌ Randevu kaydedilemedi ({_firma_rn}): {_rn_hata}")

                # ── Güncelleme Tarihi izi — gerçekten bir alan (aşama, durum, açıklama,
                # ciro vb.) değişen HER satır için "şu an" damgası basılır. "Seç"
                # (checkbox işaretleme) tek başına değişiklik sayılmaz. ISO format
                # kullanılıyor (diğer tarih kaynaklarıyla — cari_kartlar.tarih,
                # created_at — aynı ayraç/biçim, karşılaştırma tutarlı olsun diye).
                _sg_guncel = dict(st.session_state.get("_cari_son_guncelleme", {}))
                _sg_simdi = datetime.now().isoformat()
                _sg_degisti = False
                for _idx_str_sg, _deg_sg in _edited_rows.items():
                    _gercek_degisiklik = any(k not in ("Seç", "🗑️ Sil") for k in _deg_sg.keys())
                    if not _gercek_degisiklik:
                        continue
                    _idxn_sg = int(_idx_str_sg)
                    if _idxn_sg >= len(_rows):
                        continue
                    _rid_sg = int(float(str(_rows[_idxn_sg].get("id", 0))))
                    if not _rid_sg:
                        continue
                    _sg_guncel[str(_rid_sg)] = _sg_simdi
                    _sg_degisti = True
                if _sg_degisti:
                    st.session_state["_cari_son_guncelleme"] = _sg_guncel
                    try:
                        _sb_sg1 = get_sb_client()
                        if _sb_sg1:
                            import json as _sgj1
                            _sb_sg1.table("kullanici_tercih").upsert({
                                "kullanici": "__liste_ui__", "anahtar": "_cari_son_guncelleme",
                                "deger": _sgj1.dumps(_sg_guncel, ensure_ascii=False)
                            }, on_conflict="kullanici,anahtar").execute()
                    except:
                        pass

                # ── İL SÜTUNLARI kaydı — cari_kartlar'a değil, ayrı JSON haritaya
                # yazılır (kullanici_tercih._il_gonderim_matrisi). "Hangi ile ne
                # gönderiyor" bilgisi firma bazlı olarak burada tutulur.
                _ilm_degisti = False
                _ilm_guncel = dict(_il_gonderim_matrisi)

                def _vi_norm(_s):
                    return (str(_s or "").strip().upper().replace("İ", "I").replace("Ş", "S")
                            .replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C"))

                for _idx_str_ilm, _deg_ilm in _edited_rows.items():
                    _ilm_fark = {k: v for k, v in _deg_ilm.items() if k in _IL_SUTUN_LISTESI}
                    _varis_illeri_metni = str(_deg_ilm.get("Varış İlleri", "") or "").strip()
                    if not _ilm_fark and not _varis_illeri_metni:
                        continue
                    _idxn_ilm = int(_idx_str_ilm)
                    if _idxn_ilm >= len(_rows):
                        continue
                    _rid_ilm = int(float(str(_rows[_idxn_ilm].get("id", 0))))
                    if not _rid_ilm:
                        continue
                    _rid_ilm_str = str(_rid_ilm)
                    _ilm_guncel.setdefault(_rid_ilm_str, {})
                    for _ilk, _ilv in _ilm_fark.items():
                        _ilm_guncel[_rid_ilm_str][_ilk] = str(_ilv) if _ilv is not None else ""
                        _ilm_degisti = True
                    # ── "Varış İlleri" hızlı-giriş — karışık/serbest yazılan il
                    # isimlerini ayırıp, eşleşen il sütununu (boşsa) "✓" ile işaretler.
                    if _varis_illeri_metni:
                        _vi_metin_norm = _vi_norm(_varis_illeri_metni)
                        for _il_ad_vi in _IL_SUTUN_LISTESI:
                            if _il_ad_vi == "Diğer":
                                continue
                            if _vi_norm(_il_ad_vi) in _vi_metin_norm:
                                _mevcut_deg = _ilm_guncel[_rid_ilm_str].get(_il_ad_vi, "")
                                if not str(_mevcut_deg).strip():
                                    _ilm_guncel[_rid_ilm_str][_il_ad_vi] = _il_ad_vi.upper()
                                    _ilm_degisti = True
                if _ilm_degisti:
                    _il_gonderim_matrisi_kaydet(_ilm_guncel)
                    try: _il_gonderim_matrisi_yukle.clear()
                    except: pass

                def _tek_satir_guncelle(idx_str, degisiklikler):
                    """Tek bir satırı DB'ye yazar — paralel çalıştırılabilsin diye ayrı fonksiyon."""
                    idx = int(idx_str)
                    if idx >= len(_rows):
                        return None
                    rid = int(float(str(_rows[idx].get("id", 0))))
                    if not rid:
                        return None
                    guncelle = {}
                    for k, v in degisiklikler.items():
                        if k in ("Seç", "🗑️ Sil", "🧾 Teklif", "💬 Mesaj", "✅ Analiz", "Varış İli", "Koli/Palet", "📅 Son Randevu", "Varış İlleri", "Fiyatlandırma", "Hesaplama", "hesaplama",
                                 "vergi_no", "vergi_dairesi", "musteri_subesi", "vade", "odeme", "musteri_kodu", "teklif_fiyat", "islem_tarihi_manuel", "takip_tarihi_manuel", "randevu_tarihi_manuel", "il_ciro_ozet") or k in _IL_SUTUN_LISTESI: continue
                        if k in ("beklenen_ciro", "gerceklesen_ciro"):
                            try: guncelle[k] = float(v or 0)
                            except: guncelle[k] = 0
                        elif k in ("Hedef ₺",):
                            try: guncelle["beklenen_ciro"] = float(str(v or "").replace(".","").replace("₺","").replace(",",".").strip() or 0)
                            except: guncelle["beklenen_ciro"] = 0
                        elif k in ("Gerçek ₺",):
                            try: guncelle["gerceklesen_ciro"] = float(str(v or "").replace(".","").replace("₺","").replace(",",".").strip() or 0)
                            except: guncelle["gerceklesen_ciro"] = 0
                        elif k in ("gsm", "sabit"):
                            # KULLANICI İSTEĞİ: Artık otomatik "sadece rakam" temizliği
                            # YAPILMIYOR — birden fazla numarayı "533 405 55 18 - 539 266
                            # 42 86" gibi kendi ayracıyla tek hücrede tutabilmek için,
                            # kullanıcı ne yazarsa AYNEN kaydediliyor. (Eskiden boşluk/tire
                            # gibi her şey silinip iki numara birbirine yapışıyordu.)
                            guncelle[k] = str(v).strip() if v is not None else ""
                        else:
                            guncelle[k] = str(v) if v is not None else ""
                    if not guncelle:
                        return None
                    # 🚨 GÜVENLİK KİLİDİ (2026-09): yukarıdaki hariç tutma listesi
                    # "hesaplama"yı zaten dışarıda bırakıyor, ama burada BİR DAHA,
                    # son bir güvenlik olarak kesin süzülür — "cari_kartlar"da
                    # olmayan bu sütun asla veritabanına gönderilmesin.
                    guncelle.pop("hesaplama", None)
                    guncelle.pop("Hesaplama", None)
                    if not guncelle:
                        return None
                    if sb_liste:
                        sb_liste.table("cari_kartlar").update(guncelle).eq("id", rid).execute()
                    else:
                        conn_u = get_conn()
                        sets = ", ".join([f"{k}=?" for k in guncelle])
                        conn_u.execute(f"UPDATE cari_kartlar SET {sets} WHERE id=?",
                            list(guncelle.values()) + [rid])
                        conn_u.commit(); conn_u.close()
                    return True

                # ── SATIRLARI PARALEL KAYDET — sıra sıra beklemek yerine aynı anda
                # gönderilir, N satır için toplam süre ~1 satırlık süreye yakın olur.
                _kaydedilen_firmalar = []
                _alt_bar_yer = st.empty()
                _kayit_toplam_sayisi = len(_edited_rows)
                _kayit_tamamlanan = 0
                _alt_bar_yer.markdown(_alt_ilerleme_cubugu_html(0, f"Kaydediliyor... 0/{_kayit_toplam_sayisi}"), unsafe_allow_html=True)
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as _havuz:
                    _gelecekler = {
                        _havuz.submit(_tek_satir_guncelle, idx_str, degisiklikler): idx_str
                        for idx_str, degisiklikler in _edited_rows.items()
                    }
                    for _gelecek in concurrent.futures.as_completed(_gelecekler):
                        _idx_str_g = _gelecekler[_gelecek]
                        try:
                            if _gelecek.result():
                                kayit_sayi += 1
                                try:
                                    _idxn_g = int(_idx_str_g)
                                    if _idxn_g < len(_rows):
                                        _kaydedilen_firmalar.append(str(_rows[_idxn_g].get("firma","") or "(isimsiz)"))
                                except Exception:
                                    pass
                        except Exception as e_row:
                            hata_list.append(str(e_row))
                        _kayit_tamamlanan += 1
                        _kayit_yuzde = (_kayit_tamamlanan / _kayit_toplam_sayisi * 100) if _kayit_toplam_sayisi else 100
                        _alt_bar_yer.markdown(
                            _alt_ilerleme_cubugu_html(_kayit_yuzde, f"Kaydediliyor... {_kayit_tamamlanan}/{_kayit_toplam_sayisi}"),
                            unsafe_allow_html=True
                        )
                _alt_bar_yer.markdown(_alt_ilerleme_cubugu_html(100, f"Tamamlandı — {_kayit_toplam_sayisi}/{_kayit_toplam_sayisi}"), unsafe_allow_html=True)
                import time as _alt_bar_time
                _alt_bar_time.sleep(0.6)
                _alt_bar_yer.empty()

                try: db_read.clear()
                except: pass
                try: get_cari_listesi.clear()
                except: pass
                # ── AÇIKLAMA HÜCRESI DOLUYSA ARŞİVLE ─────────────────────────
                _arsiv_sayi = 0
                try:
                    _tablo_json2 = st.session_state.get("_ls_tablo")
                    _rows2 = _json_ls.loads(_tablo_json2) if _tablo_json2 else []
                    _arsivlenecekler = []
                    for _row2 in _rows2:
                        _rid2 = _row2.get("id")
                        _ac2 = str(_row2.get("aciklama","") or "").strip()
                        if not _rid2 or not _ac2 or _ac2 == "nan": continue
                        _arsivlenecekler.append((int(float(str(_rid2))), str(_row2.get("firma",""))," ".join([_ac2])))

                    def _tek_not_arsivle(rid2, firma2, ac2):
                        if sb_liste:
                            sb_liste.table("cari_aciklamalar").insert({
                                "cari_id": rid2, "aciklama": ac2,
                                "olusturan": st.session_state.get("kullanici",""),
                            }).execute()
                            sb_liste.table("cari_kartlar").update({"aciklama":""}).eq("id",rid2).execute()
                        else:
                            _cx = get_conn()
                            _cx.execute("INSERT INTO cari_aciklamalar (cari_id,cari_adi,aciklama,olusturan) VALUES (?,?,?,?)",
                                (rid2, firma2, ac2, st.session_state.get("kullanici","")))
                            _cx.execute("UPDATE cari_kartlar SET aciklama='' WHERE id=?", (rid2,))
                            _cx.commit(); _cx.close()
                        return True

                    if _arsivlenecekler:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as _havuz2:
                            _gelecekler2 = [_havuz2.submit(_tek_not_arsivle, *_a) for _a in _arsivlenecekler]
                            for _g2 in concurrent.futures.as_completed(_gelecekler2):
                                try:
                                    if _g2.result():
                                        _arsiv_sayi += 1
                                except Exception:
                                    pass
                except: pass
                st.session_state.pop("_ls_tablo", None)
                # Widget'ın eski edited_rows durumunu temizle — kaydedilenler artık
                # veritabanında, bir sonraki render'da taze veriyle baştan başlasın.
                # Bu, eski izlerin yeni bir düzenlemeyi maskelemesini de önler.
                st.session_state.pop(_cl_editor_key, None)
                st.session_state["_cl_editor_versiyon"] += 1
                st.session_state["_cl_tumu_secili_mod"] = False
                st.session_state["_cl_tumu_haric_idler"] = set()
                if kayit_sayi > 0:
                    _ozet_msg = f"{kayit_sayi} satır kaydedildi!" + (f" · {_arsiv_sayi} not arşivlendi!" if _arsiv_sayi > 0 else "")
                    if _kaydedilen_firmalar:
                        _ozet_msg += " → " + ", ".join(_kaydedilen_firmalar[:8]) + (" ..." if len(_kaydedilen_firmalar) > 8 else "")
                elif _arsiv_sayi > 0:
                    _ozet_msg = f"{_arsiv_sayi} not arşivlendi!"
                else:
                    _ozet_msg = "Değişiklik kaydedildi."
                # Toast rerun sonrası da görünür ama kalıcı bir banner için ayrıca sakla —
                # kullanıcı notunun/kaydının gerçekten kaydedildiğini rerun sonrası da görsün.
                st.session_state["_son_kaydet_ozeti"] = "✅ " + _ozet_msg
                st.toast("✅ " + _ozet_msg, icon="✅")
                if hata_list:
                    st.error(f"Hata: {'; '.join(hata_list[:2])}")
                st.rerun()
    with btn_a:
        pass  # (Seçili → Arşive butonu kullanıcı isteğiyle kaldırıldı)

    with btn_s:
        # KULLANICI İSTEĞİ (2026-09): buton artık BURADA değil, üst sticky
        # satırında ("🗑️ Seçili Kaydı Sil") — orada tıklanınca sadece bir
        # NİYET bayrağı ayarlanıyor, gerçek silme burada (seçili sayı netleşince) yapılıyor.
        if st.session_state.pop("_cl_sil_niyeti", False):
            if secili_sayi < 1:
                st.warning("⚠️ Önce silmek istediğin müşteri(ler)in 'Seç' kutusunu işaretle.")
            else:
                try:
                    for _cl_sid in secili_idler:
                        try:
                            db_update("cari_kartlar", {"silindi": 1}, "id", int(_cl_sid))
                        except (ValueError, TypeError):
                            continue  # geçersiz/boş id — güvenlik için atla
                    try: db_read.clear()
                    except: pass
                    try: get_cari_listesi.clear()
                    except: pass
                    st.session_state.pop(_cl_editor_key, None)
                    st.session_state["_cl_editor_versiyon"] += 1
                    st.session_state["_cl_tumu_secili_mod"] = False
                    st.session_state["_cl_tumu_haric_idler"] = set()
                    st.toast(f"🗑️ {secili_sayi} müşteri silindi", icon="🗑️")
                    st.rerun()
                except Exception as _cl_sil_hata:
                    st.error(f"Silme hatası: {_cl_sil_hata}")



    # ── SAYFALAMA KONTROLLERİ KALDIRILDI — kullanıcı isteği üzerine ──────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if _cl_toplam_kayit > 0:
        st.caption(f"Seçmek için Seç kolonunu işaretleyin · **Tümü** gösteriliyor — {_cl_toplam_kayit} kayıt")

    st.divider()


elif aktif == "dis_nakliye_toplu":
    sayfa_log("dis_nakliye_toplu")
    st.markdown("## 🚚 Dış Nakliyeler Listesi")
    st.caption("Tüm müşterilerin dış nakliye kayıtları, cari ekstre ve taşıyıcı yönetimi. Müşteri bazlı ekleme/düzenleme, o müşterinin 'Notlar & Randevu' penceresindeki 🚚 Dış Nakliye sekmesinden yapılır.")

    _dnb_tab_liste, _dnb_tab_ekstre, _dnb_tab_tasiyici = st.tabs(["📦 Tüm Kayıtlar", "🧾 Cari Ekstre", "🚛 Taşıyıcı Yönetimi"])

    with _dnb_tab_liste:
        _dnb_tum = _dis_nakliye_yukle()
        if _dnb_tum:
            _dnb_df = pd.DataFrame(_dnb_tum)
            for _c in _DIS_NAKLIYE_KOLONLAR:
                if _c not in _dnb_df.columns:
                    _dnb_df[_c] = 0 if _c in _DIS_NAKLIYE_SAYI_KOLON or _c in _DIS_NAKLIYE_HESAP_KOLON else (False if _c in _DIS_NAKLIYE_CHECK_KOLON else "")
            _dnb_df = _dis_nakliye_hesapla(_dnb_df)
            _dnb_df = _dnb_df[["id", "cari_id"] + _DIS_NAKLIYE_KOLONLAR]
            _dnb_df = _dnb_df.reset_index(drop=True)
            _dnb_df.insert(0, "Seç", False)
            _dnb_df.index = _dnb_df.index + 1
            _dnb_df.index.name = "S.No"

            st.caption(f"📌 {len(_dnb_df)} kayıt — toplam kar: {_dnb_df['kar'].sum():,.2f} ₺".replace(",", "."))
            _dnb_edited = st.data_editor(
                _dnb_df, use_container_width=True, num_rows="fixed",
                column_config={
                    **_dis_nakliye_col_config(), "id": None, "cari_id": None,
                    "Seç": st.column_config.CheckboxColumn("Seç", default=False),
                },
                key="dnb_editor",
                height=min(650, 45 + (len(_dnb_df) * 35) + 5),
            )

            _dnb_secili = _dnb_edited[_dnb_edited["Seç"] == True]
            _dnb_secili_sayi = len(_dnb_secili)
            _dnb_secili_idler = _dnb_secili["id"].tolist() if not _dnb_secili.empty else []

            _dnb_bk1, _dnb_bk2 = st.columns([1, 1])
            with _dnb_bk1:
                if st.button("💾 Değişiklikleri Kaydet", key="dnb_kaydet_btn", type="primary", use_container_width=True):
                    _dnb_final = _dnb_edited.drop(columns=["Seç"]).reset_index(drop=True).copy()
                    _dnb_final = _dis_nakliye_hesapla(_dnb_final)
                    for _c in ["id", "cari_id"]:
                        if _c not in _dnb_final.columns:
                            _dnb_final[_c] = 0
                    _dnb_final["id"] = _dnb_final["id"].apply(lambda x: int(x) if str(x).strip() not in ("", "nan", "None") and float(x) > 0 else 0)
                    _dnb_final["cari_id"] = _dnb_final["cari_id"].apply(lambda x: int(x) if str(x).strip() not in ("", "nan", "None") else 0)
                    _yeni_id_sayac_b = int(max([int(r.get("id", 0) or 0) for r in _dnb_tum], default=0)) + 1
                    _tum_yeni = []
                    for _, _row in _dnb_final.iterrows():
                        _rd = _row.to_dict()
                        if not _rd.get("id"):
                            _rd["id"] = _yeni_id_sayac_b
                            _yeni_id_sayac_b += 1
                        _tum_yeni.append(_rd)
                    if _dis_nakliye_kaydet(_tum_yeni):
                        st.toast("✅ Dış nakliye kayıtları güncellendi!", icon="✅")
                        st.rerun()
                    else:
                        st.error("❌ Kaydedilemedi, bağlantıyı kontrol et.")
            with _dnb_bk2:
                if _dnb_secili_sayi > 0:
                    if not st.session_state.get("_dnb_sil_onay_bekliyor"):
                        if st.button(f"🗑️ Seçili {_dnb_secili_sayi} Kaydı Sil", key="dnb_sil_btn", use_container_width=True):
                            st.session_state["_dnb_sil_onay_bekliyor"] = True
                            st.rerun()
                else:
                    st.caption("Silmek için satırları soldaki Seç kutusuyla işaretle.")

            if _dnb_secili_sayi > 0 and st.session_state.get("_dnb_sil_onay_bekliyor"):
                st.warning(f"⚠️ Seçili {_dnb_secili_sayi} kayıt kalıcı olarak silinecek, geri alınamaz! Silmek istediğine emin misin?")
                _dnb_sa1, _dnb_sa2 = st.columns(2)
                with _dnb_sa1:
                    if st.button(f"✅ Evet, {_dnb_secili_sayi} kaydı sil", type="primary", key="dnb_sil_onay", use_container_width=True):
                        _dnb_silinecek_idler = set(int(x) for x in _dnb_secili_idler)
                        _dnb_kalan = [r for r in _dnb_tum if int(r.get("id", 0) or 0) not in _dnb_silinecek_idler]
                        if _dis_nakliye_kaydet(_dnb_kalan):
                            st.session_state.pop("_dnb_sil_onay_bekliyor", None)
                            st.success(f"✅ {_dnb_secili_sayi} kayıt silindi!")
                            st.rerun()
                        else:
                            st.error("❌ Silinemedi, bağlantıyı kontrol et.")
                with _dnb_sa2:
                    if st.button("❌ Vazgeç", key="dnb_sil_vazgec", use_container_width=True):
                        st.session_state.pop("_dnb_sil_onay_bekliyor", None)
                        st.rerun()
        else:
            st.caption("Henüz hiç dış nakliye kaydı yok. Bir müşterinin 'Notlar & Randevu' penceresindeki 🚚 Dış Nakliye sekmesinden veya aşağıdaki taşıyıcı yönetiminden başlayabilirsin.")

    with _dnb_tab_ekstre:
        st.caption("Bir müşteri seç, o müşterinin dış nakliye üzerinden tüm cari hareketini (tarih, tutar, KDV'li, ödendi durumu, kar) tek ekranda gör.")
        _dnb_ekstre_kaynak = _dis_nakliye_yukle()
        if _dnb_ekstre_kaynak:
            _dnb_ekstre_df_tum = pd.DataFrame(_dnb_ekstre_kaynak)
            for _c in _DIS_NAKLIYE_KOLONLAR:
                if _c not in _dnb_ekstre_df_tum.columns:
                    _dnb_ekstre_df_tum[_c] = 0 if _c in _DIS_NAKLIYE_SAYI_KOLON or _c in _DIS_NAKLIYE_HESAP_KOLON else (False if _c in _DIS_NAKLIYE_CHECK_KOLON else "")
            _dnb_ekstre_df_tum = _dis_nakliye_hesapla(_dnb_ekstre_df_tum)
            _dnb_ekstre_df_tum["cari_id"] = pd.to_numeric(_dnb_ekstre_df_tum.get("cari_id", 0), errors="coerce").fillna(0).astype(int)
            _dnb_musteri_map = {}
            for _, _r in _dnb_ekstre_df_tum[_dnb_ekstre_df_tum["cari_id"] > 0].iterrows():
                _dnb_musteri_map[int(_r["cari_id"])] = str(_r.get("gonderen_firma", "")).strip() or f"Müşteri #{int(_r['cari_id'])}"
            if _dnb_musteri_map:
                _dnb_secenek_idler = sorted(_dnb_musteri_map.keys(), key=lambda cid: _dnb_musteri_map[cid])
                _dnb_secili_cid = st.selectbox(
                    "Müşteri", _dnb_secenek_idler, key="dnb_ekstre_musteri_sec",
                    format_func=lambda cid: _dnb_musteri_map.get(cid, str(cid)),
                )
                _dnb_ekstre_df = _dnb_ekstre_df_tum[_dnb_ekstre_df_tum["cari_id"] == _dnb_secili_cid].copy()
                _dnb_ekstre_df = _dnb_ekstre_df.sort_values("tarih")
                _dnb_ekstre_df["bakiye"] = (_dnb_ekstre_df["kdvli1"] * (~_dnb_ekstre_df["odendi1"].astype(bool))).cumsum()

                _ek1, _ek2, _ek3, _ek4 = st.columns(4)
                _ek1.metric("Toplam İşlem", len(_dnb_ekstre_df))
                _ek2.metric("Toplam Tutar (KDV'li)", f"{_dnb_ekstre_df['kdvli1'].sum():,.2f} ₺".replace(",", "."))
                _ek3.metric("Ödenmemiş Tutar", f"{_dnb_ekstre_df.loc[~_dnb_ekstre_df['odendi1'].astype(bool), 'kdvli1'].sum():,.2f} ₺".replace(",", "."))
                _ek4.metric("Toplam Kar", f"{_dnb_ekstre_df['kar'].sum():,.2f} ₺".replace(",", "."))

                _dnb_ekstre_goster = _dnb_ekstre_df[[
                    "tarih", "alici_firma", "adet1", "fiyat1", "yekun1", "kdvli1", "odendi1", "bakiye", "kar"
                ]].rename(columns={
                    "tarih": "Tarih", "alici_firma": "Alıcı Firma", "adet1": "Adet", "fiyat1": "Birim Fiyat",
                    "yekun1": "Yekün", "kdvli1": "KDV'li Tutar", "odendi1": "Ödendi",
                    "bakiye": "Ödenmemiş Bakiye (Kümülatif)", "kar": "Kar",
                })
                _dnb_ekstre_goster = _dnb_ekstre_goster.reset_index(drop=True)
                _dnb_ekstre_goster.index = _dnb_ekstre_goster.index + 1
                _dnb_ekstre_goster.index.name = "S.No"
                st.dataframe(
                    _dnb_ekstre_goster, use_container_width=True,
                    column_config={
                        "Birim Fiyat": st.column_config.NumberColumn(format="%.2f ₺"),
                        "Yekün": st.column_config.NumberColumn(format="%.2f ₺"),
                        "KDV'li Tutar": st.column_config.NumberColumn(format="%.2f ₺"),
                        "Ödenmemiş Bakiye (Kümülatif)": st.column_config.NumberColumn(format="%.2f ₺"),
                        "Kar": st.column_config.NumberColumn(format="%.2f ₺"),
                    },
                )
            else:
                st.caption("Kayıtlarda müşteri bilgisi bulunamadı.")
        else:
            st.caption("Henüz hiç dış nakliye kaydı yok.")

    with _dnb_tab_tasiyici:
        st.info("🚛 Taşıyıcı/tedarikçi yönetimi artık sol menüdeki **'🚛 Tedarikçi'** sayfasına taşındı — "
                "orada Firma Adı, GSM, Sabit Tel, Email, Adres, İl/İlçe, Yük Açıklaması, Tür, Adet ve Tutar gibi "
                "daha detaylı bilgilerle kaydedebilirsin. Eski kayıtlı taşıyıcıların hepsi otomatik olarak oraya taşındı, hiçbiri kaybolmadı.")

elif aktif == "dis_nakliye":
    sayfa_log("dis_nakliye")
    st.markdown("""<style>
.block-container { padding-left: 0.6rem !important; padding-right: 0.6rem !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { max-width: 100% !important; }
div[data-testid="stHorizontalBlock"] { gap: 0.3rem !important; justify-content: flex-start !important; }
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { padding: 0 !important; }
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {
    flex: 0 1 auto !important; max-width: none !important; width: auto !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {
    max-width: 260px !important; flex: 0 0 260px !important; width: 260px !important;
}
</style>""", unsafe_allow_html=True)

    _dn_kolonlar = [
        "tarih", "gonderen_firma", "gonderici_tel", "gonderen_adres", "gonderen_il", "gonderen_ilce",
        "alici_firma", "alici_tel", "alici_adres", "alici_il", "alici_ilce",
        "odeme_yapacak_musteri", "fatura_adresi", "vergi_dairesi", "vergi_no", "yetkili_tel", "odeme_turu",
        "adet", "tur", "tasiyici", "tasiyici_fatura", "tasiyici_odendi",
        "stf_faturasi", "stf_odendi", "kar"
    ]
    _dn_basliklar = {
        "tarih": "TARİH",
        "gonderen_firma": "GÖNDEREN FİRMA", "gonderici_tel": "GÖNDERİCİ TEL", "gonderen_adres": "GÖNDEREN ADRESİ",
        "gonderen_il": "GÖNDEREN İL", "gonderen_ilce": "GÖNDEREN İLÇE",
        "alici_firma": "ALICI FİRMA", "alici_tel": "ALICI TEL", "alici_adres": "ALICI ADRES",
        "alici_il": "ALICI İL", "alici_ilce": "ALICI İLÇE",
        "odeme_yapacak_musteri": "ÖDEME YAPACAK MÜŞTERİ", "fatura_adresi": "FATURA ADRESİ",
        "vergi_dairesi": "VERGİ DAİRESİ", "vergi_no": "VERGİ NO", "yetkili_tel": "YETKİLİ TEL",
        "odeme_turu": "ÖDEME TÜRÜ", "adet": "ADET", "tur": "TÜR", "tasiyici": "TAŞIYICI",
        "tasiyici_fatura": "TAŞIYICI FATURA", "tasiyici_odendi": "ÖDENDİ",
        "stf_faturasi": "STF FATURASI", "stf_odendi": "ÖDENDİ", "kar": "KAR"
    }
    # Cari Liste ile AYNI ölçekte kompakt piksel genişlikleri — tüm kolonlar
    # tek ekrana sığsın diye iyice daraltıldı
    _dn_pixel_genislik = {
        "tarih":85,"gonderen_firma":115,"gonderici_tel":95,"gonderen_adres":115,"gonderen_il":80,"gonderen_ilce":80,
        "alici_firma":115,"alici_tel":95,"alici_adres":115,"alici_il":80,"alici_ilce":80,
        "odeme_yapacak_musteri":135,"fatura_adresi":115,"vergi_dairesi":95,"vergi_no":85,"yetkili_tel":95,
        "odeme_turu":85,"adet":60,"tur":80,"tasiyici":95,"tasiyici_fatura":100,"tasiyici_odendi":70,
        "stf_faturasi":100,"stf_odendi":70,"kar":85
    }

    # ── Yükle — kullanici_tercih tablosunda TEK bir JSON kayıt olarak
    # saklanır (yeni tablo açmadan). Sayfa açılışında bir kere çekilir. ──────
    if "_dn_kayitlar" not in st.session_state:
        st.session_state["_dn_kayitlar"] = []
        try:
            _sb_dn0 = get_sb_client()
            if _sb_dn0:
                import json as _dnj0
                _r_dn0 = _sb_dn0.table("kullanici_tercih").select("deger").eq(
                    "kullanici", "__liste_ui__").eq("anahtar", "dis_nakliye_kayitlari").execute()
                if _r_dn0.data:
                    st.session_state["_dn_kayitlar"] = _dnj0.loads(_r_dn0.data[0]["deger"])
        except Exception:
            pass

    _dn_liste = st.session_state["_dn_kayitlar"]
    if _dn_liste:
        _dn_df = pd.DataFrame(_dn_liste)
        for _k in _dn_kolonlar:
            if _k not in _dn_df.columns:
                _dn_df[_k] = 0 if _k in ("adet", "kar", "tasiyici_fatura", "stf_faturasi") else ("" if _k not in ("tasiyici_odendi","stf_odendi") else False)
        _dn_df = _dn_df[_dn_kolonlar]
    else:
        _dn_df = pd.DataFrame(columns=_dn_kolonlar)

    if _dn_df.empty:
        _dn_df = pd.DataFrame([{c: (0 if c in ("adet","kar","tasiyici_fatura","stf_faturasi") else (False if c in ("tasiyici_odendi","stf_odendi") else "")) for c in _dn_kolonlar}]).iloc[0:0]
    _dn_df["adet"] = pd.to_numeric(_dn_df["adet"], errors="coerce").fillna(0).astype(int)
    _dn_df["tasiyici_fatura"] = pd.to_numeric(_dn_df["tasiyici_fatura"], errors="coerce").fillna(0.0)
    _dn_df["stf_faturasi"] = pd.to_numeric(_dn_df["stf_faturasi"], errors="coerce").fillna(0.0)
    # KAR otomatik hesaplanır — STF Faturası TUTARI eksi Taşıyıcı Fatura TUTARI.
    # Manuel yazılamaz (disabled), kaydettikçe otomatik güncellenir.
    _dn_df["kar"] = _dn_df["stf_faturasi"] - _dn_df["tasiyici_fatura"]
    _dn_df["tasiyici_odendi"] = _dn_df["tasiyici_odendi"].apply(lambda x: bool(x) if str(x).strip() not in ["", "nan", "None"] else False)
    _dn_df["stf_odendi"] = _dn_df["stf_odendi"].apply(lambda x: bool(x) if str(x).strip() not in ["", "nan", "None"] else False)
    for _tk in ["tarih","gonderen_firma","gonderici_tel","gonderen_adres","gonderen_il","gonderen_ilce",
                "alici_firma","alici_tel","alici_adres","alici_il","alici_ilce",
                "odeme_yapacak_musteri","fatura_adresi","vergi_dairesi","vergi_no","yetkili_tel","odeme_turu","tur","tasiyici"]:
        _dn_df[_tk] = _dn_df[_tk].astype(str).replace(["nan","None"], "")

    _dn_df = _dn_df.reset_index(drop=True)
    _dn_df.index = _dn_df.index + 1
    _dn_df.index.name = "S.No"

    _dn_col_config = {}
    for _k in _dn_kolonlar:
        _dn_w = _dn_pixel_genislik.get(_k, 90)
        if _k == "adet":
            _dn_col_config[_k] = st.column_config.NumberColumn(_dn_basliklar[_k], min_value=0, step=1, width=_dn_w)
        elif _k == "kar":
            _dn_col_config[_k] = st.column_config.NumberColumn(_dn_basliklar[_k], format="%.2f ₺", width=_dn_w, disabled=True, help="Otomatik hesaplanır: STF Faturası − Taşıyıcı Fatura")
        elif _k in ("tasiyici_fatura", "stf_faturasi"):
            _dn_col_config[_k] = st.column_config.NumberColumn(_dn_basliklar[_k], format="%.2f ₺", width=_dn_w, min_value=0)
        elif _k in ("tasiyici_odendi", "stf_odendi"):
            _dn_col_config[_k] = st.column_config.CheckboxColumn(_dn_basliklar[_k], width=_dn_w)
        else:
            _dn_col_config[_k] = st.column_config.TextColumn(_dn_basliklar[_k], width=_dn_w)

    _dn_ana_col, _dn_yan_col = st.columns([2.6, 1], gap="small")
    with _dn_ana_col:
        _dn_yukseklik = max(650, min(800, 38 + (max(len(_dn_df), 3) * 35) + 3))
        _dn_edited = st.data_editor(
            _dn_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config=_dn_col_config,
            key="dn_editor",
            height=_dn_yukseklik
        )

        _dn_k1, _dn_k2, _dn_k3 = st.columns([1, 1, 4])
        with _dn_k1:
            if st.button("💾 Kaydet", type="primary", key="dn_kaydet_btn"):
                _dn_final_df = _dn_edited.reset_index(drop=True).copy()
                # KAR'ı en güncel Taşıyıcı Fatura / STF Faturası değerlerinden
                # yeniden hesapla — disabled kolon canlı güncellenmediği için
                # kaydetme anında kesin doğru değeri burada üretiyoruz.
                _dn_final_df["tasiyici_fatura"] = pd.to_numeric(_dn_final_df["tasiyici_fatura"], errors="coerce").fillna(0.0)
                _dn_final_df["stf_faturasi"] = pd.to_numeric(_dn_final_df["stf_faturasi"], errors="coerce").fillna(0.0)
                _dn_final_df["kar"] = _dn_final_df["stf_faturasi"] - _dn_final_df["tasiyici_fatura"]
                _dn_kayit_listesi = _dn_final_df.to_dict(orient="records")
                _dn_kaydedildi = False
                _dn_hata_msg = ""
                try:
                    _sb_dn1 = get_sb_client()
                    if _sb_dn1:
                        import json as _dnj1
                        _dn_json_str = _dnj1.dumps(_dn_kayit_listesi, ensure_ascii=False)
                        _sb_dn1.table("kullanici_tercih").upsert({
                            "kullanici": "__liste_ui__", "anahtar": "dis_nakliye_kayitlari",
                            "deger": _dn_json_str
                        }, on_conflict="kullanici,anahtar").execute()
                        # Doğrulama — gerçekten yazıldı mı diye geri okuyoruz
                        _dn_dogrula = _sb_dn1.table("kullanici_tercih").select("deger").eq(
                            "kullanici", "__liste_ui__").eq("anahtar", "dis_nakliye_kayitlari").execute()
                        if _dn_dogrula.data and _dn_dogrula.data[0]["deger"] == _dn_json_str:
                            _dn_kaydedildi = True
                        else:
                            _dn_hata_msg = "Yazma işlemi doğrulanamadı — veritabanına ulaşmamış olabilir."
                    else:
                        _dn_hata_msg = "Supabase bağlantısı yok."
                except Exception as _dn_e:
                    _dn_hata_msg = str(_dn_e)

                if _dn_kaydedildi:
                    st.session_state["_dn_kayitlar"] = _dn_kayit_listesi
                    st.toast(f"✅ {len(_dn_kayit_listesi)} kayıt kaydedildi!", icon="✅")
                    st.success(f"✅ {len(_dn_kayit_listesi)} kayıt kaydedildi ve doğrulandı!")
                    st.rerun()
                else:
                    st.error(f"❌ Kaydedilemedi: {_dn_hata_msg}")
        with _dn_k2:
            if st.button("➕ Satır Ekle", key="dn_satir_ekle_btn"):
                _dn_bos_satir = {c: (0 if c in ("adet","kar","tasiyici_fatura","stf_faturasi") else (False if c in ("tasiyici_odendi","stf_odendi") else "")) for c in _dn_kolonlar}
                _dn_guncel_liste = _dn_edited.reset_index(drop=True).to_dict(orient="records")
                _dn_guncel_liste.append(_dn_bos_satir)
                st.session_state["_dn_kayitlar"] = _dn_guncel_liste
                st.rerun()
    with _dn_yan_col:
        st.markdown("**🧮 KDV Hesaplayıcı**")
        _dn_h_adet = st.number_input("Adet", min_value=0, value=0, step=1, key="dn_hesap_adet")
        _dn_h_birim = st.number_input("Birim Fiyat", min_value=0.0, value=0.0, step=1.0, format="%.2f", key="dn_hesap_birim")
        _dn_h_kdv = st.number_input("KDV (%)", min_value=0.0, value=20.0, step=1.0, key="dn_hesap_kdv")
        _dn_h_toplam = _dn_h_adet * _dn_h_birim
        _dn_h_kdvli = _dn_h_toplam * (1 + _dn_h_kdv / 100)
        st.divider()
        st.metric("Toplam Tutar", f"{_dn_h_toplam:,.2f} ₺")
        st.metric("KDV'li Tutar", f"{_dn_h_kdvli:,.2f} ₺")


elif aktif == "kullanici":
    sayfa_log("kullanici")
    st.markdown("## 👥 Kullanıcı & Firma Yönetimi")

    _ben = st.session_state.get("kullanici","")
    _rol = st.session_state.get("rol","")

    # ── NORMAL KULLANICI — sadece şifre + kendi logu ──────────────────────────
    if _rol != "admin":
        ut1, ut2 = st.tabs(["🔑 Şifre Değiştir", "📊 Aktivitelerim"])

        with ut1:
            st.markdown(f"**👤 {_ben}** — Şifrenizi değiştirin")
            with st.form("kendi_sifre_form"):
                _eski = st.text_input("Mevcut Şifre:", type="password")
                _yeni1 = st.text_input("Yeni Şifre:", type="password")
                _yeni2 = st.text_input("Yeni Şifre Tekrar:", type="password")
                if st.form_submit_button("💾 Şifremi Değiştir", type="primary", use_container_width=True):
                    if not _eski or not _yeni1 or not _yeni2:
                        st.warning("Tüm alanları doldurun!")
                    elif _yeni1 != _yeni2:
                        st.error("Yeni şifreler eşleşmiyor!")
                    elif len(_yeni1) < 4:
                        st.warning("Şifre en az 4 karakter olmalı!")
                    else:
                        # Eski şifreyi doğrula
                        _df_ben = db_read("kullanicilar", extra_sql="")
                        if not _df_ben.empty:
                            _satir = _df_ben[_df_ben["kullanici_adi"]==_ben]
                            if not _satir.empty:
                                if str(_satir.iloc[0].get("sifre","")) == _eski:
                                    db_update("kullanicilar",{"sifre":_yeni1},"kullanici_adi",_ben)
                                    try: db_read.clear()
                                    except: pass
                                    kullanici_log_kaydet("SIFRE_DEGISTIRDI","kullanici","Kendi şifresini değiştirdi")
                                    st.success("✅ Şifreniz güncellendi!")
                                else:
                                    st.error("❌ Mevcut şifre hatalı!")

        with ut2:
            st.markdown(f"**📊 {_ben} — Aktivite Geçmişim**")
            _sb_ut = get_sb_client()
            try:
                _r_klog = _sb_ut.table("kullanici_log").select("*") \
                    .eq("kullanici",_ben).order("tarih",desc=True).limit(100).execute()
                _df_klog = pd.DataFrame(_r_klog.data) if _r_klog.data else pd.DataFrame()
            except:
                _df_klog = pd.DataFrame()

            if _df_klog.empty:
                st.info("Henüz aktivite kaydı yok.")
            else:
                km1,km2,km3 = st.columns(3)
                km1.metric("Toplam İşlem", len(_df_klog))
                _bugun_k = len(_df_klog[pd.to_datetime(_df_klog["tarih"],errors="coerce").dt.date == pd.Timestamp.now().date()])
                km2.metric("Bugün", _bugun_k)
                km3.metric("Son Giriş", str(_df_klog[_df_klog["islem"]=="GİRİŞ_YAPILDI"]["tarih"].max())[:16] if "GİRİŞ_YAPILDI" in _df_klog["islem"].values else "—")
                st.dataframe(
                    _df_klog[["tarih","sayfa","islem","detay"]].rename(
                        columns={"tarih":"Tarih","sayfa":"Sayfa","islem":"İşlem","detay":"Detay"}
                    ).assign(Tarih=_df_klog["tarih"].astype(str).str[:16]),
                    use_container_width=True, hide_index=True
                )
        st.stop()

    # ── ADMİN — tam yetki ─────────────────────────────────────────────────────
    TUM_MENULER = {
        "yeni":"➕ Yeni Kart","liste":"📋 Cari Liste",
        "excel":"📥 Excel","mesajlar":"💬 Mesajlar",
        "kullanici_log":"📊 Kullanıcı Log",
        "surum_yonetimi":"🚀 Sürüm Yönetimi"
    }

    # Sürüm Yönetimi sekmesi: sadece admin VEYA yetkisi olan kullanıcı
    _surum_yetkisi = (
        st.session_state.get("rol") == "admin" or
        "surum_yonetimi" in str(st.session_state.get("_yetki_listesi",""))
    )

    if st.session_state.get("rol") == "admin":
        kul_tab1, kul_tab2, kul_tab3, kul_tab4, kul_tab5, kul_tab5_ekran, kul_tab_tanim, kul_tab_kolon, kul_tab_toplu, kul_tab_font, kul_tab_kural = st.tabs(["📋 Kullanıcılar","➕ Yeni Kullanıcı","🔐 Yetki Düzenle","📊 Kullanıcı Log","🚀 Sürüm Yönetimi","🎨 Ekran Ayarları","⚙️ Tanımlar","📐 Kolon Ayarları","🔄 Toplu Değiştir","🔤 Fontlar","📌 Kurallar"])
    elif _surum_yetkisi:
        kul_tab1, kul_tab2, kul_tab3, kul_tab4, kul_tab5, kul_tab5_ekran, kul_tab_tanim, kul_tab_kolon, kul_tab_toplu, kul_tab_font, kul_tab_kural = st.tabs(["📋 Kullanıcılar","➕ Yeni Kullanıcı","🔐 Yetki Düzenle","📊 Kullanıcı Log","🚀 Sürüm Yönetimi","🎨 Ekran Ayarları","⚙️ Tanımlar","📐 Kolon Ayarları","🔄 Toplu Değiştir","🔤 Fontlar","📌 Kurallar"])
    else:
        kul_tab1, kul_tab2, kul_tab3, kul_tab4, kul_tab5_ekran, kul_tab_tanim, kul_tab_kolon, kul_tab_toplu, kul_tab_font, kul_tab_kural = st.tabs(["📋 Kullanıcılar","➕ Yeni Kullanıcı","🔐 Yetki Düzenle","📊 Kullanıcı Log","🎨 Ekran Ayarları","⚙️ Tanımlar","📐 Kolon Ayarları","🔄 Toplu Değiştir","🔤 Fontlar","📌 Kurallar"])
        kul_tab5 = None

    with kul_tab1:
        df_kul = db_read("kullanicilar", extra_sql="")
        if not df_kul.empty:
            goster_k = [c for c in ["id","kullanici_adi","ad","soyad","email","telefon","rol","yetkiler"] if c in df_kul.columns]
            st.dataframe(df_kul[goster_k], use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("#### 🔑 Şifre Değiştir")
            sp1,sp2,sp3 = st.columns(3)
            s_opts = [f"[{int(r['id'])}] {r['kullanici_adi']}" for _,r in df_kul.iterrows()]
            s_sec = sp1.selectbox("Kullanıcı:",s_opts,key="sifre_kul")
            s1 = sp2.text_input("Yeni Şifre:",type="password",key="yeni_sif1")
            s2 = sp3.text_input("Tekrar:",type="password",key="yeni_sif2")
            if st.button("🔑 Şifreyi Güncelle", use_container_width=True):
                if s1 and s1 == s2:
                    try:
                        _sb_sf = get_sb_client()
                        _sf_id = int(s_sec.split("]")[0].replace("[",""))
                        if _sb_sf:
                            _sb_sf.table("kullanicilar").update({"sifre": s1}).eq("id", _sf_id).execute()
                        try: db_read.clear()
                        except: pass
                        st.success("✅ Şifre güncellendi! Yeni şifre ile giriş yapabilirsiniz.")
                    except Exception as _sfe:
                        st.error(f"Hata: {_sfe}")
                else:
                    st.error("Şifreler eşleşmiyor veya boş!")

            st.divider()
            st.markdown("#### 🗑️ Kullanıcı Sil")
            sil_opts = [f"[{int(r['id'])}] {r['kullanici_adi']}" for _,r in df_kul.iterrows() if r["kullanici_adi"]!="admin"]
            if sil_opts:
                sil_sec = st.selectbox("Silinecek:",sil_opts,key="sil_kul")
                if st.button("🗑️ Sil",type="primary"):
                    sil_id = int(sil_sec.split("]")[0].replace("[",""))
                    sb_s = get_sb_client()
                    if sb_s:
                        sb_s.table("kullanicilar").delete().eq("id",sil_id).execute()
                    st.success("Silindi!"); st.rerun()

    with kul_tab2:
        st.markdown("#### ➕ Yeni Kullanıcı")
        with st.form("yeni_kul_form"):
            f1,f2 = st.columns(2)
            yk_ad      = f1.text_input("Ad*")
            yk_soyad   = f2.text_input("Soyad")
            yk_kadi    = f1.text_input("Kullanıcı Adı*")
            yk_sifre   = f2.text_input("Şifre*", type="password")
            yk_email   = f1.text_input("Email")
            yk_tel     = f2.text_input("Telefon", placeholder="05xxxxxxxxx")
            yk_rol     = f1.selectbox("Rol:", ["kullanici","admin"])

            st.markdown("#### 🔐 Menü Yetkileri")
            tam = st.checkbox("✅ Tam Yetki (Tümü)", value=True, key="yk_tam")
            secili_m = []
            if not tam:
                mc = st.columns(3)
                for i,(k,v) in enumerate(TUM_MENULER.items()):
                    if mc[i%3].checkbox(v, value=True, key=f"yk_m_{k}"):
                        secili_m.append(k)

            if st.form_submit_button("💾 Kaydet", use_container_width=True, type="primary"):
                if yk_kadi and yk_sifre:
                    _kadi_cakisiyor = False
                    try:
                        _df_mevcut = db_read("kullanicilar", extra_sql="")
                        if not _df_mevcut.empty and "kullanici_adi" in _df_mevcut.columns:
                            _kadi_cakisiyor = yk_kadi.strip().lower() in _df_mevcut["kullanici_adi"].astype(str).str.strip().str.lower().values
                    except Exception:
                        _kadi_cakisiyor = False

                    if _kadi_cakisiyor:
                        st.error(f"⚠️ '{yk_kadi}' kullanıcı adı zaten kayıtlı. Lütfen başka bir kullanıcı adı seçin.")
                        st.stop()

                    yetki = "tam" if tam else json.dumps(secili_m)
                    # Önce temel kolonlarla dene
                    veri = {"kullanici_adi": yk_kadi, "sifre": yk_sifre, "rol": yk_rol}
                    # Ek kolonları tek tek ekle
                    sb_k = get_sb_client()
                    if sb_k:
                        try:
                            # Tam veri ile dene
                            sb_k.table("kullanicilar").insert({
                                **veri, "ad": yk_ad, "soyad": yk_soyad,
                                "email": yk_email, "telefon": yk_tel, "yetkiler": yetki
                            }).execute()
                            st.success(f"✅ '{yk_kadi}' eklendi!")
                            st.rerun()
                        except Exception as e1:
                            if "duplicate key" in str(e1).lower() or "23505" in str(e1):
                                st.error(f"⚠️ '{yk_kadi}' kullanıcı adı zaten kayıtlı. Lütfen başka bir kullanıcı adı seçin.")
                            else:
                                try:
                                    # Sadece temel kolonlarla dene
                                    sb_k.table("kullanicilar").insert(veri).execute()
                                    st.success(f"✅ '{yk_kadi}' eklendi! (Ek bilgiler için Supabase'e kolon ekleyin)")
                                    st.rerun()
                                except Exception as e2:
                                    if "duplicate key" in str(e2).lower() or "23505" in str(e2):
                                        st.error(f"⚠️ '{yk_kadi}' kullanıcı adı zaten kayıtlı. Lütfen başka bir kullanıcı adı seçin.")
                                    else:
                                        st.error(f"Hata: {e2}")
                    else:
                        try:
                            conn_k = get_conn()
                            conn_k.execute("INSERT INTO kullanicilar (kullanici_adi,sifre,rol) VALUES (?,?,?)",
                                (yk_kadi, yk_sifre, yk_rol))
                            conn_k.commit(); conn_k.close()
                            st.success(f"✅ '{yk_kadi}' eklendi!")
                            st.rerun()
                        except Exception as e3:
                            if "unique" in str(e3).lower() or "duplicate" in str(e3).lower():
                                st.error(f"⚠️ '{yk_kadi}' kullanıcı adı zaten kayıtlı. Lütfen başka bir kullanıcı adı seçin.")
                            else:
                                st.error(f"Hata: {e3}")
                else:
                    st.warning("Kullanıcı adı ve şifre zorunlu!")

    with kul_tab3:
        st.markdown("#### 🔐 Yetki Düzenle")
        df_kul3 = db_read("kullanicilar", extra_sql="")
        if not df_kul3.empty:
            k3_opts = [f"[{int(r['id'])}] {r['kullanici_adi']}" for _,r in df_kul3.iterrows()]
            k3_sec  = st.selectbox("Kullanıcı:", k3_opts, key="yetki_sec")
            k3_id   = int(k3_sec.split("]")[0].replace("[",""))
            _k3m = df_kul3[df_kul3["id"]==k3_id]
            if _k3m.empty: raise Exception("Kullanıcı bulunamadı")
            k3_row = _k3m.iloc[0]

            mv = str(k3_row.get("yetkiler","tam") or "tam")
            try:
                mv_liste = json.loads(mv) if mv!="tam" else list(TUM_MENULER.keys())
                tam2 = mv=="tam"
            except:
                mv_liste = list(TUM_MENULER.keys()); tam2 = True

            tam2_cb = st.checkbox("✅ Tam Yetki", value=tam2, key="yetki_tam2")
            yeni_liste = []
            if not tam2_cb:
                mc2 = st.columns(3)
                for i,(k,v) in enumerate(TUM_MENULER.items()):
                    if mc2[i%3].checkbox(v, value=k in mv_liste, key=f"yetki2_{k}"):
                        yeni_liste.append(k)

            if st.button("💾 Yetkileri Kaydet", use_container_width=True, type="primary"):
                ystr = "tam" if tam2_cb else json.dumps(yeni_liste)
                db_update("kullanicilar",{"yetkiler":ystr},"id",k3_id)
                try: db_read.clear()
                except: pass
                st.success("✅ Yetkiler güncellendi!"); st.rerun()

    with kul_tab4:
        st.markdown("### 📊 Kullanıcı Aktivite Logu")
        st.caption("Kim giriş yaptı, hangi sayfaya girdi, ne yaptı — tarih saat ile")

        _sb_log = get_sb_service()
        _df_log = pd.DataFrame()
        _log_hata = ""

        try:
            if _sb_log:
                _r_log = _sb_log.table("kullanici_log").select("*").order("tarih", desc=True).limit(1000).execute()
                _df_log = pd.DataFrame(_r_log.data) if _r_log.data else pd.DataFrame()
            else:
                _log_hata = "Supabase bağlantısı yok"
        except Exception as _e_log:
            _log_hata = str(_e_log)
            st.error(f"Log yüklenemedi: {_e_log}")

        # Test log butonu
        col_test1, col_test2 = st.columns(2)
        with col_test1:
            if st.button("🔄 Logları Yenile", key="log_yenile", use_container_width=True):
                kullanici_log_kaydet("LOG_SAYFASI_YENİLENDİ", "kullanici", "Admin log sayfasını yeniledi")
                st.rerun()
        with col_test2:
            if st.button("🧪 Test Log Yaz", key="log_test", use_container_width=True):
                try:
                    _sb_log.table("kullanici_log").insert({
                        "kullanici": st.session_state.get("kullanici","admin"),
                        "rol": st.session_state.get("rol","admin"),
                        "sayfa": "test",
                        "islem": "TEST_LOG",
                        "detay": "Manuel test logu yazıldı",
                    }).execute()
                    st.success("✅ Test logu yazıldı! Şimdi yenile.")
                except Exception as _et:
                    st.error(f"Test log hatası: {_et}")

        if _log_hata:
            st.warning(f"⚠️ {_log_hata}")

        if _df_log.empty:
            st.warning("Log kaydı yok. 'Test Log Yaz' butonuna basıp 'Logları Yenile' dene.")
            st.info("Eğer test logu da yazılmıyorsa Supabase'de tablo/izin sorunu var.")
        else:
            # Filtreler
            lf1, lf2, lf3, lf4 = st.columns(4)
            _log_kullar = ["Tümü"] + sorted(_df_log["kullanici"].dropna().unique().tolist())
            _log_islemler = ["Tümü"] + sorted(_df_log["islem"].dropna().unique().tolist())
            _fil_kul  = lf1.selectbox("Kullanıcı:", _log_kullar, key="log_fil_kul")
            _fil_isl  = lf2.selectbox("İşlem:", _log_islemler, key="log_fil_isl")
            _fil_gun  = lf3.date_input("Tarihten:", key="log_fil_gun", value=None)
            _fil_ara  = lf4.text_input("🔍 Ara:", key="log_fil_ara", placeholder="Detay ara...")

            _df_fil = _df_log.copy()
            if _fil_kul  != "Tümü": _df_fil = _df_fil[_df_fil["kullanici"] == _fil_kul]
            if _fil_isl  != "Tümü": _df_fil = _df_fil[_df_fil["islem"] == _fil_isl]
            if _fil_gun: _df_fil = _df_fil[pd.to_datetime(_df_fil["tarih"], errors="coerce").dt.date >= _fil_gun]
            if _fil_ara: _df_fil = _df_fil[_df_fil.apply(lambda r: _fil_ara.lower() in str(r).lower(), axis=1)]

            st.caption(f"**{len(_df_fil)} kayıt**")

            # Özet metrikler
            lm1,lm2,lm3,lm4,lm5 = st.columns(5)
            lm1.metric("Toplam İşlem", len(_df_log))
            lm2.metric("Aktif Kullanıcı", _df_log["kullanici"].nunique())
            _bugun = pd.Timestamp.now().date()
            _bugun_log = _df_log[pd.to_datetime(_df_log["tarih"],errors="coerce").dt.date == _bugun]
            lm3.metric("Bugün", len(_bugun_log))
            _giris_say = len(_df_log[_df_log["islem"]=="GİRİŞ_YAPILDI"])
            lm4.metric("Toplam Giriş", _giris_say)
            lm5.metric("Filtrede", len(_df_fil))

            st.divider()

            # Kullanıcı bazlı özet
            with st.expander("👤 Kullanıcı Bazlı Özet"):
                _kul_oz = _df_log.groupby("kullanici").agg(
                    İşlem=("id","count"),
                    SonGiriş=("tarih","max"),
                    Sayfalar=("sayfa", lambda x: ", ".join(x.dropna().unique()[:5]))
                ).reset_index().sort_values("İşlem", ascending=False)
                _kul_oz["SonGiriş"] = _kul_oz["SonGiriş"].astype(str).str[:16]
                st.dataframe(_kul_oz, use_container_width=True, hide_index=True)

            # Sayfa bazlı özet
            with st.expander("📄 Sayfa Bazlı Ziyaret"):
                _sayfa_oz = _df_log.groupby("sayfa").agg(
                    Ziyaret=("id","count"),
                    Kullanıcı=("kullanici","nunique")
                ).reset_index().sort_values("Ziyaret", ascending=False)
                st.dataframe(_sayfa_oz, use_container_width=True, hide_index=True)

            # İşlem bazlı özet
            with st.expander("⚡ İşlem Bazlı Özet"):
                _isl_oz = _df_log.groupby("islem").agg(
                    Adet=("id","count"),
                    Kullanıcı=("kullanici","nunique")
                ).reset_index().sort_values("Adet", ascending=False)
                st.dataframe(_isl_oz, use_container_width=True, hide_index=True)

            st.divider()

            # Detay tablo
            st.markdown("**📋 Detaylı Log:**")
            _gos_kol = [c for c in ["tarih","kullanici","rol","sayfa","islem","detay"] if c in _df_fil.columns]
            _df_gos = _df_fil[_gos_kol].copy()
            _df_gos["tarih"] = _df_gos["tarih"].astype(str).str[:16]
            st.dataframe(_df_gos, use_container_width=True, hide_index=True)

            # Excel indir
            import io as _log_io
            _buf_log = _log_io.BytesIO()
            _df_fil.to_excel(_buf_log, index=False); _buf_log.seek(0)
            st.download_button(
                "📥 Log Excel İndir",
                data=_buf_log,
                file_name=f"kullanici_log_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                use_container_width=True
            )

            # Log temizle (sadece admin)
            with st.expander("🗑️ Log Temizle"):
                st.warning("Dikkat: Bu işlem geri alınamaz!")
                _sil_gun = st.number_input("Kaç günden eski logları sil:", min_value=7, value=30, step=1)
                if st.button("🗑️ Eski Logları Sil", type="primary"):
                    try:
                        from datetime import timedelta
                        _esik = (pd.Timestamp.now() - timedelta(days=int(_sil_gun))).isoformat()
                        _sb_log.table("kullanici_log").delete().lt("tarih", _esik).execute()
                        st.success(f"✅ {_sil_gun} günden eski loglar silindi!")
                        st.rerun()
                    except Exception as _e_del:
                        st.error(f"Silinemedi: {_e_del}")

    with kul_tab5_ekran:
        st.markdown("### 🎨 Ekran Ayarları")
        _sb_ekran = get_sb_client()
        _ekran_kul = st.session_state.get("kullanici","")

        def _ekran_yukle():
            try:
                if _sb_ekran:
                    _r = _sb_ekran.table("kullanici_tercih").select("deger").eq("kullanici",_ekran_kul).eq("anahtar","ekran_ayar").execute()
                    if _r.data:
                        import json as _ej
                        return _ej.loads(_r.data[0]["deger"])
            except: pass
            return {"bosluk":"normal","tema":"beyaz"}

        def _ekran_kaydet(ayar):
            try:
                import json as _ej
                if _sb_ekran:
                    _sb_ekran.table("kullanici_tercih").upsert({
                        "kullanici":_ekran_kul,"anahtar":"ekran_ayar",
                        "deger":_ej.dumps(ayar,ensure_ascii=False)
                    },on_conflict="kullanici,anahtar").execute()
                    return True
            except: pass
            return False

        _mevcut = _ekran_yukle()

        # ── SAYFA BOŞLUĞU ───────────────────────────────────────────────────
        # ── EKRAN ANALİZİ + BOŞLUK AYARI ────────────────────────────────────
        st.markdown("#### 🖥️ Ekran Analizi & Boşluk Ayarı")

        # Mevcut px değerlerini session veya Supabase'den al
        if "_ust_px" not in st.session_state:
            _kayitli_b = _mevcut.get("ust_px", 32)
            st.session_state["_ust_px"] = int(_kayitli_b)
            st.session_state["_alt_px"] = int(_mevcut.get("alt_px", 32))
            st.session_state["_yan_px"] = int(_mevcut.get("yan_px", 16))
        _ust_px  = st.session_state.get("_ust_px", 32)
        _alt_px  = st.session_state.get("_alt_px", 32)
        _yan_px  = st.session_state.get("_yan_px", 16)

        # Ekran bilgi kartları — JS ile dolduruluyor
        st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;">
  <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px;border:0.5px solid var(--color-border-tertiary);text-align:center;">
    <div style="font-size:10px;color:gray;margin-bottom:4px;">Ekran Genişliği</div>
    <div style="font-size:16px;font-weight:500;" id="sw_val">—</div>
    <div style="font-size:10px;color:gray;">px</div>
  </div>
  <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px;border:0.5px solid var(--color-border-tertiary);text-align:center;">
    <div style="font-size:10px;color:gray;margin-bottom:4px;">Ekran Yüksekliği</div>
    <div style="font-size:16px;font-weight:500;" id="sh_val">—</div>
    <div style="font-size:10px;color:gray;">px</div>
  </div>
  <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px;border:0.5px solid var(--color-border-tertiary);text-align:center;">
    <div style="font-size:10px;color:gray;margin-bottom:4px;">Üst Boşluk</div>
    <div style="font-size:16px;font-weight:500;" id="pt_val">{_ust_px}</div>
    <div style="font-size:10px;color:gray;">px</div>
  </div>
  <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px;border:0.5px solid var(--color-border-tertiary);text-align:center;">
    <div style="font-size:10px;color:gray;margin-bottom:4px;">Alt Boşluk</div>
    <div style="font-size:16px;font-weight:500;" id="pb_val">{_alt_px}</div>
    <div style="font-size:10px;color:gray;">px</div>
  </div>
</div>

<!-- Görsel temsil -->
<div style="border:0.5px solid var(--color-border-tertiary);border-radius:8px;overflow:hidden;margin-bottom:12px;">
  <div style="background:#1f6feb;height:4px;"></div>
  <div id="top_vis" style="background:#e8f4ff;display:flex;align-items:center;justify-content:center;font-size:11px;color:#1f6feb;height:{_ust_px}px;min-height:16px;transition:height 0.2s;">
    ↕ üst: <b id="top_lbl" style="margin-left:4px;">{_ust_px}px</b>
  </div>
  <div style="background:white;padding:8px 14px;font-size:12px;border-top:0.5px solid #eee;border-bottom:0.5px solid #eee;">📊 İçerik alanı</div>
  <div id="bot_vis" style="background:#e8f4ff;display:flex;align-items:center;justify-content:center;font-size:11px;color:#1f6feb;height:{_alt_px}px;min-height:16px;transition:height 0.2s;">
    ↕ alt: <b id="bot_lbl" style="margin-left:4px;">{_alt_px}px</b>
  </div>
  <div style="background:#f0f2f6;height:4px;"></div>
</div>
<script>
document.getElementById('sw_val').textContent = window.screen.width;
document.getElementById('sh_val').textContent = window.screen.height;
function updateTop(v){{
  document.getElementById('top_lbl').textContent=v+'px';
  document.getElementById('top_vis').style.height=Math.max(16,parseInt(v))+'px';
  document.getElementById('pt_val').textContent=v;
}}
function updateBot(v){{
  document.getElementById('bot_lbl').textContent=v+'px';
  document.getElementById('bot_vis').style.height=Math.max(16,parseInt(v))+'px';
  document.getElementById('pb_val').textContent=v;
}}
</script>
""", unsafe_allow_html=True)

        # Sliderlar
        _yeni_ust = st.slider("⬆️ Üst Boşluk (px)", 0, 100, _ust_px, key="slider_ust")
        _yeni_alt = st.slider("⬇️ Alt Boşluk (px)", 0, 100, _alt_px, key="slider_alt")
        _yeni_yan = st.slider("↔️ Yan Boşluk (px)", 0, 100, _yan_px, key="slider_yan")

        _bs1, _bs2 = st.columns(2)
        if _bs1.button("💾 Boşlukları Kaydet", use_container_width=True, type="primary", key="bosluk_kaydet"):
            st.session_state["_ust_px"] = _yeni_ust
            st.session_state["_alt_px"] = _yeni_alt
            st.session_state["_yan_px"] = _yeni_yan
            st.session_state["_ekran_bosluk"] = f"{_yeni_ust}px"
            st.session_state["_ekran_altbosluk"] = f"{_yeni_alt}px"
            st.session_state["_ekran_yanbosluk"] = f"{_yeni_yan}px"
            _mevcut["ust_px"] = _yeni_ust
            _mevcut["alt_px"] = _yeni_alt
            _mevcut["yan_px"] = _yeni_yan
            _ekran_kaydet(_mevcut)
            st.success("✅ Kaydedildi!")
            st.rerun()
        if _bs2.button("↺ Sıfırla", use_container_width=True, key="bosluk_sifirla"):
            st.session_state["_ust_px"] = 32
            st.session_state["_alt_px"] = 32
            st.session_state["_yan_px"] = 16
            st.session_state["_ekran_bosluk"] = "32px"
            st.session_state["_ekran_altbosluk"] = "32px"
            st.session_state["_ekran_yanbosluk"] = "16px"
            st.rerun()

        st.divider()

        if st.button("↺ Boşlukları Varsayılana Sıfırla", use_container_width=True, key="ekran_sifirla"):
            _ekran_kaydet({"bosluk": "normal"})
            st.session_state.pop("_ekran_bosluk", None)
            st.rerun()

    if kul_tab5 and (st.session_state.get("rol") == "admin" or _surum_yetkisi):
        with kul_tab5:
            st.markdown("### 🚀 Sürüm Yönetimi")

            _sb_sv = get_sb_client()
            _simdi = pd.Timestamp.now().strftime("%d.%m.%Y %H:%M")

            # Supabase'den stable bilgilerini çek
            try:
                _res_stable = _sb_sv.table("sistem_ayarlari").select("deger").eq("anahtar","stable_surum").execute()
                _stable_v = _res_stable.data[0]["deger"] if _res_stable.data else GUNCEL_SURUM
            except:
                _stable_v = GUNCEL_SURUM

            # Son yayın tarihini çek
            try:
                _res_ytar = _sb_sv.table("kullanici_log").select("tarih,kullanici").eq("islem","SURUM_YAYINLANDI").order("tarih",desc=True).limit(1).execute()
                _son_yayin = _res_ytar.data[0]["tarih"][:16].replace("T"," ") if _res_ytar.data else "—"
                _son_yayin_kim = _res_ytar.data[0]["kullanici"] if _res_ytar.data else "—"
            except:
                _son_yayin = "—"
                _son_yayin_kim = "—"

            st.markdown("---")
            _col_a, _col_b = st.columns(2)

            # ── ADMİN KARTI ──────────────────────────────────────────────────
            with _col_a:
                st.markdown(f"""
                <div style='background:#0d1117;border:2px solid #1f6feb;border-radius:12px;padding:20px'>
                <div style='font-size:0.85rem;color:#888;margin-bottom:8px'>👑 ADMİN — Son Geliştirme Sürümü</div>
                <div style='font-size:2.2rem;font-weight:bold;color:#1f6feb;margin-bottom:4px'>{GUNCEL_SURUM}</div>
                <div style='font-size:0.8rem;color:#666'>📅 Şu an: {_simdi}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("")
                # Yayınla butonu — her zaman görünür
                if _stable_v == GUNCEL_SURUM:
                    st.success(f"✅ Son sürüm ({GUNCEL_SURUM}) zaten yayında")
                else:
                    st.info(f"📢 Kullanıcılar **{_stable_v}** sürümünde. **{GUNCEL_SURUM}** hazır.")

                if st.button(f"🚀 {GUNCEL_SURUM} Sürümünü Yayınla",
                            type="primary", use_container_width=True, key="surum_yayinla"):
                    try:
                        _sb_sv.table("sistem_ayarlari").upsert(
                            {"anahtar":"stable_surum","deger":GUNCEL_SURUM},
                            on_conflict="anahtar").execute()
                        kullanici_log_kaydet("SURUM_YAYINLANDI","kullanici",
                            f"{_stable_v} → {GUNCEL_SURUM} yayınlandı")
                        st.success(f"✅ {GUNCEL_SURUM} yayınlandı!")
                        st.balloons()
                        st.rerun()
                    except Exception as _esv:
                        st.error(f"Hata: {_esv}")

                # Geri yükle — önceki sürüme dön
                st.markdown("")
                with st.expander("🔄 Önceki Sürüme Geri Al"):
                    try:
                        _res_gecmis = _sb_sv.table("kullanici_log").select("tarih,detay").eq("islem","SURUM_YAYINLANDI").order("tarih",desc=True).limit(10).execute()
                        if _res_gecmis.data and len(_res_gecmis.data) > 1:
                            _gecmis_opts = [r["detay"] for r in _res_gecmis.data[1:6]]
                            _geri_sec = st.selectbox("Sürüm seç:", _gecmis_opts, key="geri_yukle_sec")
                            if st.button("🔄 Geri Yükle", key="geri_yukle_btn", use_container_width=True):
                                # Sürüm adını parse et
                                import re as _re_sv
                                _match = _re_sv.search(r'→ (v[\d.]+)', _geri_sec)
                                if _match:
                                    _geri_v = _match.group(1)
                                    _sb_sv.table("sistem_ayarlari").upsert(
                                        {"anahtar":"stable_surum","deger":_geri_v},
                                        on_conflict="anahtar").execute()
                                    kullanici_log_kaydet("SURUM_GERİ_ALINDI","kullanici",f"→ {_geri_v}")
                                    st.success(f"✅ {_geri_v} geri yüklendi!")
                                    st.rerun()
                        else:
                            st.caption("Geri alınabilecek sürüm yok.")
                    except Exception as _eg:
                        st.caption(f"Hata: {_eg}")

            # ── KULLANICI KARTI ───────────────────────────────────────────────
            with _col_b:
                _renk = "#28a745" if _stable_v == GUNCEL_SURUM else "#ff9800"
                _durum_yazi = "✅ Güncel" if _stable_v == GUNCEL_SURUM else "⏳ Güncelleme Hazır"
                st.markdown(f"""
                <div style='background:#0d1117;border:2px solid {_renk};border-radius:12px;padding:20px'>
                <div style='font-size:0.85rem;color:#888;margin-bottom:8px'>👥 KULLANICILAR — Yayındaki Sürüm</div>
                <div style='font-size:2.2rem;font-weight:bold;color:{_renk};margin-bottom:4px'>{_stable_v}</div>
                <div style='font-size:0.8rem;color:#666'>📅 Son yayın: {_son_yayin}</div>
                <div style='font-size:0.8rem;color:#666'>👤 Yayınlayan: {_son_yayin_kim}</div>
                <div style='font-size:0.85rem;color:{_renk};margin-top:8px'>{_durum_yazi}</div>
                </div>
                """, unsafe_allow_html=True)

                # Yayınlama geçmişi
                st.markdown("")
                with st.expander("📋 Yayınlama Geçmişi"):
                    try:
                        _res_log_sv = _sb_sv.table("kullanici_log").select("*")                             .in_("islem",["SURUM_YAYINLANDI","SURUM_GERİ_ALINDI"])                             .order("tarih",desc=True).limit(15).execute()
                        if _res_log_sv.data:
                            _df_sv = pd.DataFrame(_res_log_sv.data)[["tarih","kullanici","islem","detay"]]
                            _df_sv["tarih"] = _df_sv["tarih"].astype(str).str[:16].str.replace("T"," ")
                            _df_sv.columns = ["Tarih","Kim","İşlem","Detay"]
                            st.dataframe(_df_sv, use_container_width=True, hide_index=True)
                        else:
                            st.caption("Henüz yayın geçmişi yok.")
                    except:
                        st.caption("Yüklenemedi.")

            st.divider()
            with st.expander("📖 Nasıl Çalışır?"):
                st.markdown(f"""
**Kullanıcılar hiç durmaz — iş kesilmez.**

| | Admin | Kullanıcılar |
|---|---|---|
| Sürüm | **{GUNCEL_SURUM}** | **{_stable_v}** |
| Durum | Son geliştirme | Kararlı yayın |

1. Kodu değiştir → push yap *(kullanıcılar etkilenmez)*
2. Admin olarak test et
3. **🚀 Yayınla** → kullanıcılar yeni sürüme geçer
4. Sorun çıkarsa **🔄 Geri Al** → önceki sürüme dön
                """)

    # ── 📐 KOLON AYARLARI ─────────────────────────────────────────────────────
    with kul_tab_kolon:
        # ── 🔍 FİLTRE DÜZENLE — KULLANICI İSTEĞİ (2026-09): Cari Liste'nin
        # filtre satırında EK bir filtre gösterilsin, ama HANGİ alanın
        # filtreleneceği burada seçilebilsin (örn. "Yetkili") — sabit kod
        # yazmak yerine, istenirse başka bir alana da kolayca çevrilebilir.
        st.markdown("### 🔍 Filtre Düzenle")
        st.caption("Cari Liste'nin filtre satırında ek bir filtre kutusu göstermek için, hangi alanın filtreleneceğini seçin (örn. Yetkili).")
        _cl_filtre_mevcut = st.session_state.get("_cl_ozel_filtre_alani_cache")
        if _cl_filtre_mevcut is None:
            _cl_filtre_mevcut = _cl_ozel_filtre_alani_yukle()
            st.session_state["_cl_ozel_filtre_alani_cache"] = _cl_filtre_mevcut
        _cl_filtre_secenek_liste = list(_CL_OZEL_FILTRE_SECENEKLERI.keys())
        _cl_filtre_idx = _cl_filtre_secenek_liste.index(_cl_filtre_mevcut) if _cl_filtre_mevcut in _cl_filtre_secenek_liste else 0
        _cl_filtre_sec_ui = st.selectbox(
            "Filtrelenecek alan", _cl_filtre_secenek_liste, index=_cl_filtre_idx,
            format_func=lambda k: _CL_OZEL_FILTRE_SECENEKLERI[k], key="cl_filtre_duzenle_sec"
        )
        if st.button("💾 Filtre Ayarını Kaydet", key="cl_filtre_duzenle_kaydet_btn"):
            _cl_filtre_kaydet_ok = _cl_ozel_filtre_alani_kaydet(_cl_filtre_sec_ui)
            if _cl_filtre_kaydet_ok:
                st.session_state["_cl_ozel_filtre_alani_cache"] = _cl_filtre_sec_ui
                st.success(f"✅ Cari Liste'de artık '{_CL_OZEL_FILTRE_SECENEKLERI[_cl_filtre_sec_ui]}' filtresi gösterilecek." if _cl_filtre_sec_ui else "✅ Ek filtre kapatıldı.")
            else:
                st.error("⚠️ Kaydedilemedi — lütfen tekrar dene.")
        st.divider()

        # ── 🔢 MÜŞTERİ KODU YENİDEN BAŞLAT — KULLANICI İSTEĞİ (2026-09) ──────
        st.markdown("### 🔢 Müşteri Kodu (MW1, MW2, ...) Yeniden Başlat")
        st.caption("Gerçek veritabanı ID'sine (kargo/not/randevu gibi onlarca yerde kullanılan asıl anahtar) DOKUNULMAZ, o hep sabit kalır. Bu SADECE görüntülenen 'Müşteri Kodu' sütununu, kayıt tarihine göre sıralı, boşluksuz MW1'den başlayarak yeniden numaralar. Bundan sonra silinen bir müşterinin kodu, yeni eklenen bir müşteriye otomatik verilir.")
        if st.button("🔄 Müşteri Kodlarını MW1'den Yeniden Başlat", key="mk_yeniden_baslat_btn"):
            st.session_state["_mk_yeniden_baslat_onay"] = True
        if st.session_state.get("_mk_yeniden_baslat_onay"):
            st.warning("⚠️ Bu, TÜM müşterilerin görüntülenen kodunu değiştirir (kayıt tarihine göre MW1, MW2, ...). Emin misin?")
            _mkc1, _mkc2 = st.columns(2)
            if _mkc1.button("✅ Evet, Yeniden Başlat", key="mk_yeniden_baslat_evet", use_container_width=True):
                _mk_tum_df = get_cari_listesi()
                _mk_yeni_harita = _musteri_kodu_yeniden_baslat(_mk_tum_df)
                if _mk_yeni_harita:
                    _mk_ok = _musteri_kodu_kaydet(_mk_yeni_harita)
                    if _mk_ok:
                        st.session_state.pop("_mk_yeniden_baslat_onay", None)
                        st.success(f"✅ {len(_mk_yeni_harita)} müşterinin kodu MW1'den yeniden numaralandırıldı (kayıt tarihine göre).")
                        st.rerun()
                    else:
                        st.error("⚠️ Kaydedilemedi — lütfen tekrar dene.")
                else:
                    st.warning("Müşteri bulunamadı.")
            if _mkc2.button("❌ Vazgeç", key="mk_yeniden_baslat_vazgec", use_container_width=True):
                st.session_state.pop("_mk_yeniden_baslat_onay", None)
                st.rerun()
        st.divider()

        # ── 🔁 İL CİROLARI / HEDEFLENEN CİRO YENİDEN HESAPLA — KULLANICI
        # İSTEĞİ (2026-09): eski (hatalı) hesaplama yöntemiyle daha önce
        # kaydedilmiş müşterilerin "İl Ciroları" ve "Hedeflenen Ciro" değerleri
        # YANLIŞ kalmaya devam ediyordu (kod düzeltmesi SADECE bundan sonraki
        # yeni kayıtları etkiler, geçmiş kayıtları OTOMATİK düzeltmez). Bu
        # buton, Koli/Palet fiyat tablosu OLAN TÜM müşteriler için ikisini de
        # GÜNCEL (doğru) yöntemle tek seferde yeniden hesaplar.
        st.markdown("### 🔁 İl Ciroları / Hedeflenen Ciro Yeniden Hesapla")
        st.caption("Koli/Palet fiyat tablosu olan TÜM müşteriler için 'İl Ciroları' ve 'Hedeflenen Ciro'yu, GÜNCEL (düzeltilmiş) yönteme göre tek seferde yeniden hesaplar. Sadece bu iki alan güncellenir, başka hiçbir veriye dokunulmaz.")
        if st.button("🔁 Tüm Müşteriler İçin Yeniden Hesapla", key="icy_yeniden_hesapla_btn"):
            st.session_state["_icy_yeniden_hesapla_onay"] = True
        if st.session_state.get("_icy_yeniden_hesapla_onay"):
            st.warning("⚠️ Bu, Koli/Palet fiyat tablosu olan TÜM müşterilerin 'İl Ciroları' ve 'Hedeflenen Ciro' değerlerini günceller. Emin misin?")
            _icyc1, _icyc2 = st.columns(2)
            if _icyc1.button("✅ Evet, Yeniden Hesapla", key="icy_yeniden_hesapla_evet", use_container_width=True):
                _icy_koli_harita = st.session_state.get("_koli_palet_manuel", {})
                if not _icy_koli_harita:
                    try:
                        _sb_icy = get_sb_client()
                        if _sb_icy:
                            _r_icy = _sb_icy.table("kullanici_tercih").select("deger").eq(
                                "kullanici", "__liste_ui__").eq("anahtar", "_koli_palet_manuel").execute()
                            if _r_icy.data:
                                _icy_koli_harita = json.loads(_r_icy.data[0]["deger"])
                    except Exception:
                        _icy_koli_harita = {}
                if not _icy_koli_harita:
                    st.warning("Koli/Palet fiyat tablosu olan hiçbir müşteri bulunamadı.")
                    st.session_state.pop("_icy_yeniden_hesapla_onay", None)
                else:
                    _icy_ilerleme = st.progress(0, text="Hesaplanıyor...")
                    _icy_ek_harita = _cari_ek_bilgi_yukle()
                    _icy_toplam_sayi = len(_icy_koli_harita)
                    _icy_guncellenen = 0
                    for _icy_i, (_icy_cid, _icy_metin) in enumerate(_icy_koli_harita.items()):
                        _icy_ilerleme.progress((_icy_i + 1) / _icy_toplam_sayi, text=f"Hesaplanıyor... {_icy_i + 1}/{_icy_toplam_sayi}")
                        if not str(_icy_metin or "").strip():
                            continue
                        _icy_yeni_ozet = _fy_il_ciro_ozet_cikar(_icy_metin)
                        _icy_yeni_hedef = _fy_il_ciro_genel_toplam(_icy_metin)
                        _icy_ek_harita.setdefault(_icy_cid, {})["il_ciro_ozet"] = _icy_yeni_ozet
                        if _icy_yeni_hedef is not None:
                            try:
                                db_update("cari_kartlar", {"beklenen_ciro": _icy_yeni_hedef}, "id", int(_icy_cid))
                                _icy_guncellenen += 1
                            except Exception:
                                pass
                    _cari_ek_bilgi_kaydet(_icy_ek_harita)
                    get_cari_listesi.clear()
                    _icy_ilerleme.empty()
                    st.session_state.pop("_icy_yeniden_hesapla_onay", None)
                    st.success(f"✅ {_icy_guncellenen} müşterinin İl Ciroları ve Hedeflenen Ciro'su yeniden hesaplandı.")
                    st.rerun()
            if _icyc2.button("❌ Vazgeç", key="icy_yeniden_hesapla_vazgec", use_container_width=True):
                st.session_state.pop("_icy_yeniden_hesapla_onay", None)
                st.rerun()
        st.divider()

        st.markdown("### 📐 Cari Liste Kolon Ayarları")
        st.caption("Genişlik ayarlayın, gizlemek istediklerinizi kapatın → Kaydet")
        _KOL_VARS_UI = {
            "Seç":40,"tarih":90,"guncelleme_tarihi":100,
            "hesaplama":130,"firma":100,"rakip_firma":100,"yetkili":100,"gsm":110,"sabit":100,"email":100,
            "adres":120,"il":80,"ilce":70,"durum":90,"temsilci":90,
            "vergi_no":90,"vergi_dairesi":100,"musteri_subesi":100,"vade":70,"odeme":80,"teklif_fiyat":90,"islem_tarihi_manuel":90,"takip_tarihi_manuel":90,"randevu_tarihi_manuel":100,
            "islem_asamasi":90,"aciklama":120,"📅 Son Randevu":180,"📨 Notlar":60,"id":50,"musteri_kodu":80,
            "asama1":100,"asama2":100,"asama3":100,"sonuc":100,"ara_islem":100,"il_ciro_ozet":120,"sektor":100,"rut":100,
            "beklenen_ciro":80,"gerceklesen_ciro":80,"✅ Analiz":80,"Varış İli":100,"Koli/Palet":120,
            "🧾 Teklif":70,"💬 Mesaj":70
        }
        for _il_kv in _IL_SUTUN_LISTESI:
            _KOL_VARS_UI[_il_kv] = 60
        _KG_UI_ETIKET = {
            "Seç":"Seç (işaret kutusu)","tarih":"İşlem Tarih","guncelleme_tarihi":"Güncelleme Tarihi",
            "hesaplama":"Hesaplama","firma":"Firma","rakip_firma":"Özel","yetkili":"Yetkili","gsm":"GSM","sabit":"S.Tel",
            "email":"Email","adres":"Adres","il":"İl","ilce":"İlçe",
            "durum":"Durum","temsilci":"Temsilci","islem_asamasi":"İlk Temas",
            "vergi_no":"Vergi No","vergi_dairesi":"Vergi Dairesi","musteri_subesi":"Müşteri Şubesi","vade":"Vade","odeme":"Ödeme","musteri_kodu":"Müşteri Kodu","teklif_fiyat":"Teklif Fiyat","islem_tarihi_manuel":"İşlem Tarihi","takip_tarihi_manuel":"Takip Tarihi","randevu_tarihi_manuel":"Randevu Tarihi",
            "aciklama":"Açıklama","📅 Son Randevu":"Randevu","📨 Notlar":"Notlar","id":"ID",
            "asama1":"1. Aşama","asama2":"2. Aşama","asama3":"3. Aşama","sonuc":"Sonuç","ara_islem":"Ara İşlem","il_ciro_ozet":"İl Ciroları","sektor":"Sektör","rut":"🛣️ Rut",
            "beklenen_ciro":"Hedef ₺","gerceklesen_ciro":"Gerçek ₺","✅ Analiz":"Analiz","Varış İli":"Varış İli","Koli/Palet":"Koli/Palet",
            "🧾 Teklif":"Teklif","💬 Mesaj":"Mesaj"
        }
        for _il_ke in _IL_SUTUN_LISTESI:
            _KG_UI_ETIKET[_il_ke] = _il_ke
        # ÖNEMLİ: Ana listenin de kullandığı session_state["_kol_genislik"] tek doğruluk kaynağıdır.
        # Burada AYRI bir DB sorgusu yapmıyoruz — aksi halde iki farklı kaynak birbirini
        # ezip "ayarladığım gibi kalmıyor" sorununa yol açıyordu.
        # NOT (hata düzeltmesi): _sb_kg_ui ve _kguj burada, session_state zaten
        # doluysa (yani aşağıdaki "else" dalı çalışıyorsa) TANIMLANMIYORDU.
        # Bu yüzden "Gizle/Göster" butonuna basınca (sayfa ilk açılıştan sonra,
        # yani hep) sessizce NameError alıp hiçbir şey kaydetmiyordu — "çalışmıyor"
        # sorununun kök nedeni buydu. Şimdi her ikisi de KOŞULDAN BAĞIMSIZ,
        # her zaman tanımlanıyor.
        import json as _kguj
        _sb_kg_ui = get_sb_client()
        if "_kol_genislik" not in st.session_state or "_kol_gizli" not in st.session_state:
            try:
                _kg_ui_mevcut = _KOL_VARS_UI.copy()
                _gizli_ui = []
                if _sb_kg_ui:
                    _r_kgu = _sb_kg_ui.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_kol_genislik").execute()
                    if _r_kgu.data:
                        _kg_ui_mevcut = _kguj.loads(_r_kgu.data[0]["deger"])
                    _r_gizli = _sb_kg_ui.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_kol_gizli").execute()
                    if _r_gizli.data:
                        _gizli_ui = _kguj.loads(_r_gizli.data[0]["deger"])
            except:
                _kg_ui_mevcut = _KOL_VARS_UI.copy()
                _gizli_ui = []
            st.session_state["_kol_genislik"] = {**_KOL_VARS_UI.copy(), **_kg_ui_mevcut}
            st.session_state["_kol_gizli"] = _gizli_ui
        else:
            _kg_ui_mevcut = st.session_state["_kol_genislik"]
            _gizli_ui = st.session_state["_kol_gizli"]

        _yeni_kg_ui = {}
        _yeni_gizli_ui = []
        # NOT: 50+ alan tek satıra sığmadığı için (bazıları görünmez oluyordu),
        # 12'şerli satırlara bölünüyor — görünüm (kutu/ikon YOK, sade göz+
        # kaydırıcı) aynı kalıyor, sadece satır satır devam ediyor.
        _kg_ui_anahtarlar = list(_KOL_VARS_UI.keys())
        for _s in range(0, len(_kg_ui_anahtarlar), 12):
            _ui_cols = st.columns(min(12, len(_kg_ui_anahtarlar) - _s))
            for _j, _k in enumerate(_kg_ui_anahtarlar[_s:_s + 12]):
                _i = _s + _j
                _etiket = _KG_UI_ETIKET.get(_k, _k)
                _gizli_mi = _k in _gizli_ui
                with _ui_cols[_j]:
                    # Göz ikonu — tıklayınca gizle/göster
                    _goz = "🙈" if _gizli_mi else "👁"
                    if st.button(_goz, key=f"ui_giz_{_i}_{_k[:4]}", use_container_width=True,
                                 help="Gizle/Göster"):
                        if _gizli_mi:
                            _gizli_ui = [x for x in _gizli_ui if x != _k]
                        else:
                            _gizli_ui.append(_k)
                        # Oturum içinde HEMEN uygula — DB yazımı başarısız olsa bile
                        # buton görsel olarak tepkisiz kalmasın.
                        st.session_state["_kol_gizli"] = _gizli_ui
                        st.session_state.pop("_kol_genislik_init", None)
                        # Kalıcı olması için DB'ye de yaz (upsert+on_conflict yerine
                        # sil+ekle — kullanici_tercih tablosunda bu kısıt olmadığı
                        # için upsert sessizce başarısız oluyordu, ayarlar hiç
                        # kalıcı olmuyordu).
                        try:
                            _kguj_deger = _kguj.dumps(_gizli_ui, ensure_ascii=False)
                            _kgui_guncelle = _sb_kg_ui.table("kullanici_tercih").update({"deger": _kguj_deger}).eq(
                                "kullanici", "__liste_ui__").eq("anahtar", "_kol_gizli").execute()
                            if not _kgui_guncelle.data:
                                _sb_kg_ui.table("kullanici_tercih").insert({
                                    "kullanici": "__liste_ui__", "anahtar": "_kol_gizli", "deger": _kguj_deger
                                }).execute()
                        except Exception as _kgize:
                            st.toast(f"⚠️ Gizle/Göster kaydedilemedi: {_kgize}", icon="⚠️")
                        st.rerun()
                    # Slider — gizliyse devre dışı.
                    _yeni_kg_ui[_k] = st.slider(
                        f"{'~~' if _gizli_mi else ''}{_etiket}",
                        min_value=5, max_value=50,
                        value=max(min(int(_kg_ui_mevcut.get(_k, _KOL_VARS_UI.get(_k,100))), 50), 5),
                        step=5, key=f"ui_kg_{_k}",
                        disabled=_gizli_mi
                    )
                    if _gizli_mi:
                        _yeni_gizli_ui.append(_k)

        # Canlı önizleme: Kaydet'e basmadan slider'ı hareket ettirir ettirmez
        # ana listedeki tablo hemen bu genişlikleri kullanır (henüz DB'ye yazılmaz,
        # sayfayı/oturumu tamamen kapatıp açarsan Kaydet basılmayan değişiklik kaybolur)
        st.session_state["_kol_genislik"] = {**st.session_state.get("_kol_genislik", {}), **_yeni_kg_ui}
        st.session_state["_kol_genislik_init"] = True  # liste sayfası DB'den tekrar çekip ezmesin
        st.caption("👆 Değerler anında canlı önizlenir. Kalıcı olması (herkeste, her oturumda) için **Kaydet**'e basın.")

        if st.button("💾 Kaydet", type="primary", key="ui_kg_kaydet"):
            try:
                _sb_kg_s = get_sb_client()
                if _sb_kg_s:
                    import json as _kgsj2
                    # GÜVENLİ (2026-09): satır varsa UPDATE (unique constraint
                    # gerektirmez), yoksa INSERT — "önce sil sonra ekle" ARTIK
                    # KULLANILMIYOR (ağ kopmasında veri kaybı riski taşıyordu).
                    _kg_genislik_deger = _kgsj2.dumps(_yeni_kg_ui, ensure_ascii=False)
                    _kg_genislik_guncelle = _sb_kg_s.table("kullanici_tercih").update({"deger": _kg_genislik_deger}).eq(
                        "kullanici", "__liste_ui__").eq("anahtar", "_kol_genislik").execute()
                    if not _kg_genislik_guncelle.data:
                        _sb_kg_s.table("kullanici_tercih").insert({
                            "kullanici": "__liste_ui__", "anahtar": "_kol_genislik", "deger": _kg_genislik_deger
                        }).execute()
                    _kg_gizli_deger = _kgsj2.dumps(_gizli_ui, ensure_ascii=False)
                    _kg_gizli_guncelle = _sb_kg_s.table("kullanici_tercih").update({"deger": _kg_gizli_deger}).eq(
                        "kullanici", "__liste_ui__").eq("anahtar", "_kol_gizli").execute()
                    if not _kg_gizli_guncelle.data:
                        _sb_kg_s.table("kullanici_tercih").insert({
                            "kullanici": "__liste_ui__", "anahtar": "_kol_gizli", "deger": _kg_gizli_deger
                        }).execute()
                st.session_state["_kol_genislik"] = _yeni_kg_ui
                st.session_state["_kol_gizli"] = _gizli_ui
                st.session_state.pop("_kol_genislik_init", None)
                st.toast("✅ Kolon ayarları kaydedildi!", icon="✅")
                st.rerun()
            except Exception as _kgue:
                st.error(f"Hata: {_kgue}")

        # ── 📦 KARGO GİRİŞİ KOLON AYARLARI — ayrı, bağımsız bir ayar seti.
        # Ana Cari Liste'nin kolon genişlik mantığına dokunmaz, kendi anahtarında
        # ("_kargo_kol_genislik") saklanır. Genişlik aralığı: 5 – 50.
        st.divider()
        st.markdown("### 📦 Kargo Girişi Kolon Ayarları")
        _KARGO_KOL_ETIKET = {
            "Müşteri":"Müşteri","Tarih":"Tarih","Takip No":"Takip No","Gönderen":"Gönderen","Alıcı":"Alıcı",
            "Fatura Ödeyen":"Fatura Ödeyen","Gönderen İl":"Gönderen İl","Alıcı İl":"Alıcı İl","Adet":"Adet",
            "Tür":"Tür","Tutar":"Tutar","KDV":"KDV","Sigorta":"Sigorta","Toplam Fatura":"Toplam Fatura",
            "Ödeme Türü":"Ödeme Türü","Fatura Ödeme Şekli":"Fatura Ödeme Şekli","Tahsilat":"Tahsilat",
            "Dış Nakliye Firma":"Dış Nak. Firma",
            "Dış Nakliye Fatura":"Dış Nak. Fatura","Dış Nakliye Detay":"Dış Nak. Detay",
            "Dış Nakliye Tutar":"Dış Nak. Tutar","Müşteri Tutar":"Müşteri Tutar","Kar":"Kar",
            "Dış Nak. Ödeme":"Dış Nak. Ödeme", "Desi":"Desi", "Kilo":"Kilo",
        }
        _KARGO_KOL_VARSAYILAN = {k: 15 for k in _KARGO_KOL_ETIKET}
        try:
            _sb_kg2 = get_sb_client()
            _kargo_kg_mevcut = _KARGO_KOL_VARSAYILAN.copy()
            if _sb_kg2:
                _r_kargokg = _sb_kg2.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_kargo_kol_genislik").execute()
                if _r_kargokg.data:
                    import json as _kkgj
                    _kargo_kg_mevcut = {**_KARGO_KOL_VARSAYILAN, **_kkgj.loads(_r_kargokg.data[0]["deger"])}
        except Exception:
            _kargo_kg_mevcut = _KARGO_KOL_VARSAYILAN.copy()

        _yeni_kargo_kg = {}
        _kargo_ui_cols = st.columns(6)
        for _ki, _kk_ad in enumerate(_KARGO_KOL_ETIKET.keys()):
            with _kargo_ui_cols[_ki % 6]:
                _yeni_kargo_kg[_kk_ad] = st.slider(
                    _KARGO_KOL_ETIKET[_kk_ad], min_value=5, max_value=50,
                    value=int(_kargo_kg_mevcut.get(_kk_ad, 15)), step=1, key=f"kargo_kg_{_ki}"
                )
        if st.button("💾 Kargo Kolon Ayarlarını Kaydet", type="primary", key="kargo_kg_kaydet_btn"):
            try:
                _sb_kg3 = get_sb_client()
                if _sb_kg3:
                    import json as _kkgj2
                    _kkg_deger = _kkgj2.dumps(_yeni_kargo_kg, ensure_ascii=False)
                    _kkg_guncelle = _sb_kg3.table("kullanici_tercih").update({"deger": _kkg_deger}).eq(
                        "kullanici", "__liste_ui__").eq("anahtar", "_kargo_kol_genislik").execute()
                    if not _kkg_guncelle.data:
                        _sb_kg3.table("kullanici_tercih").insert({
                            "kullanici": "__liste_ui__", "anahtar": "_kargo_kol_genislik", "deger": _kkg_deger
                        }).execute()
                st.session_state["_kargo_kol_genislik"] = _yeni_kargo_kg
                st.toast("✅ Kargo kolon ayarları kaydedildi!", icon="✅")
                st.rerun()
            except Exception as _kkgue:
                st.error(f"Hata: {_kkgue}")

    # ── 🔄 TOPLU DEĞİŞTİR ────────────────────────────────────────────────────
    with kul_tab_toplu:
        st.markdown("### 🔄 Toplu Aşama / Durum Değiştir")
        st.caption("Seçili aşama veya durumu toplu olarak değiştirin")

        _sb_toplu = get_sb_client()
        _df_toplu = db_read("cari_kartlar", extra_sql="WHERE (silindi=0 OR silindi='0' OR silindi IS NULL)")

        if not _df_toplu.empty:
            _tc1, _tc2, _tc3 = st.columns(3)

            # Filtrele
            _t_tem_opts = ["Tümü"] + sorted(_df_toplu["temsilci"].dropna().astype(str).unique().tolist()) if "temsilci" in _df_toplu.columns else ["Tümü"]
            _t_tem = _tc1.selectbox("Temsilci filtrele", _t_tem_opts, key="toplu_tem")
            if _t_tem != "Tümü":
                _df_toplu = _df_toplu[_df_toplu["temsilci"] == _t_tem]

            _t_asama_l = _tanimlar_yukle("asama")
            _t_durum_l  = _tanimlar_yukle("durum")

            _t_asama_opts = ["Tümü"] + _t_asama_l
            _t_asama_fil = _tc2.selectbox("Mevcut Aşama filtrele", _t_asama_opts, key="toplu_asama_fil")
            if _t_asama_fil != "Tümü":
                _df_toplu = _df_toplu[_df_toplu["islem_asamasi"] == _t_asama_fil]

            _t_durum_opts = ["Tümü"] + _t_durum_l
            _t_durum_fil = _tc3.selectbox("Mevcut Durum filtrele", _t_durum_opts, key="toplu_durum_fil")
            if _t_durum_fil != "Tümü":
                _df_toplu = _df_toplu[_df_toplu["durum"] == _t_durum_fil]

            st.caption(f"**{len(_df_toplu)} müşteri** seçili")

            st.divider()
            st.markdown("#### Ne Değiştirilsin?")
            _tc4, _tc5 = st.columns(2)

            _degistir_ne = _tc4.radio("Değiştirilecek alan:", ["Aşama", "Durum"], horizontal=True, key="toplu_ne")

            if _degistir_ne == "Aşama":
                _yeni_deger = _tc5.selectbox("Yeni Aşama:", ["— Boş (Temizle) —"] + _t_asama_l, key="toplu_yeni_asama")
                _alan = "islem_asamasi"
                _yeni_deger_db = "" if _yeni_deger == "— Boş (Temizle) —" else _yeni_deger
            else:
                _yeni_deger = _tc5.selectbox("Yeni Durum:", ["— Boş (Temizle) —"] + _t_durum_l, key="toplu_yeni_durum")
                _alan = "durum"
                _yeni_deger_db = "" if _yeni_deger == "— Boş (Temizle) —" else _yeni_deger

            _secim_gecerli = True  # Boş da geçerli seçim

            # Önizleme
            with st.expander(f"👁 Etkilenecek {len(_df_toplu)} müşteriyi gör", expanded=False):
                st.dataframe(_df_toplu[["id","firma","durum","islem_asamasi","temsilci"]].head(50),
                           use_container_width=True, hide_index=True)

            _onay = st.checkbox(f"✅ **{len(_df_toplu)} müşterinin {_degistir_ne} değerini '{_yeni_deger}' yapmayı onaylıyorum**", key="toplu_onay", disabled=not _secim_gecerli)

            if st.button("🔄 Toplu Değiştir", type="primary", key="toplu_kaydet", disabled=not (_onay and _secim_gecerli)):
                _basarili = 0
                _hatali = 0
                for _, _tr in _df_toplu.iterrows():
                    try:
                        if _sb_toplu:
                            _sb_toplu.table("cari_kartlar").update({_alan: _yeni_deger_db}).eq("id", int(_tr["id"])).execute()
                        _basarili += 1
                    except:
                        _hatali += 1
                try: db_read.clear()
                except: pass
                st.session_state.pop("toplu_onay", None)
                if _basarili:
                    st.success(f"✅ {_basarili} müşteri güncellendi!" + (f" ⚠️ {_hatali} hata" if _hatali else ""))
                    st.rerun()
                else:
                    st.error("Güncelleme başarısız!")
        else:
            st.info("Müşteri verisi bulunamadı.")
    with kul_tab_tanim:
        st.markdown("### ⚙️ Aşama & Durum Tanımları")
        _sb_tan = get_sb_client()

        def _tan_liste(tip):
            try:
                if _sb_tan:
                    r = _sb_tan.table("sistem_tanimlar").select("deger").eq("tip",tip).order("sira").execute()
                    # Deduplicate — sırayı koru
                    _goruldu = set()
                    _liste = []
                    for d in (r.data or []):
                        v = str(d["deger"] or "").strip()
                        if v and v not in _goruldu:
                            _liste.append(v)
                            _goruldu.add(v)
                    return _liste
            except: return []

        def _tan_ekle(tip, deger):
            try:
                if _sb_tan:
                    # Önce duplicate kontrolü
                    mevcut_kayit = _sb_tan.table("sistem_tanimlar").select("id").eq("tip",tip).eq("deger",deger.strip()).execute()
                    if mevcut_kayit.data:
                        return False  # Zaten var
                    mevcut_sira = _sb_tan.table("sistem_tanimlar").select("sira").eq("tip",tip).order("sira",desc=True).limit(1).execute()
                    sira = (mevcut_sira.data[0]["sira"] + 1) if mevcut_sira.data else 1
                    _sb_tan.table("sistem_tanimlar").insert({"tip":tip,"deger":deger.strip(),"sira":sira}).execute()
                    return True
            except: return False

        def _tan_sil(tip, deger):
            try:
                if _sb_tan:
                    # Aynı isimde TÜM kayıtları sil (duplicate temizler)
                    _sb_tan.table("sistem_tanimlar").delete().eq("tip",tip).eq("deger",deger).execute()
                    return True
            except: return False

        def _tan_temizle(tip):
            """Duplicate kayıtları temizle — her değerden sadece birini bırak"""
            try:
                if _sb_tan:
                    r = _sb_tan.table("sistem_tanimlar").select("id,deger,sira").eq("tip",tip).order("sira").execute()
                    if not r.data: return
                    _goruldu = set()
                    _silinecek = []
                    for d in r.data:
                        v = str(d["deger"] or "").strip()
                        if v in _goruldu:
                            _silinecek.append(d["id"])
                        else:
                            _goruldu.add(v)
                    for _sid in _silinecek:
                        _sb_tan.table("sistem_tanimlar").delete().eq("id",_sid).execute()
                    return len(_silinecek)
            except: return 0

        _ta1, _ta2 = st.columns(2)

        # AŞAMA
        with _ta1:
            st.markdown("**🔄 Aşama Yönetimi**")
            _asama_listesi = _tan_liste("asama")
            _asama_unique = list(dict.fromkeys(_asama_listesi))
            if len(_asama_unique) < len(_asama_listesi):
                st.warning(f"⚠️ {len(_asama_listesi) - len(_asama_unique)} tekrar var!")
                if st.button("🧹 Tekrarları Temizle", key="asama_temizle", type="primary"):
                    _silinen = _tan_temizle("asama")
                    st.success(f"✅ {_silinen} tekrar silindi!"); st.rerun()
            _ea1, _ea2 = st.columns([3,1])
            _yeni_asama = _ea1.text_input("", placeholder="Yeni aşama adı...", key="kul_yeni_asama", label_visibility="collapsed")
            if _ea2.button("➕ Ekle", key="kul_asama_ekle", use_container_width=True):
                if _yeni_asama.strip():
                    if _yeni_asama.strip() in _asama_unique:
                        st.warning("Bu aşama zaten var!")
                    elif _tan_ekle("asama", _yeni_asama.strip()):
                        st.success(f"✅ '{_yeni_asama}' eklendi!"); st.rerun()
            st.caption(f"{len(_asama_unique)} aşama")
            for _ai, _a in enumerate(_asama_unique):
                _ac1, _ac2 = st.columns([4,1])
                _ac1.markdown(f"🔸 **{_a}**")
                if _ac2.button("🗑", key=f"asil_{_ai}_{_a[:8]}", use_container_width=True, help="Sil"):
                    if _tan_sil("asama", _a):
                        st.success(f"'{_a}' silindi!"); st.rerun()

        # DURUM
        with _ta2:
            st.markdown("**📊 Durum Yönetimi**")
            _durum_listesi = _tan_liste("durum")
            # Duplicate temizle butonu
            _durum_unique = list(dict.fromkeys(_durum_listesi))
            if len(_durum_unique) < len(_durum_listesi):
                st.warning(f"⚠️ {len(_durum_listesi) - len(_durum_unique)} tekrar var!")
                if st.button("🧹 Tekrarları Temizle", key="durum_temizle", type="primary"):
                    _silinen = _tan_temizle("durum")
                    st.success(f"✅ {_silinen} tekrar silindi!"); st.rerun()
            _ed1, _ed2 = st.columns([3,1])
            _yeni_durum = _ed1.text_input("", placeholder="Yeni durum adı...", key="kul_yeni_durum", label_visibility="collapsed")
            if _ed2.button("➕ Ekle", key="kul_durum_ekle", use_container_width=True):
                if _yeni_durum.strip():
                    if _yeni_durum.strip() in _durum_listesi:
                        st.warning("Bu durum zaten var!")
                    elif _tan_ekle("durum", _yeni_durum.strip()):
                        st.success(f"✅ '{_yeni_durum}' eklendi!"); st.rerun()
            st.caption(f"{len(_durum_unique)} durum")
            for _di, _d in enumerate(_durum_listesi):
                _dc1, _dc2 = st.columns([4,1])
                _dc1.markdown(f"🔹 **{_d}**")
                if _dc2.button("🗑", key=f"dsil2_{_di}_{_d[:8]}", use_container_width=True, help="Sil"):
                    if _tan_sil("durum", _d):
                        st.success(f"'{_d}' silindi!"); st.rerun()

    with kul_tab_font:
        st.markdown("### 🔤 Sözleşme PDF Fontları")
        st.caption("Sözleşme PDF'lerinin Türkçe karakterleri (ş, ğ, ı, ç, ö, ü, İ) doğru basabilmesi için gereken "
                   "font dosyaları. Başka bir bilgisayarda kuruluma ihtiyaç olursa buradan indirilebilir; "
                   "`fonts/` klasörüne konup GitHub'a yüklenmesi gerekir.")
        import os as _fnt_os
        _fnt_dir = None
        for _aday in ["fonts", "./fonts", "/mount/src/mwcrmpro/fonts"]:
            if _fnt_os.path.isdir(_aday):
                _fnt_dir = _aday; break
        if not _fnt_dir:
            st.warning("⚠️ Sunucuda `fonts/` klasörü henüz yok — önce font dosyalarını repo'ya eklemeniz gerekiyor.")
        else:
            _fnt1, _fnt2 = st.columns(2)
            _fnt_normal = _fnt_os.path.join(_fnt_dir, "DejaVuSans.ttf")
            _fnt_bold   = _fnt_os.path.join(_fnt_dir, "DejaVuSans-Bold.ttf")
            if _fnt_os.path.isfile(_fnt_normal):
                with open(_fnt_normal, "rb") as _f:
                    _fnt1.download_button("⬇️ DejaVuSans.ttf indir", data=_f.read(),
                        file_name="DejaVuSans.ttf", mime="font/ttf", use_container_width=True, key="fnt_dl_normal")
            else:
                _fnt1.warning("DejaVuSans.ttf bulunamadı")
            if _fnt_os.path.isfile(_fnt_bold):
                with open(_fnt_bold, "rb") as _f:
                    _fnt2.download_button("⬇️ DejaVuSans-Bold.ttf indir", data=_f.read(),
                        file_name="DejaVuSans-Bold.ttf", mime="font/ttf", use_container_width=True, key="fnt_dl_bold")
            else:
                _fnt2.warning("DejaVuSans-Bold.ttf bulunamadı")

    with kul_tab_kural:
        st.markdown("### 🔧 Bağlantısız Teklif Onarımı")
        st.caption("Eskiden bazı teklifler hiçbir cari karta bağlanmadan (musteri_id=0) kaydediliyordu — bu yüzden Cari Liste'deki '🧾 Teklif' rozetinde hiç görünmüyorlardı. Bu araç, teklif üzerindeki müşteri adını cari kartlardaki firma adıyla eşleştirip düzeltir.")
        if st.button("🔍 Bağlantısız Teklifleri Tara", key="kural_teklif_tara"):
            _tor_sb = get_sb_client()
            if _tor_sb:
                with st.spinner("Taranıyor..."):
                    _tor_tek = _tor_sb.table("teklifler").select("id,musteri_id,musteri_adi").execute().data or []
                    _tor_cari = _tor_sb.table("cari_kartlar").select("id,firma").execute().data or []
                _tor_bagsiz = [t for t in _tor_tek if not t.get("musteri_id")]
                _tor_firma_map = {str(c.get("firma","")).strip().lower(): c.get("id") for c in _tor_cari if c.get("firma")}
                _tor_eslesen = []
                for _t in _tor_bagsiz:
                    _ad = str(_t.get("musteri_adi","")).strip().lower()
                    _bulunan_id = _tor_firma_map.get(_ad)
                    if _bulunan_id:
                        _tor_eslesen.append({"teklif_id": _t["id"], "musteri_adi": _t.get("musteri_adi",""), "bulunan_cari_id": _bulunan_id})
                st.session_state["_tor_eslesen"] = _tor_eslesen
                st.session_state["_tor_bagsiz_sayi"] = len(_tor_bagsiz)
        if "_tor_eslesen" in st.session_state:
            _tor_e = st.session_state["_tor_eslesen"]
            st.info(f"Toplam {st.session_state.get('_tor_bagsiz_sayi',0)} bağlantısız teklif bulundu, {len(_tor_e)} tanesi isimden otomatik eşleşti.")
            if _tor_e:
                st.dataframe(pd.DataFrame(_tor_e), use_container_width=True, hide_index=True)
                if st.button(f"✅ {len(_tor_e)} teklifi düzelt", type="primary", key="kural_teklif_onar"):
                    _tor_sb2 = get_sb_client()
                    _tor_ok = 0
                    for _e in _tor_e:
                        try:
                            _tor_sb2.table("teklifler").update({"musteri_id": _e["bulunan_cari_id"]}).eq("id", _e["teklif_id"]).execute()
                            _tor_ok += 1
                        except Exception:
                            pass
                    st.success(f"✅ {_tor_ok} teklif düzeltildi. Cari Liste'yi yenileyince rozetlerde görünecek.")
                    st.session_state.pop("_tor_eslesen", None)
                    st.session_state.pop("_tor_bagsiz_sayi", None)
        st.divider()
        st.markdown("### 📌 Proje Kuralları & Bilgileri")
        if not st.session_state.get("kurallar_pin_dogru", False):
            st.caption("Bu alanda hassas bilgiler var (Supabase anahtarı vb.) — devam etmek için PIN girin.")
            _kp1, _kp2 = st.columns([2,1])
            _kural_pin_giris = _kp1.text_input("PIN:", type="password", key="kurallar_pin_input", label_visibility="collapsed", placeholder="PIN girin")
            if _kp2.button("🔓 Aç", key="kurallar_pin_btn", use_container_width=True):
                if _kural_pin_giris == KURALLAR_PIN:
                    st.session_state["kurallar_pin_dogru"] = True
                    st.rerun()
                else:
                    st.error("❌ PIN hatalı!")
        else:
            st.caption("Bu kurallar Claude ile yeni bir sohbet başlatıldığında main.py'nin en üstünden otomatik okunur — kodla birebir aynıdır. Sadece admin görür.")
            st.markdown(PROJE_KURALLARI)
            if st.button("🔒 Kilitle", key="kurallar_kilitle_btn"):
                st.session_state["kurallar_pin_dogru"] = False
                st.rerun()

elif aktif == "excel":
    sayfa_log("excel")
    import io

    st.markdown("## 📥 Excel ile Toplu Veri Aktarımı")

    sablon_kolonlar = ["firma","yetkili","gsm","sabit","email","adres","ilce","il","durum","temsilci","islem_asamasi","beklenen_ciro","gerceklesen_ciro",
                       "vergi_no","vergi_dairesi","musteri_subesi","vade","odeme","teklif_fiyat","islem_tarihi_manuel","takip_tarihi_manuel"]

    sablon_buf = io.BytesIO()
    pd.DataFrame(columns=sablon_kolonlar).to_excel(sablon_buf, index=False)
    sablon_buf.seek(0)
    st.download_button("📥 Şablonu İndir", data=sablon_buf, file_name="cari_sablon.xlsx", key="dl_sablon")

    st.divider()

    yukl_dosya = st.file_uploader("Excel dosyası yükle", type=["xlsx","xls"], key="excel_yukle")

    if yukl_dosya is not None:
        df_yukl = pd.read_excel(yukl_dosya)
        df_yukl.columns = [str(c).strip().lower().replace(" ","_") for c in df_yukl.columns]
    else:
        df_yukl = None

    if df_yukl is not None:

        # Hedef/Gerçek ciro sütunları farklı isimlerle gelebilir — hepsini "beklenen_ciro" /
        # "gerceklesen_ciro" olarak tanı, ilk eşleşen sütunu kullan (sessizce 0 atmasın diye).
        _hedef_takma_adlar = ["beklenen_ciro","hedef","hedef_ciro","hedef_₺","hedefciro",
                               "hedef_tl","target","hedef_tutar"]
        _gercek_takma_adlar = ["gerceklesen_ciro","gerçekleşen_ciro","gerçek","gercek",
                                "gerçek_ciro","gercek_ciro","gerçek_₺","gerceklesen"]
        for _hedef_ad in _hedef_takma_adlar:
            if _hedef_ad in df_yukl.columns:
                if _hedef_ad != "beklenen_ciro":
                    df_yukl["beklenen_ciro"] = df_yukl[_hedef_ad]
                break
        for _gercek_ad in _gercek_takma_adlar:
            if _gercek_ad in df_yukl.columns:
                if _gercek_ad != "gerceklesen_ciro":
                    df_yukl["gerceklesen_ciro"] = df_yukl[_gercek_ad]
                break

        if "firma" not in df_yukl.columns:
            st.error("❌ Zorunlu sütun eksik: firma")
        else:
            if "beklenen_ciro" not in df_yukl.columns:
                st.warning("⚠️ Hedef ciro sütunu bulunamadı — dosyanızdaki sütun başlığını "
                           f"şunlardan biri yapın: {', '.join(_hedef_takma_adlar)}. "
                           "Bulunamazsa tüm satırlar 0 ₺ hedef ile eklenir.")
            st.success(f"{len(df_yukl)} satır okundu.")

            def _ex_temiz_str(v):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return ""
                return str(v)

            def _ex_temiz_tel(v):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return ""
                s = str(v).strip()
                if s.endswith(".0"):
                    s = s[:-2]
                return s

            def _ex_temiz_float(v):
                try:
                    if v is None or (isinstance(v, float) and pd.isna(v)):
                        return 0.0
                    return float(v)
                except:
                    return 0.0

            # ── ID ALMADAN ÖNCE MÜKERRER TESPİTİ ──────────────────────────────
            # Her müşterinin ID'si kalıcıdır, asla değişmez — bu yüzden sisteme
            # ID vererek eklemeden önce, firma adı VEYA telefon numarası
            # hâlihazırda var mı diye bakılır (ikisinden biri eşleşirse şüpheli
            # mükerrer sayılır, onaylanmadan sisteme eklenmez).
            _ex_mevcut_df = get_cari_listesi()
            _ex_mevcut_isimler = {}
            _ex_mevcut_telefonlar = {}

            def _ex_tel_norm(_v):
                _s = str(_v or "").strip()
                _s = "".join(ch for ch in _s if ch.isdigit())
                if _s.endswith(".0"):  # ihtimale karşı, zaten yukarıda digit filtrelendi ama garanti olsun
                    _s = _s[:-2]
                # Baştaki 0/90 farklarını yok say — son 10 haneyi karşılaştır
                return _s[-10:] if len(_s) >= 10 else _s

            if not _ex_mevcut_df.empty and "firma" in _ex_mevcut_df.columns:
                for _, _mr in _ex_mevcut_df.iterrows():
                    _ex_ad = str(_mr.get("firma","")).strip().upper()
                    if _ex_ad:
                        _ex_mevcut_isimler.setdefault(_ex_ad, []).append(_mr.to_dict())
                    for _tel_kol in ["gsm", "sabit"]:
                        _ex_tel_n = _ex_tel_norm(_mr.get(_tel_kol, ""))
                        if _ex_tel_n:
                            _ex_mevcut_telefonlar.setdefault(_ex_tel_n, []).append(_mr.to_dict())

            _ex_temiz_kayitlar = []
            _ex_taslak_kayitlar = []
            _ex_dosya_icinde_gorulen = set()
            _ex_dosya_icinde_telefon = set()

            for _ei, _row in df_yukl.iterrows():
                _ex_firma = str(_row.get("firma","") or "").strip()
                if not _ex_firma:
                    continue
                _ex_kayit = {
                    "firma": _ex_firma,
                    "yetkili": _ex_temiz_str(_row.get("yetkili","")),
                    "gsm": _ex_temiz_tel(_row.get("gsm","")),
                    "sabit": _ex_temiz_tel(_row.get("sabit","")),
                    "email": _ex_temiz_str(_row.get("email","")),
                    "adres": _ex_temiz_str(_row.get("adres","")),
                    "ilce": _ex_temiz_str(_row.get("ilce","")),
                    "il": _ex_temiz_str(_row.get("il","")),
                    "durum": _ex_temiz_str(_row.get("durum","Hedef")) or "Hedef",
                    "temsilci": _ex_temiz_str(_row.get("temsilci","")),
                    "islem_asamasi": _ex_temiz_str(_row.get("islem_asamasi","")) or "",
                    "beklenen_ciro": _ex_temiz_float(_row.get("beklenen_ciro",0)),
                    "gerceklesen_ciro": _ex_temiz_float(_row.get("gerceklesen_ciro",0)),
                    "olusturan": st.session_state.get("kullanici",""),
                    "silindi": 0,
                }
                # KULLANICI İSTEĞİ (2026-09): Vergi No / Vergi Dairesi / Müşteri
                # Şubesi / Vade / Ödeme — cari_kartlar'da GERÇEK sütun DEĞİL,
                # bu yüzden INSERT payload'ına eklenmez; ayrı bir alt sözlükte
                # geçici olarak taşınıp INSERT'ten SONRA (yeni id belli
                # olunca) _cari_ek_bilgi_kaydet ile kaydedilir.
                _ex_ek_bilgi_gecici = {}
                for _ex_ek_alan in _CARI_EK_ALAN_LISTESI:
                    _ex_ek_v = _ex_temiz_str(_row.get(_ex_ek_alan, ""))
                    if _ex_ek_v:
                        _ex_ek_bilgi_gecici[_ex_ek_alan] = _ex_ek_v
                _ex_kayit["_ek_bilgi"] = _ex_ek_bilgi_gecici
                _ex_ad_norm = _ex_firma.upper()
                _ex_gsm_norm = _ex_tel_norm(_ex_kayit["gsm"])
                _ex_sabit_norm = _ex_tel_norm(_ex_kayit["sabit"])

                if _ex_ad_norm in _ex_mevcut_isimler:
                    _ex_taslak_kayitlar.append({**_ex_kayit, "_sebep": "Firma adı sistemde zaten var",
                                                 "_eslesen": _ex_mevcut_isimler[_ex_ad_norm]})
                elif _ex_gsm_norm and _ex_gsm_norm in _ex_mevcut_telefonlar:
                    _ex_taslak_kayitlar.append({**_ex_kayit, "_sebep": "Telefon (GSM) numarası sistemde başka bir firmada kayıtlı",
                                                 "_eslesen": _ex_mevcut_telefonlar[_ex_gsm_norm]})
                elif _ex_sabit_norm and _ex_sabit_norm in _ex_mevcut_telefonlar:
                    _ex_taslak_kayitlar.append({**_ex_kayit, "_sebep": "Sabit telefon numarası sistemde başka bir firmada kayıtlı",
                                                 "_eslesen": _ex_mevcut_telefonlar[_ex_sabit_norm]})
                elif _ex_ad_norm in _ex_dosya_icinde_gorulen:
                    _ex_taslak_kayitlar.append({**_ex_kayit, "_sebep": "Excel dosyasında tekrar ediyor",
                                                 "_eslesen": []})
                elif _ex_gsm_norm and _ex_gsm_norm in _ex_dosya_icinde_telefon:
                    _ex_taslak_kayitlar.append({**_ex_kayit, "_sebep": "Excel dosyasında aynı telefon başka satırda da var",
                                                 "_eslesen": []})
                else:
                    _ex_dosya_icinde_gorulen.add(_ex_ad_norm)
                    if _ex_gsm_norm: _ex_dosya_icinde_telefon.add(_ex_gsm_norm)
                    _ex_temiz_kayitlar.append(_ex_kayit)

            _ex_c1, _ex_c2 = st.columns(2)
            _ex_c1.metric("✅ Temiz (yeni) kayıt", len(_ex_temiz_kayitlar))
            _ex_c2.metric("⚠️ Şüpheli mükerrer (taslakta bekliyor)", len(_ex_taslak_kayitlar))

            if st.button("✅ Temiz Olanları Sisteme Aktar", type="primary", key="excel_aktar_btn_v2"):
                sb = get_sb_client()
                if not sb:
                    st.error("Supabase bağlantısı yok!")
                elif not _ex_temiz_kayitlar:
                    st.info("Aktarılacak temiz (yeni) kayıt yok.")
                else:
                    kayitlar = _ex_temiz_kayitlar

                    toplam = len(kayitlar)
                    basarili = 0
                    hatalar = []
                    BATCH = 25
                    bar = st.progress(0)
                    durum_text = st.empty()
                    _ex_ek_bilgi_toplu = {}

                    for i in range(0, toplam, BATCH):
                        parca = kayitlar[i:i+BATCH]
                        # Vergi No/Dairesi/Şube/Vade/Ödeme, cari_kartlar'a GERÇEK
                        # sütun olmadığı için INSERT payload'ından çıkarılır —
                        # sadece bu parçadaki (satır sırasına göre) geçici
                        # listede tutulur, aşağıda yeni id'lerle eşleştirilir.
                        _parca_ek_bilgiler = [p.pop("_ek_bilgi", {}) for p in parca]
                        try:
                            _res_ex_ins = sb.table("cari_kartlar").insert(parca).execute()
                            basarili += len(parca)
                            # Dönen kayıtların id'leri, gönderilen sırayla eşleşir
                            # (Supabase/PostgREST tek bir INSERT çağrısında sırayı korur).
                            for _yeni_satir, _ek_bilgi_bu in zip(_res_ex_ins.data or [], _parca_ek_bilgiler):
                                if _ek_bilgi_bu and _yeni_satir.get("id"):
                                    _ex_ek_bilgi_toplu[str(_yeni_satir["id"])] = _ek_bilgi_bu
                        except Exception as e:
                            hatalar.append(f"Satır {i+1}-{i+len(parca)}: {e}")
                        bar.progress(min((i+BATCH)/toplam, 1.0))
                        durum_text.text(f"{min(i+BATCH,toplam)}/{toplam} işlendi, {basarili} eklendi")

                    if _ex_ek_bilgi_toplu:
                        _ex_ek_bilgi_mevcut = _cari_ek_bilgi_yukle()
                        _ex_ek_bilgi_mevcut.update(_ex_ek_bilgi_toplu)
                        _cari_ek_bilgi_kaydet(_ex_ek_bilgi_mevcut)

                    st.success(f"🎉 Tamamlandı! {basarili}/{toplam} kayıt eklendi.")
                    if hatalar:
                        st.error(f"❌ {len(hatalar)} grup hata verdi:")
                        for h in hatalar:
                            st.code(h)

            # ── TASLAK: Şüpheli Mükerrer Kayıtlar — henüz sisteme ID almadılar ──
            if "_ex_tas_gecilen" not in st.session_state:
                st.session_state["_ex_tas_gecilen"] = set()
            _ex_taslak_kayitlar = [tk for _ti0, tk in enumerate(_ex_taslak_kayitlar)
                                    if f"{tk['firma']}_{_ti0}" not in st.session_state["_ex_tas_gecilen"]]
            if _ex_taslak_kayitlar:
                st.divider()
                st.warning(f"⚠️ {len(_ex_taslak_kayitlar)} kayıt taslakta bekliyor — bunlara henüz ID verilmedi, sisteme eklenmedi. "
                           "Aşağıda mevcut kayıtla karşılaştırıp siz karar verin: aynen ekleyin, düzenleyip ekleyin, ya da vazgeçin.")

                # ── Şüpheli mükerrer karşılaştırma listesini Excel olarak indir ──
                _ex_indir_satirlar = []
                for _tk_i in _ex_taslak_kayitlar:
                    _es_i = _tk_i["_eslesen"][0] if _tk_i["_eslesen"] else {}
                    _ex_indir_satirlar.append({
                        "Sebep": _tk_i.get("_sebep", ""),
                        "Excel - Firma": _tk_i.get("firma", ""),
                        "Excel - Yetkili": _tk_i.get("yetkili", ""),
                        "Excel - GSM": _tk_i.get("gsm", ""),
                        "Excel - Sabit": _tk_i.get("sabit", ""),
                        "Excel - İl": _tk_i.get("il", ""),
                        "Excel - İlçe": _tk_i.get("ilce", ""),
                        "Excel - Hedef Ciro": _tk_i.get("beklenen_ciro", 0),
                        "Sistem - ID": _es_i.get("id", ""),
                        "Sistem - Firma": _es_i.get("firma", ""),
                        "Sistem - Yetkili": _es_i.get("yetkili", ""),
                        "Sistem - GSM": _es_i.get("gsm", ""),
                        "Sistem - Sabit": _es_i.get("sabit", ""),
                        "Sistem - İl": _es_i.get("il", ""),
                        "Sistem - İlçe": _es_i.get("ilce", ""),
                        "Sistem - Hedef Ciro": _es_i.get("beklenen_ciro", 0),
                    })
                _ex_indir_buf = io.BytesIO()
                pd.DataFrame(_ex_indir_satirlar).to_excel(_ex_indir_buf, index=False, engine="openpyxl")
                _ex_indir_buf.seek(0)
                st.download_button("📥 Şüpheli Mükerrer Listesini Excel Olarak İndir", data=_ex_indir_buf,
                                    file_name=f"mukerrer_karsilastirma_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="ex_tas_excel_indir")

                with st.expander(f"🔍 Taslaktaki {len(_ex_taslak_kayitlar)} şüpheli kaydı incele", expanded=True):
                    for _ti, _tk in enumerate(_ex_taslak_kayitlar):
                        _ex_tas_anahtar = f"{_tk['firma']}_{_ti}"
                        st.markdown(f"**{_tk['firma']}** — *{_tk['_sebep']}*")
                        _tc1, _tc2 = st.columns(2)
                        with _tc1:
                            st.caption("📄 Excel'den gelen (henüz ID yok)")
                            st.text(f"Yetkili: {_tk.get('yetkili','—')}\n"
                                    f"GSM: {_tk.get('gsm','—')}\n"
                                    f"İl/İlçe: {_tk.get('il','—')} / {_tk.get('ilce','—')}\n"
                                    f"Hedef ciro: {_tk.get('beklenen_ciro',0):,.0f} ₺")
                        with _tc2:
                            if _tk["_eslesen"]:
                                _es = _tk["_eslesen"][0]
                                st.caption(f"💾 Sistemde kayıtlı (id {_es.get('id')})")
                                st.text(f"Yetkili: {_es.get('yetkili') or '—'}\n"
                                        f"GSM: {_es.get('gsm') or '—'}\n"
                                        f"İl/İlçe: {_es.get('il') or '—'} / {_es.get('ilce') or '—'}\n"
                                        f"Hedef ciro: {float(_es.get('beklenen_ciro') or 0):,.0f} ₺")
                            else:
                                st.caption("💾 Excel dosyasının kendi içinde tekrar ediyor")

                        _ex_duzenle_flag_key = f"_ex_tas_duzenle_acik_{_ex_tas_anahtar}"
                        _tb1, _tb2, _tb3 = st.columns(3)
                        with _tb1:
                            if st.button("✅ Aynen Ekle", key=f"ex_tas_ekle_{_ex_tas_anahtar}", use_container_width=True):
                                _sb_tas = get_sb_client()
                                if _sb_tas:
                                    try:
                                        _tk_temiz = {k: v for k, v in _tk.items() if not k.startswith("_")}
                                        _sb_tas.table("cari_kartlar").insert(_tk_temiz).execute()
                                        try: get_cari_listesi.clear()
                                        except: pass
                                        st.toast(f"✅ '{_tk['firma']}' yeni kayıt olarak eklendi (yeni ID verildi)", icon="✅")
                                        st.rerun()
                                    except Exception as _tase:
                                        st.error(f"Hata: {_tase}")
                        with _tb2:
                            if st.button("✏️ Düzenle", key=f"ex_tas_duzenle_btn_{_ex_tas_anahtar}", use_container_width=True):
                                st.session_state[_ex_duzenle_flag_key] = not st.session_state.get(_ex_duzenle_flag_key, False)
                                st.rerun()
                        with _tb3:
                            if st.button("❌ Vazgeç (atla)", key=f"ex_tas_vazgec_{_ex_tas_anahtar}", use_container_width=True):
                                st.session_state["_ex_tas_gecilen"].add(_ex_tas_anahtar)
                                st.toast(f"❌ '{_tk['firma']}' atlandı — bir daha bu incelemede görünmeyecek", icon="❌")
                                st.rerun()

                        if st.session_state.get(_ex_duzenle_flag_key, False):
                            with st.form(key=f"ex_tas_duzenle_form_{_ex_tas_anahtar}"):
                                st.caption("Kaydetmeden önce alanları düzenleyebilirsin:")
                                _dc1, _dc2 = st.columns(2)
                                _dz_firma = _dc1.text_input("Firma", value=_tk.get("firma",""))
                                _dz_yetkili = _dc2.text_input("Yetkili", value=_tk.get("yetkili",""))
                                _dz_gsm = _dc1.text_input("GSM", value=_tk.get("gsm",""))
                                _dz_sabit = _dc2.text_input("Sabit", value=_tk.get("sabit",""))
                                _dz_email = _dc1.text_input("Email", value=_tk.get("email",""))
                                _dz_adres = _dc2.text_input("Adres", value=_tk.get("adres",""))
                                _dz_il = _dc1.text_input("İl", value=_tk.get("il",""))
                                _dz_ilce = _dc2.text_input("İlçe", value=_tk.get("ilce",""))
                                _dz_hedef = _dc1.number_input("Hedef ciro", value=float(_tk.get("beklenen_ciro",0) or 0))
                                if st.form_submit_button("💾 Düzenlediğimi Kaydet ve Ekle", type="primary"):
                                    _sb_tas2 = get_sb_client()
                                    if _sb_tas2:
                                        try:
                                            _tk_duzenlenmis = {k: v for k, v in _tk.items() if not k.startswith("_")}
                                            _tk_duzenlenmis.update({
                                                "firma": _dz_firma, "yetkili": _dz_yetkili, "gsm": _dz_gsm,
                                                "sabit": _dz_sabit, "email": _dz_email, "adres": _dz_adres,
                                                "il": _dz_il, "ilce": _dz_ilce, "beklenen_ciro": _dz_hedef,
                                            })
                                            _sb_tas2.table("cari_kartlar").insert(_tk_duzenlenmis).execute()
                                            try: get_cari_listesi.clear()
                                            except: pass
                                            st.session_state["_ex_tas_gecilen"].add(_ex_tas_anahtar)
                                            st.toast(f"✅ '{_dz_firma}' düzenlenmiş haliyle eklendi (yeni ID verildi)", icon="✅")
                                            st.rerun()
                                        except Exception as _tase2:
                                            st.error(f"Hata: {_tase2}")
                        else:
                            st.caption("Hiçbir şey yapmazsanız bu kayıt sisteme eklenmez, taslakta kalır.")
                        st.markdown("---")


elif aktif == "kargolar":
    sayfa_log("kargolar")
    st.markdown("## 🚚 Kargolar — Tüm Müşteriler")
    st.caption("Tüm müşterilerin kargo giriş kayıtları burada birleşik olarak görünür. "
               "'Seç' işaretleyip düzenleyebilir veya silebilirsin.")

    @st.cache_data(ttl=30, show_spinner=False)
    def _kargolar_tumunu_yukle():
        try:
            _sb_kt = get_sb_client()
            if not _sb_kt:
                return []
            # NOT: Supabase/PostgREST tek sorguda varsayılan olarak en fazla 1000
            # satır döner. 1000'den fazla müşterinin kargo kaydı olduğunda önceki
            # kod bunun bir kısmını sessizce KAÇIRIYORDU (Excel'den doğru yüklenmiş
            # olsa bile Kargolar listesinde eksik görünüyordu). Burada 1000'lik
            # bloklar halinde TÜMÜ bitene kadar çekiliyor — sınırsız.
            _tum_satirlar_kt = []
            _offset_kt = 0
            while True:
                _r_kt = _sb_kt.table("kullanici_tercih").select("anahtar,deger").eq(
                    "kullanici", "__liste_ui__").like("anahtar", "_kargo_kayitlari_%").range(
                    _offset_kt, _offset_kt + 999).execute()
                _batch_kt = _r_kt.data or []
                _tum_satirlar_kt.extend(_batch_kt)
                if len(_batch_kt) < 1000:
                    break
                _offset_kt += 1000
            import json as _ktj
            _tum_kayitlar = []
            for _row in _tum_satirlar_kt:
                try:
                    _cid = int(str(_row["anahtar"]).replace("_kargo_kayitlari_", ""))
                except Exception:
                    continue
                try:
                    _liste = _ktj.loads(_row["deger"])
                except Exception:
                    _liste = []
                for _i, _kayit in enumerate(_liste):
                    _kayit_kopya = dict(_kayit)
                    _kayit_kopya["_cari_id"] = _cid
                    _kayit_kopya["_satir_no"] = _i
                    _tum_kayitlar.append(_kayit_kopya)
            return _tum_kayitlar
        except Exception:
            return []

    def _kargolar_yaz(_cari_id, _yeni_liste_o_musteri):
        """GÜVENLİ (2026-09) — bkz. _tedarikci_kaydet ile aynı gerekçe. SİLME
        YOK: satır zaten varsa doğrudan UPDATE edilir, yoksa INSERT edilir.
        Eski 'önce sil sonra ekle' sırası, 'Değişiklikleri Kaydet' her
        tıklandığında etkilenen HER müşteri için ayrı ayrı çalıştığından,
        aralarından biri ağ kopmasına denk gelirse o müşterinin TÜM kargo
        geçmişi sıfırlanabiliyordu — kullanıcının bildirdiği 'kayıtlar
        kendiliğinden siliniyor' sorununun kök nedeni buydu."""
        try:
            _sb_kt2 = get_sb_client()
            if not _sb_kt2:
                return False
            import json as _ktj2
            _anahtar = f"_kargo_kayitlari_{int(_cari_id)}"
            _deger = _ktj2.dumps(_yeni_liste_o_musteri, ensure_ascii=False)
            _guncelle_sonuc = _sb_kt2.table("kullanici_tercih").update({"deger": _deger}).eq(
                "kullanici", "__liste_ui__").eq("anahtar", _anahtar).execute()
            if not _guncelle_sonuc.data:
                _sb_kt2.table("kullanici_tercih").insert(
                    {"kullanici": "__liste_ui__", "anahtar": _anahtar, "deger": _deger}
                ).execute()
            # Kargo değişti — Cari Liste'deki "Gerçekleşen Ciro" önbelleğini
            # (performans için 5 dk'lık) hemen geçersiz kıl.
            try: _tum_musteri_kargo_yekun_toplami.clear()
            except Exception: pass
            return True
        except Exception:
            return False

    if "_kargo_kol_genislik" not in st.session_state:
        try:
            _sb_kkg0 = get_sb_client()
            if _sb_kkg0:
                _r_kkg0 = _sb_kkg0.table("kullanici_tercih").select("deger").eq("kullanici","__liste_ui__").eq("anahtar","_kargo_kol_genislik").execute()
                if _r_kkg0.data:
                    import json as _kkgj0
                    st.session_state["_kargo_kol_genislik"] = _kkgj0.loads(_r_kkg0.data[0]["deger"])
        except Exception:
            pass

    _kl_tum_kayitlar_ham = _kargolar_tumunu_yukle()
    # GÜVENLİK: silinen kayıtlar (yumuşak silme) normal listede GÖRÜNMEZ ama
    # veri tabanından da silinmez — "🗑️ Silinenler" açıkken SADECE onlar
    # gösterilir, oradan geri alınabilir ya da kalıcı silinebilir.
    _kl_silinenler_aktif = st.session_state.get("_kargolar_silinenler_goster", False)
    if _kl_silinenler_aktif:
        _kl_tum_kayitlar = [_k for _k in _kl_tum_kayitlar_ham if _k.get("silindi")]
    else:
        _kl_tum_kayitlar = [_k for _k in _kl_tum_kayitlar_ham if not _k.get("silindi")]
    if not _kl_tum_kayitlar:
        if _kl_silinenler_aktif:
            st.info("💡 Silinmiş kargo kaydı yok.")
        else:
            st.info("💡 Henüz hiçbir müşteride kargo kaydı yok — ama filtreler ve Excel Yükle yine de aşağıda çalışır, "
                    "istersen doğrudan Excel'den toplu kayıt yükleyebilirsin.")
    # NOT: Önceden burada "else:" vardı ve liste boşken TÜM filtreler/Excel
    # Yükle/Genel Rapor da gizleniyordu — tam da geri yükleme yapman gereken
    # anda erişilemez oluyordu. Artık aşağıdaki blok HER ZAMAN çalışır.
    if True:
        try:
            _kl_musteri_map = dict(zip(get_cari_listesi()["id"], get_cari_listesi()["firma"]))
        except Exception:
            _kl_musteri_map = {}
        for _kk in _kl_tum_kayitlar:
            _kk["Müşteri"] = _kl_musteri_map.get(_kk.get("_cari_id"), f"(ID {_kk.get('_cari_id')})")

        _kl_df = pd.DataFrame(_kl_tum_kayitlar)
        # Liste boşsa (hiç kargo kaydı yoksa) beklenen tüm sütunları BOŞ olarak
        # ekle — yoksa aşağıdaki filtre/Excel/rapor kodları "sütun yok" hatası
        # verip çökerdi (tam da liste boşken erişilmesi gereken özellikler).
        _KL_BEKLENEN_KOLONLAR = ["tarih", "takip_no", "fatura_no", "gonderen_firma", "alici_firma", "fatura_firma", "yetkili",
                                  "gonderen_il", "alici_il", "adet", "tur", "tutar", "yekun", "sigorta", "ara_toplam", "kdv",
                                  "toplam_fatura", "odeme_tur", "tahsilat_durumu", "not", "dis_nakliye_firma",
                                  "dis_nakliye_fatura", "dis_nakliye_detay", "dis_nakliye_tutar",
                                  "musteri_tutar", "kar", "zarar", "dis_nakliye_odeme_durumu", "fatura_odeme_sekli",
                                  "desi", "kilo", "Müşteri", "_cari_id", "_satir_no"]
        for _kl_bk in _KL_BEKLENEN_KOLONLAR:
            if _kl_bk not in _kl_df.columns:
                _kl_df[_kl_bk] = pd.Series(dtype=object)
        _kl_df = _kl_df.fillna("")  # eski kayıtlarda olmayan alanlar "None" değil boş görünsün
        # Müşteri alfabetik, kendi içinde tarihe göre sırala
        _kl_df = _kl_df.sort_values(by=["Müşteri", "tarih"], kind="stable").reset_index(drop=True)

        # ── TÜM FİLTRELER TEK SATIRDA ──────────────────────────────────────────
        _kl_musteri_secenekler = ["-- Tüm Müşteriler --"] + sorted(_kl_musteri_map.values())
        _kl_gonderen_opts_ham = ["-- Tümü --"] + sorted([x for x in _kl_df["gonderen_firma"].dropna().unique().tolist() if str(x).strip()]) if "gonderen_firma" in _kl_df.columns else ["-- Tümü --"]
        _kl_alici_opts_ham = ["-- Tümü --"] + sorted([x for x in _kl_df["alici_firma"].dropna().unique().tolist() if str(x).strip()]) if "alici_firma" in _kl_df.columns else ["-- Tümü --"]
        _kl_fatura_opts_ham = ["-- Tümü --"] + sorted([x for x in _kl_df["fatura_firma"].dropna().unique().tolist() if str(x).strip()]) if "fatura_firma" in _kl_df.columns else ["-- Tümü --"]
        # Tedarikçi (Dış Nakliye Firma) filtresi — o an filtrede görünen
        # kayıtlarda GERÇEKTEN kullanılmış tedarikçilerle sınırlı (Gönderen/
        # Alıcı/Fatura Ödeyen filtreleriyle aynı mantık). "🚚 Hepsi" seçeneği
        # HANGİ tedarikçi olduğuna bakmaksızın Dış Nakliye Firma'sı DOLU olan
        # (yani dışarıya nakliyeye verilmiş) TÜM kayıtları birden gösterir —
        # "-- Tümü --" ise hiç filtre uygulamaz (boş olanlar dahil hepsi).
        _kl_tedarikci_gercek_opts = sorted([x for x in _kl_df["dis_nakliye_firma"].dropna().unique().tolist() if str(x).strip()]) if "dis_nakliye_firma" in _kl_df.columns else []
        _kl_tedarikci_opts_ham = ["-- Tümü --", "🚚 Hepsi (Dış Nakliyesi Olanlar)"] + _kl_tedarikci_gercek_opts

        _kl_fc1, _kl_fc3, _kl_fc4, _kl_fc4b, _kl_fc5, _kl_fc5b, _kl_fc5c, _kl_fc6, _kl_fc7, _kl_fc8, _kl_fc9 = st.columns(
            [1.5, 1.0, 1.0, 1.0, 1.0, 1.1, 1.0, 0.9, 1.0, 1.0, 1.0], vertical_alignment="bottom")
        _kl_secili_musteri_genel = _kl_fc1.selectbox("Genel Müşteri Seç (kargo girişi için)", _kl_musteri_secenekler, key="kargolar_musteri_filtre")
        _kl_sec_gonderen = _kl_fc3.selectbox("Gönderen", _kl_gonderen_opts_ham, key="kargolar_gonderen_filtre")
        _kl_sec_alici = _kl_fc4.selectbox("Alıcı", _kl_alici_opts_ham, key="kargolar_alici_filtre")
        # Alıcı İl seçenekleri, "Genel Müşteri Seç" ile bir müşteri seçiliyse
        # SADECE O MÜŞTERİNİN kayıtlarındaki illerle sınırlanır (cirosu olsun
        # olmasın, kayıt varsa il listede çıkar) — 81 ili arayıp durmasın diye.
        if _kl_secili_musteri_genel != "-- Tüm Müşteriler --":
            _kl_alici_il_kapsam = _kl_df[_kl_df["Müşteri"] == _kl_secili_musteri_genel]
        else:
            _kl_alici_il_kapsam = _kl_df
        _kl_alici_il_opts_ham = ["-- Tümü --"] + sorted([x for x in _kl_alici_il_kapsam["alici_il"].dropna().unique().tolist() if str(x).strip()]) if "alici_il" in _kl_alici_il_kapsam.columns else ["-- Tümü --"]
        _kl_sec_alici_il = _kl_fc4b.selectbox("Alıcı İl", _kl_alici_il_opts_ham, key="kargolar_alici_il_filtre")
        _kl_sec_fatura = _kl_fc5.selectbox("Fatura Ödeyen", _kl_fatura_opts_ham, key="kargolar_fatura_filtre")
        _KL_AY_ADLARI = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        _kl_ay_secenekleri_ham = set()
        if "tarih" in _kl_df.columns:
            for _kl_t in _kl_df["tarih"].dropna().astype(str):
                _kl_t = _kl_t.strip()
                if len(_kl_t) >= 7:
                    try:
                        _kl_yil_t, _kl_ay_t = _kl_t[:4], int(_kl_t[5:7])
                        if 1 <= _kl_ay_t <= 12:
                            _kl_ay_secenekleri_ham.add((_kl_yil_t, _kl_ay_t))
                    except Exception:
                        pass
        _kl_ay_secenekleri_sirali = sorted(_kl_ay_secenekleri_ham)
        _kl_ay_opts = ["-- Tümü --"] + [f"{_KL_AY_ADLARI[_ay - 1]} {_yil}" for _yil, _ay in _kl_ay_secenekleri_sirali]
        _kl_ay_haritasi = {f"{_KL_AY_ADLARI[_ay - 1]} {_yil}": (_yil, _ay) for _yil, _ay in _kl_ay_secenekleri_sirali}
        _kl_sec_ay = _kl_fc5b.selectbox("Ay", _kl_ay_opts, key="kargolar_ay_filtre")
        _kl_sec_tedarikci = _kl_fc5c.selectbox("Tedarikçi", _kl_tedarikci_opts_ham, key="kargolar_tedarikci_filtre")
        with _kl_fc6:
            if _kl_secili_musteri_genel != "-- Tüm Müşteriler --":
                _kl_sec_cari_id = None
                for _cid_ara, _fad_ara in _kl_musteri_map.items():
                    if _fad_ara == _kl_secili_musteri_genel:
                        _kl_sec_cari_id = _cid_ara
                        break
                if st.button("📦 Kargo Girişi", key="kargolar_giris_ac_btn", use_container_width=True, disabled=_kl_sec_cari_id is None):
                    not_dialog(_kl_sec_cari_id, _kl_secili_musteri_genel)
        # "Excel İndir" burada sadece bir yer tutucu (container) — gerçek indirme
        # verisi aşağıda (tüm filtreler uygulandıktan sonra) hazır olunca içine konur.
        _kl_excel_indir_kutu = _kl_fc7.container()
        with _kl_fc8:
            if st.button("📤 Excel Yükle", key="kargolar_excel_yukle_toggle_btn", use_container_width=True):
                st.session_state["_kargolar_excel_yukle_ac"] = not st.session_state.get("_kargolar_excel_yukle_ac", False)
        with _kl_fc9:
            if st.button("📊 Genel Rapor", key="kargolar_genel_rapor_toggle_btn", use_container_width=True):
                st.session_state["_kargolar_genel_rapor_ac"] = not st.session_state.get("_kargolar_genel_rapor_ac", False)

        # ── Filtreleri sırayla uygula
        if _kl_sec_gonderen != "-- Tümü --":
            _kl_df = _kl_df[_kl_df["gonderen_firma"] == _kl_sec_gonderen]
        if _kl_sec_alici != "-- Tümü --":
            _kl_df = _kl_df[_kl_df["alici_firma"] == _kl_sec_alici]
        if _kl_sec_alici_il != "-- Tümü --":
            _kl_df = _kl_df[_kl_df["alici_il"] == _kl_sec_alici_il]
        if _kl_sec_tedarikci == "🚚 Hepsi (Dış Nakliyesi Olanlar)":
            _kl_df = _kl_df[_kl_df["dis_nakliye_firma"].astype(str).str.strip() != ""]
        elif _kl_sec_tedarikci != "-- Tümü --":
            _kl_df = _kl_df[_kl_df["dis_nakliye_firma"] == _kl_sec_tedarikci]
        if _kl_sec_fatura != "-- Tümü --":
            _kl_df = _kl_df[_kl_df["fatura_firma"] == _kl_sec_fatura]
        if _kl_sec_ay != "-- Tümü --":
            _kl_hedef_yil, _kl_hedef_ay = _kl_ay_haritasi[_kl_sec_ay]
            _kl_df = _kl_df[_kl_df["tarih"].astype(str).str[:4] == _kl_hedef_yil]
            _kl_df = _kl_df[_kl_df["tarih"].astype(str).str[5:7] == f"{_kl_hedef_ay:02d}"]

        # ── ÖDEME EKSTRESİ — "Fatura Ödeyen Filtrele" ile bir firma seçilince,
        # o firmanın ödeme geçmişini/bakiyesini gösteren ayrı, indirilebilir ekstre.
        if _kl_sec_fatura != "-- Tümü --" and not _kl_df.empty:
            with st.expander(f"💳 Ödeme Ekstresi — {_kl_sec_fatura}", expanded=True):
                _ek_df = _kl_df.copy()
                _ek_df["_efektif_tutar"] = pd.to_numeric(_ek_df.get("toplam_fatura", 0), errors="coerce").fillna(0)
                _ek_tutar_num = pd.to_numeric(_ek_df.get("tutar", 0), errors="coerce").fillna(0)
                _ek_df.loc[_ek_df["_efektif_tutar"] == 0, "_efektif_tutar"] = _ek_tutar_num
                _ek_df["_tarih_dt"] = pd.to_datetime(_ek_df.get("tarih", ""), errors="coerce")
                _ek_df = _ek_df.sort_values("_tarih_dt")

                _ek_toplam_tutar = float(_ek_df["_efektif_tutar"].sum())
                _ek_tahsil = _ek_df[_ek_df.get("tahsilat_durumu", "") == "Tahsil Edildi"]
                _ek_tahsil_tutar = float(_ek_tahsil["_efektif_tutar"].sum())
                _ek_bakiye = _ek_toplam_tutar - _ek_tahsil_tutar

                _ekm1, _ekm2, _ekm3 = st.columns(3)
                _ekm1.metric("💰 Toplam Tutar", f"{_ek_toplam_tutar:,.0f} ₺")
                _ekm2.metric("✅ Tahsil Edilen", f"{_ek_tahsil_tutar:,.0f} ₺")
                _ekm3.metric("⏳ Bakiye (Kalan Borç)", f"{_ek_bakiye:,.0f} ₺")

                if not _ek_tahsil.empty:
                    _ek_son_odeme = _ek_tahsil.sort_values("_tarih_dt").iloc[-1]
                    st.caption(f"🕐 En son ödeme: **{_ek_son_odeme['_tarih_dt'].strftime('%Y-%m-%d') if pd.notna(_ek_son_odeme['_tarih_dt']) else '—'}** "
                               f"— {_ek_son_odeme['_efektif_tutar']:,.0f} ₺ ({_ek_son_odeme.get('alici_il','')})")
                else:
                    st.caption("🕐 Henüz tahsil edilmiş bir kayıt yok.")
                st.caption("💡 Not: Sistemde şu an bir 'vade/ödeme tarihi' alanı tutulmuyor, bu yüzden "
                           "'yaklaşan ödeme ne zaman' bilgisini gösteremiyoruz — istersen Kargo Girişi formuna bir 'Vade Tarihi' alanı ekleyebiliriz.")

                st.caption("📋 Bu firmadan/için gelen tüm kargolar (tarih sırasıyla):")
                _ek_goster = _ek_df[["_tarih_dt", "gonderen_il", "alici_il", "tur", "adet", "_efektif_tutar", "tahsilat_durumu"]].copy()
                _ek_goster.columns = ["Tarih", "Gönderen İl", "Alıcı İl", "Tür", "Adet", "Tutar", "Tahsilat"]
                _ek_goster["Tarih"] = _ek_goster["Tarih"].dt.strftime("%Y-%m-%d").fillna("—")
                st.dataframe(_ek_goster, use_container_width=True, hide_index=True,
                             height=min(38 * (len(_ek_goster) + 1) + 25, 500))

                # ── Excel ekstre — TEK sayfa, bölünmemiş ──
                _ek_excel_buf = io.BytesIO()
                _ek_goster.to_excel(_ek_excel_buf, index=False, engine="openpyxl")
                _ek_excel_buf.seek(0)
                st.download_button("📥 Ödeme Ekstresini Excel Olarak İndir", data=_ek_excel_buf,
                                    file_name=f"ekstre_{_kl_sec_fatura.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="kargolar_ekstre_excel_indir")

        # Panel/özet gösterimi hâlâ "genel müşteri seçimi"ne bağlı çalışıyor
        _kl_secili_musteri = _kl_secili_musteri_genel
        if _kl_secili_musteri != "-- Tüm Müşteriler --":
            _kl_df = _kl_df[_kl_df["Müşteri"] == _kl_secili_musteri]

        # ── MÜKERRER (BİREBİR AYNI) KAYIT TESPİTİ — aynı müşteride, tarih/
        # takip no/tutar/desi/kilo vb. TÜM alanları birebir aynı olan kayıtlar
        # (ör. Excel'den yanlışlıkla iki kez yüklenmiş olabilir). Toplam sayı
        # her zaman güncel filtreye göre hesaplanır; "🔁 Mükerrer" butonu
        # açıkken tabloda SADECE bunlar listelenir.
        _KL_MUKERRER_KARSILASTIRMA_KOLONLARI = [c for c in _KL_BEKLENEN_KOLONLAR if c not in ("Müşteri", "_cari_id", "_satir_no")]
        if len(_kl_df) > 0:
            _kl_df["_mukerrer_anahtar"] = list(zip(
                _kl_df["_cari_id"],
                *[_kl_df[c].astype(str) for c in _KL_MUKERRER_KARSILASTIRMA_KOLONLARI]
            ))
            _kl_mukerrer_sayilar = _kl_df["_mukerrer_anahtar"].value_counts()
            _kl_df["_mukerrer_mi"] = _kl_df["_mukerrer_anahtar"].map(lambda k: _kl_mukerrer_sayilar.get(k, 1) > 1)
            _kl_mukerrer_toplam = int(_kl_df["_mukerrer_mi"].sum())
        else:
            _kl_df["_mukerrer_mi"] = pd.Series(dtype=bool)
            _kl_mukerrer_toplam = 0
        if st.session_state.get("_kargolar_mukerrer_goster", False):
            _kl_df = _kl_df[_kl_df["_mukerrer_mi"] == True]
        _kl_df = _kl_df.drop(columns=[c for c in ["_mukerrer_anahtar", "_mukerrer_mi"] if c in _kl_df.columns])

        _kl_df.insert(0, "Seç", False)
        _kl_kolon_isim = {"Müşteri": "Müşteri", "tarih": "Tarih", "takip_no": "Takip No", "fatura_no": "Fatura No",
                           "gonderen_firma": "Gönderen", "alici_firma": "Alıcı", "fatura_firma": "Fatura Ödeyen", "yetkili": "Yetkili",
                           "gonderen_il": "Gönderen İl", "alici_il": "Alıcı İl", "tur": "Tür", "desi": "Desi", "kilo": "Kilo", "adet": "Adet",
                           "fatura_odeme_sekli": "Fatura Ödeme Şekli", "tutar": "B.Tutar", "yekun": "Yekün", "sigorta": "Sigorta %6", "ara_toplam": "Ara Toplam",
                           "kdv": "Kdv %20", "toplam_fatura": "Son Toplam", "odeme_tur": "Ödeme Türü", "tahsilat_durumu": "Tahsilat", "not": "Not",
                           "dis_nakliye_firma": "Dış Nakliye Firma", "dis_nakliye_fatura": "Dış Nakliye Fatura", "dis_nakliye_detay": "Dış Nakliye Detay",
                           "dis_nakliye_tutar": "Dış Nakliye Tutar", "musteri_tutar": "Müşteri Tutar", "kar": "Kar", "zarar": "Zarar",
                           "dis_nakliye_odeme_durumu": "Dış Nak. Ödeme"}
        if _kl_silinenler_aktif:
            _kl_kolon_isim["silinme_tarihi"] = "Silinme Tarihi"
        _kl_gorunur_kolonlar = ["Seç", "Müşteri"] + [c for c in _kl_kolon_isim if c in _kl_df.columns and c != "Müşteri"]
        _kl_df = _kl_df.reset_index(drop=True)  # filtrelerden sonra index'ler boşluklu kalmasın (iloc hatası önlenir)
        _kl_df_goster = _kl_df[_kl_gorunur_kolonlar + ["_cari_id", "_satir_no"]].rename(columns=_kl_kolon_isim)
        # Takip No / Fatura No PARASAL DEĞİL — geçmişte Excel'den sayı olarak
        # okunup '1910372.0' gibi gereksiz '.0' kuyruğuyla kaydedilmiş kayıtlar
        # burada temizlenip düz '1910372' gösterilir (kullanıcı isteği).
        # Kaydedince ya da Excel İndir'e basılınca bu temiz hâliyle kalıcı olur.
        for _kl_ref_kol in ("Takip No", "Fatura No"):
            if _kl_ref_kol in _kl_df_goster.columns:
                _kl_df_goster[_kl_ref_kol] = _kl_df_goster[_kl_ref_kol].map(_kg_referans_no_temizle)
        # Kar/Zarar'da ikisinden sadece biri dolu olur — 0 yerine "-"
        # göstersin diye biçimlendiriliyor (kayıt sırasında gerçek sayısal
        # değer zaten otomatik yeniden hesaplanıp yazılıyor).
        for _kl_kz_kol in ("Kar", "Zarar"):
            if _kl_kz_kol in _kl_df_goster.columns:
                _kl_df_goster[_kl_kz_kol] = _kl_df_goster[_kl_kz_kol].map(_kg_sifir_tire)
        for _kl_hesap_kol in ("B.Tutar", "Desi", "Kilo", "Yekün", "Sigorta %6", "Ara Toplam", "Kdv %20", "Son Toplam",
                               "Müşteri Tutar", "Dış Nakliye Tutar"):
            if _kl_hesap_kol in _kl_df_goster.columns:
                _kl_df_goster[_kl_hesap_kol] = _kl_df_goster[_kl_hesap_kol].map(_kg_tr_format)
        if _kl_mukerrer_toplam > 0:
            st.caption(f"🔁 Şu an sadece **birebir mükerrer** ({_kl_mukerrer_toplam} kayıt) gösteriliyor — kapatmak için üstteki butona tekrar bas."
                       if st.session_state.get("_kargolar_mukerrer_goster", False) else
                       f"🔁 {_kl_mukerrer_toplam} birebir mükerrer kayıt bulundu.")

        # ── ÖZET ROZETLERİ — kullanıcı isteği: İl kırılımı, Toplam Yekün, Dış
        # Nakliye Tutarı, Müşteri Tutarı ve Kar/Zarar HEPSİ aynı görünümde,
        # TEK SATIRDA gösterilir. Satır asla alt satıra kaymaz (flex-wrap:
        # nowrap); sığmazsa yazı boyutu görünürlük genişliğine göre otomatik
        # küçülür (font-size: clamp), yine de sığmazsa yatay kaydırılabilir
        # (overflow-x:auto) — böylece hep tek satırda, hep okunur kalır.
        _OZ_ROZET_STIL = ("display:inline-block;white-space:nowrap;padding:3px 8px;"
                           "border:1px solid #c9d3e0;border-radius:6px;background:#eef1f5;")
        _OZ_SATIR_STIL = ("display:flex;flex-wrap:nowrap;overflow-x:auto;gap:5px;align-items:center;"
                           "padding:6px 2px 14px 2px;font-size:clamp(9px,1.05vw,11px);")

        # "Toplam X kargo kaydı, Y müşteride" — kullanıcı isteği: satırın EN
        # BAŞINDA, kırmızı ve belirgin (kalın) yazıyla.
        _oz_toplam_rozeti = (
            f"<span style='display:inline-block;white-space:nowrap;padding:3px 8px;"
            f"border:2px solid #d64545;border-radius:6px;background:#ffffff;'>"
            f"<b style='color:#d64545;'>Toplam {len(_kl_df)} kargo kaydı, {_kl_df['_cari_id'].nunique()} müşteride.</b></span>"
        )

        # Dış Nakliye / Müşteri Tutarı / Kar-Zarar — hem tek müşteri hem tüm
        # müşteriler görünümünde ORTAK (branch'e bağlı değil).
        _kzo_dn_toplam = float(pd.to_numeric(_kl_df.get("dis_nakliye_tutar", 0), errors="coerce").fillna(0).sum()) if len(_kl_df) > 0 else 0.0
        _kzo_mt_toplam = float(pd.to_numeric(_kl_df.get("musteri_tutar", 0), errors="coerce").fillna(0).sum()) if len(_kl_df) > 0 else 0.0
        _kzo_kar = _kzo_mt_toplam - _kzo_dn_toplam
        _kzo_yuzde = (_kzo_kar / _kzo_mt_toplam * 100) if _kzo_mt_toplam else 0.0
        _kzo_renk_kenar = "#8fce9b" if _kzo_kar >= 0 else "#e5a3a3"
        _kzo_renk_zemin = "#e9f7ec" if _kzo_kar >= 0 else "#fbeaea"
        _kzo_etiket = "Kar" if _kzo_kar >= 0 else "Zarar"
        _kzo_ikon = "📈" if _kzo_kar >= 0 else "📉"
        _kzo_yuzde_str = f"{abs(_kzo_yuzde):.1f}".replace(".", ",")
        _oz_kar_zarar_rozeti = (
            f"<span style='display:inline-block;white-space:nowrap;padding:3px 8px;"
            f"border:1px solid #c9d3e0;border-radius:6px;background:#eef1f5;'>"
            f"🚚 <b>Dış Nakliye Tutarı Toplamı: {_kg_tr_format(_kzo_dn_toplam)} ₺</b></span>"
            f"<span style='{_OZ_ROZET_STIL}'>"
            f"👤 <b>Müşteri Tutarı Toplamı: {_kg_tr_format(_kzo_mt_toplam)} ₺</b></span>"
            f"<span style='display:inline-block;white-space:nowrap;padding:3px 8px;"
            f"border:1px solid {_kzo_renk_kenar};border-radius:6px;background:{_kzo_renk_zemin};'>"
            f"{_kzo_ikon} <b>{_kzo_etiket}: {_kg_tr_format(abs(_kzo_kar))} ₺ (%{_kzo_yuzde_str})</b></span>"
        )

        # ── İL ÖZETİ (KUTUCUKLU) — tek müşteri seçiliyken İl+Tür kırılımında
        # detaylı, birden çok müşteri (genel liste) görünüyorken sadece İl
        # bazında (tür ayrımı olmadan, kalabalık olmasın diye) gösterilir.
        # Her il kendi kutucuğunda; tutar olarak YEKÜN (B.Tutar × Adet)
        # toplamı gösterilir. En yoğun (adedi en yüksek) il soldan başlar.
        # NOT: "Toplam X kargo kaydı..." ve Kar/Zarar rozetleri, il verisi
        # (Alıcı İl doldurulmuş kayıt) olmasa bile HER ZAMAN gösterilir —
        # sadece il kutucukları ve Toplam Yekün, il verisi varsa eklenir.
        if len(_kl_df) > 0:
            _oz_il_parcalari = ""
            _oz_yekun_rozeti = ""
            if _kl_df["_cari_id"].nunique() == 1:
                _oz_df = _kl_df.copy()
                _oz_df["_il_norm"] = _oz_df.get("alici_il", "").astype(str).str.strip()
                _oz_df["_tur_norm"] = _oz_df.get("tur", "").astype(str).str.strip()
                _oz_df = _oz_df[_oz_df["_il_norm"] != ""]
                if not _oz_df.empty:
                    _oz_df["_yekun_num"] = pd.to_numeric(_oz_df.get("yekun", 0), errors="coerce").fillna(0)
                    _oz_df["_adet_num"] = pd.to_numeric(_oz_df.get("adet", 0), errors="coerce").fillna(0)
                    _oz_grup = (_oz_df.groupby(["_il_norm", "_tur_norm"])
                                .agg(Adet=("_adet_num", "sum"), Yekun=("_yekun_num", "sum"))
                                .reset_index()
                                .sort_values("Adet", ascending=False))
                    _oz_il_parcalari = "".join(
                        f"<span style='{_OZ_ROZET_STIL}'>"
                        f"<b>{_r['_il_norm']}</b> — {int(_r['Adet'])} {_r['_tur_norm'] or 'adet'} — {_kg_tr_format(_r['Yekun'])} ₺</span>"
                        for _, _r in _oz_grup.iterrows()
                    )
                    _oz_yekun_rozeti = (f"<span style='{_OZ_ROZET_STIL}'>"
                                         f"💰 <b>Toplam Yekün: {_kg_tr_format(float(_oz_df['_yekun_num'].sum()))} ₺</b></span>")
            else:
                # Birden çok müşteri görünüyorken (genel liste) tür kırılımına
                # inmiyoruz (kalabalık/karışık olduğu için) — sadece İL bazında,
                # tüm türler "Parça" olarak toplanmış, kutucuklu özet.
                _oz_df2 = _kl_df.copy()
                _oz_df2["_il_norm"] = _oz_df2.get("alici_il", "").astype(str).str.strip()
                _oz_df2 = _oz_df2[_oz_df2["_il_norm"] != ""]
                if not _oz_df2.empty:
                    _oz_df2["_yekun_num"] = pd.to_numeric(_oz_df2.get("yekun", 0), errors="coerce").fillna(0)
                    _oz_df2["_adet_num"] = pd.to_numeric(_oz_df2.get("adet", 0), errors="coerce").fillna(0)
                    _oz_grup2 = (_oz_df2.groupby("_il_norm")
                                 .agg(Adet=("_adet_num", "sum"), Yekun=("_yekun_num", "sum"))
                                 .reset_index()
                                 .sort_values("Adet", ascending=False))
                    _oz_il_parcalari = "".join(
                        f"<span style='{_OZ_ROZET_STIL}'>"
                        f"<b>{_r['_il_norm']}</b> — {int(_r['Adet'])} — {_kg_tr_format(_r['Yekun'])} ₺</span>"
                        for _, _r in _oz_grup2.iterrows()
                    )
                    _oz_yekun_rozeti = (f"<span style='{_OZ_ROZET_STIL}'>"
                                         f"💰 <b>Toplam Yekün: {_kg_tr_format(float(_oz_df2['_yekun_num'].sum()))} ₺</b></span>")
            st.markdown(
                f"<div style='{_OZ_SATIR_STIL}'>"
                f"{_oz_toplam_rozeti}"
                + (f"<span>📍</span>{_oz_il_parcalari}" if _oz_il_parcalari else "")
                + _oz_yekun_rozeti
                + _oz_kar_zarar_rozeti
                + f"</div>",
                unsafe_allow_html=True
            )

        # ── EXCEL İNDİR — tek sayfalık, bölünmemiş tam liste. Buton satırdaki
        # rezerve edilmiş kutunun İÇİNE konur (yukarıda "_kl_excel_indir_kutu").
        _kl_excel_buf = io.BytesIO()
        _kl_df_goster.drop(columns=["Seç", "_cari_id", "_satir_no"]).to_excel(_kl_excel_buf, index=False, engine="openpyxl")
        _kl_excel_buf.seek(0)
        with _kl_excel_indir_kutu:
            st.download_button("📥 Excel İndir", data=_kl_excel_buf,
                                file_name=f"kargolar_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="kargolar_excel_indir", use_container_width=True)

        # ── EXCEL YÜKLE — "📤 Excel Yükle" butonuna basılınca açılır/kapanır.
        if st.session_state.get("_kargolar_excel_yukle_ac", False):
            st.markdown("##### 📤 Excel Yükle (toplu geri yükleme)")
            st.caption("İndirdiğin Excel dosyasının sütun başlıklarıyla (Müşteri, Tarih, Gönderen, Alıcı, Fatura Ödeyen, vb.) aynı olmalı. "
                       "'Müşteri' sütunundaki isim sistemde kayıtlı bir firma adıyla BİREBİR eşleşmeli.")
            _kl_yuklenen_dosya = st.file_uploader("Excel dosyası seç (.xlsx)", type=["xlsx"], key="kargolar_excel_yukle_dosya")
            if _kl_yuklenen_dosya is not None:
                try:
                    _kl_yukleme_df = pd.read_excel(_kl_yuklenen_dosya)
                    st.caption(f"Dosyada {len(_kl_yukleme_df)} satır bulundu. Önizleme:")
                    st.dataframe(_kl_yukleme_df.head(10), use_container_width=True, hide_index=True)
                    if st.button("📤 Bu Dosyadaki Kayıtları Yükle", key="kargolar_excel_yukle_btn", type="primary"):
                        _kl_ters_yukle = {v: k for k, v in _kl_kolon_isim.items()}
                        _kl_musteri_adi_to_id = {v: k for k, v in _kl_musteri_map.items()}
                        # NOT: Eski kod sadece BİREBİR aynı yazımı veya (nadiren işe
                        # yarayan) büyük harf halini eşleştiriyordu — Excel'deki isimde
                        # ufak bir boşluk/büyük-küçük harf farkı olunca sessizce
                        # ATLANIYORDU (94 satırdan 91'i yüklenip 3'ü kaybolması gibi).
                        # Şimdi hem Excel'deki hem sistemdeki isim boşluksuz+Türkçe
                        # büyük harfe çevrilip öyle karşılaştırılıyor — sadece GERÇEKTEN
                        # sistemde kaydı olmayan firmalar eşleşmez.
                        _kl_musteri_adi_norm_to_id = {_tr_buyuk(str(_v).strip()): _k for _k, _v in _kl_musteri_map.items()}
                        _kl_yuklenen_sayac = 0
                        _kl_eslesmeyen = []
                        _kl_yeni_gruplar = {}
                        for _, _yr in _kl_yukleme_df.iterrows():
                            _yr_musteri = str(_yr.get("Müşteri", "")).strip()
                            _yr_cid = (_kl_musteri_adi_to_id.get(_yr_musteri)
                                       or _kl_musteri_adi_norm_to_id.get(_tr_buyuk(_yr_musteri)))
                            if not _yr_cid:
                                _kl_eslesmeyen.append(_yr_musteri)
                                continue
                            _yr_kayit = {}
                            for _yr_kol, _yr_val in _yr.items():
                                if _yr_kol == "Müşteri":
                                    continue
                                _yr_anahtar = _kl_ters_yukle.get(_yr_kol, _yr_kol)
                                # ÖNEMLİ: Excel'de "Takip No"/"Fatura No" gibi sütunlar
                                # sayı olarak algılanınca pandas bunları float (1910372.0)
                                # okur — düz str() bu ".0" kuyruğunu KALICI olarak veriye
                                # işlerdi (parasal olmayan bir alanda anlamsız/yanlış
                                # görünüyordu). Tam sayıya denk gelen float'lar burada
                                # ".0" eklenmeden tam sayı metnine çevrilir; gerçek
                                # ondalıklı değerler ve Tarih olduğu gibi bırakılır.
                                if pd.isna(_yr_val):
                                    _yr_kayit[_yr_anahtar] = ""
                                elif _yr_kol == "Tarih":
                                    _yr_kayit[_yr_anahtar] = str(_yr_val)[:10]
                                elif isinstance(_yr_val, float) and _yr_val.is_integer():
                                    _yr_kayit[_yr_anahtar] = str(int(_yr_val))
                                else:
                                    _yr_kayit[_yr_anahtar] = str(_yr_val)
                            _kg_hesap_zinciri(_yr_kayit)
                            _kg_kar_zarar_hesapla(_yr_kayit)
                            _kl_yeni_gruplar.setdefault(_yr_cid, []).append(_yr_kayit)
                            _kl_yuklenen_sayac += 1
                        _kl_taze_basarisiz_musteriler = []
                        for _yr_cid2, _yr_yeni_kayitlar in _kl_yeni_gruplar.items():
                            _yr_taze_sonuc = _kg_kayitlari_yukle_taze(f"_kargo_kayitlari_{_yr_cid2}")
                            if _yr_taze_sonuc is _OKUMA_BASARISIZ:
                                _kl_taze_basarisiz_musteriler.append(_kl_musteri_map.get(_yr_cid2, str(_yr_cid2)))
                                continue
                            _yr_mevcut = list(_yr_taze_sonuc)
                            _yr_mevcut.extend(_yr_yeni_kayitlar)
                            _kargolar_yaz(_yr_cid2, _yr_mevcut)
                            _yr_eklenen_tutar = sum(_kg_efektif_tutar(_k) for _k in _yr_yeni_kayitlar)
                            _cari_gerceklesen_ciro_ekle(_yr_cid2, _yr_eklenen_tutar)
                        _kargolar_tumunu_yukle.clear()
                        _kg_kayitlari_yukle.clear()
                        if _kl_taze_basarisiz_musteriler:
                            st.error(f"⚠️ Şu müşteriler için veritabanına ulaşılamadı, GÜVENLİK İÇİN o müşterilerin kayıtları yüklenmedi (diğerleri yüklendi): {', '.join(_kl_taze_basarisiz_musteriler)}. Lütfen bu müşteriler için tekrar dene.")
                        if _kl_eslesmeyen:
                            st.warning(f"⚠️ {len(set(_kl_eslesmeyen))} farklı müşteri adı sistemde bulunamadı (eklenmedi — hepsi): {', '.join(sorted(set(_kl_eslesmeyen)))}")
                        st.toast(f"✅ {_kl_yuklenen_sayac} kayıt yüklendi", icon="📤")
                        st.rerun()
                except Exception as _kl_yukleme_hata:
                    st.error(f"Dosya okunamadı: {_kl_yukleme_hata}")
            st.divider()

        # ── TÜM MÜŞTERİLER GENEL RAPORU — filtrelerden bağımsız, sistemdeki
        # HERKESİ kapsar. Firma + Gönderen İl + Alıcı İl + Tür kırılımlı, altında
        # genel toplam satırı. Aylık ya da tüm zaman seçilebilir.
        if st.session_state.get("_kargolar_genel_rapor_ac", False):
            st.markdown("##### 📊 Tüm Müşteriler — Genel Rapor")
            _tg_df = pd.DataFrame(_kl_tum_kayitlar).fillna("") if _kl_tum_kayitlar else pd.DataFrame()
            if _tg_df.empty:
                st.caption("Henüz hiçbir kayıt yok.")
            else:
                _tg_df["Müşteri"] = _tg_df["_cari_id"].map(_kl_musteri_map).fillna("(Bilinmiyor)")
                _tg_df["_efektif_tutar"] = pd.to_numeric(_tg_df.get("toplam_fatura", 0), errors="coerce").fillna(0)
                _tg_tutar_num = pd.to_numeric(_tg_df.get("tutar", 0), errors="coerce").fillna(0)
                _tg_df.loc[_tg_df["_efektif_tutar"] == 0, "_efektif_tutar"] = _tg_tutar_num
                _tg_df["_tarih_dt"] = pd.to_datetime(_tg_df.get("tarih", ""), errors="coerce")

                _tgc1, _tgc2 = st.columns([1, 2])
                _tg_zaman_secim = _tgc1.radio("Zaman Aralığı", ["Tüm Zaman", "Belirli Ay"], key="tg_zaman_secim", horizontal=True)
                if _tg_zaman_secim == "Belirli Ay":
                    _tg_ay_secenekleri = sorted(_tg_df["_tarih_dt"].dropna().dt.strftime("%Y-%m").unique().tolist(), reverse=True)
                    if _tg_ay_secenekleri:
                        _tg_sec_ay = _tgc2.selectbox("Ay seç", _tg_ay_secenekleri, key="tg_sec_ay")
                        _tg_df = _tg_df[_tg_df["_tarih_dt"].dt.strftime("%Y-%m") == _tg_sec_ay]
                    else:
                        st.caption("Tarihli kayıt yok.")

                _tg_df["_tur_norm"] = _tg_df.get("tur", "").astype(str).str.strip().str.upper().replace("", "(TÜR BELİRTİLMEMİŞ)")
                _tg_grup = (_tg_df.groupby(["Müşteri", "gonderen_il", "alici_il", "_tur_norm"])
                            .agg(Adet=("_tur_norm", "size"), Tutar=("_efektif_tutar", "sum"))
                            .reset_index()
                            .rename(columns={"gonderen_il": "Gönderen İl", "alici_il": "Alıcı İl", "_tur_norm": "Tür"})
                            .sort_values(["Müşteri", "Adet"], ascending=[True, False]))

                if _tg_grup.empty:
                    st.caption("Bu aralıkta kayıt yok.")
                else:
                    _tg_grup_goster = _tg_grup.copy()
                    _tg_grup_goster["Tutar"] = _tg_grup_goster["Tutar"].apply(lambda x: f"{x:,.0f} ₺")
                    st.dataframe(_tg_grup_goster, use_container_width=True, hide_index=True,
                                 height=min(38 * (len(_tg_grup_goster) + 1) + 25, 600))

                    _tg_genel_adet = int(_tg_grup["Adet"].sum())
                    _tg_genel_tutar = float(_tg_grup["Tutar"].sum())
                    st.markdown(f"#### 🧮 GENEL TOPLAM: {_tg_genel_adet} adet — {_tg_genel_tutar:,.0f} ₺")

        # Butonlar tablonun ÜSTÜNDE görünsün diye önce boş bir kutu (container)
        # ayrılıyor, düzenlenen tablo aşağıda oluşuyor, butonlar en son bu
        # kutunun İÇİNE render ediliyor — ama DOM'da (ekranda) yeri en üstte kalıyor.
        _kl_btn_kutu = st.container()

        # Tablo yüksekliği: TÜM satırlar tek seferde, kaydırmaya gerek kalmadan
        # görünsün diye satır sayısına göre otomatik büyütülüyor (üst sınırla).
        _kl_yukseklik = min(38 * (len(_kl_df_goster) + 1) + 25, 900)
        # Kolon Ayarları (Kullanıcılar sayfası) sekmesinde ayarlanan genişlikler
        _kl_kol_genislik = st.session_state.get("_kargo_kol_genislik", {})
        _KL_OTOMATIK_HESAPLI_KOLONLAR = {
            "Kar": "Otomatik hesaplanır: Müşteri Tutar − Dış Nakliye Tutar (pozitifse burada görünür)",
            "Zarar": "Otomatik hesaplanır: Müşteri Tutar − Dış Nakliye Tutar (negatifse burada görünür)",
            "Yekün": "Otomatik hesaplanır: B.Tutar × Adet",
            "Sigorta %6": "Otomatik hesaplanır: Yekün × %6",
            "Ara Toplam": "Otomatik hesaplanır: Yekün + Sigorta %6",
            "Kdv %20": "Otomatik hesaplanır: Ara Toplam × %20",
            "Son Toplam": "Otomatik hesaplanır: Ara Toplam + Kdv %20",
        }
        # Dış Nakliye Firma SADECE Tedarikçi listesinden gelir — eski kargo
        # kayıtlarındaki (bazen bozuk/uzun/"None" gibi) elle yazılmış
        # değerler seçeneklere KARIŞTIRILMAZ (kullanıcı isteği).
        _kl_dnf_opts = sorted(set(
            _t.get("firma_adi", "") for _t in _tedarikci_yukle_goster() if not _t.get("silindi") and _gecerli_metin(_t.get("firma_adi", ""))
        ))
        _kl_col_config = {"Seç": st.column_config.CheckboxColumn("Seç", default=False)}
        for _kl_kol_ad in _kl_df_goster.columns:
            if _kl_kol_ad in ("Seç", "_cari_id", "_satir_no"):
                continue
            _kl_gen = _kl_kol_genislik.get(_kl_kol_ad)
            if _kl_kol_ad in _KL_OTOMATIK_HESAPLI_KOLONLAR:
                # Bu sütunlar artık ELLE YAZILMIYOR — otomatik hesaplanıp
                # kayıt anında üzerine yazılıyor.
                _kl_col_config[_kl_kol_ad] = st.column_config.Column(
                    _kl_kol_ad, width=(int(_kl_gen) * 8 if _kl_gen else None), disabled=True,
                    help=_KL_OTOMATIK_HESAPLI_KOLONLAR[_kl_kol_ad])
            elif _kl_kol_ad == "Dış Nakliye Firma":
                _kl_col_config[_kl_kol_ad] = st.column_config.SelectboxColumn(
                    _kl_kol_ad, width=(int(_kl_gen) * 8 if _kl_gen else None), options=[""] + _kl_dnf_opts,
                    help="Tedarikçi sayfasından eklediğin firmalar burada listelenir.")
            elif _kl_gen:
                _kl_col_config[_kl_kol_ad] = st.column_config.Column(_kl_kol_ad, width=int(_kl_gen) * 8)
        if "_kl_editor_versiyon" not in st.session_state:
            st.session_state["_kl_editor_versiyon"] = 0
        # NOT: Bu bayrak artık KALICI — bir önceki denemede sadece TEK render'da
        # geçerli oluyordu (pop ile siliniyordu). Streamlit'in data_editor'ü
        # seçimi taban veriye göre değil FARK (delta) olarak sakladığı için,
        # ikinci render'da (mesela Sil butonuna basılınca) taban veri tekrar
        # False'a dönüyor ve "işaretliydi ama artık değil" gibi görünüyordu —
        # aslında hiç silinmiyordu çünkü Sil'in kendi render'ında seçim zaten
        # sıfırlanmış oluyordu. Şimdi bayrak, Temizle'ye ya da başarılı bir
        # Kaydet/Sil işlemine kadar HER render'da yeniden uygulanıyor.
        if st.session_state.get("_kl_tumu_secili_mod", False):
            _kl_df_goster["Seç"] = True
        # ── "🔄 Hesapla" butonuna basılınca, o an tablodaki TÜM elle yapılmış
        # düzenlemeler (B.Tutar değişikliği dahil) burada üzerine yazılır —
        # sadece hesaplanan sütunlar (Sigorta/Ara Toplam/Kdv/Son Toplam/Kar/
        # Zarar) TAZE değerlerle güncellenmiş olarak geri gelir. Kaydet'e
        # basmadan önce, tablo üzerinde canlı gibi görünmesini sağlar.
        if "_kl_hesapla_bekleyen" in st.session_state:
            _kl_bekleyen = st.session_state.pop("_kl_hesapla_bekleyen")
            if len(_kl_bekleyen) == len(_kl_df_goster):
                for _pcol in _kl_bekleyen.columns:
                    if _pcol in _kl_df_goster.columns:
                        _kl_df_goster[_pcol] = _kl_bekleyen[_pcol].values
        _kl_df_goster = _hic_none_gosterme(_kl_df_goster)
        _kl_editor_key = f"kargolar_editor_{st.session_state['_kl_editor_versiyon']}"
        _kl_duzenlenen = st.data_editor(
            _kl_df_goster.drop(columns=["_cari_id", "_satir_no"]), use_container_width=True, hide_index=True,
            key=_kl_editor_key, height=_kl_yukseklik,
            column_config=_kl_col_config
        )

        with _kl_btn_kutu:
            _klb0a, _klb0b, _klb0c, _klb0d, _klb0e, _klb0f, _klb1, _klb2 = st.columns(8)
            with _klb0a:
                if st.button("☑️ Tümünü Seç", key="kargolar_tumunu_sec_btn", use_container_width=True):
                    st.session_state["_kl_tumu_secili_mod"] = True
                    st.session_state["_kl_editor_versiyon"] += 1
                    st.rerun()
            with _klb0b:
                if st.button("⬜ Seçimi Temizle", key="kargolar_secimi_temizle_btn", use_container_width=True):
                    st.session_state["_kl_tumu_secili_mod"] = False
                    st.session_state["_kl_editor_versiyon"] += 1
                    st.rerun()
            with _klb0c:
                if st.button("🔄 Hesapla", key="kargolar_hesapla_btn", use_container_width=True,
                             help="B.Tutar / Müşteri Tutar / Dış Nakliye Tutar'ı burada değiştirdiysen, Kaydet'e basmadan ÖNCE Sigorta/Ara Toplam/Kdv/Son Toplam/Kar/Zarar'ı bu tabloda güncellemek için tıkla."):
                    _kl_yeni_taban = _kl_duzenlenen.copy()
                    for _hidx in _kl_yeni_taban.index:
                        _hkayit = {
                            "tutar": _kl_yeni_taban.at[_hidx, "B.Tutar"] if "B.Tutar" in _kl_yeni_taban.columns else 0,
                            "adet": _kl_yeni_taban.at[_hidx, "Adet"] if "Adet" in _kl_yeni_taban.columns else 0,
                            "musteri_tutar": _kl_yeni_taban.at[_hidx, "Müşteri Tutar"] if "Müşteri Tutar" in _kl_yeni_taban.columns else 0,
                            "dis_nakliye_tutar": _kl_yeni_taban.at[_hidx, "Dış Nakliye Tutar"] if "Dış Nakliye Tutar" in _kl_yeni_taban.columns else 0,
                        }
                        _kg_hesap_zinciri(_hkayit)
                        _kg_kar_zarar_hesapla(_hkayit)
                        for _hkol, _hdeger in (("Sigorta %6", _hkayit["sigorta"]), ("Ara Toplam", _hkayit["ara_toplam"]),
                                                ("Kdv %20", _hkayit["kdv"]), ("Son Toplam", _hkayit["toplam_fatura"])):
                            if _hkol in _kl_yeni_taban.columns:
                                _kl_yeni_taban.at[_hidx, _hkol] = _hdeger
                        for _hkol2, _hdeger2 in (("Kar", _hkayit["kar"]), ("Zarar", _hkayit["zarar"])):
                            if _hkol2 in _kl_yeni_taban.columns:
                                _kl_yeni_taban.at[_hidx, _hkol2] = _kg_sifir_tire(_hdeger2)
                    st.session_state["_kl_hesapla_bekleyen"] = _kl_yeni_taban
                    st.session_state["_kl_editor_versiyon"] += 1
                    st.rerun()
            with _klb0d:
                _kl_mukerrer_aktif = st.session_state.get("_kargolar_mukerrer_goster", False)
                _kl_mukerrer_etiket = f"🔁 {_kl_mukerrer_toplam} Mükerrer" if not _kl_mukerrer_aktif else "🔁 Mükerrer — Kapat"
                if st.button(_kl_mukerrer_etiket, key="kargolar_mukerrer_btn", use_container_width=True,
                             type="primary" if _kl_mukerrer_aktif else "secondary",
                             disabled=(_kl_mukerrer_toplam == 0 and not _kl_mukerrer_aktif)):
                    st.session_state["_kargolar_mukerrer_goster"] = not _kl_mukerrer_aktif
                    st.session_state["_kl_tumu_secili_mod"] = False
                    st.session_state["_kl_editor_versiyon"] += 1
                    st.rerun()
            with _klb0e:
                _kl_secili_indeksler = [_i for _i in _kl_duzenlenen.index if bool(_kl_duzenlenen.loc[_i].get("Seç"))]
                if st.button("✏️ Düzenle", key="kargolar_duzenle_btn", use_container_width=True,
                             disabled=len(_kl_secili_indeksler) != 1,
                             help="Kargo Girişi formunda açıp düzenlemek için tam olarak 1 kayıt seç."):
                    _kl_duz_idx = _kl_secili_indeksler[0]
                    _kl_duz_cid = int(_kl_df_goster.iloc[_kl_duz_idx]["_cari_id"])
                    _kl_duz_satir = int(_kl_df_goster.iloc[_kl_duz_idx]["_satir_no"])
                    # Ek güvenlik: pencere kapanınca kutu işaretli kalıp
                    # unutulmasın diye seçim burada temizleniyor.
                    st.session_state["_kl_tumu_secili_mod"] = False
                    st.session_state["_kl_editor_versiyon"] += 1
                    kargo_kaydi_duzenle_dialog(_kl_duz_cid, _kl_duz_satir)
            with _klb0f:
                _kl_silinenler_etiket = f"🗑️ Silinenler" if not _kl_silinenler_aktif else "🗑️ Silinenler — Kapat"
                if st.button(_kl_silinenler_etiket, key="kargolar_silinenler_btn", use_container_width=True,
                             type="primary" if _kl_silinenler_aktif else "secondary",
                             help="Silinen kargo kayıtlarını görüp geri alabilir ya da kalıcı olarak silebilirsin."):
                    st.session_state["_kargolar_silinenler_goster"] = not _kl_silinenler_aktif
                    st.session_state["_kl_tumu_secili_mod"] = False
                    st.session_state["_kl_editor_versiyon"] += 1
                    st.rerun()
            with _klb1:
                if st.button("💾 Değişiklikleri Kaydet", key="kargolar_kaydet_btn", type="primary", use_container_width=True):
                    _kl_ters = {v: k for k, v in _kl_kolon_isim.items()}
                    # ── DOĞRU MANTIK: her müşterinin TAM listesi (filtre dışında
                    # kalanlar dahil) fresh olarak yüklenir, sadece o an TABLODA
                    # GÖRÜNEN satırlar (kendi _satir_no'suna göre) güncellenir/silinir
                    # — filtre dışındaki diğer kayıtlara HİÇ dokunulmaz.
                    _kl_etkilenen_cid = set(int(x) for x in _kl_df["_cari_id"].unique())
                    _kl_tam_listeler = {}
                    _kl_eski_toplamlar = {}
                    _kl_kaydet_basarisiz_musteriler = []
                    for _cid_yukle in _kl_etkilenen_cid:
                        _cid_taze_sonuc = _kg_kayitlari_yukle_taze(f"_kargo_kayitlari_{_cid_yukle}")
                        if _cid_taze_sonuc is _OKUMA_BASARISIZ:
                            _kl_kaydet_basarisiz_musteriler.append(_kl_musteri_map.get(_cid_yukle, str(_cid_yukle)))
                            continue
                        _kl_tam_listeler[_cid_yukle] = list(_cid_taze_sonuc)
                        _kl_eski_toplamlar[_cid_yukle] = sum(_kg_efektif_tutar(_k) for _k in _kl_tam_listeler[_cid_yukle])
                    # GÜVENLİK: Kaydet artık "Seç" işaretine bakmadan SADECE
                    # değerleri günceller — işaretli olsa bile SATIR SİLİNMEZ.
                    # Silme SADECE aşağıdaki ayrı "Sil" butonuyla yapılır. (Bu
                    # ayrım olmayınca, "Düzenle" için işaretlenip sonra
                    # unutulan bir kutu, alakasız bir Kaydet tıklamasında
                    # kaydı sessizce siliyordu — tehlikeliydi, düzeltildi.)
                    for _idx, _r in _kl_duzenlenen.iterrows():
                        _cid = int(_kl_df_goster.iloc[_idx]["_cari_id"])
                        if _cid not in _kl_tam_listeler:
                            continue  # bu müşterinin verisi taze okunamadı, GÜVENLİK için dokunulmuyor
                        _satir_no = int(_kl_df_goster.iloc[_idx]["_satir_no"])
                        if _satir_no >= len(_kl_tam_listeler[_cid]):
                            continue
                        _kayit = {}
                        for _kol, _val in _r.items():
                            if _kol in ("Seç", "Müşteri"):
                                continue
                            _kayit[_kl_ters.get(_kol, _kol)] = _val
                        _kg_hesap_zinciri(_kayit)
                        _kg_kar_zarar_hesapla(_kayit)
                        _kl_tam_listeler[_cid][_satir_no] = _kayit
                    for _cid_kaydet, _liste_kaydet in _kl_tam_listeler.items():
                        _kl_liste_temiz = [x for x in _liste_kaydet if x is not None]
                        _kargolar_yaz(_cid_kaydet, _kl_liste_temiz)
                        _kl_yeni_toplam = sum(_kg_efektif_tutar(_k) for _k in _kl_liste_temiz)
                        _cari_gerceklesen_ciro_ekle(_cid_kaydet, _kl_yeni_toplam - _kl_eski_toplamlar.get(_cid_kaydet, 0))
                    _kargolar_tumunu_yukle.clear()
                    _kg_kayitlari_yukle.clear()
                    if _kl_kaydet_basarisiz_musteriler:
                        st.error(f"⚠️ Şu müşterilerin verisine şu an ulaşılamadı, GÜVENLİK İÇİN onların değişiklikleri kaydedilmedi (diğerleri kaydedildi): {', '.join(_kl_kaydet_basarisiz_musteriler)}. Lütfen tekrar dene.")
                    st.session_state["_kl_tumu_secili_mod"] = False
                    st.session_state["_kl_editor_versiyon"] += 1
                    st.toast("✅ Kargo kayıtları güncellendi (filtre dışındaki kayıtlara dokunulmadı)", icon="🚚")
                    st.rerun()
            with _klb2:
                _kl_secili_sayi = int(_kl_duzenlenen["Seç"].sum()) if "Seç" in _kl_duzenlenen.columns else 0
                if st.button(f"🗑️ Seçili {_kl_secili_sayi} Kaydı Sil", key="kargolar_sil_btn", use_container_width=True, disabled=_kl_secili_sayi == 0):
                    _kl_etkilenen_cid2 = set(int(_kl_df_goster.iloc[_idx2]["_cari_id"])
                                              for _idx2, _r2 in _kl_duzenlenen.iterrows() if bool(_r2.get("Seç")))
                    _kl_tam_listeler2 = {}
                    _kl_eski_toplamlar2 = {}
                    _kl_sil_basarisiz_musteriler = []
                    for _cid_yukle2 in _kl_etkilenen_cid2:
                        _cid2_taze_sonuc = _kg_kayitlari_yukle_taze(f"_kargo_kayitlari_{_cid_yukle2}")
                        if _cid2_taze_sonuc is _OKUMA_BASARISIZ:
                            _kl_sil_basarisiz_musteriler.append(_kl_musteri_map.get(_cid_yukle2, str(_cid_yukle2)))
                            continue
                        _kl_tam_listeler2[_cid_yukle2] = list(_cid2_taze_sonuc)
                        _kl_eski_toplamlar2[_cid_yukle2] = sum(_kg_efektif_tutar(_k) for _k in _kl_tam_listeler2[_cid_yukle2])
                    # GÜVENLİK: YUMUŞAK SİLME — kayıt listeden ÇIKARILMIYOR,
                    # sadece "silindi" olarak işaretlenip normal görünümden
                    # gizleniyor. "🗑️ Silinenler" görünümünden geri alınabilir.
                    for _idx2, _r2 in _kl_duzenlenen.iterrows():
                        if not bool(_r2.get("Seç")):
                            continue
                        _cid2 = int(_kl_df_goster.iloc[_idx2]["_cari_id"])
                        _satir_no2 = int(_kl_df_goster.iloc[_idx2]["_satir_no"])
                        if _cid2 in _kl_tam_listeler2 and _satir_no2 < len(_kl_tam_listeler2[_cid2]):
                            _kl_tam_listeler2[_cid2][_satir_no2]["silindi"] = True
                            _kl_tam_listeler2[_cid2][_satir_no2]["silinme_tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    for _cid_kaydet2, _liste_kaydet2 in _kl_tam_listeler2.items():
                        _kargolar_yaz(_cid_kaydet2, _liste_kaydet2)
                        _kl_yeni_toplam2 = sum(_kg_efektif_tutar(_k) for _k in _liste_kaydet2 if not _k.get("silindi"))
                        _cari_gerceklesen_ciro_ekle(_cid_kaydet2, _kl_yeni_toplam2 - _kl_eski_toplamlar2.get(_cid_kaydet2, 0))
                    _kargolar_tumunu_yukle.clear()
                    _kg_kayitlari_yukle.clear()
                    if _kl_sil_basarisiz_musteriler:
                        st.error(f"⚠️ Şu müşterilerin verisine şu an ulaşılamadı, GÜVENLİK İÇİN onlardan hiçbir şey silinmedi: {', '.join(_kl_sil_basarisiz_musteriler)}. Lütfen tekrar dene.")
                    st.session_state["_kl_tumu_secili_mod"] = False
                    st.session_state["_kl_editor_versiyon"] += 1
                    st.toast(f"🗑️ {_kl_secili_sayi} kayıt silindi — '🗑️ Silinenler'den geri alabilirsin", icon="🗑️")
                    st.rerun()

            if _kl_silinenler_aktif:
                st.caption("🗑️ Şu an sadece **silinmiş** kayıtlar gösteriliyor. Seçip geri alabilir ya da kalıcı olarak silebilirsin (kalıcı silme geri alınamaz).")
                _klg1, _klg2 = st.columns(2)
                with _klg1:
                    if st.button("↩️ Seçilenleri Geri Al", key="kargolar_geri_al_btn", use_container_width=True,
                                 disabled=_kl_secili_sayi == 0):
                        _kl_etkilenen_cid3 = set(int(_kl_df_goster.iloc[_idx3]["_cari_id"])
                                                  for _idx3, _r3 in _kl_duzenlenen.iterrows() if bool(_r3.get("Seç")))
                        _kl_tam_listeler3 = {}
                        _kl_geri_al_basarisiz_musteriler = []
                        for _cid_yukle3 in _kl_etkilenen_cid3:
                            _cid3_taze_sonuc = _kg_kayitlari_yukle_taze(f"_kargo_kayitlari_{_cid_yukle3}")
                            if _cid3_taze_sonuc is _OKUMA_BASARISIZ:
                                _kl_geri_al_basarisiz_musteriler.append(_kl_musteri_map.get(_cid_yukle3, str(_cid_yukle3)))
                                continue
                            _kl_tam_listeler3[_cid_yukle3] = list(_cid3_taze_sonuc)
                        _kl_geri_alinan_tutar = {}
                        for _idx3, _r3 in _kl_duzenlenen.iterrows():
                            if not bool(_r3.get("Seç")):
                                continue
                            _cid3 = int(_kl_df_goster.iloc[_idx3]["_cari_id"])
                            _satir_no3 = int(_kl_df_goster.iloc[_idx3]["_satir_no"])
                            if _cid3 in _kl_tam_listeler3 and _satir_no3 < len(_kl_tam_listeler3[_cid3]):
                                _kl_tam_listeler3[_cid3][_satir_no3]["silindi"] = False
                                _kl_tam_listeler3[_cid3][_satir_no3].pop("silinme_tarihi", None)
                                _kl_geri_alinan_tutar[_cid3] = _kl_geri_alinan_tutar.get(_cid3, 0.0) + _kg_efektif_tutar(_kl_tam_listeler3[_cid3][_satir_no3])
                        for _cid_kaydet3, _liste_kaydet3 in _kl_tam_listeler3.items():
                            _kargolar_yaz(_cid_kaydet3, _liste_kaydet3)
                            if _cid_kaydet3 in _kl_geri_alinan_tutar:
                                # Not: geri alınca ciro tekrar eklenir — Sil'de düşülen tutar geri gelir.
                                _cari_gerceklesen_ciro_ekle(_cid_kaydet3, _kl_geri_alinan_tutar[_cid_kaydet3])
                        _kargolar_tumunu_yukle.clear()
                        _kg_kayitlari_yukle.clear()
                        if _kl_geri_al_basarisiz_musteriler:
                            st.error(f"⚠️ Şu müşterilerin verisine şu an ulaşılamadı, GÜVENLİK İÇİN onlar için geri alma yapılmadı: {', '.join(_kl_geri_al_basarisiz_musteriler)}. Lütfen tekrar dene.")
                        st.session_state["_kl_tumu_secili_mod"] = False
                        st.session_state["_kl_editor_versiyon"] += 1
                        st.toast("↩️ Seçili kayıtlar geri alındı", icon="↩️")
                        st.rerun()
                with _klg2:
                    _kl_kalici_onay = st.checkbox("Eminim, kalıcı olarak sil (geri alınamaz)", key="kargolar_kalici_sil_onay")
                    if st.button(f"❌ Kalıcı Olarak Sil (Seçili {_kl_secili_sayi})", key="kargolar_kalici_sil_btn", use_container_width=True,
                                 disabled=(_kl_secili_sayi == 0 or not _kl_kalici_onay),
                                 help="DİKKAT: bu işlem geri alınamaz, kayıt tamamen silinir."):
                        _kl_etkilenen_cid4 = set(int(_kl_df_goster.iloc[_idx4]["_cari_id"])
                                                  for _idx4, _r4 in _kl_duzenlenen.iterrows() if bool(_r4.get("Seç")))
                        _kl_tam_listeler4 = {}
                        _kl_kalici_basarisiz_musteriler = []
                        for _cid_yukle4 in _kl_etkilenen_cid4:
                            _cid4_taze_sonuc = _kg_kayitlari_yukle_taze(f"_kargo_kayitlari_{_cid_yukle4}")
                            if _cid4_taze_sonuc is _OKUMA_BASARISIZ:
                                _kl_kalici_basarisiz_musteriler.append(_kl_musteri_map.get(_cid_yukle4, str(_cid_yukle4)))
                                continue
                            _kl_tam_listeler4[_cid_yukle4] = list(_cid4_taze_sonuc)
                        _kl_silinecek_satirlar = {}
                        for _idx4, _r4 in _kl_duzenlenen.iterrows():
                            if not bool(_r4.get("Seç")):
                                continue
                            _cid4 = int(_kl_df_goster.iloc[_idx4]["_cari_id"])
                            _satir_no4 = int(_kl_df_goster.iloc[_idx4]["_satir_no"])
                            _kl_silinecek_satirlar.setdefault(_cid4, set()).add(_satir_no4)
                        for _cid_kaydet4, _liste_kaydet4 in _kl_tam_listeler4.items():
                            _silinecekler4 = _kl_silinecek_satirlar.get(_cid_kaydet4, set())
                            _kl_liste_temiz4 = [_k for _i5, _k in enumerate(_liste_kaydet4) if _i5 not in _silinecekler4]
                            _kargolar_yaz(_cid_kaydet4, _kl_liste_temiz4)
                        _kargolar_tumunu_yukle.clear()
                        _kg_kayitlari_yukle.clear()
                        if _kl_kalici_basarisiz_musteriler:
                            st.error(f"⚠️ Şu müşterilerin verisine şu an ulaşılamadı, GÜVENLİK İÇİN onlardan hiçbir şey kalıcı silinmedi: {', '.join(_kl_kalici_basarisiz_musteriler)}. Lütfen tekrar dene.")
                        st.session_state["_kl_tumu_secili_mod"] = False
                        st.session_state["_kl_editor_versiyon"] += 1
                        st.session_state["kargolar_kalici_sil_onay"] = False
                        st.toast(f"❌ {_kl_secili_sayi} kayıt kalıcı olarak silindi", icon="❌")
                        st.rerun()

elif aktif == "tedarikci":
    sayfa_log("tedarikci")
    st.subheader("🚛 Tedarikçi")
    st.caption("Nakliyeci/taşıyıcı firmaları burada kaydet — Kargo Girişi'ndeki 'Dış Nakliye Firma' listesi buradan gelir.")

    if "_td_editor_versiyon" not in st.session_state:
        st.session_state["_td_editor_versiyon"] = 0
    _td_silinenler_aktif = st.session_state.get("_td_silinenler_goster", False)

    # GÜVENLİK: okuma başarısız olursa (bağlantı sorunu) sayfanın geri kalanını
    # HİÇ render ETME — aksi halde "boşmuş" sanılıp yanlışlıkla migrasyon ya da
    # kaydetme tetiklenip var olan veri EZİLEBİLİRDİ (yaşanan veri kaybı buydu).
    _td_okuma_sonuc = _tedarikci_yukle_ham_guvenli()
    if _td_okuma_sonuc is _OKUMA_BASARISIZ:
        st.error("⚠️ Tedarikçi verisine şu an ulaşılamadı. Güvenlik için hiçbir şey değiştirilmedi/taşınmadı. Sayfayı yenileyip tekrar dene.")
        st.stop()
    elif not _td_okuma_sonuc and not _tedarikci_migrasyon_yapildi_mi():
        # Migrasyon GERÇEKTEN hiç yapılmamış (hem liste boş HEM işaret yok) —
        # bu durumda güvenle eski taşıyıcı listesinden bir kerelik taşınır.
        _td_eski = _dis_nakliye_tasiyici_yukle()
        _td_migrasyon_liste = []
        for _e in (_td_eski or []):
            if isinstance(_e, dict):
                _td_migrasyon_liste.append({
                    "tarih": "", "firma_adi": _tr_buyuk(_e.get("tasiyici", "")), "gsm": _e.get("yetkili_tel", ""),
                    "sabit_tel": "", "email": "", "adres": "", "ilce": "", "il": "",
                    "yuk_aciklamasi": "", "tur": "", "adet": 0, "tutar": 0.0,
                    "yetkili": _e.get("yetkili", ""), "silindi": False,
                })
            elif isinstance(_e, str) and _e.strip():
                _td_migrasyon_liste.append({
                    "tarih": "", "firma_adi": _tr_buyuk(_e), "gsm": "", "sabit_tel": "", "email": "",
                    "adres": "", "ilce": "", "il": "", "yuk_aciklamasi": "", "tur": "", "adet": 0, "tutar": 0.0,
                    "yetkili": "", "silindi": False,
                })
        if _td_migrasyon_liste:
            _tedarikci_kaydet(_td_migrasyon_liste)
        _tedarikci_migrasyon_isaretle()  # bir daha ASLA tekrar denenmesin
        _td_tum = _td_migrasyon_liste
    else:
        _td_tum = _td_okuma_sonuc
    _td_liste_goster = [t for t in _td_tum if bool(t.get("silindi")) == _td_silinenler_aktif]

    if not _td_silinenler_aktif:
        with st.expander("➕ Yeni Tedarikçi Ekle", expanded=not _td_liste_goster):
            st.markdown("**📋 Firma Bilgileri**")
            with st.container(border=True):
                _tdc1, _tdc2, _tdc3 = st.columns(3)
                _td_firma = _tdc1.text_input("Firma Adı", key="td_yeni_firma")
                _td_yetkili = _tdc2.text_input("Yetkili", key="td_yeni_yetkili")
                _td_tarih = _tdc3.date_input("Tarih", key="td_yeni_tarih")
                _td_gsm = _tdc1.text_input("GSM", key="td_yeni_gsm")
                _td_sabit = _tdc2.text_input("Sabit Tel", key="td_yeni_sabit")
                _td_email = _tdc3.text_input("Email", key="td_yeni_email")

            st.markdown("**📍 Adres**")
            with st.container(border=True):
                _tda1, _tda2, _tda3 = st.columns(3)
                _td_il_opts = ["-- İl seçilir --"] + sorted(_IL_ILCE_HARITASI.keys())
                _td_il = _tda1.selectbox("İl", _td_il_opts, key="td_yeni_il")
                # İlçe listesi seçilen İl'e göre otomatik doluyor.
                _td_ilce_opts = _IL_ILCE_HARITASI.get(_td_il, []) if _td_il != "-- İl seçilir --" else []
                _td_ilce = _tda2.selectbox("İlçe", (["-- Önce il seç --"] if not _td_ilce_opts else _td_ilce_opts), key="td_yeni_ilce")
                _td_adres = _tda3.text_input("Adres", key="td_yeni_adres")

            st.markdown("**📦 Yük Bilgisi**")
            with st.container(border=True):
                _tdy1, _tdy2, _tdy3 = st.columns(3)
                _td_tur = _tdy1.text_input("Tür", key="td_yeni_tur", placeholder="Koli / Palet / ...")
                _td_adet = _tdy2.number_input("Adet", min_value=0, step=1, key="td_yeni_adet")
                _td_tutar = _kg_tr_parse(_tdy3.text_input("Tutar", value="0", key="td_yeni_tutar", help="Virgülle ondalık yazabilirsin (ör. 3.500,50)"))
                _td_yuk_aciklama = st.text_input("Verdiğimiz Yük Açıklaması", key="td_yeni_yuk")

            if st.button("💾 Tedarikçiyi Kaydet", type="primary", key="td_yeni_kaydet_btn", use_container_width=True):
                if not _td_firma.strip():
                    st.error("⚠️ Firma Adı zorunlu.")
                else:
                    _td_tum_taze = _tedarikci_yukle_ham_guvenli()
                    if _td_tum_taze is _OKUMA_BASARISIZ:
                        st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için kaydedilmedi. Lütfen tekrar dene.")
                    else:
                        _td_tum_taze.append({
                            "tarih": str(_td_tarih), "firma_adi": _tr_buyuk(_td_firma), "yetkili": _tr_buyuk(_td_yetkili),
                            "gsm": _td_gsm, "sabit_tel": _td_sabit, "email": _td_email,
                            "il": (_td_il if _td_il != "-- İl seçilir --" else ""),
                            "ilce": (_td_ilce if _td_ilce != "-- Önce il seç --" else ""),
                            "adres": _tr_buyuk(_td_adres), "yuk_aciklamasi": _tr_buyuk(_td_yuk_aciklama),
                            "tur": _tr_buyuk(_td_tur), "adet": _td_adet, "tutar": _td_tutar, "silindi": False,
                        })
                        _tedarikci_kaydet(_td_tum_taze)
                        st.toast("✅ Tedarikçi eklendi", icon="🚛")
                        st.rerun()

        # ── MANUEL TEK KAYIT DÜZENLEME — "Değişiklikleri Kaydet" (toplu tablo)
        # bazı durumlarda satır eşleşmesi kayabiliyor diye kullanıcı talebiyle
        # eklendi. Burada pozisyona GÜVENİLMİYOR: seçilen kaydın TAM içeriği
        # taze listede birebir aranıp öyle güncelleniyor — sıra/uzunluk arada
        # değişse bile doğru satır bulunur, yanlış satır asla ezilmez.
        if _td_liste_goster:
            with st.expander("✏️ Tedarikçiyi Tek Tek Düzenle (güvenli manuel düzeltme)"):
                st.caption("Tablodaki toplu 'Değişiklikleri Kaydet' yerine, tek bir tedarikçiyi seçip burada güvenle güncelleyebilirsin.")
                _td_secenekler = [f"{i+1}) {t.get('firma_adi','') or '(isimsiz)'} — {t.get('tarih','') or '-'}"
                                   for i, t in enumerate(_td_liste_goster)]
                _td_secili_pos = st.selectbox("Düzenlenecek tedarikçi", list(range(len(_td_secenekler))),
                                               format_func=lambda i: _td_secenekler[i], key="td_duzenle_secim")
                _td_secili_kayit = _td_liste_goster[_td_secili_pos]

                st.markdown("**📋 Firma Bilgileri**")
                with st.container(border=True):
                    _tde1, _tde2, _tde3 = st.columns(3)
                    _tde_firma = _tde1.text_input("Firma Adı", value=_td_secili_kayit.get("firma_adi", ""), key=f"td_duzenle_firma_{_td_secili_pos}")
                    _tde_yetkili = _tde2.text_input("Yetkili", value=_td_secili_kayit.get("yetkili", ""), key=f"td_duzenle_yetkili_{_td_secili_pos}")
                    _tde_tarih = _tde3.text_input("Tarih (YYYY-AA-GG)", value=str(_td_secili_kayit.get("tarih", "") or ""), key=f"td_duzenle_tarih_{_td_secili_pos}")
                    _tde_gsm = _tde1.text_input("GSM", value=_td_secili_kayit.get("gsm", ""), key=f"td_duzenle_gsm_{_td_secili_pos}")
                    _tde_sabit = _tde2.text_input("Sabit Tel", value=_td_secili_kayit.get("sabit_tel", ""), key=f"td_duzenle_sabit_{_td_secili_pos}")
                    _tde_email = _tde3.text_input("Email", value=_td_secili_kayit.get("email", ""), key=f"td_duzenle_email_{_td_secili_pos}")

                st.markdown("**📍 Adres**")
                with st.container(border=True):
                    _tdea1, _tdea2, _tdea3 = st.columns(3)
                    _td_il_opts2 = ["-- İl seçilir --"] + sorted(_IL_ILCE_HARITASI.keys())
                    _tde_il_mevcut = _td_secili_kayit.get("il", "")
                    _tde_il_idx = _td_il_opts2.index(_tde_il_mevcut) if _tde_il_mevcut in _td_il_opts2 else 0
                    _tde_il = _tdea1.selectbox("İl", _td_il_opts2, index=_tde_il_idx, key=f"td_duzenle_il_{_td_secili_pos}")
                    _tde_ilce_opts = _IL_ILCE_HARITASI.get(_tde_il, []) if _tde_il != "-- İl seçilir --" else []
                    _tde_ilce_mevcut = _td_secili_kayit.get("ilce", "")
                    _tde_ilce_liste = (["-- Önce il seç --"] if not _tde_ilce_opts else _tde_ilce_opts)
                    _tde_ilce_idx = _tde_ilce_liste.index(_tde_ilce_mevcut) if _tde_ilce_mevcut in _tde_ilce_liste else 0
                    _tde_ilce = _tdea2.selectbox("İlçe", _tde_ilce_liste, index=_tde_ilce_idx, key=f"td_duzenle_ilce_{_td_secili_pos}")
                    _tde_adres = _tdea3.text_input("Adres", value=_td_secili_kayit.get("adres", ""), key=f"td_duzenle_adres_{_td_secili_pos}")

                st.markdown("**📦 Yük Bilgisi**")
                with st.container(border=True):
                    _tdey1, _tdey2, _tdey3 = st.columns(3)
                    _tde_tur = _tdey1.text_input("Tür", value=_td_secili_kayit.get("tur", ""), key=f"td_duzenle_tur_{_td_secili_pos}")
                    try:
                        _tde_adet_baslangic = int(float(_td_secili_kayit.get("adet", 0) or 0))
                    except Exception:
                        _tde_adet_baslangic = 0
                    _tde_adet = _tdey2.number_input("Adet", min_value=0, step=1, value=_tde_adet_baslangic, key=f"td_duzenle_adet_{_td_secili_pos}")
                    _tde_tutar_str = _tdey3.text_input("Tutar", value=_kg_tr_format(_td_secili_kayit.get("tutar", 0)),
                                                        key=f"td_duzenle_tutar_{_td_secili_pos}", help="Virgülle ondalık yazabilirsin (ör. 3.500,50)")
                    _tde_yuk = st.text_input("Verdiğimiz Yük Açıklaması", value=_td_secili_kayit.get("yuk_aciklamasi", ""), key=f"td_duzenle_yuk_{_td_secili_pos}")

                if st.button("💾 Bu Tedarikçiyi Güncelle", type="primary", key=f"td_duzenle_kaydet_btn_{_td_secili_pos}", use_container_width=True):
                    _td_tam_taze3 = _tedarikci_yukle_ham_guvenli()
                    if _td_tam_taze3 is _OKUMA_BASARISIZ:
                        st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için hiçbir şey kaydedilmedi. Lütfen tekrar dene.")
                    else:
                        # Pozisyona değil, seçim anındaki kaydın TAM İÇERİĞİNE göre
                        # arıyoruz — arada tablo sırası/uzunluğu değişse bile
                        # doğru (ve SADECE doğru) satır güncellenir.
                        _tde_hedef_idx = None
                        for _j, _t in enumerate(_td_tam_taze3):
                            if _t == _td_secili_kayit:
                                _tde_hedef_idx = _j
                                break
                        if _tde_hedef_idx is None:
                            st.error("⚠️ Bu kayıt veritabanında bulunamadı — muhtemelen arada değişti/silindi. Sayfayı yenileyip tekrar dene.")
                        else:
                            _td_tam_taze3[_tde_hedef_idx] = {
                                "tarih": _tde_tarih, "firma_adi": _tr_buyuk(_tde_firma), "yetkili": _tr_buyuk(_tde_yetkili),
                                "gsm": _tde_gsm, "sabit_tel": _tde_sabit, "email": _tde_email,
                                "il": (_tde_il if _tde_il != "-- İl seçilir --" else ""),
                                "ilce": (_tde_ilce if _tde_ilce != "-- Önce il seç --" else ""),
                                "adres": _tr_buyuk(_tde_adres), "yuk_aciklamasi": _tr_buyuk(_tde_yuk),
                                "tur": _tr_buyuk(_tde_tur), "adet": _tde_adet, "tutar": _kg_tr_parse(_tde_tutar_str),
                                "silindi": _td_secili_kayit.get("silindi", False),
                            }
                            _tedarikci_kaydet(_td_tam_taze3)
                            st.toast("✅ Tedarikçi güncellendi", icon="🚛")
                            st.rerun()

    if not _td_liste_goster:
        if _td_silinenler_aktif:
            st.info("💡 Silinmiş tedarikçi yok.")
        else:
            st.info("💡 Henüz kayıtlı tedarikçi yok — yukarıdan ekleyebilirsin.")
    else:
        if _td_silinenler_aktif:
            st.caption(f"🗑️ {len(_td_liste_goster)} silinmiş tedarikçi gösteriliyor. Seçip geri alabilir ya da kalıcı silebilirsin.")
        _TD_SIRA = ["tarih", "firma_adi", "yetkili", "gsm", "sabit_tel", "email", "il", "ilce", "adres",
                    "yuk_aciklamasi", "tur", "adet", "tutar"]
        _TD_ISIM = {"tarih": "Tarih", "firma_adi": "Firma Adı", "yetkili": "Yetkili", "gsm": "GSM", "sabit_tel": "Sabit Tel", "email": "Email",
                    "adres": "Adres", "ilce": "İlçe", "il": "İl", "yuk_aciklamasi": "Verdiğimiz Yük Açıklaması",
                    "tur": "Tür", "adet": "Adet", "tutar": "Tutar"}
        _td_df = pd.DataFrame(_td_liste_goster)
        for _c in _TD_SIRA:
            if _c not in _td_df.columns:
                _td_df[_c] = ""
        _td_df = _td_df[_TD_SIRA].fillna("")
        _td_df.insert(0, "Seç", False)
        _td_df = _td_df.rename(columns=_TD_ISIM)
        _td_df["Tutar"] = _td_df["Tutar"].map(_kg_tr_format)

        # Butonlar tablonun ÜSTÜNDE görünsün diye önce boş bir kutu (container)
        # ayrılıyor, düzenlenen tablo aşağıda oluşuyor, butonlar en son bu
        # kutunun İÇİNE render ediliyor — ama DOM'da (ekranda) yeri en üstte kalıyor.
        _td_btn_kutu = st.container()

        if st.session_state.get("_td_tumu_secili_mod", False):
            _td_df["Seç"] = True
        _td_df = _hic_none_gosterme(_td_df)
        _td_editor_key = f"tedarikci_editor_{st.session_state['_td_editor_versiyon']}"
        # GÖRÜNÜM: yükseklik sabit/küçük bırakılmıyor — kayıt sayısına göre
        # otomatik hesaplanıyor ki hepsi TEK SEFERDE (iç kaydırma olmadan)
        # görünsün. (Kullanıcı isteği: "hepsi görünsün, dar pencere olmasın".)
        _td_satir_yuksekligi = 35
        _td_yukseklik = 38 + _td_satir_yuksekligi * max(len(_td_df), 1) + 3
        _td_duzenlenen = st.data_editor(_td_df, use_container_width=True, hide_index=True, key=_td_editor_key,
                                         height=_td_yukseklik)

        with _td_btn_kutu:
            _tdb1, _tdb2, _tdb3, _tdb4 = st.columns(4)
            with _tdb1:
                if st.button("☑️ Tümünü Seç", key="td_tumunu_sec_btn", use_container_width=True):
                    st.session_state["_td_tumu_secili_mod"] = True
                    st.session_state["_td_editor_versiyon"] += 1
                    st.rerun()
            with _tdb2:
                if st.button("⬜ Seçimi Temizle", key="td_secimi_temizle_btn", use_container_width=True):
                    st.session_state["_td_tumu_secili_mod"] = False
                    st.session_state["_td_editor_versiyon"] += 1
                    st.rerun()
            with _tdb3:
                if not _td_silinenler_aktif:
                    if st.button("💾 Değişiklikleri Kaydet", type="primary", key="td_kaydet_btn", use_container_width=True):
                        _td_ters = {v: k for k, v in _TD_ISIM.items()}
                        # GÜVENLİK: tam listeyi TAZE çek; sadece bu görünümdeki
                        # (aktif/silinmiş) kayıtları güncelle, diğerlerine dokunma.
                        _td_tam_taze = _tedarikci_yukle_ham_guvenli()
                        if _td_tam_taze is _OKUMA_BASARISIZ:
                            st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için hiçbir şey kaydedilmedi. Lütfen tekrar dene.")
                        else:
                            _td_goster_idx = [i for i, t in enumerate(_td_tam_taze) if bool(t.get("silindi")) == _td_silinenler_aktif]
                            if len(_td_goster_idx) != len(_td_duzenlenen):
                                st.error("⚠️ Liste arada değişmiş görünüyor, güvenlik için kaydetmedim — sayfayı yenileyip tekrar dene.")
                            else:
                                for _pos, _i in enumerate(_td_goster_idx):
                                    _r = _td_duzenlenen.iloc[_pos]
                                    _yeni_kayit = {}
                                    for _kol, _val in _r.items():
                                        if _kol == "Seç":
                                            continue
                                        _yeni_kayit[_td_ters.get(_kol, _kol)] = _val
                                    _yeni_kayit["tutar"] = _kg_tr_parse(_yeni_kayit.get("tutar", 0))
                                    _yeni_kayit["silindi"] = _td_tam_taze[_i].get("silindi", False)
                                    _td_tam_taze[_i] = _yeni_kayit
                                _tedarikci_kaydet(_td_tam_taze)
                                st.session_state["_td_tumu_secili_mod"] = False
                                st.session_state["_td_editor_versiyon"] += 1
                                st.toast("✅ Tedarikçiler güncellendi", icon="🚛")
                                st.rerun()
            with _tdb4:
                _td_secili_sayi = int(_td_duzenlenen["Seç"].sum()) if "Seç" in _td_duzenlenen.columns else 0
                _td_buton_metni = f"↩️ Seçilenleri Geri Al ({_td_secili_sayi})" if _td_silinenler_aktif else f"🗑️ Seçili {_td_secili_sayi} Kaydı Sil"
                if st.button(_td_buton_metni, key="td_sil_geri_al_btn", use_container_width=True, disabled=_td_secili_sayi == 0):
                    _td_tam_taze2 = _tedarikci_yukle_ham_guvenli()
                    if _td_tam_taze2 is _OKUMA_BASARISIZ:
                        st.error("⚠️ Veritabanına şu an ulaşılamadı — güvenlik için hiçbir işlem yapılmadı. Lütfen tekrar dene.")
                    else:
                        _td_goster_idx2 = [i for i, t in enumerate(_td_tam_taze2) if bool(t.get("silindi")) == _td_silinenler_aktif]
                        if len(_td_goster_idx2) != len(_td_duzenlenen):
                            st.error("⚠️ Liste arada değişmiş görünüyor, güvenlik için işlemi yapmadım — sayfayı yenileyip tekrar dene.")
                        else:
                            for _pos2, (_, _r2) in enumerate(_td_duzenlenen.iterrows()):
                                if not bool(_r2.get("Seç")):
                                    continue
                                _i2 = _td_goster_idx2[_pos2]
                                _td_tam_taze2[_i2]["silindi"] = not _td_silinenler_aktif
                                if not _td_silinenler_aktif:
                                    _td_tam_taze2[_i2]["silinme_tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                else:
                                    _td_tam_taze2[_i2].pop("silinme_tarihi", None)
                            _tedarikci_kaydet(_td_tam_taze2)
                            st.session_state["_td_tumu_secili_mod"] = False
                            st.session_state["_td_editor_versiyon"] += 1
                            st.toast("✅ İşlem tamamlandı", icon="🚛")
                            st.rerun()

    st.divider()
    _td_silinen_sayi = sum(1 for t in _td_tum if t.get("silindi"))
    _td_silinenler_etiket = f"🗑️ Silinenler ({_td_silinen_sayi})" if not _td_silinenler_aktif else "🗑️ Silinenler — Kapat"
    if st.button(_td_silinenler_etiket, key="td_silinenler_toggle_btn"):
        st.session_state["_td_silinenler_goster"] = not _td_silinenler_aktif
        st.session_state["_td_editor_versiyon"] += 1
        st.rerun()

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='position:fixed;bottom:0;left:0;right:0;background:#f0f2f6;padding:6px;text-align:center;font-size:11px;color:#888;z-index:999;'>"
    "MWCRMPRO v6.7 &nbsp;|&nbsp; "
    "<a href='tel:05400344228' style='color:#888;text-decoration:none;'>📞 5400344228</a>"
    " &nbsp;|&nbsp; "
    "<a href='mailto:osnenufu@gmail.com' style='color:#888;text-decoration:none;'>✉️ osnenufu@gmail.com</a>"
    " &nbsp;|&nbsp; "
    "<span style='color:#9ca3af;'>💬 WhatsApp (devre dışı)</span>"
    "</div>",
    unsafe_allow_html=True
)