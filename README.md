# 🚀 AD Automation API - Gerenciamento de Usuários no Active Directory

API RESTful moderna e assíncrona desenvolvida com **FastAPI**, **ldap3** e **PostgreSQL**, projetada para automatizar, gerenciar e auditar o ciclo de vida de usuários no **Microsoft Active Directory (AD)** via **LDAPS** (LDAP sobre SSL/TLS).

---

## 📌 Visão Geral

O **AD Automation** centraliza as operações administrativas do Active Directory por meio de uma interface HTTP segura. O sistema oferece autenticação via tokens JWT baseada nas credenciais corporativas do AD, criação individual e em lote de usuários, consulta, ativação/desativação de contas e um sistema de **auditoria assíncrona** persistido em banco de dados relacional.

---

## ✨ Principais Funcionalidades

- 🔒 **Autenticação Segura (LDAP + JWT):** Validação de credenciais diretamente no Active Directory com emissão de tokens JWT para proteção das rotas.
- 🛡️ **Comunicação Segura LDAPS (Porta 636):** Criptografia TLS v1.2 com validação de certificados de Autoridade Certificadora (CA).
- 👤 **Gestão de Usuários no AD:**
  - **Listagem de Usuários:** Consulta de contas existentes na Unidade Organizacional (OU) configurada.
  - **Criação de Usuário:** Criação de contas preenchendo atributos essenciais (`sAMAccountName`, `userPrincipalName`, `mail`, cargo, departamento, etc.).
  - **Criação em Lote (Bulk):** Criação de múltiplos usuários em uma única requisição.
  - **Busca por Username:** Localização e detalhamento de usuários por `sAMAccountName` com proteção contra injeção LDAP (`escape_filter_chars`).
  - **Ativação de Conta:** Ativação de usuário com geração de senha temporária segura e configuração para exigir troca de senha no primeiro logon (`pwdLastSet = 0`).
  - **Desativação de Conta:** Bloqueio imediato de contas através do ajuste no `userAccountControl`.
