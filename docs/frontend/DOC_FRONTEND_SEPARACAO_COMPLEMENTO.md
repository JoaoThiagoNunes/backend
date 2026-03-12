# Documentação Frontend - Separação de Complementos por Tipo de Ensino

**Versão:** 1.0  
**Data:** 2026-03-11  
**Endpoint:** `POST /complemento/separar`

---

## 📋 Visão Geral

Esta funcionalidade permite separar os valores de complemento entre ensino **fundamental** e **médio**, seguindo a mesma lógica de separação usada nas parcelas normais. Isso é necessário para que o sistema possa gerar relatórios e planilhas separadas por tipo de ensino.

---

## 🎯 Quando Usar

Use esta funcionalidade **após** fazer o upload de uma planilha de complemento e **antes** de liberar escolas para folhas. A separação é opcional, mas recomendada para relatórios detalhados.

**Fluxo Recomendado:**
1. ✅ Upload de planilha de complemento (`POST /complemento/upload`)
2. ✅ Separar complementos por tipo de ensino (`POST /complemento/separar`) ← **Nova funcionalidade**
3. ✅ Visualizar resumo agrupado por folhas (`GET /complemento/repasse`) ← **Agora retorna valores separados por ensino**
4. ✅ Consultar histórico de uma escola (`GET /complemento/escola/{escola_id}`) ← **Agora retorna valores separados por ensino**
5. ✅ Liberar escolas para folhas (`POST /complemento/liberar`)

---

## 🔌 Integração

### Tipos TypeScript

```typescript
// Request
interface SepararComplementoRequest {
  complemento_upload_id?: number;
  ano_letivo_id?: number;
  recalcular?: boolean;
  calculation_version?: string;
}

// Response
interface ParcelaComplementoPorCota {
  tipo_cota: string;  // "CUSTEIO" | "MERENDA" | "KIT_ESCOLAR" | "UNIFORME" | "SALA_RECURSO"
  valor_total_reais: number;
  parcela_1: {
    fundamental: number;
    medio: number;
  };
  porcentagens: {
    fundamental: number;
    medio: number;
  };
}

interface EscolaComplementoParcelas {
  escola_id: number;
  nome_uex: string;
  dre?: string;
  porcentagem_fundamental: number;
  porcentagem_medio: number;
  parcelas_por_cota: ParcelaComplementoPorCota[];
}

interface SepararComplementoResponse {
  success: boolean;
  message: string;
  total_escolas: number;
  escolas_processadas: number;
  total_parcelas_criadas: number;
  complemento_upload_id: number;
  escolas: EscolaComplementoParcelas[];
  calculation_version?: string;
}
```

### Função de Separação

```typescript
/**
 * Separa os valores de complemento entre ensino fundamental e médio
 * 
 * @param complementoUploadId - ID do upload de complemento (opcional, usa o mais recente)
 * @param anoLetivoId - ID do ano letivo (opcional, usa o ano ativo)
 * @param recalcular - Se true, recalcula mesmo que já existam parcelas
 * @returns Promise com os dados das parcelas separadas
 */
async function separarComplementos(
  complementoUploadId?: number,
  anoLetivoId?: number,
  recalcular = false
): Promise<SepararComplementoResponse> {
  const response = await fetch(`${API_BASE_URL}/complemento/separar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      complemento_upload_id: complementoUploadId,
      ano_letivo_id: anoLetivoId,
      recalcular,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Erro ao separar complementos: ${response.statusText}`);
  }

  return response.json();
}
```

---

## 📊 Exemplo de Resposta

