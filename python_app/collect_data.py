import requests
import datetime
import json
import os

# --- Configurações ---
WEATHERAPI_API_KEY = os.environ.get('WEATHERAPI_API_KEY', 'SUA_CHAVE_DE_API')
CITY = "Sao Paulo"
OUTPUT_DIR = "data"

# Função para buscar dados na API
def fetch_weather_data(city):
    # URL da API gratuita, que sempre retorna a previsão para os próximos 3 dias
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city}&days=3&aqi=no&alerts=no"
    
    print(f"Fazendo requisição para a API: {url}")
    try:
        response = requests.get(url, timeout=30)
        print(f"Resposta da API - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            forecast_days = data.get('forecast', {}).get('forecastday', [])
            print(f"Dados recebidos com sucesso. Número de dias: {len(forecast_days)}")
            
            # A lógica de conversão dos dados permanece a mesma
            days_data = []
            for day in forecast_days:
                day_data = {
                    'datetime': day.get('date'), 'datetimeEpoch': day.get('date_epoch'), 'tempmax': day.get('day', {}).get('maxtemp_c'),
                    'tempmin': day.get('day', {}).get('mintemp_c'), 'temp': day.get('day', {}).get('avgtemp_c'), 'feelslikemax': day.get('day', {}).get('maxtemp_c'),
                    'feelslikemin': day.get('day', {}).get('mintemp_c'), 'humidity': day.get('day', {}).get('avghumidity'), 'precip': day.get('day', {}).get('totalprecip_mm'),
                    'precipprob': day.get('day', {}).get('daily_chance_of_rain'), 'precipcover': None, 'preciptype': ['rain'] if day.get('day', {}).get('daily_will_it_rain') == 1 else None,
                    'snow': day.get('day', {}).get('totalsnow_cm', 0), 'snowdepth': None, 'windgust': day.get('day', {}).get('maxwind_kph'),
                    'windspeed': day.get('day', {}).get('maxwind_kph'), 'winddir': day.get('day', {}).get('wind_dir'), 'pressure': day.get('day', {}).get('pressure_mb'),
                    'cloudcover': day.get('day', {}).get('avgvis_km'), 'visibility': day.get('day', {}).get('avgvis_km'), 'solarradiation': None, 'solarenergy': None,
                    'uvindex': day.get('day', {}).get('uv'), 'severerisk': None, 'sunrise': day.get('astro', {}).get('sunrise'), 'sunset': day.get('astro', {}).get('sunset'),
                    'moonphase': day.get('astro', {}).get('moon_phase'), 'conditions': day.get('day', {}).get('condition', {}).get('text'),
                    'description': day.get('day', {}).get('condition', {}).get('text'), 'icon': day.get('day', {}).get('condition', {}).get('icon'), 'source': 'WeatherAPI.com'
                }
                days_data.append(day_data)
            return days_data
        else:
            print(f"Erro ao consultar a API: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição à API: {str(e)}")
        return None

# Função para salvar os dados em um arquivo JSON com nome único
def save_to_json(days_data, output_file):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    data_to_save = {
        "id": "weather:SaoPaulo", "type": "Weather",
        "forecast": { "type": "StructuredValue", "value": { "days": days_data } }
    }
    
    with open(output_file, 'w') as f:
        json.dump(data_to_save, f, indent=2)
    
    print(f"Dados salvos com sucesso em {output_file}")

def main():
    print("Iniciando coleta de dados meteorológicos...")
    
    # 1. Busca os dados da API
    days_data = fetch_weather_data(CITY)
    if days_data is None:
        print("Não foi possível coletar os dados climáticos.")
        return
        
    # 2. Gera um nome de arquivo único usando a data e hora atuais
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"{OUTPUT_DIR}/weather_data_{timestamp}.json"
    
    # 3. Salva os dados no arquivo
    save_to_json(days_data, output_file)
    
    print("Processo concluído.")

if __name__ == "__main__":
    main()