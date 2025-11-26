import os
import subprocess
from flask import Flask, request, jsonify, abort, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='templates')

CORS(app)

# Caminho para o arquivo de bloqueio que o Squid lê
BLOCKLIST_FILE = "/etc/squid/blocked_sites.txt"

def read_blocklist():
    """Lê a lista de domínios do arquivo."""
    if not os.path.exists(BLOCKLIST_FILE):
        return set()
    with open(BLOCKLIST_FILE, 'r') as f:
        # Usamos um 'set' para evitar duplicatas facilmente
        return set(line.strip() for line in f if line.strip())

def write_blocklist(domains):
    """Escreve a lista de domínios no arquivo."""
    try:
        with open(BLOCKLIST_FILE, 'w') as f:
            for domain in sorted(list(domains)):
                f.write(domain + '\n')
        return True
    except IOError as e:
        print(f"Erro ao escrever no arquivo: {e}")
        return False

def reload_squid():
    """Sinaliza ao Squid para recarregar a configuração."""
    try:
        # ATENÇÃO: Isso requer permissões de sudo. Veja a nota abaixo.
        # Um método mais seguro é configurar o 'sudo' para permitir
        # que este usuário específico rode APENAS este comando sem senha.
        subprocess.run(["squid", "-k", "reconfigure"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao recarregar o Squid: {e}")
        return False

@app.route('/api/blocklist', methods=['GET'])
def get_blocklist():
    """Retorna a lista atual de sites bloqueados."""
    domains = read_blocklist()
    return jsonify(list(domains))

@app.route('/api/blocklist/add', methods=['POST'])
def add_to_blocklist():
    """Adiciona um novo domínio à lista de bloqueio."""
    if not request.json or 'domain' not in request.json:
        abort(400, description="Payload JSON deve conter uma chave 'domain'.")

    domain_to_add = request.json['domain'].strip().lower()
    if not domain_to_add:
        abort(400, description="Domínio não pode ser vazio.")

    domains = read_blocklist()
    
    if domain_to_add in domains:
        return jsonify({"message": "Domínio já estava na lista."}), 200

    domains.add(domain_to_add)
    
    if not write_blocklist(domains):
        abort(500, description="Não foi possível escrever no arquivo de bloqueio.")
        
    if not reload_squid():
        abort(500, description="Arquivo escrito, mas falha ao recarregar o Squid.")

    return jsonify({"message": f"Domínio '{domain_to_add}' bloqueado."}), 201

@app.route('/api/blocklist/remove', methods=['POST'])
def remove_from_blocklist():
    """Remove um domínio da lista de bloqueio."""
    if not request.json or 'domain' not in request.json:
        abort(400, description="Payload JSON deve conter uma chave 'domain'.")

    domain_to_remove = request.json['domain'].strip().lower()
    domains = read_blocklist()

    if domain_to_remove not in domains:
        return jsonify({"message": "Domínio não encontrado na lista."}), 404

    domains.remove(domain_to_remove)
    
    if not write_blocklist(domains):
        abort(500, description="Não foi possível escrever no arquivo de bloqueio.")
        
    if not reload_squid():
        abort(500, description="Arquivo escrito, mas falha ao recarregar o Squid.")

    return jsonify({"message": f"Domínio '{domain_to_remove}' desbloqueado."}), 200

@app.route('/')
def index():
    """Serve a página principal index.html."""
    # O Flask procurará por 'index.html' dentro da pasta 'templates'
    return render_template('index.html')

if __name__ == '__main__':
    # Execute em '0.0.0.0' para ser acessível na rede
    # ATENÇÃO: Isso torna a API acessível a qualquer pessoa na sua rede.
    # Use um servidor WSGI (como Gunicorn) em produção.
    app.run(host='0.0.0.0', port=5000, debug=True)
