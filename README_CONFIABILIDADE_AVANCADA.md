# Sistema de Confiabilidade Avançada

## 🔗 Visão Geral

O sistema agora possui um algoritmo de confiabilidade muito mais inteligente que considera múltiplos fatores além da simples contagem de campos identificados. Isso torna a avaliação da qualidade das sugestões muito mais precisa e informativa.

## 🧩 Fatores de Confiabilidade

### 1. Confiabilidade Base (25%)
- **Cálculo**: Percentual de campos identificados (tipo, marca, particularidade, volume)
- **Exemplo**: 3/4 campos = 75% base

### 2. Fator de Caracteres (-20 a 0 pontos)
- **Comparação**: Razão entre caracteres da sugestão vs nome original
- **Penalidades**:
  - < 50%: -20 pontos (sugestão muito menor)
  - < 70%: -10 pontos (sugestão menor)
  - < 90%: -5 pontos (sugestão ligeiramente menor)
  - 90-120%: 0 pontos (ideal)
  - > 120%: -5 pontos (sugestão muito maior)

### 3. Fator de Palavras Perdidas (-5 por palavra)
- **Análise**: Palavras do original que não aparecem na sugestão
- **Impacto**: Cada palavra perdida reduz 5 pontos
- **Exemplo**: "CERVEJA HEINEKEN PREMIUM LATA 350ML" → "CERVEJA HEINEKEN 350ML"
  - Palavras perdidas: ["PREMIUM", "LATA"] = -10 pontos

### 4. Fator de Palavras Adicionadas (+2 por palavra)
- **Análise**: Palavras na sugestão que não estavam no original
- **Impacto**: Cada palavra adicionada soma 2 pontos
- **Exemplo**: Estruturação de informações

### 5. Fator de Cobertura (-10 a +10 pontos)
- **Análise**: Percentual de palavras importantes do original cobertas
- **Cálculo**: (palavras_cobertas / palavras_importantes - 0.5) * 20
- **Palavras importantes**: 4+ letras, excluindo artigos/preposições

### 6. Fator de Estrutura (+10 a +15 pontos)
- **Estrutura básica**: Tipo + Marca + Volume = +10 pontos
- **Estrutura avançada**: + Particularidade = +5 pontos adicionais

## 📊 Exemplos de Cálculo

### Exemplo 1: Produto Completo
```
Produto: "FARINHA LACTEA NESTLE 500G"
Sugestão: "FARINHA FARINHA LACTEA NESTLE 500G"

Cálculo:
- Base: 4/4 campos = 100%
- Caracteres: 25/20 = 1.25 → -5 pontos
- Palavras perdidas: 0 → 0 pontos
- Palavras adicionadas: 1 → +2 pontos
- Cobertura: 100% → +10 pontos
- Estrutura: TMPV → +15 pontos

Total: 100 - 5 + 0 + 2 + 10 + 15 = 122% → 100% (limitado)
```

### Exemplo 2: Produto com Informações Perdidas
```
Produto: "CERVEJA HEINEKEN PREMIUM LATA 350ML"
Sugestão: "CERVEJA HEINEKEN 350ML"

Cálculo:
- Base: 3/4 campos = 75%
- Caracteres: 18/30 = 0.6 → -10 pontos
- Palavras perdidas: ["PREMIUM", "LATA"] → -10 pontos
- Palavras adicionadas: 0 → 0 pontos
- Cobertura: 60% → +2 pontos
- Estrutura: TMV → +10 pontos

Total: 75 - 10 - 10 + 0 + 2 + 10 = 67%
```

### Exemplo 3: Produto com Palavras Compostas
```
Produto: "MOLHO DE ALHO KNORR 200ML"
Sugestão: "MOLHO MOLHO DE ALHO KNORR 200ML"

Cálculo:
- Base: 4/4 campos = 100%
- Caracteres: 25/22 = 1.14 → 0 pontos
- Palavras perdidas: 0 → 0 pontos
- Palavras adicionadas: 1 → +2 pontos
- Cobertura: 100% → +10 pontos
- Estrutura: TMPV → +15 pontos

Total: 100 + 0 + 0 + 2 + 10 + 15 = 127% → 100% (limitado)
```

## 🎯 Benefícios do Sistema

### Para o Usuário
1. **Transparência**: Vê exatamente por que a confiabilidade é alta ou baixa
2. **Precisão**: Avaliação muito mais realista da qualidade
3. **Insights**: Identifica palavras perdidas e oportunidades de melhoria
4. **Decisão**: Base mais sólida para aceitar ou rejeitar sugestões

### Para o Sistema
1. **Qualidade**: Incentiva identificação completa de informações
2. **Melhoria**: Identifica pontos fracos para otimização
3. **Consistência**: Padronização mais rigorosa
4. **Inteligência**: Aprende com padrões de qualidade

