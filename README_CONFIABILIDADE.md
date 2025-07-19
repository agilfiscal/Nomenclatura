# Sistema de Confiabilidade TMPV/TMV

## Visão Geral

O sistema agora inclui um mecanismo de confiabilidade que calcula a porcentagem de proximidade das sugestões de nomenclatura com o padrão TMPV (Tipo-Marca-Particularidade-Volume) ou TMV (Tipo-Marca-Volume).

## Como Funciona

### Cálculo da Confiabilidade

A confiabilidade é calculada baseada na identificação dos campos:

1. **Tipo**: Produto identificado (ex: CERVEJA, REFRIGERANTE)
2. **Marca**: Marca identificada (ex: HEINEKEN, COCA COLA)
3. **Particularidade**: Característica específica (ex: AO LEITE, DIET) - *opcional*
4. **Volume**: Quantidade/embalagem (ex: 350ML, 2L)

**Fórmula**: `(campos_identificados / total_campos) * 100`

### Padrões

- **TMPV**: Quando uma particularidade é identificada
- **TMV**: Quando apenas tipo, marca e volume são identificados

### Níveis de Confiabilidade

- **Alta (≥75%)**: Verde - Boa identificação dos campos
- **Média (50-74%)**: Amarelo - Identificação parcial
- **Baixa (<50%)**: Vermelho - Baixa identificação

## Interface do Usuário

### Resumo Estatístico
- Confiabilidade média geral
- Contagem de produtos por padrão (TMPV/TMV)
- Contagem de produtos com baixa confiabilidade

### Filtros
- **Todos**: Mostra todos os produtos
- **Alta (≥75%)**: Apenas produtos com alta confiabilidade
- **Média (50-74%)**: Produtos com confiabilidade média
- **Baixa (<50%)**: Produtos com baixa confiabilidade

### Tabela de Resultados
- Coluna "Padrão": Indica se é TMPV ou TMV
- Coluna "Confiabilidade": Barra visual + percentual
- Cores indicam o nível de confiabilidade

## Exemplo de Uso

### Produto: "CERVEJA HEINEKEN LATA 350ML"
- Tipo: CERVEJA ✓
- Marca: HEINEKEN ✓
- Particularidade: (não identificada)
- Volume: 350ML ✓
- **Padrão**: TMV
- **Confiabilidade**: 75% (3/4 campos identificados)

### Produto: "CHOCOLATE LACTA AO LEITE 90G"
- Tipo: CHOCOLATE ✓
- Marca: LACTA ✓
- Particularidade: AO LEITE ✓
- Volume: 90G ✓
- **Padrão**: TMPV
- **Confiabilidade**: 100% (4/4 campos identificados)

## Como Melhorar a Confiabilidade

1. **Adicionar mais marcas** ao banco de dados
2. **Incluir mais tipos** de produtos
3. **Cadastrar particularidades** específicas
4. **Adicionar volumes** comuns
5. **Configurar abreviações** para expandir termos

## Teste do Sistema

1. Execute o backend: `python main.py`
2. Popule o banco: `python popular_banco.py`
3. Execute o frontend: `npm run dev`
4. Faça upload do arquivo `teste_confiabilidade.csv`
5. Observe os diferentes níveis de confiabilidade

## Benefícios

- **Transparência**: O usuário sabe quão confiável é cada sugestão
- **Filtragem**: Pode focar em produtos com alta confiabilidade
- **Melhoria**: Identifica onde o sistema precisa de mais dados
- **Qualidade**: Garante que apenas sugestões confiáveis sejam usadas 