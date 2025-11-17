"""Verificar se a página do SEFAZ está acessível e como ela responde"""
import asyncio
from playwright.async_api import async_playwright

async def check_sefaz_page():
    print("\n" + "="*80)
    print("VERIFICANDO PÁGINA DO SEFAZ")
    print("="*80 + "\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = "https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin"
        
        print(f"Acessando: {url}\n")
        
        try:
            response = await page.goto(url, timeout=60000)
            print(f"✅ Página carregou")
            print(f"   Status HTTP: {response.status}")
            print(f"   URL final: {page.url}")
            print(f"   Título: {await page.title()}\n")
            
            # Aguardar página carregar
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Salvar HTML
            html = await page.content()
            with open("debug_sefaz_login_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            await page.screenshot(path="debug_sefaz_login_page.png", full_page=True)
            
            print(f"📊 Informações da página:")
            print(f"   Tamanho HTML: {len(html):,} bytes")
            
            # Verificar campos de login
            print(f"\n🔍 Verificando campos de login:")
            
            user_field = await page.query_selector('input[name="identificacao"]')
            if user_field:
                print(f"   ✅ Campo 'identificacao' encontrado")
            else:
                print(f"   ❌ Campo 'identificacao' NÃO encontrado")
                
            pass_field = await page.query_selector('input[name="senha"]')
            if pass_field:
                print(f"   ✅ Campo 'senha' encontrado")
            else:
                print(f"   ❌ Campo 'senha' NÃO encontrado")
            
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                print(f"   ✅ Botão submit encontrado")
            else:
                print(f"   ❌ Botão submit NÃO encontrado")
            
            # Verificar se há captcha
            captcha = await page.query_selector('[class*="captcha"], [id*="captcha"], iframe[src*="recaptcha"]')
            if captcha:
                print(f"   ⚠️  CAPTCHA detectado!")
            else:
                print(f"   ✅ Sem CAPTCHA visível")
            
            # Verificar mensagens de erro ou avisos
            print(f"\n📝 Procurando mensagens na página:")
            page_text = await page.text_content('body')
            
            keywords = ['erro', 'inválido', 'incorreto', 'bloqueado', 'suspenso', 'manutenção', 
                       'indisponível', 'temporariamente', 'fora do ar']
            
            for keyword in keywords:
                if keyword.lower() in page_text.lower():
                    print(f"   ⚠️  Encontrado: '{keyword}'")
            
            # Listar todos os inputs
            print(f"\n📋 Todos os campos input encontrados:")
            inputs = await page.query_selector_all('input')
            for inp in inputs:
                name = await inp.get_attribute('name')
                input_type = await inp.get_attribute('type')
                placeholder = await inp.get_attribute('placeholder')
                print(f"   - name='{name}' type='{input_type}' placeholder='{placeholder}'")
            
            print(f"\n💾 Arquivos salvos:")
            print(f"   - debug_sefaz_login_page.html")
            print(f"   - debug_sefaz_login_page.png")
            
            print(f"\n⏸️  Navegador ficará aberto por 2 minutos para você inspecionar.")
            print(f"   Tente fazer login manualmente e veja qual erro aparece.")
            print(f"   Pressione Ctrl+C para fechar antes.\n")
            
            await asyncio.sleep(120)
            
        except Exception as e:
            print(f"\n❌ ERRO ao acessar página: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_sefaz_page())
