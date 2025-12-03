# Documentação - Utilitários

Esta pasta contém a documentação das funções utilitárias genéricas do sistema.

**Nota:** Funções específicas de domínio foram movidas para seus respectivos módulos de features.

**Arquivo:** `src/core/utils.py`

Todas as funções utilitárias estão centralizadas em um único arquivo.

---

## 📚 Documentação Completa

### [📖 Documentação Detalhada de Todas as Funções](DOC_UTILS_COMPLETO.md)

Documentação completa com todas as funções utilitárias, parâmetros, retornos, exemplos e fórmulas.

---

## 📋 Resumo dos Utilitários

### `src/core/utils.py`

Funções auxiliares para processamento de dados, cálculos e divisão de parcelas.

**Seções:**
- Buscas e limpeza
- Processamento de dados
- Cálculos das cotas PROFIN
- Parcelas e ensino

#### `calcular_todas_cotas(row: pd.Series) -> Dict[str, float]`
Calcula todas as cotas PROFIN para uma escola.

**Parâmetros:**
- `row`: Series do pandas com dados da escola

**Retorna:**
- Dicionário com todas as cotas calculadas

---

#### `obter_texto(row: pd.Series, campo: str, default: str = "") -> str`
Obtém texto de uma linha do DataFrame.

---

#### `obter_quantidade(row: pd.Series, campo: str, default: int = 0) -> int`
Obtém quantidade (inteiro) de uma linha do DataFrame.

---

#### `validar_indigena_e_quilombola(row: pd.Series, campo: str) -> str`
Valida e retorna "SIM" ou "NÃO" para campo indígena/quilombola.

---

#### `obter_ano_letivo(db: Session, ano_letivo_id: Optional[int] = None, raise_if_not_found: bool = True) -> Tuple[AnoLetivo, int]`
Determina e retorna o ano letivo baseado no ID fornecido ou no ano ativo.

**Parâmetros:**
- `db`: Sessão do banco de dados
- `ano_letivo_id`: ID do ano letivo (opcional)
- `raise_if_not_found`: Se True, lança exceção se não encontrar

**Retorna:**
- Tupla (AnoLetivo, ano_letivo_id)

---

---

**Nota:** A função `obter_ou_criar_upload_ativo()` foi movida para `src/modules/features/uploads/utils.py`

---

### Funções de Parcelas

**Nota:** As funções de parcelas foram movidas para `src/modules/features/parcelas/utils.py`

#### `calcular_porcentagens_ensino(escola: Escola) -> Tuple[float, float]`
Calcula a porcentagem de alunos em cada tipo de ensino usando pesos.

**Parâmetros:**
- `escola`: Objeto Escola com dados dos alunos

**Retorna:**
- Tupla (porcentagem_fundamental, porcentagem_medio)

**Pesos Utilizados:**
- Fundamental Inicial: 1.0
- Fundamental Final: 1.10
- Fundamental Integral: 1.40
- Especial Fundamental Regular: 1.0
- Especial Fundamental Integral: 1.40
- Profissionalizante: 1.30
- Alternância: 1.40
- Ensino Médio Integral: 1.40
- Ensino Médio Regular: 1.25
- Especial Médio Parcial: 1.25
- Especial Médio Integral: 1.40

---

#### `dividir_em_parcelas(valor_reais: float) -> Tuple[int, int]`
Divide um valor em duas parcelas iguais (ou quase iguais).

**Parâmetros:**
- `valor_reais`: Valor em reais (float)

**Retorna:**
- Tupla (parcela_1_centavos, parcela_2_centavos) em centavos

---

#### `dividir_parcela_por_ensino(parcela_centavos: int, porcentagem_fundamental: float, porcentagem_medio: float) -> Tuple[int, int]`
Divide uma parcela entre ensino fundamental e médio baseado nas porcentagens.

**Parâmetros:**
- `parcela_centavos`: Valor da parcela em centavos
- `porcentagem_fundamental`: Porcentagem de alunos em fundamental
- `porcentagem_medio`: Porcentagem de alunos em médio

**Retorna:**
- Tupla (valor_fundamental_centavos, valor_medio_centavos)

---

#### `dividir_cota_em_parcelas_por_ensino(valor_cota_reais: float, porcentagem_fundamental: float, porcentagem_medio: float) -> Dict[str, Dict[str, int]]`
Divide uma cota completa em 2 parcelas, e cada parcela por tipo de ensino.

**Parâmetros:**
- `valor_cota_reais`: Valor total da cota em reais
- `porcentagem_fundamental`: Porcentagem de alunos em fundamental
- `porcentagem_medio`: Porcentagem de alunos em médio

**Retorna:**
- Dicionário com estrutura de parcelas por ensino

---

## 📝 Notas

- **Valores em Centavos:** Funções de parcelas trabalham com centavos (inteiros) para evitar problemas com floats
- **Distribuição de Resto:** Centavos restantes são distribuídos de forma determinística
- **Pesos:** Porcentagens são calculadas usando pesos (multiplicadores) para cada modalidade

---

## 🔗 Arquivos Relacionados

- `src/core/utils.py` - Funções utilitárias genéricas
- `src/modules/features/uploads/utils.py` - Utilitários de upload
- `src/modules/features/projetos/utils.py` - Utilitários de projetos
- `src/modules/features/calculos/utils.py` - Funções de cálculo de cotas
- `src/modules/features/parcelas/utils.py` - Funções de parcelas

