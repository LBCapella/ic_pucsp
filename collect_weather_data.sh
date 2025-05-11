#!/bin/bash

# Verifica se o diretório data existe, se não, cria
mkdir -p data

# Define a chave da API (pode ser passada como parâmetro ou usar o valor padrão)
API_KEY=${1:-"SUA_CHAVE_DE_API"}

# Executa o script Python para coletar dados
echo "Coletando dados meteorológicos da API WeatherAPI..."
WEATHERAPI_API_KEY=$API_KEY python python_app/collect_data.py

echo "Dados coletados e salvos em data/weather_data.json"
echo "Para iniciar o sistema FIWARE sem chamar a API novamente, execute:"
echo "docker-compose up" 