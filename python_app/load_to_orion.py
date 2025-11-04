import json
import os
import time
import requests
import sys
import traceback
import glob
import shutil

# Garante que as mensagens sejam exibidas imediatamente no terminal
sys.stdout.reconfigure(line_buffering=True)

print("--- Script de Carregamento Contínuo para Orion Iniciado ---")

# --- Configurações Gerais ---

# Diretório onde o script 'collect_data.py' salva os arquivos JSON
DATA_DIR = "./data"

# Diretório onde os arquivos já processados serão armazenados
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# Endereço padrão do Orion Context Broker
ORION_URL = os.environ.get('ORION_URL', 'http://orion:1026/v2/entities')

# Endpoint usado para verificar se o Orion está ativo
ORION_VERSION_URL = 'http://orion:1026/version'

# Endpoint usado para criar e consultar subscriptions
ORION_SUBSCRIPTION_URL = os.environ.get('ORION_SUBSCRIPTION_URL', 'http://orion:1026/v2/subscriptions')

# ID da entidade que será atualizada continuamente
ENTITY_ID = "weather:SaoPaulo"

# Número máximo de tentativas para aguardar o Orion ficar disponível
MAX_RETRIES = 20

# Tempo (em segundos) entre cada varredura no diretório
SCAN_INTERVAL = 30


def wait_for_orion():
    """Espera até que o Orion Context Broker esteja disponível."""
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
    """Cria uma subscription no Orion para que o Cygnus receba notificações de novas atualizações."""
    print("Verificando se já existe uma subscription para o Cygnus...")

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
                    print("Subscription já existente — nenhuma ação necessária.")
                    return
        print("Criando nova subscription para o Cygnus...")
        headers = {'Content-Type': 'application/json'}
        create_response = requests.post(ORION_SUBSCRIPTION_URL, json=subscription_payload, headers=headers)
        if create_response.status_code == 201:
            print("Subscription criada com sucesso!")
        else:
            print(f"Erro ao criar subscription: {create_response.status_code} - {create_response.text}")
    except Exception as e:
        print(f"Erro ao criar subscription: {e}")
        traceback.print_exc()


def send_to_orion(data):
    """Envia dados atualizados para o Orion. Se a entidade ainda não existir, ela é criada."""
    print(f"Enviando atualização para a entidade {data['id']}...")
    headers = {"Content-Type": "application/json"}

    # Atualiza apenas o atributo 'forecast' da entidade já existente
    patch_url = f"{ORION_URL}/{data['id']}/attrs"
    patch_payload = {"forecast": data["forecast"]}

    try:
        response = requests.patch(patch_url, headers=headers, data=json.dumps(patch_payload))
        # O status 204 indica sucesso na atualização parcial (PATCH)
        if response.status_code == 204:
            print(f"Entidade {data['id']} atualizada com sucesso.")
            return True
        # Caso a entidade ainda não exista, tenta criá-la do zero
        elif response.status_code == 404:
            print(f"Entidade {data['id']} não encontrada. Criando nova...")
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
        print(f"Erro ao enviar dados para o Orion: {e}")
        traceback.print_exc()
        return False


def main():
    """Executa o processo contínuo de leitura e envio de dados JSON ao Orion."""
    if not wait_for_orion():
        sys.exit(1)

    create_subscription()

    # Cria o diretório de arquivos processados, caso não exista
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    print(f"Monitorando o diretório '{DATA_DIR}' em busca de novos arquivos JSON...")

    try:
        while True:
            # Lista todos os arquivos .json no diretório principal
            json_files = glob.glob(os.path.join(DATA_DIR, '*.json'))

            if not json_files:
                print(f"Nenhum arquivo novo encontrado. Aguardando {SCAN_INTERVAL} segundos...")
            else:
                print(f"{len(json_files)} arquivo(s) encontrado(s) para processamento.")
                for file_path in json_files:
                    print(f"\nProcessando arquivo: {os.path.basename(file_path)}")
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)

                        # Tenta enviar os dados para o Orion
                        success = send_to_orion(data)

                        # Se o envio for bem-sucedido, move o arquivo para o diretório de “processados”
                        if success:
                            destination_path = os.path.join(PROCESSED_DIR, os.path.basename(file_path))
                            shutil.move(file_path, destination_path)
                            print(f"Arquivo movido para: {destination_path}")
                        else:
                            print(f"Falha ao processar {os.path.basename(file_path)}. O arquivo será mantido para nova tentativa.")

                    except Exception as e:
                        print(f"Erro ao processar o arquivo {os.path.basename(file_path)}: {e}")
                        traceback.print_exc()

            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print("\nScript encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro inesperado no loop principal: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