## 🔧 Implementação Técnica

### Backend

#### Nova Função `calcular_confiabilidade_avancada()`
```python
def calcular_confiabilidade_avancada(nome_original, tipo, marca, particularidade, volume, confiabilidade_base):
    # Fator 1: Comparação de caracteres
    # Fator 2: Análise de palavras perdidas/adicionadas
    # Fator 3: Cobertura de informações importantes
    # Fator 4: Qualidade da estrutura
    # Retorna confiabilidade final e detalhes
```

#### Retorno Detalhado
```python
{
    'confiabilidade': 85.5,
    'detalhes': {
        'base': 75.0,
        'fator_chars': -5,
        'fator_palavras_perdidas': -10,
        'fator_palavras_adicionadas': 2,
        'fator_cobertura': 10,
        'fator_estrutura': 15,
        'palavras_perdidas': ['PREMIUM', 'LATA'],
        'palavras_adicionadas': ['ESTRUTURADO'],
        'razao_chars': 0.85
    }
}
```

### Frontend

#### Tooltip Informativo
- **Ícone ℹ️**: Ao lado da barra de confiabilidade
- **Hover**: Mostra detalhes completos dos fatores
- **Cores**: Verde (alta), Amarelo (média), Vermelho (baixa)

## 📋 Casos de Teste

### Produtos de Teste
1. **CERVEJA HEINEKEN PREMIUM LATA 350ML** → Testa palavras perdidas
2. **CHOCOLATE AO LEITE LACTA PREMIUM 90G** → Testa palavras compostas
3. **ARROZ INTEGRAL CAMIL ORGANICO 1KG** → Testa múltiplas particularidades
4. **TEMPERO PARA CARNE KITANO NORDESTINO 100G** → Testa muitas palavras
5. **FARINHA LACTEA NESTLE 500G** → Testa palavra composta específica
6. **MOLHO DE ALHO KNORR 200ML** → Testa palavra composta específica
7. **CAFE EM GRAOS PILAO TRADICIONAL 1KG** → Testa múltiplas particularidades
8. **REFRIGERANTE ZERO ACUCAR PEPSI DIET 2L** → Testa possível perda
9. **CERVEJA BRAHMA CHOPP ARTESANAL 473ML** → Testa palavras específicas
10. **TEMPERO MAIS SABOR KITANO NORDESTINO 60G** → Testa perda de informações

### Métricas Esperadas
- **Confiabilidade média**: 70-85%
- **Produtos com alta confiabilidade**: 60-80%
- **Produtos com média confiabilidade**: 20-30%
- **Produtos com baixa confiabilidade**: 0-10%

## 🚀 Como Testar

### Teste Automático
```bash
cd backend
.\venv\Scripts\Activate.ps1
python testar_confiabilidade_avancada.py
```

### Teste Manual
1. **Iniciar backend**: `python main.py`
2. **Popular banco**: `python popular_banco.py`
3. **Iniciar frontend**: `npm run dev`
4. **Upload**: `teste_confiabilidade_avancada.csv`
5. **Verificar**: Hover sobre ℹ️ para ver detalhes

### Validação
- Verificar se confiabilidades fazem sentido
- Observar detalhes nos tooltips
- Confirmar que produtos com mais informações têm confiabilidade maior
- Testar produtos com palavras perdidas

## 📈 Interpretação dos Resultados

### Confiabilidade Alta (≥75%)
- **Verde**: Sugestão de alta qualidade
- **Características**: Boa cobertura, estrutura completa
- **Ação**: Geralmente aceitar

### Confiabilidade Média (50-74%)
- **Amarelo**: Sugestão com algumas limitações
- **Características**: Algumas palavras perdidas ou estrutura incompleta
- **Ação**: Revisar e considerar melhorias

### Confiabilidade Baixa (<50%)
- **Vermelho**: Sugestão com problemas significativos
- **Características**: Muitas palavras perdidas, cobertura baixa
- **Ação**: Revisar completamente ou rejeitar

## 🔮 Próximos Passos

1. **Machine Learning**: Treinar modelo com dados de aceitação/rejeição
2. **Ajuste Dinâmico**: Ajustar pesos baseado em feedback do usuário
3. **Análise Temporal**: Considerar padrões históricos
4. **Relatórios Avançados**: Análise de tendências de confiabilidade
5. **Otimização Automática**: Sugestões automáticas de melhoria

## 🎉 Resultado

O sistema agora oferece uma avaliação de confiabilidade muito mais inteligente e transparente! Ele considera:

1. **Quantidade de caracteres** vs nome original
2. **Palavras perdidas** (informação importante não capturada)
3. **Palavras adicionadas** (estruturação)
4. **Cobertura** de informações importantes
5. **Qualidade da estrutura** TMPV/TMV

Isso torna o sistema muito mais preciso e informativo para o usuário! 🎯 