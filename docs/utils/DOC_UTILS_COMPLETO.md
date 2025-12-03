# Documentação Completa - Funções Utilitárias

**Arquivo:** `src/core/utils.py`

---

## 📋 Visão Geral

Funções auxiliares genéricas para processamento de dados e operações comuns do sistema.

**Nota:** Funções específicas de domínio foram movidas para seus respectivos módulos:
- Funções de upload: `src/modules/features/uploads/utils.py`
- Funções de projetos: `src/modules/features/projetos/utils.py`
- Funções de cálculos: `src/modules/features/calculos/utils.py`
- Funções de parcelas: `src/modules/features/parcelas/utils.py`

---

## 📁 src/core/utils.py

### 🔍 Funções de Busca e Validação

---

#### `obter_ano_letivo(db: Session, ano_letivo_id: Optional[int] = None, raise_if_not_found: bool = True) -> Union[Tuple[AnoLetivo, int], Tuple[None, None]]`

Determina e retorna o ano letivo baseado no ID fornecido ou no ano ativo.

**Parâmetros:**
- `db`: Sessão do banco de dados
- `ano_letivo_id`: ID do ano letivo (opcional). Se `None`, busca o ano ativo
- `raise_if_not_found`: Se `True`, lança exceção se não encontrar. Se `False`, retorna `None`

**Retorna:**
- `Tuple[AnoLetivo, int]`: Tupla com o ano letivo e seu ID, ou `(None, None)` se não encontrado e `raise_if_not_found=False`

**Comportamento:**
- Se `ano_letivo_id` for `None`: busca o ano letivo com status `ATIVO`
- Se `ano_letivo_id` for fornecido: busca o ano letivo específico
- Se não encontrar e `raise_if_not_found=True`: lança `HTTPException` (400 ou 404)
- Se não encontrar e `raise_if_not_found=False`: retorna `(None, None)`

**Exemplo:**
```python
# Buscar ano ativo
ano_letivo, ano_id = obter_ano_letivo(db)

# Buscar ano específico
ano_letivo, ano_id = obter_ano_letivo(db, ano_letivo_id=2)

# Buscar sem lançar exceção
ano_letivo, ano_id = obter_ano_letivo(db, raise_if_not_found=False)
if ano_letivo is None:
    print("Ano não encontrado")
```

---

### 📊 Funções de Processamento de Dados

#### `obter_quantidade(row: pd.Series, coluna: str) -> int`

Obtém quantidade (inteiro) de uma linha do DataFrame.

**Parâmetros:**
- `row`: Series do pandas (linha do DataFrame)
- `coluna`: Nome da coluna

**Retorna:**
- `int`: Valor inteiro ou `0` se inválido/NaN

**Comportamento:**
- Converte para inteiro
- Retorna `0` se valor for `NaN`, `None` ou não conversível

**Exemplo:**
```python
total = obter_quantidade(row, "TOTAL")
fund_inicial = obter_quantidade(row, "FUNDAMENTAL INICIAL")
```

---

#### `obter_texto(row: pd.Series, coluna: str, default: str = "") -> str`

Obtém texto de uma linha do DataFrame.

**Parâmetros:**
- `row`: Series do pandas (linha do DataFrame)
- `coluna`: Nome da coluna
- `default`: Valor padrão se não encontrar

**Retorna:**
- `str`: Valor como string ou `default` se inválido/NaN

**Exemplo:**
```python
nome = obter_texto(row, "NOME DA UEX")
dre = obter_texto(row, "DRE", None)
```

---

#### `validar_indigena_e_quilombola(row: pd.Series, coluna: str) -> str`

Valida e retorna "SIM" ou "NÃO" para campo indígena/quilombola.

**Parâmetros:**
- `row`: Series do pandas (linha do DataFrame)
- `coluna`: Nome da coluna

**Retorna:**
- `str`: "SIM" ou "NÃO" (padrão: "NÃO")

**Comportamento:**
- Converte para string
- Retorna "NÃO" se valor for inválido/NaN

**Exemplo:**
```python
indigena = validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA")
```

