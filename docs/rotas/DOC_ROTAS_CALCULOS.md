# Documentação - Rotas de Cálculos

**Arquivo:** `src/modules/routes/calculos_routes.py`  
**Prefixo:** `/calculos`

---

## 📋 Visão Geral

Rota para calcular os valores das cotas PROFIN para todas as escolas de um ano letivo. Os cálculos são baseados nas regras de negócio definidas em `src/core/utils.py`.

---

## 🔑 Conceitos Importantes

### Cotas PROFIN Calculadas

O sistema calcula as seguintes cotas para cada escola:

1. **PROFIN Custeio** (Gestão)
2. **PROFIN Projeto**
3. **PROFIN Kit Escolar**
4. **PROFIN Uniforme**
5. **PROFIN Merenda**
6. **PROFIN Sala de Recurso**
7. **PROFIN Permanente**
8. **PROFIN Climatização**
9. **PROFIN Preuni**

### Valores Calculados

Cada cota tem regras específicas de cálculo baseadas em:
- Quantidade total de alunos
- Tipos de ensino (fundamental, médio, especial, etc.)
- Modalidades específicas (integral, regular, etc.)

---

## 📍 Rotas Disponíveis

### **POST /** - Calcular Valores

Calcula os valores das cotas PROFIN para todas as escolas de um ano letivo específico.

**Endpoint:** `POST /calculos`

**Autenticação:** Não requerida

**Query Parameters:**
- `ano_letivo_id` (opcional, int): ID do ano letivo. Se não fornecido, usa o ano ativo.

**Response:**
```json
{
  "success": true,
  "message": "Cálculos realizados para 250 escolas do ano 2026",
  "total_escolas": 250,
  "valor_total_geral": 40000000.00,
  "escolas": [
    {
      "id": 1,
      "nome_uex": "ESCOLA MUNICIPAL EXEMPLO",
      "dre": "DRE-01",
      "profin_custeio": 50000.00,
      "profin_projeto": 10000.00,
      "profin_kit_escolar": 25000.00,
      "profin_uniforme": 20000.00,
      "profin_merenda": 30000.00,
      "profin_sala_recurso": 5000.00,
      "profin_permanente": 15000.00,
      "profin_climatizacao": 10000.00,
      "profin_preuni": 0.00,
      "valor_total": 160000.00
    }
    // ... mais escolas
  ],
  "upload_id": 1,
  "ano_letivo_id": 2
}
```

**Comportamento:**

1. **Determina Ano Letivo:** Se `ano_letivo_id` não for fornecido, usa o ano ativo.
2. **Busca Escolas:** Busca todas as escolas do ano letivo.
3. **Calcula Cotas:** Para cada escola, calcula todas as cotas PROFIN usando as regras de negócio.
4. **Upsert:** Atualiza cálculos existentes ou cria novos.

**Erros:**
- `404 Not Found`: Nenhuma escola encontrada para o ano letivo
- `500 Internal Server Error`: Erro ao calcular valores

**Exemplo de uso:**

Calcular para o ano ativo:
```bash
curl -X POST http://localhost:8000/calculos
```

Calcular para um ano específico:
```bash
curl -X POST "http://localhost:8000/calculos?ano_letivo_id=2"
```

Com JavaScript:
```javascript
const calcularValores = async (anoLetivoId = null) => {
  const url = anoLetivoId 
    ? `http://localhost:8000/calculos?ano_letivo_id=${anoLetivoId}`
    : 'http://localhost:8000/calculos';
  
  const response = await fetch(url, {
    method: 'POST'
  });
  
  return response.json();
};

// Usar ano ativo
const resultado = await calcularValores();

// Usar ano específico
const resultado2025 = await calcularValores(1);
```

Com Python:
```python
import requests

def calcular_valores(ano_letivo_id=None):
    url = 'http://localhost:8000/calculos'
    params = {'ano_letivo_id': ano_letivo_id} if ano_letivo_id else {}
    
    response = requests.post(url, params=params)
    return response.json()

# Calcular para ano ativo
resultado = calcular_valores()

