# Diagrama do Banco de Dados - Sistema PROFIN

## Diagrama ER (Entity-Relationship)

```mermaid
erDiagram
    AnoLetivo ||--o{ Upload : "tem"
    AnoLetivo ||--|| ContextoAtivo : "tem"
    Upload ||--o{ Escola : "contém"
    Upload ||--o| ContextoAtivo : "pode ter"
    Escola ||--|| CalculosProfin : "tem"
    CalculosProfin ||--o{ ParcelasProfin : "gera"
    Escola ||--o{ LiberacoesParcela : "tem"
    Escola ||--|| LiberacoesProjeto : "tem"

    AnoLetivo {
        int id PK
        int ano UK
        enum status
        datetime created_at
        datetime arquivado_em
    }

    ContextoAtivo {
        int id PK
        int ano_letivo_id FK "unique"
        int upload_id FK
        datetime ativado_em
    }

    Upload {
        int id PK
        int ano_letivo_id FK
        string filename
        datetime upload_date
        int total_escolas
    }

    Escola {
        int id PK
        int upload_id FK
        string nome_uex
        string dre
        string cnpj
        string codigo_ept
        string codigo_inep
        int total_alunos
        int fundamental_inicial
        int fundamental_final
        int fundamental_integral
        int profissionalizante
        int profissionalizante_integrado
        int alternancia
        int ensino_medio_integral
        int ensino_medio_regular
        int especial_fund_regular
        int especial_fund_integral
        int especial_medio_parcial
        int especial_medio_integral
        int sala_recurso
        int preuni
        string indigena_quilombola
        int quantidade_projetos_aprovados
        int repasse_por_area
        float saldo_reprogramado_gestao
        float saldo_reprogramado_merenda
        string numeracao_folha
        datetime created_at
    }

    CalculosProfin {
        int id PK
        int escola_id FK "unique"
        float profin_gestao
        float profin_projeto
        float profin_kit_escolar
        float profin_uniforme
        float profin_merenda
        float profin_sala_recurso
        float profin_preuni
        float valor_total
        datetime calculated_at
    }

    ParcelasProfin {
        int id PK
        int calculo_id FK
        enum tipo_cota
        int numero_parcela
        enum tipo_ensino
        int valor_centavos
        float porcentagem_alunos
    }

    LiberacoesParcela {
        int id PK
        int escola_id FK
        int numero_parcela
        boolean liberada
        int numero_folha
        datetime data_liberacao
        float valor_projetos_aprovados
    }

    LiberacoesProjeto {
        int id PK
        int escola_id FK "unique"
        boolean liberada
        int numero_folha
        datetime data_liberacao
        float valor_projetos_aprovados
    }
```

## Relacionamentos

| Relacionamento | Tipo | Cardinalidade | Cascade |
|---------------|------|---------------|---------|
| AnoLetivo → Upload | 1:N | Um ano tem vários uploads | DELETE CASCADE |
| AnoLetivo → ContextoAtivo | 1:1 | Um ano tem um contexto ativo | DELETE CASCADE |
| Upload → Escola | 1:N | Um upload tem várias escolas | DELETE CASCADE |
| Upload → ContextoAtivo | 1:0..1 | Um upload pode ter um contexto ativo | DELETE CASCADE |
| Escola → CalculosProfin | 1:1 | Uma escola tem um cálculo | DELETE CASCADE |
| CalculosProfin → ParcelasProfin | 1:N | Um cálculo tem várias parcelas | DELETE CASCADE |
| Escola → LiberacoesParcela | 1:N | Uma escola tem várias liberações de parcelas | DELETE CASCADE |
| Escola → LiberacoesProjeto | 1:1 | Uma escola tem uma liberação de projeto | DELETE CASCADE |

## Constraints

- **AnoLetivo.ano**: UNIQUE
- **ContextoAtivo.ano_letivo_id**: UNIQUE (apenas um contexto ativo por ano letivo)
- **Escola (upload_id, nome_uex, dre)**: UNIQUE
- **CalculosProfin.escola_id**: UNIQUE
- **ParcelasProfin (calculo_id, tipo_cota, numero_parcela, tipo_ensino)**: UNIQUE
- **LiberacoesParcela (escola_id, numero_parcela)**: UNIQUE
- **LiberacoesProjeto.escola_id**: UNIQUE

## Notas Importantes

- **estado_liberacao**: Campo removido da tabela `Escola`. O estado de liberação agora é derivado das tabelas `LiberacoesParcela` e `LiberacoesProjeto` através da função `escola_esta_liberada()`.
- **is_active**: Campo removido da tabela `Upload`. O upload ativo é gerenciado através da tabela `ContextoAtivo`, que mantém apenas um contexto ativo por ano letivo.
- **ContextoAtivo**: Gerencia qual upload está ativo para cada ano letivo, permitindo histórico completo de uploads sem sobrescrita.
