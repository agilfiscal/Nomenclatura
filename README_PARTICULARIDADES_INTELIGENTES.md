# Sistema Inteligente de Sugestões de Particularidades

## 🧠 Visão Geral

O sistema agora é mais inteligente! Além de identificar particularidades já cadastradas, ele analisa o nome original do produto e sugere possíveis particularidades que podem estar "escondidas" no texto, permitindo transformar sugestões TMV em TMPV.

## 🔍 Como Funciona

### Análise Inteligente do Nome Original

O sistema analisa cada palavra do nome original e identifica possíveis particularidades usando os seguintes critérios:

1. **Filtros de Exclusão**:
   - Palavras muito curtas (< 3 letras)
   - Artigos e preposições (DE, DA, DO, COM, etc.)
   - Palavras já identificadas como tipo, marca ou volume
   - Números e medidas
   - Palavras comuns que não são particularidades

2. **Identificação de Particularidades**:
   - Palavras significativas que passam pelos filtros
   - Termos descritivos do produto
   - Características específicas

### Exemplo Prático

**Nome Original**: "TEMPERO MAIS SABOR KITANO NORDESTINO 60G"

**Análise**:
- Tipo: TEMPERO ✓
- Marca: KITANO ✓  
- Volume: 60G ✓
- Particularidade: (não encontrada no banco)

**Sugestões Identificadas**:
- NORDESTINO (palavra significativa no nome)

**Resultado**: TMV com sugestão de particularidade

## 🎯 Interface do Usuário

### Sugestões Visuais

Quando o sistema identifica possíveis particularidades, elas aparecem na coluna "Particularidade" como:

```
💡 Sugestões para TMPV:
[NORDESTINO] [PREMIUM] [ORGANICO]
```

### Aceitar Sugestões

O usuário pode clicar em qualquer sugestão para:
1. **Cadastrar automaticamente** a particularidade no banco
2. **Atualizar o produto** para padrão TMPV
3. **Recalcular a confiabilidade** (geralmente aumenta para 100%)
4. **Atualizar a sugestão** de nomenclatura

### Feedback Visual

- **Botões azuis**: Sugestões disponíveis
- **Loading**: Indica processamento
- **Alertas**: Confirmação de sucesso ou erro

## 📊 Benefícios

### Para o Usuário
1. **Descoberta**: Encontra particularidades que não sabia que existiam
2. **Eficiência**: Transforma TMV em TMPV com um clique
3. **Aprendizado**: Entende melhor os padrões de nomenclatura
4. **Qualidade**: Aumenta a confiabilidade das sugestões

### Para o Sistema
1. **Evolução**: O banco de dados cresce automaticamente
2. **Inteligência**: Aprende novos padrões de particularidades
3. **Precisão**: Melhora a identificação futura de produtos similares
4. **Escalabilidade**: Funciona com qualquer tipo de produto

## 🔧 Implementação Técnica

### Backend

#### Função `identificar_possiveis_particularidades()`
```python
def identificar_possiveis_particularidades(nome: str, tipo: str, marca: str, volume: str):
    # Filtros inteligentes
    palavras_ignoradas = {'DE', 'DA', 'DO', 'COM', 'MAIS', 'SABOR', ...}
    
    # Análise de cada palavra
    for palavra in palavras:
        if (len(palavra) >= 3 and 
            palavra not in [tipo, marca, volume] and
            palavra not in palavras_ignoradas):
            possiveis_particularidades.append(palavra)
```

#### Endpoint `/particularidades/sugerir/`
- Cadastra particularidades sugeridas
- Retorna status de sucesso/erro
- Integra com o banco de dados

### Frontend

#### Componente de Sugestões
- Exibe sugestões em cards visuais
- Botões interativos para aceitar
- Feedback em tempo real

#### Função `aceitarParticularidade()`
- Faz requisição para cadastrar
- Atualiza interface localmente
- Recalcula confiabilidade
- Atualiza contadores

## 📈 Exemplos de Uso

### Exemplo 1: Tempero Regional
```
Nome: "TEMPERO MAIS SABOR KITANO NORDESTINO 60G"
Antes: TEMPERO KITANO 60G (TMV - 75%)
Sugestão: NORDESTINO
Depois: TEMPERO KITANO NORDESTINO 60G (TMPV - 100%)
```

### Exemplo 2: Produto Premium
```
Nome: "CERVEJA HEINEKEN PREMIUM LATA 350ML"
Antes: CERVEJA HEINEKEN 350ML (TMV - 75%)
Sugestão: PREMIUM
Depois: CERVEJA HEINEKEN PREMIUM 350ML (TMPV - 100%)
```

### Exemplo 3: Produto Orgânico
```
Nome: "ARROZ INTEGRAL CAMIL ORGANICO 1KG"
Antes: ARROZ CAMIL 1KG (TMV - 75%)
Sugestão: ORGANICO
Depois: ARROZ CAMIL ORGANICO 1KG (TMPV - 100%)
```

## 🚀 Como Testar

### 1. Preparar Ambiente
```bash
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

### 2. Popular Banco Básico
```bash
python popular_banco.py
```

### 3. Testar Sistema
```bash
python testar_particularidades.py
```

### 4. Upload Manual
- Usar arquivo `teste_particularidades.csv`
- Observar sugestões na interface
- Clicar nas sugestões para aceitar

## 📋 Arquivos de Teste

### teste_particularidades.csv
Contém produtos com particularidades "escondidas":
- TEMPERO MAIS SABOR KITANO NORDESTINO 60G
- CERVEJA HEINEKEN PREMIUM LATA 350ML
- CHOCOLATE LACTA AO LEITE PREMIUM 90G
- ARROZ INTEGRAL CAMIL ORGANICO 1KG
- CAFE PILAO TRADICIONAL GOURMET 500G
- REFRIGERANTE COCA COLA ZERO DIET 2L
- CERVEJA BRAHMA CHOPP ARTESANAL 473ML
- REFRIGERANTE PEPSI DIET LIGHT 350ML

## 🎯 Métricas de Sucesso

- **Taxa de Descoberta**: % de produtos TMV que geram sugestões
- **Taxa de Aceitação**: % de sugestões aceitas pelo usuário
- **Melhoria de Confiabilidade**: Aumento médio na confiabilidade
- **Crescimento do Banco**: Novas particularidades cadastradas

## 🔮 Próximos Passos

1. **Machine Learning**: Algoritmos mais sofisticados para identificação
2. **Histórico**: Salvar padrões de aceitação/rejeição
3. **Sugestões Contextuais**: Baseadas em produtos similares
4. **Validação Automática**: Verificar se sugestões fazem sentido
5. **Relatórios**: Análise de performance do sistema inteligente 