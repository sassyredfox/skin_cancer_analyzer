import './globals.css';

export const metadata = {
  title: 'DermAI — Skin Lesion Analysis',
  description: 'AI-powered skin lesion classification using CNN trained on HAM10000',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
