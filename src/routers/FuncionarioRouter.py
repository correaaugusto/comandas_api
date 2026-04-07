from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from src.services.AuditoriaService import AuditoriaService

from src.infra.rate_limit import limiter, get_rate_limit

# Domain Schemas
from src.domain.entities.FuncionarioSchema import (
    FuncionarioCreate,
    FuncionarioUpdate,
    FuncionarioResponse
)

from src.domain.Schemas.AuthSchema import FuncionarioAuth

# Infra
from src.infra.orm.FuncionarioModel import FuncionarioDB
from src.infra.database import get_db
from src.infra.security import get_password_hash
from src.infra.dependencies import get_current_active_user, require_group

router = APIRouter()


# =========================
# GET TODOS
# =========================
@router.get(
    "/funcionario/",
    response_model=List[FuncionarioResponse],
    tags=["Funcionário"],
    status_code=status.HTTP_200_OK
)

@limiter.limit(get_rate_limit("moderate"))
async def get_funcionarios(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    """Retorna todos os funcionários"""
    try:
        return db.query(FuncionarioDB).all()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar funcionários: {str(e)}"
        )


# =========================
# GET POR ID
# =========================
@router.get(
    "/funcionario/{id}",
    response_model=FuncionarioResponse,
    tags=["Funcionário"],
    status_code=status.HTTP_200_OK
)

@limiter.limit(get_rate_limit("moderate"))
async def get_funcionario_por_id(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    """Retorna um funcionário específico pelo ID"""
    try:
        funcionario = db.query(FuncionarioDB).filter(FuncionarioDB.id == id).first()

        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funcionário não encontrado"
            )

        return funcionario

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar funcionário: {str(e)}"
        )


# =========================
# POST
# =========================
@router.post(
    "/funcionario/",
    response_model=FuncionarioResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Funcionário"]
)
@limiter.limit(get_rate_limit("restrictive"))
async def post_funcionario(
    request: Request,
    funcionario_data: FuncionarioCreate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    """Cria um novo funcionário"""
    try:
        existing = db.query(FuncionarioDB).filter(
            FuncionarioDB.cpf == funcionario_data.cpf
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um funcionário com este CPF"
            )

        hashed_password = get_password_hash(funcionario_data.senha)

        novo_funcionario = FuncionarioDB(
            nome=funcionario_data.nome,
            matricula=funcionario_data.matricula,
            cpf=funcionario_data.cpf,
            telefone=funcionario_data.telefone,
            grupo=funcionario_data.grupo,
            senha=hashed_password
        )

        db.add(novo_funcionario)
        db.commit()
        db.refresh(novo_funcionario)

        # Depois de tudo executado e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="CREATE",
            recurso="FUNCIONARIO",
            recurso_id=novo_funcionario.id,
            dados_antigos=None,
            dados_novos=novo_funcionario, # Objeto SQLAlchemy com dados novos
            request=request # Request completo para capturar IP e user agent
        )

        return novo_funcionario

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar funcionário: {str(e)}"
        )


# =========================
# PUT
# =========================
@router.put(
    "/funcionario/{id}",
    response_model=FuncionarioResponse,
    tags=["Funcionário"],
    status_code=status.HTTP_200_OK
)
@limiter.limit(get_rate_limit("restrictive"))
async def put_funcionario(
    request: Request,
    id: int,
    funcionario_data: FuncionarioUpdate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    """Atualiza um funcionário"""
    try:
        funcionario = db.query(FuncionarioDB).filter(
            FuncionarioDB.id == id
        ).first()

        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funcionário não encontrado"
            )

        if funcionario_data.cpf and funcionario_data.cpf != funcionario.cpf:
            existing = db.query(FuncionarioDB).filter(
                FuncionarioDB.cpf == funcionario_data.cpf
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado"
                )

        if funcionario_data.senha:
            funcionario_data.senha = get_password_hash(funcionario_data.senha)

            # não pode manter referencia com funcionário, para que o auditoria possa comparar
            # por isso a cópia do __dict__
            dados_antigos_obj = funcionario.__dict__.copy()

        update_data = funcionario_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(funcionario, field, value)

        db.commit()
        db.refresh(funcionario)

        # Depois de tudo executado e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="UPDATE",
            recurso="FUNCIONARIO",
            recurso_id=funcionario.id,
            dados_antigos=dados_antigos_obj,
            dados_novos=funcionario, # Objeto SQLAlchemy com dados novos
            request=request # Request completo para capturar IP e user agent
        )

        return funcionario

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar funcionário: {str(e)}"
        )


# =========================
# DELETE
# =========================
@router.delete(
    "/funcionario/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Funcionário"]
)
@limiter.limit(get_rate_limit("restrictive"))
async def delete_funcionario(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    """Remove um funcionário"""
    try:
        funcionario = db.query(FuncionarioDB).filter(
            FuncionarioDB.id == id
        ).first()

        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funcionário não encontrado"
            )

        db.delete(funcionario)
        db.commit()

        # Depois de tudo executado e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="DELETE",
            recurso="FUNCIONARIO",
            recurso_id=funcionario.id,
            dados_antigos=funcionario,
            dados_novos=None,
            request=request
        )   

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover funcionário: {str(e)}"
        )