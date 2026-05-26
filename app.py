from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLIENT_ID = "1482530022695442"
CLIENT_SECRET = "tm7l1c67Qp7CQzRwDyzs6cabC7GwmeE7"
TOKEN_FILE = "token_atual.txt"
REFRESH_INICIAL = "TG-6a14af90cc4ec7000112a866-162089212"

if not os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, "w") as f:
        f.write(REFRESH_INICIAL)

def obter_refresh_token():
    with open(TOKEN_FILE, "r") as f:
        return f.read().strip()

def salvar_refresh_token(novo_token):
    with open(TOKEN_FILE, "w") as f:
        f.write(novo_token)

@app.route('/reset', methods=['GET'])
def reset_token():
    url_token = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_INICIAL
    }
    try:
        response = requests.post(url_token, data=payload, timeout=12)
        data = response.json()
        if "access_token" in data:
            if "refresh_token" in data:
                salvar_refresh_token(data["refresh_token"])
            return jsonify({"status": "sucesso", "mensagem": "Token master resetado com sucesso!"})
        return jsonify({"status": "erro", "resposta": data}), 400
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 500

@app.route('/buscar', methods=['GET'])
def buscar():
    termo = request.args.get('q', '')
    if not termo:
        return jsonify({"results": []})
        
    current_refresh = obter_refresh_token()
    url_token = "https://api.mercadolibre.com/oauth/token"
    
    payload_refresh = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": current_refresh
    }
    
    try:
        res_token = requests.post(url_token, data=payload_refresh, timeout=12)
        data_token = res_token.json()
        
        if "access_token" not in data_token:
            payload_refresh["refresh_token"] = REFRESH_INICIAL
            res_token = requests.post(url_token, data=payload_refresh, timeout=12)
            data_token = res_token.json()
            
        if "access_token" not in data_token:
            return jsonify({"error": "Falha na autenticacao", "detalhes": data_token}), 401
            
        access_token = data_token["access_token"]
        if "refresh_token" in data_token:
            salvar_refresh_token(data_token["refresh_token"])
            
        # --- MÁGICA DA GEOLOCALIZAÇÃO ---
        # Forçamos a busca apontando explicitamente o site MLB (Brasil) e injetando headers brasileiros
        url_busca = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "X-Target-Country": "BR",
            "X-Site-Id": "MLB"
        }
        
        res_busca = requests.get(url_busca, headers=headers, timeout=12)
        return jsonify(res_busca.json())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
