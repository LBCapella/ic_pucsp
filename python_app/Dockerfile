# Utiliza uma imagem oficial leve do Python
FROM python:3.8-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cria o diretório data com permissões adequadas
RUN mkdir -p /app/data && chmod 777 /app/data

# Copia o restante dos arquivos da aplicação para o container
COPY . .

# Por padrão, executa o script de carregamento
# Pode ser substituído pelo comando no docker-compose
CMD ["python", "load_to_orion.py"]

