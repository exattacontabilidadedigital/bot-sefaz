"""
Script de diagnóstico para identificar seletores da página de login SEFAZ
"""
import asyncio
from playwright.async_api import async_playwright
import sys
import os

# Adicionar o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def diagnosticar_login():
    """Captura e analisa a página de login da SEFAZ"""
    
    print("🔍 Iniciando diagnóstico da página de login SEFAZ...")
    
    async with async_playwright() as p:
        # Iniciar browser
        print("🌐 Iniciando navegador...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navegar para página de login
        url = "https://www.sefaz.rs.gov.br/ASP/AAE_ROOT/AAE_LOGIN.asp"
        print(f"📍 Navegando para: {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        print("\n" + "="*80)
        print("📋 DIAGNÓSTICO DA PÁGINA DE LOGIN")
        print("="*80)
        
        # Verificar título da página
        titulo = await page.title()
        print(f"\n📄 Título da página: {titulo}")
        
        # Verificar URL atual
        url_atual = page.url
        print(f"🔗 URL atual: {url_atual}")
        
        # Verificar campos de input
        print("\n" + "-"*80)
        print("🔍 CAMPOS DE INPUT ENCONTRADOS:")
        print("-"*80)
        
        inputs = await page.query_selector_all("input")
        for i, input_elem in enumerate(inputs, 1):
            input_type = await input_elem.get_attribute("type") or "text"
            input_name = await input_elem.get_attribute("name") or "(sem name)"
            input_id = await input_elem.get_attribute("id") or "(sem id)"
            input_value = await input_elem.get_attribute("value") or "(vazio)"
            input_placeholder = await input_elem.get_attribute("placeholder") or "(sem placeholder)"
            
            print(f"\nInput {i}:")
            print(f"  • Type: {input_type}")
            print(f"  • Name: {input_name}")
            print(f"  • ID: {input_id}")
            print(f"  • Value: {input_value}")
            print(f"  • Placeholder: {input_placeholder}")
        
        # Verificar botões
        print("\n" + "-"*80)
        print("🔍 BOTÕES ENCONTRADOS:")
        print("-"*80)
        
        buttons = await page.query_selector_all("button, input[type='submit'], input[type='button']")
        for i, button in enumerate(buttons, 1):
            tag = await button.evaluate("el => el.tagName")
            button_type = await button.get_attribute("type") or "button"
            button_name = await button.get_attribute("name") or "(sem name)"
            button_id = await button.get_attribute("id") or "(sem id)"
            button_value = await button.get_attribute("value") or "(vazio)"
            button_text = await button.inner_text() if tag == "BUTTON" else "(N/A)"
            button_onclick = await button.get_attribute("onclick") or "(sem onclick)"
            
            print(f"\nBotão {i}:")
            print(f"  • Tag: {tag}")
            print(f"  • Type: {button_type}")
            print(f"  • Name: {button_name}")
            print(f"  • ID: {button_id}")
            print(f"  • Value: {button_value}")
            print(f"  • Text: {button_text}")
            print(f"  • OnClick: {button_onclick[:50]}..." if len(button_onclick) > 50 else f"  • OnClick: {button_onclick}")
        
        # Verificar forms
        print("\n" + "-"*80)
        print("🔍 FORMULÁRIOS ENCONTRADOS:")
        print("-"*80)
        
        forms = await page.query_selector_all("form")
        for i, form in enumerate(forms, 1):
            form_name = await form.get_attribute("name") or "(sem name)"
            form_id = await form.get_attribute("id") or "(sem id)"
            form_action = await form.get_attribute("action") or "(sem action)"
            form_method = await form.get_attribute("method") or "GET"
            
            print(f"\nForm {i}:")
            print(f"  • Name: {form_name}")
            print(f"  • ID: {form_id}")
            print(f"  • Action: {form_action}")
            print(f"  • Method: {form_method}")
        
        # Salvar HTML da página
        print("\n" + "-"*80)
        print("💾 SALVANDO HTML DA PÁGINA...")
        print("-"*80)
        
        html_content = await page.content()
        output_file = "debug_login_page.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ HTML salvo em: {output_file}")
        
        # Capturar screenshot
        screenshot_file = "debug_login_screenshot.png"
        await page.screenshot(path=screenshot_file, full_page=True)
        print(f"📸 Screenshot salvo em: {screenshot_file}")
        
        print("\n" + "="*80)
        print("✅ DIAGNÓSTICO CONCLUÍDO!")
        print("="*80)
        print("\nPressione ENTER para fechar o navegador...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnosticar_login())
