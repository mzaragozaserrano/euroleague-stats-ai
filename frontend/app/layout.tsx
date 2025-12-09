import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { BackupSystemInit } from '@/components/BackupSystemInit'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Euroleague AI Stats',
  description: 'Consulta estadísticas de la Euroliga con lenguaje natural',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <BackupSystemInit />
        {children}
      </body>
    </html>
  )
}


