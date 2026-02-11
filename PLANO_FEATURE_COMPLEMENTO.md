# 📋 Plano de Desenvolvimento - Feature: Complemento de Alunos

**Versão:** 1.0  
**Data:** 2025-12-02  
**Status:** Em Planejamento

---

## 🎯 Objetivo

Implementar uma funcionalidade que permite o upload de uma planilha complementar com quantidades atualizadas de alunos. O sistema deve:

1. **Comparar** as novas quantidades com as existentes no sistema
2. **Calcular complemento** apenas se houver aumento de alunos
3. **Identificar e registrar** casos onde não houve aumento ou houve diminuição

---

## 📊 Análise do Sistema Atual

### Estrutura Existente

- **Modelo `Escola`**: Armazena quantidades de alunos por modalidade
- **Modelo `CalculosProfin`**: Armazena valores calculados (um por escola)
- **Modelo `Upload`**: Representa um upload de planilha
- **Service `UploadService`**: Processa planilhas e atualiza escolas (substituição completa)
- **Service `CalculoService`**: Calcula valores PROFIN baseado nas quantidades atuais

### Limitações Identificadas

- Upload atual substitui completamente os dados
- Não há histórico de alterações de quantidades
- Não há rastreamento de complementos calculados
- Cálculos são sempre feitos sobre o total atual

---

## 🏗️ Arquitetura da Solução

### 1. Modelos de Dados

#### 1.1 Novo Modelo: `ComplementoUpload`

Armazena informações sobre uploads de complemento.

```python
class ComplementoUpload(Base):
    __tablename__ = "complemento_uploads"
    
    id = Column(Integer, primary_key=True)
    ano_letivo_id = Column(Integer, ForeignKey("anos_letivos.id"), nullable=False)
    upload_base_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)  # Upload original
    upload_complemento_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)  # Upload complementar
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now)
    
    # Estatísticas
    total_escolas_processadas = Column(Integer, default=0)
    escolas_com_aumento = Column(Integer, default=0)
    escolas_sem_mudanca = Column(Integer, default=0)
    escolas_com_diminuicao = Column(Integer, default=0)
    escolas_com_erro = Column(Integer, default=0)
    
    # Relacionamentos
    ano_letivo = relationship("AnoLetivo")
    upload_base = relationship("Upload", foreign_keys=[upload_base_id])
    upload_complemento = relationship("Upload", foreign_keys=[upload_complemento_id])
    complementos_escola = relationship("ComplementoEscola", back_populates="complemento_upload")
```

#### 1.2 Novo Modelo: `ComplementoEscola`

Armazena os dados de complemento por escola.

```python
class ComplementoEscola(Base):
    __tablename__ = "complemento_escolas"
    
    id = Column(Integer, primary_key=True)
    complemento_upload_id = Column(Integer, ForeignKey("complemento_uploads.id"), nullable=False)
    escola_id = Column(Integer, ForeignKey("escolas.id"), nullable=False)
    
    # Quantidades ANTES (do upload base)
    total_alunos_antes = Column(Integer, default=0)
    fundamental_inicial_antes = Column(Integer, default=0)
    fundamental_final_antes = Column(Integer, default=0)
    # ... (todas as modalidades)
    
    # Quantidades DEPOIS (do upload complemento)
    total_alunos_depois = Column(Integer, default=0)
    fundamental_inicial_depois = Column(Integer, default=0)
    fundamental_final_depois = Column(Integer, default=0)
    # ... (todas as modalidades)
    
    # Diferenças calculadas (apenas positivas)
    total_alunos_diferenca = Column(Integer, default=0)
    fundamental_inicial_diferenca = Column(Integer, default=0)
    # ... (todas as modalidades)
    
    # Status do processamento
    status = Column(String(20), nullable=False)  # 'AUMENTO', 'SEM_MUDANCA', 'DIMINUICAO', 'ERRO'
    
    # Valores calculados do complemento (apenas se houve aumento)
    valor_complemento_gestao = Column(Float, default=0.0)
    valor_complemento_projeto = Column(Float, default=0.0)
    valor_complemento_kit_escolar = Column(Float, default=0.0)
    valor_complemento_uniforme = Column(Float, default=0.0)
    valor_complemento_merenda = Column(Float, default=0.0)
    valor_complemento_sala_recurso = Column(Float, default=0.0)
    valor_complemento_preuni = Column(Float, default=0.0)
    valor_complemento_total = Column(Float, default=0.0)
    
    # Data de processamento
    processed_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    complemento_upload = relationship("ComplementoUpload", back_populates="complementos_escola")
    escola = relationship("Escola")
```

#### 1.3 Novo Modelo: `HistoricoQuantidades` (Opcional - para auditoria)

Armazena histórico de alterações de quantidades.

```python
class HistoricoQuantidades(Base):
    __tablename__ = "historico_quantidades"
    
    id = Column(Integer, primary_key=True)
    escola_id = Column(Integer, ForeignKey("escolas.id"), nullable=False)
    complemento_upload_id = Column(Integer, ForeignKey("complemento_uploads.id"), nullable=True)
    
    # Timestamp da alteração
    data_alteracao = Column(DateTime, default=datetime.now)
    
    # Tipo de alteração
    tipo_alteracao = Column(String(20), nullable=False)  # 'UPLOAD_INICIAL', 'COMPLEMENTO', 'CORRECAO'
    
    # Quantidades (snapshot)
    total_alunos = Column(Integer, default=0)
    # ... (todas as modalidades)
    
    # Relacionamentos
    escola = relationship("Escola")
    complemento_upload = relationship("ComplementoUpload")
```

### 2. Estrutura de Arquivos

```
src/modules/features/complemento/
├── __init__.py
├── models.py              # ComplementoUpload, ComplementoEscola, HistoricoQuantidades
├── repository.py          # ComplementoUploadRepository, ComplementoEscolaRepository
├── service.py             # ComplementoService
├── utils.py               # Funções auxiliares de comparação e cálculo
└── routes.py              # Endpoints da API
```

### 3. Schemas Pydantic

#### 3.1 Schemas de Request

```python
# src/modules/schemas/complemento.py

class UploadComplementoRequest(BaseModel):
    ano_letivo_id: Optional[int] = None
    upload_base_id: Optional[int] = None  # Se não fornecido, usa upload ativo
```

#### 3.2 Schemas de Response

```python
class ComplementoEscolaInfo(BaseModel):
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    status: str  # 'AUMENTO', 'SEM_MUDANCA', 'DIMINUICAO'
    
    # Quantidades antes/depois
    total_alunos_antes: int
    total_alunos_depois: int
    total_alunos_diferenca: int
    
    # Valores calculados (se houver aumento)
    valor_complemento_total: Optional[float] = None
    
    # Detalhes por modalidade (opcional, para detalhamento)
    detalhes_modalidades: Optional[Dict[str, Any]] = None

class UploadComplementoResponse(BaseModel):
    success: bool
    complemento_upload_id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    
    # Estatísticas
    total_escolas_processadas: int
    escolas_com_aumento: int
    escolas_sem_mudanca: int
    escolas_com_diminuicao: int
    escolas_com_erro: int
    
    # Valor total de complemento calculado
    valor_complemento_total: float
    
    # Lista de escolas (opcional, pode ser paginada)
    escolas: Optional[List[ComplementoEscolaInfo]] = None
    erros: Optional[List[Dict[str, Any]]] = None
```

---

## 🔄 Fluxo de Processamento

### 1. Upload da Planilha Complementar

```
1. Usuário faz upload via POST /complemento/upload
2. Sistema identifica upload base (ativo ou especificado)
3. Processa planilha complementar linha por linha
4. Para cada escola:
   a. Busca escola no upload base (por nome_uex + DRE)
   b. Compara quantidades
   c. Determina status (AUMENTO, SEM_MUDANCA, DIMINUICAO)
   d. Se AUMENTO: calcula complemento apenas da diferença
   e. Se SEM_MUDANCA ou DIMINUICAO: apenas registra
5. Salva ComplementoUpload e ComplementoEscola
6. Retorna resumo com estatísticas
```

### 2. Comparação de Quantidades

```python
def comparar_quantidades(escola_base: Escola, escola_complemento: Dict) -> Dict:
    """
    Compara quantidades entre escola base e complemento.
    
    Retorna:
    {
        'status': 'AUMENTO' | 'SEM_MUDANCA' | 'DIMINUICAO',
        'diferencas': {
            'total_alunos': int,  # positivo se aumento, negativo se diminuição
            'fundamental_inicial': int,
            ...
        },
        'quantidades_antes': {...},
        'quantidades_depois': {...}
    }
    """
```

### 3. Cálculo de Complemento

