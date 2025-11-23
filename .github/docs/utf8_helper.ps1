# Helper function para convertir strings con caracteres especiales a codigos Unicode
# Uso: Get-UnicodeSafeString "Anadir documentacion"
# Retorna: String con caracteres especiales convertidos a codigos Unicode

function Get-UnicodeSafeString {
    param(
        [string]$InputString
    )
    
    # Mapa de caracteres especiales a codigos Unicode
    # Usamos codigos Unicode directamente para evitar problemas de codificacion del archivo
    $unicodeMap = @{
        [char]0x00F1 = [char]0x00F1  # n
        [char]0x00F3 = [char]0x00F3  # o
        [char]0x00E1 = [char]0x00E1  # a
        [char]0x00E9 = [char]0x00E9  # e
        [char]0x00ED = [char]0x00ED  # i
        [char]0x00FA = [char]0x00FA  # u
        [char]0x00FC = [char]0x00FC  # u con dieresis
        [char]0x00D1 = [char]0x00D1  # N
        [char]0x00D3 = [char]0x00D3  # O
        [char]0x00C1 = [char]0x00C1  # A
        [char]0x00C9 = [char]0x00C9  # E
        [char]0x00CD = [char]0x00CD  # I
        [char]0x00DA = [char]0x00DA  # U
        [char]0x00DC = [char]0x00DC  # U con dieresis
    }
    
    $result = ""
    
    foreach ($char in $InputString.ToCharArray()) {
        if ($unicodeMap.ContainsKey($char)) {
            $result += $unicodeMap[$char]
        } else {
            $result += $char
        }
    }
    
    return $result
}
