import asyncio
import aiohttp
import json

async def testar_correcoes_confiabilidade():
    base_url = "http://localhost:8000"
    
    print("=== TESTANDO CORREÇÕES DA CONFIABILIDADE ===")
    
    # Produtos problemáticos da imagem
    produtos_teste = [
        "FARINHA LACTEA NESTLE 500G",      # Deve perder "LACTEA" - confiabilidade deve ser < 100%
        "MOLHO DE ALHO KNORR 200ML",       # Tipo errado, palavra repetida - confiabilidade deve ser baixa
        "TEMPERO PARA CARNE KITANO 100G",  # Deve estar correto - confiabilidade alta
        "CAFE EM GRAOS PILAO 1KG",         # Deve estar correto - confiabilidade alta
        "ARROZ INTEGRAL CAMIL ORGANICO 1KG" # Múltiplas particularidades - confiabilidade alta
    ]
    
    # Criar arquivo CSV temporário
    csv_content = "nome,ean\n"
    for i, produto in enumerate(produtos_teste):
        csv_content += f"{produto},{7891234567890 + i}\n"
    
    async with aiohttp.ClientSession() as session:
        # Primeiro, popular o banco com dados completos
        print("Populando banco com dados completos...")
        await popular_banco_completo(session)
        
        # Testar upload
        print("\nEnviando arquivo de teste...")
        data = aiohttp.FormData()
        data.add_field('file', 
                      csv_content.encode('utf-8'),
                      filename='teste_confiabilidade_corrigida.csv',
                      content_type='text/csv')
        
        async with session.post(f"{base_url}/upload/", data=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Upload realizado com sucesso!")
                print(f"📊 {len(result['produtos'])} produtos processados")
                
                # Analisar resultados detalhados
                print("\n=== ANÁLISE DAS CORREÇÕES ===")
                
                for i, produto in enumerate(result['produtos']):
                    print(f"\n{i+1}. {produto['nome_original']}")
                    print(f"   Sugestão: {produto['sugestao_tmpv']}")
                    print(f"   Padrão: {produto['padrao']}")
                    print(f"   Confiabilidade: {produto['confiabilidade']}%")
                    
                    if produto.get('detalhes_confiabilidade'):
                        detalhes = produto['detalhes_confiabilidade']
                        print(f"   📊 Detalhes:")
                        print(f"      Base: {detalhes['base']}%")
                        print(f"      Caracteres: {detalhes['fator_chars']} (razão: {detalhes['razao_chars']})")
                        print(f"      Palavras perdidas: {detalhes['fator_palavras_perdidas']}")
                        print(f"      Palavras adicionadas: {detalhes['fator_palavras_adicionadas']}")
                        print(f"      Cobertura: {detalhes['fator_cobertura']} ({detalhes['cobertura_percentual']}%)")
                        print(f"      Estrutura: {detalhes['fator_estrutura']}")
                        
                        if detalhes.get('palavras_importantes_perdidas') and detalhes['palavras_importantes_perdidas']:
                            print(f"      ❌ Importantes perdidas: {', '.join(detalhes['palavras_importantes_perdidas'])}")
                        
                        if detalhes['palavras_adicionadas']:
                            print(f"      ⚠️ Adicionadas: {', '.join(detalhes['palavras_adicionadas'])}")
                        
                        # Verificar se a confiabilidade faz sentido
                        if produto['confiabilidade'] >= 100:
                            print(f"      ⚠️ ATENÇÃO: Confiabilidade muito alta ({produto['confiabilidade']}%)")
                        elif produto['confiabilidade'] >= 80:
                            print(f"      ✅ Confiabilidade boa ({produto['confiabilidade']}%)")
                        elif produto['confiabilidade'] >= 60:
                            print(f"      ⚠️ Confiabilidade média ({produto['confiabilidade']}%)")
                        else:
                            print(f"      ❌ Confiabilidade baixa ({produto['confiabilidade']}%)")
                    
                    # Mostrar sugestões se houver
                    if produto.get('sugestoes_particularidades'):
                        print(f"   💡 Sugestões: {', '.join(produto['sugestoes_particularidades'])}")
                
                # Estatísticas gerais
                confiabilidades = [p['confiabilidade'] for p in result['produtos']]
                print(f"\n=== ESTATÍSTICAS ===")
                print(f"📈 Confiabilidade média: {sum(confiabilidades)/len(confiabilidades):.1f}%")
                print(f"📊 Confiabilidade mínima: {min(confiabilidades):.1f}%")
                print(f"📊 Confiabilidade máxima: {max(confiabilidades):.1f}%")
                
                # Verificar se as correções funcionaram
                alta = sum(1 for c in confiabilidades if c >= 80)
                media = sum(1 for c in confiabilidades if 60 <= c < 80)
                baixa = sum(1 for c in confiabilidades if c < 60)
                
                print(f"🟢 Alta confiabilidade (≥80%): {alta} produtos")
                print(f"🟡 Média confiabilidade (60-79%): {media} produtos")
                print(f"🔴 Baixa confiabilidade (<60%): {baixa} produtos")
                
                # Verificar se há produtos com 100% que não deveriam ter
                produtos_100_percent = [p for p in result['produtos'] if p['confiabilidade'] >= 100]
                if produtos_100_percent:
                    print(f"\n⚠️ PRODUTOS COM 100% DE CONFIABILIDADE:")
                    for p in produtos_100_percent:
                        print(f"   - {p['nome_original']} → {p['sugestao_tmpv']}")
                
            else:
                print(f"❌ Erro no upload: {resp.status}")
                error_text = await resp.text()
                print(f"Detalhes: {error_text}")

async def popular_banco_completo(session):
    base_url = "http://localhost:8000"
    
    # Dados completos para teste
    marcas = ["HEINEKEN", "LACTA", "CAMIL", "KITANO", "NESTLE", "KNORR", "PILAO", "PEPSI", "BRAHMA"]
    tipos = ["CERVEJA", "CHOCOLATE", "ARROZ", "TEMPERO", "FARINHA", "MOLHO", "CAFE", "REFRIGERANTE"]
    particularidades = [
        "AO LEITE", "INTEGRAL", "ORGANICO", "PARA CARNE", "NORDESTINO", "FARINHA LACTEA", 
        "MOLHO DE ALHO", "EM GRAOS", "TRADICIONAL", "ZERO ACUCAR", "DIET", "CHOPP", 
        "ARTESANAL", "PREMIUM", "LATA", "MAIS SABOR", "LACTEA", "DE ALHO"
    ]
    volumes = ["350ML", "90G", "1KG", "100G", "500G", "200ML", "2L", "473ML", "60G"]
    
    print("  Populando marcas...")
    for marca in marcas:
        data = aiohttp.FormData()
        data.add_field('nome', marca)
        async with session.post(f"{base_url}/marcas/", data=data) as resp:
            result = await resp.json()
            print(f"    ✓ {marca}")
    
    print("  Populando tipos...")
    for tipo in tipos:
        data = aiohttp.FormData()
        data.add_field('nome', tipo)
        async with session.post(f"{base_url}/tipos/", data=data) as resp:
            result = await resp.json()
            print(f"    ✓ {tipo}")
    
    print("  Populando particularidades...")
    for part in particularidades:
        data = aiohttp.FormData()
        data.add_field('nome', part)
        async with session.post(f"{base_url}/particularidades/", data=data) as resp:
            result = await resp.json()
            print(f"    ✓ {part}")
    
    print("  Populando volumes...")
    for volume in volumes:
        data = aiohttp.FormData()
        data.add_field('nome', volume)
        async with session.post(f"{base_url}/volumes/", data=data) as resp:
            result = await resp.json()
            print(f"    ✓ {volume}")
    
    print("  Inicializando abreviações...")
    async with session.post(f"{base_url}/abreviacoes/inicializar/") as resp:
        result = await resp.json()
        print(f"    ✓ {result['adicionadas']} abreviações adicionadas")

if __name__ == "__main__":
    print("🚀 Iniciando teste das correções da confiabilidade...")
    print("⚠️  Certifique-se de que o backend está rodando em http://localhost:8000")
    print()
    
    try:
        asyncio.run(testar_correcoes_confiabilidade())
        print("\n✅ Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        print("Certifique-se de que o backend está rodando e acessível.") 