```python
def calcular_complemento_escola(
    escola_base: Escola,
    diferencas: Dict[str, int]
) -> Dict[str, float]:
    """
    Calcula valores de complemento apenas para as diferenças positivas.
    
    Usa as mesmas funções de cálculo, mas aplicadas apenas às diferenças.
    """
    # Criar um Series com apenas as diferenças positivas
    row_diferenca = pd.Series({
        'TOTAL': diferencas['total_alunos'],
        'FUNDAMENTAL INICIAL': max(0, diferencas['fundamental_inicial']),
        # ... (apenas valores positivos)
    })
    
    # Calcular usando funções existentes
    cotas = calcular_todas_cotas(row_diferenca)
    
    return cotas
```

---

## 🛣️ Endpoints da API

### 1. POST /complemento/upload

Faz upload de planilha complementar.

**Request:**
- `file`: Arquivo Excel/CSV (multipart/form-data)
- `ano_letivo_id`: Opcional (usa ano ativo se não fornecido)
- `upload_base_id`: Opcional (usa upload ativo se não fornecido)

**Response:**
```json
{
  "success": true,
  "complemento_upload_id": 1,
  "ano_letivo_id": 2,
  "ano_letivo": 2026,
  "filename": "complemento_2026.xlsx",
  "upload_date": "2025-12-02T10:30:00",
  "total_escolas_processadas": 250,
  "escolas_com_aumento": 45,
  "escolas_sem_mudanca": 200,
  "escolas_com_diminuicao": 5,
  "escolas_com_erro": 0,
  "valor_complemento_total": 125000.50,
  "escolas": [...],
  "erros": null
}
```

### 2. GET /complemento/{complemento_upload_id}

Obtém detalhes de um upload de complemento.

**Response:**
```json
{
  "complemento_upload_id": 1,
  "ano_letivo_id": 2,
  "ano_letivo": 2026,
  "filename": "complemento_2026.xlsx",
  "upload_date": "2025-12-02T10:30:00",
  "estatisticas": {...},
  "escolas": [...],  // Lista completa ou paginada
  "valor_complemento_total": 125000.50
}
```

### 3. GET /complemento/escola/{escola_id}

Obtém histórico de complementos de uma escola específica.

**Response:**
```json
{
  "escola_id": 123,
  "nome_uex": "Escola Exemplo",
  "complementos": [
    {
      "complemento_upload_id": 1,
      "data": "2025-12-02T10:30:00",
      "status": "AUMENTO",
      "total_alunos_diferenca": 50,
      "valor_complemento_total": 2500.00
    }
  ]
}
```

### 4. GET /complemento

Lista todos os uploads de complemento (com paginação).

**Query Parameters:**
- `ano_letivo_id`: Filtrar por ano letivo
- `page`: Número da página
- `page_size`: Tamanho da página

---

## 🔧 Implementação Técnica

### 1. Migração Alembic

Criar migração para as novas tabelas:

```python
# alembic/versions/XXXXX_criar_tabelas_complemento.py

def upgrade():
    op.create_table(
        'complemento_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ano_letivo_id', sa.Integer(), nullable=False),
        sa.Column('upload_base_id', sa.Integer(), nullable=False),
        sa.Column('upload_complemento_id', sa.Integer(), nullable=False),
        # ... outros campos
        sa.ForeignKeyConstraint(['ano_letivo_id'], ['anos_letivos.id']),
        sa.ForeignKeyConstraint(['upload_base_id'], ['uploads.id']),
        sa.ForeignKeyConstraint(['upload_complemento_id'], ['uploads.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'complemento_escolas',
        # ... campos
    )
    
    # Criar índices
    op.create_index('ix_complemento_uploads_ano_letivo_id', 'complemento_uploads', ['ano_letivo_id'])
    op.create_index('ix_complemento_escolas_escola_id', 'complemento_escolas', ['escola_id'])
```

### 2. Service Layer

```python
class ComplementoService:
    @staticmethod
    def processar_planilha_complemento(
        db: Session,
        file_contents: bytes,
        filename: str,
        ano_letivo_id: Optional[int] = None,
        upload_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processa planilha complementar e calcula complementos.
        """
        # 1. Identificar upload base
        upload_base = obter_upload_base(db, ano_letivo_id, upload_base_id)
        
        # 2. Criar upload temporário para planilha complementar
        upload_complemento = criar_upload_temporario(db, file_contents, filename)
        
        # 3. Processar comparações
        resultados = []
        escolas_base = obter_escolas_upload(db, upload_base.id)
        
        for escola_base in escolas_base:
            escola_complemento = buscar_escola_complemento(upload_complemento, escola_base)
            
            if escola_complemento:
                comparacao = comparar_quantidades(escola_base, escola_complemento)
                resultado = processar_comparacao(escola_base, comparacao)
                resultados.append(resultado)
        
        # 4. Criar ComplementoUpload
        complemento_upload = criar_complemento_upload(db, upload_base, upload_complemento, resultados)
        
        # 5. Retornar resumo
        return gerar_resumo(complemento_upload, resultados)
```

### 3. Utils

```python
def comparar_quantidades(escola_base: Escola, dados_complemento: Dict) -> Dict:
    """Compara quantidades e retorna diferenças."""
    
def calcular_complemento_valores(diferencas: Dict[str, int]) -> Dict[str, float]:
    """Calcula valores de complemento apenas para diferenças positivas."""
    
def criar_row_diferenca(diferencas: Dict[str, int]) -> pd.Series:
    """Cria Series do pandas apenas com diferenças positivas."""
```

---

## ✅ Checklist de Implementação

### Fase 1: Modelos e Migração
- [ ] Criar modelo `ComplementoUpload`
- [ ] Criar modelo `ComplementoEscola`
- [ ] Criar modelo `HistoricoQuantidades` (opcional)
- [ ] Criar migração Alembic
- [ ] Testar migração em ambiente de desenvolvimento

### Fase 2: Repositórios
- [ ] Criar `ComplementoUploadRepository`
- [ ] Criar `ComplementoEscolaRepository`
- [ ] Implementar métodos CRUD básicos
- [ ] Implementar métodos de consulta específicos

### Fase 3: Lógica de Negócio
- [ ] Implementar `comparar_quantidades()`
- [ ] Implementar `calcular_complemento_valores()`
- [ ] Implementar `processar_planilha_complemento()`
- [ ] Criar funções auxiliares de cálculo

### Fase 4: Service Layer
- [ ] Criar `ComplementoService`
- [ ] Implementar processamento completo
- [ ] Implementar tratamento de erros
- [ ] Implementar validações

### Fase 5: Schemas
- [ ] Criar schemas de request
- [ ] Criar schemas de response
- [ ] Criar schemas de detalhamento

### Fase 6: Rotas da API
- [ ] Implementar `POST /complemento/upload`
- [ ] Implementar `GET /complemento/{id}`
- [ ] Implementar `GET /complemento/escola/{escola_id}`
- [ ] Implementar `GET /complemento` (listagem)
- [ ] Adicionar documentação Swagger

### Fase 7: Testes
- [ ] Testes unitários para comparação
- [ ] Testes unitários para cálculo de complemento
- [ ] Testes de integração para upload
- [ ] Testes de integração para endpoints

### Fase 8: Documentação
- [ ] Documentar endpoints na pasta `docs/rotas/`
- [ ] Documentar modelos na pasta `docs/modelos/`
- [ ] Atualizar README principal
- [ ] Criar exemplos de uso

---

## 🎯 Regras de Negócio

### 1. Identificação de Escolas

- Escolas são identificadas por `nome_uex` + `dre`
- Deve ser case-insensitive e tolerante a espaços
- Se escola não for encontrada no upload base, registrar como erro

### 2. Comparação de Quantidades

- Comparar TODAS as modalidades de alunos
- Considerar aumento se QUALQUER modalidade aumentou
- Considerar diminuição se QUALQUER modalidade diminuiu (sem aumento)
- Considerar sem mudança se todas as quantidades são iguais

### 3. Cálculo de Complemento

- **Apenas calcular se houver aumento**
- Calcular apenas sobre as diferenças positivas
- Usar as mesmas fórmulas de cálculo existentes
- Não recalcular valores já calculados anteriormente

### 4. Validações

- Validar formato do arquivo (Excel/CSV)
- Validar colunas obrigatórias
- Validar tipos de dados
- Validar que upload base existe
- Validar que ano letivo está ativo (ou permitir arquivado?)

### 5. Tratamento de Erros

- Escolas não encontradas: registrar como erro, continuar processamento
- Dados inválidos: registrar como erro, continuar processamento
- Erros críticos: interromper processamento, fazer rollback

---

## 📊 Exemplo de Fluxo

### Cenário 1: Aumento de Alunos

**Escola Base:**
- Total: 500 alunos
- Fundamental Inicial: 200
- Fundamental Final: 300

