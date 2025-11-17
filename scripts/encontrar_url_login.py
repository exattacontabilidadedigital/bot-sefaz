"""
Script para encontrar a URL correta de login da SEFAZ-RS
"""
import asyncio
from playwright.async_api import async_playwright

async def encontrar_url_login():
    """Tenta encontrar a URL correta de login"""
    
    urls_para_testar = [
        # URLs antigas conhecidas
        "https://www.sefaz.rs.gov.br/ASP/AAE_ROOT/AAE_LOGIN.asp",
        
        # Possíveis novas URLs
        "https://www.sefaz.rs.gov.br/",
        "https://cad.sefaz.rs.gov.br/",
        "https://www.sefaz.rs.gov.br/login",
        "https://www.sefaz.rs.gov.br/ASP/AAE_LOGIN.asp",
        "https://cav.sefaz.rs.gov.br/",
        "https://www.sefaznet.rs.gov.br/",
        "https://atf.sefaz.rs.gov.br/",
        
        # URLs modernas
        "https://sefaz.rs.gov.br/login",
        "https://sefaz.rs.gov.br/inicial",
    ]
    
    print("🔍 Procurando URL correta de login da SEFAZ-RS...\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        for url in urls_para_testar:
            print(f"\n{'='*80}")
            print(f"🌐 Testando: {url}")
            print('='*80)
            
            page = await context.new_page()
            
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                
                # Verificar status code
                status = response.status if response else 0
                print(f"📊 Status Code: {status}")
                
                # Verificar título
                titulo = await page.title()
                print(f"📄 Título: {titulo}")
                
                # Verificar URL final (após redirects)
                url_final = page.url
                print(f"🔗 URL Final: {url_final}")
                
                # Procurar por campos de login
                campo_usuario = await page.query_selector("input[name='identificacao'], input[name='usuario'], input[name='username'], input[type='text']")
                campo_senha = await page.query_selector("input[name='senha'], input[name='password'], input[type='password']")
                botao_entrar = await page.query_selector("input[type='submit'], button[type='submit']")
                
                tem_login = campo_usuario and campo_senha
                
                if tem_login:
                    print("✅ PÁGINA DE LOGIN ENCONTRADA!")
                    print(f"\n🎯 Campo usuário: {await campo_usuario.get_attribute('name') if campo_usuario else 'não encontrado'}")
                    print(f"🎯 Campo senha: {await campo_senha.get_attribute('name') if campo_senha else 'não encontrado'}")
                    
                    if botao_entrar:
                        botao_type = await botao_entrar.evaluate("el => el.tagName")
                        botao_value = await botao_entrar.get_attribute('value') or await botao_entrar.inner_text()
                        print(f"🎯 Botão: <{botao_type.lower()}> '{botao_value}'")
                    
                    # Salvar HTML
                    html = await page.content()
                    with open(f"login_encontrado_{len(urls_para_testar)}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"\n💾 HTML salvo: login_encontrado_{len(urls_para_testar)}.html")
                    
                    # Screenshot
                    await page.screenshot(path=f"login_encontrado_{len(urls_para_testar)}.png")
                    print(f"📸 Screenshot salva: login_encontrado_{len(urls_para_testar)}.png")
                    
                    print("\n" + "="*80)
                    print("🎉 URL CORRETA DE LOGIN ENCONTRADA!")
                    print("="*80)
                    print(f"\n✅ Use esta URL: {url_final}")
                    
                    input("\nPressione ENTER para continuar testando outras URLs...")
                else:
                    print("❌ Não é página de login")
                
            except Exception as e:
                print(f"❌ Erro ao acessar: {str(e)[:100]}")
            
            finally:
                await page.close()
        
        print("\n" + "="*80)
        print("🏁 TESTE CONCLUÍDO")
        print("="*80)
        
        input("\nPressione ENTER para fechar...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(encontrar_url_login())
