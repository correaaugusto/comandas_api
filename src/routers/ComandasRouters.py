from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from src.domain.Schemas.ComandaSchema import (
ComandaCreate, ComandaUpdate, ComandaResponse, FuncionarioResponse, ClienteResponse,
ComandaProdutosCreate, ComandaProdutosUpdate, ComandaProdutosResponse, ProdutoResponse
)

from src.domain.Schemas.AuthSchema import FuncionarioAuth
from src.infra.orm.ComandaModel import ComandaDB, ComandaProdutoDB
from src.infra.orm.ProdutoModel import ProdutoDB
from src.infra.orm.FuncionarioModel import FuncionarioDB
from src.infra.orm.ClienteModel import ClienteDB
from src.infra.database import get_async_db
from src.infra.dependencies import require_group, get_current_active_user
from src.infra.rate_limit import limiter
from src.services.AuditoriaService import AuditoriaService

router = APIRouter()