**Escola Complemento:**
- Total: 550 alunos (+50)
- Fundamental Inicial: 220 (+20)
- Fundamental Final: 330 (+30)

**Processamento:**
1. Status: `AUMENTO`
2. Diferenças: Total=+50, FI=+20, FF=+30
3. Calcular complemento apenas para +50 alunos (FI+20, FF+30)
4. Salvar valores calculados

### Cenário 2: Sem Mudança

**Escola Base:**
- Total: 500 alunos

**Escola Complemento:**
- Total: 500 alunos

**Processamento:**
1. Status: `SEM_MUDANCA`
2. Diferenças: todas zero
3. Não calcular complemento
4. Apenas registrar status

### Cenário 3: Diminuição

**Escola Base:**
- Total: 500 alunos

**Escola Complemento:**
- Total: 480 alunos (-20)

**Processamento:**
1. Status: `DIMINUICAO`
2. Diferenças: Total=-20
3. Não calcular complemento
4. Registrar status e diferença (para auditoria)

---

## 🔍 Considerações Importantes

### 1. Performance

- Processar em lotes se houver muitas escolas
- Usar transações para garantir consistência
- Considerar processamento assíncrono para arquivos grandes

### 2. Auditoria

- Manter histórico de todas as alterações
- Registrar quem fez o upload (quando autenticação estiver implementada)
- Manter logs detalhados

### 3. Integração com Cálculos Existentes

- Complementos não devem afetar cálculos já realizados
- Complementos são aditivos aos valores existentes
- Considerar como integrar complementos nas parcelas futuras

### 4. Validações Adicionais

- Validar que não há complementos duplicados
- Validar que upload base não foi alterado após complemento
- Considerar bloqueio de edição após complemento

---

## 📅 Estimativa de Tempo

| Fase | Tarefas | Estimativa |
|------|---------|------------|
| Fase 1: Modelos | 4 tarefas | 1 dia |
| Fase 2: Repositórios | 4 tarefas | 1 dia |
| Fase 3: Lógica de Negócio | 4 tarefas | 2 dias |
| Fase 4: Service Layer | 4 tarefas | 2 dias |
| Fase 5: Schemas | 3 tarefas | 0.5 dia |
| Fase 6: Rotas | 4 tarefas | 1.5 dias |
| Fase 7: Testes | 4 tarefas | 2 dias |
| Fase 8: Documentação | 4 tarefas | 1 dia |

**Total Estimado:** 11 dias úteis (~2-3 semanas)

---

## 🎓 Guia Didático de Implementação

Esta seção explica passo a passo **onde** inserir cada trecho de código e **por que** fazer isso em cada local específico.

---

### Fase 1: Criando os Modelos de Dados

#### Passo 1.1: Criar arquivo de modelos

**Onde:** `src/modules/features/complemento/models.py` (criar arquivo novo)

**Por quê:** Este arquivo centraliza todas as definições de modelos SQLAlchemy para a feature de complemento, seguindo o padrão do projeto onde cada feature tem seu próprio arquivo `models.py`.

**O que inserir:**

```python
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base
import enum


class StatusComplemento(str, enum.Enum):
    """Enum para status do processamento de complemento."""
    AUMENTO = "AUMENTO"
    SEM_MUDANCA = "SEM_MUDANCA"
    DIMINUICAO = "DIMINUICAO"
    ERRO = "ERRO"


class ComplementoUpload(Base):
    """
    Modelo que representa um upload de planilha complementar.
    
    Armazena metadados sobre o upload e estatísticas do processamento.
    Relaciona-se com o upload base (original) e o upload complementar (novo).
    """
    __tablename__ = "complemento_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    ano_letivo_id = Column(Integer, ForeignKey("anos_letivos.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_base_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_complemento_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # Estatísticas do processamento
    total_escolas_processadas = Column(Integer, default=0)
    escolas_com_aumento = Column(Integer, default=0)
    escolas_sem_mudanca = Column(Integer, default=0)
    escolas_com_diminuicao = Column(Integer, default=0)
    escolas_com_erro = Column(Integer, default=0)
    
    # Relacionamentos
    ano_letivo = relationship("AnoLetivo", back_populates="complemento_uploads")
    upload_base = relationship("Upload", foreign_keys=[upload_base_id])
    upload_complemento = relationship("Upload", foreign_keys=[upload_complemento_id])
    complementos_escola = relationship("ComplementoEscola", back_populates="complemento_upload", 
                                       cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ComplementoUpload(id={self.id}, ano={self.ano_letivo_id}, filename='{self.filename}')>"


class ComplementoEscola(Base):
    """
    Modelo que armazena os dados de complemento por escola.
    
    Para cada escola processada, armazena:
    - Quantidades ANTES (do upload base)
    - Quantidades DEPOIS (do upload complemento)
    - Diferenças calculadas (apenas positivas)
    - Valores calculados do complemento (se houver aumento)
    """
    __tablename__ = "complemento_escolas"
    
    id = Column(Integer, primary_key=True, index=True)
    complemento_upload_id = Column(Integer, ForeignKey("complemento_uploads.id", ondelete="CASCADE"), 
                                   nullable=False, index=True)
    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Quantidades ANTES (snapshot do upload base)
    total_alunos_antes = Column(Integer, default=0)
    fundamental_inicial_antes = Column(Integer, default=0)
    fundamental_final_antes = Column(Integer, default=0)
    fundamental_integral_antes = Column(Integer, default=0)
    profissionalizante_antes = Column(Integer, default=0)
    profissionalizante_integrado_antes = Column(Integer, default=0)
    alternancia_antes = Column(Integer, default=0)
    ensino_medio_integral_antes = Column(Integer, default=0)
    ensino_medio_regular_antes = Column(Integer, default=0)
    especial_fund_regular_antes = Column(Integer, default=0)
    especial_fund_integral_antes = Column(Integer, default=0)
    especial_medio_parcial_antes = Column(Integer, default=0)
    especial_medio_integral_antes = Column(Integer, default=0)
    sala_recurso_antes = Column(Integer, default=0)
    preuni_antes = Column(Integer, default=0)
    
    # Quantidades DEPOIS (do upload complemento)
    total_alunos_depois = Column(Integer, default=0)
    fundamental_inicial_depois = Column(Integer, default=0)
    fundamental_final_depois = Column(Integer, default=0)
    fundamental_integral_depois = Column(Integer, default=0)
    profissionalizante_depois = Column(Integer, default=0)
    profissionalizante_integrado_depois = Column(Integer, default=0)
    alternancia_depois = Column(Integer, default=0)
    ensino_medio_integral_depois = Column(Integer, default=0)
    ensino_medio_regular_depois = Column(Integer, default=0)
    especial_fund_regular_depois = Column(Integer, default=0)
    especial_fund_integral_depois = Column(Integer, default=0)
    especial_medio_parcial_depois = Column(Integer, default=0)
    especial_medio_integral_depois = Column(Integer, default=0)
    sala_recurso_depois = Column(Integer, default=0)
    preuni_depois = Column(Integer, default=0)
    
    # Diferenças calculadas (apenas valores positivos para cálculo)
    total_alunos_diferenca = Column(Integer, default=0)
    fundamental_inicial_diferenca = Column(Integer, default=0)
    fundamental_final_diferenca = Column(Integer, default=0)
    fundamental_integral_diferenca = Column(Integer, default=0)
    profissionalizante_diferenca = Column(Integer, default=0)
    profissionalizante_integrado_diferenca = Column(Integer, default=0)
    alternancia_diferenca = Column(Integer, default=0)
    ensino_medio_integral_diferenca = Column(Integer, default=0)
    ensino_medio_regular_diferenca = Column(Integer, default=0)
    especial_fund_regular_diferenca = Column(Integer, default=0)
    especial_fund_integral_diferenca = Column(Integer, default=0)
    especial_medio_parcial_diferenca = Column(Integer, default=0)
    especial_medio_integral_diferenca = Column(Integer, default=0)
    sala_recurso_diferenca = Column(Integer, default=0)
    preuni_diferenca = Column(Integer, default=0)
    
    # Status do processamento
    status = Column(SQLEnum(StatusComplemento), nullable=False, default=StatusComplemento.SEM_MUDANCA)
    
    # Valores calculados do complemento (apenas se houve aumento)
    valor_complemento_gestao = Column(Float, default=0.0)
    valor_complemento_projeto = Column(Float, default=0.0)
    valor_complemento_kit_escolar = Column(Float, default=0.0)
    valor_complemento_uniforme = Column(Float, default=0.0)
    valor_complemento_merenda = Column(Float, default=0.0)
    valor_complemento_sala_recurso = Column(Float, default=0.0)
    valor_complemento_preuni = Column(Float, default=0.0)
    valor_complemento_total = Column(Float, default=0.0, index=True)
    
    # Data de processamento
    processed_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relacionamentos
    complemento_upload = relationship("ComplementoUpload", back_populates="complementos_escola")
    escola = relationship("Escola", back_populates="complementos")
    
    def __repr__(self):
        return f"<ComplementoEscola(escola_id={self.escola_id}, status={self.status.value}, valor={self.valor_complemento_total})>"
```

