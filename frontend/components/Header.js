import styles from './Header.module.css';

export default function Header() {
    return ( <
        header className = { styles.header } >
        <
        div className = { styles.logo } >
        <
        span className = { styles.name } > DermAI < /span> <
        span className = { styles.tag } > Research Preview < /span> <
        /div> <
        div className = { styles.meta } >
        <
        span className = { styles.dot } > < /span> <
        span > ResNet18· 7 classes < /span> <
        /div> <
        /header>
    );
}