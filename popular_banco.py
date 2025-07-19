import asyncio
import aiohttp
import json

async def popular_banco():
    base_url = "http://localhost:8000"
    
    # Dados de teste
    marcas = ["HEINEKEN", "COCA COLA", "LACTA", "CAMIL", "PILAO", "BRAHMA", "PEPSI", "KITANO", "NESTLE", "KNORR", "HELLMANNS"]
    tipos = ["CERVEJA", "REFRIGERANTE", "CHOCOLATE", "ARROZ", "CAFE", "TEMPERO", "FARINHA", "MOLHO"]
    particularidades = [
        "AO LEITE", "INTEGRAL", "TRADICIONAL", "CHOPP", "DIET", "NORDESTINO",
        "FARINHA LACTEA", "MOLHO DE ALHO", "PARA CARNE", "EM GRAOS", "ORGANICO", 
        "PREMIUM", "SEM ALCOOL", "ZERO ACUCAR", "PARA FRANGO", "DE TOMATE"
    ]
    volumes = ["350ML", "2L", "90G", "1KG", "500G", "473ML", "60G", "200ML", "100G", "80G"]
    
    async with aiohttp.ClientSession() as session:
        print("Populando marcas...")
        for marca in marcas:
            data = aiohttp.FormData()
            data.add_field('nome', marca)
            async with session.post(f"{base_url}/marcas/", data=data) as resp:
                result = await resp.json()
                print(f"Marca {marca}: {result['status']}")
        
        print("\nPopulando tipos...")
        for tipo in tipos:
            data = aiohttp.FormData()
            data.add_field('nome', tipo)
            async with session.post(f"{base_url}/tipos/", data=data) as resp:
                result = await resp.json()
                print(f"Tipo {tipo}: {result['status']}")
        
        print("\nPopulando particularidades...")
        for part in particularidades:
            data = aiohttp.FormData()
            data.add_field('nome', part)
            async with session.post(f"{base_url}/particularidades/", data=data) as resp:
                result = await resp.json()
                print(f"Particularidade {part}: {result['status']}")
        
        print("\nPopulando volumes...")
        for volume in volumes:
            data = aiohttp.FormData()
            data.add_field('nome', volume)
            async with session.post(f"{base_url}/volumes/", data=data) as resp:
                result = await resp.json()
                print(f"Volume {volume}: {result['status']}")
        
        print("\nInicializando abreviações...")
        async with session.post(f"{base_url}/abreviacoes/inicializar/") as resp:
            result = await resp.json()
            print(f"Abreviações: {result['adicionadas']} adicionadas, {result['ja_existiam']} já existiam")
        
        print("\nBanco de dados populado com sucesso!")

if __name__ == "__main__":
    asyncio.run(popular_banco()) 