**Motivo:** Os modelos SQLAlchemy definem a estrutura das tabelas no banco de dados. Eles são a base para todo o sistema de persistência e devem ser criados primeiro para que as migrações possam ser geradas.

---

#### Passo 1.2: Atualizar modelo Escola para relacionamento

**Onde:** `src/modules/features/escolas/models.py` (adicionar ao modelo existente)

**Por quê:** Precisamos adicionar o relacionamento reverso para que possamos navegar de uma `Escola` para seus `ComplementoEscola` relacionados.

**O que inserir:** No modelo `Escola`, dentro da seção de relacionamentos (após a linha com `liberacoes_projetos`):

```python
    # Relacionamento com complementos
    complementos = relationship(
        "ComplementoEscola",
        back_populates="escola",
        cascade="all, delete-orphan"
    )
```

**Motivo:** O SQLAlchemy precisa do relacionamento bidirecional (`back_populates`) para funcionar corretamente. Isso permite acessar `escola.complementos` e `complemento.escola`.

---

#### Passo 1.3: Atualizar modelo AnoLetivo para relacionamento

**Onde:** `src/modules/features/anos/models.py` (adicionar ao modelo existente)

**Por quê:** Similar ao passo anterior, precisamos do relacionamento reverso para navegar de um `AnoLetivo` para seus `ComplementoUpload`.

**O que inserir:** No modelo `AnoLetivo`, dentro da seção de relacionamentos:

```python
    # Relacionamento com complementos
    complemento_uploads = relationship(
        "ComplementoUpload",
        back_populates="ano_letivo",
        cascade="all, delete-orphan"
    )
```

**Motivo:** Mantém a consistência dos relacionamentos e permite consultas como "todos os complementos de um ano letivo".

---

#### Passo 1.4: Criar arquivo __init__.py do módulo complemento

**Onde:** `src/modules/features/complemento/__init__.py` (criar arquivo novo)

**Por quê:** Este arquivo torna o diretório um pacote Python e exporta os componentes principais do módulo, seguindo o padrão usado em outros módulos do projeto.

**O que inserir:**

```python
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento
from .service import ComplementoService
from .repository import ComplementoUploadRepository, ComplementoEscolaRepository

__all__ = [
    "ComplementoUpload",
    "ComplementoEscola", 
    "StatusComplemento",
    "ComplementoService",
    "ComplementoUploadRepository",
    "ComplementoEscolaRepository"
]
```

**Motivo:** Permite importações limpas como `from src.modules.features.complemento import ComplementoService` em vez de caminhos longos.

---

### Fase 2: Criando a Migração Alembic

#### Passo 2.1: Gerar migração

**Onde:** Terminal/Command Prompt

**Por quê:** O Alembic precisa gerar automaticamente a migração baseada nos modelos que criamos.

**Comando:**

```bash
alembic revision --autogenerate -m "criar_tabelas_complemento"
```

**Motivo:** O Alembic compara os modelos SQLAlchemy com o estado atual do banco e gera o script de migração automaticamente.

---

#### Passo 2.2: Revisar e ajustar migração gerada

**Onde:** `alembic/versions/XXXXX_criar_tabelas_complemento.py` (arquivo gerado)

**Por quê:** Às vezes o Alembic não captura todos os detalhes ou precisamos ajustar índices e constraints.

**O que verificar/ajustar:**

1. **Índices:** Certifique-se de que há índices nas foreign keys e campos frequentemente consultados:
   - `complemento_uploads.ano_letivo_id`
   - `complemento_uploads.upload_base_id`
   - `complemento_escolas.escola_id`
   - `complemento_escolas.complemento_upload_id`
   - `complemento_escolas.status`
   - `complemento_escolas.valor_complemento_total`

2. **Constraints:** Verificar se as foreign keys estão com `ondelete="CASCADE"` corretamente.

3. **Tipos de dados:** Verificar se os tipos estão corretos (Integer, Float, String, DateTime, Enum).

**Motivo:** Índices melhoram a performance de consultas. Constraints garantem integridade referencial.

---

#### Passo 2.3: Executar migração

**Onde:** Terminal/Command Prompt

**Por quê:** Aplicar as mudanças no banco de dados.

**Comando:**

```bash
alembic upgrade head
```

**Motivo:** Cria as tabelas físicas no banco de dados PostgreSQL.

---

### Fase 3: Criando os Repositórios

#### Passo 3.1: Criar arquivo de repositório

**Onde:** `src/modules/features/complemento/repository.py` (criar arquivo novo)

**Por quê:** Os repositórios encapsulam toda a lógica de acesso ao banco de dados, seguindo o padrão Repository do projeto. Isso facilita testes e manutenção.

**O que inserir:**

```python
from sqlalchemy.orm import Session
from typing import Optional, List
from src.modules.shared.repositories import BaseRepository
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento


class ComplementoUploadRepository(BaseRepository[ComplementoUpload]):
    """
    Repositório para operações CRUD com ComplementoUpload.
    
    Herda de BaseRepository que já fornece métodos básicos:
    - create, find_by_id, find_all, update, delete
    """
    
    def __init__(self, db: Session):
        super().__init__(ComplementoUpload, db)
    
    def find_by_ano_letivo(self, ano_letivo_id: int) -> List[ComplementoUpload]:
        """Busca todos os complementos de um ano letivo."""
        return self.db.query(ComplementoUpload).filter(
            ComplementoUpload.ano_letivo_id == ano_letivo_id
        ).order_by(ComplementoUpload.upload_date.desc()).all()
    
    def find_by_upload_base(self, upload_base_id: int) -> List[ComplementoUpload]:
        """Busca todos os complementos baseados em um upload específico."""
        return self.db.query(ComplementoUpload).filter(
            ComplementoUpload.upload_base_id == upload_base_id
        ).all()


class ComplementoEscolaRepository(BaseRepository[ComplementoEscola]):
    """
    Repositório para operações CRUD com ComplementoEscola.
    """
    
    def __init__(self, db: Session):
        super().__init__(ComplementoEscola, db)
    
    def find_by_complemento_upload(self, complemento_upload_id: int) -> List[ComplementoEscola]:
        """Busca todos os complementos de escolas de um upload de complemento."""
        return self.db.query(ComplementoEscola).filter(
            ComplementoEscola.complemento_upload_id == complemento_upload_id
        ).all()
    
    def find_by_escola(self, escola_id: int) -> List[ComplementoEscola]:
        """Busca histórico de complementos de uma escola específica."""
        return self.db.query(ComplementoEscola).filter(
            ComplementoEscola.escola_id == escola_id
        ).order_by(ComplementoEscola.processed_at.desc()).all()
    
    def find_by_status(self, complemento_upload_id: int, status: StatusComplemento) -> List[ComplementoEscola]:
        """Busca escolas com um status específico em um complemento."""
        return self.db.query(ComplementoEscola).filter(
            ComplementoEscola.complemento_upload_id == complemento_upload_id,
            ComplementoEscola.status == status
        ).all()
```

**Motivo:** Centraliza todas as consultas ao banco relacionadas a complementos, facilitando manutenção e testes. Herda de `BaseRepository` que já existe no projeto para evitar código duplicado.

---

### Fase 4: Criando Funções Utilitárias

#### Passo 4.1: Criar arquivo de utils

**Onde:** `src/modules/features/complemento/utils.py` (criar arquivo novo)

**Por quê:** As funções utilitárias contêm lógica pura (sem dependências de banco) que pode ser facilmente testada. Elas são reutilizáveis e seguem o princípio de responsabilidade única.

**O que inserir:**

