# 📘 Type Hints - Documentação

## O que são Type Hints?

**Type Hints** (Anotações de Tipo) são informações que você adiciona ao código Python para indicar **que tipo de dado** cada variável, parâmetro ou retorno de função deve ter.

### **Antes (sem type hints):**
```python
def calcular_total(preco, quantidade):
    return preco * quantidade
```

**Problemas:**
- ❌ Não sabemos se `preco` é `int`, `float`, ou `str`
- ❌ Não sabemos o que a função retorna
- ❌ IDEs não conseguem sugerir autocompletar
- ❌ Erros só aparecem em tempo de execução

### **Depois (com type hints):**
```python
def calcular_total(preco: float, quantidade: int) -> float:
    return preco * quantidade
```

**Benefícios:**
- ✅ Fica claro: `preco` é `float`, `quantidade` é `int`
- ✅ Retorna `float`
- ✅ IDEs autocompletam corretamente
- ✅ Ferramentas como `mypy` detectam erros antes de executar

---

## Sintaxe Básica

### **1. Parâmetros de Função:**
```python
def minha_funcao(parametro: tipo) -> tipo_retorno:
    ...
```

**Exemplos:**
```python
# Função simples
def somar(a: int, b: int) -> int:
    return a + b

# Com strings
def saudacao(nome: str) -> str:
    return f"Olá, {nome}!"

# Com lista
def processar_items(items: list[str]) -> int:
    return len(items)
```

### **2. Variáveis:**
```python
# Opcional, mas útil
idade: int = 25
nome: str = "João"
precos: list[float] = [10.5, 20.0, 30.75]
```

### **3. Tipos Opcionais:**
```python
from typing import Optional

# Valor pode ser int ou None
def dividir(a: int, b: Optional[int]) -> Optional[float]:
    if b is None or b == 0:
        return None
    return a / b
```

### **4. Tipos Múltiplos (Union):**
```python
from typing import Union

# Pode retornar int OU str
def processar(valor: Union[int, str]) -> Union[int, str]:
    return valor
```

### **5. Tuplas:**
```python
from typing import Tuple

# Retorna tupla (int, str)
def obter_dados() -> Tuple[int, str]:
    return (1, "sucesso")
```

### **6. Dicionários:**
```python
from typing import Dict

# Dicionário com chaves str e valores int
def contar_items(items: list[str]) -> Dict[str, int]:
    resultado: Dict[str, int] = {}
    for item in items:
        resultado[item] = resultado.get(item, 0) + 1
    return resultado
```

---

## Type Hints no Projeto

### **Funções de Utilitários:**
```python
def obter_quantidade(row: pd.Series, coluna: str) -> int:
    """Retorna quantidade do DataFrame como int"""
    ...
```

**O que significa:**
- `row: pd.Series` → Parâmetro `row` é uma Series do pandas
- `coluna: str` → Parâmetro `coluna` é uma string
- `-> int` → Função retorna um inteiro

### **Funções do Banco:**
```python
def get_db() -> Generator:
    """Retorna gerador de sessões do banco"""
    ...
```

### **Rotas do FastAPI:**
```python
@router.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    ano_letivo_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload de arquivo Excel"""
    ...
```

**O que significa:**
- `file: UploadFile` → Arquivo enviado
- `ano_letivo_id: Optional[int]` → ID opcional (pode ser None)
- `db: Session` → Sessão do banco de dados
- `-> Dict[str, Any]` → Retorna dicionário

---

## Benefícios no Projeto

### **1. Autocompletar Melhorado:**
```python
# IDE sabe que ano_letivo é AnoLetivo e tem atributos .ano, .status, etc.
ano_letivo, ano_id = obter_ano_letivo(db)
print(ano_letivo.ano)  # IDE autocompleta .ano
```

### **2. Detecção de Erros:**
```python
# mypy detectaria esse erro:
total = obter_quantidade(row, "TOTAL")
resultado = total + "escolas"  # Erro! int + str não funciona
```

### **3. Documentação Viva:**
```python
# Lendo a assinatura já entende o que a função faz
def calcular_total(preco: float, quantidade: int) -> float:
    ...
```

### **4. Refatoração Segura:**
Se você mudar o tipo de retorno, ferramentas avisam onde precisa atualizar.

---

## Ferramentas Úteis

### **mypy** (verificador de tipos):
```bash
pip install mypy
mypy src/
```

Verifica se os type hints estão corretos em todo o projeto.

### **IDEs:**
- **VS Code** com extensão Python
- **PyCharm**
- **Cursor** (já tem suporte)

Todos autocompletam melhor com type hints.

---

## Exemplos no Projeto

### **Função com Múltiplos Retornos:**
```python
from typing import Union, Tuple

def obter_ano_letivo(...) -> Union[Tuple[AnoLetivo, int], Tuple[None, None]]:
    # Pode retornar (AnoLetivo, int) OU (None, None)
    ...
```

### **Função com Callback:**
```python
from typing import Callable

def processar_com_callback(
    dados: list[int],
    callback: Callable[[int], bool]
) -> list[int]:
    """Processa dados usando função callback"""
    return [d for d in dados if callback(d)]
```

---

## Resumo

**Type Hints são:**
- ✅ Anotações opcionais no código Python
- ✅ Ajudam IDEs a autocompletar
- ✅ Facilitam detecção de erros
- ✅ Funcionam como documentação
- ✅ Não afetam performance (são ignorados em runtime)
- ✅ Melhoram manutenibilidade do código

**Importante:** Type hints são **opcionais** em Python - o código funciona sem eles, mas fica muito melhor com eles!

