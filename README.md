# Sistema de Coleta e Visualização de Dados Meteorológicos

Este repositório contém um sistema completo para coleta, processamento e visualização de dados meteorológicos utilizando a arquitetura FIWARE.

## Visão Geral

O sistema coleta dados meteorológicos da API WeatherAPI.com, armazena-os em um formato estruturado e os disponibiliza através de uma arquitetura baseada em FIWARE, permitindo a persistência histórica e visualização dos dados.

## Componentes

O sistema é composto pelos seguintes componentes:

- **Orion Context Broker**: Gerencia as entidades e seus atributos no sistema
- **MongoDB**: Banco de dados utilizado pelo Orion para persistência interna
- **Cygnus**: Responsável por captar notificações do Orion e encaminhar para o PostgreSQL
- **PostgreSQL**: Banco de dados onde o Cygnus armazena os dados históricos
- **Grafana**: Ferramenta para visualização e análise dos dados armazenados
- **Aplicação Python**: Scripts para coleta e envio de dados para o Orion

## Estrutura do Repositório

```
.
├── collect_weather_data.sh    # Script para coletar dados meteorológicos
├── docker-compose.yml         # Configuração dos serviços Docker
├── data/                      # Diretório para armazenamento de dados
└── python_app/                # Aplicação Python
    ├── collect_data.py        # Script para coleta de dados da API WeatherAPI
    ├── load_to_orion.py       # Script para envio de dados ao Orion
    ├── weather_data.json      # Dados meteorológicos coletados
    ├── Dockerfile             # Configuração para build da imagem Docker
    └── requirements.txt       # Dependências Python
```

## Como Usar

### Pré-requisitos

- Docker e Docker Compose instalados
- Chave de API da WeatherAPI.com (opcional para coleta de novos dados)

### Coleta de Dados Meteorológicos

Para coletar dados meteorológicos atualizados:

```bash
# Sem chave de API (usando a chave padrão configurada)
./collect_weather_data.sh

# Com chave de API personalizada
./collect_weather_data.sh SUA_CHAVE_API
```

### Iniciar o Sistema

```bash
docker-compose up
```

Este comando iniciará todos os serviços definidos no arquivo docker-compose.yml.

### Acessando os Serviços

- **Orion Context Broker**: http://localhost:1026/v2/entities
- **Grafana**: http://localhost:3000 (usuário: admin, senha: admin)
- **PostgreSQL**: localhost:5432 (usuário: fiware, senha: fiware, banco: fiware)

## Fluxo de Dados

1. O script `collect_data.py` coleta dados meteorológicos da API WeatherAPI.com
2. Os dados são armazenados localmente em `data/weather_data.json`
3. O serviço `python_script` envia os dados para o Orion Context Broker
4. O Orion notifica o Cygnus sobre as atualizações através de uma subscription
5. O Cygnus persiste os dados no PostgreSQL
6. O Grafana é utilizado para visualizar e analisar os dados armazenados

## Personalização

Para personalizar a coleta de dados para outra cidade, modifique a variável `CITY` no arquivo `python_app/collect_data.py`. 