import requests
import datetime
import json
import os
import time

# Configurações
WEATHERAPI_API_KEY = os.environ.get('WEATHERAPI_API_KEY', 'SUA_CHAVE_DE_API')
CITY = "Sao Paulo"
OUTPUT_DIR = "data"
OUTPUT_FILE = f"{OUTPUT_DIR}/weather_data.json"

# Função para calcular a data de início (segunda) e fim (domingo) da semana atual
def get_current_week_dates():
    today = datetime.date.today()
    # Monday: hoje - weekday (weekday() retorna 0 para segunda, 6 para domingo)
    start_date = today - datetime.timedelta(days=today.weekday())
    # Sunday: start_date + 6 dias
    end_date = start_date + datetime.timedelta(days=6)
    return start_date, end_date

# Função para buscar dados na API da WeatherAPI.com
def fetch_weather_data(city):
    # WeatherAPI.com fornece previsão para até 3 dias no plano gratuito
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city}&days=3&aqi=no&alerts=no"
    
    print(f"Fazendo requisição para a API: {url}")
    try:
        response = requests.get(url, timeout=30)  # Adicionando timeout de 30 segundos
        print(f"Resposta da API - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            forecast_days = data.get('forecast', {}).get('forecastday', [])
            print(f"Dados recebidos com sucesso. Número de dias: {len(forecast_days)}")
            
            # Converter os dados para um formato compatível com o formato anterior
            days_data = []
            for day in forecast_days:
                date = day.get('date')
                print(f"Processando dados para a data: {date}")
                day_data = {
                    'datetime': date,
                    'datetimeEpoch': day.get('date_epoch'),
                    'tempmax': day.get('day', {}).get('maxtemp_c'),
                    'tempmin': day.get('day', {}).get('mintemp_c'),
                    'temp': day.get('day', {}).get('avgtemp_c'),
                    'feelslikemax': day.get('day', {}).get('maxtemp_c'),  # Aproximado
                    'feelslikemin': day.get('day', {}).get('mintemp_c'),  # Aproximado
                    'humidity': day.get('day', {}).get('avghumidity'),
                    'precip': day.get('day', {}).get('totalprecip_mm'),
                    'precipprob': day.get('day', {}).get('daily_chance_of_rain'),
                    'precipcover': None,  # Não disponível diretamente
                    'preciptype': ['rain'] if day.get('day', {}).get('daily_will_it_rain') == 1 else None,
                    'snow': day.get('day', {}).get('totalsnow_cm', 0),
                    'snowdepth': None,  # Não disponível
                    'windgust': day.get('day', {}).get('maxwind_kph'),
                    'windspeed': day.get('day', {}).get('maxwind_kph'),
                    'winddir': day.get('day', {}).get('wind_dir'),
                    'pressure': day.get('day', {}).get('pressure_mb'),
                    'cloudcover': day.get('day', {}).get('avgvis_km'),  # Aproximado
                    'visibility': day.get('day', {}).get('avgvis_km'),
                    'solarradiation': None,  # Não disponível
                    'solarenergy': None,  # Não disponível
                    'uvindex': day.get('day', {}).get('uv'),
                    'severerisk': None,  # Não disponível
                    'sunrise': day.get('astro', {}).get('sunrise'),
                    'sunset': day.get('astro', {}).get('sunset'),
                    'moonphase': day.get('astro', {}).get('moon_phase'),
                    'conditions': day.get('day', {}).get('condition', {}).get('text'),
                    'description': day.get('day', {}).get('condition', {}).get('text'),
                    'icon': day.get('day', {}).get('condition', {}).get('icon'),
                    'source': 'WeatherAPI.com'
                }
                days_data.append(day_data)
            
            return days_data
        else:
            print(f"Erro ao consultar a API da WeatherAPI.com: {response.status_code}")
            print(f"Resposta completa: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("Timeout ao tentar conectar com a API da WeatherAPI.com")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição à API da WeatherAPI.com: {str(e)}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar dados da API: {str(e)}")
        return None

# Função para salvar os dados em um arquivo JSON
def save_to_json(days_data):
    # Criar diretório se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Diretório '{OUTPUT_DIR}' criado.")
    
    # Formatar os dados para salvar
    data_to_save = {
        "id": "weather:SaoPaulo",
        "type": "Weather",
        "forecast": {
            "type": "StructuredValue",
            "value": {
                "days": days_data
            }
        }
    }
    
    # Salvar no arquivo
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data_to_save, f, indent=2)
    
    print(f"Dados salvos com sucesso em {OUTPUT_FILE}")

def main():
    # 1. Calcula as datas da semana atual
    start_date, end_date = get_current_week_dates()
    print(f"Coletando dados para o período: {start_date} a {end_date}")
    
    # 2. Busca os dados da API da WeatherAPI.com
    days_data = fetch_weather_data(CITY)
    if days_data is None:
        print("Não foi possível coletar os dados climáticos.")
        return
    
    print(f"Foram obtidos dados para {len(days_data)} dias.")
    
    # 3. Salva os dados em um arquivo JSON
    save_to_json(days_data)
    
    print("Processo concluído. Dados meteorológicos salvos localmente.")

if __name__ == "__main__":
    main() 