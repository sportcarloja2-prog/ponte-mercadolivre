from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLIENT_ID = "1482530022695442"
CLIENT_SECRET = "tm7l1c67Qp7CQzRwDyzs6cabC7GwmeE7"
TOKEN_FILE = "token_atual.txt"

def salvar_refresh_token(novo_token):
    with open(TOKEN_FILE, "w") as f:
        f.write(novo_token)

@app.route('/atualizar_token', methods=['GET'])
def atualizar_token():
    """Rota para ativar o servidor com um código TG- novinho gerado na hora"""
    codigo_tg = request.args.get('code', '')
    if not codigo_tg:
        return jsonify({"error": "Envie o parametro ?code=TG-..."}), 400
        
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": codigo_tg,
        "redirect_uri": "https://www.google.com"
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        data = response.json()
        if "refresh_token" in data:
            salvar_refresh_token(data["refresh_token"])
            return jsonify({"status": "sucesso", "mensagem": "Servidor ativado com sucesso por 6 meses!"})
        else:
            return jsonify({"error": "ML recusou o codigo", "detalhes": data}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/buscar', methods=['GET'])
def buscar():
    termo = request.args.get('q', '')
    if not termo:
        return jsonify({"results": []})
        
    if not os.path.exists(TOKEN_FILE):
        return jsonify({"error": "Servidor nao ativado. Acesse /atualizar_token primeiro."}), 400
        
    with open(TOKEN_FILE, "r") as f:
        current_refresh = f.read().strip()
        
    # Renova o access_token usando o refresh salvo
    url_token = "https://api.mercadolibre.com/oauth/token"
    payload_refresh = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": current_refresh
    }
    
    try:
        res_token = requests.post(url_token, data=payload_refresh, timeout=10)
        data_token = res_token.json()
        
        if "access_token" not in data_token:
            return jsonify({"error": "Refresh token expirado ou invalido", "detalhes": data_token}), 401
            
        access_token = data_token["access_token"]
        if "refresh_token" in data_token:
            salvar_refresh_token(data_token["refresh_token"])
            
        # Faz a busca real
        url_busca = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}"
        headers = {"Authorization": f"Bearer {access_token}"}
        res_busca = requests.get(url_busca, headers=headers, timeout=12)
        return jsonify(res_busca.json())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
