from dotenv import load_dotenv, find_dotenv
import os

# =========================
# Carregar .env
# =========================
dotenv_file = find_dotenv()
load_dotenv(dotenv_file)

# =========================
# Configurações da API
# =========================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", "8000")
RELOAD = os.getenv("RELOAD", "True") == "True"

# =========================
# Configurações banco de dados
# =========================
DB_SGDB = os.getenv("DB_SGDB")
DB_NAME = os.getenv("DB_NAME")

# Caso não seja sqlite
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# =========================
# String de conexão (síncrona)
# =========================
if DB_SGDB == "sqlite":
    # habilita foreign keys
    STR_DATABASE = f"sqlite:///{DB_NAME}.db?foreign_keys=1"

elif DB_SGDB == "mysql":
    import pymysql
    STR_DATABASE = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

elif DB_SGDB == "mssql":
    import pymssql
    STR_DATABASE = f"mssql+pymssql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8"

else:
    # fallback sqlite
    STR_DATABASE = "sqlite:///apiDatabase.db?foreign_keys=1"

# =========================
# String de conexão (assíncrona)
# =========================
if STR_DATABASE.startswith("sqlite:///"):
    ASYNC_STR_DATABASE = STR_DATABASE.replace("sqlite:///", "sqlite+aiosqlite:///")

elif STR_DATABASE.startswith("sqlite://"):
    ASYNC_STR_DATABASE = STR_DATABASE.replace("sqlite://", "sqlite+aiosqlite:///")

elif DB_SGDB == "mysql":
    ASYNC_STR_DATABASE = STR_DATABASE.replace("mysql+pymysql://", "mysql+aiomysql://")

elif DB_SGDB == "mssql":
    # Não há driver async oficial
    ASYNC_STR_DATABASE = STR_DATABASE

elif DB_SGDB == "postgresql":
    ASYNC_STR_DATABASE = STR_DATABASE.replace("postgresql://", "postgresql+asyncpg://")

else:
    ASYNC_STR_DATABASE = STR_DATABASE

# =========================
# Configurações JWT
# =========================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "sua-chave-secreta-super-forte-mudar-em-producao"
)

ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)

REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)


CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else "*"