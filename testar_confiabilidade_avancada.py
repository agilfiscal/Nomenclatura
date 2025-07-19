import asyncio
import aiohttp
import json

async def testar_confiabilidade_avancada():
    base_url = "http://localhost:8000"
    
    print("=== TESTANDO SISTEMA DE CONFIABILIDADE AVANÇADA ===")
    
    # Produtos que testam diferentes aspectos da confiabilidade
    produtos_teste = [
        "CERVEJA HEINEKEN PREMIUM LATA 350ML",      # Muitas palavras, boa cobertura
        "CHOCOLATE AO LEITE LACTA PREMIUM 90G",     # Palavras compostas, boa estrutura
        "ARROZ INTEGRAL CAMIL ORGANICO 1KG",        # Múltiplas particularidades
        "TEMPERO PARA CARNE KITANO NORDESTINO 100G", # Muitas palavras importantes
        "FARINHA LACTEA NESTLE 500G",               # Palavra composta específica
        "MOLHO DE ALHO KNORR 200ML",                # Palavra composta específica
        "CAFE EM GRAOS PILAO TRADICIONAL 1KG",      # Múltiplas particularidades
        "REFRIGERANTE ZERO ACUCAR PEPSI DIET 2L",   # Muitas palavras, possível perda
        "CERVEJA BRAHMA CHOPP ARTESANAL 473ML",     # Palavras específicas
        "TEMPERO MAIS SABOR KITANO NORDESTINO 60G"  # Muitas palavras, teste de perda
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
                      filename='teste_confiabilidade_avancada.csv',
                      content_type='text/csv')
        
        async with session.post(f"{base_url}/upload/", data=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Upload realizado com sucesso!")
                print(f"📊 {len(result['produtos'])} produtos processados")
                
                # Analisar resultados detalhados
                print("\n=== ANÁLISE DETALHADA DA CONFIABILIDADE ===")
                
                confiabilidades = []
                produtos_analisados = 0
                
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
                        print(f"      Cobertura: {detalhes['fator_cobertura']}")
                        print(f"      Estrutura: {detalhes['fator_estrutura']}")
                        
                        if detalhes['palavras_perdidas']:
                            print(f"      ❌ Palavras perdidas: {', '.join(detalhes['palavras_perdidas'])}")
                        
                        confiabilidades.append(produto['confiabilidade'])
                        produtos_analisados += 1
                    
                    # Mostrar sugestões se houver
                    if produto.get('sugestoes_particularidades'):
                        print(f"   💡 Sugestões: {', '.join(produto['sugestoes_particularidades'])}")
                
                # Estatísticas gerais
                if confiabilidades:
                    print(f"\n=== ESTATÍSTICAS ===")
                    print(f"📈 Confiabilidade média: {sum(confiabilidades)/len(confiabilidades):.1f}%")
                    print(f"📊 Confiabilidade mínima: {min(confiabilidades):.1f}%")
                    print(f"📊 Confiabilidade máxima: {max(confiabilidades):.1f}%")
                    print(f"📊 Produtos analisados: {produtos_analisados}")
                    
                    # Análise por faixas
                    alta = sum(1 for c in confiabilidades if c >= 75)
                    media = sum(1 for c in confiabilidades if 50 <= c < 75)
                    baixa = sum(1 for c in confiabilidades if c < 50)
                    
                    print(f"🟢 Alta confiabilidade (≥75%): {alta} produtos")
                    print(f"🟡 Média confiabilidade (50-74%): {media} produtos")
                    print(f"🔴 Baixa confiabilidade (<50%): {baixa} produtos")
                
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
        "ARTESANAL", "PREMIUM", "LATA", "MAIS SABOR"
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
    print("🚀 Iniciando teste do sistema de confiabilidade avançada...")
    print("⚠️  Certifique-se de que o backend está rodando em http://localhost:8000")
    print()
    
    try:
        asyncio.run(testar_confiabilidade_avancada())
        print("\n✅ Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        print("Certifique-se de que o backend está rodando e acessível.") 