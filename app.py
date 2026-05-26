from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLIENT_ID = "1482530022695442"
CLIENT_SECRET = "tm7l1c67Qp7CQzRwDyzs6cabC7GwmeE7"
TOKEN_FILE = "token_atual.txt"

# O truque definitivo: Este é o código master (Refresh Token) válido por 6 meses 
# que o Mercado Livre gerou para nós no início. Vamos gravá-lo direto no servidor.
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
    """Força o servidor a voltar para o token master original de 6 meses"""
    salvar_refresh_token(REFRESH_INICIAL)
    return jsonify({"status": "sucesso", "mensagem": "Token master resetado com sucesso no servidor!"})

@app.route('/buscar', methods=['GET'])
def buscar():
    termo = request.args.get('q', '')
    if not termo:
        return jsonify({"results": []})
        
    current_refresh = obter_refresh_token()
        
    # O Render vai pedir um novo Access Token usando o Refresh salvo em arquivo
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
        
        # Se o token guardado falhar por algum motivo, tentamos usar o master original de emergência
        if "access_token" not in data_token:
            payload_refresh["refresh_token"] = REFRESH_INICIAL
            res_token = requests.post(url_token, data=payload_refresh, timeout=12)
            data_token = res_token.json()
            
        if "access_token" not in data_token:
            return jsonify({"error": "Nao foi possivel autenticar com o ML", "detalhes": data_token}), 401
            
        access_token = data_token["access_token"]
        
        # Se o Mercado Livre devolver um novo refresh_token na rota de rotação, salvamos ele
        if "refresh_token" in data_token:
            salvar_refresh_token(data_token["refresh_token"])
            
        # Faz a busca oficial livre de bloqueios geográficos
        url_busca = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}"
        headers = {"Authorization": f"Bearer {access_token}"}
        res_busca = requests.get(url_busca, headers=headers, timeout=12)
        return jsonify(res_busca.json())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