```json
{
  "success": true,
  "message": "Separados 150 complemento(s) em 1500 parcela(s)",
  "total_escolas": 150,
  "escolas_processadas": 150,
  "total_parcelas_criadas": 1500,
  "complemento_upload_id": 15,
  "calculation_version": "v1_20260311_114943",
  "escolas": [
    {
      "escola_id": 100,
      "nome_uex": "ESCOLA MUNICIPAL EXEMPLO",
      "dre": "DRE-01",
      "porcentagem_fundamental": 52.5,
      "porcentagem_medio": 47.5,
      "parcelas_por_cota": [
        {
          "tipo_cota": "CUSTEIO",
          "valor_total_reais": 5000.00,
          "parcela_1": {
            "fundamental": 2625.00,
            "medio": 2375.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "MERENDA",
          "valor_total_reais": 3000.00,
          "parcela_1": {
            "fundamental": 1575.00,
            "medio": 1425.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "KIT_ESCOLAR",
          "valor_total_reais": 1500.00,
          "parcela_1": {
            "fundamental": 787.50,
            "medio": 712.50
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "UNIFORME",
          "valor_total_reais": 600.00,
          "parcela_1": {
            "fundamental": 315.00,
            "medio": 285.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "SALA_RECURSO",
          "valor_total_reais": 2000.00,
          "parcela_1": {
            "fundamental": 1050.00,
            "medio": 950.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        }
      ]
    }
  ]
}
```

---

## 💡 Casos de Uso

### 1. Separar Após Upload

```typescript
// Após fazer upload de complemento
const uploadResult = await uploadComplemento(file, anoLetivoId);

// Separar automaticamente
const separacaoResult = await separarComplementos(
  uploadResult.complemento_upload_id,
  anoLetivoId,
  false
);

console.log(`Separados ${separacaoResult.total_parcelas_criadas} parcelas`);
```

### 2. Verificar se Já Foi Separado

```typescript
try {
  const resultado = await separarComplementos(complementoUploadId, anoLetivoId, false);
  
  if (resultado.message.includes("já existem")) {
    // Parcelas já existem, usar dados retornados
    console.log("Parcelas já separadas anteriormente");
  } else {
    // Parcelas foram criadas agora
    console.log("Parcelas criadas com sucesso");
  }
} catch (error) {
  console.error("Erro ao verificar separação:", error);
}
```

### 3. Recalcular Parcelas

```typescript
// Recalcular com nova versão
const resultado = await separarComplementos(
  complementoUploadId,
  anoLetivoId,
  true, // recalcular
  `v2_${new Date().toISOString().replace(/[-:]/g, '').split('.')[0]}`
);
```

### 4. Exibir Dados em Tabela

```typescript
function ComponenteTabelaComplementos({ escolas }: { escolas: EscolaComplementoParcelas[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Escola</th>
          <th>Cota</th>
          <th>Total</th>
          <th>Fundamental</th>
          <th>Médio</th>
          <th>% Fund.</th>
          <th>% Médio</th>
        </tr>
      </thead>
      <tbody>
        {escolas.map(escola =>
          escola.parcelas_por_cota.map((cota, idx) => (
            <tr key={`${escola.escola_id}-${idx}`}>
              {idx === 0 && (
                <td rowSpan={escola.parcelas_por_cota.length}>
                  {escola.nome_uex}
                </td>
              )}
              <td>{cota.tipo_cota}</td>
              <td>R$ {cota.valor_total_reais.toFixed(2)}</td>
              <td>R$ {cota.parcela_1.fundamental.toFixed(2)}</td>
              <td>R$ {cota.parcela_1.medio.toFixed(2)}</td>
              <td>{cota.porcentagens.fundamental}%</td>
              <td>{cota.porcentagens.medio}%</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
```

### 5. Calcular Totais por Tipo de Ensino

```typescript
function calcularTotaisPorEnsino(escolas: EscolaComplementoParcelas[]) {
  const totais = {
    fundamental: {
      custeio: 0,
      merenda: 0,
      kit_escolar: 0,
      uniforme: 0,
      sala_recurso: 0,
      total: 0,
    },
    medio: {
      custeio: 0,
      merenda: 0,
      kit_escolar: 0,
      uniforme: 0,
      sala_recurso: 0,
      total: 0,
    },
  };

  escolas.forEach(escola => {
    escola.parcelas_por_cota.forEach(cota => {
      const cotaKey = cota.tipo_cota.toLowerCase() as keyof typeof totais.fundamental;
      
      totais.fundamental[cotaKey] += cota.parcela_1.fundamental;
      totais.medio[cotaKey] += cota.parcela_1.medio;
      
      totais.fundamental.total += cota.parcela_1.fundamental;
      totais.medio.total += cota.parcela_1.medio;
    });
  });

  return totais;
}
```

