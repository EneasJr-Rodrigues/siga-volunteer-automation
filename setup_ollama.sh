#!/bin/bash

# Script de Instalação Automatizada do Ollama para Git Bash / Linux
echo "=== Iniciando a instalação do Ollama ==="

# 1. Verifica se o curl está instalado
if ! command -v curl &> /dev/null; then
    echo "Erro: O 'curl' é necessário para baixar o instalador."
    exit 1
fi

# 2. Instala o Ollama usando o script oficial do projeto
echo "Baixando e instalando o Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# 3. Configura a variável de ambiente OLLAMA_HOST para escutar na rede local (0.0.0.0)
# Isso permite que o seu Mac na rede envie imagens para processar na GPU do Desktop
echo "Configurando o OLLAMA_HOST para escutar na rede local..."

# Adiciona a variável no perfil do Bash caso já não exista
if ! grep -q "OLLAMA_HOST" ~/.bashrc; then
    echo 'export OLLAMA_HOST="0.0.0.0"' >> ~/.bashrc
fi

export OLLAMA_HOST="0.0.0.0"

# 4. Inicia o servidor Ollama em segundo plano (se já não estiver rodando)
if pgrep -x "ollama" > /dev/null; then
    echo "O Ollama já está rodando em segundo plano."
else
    echo "Iniciando o servidor Ollama..."
    ollama serve &
    sleep 3
fi

# 5. Baixa o modelo multimodal recomendado para visão
echo "Baixando o modelo multimodal gemma3:4b..."
ollama pull gemma3:4b

echo "=== Ollama instalado e configurado com sucesso! ==="