from playwright.sync_api import sync_playwright
import time
import pandas as pd
import re


def scrape_portal_inmobiliario(url, max_pages=3, headless=False):
    """
    Scraper simple que:
    1. Entra a la página
    2. Hace scroll hasta el final
    3. Extrae información básica de propiedades (excluyendo proyectos)
    4. Da click en "Siguiente" para navegar páginas
    """
    all_properties = []  # Lista para guardar toda la información de propiedades

    with sync_playwright() as p:
        # Lanzar navegador
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            print(f"\n{'='*60}")
            print(f"Iniciando scraper para: {url}")
            print(f"Máximo de páginas: {max_pages}")
            print(f"{'='*60}\n")

            # Navegar a la primera página
            print("📄 Cargando página...")
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)

            # Cerrar popups y modals
            close_popups_and_modals(page)

            # Procesar múltiples páginas
            current_page = 1
            for page_num in range(1, max_pages + 1):
                current_page = page_num
                print(f"\n{'─'*60}")
                print(f"PÁGINA {page_num}")
                print(f"{'─'*60}")

                # Hacer scroll hasta el final para cargar todo el contenido
                print("📜 Haciendo scroll hasta el final...")
                scroll_to_bottom(page)
                print("✓ Scroll completado\n")

                # Extraer información de propiedades (excluyendo proyectos)
                print("📊 Extrayendo información de propiedades...")
                page_properties = extract_property_info(page)
                all_properties.extend(page_properties)

                print(f"✓ Propiedades válidas encontradas en esta página: {len(page_properties)}")
                print(f"✓ Total acumulado: {len(all_properties)}\n")

                # Intentar ir a la siguiente página
                if page_num < max_pages:
                    print("🔄 Buscando botón 'Siguiente'...")

                    # Cerrar cualquier popup que pueda haber aparecido
                    close_popups_and_modals(page)

                    # Buscar la paginación y hacer scroll hacia ella
                    print("   Buscando paginación en la página...")
                    try:
                        # Intentar encontrar el elemento de paginación primero
                        pagination = page.locator('.andes-pagination, nav[aria-label*="pagination"], nav[aria-label*="Paginación"]').first
                        if pagination.is_visible(timeout=2000):
                            pagination.scroll_into_view_if_needed()
                            print("   ✓ Paginación encontrada y visible")
                            time.sleep(0.5)
                    except:
                        # Si no se encuentra, hacer scroll hacia arriba
                        print("   Haciendo scroll hacia arriba...")
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight - 1500)")
                        time.sleep(0.5)

                    if go_to_next_page(page):
                        print("✓ Navegado a la siguiente página\n")
                        time.sleep(2)
                    else:
                        print("⚠️  No se encontró botón 'Siguiente' o última página alcanzada")
                        break

            print(f"\n{'='*60}")
            print("✅ Scraping completado!")
            print(f"{'='*60}\n")

            # Mostrar resumen de extracción
            print(f"📋 RESUMEN DE EXTRACCIÓN:")
            print(f"   Total de propiedades encontradas: {len(all_properties)}")
            print(f"   Páginas procesadas: {current_page}\n")

            # Mostrar las primeras propiedades como ejemplo
            if all_properties:
                print("📊 Primeras propiedades extraídas (ejemplo):")
                for i, prop in enumerate(all_properties[:5], 1):
                    ubicacion = prop.get('ubicacion') or 'N/A'
                    ubicacion_short = ubicacion[:50] if len(ubicacion) > 50 else ubicacion
                    print(f"   {i}. {prop.get('dormitorios') or 'N/A'} dorm | "
                          f"{prop.get('banos') or 'N/A'} baños | "
                          f"{prop.get('superficie') or 'N/A'} | "
                          f"{ubicacion_short}...")
                if len(all_properties) > 5:
                    print(f"   ... y {len(all_properties) - 5} más\n")
                else:
                    print()

            # Guardar información en CSV
            if all_properties:
                save_to_csv(all_properties, 'data/property_basic_info.csv')
                # También guardar solo las URLs en un archivo de texto
                urls_only = [prop['url'] for prop in all_properties if 'url' in prop]
                save_urls_to_file(urls_only, 'data/property_urls.txt')

            return all_properties

        except Exception as e:
            print(f"\n❌ Error durante el scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            browser.close()


def scroll_to_bottom(page, pause_time=0.5):
    """
    Hace scroll hasta el final de la página de manera gradual
    para cargar todo el contenido lazy-loaded
    """
    last_height = page.evaluate("document.body.scrollHeight")
    scroll_attempts = 0
    max_attempts = 10

    while scroll_attempts < max_attempts:
        # Scroll hacia abajo
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause_time)

        # Obtener nueva altura
        new_height = page.evaluate("document.body.scrollHeight")

        # Si no cambió la altura, ya llegamos al final
        if new_height == last_height:
            break

        last_height = new_height
        scroll_attempts += 1

    # Volver arriba
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.3)


