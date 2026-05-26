from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLIENT_ID = "1482530022695442"
CLIENT_SECRET = "tm7l1c67Qp7CQzRwDyzs6cabC7GwmeE7"
TOKEN_FILE = "token_atual.txt"

# Cria o arquivo de token inicial se não existir
if not os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, "w") as f:
        f.write("TG-6a14af90cc4ec7000112a866-162089212")

def gerar_novo_access_token():
    with open(TOKEN_FILE, "r") as f:
        current_refresh = f.read().strip()
    
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": current_refresh
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        data = response.json()
        if "access_token" in data:
            if "refresh_token" in data:
                with open(TOKEN_FILE, "w") as f:
                    f.write(data["refresh_token"])
            return data["access_token"]
    except Exception as e:
        print(f"Erro na renovação: {e}")
    return None

@app.route('/buscar', methods=['GET'])
def buscar():
    termo = request.args.get('q', '')
    if not termo:
        return jsonify({"results": []})
        
    access_token = gerar_novo_access_token()
    if not access_token:
        return jsonify({"error": "Erro de autenticação com o Mercado Livre"}), 500

    url = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=12)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # O Render exige que o app rode na porta definida por eles
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)