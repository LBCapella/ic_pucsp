import json
import os
import time
import requests
import sys
import traceback
import glob
import shutil

# Configurar saída para não usar buffer
sys.stdout.reconfigure(line_buffering=True)

print("--- Script de Carregamento Contínuo para Orion Iniciado ---")

# --- Configurações ---
# O diretório onde o script `collect_data.py` salva os arquivos
DATA_DIR = "./data"
# O diretório para onde os arquivos processados serão movidos
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

ORION_URL = os.environ.get('ORION_URL', 'http://orion:1026/v2/entities')
ORION_VERSION_URL = 'http://orion:1026/version'
ORION_SUBSCRIPTION_URL = os.environ.get('ORION_SUBSCRIPTION_URL', 'http://orion:1026/v2/subscriptions')
ENTITY_ID = "weather:SaoPaulo"
MAX_RETRIES = 20
# Intervalo em segundos para o script verificar por novos arquivos
SCAN_INTERVAL = 30

def wait_for_orion():
    """Aguarda ativamente o Orion ficar online."""
    print(f"Aguardando o Orion Context Broker em {ORION_VERSION_URL}...")
    for i in range(MAX_RETRIES):
        try:
            response = requests.get(ORION_VERSION_URL, timeout=5)
            if response.status_code == 200:
                print(f"Orion está online! Versão: {response.json().get('orion', {}).get('version')}")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Tentativa {i+1}/{MAX_RETRIES}: Orion ainda não está disponível. Aguardando...")
        time.sleep(10)
    print("ERRO: O Orion não ficou disponível a tempo.")
    return False

def create_subscription():
    """Cria a subscrição para o Cygnus se ela não existir."""
    print("Verificando subscrição para o Cygnus...")
    # Usando o mesmo payload da versão anterior
    subscription_payload = {
        "description": "Subscription para enviar dados ao Cygnus",
        "subject": { "entities": [{"id": ENTITY_ID, "type": "Weather"}] },
        "notification": {
            "http": {"url": "http://cygnus:5055/notify"},
            "attrsFormat": "normalized"
        },
        "expires": "2030-01-01T00:00:00.00Z"
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
    """Envia os dados para o Orion, atualizando a entidade."""
    print(f"Enviando atualização para a entidade {data['id']}...")
    headers = {"Content-Type": "application/json"}
    
    # A entidade já deve existir. Vamos apenas atualizar o atributo 'forecast'.
    # Isso é mais eficiente e garante que a notificação seja disparada.
    patch_url = f"{ORION_URL}/{data['id']}/attrs"
    patch_payload = {"forecast": data["forecast"]}

    try:
        response = requests.patch(patch_url, headers=headers, data=json.dumps(patch_payload))
        # 204 No Content é a resposta de sucesso para um PATCH
        if response.status_code == 204:
            print(f"Entidade {data['id']} atualizada com sucesso no Orion.")
            return True
        # Se a entidade não existir por algum motivo, tentamos criá-la
        elif response.status_code == 404:
            print(f"Entidade {data['id']} não encontrada. Tentando criar...")
            create_response = requests.post(ORION_URL, headers=headers, data=json.dumps(data))
            if create_response.status_code == 201:
                 print(f"Entidade {data['id']} criada com sucesso.")
                 return True
            else:
                print(f"Erro ao criar entidade: {create_response.status_code} - {create_response.text}")
                return False
        else:
            print(f"Erro ao atualizar entidade: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exceção ao enviar dados para o Orion: {e}")
        traceback.print_exc()
        return False

def main():
    """Função principal que roda em loop para processar arquivos."""
    if not wait_for_orion():
        sys.exit(1)

    create_subscription()
    
    # Garante que o diretório de arquivos processados exista
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    print(f"Observando o diretório '{DATA_DIR}' por novos arquivos .json...")

    try:
        while True:
            # Procura por todos os arquivos .json no diretório de dados
            json_files = glob.glob(os.path.join(DATA_DIR, '*.json'))
            
            if not json_files:
                print(f"Nenhum arquivo novo encontrado. Aguardando {SCAN_INTERVAL} segundos...")
            else:
                print(f"Encontrados {len(json_files)} arquivos para processar.")
                for file_path in json_files:
                    print(f"\nProcessando arquivo: {os.path.basename(file_path)}")
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Envia os dados para o Orion
                        success = send_to_orion(data)
                        
                        # Se o envio foi bem-sucedido, move o arquivo
                        if success:
                            destination_path = os.path.join(PROCESSED_DIR, os.path.basename(file_path))
                            shutil.move(file_path, destination_path)
                            print(f"Arquivo movido para: {destination_path}")
                        else:
                            print(f"Falha ao processar o arquivo {os.path.basename(file_path)}. Ele não será movido.")

                    except Exception as e:
                        print(f"Erro ao processar o arquivo {os.path.basename(file_path)}: {e}")
                        traceback.print_exc()
            
            time.sleep(SCAN_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nScript encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro fatal no loop principal: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()