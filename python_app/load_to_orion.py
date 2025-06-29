import json
import os
import time
import requests
import sys
import traceback

# Configurar saída para não usar buffer
sys.stdout.reconfigure(line_buffering=True)

print("Script iniciado!")

# --- Configurações ---
DATA_FILE = "weather_data.json"  # Como solicitado, assumindo que o arquivo está acessível
ORION_URL = os.environ.get('ORION_URL', 'http://orion:1026/v2/entities')
ORION_VERSION_URL = 'http://orion:1026/version' # Endpoint para checagem de saúde
ORION_SUBSCRIPTION_URL = os.environ.get('ORION_SUBSCRIPTION_URL', 'http://orion:1026/v2/subscriptions')
ENTITY_ID = "weather:SaoPaulo"
MAX_RETRIES = 20
RETRY_INTERVAL = 10  # segundos

# --- NOVA FUNÇÃO DE ESPERA ---
def wait_for_orion():
    """Aguarda ativamente o Orion ficar online e pronto para receber requisições."""
    print(f"Aguardando o Orion Context Broker em {ORION_VERSION_URL}...")
    for i in range(MAX_RETRIES):
        try:
            response = requests.get(ORION_VERSION_URL, timeout=5)
            if response.status_code == 200:
                print(f"Orion está online! Versão: {response.json().get('orion', {}).get('version')}")
                return True
        except requests.exceptions.RequestException:
            pass # Ignora erros de conexão enquanto espera
        
        print(f"Tentativa {i+1}/{MAX_RETRIES}: Orion ainda não está disponível. Aguardando {RETRY_INTERVAL}s...")
        time.sleep(RETRY_INTERVAL)
        
    print("ERRO: O Orion não ficou disponível a tempo. Encerrando script.")
    return False

def create_subscription():
    """Cria a subscrição para o Cygnus se ela não existir."""
    print("Verificando subscrição para o Cygnus...")
    subscription_payload = {
        "description": "Subscription para enviar dados ao Cygnus",
        "subject": {
            "entities": [{"id": ENTITY_ID, "type": "Weather"}],
            "condition": {"attrs": ["forecast"]}
        },
        "notification": {
            "http": {"url": "http://cygnus:5055/notify"},
            "attrsFormat": "normalized"
        },
        "expires": "2030-01-01T00:00:00.00Z",
        "throttling": 5
    }
    try:
        response = requests.get(ORION_SUBSCRIPTION_URL)
        if response.status_code == 200:
            for sub in response.json():
                if sub.get("description") == subscription_payload["description"]:
                    print("Subscrição para o Cygnus já existe.")
                    return

        print("Criando nova subscrição para o Cygnus...")
        headers = {'Content-Type': 'application/json'}
        create_response = requests.post(ORION_SUBSCRIPTION_URL, json=subscription_payload, headers=headers)
        if create_response.status_code == 201:
            print("Subscrição criada com sucesso!")
        else:
            print(f"Erro ao criar subscrição: {create_response.status_code} - {create_response.text}")
    except Exception as e:
        print(f"Exceção ao criar subscrição: {e}")
        traceback.print_exc()

def send_to_orion(data):
    """Envia os dados para o Orion, criando ou atualizando a entidade."""
    print("Enviando dados para o Orion...")
    headers = {"Content-Type": "application/json"}
    # Usando o método PATCH que cria a entidade se ela não existir (upsert)
    # Requer o header `?options=keyValues` para simplificar o payload
    entity_url = f"{ORION_URL}?options=upsert"
    
    # Payload para upsert é o corpo da entidade
    patch_payload = {
        "id": data["id"],
        "type": data["type"],
        "forecast": data["forecast"]
    }

    try:
        response = requests.post(entity_url, headers=headers, data=json.dumps(patch_payload))
        if response.status_code in [201, 204]: # 201 (Created) ou 204 (No Content/Updated)
             print("Entidade criada/atualizada com sucesso no Orion.")
        else:
            print(f"Erro ao enviar dados para o Orion: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exceção ao enviar dados para o Orion: {e}")
        traceback.print_exc()

def main():
    # 1. Aguarda a inicialização do Orion de forma robusta
    if not wait_for_orion():
        sys.exit(1) # Encerra o script se o Orion não responder

    # 2. Carrega os dados (assumindo que o arquivo está no lugar certo)
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        print("Dados carregados com sucesso do arquivo.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{DATA_FILE}' não encontrado. Encerrando.")
        sys.exit(1)
        
    # 3. Garante que a subscrição exista ANTES de enviar os dados
    create_subscription()
    
    # 4. Envia os dados para o Orion
    send_to_orion(data)
    
    print("\nProcesso concluído. O sistema está em execução e a notificação foi enviada.")
    print("Mantendo o contêiner em execução para facilitar o debug.")
    # Mantém o container rodando para que você possa inspecionar os logs
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()