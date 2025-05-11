import json
import os
import time
import requests
import sys
import traceback

# Configurar saída para não usar buffer
sys.stdout.reconfigure(line_buffering=True)

print("Script iniciado!")

# Configurações
DATA_FILE = "weather_data.json"  # Arquivo no diretório atual
ORION_URL = os.environ.get('ORION_URL', 'http://orion:1026/v2/entities')
ORION_SUBSCRIPTION_URL = os.environ.get('ORION_SUBSCRIPTION_URL', 'http://orion:1026/v2/subscriptions')
ENTITY_ID = "weather:SaoPaulo"  # ID da entidade no Orion
MAX_RETRIES = 10
RETRY_INTERVAL = 10  # segundos

print(f"Configurações carregadas: DATA_FILE={DATA_FILE}, ORION_URL={ORION_URL}")

# Função para criar a subscription no Orion
def create_subscription():
    print("Iniciando criação de subscription...")
    subscription_payload = {
        "description": "Subscription para enviar dados ao Cygnus",
        "subject": {
            "entities": [{"id": ENTITY_ID, "type": "Weather"}],
            "condition": {"attrs": ["forecast"]}
        },
        "notification": {
            "http": {"url": "http://cygnus:5055/notify"},
            "attrs": ["forecast"]
        },
        "expires": "2030-01-01T00:00:00.00Z",
        "throttling": 5
    }
    try:
        # Verifica subscriptions existentes
        print("Verificando subscriptions existentes...")
        response = requests.get(ORION_SUBSCRIPTION_URL)
        print(f"Resposta da verificação: {response.status_code}")
        if response.status_code == 200:
            existing_subscriptions = response.json()
            # Verifica se já existe uma subscription com a mesma descrição
            if any(sub.get("description") == "Subscription para enviar dados ao Cygnus" for sub in existing_subscriptions):
                print("Subscription já existe!")
                return
        # Cria a subscription
        print("Criando nova subscription...")
        create_response = requests.post(ORION_SUBSCRIPTION_URL, json=subscription_payload)
        if create_response.status_code in [200, 201]:
            print("Subscription criada com sucesso!")
        else:
            print(f"Erro ao criar subscription: {create_response.status_code} - {create_response.text}")
    except Exception as e:
        print(f"Exceção ao criar subscription: {str(e)}")
        print(traceback.format_exc())

# Função para enviar os dados para o Orion Context Broker
def send_to_orion(data):
    print("Enviando dados para o Orion...")
    headers = {"Content-Type": "application/json"}
    
    # Tenta criar a entidade via POST
    try:
        print(f"Enviando POST para {ORION_URL}")
        response = requests.post(ORION_URL, headers=headers, data=json.dumps(data))
        print(f"Resposta do POST: {response.status_code}")
        
        if response.status_code == 201:
            print("Entidade criada com sucesso no Orion.")
        elif response.status_code == 409:
            # Caso a entidade já exista, atualiza o atributo 'forecast' usando PATCH
            patch_url = f"{ORION_URL}/{data['id']}/attrs"
            patch_payload = {
                "forecast": data["forecast"]
            }
            print(f"Entidade já existe. Enviando PATCH para {patch_url}")
            patch_response = requests.patch(patch_url, headers=headers, data=json.dumps(patch_payload))
            print(f"Resposta do PATCH: {patch_response.status_code}")
            if patch_response.status_code in [204, 201]:
                print("Entidade atualizada com sucesso no Orion.")
            else:
                print(f"Erro ao atualizar a entidade: {patch_response.status_code} - {patch_response.text}")
        else:
            print(f"Erro ao criar a entidade: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exceção ao enviar dados para o Orion: {str(e)}")
        print(traceback.format_exc())

def load_data_file():
    print(f"Tentando carregar arquivo de dados: {DATA_FILE}")
    retries = 0
    while retries < MAX_RETRIES:
        print(f"Tentativa {retries+1}/{MAX_RETRIES} de carregar o arquivo {DATA_FILE}")
        
        # Verifica se o arquivo de dados existe
        if os.path.exists(DATA_FILE):
            print(f"Arquivo {DATA_FILE} encontrado!")
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                print("Dados carregados com sucesso do arquivo.")
                return data
            except Exception as e:
                print(f"Erro ao carregar dados do arquivo: {str(e)}")
                print(traceback.format_exc())
        else:
            print(f"Arquivo {DATA_FILE} não encontrado.")
            
            # Tentar outros caminhos possíveis
            alternative_paths = [
                "/app/data/weather_data.json",
                "./data/weather_data.json",
                "../data/weather_data.json",
                "/data/weather_data.json"
            ]
            
            for path in alternative_paths:
                if path != DATA_FILE and os.path.exists(path):
                    print(f"Arquivo encontrado em caminho alternativo: {path}")
                    try:
                        with open(path, 'r') as f:
                            data = json.load(f)
                        print(f"Dados carregados com sucesso do arquivo {path}.")
                        return data
                    except Exception as e:
                        print(f"Erro ao carregar dados do arquivo {path}: {str(e)}")
            
            # Listar diretório atual para debug
            try:
                print("Diretório atual:")
                print(os.getcwd())
                print("Conteúdo do diretório atual:")
                print(os.listdir("."))
            except Exception as e:
                print(f"Erro ao listar diretório atual: {str(e)}")
                print(traceback.format_exc())
        
        retries += 1
        
        # Aguarda antes de tentar novamente
        if retries < MAX_RETRIES:
            print(f"Aguardando {RETRY_INTERVAL} segundos antes de tentar novamente...")
            sys.stdout.flush()  # Força a saída do buffer
            time.sleep(RETRY_INTERVAL)
    
    print(f"Falha ao carregar o arquivo após {MAX_RETRIES} tentativas.")
    return None

def main():
    try:
        # Aguarda a inicialização dos demais serviços
        print("Aguardando inicialização dos serviços...")
        sys.stdout.flush()  # Força a saída do buffer
        time.sleep(15)
        
        # Carrega os dados do arquivo JSON
        data = load_data_file()
        if data is None:
            print("Não foi possível carregar os dados. Encerrando.")
            return
        
        # Envia os dados para o Orion Context Broker
        send_to_orion(data)
        
        # Cria a subscription para o Cygnus
        print("Criando subscription para o Cygnus...")
        create_subscription()
        
        print("Processo concluído. Dados meteorológicos enviados e subscription configurada.")
        
        # Mantém o container em execução
        print("Mantendo o container em execução. Pressione Ctrl+C para encerrar.")
        sys.stdout.flush()  # Força a saída do buffer
        try:
            while True:
                print("Container em execução... (log a cada minuto)")
                sys.stdout.flush()  # Força a saída do buffer
                time.sleep(60)
        except KeyboardInterrupt:
            print("Container encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro não tratado: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 