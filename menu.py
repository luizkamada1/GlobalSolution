import matplotlib.pyplot as plt
import pandas as pd
import requests
import json

def menu_principal():
    while True:
        print("\nMenu Principal")
        print("1. Registrar Usuário")
        print("2. Login de Usuário")
        print("3. Listar Usuários")
        print("4. Cadastrar Instalação")
        print("5. Cadastrar Painel Solar")
        print("6. Cadastrar Endereço")
        print("7. Consultar Dados Solcast")  # Nova opção
        print("8. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            registrar_usuario()
        elif opcao == "2":
            login_usuario()
        elif opcao == "3":
            listar_usuarios()
        elif opcao == "4":
            cadastrar_instalacao()
        elif opcao == "5":
            cadastrar_painel()
        elif opcao == "6":
            cadastrar_endereco()
        elif opcao == "7":
            consultar_dados_solcast()  
        elif opcao == "8":
            print("Saindo do programa.")
            break
        else:
            print("Opção inválida. Tente novamente.")


def registrar_usuario():
    username = input("Digite o nome de usuário: ")
    email = input("Digite o email do usuário: ")
    senha = input("Digite a senha do usuário: ")

    payload = {
        "username": username,
        "email": email,
        "senha": senha
    }

    response = requests.post("http://127.0.0.1:5000/register", json=payload)
    print(response.json())


def login_usuario():
    global token

    email = input("Digite seu email: ")
    senha = input("Digite sua senha: ")

    payload = {
        "email": email,
        "senha": senha
    }

    response = requests.post("http://127.0.0.1:5000/login", json=payload)
    resposta = response.json()

    if response.status_code == 200:
        token = resposta.get("token")
        print(f"Seu token é : {token}")
        print()
        print("Login bem-sucedido! Token armazenado.")
    else:
        print(resposta)


def listar_usuarios():
    """
    Lista todos os usuários registrados no sistema.
    """
    global token  # Certifique-se de que o token foi definido no login

    if not token:
        print("\nErro: Você precisa fazer login antes de listar usuários.")
        return

    url = "http://127.0.0.1:5000/usuarios"  # Endpoint para listar os usuários
    headers = {
        "x-access-token": token
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            usuarios = response.json().get("usuarios", [])
            if usuarios:
                print("\nLista de Usuários:")
                for usuario in usuarios:
                    # Atualizado para refletir as chaves corretas do novo esquema
                    print(f"ID: {usuario['id_usuario']}, Nome: {usuario['username']}, Email: {usuario['email']}")
            else:
                print("\nNenhum usuário encontrado.")
        else:
            print("\nErro ao obter usuários:", response.json().get("message", "Erro desconhecido."))
    except requests.RequestException as e:
        print("\nErro na solicitação:", str(e))


def cadastrar_instalacao():
    """
    Função para cadastrar uma instalação no sistema.
    """
    global token  # Certifique-se de que o token foi definido no login

    if not token:
        print("\nErro: Você precisa fazer login antes de cadastrar uma instalação.")
        return

    num_instalacao = int(input("Digite o número da instalação: "))

    while True:
        tipo_instalacao = int(input("Digite o tipo da instalação (0 para residencial, 1 para comercial): "))
        if tipo_instalacao in [0, 1]:
            break
        print("Erro: Tipo de instalação inválido. Escolha 0 para residencial ou 1 para comercial.")

    payload = {
        "num_instalacao": num_instalacao,
        "tipo_instalacao": tipo_instalacao
    }

    headers = {
        "x-access-token": token
    }

    try:
        response = requests.post("http://127.0.0.1:5000/instalacoes", json=payload, headers=headers)
        print(response.json())
    except requests.RequestException as e:
        print("\nErro na solicitação:", str(e))


def cadastrar_painel():
    num_instalacao = int(input("Digite o número da instalação: "))
    quantidade = int(input("Digite a quantidade de painéis: "))
    potencia_wp = float(input("Digite a potência dos painéis (em Watts): "))
    altura_em_m = float(input("Digite a altura dos painéis (em metros): "))
    largura_em_m = float(input("Digite a largura dos painéis (em metros): "))
    orientacao = float(input("Digite a orientação dos painéis: "))
    inclinacao = float(input("Digite a inclinação dos painéis: "))
    eficiencia_painel = float(input("Digite a eficiência dos painéis (em %): "))

    payload = {
        "num_instalacao": num_instalacao,
        "quantidade": quantidade,
        "potencia_wp": potencia_wp,
        "altura_em_m": altura_em_m,
        "largura_em_m": largura_em_m,
        "orientacao": orientacao,
        "inclinacao": inclinacao,
        "eficiencia_painel": eficiencia_painel
    }

    headers = {
        "x-access-token": token
    }

    response = requests.post("http://127.0.0.1:5000/paineis", json=payload, headers=headers)
    print(response.json())


def cadastrar_endereco():
    """
    Função para cadastrar um endereço no sistema.
    """
    global token  # Certifique-se de que o token foi definido no login

    if not token:
        print("\nErro: Você precisa fazer login antes de cadastrar um endereço.")
        return

    num_instalacao = int(input("Digite o número da instalação associada: "))
    cep = input("Digite o CEP (apenas números): ")
    endereco = input("Digite o nome da rua/avenida: ")
    numero = int(input("Digite o número do imóvel: "))
    cidade = input("Digite o nome da cidade: ")
    estado = input("Digite a sigla do estado (2 caracteres): ").upper()

    payload = {
        "num_instalacao": num_instalacao,
        "cep": cep,
        "endereco": endereco,
        "numero": numero,
        "cidade": cidade,
        "estado": estado
    }

    headers = {
        "x-access-token": token
    }

    try:
        response = requests.post("http://127.0.0.1:5000/enderecos", json=payload, headers=headers)
        print(response.json())
    except requests.RequestException as e:
        print("\nErro na solicitação:", str(e))


def consultar_dados_solcast():
    """
    Função para consultar dados da API Solcast via endpoint do backend.
    """
    global token  # Certifique-se de que o token foi definido no login

    if not token:
        print("\nErro: Você precisa fazer login antes de consultar os dados do Solcast.")
        return

    try:
        painel_id = int(input("Digite o ID do painel solar: "))
        horas = int(input("Digite o número de horas (exemplo: 168): "))

        # Parâmetros para a chamada ao endpoint
        params = {
            "id": painel_id,
            "hours": horas
        }

        # Headers com o token
        headers = {
            "x-access-token": token
        }

        # Chamar o endpoint
        response = requests.get("http://127.0.0.1:5000/dados_solcast", params=params, headers=headers)

        # Processar a resposta
        if response.status_code == 200:
            dados = response.json()

            # Exibir informações básicas
            print("\n=== Dados retornados da API Solcast ===")
            print(f"Latitude: {dados.get('latitude', 'N/A')}")
            print(f"Longitude: {dados.get('longitude', 'N/A')}")
            print(f"Endereço: {dados.get('endereco', 'N/A')}\n")

            # Exibir estimativas de energia
            print("=== Estimativa de Geração de Energia ===")
            estimated_actuals = dados.get('solcast_data', {}).get('estimated_actuals', [])
            
            if not estimated_actuals:
                print("Nenhuma estimativa de geração encontrada.")
            else:
                total_energy_generated = 0  # Variável para acumular a energia total gerada
                
                for item in estimated_actuals:
                    pv_estimate = item.get('pv_estimate', 0)
                    period_end = item.get('period_end', "N/A")
                    period_duration = item.get('period', "N/A")
                    total_energy_generated += pv_estimate  # Soma o valor de pv_estimate
                    print(f"Data/Hora: {period_end}, Estimativa: {pv_estimate} kW, Período: {period_duration}")

                # Exibir a soma total da energia gerada
                print("\n=== Energia Total Gerada ===")
                print(f"Total: {total_energy_generated:.2f} kWh no período de {horas} horas.")
        else:
            # Em caso de erro, exibir a mensagem de erro retornada pelo backend
            print("\nErro ao consultar os dados:")
            print(response.json().get("message", "Erro desconhecido."))

    except ValueError:
        print("Erro: O ID do painel solar e o número de horas devem ser valores numéricos.")
    except requests.RequestException as e:
        print(f"Erro na solicitação: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")



if __name__ == "__main__":
    token = None  
    menu_principal()
