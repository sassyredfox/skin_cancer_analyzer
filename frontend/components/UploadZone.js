"use client";
import { useRef, useState } from "react";
import styles from "./UploadZone.module.css";

export default function UploadZone({ onFile, preview, loading, onReset }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    var f = e.dataTransfer.files[0];
    if (f && f.type.startsWith("image/")) onFile(f);
  }

  function handleChange(e) {
    var f = e.target.files[0];
    if (f) onFile(f);
  }

  if (preview) {
    return (
      <div className={styles.previewWrap}>
        <img src={preview} alt="Uploaded lesion" className={styles.previewImg} />
        <div className={styles.previewOverlay}>
          {loading ? (
            <div className={styles.analyzing}>
              <div className={styles.spinner}></div>
              <span>Analyzing...</span>
            </div>
          ) : (
            <button className={styles.resetBtn} onClick={onReset}>
              Upload another
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={dragging ? styles.zone + " " + styles.dragging : styles.zone}
      onDragOver={function(e) { e.preventDefault(); setDragging(true); }}
      onDragLeave={function() { setDragging(false); }}
      onDrop={handleDrop}
      onClick={function() { inputRef.current && inputRef.current.click(); }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleChange}
        className={styles.hiddenInput}
      />
      <div className={styles.iconWrap}>
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.2">
          <rect x="3" y="6" width="30" height="24" rx="3"/>
          <circle cx="13" cy="16" r="3.5"/>
          <path d="M3 26l8-7 6 5 5-4 11 8"/>
        </svg>
      </div>
      <p className={styles.primary}>
        Drop image here or <strong>browse</strong>
      </p>
      <p className={styles.secondary}>JPG · PNG · WEBP · max 10 MB</p>
      <div className={styles.accepted}>
        <span>Dermoscopic</span>
        <span>Clinical photo</span>
        <span>Macro photo</span>
      </div>
    </div>
  );
}