---

### 💰 Funções de Cálculo de Cotas

#### `calcular_profin_custeio(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Custeio.

**Fórmula:**
```
Valor Fixo: R$ 2.000,00
Valor Variável = (
  (fund_inicial * 1.0) +
  (fund_final * 1.10) +
  (fund_integral * 1.4) +
  (profissionalizante * 1.3) +
  ((alternancia * 1.4) * 4.0) +
  (medio_integral * 1.4) +
  (medio_regular * 1.25) +
  ((esp_fund_regular * 1.0) * 2.0) +
  ((esp_fund_integral * 1.4) * 2.0) +
  ((esp_medio_parcial * 1.25) * 2.0) +
  ((esp_medio_integral * 1.4) * 2.0)
) * 90.0

Total = Valor Fixo + Valor Variável
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_projeto(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Projeto.

**Regras:**
- Se `quantidade_aluno <= 500`:
  - Com ensino integral: R$ 10.000,00 (5000 * 2)
  - Sem ensino integral: R$ 5.000,00
- Se `500 < quantidade_aluno <= 1000`:
  - Com ensino integral: R$ 20.000,00 (10000 * 2)
  - Sem ensino integral: R$ 10.000,00
- Se `quantidade_aluno > 1000`:
  - Com ensino integral: R$ 30.000,00 (15000 * 2)
  - Sem ensino integral: R$ 15.000,00

**Ensino Integral:** Verifica se tem alunos em:
- Fundamental Integral
- Ensino Médio Integral
- Especial Fundamental Integral
- Especial Médio Integral

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_kit_escolar(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Kit Escolar.

**Fórmula:**
```
Valor = total_alunos * 150
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_uniforme(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Uniforme.

**Fórmula:**
```
Valor = total_alunos * 60
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_merenda(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Merenda.

**Fórmula:**
```
Valor per capita: R$ 35,00

Valor Base = (
  (fund_inicial + fund_final + profissionalizante + medio_regular) * 35.0 +
  (fund_integral + medio_integral + esp_fund_integral + esp_medio_integral + 
   esp_fund_regular + esp_medio_parcial) * 2 * 35.0 +
  (alternancia * 35.0 * 4)
)

Se indígena/quilombola = "SIM":
  Valor = Valor Base * 2
Senão:
  Valor = Valor Base
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_sala_recurso(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Sala de Recurso.

**Fórmula:**
```
Se sala_recurso > 0:
  Valor = (sala_recurso * 180) + 2000
Senão:
  Valor = 0
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_climatizacao(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Climatização.

**Fórmula:**
```
Valor = quantidade_aparelhos * 300
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_preuni(row: pd.Series) -> float`

Calcula o valor da cota PROFIN PREUNI.

**Fórmula:**
```
Valor = quantidade_alunos_preuni * 90
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_profin_permanente(row: pd.Series) -> float`

Calcula o valor da cota PROFIN Permanente.

**Fórmula:**
```
Valor = total_alunos * 110
```

**Retorna:**
- `float`: Valor calculado (arredondado para 2 casas decimais)

---

#### `calcular_todas_cotas(row: pd.Series) -> Dict[str, Any]`

Calcula todas as cotas PROFIN para uma escola.

**Parâmetros:**
- `row`: Series do pandas com dados da escola

**Retorna:**
- `Dict[str, Any]`: Dicionário com todas as cotas e valor total

**Estrutura do Retorno:**
```python
{
  "profin_custeio": float,
  "profin_projeto": float,
  "profin_kit_escolar": float,
  "profin_uniforme": float,
  "profin_merenda": float,
  "profin_sala_recurso": float,
  "profin_permanente": float,
  "profin_climatizacao": float,
  "profin_preuni": float,
  "valor_total": float  # Soma de todas as cotas
}
```

**Exemplo:**
```python
cotas = calcular_todas_cotas(row_series)
print(f"Custeio: R$ {cotas['profin_custeio']:,.2f}")
print(f"Total: R$ {cotas['valor_total']:,.2f}")
```

---

### 📊 Funções de Cálculo de Porcentagens e Divisão de Parcelas

#### `calcular_porcentagens_ensino(escola: Escola) -> Tuple[float, float]`

Calcula a porcentagem de alunos em cada tipo de ensino usando pesos (multiplicadores).

**Parâmetros:**
- `escola`: Objeto Escola com dados dos alunos

**Retorna:**
- `Tuple[float, float]`: Tupla (porcentagem_fundamental, porcentagem_medio)
  - Valores entre 0.0 e 100.0
  - Soma sempre = 100%

**Pesos Utilizados:**

**Fundamental:**
- Fundamental Inicial: 1.0
- Fundamental Final: 1.10
- Fundamental Integral: 1.40
- Especial Fundamental Regular: 1.0
- Especial Fundamental Integral: 1.40

**Médio:**
- Profissionalizante: 1.30
- Alternância: 1.40
- Ensino Médio Integral: 1.40
- Ensino Médio Regular: 1.25
- Especial Médio Parcial: 1.25
- Especial Médio Integral: 1.40

**Fórmula:**
```
Valor_Fundamental = Soma(alunos_fundamental * peso_fundamental)
Valor_Médio = Soma(alunos_médio * peso_médio)
Total_Ponderado = Valor_Fundamental + Valor_Médio

% Fundamental = (Valor_Fundamental / Total_Ponderado) * 100
% Médio = 100% - % Fundamental
```

**Exemplo:**
```python
pct_fund, pct_medio = calcular_porcentagens_ensino(escola)
print(f"Fundamental: {pct_fund}%")
print(f"Médio: {pct_medio}%")
```

---

### 💰 Funções de Divisão de Parcelas

#### `dividir_em_parcelas(valor_reais: float) -> Tuple[int, int]`

Divide um valor em duas parcelas iguais (ou quase iguais).

**Parâmetros:**
- `valor_reais`: Valor em reais (float)

**Retorna:**
- `Tuple[int, int]`: Tupla (parcela_1_centavos, parcela_2_centavos) em centavos

**Algoritmo:**
1. Converte valor para centavos (multiplica por 100 e arredonda)
2. Divide por 2 (divisão inteira)
3. Resto vai para a segunda parcela

**Exemplo:**
```python
# R$ 50.000,00
parcela_1, parcela_2 = dividir_em_parcelas(50000.00)
# Resultado: (2500000, 2500000) centavos
# = R$ 25.000,00 e R$ 25.000,00

# R$ 50.000,01 (valor ímpar)
parcela_1, parcela_2 = dividir_em_parcelas(50000.01)
# Resultado: (2500000, 2500001) centavos
# = R$ 25.000,00 e R$ 25.000,01
```

---

#### `dividir_parcela_por_ensino(parcela_centavos: int, porcentagem_fundamental: float, porcentagem_medio: float) -> Tuple[int, int]`

Divide uma parcela entre ensino fundamental e médio baseado nas porcentagens.

**Parâmetros:**
- `parcela_centavos`: Valor da parcela em centavos (inteiro)
- `porcentagem_fundamental`: Porcentagem de alunos em fundamental (0-100)
- `porcentagem_medio`: Porcentagem de alunos em médio (0-100)

**Retorna:**
- `Tuple[int, int]`: Tupla (valor_fundamental_centavos, valor_medio_centavos)

**Algoritmo:**
1. Calcula valores baseados nas porcentagens
2. Distribui centavos restantes para o tipo com maior porcentagem
3. Se empate, dá para fundamental

**Exemplo:**
```python
# Parcela: R$ 25.000,00 (2.500.000 centavos)
# 52.5% fundamental, 47.5% médio
fund, medio = dividir_parcela_por_ensino(2500000, 52.5, 47.5)
# Resultado: (1312500, 1187500) centavos
# = R$ 13.125,00 e R$ 11.875,00
```

---

#### `dividir_cota_em_parcelas_por_ensino(valor_cota_reais: float, porcentagem_fundamental: float, porcentagem_medio: float) -> Dict[str, Dict[str, int]]`

Divide uma cota completa em 2 parcelas, e cada parcela por tipo de ensino.

**Parâmetros:**
- `valor_cota_reais`: Valor total da cota em reais
- `porcentagem_fundamental`: Porcentagem de alunos em fundamental
- `porcentagem_medio`: Porcentagem de alunos em médio

**Retorna:**
- `Dict[str, Dict[str, int]]`: Dicionário com estrutura de parcelas

**Estrutura do Retorno:**
```python
{
  "parcela_1": {
    "fundamental": int,  # centavos
    "medio": int         # centavos
  },
  "parcela_2": {
    "fundamental": int,  # centavos
    "medio": int         # centavos
  }
}
```

**Exemplo:**
```python
# Cota: R$ 50.000,00
# 52.5% fundamental, 47.5% médio
divisao = dividir_cota_em_parcelas_por_ensino(50000.00, 52.5, 47.5)

# Resultado:
{
  "parcela_1": {
    "fundamental": 1312500,  # R$ 13.125,00
    "medio": 1187500          # R$ 11.875,00
  },
  "parcela_2": {
    "fundamental": 1312500,  # R$ 13.125,00
    "medio": 1187500          # R$ 11.875,00
  }
}
```

---

## 🔧 Uso Combinado

### Exemplo Completo: Calcular e Dividir Parcelas

```python
# 1. Calcular porcentagens
pct_fund, pct_medio = calcular_porcentagens_ensino(escola)

# 2. Obter valor da cota
valor_cota = calculo.profin_custeio  # R$ 50.000,00

# 3. Dividir em parcelas por ensino
divisao = dividir_cota_em_parcelas_por_ensino(
    valor_cota,
    pct_fund,
    pct_medio
)

# 4. Criar registros de parcelas
parcela_1_fund = ParcelasProfin(
    calculo_id=calculo.id,
    tipo_cota=TipoCota.CUSTEIO,
    numero_parcela=1,
    tipo_ensino=TipoEnsino.FUNDAMENTAL,
    valor_centavos=divisao["parcela_1"]["fundamental"],
    porcentagem_alunos=pct_fund
)
```

---

## 📝 Notas Importantes

1. **Valores em Centavos:** Funções de parcelas trabalham com centavos (inteiros) para evitar problemas com floats
2. **Distribuição de Resto:** Centavos restantes são distribuídos de forma determinística
3. **Pesos:** Porcentagens são calculadas usando pesos (multiplicadores) para cada modalidade
4. **Arredondamento:** Valores são arredondados para 2 casas decimais nos cálculos de cotas
5. **Validação:** Funções de processamento retornam valores padrão seguros se dados forem inválidos

---

---

## 📝 Notas Importantes

1. **Funções Movidas:** Algumas funções foram movidas para módulos específicos:
   - `obter_ou_criar_upload_ativo()` → `src/modules/features/uploads/utils.py`
   - `obter_quantidade_projetos_aprovados()` → `src/modules/features/projetos/utils.py`
   - Funções de cálculo de cotas → `src/modules/features/calculos/utils.py`
   - Funções de parcelas → `src/modules/features/parcelas/utils.py`

2. **Valores em Centavos:** Funções de parcelas trabalham com centavos (inteiros) para evitar problemas com floats

3. **Distribuição de Resto:** Centavos restantes são distribuídos de forma determinística

4. **Pesos:** Porcentagens são calculadas usando pesos (multiplicadores) para cada modalidade

5. **Arredondamento:** Valores são arredondados para 2 casas decimais nos cálculos de cotas

6. **Validação:** Funções de processamento retornam valores padrão seguros se dados forem inválidos

---

## 🔗 Arquivos Relacionados

- `src/core/utils.py` - Código fonte das funções utilitárias genéricas
- `src/modules/features/uploads/utils.py` - Utilitários de upload
- `src/modules/features/projetos/utils.py` - Utilitários de projetos
- `src/modules/features/calculos/utils.py` - Funções de cálculo de cotas
- `src/modules/features/parcelas/utils.py` - Funções de parcelas

