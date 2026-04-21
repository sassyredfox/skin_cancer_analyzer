import styles from "./Disclaimer.module.css";

export default function Disclaimer() {
    return ( <
        div className = { styles.wrap } >
        <
        svg width = "14"
        height = "14"
        viewBox = "0 0 24 24"
        fill = "none"
        stroke = "currentColor"
        strokeWidth = "2"
        className = { styles.icon } >
        <
        path d = "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" / >
        <
        line x1 = "12"
        y1 = "9"
        x2 = "12"
        y2 = "13" / >
        <
        line x1 = "12"
        y1 = "17"
        x2 = "12.01"
        y2 = "17" / >
        <
        /svg> <
        p className = { styles.text } >
        <
        span className = { styles.strong } > Not a medical diagnosis. < /span> DermAI is an experimental research tool and should not be used as a substitute for professional dermatological assessment. Always consult a qualified physician for any skin concerns. <
        /p> <
        /div>
    );
}