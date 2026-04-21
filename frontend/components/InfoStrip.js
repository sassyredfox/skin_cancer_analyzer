import styles from "./InfoStrip.module.css";

var CLASSES = [
  { code: "nv",    name: "Melanocytic Nevus",    risk: "low" },
  { code: "mel",   name: "Melanoma",             risk: "high" },
  { code: "bkl",   name: "Benign Keratosis",     risk: "low" },
  { code: "bcc",   name: "Basal Cell Carcinoma", risk: "high" },
  { code: "akiec", name: "Actinic Keratosis",    risk: "medium" },
  { code: "vasc",  name: "Vascular Lesion",      risk: "low" },
  { code: "df",    name: "Dermatofibroma",       risk: "low" },
];

export default function InfoStrip() {
  return (
    <div className={styles.wrap}>
      <div className={styles.label}>Detectable conditions</div>
      {CLASSES.map(function(c) {
        return (
          <div key={c.code} className={styles.row}>
            <span className={styles.dot + " " + styles["dot_" + c.risk]}></span>
            <span className={styles.code}>{c.code}</span>
            <span className={styles.name}>{c.name}</span>
          </div>
        );
      })}
    </div>
  );
}
