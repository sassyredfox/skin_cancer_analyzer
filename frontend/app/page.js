"use client";
import { useState } from "react";
import Header from "../components/Header";
import UploadZone from "../components/UploadZone";
import ResultPanel from "../components/ResultPanel";
import InfoStrip from "../components/InfoStrip";
import Disclaimer from "../components/Disclaimer";
import styles from "./page.module.css";

export default function Home() {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [preview, setPreview] = useState(null);
    const statusLabel = loading ? "Analyzing" : result ? "Ready" : "Awaiting upload";
    const topConfidence = result && !result.uncertain ? Math.round((result.confidence || 0) * 100) : null;

    async function handleUpload(file) {
        setLoading(true);
        setError(null);
        setResult(null);
        const formData = new FormData();
        formData.append("file", file);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const res = await fetch(apiUrl + "/analyze", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Server error");
            }
            const data = await res.json();
            setResult(data);
        } catch (e) {
            setError(e.message || "Failed to connect to API.");
        } finally {
            setLoading(false);
        }
    }

    function handleFile(file) {
        const reader = new FileReader();
        reader.onload = function(e) { setPreview(e.target.result); };
        reader.readAsDataURL(file);
        handleUpload(file);
    }

    function reset() {
        setResult(null);
        setError(null);
        setPreview(null);
    }

    return ( <
        div className = { styles.page } >
        <
        Header / >
        <
        main className = { styles.main } >
        <
        div className = { styles.heroRow } >
        <
        section className = { styles.hero } >
        <
        h1 className = { styles.title } >
        Dermoscopic < br / >
        <
        em > lesion analysis < /em> <
        /h1> <
        p className = { styles.subtitle } >
        Upload a skin image
        for instant AI classification across seven diagnostic categories. <
        /p> <
        /section> <
        aside className = { styles.heroMeta } >
        <
        div className = { styles.metaLabel } > Session snapshot < /div> <
        div className = { styles.metaGrid } >
        <
        div className = { styles.metaItem } >
        <
        span > Classes < /span> <
        strong > 7 types < /strong> <
        /div> <
        div className = { styles.metaItem } >
        <
        span > Status < /span> <
        strong > { statusLabel } < /strong> <
        /div> <
        div className = { styles.metaItem } >
        <
        span > Top confidence < /span> <
        strong > { topConfidence !== null ? topConfidence + "%" : "--" } < /strong> <
        /div> <
        div className = { styles.metaItem } >
        <
        span > Mode < /span> <
        strong > Research preview < /strong> <
        /div> <
        /div> <
        div className = { styles.captureHint } >
        <
        h3 > Capture tips < /h3> <
        p > Keep lesion centered, use even lighting, and avoid blur
        for a stronger result. < /p> <
        /div> <
        /aside> <
        /div> <
        div className = { styles.workspace } >
        <
        div className = { styles.left } >
        <
        UploadZone onFile = { handleFile }
        preview = { preview }
        loading = { loading }
        onReset = { reset }
        /> <
        /div> <
        div className = { styles.right } > {
            error && ( <
                div className = { styles.errorBox } >
                <
                span > ⚠ < /span> { error } <
                /div>
            )
        } {
            (result || loading) && ( <
                ResultPanel result = { result }
                loading = { loading }
                />
            )
        } {
            !result && !loading && !error && ( <
                InfoStrip / >
            )
        } <
        /div> <
        /div> <
        section className = { styles.supportBand } >
        <
        article className = { styles.supportCard } >
        <
        h3 > Confidence guide < /h3> <
        p >
        Confidence reflects model preference between classes.Higher values are stronger signals,
        while lower values should be treated as screening cues. <
        /p> <
        /article> <
        article className = { styles.supportCard } >
        <
        h3 > Dataset coverage < /h3> <
        p >
        This demo classifies across seven HAM10000 lesion categories and is intended
        for research and educational presentation workflows. <
        /p> <
        /article> <
        article className = { styles.supportCard } >
        <
        h3 > Presentation flow < /h3> <
        p >
        Upload image, review top prediction and all class bars, then explain that results are assistive and must be confirmed clinically. <
        /p> <
        /article> <
        /section> <
        Disclaimer / >
        <
        /main> <
        footer className = { styles.footer } >
        <
        span > DermAI· Research use only· HAM10000 dataset < /span> <
        span > Not a substitute
        for medical advice < /span> <
        /footer> <
        /div>
    );
}