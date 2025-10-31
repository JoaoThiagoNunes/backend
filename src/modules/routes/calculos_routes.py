from fastapi import APIRouter, Depends, HTTPException, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.schemas.calculos import *
from src.modules.models import  *
from datetime import datetime
from typing import Optional
import pandas as pd
from src.core.utils import calcular_todas_cotas

router = APIRouter()

@router.post("/calcular-valores", response_model=ResponseCalculos, tags=["Calculos"])
async def calcular_valores(
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (usa ano ativo se não informado)"),
    db: Session = Depends(get_db)
):
    """
    Calcula os valores das escolas de um ano letivo específico.
    Se ano_letivo_id não for informado, usa o ano ativo.
    """
    try:
        # 1. Determinar ano letivo
        if ano_letivo_id is None:
            ano_letivo = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
            if not ano_letivo:
                raise HTTPException(status_code=400, detail="Nenhum ano letivo ativo encontrado")
            ano_letivo_id = ano_letivo.id
        else:
            ano_letivo = db.query(AnoLetivo).filter(AnoLetivo.id == ano_letivo_id).first()
            if not ano_letivo:
                raise HTTPException(status_code=404, detail=f"Ano letivo ID {ano_letivo_id} não encontrado")
        
        print(f"\n{'='*60}")
        print(f"CALCULANDO VALORES - ANO LETIVO: {ano_letivo.ano}")
        print(f"{'='*60}\n")
        
        # 2. Buscar escolas do ano letivo
        escolas = db.query(Escola).join(Upload).filter(
            Upload.ano_letivo_id == ano_letivo_id
        ).all()
        
        if not escolas:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhuma escola encontrada para o ano letivo {ano_letivo.ano}"
            )
        
        escolas_calculadas = []
        valor_total_geral = 0.0
        upload_id = escolas[0].upload_id if escolas else None
        
        # 3. Calcular para cada escola
        for escola_obj in escolas:
            # Criar objeto row-like para cálculos
            row_data = {
                "TOTAL": escola_obj.total_alunos,
                "FUNDAMENTAL INICIAL": escola_obj.fundamental_inicial,
                "FUNDAMENTAL FINAL": escola_obj.fundamental_final,
                "FUNDAMENTAL INTEGRAL": escola_obj.fundamental_integral,
                "PROFISSIONALIZANTE": escola_obj.profissionalizante,
                "ALTERNÂNCIA": escola_obj.alternancia,
                "ENSINO MÉDIO INTEGRAL": escola_obj.ensino_medio_integral,
                "ENSINO MÉDIO REGULAR": escola_obj.ensino_medio_regular,
                "ESPECIAL FUNDAMENTAL REGULAR": escola_obj.especial_fund_regular,
                "ESPECIAL FUNDAMENTAL INTEGRAL": escola_obj.especial_fund_integral,
                "ESPECIAL MÉDIO PARCIAL": escola_obj.especial_medio_parcial,
                "ESPECIAL MÉDIO INTEGRAL": escola_obj.especial_medio_integral,
                "SALA DE RECURSO": escola_obj.sala_recurso,
                "CLIMATIZAÇÃO": escola_obj.climatizacao,
                "PREUNI": escola_obj.preuni,
                "INDIGENA & QUILOMBOLA": escola_obj.indigena_quilombola
            }
            
            row_series = pd.Series(row_data)
            
            # Calcular todas as cotas
            cotas = calcular_todas_cotas(row_series)
            
            # Upsert na tabela CalculosProfin
            calculo_obj = db.query(CalculosProfin).filter(
                CalculosProfin.escola_id == escola_obj.id
            ).first()
            
            if calculo_obj:
                # Atualizar cálculo existente
                calculo_obj.profin_custeio = cotas["profin_custeio"]
                calculo_obj.profin_projeto = cotas["profin_projeto"]
                calculo_obj.profin_kit_escolar = cotas["profin_kit_escolar"]
                calculo_obj.profin_uniforme = cotas["profin_uniforme"]
                calculo_obj.profin_merenda = cotas["profin_merenda"]
                calculo_obj.profin_sala_recurso = cotas["profin_sala_recurso"]
                calculo_obj.profin_permanente = cotas["profin_permanente"]
                calculo_obj.profin_climatizacao = cotas["profin_climatizacao"]
                calculo_obj.profin_preuni = cotas["profin_preuni"]
                calculo_obj.valor_total = cotas["valor_total"]
                calculo_obj.calculated_at = datetime.now()
            else:
                # Criar novo cálculo
                calculo_obj = CalculosProfin(
                    escola_id=escola_obj.id,
                    profin_custeio=cotas["profin_custeio"],
                    profin_projeto=cotas["profin_projeto"],
                    profin_kit_escolar=cotas["profin_kit_escolar"],
                    profin_uniforme=cotas["profin_uniforme"],
                    profin_merenda=cotas["profin_merenda"],
                    profin_sala_recurso=cotas["profin_sala_recurso"],
                    profin_permanente=cotas["profin_permanente"],
                    profin_climatizacao=cotas["profin_climatizacao"],
                    profin_preuni=cotas["profin_preuni"],
                    valor_total=cotas["valor_total"],
                    calculated_at=datetime.now()
                )
                db.add(calculo_obj)
            
            escola_data = {
                "id": escola_obj.id,
                "nome_uex": escola_obj.nome_uex,
                "dre": escola_obj.dre,
                **cotas
            }
            
            escolas_calculadas.append(escola_data)
            valor_total_geral += cotas["valor_total"]
        
        db.commit()
        
        print(f"✅ Cálculos concluídos para {len(escolas_calculadas)} escolas")
        print(f"💰 Valor total: R$ {valor_total_geral:,.2f}")
        print(f"{'='*60}\n")
        
        return ResponseCalculos(
            success=True,
            message=f"Cálculos realizados para {len(escolas_calculadas)} escolas do ano {ano_letivo.ano}",
            total_escolas=len(escolas_calculadas),
            valor_total_geral=round(valor_total_geral, 2),
            escolas=escolas_calculadas,
            upload_id=upload_id,
            ano_letivo_id=ano_letivo_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao calcular: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valores: {str(e)}")