def extract_property_info(page):
    """
    Extrae información básica de propiedades individuales, excluyendo proyectos.

    Filtra propiedades que tienen:
    - El tag "PROYECTO"
    - "X unidades disponibles"

    Extrae:
    - URL
    - Dormitorios
    - Baños
    - Superficie (m²)
    - Ubicación
    """
    properties = []
    seen_urls = set()

    # Buscar todos los artículos/cards de propiedades
    article_selectors = [
        'article',
        'li[class*="ui-search-layout__item"]',
        'div[class*="ui-search-result"]',
        '.poly-card'
    ]

    articles = []
    for selector in article_selectors:
        try:
            found = page.locator(selector).all()
            if found and len(found) > 5:
                articles = found
                print(f"   Usando selector: {selector} ({len(articles)} elementos)")
                break
        except:
            continue

    if not articles:
        print("   ⚠️ No se encontraron artículos de propiedades")
        return properties

    total_analyzed = 0
    skipped_proyecto = 0
    skipped_unidades = 0
    added = 0

    for article in articles:
        total_analyzed += 1

        try:
            # Obtener el HTML interno del artículo
            html_content = article.inner_html()

            # Verificar si es un proyecto (tiene el tag PROYECTO)
            if 'poly-pill__pill' in html_content and 'PROYECTO' in html_content.upper():
                skipped_proyecto += 1
                continue

            # Verificar si tiene "unidades disponibles"
            if 'poly-component__available-units' in html_content or 'unidades disponibles' in html_content.lower():
                skipped_unidades += 1
                continue

            # Inicializar diccionario de propiedad
            property_data = {
                'url': None,
                'dormitorios': None,
                'banos': None,
                'superficie': None,
                'ubicacion': None
            }

            # Extraer URL
            links = article.locator('a[href*="/MLC-"]').all()
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue

                    # Construir URL completa
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"https://www.portalinmobiliario.com{href}"
                    else:
                        full_url = f"https://www.portalinmobiliario.com/{href}"

                    # Evitar duplicados
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        property_data['url'] = full_url
                        break

                except:
                    continue

            if not property_data['url']:
                continue

            # Extraer atributos (dormitorios, baños, superficie)
            try:
                attributes = article.locator('.poly-attributes_list__item').all()
                for attr in attributes:
                    text = attr.inner_text().strip()

                    # Dormitorios
                    if 'dormitorio' in text.lower():
                        match = re.search(r'(\d+)', text)
                        if match:
                            property_data['dormitorios'] = match.group(1)

                    # Baños
                    elif 'baño' in text.lower():
                        match = re.search(r'(\d+)', text)
                        if match:
                            property_data['banos'] = match.group(1)

                    # Superficie (m²)
                    elif 'm²' in text or 'm2' in text.lower():
                        match = re.search(r'(\d+(?:\.\d+)?)\s*m', text)
                        if match:
                            property_data['superficie'] = f"{match.group(1)} m²"

            except Exception:
                pass

            # Extraer ubicación
            try:
                location_elem = article.locator('.poly-component__location').first
                if location_elem.is_visible():
                    property_data['ubicacion'] = location_elem.inner_text().strip()
            except Exception:
                pass

            # Agregar a la lista
            properties.append(property_data)
            added += 1

        except Exception:
            continue

    print(f"   📊 Análisis: {total_analyzed} artículos | "
          f"Proyectos: {skipped_proyecto} | "
          f"Unidades múltiples: {skipped_unidades} | "
          f"✓ Válidas: {added}")

    return properties


