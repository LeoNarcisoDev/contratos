from getpass import getpass
from werkzeug.security import generate_password_hash
from utils.pg import get_pg_conn


def criar_usuario():
    conn = get_pg_conn()
    cur = conn.cursor()

    username = input("Digite o nome de usuário: ").strip()

    # Verifica se já existe
    cur.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
    if cur.fetchone():
        print("Este nome de usuário já está cadastrado.")
        conn.close()
        return

    senha = getpass("Digite a senha: ")
    senha_confirm = getpass("Confirme a senha: ")

    if senha != senha_confirm:
        print("As senhas não coincidem.")
        conn.close()
        return

    senha_hash = generate_password_hash(senha)

    cur.execute("INSERT INTO usuarios (username, senha_hash) VALUES (%s, %s)", (username, senha_hash))
    conn.commit()
    conn.close()

    print(f"Usuário '{username}' criado com sucesso!")


if __name__ == "__main__":
    criar_usuario()
