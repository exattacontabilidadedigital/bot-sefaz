"""
Teste rápido da URL de login SEFAZ-MA
"""
import asyncio
from playwright.async_api import async_playwright

async def testar_login_ma():
    url = "https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin"
    
    print(f"🔍 Testando URL: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("📍 Navegando para página de login...")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        print(f"\n✅ Página carregada!")
        print(f"📄 Título: {await page.title()}")
        print(f"🔗 URL: {page.url}\n")
        
        print("="*80)
        print("🔍 ANALISANDO SELETORES")
        print("="*80)
        
        # Testar seletores atuais
        seletores_teste = {
            "Campo usuário (name='identificacao')": "input[name='identificacao']",
            "Campo senha (name='senha')": "input[name='senha']",
            "Botão submit (value='Entrar')": "input[type='submit'][value='Entrar']",
            "Qualquer input text": "input[type='text']",
            "Qualquer input password": "input[type='password']",
            "Qualquer botão submit": "input[type='submit'], button[type='submit']",
        }
        
        for descricao, seletor in seletores_teste.items():
            elemento = await page.query_selector(seletor)
            if elemento:
                tag = await elemento.evaluate("el => el.tagName")
                name = await elemento.get_attribute("name") or "(sem name)"
                id_attr = await elemento.get_attribute("id") or "(sem id)"
                value = await elemento.get_attribute("value") or ""
                tipo = await elemento.get_attribute("type") or ""
                
                print(f"\n✅ {descricao}")
                print(f"   Seletor: {seletor}")
                print(f"   Tag: {tag}, Type: {tipo}, Name: {name}, ID: {id_attr}, Value: {value}")
            else:
                print(f"\n❌ {descricao}")
                print(f"   Seletor: {seletor} - NÃO ENCONTRADO")
        
        # Listar TODOS os inputs
        print("\n" + "="*80)
        print("📋 TODOS OS INPUTS DA PÁGINA")
        print("="*80)
        
        inputs = await page.query_selector_all("input")
        for i, inp in enumerate(inputs, 1):
            tag = await inp.evaluate("el => el.tagName")
            tipo = await inp.get_attribute("type") or "text"
            name = await inp.get_attribute("name") or "(sem name)"
            id_attr = await inp.get_attribute("id") or "(sem id)"
            value = await inp.get_attribute("value") or ""
            
            print(f"\n{i}. <{tag.lower()} type='{tipo}' name='{name}' id='{id_attr}' value='{value}'>")
        
        # Salvar HTML
        print("\n" + "="*80)
        html = await page.content()
        with open("sefaz_ma_login.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("💾 HTML salvo: sefaz_ma_login.html")
        
        await page.screenshot(path="sefaz_ma_login.png", full_page=True)
        print("📸 Screenshot: sefaz_ma_login.png")
        print("="*80)
        
        input("\n\nPressione ENTER para fechar...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(testar_login_ma())