```python
from typing import Dict, Any
import pandas as pd
from src.modules.features.escolas import Escola
from src.modules.features.complemento.models import StatusComplemento
from src.modules.features.calculos.utils import calcular_todas_cotas


def comparar_quantidades(escola_base: Escola, dados_complemento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compara quantidades entre escola base e dados do complemento.
    
    Args:
        escola_base: Objeto Escola com quantidades atuais
        dados_complemento: Dicionário com quantidades do complemento (chaves como "TOTAL", "FUNDAMENTAL INICIAL", etc.)
    
    Returns:
        Dicionário com:
        - status: StatusComplemento (AUMENTO, SEM_MUDANCA, DIMINUICAO)
        - diferencas: Dict com diferenças por modalidade (valores podem ser negativos)
        - quantidades_antes: Dict com snapshot das quantidades antes
        - quantidades_depois: Dict com quantidades do complemento
    """
    # Mapear campos do modelo Escola para nomes das colunas da planilha
    campos_antes = {
        'total_alunos': escola_base.total_alunos or 0,
        'fundamental_inicial': escola_base.fundamental_inicial or 0,
        'fundamental_final': escola_base.fundamental_final or 0,
        'fundamental_integral': escola_base.fundamental_integral or 0,
        'profissionalizante': escola_base.profissionalizante or 0,
        'profissionalizante_integrado': escola_base.profissionalizante_integrado or 0,
        'alternancia': escola_base.alternancia or 0,
        'ensino_medio_integral': escola_base.ensino_medio_integral or 0,
        'ensino_medio_regular': escola_base.ensino_medio_regular or 0,
        'especial_fund_regular': escola_base.especial_fund_regular or 0,
        'especial_fund_integral': escola_base.especial_fund_integral or 0,
        'especial_medio_parcial': escola_base.especial_medio_parcial or 0,
        'especial_medio_integral': escola_base.especial_medio_integral or 0,
        'sala_recurso': escola_base.sala_recurso or 0,
        'preuni': escola_base.preuni or 0,
    }
    
    # Mapear dados do complemento (vindos da planilha)
    campos_depois = {
        'total_alunos': dados_complemento.get('TOTAL', 0),
        'fundamental_inicial': dados_complemento.get('FUNDAMENTAL INICIAL', 0),
        'fundamental_final': dados_complemento.get('FUNDAMENTAL FINAL', 0),
        'fundamental_integral': dados_complemento.get('FUNDAMENTAL INTEGRAL', 0),
        'profissionalizante': dados_complemento.get('PROFISSIONALIZANTE', 0),
        'profissionalizante_integrado': dados_complemento.get('PROFISSIONALIZANTE INTEGRADO', 0),
        'alternancia': dados_complemento.get('ALTERNÂNCIA', 0),
        'ensino_medio_integral': dados_complemento.get('ENSINO MÉDIO INTEGRAL', 0),
        'ensino_medio_regular': dados_complemento.get('ENSINO MÉDIO REGULAR', 0),
        'especial_fund_regular': dados_complemento.get('ESPECIAL FUNDAMENTAL REGULAR', 0),
        'especial_fund_integral': dados_complemento.get('ESPECIAL FUNDAMENTAL INTEGRAL', 0),
        'especial_medio_parcial': dados_complemento.get('ESPECIAL MÉDIO PARCIAL', 0),
        'especial_medio_integral': dados_complemento.get('ESPECIAL MÉDIO INTEGRAL', 0),
        'sala_recurso': dados_complemento.get('SALA DE RECURSO', 0),
        'preuni': dados_complemento.get('PREUNI', 0),
    }
    
    # Calcular diferenças
    diferencas = {}
    tem_aumento = False
    tem_diminuicao = False
    
    for campo in campos_antes.keys():
        antes = campos_antes[campo]
        depois = campos_depois[campo]
        diferenca = depois - antes
        diferencas[campo] = diferenca
        
        if diferenca > 0:
            tem_aumento = True
        elif diferenca < 0:
            tem_diminuicao = True
    
    # Determinar status
    if tem_aumento:
        status = StatusComplemento.AUMENTO
    elif tem_diminuicao:
        status = StatusComplemento.DIMINUICAO
    else:
        status = StatusComplemento.SEM_MUDANCA
    
    return {
        'status': status,
        'diferencas': diferencas,
        'quantidades_antes': campos_antes,
        'quantidades_depois': campos_depois
    }


def calcular_complemento_valores(diferencas: Dict[str, int]) -> Dict[str, float]:
    """
    Calcula valores de complemento apenas para diferenças positivas.
    
    Args:
        diferencas: Dicionário com diferenças por modalidade (valores podem ser negativos)
    
    Returns:
        Dicionário com valores calculados para cada cota PROFIN
    """
    # Criar Series do pandas apenas com diferenças positivas
    # Mapear nomes de campos do modelo para nomes de colunas da planilha
    row_diferenca = pd.Series({
        'TOTAL': max(0, diferencas.get('total_alunos', 0)),
        'FUNDAMENTAL INICIAL': max(0, diferencas.get('fundamental_inicial', 0)),
        'FUNDAMENTAL FINAL': max(0, diferencas.get('fundamental_final', 0)),
        'FUNDAMENTAL INTEGRAL': max(0, diferencas.get('fundamental_integral', 0)),
        'PROFISSIONALIZANTE': max(0, diferencas.get('profissionalizante', 0)),
        'PROFISSIONALIZANTE INTEGRADO': max(0, diferencas.get('profissionalizante_integrado', 0)),
        'ALTERNÂNCIA': max(0, diferencas.get('alternancia', 0)),
        'ENSINO MÉDIO INTEGRAL': max(0, diferencas.get('ensino_medio_integral', 0)),
        'ENSINO MÉDIO REGULAR': max(0, diferencas.get('ensino_medio_regular', 0)),
        'ESPECIAL FUNDAMENTAL REGULAR': max(0, diferencas.get('especial_fund_regular', 0)),
        'ESPECIAL FUNDAMENTAL INTEGRAL': max(0, diferencas.get('especial_fund_integral', 0)),
        'ESPECIAL MÉDIO PARCIAL': max(0, diferencas.get('especial_medio_parcial', 0)),
        'ESPECIAL MÉDIO INTEGRAL': max(0, diferencas.get('especial_medio_integral', 0)),
        'SALA DE RECURSO': max(0, diferencas.get('sala_recurso', 0)),
        'PREUNI': max(0, diferencas.get('preuni', 0)),
        # Campos adicionais necessários para cálculos
        'PROJETOS': 0,  # Não consideramos projetos no complemento
        'INDIGENA & QUILOMBOLA': 'NÃO',  # Não consideramos no complemento
        'REPASSE POR AREA': 0,  # Não consideramos no complemento
        'EPT': None,
        'INEP': None,
    })
    
    # Usar função existente de cálculo
    cotas = calcular_todas_cotas(row_diferenca)
    
    return cotas


def criar_row_diferenca(diferencas: Dict[str, int]) -> pd.Series:
    """
    Cria Series do pandas apenas com diferenças positivas.
    
    Função auxiliar para criar a estrutura esperada pelas funções de cálculo.
    """
    return pd.Series({
        'TOTAL': max(0, diferencas.get('total_alunos', 0)),
        'FUNDAMENTAL INICIAL': max(0, diferencas.get('fundamental_inicial', 0)),
        'FUNDAMENTAL FINAL': max(0, diferencas.get('fundamental_final', 0)),
        'FUNDAMENTAL INTEGRAL': max(0, diferencas.get('fundamental_integral', 0)),
        'PROFISSIONALIZANTE': max(0, diferencas.get('profissionalizante', 0)),
        'PROFISSIONALIZANTE INTEGRADO': max(0, diferencas.get('profissionalizante_integrado', 0)),
        'ALTERNÂNCIA': max(0, diferencas.get('alternancia', 0)),
        'ENSINO MÉDIO INTEGRAL': max(0, diferencas.get('ensino_medio_integral', 0)),
        'ENSINO MÉDIO REGULAR': max(0, diferencas.get('ensino_medio_regular', 0)),
        'ESPECIAL FUNDAMENTAL REGULAR': max(0, diferencas.get('especial_fund_regular', 0)),
        'ESPECIAL FUNDAMENTAL INTEGRAL': max(0, diferencas.get('especial_fund_integral', 0)),
        'ESPECIAL MÉDIO PARCIAL': max(0, diferencas.get('especial_medio_parcial', 0)),
        'ESPECIAL MÉDIO INTEGRAL': max(0, diferencas.get('especial_medio_integral', 0)),
        'SALA DE RECURSO': max(0, diferencas.get('sala_recurso', 0)),
        'PREUNI': max(0, diferencas.get('preuni', 0)),
        'PROJETOS': 0,
        'INDIGENA & QUILOMBOLA': 'NÃO',
        'REPASSE POR AREA': 0,
        'EPT': None,
        'INEP': None,
    })
```

**Motivo:** Essas funções são puras (sem efeitos colaterais) e podem ser testadas facilmente. Elas encapsulam a lógica de comparação e cálculo que será reutilizada pelo service.

---

### Fase 5: Criando o Service Layer

#### Passo 5.1: Criar arquivo de service

**Onde:** `src/modules/features/complemento/service.py` (criar arquivo novo)

**Por quê:** O service contém a lógica de negócio principal, orquestrando repositórios e utils. É aqui que acontece o processamento completo do complemento.

**O que inserir:**