---

## ⚠️ Tratamento de Erros

```typescript
async function separarComplementosComTratamento(
  complementoUploadId?: number,
  anoLetivoId?: number
) {
  try {
    const resultado = await separarComplementos(complementoUploadId, anoLetivoId);
    return resultado;
  } catch (error: any) {
    if (error.message.includes('404')) {
      // Nenhum complemento encontrado
      throw new Error('Nenhum complemento encontrado. Faça o upload primeiro.');
    } else if (error.message.includes('Nenhum complemento com valores')) {
      // Complementos existem mas não têm valores
      throw new Error('Os complementos não têm valores para separar.');
    } else {
      // Erro genérico
      throw new Error(`Erro ao separar complementos: ${error.message}`);
    }
  }
}
```

---

## 📈 Estados da UI

### Estado de Loading

```typescript
const [isSeparando, setIsSeparando] = useState(false);
const [resultado, setResultado] = useState<SepararComplementoResponse | null>(null);

async function handleSeparar() {
  setIsSeparando(true);
  try {
    const resultado = await separarComplementos(complementoUploadId, anoLetivoId);
    setResultado(resultado);
    // Mostrar mensagem de sucesso
  } catch (error) {
    // Mostrar mensagem de erro
  } finally {
    setIsSeparando(false);
  }
}
```

### Indicador Visual

```tsx
{isSeparando && (
  <div className="loading">
    <Spinner />
    <span>Separando complementos por tipo de ensino...</span>
  </div>
)}

{resultado && (
  <div className="success-message">
    ✅ {resultado.message}
    <br />
    <small>
      {resultado.total_parcelas_criadas} parcelas criadas para {resultado.escolas_processadas} escolas
    </small>
  </div>
)}
```

---

## 🔄 Fluxo Completo de Integração

```typescript
// 1. Upload de complemento
const uploadResult = await uploadComplemento(file, anoLetivoId);

// 2. Separar por tipo de ensino
const separacaoResult = await separarComplementos(
  uploadResult.complemento_upload_id,
  uploadResult.ano_letivo_id,
  false
);

// 3. Exibir resultados
console.log(`Total de escolas: ${separacaoResult.total_escolas}`);
console.log(`Parcelas criadas: ${separacaoResult.total_parcelas_criadas}`);

// 4. Processar dados para exibição
separacaoResult.escolas.forEach(escola => {
  console.log(`\nEscola: ${escola.nome_uex}`);
  console.log(`Porcentagem: ${escola.porcentagem_fundamental}% fund. / ${escola.porcentagem_medio}% médio`);
  
  escola.parcelas_por_cota.forEach(cota => {
    console.log(`  ${cota.tipo_cota}:`);
    console.log(`    Total: R$ ${cota.valor_total_reais.toFixed(2)}`);
    console.log(`    Fundamental: R$ ${cota.parcela_1.fundamental.toFixed(2)}`);
    console.log(`    Médio: R$ ${cota.parcela_1.medio.toFixed(2)}`);
  });
});
```

---

## 📍 Valores Separados por Ensino em Outras Rotas

Após executar `POST /complemento/separar`, os valores separados por ensino também estarão disponíveis em outras rotas:

### GET /complemento/escola/{escola_id}

Esta rota retorna o histórico de complementos de uma escola, e agora inclui valores separados por ensino quando disponíveis:

```typescript
interface ComplementoHistorico {
  complemento_upload_id: number;
  data: string;
  status: string;
  total_alunos_diferenca: number;
  valor_complemento_total: number;
  // ... outros campos de valores por cota ...
  
  // Novos campos (opcionais - apenas se separação foi feita)
  parcelas?: ComplementoParcelaDetalhe[] | null;
  porcentagem_fundamental?: number | null;
  porcentagem_medio?: number | null;
}

interface ComplementoParcelaDetalhe {
  id: number;
  tipo_cota: string;
  numero_parcela: number;
  tipo_ensino: string;
  valor_reais: number;
  valor_centavos: number;
  porcentagem_alunos: number;
  created_at: string;
}
```

