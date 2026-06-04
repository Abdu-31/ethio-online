import { useState } from "react";
import { API_BASE, getInitData } from "../App";

const LABELS = {
  en: {
    title: "New Passport Order",
    name: "Full Name", namePh: "As shown on your ID",
    phone: "Phone Number", phonePh: "0911 234 567",
    city: "City", cityPh: "e.g. Addis Ababa, Jimma...",
    type: "Passport Type", newPass: "New Passport", renewal: "Renewal",
    urgency: "Urgency", urgent: "🔴 Urgent (1–3 days)", regular: "🟢 Regular (1–2 weeks)",
    photos: "Document Photos", photoHint: "Tap to upload ID & photos",
    submit: "Submit Order", submitting: "Submitting...",
    successTitle: "Order Submitted!",
    successSub: "Our team will contact you within a few hours.",
    orderId: "Order ID",
    newOrder: "Place Another Order",
  },
  am: {
    title: "አዲስ የፓስፖርት ትዕዛዝ",
    name: "ሙሉ ስም", namePh: "በመታወቂያ ላይ እንዳለ",
    phone: "ስልክ ቁጥር", phonePh: "0911 234 567",
    city: "ከተማ", cityPh: "ለምሳሌ አዲስ አበባ፣ ጅማ...",
    type: "የፓስፖርት አይነት", newPass: "አዲስ ፓስፖርት", renewal: "ታደሰ",
    urgency: "አስቸኳይነት", urgent: "🔴 አስቸኳይ (1–3 ቀናት)", regular: "🟢 መደበኛ (1–2 ሳምንት)",
    photos: "የሰነድ ፎቶዎች", photoHint: "ፎቶ ለመጫን ይጫኑ",
    submit: "ትዕዛዝ ላክ", submitting: "እየተላከ ነው...",
    successTitle: "ትዕዛዝ ተልኳል!",
    successSub: "ቡድናችን በጥቂት ሰዓታት ውስጥ ያገኝዎታል።",
    orderId: "የትዕዛዝ መለያ",
    newOrder: "ሌላ ትዕዛዝ ስጥ",
  },
  om: {
    title: "Ajaja Paaspoortii Haaraa",
    name: "Maqaa Guutuu", namePh: "ID irratti akka jirutti",
    phone: "Lakkoofsa Bilbilaa", phonePh: "0911 234 567",
    city: "Magaalaa", cityPh: "fkn. Finfinnee, Jimmaa...",
    type: "Gosa Paaspoortii", newPass: "Paaspoortii Haaraa", renewal: "Haaromsa",
    urgency: "Ariifachisummaa", urgent: "🔴 Ariifachiisaa (guyyaa 1–3)", regular: "🟢 Idilee (torbee 1–2)",
    photos: "Suuraa Sanadeewwanii", photoHint: "Suuraa fe'uuf tuqi",
    submit: "Ajaja Ergi", submitting: "Ergamaa jira...",
    successTitle: "Ajajni Ergame!",
    successSub: "Gareen keenya sa'aatii muraasa keessatti si quunnamti.",
    orderId: "ID Ajajaa",
    newOrder: "Ajaja Biraa Kennii",
  },
};

export default function OrderForm({ tgUser }) {
  const [lang, setLang] = useState("en");
  const L = LABELS[lang];

  const [form, setForm] = useState({
    name: tgUser ? `${tgUser.first_name || ""} ${tgUser.last_name || ""}`.trim() : "",
    phone: "",
    city: "",
    passport_type: "New Passport",
    urgency: "Regular (1–2 weeks)",
  });
  const [photoFiles, setPhotoFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handlePhotos = (e) => {
    const files = Array.from(e.target.files);
    setPhotoFiles(prev => [...prev, ...files].slice(0, 6));
  };

  const handleSubmit = async () => {
    if (!form.name || !form.phone || !form.city) {
      setError("Please fill in all required fields.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-init-data": getInitData() || "dev_mode",
        },
        body: JSON.stringify({
          ...form,
          lang,
          photos: photoFiles.map(f => f.name),
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setSuccess(data);
      // Telegram haptic feedback
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred("success");
    } catch (e) {
      setError("Failed to submit. Please try again.");
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred("error");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="success-screen">
        <div className="success-icon">✅</div>
        <div className="success-title">{L.successTitle}</div>
        <div className="success-sub">{L.successSub}</div>
        <div className="success-order-id">{L.orderId}: #{success.order_id}</div>
        <button className="btn btn-ghost" style={{marginTop:8, width:"auto", padding:"10px 24px"}}
          onClick={() => { setSuccess(null); setForm({ name:"", phone:"", city:"", passport_type:"New Passport", urgency:"Regular (1–2 weeks)" }); setPhotoFiles([]); }}>
          {L.newOrder}
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Language selector */}
      <div className="lang-row">
        {["en","am","om"].map(l => (
          <button key={l} className={`lang-btn ${lang===l?"active":""}`} onClick={() => setLang(l)}>
            {l==="en"?"🇬🇧 EN" : l==="am"?"🇪🇹 አማ" : "OM"}
          </button>
        ))}
      </div>

      <div className="section-title">{L.title}</div>

      {error && <div className="error-msg">{error}</div>}

      <div className="card">
        <div className="form-group">
          <label className="form-label">{L.name}</label>
          <input className="form-input" placeholder={L.namePh}
            value={form.name} onChange={e => set("name", e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">{L.phone}</label>
          <input className="form-input" placeholder={L.phonePh} type="tel"
            value={form.phone} onChange={e => set("phone", e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">{L.city}</label>
          <input className="form-input" placeholder={L.cityPh}
            value={form.city} onChange={e => set("city", e.target.value)} />
        </div>
      </div>

      <div className="card">
        <div className="form-group">
          <label className="form-label">{L.type}</label>
          <div className="segment">
            <button className={`segment-btn ${form.passport_type==="New Passport"?"active":""}`}
              onClick={() => set("passport_type","New Passport")}>{L.newPass}</button>
            <button className={`segment-btn ${form.passport_type==="Renewal"?"active":""}`}
              onClick={() => set("passport_type","Renewal")}>{L.renewal}</button>
          </div>
        </div>
        <div className="form-group" style={{marginBottom:0}}>
          <label className="form-label">{L.urgency}</label>
          <div className="segment">
            <button className={`segment-btn ${form.urgency.startsWith("Urgent")?"active":""}`}
              onClick={() => set("urgency","Urgent (1–3 days)")}>{L.urgent}</button>
            <button className={`segment-btn ${form.urgency.startsWith("Regular")?"active":""}`}
              onClick={() => set("urgency","Regular (1–2 weeks)")}>{L.regular}</button>
          </div>
        </div>
      </div>

      <div className="card">
        <label className="form-label">{L.photos}</label>
        <label htmlFor="photo-upload">
          <div className="photo-upload-area">
            <div className="photo-upload-icon">📎</div>
            <div className="photo-upload-text">{L.photoHint}</div>
            {photoFiles.length > 0 && (
              <div className="photo-count">{photoFiles.length} file(s) selected</div>
            )}
          </div>
        </label>
        <input id="photo-upload" type="file" multiple accept="image/*,.pdf"
          onChange={handlePhotos} />
      </div>

      <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
        {loading ? L.submitting : L.submit}
      </button>
    </div>
  );
}
