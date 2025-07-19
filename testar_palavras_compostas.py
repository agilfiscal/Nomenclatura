import asyncio
import aiohttp
import json

async def testar_palavras_compostas():
    base_url = "http://localhost:8000"
    
    print("=== TESTANDO SISTEMA DE PALAVRAS COMPOSTAS ===")
    
    # Produtos que devem testar palavras compostas
    produtos_teste = [
        "FARINHA LACTEA NESTLE 500G",           # Deve encontrar: FARINHA LACTEA
        "MOLHO DE ALHO KNORR 200ML",            # Deve encontrar: MOLHO DE ALHO
        "TEMPERO PARA CARNE KITANO 100G",       # Deve encontrar: PARA CARNE
        "CAFE EM GRAOS PILAO 1KG",              # Deve encontrar: EM GRAOS
        "ARROZ INTEGRAL CAMIL ORGANICO 1KG",    # Deve encontrar: INTEGRAL + ORGANICO
        "CHOCOLATE AO LEITE LACTA PREMIUM 90G", # Deve encontrar: AO LEITE + PREMIUM
        "CERVEJA SEM ALCOOL BRAHMA 350ML",      # Deve encontrar: SEM ALCOOL
        "REFRIGERANTE ZERO ACUCAR PEPSI 2L",    # Deve encontrar: ZERO ACUCAR
        "TEMPERO PARA FRANGO KITANO 80G",       # Deve encontrar: PARA FRANGO
        "MOLHO DE TOMATE HELLMANNS 500ML"       # Deve encontrar: DE TOMATE
    ]
    
    # Criar arquivo CSV temporário
    csv_content = "nome,ean\n"
    for i, produto in enumerate(produtos_teste):
        csv_content += f"{produto},{7891234567890 + i}\n"
    
    async with aiohttp.ClientSession() as session:
        # Primeiro, popular o banco com dados incluindo palavras compostas
        print("Populando banco com palavras compostas...")
        await popular_banco_compostas(session)
        
        # Testar upload
        print("\nEnviando arquivo de teste...")
        data = aiohttp.FormData()
        data.add_field('file', 
                      csv_content.encode('utf-8'),
                      filename='teste_palavras_compostas.csv',
                      content_type='text/csv')
        
        async with session.post(f"{base_url}/upload/", data=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Upload realizado com sucesso!")
                print(f"📊 {len(result['produtos'])} produtos processados")
                
                # Analisar resultados
                print("\n=== ANÁLISE DAS PALAVRAS COMPOSTAS ===")
                
                produtos_tmpv = 0
                produtos_tmv = 0
                total_particularidades = 0
                
                for i, produto in enumerate(result['produtos']):
                    print(f"\n{i+1}. {produto['nome_original']}")
                    print(f"   Padrão: {produto['padrao']}")
                    print(f"   Confiabilidade: {produto['confiabilidade']}%")
                    print(f"   Tipo: {produto['tipo']}")
                    print(f"   Marca: {produto['marca']}")
                    print(f"   Particularidade: {produto['particularidade']}")
                    print(f"   Volume: {produto['volume']}")
                    print(f"   Sugestão: {produto['sugestao_tmpv']}")
                    
                    if produto['padrao'] == 'TMPV':
                        produtos_tmpv += 1
                        total_particularidades += 1
                    else:
                        produtos_tmv += 1
                        
                        # Mostrar sugestões se houver
                        if produto['sugestoes_particularidades']:
                            print(f"   💡 Sugestões: {', '.join(produto['sugestoes_particularidades'])}")
                            total_particularidades += len(produto['sugestoes_particularidades'])
                
                print(f"\n=== RESUMO ===")
                print(f"📈 Produtos TMPV: {produtos_tmpv}/{len(result['produtos'])} ({produtos_tmpv/len(result['produtos'])*100:.1f}%)")
                print(f"📈 Produtos TMV: {produtos_tmv}/{len(result['produtos'])} ({produtos_tmv/len(result['produtos'])*100:.1f}%)")
                print(f"💡 Total de particularidades identificadas: {total_particularidades}")
                print(f"📊 Confiabilidade média: {sum(p['confiabilidade'] for p in result['produtos'])/len(result['produtos']):.1f}%")
                
            else:
                print(f"❌ Erro no upload: {resp.status}")
                error_text = await resp.text()
                print(f"Detalhes: {error_text}")

async def popular_banco_compostas(session):
    base_url = "http://localhost:8000"
    
    # Dados incluindo palavras compostas
    marcas = ["HEINEKEN", "COCA COLA", "LACTA", "CAMIL", "PILAO", "BRAHMA", "PEPSI", "KITANO", "NESTLE", "KNORR", "HELLMANNS"]
    tipos = ["CERVEJA", "REFRIGERANTE", "CHOCOLATE", "ARROZ", "CAFE", "TEMPERO", "FARINHA", "MOLHO"]
    particularidades = [
        "AO LEITE", "INTEGRAL", "TRADICIONAL", "CHOPP", "DIET", "NORDESTINO",
        "FARINHA LACTEA", "MOLHO DE ALHO", "PARA CARNE", "EM GRAOS", "ORGANICO", 
        "PREMIUM", "SEM ALCOOL", "ZERO ACUCAR", "PARA FRANGO", "DE TOMATE"
    ]
    volumes = ["350ML", "2L", "90G", "1KG", "500G", "473ML", "60G", "200ML", "100G", "80G"]
    
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
    
    print("  Populando particularidades (incluindo compostas)...")
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
    print("🚀 Iniciando teste do sistema de palavras compostas...")
    print("⚠️  Certifique-se de que o backend está rodando em http://localhost:8000")
    print()
    
    try:
        asyncio.run(testar_palavras_compostas())
        print("\n✅ Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        print("Certifique-se de que o backend está rodando e acessível.") 