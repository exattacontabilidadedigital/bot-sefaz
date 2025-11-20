"""
Módulo para simulação de comportamento humano em automação web.

Este módulo centraliza todas as funções relacionadas à simulação de comportamento
humano para evitar detecção de automação.
"""

import asyncio
import random
from typing import Optional, Union
from playwright.async_api import Page, ElementHandle, Locator


class HumanBehavior:
    """Classe para simulação de comportamento humano realista"""
    
    # Constantes para delays (em milissegundos) - Mais humanísticas
    DELAY_MIN_HUMAN = 150
    DELAY_MAX_HUMAN = 1200
    DELAY_MIN_TYPING = 80
    DELAY_MAX_TYPING = 350
    DELAY_MIN_MOUSE = 200
    DELAY_MAX_MOUSE = 800
    DELAY_MIN_PAUSE = 800
    DELAY_MAX_PAUSE = 3500
    
    @staticmethod
    def random_delay(min_ms: int = DELAY_MIN_HUMAN, max_ms: int = DELAY_MAX_HUMAN) -> int:
        """
        Gera delay aleatório para simular comportamento humano com distribuição mais realista
        
        Args:
            min_ms: Tempo mínimo em milissegundos
            max_ms: Tempo máximo em milissegundos
            
        Returns:
            int: Delay em milissegundos
        """
        # Usar distribuição normal para comportamento mais humano
        mean = (min_ms + max_ms) / 2
        std_dev = (max_ms - min_ms) / 6  # 99.7% dos valores dentro do range
        
        delay = random.normalvariate(mean, std_dev)
        return max(min_ms, min(max_ms, int(delay)))
    
    @staticmethod
    async def human_type_text(page: Page, element: Union[ElementHandle, Locator], text: str, 
                             clear_first: bool = True) -> None:
        """
        Digita texto com comportamento humano mais realista
        
        Args:
            page: Página do Playwright
            element: Elemento onde digitar
            text: Texto a ser digitado
            clear_first: Se deve limpar o campo antes
        """
        # Focar no elemento primeiro
        await element.focus()
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        # Limpar campo se solicitado
        if clear_first:
            await element.press('Control+a')
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Digitar caractere por caractere com delays humanos
        for i, char in enumerate(text):
            # Simular algumas correções (typos) ocasionais
            if random.random() < 0.02 and i > 0:  # 2% de chance de "erro"
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await element.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.4))
                await element.press('Backspace')
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Digitar caractere correto
            await element.type(char)
            
            # Delay entre caracteres com variação humanística
            base_delay = random.uniform(0.08, 0.25)
            
            # Delays maiores após espaços e pontos
            if char in [' ', '.', ',', ';']:
                base_delay *= random.uniform(1.5, 2.5)
            
            # Pausas ocasionais (como se a pessoa parasse para pensar)
            if random.random() < 0.05:  # 5% de chance
                base_delay *= random.uniform(3, 8)
            
            await asyncio.sleep(base_delay)
    
    @staticmethod
    def random_position_in_element(width: float, height: float) -> tuple[float, float]:
        """
        Gera posição aleatória dentro de um elemento
        
        Args:
            width: Largura do elemento
            height: Altura do elemento
            
        Returns:
            tuple: (x_offset, y_offset) relativos ao elemento
        """
        # Evitar bordas extremas
        margin_x = max(10, width * 0.1)
        margin_y = max(5, height * 0.1)
        
        x_offset = random.uniform(margin_x, width - margin_x)
        y_offset = random.uniform(margin_y, height - margin_y)
        
        return x_offset, y_offset
    
    @staticmethod
    def calculate_typing_delay(char: str) -> int:
        """
        Calcula delay para digitação baseado no tipo de caractere
        
        Args:
            char: Caractere sendo digitado
            
        Returns:
            int: Delay em milissegundos
        """
        if char.isdigit():
            return HumanBehavior.random_delay(80, 200)
        elif char in ".-@":
            return HumanBehavior.random_delay(200, 500)
        elif char.isupper():
            return HumanBehavior.random_delay(150, 350)
        else:
            return HumanBehavior.random_delay(100, 280)
    
    @staticmethod
    async def human_click(
        page: Page, 
        element: Union[ElementHandle, Locator], 
        delay_before: Optional[int] = None,
        delay_after: Optional[int] = None
    ) -> None:
        """
        Simula clique humano com movimento de mouse
        
        Args:
            page: Página do Playwright
            element: Elemento a ser clicado
            delay_before: Delay antes do clique (ms)
            delay_after: Delay após o clique (ms)
        """
        try:
            # Delay antes do clique
            if delay_before:
                await page.wait_for_timeout(delay_before)
            else:
                await page.wait_for_timeout(HumanBehavior.random_delay(100, 300))
            
            # Obter bounding box do elemento
            box = await element.bounding_box()
            
            if box:
                # Calcular posição aleatória dentro do elemento
                x_offset, y_offset = HumanBehavior.random_position_in_element(
                    box['width'], box['height']
                )
                
                x = box['x'] + x_offset
                y = box['y'] + y_offset
                
                # Mover mouse para a posição
                await page.mouse.move(x, y)
                await page.wait_for_timeout(HumanBehavior.random_delay(50, 150))
                
                # Clicar
                await page.mouse.click(x, y)
            else:
                # Fallback para clique direto no elemento
                await element.click()
            
            # Delay após o clique
            if delay_after:
                await page.wait_for_timeout(delay_after)
            else:
                await page.wait_for_timeout(HumanBehavior.random_delay(200, 500))
                
        except Exception as e:
            # Fallback em caso de erro
            await element.click()
            if delay_after:
                await page.wait_for_timeout(delay_after)
    
    @staticmethod
    async def human_type(
        page: Page, 
        element: Union[ElementHandle, Locator], 
        text: str,
        clear_first: bool = True
    ) -> None:
        """
        Simula digitação humana realista com velocidade variável
        
        Args:
            page: Página do Playwright
            element: Elemento onde digitar
            text: Texto a ser digitado
            clear_first: Se deve limpar o campo antes de digitar
        """
        try:
            # Clicar no elemento primeiro
            await HumanBehavior.human_click(page, element)
            
            # Limpar campo se solicitado
            if clear_first:
                await page.keyboard.press("Control+A")
                await page.wait_for_timeout(HumanBehavior.random_delay(50, 150))
                await page.keyboard.press("Backspace")
                await page.wait_for_timeout(HumanBehavior.random_delay(200, 500))
            
            # Simular "pensamento" antes de digitar
            await page.wait_for_timeout(HumanBehavior.random_delay(300, 1200))
            
            # Digitar caractere por caractere
            for i, char in enumerate(text):
                delay = HumanBehavior.calculate_typing_delay(char)
                
                # Burst typing ocasional (30% de chance de digitar mais rápido)
                if i > 0 and random.random() < 0.3:
                    delay = int(delay * 0.6)
                
                # Pausa mais longa ocasional (5% de chance)
                if random.random() < 0.05:
                    delay = HumanBehavior.random_delay(800, 2000)
                
                # Digitar caractere
                await element.type(char, delay=0)
                await page.wait_for_timeout(delay)
                
                # Movimento de mouse ocasional (15% de chance)
                if random.random() < 0.15:
                    await HumanBehavior._random_mouse_movement(page, element)
            
            # Pausa após terminar (usuário revisa)
            await page.wait_for_timeout(HumanBehavior.random_delay(300, 800))
            
        except Exception as e:
            # Fallback para preenchimento direto
            await element.fill(text)
            await page.wait_for_timeout(HumanBehavior.random_delay(500, 1000))
    
    @staticmethod
    async def _random_mouse_movement(page: Page, element: Union[ElementHandle, Locator]) -> None:
        """Movimento aleatório do mouse próximo ao elemento"""
        try:
            box = await element.bounding_box()
            if box:
                # Movimento próximo ao elemento
                x = box['x'] + random.randint(-50, int(box['width']) + 50)
                y = box['y'] + random.randint(-30, int(box['height']) + 30)
                await page.mouse.move(x, y)
        except:
            pass  # Ignorar erros de movimento
    
    @staticmethod
    async def simulate_reading_pause(page: Page, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """
        Simula pausa de leitura humana
        
        Args:
            page: Página do Playwright
            min_seconds: Tempo mínimo de pausa
            max_seconds: Tempo máximo de pausa
        """
        delay_ms = random.randint(int(min_seconds * 1000), int(max_seconds * 1000))
        await page.wait_for_timeout(delay_ms)
    
    @staticmethod
    async def simulate_page_scanning(page: Page, num_movements: int = 3) -> None:
        """
        Simula movimento do mouse pela página (como se estivesse lendo/procurando)
        
        Args:
            page: Página do Playwright  
            num_movements: Número de movimentos do mouse
        """
        for _ in range(random.randint(2, num_movements)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await page.wait_for_timeout(HumanBehavior.random_delay(300, 800))
    
    @staticmethod
    async def hover_before_click(page: Page, element: Union[ElementHandle, Locator]) -> None:
        """
        Simula hover antes de clicar (comportamento humano comum)
        
        Args:
            page: Página do Playwright
            element: Elemento para fazer hover
        """
        try:
            await element.hover()
            await page.wait_for_timeout(HumanBehavior.random_delay(200, 600))
        except:
            pass  # Ignorar erros de hover
    
    @staticmethod
    async def wait_for_page_stability(page: Page, timeout: int = 30000) -> None:
        """
        Aguarda a página estabilizar após uma ação
        
        Args:
            page: Página do Playwright
            timeout: Timeout em milissegundos
        """
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except:
            # Fallback para timeout fixo se networkidle falhar
            await page.wait_for_timeout(3000)
    
    @staticmethod
    def should_add_random_pause() -> bool:
        """
        Decide aleatoriamente se deve adicionar uma pausa extra
        
        Returns:
            bool: True se deve pausar (20% de chance)
        """
        return random.random() < 0.2
    
    @staticmethod
    async def conditional_pause(page: Page) -> None:
        """
        Adiciona pausa condicional baseada em probabilidade
        
        Args:
            page: Página do Playwright
        """
        if HumanBehavior.should_add_random_pause():
            await page.wait_for_timeout(HumanBehavior.random_delay(1000, 3000))
    
    @staticmethod
    async def scroll_into_view_naturally(page: Page, element: Union[ElementHandle, Locator]) -> None:
        """
        Faz scroll até o elemento de forma natural
        
        Args:
            page: Página do Playwright
            element: Elemento a ser visualizado
        """
        try:
            # Scroll gradual em vez de scroll direto
            await element.scroll_into_view_if_needed()
            await page.wait_for_timeout(HumanBehavior.random_delay(300, 700))
        except:
            pass
    
    @staticmethod
    async def simulate_form_navigation(page: Page, elements: list) -> None:
        """
        Simula navegação natural entre campos de formulário
        
        Args:
            page: Página do Playwright
            elements: Lista de elementos do formulário
        """
        for i, element in enumerate(elements):
            if i > 0:
                # Pausa entre campos
                await page.wait_for_timeout(HumanBehavior.random_delay(500, 1500))
            
            # Scroll até o elemento se necessário
            await HumanBehavior.scroll_into_view_naturally(page, element)
            
            # Hover antes de interagir
            await HumanBehavior.hover_before_click(page, element)


class AntiDetection:
    """Classe para métodos anti-detecção"""
    
    @staticmethod
    async def setup_page_scripts(page: Page) -> None:
        """
        Configura scripts anti-detecção na página
        
        Args:
            page: Página do Playwright
        """
        await page.add_init_script("""
            // Remover webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Sobrescrever chrome runtime
            window.chrome = {
                runtime: {}
            };
            
            // Adicionar propriedades reais do navigator
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ],
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
            
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.',
            });
            
            // Adicionar permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Sobrescrever toString para esconder traces
            const modifiedNavigator = Navigator.prototype;
            Object.getOwnPropertyNames(modifiedNavigator).forEach(prop => {
                if (prop !== 'userAgent') {
                    try {
                        const original = modifiedNavigator[prop];
                        modifiedNavigator.__defineGetter__(prop, function() {
                            if (prop === 'webdriver') return undefined;
                            return original;
                        });
                    } catch (e) {}
                }
            });
        """)
    
    @staticmethod
    def get_human_user_agent() -> str:
        """
        Retorna user agent humano realista
        
        Returns:
            str: User agent string
        """
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    @staticmethod
    def get_browser_viewport() -> dict:
        """
        Retorna configurações de viewport realistas
        
        Returns:
            dict: Configurações de viewport
        """
        return {
            'width': 1920,
            'height': 1080
        }