def save_to_csv(properties, filepath='data/property_basic_info.csv'):
    """
    Guarda la información de propiedades en un archivo CSV
    """
    try:
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Crear DataFrame de pandas
        df = pd.DataFrame(properties)

        # Reordenar columnas
        columns_order = ['url', 'dormitorios', 'banos', 'superficie', 'ubicacion']
        df = df[columns_order]

        # Guardar a CSV
        df.to_csv(filepath, index=False, encoding='utf-8')

        print(f"💾 Datos guardados en CSV: {filepath}")
        print(f"   Columnas: {', '.join(df.columns.tolist())}")
        print(f"   Total de filas: {len(df)}")

    except Exception as e:
        print(f"⚠️ Error al guardar CSV: {e}")


def save_urls_to_file(urls, filepath='data/property_urls.txt'):
    """
    Guarda las URLs en un archivo de texto
    """
    try:
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")

        print(f"💾 URLs guardadas en: {filepath}")

    except Exception as e:
        print(f"⚠️ Error al guardar archivo: {e}")


def close_popups_and_modals(page):
    """
    Cierra popups, modals y banners que puedan estar bloqueando la página
    """
    # Lista de selectores para cerrar popups
    close_selectors = [
        # Botón "Entendido" del modal de mapa
        'button:has-text("Entendido")',
        # Botón "Aceptar" de cookies
        'button:has-text("Aceptar")',
        'button:has-text("Acepto")',
        # Botones de cerrar (X)
        'button[aria-label="Cerrar"]',
        'button[aria-label="Close"]',
        '[class*="close-button"]',
        '[class*="modal"] button:has-text("×")',
        # Banner de publicidad
        '.ad-banner button',
        '[class*="banner"] button[class*="close"]',
    ]

    for selector in close_selectors:
        try:
            button = page.locator(selector).first
            if button.is_visible(timeout=1000):
                button.click()
                print(f"   ✓ Popup/modal cerrado con: {selector}")
                time.sleep(0.5)
        except:
            continue


def go_to_next_page(page):
    """
    Busca y hace click en el botón 'Siguiente' para ir a la próxima página
    """
    # Lista de selectores comunes para el botón "Siguiente"
    selectors = [
        '.andes-pagination__button--next a',  # Selector más específico primero
        'li.andes-pagination__button--next a',
        'a.andes-pagination__link[aria-label*="iguiente"]',
        'a:has-text("Siguiente")',
        'button:has-text("Siguiente")',
        'a[title*="iguiente"]',
        'a[aria-label*="iguiente"]',
        '.ui-search-pagination a[aria-label*="Siguiente"]',
    ]

    for selector in selectors:
        try:
            next_button = page.locator(selector).first
            if next_button.is_visible(timeout=3000):
                # Verificar que no esté deshabilitado
                is_disabled = next_button.evaluate('''(el) => {
                    const parent = el.closest('li');
                    return el.classList.contains('disabled') ||
                           el.getAttribute('aria-disabled') === 'true' ||
                           el.hasAttribute('disabled') ||
                           (parent && (parent.classList.contains('disabled') ||
                                      parent.classList.contains('andes-pagination__button--disabled')));
                }''')

                if not is_disabled:
                    print(f"   ✓ Botón encontrado con selector: {selector}")
                    # Hacer scroll al botón por si acaso
                    next_button.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    # Hacer click y esperar a que cargue
                    next_button.click()
                    page.wait_for_load_state('domcontentloaded', timeout=10000)
                    return True
                else:
                    print(f"   ⚠️ Botón encontrado pero está deshabilitado (última página)")
        except Exception:
            continue

    return False


if __name__ == "__main__":
    # URL de ejemplo
    url = "https://www.portalinmobiliario.com/venta/departamento/las-condes-metropolitana"

    # Ejecutar scraper
    # headless=False para ver el navegador en acción
    # headless=True para ejecución en segundo plano
    scrape_portal_inmobiliario(url, max_pages=3, headless=False)
