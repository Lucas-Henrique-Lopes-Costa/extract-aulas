#!/bin/bash
# Relança o Chrome com remote debugging habilitado
# IMPORTANTE: Feche o Chrome completamente antes de rodar este script

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE="$HOME/Library/Application Support/Google/Chrome"

echo "🔧 Verificando se o Chrome está fechado..."
if pgrep -x "Google Chrome" > /dev/null; then
    echo "⚠️  Chrome ainda está aberto. Fechando..."
    osascript -e 'quit app "Google Chrome"'
    sleep 2
fi

echo "🚀 Iniciando Chrome com remote debugging na porta 9222..."
echo "   (usando seu perfil existente - você continuará logado)"
echo ""

"$CHROME" \
    --remote-debugging-port=9222 \
    --user-data-dir="$PROFILE" \
    --no-first-run \
    --no-default-browser-check \
    2>/dev/null &

sleep 3

# Verifica se está acessível
if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "✅ Chrome iniciado com sucesso!"
    echo "   Acesse http://localhost:9222 para confirmar"
    echo ""
    echo "👉 Agora rode: python3 extract_iframes.py"
else
    echo "❌ Falha ao iniciar Chrome com debugging"
    echo "   Tente fechar o Chrome manualmente e rodar este script novamente"
fi