```python
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from io import BytesIO
import pandas as pd
from src.core.logging_config import logger
from src.core.database import transaction
from src.core.exceptions import UploadNaoEncontradoException
from src.modules.features.anos import obter_ano_letivo
from src.modules.features.uploads import UploadService, obter_ou_criar_upload_ativo
from src.modules.features.escolas.repository import EscolaRepository
from src.modules.features.uploads.repository import UploadRepository
from .repository import ComplementoUploadRepository, ComplementoEscolaRepository
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento
from .utils import comparar_quantidades, calcular_complemento_valores
from src.modules.shared.utils import obter_texto, obter_quantidade


class ComplementoService:
    """
    Service para processamento de complementos de alunos.
    
    Responsável por:
    - Processar planilhas complementares
    - Comparar quantidades
    - Calcular valores de complemento
    - Persistir resultados
    """
    
    @staticmethod
    def obter_upload_base(
        db: Session,
        ano_letivo_id: Optional[int] = None,
        upload_base_id: Optional[int] = None
    ):
        """
        Obtém o upload base para comparação.
        
        Se upload_base_id for fornecido, usa ele.
        Caso contrário, busca o upload ativo do ano letivo.
        """
        if upload_base_id:
            upload_repo = UploadRepository(db)
            upload = upload_repo.find_by_id(upload_base_id)
            if not upload:
                raise UploadNaoEncontradoException(upload_id=upload_base_id)
            return upload
        
        # Buscar upload ativo
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)
        upload = UploadService.obter_upload_unico(db, ano_id)
        
        upload_repo = UploadRepository(db)
        return upload_repo.find_by_id(upload.id)
    
    @staticmethod
    def processar_planilha_complemento(
        db: Session,
        file_contents: bytes,
        filename: str,
        ano_letivo_id: Optional[int] = None,
        upload_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processa planilha complementar e calcula complementos.
        
        Fluxo:
        1. Identifica upload base
        2. Processa planilha complementar
        3. Compara escola por escola
        4. Calcula complementos quando há aumento
        5. Salva resultados
        """
        ano_letivo, ano_id = obter_ano_letivo(db, ano_letivo_id)
        logger.info(f"PROCESSANDO COMPLEMENTO PARA ANO LETIVO: {ano_letivo.ano}")
        
        # 1. Obter upload base
        upload_base = ComplementoService.obter_upload_base(db, ano_id, upload_base_id)
        logger.info(f"Upload base ID: {upload_base.id}, Filename: {upload_base.filename}")
        
        # 2. Processar planilha complementar
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_contents))
        else:
            df = pd.read_excel(BytesIO(file_contents))
        
        logger.info(f"Planilha complementar: {filename}, Total de linhas: {len(df)}")
        
        # 3. Criar upload temporário para planilha complementar (opcional, para rastreamento)
        upload_complemento = obter_ou_criar_upload_ativo(db, ano_id, f"complemento_{filename}")
        db.flush()
        
        # 4. Obter escolas do upload base
        escola_repo = EscolaRepository(db)
        escolas_base = escola_repo.find_by_upload_id(upload_base.id)
        mapa_escolas_base = {
            (e.nome_uex.strip().upper(), (e.dre or "").strip().upper()): e
            for e in escolas_base
        }
        
        logger.info(f"Escolas no upload base: {len(escolas_base)}")
        
        # 5. Processar comparações
        complemento_repo = ComplementoUploadRepository(db)
        complemento_escola_repo = ComplementoEscolaRepository(db)
        
        resultados = []
        escolas_com_aumento = 0
        escolas_sem_mudanca = 0
        escolas_com_diminuicao = 0
        escolas_com_erro = 0
        valor_total_complemento = 0.0
        
        with transaction(db):
            # Criar registro de ComplementoUpload
            complemento_upload = complemento_repo.create(
                ano_letivo_id=ano_id,
                upload_base_id=upload_base.id,
                upload_complemento_id=upload_complemento.id,
                filename=filename,
                total_escolas_processadas=0,
                escolas_com_aumento=0,
                escolas_sem_mudanca=0,
                escolas_com_diminuicao=0,
                escolas_com_erro=0
            )
            db.flush()
            
            # Processar cada linha da planilha complementar
            for idx, row in df.iterrows():
                try:
                    nome_escola = (
                        row.get('NOME DA UEX') or 
                        row.get('nome') or 
                        row.get('Escola') or 
                        f"Escola {idx + 1}"
                    )
                    nome_escola = str(nome_escola).strip()
                    dre_val = obter_texto(row, "DRE", None) or ""
                    dre_val = dre_val.strip()
                    
                    chave_escola = (nome_escola.upper(), dre_val.upper())
                    escola_base = mapa_escolas_base.get(chave_escola)
                    
                    if not escola_base:
                        logger.warning(f"Escola não encontrada: {nome_escola} (DRE: {dre_val})")
                        escolas_com_erro += 1
                        continue
                    
                    # Extrair dados do complemento
                    dados_complemento = {
                        'TOTAL': obter_quantidade(row, "TOTAL"),
                        'FUNDAMENTAL INICIAL': obter_quantidade(row, "FUNDAMENTAL INICIAL"),
                        'FUNDAMENTAL FINAL': obter_quantidade(row, "FUNDAMENTAL FINAL"),
                        'FUNDAMENTAL INTEGRAL': obter_quantidade(row, "FUNDAMENTAL INTEGRAL"),
                        'PROFISSIONALIZANTE': obter_quantidade(row, "PROFISSIONALIZANTE"),
                        'PROFISSIONALIZANTE INTEGRADO': obter_quantidade(row, "PROFISSIONALIZANTE INTEGRADO"),
                        'ALTERNÂNCIA': obter_quantidade(row, "ALTERNÂNCIA"),
                        'ENSINO MÉDIO INTEGRAL': obter_quantidade(row, "ENSINO MÉDIO INTEGRAL"),
                        'ENSINO MÉDIO REGULAR': obter_quantidade(row, "ENSINO MÉDIO REGULAR"),
                        'ESPECIAL FUNDAMENTAL REGULAR': obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR"),
                        'ESPECIAL FUNDAMENTAL INTEGRAL': obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL"),
                        'ESPECIAL MÉDIO PARCIAL': obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL"),
                        'ESPECIAL MÉDIO INTEGRAL': obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL"),
                        'SALA DE RECURSO': obter_quantidade(row, "SALA DE RECURSO"),
                        'PREUNI': obter_quantidade(row, "PREUNI"),
                    }
                    
                    # Comparar quantidades
                    comparacao = comparar_quantidades(escola_base, dados_complemento)
                    status = comparacao['status']
                    
                    # Calcular valores se houver aumento
                    valores_complemento = {}
                    if status == StatusComplemento.AUMENTO:
                        valores_complemento = calcular_complemento_valores(comparacao['diferencas'])
                        valor_total_complemento += valores_complemento.get('valor_total', 0.0)
                        escolas_com_aumento += 1
                    elif status == StatusComplemento.SEM_MUDANCA:
                        escolas_sem_mudanca += 1
                    elif status == StatusComplemento.DIMINUICAO:
                        escolas_com_diminuicao += 1
                    
                    # Criar ComplementoEscola
                    diferencas = comparacao['diferencas']
                    quantidades_antes = comparacao['quantidades_antes']
                    quantidades_depois = comparacao['quantidades_depois']
                    
                    complemento_escola = complemento_escola_repo.create(
                        complemento_upload_id=complemento_upload.id,
                        escola_id=escola_base.id,
                        # Quantidades antes
                        total_alunos_antes=quantidades_antes['total_alunos'],
                        fundamental_inicial_antes=quantidades_antes['fundamental_inicial'],
                        fundamental_final_antes=quantidades_antes['fundamental_final'],
                        fundamental_integral_antes=quantidades_antes['fundamental_integral'],
                        profissionalizante_antes=quantidades_antes['profissionalizante'],
                        profissionalizante_integrado_antes=quantidades_antes['profissionalizante_integrado'],
                        alternancia_antes=quantidades_antes['alternancia'],
                        ensino_medio_integral_antes=quantidades_antes['ensino_medio_integral'],
                        ensino_medio_regular_antes=quantidades_antes['ensino_medio_regular'],
                        especial_fund_regular_antes=quantidades_antes['especial_fund_regular'],
                        especial_fund_integral_antes=quantidades_antes['especial_fund_integral'],
                        especial_medio_parcial_antes=quantidades_antes['especial_medio_parcial'],
                        especial_medio_integral_antes=quantidades_antes['especial_medio_integral'],
                        sala_recurso_antes=quantidades_antes['sala_recurso'],
                        preuni_antes=quantidades_antes['preuni'],
                        # Quantidades depois
                        total_alunos_depois=quantidades_depois['total_alunos'],
                        fundamental_inicial_depois=quantidades_depois['fundamental_inicial'],
                        fundamental_final_depois=quantidades_depois['fundamental_final'],
                        fundamental_integral_depois=quantidades_depois['fundamental_integral'],
                        profissionalizante_depois=quantidades_depois['profissionalizante'],
                        profissionalizante_integrado_depois=quantidades_depois['profissionalizante_integrado'],
                        alternancia_depois=quantidades_depois['alternancia'],
                        ensino_medio_integral_depois=quantidades_depois['ensino_medio_integral'],
                        ensino_medio_regular_depois=quantidades_depois['ensino_medio_regular'],
                        especial_fund_regular_depois=quantidades_depois['especial_fund_regular'],
                        especial_fund_integral_depois=quantidades_depois['especial_fund_integral'],
                        especial_medio_parcial_depois=quantidades_depois['especial_medio_parcial'],
                        especial_medio_integral_depois=quantidades_depois['especial_medio_integral'],
                        sala_recurso_depois=quantidades_depois['sala_recurso'],
                        preuni_depois=quantidades_depois['preuni'],
                        # Diferenças (apenas positivas para cálculo)
                        total_alunos_diferenca=max(0, diferencas['total_alunos']),
                        fundamental_inicial_diferenca=max(0, diferencas['fundamental_inicial']),
                        fundamental_final_diferenca=max(0, diferencas['fundamental_final']),
                        fundamental_integral_diferenca=max(0, diferencas['fundamental_integral']),
                        profissionalizante_diferenca=max(0, diferencas['profissionalizante']),
                        profissionalizante_integrado_diferenca=max(0, diferencas['profissionalizante_integrado']),
                        alternancia_diferenca=max(0, diferencas['alternancia']),
                        ensino_medio_integral_diferenca=max(0, diferencas['ensino_medio_integral']),
                        ensino_medio_regular_diferenca=max(0, diferencas['ensino_medio_regular']),
                        especial_fund_regular_diferenca=max(0, diferencas['especial_fund_regular']),
                        especial_fund_integral_diferenca=max(0, diferencas['especial_fund_integral']),
                        especial_medio_parcial_diferenca=max(0, diferencas['especial_medio_parcial']),
                        especial_medio_integral_diferenca=max(0, diferencas['especial_medio_integral']),
                        sala_recurso_diferenca=max(0, diferencas['sala_recurso']),
                        preuni_diferenca=max(0, diferencas['preuni']),
                        # Status e valores
                        status=status,
                        valor_complemento_gestao=valores_complemento.get('profin_gestao', 0.0),
                        valor_complemento_projeto=valores_complemento.get('profin_projeto', 0.0),
                        valor_complemento_kit_escolar=valores_complemento.get('profin_kit_escolar', 0.0),
                        valor_complemento_uniforme=valores_complemento.get('profin_uniforme', 0.0),
                        valor_complemento_merenda=valores_complemento.get('profin_merenda', 0.0),
                        valor_complemento_sala_recurso=valores_complemento.get('profin_sala_recurso', 0.0),
                        valor_complemento_preuni=valores_complemento.get('profin_preuni', 0.0),
                        valor_complemento_total=valores_complemento.get('valor_total', 0.0),
                    )
                    
                    resultados.append({
                        'escola_id': escola_base.id,
                        'nome_uex': escola_base.nome_uex,
                        'status': status.value,
                        'valor_complemento_total': valores_complemento.get('valor_total', 0.0)
                    })
                    
                except Exception as e:
                    logger.error(f"Erro ao processar linha {idx + 1}: {str(e)}")
                    escolas_com_erro += 1
                    continue
            
            # Atualizar estatísticas do ComplementoUpload
            total_processadas = len(resultados) + escolas_com_erro
            complemento_repo.update(
                complemento_upload,
                total_escolas_processadas=total_processadas,
                escolas_com_aumento=escolas_com_aumento,
                escolas_sem_mudanca=escolas_sem_mudanca,
                escolas_com_diminuicao=escolas_com_diminuicao,
                escolas_com_erro=escolas_com_erro
            )
        
        logger.info("="*60)
        logger.info("COMPLEMENTO PROCESSADO")
        logger.info(f"Total processadas: {total_processadas}")
        logger.info(f"  - Com aumento: {escolas_com_aumento}")
        logger.info(f"  - Sem mudança: {escolas_sem_mudanca}")
        logger.info(f"  - Com diminuição: {escolas_com_diminuicao}")
        logger.info(f"  - Com erro: {escolas_com_erro}")
        logger.info(f"Valor total complemento: R$ {valor_total_complemento:,.2f}")
        logger.info("="*60)
        
        return {
            "complemento_upload_id": complemento_upload.id,
            "ano_letivo_id": ano_id,
            "ano_letivo": ano_letivo.ano,
            "filename": filename,
            "total_escolas_processadas": total_processadas,
            "escolas_com_aumento": escolas_com_aumento,
            "escolas_sem_mudanca": escolas_sem_mudanca,
            "escolas_com_diminuicao": escolas_com_diminuicao,
            "escolas_com_erro": escolas_com_erro,
            "valor_complemento_total": valor_total_complemento,
            "resultados": resultados
        }
```