- 📋 **Trilha de Auditoria Assíncrona:** Registro em segundo plano (`BackgroundTasks`) de todas as operações administrativas (operador, ação, alvo, sucesso e mensagens de erro) no PostgreSQL via SQLAlchemy Async.
- 🔄 **Migrações de Banco de Dados:** Versionamento de schema automatizado com **Alembic**.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** [Python 3.14+](https://www.python.org/)
- **Gerenciador de Dependências:** [Poetry](https://python-poetry.org/)
- **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/) & [Uvicorn](https://www.uvicorn.org/)
- **Integração com Active Directory:** [ldap3](https://ldap3.readthedocs.io/)
- **Banco de Dados & ORM:** [PostgreSQL](https://www.postgresql.org/), [SQLAlchemy (AsyncIO)](https://www.sqlalchemy.org/), [asyncpg](https://github.com/MagicStack/asyncpg)
- **Migrações de Schema:** [Alembic](https://alembic.sqlalchemy.org/)
- **Segurança & Tokens:** [PyJWT](https://pyjwt.readthedocs.io/), [pycryptodome](https://www.pycryptodome.org/)
- **Configurações:** [python-decouple](https://github.com/HBNetwork/python-decouple)
- **Testes:** [pytest](https://docs.pytest.org/), [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio), [httpx](https://www.python-httpx.org/)

---

## 📁 Estrutura do Projeto

```text
AD-Automation-Python/
│
├── alembic/                 # Configurações e versões de migração do banco
│   ├── versions/            # Scripts de migração do Alembic
│   └── env.py               # Configuração do ambiente assíncrono do Alembic
│
├── certicate/               # Certificados CA para conexão LDAPS segura
│
├── src/
│   ├── api/                 # Endpoints e roteadores da API
│   │   ├── auth.py          # Rota de autenticação (/auth/login)
│   │   └── users.py         # Rotas de usuários (/users)
│   │
│   ├── core/                # Configurações centrais do sistema
│   │   ├── database.py      # Conexão e sessão assíncrona com PostgreSQL
│   │   ├── exceptions.py    # Exceções customizadas da aplicação
│   │   └── security.py      # Dependências de autenticação e validação de token
│   │
│   ├── models/              # Modelos do SQLAlchemy
│   │   └── audit_model.py   # Modelo da tabela de logs de auditoria
│   │
│   ├── schemas/             # Schemas de validação e serialização (Pydantic)
│   │   ├── schema_auth.py   # Schemas para autenticação e token
│   │   ├── schema_record.py # Schemas para registros de auditoria
│   │   └── schema_user.py   # Schemas para criação, retorno e ativação de usuários
│   │
│   ├── services/            # Camada de regras de negócio e integrações
│   │   ├── audit_service.py # Serviço para persistência de logs de auditoria
│   │   ├── auth_service.py  # Serviço de autenticação e geração de JWT
│   │   └── ldap_service.py  # Serviço de comunicação direta com o Active Directory
│   │
│   ├── utils/               # Utilitários auxiliares
│   │   ├── logging_provider.py # Configuração de logs da aplicação
│   │   └── secret_passwd.py    # Gerador de senhas aleatórias seguras
│   │
│   └── main.py              # Ponto de entrada da aplicação FastAPI
│
├── tests/                   # Testes automatizados unitários e de integração
│   ├── conftest.py          # Fixtures e mocks para testes
│   ├── test_auth.py         # Testes de autenticação
│   └── test_users.py        # Testes das rotas de usuários
│
├── alembic.ini              # Configuração do Alembic
├── .env.example             # Modelo de variáveis de ambiente (sem segredos)
├── .gitignore               # Regras de exclusão do Git com foco em segurança
├── pyproject.toml           # Dependências e metadados do Poetry
├── pytest.ini               # Configurações do Pytest
└── README.md                # Documentação do projeto
```

---

## ⚙️ Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em seu ambiente:
- **Python 3.14** (ou versão compatível configurada no seu ambiente)
- **Poetry** (Gerenciador de pacotes e ambientes virtuais)
- **PostgreSQL** em execução
- Acesso de rede à porta `636` (LDAPS) do servidor **Active Directory**
- Certificado digital da Autoridade Certificadora (CA) do AD (formato `.cer` ou `.pem`)

---

## 🔐 Configuração das Variáveis de Ambiente & Segurança

> ⚠️ **IMPORTANTE - SEGURANÇA EM PRIMEIRO LUGAR:**
> - **NUNCA** envie seu arquivo `.env`, certificados reais (`.cer`, `.pem`, `.key`) ou credenciais administrativas para repositórios públicos ou de controle de versão (GitHub, GitLab, etc.).
> - O arquivo `.gitignore` já está pré-configurado para ignorar `.env`, arquivos de certificado (`certicate/`, `*.cer`, `*.pem`, `*.key`) e logs (`src/logs/app.log`).
> - Utilize o arquivo `.env.example` como base para configurar o seu ambiente local de forma segura.

Crie uma cópia do `.env.example` nomeada como `.env` na raiz do projeto e preencha com suas configurações reais:

```bash
cp .env.example .env
```

Conteúdo de exemplo:

```env
# Configurações do Active Directory
AD_SERVER=seu-dominio.ad.local
LDAP_USER=usuario_servico@seu-dominio.ad.local
LDAP_PASSWORD=SenhaDoUsuarioDeServico
OU_DN=OU=Usuarios,DC=seu-dominio,DC=ad,DC=local
DOMINIO=seu-dominio.ad.local
CA_FILE_PATH=certicate/cert_CA.cer

# Segurança e JWT
SECRET_KEY=sua_chave_secreta_super_segura_jwt

# Banco de Dados (PostgreSQL Assíncrono)
DATABASE_URL=postgresql+asyncpg://postgres:sua_senha@localhost:5432/ad_automation_db
```

### 📋 Descrição das Variáveis

| Variável | Descrição |
| :--- | :--- |
| `AD_SERVER` | Hostname ou FQDN do controlador de domínio Active Directory. |
| `LDAP_USER` | Usuário com permissões administrativas para gerenciar contas no AD. |
| `LDAP_PASSWORD` | Senha do usuário administrativo do LDAP. |
| `OU_DN` | Distinguished Name da Unidade Organizacional padrão (ex: `OU=Users,DC=empresa,DC=com`). |
| `DOMINIO` | Domínio utilizado para compor o `userPrincipalName` (UPN). |
| `CA_FILE_PATH` | Caminho para o arquivo do certificado CA para validação TLS. |
| `SECRET_KEY` | Chave secreta utilizada para assinar e validar os tokens JWT. |
| `DATABASE_URL` | String de conexão assíncrona com o PostgreSQL (`postgresql+asyncpg://...`). |

---

## 🚀 Instalação e Execução

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/AD-Automation-Python.git
cd AD-Automation-Python
```

### 2. Instalar as dependências com Poetry

```bash
poetry install
```

### 3. Executar as migrações do banco de dados

Crie o banco de dados no PostgreSQL e execute o Alembic para criar a tabela de auditoria:

```bash
poetry run alembic upgrade head
```

### 4. Iniciar o servidor da API

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: `http://localhost:8000`

---

## 📖 Documentação Interativa da API

Após iniciar o servidor, você pode acessar a documentação interativa gerada automaticamente pelo FastAPI:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🛣️ Endpoints da API

### 🔑 Autenticação (`/auth`)

| Método | Endpoint | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Autentica o usuário no AD e retorna um token JWT de acesso | Pública |

#### Exemplo de Requisição: `POST /auth/login`
```json
{
  "username": "admin_usuario",
  "password": "SenhaDoUsuario123!"
}
```

#### Resposta de Sucesso (`200 OK`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 👥 Gerenciamento de Usuários (`/users`)

> **Nota:** Todos os endpoints abaixo exigem o cabeçalho `Authorization: Bearer <seu_token_jwt>`.

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/users/` | Lista os usuários da Unidade Organizacional configurada |
| `POST` | `/users/` | Cria um novo usuário no Active Directory |
| `POST` | `/users/bulk/` | Criação de múltiplos usuários em lote |
| `GET` | `/users/{username}` | Busca detalhes de um usuário específico por `sAMAccountName` |
| `PATCH` | `/users/{username}/enable/` | Ativa a conta do usuário e gera uma nova senha temporária |
| `PATCH` | `/users/{username}/disable/` | Desativa a conta do usuário no Active Directory |

---

#### ➕ Exemplo: Criar Usuário (`POST /users/`)

**Payload:**
```json
{
  "first_name": "João",
  "last_name": "Silva",
  "username": "joao.silva",
  "email": "joao.silva@empresa.com",
  "department": "Tecnologia da Informação",
  "job_title": "Analista de Sistemas",
  "company": "Minha Empresa",
  "manager": "gerente.ti",
  "office": "Matriz - SP",
  "employee_id": "1001",
  "employee_number": "EMP-1001"
}
```

**Resposta (`200 OK`):**
```json
{
  "first_name": "João",
  "last_name": "Silva",
  "username": "joao.silva",
  "email": "joao.silva@empresa.com",
  "department": "Tecnologia da Informação",
  "job_title": "Analista de Sistemas",
  "company": "Minha Empresa",
  "manager": "gerente.ti",
  "office": "Matriz - SP",
  "employee_id": "1001",
  "employee_number": "EMP-1001",
  "account_control": 514
}
```

---

#### ⚡ Exemplo: Ativar Usuário (`PATCH /users/{username}/enable/`)

Ao ativar uma conta, o sistema redefine a senha com um gerador criptograficamente seguro e obriga o usuário a alterá-la no próximo logon.

**Resposta (`200 OK`):**
```json
{
  "message": "Usuário ativado com sucesso",
  "enabled": true,
  "temporary_password": "A#8k$pL9!mZ2@vQ1"
}
```

---

## 📊 Sistema de Auditoria

Todas as operações de criação, busca, listagem, ativação e desativação disparam uma tarefa em segundo plano (`BackgroundTasks`) que registra a ação na tabela `audit_logs`:

- **`id`**: Identificador único do log.
- **`operator`**: Login do usuário que realizou a operação (extraído do token JWT).
- **`action`**: Ação executada (`CREATE`, `SEARCH`, `LIST`, `ENABLE`, `DISABLE`).
- **`target`**: Alvo da operação (ex: username afetado ou `all`).
- **`success`**: Booleano indicando se a operação foi bem-sucedida.
- **`error_message`**: Detalhamento do erro em caso de falha.
- **`timestamp`**: Data e hora exata da ocorrência (com timezone).

---

## 🧪 Executando os Testes

O projeto possui suíte de testes automatizados com cobertura para autenticação e rotas de usuários utilizando mocks para as conexões LDAP.

Para rodar todos os testes:

```bash
poetry run pytest
```

Para rodar com exibição detalhada de logs e saída no terminal:

```bash
poetry run pytest -v -s
```

---

## 👤 Autor

Desenvolvido por **William Cruz**  
- E-mail: [cruzwilliam14@gmail.com](mailto:cruzwilliam14@gmail.com)

---

## 📄 Licença

Este projeto é disponibilizado para fins de automação e integração de infraestrutura Active Directory. Consulte os termos internos ou adicione a licença apropriada (MIT, Apache, etc.).
