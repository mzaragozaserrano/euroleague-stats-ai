# Archivo: .github/scripts/Enable-Utf8.ps1
# Configura la salida visual de la consola a UTF-8 para evitar "garabatos"

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    # chcp 65001 fuerza la página de códigos UTF-8 en Windows
    chcp 65001 | Out-Null 
} catch {
    # Si falla (ej. en algunos entornos CI), no detenemos la ejecución
    Write-Warning "No se pudo configurar UTF-8 visual. Los acentos en consola pueden verse mal."
}

Write-Host "Consola visual configurada en UTF-8" -ForegroundColor DarkGray