**Motivo:** O service orquestra todo o fluxo de processamento, usando os repositórios para persistência e as funções utils para lógica pura. É a camada que conecta tudo.

---

### Fase 6: Criando os Schemas Pydantic

#### Passo 6.1: Criar arquivo de schemas

**Onde:** `src/modules/schemas/complemento.py` (criar arquivo novo)

**Por quê:** Os schemas Pydantic validam e serializam dados nas requisições e respostas da API. Eles garantem que os dados estão no formato correto antes de serem processados.

**O que inserir:**

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UploadComplementoRequest(BaseModel):
    """Schema para request de upload de complemento."""
    ano_letivo_id: Optional[int] = None
    upload_base_id: Optional[int] = None


class ComplementoEscolaInfo(BaseModel):
    """Informações de complemento de uma escola."""
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    status: str  # 'AUMENTO', 'SEM_MUDANCA', 'DIMINUICAO'
    
    # Quantidades antes/depois
    total_alunos_antes: int
    total_alunos_depois: int
    total_alunos_diferenca: int
    
    # Valores calculados (se houver aumento)
    valor_complemento_total: Optional[float] = None
    
    # Detalhes por modalidade (opcional)
    detalhes_modalidades: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class UploadComplementoResponse(BaseModel):
    """Response do upload de complemento."""
    success: bool
    complemento_upload_id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    
    # Estatísticas
    total_escolas_processadas: int
    escolas_com_aumento: int
    escolas_sem_mudanca: int
    escolas_com_diminuicao: int
    escolas_com_erro: int
    
    # Valor total de complemento calculado
    valor_complemento_total: float
    
    # Lista de escolas (opcional)
    escolas: Optional[List[ComplementoEscolaInfo]] = None
    erros: Optional[List[Dict[str, Any]]] = None


class ComplementoUploadDetailResponse(BaseModel):
    """Response detalhado de um complemento upload."""
    complemento_upload_id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    upload_base_id: int
    upload_complemento_id: int
    
    # Estatísticas
    total_escolas_processadas: int
    escolas_com_aumento: int
    escolas_sem_mudanca: int
    escolas_com_diminuicao: int
    escolas_com_erro: int
    
    # Valor total
    valor_complemento_total: float
    
    # Lista de escolas
    escolas: List[ComplementoEscolaInfo]
    
    class Config:
        from_attributes = True


class ComplementoEscolaHistoricoResponse(BaseModel):
    """Response do histórico de complementos de uma escola."""
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    complementos: List[Dict[str, Any]]
```

**Motivo:** Os schemas garantem validação automática de tipos e formatos, melhorando a segurança e a qualidade da API. Eles também geram documentação automática no Swagger.

---

### Fase 7: Criando as Rotas da API

#### Passo 7.1: Criar arquivo de rotas

**Onde:** `src/modules/features/complemento/routes.py` (criar arquivo novo)

**Por quê:** As rotas definem os endpoints HTTP da API. Elas recebem requisições, chamam os services e retornam respostas formatadas.

**O que inserir:**

```python
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from src.core.database import get_db
from src.core.logging_config import logger
from .service import ComplementoService
from .repository import ComplementoUploadRepository, ComplementoEscolaRepository
from src.modules.schemas.complemento import (
    UploadComplementoResponse,
    ComplementoUploadDetailResponse,
    ComplementoEscolaHistoricoResponse
)


complemento_router = APIRouter()


