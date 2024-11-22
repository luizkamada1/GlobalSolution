# Importação das bibliotecas necessárias
import oracledb
import json
import pandas as pd
import requests
from jwt import encode, decode, exceptions
import datetime
from flask import Flask, request, jsonify, make_response
from functools import wraps
from dotenv import load_dotenv
import os
import schedule
import time
import threading


# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uVwXyZ12345'

# Função para conexão com o banco de dados
def get_conexao():
    return oracledb.connect(user="rm555285", password="270102",
                            dsn="oracle.fiap.com.br/orcl")

# Funções auxiliares para autenticação
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token ausente!'}), 401
        try:
            # Decodifica o token usando PyJWT
            data = decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['email']
        except exceptions.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado!'}), 401
        except exceptions.InvalidTokenError:
            return jsonify({'message': 'Token inválido!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


# Cadastro
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    try:
        conn = get_conexao()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tb_usuario (username, email, senha, criado_em)
            VALUES (:1, :2, :3, SYSTIMESTAMP)
            """,
            (data['username'], data['email'], data['senha'])
        )
        conn.commit()
        return jsonify({'message': 'Usuário registrado com sucesso!'}), 201
    except oracledb.DatabaseError as e:
        return jsonify({'message': 'Erro ao registrar usuário!', 'error': str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()


# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        conn = get_conexao()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tb_usuario WHERE email = :1 AND senha = :2",
            (data['email'], data['senha'])
        )
        usuario = cursor.fetchone()
        if usuario:
            token = encode(
                {'email': data['email'], 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},
                app.config['SECRET_KEY'],
                algorithm="HS256"
            )
            return jsonify({'token': token}), 200
        else:
            return jsonify({'message': 'Credenciais inválidas!'}), 401
    except oracledb.DatabaseError as e:
        return jsonify({'message': 'Erro ao autenticar usuário!', 'error': str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()


# Listar Usuarios
@app.route('/usuarios', methods=['GET'])
@token_required
def get_usuarios(current_user):
    try:
        conn = get_conexao()
        cursor = conn.cursor()
        
        # Atualizar a consulta SQL para a nova tabela tb_usuario
        cursor.execute("SELECT id_usuario, username, email FROM tb_usuario")
        usuarios = cursor.fetchall()
        
        # Converta os dados em uma lista de dicionários para facilitar a serialização
        usuarios_list = []
        for usuario in usuarios:
            usuarios_list.append({
                "id_usuario": usuario[0],
                "username": usuario[1],
                "email": usuario[2]
            })
        
        return jsonify({"usuarios": usuarios_list}), 200
    except oracledb.DatabaseError as e:
        return jsonify({"message": "Erro ao buscar usuários!", "error": str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()


# Cadastra Instalação
@app.route('/instalacoes', methods=['POST'])
@token_required
def cadastrar_instalacao(current_user):
    data = request.json
    try:
        conn = get_conexao()
        cursor = conn.cursor()

        # Obter id_usuario com base no email do usuário
        cursor.execute("SELECT id_usuario FROM tb_usuario WHERE email = :1", (current_user,))
        id_usuario = cursor.fetchone()
        if not id_usuario:
            return jsonify({'message': 'Usuário não encontrado!'}), 404
        id_usuario = id_usuario[0]

        # Validar tipo_instalacao
        if data['tipo_instalacao'] not in [0, 1]:
            return jsonify({'message': 'Tipo de instalação inválido! Apenas 0 ou 1 são permitidos.'}), 400

        # Inserir nova instalação
        cursor.execute(
            """
            INSERT INTO tb_instalacao (num_instalacao, id_usuario, tipo_instalacao)
            VALUES (:1, :2, :3)
            """,
            (data['num_instalacao'], id_usuario, data['tipo_instalacao'])
        )
        conn.commit()
        return jsonify({'message': 'Instalação cadastrada com sucesso!'}), 201
    except oracledb.DatabaseError as e:
        return jsonify({'message': 'Erro ao cadastrar instalação!', 'error': str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()


# Cadastro de painéis solares
@app.route('/paineis', methods=['POST'])
@token_required
def cadastrar_painel(current_user):
    data = request.json
    try:
        conn = get_conexao()
        cursor = conn.cursor()

        # Obter id_usuario com base no email do usuário
        cursor.execute("SELECT id_usuario FROM tb_usuario WHERE email = :1", (current_user,))
        id_usuario = cursor.fetchone()[0]

        # Variável para capturar o id_painel_solar gerado
        id_painel_solar = cursor.var(int)

        # Inserção dos dados do painel solar com RETURNING para capturar o id gerado
        cursor.execute(
            """
            INSERT INTO tb_painel_solar 
            (num_instalacao, quantidade, potencia_wp, altura_em_m, largura_em_m, orientacao, inclinacao, eficiencia_painel)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
            RETURNING id_painel_solar INTO :9
            """,
            (data['num_instalacao'], data['quantidade'], data['potencia_wp'], data['altura_em_m'],
             data['largura_em_m'], data['orientacao'], data['inclinacao'], data['eficiencia_painel'], id_painel_solar)
        )
        conn.commit()

        # Retornar mensagem de sucesso com o id do painel solar cadastrado
        return jsonify({
            'message': 'Painel cadastrado com sucesso!',
            'id_painel_solar': id_painel_solar.getvalue()
        }), 201
    except oracledb.DatabaseError as e:
        return jsonify({'message': 'Erro ao cadastrar painel!', 'error': str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()



# Cadastra Endereço
@app.route('/enderecos', methods=['POST'])
@token_required
def cadastrar_endereco(current_user):
    data = request.json
    try:
        conn = get_conexao()
        cursor = conn.cursor()

        # Validar se a instalação existe
        cursor.execute("SELECT COUNT(*) FROM tb_instalacao WHERE num_instalacao = :1", [data['num_instalacao']])
        if cursor.fetchone()[0] == 0:
            return jsonify({'message': 'Número de instalação não encontrado!'}), 404

        # Inserir o endereço
        cursor.execute(
            """
            INSERT INTO tb_endereco (num_instalacao, cep, endereco, numero, cidade, estado)
            VALUES (:1, :2, :3, :4, :5, :6)
            """,
            (data['num_instalacao'], data['cep'], data['endereco'], data['numero'], data['cidade'], data['estado'])
        )
        conn.commit()
        return jsonify({'message': 'Endereço cadastrado com sucesso!'}), 201
    except oracledb.DatabaseError as e:
        return jsonify({'message': 'Erro ao cadastrar endereço!', 'error': str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.route('/dados_solcast', methods=['GET'])
@token_required
def dados_solcast(current_user):
    try:
        # Capturar parâmetros do usuário
        painel_id = request.args.get('id', type=int)
        horas = request.args.get('hours', type=int)

        if not painel_id or not horas:
            return jsonify({'message': 'ID do painel e número de horas são obrigatórios!'}), 400

        conn = get_conexao()
        cursor = conn.cursor()

        # Buscar dados do painel e endereço
        cursor.execute("""
            SELECT p.potencia_wp, p.inclinacao, p.orientacao, e.endereco 
            FROM tb_painel_solar p 
            JOIN tb_endereco e ON p.num_instalacao = e.num_instalacao
            WHERE p.id_painel_solar = :1
        """, [painel_id])
        painel_data = cursor.fetchone()

        if not painel_data:
            return jsonify({'message': 'Painel solar não encontrado!'}), 404

        potencia_wp, inclinacao, orientacao, endereco = painel_data

        # Obter latitude e longitude com OpenCageData
        opencage_url = f"https://api.opencagedata.com/geocode/v1/json?q={endereco}&key=bf61689c2b494ec6a6044117ecd8154f"
        geocode_response = requests.get(opencage_url)

        if geocode_response.status_code != 200:
            return jsonify({'message': 'Erro ao buscar coordenadas na API OpenCageData!'}), 500

        geocode_data = geocode_response.json()
        if not geocode_data['results']:
            return jsonify({'message': 'Endereço não encontrado pela API OpenCageData!'}), 404

        latitude = geocode_data['results'][0]['geometry']['lat']
        longitude = geocode_data['results'][0]['geometry']['lng']

        # Chamar a API Solcast com os dados obtidos
        solcast_url = f"https://api.solcast.com.au/world_pv_power/estimated_actuals"
        solcast_params = {
            'latitude': latitude,
            'longitude': longitude,
            'capacity': potencia_wp,
            'tilt': inclinacao,
            'azimuth': orientacao,
            'hours': horas,
            'api_key': 'JTFFB7_aG3H4hLva4QU1QW7aJJpMI64G'
        }
        solcast_response = requests.get(solcast_url, params=solcast_params, headers={'Accept': 'application/json'})

        if solcast_response.status_code != 200:
            return jsonify({'message': 'Erro ao buscar dados na API Solcast!'}), 500

        solcast_data = solcast_response.json()

        # Retornar os dados da API Solcast
        return jsonify(solcast_data), 200

    except requests.RequestException as e:
        print(f"Erro na solicitação às APIs externas: {e}")
        return jsonify({'message': 'Erro ao consultar APIs externas!', 'error': str(e)}), 500

    except oracledb.DatabaseError as e:
        print(f"Erro no banco de dados: {e}")
        return jsonify({'message': 'Erro ao acessar o banco de dados!', 'error': str(e)}), 500

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'message': 'Erro interno ao processar os dados!', 'error': str(e)}), 500

    finally:
        if conn:
            cursor.close()
            conn.close()




# Agendamento do job diário
schedule.every().day.at("00:00").do(dados_solcast)

# Função para executar o agendador de tarefas
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":

    # Inicia o agendador em uma thread separada
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True  # Permite que o programa termine mesmo que a thread esteja ativa
    scheduler_thread.start()

    # Inicia o servidor Flask
    app.run(debug=True)
    