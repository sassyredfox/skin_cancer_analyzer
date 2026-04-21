import styles from "./ResultPanel.module.css";

var CLASS_DETAILS = {
    nv: {
        desc: "A common benign mole caused by a cluster of melanocytes. Most are harmless but changes should be monitored.",
        rec: "Annual skin check. Monitor for asymmetry, border changes, or color variation.",
    },
    mel: {
        desc: "A malignant tumor of melanocytes. The most dangerous form of skin cancer - early detection is critical.",
        rec: "Seek immediate evaluation by a dermatologist or oncologist.",
    },
    bkl: {
        desc: "Includes seborrheic keratoses and solar lentigines. Benign skin growths that tend to appear with age.",
        rec: "Routine monitoring. Consult a doctor if appearance changes rapidly.",
    },
    bcc: {
        desc: "Most common skin cancer, arising from basal cells. Rarely metastasizes but can cause significant local damage.",
        rec: "Schedule a dermatology appointment promptly for biopsy and treatment.",
    },
    akiec: {
        desc: "Rough, scaly patches caused by UV exposure. Considered precancerous with potential to progress.",
        rec: "Dermatology referral recommended. Cryotherapy or topical agents may be prescribed.",
    },
    vasc: {
        desc: "Includes hemangiomas and angiokeratomas. Usually benign vascular proliferations of the skin.",
        rec: "Evaluate if the lesion bleeds, grows rapidly, or becomes symptomatic.",
    },
    df: {
        desc: "A common benign fibrous nodule, most often on the legs. Harmless and rarely requires treatment.",
        rec: "No urgent action required. Can be excised for comfort or cosmetic reasons.",
    },
};

var SEV_LABEL = { low: "Likely benign", medium: "Moderate risk", high: "High risk" };
var CLASS_ORDER = ["nv", "mel", "bkl", "bcc", "akiec", "vasc", "df"];

function normalizeScores(allScores, prediction, confidence) {
    var byCode = {};

    if (Array.isArray(allScores)) {
        allScores.forEach(function(item) {
            if (!item || !item.code) return;
            byCode[item.code] = Number(item.confidence) || 0;
        });
    }

    if (prediction && byCode[prediction] === undefined) {
        byCode[prediction] = Number(confidence) || 0;
    }

    return CLASS_ORDER.map(function(code) {
        return {
            code: code,
            confidence: byCode[code] !== undefined ? byCode[code] : 0,
        };
    });
}

function toBarStyle(confidence) {
    var pct = Math.max(0, Math.min(100, (Number(confidence) || 0) * 100));
    return {
        width: pct.toFixed(2) + "%",
        minWidth: pct > 0 ? "2px" : "0",
    };
}

export default function ResultPanel(props) {
    var result = props.result;
    var loading = props.loading;

    if (loading) {
        return ( <
            div className = { styles.skeleton } >
            <
            div className = { styles.skRow + " " + styles.wide } > < /div> <
            div className = { styles.skRow + " " + styles.narrow } > < /div> <
            div className = { styles.skRow + " " + styles.medium } > < /div> <
            div className = { styles.skBar } > < /div> <
            /div>
        );
    }

    if (!result) return null;

    var normalizedScores = normalizeScores(result.all_scores, result.prediction, result.confidence);

    if (result.uncertain) {
        return ( <
            div className = { styles.card } >
            <
            div className = { styles.topRow } >
            <
            span className = { styles.severityBadge + " " + styles.sev_none } > No lesion detected < /span> <
            /div> <
            div className = { styles.diagnosisName + " " + styles.uncertainName } > Unrecognised image < /div> <
            div className = { styles.diagnosisCode } > Confidence too low to classify < /div> <
            p className = { styles.desc } >
            The model could not confidently identify a skin lesion in this image.This may be a healthy skin photo,
            a non - dermoscopic image, or an unclear photo. <
            /p> <
            div className = { styles.rec + " " + styles.rec_none } >
            <
            div className = { styles.recLabel } > What to do </div> <
                p > Try uploading a clearer, closer photo of the lesion.If you have a skin concern, consult a dermatologist directly. < /p> <
                /div> <
                div className = { styles.allScores } >
                <
                div className = { styles.scoresLabel } > Raw scores < /div> {
                    normalizedScores.map(function(s) {
                        return ( <
                            div key = { s.code }
                            className = { styles.scoreRow } >
                            <
                            span className = { styles.scoreCode } > { s.code } < /span> <
                            div className = { styles.scoreTrack } >
                            <
                            div className = { styles.scoreBar }
                            style = { toBarStyle(s.confidence) } > < /div> <
                            /div> <
                            span className = { styles.scorePct } > {
                                (s.confidence * 100).toFixed(1) } % < /span> <
                            /div>
                        );
                    })
                } <
                /div> <
                /div>
        );
    }

    var prediction = result.prediction;
    var name = result.name;
    var confidence = result.confidence;
    var severity = result.severity;
    var benign = result.benign;
    var pct = Math.round(confidence * 100);
    var detail = CLASS_DETAILS[prediction] || { desc: "-", rec: "Consult a dermatologist." };

    return ( <
        div className = { styles.card } >
        <
        div className = { styles.topRow } >
        <
        span className = { styles.severityBadge + " " + styles["sev_" + severity] } > { SEV_LABEL[severity] } < /span> <
        span className = { styles.benigntag } > { benign ? "Benign" : "Potentially malignant" } < /span> <
        /div> <
        div className = { styles.diagnosisName } > { name } < /div> <
        div className = { styles.diagnosisCode } > Code: { prediction.toUpperCase() } < /div> <
        div className = { styles.confWrap } >
        <
        div className = { styles.confLabel } >
        <
        span > Confidence < /span> <
        span className = { styles.confPct } > { pct } % < /span> <
        /div> <
        div className = { styles.confBar } >
        <
        div className = { styles.confFill + " " + styles["fill_" + severity] }
        style = {
            { width: pct + "%" } } > < /div> <
        /div> <
        /div> <
        p className = { styles.desc } > { detail.desc } < /p> <
        div className = { styles.rec + " " + styles["rec_" + severity] } >
        <
        div className = { styles.recLabel } > Clinical note < /div> <
        p > { detail.rec } < /p> <
        /div> <
        div className = { styles.allScores } >
        <
        div className = { styles.scoresLabel } > All class scores < /div> {
            normalizedScores.map(function(s) {
                return ( <
                    div key = { s.code }
                    className = { styles.scoreRow } >
                    <
                    span className = { styles.scoreCode } > { s.code } < /span> <
                    div className = { styles.scoreTrack } >
                    <
                    div className = { s.code === prediction ? styles.scoreBar + " " + styles.scoreBarActive : styles.scoreBar }
                    style = { toBarStyle(s.confidence) } >
                    < /div> <
                    /div> <
                    span className = { styles.scorePct } > {
                        (s.confidence * 100).toFixed(1) } % < /span> <
                    /div>
                );
            })
        } <
        /div> <
        /div>
    );
}