@complemento_router.post("/upload", response_model=UploadComplementoResponse, tags=["Complemento"])
async def upload_complemento(
    file: UploadFile = File(...),
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (padrão: ano ativo)"),
    upload_base_id: Optional[int] = Query(None, description="ID do upload base (padrão: upload ativo)"),
    db: Session = Depends(get_db)
) -> UploadComplementoResponse:
    """
    Faz upload de planilha complementar e processa complementos.
    
    Compara as quantidades da planilha com o upload base e calcula
    complementos apenas para escolas que tiveram aumento de alunos.
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx, .xls ou .csv)")
    
    try:
        contents = await file.read()
        resultado = ComplementoService.processar_planilha_complemento(
            db, contents, file.filename, ano_letivo_id, upload_base_id
        )
        
        # Buscar complemento_upload para obter upload_date
        complemento_repo = ComplementoUploadRepository(db)
        complemento_upload = complemento_repo.find_by_id(resultado["complemento_upload_id"])
        
        return UploadComplementoResponse(
            success=True,
            complemento_upload_id=resultado["complemento_upload_id"],
            ano_letivo_id=resultado["ano_letivo_id"],
            ano_letivo=resultado["ano_letivo"],
            filename=resultado["filename"],
            upload_date=complemento_upload.upload_date,
            total_escolas_processadas=resultado["total_escolas_processadas"],
            escolas_com_aumento=resultado["escolas_com_aumento"],
            escolas_sem_mudanca=resultado["escolas_sem_mudanca"],
            escolas_com_diminuicao=resultado["escolas_com_diminuicao"],
            escolas_com_erro=resultado["escolas_com_erro"],
            valor_complemento_total=resultado["valor_complemento_total"],
            escolas=None,  # Opcional, pode ser implementado depois
            erros=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("ERRO NO UPLOAD DE COMPLEMENTO")
        raise HTTPException(status_code=500, detail=f"Erro ao processar complemento: {str(e)}")


@complemento_router.get("/{complemento_upload_id}", response_model=ComplementoUploadDetailResponse, tags=["Complemento"])
def obter_complemento_detalhado(
    complemento_upload_id: int,
    db: Session = Depends(get_db)
) -> ComplementoUploadDetailResponse:
    """
    Obtém detalhes de um upload de complemento específico.
    """
    complemento_repo = ComplementoUploadRepository(db)
    complemento_upload = complemento_repo.find_by_id(complemento_upload_id)
    
    if not complemento_upload:
        raise HTTPException(status_code=404, detail="Complemento não encontrado")
    
    complemento_escola_repo = ComplementoEscolaRepository(db)
    complementos_escola = complemento_escola_repo.find_by_complemento_upload(complemento_upload_id)
    
    # Calcular valor total
    valor_total = sum(c.valor_complemento_total or 0.0 for c in complementos_escola)
    
    # Mapear para schema
    escolas_info = []
    for ce in complementos_escola:
        escolas_info.append({
            'escola_id': ce.escola_id,
            'nome_uex': ce.escola.nome_uex,
            'dre': ce.escola.dre,
            'status': ce.status.value,
            'total_alunos_antes': ce.total_alunos_antes,
            'total_alunos_depois': ce.total_alunos_depois,
            'total_alunos_diferenca': ce.total_alunos_diferenca,
            'valor_complemento_total': ce.valor_complemento_total
        })
    
    return ComplementoUploadDetailResponse(
        complemento_upload_id=complemento_upload.id,
        ano_letivo_id=complemento_upload.ano_letivo_id,
        ano_letivo=complemento_upload.ano_letivo.ano,
        filename=complemento_upload.filename,
        upload_date=complemento_upload.upload_date,
        upload_base_id=complemento_upload.upload_base_id,
        upload_complemento_id=complemento_upload.upload_complemento_id,
        total_escolas_processadas=complemento_upload.total_escolas_processadas,
        escolas_com_aumento=complemento_upload.escolas_com_aumento,
        escolas_sem_mudanca=complemento_upload.escolas_sem_mudanca,
        escolas_com_diminuicao=complemento_upload.escolas_com_diminuicao,
        escolas_com_erro=complemento_upload.escolas_com_erro,
        valor_complemento_total=valor_total,
        escolas=escolas_info
    )


@complemento_router.get("/escola/{escola_id}", response_model=ComplementoEscolaHistoricoResponse, tags=["Complemento"])
def obter_complementos_escola(
    escola_id: int,
    db: Session = Depends(get_db)
) -> ComplementoEscolaHistoricoResponse:
    """
    Obtém histórico de complementos de uma escola específica.
    """
    from src.modules.features.escolas.repository import EscolaRepository
    
    escola_repo = EscolaRepository(db)
    escola = escola_repo.find_by_id(escola_id)
    
    if not escola:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    complemento_escola_repo = ComplementoEscolaRepository(db)
    complementos = complemento_escola_repo.find_by_escola(escola_id)
    
    complementos_info = []
    for c in complementos:
        complementos_info.append({
            'complemento_upload_id': c.complemento_upload_id,
            'data': c.processed_at,
            'status': c.status.value,
            'total_alunos_diferenca': c.total_alunos_diferenca,
            'valor_complemento_total': c.valor_complemento_total
        })
    
    return ComplementoEscolaHistoricoResponse(
        escola_id=escola.id,
        nome_uex=escola.nome_uex,
        dre=escola.dre,
        complementos=complementos_info
    )


@complemento_router.get("/", tags=["Complemento"])
def listar_complementos(
    ano_letivo_id: Optional[int] = Query(None, description="Filtrar por ano letivo"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    db: Session = Depends(get_db)
):
    """
    Lista todos os uploads de complemento (com paginação).
    """
    complemento_repo = ComplementoUploadRepository(db)
    
    if ano_letivo_id:
        complementos = complemento_repo.find_by_ano_letivo(ano_letivo_id)
    else:
        complementos = complemento_repo.find_all()
    
    # Paginação simples
    total = len(complementos)
    start = (page - 1) * page_size
    end = start + page_size
    complementos_paginados = complementos[start:end]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "complemento_upload_id": c.id,
                "ano_letivo_id": c.ano_letivo_id,
                "ano_letivo": c.ano_letivo.ano,
                "filename": c.filename,
                "upload_date": c.upload_date,
                "total_escolas_processadas": c.total_escolas_processadas,
                "escolas_com_aumento": c.escolas_com_aumento,
                "valor_complemento_total": sum(ce.valor_complemento_total or 0.0 for ce in c.complementos_escola)
            }
            for c in complementos_paginados
        ]
    }
```

**Motivo:** As rotas são o ponto de entrada da API. Elas recebem requisições HTTP, validam dados com Pydantic, chamam os services e retornam respostas formatadas.

---

#### Passo 7.2: Registrar router no main.py

**Onde:** `main.py` (adicionar import e registro)

**Por quê:** O FastAPI precisa saber sobre as rotas para expô-las na API.

**O que inserir:**

1. **No topo do arquivo**, junto com os outros imports de routers:

```python
from src.modules.features.complemento.routes import complemento_router
```

2. **Na seção de rotas** (após as outras rotas):

```python
app.include_router(complemento_router, prefix="/complemento")
```

**Motivo:** O `main.py` é o ponto central de configuração da aplicação FastAPI. Todas as rotas devem ser registradas aqui para ficarem disponíveis.

---

#### Passo 7.3: Atualizar módulo api/__init__.py

**Onde:** `src/modules/api/__init__.py` (adicionar imports)

**Por quê:** Este arquivo centraliza exports de routers e models para facilitar imports em outros lugares.

**O que inserir:**

1. **Na seção de routers:**

```python
from src.modules.features.complemento.routes import complemento_router
```

E adicionar no `__all__`:

```python
"complemento_router",
```

2. **Na seção de models:**

```python
from src.modules.features.complemento import ComplementoUpload, ComplementoEscola
```

E adicionar no `__all__`:

```python
"ComplementoUpload",
"ComplementoEscola",
```

**Motivo:** Mantém a organização centralizada e permite imports limpos como `from src.modules.api import complemento_router`.

---

### Fase 8: Atualizando Documentação

#### Passo 8.1: Criar documentação de rotas

**Onde:** `docs/rotas/DOC_ROTAS_COMPLEMENTO.md` (criar arquivo novo)

**Por quê:** A documentação ajuda outros desenvolvedores e usuários da API a entenderem como usar os endpoints.

**O que inserir:** Documentação detalhada de cada endpoint, seguindo o padrão dos outros arquivos de documentação de rotas.

---

#### Passo 8.2: Atualizar índice de rotas

**Onde:** `docs/rotas/DOC_INDICE_ROTAS.md` (adicionar seção)

**Por quê:** O índice facilita a navegação na documentação.

**O que inserir:** Adicionar seção sobre rotas de complemento.

---

## 🚀 Próximos Passos

1. **Revisar e aprovar** este plano
2. **Criar branch** de desenvolvimento: `feature/complemento-alunos`
3. **Iniciar Fase 1**: Modelos e migração
4. **Revisar código** após cada fase
5. **Testar** em ambiente de desenvolvimento
6. **Documentar** durante o desenvolvimento

---

**Última atualização:** 2025-12-02  
**Responsável:** [A definir]
