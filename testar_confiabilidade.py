import asyncio
import aiohttp
import json

async def testar_confiabilidade():
    base_url = "http://localhost:8000"
    
    # Primeiro, popular o banco
    print("=== POPULANDO BANCO DE DADOS ===")
    await popular_banco()
    
    print("\n=== TESTANDO SISTEMA DE CONFIABILIDADE ===")
    
    # Dados de teste com diferentes níveis de confiabilidade
    produtos_teste = [
        "CERVEJA HEINEKEN LATA 350ML",  # TMV - 75%
        "REFRIGERANTE COCA COLA 2L",     # TMV - 75%
        "CHOCOLATE LACTA AO LEITE 90G",  # TMPV - 100%
        "ARROZ INTEGRAL CAMIL 1KG",      # TMPV - 100%
        "CAFE PILAO TRADICIONAL 500G",   # TMPV - 100%
        "PRODUTO DESCONHECIDO XYZ",      # Baixa confiabilidade
        "CERVEJA BRAHMA CHOPP 473ML",    # TMPV - 100%
        "REFRIGERANTE PEPSI DIET 350ML"  # TMPV - 100%
    ]
    
    # Criar arquivo CSV temporário
    csv_content = "nome,ean\n"
    for i, produto in enumerate(produtos_teste):
        csv_content += f"{produto},{7891234567890 + i}\n"
    
    # Simular upload
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('file', 
                      csv_content.encode('utf-8'),
                      filename='teste.csv',
                      content_type='text/csv')
        
        print("Enviando arquivo de teste...")
        async with session.post(f"{base_url}/upload/", data=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Upload realizado com sucesso!")
                print(f"📊 {len(result['produtos'])} produtos processados")
                
                # Analisar resultados
                print("\n=== ANÁLISE DOS RESULTADOS ===")
                
                # Estatísticas gerais
                total = len(result['produtos'])
                confiabilidade_media = sum(p['confiabilidade'] for p in result['produtos']) / total
                tmpv_count = sum(1 for p in result['produtos'] if p['padrao'] == 'TMPV')
                tmv_count = sum(1 for p in result['produtos'] if p['padrao'] == 'TMV')
                alta_conf = sum(1 for p in result['produtos'] if p['confiabilidade'] >= 75)
                media_conf = sum(1 for p in result['produtos'] if p['confiabilidade'] >= 50 and p['confiabilidade'] < 75)
                baixa_conf = sum(1 for p in result['produtos'] if p['confiabilidade'] < 50)
                
                print(f"📈 Confiabilidade Média: {confiabilidade_media:.1f}%")
                print(f"🏷️  Padrão TMPV: {tmpv_count} produtos")
                print(f"🏷️  Padrão TMV: {tmv_count} produtos")
                print(f"🟢 Alta Confiabilidade (≥75%): {alta_conf} produtos")
                print(f"🟡 Média Confiabilidade (50-74%): {media_conf} produtos")
                print(f"🔴 Baixa Confiabilidade (<50%): {baixa_conf} produtos")
                
                # Detalhes por produto
                print("\n=== DETALHES POR PRODUTO ===")
                for i, produto in enumerate(result['produtos']):
                    print(f"\n{i+1}. {produto['nome_original']}")
                    print(f"   Sugestão: {produto['sugestao_tmpv']}")
                    print(f"   Padrão: {produto['padrao']}")
                    print(f"   Confiabilidade: {produto['confiabilidade']}%")
                    print(f"   Campos: T={produto['tipo']}, M={produto['marca']}, P={produto['particularidade']}, V={produto['volume']}")
                
            else:
                print(f"❌ Erro no upload: {resp.status}")
                error_text = await resp.text()
                print(f"Detalhes: {error_text}")

async def popular_banco():
    base_url = "http://localhost:8000"
    
    # Dados de teste
    marcas = ["HEINEKEN", "COCA COLA", "LACTA", "CAMIL", "PILAO", "BRAHMA", "PEPSI"]
    tipos = ["CERVEJA", "REFRIGERANTE", "CHOCOLATE", "ARROZ", "CAFE"]
    particularidades = ["AO LEITE", "INTEGRAL", "TRADICIONAL", "CHOPP", "DIET"]
    volumes = ["350ML", "2L", "90G", "1KG", "500G", "473ML"]
    
    async with aiohttp.ClientSession() as session:
        print("Populando marcas...")
        for marca in marcas:
            data = aiohttp.FormData()
            data.add_field('nome', marca)
            async with session.post(f"{base_url}/marcas/", data=data) as resp:
                result = await resp.json()
                print(f"  ✓ {marca}")
        
        print("Populando tipos...")
        for tipo in tipos:
            data = aiohttp.FormData()
            data.add_field('nome', tipo)
            async with session.post(f"{base_url}/tipos/", data=data) as resp:
                result = await resp.json()
                print(f"  ✓ {tipo}")
        
        print("Populando particularidades...")
        for part in particularidades:
            data = aiohttp.FormData()
            data.add_field('nome', part)
            async with session.post(f"{base_url}/particularidades/", data=data) as resp:
                result = await resp.json()
                print(f"  ✓ {part}")
        
        print("Populando volumes...")
        for volume in volumes:
            data = aiohttp.FormData()
            data.add_field('nome', volume)
            async with session.post(f"{base_url}/volumes/", data=data) as resp:
                result = await resp.json()
                print(f"  ✓ {volume}")
        
        print("Inicializando abreviações...")
        async with session.post(f"{base_url}/abreviacoes/inicializar/") as resp:
            result = await resp.json()
            print(f"  ✓ {result['adicionadas']} abreviações adicionadas")

if __name__ == "__main__":
    print("🚀 Iniciando teste do sistema de confiabilidade...")
    print("⚠️  Certifique-se de que o backend está rodando em http://localhost:8000")
    print()
    
    try:
        asyncio.run(testar_confiabilidade())
        print("\n✅ Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        print("Certifique-se de que o backend está rodando e acessível.") 