### GET /complemento/repasse

Esta rota retorna o resumo agrupado por folhas, e agora inclui valores separados por ensino nas escolas:

```typescript
interface ComplementoEscolaPrevisaoInfo {
  escola_id: number;
  nome_uex: string;
  dre?: string;
  liberada: boolean;
  numero_folha?: number;
  valor_complemento_total: number;
  status: string;
  
  // Novos campos (opcionais - apenas se separação foi feita)
  parcelas_por_cota?: ParcelaComplementoPorCota[] | null;
  porcentagem_fundamental?: number | null;
  porcentagem_medio?: number | null;
}
```

**Exemplo de uso:**

```typescript
// Buscar histórico de uma escola
const historico = await fetch(`${API_BASE_URL}/complemento/escola/${escolaId}`);
const data = await historico.json();

// Verificar se tem valores separados por ensino
data.complementos.forEach(complemento => {
  if (complemento.parcelas) {
    console.log(`Complemento ${complemento.complemento_upload_id}:`);
    console.log(`  Porcentagem: ${complemento.porcentagem_fundamental}% fund. / ${complemento.porcentagem_medio}% médio`);
    complemento.parcelas.forEach(parcela => {
      console.log(`  ${parcela.tipo_cota} - ${parcela.tipo_ensino}: R$ ${parcela.valor_reais.toFixed(2)}`);
    });
  }
});

// Buscar resumo por folhas
const repasse = await fetch(`${API_BASE_URL}/complemento/repasse`);
const repasseData = await repasse.json();

// Verificar valores separados por ensino nas escolas
repasseData.folhas.forEach(folha => {
  folha.escolas.forEach(escola => {
    if (escola.parcelas_por_cota) {
      console.log(`${escola.nome_uex}:`);
      escola.parcelas_por_cota.forEach(cota => {
        console.log(`  ${cota.tipo_cota}:`);
        console.log(`    Fundamental: R$ ${cota.parcela_1.fundamental.toFixed(2)}`);
        console.log(`    Médio: R$ ${cota.parcela_1.medio.toFixed(2)}`);
      });
    }
  });
});
```

---

## 📝 Notas Importantes

1. **Idempotência:** A rota é idempotente. Se `recalcular=false` e já existem parcelas, retorna as existentes sem recriar.

2. **Valores em Reais:** A resposta retorna valores em reais (float), mas internamente são armazenados em centavos (inteiros).

3. **Apenas Complementos com Aumento:** Apenas complementos com status `AUMENTO` e valores > 0 são processados.

4. **1 Parcela Única:** Diferente das parcelas normais que têm 2 parcelas, o complemento tem apenas 1 parcela única, mas ainda é dividida entre fundamental e médio.

5. **Porcentagens:** As porcentagens são calculadas baseadas nas **diferenças** de quantidades do complemento, não nas quantidades totais da escola.

6. **Campos Opcionais:** Os campos de valores separados por ensino (`parcelas`, `parcelas_por_cota`, `porcentagem_fundamental`, `porcentagem_medio`) são opcionais e retornam `null` se a separação ainda não foi executada. Sempre verifique se os valores existem antes de usá-los.

7. **Disponibilidade em Outras Rotas:** Após executar `POST /complemento/separar`, os valores separados por ensino também estarão disponíveis em:
   - `GET /complemento/escola/{escola_id}` - Campo `parcelas` em cada complemento do histórico
   - `GET /complemento/repasse` - Campo `parcelas_por_cota` em cada escola do resumo

---

## 🔗 Links Relacionados

- [Documentação Completa de Complemento](../rotas/DOC_ROTAS_COMPLEMENTO.md)
- [Documentação de Parcelas](../rotas/DOC_ROTAS_PARCELAS.md) - Sistema similar para parcelas normais
- [Índice de Rotas](../rotas/DOC_INDICE_ROTAS.md)

---

**Última atualização:** 2026-03-11

**Atualizações:**
- ✅ Valores separados por ensino agora disponíveis em `GET /complemento/escola/{escola_id}` e `GET /complemento/repasse`
