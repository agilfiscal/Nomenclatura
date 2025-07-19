import asyncio
import aiohttp
import json

async def testar_sistema_particularidades():
    base_url = "http://localhost:8000"
    
    print("=== TESTANDO SISTEMA DE SUGESTÕES DE PARTICULARIDADES ===")
    
    # Produtos que devem gerar sugestões de particularidades
    produtos_teste = [
        "TEMPERO MAIS SABOR KITANO NORDESTINO 60G",  # Deve sugerir: NORDESTINO
        "CERVEJA HEINEKEN PREMIUM LATA 350ML",       # Deve sugerir: PREMIUM
        "CHOCOLATE LACTA AO LEITE PREMIUM 90G",      # Deve sugerir: PREMIUM
        "ARROZ INTEGRAL CAMIL ORGANICO 1KG",         # Deve sugerir: ORGANICO
        "CAFE PILAO TRADICIONAL GOURMET 500G",       # Deve sugerir: GOURMET
        "REFRIGERANTE COCA COLA ZERO DIET 2L",       # Deve sugerir: ZERO
        "CERVEJA BRAHMA CHOPP ARTESANAL 473ML",      # Deve sugerir: ARTESANAL
        "REFRIGERANTE PEPSI DIET LIGHT 350ML"        # Deve sugerir: LIGHT
    ]
    
    # Criar arquivo CSV temporário
    csv_content = "nome,ean\n"
    for i, produto in enumerate(produtos_teste):
        csv_content += f"{produto},{7891234567890 + i}\n"
    
    async with aiohttp.ClientSession() as session:
        # Primeiro, popular o banco com dados básicos
        print("Populando banco com dados básicos...")
        await popular_banco_basico(session)
        
        # Testar upload
        print("\nEnviando arquivo de teste...")
        data = aiohttp.FormData()
        data.add_field('file', 
                      csv_content.encode('utf-8'),
                      filename='teste_particularidades.csv',
                      content_type='text/csv')
        
        async with session.post(f"{base_url}/upload/", data=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Upload realizado com sucesso!")
                print(f"📊 {len(result['produtos'])} produtos processados")
                
                # Analisar sugestões de particularidades
                print("\n=== ANÁLISE DAS SUGESTÕES DE PARTICULARIDADES ===")
                
                produtos_com_sugestoes = 0
                total_sugestoes = 0
                
                for i, produto in enumerate(result['produtos']):
                    print(f"\n{i+1}. {produto['nome_original']}")
                    print(f"   Padrão atual: {produto['padrao']}")
                    print(f"   Confiabilidade: {produto['confiabilidade']}%")
                    
                    if produto['sugestoes_particularidades'] and len(produto['sugestoes_particularidades']) > 0:
                        produtos_com_sugestoes += 1
                        total_sugestoes += len(produto['sugestoes_particularidades'])
                        print(f"   💡 Sugestões: {', '.join(produto['sugestoes_particularidades'])}")
                        
                        # Testar cadastro de uma particularidade
                        if produto['sugestoes_particularidades']:
                            sugestao_teste = produto['sugestoes_particularidades'][0]
                            print(f"   🧪 Testando cadastro de '{sugestao_teste}'...")
                            
                            # Cadastrar particularidade
                            form_data = aiohttp.FormData()
                            form_data.add_field('nome', sugestao_teste)
                            
                            async with session.post(f"{base_url}/particularidades/sugerir/", data=form_data) as cadastro_resp:
                                cadastro_result = await cadastro_resp.json()
                                if cadastro_result['status'] == 'adicionado':
                                    print(f"   ✅ '{sugestao_teste}' cadastrada com sucesso!")
                                elif cadastro_result['status'] == 'já_existia':
                                    print(f"   ℹ️ '{sugestao_teste}' já existia no banco")
                                else:
                                    print(f"   ❌ Erro ao cadastrar '{sugestao_teste}': {cadastro_result['mensagem']}")
                    else:
                        print(f"   ℹ️ Nenhuma sugestão de particularidade")
                
                print(f"\n=== RESUMO ===")
                print(f"📈 Produtos com sugestões: {produtos_com_sugestoes}/{len(result['produtos'])}")
                print(f"💡 Total de sugestões: {total_sugestoes}")
                print(f"📊 Média de sugestões por produto: {total_sugestoes/len(result['produtos']):.1f}")
                
            else:
                print(f"❌ Erro no upload: {resp.status}")
                error_text = await resp.text()
                print(f"Detalhes: {error_text}")

async def popular_banco_basico(session):
    base_url = "http://localhost:8000"
    
    # Dados básicos (sem as particularidades que queremos testar)
    marcas = ["HEINEKEN", "COCA COLA", "LACTA", "CAMIL", "PILAO", "BRAHMA", "PEPSI", "KITANO"]
    tipos = ["CERVEJA", "REFRIGERANTE", "CHOCOLATE", "ARROZ", "CAFE", "TEMPERO"]
    particularidades = ["AO LEITE", "INTEGRAL", "TRADICIONAL", "CHOPP", "DIET"]  # Sem as novas
    volumes = ["350ML", "2L", "90G", "1KG", "500G", "473ML", "60G"]
    
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
    
    print("  Populando particularidades básicas...")
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
    print("🚀 Iniciando teste do sistema de sugestões de particularidades...")
    print("⚠️  Certifique-se de que o backend está rodando em http://localhost:8000")
    print()
    
    try:
        asyncio.run(testar_sistema_particularidades())
        print("\n✅ Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        print("Certifique-se de que o backend está rodando e acessível.") 