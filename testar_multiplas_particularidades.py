#!/usr/bin/env python3
"""
Script para testar a captura de múltiplas particularidades
"""

import asyncio
import aiohttp
import pandas as pd
import json

async def testar_multiplas_particularidades():
    """Testa a captura de múltiplas particularidades no sistema"""
    
    print("🧪 TESTANDO CAPTURA DE MÚLTIPLAS PARTICULARIDADES")
    print("=" * 60)
    
    # URL do backend
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Verificar se o backend está rodando
            print("1. Verificando se o backend está rodando...")
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    print("✅ Backend está rodando")
                else:
                    print("❌ Backend não está respondendo")
                    return
        except Exception as e:
            print(f"❌ Erro ao conectar com o backend: {e}")
            return
        
        # 2. Verificar particularidades cadastradas
        print("\n2. Verificando particularidades cadastradas...")
        async with session.get(f"{base_url}/particularidades/") as response:
            if response.status == 200:
                particularidades = await response.json()
                print(f"✅ Encontradas {len(particularidades)} particularidades:")
                for p in particularidades:
                    print(f"   - {p}")
            else:
                print("❌ Erro ao buscar particularidades")
                return
        
        # 3. Testar upload do arquivo CSV
        print("\n3. Testando upload do arquivo CSV...")
        
        # Ler o arquivo CSV
        try:
            df = pd.read_csv("teste_multiplas_particularidades.csv")
            print(f"✅ Arquivo CSV carregado com {len(df)} produtos")
        except Exception as e:
            print(f"❌ Erro ao ler arquivo CSV: {e}")
            return
        
        # Preparar dados para upload
        csv_content = df.to_csv(index=False)
        
        # Fazer upload
        data = aiohttp.FormData()
        data.add_field('file', 
                      csv_content.encode('utf-8'), 
                      filename='teste_multiplas_particularidades.csv',
                      content_type='text/csv')
        
        async with session.post(f"{base_url}/upload/", data=data) as response:
            if response.status == 200:
                resultado = await response.json()
                produtos = resultado.get('produtos', [])
                print(f"✅ Upload realizado com sucesso! {len(produtos)} produtos processados")
                
                # 4. Analisar resultados
                print("\n4. Analisando resultados das múltiplas particularidades:")
                print("-" * 60)
                
                for i, produto in enumerate(produtos, 1):
                    print(f"\n📦 Produto {i}: {produto['nome_original']}")
                    print(f"   Tipo: {produto['tipo']}")
                    print(f"   Marca: {produto['marca']}")
                    print(f"   Particularidade: '{produto['particularidade']}'")
                    print(f"   Volume: {produto['volume']}")
                    print(f"   Sugestão TMPV: {produto['sugestao_tmpv']}")
                    print(f"   Confiabilidade: {produto['confiabilidade']}%")
                    print(f"   Padrão: {produto['padrao']}")
                    
                    # Verificar se capturou múltiplas particularidades
                    if produto['particularidade']:
                        partic_count = len(produto['particularidade'].split())
                        if partic_count > 1:
                            print(f"   ✅ CAPTURADAS {partic_count} PARTICULARIDADES!")
                        else:
                            print(f"   ⚠️  Capturada apenas 1 particularidade")
                    else:
                        print(f"   ❌ Nenhuma particularidade capturada")
                
                # 5. Resumo estatístico
                print("\n5. Resumo estatístico:")
                print("-" * 30)
                
                total_produtos = len(produtos)
                produtos_com_particularidade = sum(1 for p in produtos if p['particularidade'])
                produtos_com_multiplas = sum(1 for p in produtos if p['particularidade'] and len(p['particularidade'].split()) > 1)
                
                print(f"Total de produtos: {total_produtos}")
                print(f"Produtos com particularidade: {produtos_com_particularidade}")
                print(f"Produtos com múltiplas particularidades: {produtos_com_multiplas}")
                print(f"Taxa de sucesso: {(produtos_com_particularidade/total_produtos)*100:.1f}%")
                print(f"Taxa de múltiplas: {(produtos_com_multiplas/total_produtos)*100:.1f}%")
                
                # 6. Verificar casos específicos esperados
                print("\n6. Verificando casos específicos:")
                print("-" * 30)
                
                casos_esperados = {
                    "CERVEJA HEINEKEN PREMIUM LATA 350ML": ["PREMIUM", "LATA"],
                    "CHOCOLATE AO LEITE LACTA PREMIUM 90G": ["AO LEITE", "PREMIUM"],
                    "ARROZ INTEGRAL CAMIL ORGANICO 1KG": ["INTEGRAL", "ORGANICO"],
                    "TEMPERO PARA CARNE KITANO NORDESTINO 100G": ["PARA CARNE", "NORDESTINO"]
                }
                
                for nome_original, partic_esperadas in casos_esperados.items():
                    produto = next((p for p in produtos if p['nome_original'] == nome_original), None)
                    if produto:
                        partic_encontradas = produto['particularidade'].split() if produto['particularidade'] else []
                        print(f"\n📋 {nome_original}")
                        print(f"   Esperadas: {partic_esperadas}")
                        print(f"   Encontradas: {partic_encontradas}")
                        
                        # Verificar se todas as esperadas foram encontradas
                        todas_encontradas = all(partic in produto['particularidade'] for partic in partic_esperadas)
                        if todas_encontradas:
                            print(f"   ✅ SUCESSO: Todas as particularidades foram capturadas!")
                        else:
                            print(f"   ❌ FALHA: Algumas particularidades não foram capturadas")
                    else:
                        print(f"\n❌ Produto não encontrado: {nome_original}")
                
            else:
                print(f"❌ Erro no upload: {response.status}")
                error_text = await response.text()
                print(f"Detalhes: {error_text}")
        
        print("\n" + "=" * 60)
        print("🏁 TESTE CONCLUÍDO")

if __name__ == "__main__":
    asyncio.run(testar_multiplas_particularidades()) 