# Calcular para ano específico
resultado_2025 = calcular_valores(ano_letivo_id=1)
```

---

## 🔄 Fluxo de Trabalho

### 1. Upload de Dados

```bash
POST /uploads/excel
# Upload de arquivo com dados das escolas
```

### 2. Calcular Valores

```bash
POST /calculos
# Calcula todas as cotas PROFIN para todas as escolas
```

### 3. Criar Parcelas (Opcional)

```bash
POST /parcelas
# Divide valores em parcelas e por tipo de ensino
```

---

## 📊 Estrutura de Dados

### ResponseCalculos

```typescript
{
  success: boolean;
  message: string;
  total_escolas: number;
  valor_total_geral: number;  // Soma de todos os valores totais
  escolas: EscolaCalculo[];
  upload_id: number;
  ano_letivo_id: number | null;
}
```

### EscolaCalculo

```typescript
{
  id: number;
  dre: string | null;
  nome_uex: string;
  profin_custeio: number;
  profin_projeto: number;
  profin_kit_escolar: number;
  profin_uniforme: number;
  profin_merenda: number;
  profin_sala_recurso: number;
  profin_permanente: number;
  profin_climatizacao: number;
  profin_preuni: number;
  valor_total: number;  // Soma de todas as cotas
}
```

---

## 🧮 Regras de Cálculo

As regras de cálculo estão definidas em `src/core/utils.py` na função `calcular_todas_cotas()`. Cada cota tem regras específicas baseadas em:

- **Quantidade de alunos:** Total de alunos da escola
- **Modalidades:** Tipos de ensino (fundamental, médio, especial, etc.)
- **Recursos especiais:** Sala de recurso, climatização, PREUNI, etc.

### Exemplo de Regra (PROFIN Projeto)

```python
# Se quantidade <= 500:
#   - Com ensino integral: 5000 * 2 = 10000
#   - Sem ensino integral: 5000
# Se quantidade > 500 e <= 1000:
#   - Com ensino integral: 10000 * 2 = 20000
#   - Sem ensino integral: 10000
# Se quantidade > 1000:
#   - Com ensino integral: 15000 * 2 = 30000
#   - Sem ensino integral: 15000
```

---

## ⚠️ Códigos de Erro

- `404 Not Found`: Nenhuma escola encontrada para o ano letivo
- `500 Internal Server Error`: Erro ao calcular valores

---

## 📝 Notas Importantes

1. **Isolamento por Ano:** Cálculos são isolados por ano letivo. Cada ano tem seus próprios cálculos.

2. **Upsert:** Se um cálculo já existe para uma escola, ele é atualizado. Se não existe, é criado.

3. **Reexecução:** A rota pode ser executada múltiplas vezes. Os cálculos serão atualizados com os valores mais recentes.

4. **Pré-requisito:** É necessário ter escolas cadastradas (via upload) antes de calcular valores.

5. **Valor Total:** O campo `valor_total` é a soma de todas as cotas calculadas para a escola.

6. **Timestamp:** Cada cálculo registra `calculated_at` para auditoria.

---

## 🔗 Relacionamento com Outras Rotas

### Upload → Cálculos

```bash
# 1. Upload de dados
POST /uploads/excel

# 2. Calcular valores
POST /calculos
```

### Cálculos → Parcelas

```bash
# 1. Calcular valores
POST /calculos

# 2. Criar parcelas
POST /parcelas
```

---

## 🚀 Exemplos de Integração

### Verificar Status dos Cálculos

```javascript
// Obter detalhes de um upload para ver se tem cálculos
const uploadDetails = await fetch('http://localhost:8000/uploads/1')
  .then(r => r.json());

// Verificar se escolas têm cálculos
uploadDetails.escolas.forEach(escola => {
  if (escola.calculos) {
    console.log(`${escola.escola.nome_uex}: R$ ${escola.calculos.valor_total}`);
  }
});
```

### Recalcular Valores

```python
# Recalcular valores para um ano específico
import requests

def recalcular_ano(ano_letivo_id):
    response = requests.post(
        'http://localhost:8000/calculos',
        params={'ano_letivo_id': ano_letivo_id}
    )
    resultado = response.json()
    print(f"✅ {resultado['message']}")
    print(f"💰 Valor total: R$ {resultado['valor_total_geral']:,.2f}")
    return resultado
```

