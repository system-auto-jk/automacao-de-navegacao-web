import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog, messagebox
import threading, time, os
from datetime import datetime
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from ia_core import conversar_ia, interpretar_comando
from navegador import iniciar_navegador
from memory_manager import MemoryManager

APP_TITLE = "System Auto JK - Web-IA v6.1 (Macro Controller)"
SAJK_GREEN = "#00FF88"
SAJK_PURPLE = "#6D28D9"
BG = "#0D0E11"

ctk.set_appearance_mode("dark")


class Accordion(ctk.CTkFrame):
    def __init__(self, master, title: str, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(fg_color="#0B0C10")
        self.columnconfigure(0, weight=1)
        self.opened = True
        self.btn = ctk.CTkButton(
            self,
            text=title,
            fg_color="#111318",
            hover_color="#1b1f27",
            corner_radius=8,
            anchor="w",
            command=self.toggle,
        )
        self.btn.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        self.content = ctk.CTkFrame(self, fg_color="#0F1115", corner_radius=8)
        self.content.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

    def toggle(self):
        if self.opened:
            self.content.grid_remove()
            self.opened = False
        else:
            self.content.grid()
            self.opened = True


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1260x900")
        self.configure(fg_color=BG)

        self.driver = None
        self.mm = MemoryManager()
        self.executando = False
        self.executando_macro = False
        self.gravando_macro = None
        self.gravando_count = 0

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color="#0B0C10")
        self.header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.header.grid_columnconfigure(1, weight=1)
        self.header_label = ctk.CTkLabel(
            self.header,
            text="System Auto JK – Web-IA",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=SAJK_GREEN,
        )
        self.header_label.grid(row=0, column=0, padx=14, pady=(10, 0), sticky="w")
        self.status_lbl = ctk.CTkLabel(
            self.header,
            text="IA pronta – Navegador: inativo",
            text_color="#94a3b8",
        )
        self.status_lbl.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")
        self.header_macro_btn = None

        self.url_entry = ctk.CTkEntry(self.header, placeholder_text="https://...")
        self.url_entry.grid(row=0, column=1, padx=(10, 4), pady=12, sticky="ew")
        ctk.CTkButton(
            self.header,
            text="Abrir",
            fg_color=SAJK_GREEN,
            text_color="black",
            command=self._abrir_da_barra,
        ).grid(row=0, column=2, padx=(4, 10), pady=12)

        # Sidebar
        self.sidebar = ctk.CTkScrollableFrame(self, width=300, corner_radius=0, fg_color="#0B0C10")
        self.sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)

        def add_btn(parent, text, cmd, color=SAJK_PURPLE):
            b = ctk.CTkButton(parent, text=text, fg_color=color, hover_color="#4C1D95", command=cmd)
            b.pack(fill="x", padx=10, pady=6)
            return b

        nav = Accordion(self.sidebar, "Navegação")
        nav.grid(row=0, column=0, sticky="ew")
        add_btn(nav.content, "Abrir Site", lambda: self._processar(self.url_entry.get() or "https://www.gazetadopovo.com.br/"))
        add_btn(nav.content, "Recarregar", lambda: self._processar("recarregar"))
        add_btn(nav.content, "Voltar", lambda: self._processar("voltar"))
        add_btn(nav.content, "Avançar", lambda: self._processar("avançar"))
        add_btn(nav.content, "Nova Aba", lambda: self._processar("abrir nova aba"))
        add_btn(nav.content, "Fechar Aba", lambda: self._processar("fechar aba"))

        ext = Accordion(self.sidebar, "Extração de Conteúdo")
        ext.grid(row=1, column=0, sticky="ew")
        add_btn(ext.content, "Extrair Notícias", lambda: self._processar("pegue as noticias"), SAJK_GREEN)
        add_btn(ext.content, "Extrair Links", lambda: self._processar("extrair links"))
        add_btn(ext.content, "Extrair Imagens", lambda: self._processar("extrair imagens"))
        add_btn(ext.content, "Extrair Tabelas", lambda: self._processar("extrair tabelas"))
        add_btn(ext.content, "Salvar HTML", lambda: self._processar("salvar html"))

        ia = Accordion(self.sidebar, "IA e Memória")
        ia.grid(row=2, column=0, sticky="ew")
        add_btn(ia.content, "Resumir Página", lambda: self._processar("resuma a página atual"))
        add_btn(ia.content, "Listar Notícias", lambda: self._processar("listar noticias"))
        add_btn(ia.content, "Exportar JSON", lambda: self._processar("exportar json"))

        macros = Accordion(self.sidebar, "Macros e Capturas")
        macros.grid(row=3, column=0, sticky="ew")
        add_btn(macros.content, "Criar Macro", lambda: self._processar("criar macro"))
        add_btn(macros.content, "Parar Macro", lambda: self._processar("parar macro"))
        add_btn(macros.content, "Listar Macros", lambda: self._processar("listar macros"))
        add_btn(macros.content, "Screenshot", lambda: self._processar("screenshot"))

        # Content area
        self.content = ctk.CTkFrame(self, corner_radius=12, fg_color="#111318")
        self.content.grid(row=1, column=1, sticky="nsew", padx=12, pady=12)
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.cards = ctk.CTkScrollableFrame(self.content, fg_color="#0F1115")
        self.cards.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))
        ctk.CTkLabel(self.cards, text="Notícias (use 'Extrair Notícias' para preencher)", text_color="#9aa4b2").grid(row=0, column=0, padx=10, pady=8, sticky="w")

        self.log = ctk.CTkTextbox(self.content, height=240, wrap="word", fg_color="#0F1115", text_color="#E5E7EB")
        self.log.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        self._log("Bem-vindo ao " + APP_TITLE)

        # Command line
        self.cmd_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0B0C10")
        self.cmd_frame.grid(row=2, column=1, sticky="ew", padx=12, pady=(0, 10))
        self.cmd_frame.grid_columnconfigure(0, weight=1)

        self.cmd_entry = ctk.CTkEntry(
            self.cmd_frame,
            placeholder_text="Ex.: 'clique no id login', 'escreva \"ola\" no xpath //input', 'abrir https://...'",
            height=44,
        )
        self.cmd_entry.grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=10)
        self.cmd_entry.bind("<Return>", self.enviar_cmd)
        ctk.CTkButton(
            self.cmd_frame, text="Enviar", fg_color=SAJK_GREEN, text_color="black", command=self.enviar_cmd
        ).grid(row=0, column=1, padx=(6, 10), pady=10)

        # Shortcuts
        self.bind_all("<Control-e>", lambda e: self._processar("pegue as noticias"))
        self.bind_all("<Control-l>", lambda e: self._limpar())
        self.bind_all("<Control-p>", lambda e: self._processar("screenshot"))
        self.bind_all("<Control-s>", lambda e: self._processar("exportar json"))
        self.bind_all("<Control-Left>", lambda e: self._processar("voltar"))
        self.bind_all("<Control-Right>", lambda e: self._processar("avançar"))
        self.bind_all("<Control-r>", lambda e: self._processar("recarregar"))

    def _log(self, msg: str):
        def _do():
            self.log.configure(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            m = msg if msg.endswith("\n") else msg + "\n"
            self.log.insert("end", f"[{ts}] {m}")
            self.log.see("end")
            self.log.configure(state="disabled")
        self._on_ui(_do)

    def _set_status(self, txt):
        def _do():
            self.status_lbl.configure(text=txt)
            try:
                self.update_idletasks()
            except Exception:
                pass
        self._on_ui(_do)

    def _limpar(self, *args):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._log("Log limpo.")

    def _abrir_da_barra(self):
        url = self.url_entry.get().strip()
        if url:
            if not url.startswith("http"):
                url = "https://" + url
            self._processar(f"abrir {url}")

    def enviar_cmd(self, event=None):
        texto = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, "end")
        if not texto:
            return
        self._log("Você: " + texto)
        self.mm.set_ultimo(texto)
        threading.Thread(target=self._processar, args=(texto,), daemon=True).start()

    def _processar(self, texto):
        if self.executando:
            self._log("Ainda processando o comando anterior...")
            return
        self.executando = True
        try:
            html = ""
            if self.driver:
                try:
                    html = self.driver.page_source
                except Exception:
                    pass
            acao = interpretar_comando(texto, html)
            self._executar_acao(acao, entrada_original=texto)
        finally:
            self.executando = False

    def _executar_acao(self, acao: dict, entrada_original: str = ""):
        nome = acao.get("acao", "desconhecida")
        try:
            # registrar em macro (captura comandos vindos de qualquer origem)
            if (
                self.gravando_macro
                and not self.executando_macro
                and entrada_original
                and nome not in {"criar_macro", "parar_macro", "rodar_macro", "listar_macros"}
            ):
                macro = self.mm.obter_macro(self.gravando_macro) or []
                macro.append(entrada_original)
                self.mm.salvar_macro(self.gravando_macro, macro)
                self.gravando_count += 1
                self._update_macro_header()
                self._log(f"Gravado na macro '{self.gravando_macro}' (comando {self.gravando_count}).")
            # Abertura direta de URL se o usuário digitar uma URL
            if self.driver is None and nome not in ["abrir_url"] and (
                entrada_original.startswith("http") or ".com" in entrada_original or "www" in entrada_original
            ):
                url = entrada_original if entrada_original.startswith("http") else "https://" + entrada_original
                self._abrir_url(url)
                return

            if nome == "abrir_url":
                self._abrir_url(acao.get("valor"))
                return
            if nome == "voltar":
                self.driver.back(); time.sleep(1); self._log("Voltar")
                return
            if nome == "avancar" or nome == "avançar":
                self.driver.forward(); time.sleep(1); self._log("Avançar")
                return
            if nome == "recarregar":
                self.driver.refresh(); time.sleep(1); self._log("Página recarregada")
                return
            if nome == "nova_aba":
                self.driver.switch_to.new_window('tab'); self._log("Nova aba aberta")
                return
            if nome == "fechar_aba":
                self.driver.close(); self._log("Aba fechada")
                return

            if nome == "rolar":
                direcao = acao.get("valor", "down")
                if direcao == "down":
                    self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.9);")
                    self._log("Rolagem para baixo")
                else:
                    self.driver.execute_script("window.scrollBy(0, -window.innerHeight * 0.9);")
                    self._log("Rolagem para cima")
                return

            if nome == "clicar":
                self._clicar_smart(acao.get("localizador"))
                return

            if nome == "digitar":
                self._digitar_smart(acao.get("texto", ""), acao.get("localizador"))
                return

            if nome == "enter":
                self._enter(); return

            if nome == "fechar_popup":
                self._fechar_popup(); return

            if nome == "extrair_noticias":
                self._extrair_noticias(); return
            if nome == "extrair_links":
                self._extrair_links(); return
            if nome == "extrair_imagens":
                self._extrair_imagens(); return
            if nome == "extrair_tabelas":
                self._extrair_tabelas(); return
            if nome == "salvar_html":
                self._salvar_html(); return

            if nome == "listar_memoria":
                self._listar_memoria(acao.get("formato", "")); return

            if nome == "exportar":
                p = self.mm.exportar(
                    acao.get("formato", "json"),
                    base_dir="exports",
                    somente_favoritos=acao.get("somente_favoritos", False),
                    filtro=acao.get("filtro", ""),
                )
                self._log(f"Exportado: {p}")
                return

            if nome == "screenshot":
                p = self._screenshot(); self._log(f"Screenshot salvo: {p}")
                return

            if nome == "repetir_ultimo":
                ultimo = self.mm.get_ultimo()
                if ultimo:
                    self._log(f"Reexecutando: {ultimo}")
                    self._processar(ultimo)
                else:
                    self._log("Sem último comando")
                return

            if nome == "help":
                self._log(self._help_text()); return

            if nome == "limpar":
                self._limpar(); return

            if nome == "sair":
                self._on_close(); return

            if nome == "resumir":
                html = ""
                try:
                    html = self.driver.page_source
                except Exception:
                    pass
                pedido = acao.get("pedido", "Resuma a página atual.")
                resp = conversar_ia(f"{pedido}\n\nHTML:\n{html[:6000]}")
                self._log("IA:\n" + resp)
                return

            if nome == "criar_macro":
                self._criar_macro(acao.get("nome", "macro")); return
            if nome == "parar_macro":
                self._parar_macro(); return
            if nome == "rodar_macro":
                self._rodar_macro(acao.get("nome", "")); return
            if nome == "listar_macros":
                self._log("Macros: " + (", ".join(self.mm.listar_macros()) or "(nenhuma)")); return

            self._log(f"Ação não reconhecida: {nome}")

        except Exception as e:
            self._log(f"Erro ao executar: {e}")

    def _abrir_url(self, url: str):
        self._set_status("Abrindo navegador…")
        if self.driver is None:
            self.driver = iniciar_navegador(headless=False)
        self._set_status(f"Acessando {url}…")
        self.driver.get(url)
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self._log(f"Site aberto: {url}")
        def _do():
            try:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, url)
            except Exception:
                pass
        self._on_ui(_do)
        self._set_status(self._status_text())

    def _status_text(self):
        if self.gravando_macro:
            return f"IA pronta – Macro: {self.gravando_macro} ({self.gravando_count} cmds)"
        return f"IA pronta – Navegador: {'ativo' if self.driver else 'inativo'}"

    def _enter(self):
        try:
            body = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            body.send_keys(Keys.ENTER)
            self._log("ENTER enviado")
        except Exception:
            self._log("ENTER falhou")
        self._set_status(self._status_text())

    def _encontrar_elemento(self, loc: dict):
        if not loc:
            return None, "nenhum localizador"
        tipo = (loc.get("tipo") or "").lower()
        val = loc.get("valor") or ""
        try:
            if tipo == "css" and val:
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, val)))
                return el, f"css={val}"
            if tipo == "xpath" and val:
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.XPATH, val)))
                return el, f"xpath={val}"
            if tipo == "id" and val:
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.ID, val)))
                return el, f"id={val}"
            if tipo == "name" and val:
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.NAME, val)))
                return el, f"name={val}"
            if tipo in ("class","classe") and val:
                classes = [c for c in val.strip().split() if c]
                sel = "".join([f".{c}" for c in classes]) or f".{val}"
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                return el, f"class={val}"
            if tipo in ("type","tipo") and val:
                v = val.lower()
                xp = f"//input[translate(@type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='{v}']"
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.XPATH, xp)))
                return el, f"type={val}"
            if tipo == "placeholder" and val:
                v = val.lower()
                xp = "//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '" + v + "')]"
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.XPATH, xp)))
                return el, f"placeholder~{val}"
            if tipo in ("aria-label","aria") and val:
                v = val.lower()
                xp = "//*[@aria-label and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '" + v + "')]"
                el = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.XPATH, xp)))
                return el, f"aria-label~{val}"
            if tipo == "texto" and val:
                v = val.lower()
                xp_text = (
                    "//*[self::button or self::a or self::div or self::span or self::label]"
                    f"[contains(translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')," +
                    f"'{v}')]"
                )
                try:
                    el = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.XPATH, xp_text)))
                    return el, f"texto~{val}"
                except Exception:
                    xp_input = (
                        "//input[@type='text' or @type='search' or @type='email' or @type='password' or @type='tel' or @type='number']"
                        f"[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{v}')]"
                    )
                    el = WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.XPATH, xp_input)))
                    return el, f"campo~{val}"
        except Exception:
            return None, f"não encontrado: {tipo}={val}"
        return None, f"localizador inválido: {tipo}={val}"

    def _clicar_smart(self, loc: dict):
        try:
            el, desc = self._encontrar_elemento(loc)
            if not el:
                self._log(f"Elemento não encontrado ({desc})")
                return
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            try:
                el.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", el)
            self._log(f"Clique em {desc}")
        except Exception as e:
            self._log(f"Falha ao clicar: {e}")

    def _digitar_smart(self, texto: str, loc: dict):
        try:
            el, desc = self._encontrar_elemento(loc)
            if not el:
                self._log(f"Campo não encontrado ({desc})")
                return
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            try:
                el.clear()
            except Exception:
                pass
            el.send_keys(texto)
            self._log(f"Digitado em {desc}: '{texto}'")
        except Exception as e:
            self._log(f"Falha ao digitar: {e}")

    def _fechar_popup(self):
        candidatos = [
            "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'fechar')]",
            "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'close')]",
            "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'ok')]",
            "//div[@role='dialog']//button",
            "//span[text()='×' or text()='x']/ancestor::button[1]",
        ]
        for xp in candidatos:
            try:
                el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, xp)))
                self.driver.execute_script("arguments[0].click();", el)
                self._log("Popup fechado")
                return
            except Exception:
                continue
        # ESC como fallback
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            self._log("Tentativa de fechar com ESC")
        except Exception:
            self._log("Nenhum popup fechado")

    def _extrair_noticias(self):
        try:
            from lxml import html as lhtml
        except Exception as e:
            self._log(f"lxml não disponível: {e}")
            return
        try:
            src = self.driver.page_source
            tree = lhtml.fromstring(src)
            base = self.driver.current_url
            itens = []
            # preferir artigos e headings
            for a in tree.xpath("//article//a[normalize-space(string())] | //h1//a | //h2//a | //h3//a"):
                titulo = " ".join(" ".join(a.itertext()).split())[:300]
                href = a.get("href") or ""
                if not titulo or not href:
                    continue
                link = urljoin(base, href)
                itens.append({"titulo": titulo, "link": link})
            # fallback: links proeminentes
            if not itens:
                for a in tree.xpath("//a[normalize-space(string())]"):
                    titulo = " ".join(" ".join(a.itertext()).split())[:300]
                    href = a.get("href") or ""
                    if len(titulo) >= 24 and href:
                        itens.append({"titulo": titulo, "link": urljoin(base, href)})
            # limitar
            vistos = set()
            uniq = []
            for n in itens:
                k = (n["titulo"], n["link"])
                if k in vistos:
                    continue
                vistos.add(k)
                uniq.append(n)
            noticias = uniq[:100]
            self.mm.set_noticias(noticias)
            self._render_noticias(noticias)
            self._log(f"Notícias extraídas: {len(noticias)}")
        except Exception as e:
            self._log(f"Falha ao extrair notícias: {e}")

    def _render_noticias(self, noticias):
        def _do():
            # limpar conteúdo do frame (mantém a primeira label do cabeçalho em row 0)
            for child in list(self.cards.winfo_children())[1:]:
                try:
                    child.destroy()
                except Exception:
                    pass
            for i, n in enumerate(noticias, start=1):
                titulo = n.get("titulo", "")
                link = n.get("link", "")
                row = i
                lbl = ctk.CTkLabel(self.cards, text=f"{i}. {titulo}", anchor="w", justify="left")
                lbl.grid(row=row, column=0, sticky="ew", padx=10, pady=4)
                def abrir(l=link):
                    if l:
                        self._processar(f"abrir {l}")
                def favoritar(item=n):
                    self.mm.toggle_favorito(item)
                    self._log("Favoritos: " + str(len(self.mm.get_favoritos())))
                btns = ctk.CTkFrame(self.cards, fg_color="transparent")
                btns.grid(row=row, column=1, padx=8, pady=4)
                ctk.CTkButton(btns, text="Abrir", width=70, command=abrir).pack(side="left", padx=4)
                ctk.CTkButton(btns, text="Favoritar", width=90, command=favoritar).pack(side="left", padx=4)
        self._on_ui(_do)

    def _extrair_links(self):
        try:
            from lxml import html as lhtml
            tree = lhtml.fromstring(self.driver.page_source)
            base = self.driver.current_url
            links = [urljoin(base, a) for a in tree.xpath("//a/@href")]
            self._log(f"Links encontrados: {len(links)}")
        except Exception as e:
            self._log(f"Falha ao extrair links: {e}")

    def _extrair_imagens(self):
        try:
            from lxml import html as lhtml
            tree = lhtml.fromstring(self.driver.page_source)
            base = self.driver.current_url
            imgs = [urljoin(base, a) for a in tree.xpath("//img/@src")]
            self._log(f"Imagens encontradas: {len(imgs)}")
        except Exception as e:
            self._log(f"Falha ao extrair imagens: {e}")

    def _extrair_tabelas(self):
        try:
            from lxml import html as lhtml
            tree = lhtml.fromstring(self.driver.page_source)
            tabelas = tree.xpath("//table")
            self._log(f"Tabelas encontradas: {len(tabelas)}")
        except Exception as e:
            self._log(f"Falha ao extrair tabelas: {e}")

    def _salvar_html(self):
        try:
            os.makedirs("exports", exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d_%Hh%M%S")
            p = os.path.join("exports", f"pagina_{ts}.html")
            with open(p, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self._log(f"HTML salvo em {p}")
        except Exception as e:
            self._log(f"Falha ao salvar HTML: {e}")

    def _listar_memoria(self, formato: str = ""):
        use_favs = "favorit" in (formato or "").lower()
        itens = self.mm.get_favoritos() if use_favs else self.mm.get_noticias()
        if not itens:
            self._log("Nenhuma notícia na memória.")
            return
        linhas = []
        for i, n in enumerate(itens, 1):
            linhas.append(f"{i}. {n.get('titulo','')} - {n.get('link','')}")
        self._log("\n".join(linhas))

    def _screenshot(self):
        try:
            os.makedirs("exports", exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d_%Hh%M%S")
            p = os.path.join("exports", f"screenshot_{ts}.png")
            self.driver.save_screenshot(p)
            return p
        except Exception as e:
            self._log(f"Falha ao capturar tela: {e}")
            return ""

    def _help_text(self) -> str:
        return (
            "Comandos:\n"
            "- abrir <url> | recarregar | voltar | avançar | nova aba | fechar aba\n"
            "- clicar no xpath <...> | clicar \"Texto do Botão\"\n"
            "- digitar \"texto\" no xpath <...> | enter | fechar popup\n"
            "- pegue as noticias | extrair links | extrair imagens | extrair tabelas | salvar html\n"
            "- listar noticias | exportar json/csv/txt/xlsx/html [favoritos] [\"filtro\"]\n"
            "- screenshot | repetir ultimo | limpar | sair\n"
            "- criar macro \"nome\" | parar macro | rodar macro \"nome\" | listar macros\n"
        )

    def _criar_macro(self, nome: str):
        if not nome:
            nome = self._ask_string("Criar Macro", "Nome da macro:") or "macro"
        self.gravando_macro = nome
        self.gravando_count = 0
        self.mm.salvar_macro(nome, [])
        self._update_macro_header()
        self._log(f"Gravação de macro iniciada: {nome}")
        self._set_status(self._status_text())

    def _parar_macro(self):
        if self.gravando_macro:
            self._log(f"Gravação da macro '{self.gravando_macro}' finalizada ({self.gravando_count} comandos).")
        self.gravando_macro = None
        self.gravando_count = 0
        self._update_macro_header()
        self._set_status(self._status_text())

    def _rodar_macro(self, nome: str):
        if not nome:
            nome = self._ask_string("Rodar Macro", "Nome da macro:") or ""
        comandos = self.mm.obter_macro(nome)
        if not comandos:
            self._log("Macro não encontrada ou vazia.")
            return
        self._log(f"Executando macro '{nome}' ({len(comandos)} comandos)...")
        self.executando_macro = True
        try:
            for cmd in comandos:
                self._log(f"> {cmd}")
                self._processar(cmd)
                time.sleep(0.6)
        finally:
            self.executando_macro = False
        self._log("Macro concluída.")

    def _ask_string(self, title: str, prompt: str, default: str = "") -> str:
        result = {"v": None}
        ev = threading.Event()
        def _do():
            try:
                v = simpledialog.askstring(title, prompt, initialvalue=default, parent=self)
            except Exception:
                v = default
            result["v"] = v
            ev.set()
        self._on_ui(_do)
        ev.wait()
        return result["v"]

    def _update_macro_header(self):
        def _do():
            if self.header_macro_btn:
                try:
                    self.header_macro_btn.destroy()
                except Exception:
                    pass
                self.header_macro_btn = None
            if self.gravando_macro:
                self.header_macro_btn = ctk.CTkButton(
                    self.header,
                    text=f"Gravando: {self.gravando_macro} ({self.gravando_count}) – Parar",
                    fg_color="#ef4444",
                    hover_color="#dc2626",
                    command=self._parar_macro,
                )
                self.header_macro_btn.grid(row=0, column=3, padx=10, pady=12)
        self._on_ui(_do)

    def _on_ui(self, func, *args, **kwargs):
        try:
            if threading.current_thread() is threading.main_thread():
                func(*args, **kwargs)
            else:
                self.after(0, lambda: func(*args, **kwargs))
        except Exception:
            # Silencia erros ocasionais de fechamento/visibilidade quando janela é destruída
            pass

    def _on_close(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()
